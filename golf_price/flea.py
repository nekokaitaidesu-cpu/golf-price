"""フリマ実売（Yahoo落札相場）の取得＋機種一致フィルタ。

検索キーワードでは別機種・部品・スパムが混ざるため、
圧縮キー照合・ブランド一致・部品ノイズ除去・最低価格で本体のみに絞る。
"""

import re
import unicodedata

from .scrapers import yahoo_auction
from .scrapers.base import Listing
from .normalize import compact, is_parts_junk


def params_from_label(label: str) -> tuple[str, str, list[str]]:
    """モデル名ラベルから (検索KW, 必須圧縮キー, ブランド圧縮キー群) を導出。"""
    t = unicodedata.normalize("NFKC", label or "")
    t = re.sub(r"\d{1,2}(?:\.\d)?\s*[°度]", "", t)  # ロフト除去
    toks = [w for w in t.split() if w]
    brand = toks[0] if toks else ""
    model_core = " ".join(toks[1:]).strip()
    keyword = f"{brand} {model_core} ドライバー".strip()
    return keyword, compact(model_core), [compact(brand)] if brand else []


def collect(keyword: str, required_compact: str, brand_compacts: list[str],
            min_price: int = 3000, pages: int = 2) -> list[Listing]:
    """落札相場から、当該機種の本体出品（実売）だけを返す。"""
    raw = yahoo_auction.search_closed(keyword, pages=pages)
    out: list[Listing] = []
    for l in raw:
        if l.price < min_price:
            continue
        if is_parts_junk(l.title):
            continue
        ct = compact(l.title)
        if required_compact and required_compact not in ct:
            continue
        if brand_compacts and not any(b in ct for b in brand_compacts):
            continue
        out.append(l)
    return out
