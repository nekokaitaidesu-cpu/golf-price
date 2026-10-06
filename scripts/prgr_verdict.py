"""PRGRアウトレットの買い度判定（2026-10-06 測定）。

`prgr_outlet.py` が読むリストに、手で測ったメルカリ実売中央値を突き合わせて
1.30倍判定・粗利を出す。測定値は MARKET に直書き（再測定したら更新すること）。

使い方:
  python scripts/prgr_verdict.py > .cache/prgr_verdict.txt

測定方法: scripts/prgr_comps*.sh（120日・完品のみ・世代で分割）
"""
from __future__ import annotations

import io
import re
import sys

sys.path.insert(0, "scripts")
from prgr_outlet import load  # noqa: E402

SHIP = {"ドライバー": 1700, "フェアウエイ": 1700, "ユーティリティー": 1700,
        "アイアンセット": 1450, "単品アイアン": 1450, "単品ウエッジ": 1450,
        "ウエッジ": 1450, "単品": 1450, "ドライバー カスタムシャフト": 1700}

# (正規表現, ラベル, 実売中央, n, 備考)
# ⚠ 世代を分けずに測ると全部外れる。必ず年式・グレードで割った値を入れること。
MARKET = [
    (r"24 SUPER EGG DR",      "24 SUPER EGG DR(高反発)", 66900, 10, "個人のみだとn=2で58,500。新品なら70,000狙える"),
    (r"22 SUPER EGG DR",      "22 SUPER EGG DR(高反発)", 36825, 22, "個人のみだと中央28,800。新品なら35,000狙える"),
    (r"24 SUPER EGG FW",      "24 SUPER EGG FW(高反発)", 34223,  4, "n=4で薄い。販売中n=29中央31,760"),
    (r"22 SUPER EGG FW",      "22 SUPER EGG FW(高反発)", 13343, 16, "2017金eggが大半の混在値。22年単独はn=1"),
    (r"24 SUPER EGG UT",      "24 SUPER EGG UT(高反発)", 24570,  7, "販売中n=19中央25,200"),
    (r"EGG44 DR",             "21 EGG44 DR",            21000, 23, ""),
    (r"EGG SPOON",            "21 EGG SPOON",           10000, 19, ""),
    (r"24 RS FW #7",          "24 RS FW 7W",            24575, 16, ""),
    (r"22 RS FW #7",          "22 RS FW 7W",            16889,  4, "n=4で薄い"),
    (r"20 RS FW #7",          "20 RS FW 7W",            12304,  4, "n=4で薄い"),
    (r"21 LS LY FW #7",       "21 LS LY FW 7W(レディース)", 10470, 6, "120日でn=6＝月1.5本"),
    (r"23 LS LY FW #7",       "23 LS LY FW 7W(レディース)", 10470, 6, "7Wは年式で分けられずn=6"),
    (r"2[13] LS LY FW #4",    "LS LY FW 4W(レディース)",  9000,  9, ""),
    (r"21 LS LY UT",          "21 LS LY UT(レディース)", 11942, 21, "メンズLS UT 2021と同値で代用"),
    (r"23 LS LY UT",          "23 LS LY UT(レディース)", 15910, 40, "未使用の販売中が14,242で頭打ち"),
    (r"23 LS LY DR",          "23 LS LY DR(レディース)", 18000, 21, ""),
    (r"Q\d+ LADIES",          "Q LADIES(レディース)",     6500,  5, "n=5で薄い"),
    (r"21 LS UT",             "21 LS UT",               11942, 21, ""),
    (r"23 LS UT",             "23 LS UT",               15910, 40, ""),
    # SWEEP はレディースライン。実売 n=34 中央14,611（4,699〜29,401）の二層分布で、
    # 下half 4,699〜12,000 が旧M-10/M-12、上half 14,100〜29,401 が新しめ。
    # M-16 単独の実売は 11,000 が1件だけ。保守側（11,000）で評価する。
    (r"WOOD M15 SWEEP #1",    "SWEEP M15 DR(レディース)", 11000,  1, "⚠M-16の実売1件を代用。SWEEP DR全体ならn=34中央14,611"),
    (r"WOOD M16 SWEEP #1",    "SWEEP M16 DR(レディース)", 11000,  1, "⚠同上"),
    (r"WOOD M15 SWEEP #7",    "SWEEP M15 7W(レディース)",  8844,  6, "n=6で薄い"),
    (r"WOOD M16 SWEEP #7",    "SWEEP M16 7W(レディース)",  8844,  6, "n=6で薄い"),
    (r"WOOD UT M16 SWEEP",    "SWEEP UT(レディース)",      8844,  6, "FW7Wの値を代用。UT単独の実売なし"),
    (r"0[12] IRON.*#[56]-P",  "01/02 IRONセット",        38000, 77, ""),
    (r"05 IRON.*#7-A",        "05 IRONセット",           41047, 74, ""),
    (r"0[123] IRON.*#7-A",    "03 IRONセット",           38000, 77, ""),
    # ⚠ セットと単品を分ける。単品に「セットの中央値」を当てると1.71倍の偽物が出る
    (r"05 LY IRON CB-L #7-P", "05 LY IRONセット(レディース)", 10999, 39, "PRGRレディースアイアンセット全般の値"),
]


def match_market(name: str):
    for pat, label, med, n, note in MARKET:
        if re.search(pat, name):
            return label, med, n, note
    return None


def verdict(ratio: float, n: int) -> str:
    if n < 5:
        return "❓分母薄"
    if ratio >= 1.40:
        return "🔥買い"
    if ratio >= 1.30:
        return "⭕買い"
    if ratio >= 1.15:
        return "△薄い"
    return "❌見送り"


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    items = [d for d in load() if d["is_club"]]
    rows = []
    unmatched = []
    for d in items:
        m = match_market(d["name"])
        if not m:
            unmatched.append(d)
            continue
        label, med, n, note = m
        ship = SHIP.get(d["cat"], 1700)
        cost = d["sale_price"] + ship
        ratio = med / cost if cost else 0
        profit = med * 0.9 - ship - d["sale_price"]
        rows.append((ratio, profit, d, label, med, n, note))

    rows.sort(key=lambda r: -r[0])
    print("# PRGRアウトレット 買い度判定（市場=メルカリ120日実売中央・完品のみ）")
    print("# 倍率 = 実売中央 ÷ (セール価格 + 送料) ／ 1.30倍未満は原則見送り\n")
    print(f"{'判定':<6}{'倍率':>6} {'粗利':>8}  {'セール':>7} {'実売中央':>8} {'n':>4}  品目")
    print("-" * 110)
    for ratio, profit, d, label, med, n, note in rows:
        v = verdict(ratio, n)
        tag = "👩" if d["ladies"] else "  "
        print(
            f"{v:<6}{ratio:>5.2f}倍 {profit:>+8,.0f}  {d['sale_price']:>7,} "
            f"{med:>8,} {n:>4}  {tag}{d['name']:<30} 在庫{d['stock']:>3} [{label}]"
        )
        if note:
            print(f"{'':>30}└ {note}")

    print(f"\n--- 未測定 {len(unmatched)} 行（市場データなし） ---")
    seen = set()
    for d in unmatched:
        k = (d["brand"], re.sub(r"[\d.#]+", "", d["name"])[:24])
        if k in seen:
            continue
        seen.add(k)
        print(f"  {d['cat']:<10} {d['name']:<32} → {d['sale_price']:>6,} 在庫{d['stock']:>3}")


if __name__ == "__main__":
    main()
