# -*- coding: utf-8 -*-
"""今日の本命スキャン: 人気上位機種をライブ再集計しつつ割安候補を拾う。

「今日の本命教えて」ワークフローの第1段。実行前に data ブランチから
最新データを同期しておくこと（CLAUDE.md の手順参照）。

  python scripts/honmei_scan.py

- .cache/popularity.json からウォッチリスト選定（30日15本以上 or 7日4本以上）
- 各機種を再集計して popularity.json にマージ（朝版は日付き .bak に退避）
- 販売中×直近7日出品×実売中央値の35〜80%×状態6以下×非ヘッド単品を候補化
- オークション形式は raw の auction フィールドで判定して印を付ける
- 候補は .cache/honmei_candidates.json へ（第2段 honmei_autopsy.py に渡す）

80機種で10分前後かかる。バックグラウンド実行推奨。
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG
from golf_price.normalize import compact
from golf_price import popularity
from golf_price.popularity import MIN_PRICE, MIN_PRICE_CHIPPER, _pick
from golf_price.scrapers import mercari

POP_PATH = os.path.join(CACHE_DIR, "popularity.json")
BAK_PATH = os.path.join(
    CACHE_DIR, f"popularity_{time.strftime('%Y%m%d')}_morning.bak.json")
OUT_PATH = os.path.join(CACHE_DIR, "honmei_candidates.json")

RATIO_MIN, RATIO_MAX = 0.35, 0.80   # 0.72超〜0.80は準割安
COND_MAX = 6
LOOKBACK_DAYS = 7                    # 候補は直近7日出品まで(鮮度は age_h で見る)

with open(POP_PATH, encoding="utf-8") as f:
    pop = json.load(f)
by_key = {m.key: m for m in CATALOG}

watch, seen = [], set()
for r in pop["rows"]:
    w7 = r.get("w7") or {}
    med = r.get("sold_price_median") or 0
    dedup = (r.get("category") or "", compact(r["label"]))
    if r["key"] not in by_key or dedup in seen:
        continue
    if med < 8000:
        continue
    if r.get("sold", 0) < 15 and w7.get("sold", 0) < 4:
        continue
    seen.add(dedup)
    watch.append(r["key"])
print(f"ウォッチ {len(watch)} 機種: " + " / ".join(watch))

now = time.time()
since7 = now - LOOKBACK_DAYS * 86400
fresh_rows, cands, errors = {}, [], []

for i, key in enumerate(watch, 1):
    m = by_key[key]
    min_price = MIN_PRICE_CHIPPER if m.category == "chipper" else MIN_PRICE
    since30 = now - 30 * 86400
    try:
        sold_raw, st = mercari.search_recent_raw(
            m.keyword, "STATUS_SOLD_OUT", price_min=min_price,
            max_pages=3, stop_before=since30)
        active_raw, at = mercari.search_recent_raw(
            m.keyword, "STATUS_ON_SALE", price_min=min_price,
            max_pages=3, stop_before=since30)
    except mercari.MercariError as e:
        errors.append(f"{key}: {e}")
        print(f"[{i}/{len(watch)}] {key}: 取得失敗 {e}")
        if "スキップ" in str(e):
            print("連続失敗のため中断")
            break
        continue

    sold = _pick(sold_raw, m, min_price, since30)
    active = _pick(active_raw, m, min_price, since30)
    row = {"key": m.key, "label": f"{m.brand} {m.label}", "brand": m.brand,
           "year": m.year, "category": m.category, "window_days": 30}
    row.update(popularity._aggregate(sold, active, bool(st or at), 30))
    t7 = (popularity._window_truncated(sold_raw, st, since7)
          or popularity._window_truncated(active_raw, at, since7))
    row["w7"] = popularity._aggregate(
        [x for x in sold if x["created"] >= since7],
        [x for x in active if x["created"] >= since7], t7, 7)
    fresh_rows[key] = row
    w7 = row["w7"]
    print(f"[{i}/{len(watch)}] {key}: 30日 売{row['sold']}/中{row['active']} "
          f"中央{row['sold_price_median']} | 7日 売{w7['sold']}/中{w7['active']} "
          f"{'★' + row['flag'] if row['flag'] else ''}")

    med = row["sold_price_median"]
    if not med:
        continue
    raw_by_id = {r2.get("id"): r2 for r2 in active_raw}
    for p in active:
        if p["created"] < since7 or p["head_only"]:
            continue
        ratio = p["price"] / med
        if not (RATIO_MIN <= ratio <= RATIO_MAX):
            continue
        raw = raw_by_id.get(p["id"], {})
        cond = int(raw.get("itemConditionId") or 0)
        if cond > COND_MAX:
            continue
        cands.append({
            "key": key, "label": row["label"], "id": p["id"],
            "title": p["title"], "price": p["price"],
            "median": med, "ratio": round(ratio, 3), "cond": cond,
            "age_h": round((now - p["created"]) / 3600, 1),
            "w7_sold": w7["sold"], "w7_active": w7["active"],
            "sell_rate": row["sell_rate"],
            "auction": bool(raw.get("auction")),
        })

if fresh_rows:
    if not os.path.exists(BAK_PATH):
        with open(BAK_PATH, "w", encoding="utf-8") as f:
            json.dump(pop, f, ensure_ascii=False)
    merged = [fresh_rows.get(r["key"], r) for r in pop["rows"]]
    merged.sort(key=lambda r: (-r["sold"], -(r["sell_rate"] or 0)))
    pop["rows"] = merged
    pop["generated_at"] += (" (+" + time.strftime("%m/%d %H:%M")
                            + f" ライブ{len(fresh_rows)}機種マージ)")
    with open(POP_PATH, "w", encoding="utf-8") as f:
        json.dump(pop, f, ensure_ascii=False)

cands.sort(key=lambda c: c["ratio"])
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(cands, f, ensure_ascii=False, indent=1)
print(f"\n一次候補 {len(cands)} 件 → {OUT_PATH}")
for c in cands:
    au = " 🔨オークション" if c["auction"] else ""
    print(f"  {c['label']} ¥{c['price']:,} ({c['ratio']:.0%}) 状態{c['cond']} "
          f"{c['age_h']}h前 7日{c['w7_sold']}本{au} | {c['title'][:38]}")
if errors:
    print("失敗:", errors)
