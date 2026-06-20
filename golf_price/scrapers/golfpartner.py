"""ゴルフパートナー 中古検索スクレイパー。

model_code を使うと機種固有IDでピンポイント取得できる（名寄せ不要・高精度）。
キーワード検索にも対応。商品カードは div.tile_elm_。
"""

import urllib.parse
from bs4 import BeautifulSoup

from .base import Listing, make_session, polite_sleep
from ..normalize import extract_loft

# パス部分（カテゴリ_区分_ブランド）は機種ごとに異なるので、URLから受け取る。
# 未指定時のフォールバック（キャロウェイ ドライバー）。
DEFAULT_PATH = "h010001_m9_b156522"


def _build_url(code: str, path: str, page: int) -> str:
    base = (f"https://www.golfpartner.jp/shop/usedgoods/{path}/"
            f"?search=x&model_code={code}")
    return base if page == 1 else base + f"&p={page}"


def _price_to_int(text: str) -> int | None:
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def _parse(html: str) -> list[Listing]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[Listing] = []
    for card in soup.select("div.tile_elm_"):
        name_el = card.select_one(".name1_ a.goods_name_, a.goods_name_")
        if not name_el:
            continue
        # title属性にモデル名フルが入る。ブランド・シャフトも結合して網羅性を上げる
        brand_el = card.select_one(".name2_ a")
        shaft_el = card.select_one(".name_ .category_name_:last-of-type a")
        parts = []
        if brand_el:
            parts.append(brand_el.get_text(strip=True))
        parts.append(name_el.get("title") or name_el.get_text(strip=True))
        if shaft_el and shaft_el is not name_el:
            parts.append(shaft_el.get_text(strip=True))
        title = " ".join(p for p in parts if p)

        price_el = card.select_one("span.price_")
        if not price_el:
            continue
        price = _price_to_int(price_el.get_text())
        if not price:
            continue

        a = card.select_one("a[href*='/shop/g/']")
        href = a.get("href", "") if a else ""
        url = ("https://www.golfpartner.jp" + href) if href.startswith("/") else href

        state_el = card.select_one(".state_box_")
        year_el = card.select_one(".model_c_")
        cond = state_el.get_text(strip=True) if state_el else ""
        year = year_el.get_text(strip=True) if year_el else ""
        shop = "ゴルフパートナー" + (f"（状態{cond}・{year}年式）" if cond else "")

        out.append(Listing(
            source="golfpartner",
            title=title,
            price=price,
            url=url,
            shop=shop,
            is_used=True,
            sold=False,
            image="",
            loft=extract_loft(title),
        ))
    return out


def search_by_model_code(code: str, path: str | None = None, pages: int = 1,
                         max_pages: int = 30) -> list[Listing]:
    """model_code で取得。path はURLのカテゴリ/ブランド部分（例: h010001_m7_b144905）。

    pages にページ数を指定。全ロフトを網羅したい場合は all=True 相当として
    fetch_all() を使う（こちらは在庫が尽きるまで巡回）。
    """
    path = path or DEFAULT_PATH
    sess = make_session()
    results: list[Listing] = []
    for page in range(1, min(pages, max_pages) + 1):
        url = _build_url(code, path, page)
        polite_sleep(1.2)
        r = sess.get(url, timeout=25)
        if r.status_code != 200:
            break
        items = _parse(r.text)
        if not items:
            break
        results.extend(items)
    return results


def fetch_all(code: str, path: str | None = None, max_pages: int = 30) -> list[Listing]:
    """在庫が尽きるまで全ページ巡回（ロフト網羅用）。"""
    return search_by_model_code(code, path=path, pages=max_pages, max_pages=max_pages)


def search(keyword: str, pages: int = 1) -> list[Listing]:
    """キーワード検索（model_codeが無い場合のフォールバック）。"""
    sess = make_session()
    kw = urllib.parse.quote(keyword)
    url = f"https://www.golfpartner.jp/shop/usedgoods/h010001_m9/?search=x&keyword={kw}"
    polite_sleep()
    r = sess.get(url, timeout=25)
    return _parse(r.text) if r.status_code == 200 else []
