# -*- coding: utf-8 -*-
"""特定の中古ショップ（既定: ゴルフドゥ）の在庫を横断スキャンして割安個体を洗い出す。

  python scripts/shop_watch.py                      # ゴルフドゥ・回転上位40機種
  python scripts/shop_watch.py --shop gdoshop       # 別の店
  python scripts/shop_watch.py --limit 80 --min-profit 3000
  python scripts/shop_watch.py --category fw

楽天のセール前は、店側が **販売期間を先に設定した「予告出品」** を並べることがある
（2026-08-22に発見。ゴルフドゥが 9/3 20:00 開始の枠で複数点を仕込んでいた）。
予告出品は割引後価格が先に入っているので、**セール開始前に買いラインを作れる**。

出力は2種類:
  1. 割安候補 … メルカリ実売中央で売り直したときの粗利が閾値以上
  2. ⚠価格ミス疑い … **同一モデル・同一店内の他個体より大きく安い**個体
     2026-08-22の教訓: ゴルフドゥのQi10 5Wに11,008円の出品があったが、
     同店の同モデル最安は16,608円（43%下）で、ページごと消えた。
     **相場から4割下は掘り出し物より入力ミスを疑う**。飛びついても買えない
"""
import argparse
import json
import os
import re
import statistics
import sys
import concurrent.futures as cf
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG, CATALOG_BY_KEY
from golf_price.normalize import (detect_head_only, is_ladies, is_lefty,
                                  is_parts_junk, normalize)
from golf_price.scrapers import rakuten
from golf_price.service import _catalog_match

POP = os.path.join(CACHE_DIR, "popularity.json")
FEE_RATE = 0.10
SHIPPING = {"driver": 1700, "mini": 1700, "iron": 1450}   # 既定は1450
# 同一モデル・同一店内で、他個体の中央値からこの割合より安い個体は入力ミスを疑う
ERROR_FRAC = 0.70
# ただし**安さの理由が題名に書いてある**なら入力ミスではない（訳あり・低ランク・
# リシャフト等）。これを弾かないと、単なる状態難品が「ミス疑い」を埋め尽くす
_EXPLAINED = re.compile(r"訳あり|ワケあり|ジャンク|[DE]ランク|リシャフト|"
                        r"シャフト交換|グリップ交換|傷|キズ|凹み|打痕|割れ|クラック")


def ship(cat: str) -> int:
    return SHIPPING.get(cat, 1450)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shop", default="golfdo", help="店の識別子（URL/店名の部分一致）")
    ap.add_argument("--limit", type=int, default=40, help="回転上位から何機種見るか")
    ap.add_argument("--min-profit", type=int, default=2500)
    ap.add_argument("--category", default="")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    with open(POP, encoding="utf-8") as f:
        pop = json.load(f)
    rows = {r["key"]: r for r in pop["rows"]}

    # 回転のある機種を上位から。回転のない粗利は罠（CLAUDE.md）
    cands = []
    for m in CATALOG:
        r = rows.get(m.key)
        if not r or not r.get("sold_price_median"):
            continue
        if args.category and m.category != args.category:
            continue
        if m.mixed_median:          # 中央値が世代/番手混在の機種は粗利が絵に描いた餅
            continue
        sold30 = r.get("sold") or 0
        sold7 = (r.get("w7") or {}).get("sold") or 0
        if sold30 < 8 and sold7 < 3:
            continue
        cands.append((m, r, sold30))
    cands.sort(key=lambda x: -x[2])
    cands = cands[:args.limit]

    print(f"店「{args.shop}」を {len(cands)} 機種ぶんスキャンします "
          f"（人気データ: {pop['generated_at']}）", file=sys.stderr)

    def one(item):
        m, r, _ = item
        out = []
        try:
            listings = rakuten.search(m.keyword + " 中古", pages=3)
        except Exception:
            return m, r, out
        for l in listings:
            blob = f"{l.url or ''} {l.shop or ''}"
            if args.shop.lower() not in blob.lower():
                continue
            t = l.title or ""
            if not l.is_used or is_parts_junk(t) or is_lefty(t) or is_ladies(t):
                continue
            if detect_head_only(normalize(t)):
                continue
            if not _catalog_match(t, m):
                continue
            out.append(l)
        return m, r, out

    found, errsus = [], []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for m, r, listings in ex.map(one, cands):
            if not listings:
                continue
            med = r["sold_price_median"]
            prices = sorted(l.price for l in listings)
            shop_med = statistics.median(prices)
            for l in listings:
                profit = round(med * (1 - FEE_RATE) - ship(m.category) - l.price)
                y_profit = round(med - ship(m.category) - l.price)
                # 同一店内で他個体より極端に安く、**かつ安さの理由が題名に無い**
                # ものだけを入力ミス疑いに回す
                unexplained = (len(prices) >= 3
                               and l.price < shop_med * ERROR_FRAC
                               and not _EXPLAINED.search(t_short(l.title)))
                if unexplained:
                    errsus.append((m, r, l, y_profit, shop_med))
                elif y_profit >= args.min_profit:
                    found.append((m, r, l, y_profit, shop_med,
                                  bool(_EXPLAINED.search(l.title or ""))))

    found.sort(key=lambda x: -x[3])
    print(f"\n# {args.shop} 割安候補（{len(found)}件）")
    print("  粗利はヤフーフリマ0%枠での手取り（実売中央 − 送料 − 仕入）\n")
    for m, r, l, yp, sm, flawed in found[:25]:
        mp = round(r["sold_price_median"] * (1 - FEE_RATE) - ship(m.category) - l.price)
        warn = "  ⚠状態難あり表記" if flawed else ""
        print(f"+{yp:>6,} (メルカリ+{mp:>6,}) ¥{l.price:>7,} | "
              f"{m.brand} {m.label}{warn}")
        print(f"         実売中央{r['sold_price_median']:,} / 30日{r.get('sold')}本 "
              f"/ 7日{(r.get('w7') or {}).get('sold', 0)}本 / 回転{r.get('days_median')}日")
        print(f"         {t_short(l.title)}")
        print(f"         {l.url}")

    print(f"\n# ⚠価格ミス疑い（{len(errsus)}件）"
          f" — 同一店内の他個体より {int((1-ERROR_FRAC)*100)}%以上安い")
    print("  2026-08-22の教訓: この形は買えずに消えることがある。飛びつく前にページを開いて"
          "販売期間・在庫を確認すること\n")
    for m, r, l, yp, sm in errsus[:15]:
        print(f"  ¥{l.price:>7,} (同店中央 {sm:,.0f} の {l.price/sm*100:.0f}%) "
              f"| {m.brand} {m.label} → 粗利+{yp:,}")
        print(f"         {t_short(l.title)}")
        print(f"         {l.url}")
    if not errsus:
        print("  なし")


def t_short(t: str) -> str:
    return re.sub(r"\s+", " ", (t or ""))[:74]


if __name__ == "__main__":
    main()
