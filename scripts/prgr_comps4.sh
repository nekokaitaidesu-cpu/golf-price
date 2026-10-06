#!/usr/bin/env bash
# PRGRアウトレット 第4バッチ: 高反発 SUPER egg を世代別に厚く測る（2026-10-06）
cd "$(dirname "$0")/.." || exit 1
run() {
  echo "##### $1 #####"
  timeout 250 python scripts/flea_comps.py "$2" --must "$3" --exclude "$4" --days 120 --limit 20 2>&1
  echo
}
run "SUPER egg DR 高反発(総)"  "プロギア SUPER egg 高反発 ドライバー"  "egg,高反発"        "アイアン,ユーティリティ,フェアウェイ,レディース,パター,バード"
run "SUPER egg DR 2022"       "プロギア SUPER egg ドライバー 2022"    "egg,ドライバー,2022" "アイアン,ユーティリティ,フェアウェイ,レディース,バード"
run "SUPER egg DR 2024"       "プロギア SUPER egg ドライバー 2024"    "egg,ドライバー,2024" "アイアン,ユーティリティ,フェアウェイ,レディース,バード"
run "SUPER egg FW 高反発"      "プロギア SUPER egg フェアウェイ 高反発" "egg,フェアウェイ"   "アイアン,ユーティリティ,ドライバー,レディース,バード"
run "egg SPOON"               "プロギア egg スプーン"                 "egg,スプーン"      "アイアン,ユーティリティ,ドライバー,レディース"
