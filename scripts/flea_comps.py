# -*- coding: utf-8 -*-
"""カタログに無い機種でも、キーワード指定でメルカリの実売（フリマ相場）を測る。

  python scripts/flea_comps.py "ブリヂストン B1 フェアウェイウッド" --must 5w,5番 --days 120
  python scripts/flea_comps.py "PING G440 フェアウェイウッド" --must 3w --exclude ヘッドのみ

出品（/shuppin）や店頭仕入れの判定で、**カタログ外の機種の分母を作る**ための道具。
カタログキーがある機種は `scripts/denominator_check.py` の方が情報量が多い。

出すもの:
  - 完品／ヘッド単品を分けた実売の中央値・レンジ・件数（部品を混ぜると分母が壊れる）
  - 実売サンプル（安い順・タイトル付き）＝根拠として出品メモに貼れる
  - 販売中の最安（＝いま競合になる値段）

⚠ 中央値は「売れた値段」であって「自分が売れる値段」ではない。
状態が下の個体は下限側に寄せること（CLAUDE.md の判断基準を参照）。
"""
import argparse
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.normalize import compact, detect_head_only, is_parts_junk
from golf_price.scrapers import mercari


def pick(items, must, exclude):
    out = []
    for i in items:
        t = compact(i.get("name") or "")
        if any(compact(m) not in t for m in must):
            continue
        if any(compact(x) in t for x in exclude):
            continue
        out.append(i)
    return out


def show(title, items, limit):
    if not items:
        print(f"  {title}: 0件")
        return None
    prices = sorted(int(i["price"]) for i in items)
    med = int(statistics.median(prices))
    print(f"  {title}: n={len(prices)} 中央 ¥{med:,}  範囲 ¥{prices[0]:,}〜¥{prices[-1]:,}")
    for i in sorted(items, key=lambda x: int(x["price"]))[:limit]:
        print(f"      ¥{int(i['price']):>7,}  {i['name'][:56]}")
        print(f"               https://jp.mercari.com/item/{i['id']}")
    return med


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword", help="メルカリ検索キーワード")
    ap.add_argument("--must", default="", help="タイトルに必須の語（カンマ区切り・空白は無視して照合）")
    ap.add_argument("--exclude", default="", help="タイトルに含まれたら除外する語（カンマ区切り）")
    ap.add_argument("--days", type=int, default=120, help="さかのぼる日数（既定120）")
    ap.add_argument("--limit", type=int, default=8, help="表示するサンプル件数")
    args = ap.parse_args()

    must = [m for m in args.must.split(",") if m.strip()]
    exclude = [x for x in args.exclude.split(",") if x.strip()]
    since = mercari.time.time() - args.days * 86400

    print(f"### {args.keyword}  must={must or '—'} exclude={exclude or '—'} / {args.days}日")
    for label, status in (("実売", "STATUS_SOLD_OUT"), ("販売中", "STATUS_ON_SALE")):
        raw, trunc = mercari.search_recent_raw(args.keyword, status, price_min=3000,
                                               max_pages=3, stop_before=since)
        hit = pick(raw, must, exclude)
        junk = [i for i in hit if is_parts_junk(i["name"])]
        head = [i for i in hit if i not in junk and detect_head_only(i["name"])]
        full = [i for i in hit if i not in junk and i not in head]
        print(f"[{label}] 取得{len(raw)}件 → 条件一致{len(hit)}件"
              f"（完品{len(full)} / ヘッド単品{len(head)} / 部品{len(junk)}）"
              f"{' ※ページ打ち切りあり' if trunc else ''}")
        show("完品", full, args.limit)
        if head:
            show("ヘッド単品", head, 3)
        print()


if __name__ == "__main__":
    main()
