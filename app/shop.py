"""
데모 쇼핑몰 (Day 27) - AI가 만든 테스트의 결함 검출률을 재기 위한 측정 대상

요구사항 문서(sample_inputs/*_requirement.md) 3개만 보고 구현했다.
요구사항에 없는 부분은 아래 "앱 정책"으로 정하고, 테스트가 이와 다른 동작을 기대하면
그 TC 항목은 측정에서 제외한다 (docs/measurement/protocol.md 참고).

앱 정책
- 비로그인 상태에서도 장바구니를 쓸 수 있다 (세션 기준)
- 로그인 실패 횟수 제한(계정 잠금)은 없다
- 로그인한 상태로 로그인 페이지에 와도 자동 이동하지 않는다
- 상품 상세 페이지에서는 한 번에 1개씩 담는다
- 수량 입력란은 문자 입력이 가능한 일반 텍스트 칸이다 (서버에서 검증)
- 비밀번호는 입력한 그대로 비교한다 (앞뒤 공백 포함), 이메일은 앞뒤 공백을 제거하고 대소문자를 구분하지 않는다
"""
import html
import itertools
import re
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from shop_faults import active_faults, injection_enabled

router = APIRouter(prefix="/shop")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INT_RE = re.compile(r"^-?\d+$")
MIN_PASSWORD_LENGTH = 8
SESSION_COOKIE = "shop_sid"

PRODUCTS = {
    "PRD-001": {"name": "테스트 상품 A", "price": 10000, "stock": 100},
    "PRD-002": {"name": "테스트 상품 B", "price": 25000, "stock": 5},
    "PRD-003": {"name": "품절 상품 C", "price": 15000, "stock": 0},
}

SEED_USERS = [
    {"name": "테스트", "email": "test@example.com", "password": "Test1234!"},
    {"name": "테스트유저", "email": "testuser@example.com", "password": "Test1234!@"},
    {"name": "중복", "email": "duplicate@example.com", "password": "Test1234!"},
]

users: list = []
sessions: dict = {}
_line_ids = itertools.count(1)


def reset_state() -> None:
    users.clear()
    users.extend(dict(u) for u in SEED_USERS)
    sessions.clear()


reset_state()


# ---- 세션 / 공통 ----

def _session(request: Request) -> tuple:
    sid = request.cookies.get(SESSION_COOKIE)
    if sid not in sessions:
        sid = secrets.token_hex(16)
        sessions[sid] = {"user": None, "lines": [], "flash": [], "removed": {}}
    return sid, sessions[sid]


def _with_cookie(response, sid: str):
    response.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="lax", path="/shop")
    return response


def _redirect(url: str, sid: str):
    return _with_cookie(RedirectResponse(url, status_code=303), sid)


def _find_user(email: str):
    key = email.lower()
    return next((u for u in users if u["email"].lower() == key), None)


def _cart_count(sess: dict) -> int:
    return sum(line["qty"] for line in sess["lines"])


def _e(value) -> str:
    return html.escape(str(value))


def _won(amount: int) -> str:
    return f"{amount:,}원"


def _page(sess: dict, sid: str, title: str, body: str) -> HTMLResponse:
    user = sess["user"]
    if user:
        account = (
            f'<span class="who">{_e(user["name"])}님</span>'
            '<form method="post" action="/shop/logout" class="inline"><button type="submit">로그아웃</button></form>'
        )
    else:
        account = '<a href="/shop/login">로그인</a><a href="/shop/signup">회원가입</a>'
    flashes = "".join(
        f'<p class="flash {kind}" role="{"alert" if kind == "error" else "status"}">{_e(text)}</p>'
        for kind, text in sess["flash"]
    )
    sess["flash"] = []
    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)} - QA Shop</title>
<style>
body{{font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;max-width:760px;margin:0 auto;padding:16px;color:#222}}
header{{display:flex;gap:12px;align-items:center;border-bottom:1px solid #ccc;padding-bottom:8px;margin-bottom:16px;flex-wrap:wrap}}
header .home{{font-weight:700;margin-right:auto;color:#222;text-decoration:none}}
.inline{{display:inline}} .flash{{padding:8px;border:1px solid #999}} .flash.error,.field-error{{color:#b00}}
label{{display:block;margin-top:10px}} input{{padding:6px;width:260px;max-width:100%}}
table{{border-collapse:collapse;width:100%}} td,th{{border-bottom:1px solid #ddd;padding:6px;text-align:left}}
.qty{{width:60px}}
</style></head><body>
<header><a class="home" href="/shop">QA Shop</a><a href="/shop/cart">장바구니 ({_cart_count(sess)})</a>{account}</header>
{flashes}
<main><h1>{_e(title)}</h1>{body}</main>
</body></html>"""
    return _with_cookie(HTMLResponse(page), sid)


def _field(label: str, name: str, value: str = "", input_type: str = "text", error: str = "") -> str:
    error_html = f'<span class="field-error" id="{name}-error">{_e(error)}</span>' if error else ""
    described = f' aria-describedby="{name}-error" aria-invalid="true"' if error else ""
    return (
        f'<label for="{name}">{label}</label>'
        f'<input id="{name}" name="{name}" type="{input_type}" value="{_e(value)}"{described}>{error_html}'
    )


# ---- 테스트용 초기화 (결함 주입 모드에서만) ----

@router.post("/__reset", include_in_schema=False)
def reset():
    if not injection_enabled():
        return HTMLResponse("not found", status_code=404)
    reset_state()
    return {"status": "reset"}


# ---- 메인 / 상품 ----

@router.get("", response_class=HTMLResponse)
def home(request: Request):
    sid, sess = _session(request)
    items = "".join(
        f'<li><a href="/shop/products/{pid}">{_e(p["name"])}</a> - {_won(p["price"])}'
        f'{" (품절)" if p["stock"] == 0 else ""}</li>'
        for pid, p in PRODUCTS.items()
    )
    return _page(sess, sid, "상품 목록", f"<ul>{items}</ul>")


@router.get("/products/{pid}", response_class=HTMLResponse)
def product_detail(pid: str, request: Request):
    sid, sess = _session(request)
    product = PRODUCTS.get(pid)
    if not product:
        return _page(sess, sid, "상품 없음", "<p>존재하지 않는 상품입니다.</p>")
    stock = "품절" if product["stock"] == 0 else f'재고 {product["stock"]}개'
    body = (
        f'<p>상품번호 {pid}</p><p>가격 {_won(product["price"])}</p><p>{stock}</p>'
        f'<form method="post" action="/shop/cart/add"><input type="hidden" name="product_id" value="{pid}">'
        '<button type="submit">장바구니 담기</button></form>'
    )
    return _page(sess, sid, product["name"], body)


# ---- 로그인 ----

def _login_page(sess, sid, email="", errors=None, password_type="password"):
    errors = errors or {}
    body = (
        '<form method="post" action="/shop/login" novalidate>'
        + _field("이메일", "email", email, error=errors.get("email", ""))
        + _field("비밀번호", "password", "", password_type, errors.get("password", ""))
        + '<p><button type="submit">로그인</button></p></form>'
        '<p><a href="/shop/signup">회원가입</a></p>'
    )
    return _page(sess, sid, "로그인", body)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    return _login_page(sess, sid, password_type="text" if "L6" in faults else "password")


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(""), password: str = Form("")):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    password_type = "text" if "L6" in faults else "password"
    email = email.strip()

    errors = {}
    if not email:
        if "L5" not in faults:
            errors["email"] = "이메일을 입력해주세요"
    elif not EMAIL_RE.match(email) and "L3" not in faults:
        errors["email"] = "올바른 이메일 형식이 아닙니다"
    if password == "" and "L4" not in faults:
        errors["password"] = "비밀번호를 입력해주세요"
    if errors:
        return _login_page(sess, sid, email, errors, password_type)

    user = _find_user(email)
    if user is None and "L2" in faults:
        raise RuntimeError("L2: user lookup failed")
    if user is None or (password != user["password"] and "L1" not in faults):
        sess["flash"].append(("error", "이메일 또는 비밀번호가 올바르지 않습니다"))
        return _login_page(sess, sid, email, password_type=password_type)

    sess["user"] = {"name": user["name"], "email": user["email"]}
    if "L7" in faults:
        return _login_page(sess, sid, password_type=password_type)
    sess["flash"].append(("info", "로그인되었습니다"))
    return _redirect("/shop", sid)


@router.post("/logout")
def logout(request: Request):
    sid, sess = _session(request)
    sessions.pop(sid, None)
    return RedirectResponse("/shop", status_code=303)


# ---- 회원가입 ----

def _signup_page(sess, sid, values=None, errors=None):
    values = values or {}
    errors = errors or {}
    form_error = f'<p class="flash error" role="alert">{_e(errors["form"])}</p>' if "form" in errors else ""
    body = (
        form_error
        + '<form method="post" action="/shop/signup" novalidate>'
        + _field("이름", "name", values.get("name", ""), error=errors.get("name", ""))
        + _field("이메일", "email", values.get("email", ""), error=errors.get("email", ""))
        + _field("비밀번호", "password", "", "password", errors.get("password", ""))
        + f"<p>비밀번호는 {MIN_PASSWORD_LENGTH}자 이상 입력해주세요.</p>"
        + '<p><button type="submit">회원가입</button></p></form>'
    )
    return _page(sess, sid, "회원가입", body)


@router.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    sid, sess = _session(request)
    return _signup_page(sess, sid)


@router.post("/signup", response_class=HTMLResponse)
def signup(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form("")):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    name_value = name if "S10" in faults else name.strip()
    email = email.strip()

    errors = {}
    required_missing = False
    if not name_value:
        errors["name"] = "이름을 입력해주세요"
        required_missing = True
    if not email:
        errors["email"] = "이메일을 입력해주세요"
        required_missing = True
    elif not EMAIL_RE.match(email) and "S6" not in faults:
        errors["email"] = "올바른 이메일 형식이 아닙니다"
    if not password:
        errors["password"] = "비밀번호를 입력해주세요"
        required_missing = True
    else:
        min_length = MIN_PASSWORD_LENGTH - 1 if "S1" in faults else MIN_PASSWORD_LENGTH + 1 if "S2" in faults else MIN_PASSWORD_LENGTH
        if len(password) < min_length:
            errors["password"] = f"비밀번호는 {MIN_PASSWORD_LENGTH}자 이상이어야 합니다"
    if required_missing and "S5" in faults:
        errors = {"form": "입력값을 확인해주세요"}

    if not errors:
        if "S4" in faults:
            exists = any(u["email"] == email for u in users)
        else:
            exists = _find_user(email) is not None
        if exists and "S3" not in faults:
            if "S8" in faults:
                raise RuntimeError("S8: duplicate email")
            errors["email"] = "이미 사용 중인 이메일입니다"

    if errors:
        return _signup_page(sess, sid, {"name": name, "email": email}, errors)

    stored_password = password + "#" if "S7" in faults else password
    users.append({"name": name_value, "email": email, "password": stored_password})
    if "S9" in faults:
        return _redirect("/shop", sid)
    body = (
        f'<p role="status">회원가입이 완료되었습니다. {_e(name_value)}님 환영합니다.</p>'
        '<p><a href="/shop/login">로그인하러 가기</a></p>'
    )
    return _page(sess, sid, "회원가입 완료", body)


# ---- 장바구니 ----

def _find_line(sess, line_id: int):
    return next((line for line in sess["lines"] if line["id"] == line_id), None)


@router.post("/cart/add")
def cart_add(request: Request, product_id: str = Form(...)):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    product = PRODUCTS.get(product_id)
    back = f"/shop/products/{quote(product_id)}"
    if not product:
        sess["flash"].append(("error", "존재하지 않는 상품입니다"))
        return _redirect("/shop", sid)

    if product["stock"] == 0 and "C4" not in faults:
        sess["flash"].append(("error", "품절된 상품입니다"))
        return _redirect(back, sid)

    line = None if "C1" in faults else next((l for l in sess["lines"] if l["product_id"] == product_id), None)
    if line:
        if line["qty"] + 1 > product["stock"] and "C7" not in faults:
            sess["flash"].append(("error", f'재고가 부족합니다 (최대 {product["stock"]}개)'))
            return _redirect(back, sid)
        line["prev_qty"] = line["qty"]
        line["qty"] += 1
    else:
        qty = sess["removed"].get(product_id, 1) if "C11" in faults else 1
        sess["lines"].append({"id": next(_line_ids), "product_id": product_id, "qty": qty, "prev_qty": qty})
    sess["flash"].append(("info", "장바구니에 추가되었습니다"))
    return _redirect(back, sid)


@router.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    if not sess["lines"]:
        empty = "" if "C9" in faults else '<p>장바구니가 비어 있습니다</p>'
        return _page(sess, sid, "장바구니", empty + '<p><a href="/shop">쇼핑 계속하기</a></p>')

    rows = []
    total = 0
    for line in sess["lines"]:
        product = PRODUCTS[line["product_id"]]
        subtotal = product["price"] * line["qty"]
        total += product["price"] * (line["prev_qty"] if "C6" in faults else line["qty"])
        rows.append(
            f'<tr data-product="{line["product_id"]}">'
            f'<td><a href="/shop/products/{line["product_id"]}">{_e(product["name"])}</a></td>'
            f'<td>{_won(product["price"])}</td>'
            f'<td><form method="post" action="/shop/cart/update" class="inline">'
            f'<input type="hidden" name="line_id" value="{line["id"]}">'
            f'<label class="inline">수량 <input class="qty" name="quantity" type="text" inputmode="numeric" value="{line["qty"]}"></label> '
            f'<button type="submit">변경</button></form></td>'
            f'<td class="subtotal">{_won(subtotal)}</td>'
            f'<td><form method="post" action="/shop/cart/remove" class="inline">'
            f'<input type="hidden" name="line_id" value="{line["id"]}"><button type="submit">삭제</button></form></td>'
            "</tr>"
        )
    body = (
        "<table><thead><tr><th>상품</th><th>가격</th><th>수량</th><th>소계</th><th></th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody></table>'
        f'<p class="total">총 금액: <strong>{_won(total)}</strong></p>'
    )
    return _page(sess, sid, "장바구니", body)


@router.post("/cart/update")
def cart_update(request: Request, line_id: int = Form(...), quantity: str = Form("")):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    line = _find_line(sess, line_id)
    if not line:
        return _redirect("/shop/cart", sid)
    product = PRODUCTS[line["product_id"]]
    raw = quantity.strip()

    if not INT_RE.match(raw):
        if "C8" in faults:
            raise ValueError("C8: invalid quantity")
        sess["flash"].append(("error", "올바른 수량을 입력해주세요"))
        return _redirect("/shop/cart", sid)
    qty = int(raw)
    if qty < 0 and "C2" not in faults:
        sess["flash"].append(("error", "올바른 수량을 입력해주세요"))
        return _redirect("/shop/cart", sid)
    if qty == 0 and "C3" not in faults:
        sess["lines"].remove(line)
        sess["removed"][line["product_id"]] = line["qty"]
        sess["flash"].append(("info", "상품을 장바구니에서 삭제했습니다"))
        return _redirect("/shop/cart", sid)
    if qty > product["stock"] and "C7" not in faults:
        sess["flash"].append(("error", f'재고가 부족합니다 (최대 {product["stock"]}개)'))
        return _redirect("/shop/cart", sid)

    if "C5" not in faults:
        line["prev_qty"] = line["qty"]
        line["qty"] = qty
    sess["flash"].append(("info", "수량을 변경했습니다"))
    return _redirect("/shop/cart", sid)


@router.post("/cart/remove")
def cart_remove(request: Request, line_id: int = Form(...)):
    sid, sess = _session(request)
    faults = active_faults(request.headers)
    line = _find_line(sess, line_id)
    if line and "C10" not in faults:
        sess["lines"].remove(line)
        sess["removed"][line["product_id"]] = line["qty"]
    sess["flash"].append(("info", "상품을 장바구니에서 삭제했습니다"))
    return _redirect("/shop/cart", sid)
