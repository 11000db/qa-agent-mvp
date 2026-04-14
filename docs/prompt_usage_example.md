# Prompt Usage Example

## 목적
이 문서는 `prompts/requirement_to_test_case.md` 프롬프트를
실제 요구사항과 어떻게 결합해서 사용하는지 설명하기 위한 예시 문서다.

핵심 개념은 아래와 같다.

- 프롬프트 템플릿에는 `{{requirement_text}}` 라는 자리표시자가 있다.
- 실제 실행 시에는 이 자리에 요구사항 원문이 들어간다.
- 그러면 AI는 요구사항을 읽고 JSON 형식의 테스트 케이스를 생성한다.

---

## 사용 흐름

### 1. 프롬프트 템플릿 준비
파일:
- `prompts/requirement_to_test_case.md`

이 파일에는 테스트 케이스를 어떻게 생성해야 하는지에 대한 규칙이 들어 있다.

### 2. 요구사항 텍스트 준비
예시 파일:
- `sample_inputs/login_requirement.md`
- `sample_inputs/signup_requirement.md`
- `sample_inputs/cart_requirement.md`

이 파일들 중 하나의 내용을 읽어서 사용한다.

### 3. 자리표시자 치환
프롬프트 안에 있는 아래 부분:

```text
{{requirement_text}}
