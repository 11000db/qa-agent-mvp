import json

import pytest

import core

SAMPLE_DIR = core.SAMPLE_OUTPUT_DIR


def load_sample(name: str) -> dict:
    return core.read_json_file(SAMPLE_DIR / name)


def failed_rules(data: dict) -> list:
    return [r["no"] for r in core.run_custom_validation(data) if not r["passed"]]


class TestValidation:

    @pytest.mark.parametrize("name", ["login_test_case.json", "signup_test_case.json", "cart_test_case.json"])
    def test_valid_samples_pass(self, name):
        """정상 샘플은 11개 규칙 + Schema 검증 모두 PASS"""
        result = core.validate_test_case(load_sample(name))
        assert result["overall_pass"] is True
        assert len(result["custom_results"]) == 11

    @pytest.mark.parametrize("name, expected_rule", [
        ("invalid_duplicate_test_case.json", 6),
        ("invalid_min_items_test_case.json", 7),
        ("invalid_duplicate_traceability_test_case.json", 8),
        ("invalid_internal_duplicate_test_case.json", 9),
        ("invalid_duplicate_negative_edge_cases.json", 10),
        ("invalid_duplicate_negative_edge_cases.json", 11),
    ])
    def test_invalid_samples_fail_on_expected_rule(self, name, expected_rule):
        """각 invalid 샘플은 의도한 규칙에서 FAIL"""
        result = core.validate_test_case(load_sample(name))
        assert result["overall_pass"] is False
        assert expected_rule in failed_rules(load_sample(name))

    def test_invalid_enum_fails_schema_too(self):
        """허용되지 않은 priority는 커스텀 규칙 4번과 Schema 둘 다 FAIL"""
        data = load_sample("login_test_case.json")
        data["priority"] = "TOP"
        result = core.validate_test_case(data)
        assert 4 in failed_rules(data)
        assert any("priority" in e for e in result["schema_errors"])

    def test_empty_object_fails(self):
        result = core.validate_test_case({})
        assert result["overall_pass"] is False
        assert 1 in failed_rules({})


class TestGeneration:

    @pytest.mark.parametrize("text, expected_feature_file", [
        ("장바구니에 상품을 담는다", "cart_test_case.json"),
        ("회원가입 기능", "signup_test_case.json"),
        ("이메일 로그인", "login_test_case.json"),
        ("알 수 없는 기능", "login_test_case.json"),
    ])
    def test_mock_picks_sample_by_keyword(self, text, expected_feature_file):
        test_case, mode = core.generate_test_case(text, "mock")
        assert mode == "mock"
        assert test_case == load_sample(expected_feature_file)

    def test_mock_returns_copy(self):
        """mock 결과를 수정해도 다음 호출에 영향이 없어야 한다"""
        first, _ = core.generate_test_case("로그인", "mock")
        first["feature_name"] = "changed"
        second, _ = core.generate_test_case("로그인", "mock")
        assert second["feature_name"] != "changed"

    def test_auto_without_api_key_uses_mock(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert core.resolve_mode("auto") == "mock"

    def test_auto_with_api_key_uses_live(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
        assert core.resolve_mode("auto") == "live"

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            core.resolve_mode("fast")

    def test_live_parses_code_block_response(self, monkeypatch):
        """Claude 응답이 ```json 코드블록이어도 파싱된다 (API 호출은 대체)"""
        sample = load_sample("login_test_case.json")
        fake = "결과입니다\n```json\n" + json.dumps(sample, ensure_ascii=False) + "\n```"
        monkeypatch.setattr(core, "call_claude_api", lambda prompt: fake)
        test_case, mode = core.generate_test_case("로그인", "live")
        assert mode == "live"
        assert test_case == sample

    def test_live_invalid_json_raises_generation_error(self, monkeypatch):
        monkeypatch.setattr(core, "call_claude_api", lambda prompt: "JSON이 아닌 응답")
        with pytest.raises(core.GenerationError):
            core.generate_test_case("로그인", "live")

    def test_prompt_contains_requirement(self):
        template = core.TEMPLATE_PATH.read_text(encoding="utf-8")
        prompt = core.build_final_prompt(template, "REQ_MARKER_123")
        assert "REQ_MARKER_123" in prompt
        assert core.PLACEHOLDER not in prompt


class TestOutputs:

    def test_report_lists_all_rules(self):
        data = load_sample("login_test_case.json")
        report = core.build_report_markdown(data, core.validate_test_case(data))
        assert "✅ PASS" in report
        assert report.count("| ✅ PASS |") == 11

    def test_report_shows_fail(self):
        data = load_sample("invalid_min_items_test_case.json")
        report = core.build_report_markdown(data, core.validate_test_case(data))
        assert "**❌ FAIL**" in report

    def test_playwright_spec_structure(self):
        code = core.build_playwright_spec(load_sample("login_test_case.json"))
        assert "import { test, expect } from '@playwright/test';" in code
        assert "test.describe(" in code
        assert "Negative Cases" in code


class TestPlaywrightEscaping:
    """사용자/AI 입력이 생성 코드의 문법을 깨지 않아야 한다"""

    def test_quote_in_feature_name_is_escaped(self):
        code = core.build_playwright_spec({"feature_name": "it's \"quoted\""})
        assert 'test.describe("it\'s \\"quoted\\"", () => {' in code

    def test_newline_cannot_escape_comment(self):
        code = core.build_playwright_spec({"test_steps": ["첫 줄\nawait page.evaluate('evil')"]})
        assert "\nawait page.evaluate('evil')" not in code
        assert "    // 첫 줄 await page.evaluate('evil')" in code

    def test_block_comment_terminator_is_neutralized(self):
        code = core.build_playwright_spec({"feature_name": "x */ alert(1) /*"})
        header = code.split(" */\n", 1)[0]
        assert "alert(1)" in header

    def test_non_list_fields_are_ignored(self):
        code = core.build_playwright_spec({"test_steps": "문자열", "negative_cases": None})
        assert "Negative Cases" not in code
