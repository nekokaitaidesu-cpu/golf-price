"""ゴルフパートナーURLの解析と、商品一覧からのモデル名自動推定。"""

import re
import unicodedata
import urllib.parse
from collections import Counter


def parse_gp_url(url: str) -> dict:
    """URLから model_code とカテゴリ/ブランドコードを抽出。"""
    p = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(p.query)
    path_codes = re.findall(r"(h\d+|m\d+|b\d+)", p.path)
    model_code = qs.get("model_code", [""])[0]
    return {
        "model_code": model_code,
        "path_codes": path_codes,
        # 例: "h010001_m7_b144905" — 取得時にこのパスをそのまま使う
        "path": "_".join(path_codes),
        "host": p.netloc,
        "url": url,
    }


def is_golfpartner_url(url: str) -> bool:
    return "golfpartner.jp" in url and "model_code=" in url


def _clean(s: str) -> str:
    # 全角英数→半角、全角スペース正規化（表示用に読みやすく）
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip()


def derive_label(listings) -> str | None:
    """商品名群から機種名を推定（メーカー非依存）。

    同じmodel_codeの商品は先頭（ブランド＋モデル名）が共通なので、
    全タイトルの「共通する先頭トークン列」を機種名として採用する。
    ロフトやシャフトは商品ごとに違うため、自然にそこで打ち切られる。
    """
    if not listings:
        return None

    token_lists = [_clean(l.title).split() for l in listings if l.title.strip()]
    if not token_lists:
        return None

    prefix: list[str] = []
    for col in zip(*token_lists):
        if all(tok == col[0] for tok in col):
            prefix.append(col[0])
        else:
            break
    label = " ".join(prefix).strip()

    # 共通部分が短すぎる場合は先頭6トークンの最頻で代替
    if len(label) < 4:
        label = Counter(" ".join(t[:6]) for t in token_lists).most_common(1)[0][0]
    return label[:70]
