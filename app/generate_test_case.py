import json
import sys
from pathlib import Path

import core

# [기록] Day 15 원본은 이 파일 안에 프롬프트 조립 / Claude API 호출 / JSON 파싱을 직접 구현했다.
#        Day 25에 같은 로직을 core.py로 옮겨 CLI와 웹 서버가 함께 쓴다.
#        원본 코드: git show bd24ae4:app/generate_test_case.py

DEFAULT_INPUT_PATH = Path("sample_inputs/login_requirement.md")
DEFAULT_OUTPUT_DIR = Path("sample_outputs")


def save_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_PATH

    if not input_path.exists():
        raise FileNotFoundError(f"요구사항 파일이 없습니다: {input_path}")

    requirement_text = input_path.read_text(encoding="utf-8")

    print("테스트 케이스 생성 시작")
    print(f"- 입력 파일: {input_path}")
    print("- Claude API 호출 중...")
    test_case_data = core.generate_live_test_case(requirement_text)

    stem = input_path.stem.replace("_requirement", "")
    output_path = DEFAULT_OUTPUT_DIR / f"{stem}_test_case.json"
    save_json_file(output_path, test_case_data)

    print(f"- 저장 완료: {output_path}")
    print("테스트 케이스 생성 완료")


if __name__ == "__main__":
    main()
