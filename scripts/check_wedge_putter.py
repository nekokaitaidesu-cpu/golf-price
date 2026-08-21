# -*- coding: utf-8 -*-
"""ウェッジ・パター部門のマッチ条件と部品検出を検査する（ネットワーク不要）。

`python scripts/check_wedge_putter.py` が PASS することを確認してから
catalog.py / service.py / normalize.py の変更を commit すること。

背景（2026-08-22の新設時に踏んだ地雷）:
  ・**パターはカバー単品それ自体が2,000〜25,000円で売買される市場**。
    スペシャルセレクトは実売20件中12件が「パターカバー」で、中央値が
    4,250円（完品の実勢は23,000〜32,000）に化けていた
  ・`_JUNK_TOKENS` の **"ネック"** がパターの形状名（ツイストネック/クランクネック/
    スラントネック/ロングネック/溶接ネック）を全部落としていた。実測1,651件で
    「ネック」を含む題名9件は**すべて完品**（7,500〜222,000円）で部品は0件
  ・`_ALWAYS_EXCLUDE_CLUB` がウェッジ・パターを全カテゴリから弾いていたので、
    CLUB_TOKENS に移して通常のカテゴリ間相互除外に任せた
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.catalog import (CATALOG, CATALOG_BY_KEY, find_duplicates,
                                find_swallowing)
from golf_price.normalize import is_parts_junk
from golf_price.service import _catalog_match

SELF_MISMATCH_BASELINE = 278
fail = 0


def chk(title: str, key: str, want: bool) -> None:
    global fail
    got = _catalog_match(title, CATALOG_BY_KEY[key])
    if got != want:
        fail += 1
    print(f"  {'ok ' if got == want else 'NG '} {key:<20} want={str(want):<5} "
          f"got={str(got):<5} | {title}")


def junk(title: str, want: bool) -> None:
    global fail
    got = is_parts_junk(title)
    if got != want:
        fail += 1
    print(f"  {'ok ' if got == want else 'NG '} 部品={str(want):<5} "
          f"got={str(got):<5} | {title}")


print("== 1) 退行検査: 自分の keyword に自分がマッチするか ==")
bad = [m.key for m in CATALOG
       if m.category not in ("shortwood",) and not _catalog_match(m.keyword, m)]
print(f"  自己マッチしないキー: {len(bad)}件（基準 {SELF_MISMATCH_BASELINE}件）")
if len(bad) > SELF_MISMATCH_BASELINE:
    others = [k for k in bad if not k.startswith(("ir_", "yt_iron"))]
    print(f"  ⚠ 退行 +{len(bad) - SELF_MISMATCH_BASELINE}件: {others[:15]}")
    fail += len(bad) - SELF_MISMATCH_BASELINE

print("\n== 2) 部品検出: パターのカバー・グリップ単品を落とすか ==")
junk("Scotty Cameron Special Select パターカバー", True)
junk("SCOTTY CAMERON パター用ヘッドカバー Special SELECT", True)
junk("TaylorMade Spider パター用 純正ヘッドカバー 美品", True)
junk("Scotty Cameron パターカバー スコッティーズスピードショップ", True)
junk("BETTINARDI パターグリップ　ベティナルディ　新品　ラムキン　ブラック", True)
junk("Callaway エクスクルージブ限定　ウェッジ用ヘッドカバー 3個セット新品", True)
print("  -- 完品を巻き込んでいないか（誤検出側）--")
junk("TaylorMade Spider パター カバー付き", False)
junk("ODYSSEY TRIPLE TRACK 2-BALL パター　ヘッドカバー有り", False)
junk("PING SIGMA 2 ANSER パター ヘッドカバー付き　32インチ", False)
junk("ODYSSEY Tri HOT パター 本体 カバー付", False)
junk("スコッティキャメロン ニューポート2 パター カバーなし", False)
junk("Odyssey EXO SEVEN パター　34インチ オデッセイヘッドカバー", False)

print("\n  -- 『ネック』はパターの形状名（完品を落とさない）--")
junk("スコッティキャメロン スタジオセレクト ニューポート2 ツイストネック", False)
junk("GSS ツアー支給品 SPIDER TOUR X BLACK クランクネック", False)
junk("レア限定　ベティナルディ　INOVAl 6.5 スパッドネックパター", False)
junk("スコッティキャメロン セレクト チェリーボンブ ブラックボロン 溶接ネック", False)
print("  -- ただし部品を指す形は落とす --")
junk("ドライバー用 ネックのみ スリーブ", True)
junk("ホーゼル単品 パーツ", True)

print("\n== 3) ウェッジ・パターのキーが正しく絞れるか ==")
chk("タイトリスト ボーケイ SM10 ウェッジ 56度 12バウンス", "wg_ti_sm10", True)
chk("タイトリスト ボーケイ SM9 ウェッジ 58度", "wg_ti_sm10", False)
chk("クリーブランド RTX6 ZipCore ウェッジ 60度", "wg_cl_rtx6", True)
chk("ピン s159 ウェッジ 54度 SS", "wg_ping_s159", True)
chk("テーラーメイド ミルドグラインド4 ウェッジ 56度", "wg_tm_mg4", True)
chk("タイトリスト ボーケイ SM10 ウェッジ 52度 56度 2本セット", "wg_ti_sm10", False)
chk("スコッティキャメロン スペシャルセレクト ニューポート2 パター 34インチ",
    "pt_sc_specialselect", True)
chk("スコッティキャメロン ファントムX 5.5 パター 34インチ", "pt_sc_phantomx", True)
chk("スコッティキャメロン ファントムX 5.5 パター 34インチ", "pt_sc_phantom", False)
chk("TaylorMade Spider TOUR パター 34インチ", "pt_tm_spidertour", True)
chk("TaylorMade Spider GT パター 33インチ", "pt_tm_spidergt", True)
chk("L.A.B. GOLF DF3 パター 34インチ カバー付", "pt_lab_df3", True)
chk("PING PLD Milled アンサー2 パター 34インチ", "pt_ping_pld", True)
print("  -- ニューポートはライン名を持つ個体を二重計上しない --")
chk("スコッティキャメロン スペシャルセレクト ニューポート2 パター", "pt_sc_newport", False)
chk("スコッティキャメロン ニューポート2 パター 35インチ", "pt_sc_newport", True)

print("\n== 4) 他カテゴリとの相互除外 ==")
chk("タイトリスト ボーケイ SM10 ウェッジ 56度", "pt_sc_newport", False)
chk("スコッティキャメロン ニューポート2 パター", "wg_ti_sm10", False)
print("  -- ウェッジ/パター語で他カテゴリが汚染されていないか --")
for cat in ("driver", "fw", "ut", "iron"):
    m = next((x for x in CATALOG
              if x.category == cat and _catalog_match(x.keyword, x)), None)
    if m:
        chk(m.keyword, m.key, True)
        chk(m.keyword + " パター", m.key, False)

print("\n== 5) 重複・包含 ==")
NEW = ("wg_", "pt_")
dups = [g for g in find_duplicates() if any(k.startswith(NEW) for k in g)]
swal = [p for p in find_swallowing() if any(k.startswith(NEW) for k in p)]
print(f"  新カテゴリ絡みの完全重複 {len(dups)}組 {dups}")
print(f"  新カテゴリ絡みの包含関係 {len(swal)}対 {swal}")
fail += len(dups) + len(swal)

nw = sum(1 for m in CATALOG if m.category == "wedge")
np_ = sum(1 for m in CATALOG if m.category == "putter")
print(f"\n全{len(CATALOG)}機種 / ウェッジ {nw}機種 / パター {np_}機種")
print("RESULT:", "PASS" if fail == 0 else f"FAIL ({fail})")
sys.exit(1 if fail else 0)
