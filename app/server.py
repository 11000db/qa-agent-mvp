"""
QA Agent 웹 API 서버 (Day 25)

실행:
    python app/server.py
    → http://127.0.0.1:8000/docs (Swagger UI)
"""
import os
from typing import Literal

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import core

MAX_REQUIREMENT_LENGTH = 20000

app = FastAPI(
    title="QA Agent MVP API",
    description="요구사항 → 테스트 케이스 생성 → 11개 규칙 + JSON Schema 검증 → 리포트 → Playwright 코드",
    version="0.1.0",
)


class RequirementRequest(BaseModel):
    requirement_text: str = Field(..., min_length=1, max_length=MAX_REQUIREMENT_LENGTH)
    mode: Literal["auto", "mock", "live"] = "auto"


class TestCaseRequest(BaseModel):
    test_case: dict


def _generate(req: RequirementRequest) -> tuple:
    if not req.requirement_text.strip():
        raise HTTPException(status_code=422, detail="requirement_text가 비어 있습니다.")
    if req.mode == "live" and not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=400, detail="live 모드는 ANTHROPIC_API_KEY 설정이 필요합니다.")
    try:
        return core.generate_test_case(req.requirement_text, req.mode)
    except core.GenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API 호출 실패: {e}") from e


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "default_mode": core.resolve_mode("auto"),
        "model": core.CLAUDE_MODEL,
    }


@app.get("/api/samples")
def samples() -> list:
    return core.list_sample_requirements()


@app.post("/api/generate")
def generate(req: RequirementRequest) -> dict:
    test_case, used_mode = _generate(req)
    return {"mode": used_mode, "test_case": test_case}


@app.post("/api/validate")
def validate(req: TestCaseRequest) -> dict:
    return core.validate_test_case(req.test_case)


@app.post("/api/report")
def report(req: TestCaseRequest) -> dict:
    validation = core.validate_test_case(req.test_case)
    return {
        "overall_pass": validation["overall_pass"],
        "report_markdown": core.build_report_markdown(req.test_case, validation, source="api"),
    }


@app.post("/api/playwright")
def playwright(req: TestCaseRequest) -> dict:
    return {"code": core.build_playwright_spec(req.test_case)}


@app.post("/api/pipeline")
def pipeline(req: RequirementRequest) -> dict:
    test_case, used_mode = _generate(req)
    validation = core.validate_test_case(test_case)
    return {
        "mode": used_mode,
        "test_case": test_case,
        "validation": validation,
        "report_markdown": core.build_report_markdown(test_case, validation, source=f"pipeline ({used_mode})"),
        "playwright_code": core.build_playwright_spec(test_case),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
