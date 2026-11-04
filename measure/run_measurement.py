"""
결함 검출률 측정 실행기 (Day 27)

1. 결함 주입 모드로 서버를 띄운다
2. 결함 없이 두 번 실행해서 기준선을 만든다 (두 번 결과가 다르면 중단: 불안정한 테스트)
3. 결함 28개를 하나씩 켜고 TC v1 / v2 테스트를 실행한다
4. 기준선에서 실패한 테스트(무효 항목)는 빼고, 결함마다 어느 세트가 잡았는지 집계한다

실행: python measure/run_measurement.py
결과: measure/results/results.json, measure/results/report.md
리포트만 다시 만들기: python measure/run_measurement.py --render
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from shop_faults import FAULTS  # noqa: E402

PORT = int(os.getenv("MEASURE_PORT", "8124"))
BASE = f"http://127.0.0.1:{PORT}"
RESULT_DIR = ROOT / "measure" / "results"
PROJECTS = ["measure-v1", "measure-v2"]
SUITES = [
    ("happy", "정상 흐름만", "measure-v2", True),
    ("v1", "TC v1 (Day 24 이전)", "measure-v1", False),
    ("v2", "TC v2 (Day 24 이후)", "measure-v2", False),
]
EXCLUDED_KINDS = {
    "not-automatable": "자동화 불가",
    "out-of-scope": "요구사항 밖",
    "no-criteria": "판정 기준 없음",
}
FEATURES = {"login": "로그인", "signup": "회원가입", "cart": "장바구니"}
ITEM_ID = re.compile(r"^\[([A-Z]+\d+)\]")


def start_server() -> subprocess.Popen:
    env = {**os.environ, "PORT": str(PORT), "HOST": "127.0.0.1", "ANTHROPIC_API_KEY": "", "SHOP_FAULT_INJECTION": "1"}
    proc = subprocess.Popen([sys.executable, "app/server.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/api/health", timeout=1)
            return proc
        except OSError:
            time.sleep(0.5)
    proc.kill()
    raise RuntimeError("서버가 뜨지 않았습니다")


def reset_shop() -> None:
    urllib.request.urlopen(urllib.request.Request(f"{BASE}/shop/__reset", method="POST"), timeout=5)


def run_playwright(fault: str | None) -> list:
    reset_shop()
    out_file = RESULT_DIR / ".last-run.json"
    env = {**os.environ, "E2E_PORT": str(PORT), "PLAYWRIGHT_JSON_OUTPUT_NAME": str(out_file), "CI": ""}
    env.pop("SHOP_FAULT", None)
    if fault:
        env["SHOP_FAULT"] = fault
    cmd = ["npx", "playwright", "test", *[f"--project={p}" for p in PROJECTS],
           "--reporter=json", "--retries=0", "--workers=4"]
    subprocess.run(cmd, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return parse_report(json.loads(out_file.read_text(encoding="utf-8")))


def parse_report(report: dict) -> list:
    rows = []

    def walk(suite, file=None):
        file = suite.get("file") or file
        for spec in suite.get("specs", []):
            for t in spec["tests"]:
                status = t["results"][-1]["status"] if t["results"] else "skipped"
                kinds = [a["type"] for a in t.get("annotations", []) if a["type"] in EXCLUDED_KINDS]
                match = ITEM_ID.match(spec["title"])
                rows.append({
                    "project": t["projectName"],
                    "feature": Path(file).name.split(".")[0],
                    "title": spec["title"],
                    "item": match.group(1) if match else spec["title"],
                    "happy": "@happy" in spec.get("tags", []) or "happy" in spec.get("tags", []),
                    "excluded": kinds[0] if kinds else None,
                    "passed": status in ("passed", "skipped"),
                    "status": status,
                })
        for child in suite.get("suites", []):
            walk(child, file)

    for s in report["suites"]:
        walk(s)
    return rows


def key(row) -> str:
    return f'{row["project"]}|{row["feature"]}|{row["title"]}'


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    server = start_server()
    try:
        print("기준선 1/2 (결함 없음)")
        base1 = run_playwright(None)
        print("기준선 2/2 (결함 없음)")
        base2 = run_playwright(None)
        status1 = {key(r): r["status"] for r in base1}
        status2 = {key(r): r["status"] for r in base2}
        unstable = sorted(k for k in status1 if status1[k] != status2.get(k))
        if unstable:
            print("기준선이 두 번 다르게 나왔습니다 (불안정한 테스트):", *unstable, sep="\n  ")
            sys.exit(1)

        runs = {}
        for i, (fid, feature, desc, basis) in enumerate(FAULTS, 1):
            print(f"[{i}/{len(FAULTS)}] {fid} {desc}")
            runs[fid] = {key(r): r for r in run_playwright(fid)}
    finally:
        server.terminate()

    write_results(base1, runs)


def write_results(baseline: list, runs: dict) -> None:
    invalid = {key(r) for r in baseline if not r["passed"]}
    tests = {key(r): r for r in baseline}

    def suite_tests(project, happy_only):
        return [r for r in baseline if r["project"] == project and (r["happy"] or not happy_only)]

    def valid(r):
        return r["excluded"] is None and key(r) not in invalid

    summary = {}
    detection = {}
    for sid, label, project, happy_only in SUITES:
        members = suite_tests(project, happy_only)
        valid_keys = [key(r) for r in members if valid(r)]
        caught = {}
        for fid, *_ in FAULTS:
            killers = [tests[k]["title"] for k in valid_keys if not runs[fid][k]["passed"]]
            caught[fid] = killers
        detection[sid] = caught

        items = {}
        for r in members:
            item = (r["feature"], r["item"])
            if r["excluded"]:
                items[item] = r["excluded"]
            elif key(r) in invalid:
                items[item] = "invalid"
            else:
                items.setdefault(item, "valid")
        counts = defaultdict(int)
        for kind in items.values():
            counts[kind] += 1
        detected = sum(1 for fid in caught if caught[fid])
        by_feature = {}
        for feat in FEATURES:
            fids = [f[0] for f in FAULTS if f[1] == feat]
            by_feature[feat] = {"detected": sum(1 for f in fids if caught[f]), "total": len(fids)}
        summary[sid] = {
            "label": label,
            "items_total": len(items),
            "items": dict(counts),
            "valid_tests": len(valid_keys),
            "detected": detected,
            "total_faults": len(FAULTS),
            "rate": round(detected / len(FAULTS) * 100, 1),
            "by_feature": by_feature,
        }

    invalid_list = sorted({(tests[k]["project"], tests[k]["feature"], tests[k]["title"]) for k in invalid})
    results = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "faults": [{"id": f[0], "feature": f[1], "description": f[2], "basis": f[3]} for f in FAULTS],
        "summary": summary,
        "detection": detection,
        "invalid_tests": [{"project": p, "feature": f, "title": t} for p, f, t in invalid_list],
    }
    (RESULT_DIR / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULT_DIR / "report.md").write_text(render_report(results), encoding="utf-8")
    print(f"\n결과: {RESULT_DIR / 'report.md'}")
    for sid, s in summary.items():
        print(f'  {s["label"]}: {s["detected"]}/{s["total_faults"]} ({s["rate"]}%)')


def render_report(results: dict) -> str:
    summary = results["summary"]
    detection = results["detection"]
    order = [s[0] for s in SUITES]
    lines = [
        "# 결함 검출률 측정 결과",
        "",
        f'측정 일시: {results["generated_at"]}  ',
        "방법: [docs/measurement/protocol.md](../../docs/measurement/protocol.md)",
        "",
        "## 요약",
        "",
        "| 테스트 세트 | 검출 | 검출률 | 로그인 | 회원가입 | 장바구니 | 유효 테스트 |",
        "|---|---|---|---|---|---|---|",
    ]
    for sid in order:
        s = summary[sid]
        bf = s["by_feature"]
        feat = " | ".join(f'{bf[f]["detected"]}/{bf[f]["total"]}' for f in FEATURES)
        lines.append(f'| {s["label"]} | {s["detected"]}/{s["total_faults"]} | **{s["rate"]}%** | {feat} | {s["valid_tests"]} |')

    lines += ["", "## TC 항목 분류", "",
              "| 테스트 세트 | 전체 항목 | 측정 사용 | 무효 (정상 앱에서 실패) | 자동화 불가 | 요구사항 밖 | 판정 기준 없음 |",
              "|---|---|---|---|---|---|---|"]
    for sid in order:
        s = summary[sid]
        c = s["items"]
        lines.append(f'| {s["label"]} | {s["items_total"]} | {c.get("valid", 0)} | {c.get("invalid", 0)} | '
                     f'{c.get("not-automatable", 0)} | {c.get("out-of-scope", 0)} | {c.get("no-criteria", 0)} |')

    lines += ["", "## 결함별 검출 여부", "",
              "| ID | 결함 | 근거 | 정상 흐름 | v1 | v2 |", "|---|---|---|---|---|---|"]
    for f in results["faults"]:
        marks = " | ".join("O" if detection[sid][f["id"]] else "-" for sid in order)
        lines.append(f'| {f["id"]} | {f["description"]} | {f["basis"]} | {marks} |')

    missed = [f for f in results["faults"] if not detection["v2"][f["id"]]]
    lines += ["", "## v2가 놓친 결함", ""]
    if missed:
        for f in missed:
            caught_by_v1 = " (v1은 검출)" if detection["v1"][f["id"]] else ""
            lines.append(f'- **{f["id"]}** {f["description"]}{caught_by_v1}')
    else:
        lines.append("- 없음")

    lines += ["", "## 무효 항목 (TC가 요구사항에 없는 동작을 기대)", ""]
    for t in results["invalid_tests"]:
        version = "v1" if t["project"].endswith("v1") else "v2"
        lines.append(f'- {version} {FEATURES[t["feature"]]}: {t["title"]}')

    lines += ["", "## 결함별로 잡아낸 테스트 (v2)", ""]
    for f in results["faults"]:
        killers = detection["v2"][f["id"]]
        if killers:
            lines.append(f'- **{f["id"]}**: ' + ", ".join(k.split("]")[0] + "]" for k in killers))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if "--render" in sys.argv:
        saved = json.loads((RESULT_DIR / "results.json").read_text(encoding="utf-8"))
        (RESULT_DIR / "report.md").write_text(render_report(saved), encoding="utf-8")
        print(f"리포트를 다시 만들었습니다: {RESULT_DIR / 'report.md'}")
    else:
        main()
