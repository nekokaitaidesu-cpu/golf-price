# -*- coding: utf-8 -*-
"""カテゴリ別（DR/FW/UT/アイアン/ミニドラ）の需給を比べる。

「FWは売れにくい気がする」「ドライバーやUTに移った方がいいか」という
仕入れ方針の問いに、体感でなく数字で答えるための道具（2026-08-19 追加）。

  python scripts/category_stats.py              # カテゴリ別の集計
  python scripts/category_stats.py --model SIM2 MAX   # 同じ機種名の DR/FW/UT を横並び

見る指標:
  sell_rate  = 売切率。期間内に出品されたうち売れた割合。**供給過多かの直接指標**
  days_median= 売れるまでの日数（中央値）
  active/sold= 販売中÷30日実売。1.0を超えると「在庫が月間需要を上回る」
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG_BY_KEY, CATEGORY_LABEL

POP = os.path.join(CACHE_DIR, "popularity.json")


def rows():
    with open(POP, encoding="utf-8") as f:
        pop = json.load(f)
    out = []
    for r in pop["rows"]:
        m = CATALOG_BY_KEY.get(r["key"])
        if not m or not (r.get("sold") or 0):
            continue
        out.append((m, r))
    return pop["generated_at"], out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", nargs="*", help="機種名で絞る（部分一致）")
    ap.add_argument("--min-sold", type=int, default=3,
                    help="30日実売がこれ未満の機種は除く（既定3）")
    args = ap.parse_args()
    gen, data = rows()
    print(f"# カテゴリ別の需給（データ: {gen}）\n")

    if args.model:
        kw = " ".join(args.model).lower().replace(" ", "")
        hit = [(m, r) for m, r in data
               if kw in (m.brand + m.label).lower().replace(" ", "")]
        print(f"「{' '.join(args.model)}」に一致する機種\n")
        print(f"{'カテゴリ':<10}{'機種':<24}{'30d売':>6}{'販売中':>6}"
              f"{'売切率':>7}{'回転':>6}{'在庫/需要':>9}{'中央値':>9}")
        for m, r in sorted(hit, key=lambda x: x[0].category):
            a, s = r.get("active") or 0, r.get("sold") or 0
            print(f"{CATEGORY_LABEL.get(m.category, m.category):<10}"
                  f"{m.label[:24]:<24}{s:>6}{a:>6}"
                  f"{(r.get('sell_rate') or 0):>7.2f}"
                  f"{(r.get('days_median') or 0):>6.1f}"
                  f"{(a / s if s else 0):>9.2f}"
                  f"{(r.get('sold_price_median') or 0):>9,}")
        return

    print(f"{'カテゴリ':<12}{'機種数':>6}{'30d売計':>8}{'販売中計':>9}"
          f"{'売切率':>8}{'回転':>7}{'在庫/需要':>10}")
    order = ["driver", "fw", "ut", "iron", "mini", "chipper"]
    for cat in order:
        g = [(m, r) for m, r in data
             if m.category == cat and (r.get("sold") or 0) >= args.min_sold]
        if not g:
            continue
        sold = sum(r.get("sold") or 0 for _, r in g)
        act = sum(r.get("active") or 0 for _, r in g)
        sr = statistics.median([r.get("sell_rate") or 0 for _, r in g])
        dm = statistics.median([r.get("days_median") or 0 for _, r in g
                                if r.get("days_median")])
        print(f"{CATEGORY_LABEL.get(cat, cat):<12}{len(g):>6}{sold:>8}{act:>9}"
              f"{sr:>8.2f}{dm:>7.1f}{(act / sold if sold else 0):>10.2f}")

    print("\n## 売切率が低い＝供給過多の機種（30日5本以上・売切率0.5未満）")
    bad = [(r.get("sell_rate") or 0, m, r) for m, r in data
           if (r.get("sold") or 0) >= 5 and (r.get("sell_rate") or 0) < 0.5]
    for sr, m, r in sorted(bad, key=lambda x: x[0])[:15]:
        print(f"  売切率{sr:>5.2f} [{CATEGORY_LABEL.get(m.category, m.category):<8}] "
              f"{m.label[:26]:<26} 30日{r.get('sold'):>3}本 販売中{r.get('active'):>3} "
              f"中央{(r.get('sold_price_median') or 0):>7,}")


if __name__ == "__main__":
    main()
