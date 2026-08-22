# -*- coding: utf-8 -*-
"""楽天（中古店）→メルカリ の粗利ランキング。日次「本命」ワークフローの第5段。

  python scripts/rakuten_rank.py            # 当日分・回転あり機種のみ
  python scripts/rakuten_rank.py --all      # 回転フィルタなし
  python scripts/rakuten_rank.py --date 2026-08-21

粗利 = メルカリ実売中央値 × (1 - 手数料) − 送料 − 楽天の当日最安(used_min)

**回転（7日実売）のない粗利は罠**（CLAUDE.md）。既定では popularity.json の
30日実売・7日実売でフィルタし、回転の裏付けがある機種だけを出す。
mixed_median の機種は中央値が世代混在なので粗利も信用できず、印を付けて末尾に回す。
used_min は数時間遅れなので、実際に買う前に scripts/rakuten_spot.py でライブ照合すること。
"""
import argparse
import json
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG_BY_KEY

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "history.db")
POP = os.path.join(CACHE_DIR, "popularity.json")
FEE_RATE = 0.10
SHIPPING = 1500


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--all", action="store_true", help="回転フィルタを外す")
    ap.add_argument("--category", default="", help="カテゴリで絞る")
    args = ap.parse_args()

    with open(POP, encoding="utf-8") as f:
        pop = json.load(f)
    prow = {r["key"]: r for r in pop["rows"]}

    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT key, label, used_min, used_count, fetched_at FROM price_history "
        "WHERE date = ? AND used_min IS NOT NULL", (args.date,)).fetchall()
    if not rows:
        print(f"{args.date} の price_history がありません。"
              f"data ブランチを同期してください。", file=sys.stderr)
        sys.exit(2)

    out = []
    for key, label, used_min, used_count, fetched in rows:
        m = CATALOG_BY_KEY.get(key)
        p = prow.get(key)
        if not m or not p:
            continue
        if args.category and m.category != args.category:
            continue
        med = p.get("sold_price_median")
        if not med or not used_min:
            continue
        sold30 = p.get("sold") or 0
        sold7 = (p.get("w7") or {}).get("sold") or 0
        if not args.all and not (sold30 >= 8 or sold7 >= 3):
            continue
        profit = round(med * (1 - FEE_RATE) - SHIPPING - used_min)
        if profit < 1000:
            continue
        out.append({
            "key": key, "label": label, "cat": m.category,
            "used_min": used_min, "used_count": used_count, "med": med,
            "profit": profit, "sold30": sold30, "sold7": sold7,
            "mixed": m.mixed_median, "days": p.get("days_median"),
            "fetched": fetched,
        })

    # mixed_median は末尾に回す（粗利が信用できない）
    out.sort(key=lambda r: (r["mixed"], -r["profit"]))
    print(f"# 楽天→メルカリ 粗利ランキング（{args.date}"
          f"{' / 回転フィルタなし' if args.all else ''}）")
    print(f"  粗利 = メルカリ実売中央 × {1-FEE_RATE:.2f} − 送料{SHIPPING:,} − 楽天最安")
    print(f"  取得: {out[0]['fetched'] if out else '—'}\n")
    print(f"{'機種':<34}{'種別':<6}{'楽天最安':>9}{'実売中央':>9}{'粗利':>8}"
          f"{'30d':>5}{'7d':>4}{'回転':>6}")
    for r in out[:args.top]:
        warn = " ⚠混在" if r["mixed"] else ""
        d = f"{r['days']}d" if r["days"] is not None else "-"
        print(f"{r['label'][:32]:<34}{r['cat']:<6}{r['used_min']:>9,}"
              f"{r['med']:>9,}{r['profit']:>8,}{r['sold30']:>5}{r['sold7']:>4}"
              f"{d:>6}{warn}")
    if not out:
        print("  該当なし")
    print(f"\n  ※used_min は数時間遅れ。買う前に "
          f"`python scripts/rakuten_spot.py <key>` でライブ照合すること")


if __name__ == "__main__":
    main()
