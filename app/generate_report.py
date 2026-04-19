import json
import re
import sys
from datetime import datetime
from pathlib import Path

import jsonschema

REQUIRED_STRING_FIELDS = ["feature_name", "requirement_summary", "priority", "risk_level"]
REQUIRED_LIST_FIELDS = ["preconditions", "test_steps", "expected_results", "negative_cases", "edge_cases", "traceability"]
ALLOWED_PRIORITY_VALUES = ["P0", "P1", "P2", "P3"]
ALLOWED_RISK_LEVEL_VALUES = ["High", "Medium", "Low"]
TRACEABILITY_PATTERN = r"^REQ-[A-Z0-9]+(-[A-Z0-9]+)*-\d{3}: .+"
MIN_ITEMS_RULES = {"test_steps": 2, "expected_results": 2}

DEFAULT_TEST_CASE_PATH = Path("sample_outputs/login_test_case.json")
DEFAULT_SCHEMA_PATH = Path("schemas/test_case.schema.json")
DEFAULT_REPORT_DIR = Path("sample_reports")


def read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def run_validate(data: dict) -> list:
    results = []

    # 1. 필수 필드 존재
    missing = [f for f in REQUIRED_STRING_FIELDS + REQUIRED_LIST_FIELDS if f not in data]
    results.append(("필수 필드 존재 여부", not missing, missing))

    # 2. 문자열 필드 공백
    empty_str = [f for f in REQUIRED_STRING_FIELDS if isinstance(data.get(f), str) and data[f].strip() == ""]
    results.append(("필수 문자열 필드 공백 여부", not empty_str, empty_str))

    # 3. 리스트 필드 공백
    empty_list = [f for f in REQUIRED_LIST_FIELDS if isinstance(data.get(f), list) and len(data[f]) == 0]
    results.append(("필수 리스트 필드 공백 여부", not empty_list, empty_list))

    # 4. enum 검증
    invalid_enum = []
    if data.get("priority") not in ALLOWED_PRIORITY_VALUES:
        invalid_enum.append(f"priority: {data.get('priority')}")
    if data.get("risk_level") not in ALLOWED_RISK_LEVEL_VALUES:
        invalid_enum.append(f"risk_level: {data.get('risk_level')}")
    results.append(("priority / risk_level 허용값 여부", not invalid_enum, invalid_enum))

    # 5. traceability 형식
    invalid_trace = [i for i in data.get("traceability", []) if isinstance(i, str) and not re.match(TRACEABILITY_PATTERN, i)]
    results.append(("traceability 형식 여부", not invalid_trace, invalid_trace))

    # 6. negative/edge 교차 중복
    neg_set = {normalize_text(i) for i in data.get("negative_cases", []) if isinstance(i, str)}
    cross_dup = [i for i in data.get("edge_cases", []) if isinstance(i, str) and normalize_text(i) in neg_set]
    results.append(("negative_cases / edge_cases 중복 여부", not cross_dup, cross_dup))

    # 7. 최소 개수
    invalid_count = [f"{f}: {len(data.get(f, []))}개 (최소 {m}개)" for f, m in MIN_ITEMS_RULES.items() if isinstance(data.get(f), list) and len(data[f]) < m]
    results.append(("test_steps / expected_results 최소 개수 여부", not invalid_count, invalid_count))

    return results


def run_schema_validate(data: dict, schema: dict) -> list:
    errors = [e.message for e in jsonschema.Draft7Validator(schema).iter_errors(data)]
    return errors


def generate_report(test_case_path: Path, schema_path: Path) -> str:
    data = read_json_file(test_case_path)
    schema = read_json_file(schema_path)

    validate_results = run_validate(data)
    schema_errors = run_schema_validate(data, schema)

    validate_pass = all(r[1] for r in validate_results)
    schema_pass = not schema_errors
    overall_pass = validate_pass and schema_pass

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feature_name = data.get("feature_name", "Unknown")
    priority = data.get("priority", "-")
    risk_level = data.get("risk_level", "-")

    lines = []
    lines.append(f"# QA Validation Report")
    lines.append(f"")
    lines.append(f"## 기본 정보")
    lines.append(f"| 항목 | 내용 |")
    lines.append(f"|------|------|")
    lines.append(f"| 생성 일시 | {now} |")
    lines.append(f"| 대상 파일 | {test_case_path} |")
    lines.append(f"| 기능명 | {feature_name} |")
    lines.append(f"| Priority | {priority} |")
    lines.append(f"| Risk Level | {risk_level} |")
    lines.append(f"")
    lines.append(f"## 최종 결과")
    lines.append(f"")
    if overall_pass:
        lines.append(f"**✅ PASS**")
    else:
        lines.append(f"**❌ FAIL**")
    lines.append(f"")
    lines.append(f"## 커스텀 검증 결과")
    lines.append(f"")
    lines.append(f"| 검사 항목 | 결과 | 상세 |")
    lines.append(f"|----------|------|------|")
    for name, passed, details in validate_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        detail_str = ", ".join(details) if details else "-"
        lines.append(f"| {name} | {status} | {detail_str} |")
    lines.append(f"")
    lines.append(f"## JSON Schema 검증 결과")
    lines.append(f"")
    if schema_pass:
        lines.append(f"✅ PASS")
    else:
        lines.append(f"❌ FAIL")
        lines.append(f"")
        lines.append(f"**발견된 오류:**")
        for err in schema_errors:
            lines.append(f"- {err}")

    return "\n".join(lines)


def main() -> None:
    test_case_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_CASE_PATH
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SCHEMA_PATH

    if not test_case_path.exists():
        raise FileNotFoundError(f"테스트 케이스 파일이 없습니다: {test_case_path}")

    report_content = generate_report(test_case_path, schema_path)

    stem = test_case_path.stem
    report_path = DEFAULT_REPORT_DIR / f"{stem}_validation_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_content, encoding="utf-8")

    print(f"리포트 생성 완료: {report_path}")


if __name__ == "__main__":
    main()