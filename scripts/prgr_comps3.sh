#!/usr/bin/env bash
# PRGRアウトレット 第3バッチ: SUPER EGG を厚く測る＋新品プレミアムの実測（2026-10-06）
# 使い方: bash scripts/prgr_comps3.sh > .cache/prgr_comps3.txt 2>&1
cd "$(dirname "$0")/.." || exit 1

run() {
  local label="$1" kw="$2" must="$3" exc="$4"
  echo "##### ${label} #####"
  timeout 250 python scripts/flea_comps.py "$kw" --must "$must" --exclude "$exc" --days 120 --limit 16 2>&1
  echo
}

# ---- SUPER EGG を表記ゆれ込みで厚く ----
run "スーパーエッグ DR(カナ)"   "プロギア スーパーエッグ ドライバー"   "スーパーエッグ,ドライバー" "アイアン,ユーティリティ,フェアウェイ,レディース,パター"
run "SUPER EGG DR(英字)"       "PRGR SUPER EGG ドライバー"          "superegg,ドライバー"      "アイアン,ユーティリティ,フェアウェイ,レディース,パター"
run "egg DR 総当たり"          "プロギア egg ドライバー 高反発"      "egg,ドライバー"           "アイアン,ユーティリティ,フェアウェイ,レディース,パター,バード"
run "スーパーエッグ UT(カナ)"   "プロギア スーパーエッグ ユーティリティ" "スーパーエッグ,ユーティリティ" "アイアン,ドライバー,フェアウェイ,レディース"
run "SUPER EGG UT(英字)"       "PRGR SUPER EGG UT"                  "superegg,ut"              "アイアン,ドライバー,フェアウェイ,レディース"

# ---- 新品プレミアムの実測（同一ライン内で 新品 vs 全体 を比べる） ----
run "RS FW 新品・未使用"       "プロギア RS フェアウェイ 新品 未使用" "rs,フェアウェイ"          "レディース,ドライバー,ユーティリティ,アイアン,中古"
run "RS ドライバー 新品・未使用" "プロギア RS ドライバー 新品 未使用"   "rs,ドライバー,新品"       "レディース,フェアウェイ,ユーティリティ,アイアン"
run "LS 新品・未使用"          "プロギア LS 新品 未使用"              "ls,新品"                  "パター,バッグ,グローブ"
