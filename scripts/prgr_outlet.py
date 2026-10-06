"""PRGR関係者向けアウトレットリスト（新品）の棚卸しと買い度判定。

2026-10-06 にユーザーが入手した `PRGR_商品リスト.xlsx` を読み、
カテゴリ・レディース/メンズ・番手を正規化して一覧する。

使い方:
  python scripts/prgr_outlet.py              # 全体サマリ
  python scripts/prgr_outlet.py --ladies     # レディースのみ
  python scripts/prgr_outlet.py --fw7        # 7W/9W のみ
  python scripts/prgr_outlet.py --cat ドライバー
  python scripts/prgr_outlet.py --models     # 市場照合すべき「機種」単位に畳む

出力は常に UTF-8 で stdout。Windows のコンソールが cp932 のときは
`python scripts/prgr_outlet.py > out.txt` してファイルで読むこと。
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from collections import Counter, defaultdict

import openpyxl

XLSX = "PRGR_商品リスト.xlsx"

# クラブ本体のカテゴリ（グローブ・カバー・バッグ等の小物は除く）
# ⚠ この表のカテゴリは「フェアウエイ」「単品ウエッジ」と**大きいエ**で書かれている。
#   2026-10-06に「フェアウェイ」で書いて77行を丸ごと取りこぼした。
CLUB_CATS = {
    "ドライバー",
    "フェアウエイ",
    "ユーティリティー",
    "アイアンセット",
    "単品アイアン",
    "単品ウエッジ",
    "ウエッジ",
    "単品",
    "ドライバー カスタムシャフト",
}

# 品目名に出るレディースの印
LADIES_PAT = re.compile(r"(?:\bL\b|LADIES|LADY|レディ|女性|WOMEN|\bA\b(?=\s|$))", re.I)
# PRGRの品目名は「… #1 10.5 L」のように末尾がフレックス。L/A はレディース系
FLEX_TAIL = re.compile(r"\s(SR|S|R|A|L|X|M37|M40|M43|M46)\s*$", re.I)


def norm(s) -> str:
    return "" if s is None else str(s).strip()


def parse_flex(name: str) -> str:
    m = FLEX_TAIL.search(name)
    return m.group(1).upper() if m else ""


def is_ladies(row) -> bool:
    brand = norm(row["brand"])
    name = norm(row["name"])
    if "レディス" in brand or "レディース" in brand:
        return True
    # SWEEP は PRGR のレディース専用ライン（2026-10-06に見落として判明）。
    # 実売も題名の9割が「SWEEP レディース ドライバー」。PI＝ピンクも女性向けの色。
    if "SWEEP" in brand.upper() or "SWEEP" in name.upper():
        return True
    # LY は LADY の略（21 LS LY FW など）
    if re.search(r"\bLY\b", name):
        return True
    # フレックス L / A はレディース・シニア向け
    if parse_flex(name) in ("L", "A"):
        return True
    return bool(re.search(r"レディ|LADIES", name, re.I))


def parse_club_no(name: str) -> str:
    """#3 / #5 / #7 / U4 / 7W のような番手を拾う。"""
    m = re.search(r"#\s*(\d+)", name)
    if m:
        return f"#{m.group(1)}"
    m = re.search(r"\bU\s*(\d+)", name, re.I)
    if m:
        return f"U{m.group(1)}"
    m = re.search(r"\b(\d+)\s*W\b", name, re.I)
    if m:
        return f"#{m.group(1)}"
    return ""


def parse_loft(name: str) -> str:
    m = re.search(r"#\s*\d+\s+(\d+(?:\.\d+)?)", name)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{2}(?:\.\d)?)\s*(?:度|°)", name)
    return m.group(1) if m else ""


def load(path: str = XLSX) -> list[dict]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    out = []
    for r in rows[1:]:
        if not r[1]:
            continue
        d = {
            "code": norm(r[1]),
            "cat": norm(r[2]),
            "brand": norm(r[3]),
            "name": norm(r[4]),
            "point": norm(r[5]),
            "list_price": r[6] or 0,
            "sale_price": r[7] or 0,
            "stock": r[8] or 0,
            "url": norm(r[11]),
            "hc_note": norm(r[12]),
        }
        d["flex"] = parse_flex(d["name"])
        d["ladies"] = is_ladies(d)
        d["no"] = parse_club_no(d["name"])
        d["loft"] = parse_loft(d["name"])
        d["is_club"] = d["cat"] in CLUB_CATS
        d["off"] = (
            1 - d["sale_price"] / d["list_price"] if d["list_price"] else 0
        )
        out.append(d)
    return out


def fmt(d: dict) -> str:
    tag = "👩L" if d["ladies"] else "  "
    return (
        f"{tag} {d['cat']:<10} {d['brand']:<14} {d['name']:<34} "
        f"定価{d['list_price']:>7,} → セール{d['sale_price']:>7,} "
        f"({d['off']*100:>3.0f}%off) 在庫{d['stock']:>3}"
    )


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladies", action="store_true")
    ap.add_argument("--fw7", action="store_true", help="7W/9W 相当のみ")
    ap.add_argument("--cat")
    ap.add_argument("--models", action="store_true")
    ap.add_argument("--all", action="store_true", help="小物も含める")
    args = ap.parse_args()

    items = load()
    clubs = [d for d in items if d["is_club"] or args.all]

    if args.cat:
        clubs = [d for d in clubs if d["cat"] == args.cat]
    if args.ladies:
        clubs = [d for d in clubs if d["ladies"]]
    if args.fw7:
        clubs = [d for d in clubs if d["no"] in ("#7", "#9")]

    if args.models:
        # 「カテゴリ＋ブランド＋品目名から番手/フレックスを除いた部分」で畳む
        g: dict[tuple, list[dict]] = defaultdict(list)
        for d in clubs:
            base = FLEX_TAIL.sub("", d["name"]).strip()
            base = re.sub(r"#\s*\d+\s*[\d.]*\s*$", "", base).strip()
            g[(d["cat"], d["brand"], base)].append(d)
        print(f"# 機種単位 {len(g)} 件（明細 {len(clubs)} 行）\n")
        for (cat, brand, base), ds in sorted(
            g.items(), key=lambda kv: -sum(x["stock"] for x in kv[1])
        ):
            lo = min(x["sale_price"] for x in ds)
            hi = max(x["sale_price"] for x in ds)
            lp = max(x["list_price"] for x in ds)
            stock = sum(x["stock"] for x in ds)
            nl = sum(1 for x in ds if x["ladies"])
            price = f"{lo:,}" if lo == hi else f"{lo:,}〜{hi:,}"
            print(
                f"{cat:<10} {brand:<14} {base:<30} 定価{lp:>7,} → {price:>15} "
                f"／明細{len(ds):>2}行 在庫計{stock:>3} レディース{nl:>2}"
            )
        return

    print(f"# 該当 {len(clubs)} 行 / 在庫計 {sum(d['stock'] for d in clubs)}\n")
    for d in sorted(clubs, key=lambda x: (x["cat"], x["brand"], x["name"])):
        print(fmt(d))

    print("\n--- カテゴリ別 ---")
    c = Counter(d["cat"] for d in clubs)
    for k, v in c.most_common():
        sub = [d for d in clubs if d["cat"] == k]
        print(
            f"  {k:<12} {v:>3}行 在庫{sum(d['stock'] for d in sub):>4} "
            f"レディース{sum(1 for d in sub if d['ladies']):>3}行"
        )


if __name__ == "__main__":
    main()
