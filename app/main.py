from pathlib import Path
import sys


TEMPLATE_PATH = Path("prompts/requirement_to_test_case.md")
DEFAULT_INPUT_PATH = Path("sample_inputs/login_requirement.md")
DEFAULT_OUTPUT_PATH = Path("sample_outputs/login_prompt.txt")
PLACEHOLDER = "{{requirement_text}}"


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_final_prompt(template_text: str, requirement_text: str) -> str:
    if PLACEHOLDER not in template_text:
        raise ValueError(f"프롬프트 템플릿에 자리표시자 {PLACEHOLDER} 가 없습니다.")
    return template_text.replace(PLACEHOLDER, requirement_text)


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_PATH
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"프롬프트 파일이 없습니다: {TEMPLATE_PATH}")

    if not input_path.exists():
        raise FileNotFoundError(f"요구사항 파일이 없습니다: {input_path}")

    template_text = read_text_file(TEMPLATE_PATH)
    requirement_text = read_text_file(input_path)
    final_prompt = build_final_prompt(template_text, requirement_text)
    write_text_file(output_path, final_prompt)

    print("최종 프롬프트 파일 생성 완료")
    print(f"- 템플릿 파일: {TEMPLATE_PATH}")
    print(f"- 입력 요구사항 파일: {input_path}")
    print(f"- 출력 파일: {output_path}")
    print()
    print("미리보기 (앞 500자):")
    print(final_prompt[:500])


if __name__ == "__main__":
    main()
