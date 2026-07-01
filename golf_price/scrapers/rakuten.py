"""楽天市場 商品検索（楽天ウェブサービス公式API / 2026新版）。

楽天は検索ページのスクレイプを datacenter IP からブロックする（Akamai）ため、
クラウド（GitHub Actions）では公式APIを使う。APIは application_id + access_key が必須で、
アプリ登録時の「許可ウェブサイト」に合わせて Referer/Origin ヘッダも必要。

認証情報の優先順位:
  1. 環境変数 RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY（クラウドはこれ）
  2. リポジトリ直下の rakuten_keys.json（gitignore。ローカル用）
認証情報が無い場合は従来のHTMLスクレイプにフォールバック（住宅IPなら動く）。

出力(Listing)の形は従来と同一なので、service など他のコードは無改造。
"""

import json
import os
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup

from .base import Listing, make_session, polite_sleep
from ..normalize import is_blocked_shop

# --- 公式API（2026新版）-------------------------------------------------------
API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
# アプリ登録の「許可ウェブサイト」に合わせる（GitHub Pages のドメイン）
ALLOWED_ORIGIN = "https://nekokaitaidesu-cpu.github.io"
_KEYS_FILE = Path(__file__).resolve().parents[2] / "rakuten_keys.json"


def _credentials() -> tuple[str, str] | None:
    app_id = os.environ.get("RAKUTEN_APP_ID", "").strip()
    key = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
    if app_id and key:
        return app_id, key
    if _KEYS_FILE.exists():
        try:
            d = json.loads(_KEYS_FILE.read_text(encoding="utf-8"))
            if d.get("app_id") and d.get("access_key"):
                return d["app_id"], d["access_key"]
        except (OSError, json.JSONDecodeError):
            pass
    return None


def _search_api(keyword: str, app_id: str, key: str, pages: int = 2) -> list[Listing]:
    """公式APIで検索。

    APIの relevance(標準)順は、安い中古出品を深い順位に埋めてしまい「中古最安」を
    取り逃す。一方 価格昇順 だけだと平均・中央値が下振れする。そこで
    「relevance を pages ページ ＋ 価格昇順を1ページ」取ってマージし、
    最安は正確・平均/中央値は従来の広がりを維持する（旧スクレイプの数字に寄せる）。
    レート制限は1req/秒なので polite_sleep で間隔を空ける。
    """
    sess = make_session()
    sess.headers.update({
        "accessKey": key,
        "Referer": ALLOWED_ORIGIN + "/",
        "Origin": ALLOWED_ORIGIN,
    })
    out: list[Listing] = []
    seen: set[str] = set()

    def fetch(sort: str | None, npages: int):
        for page in range(1, npages + 1):
            params = {"applicationId": app_id, "keyword": keyword,
                      "hits": 30, "page": page, "format": "json"}
            if sort:
                params["sort"] = sort
            polite_sleep(1.1, "rakuten")
            r = sess.get(API_URL, params=params, timeout=25)
            if r.status_code != 200:
                break
            items = r.json().get("Items", [])
            if not items:
                break
            for wrap in items:
                it = wrap.get("Item", wrap)
                title = it.get("itemName") or ""
                price = it.get("itemPrice")
                url = it.get("itemUrl", "") or ""
                if not title or not price or url in seen:
                    continue
                shop = it.get("shopName", "") or ""
                if is_blocked_shop(shop, url):
                    continue
                seen.add(url)
                imgs = it.get("mediumImageUrls") or []
                image = ""
                if imgs:
                    first = imgs[0]
                    image = first.get("imageUrl", "") if isinstance(first, dict) else first
                out.append(Listing(
                    source="rakuten", title=title, price=int(price), url=url,
                    shop=shop, is_used=("中古" in title), sold=False, image=image,
                ))
            if len(items) < 30:
                break

    fetch(sort=None, npages=max(pages, 2))  # relevance（従来の広がり・平均/中央値の安定用に2ページ以上）
    fetch(sort="+itemPrice", npages=1)      # 価格昇順（真の最安を確実に拾う）
    return out


# --- 従来スクレイプ（ローカル/住宅IP フォールバック）--------------------------
BASE = "https://search.rakuten.co.jp/search/mall/{kw}/"
PAGED = "https://search.rakuten.co.jp/search/mall/{kw}/?p={page}"


def _parse(html: str) -> list[Listing]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[Listing] = []
    for it in soup.select("div.searchresultitem"):
        price_raw = it.get("data-track-price") or it.get("data-track-price-ranges")
        if not price_raw:
            continue
        price_str = str(price_raw).split("~")[0].replace(",", "").strip()
        if not price_str.isdigit():
            continue
        price = int(price_str)
        a = it.select_one('a[data-rpp-url-copy="title"], a[data-link="item"]')
        if not a:
            continue
        title = a.get("title") or a.get_text(strip=True)
        url = a.get("href", "")
        shop_a = it.select_one(".merchant a, .content.merchant a")
        shop = shop_a.get_text(strip=True) if shop_a else ""
        if is_blocked_shop(shop, url):
            continue
        img = it.select_one("img")
        image = (img.get("src") if img else "") or ""
        out.append(Listing(
            source="rakuten", title=title, price=price, url=url, shop=shop,
            is_used=("中古" in title), sold=False, image=image,
        ))
    return out


def _search_scrape(keyword: str, pages: int = 2) -> list[Listing]:
    sess = make_session()
    kw = urllib.parse.quote(keyword)
    results: list[Listing] = []
    for page in range(1, pages + 1):
        url = BASE.format(kw=kw) if page == 1 else PAGED.format(kw=kw, page=page)
        polite_sleep(1.0, "rakuten")
        r = sess.get(url, timeout=25)
        if r.status_code != 200:
            break
        page_items = _parse(r.text)
        if not page_items:
            break
        results.extend(page_items)
    return results


def search(keyword: str, pages: int = 2) -> list[Listing]:
    """keyword で楽天を検索して Listing のリストを返す。

    認証情報があれば公式API（クラウド対応）、無ければHTMLスクレイプ。
    """
    creds = _credentials()
    if creds:
        return _search_api(keyword, creds[0], creds[1], pages=pages)
    return _search_scrape(keyword, pages=pages)
