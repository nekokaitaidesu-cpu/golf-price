# -*- coding: utf-8 -*-
"""候補を推奨する前に、その「実売中央値」が何でできているかを一覧で見る。

  python scripts/denominator_check.py pt_tm_spidertourx
  python scripts/denominator_check.py yt_ut_tsi2 fw_ping_g425max --days 120

**推奨してから汚染に気づく、を止めるための手順**（2026-08-24にユーザーが
購入ワンタップ手前まで行った反省）。3日で分母を3回間違えた:
  8/23 スパイダー無印 … 世代混在（RED/PLATINUM 8,000〜15,500 と TM1/TM2 19,900〜33,000）
  8/23 トゥーロン ……… 都市名ごとにヘッド形状が別物（18,250〜33,000）
  8/24 スパイダーX …… TORCHED（限定カラー 38,000〜60,000）が中央値を2,000円押し上げ

分母汚染は6つの型がある。この検査はそれを機械的に当てる:
  ①ヘッド単品  ②世代混在  ③番手混在  ④カバー/グリップ単品
  ⑤本数混在   ⑥限定カラー・特別仕様（パター特有）

出力の読み方:
  ・「フラグ別の中央値」を見て、**フラグ有無で中央値が大きく動く**なら汚染。
    その機種は mixed_median にするか、条件を分けるべき
  ・変種トークン別の内訳で n=1〜2 しかない層があれば、**その層は中央値を語れない**
"""
import argparse
import os
import re
import statistics
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.catalog import CATALOG_BY_KEY
from golf_price.normalize import looks_like_multi_set, normalize
from golf_price import popularity
from golf_price.scrapers import mercari

# ⑥限定カラー・特別仕様（見つかった順に足していく）
_SPECIAL = re.compile(
    r"torched|トーチド|限定|limited|マキロイ|プロト|proto|newモデル|新モデル"
    r"|カスタムショップ|customshop|ツアー支給|tour ?issue|サークルt|circlet"
    r"|ガレージ|garage|記念|別注", re.I)
# ③番手・長さの軸（ウッド/UTは番手、パターはインチ、アイアンは本数）
# 2026-08-26の教訓: **アイアンは本数で価格が階段状に上がる**。
# UD+2で 5本37,250 / 6本35,000 / 7本52,000 / 8本61,190 と大きく違い、
# 本数を揃えずに「6本の想定売値28,000〜32,000」と誤って見積もった
# （実際の6本中央は35,000で、逃した案件は1.72倍・+13,260の好条件だった）
_NUM = re.compile(r"(?<![0-9a-z])([3-9]|1[01])\s*[wWuUhH](?![0-9a-z])"
                  r"|(?<![0-9])(3[0-9])\s*(インチ|inch|㌅)"
                  r"|(?<![0-9])([4-9]|1[0-2])\s*本")
# ②世代・変種を示しやすいトークン（機種によって意味が変わるので参考表示）
_VARIANT = re.compile(
    r"(tm[12]|truss|トラス|myspider|マイスパイダー|x7|トゥルーパス|truepath"
    r"|red|black|platinum|レッド|ブラック|プラチナ"
    r"|20[12][0-9]年?|max|ls|sft|hl|tour|ツアー)", re.I)


def bucket_median(rows, pred):
    a = [r["price"] for r in rows if pred(r)]
    b = [r["price"] for r in rows if not pred(r)]
    return (statistics.median(a) if a else None, len(a),
            statistics.median(b) if b else None, len(b))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="+")
    ap.add_argument("--days", type=int, default=120)
    args = ap.parse_args()

    for key in args.keys:
        m = CATALOG_BY_KEY.get(key)
        if not m:
            print(f"{key}: カタログに無いキー", file=sys.stderr)
            continue
        since = time.time() - args.days * 86400
        raw, _ = mercari.search_recent_raw(m.keyword, "STATUS_SOLD_OUT",
                                           price_min=popularity.MIN_PRICE,
                                           max_pages=4, stop_before=since)
        got = popularity._pick(raw, m, popularity.MIN_PRICE, since)
        if not got:
            print(f"\n### {key} — 実売0件")
            continue

        print(f"\n{'='*78}\n### {key} — {m.brand} {m.label}"
              f"（{args.days}日 / 実売{len(got)}件）\n{'='*78}")
        ps = [r["price"] for r in got]
        print(f"  全体中央 {statistics.median(ps):>8,.0f}  "
              f"範囲 {min(ps):,}〜{max(ps):,}  "
              f"最大/最小 = {max(ps)/max(1,min(ps)):.1f}倍")
        if max(ps) / max(1, min(ps)) >= 3:
            print("  ⚠ 最大が最小の3倍以上。単一集団でない可能性が高い")

        # ---- 6つの汚染型を当てる ----
        checks = [
            ("①ヘッド単品", lambda r: r["head_only"]),
            ("④カバー/グリップ", lambda r: bool(re.search(
                r"カバー|グリップ", normalize(r["title"])))),
            ("⑤本数混在", lambda r: looks_like_multi_set(r["title"])),
            ("⑥限定・特別仕様", lambda r: bool(_SPECIAL.search(r["title"]))),
        ]
        print(f"\n  {'汚染型':<18}{'該当':>4}{'該当の中央':>11}"
              f"{'残りの中央':>11}{'差':>9}")
        for name, pred in checks:
            ma, na, mb, nb = bucket_median(got, pred)
            if not na:
                print(f"  {name:<18}{0:>4}{'—':>11}{(mb or 0):>11,.0f}{'—':>9}")
                continue
            diff = (ma - mb) if (ma and mb) else 0
            warn = "  ⚠" if (mb and abs(diff) >= mb * 0.12) else ""
            print(f"  {name:<18}{na:>4}{ma:>11,.0f}{(mb or 0):>11,.0f}"
                  f"{diff:>+9,.0f}{warn}")

        # ---- ③番手/長さ別 ----
        by = defaultdict(list)
        for r in got:
            mm = _NUM.search(normalize(r["title"]))
            by[(mm.group(0).strip() if mm else "（表記なし）")].append(r["price"])
        if len(by) > 1:
            print("\n  ③番手・長さ別")
            for k in sorted(by, key=lambda z: -len(by[z])):
                v = by[k]
                print(f"    {k:<12} n={len(v):>2} 中央{statistics.median(v):>8,.0f}"
                      f"  {min(v):,}〜{max(v):,}"
                      f"{'   ← n<3で中央値は語れない' if len(v) < 3 else ''}")

        # ---- ②変種トークン別 ----
        vb = defaultdict(list)
        for r in got:
            hits = set(x.group(0).lower() for x in _VARIANT.finditer(r["title"]))
            vb[("+".join(sorted(hits)) if hits else "（記載なし）")].append(r["price"])
        top = sorted(vb.items(), key=lambda z: -len(z[1]))[:8]
        if len(vb) > 1:
            print("\n  ②変種トークン別（上位8）")
            for k, v in top:
                print(f"    {k[:34]:<36} n={len(v):>2} "
                      f"中央{statistics.median(v):>8,.0f}"
                      f"{'   ← n<3' if len(v) < 3 else ''}")

        print("\n  --- 実売 全件（安い順）---")
        for r in sorted(got, key=lambda z: z["price"]):
            tags = []
            if r["head_only"]:
                tags.append("頭")
            if looks_like_multi_set(r["title"]):
                tags.append("複数")
            if _SPECIAL.search(r["title"]):
                tags.append("限定")
            t = ("[" + "/".join(tags) + "]") if tags else "    "
            print(f"    ¥{r['price']:>7,} {t:<10} {r['title'][:52]}")


if __name__ == "__main__":
    main()
