// QA Agent 웹 UI (Day 26)
// 외부 라이브러리 없이 동작. 서버/AI가 준 문자열은 모두 textContent로만 넣는다 (XSS 방지).

const REQUEST_TIMEOUT_MS = 120000;
const MAX_REQUIREMENT_LENGTH = 20000;
const DOWNLOAD_NAMES = {
  report: "validation_report.md",
  playwright: "generated.spec.ts",
  json: "test_case.json",
};
const TC_SECTIONS = [
  ["preconditions", "사전 조건", "ul"],
  ["test_steps", "테스트 절차", "ol"],
  ["expected_results", "기대 결과", "ul"],
  ["negative_cases", "Negative Cases", "ul"],
  ["edge_cases", "Edge Cases", "ul"],
  ["non_functional_checks", "비기능 점검", "ul"],
  ["traceability", "요구사항 추적", "ul"],
  ["notes", "메모", "ul"],
];
const TAG_PATTERN = /^\s*\[([^\]]+)\]\s*/;

const $ = (testId) => document.querySelector(`[data-testid="${testId}"]`);

const state = { result: null, busy: false };

// ---- 공통 유틸 ----

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = options.text;
  if (options.testId) node.dataset.testid = options.testId;
  for (const child of children) node.append(child);
  return node;
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { toast.hidden = true; }, 1800);
}

function showError(message) {
  const box = $("error-message");
  box.textContent = message;
  box.hidden = !message;
}

function errorMessageFrom(status, body) {
  const detail = body && body.detail;
  if (Array.isArray(detail)) {
    // FastAPI 422: [{loc, msg, ...}]
    return "입력값 오류: " + detail.map((d) => `${(d.loc || []).slice(1).join(".") || "body"} - ${d.msg}`).join(", ");
  }
  if (typeof detail === "string") return detail;
  return `요청 실패 (HTTP ${status})`;
}

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
    });
    let body = null;
    try { body = await response.json(); } catch { /* 본문 없음 */ }
    if (!response.ok) throw new Error(errorMessageFrom(response.status, body));
    return body;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도하세요.");
    if (error instanceof TypeError) throw new Error("서버에 연결할 수 없습니다.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

// ---- 탭 (키보드: 좌우 화살표 / Home / End) ----

function setupTabs(tablist, onChange) {
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];

  function select(tab) {
    for (const t of tabs) {
      const selected = t === tab;
      t.setAttribute("aria-selected", String(selected));
      t.tabIndex = selected ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !selected;
    }
    if (onChange) onChange(tab);
  }

  tablist.addEventListener("click", (event) => {
    const tab = event.target.closest('[role="tab"]');
    if (tab) select(tab);
  });
  tablist.addEventListener("keydown", (event) => {
    const index = tabs.indexOf(document.activeElement);
    if (index === -1) return;
    const next = {
      ArrowRight: tabs[(index + 1) % tabs.length],
      ArrowLeft: tabs[(index - 1 + tabs.length) % tabs.length],
      Home: tabs[0],
      End: tabs[tabs.length - 1],
    }[event.key];
    if (next) {
      event.preventDefault();
      next.focus();
      select(next);
    }
  });
  return { select, tabs };
}

// ---- 서버 상태 / 샘플 ----

async function loadHealth() {
  const chip = $("server-status");
  try {
    const health = await api("/api/health");
    chip.dataset.state = health.default_mode;
    chip.textContent = health.default_mode === "live" ? `LIVE · ${health.model}` : "MOCK 모드 (API 키 없음)";
  } catch {
    chip.dataset.state = "down";
    chip.textContent = "서버 연결 실패";
  }
}

async function loadSamples() {
  const list = $("sample-list");
  try {
    const samples = await api("/api/samples");
    for (const sample of samples) {
      const chip = el("button", { className: "chip", text: sample.name, testId: `sample-${sample.name}` });
      chip.type = "button";
      chip.addEventListener("click", () => {
        const input = $("requirement-input");
        input.value = sample.requirement_text;
        input.dispatchEvent(new Event("input"));
        input.focus();
        input.setSelectionRange(0, 0);
        input.scrollTop = 0;
      });
      list.append(chip);
    }
  } catch {
    list.append(el("span", { className: "muted", text: "샘플을 불러오지 못했습니다." }));
  }
}

// ---- 실행 ----

function setBusy(busy) {
  state.busy = busy;
  $("run-button").disabled = busy;
  $("analyze-button").disabled = busy;
  $("loading").hidden = !busy;
  if (busy) {
    $("empty-state").hidden = true;
    $("result").hidden = true;
  }
}

async function run(path, payload) {
  if (state.busy) return;
  showError("");
  setBusy(true);
  try {
    const result = await api(path, { method: "POST", body: JSON.stringify(payload) });
    renderResult(result);
  } catch (error) {
    showError(error.message);
    $("empty-state").hidden = state.result !== null;
    $("result").hidden = state.result === null;
  } finally {
    setBusy(false);
  }
}

function runGenerate() {
  const text = $("requirement-input").value;
  if (!text.trim()) {
    showError("요구사항을 입력하세요.");
    $("requirement-input").focus();
    return;
  }
  run("/api/pipeline", { requirement_text: text, mode: $("mode-select").value });
}

function runAnalyze() {
  const raw = $("tc-json-input").value;
  if (!raw.trim()) {
    showError("테스트 케이스 JSON을 입력하세요.");
    $("tc-json-input").focus();
    return;
  }
  let testCase;
  try {
    testCase = JSON.parse(raw);
  } catch (error) {
    showError(`JSON 형식이 올바르지 않습니다: ${error.message}`);
    return;
  }
  if (testCase === null || typeof testCase !== "object" || Array.isArray(testCase)) {
    showError("테스트 케이스는 JSON 객체({ ... })여야 합니다.");
    return;
  }
  run("/api/analyze", { test_case: testCase });
}

// ---- 결과 렌더링 ----

function listOf(value) {
  return Array.isArray(value) ? value : [];
}

function countTagged(testCase, tag) {
  let count = 0;
  for (const value of Object.values(testCase)) {
    for (const item of listOf(value)) {
      if (typeof item === "string" && item.includes(`[${tag}]`)) count += 1;
    }
  }
  return count;
}

function itemNode(item) {
  const li = el("li");
  const text = typeof item === "string" ? item : JSON.stringify(item);
  const match = text.match(TAG_PATTERN);
  if (match) {
    li.append(el("span", { className: "tag", text: match[1] }), text.slice(match[0].length));
  } else {
    li.textContent = text;
  }
  return li;
}

function renderSummary(result) {
  const { test_case: tc, validation, mode } = result;
  const verdict = $("verdict");
  verdict.textContent = validation.overall_pass ? "PASS" : "FAIL";
  verdict.className = `verdict ${validation.overall_pass ? "pass" : "fail"}`;

  $("feature-name").textContent = tc.feature_name || "(기능명 없음)";
  $("priority").textContent = `Priority ${tc.priority ?? "-"}`;
  $("risk-level").textContent = `Risk ${tc.risk_level ?? "-"}`;
  $("result-mode").textContent = { mock: "mock 결과", live: "Claude 생성", input: "직접 입력" }[mode] || mode;

  const passed = validation.custom_results.filter((r) => r.passed).length;
  $("metric-rules").textContent = `${passed}/${validation.custom_results.length}`;
  $("metric-schema").textContent = String(validation.schema_errors.length);
  $("metric-negative").textContent = String(listOf(tc.negative_cases).length);
  $("metric-edge").textContent = String(listOf(tc.edge_cases).length);
  $("metric-regression").textContent = String(countTagged(tc, "Regression"));
}

function renderValidation(validation) {
  const rows = $("rule-rows");
  rows.replaceChildren();
  for (const rule of validation.custom_results) {
    const status = el("td", {}, [el("span", {
      className: `status ${rule.passed ? "pass" : "fail"}`,
      text: rule.passed ? "PASS" : "FAIL",
    })]);
    const detail = el("td", { className: "detail", text: rule.details.length ? rule.details.map(String).join(" · ") : "-" });
    const row = el("tr", { className: rule.passed ? "" : "fail", testId: "rule-row" }, [
      el("td", { text: String(rule.no) }),
      el("td", { text: rule.name }),
      status,
      detail,
    ]);
    row.dataset.rule = String(rule.no);
    row.dataset.passed = String(rule.passed);
    rows.append(row);
  }

  const schema = $("schema-result");
  schema.replaceChildren();
  if (validation.schema_pass) {
    schema.append(el("span", { className: "schema-ok", text: "PASS" }));
  } else {
    schema.append(el("ul", { className: "schema-errors" }, validation.schema_errors.map((e) => el("li", { text: e }))));
  }
}

function renderTestCase(tc) {
  $("requirement-summary").textContent = tc.requirement_summary || "";
  const container = $("tc-sections");
  container.replaceChildren();
  for (const [key, title, listTag] of TC_SECTIONS) {
    const items = listOf(tc[key]);
    if (!items.length) continue;
    container.append(el("section", { className: "tc-section", testId: `tc-${key}` }, [
      el("h4", { text: `${title} (${items.length})` }),
      el(listTag, {}, items.map(itemNode)),
    ]));
  }
  if (tc.test_data !== undefined) {
    container.append(el("section", { className: "tc-section", testId: "tc-test_data" }, [
      el("h4", { text: "테스트 데이터" }),
      el("pre", { className: "code", text: JSON.stringify(tc.test_data, null, 2) }),
    ]));
  }
}

function outputText(kind) {
  const result = state.result;
  if (!result) return "";
  if (kind === "report") return result.report_markdown;
  if (kind === "playwright") return result.playwright_code;
  return JSON.stringify(result.test_case, null, 2);
}

function renderResult(result) {
  state.result = result;
  renderSummary(result);
  renderValidation(result.validation);
  renderTestCase(result.test_case);
  $("report-output").textContent = outputText("report");
  $("playwright-output").textContent = outputText("playwright");
  $("json-output").textContent = outputText("json");

  $("empty-state").hidden = true;
  $("result").hidden = false;
  resultTabs.select(resultTabs.tabs[0]);
}

// ---- 복사 / 다운로드 ----

async function copyOutput(kind) {
  const text = outputText(kind);
  try {
    await navigator.clipboard.writeText(text);
    showToast("클립보드에 복사했습니다.");
  } catch {
    showToast("복사하지 못했습니다. 직접 선택해서 복사하세요.");
  }
}

function downloadOutput(kind) {
  const blob = new Blob([outputText(kind)], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = el("a");
  link.href = url;
  link.download = DOWNLOAD_NAMES[kind];
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// ---- 초기화 ----

setupTabs(document.querySelector('[aria-label="입력 방식"]'), () => showError(""));
const resultTabs = setupTabs(document.querySelector('[aria-label="결과 보기"]'));

$("requirement-input").addEventListener("input", (event) => {
  $("char-count").textContent = event.target.value.length.toLocaleString("ko-KR");
});
$("run-button").addEventListener("click", runGenerate);
$("analyze-button").addEventListener("click", runAnalyze);
for (const [inputId, action] of [["requirement-input", runGenerate], ["tc-json-input", runAnalyze]]) {
  $(inputId).addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      action();
    }
  });
}
document.addEventListener("click", (event) => {
  const copyButton = event.target.closest("[data-copy]");
  if (copyButton) copyOutput(copyButton.dataset.copy);
  const downloadButton = event.target.closest("[data-download]");
  if (downloadButton) downloadOutput(downloadButton.dataset.download);
});

$("requirement-input").maxLength = MAX_REQUIREMENT_LENGTH;
loadHealth();
loadSamples();
