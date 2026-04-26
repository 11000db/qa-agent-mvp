# Day 23 Summary: GitHub Actions CI/CD 구축

## 작업 날짜
2026-04-26

## 목표
GitHub Actions를 활용한 CI/CD 파이프라인 구축
push할 때마다 pytest API 테스트 자동 실행 및 리포트 아티팩트 업로드

## 작업 내용

### 1. .github/workflows/test.yml 생성
```yaml
name: QA Agent MVP CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: 코드 체크아웃
        uses: actions/checkout@v4

      - name: Python 환경 설정
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Python 패키지 설치
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: pytest API 테스트 실행
        run: python -m pytest tests/test_api_login.py -v --html=sample_reports/api_test_report.html

      - name: 리포트 아티팩트 업로드
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: api-test-report
          path: sample_reports/api_test_report.html
```

### 2. 트러블슈팅 이력
| 시도 | 문제 | 원인 | 해결 |
|------|------|------|------|
| #1 | upload-artifact 실패 | v3 deprecated | v4로 업그레이드 |
| #2 | exit code 127 | pytest 명령어 못 찾음 | python -m pytest 로 변경 |
| #3 | exit code 1 | No module named pytest | requirements.txt에 pytest, pytest-html 추가 |
| #4 | ✅ Success | - | - |

### 3. requirements.txt 업데이트
```
jsonschema
anthropic
python-dotenv
requests
pytest
pytest-html
```

## 최종 실행 결과
```
Status: Success ✅
Total duration: 16s
Artifacts: api-test-report (6.8 KB)
```

## CI/CD 동작 흐름
```
코드 push (main 브랜치)
        ↓
GitHub Actions 자동 트리거
        ↓
Python 3.11 환경 세팅
        ↓
requirements.txt 패키지 설치
        ↓
pytest API 테스트 자동 실행
        ↓
HTML 리포트 아티팩트 업로드
```

## 다음 단계 (Day 24)
- README에 CI 뱃지 추가
- Playwright CI 추가
- PR 코멘트 자동 등록