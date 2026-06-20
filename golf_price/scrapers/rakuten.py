"""楽天市場 検索結果スクレイパー。

価格は商品カード div.searchresultitem の data-track-price 属性から取得する
（HTMLの見た目クラスはハッシュ化され変わりやすいが、data-* 属性は安定しているため）。
複数ページを巡回して件数を確保する。
"""

import urllib.parse
from bs4 import BeautifulSoup

from .base import Listing, make_session, polite_sleep

BASE = "https://search.rakuten.co.jp/search/mall/{kw}/"
# ページ送りは ?p=2 ... 楽天は &p=N
PAGED = "https://search.rakuten.co.jp/search/mall/{kw}/?p={page}"


def _parse(html: str) -> list[Listing]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[Listing] = []
    for it in soup.select("div.searchresultitem"):
        price_raw = it.get("data-track-price") or it.get("data-track-price-ranges")
        if not price_raw:
            continue
        # "23760" もしくは "23760~26000" の形があるので最初の数値を採用
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
        img = it.select_one("img")
        image = (img.get("src") if img else "") or ""
        out.append(Listing(
            source="rakuten",
            title=title,
            price=price,
            url=url,
            shop=shop,
            is_used=("中古" in title),
            sold=False,           # 楽天は販売中（実売ではない）
            image=image,
        ))
    return out


def search(keyword: str, pages: int = 2) -> list[Listing]:
    """keyword で楽天を検索して Listing のリストを返す。"""
    sess = make_session()
    kw = urllib.parse.quote(keyword)
    results: list[Listing] = []
    for page in range(1, pages + 1):
        url = BASE.format(kw=kw) if page == 1 else PAGED.format(kw=kw, page=page)
        polite_sleep()
        r = sess.get(url, timeout=25)
        if r.status_code != 200:
            break
        page_items = _parse(r.text)
        if not page_items:
            break
        results.extend(page_items)
    return results
