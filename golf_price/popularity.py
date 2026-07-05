"""メルカリ人気度（注目度）集計。

「直近 window_days 日以内にメルカリへ出品された当該機種の出品」をコホートとして、
売り切れ(実売)と販売中の両方から集め、機種ごとの人気指標を算出する。
出品ごとに created(出品日時) / updated(売却日時に近い更新日時) が取れるため、
  ・期間内に出品されて売れた数（人気の主指標）
  ・売り切れ率（需要と供給のバランス）
  ・売れるまでの日数（即売れ度）
  ・販売中の在庫数（販売中過多かどうか）
がキーワード検索＋既存の機種マッチング（_catalog_match）で正確に数えられる。

機種名の照合・ノイズ除去は損益ランキングと同じロジックを使う。
"""

import statistics
import time

from .catalog import DriverModel
from .normalize import is_parts_junk, detect_head_only, normalize
from .scrapers import mercari
from .service import _catalog_match

# ドライバー本体としてあり得ない安値（部品・カバー等）を弾く下限
MIN_PRICE = 3000
MIN_PRICE_CHIPPER = 1500

# 1機種あたりのページ上限（120件×N）。人気機種はここで打ち切り＝件数は下限値。
MAX_PAGES = 3

ITEM_URL = "https://jp.mercari.com/item/{id}"


def _pick(raws: list[dict], m: DriverModel, min_price: int, since: float) -> list[dict]:
    """生の検索結果から、期間内に出品された当該機種の本体出品だけを抜き出す。"""
    out = []
    for r in raws:
        mid = r.get("id", "")
        price = r.get("price")
        title = r.get("name") or ""
        # メルカリShops(事業者)は在庫再出品で件数・相場が歪むため個人間のみ
        if not mid.startswith("m") or r.get("itemType") == "ITEM_TYPE_BEYOND":
            continue
        created = int(r.get("created") or 0)
        updated = int(r.get("updated") or 0)
        if not price or not title or created < since:
            continue
        if int(price) < min_price or is_parts_junk(title):
            continue
        if not _catalog_match(title, m):
            continue
        out.append({
            "id": mid, "title": title, "price": int(price),
            "created": created, "updated": updated,
            "head_only": detect_head_only(normalize(title)),
        })
    return out


def _flag(sold: int, active: int, sell_rate, days_median) -> str:
    """需給の状態バッジ。
    hot   = 即売れ（よく売れ、出てもすぐ消える）
    glut  = 販売中過多（供給>需要。在庫がだぶついている）
    scarce= 品薄（売れるのに玉がない）
    """
    if sold >= 5 and (sell_rate or 0) >= 0.6 and days_median is not None and days_median <= 4:
        return "hot"
    if active >= 8 and sell_rate is not None and sell_rate <= 0.3:
        return "glut"
    if sold >= 4 and active <= 2:
        return "scarce"
    return ""


def analyze_model(m: DriverModel, window_days: int = 30,
                  max_pages: int = MAX_PAGES) -> dict:
    """1機種ぶんの人気指標を集計する。メルカリ疎通失敗は MercariError が上がる。"""
    now = time.time()
    since = now - window_days * 86400
    min_price = MIN_PRICE_CHIPPER if m.category == "chipper" else MIN_PRICE

    sold_raw, sold_trunc = mercari.search_recent_raw(
        m.keyword, "STATUS_SOLD_OUT", price_min=min_price,
        max_pages=max_pages, stop_before=since)
    active_raw, active_trunc = mercari.search_recent_raw(
        m.keyword, "STATUS_ON_SALE", price_min=min_price,
        max_pages=max_pages, stop_before=since)

    sold = _pick(sold_raw, m, min_price, since)
    active = _pick(active_raw, m, min_price, since)

    total = len(sold) + len(active)
    sell_rate = round(len(sold) / total, 3) if total else None
    days = [max(0.0, (x["updated"] - x["created"]) / 86400) for x in sold]
    days_median = round(statistics.median(days), 1) if days else None
    full_sold = [x["price"] for x in sold if not x["head_only"]]
    sold_price_median = round(statistics.median(full_sold)) if full_sold else None
    active_min = min((x["price"] for x in active), default=None)

    # 直近に売れた順のサンプル（ページで「何がいくらで売れたか」を見せる用）
    samples = sorted(sold, key=lambda x: -x["updated"])[:5]

    return {
        "key": m.key,
        "label": f"{m.brand} {m.label}",
        "brand": m.brand,
        "year": m.year,
        "category": m.category,
        "window_days": window_days,
        "sold": len(sold),                    # 期間内に出品→売れた数
        "active": len(active),                # 期間内に出品→まだ販売中
        "listed": total,                      # 期間内の出品総数（流通量・注目度）
        "sell_rate": sell_rate,               # 売り切れ率 0〜1
        "days_median": days_median,           # 売れるまでの日数（中央値）
        "sold_price_median": sold_price_median,  # 実売価格の中央値（完品のみ）
        "active_min": active_min,             # 販売中の最安値
        "truncated": bool(sold_trunc or active_trunc),  # ページ上限打ち切り=件数は下限
        "flag": _flag(len(sold), len(active), sell_rate, days_median),
        "sold_samples": [
            {"title": s["title"], "price": s["price"],
             "url": ITEM_URL.format(id=s["id"]),
             "days": round((s["updated"] - s["created"]) / 86400, 1),
             "sold_at": time.strftime("%m/%d", time.localtime(s["updated"]))}
            for s in samples
        ],
    }
