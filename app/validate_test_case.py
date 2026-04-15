import json
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


def main() -> None:
    test_case_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_CASE_PATH

    if not test_case_path.exists():
        raise FileNotFoundError(f"테스트 케이스 파일이 없습니다: {test_case_path}")

    test_case_data = read_json_file(test_case_path)

    missing_fields = validate_missing_fields(test_case_data)
    empty_string_fields = validate_empty_string_fields(test_case_data)
    empty_list_fields = validate_empty_list_fields(test_case_data)

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

    if not has_error:
        print("최종 결과: PASS")
    else:
        print("최종 결과: FAIL")


if __name__ == "__main__":
    main()
