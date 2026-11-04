"""
측정 결과 페이지 빌드 (Day 27)

measure/results/results.json을 페이지에 넣어 두 가지로 만든다.
- site/dist/index.html : GitHub Pages용 완전한 HTML 문서
- site/dist/fragment.html : 문서 껍데기 없이 본문만 (미리보기 공유용)

실행: python site/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "site" / "template.html"
RESULTS = ROOT / "measure" / "results" / "results.json"
DIST = ROOT / "site" / "dist"
PLACEHOLDER = "/*__DATA__*/null"


def main() -> None:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise ValueError(f"템플릿에 {PLACEHOLDER} 자리표시자가 없습니다")
    # </script>가 데이터 안에 있어도 스크립트가 끊기지 않게 이스케이프
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    fragment = template.replace(PLACEHOLDER, payload)

    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "fragment.html").write_text(fragment, encoding="utf-8")
    # <style>까지는 head, 나머지는 body
    head, body = fragment.split("</style>\n", 1)
    document = (
        '<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"{head}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )
    (DIST / "index.html").write_text(document, encoding="utf-8")
    print(f"빌드 완료: {DIST / 'index.html'}")


if __name__ == "__main__":
    main()
