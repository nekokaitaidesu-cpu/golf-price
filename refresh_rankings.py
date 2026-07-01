"""全機種の価格を取得してキャッシュに保存する（毎日の自動更新用）。

タスクスケジューラから毎日1回実行すると、日中はキャッシュから即座に
ランキング・詳細が表示される（ファイルキャッシュに保存）。

ログは同フォルダの refresh.log に直接書き込む（cmdのリダイレクトに依存しない）。
手動実行: python refresh_rankings.py
"""

import os
import sys
import time
from pathlib import Path

from golf_price import service, cache, registry, history
from golf_price.catalog import CATALOG, CATALOG_BY_KEY
from golf_price.spec import MODELS

# 前日比の基準は2:00の自動取得のみにしたいので、履歴記録は --record-history 指定時だけ。
# （スケジュールタスクはこのフラグ付きで実行。手動実行は履歴を書かない）
RECORD_HISTORY = "--record-history" in sys.argv

# その日の履歴行をためる
_history_rows = []

LOG_PATH = Path(__file__).resolve().parent / "refresh.log"
_logfile = open(LOG_PATH, "w", encoding="utf-8")


def log(msg: str):
    _logfile.write(msg + "\n")
    _logfile.flush()
    try:
        print(msg, flush=True)
    except Exception:
        pass


def refresh_one(key: str, label: str) -> str:
    t0 = time.time()
    try:
        d = service.run(model_key=key, pages=2)
        d["_fetched_at"] = time.strftime("%Y-%m-%d %H:%M")
        cache.put(f"{key}_p2", d)
        # 履歴行を蓄積
        m = CATALOG_BY_KEY.get(key)
        cat = m.category if m else "driver"
        year = m.year if m else ""
        _history_rows.append(history.summarize(key, cat, label, year, d))
        if d.get("mode") == "single":
            n = f"中古{d['used']['count']}/フリマ{d['flea_sold']['count']}"
        else:
            n = f"{d.get('total_listings', '?')}件"
        return f"OK  {label[:34]:<34} {n}  ({time.time()-t0:.0f}s)"
    except Exception as e:
        return f"NG  {label[:34]:<34} {type(e).__name__}: {e}"


def main():
    start = time.time()
    targets = [(m.key, f"{m.brand} {m.label}") for m in CATALOG]
    targets += [(k, m.label) for k, m in MODELS.items()]
    targets += [(k, e["label"]) for k, e in registry.load().items()]

    # 動作検証用: MODEL_LIMIT=N で先頭N機種だけ実行（本番は未設定）
    limit = os.environ.get("MODEL_LIMIT")
    if limit and limit.isdigit():
        targets = targets[: int(limit)]

    log(f"=== 自動更新開始 {time.strftime('%Y-%m-%d %H:%M:%S')} / 全{len(targets)}機種 ===")
    ok = ng = 0
    for i, (key, label) in enumerate(targets, 1):
        line = refresh_one(key, label)
        ok += line.startswith("OK")
        ng += line.startswith("NG")
        log(f"[{i:>3}/{len(targets)}] {line}")

    # 履歴(前日比の基準)は2:00の自動取得のみ記録。手動実行はスキップ。
    if RECORD_HISTORY:
        try:
            today = time.strftime("%Y-%m-%d")
            history.record(today, _history_rows)
            log(f"履歴を保存: {len(_history_rows)}行 / 累計 {history.count()}行 → history.csv")
        except Exception as e:
            log(f"履歴保存に失敗: {type(e).__name__}: {e}")
    else:
        log("手動実行のため履歴は記録しません（前日比の基準は2:00取得のまま）")

    # スマホ用静的サイトを生成してGitHub Pagesへ自動アップ
    try:
        import build_site
        n = build_site.build()
        log(f"スマホ用サイトを生成: {n}機種 → site/")
        log("公開: " + build_site.publish())
    except Exception as e:
        log(f"サイト生成/公開に失敗: {type(e).__name__}: {e}")

    mins = (time.time() - start) / 60
    log(f"=== 完了 成功{ok} / 失敗{ng} / 所要 {mins:.1f}分 ===")
    _logfile.close()


if __name__ == "__main__":
    main()
