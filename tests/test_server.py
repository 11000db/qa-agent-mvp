import pytest
from fastapi.testclient import TestClient

import core
from server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    """서버 테스트는 실제 Claude API를 호출하지 않는다"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def sample(name: str) -> dict:
    return core.read_json_file(core.SAMPLE_OUTPUT_DIR / name)


class TestHealthAndSamples:

    def test_health(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["default_mode"] == "mock"

    def test_samples(self):
        response = client.get("/api/samples")
        assert response.status_code == 200
        names = {s["name"] for s in response.json()}
        assert {"login", "signup", "cart"} <= names


class TestGenerate:

    def test_generate_mock(self):
        response = client.post("/api/generate", json={"requirement_text": "장바구니 기능", "mode": "mock"})
        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == "mock"
        assert body["test_case"] == sample("cart_test_case.json")

    def test_generate_auto_falls_back_to_mock(self):
        response = client.post("/api/generate", json={"requirement_text": "로그인"})
        assert response.status_code == 200
        assert response.json()["mode"] == "mock"

    @pytest.mark.parametrize("payload", [
        {},
        {"requirement_text": ""},
        {"requirement_text": "   "},
        {"requirement_text": "로그인", "mode": "fast"},
        {"requirement_text": "a" * 20001},
    ])
    def test_generate_rejects_invalid_input(self, payload):
        response = client.post("/api/generate", json=payload)
        assert response.status_code == 422

    def test_live_without_api_key_is_400(self):
        response = client.post("/api/generate", json={"requirement_text": "로그인", "mode": "live"})
        assert response.status_code == 400

    def test_live_bad_response_is_502(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
        monkeypatch.setattr(core, "call_claude_api", lambda prompt: "not json")
        response = client.post("/api/generate", json={"requirement_text": "로그인", "mode": "live"})
        assert response.status_code == 502


class TestValidateReportPlaywright:

    def test_validate_pass(self):
        response = client.post("/api/validate", json={"test_case": sample("login_test_case.json")})
        assert response.status_code == 200
        assert response.json()["overall_pass"] is True

    def test_validate_fail(self):
        response = client.post("/api/validate", json={"test_case": sample("invalid_duplicate_test_case.json")})
        assert response.status_code == 200
        body = response.json()
        assert body["overall_pass"] is False
        assert any(r["no"] == 6 and not r["passed"] for r in body["custom_results"])

    def test_validate_requires_object(self):
        response = client.post("/api/validate", json={"test_case": ["not", "object"]})
        assert response.status_code == 422

    def test_report(self):
        response = client.post("/api/report", json={"test_case": sample("login_test_case.json")})
        assert response.status_code == 200
        assert response.json()["report_markdown"].startswith("# QA Validation Report")

    def test_playwright(self):
        response = client.post("/api/playwright", json={"test_case": sample("login_test_case.json")})
        assert response.status_code == 200
        assert "@playwright/test" in response.json()["code"]


class TestPipeline:

    def test_pipeline_mock_end_to_end(self):
        response = client.post("/api/pipeline", json={"requirement_text": "회원가입", "mode": "mock"})
        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == "mock"
        assert body["validation"]["overall_pass"] is True
        assert "# QA Validation Report" in body["report_markdown"]
        assert "@playwright/test" in body["playwright_code"]


class TestWebUI:

    def test_index_serves_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert 'data-testid="run-button"' in response.text

    @pytest.mark.parametrize("path", ["/static/app.js", "/static/style.css"])
    def test_static_assets(self, path):
        assert client.get(path).status_code == 200

    def test_static_path_traversal_blocked(self):
        response = client.get("/static/../core.py")
        assert response.status_code == 404


class TestAnalyze:

    def test_analyze_returns_full_result(self):
        response = client.post("/api/analyze", json={"test_case": sample("invalid_duplicate_traceability_test_case.json")})
        assert response.status_code == 200
        body = response.json()
        assert body["mode"] == "input"
        assert body["validation"]["overall_pass"] is False
        assert "**❌ FAIL**" in body["report_markdown"]
        assert "@playwright/test" in body["playwright_code"]

    def test_analyze_tolerates_wrong_field_types(self):
        """필드 타입이 엉망이어도 500이 아니라 FAIL 결과를 돌려준다"""
        weird = {"feature_name": 123, "test_steps": "문자열", "traceability": {"a": 1}, "edge_cases": None}
        response = client.post("/api/analyze", json={"test_case": weird})
        assert response.status_code == 200
        assert response.json()["validation"]["overall_pass"] is False
