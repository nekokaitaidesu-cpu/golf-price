"""スクレイパー共通の型とHTTPセッション。"""

from dataclasses import dataclass, asdict
import time
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


@dataclass
class Listing:
    """1件の出品/商品。"""
    source: str            # 例: "rakuten"
    title: str
    price: int             # 円（税込）
    url: str
    shop: str = ""
    is_used: bool = True   # 中古か
    sold: bool = False     # 落札済み（実売）か。フリマ実売の集計に使う
    image: str = ""
    # 解析結果（normalize.analyze の戻り）を後付けする
    grade_key: str = ""
    grade_label: str = ""
    head_only: bool = False
    loft: str = ""         # 例 "10.5"（抽出できなければ空）

    def to_dict(self) -> dict:
        return asdict(self)


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    return s


# 簡易レート制御（連続アクセスを避ける）
_last_call = {"t": 0.0}


def polite_sleep(min_interval: float = 2.0):
    elapsed = time.time() - _last_call["t"]
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_call["t"] = time.time()
