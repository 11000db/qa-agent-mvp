import json
import re
import sys
from pathlib import Path

REQUIRED_STRING_FIELDS = [
    "feature_name",
    "requirement_summary",
    "priority",
    "risk_level"
]

REQUIRED_LIST_FIELDS = [
    "preconditions",
    "test_steps",
    "expected_results",
    "negative_cases",
    "edge_cases",
    "traceability"
]

ALLOWED_PRIORITY_VALUES = ["P0", "P1", "P2", "P3"]
ALLOWED_RISK_LEVEL_VALUES = ["High", "Medium", "Low"]

TRACEABILITY_PATTERN = r"^REQ-[A-Z0-9]+-\d{3}: .+"

DEFAULT_TEST_CASE_PATH = Path("sample_outputs/login_test_case.json")


def read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_missing_fields(data: dict) -> list:
    missing_fields = []

    for field in REQUIRED_STRING_FIELDS + REQUIRED_LIST_FIELDS:
        if field not in data:
            missing_fields.append(field)

    return missing_fields


def validate_empty_string_fields(data: dict) -> list:
    empty_string_fields = []

    for field in REQUIRED_STRING_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and value.strip() == "":
            empty_string_fields.append(field)

    return empty_string_fields


def validate_empty_list_fields(data: dict) -> list:
    empty_list_fields = []

    for field in REQUIRED_LIST_FIELDS:
        value = data.get(field)
        if isinstance(value, list) and len(value) == 0:
            empty_list_fields.append(field)

    return empty_list_fields


def validate_enum_fields(data: dict) -> list:
    invalid_fields = []

    priority = data.get("priority")
    risk_level = data.get("risk_level")

    if priority is not None and priority not in ALLOWED_PRIORITY_VALUES:
        invalid_fields.append(f"priority: {priority}")

    if risk_level is not None and risk_level not in ALLOWED_RISK_LEVEL_VALUES:
        invalid_fields.append(f"risk_level: {risk_level}")

    return invalid_fields


def validate_traceability_format(data: dict) -> list:
    invalid_traceability_items = []

    traceability_items = data.get("traceability", [])

    if not isinstance(traceability_items, list):
        return ["traceability field is not a list"]

    for item in traceability_items:
        if not isinstance(item, str):
            invalid_traceability_items.append(str(item))
            continue

        if not re.match(TRACEABILITY_PATTERN, item):
            invalid_traceability_items.append(item)

    return invalid_traceability_items


def normalize_text(value: str) -> str:
    return value.strip().lower()


def validate_duplicate_case_items(data: dict) -> list:
    duplicate_items = []

    negative_cases = data.get("negative_cases", [])
    edge_cases = data.get("edge_cases", [])

    if not isinstance(negative_cases, list) or not isinstance(edge_cases, list):
        return ["negative_cases or edge_cases is not a list"]

    normalized_negative_cases = {}
    normalized_edge_cases = {}

    for item in negative_cases:
        if isinstance(item, str):
            normalized_negative_cases[normalize_text(item)] = item

    for item in edge_cases:
        if isinstance(item, str):
            normalized_edge_cases[normalize_text(item)] = item

    for normalized_text in normalized_negative_cases:
        if normalized_text in normalized_edge_cases:
            duplicate_items.append(normalized_negative_cases[normalized_text])

    return duplicate_items


def main() -> None:
    test_case_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_CASE_PATH

    if not test_case_path.exists():
        raise FileNotFoundError(f"테스트 케이스 파일이 없습니다: {test_case_path}")

    test_case_data = read_json_file(test_case_path)

    missing_fields = validate_missing_fields(test_case_data)
    empty_string_fields = validate_empty_string_fields(test_case_data)
    empty_list_fields = validate_empty_list_fields(test_case_data)
    invalid_enum_fields = validate_enum_fields(test_case_data)
    invalid_traceability_items = validate_traceability_format(test_case_data)
    duplicate_case_items = validate_duplicate_case_items(test_case_data)

    print("테스트 케이스 파일 검사 시작")
    print(f"- 대상 파일: {test_case_path}")

    has_error = False

    if not missing_fields:
        print("1. required 필드 존재 여부: PASS")
    else:
        has_error = True
        print("1. required 필드 존재 여부: FAIL")
        print("누락된 필드:")
        for field in missing_fields:
            print(f"- {field}")

    if not empty_string_fields:
        print("2. 필수 문자열 필드 공백 여부: PASS")
    else:
        has_error = True
        print("2. 필수 문자열 필드 공백 여부: FAIL")
        print("빈 문자열 필드:")
        for field in empty_string_fields:
            print(f"- {field}")

    if not empty_list_fields:
        print("3. 필수 리스트 필드 공백 여부: PASS")
    else:
        has_error = True
        print("3. 필수 리스트 필드 공백 여부: FAIL")
        print("빈 리스트 필드:")
        for field in empty_list_fields:
            print(f"- {field}")

    if not invalid_enum_fields:
        print("4. priority / risk_level 허용값 여부: PASS")
    else:
        has_error = True
        print("4. priority / risk_level 허용값 여부: FAIL")
        print("허용되지 않은 값:")
        for field in invalid_enum_fields:
            print(f"- {field}")

    if not invalid_traceability_items:
        print("5. traceability 형식 여부: PASS")
    else:
        has_error = True
        print("5. traceability 형식 여부: FAIL")
        print("형식이 올바르지 않은 traceability 항목:")
        for item in invalid_traceability_items:
            print(f"- {item}")

    if not duplicate_case_items:
        print("6. negative_cases / edge_cases 중복 여부: PASS")
    else:
        has_error = True
        print("6. negative_cases / edge_cases 중복 여부: FAIL")
        print("중복된 항목:")
        for item in duplicate_case_items:
            print(f"- {item}")

    if not has_error:
        print("최종 결과: PASS")
    else:
        print("최종 결과: FAIL")


if __name__ == "__main__":
    main()
