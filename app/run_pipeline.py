import argparse
import json
from pathlib import Path

import core

DEFAULT_INPUT_PATH = Path("sample_inputs/login_requirement.md")
DEFAULT_OUTPUT_DIR = Path("sample_outputs")


def save_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="QA Agent MVP - End-to-End Pipeline")
    parser.add_argument("input_path", nargs="?", default=str(DEFAULT_INPUT_PATH), help="요구사항 문서 경로")
    parser.add_argument("--mode", choices=core.MODES, default="auto",
                        help="auto: API 키가 있으면 live, 없으면 mock / mock: 샘플 결과 사용 / live: Claude API 호출")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"요구사항 파일이 없습니다: {input_path}")

    print("=" * 50)
    print("QA Agent MVP - End-to-End Pipeline")
    print("=" * 50)

    # Step 1: 생성
    print("\n[Step 1] 테스트 케이스 생성")
    requirement_text = input_path.read_text(encoding="utf-8")
    used_mode = core.resolve_mode(args.mode)
    print(f"  - mode: {used_mode}")
    if used_mode == "live":
        print("  - Claude API 호출 중...")
    test_case_data, _ = core.generate_test_case(requirement_text, used_mode)

    # mock 모드는 샘플 결과를 덮어쓰지 않는다
    if used_mode == "live":
        stem = input_path.stem.replace("_requirement", "")
        output_path = DEFAULT_OUTPUT_DIR / f"{stem}_test_case.json"
        save_json_file(output_path, test_case_data)
        print(f"  - 저장 완료: {output_path}")

    validation = core.validate_test_case(test_case_data)

    # Step 2: 커스텀 검증 (11개 규칙)
    print("\n[Step 2] 커스텀 검증 (validate_test_case)")
    for r in validation["custom_results"]:
        if r["passed"]:
            print(f"  [PASS] {r['no']}. {r['name']}")
        else:
            print(f"  [FAIL] {r['no']}. {r['name']}: {r['details']}")

    # Step 3: schema validate
    print("\n[Step 3] Schema 검증 (schema_validate_test_case)")
    if validation["schema_pass"]:
        print("  [PASS] JSON Schema 검증")
    else:
        for err in validation["schema_errors"]:
            print(f"  [FAIL] {err}")

    # 최종 결과
    print("\n" + "=" * 50)
    if validation["overall_pass"]:
        print("최종 결과: PASS ✅")
    else:
        print("최종 결과: FAIL ❌")
    print("=" * 50)


if __name__ == "__main__":
    main()
