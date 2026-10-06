#!/usr/bin/env bash
# PRGRアウトレット候補の市場照合バッチ（2026-10-06作成）
# 使い方: bash scripts/prgr_comps.sh > .cache/prgr_comps.txt 2>&1
# 各行: ラベル | 検索語 | must | exclude
cd "$(dirname "$0")/.." || exit 1

run() {
  local label="$1" kw="$2" must="$3" exc="$4"
  echo "##### ${label} #####"
  if [ -n "$exc" ]; then
    timeout 250 python scripts/flea_comps.py "$kw" --must "$must" --exclude "$exc" --days 120 --limit 10 2>&1
  else
    timeout 250 python scripts/flea_comps.py "$kw" --must "$must" --days 120 --limit 10 2>&1
  fi
  echo
}

# ---- レディース（ユーザーの注目枠） ----
run "LS LY FW 7W (レディース)"      "プロギア LS レディース 7W フェアウェイ"      "ls,7w"        "ドライバー,ユーティリティ,アイアン,パター"
run "LS LY FW 4W (レディース)"      "プロギア LS レディース 4W フェアウェイ"      "ls,4w"        "ドライバー,ユーティリティ,アイアン,パター"
run "LS LY UT (レディース)"         "プロギア LS レディース ユーティリティ"        "ls,レディ"     "ドライバー,フェアウェイ,アイアン,パター,FW"
run "LS LY DR (レディース)"         "プロギア LS レディース ドライバー"            "ls,ドライバー"  "フェアウェイ,ユーティリティ,アイアン,パター"
run "Q LADIES FW"                  "プロギア Q レディース フェアウェイウッド"       "prgr,レディ"   "ドライバー,アイアン,パター"
run "PRGR レディース 全般(参考)"     "プロギア レディース ゴルフクラブ"             "prgr,レディ"   "パター,バッグ,グローブ"

# ---- 7W（メンズ） ----
run "RS FW 7W"                     "プロギア RS フェアウェイウッド 7W"            "rs,7w"        "レディース,ドライバー,ユーティリティ,アイアン"
run "SWEEP FW 7W"                  "プロギア SWEEP 7W フェアウェイ"               "sweep,7w"     "ドライバー,アイアン,パター"

# ---- 高額・高割引のメンズ枠（念のため） ----
run "SUPER EGG DR (2024)"          "プロギア スーパーエッグ ドライバー"            "egg,ドライバー" "アイアン,ユーティリティ,フェアウェイ,レディース"
run "RS DR 2024"                   "プロギア RS ドライバー 2024"                  "rs,ドライバー"  "レディース,フェアウェイ,ユーティリティ,アイアン,RSF,LS"
run "LS UT (メンズ)"               "プロギア LS ユーティリティ"                   "ls,ユーティリティ" "レディース,ドライバー,フェアウェイ,アイアン"
run "SWEEP DR"                     "プロギア SWEEP ドライバー"                    "sweep,ドライバー" "アイアン,パター,フェアウェイ"
run "01 IRON (アイアンセット)"      "プロギア 01 アイアン セット"                  "prgr,01"      "単品,ウェッジ,ドライバー,パター"
run "05 IRON (アイアンセット)"      "プロギア 05 アイアン セット"                  "prgr,05"      "単品,ウェッジ,ドライバー,パター"
