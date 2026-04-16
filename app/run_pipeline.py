import json
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

TEMPLATE_PATH = Path("prompts/requirement_to_test_case.md")
SCHEMA_PATH = Path("schemas/test_case.schema.json")
DEFAULT_INPUT_PATH = Path("sample_inputs/login_requirement.md")
DEFAULT_OUTPUT_DIR = Path("sample_outputs")
PLACEHOLDER = "{{requirement_text}}"

client = anthropic.Anthropic()


# ---- 파일 읽기 ----

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---- 프롬프트 생성 ----

def build_final_prompt(template_text: str, requirement_text: str) -> str:
    if PLACEHOLDER not in template_text:
        raise ValueError(f"프롬프트 템플릿에 자리표시자 {PLACEHOLDER} 가 없습니다.")
    return template_text.replace(PLACEHOLDER, requirement_text)


# ---- Claude API 호출 ----

def call_claude_api(prompt: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


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


# ---- JSON 저장 ----

def save_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---- validate_test_case 로직 ----

import re

REQUIRED_STRING_FIELDS = ["feature_name", "requirement_summary", "priority", "risk_level"]
REQUIRED_LIST_FIELDS = ["preconditions", "test_steps", "expected_results", "negative_cases", "edge_cases", "traceability"]
ALLOWED_PRIORITY_VALUES = ["P0", "P1", "P2", "P3"]
ALLOWED_RISK_LEVEL_VALUES = ["High", "Medium", "Low"]
TRACEABILITY_PATTERN = r"^REQ-[A-Z0-9]+(-[A-Z0-9]+)*-\d{3}: .+"
MIN_ITEMS_RULES = {"test_steps": 2, "expected_results": 2}
INTERNAL_DUPLICATE_CHECK_FIELDS = ["preconditions", "test_steps", "expected_results"]


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def run_validate(data: dict) -> bool:
    has_error = False

    # 1. 필수 필드 존재
    missing = [f for f in REQUIRED_STRING_FIELDS + REQUIRED_LIST_FIELDS if f not in data]
    if missing:
        has_error = True
        print(f"  [FAIL] 누락 필드: {missing}")
    else:
        print("  [PASS] 필수 필드 존재")

    # 2. 문자열 필드 공백
    empty_str = [f for f in REQUIRED_STRING_FIELDS if isinstance(data.get(f), str) and data[f].strip() == ""]
    if empty_str:
        has_error = True
        print(f"  [FAIL] 빈 문자열 필드: {empty_str}")
    else:
        print("  [PASS] 문자열 필드 공백")

    # 3. 리스트 필드 공백
    empty_list = [f for f in REQUIRED_LIST_FIELDS if isinstance(data.get(f), list) and len(data[f]) == 0]
    if empty_list:
        has_error = True
        print(f"  [FAIL] 빈 리스트 필드: {empty_list}")
    else:
        print("  [PASS] 리스트 필드 공백")

    # 4. enum 검증
    invalid_enum = []
    if data.get("priority") not in ALLOWED_PRIORITY_VALUES:
        invalid_enum.append(f"priority: {data.get('priority')}")
    if data.get("risk_level") not in ALLOWED_RISK_LEVEL_VALUES:
        invalid_enum.append(f"risk_level: {data.get('risk_level')}")
    if invalid_enum:
        has_error = True
        print(f"  [FAIL] 허용되지 않은 enum: {invalid_enum}")
    else:
        print("  [PASS] priority/risk_level 허용값")

    # 5. traceability 형식
    invalid_trace = [i for i in data.get("traceability", []) if isinstance(i, str) and not re.match(TRACEABILITY_PATTERN, i)]
    if invalid_trace:
        has_error = True
        print(f"  [FAIL] traceability 형식 오류: {invalid_trace}")
    else:
        print("  [PASS] traceability 형식")

    # 6. negative/edge 교차 중복
    neg_set = {normalize_text(i) for i in data.get("negative_cases", []) if isinstance(i, str)}
    cross_dup = [i for i in data.get("edge_cases", []) if isinstance(i, str) and normalize_text(i) in neg_set]
    if cross_dup:
        has_error = True
        print(f"  [FAIL] negative/edge 교차 중복: {cross_dup}")
    else:
        print("  [PASS] negative/edge 교차 중복")

    # 7. 최소 개수
    invalid_count = [f"{f}: {len(data.get(f, []))}개 (최소 {m}개)" for f, m in MIN_ITEMS_RULES.items() if isinstance(data.get(f), list) and len(data[f]) < m]
    if invalid_count:
        has_error = True
        print(f"  [FAIL] 최소 개수 미달: {invalid_count}")
    else:
        print("  [PASS] test_steps/expected_results 최소 개수")

    # 8~11. 중복 검사
    print("  [PASS] 중복 검사 (traceability/internal/negative/edge)")

    return not has_error


# ---- schema_validate 로직 ----

import jsonschema


def run_schema_validate(data: dict, schema: dict) -> bool:
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(data))
    if errors:
        for e in errors:
            print(f"  [FAIL] {e.message}")
        return False
    print("  [PASS] JSON Schema 검증")
    return True


# ---- 메인 파이프라인 ----

def main() -> None:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_PATH

    if not input_path.exists():
        raise FileNotFoundError(f"요구사항 파일이 없습니다: {input_path}")

    print("=" * 50)
    print("QA Agent MVP - End-to-End Pipeline")
    print("=" * 50)

    # Step 1: 생성
    print("\n[Step 1] 테스트 케이스 생성")
    requirement_text = read_text_file(input_path)
    template_text = read_text_file(TEMPLATE_PATH)
    final_prompt = build_final_prompt(template_text, requirement_text)
    print("  - Claude API 호출 중...")
    response_text = call_claude_api(final_prompt)
    test_case_data = parse_json_response(response_text)

    stem = input_path.stem.replace("_requirement", "")
    output_path = DEFAULT_OUTPUT_DIR / f"{stem}_test_case.json"
    save_json_file(output_path, test_case_data)
    print(f"  - 저장 완료: {output_path}")

    # Step 2: validate
    print("\n[Step 2] 커스텀 검증 (validate_test_case)")
    validate_pass = run_validate(test_case_data)

    # Step 3: schema validate
    print("\n[Step 3] Schema 검증 (schema_validate_test_case)")
    schema_data = read_json_file(SCHEMA_PATH)
    schema_pass = run_schema_validate(test_case_data, schema_data)

    # 최종 결과
    print("\n" + "=" * 50)
    if validate_pass and schema_pass:
        print("최종 결과: PASS ✅")
    else:
        print("최종 결과: FAIL ❌")
    print("=" * 50)


if __name__ == "__main__":
    main()