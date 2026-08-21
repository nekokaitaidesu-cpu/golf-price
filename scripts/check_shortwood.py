# -*- coding: utf-8 -*-
"""ショートウッド(7W/9W)部門のマッチ条件を検査する（ネットワーク不要）。

`python scripts/check_shortwood.py` で全項目が PASS することを確認してから
catalog.py / service.py の変更を commit すること。クラウド集計も同じコードを使う。

検査する4つ:
  1. 退行検査 — 他カテゴリのキーが「自分の keyword に自分でマッチする」状態を
     壊していないか。**shortwood の種別語（ウッド/7w 等）はクラブ種別を特定しない語**
     なので、これを他カテゴリの除外条件に回すとドライバー等が巻き添えで落ちる
     （2026-08-21の導入時に実際にドライバー4件を落とす退行を出した）
  2. shortwood が 7W/9W だけを拾い、3W/5W・UT(21°のハイブリッド)・DRを拒否するか
  3. 既存FWキーが7W/9W出品を落としていないか（shortwood⇔fw の互換設定）
  4. 重複・包含（find_duplicates / find_swallowing）に shortwood 絡みが無いか
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.catalog import (CATALOG, CATALOG_BY_KEY, find_duplicates,
                                find_swallowing)
from golf_price.service import _catalog_match

# HEAD時点で既に自己マッチしないキーの数。大半はアイアン（keyword に本数が無く
# looks_like_iron_set を満たさないため自明に不一致）で、shortwood 導入とは無関係。
# **この数を増やしていないこと**だけを見る
SELF_MISMATCH_BASELINE = 278

fail = 0


def chk(title: str, key: str, want: bool) -> None:
    global fail
    got = _catalog_match(title, CATALOG_BY_KEY[key])
    ok = (got == want)
    if not ok:
        fail += 1
    print(f"  {'ok ' if ok else 'NG '} {key:<18} want={str(want):<5} "
          f"got={str(got):<5} | {title}")


print("== 1) 退行検査: 自分の keyword に自分がマッチするか（shortwood以外） ==")
bad = [m.key for m in CATALOG
       if m.category != "shortwood" and not _catalog_match(m.keyword, m)]
print(f"  自己マッチしないキー: {len(bad)}件（基準 {SELF_MISMATCH_BASELINE}件）")
if len(bad) > SELF_MISMATCH_BASELINE:
    others = [k for k in bad if not k.startswith(("ir_", "yt_iron"))]
    print(f"  ⚠ 退行 +{len(bad) - SELF_MISMATCH_BASELINE}件: {others[:15]}")
    fail += len(bad) - SELF_MISMATCH_BASELINE

print("\n== 2) 7W/9Wを拾い、3W/5W・UT・DRを拒否するか ==")
chk("ピン G425 MAX フェアウェイウッド 7W 20.5° スピーダーNX BLUE 60S", "sw_ping_g425", True)
chk("ピン G425 MAX 7W 20.5度 ヘッドカバー付", "sw_ping_g425", True)
chk("ピン G425 MAX フェアウェイウッド 3W 14.5°", "sw_ping_g425", False)
chk("ピン G425 MAX フェアウェイウッド 5W 18度", "sw_ping_g425", False)
chk("ピン G425 ハイブリッド 21° 3U", "sw_ping_g425", False)
chk("ピン G425 MAX ドライバー 10.5° ALTA", "sw_ping_g425", False)
chk("テーラーメイド ステルス2 フェアウェイウッド 7W 21度 TENSEI", "sw_tm_stealth2", True)
chk("テーラーメイド ステルス2 フェアウェイウッド 5W 18°", "sw_tm_stealth2", False)
chk("タイトリスト TSR2 フェアウェイウッド 9W 23.5度", "sw_ti_tsr2", True)
chk("タイトリスト TSR2 フェアウェイウッド W7 ディアマナ", "sw_ti_tsr2", True)
chk("キャロウェイ パラダイム フェアウェイウッド 7番ウッド", "sw_cw_paradym", True)
chk("キャロウェイ ローグST MAX フェアウェイウッド 9W 24度", "sw_cw_roguest", True)
chk("タイトリスト GT2 フェアウェイウッド 7W 20.5", "sw_ti_gt2", True)
chk("タイトリスト GT250 フェアウェイウッド 7W", "sw_ti_gt2", False)

print("  -- 数字の食い込み誤ヒット（17W が 7W に、121度 が 21度 に）--")
chk("テーラーメイド M2 フェアウェイウッド 17W", "sw_tm_m2", False)
chk("ピン G430 フェアウェイウッド 3W 121度", "sw_ping_g430", False)

print("  -- 複数本セットの除外（1本あたり相場を壊すため）--")
chk("ピン G430 フェアウェイウッド 3W 5W 7W 3本セット", "sw_ping_g430", False)
# 2026-08-21の初回集計で中央値を70,000に化けさせた実物の形
chk("nob様専用 名器！G425フェアウェイウッド5w.7w.9wセット", "sw_ping_g425", False)
chk("ace19様【美品　未使用】ヘッドカバー 5W、7W パラダイム", "sw_cw_paradym", False)

print("  -- 兄弟モデルの分離 --")
chk("キャロウェイ パラダイム Ai SMOKE フェアウェイウッド 7W", "sw_cw_paradym", False)
chk("Callaway PARADYM X フェアウェイウッド 7W VENTUS", "sw_cw_paradym", False)
chk("Callaway PARADYM MAX FAST 7W 22度", "sw_cw_paradym", False)
# 裸の "x" で除外するとシャフトのXフレックスまで巻き込むので型名で除外している
chk("Callaway PARADYM 7W 21° VENTUS TR BLUE 6X", "sw_cw_paradym", True)
chk("PING G430 LST フェアウェイウッド 7W 21度", "sw_ping_g430", False)

print("\n== 3) 既存FWキーが7W/9Wを落としていないか ==")
chk("ピン G425 MAX フェアウェイウッド 7W 20.5° スピーダーNX", "fw_ping_g425max", True)
chk("ピン G425 MAX フェアウェイウッド 3W 14.5°", "fw_ping_g425max", True)
chk("テーラーメイド ステルス2 フェアウェイウッド 7W 21度", "fw_tm_stealth2", True)
chk("キャロウェイ Paradym フェアウェイウッド 9W 24度", "fw_cw_paradym", True)

print("  -- 他カテゴリが shortwood の語（ウッド/7w）で汚染されていないか --")
for cat, extra in (("driver", " ウッド"), ("driver", " 7W"),
                   ("ut", " ウッド"), ("iron", " wood")):
    m = next((x for x in CATALOG
              if x.category == cat and _catalog_match(x.keyword, x)), None)
    if m:
        chk(m.keyword + extra, m.key, True)

print("\n== 4) 重複・包含 ==")
dups = [g for g in find_duplicates() if any(k.startswith("sw_") for k in g)]
swal = [p for p in find_swallowing() if any(k.startswith("sw_") for k in p)]
print(f"  shortwood絡みの完全重複 {len(dups)}組 {dups}")
print(f"  shortwood絡みの包含関係 {len(swal)}対 {swal}")
fail += len(dups) + len(swal)

n_sw = sum(1 for m in CATALOG if m.category == "shortwood")
print(f"\n全{len(CATALOG)}機種 / shortwood {n_sw}機種")
print("RESULT:", "PASS" if fail == 0 else f"FAIL ({fail})")
sys.exit(1 if fail else 0)
