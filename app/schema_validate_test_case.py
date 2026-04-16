import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import validate, ValidationError

DEFAULT_TEST_CASE_PATH = Path("sample_outputs/login_test_case.json")
DEFAULT_SCHEMA_PATH = Path("schemas/test_case.schema.json")


def read_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_schema(test_case_data: dict, schema_data: dict) -> list:
    errors = []

    validator = jsonschema.Draft7Validator(schema_data)
    for error in validator.iter_errors(test_case_data):
        errors.append(error.message)

    return errors


def main() -> None:
    test_case_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_CASE_PATH
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SCHEMA_PATH

    if not test_case_path.exists():
        raise FileNotFoundError(f"테스트 케이스 파일이 없습니다: {test_case_path}")

    if not schema_path.exists():
        raise FileNotFoundError(f"스키마 파일이 없습니다: {schema_path}")

    test_case_data = read_json_file(test_case_path)
    schema_data = read_json_file(schema_path)

    print("JSON Schema 검증 시작")
    print(f"- 대상 파일: {test_case_path}")
    print(f"- 스키마 파일: {schema_path}")

    errors = validate_schema(test_case_data, schema_data)

    if not errors:
        print("Schema 검증 결과: PASS")
    else:
        print("Schema 검증 결과: FAIL")
        print("발견된 오류:")
        for error in errors:
            print(f"- {error}")


if __name__ == "__main__":
    main()