#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
run() { echo "##### $1 #####"; timeout 250 python scripts/flea_comps.py "$2" --must "$3" --exclude "$4" --days 120 --limit 16 2>&1; echo; }
run "SUPER egg FW 2024"  "プロギア SUPER egg フェアウェイ 2024"  "egg,フェアウェイ,2024" "ドライバー,アイアン,ユーティリティ,レディース"
run "SUPER egg UT 2024"  "プロギア SUPER egg ユーティリティ 2024" "egg,2024"            "ドライバー,アイアン,フェアウェイ,レディース"
run "SUPER egg UT 総"    "プロギア SUPER egg ユーティリティ 高反発" "egg,ユーティリティ"   "ドライバー,アイアン,フェアウェイ,レディース"
run "egg SPOON BLACK"    "プロギア egg スプーン ブラック"          "egg,スプーン"        "アイアン,ドライバー,レディース"
run "EGG44 ドライバー"    "プロギア egg44 ドライバー"               "egg44"              "アイアン,フェアウェイ,ユーティリティ"
