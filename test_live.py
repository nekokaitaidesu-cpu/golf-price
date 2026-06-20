"""実データで名寄せ・グレード分類・集計を検証する。"""
import json
from golf_price import service
from golf_price.spec import MODELS, DEFAULT_MODEL_KEY
from golf_price.scrapers import rakuten
from golf_price.normalize import analyze

spec = MODELS[DEFAULT_MODEL_KEY]

# 生の検索結果のうち、何がマッチ/非マッチでどのグレードに分類されたか確認
raw = rakuten.search("キャロウェイ パラダイム Ai SMOKE ドライバー 中古", pages=2)
print(f"楽天 生取得: {len(raw)} 件\n")
matched = nonmatch = 0
for lst in raw:
    info = analyze(lst.title, spec)
    tag = info["grade_label"] if info["matched"] else "✗除外"
    if info["matched"]:
        matched += 1
    else:
        nonmatch += 1
    print(f"  ¥{lst.price:>7,} [{tag:<22}] {lst.title[:46]}")
print(f"\nマッチ {matched} / 除外 {nonmatch}\n")

print("=== 集計結果 ===")
result = service.run(pages=2)
print(json.dumps(result["headline"], ensure_ascii=False, indent=2))
print(f"総該当件数: {result['total_listings']}")
for g in result["grades"]:
    u = g["used"]
    print(f"  - {g['grade_label']:<24} 件数{u['count']:>3}  平均¥{u['avg']}  最安¥{u['min']}  (ヘッドのみ{g['head_only_count']})")
