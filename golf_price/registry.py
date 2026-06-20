"""ユーザーが追加したモデルの保存・読込（URL→モデル登録）。

ゴルフパートナーの model_code はモデルを一意に特定するため、
URLを貼るだけで名寄せルール無しに「その機種」を登録できる。
組み込みモデル（spec.py）とは別に user_models.json に永続化する。
"""

import json
from pathlib import Path

from .gp_url import parse_gp_url, derive_label, is_golfpartner_url
from .scrapers import golfpartner

STORE = Path(__file__).resolve().parent.parent / "user_models.json"


def load() -> dict:
    if STORE.exists():
        try:
            return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(d: dict):
    STORE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def add_from_url(url: str, label: str | None = None) -> dict:
    """ゴルフパートナーURLからモデルを登録して返す。"""
    if not is_golfpartner_url(url):
        raise ValueError("ゴルフパートナーの model_code 付きURLを貼ってください。")
    info = parse_gp_url(url)
    code = info["model_code"]
    path = info["path"]
    if not code:
        raise ValueError("URLに model_code が見つかりませんでした。")

    # 実際に取得してモデル名を自動推定（＆登録時点の件数確認）
    # path（カテゴリ_区分_ブランド）はメーカーごとに異なるためURLのものを使う。
    listings = golfpartner.search_by_model_code(code, path=path, pages=1)
    if not listings:
        raise ValueError("そのURLで商品が見つかりませんでした（在庫切れ/URL違いの可能性）。")
    if not label:
        label = derive_label(listings) or f"ゴルフパートナー機種 {code}"

    key = f"gp_{code}"
    d = load()
    d[key] = {
        "key": key,
        "label": label,
        "gp_model_code": code,
        "gp_path": path,
        "source_url": url,
        "sample_count": len(listings),
    }
    _save(d)
    return d[key]


def remove(key: str):
    d = load()
    d.pop(key, None)
    _save(d)
