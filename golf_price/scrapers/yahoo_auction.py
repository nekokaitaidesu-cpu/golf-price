"""Yahoo!オークション 落札相場スクレイパー（実際に売れた価格＝③フリマ実売）。

落札相場ページは結果をJSで描画するが、HTML内の <script id="__NEXT_DATA__">
にJSONとして全件埋め込まれているため、それを解析する（ブラウザ不要）。
closedsearch は Yahoo!オークションの落札分＋Yahoo!フリマの売却分を含む。
"""

import json
import urllib.parse
from bs4 import BeautifulSoup

from .base import Listing, make_session, polite_sleep
from ..normalize import extract_loft

CLOSED = "https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={kw}&n={per}&b={begin}"


def _extract_items(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return []
    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError:
        return []
    try:
        return data["props"]["pageProps"]["initialState"]["search"]["items"]["listing"]["items"]
    except (KeyError, TypeError):
        return []


def _to_listing(raw: dict) -> Listing | None:
    price = raw.get("price")
    title = raw.get("title")
    if not price or not title:
        return None
    aid = raw.get("auctionId", "")
    url = f"https://auctions.yahoo.co.jp/jp/auction/{aid}" if aid else ""
    is_flea = bool(raw.get("isFleamarketItem"))
    end = (raw.get("endTime") or "")[:10]
    seller = ""
    s = raw.get("seller")
    if isinstance(s, dict):
        seller = s.get("displayName") or s.get("id") or ""
    label = "Yahoo!フリマ" if is_flea else "ヤフオク落札"
    if end:
        label += f"（{end}）"
    return Listing(
        source="yahoo_flea" if is_flea else "yahoo_auction",
        title=title,
        price=int(price),
        url=url,
        shop=label,
        is_used=True,
        sold=True,                 # 実際に売れた価格
        image=raw.get("imageUrl", "") or "",
        loft=extract_loft(title),
    )


def search_closed(keyword: str, pages: int = 2, per: int = 100) -> list[Listing]:
    """落札相場を取得（pages×per 件まで）。"""
    sess = make_session()
    kw = urllib.parse.quote(keyword)
    out: list[Listing] = []
    for page in range(pages):
        begin = page * per + 1
        url = CLOSED.format(kw=kw, per=per, begin=begin)
        polite_sleep(1.2)
        r = sess.get(url, timeout=25)
        if r.status_code != 200:
            break
        raws = _extract_items(r.text)
        if not raws:
            break
        for raw in raws:
            lst = _to_listing(raw)
            if lst:
                out.append(lst)
        if len(raws) < per:
            break
    return out
