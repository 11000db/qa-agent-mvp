"""
QA Agent 핵심 로직 (Day 25)

CLI(run_pipeline.py)와 웹 서버(server.py)가 같은 로직을 쓰도록
파일 입출력/print 없이 dict를 주고받는 순수 함수로 분리한 모듈.
"""
import copy
import json
import os
from datetime import datetime
from pathlib import Path

import jsonschema
from dotenv import load_dotenv

from generate_playwright import generate_playwright_code
from validate_test_case import (
    validate_duplicate_case_items,
    validate_duplicate_edge_cases,
    validate_duplicate_internal_list_items,
    validate_duplicate_negative_cases,
    validate_duplicate_traceability_items,
    validate_empty_list_fields,
    validate_empty_string_fields,
    validate_enum_fields,
    validate_minimum_items,
    validate_missing_fields,
    validate_traceability_format,
)

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "prompts" / "requirement_to_test_case.md"
SCHEMA_PATH = ROOT_DIR / "schemas" / "test_case.schema.json"
SAMPLE_INPUT_DIR = ROOT_DIR / "sample_inputs"
SAMPLE_OUTPUT_DIR = ROOT_DIR / "sample_outputs"
PLACEHOLDER = "{{requirement_text}}"

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = 4096

MODES = ("auto", "mock", "live")

# mock 모드: 요구사항 키워드로 sample_outputs 중 하나를 고른다
MOCK_KEYWORDS = {
    "cart": ["장바구니", "cart", "카트"],
    "signup": ["회원가입", "signup", "sign up", "가입"],
    "login": ["로그인", "login", "로그아웃", "비밀번호"],
}
DEFAULT_MOCK_SAMPLE = "login"

# 11개 커스텀 검증 규칙 (번호, 이름, 검사 함수)
VALIDATION_RULES = [
    (1, "필수 필드 존재 여부", validate_missing_fields),
    (2, "필수 문자열 필드 공백 여부", validate_empty_string_fields),
    (3, "필수 리스트 필드 공백 여부", validate_empty_list_fields),
    (4, "priority / risk_level 허용값 여부", validate_enum_fields),
    (5, "traceability 형식 여부", validate_traceability_format),
    (6, "negative_cases / edge_cases 교차 중복 여부", validate_duplicate_case_items),
    (7, "test_steps / expected_results 최소 개수 여부", validate_minimum_items),
    (8, "traceability 내부 중복 여부", validate_duplicate_traceability_items),
    (9, "preconditions / test_steps / expected_results 내부 중복 여부", validate_duplicate_internal_list_items),
    (10, "negative_cases 내부 중복 여부", validate_duplicate_negative_cases),
    (11, "edge_cases 내부 중복 여부", validate_duplicate_edge_cases),
]


class GenerationError(Exception):
    """Claude 응답을 테스트 케이스로 만들지 못했을 때"""


# ---- 파일 읽기 ----

def read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schema() -> dict:
    return read_json_file(SCHEMA_PATH)


def list_sample_requirements() -> list:
    samples = []
    for path in sorted(SAMPLE_INPUT_DIR.glob("*_requirement.md")):
        samples.append({
            "name": path.stem.replace("_requirement", ""),
            "requirement_text": path.read_text(encoding="utf-8"),
        })
    return samples


# ---- 프롬프트 생성 ----

def build_final_prompt(template_text: str, requirement_text: str) -> str:
    if PLACEHOLDER not in template_text:
        raise ValueError(f"프롬프트 템플릿에 자리표시자 {PLACEHOLDER} 가 없습니다.")
    return template_text.replace(PLACEHOLDER, requirement_text)


# ---- JSON 파싱 ----

def parse_json_response(response_text: str) -> dict:
    cleaned = response_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0]
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end != 0:
        cleaned = cleaned[start:end]
    return json.loads(cleaned.strip())


# ---- 테스트 케이스 생성 ----

def resolve_mode(mode: str) -> str:
    if mode not in MODES:
        raise ValueError(f"지원하지 않는 mode 입니다: {mode} (허용: {', '.join(MODES)})")
    if mode == "auto":
        return "live" if os.getenv("ANTHROPIC_API_KEY") else "mock"
    return mode


def pick_mock_sample(requirement_text: str) -> str:
    text = requirement_text.lower()
    for name, keywords in MOCK_KEYWORDS.items():
        if any(k in text for k in keywords):
            return name
    return DEFAULT_MOCK_SAMPLE


def generate_mock_test_case(requirement_text: str) -> dict:
    sample_name = pick_mock_sample(requirement_text)
    data = read_json_file(SAMPLE_OUTPUT_DIR / f"{sample_name}_test_case.json")
    return copy.deepcopy(data)


def call_claude_api(prompt: str) -> str:
    # API 키가 없어도 mock 모드가 동작하도록 live 호출 시점에만 SDK를 불러온다
    import anthropic

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    if message.stop_reason == "max_tokens":
        raise GenerationError(f"응답이 max_tokens({MAX_TOKENS})에서 잘렸습니다.")
    return "".join(block.text for block in message.content if block.type == "text")


def generate_live_test_case(requirement_text: str) -> dict:
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    prompt = build_final_prompt(template_text, requirement_text)
    response_text = call_claude_api(prompt)
    try:
        data = parse_json_response(response_text)
    except json.JSONDecodeError as e:
        raise GenerationError(f"Claude 응답을 JSON으로 파싱하지 못했습니다: {e}") from e
    if not isinstance(data, dict):
        raise GenerationError("Claude 응답이 JSON 객체가 아닙니다.")
    return data


def generate_test_case(requirement_text: str, mode: str = "auto") -> tuple:
    """(테스트 케이스 dict, 실제 사용된 mode) 반환"""
    used_mode = resolve_mode(mode)
    if used_mode == "mock":
        return generate_mock_test_case(requirement_text), used_mode
    return generate_live_test_case(requirement_text), used_mode


# ---- 검증 ----

def run_custom_validation(data: dict) -> list:
    results = []
    for no, name, rule in VALIDATION_RULES:
        details = rule(data)
        results.append({
            "no": no,
            "name": name,
            "passed": not details,
            "details": details,
        })
    return results


def run_schema_validation(data: dict, schema: dict = None) -> list:
    schema = schema if schema is not None else load_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path)
        errors.append(f"{path}: {error.message}" if path else error.message)
    return errors


def validate_test_case(data: dict) -> dict:
    custom_results = run_custom_validation(data)
    schema_errors = run_schema_validation(data)
    custom_pass = all(r["passed"] for r in custom_results)
    schema_pass = not schema_errors
    return {
        "overall_pass": custom_pass and schema_pass,
        "custom_pass": custom_pass,
        "schema_pass": schema_pass,
        "custom_results": custom_results,
        "schema_errors": schema_errors,
    }


# ---- 리포트 ----

def build_report_markdown(data: dict, validation: dict, source: str = "-") -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# QA Validation Report",
        "",
        "## 기본 정보",
        "| 항목 | 내용 |",
        "|------|------|",
        f"| 생성 일시 | {now} |",
        f"| 대상 | {source} |",
        f"| 기능명 | {data.get('feature_name', 'Unknown')} |",
        f"| Priority | {data.get('priority', '-')} |",
        f"| Risk Level | {data.get('risk_level', '-')} |",
        "",
        "## 최종 결과",
        "",
        "**✅ PASS**" if validation["overall_pass"] else "**❌ FAIL**",
        "",
        "## 커스텀 검증 결과",
        "",
        "| 번호 | 검사 항목 | 결과 | 상세 |",
        "|------|----------|------|------|",
    ]
    for r in validation["custom_results"]:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        detail_str = ", ".join(str(d) for d in r["details"]) if r["details"] else "-"
        lines.append(f"| {r['no']} | {r['name']} | {status} | {detail_str} |")

    lines += ["", "## JSON Schema 검증 결과", ""]
    if validation["schema_pass"]:
        lines.append("✅ PASS")
    else:
        lines += ["❌ FAIL", "", "**발견된 오류:**"]
        lines += [f"- {err}" for err in validation["schema_errors"]]

    return "\n".join(lines)


# ---- Playwright ----

def build_playwright_spec(data: dict) -> str:
    return generate_playwright_code(data)
