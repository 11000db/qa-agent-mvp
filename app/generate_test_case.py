import json
import sys
from pathlib import Path
from datetime import datetime

import anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_INPUT_PATH = Path("sample_inputs/login_requirement.md")
DEFAULT_OUTPUT_DIR = Path("sample_outputs")
TEMPLATE_PATH = Path("prompts/requirement_to_test_case.md")
PLACEHOLDER = "{{requirement_text}}"

client = anthropic.Anthropic()


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_final_prompt(template_text: str, requirement_text: str) -> str:
    if PLACEHOLDER not in template_text:
        raise ValueError(f"프롬프트 템플릿에 자리표시자 {PLACEHOLDER} 가 없습니다.")
    return template_text.replace(PLACEHOLDER, requirement_text)


def call_claude_api(prompt: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,  # 2048 → 4096으로 변경
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def parse_json_response(response_text: str) -> dict:
    cleaned = response_text.strip()
    
    # ```json ... ``` 형태 처리
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0]
    
    # { 부터 } 까지만 추출
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end != 0:
        cleaned = cleaned[start:end]
    
    return json.loads(cleaned.strip())


def save_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT_PATH

    if not input_path.exists():
        raise FileNotFoundError(f"요구사항 파일이 없습니다: {input_path}")

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"프롬프트 템플릿 파일이 없습니다: {TEMPLATE_PATH}")

    # 파일 읽기
    requirement_text = read_text_file(input_path)
    template_text = read_text_file(TEMPLATE_PATH)

    # 프롬프트 생성
    final_prompt = build_final_prompt(template_text, requirement_text)

    print("테스트 케이스 생성 시작")
    print(f"- 입력 파일: {input_path}")

    # 클로드 API 호출
    print("- Claude API 호출 중...")
    response_text = call_claude_api(final_prompt)

    # JSON 파싱
    print("- 응답 파싱 중...")
    test_case_data = parse_json_response(response_text)

    # 출력 파일명 생성 (입력 파일명 기반)
    stem = input_path.stem.replace("_requirement", "")
    output_filename = f"{stem}_test_case.json"
    output_path = DEFAULT_OUTPUT_DIR / output_filename

    # 저장
    save_json_file(output_path, test_case_data)

    print(f"- 저장 완료: {output_path}")
    print("테스트 케이스 생성 완료")
    


if __name__ == "__main__":
    main()