"""検索結果の簡易ファイルキャッシュ（毎回スクレイピングしないため）。"""

import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
# 毎日1回の自動更新（タスクスケジューラ）で一日中フレッシュに保てるよう約26時間。
# 即時に取り直したいときは画面の「↻最新」（refresh=true）でバイパスできる。
DEFAULT_TTL = 60 * 60 * 26


def _path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
    return CACHE_DIR / f"{safe}.json"


def get(key: str, ttl: int = DEFAULT_TTL):
    p = _path(key)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > ttl:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def put(key: str, value: dict):
    _path(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
