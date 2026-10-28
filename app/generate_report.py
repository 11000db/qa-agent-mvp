import sys
from pathlib import Path

import core

# [기록] Day 17 원본은 이 파일 안에 검증 규칙을 따로 구현했고 7개 규칙만 검사했다
#        (8~11번 중복 검사 누락). Day 25에 core.py로 통합해서 11개 규칙 모두 검사한다.
#        원본 코드: git show ac8e426:app/generate_report.py

DEFAULT_TEST_CASE_PATH = Path("sample_outputs/login_test_case.json")
DEFAULT_REPORT_DIR = Path("sample_reports")


def main() -> None:
    test_case_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_CASE_PATH

    if not test_case_path.exists():
        raise FileNotFoundError(f"테스트 케이스 파일이 없습니다: {test_case_path}")

    data = core.read_json_file(test_case_path)
    validation = core.validate_test_case(data)
    report_content = core.build_report_markdown(data, validation, source=str(test_case_path))

    report_path = DEFAULT_REPORT_DIR / f"{test_case_path.stem}_validation_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_content, encoding="utf-8")

    print(f"리포트 생성 완료: {report_path}")


if __name__ == "__main__":
    main()
