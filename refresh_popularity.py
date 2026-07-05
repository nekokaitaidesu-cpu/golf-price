"""メルカリ人気ランキングの一括集計 → .cache/popularity.json

カタログ全機種について「直近30日にメルカリへ出品された当該機種」を
売り切れ・販売中の両方から集計し、人気順ランキングのデータを書き出す。
表示は PC版 http://localhost:8000/popularity ／ スマホ版 popularity.html。

使い方:
  python refresh_popularity.py                      # 全機種（約30〜60分）
  python refresh_popularity.py --category driver    # ドライバーのみ
  python refresh_popularity.py --limit 10           # 先頭10機種（テスト）
  python refresh_popularity.py --keys tm_qi10,tm_stealth
環境変数 MODEL_LIMIT=N でも件数制限できる（GitHub Actionsのテスト用）。
"""

import argparse
import json
import os
import time

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG
from golf_price import popularity
from golf_price.scrapers.mercari import MercariError

OUT_PATH = CACHE_DIR / "popularity.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="", help="driver/fw/ut/iron/chipper に絞る")
    ap.add_argument("--limit", type=int, default=0, help="先頭N機種だけ（テスト用）")
    ap.add_argument("--keys", default="", help="カンマ区切りの機種キー指定")
    ap.add_argument("--window", type=int, default=30, help="集計期間（日）")
    args = ap.parse_args()

    targets = list(CATALOG)
    if args.keys:
        want = {k.strip() for k in args.keys.split(",") if k.strip()}
        targets = [m for m in targets if m.key in want]
    if args.category:
        targets = [m for m in targets if m.category == args.category]
    limit = args.limit or int(os.environ.get("MODEL_LIMIT") or 0)
    if limit:
        targets = targets[:limit]

    print(f"人気集計: {len(targets)}機種 / 期間{args.window}日")
    t0 = time.time()
    rows, errors = [], 0
    for i, m in enumerate(targets, 1):
        try:
            row = popularity.analyze_model(m, window_days=args.window)
        except MercariError as e:
            errors += 1
            print(f"[{i}/{len(targets)}] {m.key}: 取得失敗 {e}")
            # 連続失敗（サーキットブレーカー作動）はIPブロックの可能性大→中断
            if "スキップ" in str(e):
                print("メルカリ連続失敗のため中断（部分結果は保存しません）")
                break
            continue
        rows.append(row)
        w7 = row.get("w7") or {}
        print(f"[{i}/{len(targets)}] {m.key}: 売れた{row['sold']} 販売中{row['active']}"
              f"{'+' if row['truncated'] else ''} "
              f"(7日: {w7.get('sold', '—')}) "
              f"{'★' + row['flag'] if row['flag'] else ''}")

    if not rows:
        print("結果0件のため popularity.json は更新しません")
        return 1

    rows.sort(key=lambda r: (-r["sold"], -(r["sell_rate"] or 0)))
    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "window_days": args.window,
        "windows": [args.window] + [w for w in (7,) if w < args.window],
        "model_count": len(rows),
        "errors": errors,
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    mins = round((time.time() - t0) / 60, 1)
    print(f"完了: {len(rows)}機種を書き出し → {OUT_PATH}（{mins}分, 失敗{errors}件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
