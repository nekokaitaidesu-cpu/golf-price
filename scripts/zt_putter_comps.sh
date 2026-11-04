#!/usr/bin/env bash
# ゼロトルク系パター追加候補の実売測定（2026-11-04）
cd "$(dirname "$0")/.." || exit 1
X="カバーのみ,カバー単品,ヘッドカバー,グリップのみ,レフティ,左用"
run() { echo "##### $1 #####"; timeout 250 python scripts/flea_comps.py "$2" --must "$3" --exclude "$4" --days 120 --limit 10 2>&1; echo; }
run "LAB Mezz.1 MAX"   "LAB GOLF Mezz.1 MAX パター" "mezz1" "$X"
run "LAB Mezz.2"       "LAB GOLF Mezz.2 パター" "mezz2" "$X"
run "LAB DF2.1"        "LAB GOLF DF2.1 パター" "df2" "$X"
run "LAB DF3"          "LAB GOLF DF3 パター" "df3" "$X,df3i"
run "LAB DF3i"         "LAB GOLF DF3i パター" "df3i" "$X"
run "LAB LINK.1"       "LAB GOLF LINK.1 パター" "link1" "$X"
run "LAB LINK.2"       "LAB GOLF LINK.2 パター" "link2" "$X"
run "LAB OZ.1"         "LAB GOLF OZ.1 パター" "oz1" "$X"
run "LAB VZN"          "LAB GOLF VZN パター" "vzn" "$X"
run "S2S ジェイルバード" "オデッセイ スクエア2スクエア ジェイルバード パター" "ジェイルバード" "$X,mini,ミニ,cruiser,クルーザー"
run "S2S JAILBIRD 英"  "odyssey square 2 square jailbird putter" "jailbird" "$X,mini,ミニ,cruiser,クルーザー"
run "S2S ミニ"         "オデッセイ ジェイルバード ミニ パター" "ジェイルバード,ミニ" "$X"
run "S2S クルーザー"   "オデッセイ ジェイルバード クルーザー パター" "クルーザー" "$X"
run "S2S Ai-DUAL"      "オデッセイ Ai-DUAL スクエア2スクエア パター" "dual" "$X"
run "S2S トライホット" "オデッセイ スクエア2スクエア トライホット パター" "トライホット,スクエア" "$X"
run "S2S 総称"         "オデッセイ スクエア2スクエア パター" "スクエア" "$X"
run "Spider ZT"        "テーラーメイド スパイダー ZT パター" "zt" "$X,max,マックス"
run "Spider ZT MAX"    "テーラーメイド スパイダー ZT MAX パター" "zt,max" "$X"
# --- 他社の参考枠（ゼロ/ロートルク） ---
run "Cameron OC"       "スコッティキャメロン OC パター" "oc" "$X"
run "PING Ally Blue Onset" "PING PLD ALLY BLUE パター" "ally" "$X"
run "Bettinardi Antidote" "ベティナルディ アンチドート パター" "ベティナルディ" "$X"
run "Evnroll ZERO"     "Evnroll ZERO パター" "evnroll" "$X"
