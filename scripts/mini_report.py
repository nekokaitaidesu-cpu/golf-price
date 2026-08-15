# -*- coding: utf-8 -*-
"""「今日のミニドラ」コーナー用のレポートを出す。

2026-08-15にユーザー指示で日次の「探し物」から差し替えたコーナー。
ミニドラ・短尺部門（catalog の category="mini"）を毎日まとめて見る。
ユーザーがこの部門に在庫3本（GT280 / コブラ KING TEC-MD / RMX VD/M Steady）を
持っているため、出口判断に直結する。

  python scripts/mini_report.py            # 当日の popularity.json で出す
  python scripts/mini_report.py --prev 3   # 3日前の history と比較（既定1日前）

出す内容:
  - 部門テーブル（30日実売・販売中・中央値・7日実売・回転日数）
  - 割安圏（中央の35〜80%）に落ちている販売中の玉
  - 自己在庫3本の相対位置
  - 販売中が枯れている機種（供給薄＝売り時のサイン）
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG_BY_KEY

POP_PATH = os.path.join(CACHE_DIR, "popularity.json")

# 自己在庫（flip-inventory と対応）。キーは catalog のもの
OWNED = {
    "yt_driver_gt280": "GT280 ミニドラ（実質32,646仕入）",
    "yt_driver_king": "コブラ KING TEC-MD（実質40,775仕入）",
    "mn_ym_rmxvdm_steady": "RMX VD/M Steady（15,000仕入・2本目）",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-sold", type=int, default=0,
                    help="30日実売がこれ未満の機種は表に出さない")
    args = ap.parse_args()

    with open(POP_PATH, encoding="utf-8") as f:
        pop = json.load(f)
    rows = [r for r in pop["rows"]
            if (CATALOG_BY_KEY.get(r["key"]) or None)
            and CATALOG_BY_KEY[r["key"]].category == "mini"]
    rows.sort(key=lambda r: -(r.get("sold") or 0))

    print(f"# 今日のミニドラ（データ: {pop['generated_at']}）")
    print(f"\n部門 {len(rows)} 機種\n")
    print(f"{'機種':<34}{'30d売':>6}{'販売中':>6}{'中央値':>9}{'最安':>9}"
          f"{'7d売':>5}{'日数':>6}")
    live = []
    for r in rows:
        if (r.get("sold") or 0) < args.min_sold:
            continue
        w7 = r.get("w7") or {}
        med = r.get("sold_price_median") or 0
        amin = r.get("active_min") or 0
        mark = " ★在庫" if r["key"] in OWNED else ""
        print(f"{r['label'][:34]:<34}{r.get('sold') or 0:>6}"
              f"{r.get('active') or 0:>6}{med:>9,}{amin:>9,}"
              f"{w7.get('sold') or 0:>5}{r.get('days_median') or 0:>6}{mark}")
        if med and amin:
            live.append((amin / med, r))

    print("\n## 割安圏（販売中最安 ÷ 実売中央 が 35〜80%）")
    hit = [(ratio, r) for ratio, r in live if 0.35 <= ratio <= 0.80]
    if hit:
        for ratio, r in sorted(hit):
            print(f"  ★{ratio*100:>3.0f}% {r['label'][:30]:<30} "
                  f"最安{r['active_min']:>7,} / 中央{r['sold_price_median']:>7,} "
                  f"（30日{r.get('sold')}本）")
    else:
        print("  なし（この部門は値崩れしにくく、出たら本命級）")

    print("\n## 販売中が枯れている機種（供給薄＝売り時のサイン）")
    thin = [r for r in rows if (r.get("sold") or 0) >= 3 and (r.get("active") or 0) <= 2]
    if thin:
        for r in thin:
            print(f"  販売中{r.get('active') or 0}件 {r['label'][:30]:<30} "
                  f"30日{r.get('sold')}本・中央{(r.get('sold_price_median') or 0):,}")
    else:
        print("  なし")

    print("\n## 自己在庫の位置")
    by_key = {r["key"]: r for r in rows}
    for k, note in OWNED.items():
        r = by_key.get(k)
        if not r:
            print(f"  {note}: 部門データなし（キー {k} が見つからない）")
            continue
        print(f"  {note}")
        print(f"    30日{r.get('sold') or 0}本 / 販売中{r.get('active') or 0}件 / "
              f"中央{(r.get('sold_price_median') or 0):,} / "
              f"最安{(r.get('active_min') or 0):,} / 回転{r.get('days_median') or 0}日")


if __name__ == "__main__":
    main()
