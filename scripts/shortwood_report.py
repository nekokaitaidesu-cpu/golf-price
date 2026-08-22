# -*- coding: utf-8 -*-
"""「今日のショートウッド」コーナー用のレポートを出す。

2026-08-21にユーザー指示で新設。ショートウッド部門（catalog の
category="shortwood" ・7W/9W）を毎日まとめて見る。

新設の根拠（2026-08-21実測・メルカリ・右利き/レディース除外）:
  ・同一機種内の 7W中央 ÷ 5W中央 が **10機種すべて1.0超（中央1.23倍）**
  ・販売中/実売の比 = 3W 0.71 / 5W 0.75 / **7W 0.59 / 9W 0.41**（番手が上がるほど品薄）
  ・それでいて売れるまでの日数は3W/5Wと同等（中央4〜6日）
  → 「高い・薄い・でも回る」独立した需給。FWに混ぜると中央値が番手混在になる。

  python scripts/shortwood_report.py            # popularity.json から出す
  python scripts/shortwood_report.py --live     # メルカリを今から叩いて集計する
  python scripts/shortwood_report.py --live --workers 6

出す内容:
  - 部門テーブル（30日実売・販売中・中央値・最安・割安率・7日実売・回転日数）
  - 割安圏（中央の35〜80%）に落ちている販売中の玉（URL付き・検死対象）
  - 販売中が枯れている機種（供給薄＝仕入れ難／保有なら売り時）
  - 買いラインの目安（同機種FWキーの中央値×1.2 = ユーザー運用値）
"""
import argparse
import concurrent.futures as cf
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG, CATALOG_BY_KEY
from golf_price import popularity
from golf_price.scrapers import mercari

POP_PATH = os.path.join(CACHE_DIR, "popularity.json")
ITEM_URL = "https://jp.mercari.com/item/{id}"
# 割安圏（CLAUDE.md の運用値: 割安=35〜72%・準割安=〜80%）
CHEAP_LO, CHEAP_HI = 0.35, 0.80
# ショートウッドの買いライン（2026-08-21のユーザー運用値）:
# 同機種の5W相場×1.2以下なら割安。ここでは5W単独の相場を持っていないので
# FWキー（3W/5W主体）の中央値を代理に使う。あくまで目安として出す
BUY_LINE_MULT = 1.2
# shortwood キー → 同機種のFWキー（買いラインの代理分母）
FW_COUNTERPART = {
    "sw_tm_sim2": "fw_tm_sim2max", "sw_tm_stealth2": "fw_tm_stealth2",
    "sw_tm_qi10": "fw_tm_qi10", "sw_cw_paradym": "fw_cw_paradym",
    "sw_cw_aismoke": "fw_cw_aismoke", "sw_ping_g425": "fw_ping_g425max",
    "sw_ping_g430": "fw_ping_g430max", "sw_ping_g440": "fw_ping_g440",
    "sw_tm_m2": "fw_tm_m2",
}


def scan_live(models, workers: int) -> list[dict]:
    """メルカリを直接叩いて、販売中の明細まで持った行を作る。"""
    def one(m):
        since = popularity.time.time() - 30 * 86400
        sold_raw, st = mercari.search_recent_raw(
            m.keyword, "STATUS_SOLD_OUT", price_min=popularity.MIN_PRICE,
            max_pages=popularity.MAX_PAGES, stop_before=since)
        act_raw, at = mercari.search_recent_raw(
            m.keyword, "STATUS_ON_SALE", price_min=popularity.MIN_PRICE,
            max_pages=popularity.MAX_PAGES, stop_before=since)
        sold = popularity._pick(sold_raw, m, popularity.MIN_PRICE, since)
        act = popularity._pick(act_raw, m, popularity.MIN_PRICE, since)
        row = {"key": m.key, "label": f"{m.brand} {m.label}", "brand": m.brand}
        row.update(popularity._aggregate(sold, act, bool(st or at), 30))
        w7 = popularity.time.time() - 7 * 86400
        row["w7"] = {"sold": len([x for x in sold if x["created"] >= w7])}
        # この部門は**ヘッド単品の比率が異常に高い**（7W/9Wはヘッドにプレミアが
        # 付くため。2026-08-21のG425は実売5件中4件がヘッド単品だった）。
        # 完品とヘッドを混ぜて「実売◯本」と読むと市場の厚みを大きく誤認するので分けて出す。
        # ヘッド中央値は分売（ヘッド＋スリーブ付きシャフト）の判断にも直接使う
        row["sold_full"] = len([x for x in sold if not x["head_only"]])
        row["sold_head"] = len(sold) - row["sold_full"]
        hp = [x["price"] for x in sold if x["head_only"]]
        row["head_median"] = round(statistics.median(hp)) if hp else None
        row["_active"] = sorted(
            [x for x in act if not x["head_only"]], key=lambda x: x["price"])
        return row

    out = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(one, models):
            out.append(r)
            print(f"  ... {r['label']} 実売{r['sold']} 販売中{r['active']}",
                  file=sys.stderr)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="popularity.json でなくメルカリを今から叩く")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    models = [m for m in CATALOG if m.category == "shortwood"]
    fw_med = {}
    stamp = "live"
    if os.path.exists(POP_PATH):
        with open(POP_PATH, encoding="utf-8") as f:
            pop = json.load(f)
        fw_med = {r["key"]: r.get("sold_price_median") for r in pop["rows"]}
        stamp = pop.get("generated_at", "?")

    if args.live:
        print("メルカリをライブ集計中…", file=sys.stderr)
        rows = scan_live(models, args.workers)
        stamp = f"ライブ集計（{stamp} のFW中央値を買いライン分母に併用）"
    else:
        rows = [r for r in pop["rows"]
                if CATALOG_BY_KEY.get(r["key"])
                and CATALOG_BY_KEY[r["key"]].category == "shortwood"]
        if not rows:
            print("popularity.json にショートウッドの行がありません。"
                  "--live を付けて実行してください。", file=sys.stderr)
            sys.exit(2)

    rows.sort(key=lambda r: -(r.get("sold") or 0))

    print(f"# 今日のショートウッド（7W/9W）  データ: {stamp}")
    print(f"\n部門 {len(rows)} 機種 / 30日実売 合計 "
          f"{sum(r.get('sold') or 0 for r in rows)}本\n")
    # 完品/ヘッド単品の内訳は --live でしか計算していない（popularity.json は持たない）。
    # 内訳が無いのに「完品」列へ合計を出すと市場の厚みを誤読するので、見出しを変える
    # （2026-08-22: G425は実売4本すべてがヘッド単品なのに「完品4」と表示していた）
    split = any("sold_full" in r for r in rows)
    print(f"{'機種':<30}{('完品' if split else '実売*'):>5}{'頭':>4}{'販中':>5}"
          f"{'完品中央':>10}{'頭中央':>9}{'最安':>9}{'割安':>6}{'7d':>4}"
          f"{'日数':>6}  状態")
    cheap, thin = [], []
    for r in rows:
        med, lo = r.get("sold_price_median"), r.get("active_min")
        rate = (lo / med) if (med and lo) else None
        w7 = (r.get("w7") or {}).get("sold") or 0
        d = r.get("days_median")
        full = r.get("sold_full")
        if full is None:                      # 内訳なし（popularity.json 由来）
            full = r.get("sold") or 0
        state = r.get("flag") or ""
        if med and lo and CHEAP_LO <= (rate or 9) <= CHEAP_HI:
            state = "★割安圏 " + state
            cheap.append(r)
        if full >= 2 and (r.get("active") or 0) == 0:
            state = "品薄0件 " + state
            thin.append(r)
        print(f"{r['label']:<30}{full:>5}{r.get('sold_head', 0):>4}"
              f"{r.get('active') or 0:>5}{(med or 0):>10,}"
              f"{(r.get('head_median') or 0):>9,}{(lo or 0):>9,}"
              f"{(f'{rate*100:.0f}%' if rate else '-'):>6}{w7:>4}"
              f"{(f'{d}d' if d is not None else '-'):>6}  {state}")
    if split:
        print("  ※完品=完品の30日実売本数／頭=ヘッド単品の30日実売本数。"
              "中央値・最安・割安率はすべて完品同士で計算")
    else:
        print("  ※**実売*はヘッド単品を含む合計**（完品/ヘッドの内訳は --live でのみ算出）。"
              "中央値・最安・割安率は完品同士で計算しているので、"
              "『実売◯本・完品中央が空欄』の機種は実売が全部ヘッド単品")

    print("\n## 割安圏（中央の35〜80%）の販売中")
    if not cheap:
        print("  なし。この部門は値崩れしにくいので、出たら本命級です。")
    for r in cheap:
        med = r["sold_price_median"]
        print(f"\n  ▼ {r['label']}（中央 {med:,}円）")
        for a in (r.get("_active") or [])[:4]:
            if a["price"] > med * CHEAP_HI:
                break
            print(f"     {a['price']:>7,}円 ({a['price']/med*100:.0f}%) "
                  f"{ITEM_URL.format(id=a['id'])}")
            print(f"        {a['title'][:60]}")
        if "_active" not in r:
            print("     （明細は --live で出ます）")

    print("\n## 供給が枯れている機種（仕入れ難／保有なら売り時）")
    print("  " + ("、".join(f"{r['label']}(完品実売{r.get('sold_full', r['sold'])})"
                           for r in thin) if thin else "なし"))

    print("\n## 分売の目安（ヘッド単品中央 ÷ 完品中央）")
    print("  ※7割超ならヘッド側の値持ちが良い。スリーブ付きシャフトが中央1万前後で"
          "売れるので、上位カスタムが刺さっていれば分解が有利")
    for r in rows:
        med, hm = r.get("sold_price_median"), r.get("head_median")
        if med and hm:
            print(f"  {r['label']:<30} ヘッド {hm:>7,} / 完品 {med:>7,}"
                  f" = {hm/med*100:>5.0f}%  (ヘッド実売{r.get('sold_head', 0)}本)")

    print("\n## 買いラインの目安（同機種FW中央値 × 1.2）")
    print("  ※FW側は3W/5W主体の中央値。ユーザー運用値『5W相場×1.2以下なら割安』の代理")
    for r in rows:
        fk = FW_COUNTERPART.get(r["key"])
        base = fw_med.get(fk) if fk else None
        if not base:
            continue
        line = round(base * BUY_LINE_MULT)
        med = r.get("sold_price_median")
        note = ""
        if med:
            note = ("（実勢中央がラインより上＝プレミア健在）" if med > line
                    else "（実勢中央がラインより下＝妙味薄い）")
        print(f"  {r['label']:<32} FW中央 {base:>7,} → 買い上限 {line:>7,}  {note}")


if __name__ == "__main__":
    main()
