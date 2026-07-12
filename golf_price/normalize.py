"""タイトル文字列の正規化と、機種・グレードの判定（名寄せの中核）。"""

import re
import unicodedata

from .spec import ModelSpec, Grade


def normalize(text: str) -> str:
    """表記ゆれを吸収するための正規化。

    - NFKC で全角英数・半角カナなどを統一（パラダイム等の全角→半角、ﾊﾟﾗﾀﾞｲﾑ→パラダイム）
    - 小文字化
    - 連続空白の圧縮
    - 前後に空白を付与（' dr ' のような単語境界マッチをしやすくする）
    """
    if not text:
        return " "
    t = unicodedata.normalize("NFKC", text)
    t = t.lower()
    # 記号類を空白に（◆ は判定に使うので残す。〜はアイアン番手レンジに使うので残す）
    t = re.sub(r"[【】\[\]（）()｜|/／,，･・’'\"”“★☆●○◎■□‼]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return f" {t.strip()} "


def _has_any(norm_title: str, aliases: list[str]) -> bool:
    for a in aliases:
        a = a.strip().lower()
        if a == "":
            return True  # 空エイリアスは常に真（フォールバック用）
        if a in norm_title:
            return True
    return False


def is_target_model(norm_title: str, spec: ModelSpec) -> bool:
    """この機種かどうか（ブランド・モデル・シリーズ・種別が全て揃うか）。"""
    if spec.excludes and _has_any(norm_title, spec.excludes):
        return False
    return (
        _has_any(norm_title, [normalize(x).strip() for x in spec.brand])
        and _has_any(norm_title, [normalize(x).strip() for x in spec.model])
        and _has_any(norm_title, [normalize(x).strip() for x in spec.series])
        and _has_any(norm_title, [normalize(x).strip() for x in spec.club_type])
    )


def classify_grade(norm_title: str, spec: ModelSpec) -> Grade:
    """グレードを判定（spec.grades の順に評価し最初に当たったもの）。"""
    for g in spec.grades:
        if g.excludes and _has_any(norm_title, [normalize(x).strip() for x in g.excludes]):
            continue
        if _has_any(norm_title, [normalize(x).strip() if x else "" for x in g.aliases]):
            return g
    return spec.grades[-1]


# シャフト有無の判定。メルカリは「〜ドライバー ヘッド」「〜ヘッド 9.0度」のように
# 「のみ」を書かないヘッド単体出品が多いため、タイトル末尾の「ヘッド」、
# 「ヘッド＋付属品」、「ヘッド ＋ロフト度数」も拾う
# （「ヘッドカバー」「ヘッドに傷」「ヘッドスピード」等は拾わない）。
_HEAD_ONLY_PAT = re.compile(
    # のみ/単体等の前のスペースも許容（2026-07-09: 「ヘッド 単体」がすり抜けた）
    r"ヘッド\s*(のみ|単体|単品|だけ)|head only"
    r"|ヘッド\s*[+＋]|ヘッド\s*$|ヘッド\s*本体"
    r"|ヘッド\s*(?=[0-9.]{1,4}\s*[°度])"
    # 「〜ドライバー ヘッド 10.5」のような度なし裸ロフトで終わるタイトル
    # （2026-07-08: ROGUE ST MAX がこの形ですり抜けて割安リストに混入）
    r"|ヘッド\s*[0-9.]{1,4}\s*$"
    r"|シャフトなし|シャフト無し|シャフト欠品")


def detect_head_only(norm_title: str) -> bool:
    return bool(_HEAD_ONLY_PAT.search(norm_title))


# 説明文用のヘッド単品判定。タイトルは実クラブ風でも説明文にだけ
# 「ヘッド単品販売です」「ヘッド及びヘッドカバーの出品」「シャフトは付属しません」
# と書かれる出品が多い（2026-07-08: 割安候補6件中3件がこのパターン）。
# 逆パターンのシャフト単品（ヘッドなし）も同じ穴なのでここで拾う
# （2026-07-09: エリートミニのシャフト単品がLINE通知をすり抜けた）。
# 通知や本命抽出の最終フィルタ用で、多少の過剰検出は許容する。
_HEAD_ONLY_DESC_PAT = re.compile(
    r"ヘッド\s*(のみ|単体|単品|だけ)"
    r"|ヘッド(及び|および|と)ヘッドカバー"
    # 「ヘッドカバー付きの出品です」（完品）を誤検出しないよう「カバー付」は除く
    # （2026-07-11: Qi10 MAX完品風ヘッド単品の検死中に誤検出と判明。
    #   なお当該出品は本当にヘッド単品だった＝説明文無言型。写真確認が最終防衛線）
    r"|ヘッド(?!カバー[付つ])[^。\n]{0,10}の?出品"
    r"|シャフト[^。\n]{0,25}付属(しません|致しません|いたしません|なし|無し)"
    r"|シャフトは(付き|附属|付属)ません"
    r"|シャフト\s*(のみ|単体|単品|だけ)\s*の?\s*(出品|販売)"
    r"|ヘッド[^。\n]{0,10}(付属|附属)(しません|致しません|いたしません|なし|無し)"
    # 2026-07-12すり抜け分: 「〜のヘッドと付属品になります」(TSR2)、
    # 「シャフト付きが良い方はコメントしてください」(SIM2 MAX、ベースはヘッド単品)
    r"|ヘッドと付属品"
    r"|シャフト付きが(良い|よい|いい)方"
    r"|シャフトは?別(売|途)")


def detect_head_only_desc(norm_desc: str) -> bool:
    """説明文から部品単品出品（ヘッドのみ／シャフトのみ）を検出。
    normalize() 済みの文字列を渡す。"""
    return bool(_HEAD_ONLY_DESC_PAT.search(norm_desc))


# レフティ（左用）は市場が別で相場も薄い。右用の相場・候補に混ぜない
# （2026-07-12: 楽天used_minが左用3Wで、メルカリ候補にGT2レフティが混入していた）
_LEFTY_PAT = re.compile(r"レフティ|左用|左利き|左打ち|lefty|left\s*hand", re.I)


def is_lefty(title: str) -> bool:
    """左用（レフティ）出品かどうか。"""
    return bool(_LEFTY_PAT.search(title or ""))


# 中古/新品の判定（ソースが中古フラグを持たない場合の補助）
def detect_used(norm_title: str) -> bool:
    return ("中古" in norm_title) and ("新品" not in norm_title)


def compact(text: str) -> str:
    """空白・ハイフン等を除いた圧縮キー（『SIM 2 MAX-D』→『sim2maxd』）。

    型番の表記ゆれ（スペース/ハイフン有無）を吸収して部分一致判定するために使う。
    ◆ や日本語はそのまま残す。
    """
    t = unicodedata.normalize("NFKC", text or "").lower()
    # 各種ダッシュ/マイナス（- − – — ― 等）や区切り記号をまとめて除去
    return re.sub(r"[\s\-−–—―_/・.,'\"()\[\]【】]", "", t)


# フリマ/オークションで混ざる「部品・付属品のみ・別カテゴリ」を示す語（本体ではない）
_JUNK_TOKENS = [
    "スリーブ", "sleeve", "tip", "チップ", "アダプタ", "adapter", "ネック",
    "ウェイト", "weight", "レンチ", "wrench", "ねじ", "ビス", "ボルト",
    # 「M6フェアウェイウッド用カバー」のようなカバー単品（2026-07-09すり抜け）
    "用カバー",
    # 「ユーティリティ用 ヘッドカバー」「ALTA J CB ユーティリティシャフト 5U」
    # のような部品単品（2026-07-11すり抜け。クラブ完品のタイトルには現れない複合語のみ）
    "ユーティリティ用", "ウッド用", "アイアン用",
    "ユーティリティシャフト", "ドライバーシャフト", "ウッドシャフト",
    "シャフトのみ", "シャフト単体", "シャフト単品", "シャフトだけ",
    "リシャフト", "カバーのみ",
    "ヘッドカバーのみ", "headcover", "純正スリーブ", "中古シャフト",
    "ジャンク", "部品取り", "訳あり大", "故障",
    # シャフト単品・パーツの除外（クラブ種別はマッチャ側でカテゴリ判定するためここには入れない）
    "ドライバー用", "用シャフト", "シャフト用", "純正シャフト", "ヘッド用", "ばらし",
]


def is_parts_junk(title: str) -> bool:
    """クラブ本体ではなく部品・付属品・ジャンクと思われるか。"""
    n = normalize(title)
    return any(tok in n for tok in (normalize(t).strip() for t in _JUNK_TOKENS))


# 相場を歪めるため除外する店（楽天の輸入単品ショップ等）。店名 or 商品URLに含む語で判定。
BLOCKED_SHOPS = [
    "ajimura",   # AJIMURA-SHOP（海外輸入・単品アイアンが高値で相場を歪める）
]


def is_blocked_shop(shop: str = "", url: str = "") -> bool:
    s = ((shop or "") + " " + (url or "")).lower()
    return any(b in s for b in BLOCKED_SHOPS)


# 単品（バラ売り1本）を示す語
_SINGLE_TOKENS = ["単品", "ばら売り", "ばらうり", "1本", "１本", "単体", "バラ", "ばら"]
# 本数/レンジ系のセット判定（番手レンジ例: 5-pw, 5～pw, 6-9, 5i-pw, 5番-pw）
_SET_RANGE = re.compile(r"[4-9]\s*[i番]?\s*[-~ー－〜]\s*#?\s*(p|pw|aw|sw|gw|w|[4-9]|1[01])")


def looks_like_iron_set(title: str) -> bool:
    """アイアンが『セット』らしいか（単品を除外し、セット同士で比較するため）。"""
    n = normalize(title)
    if any(t in n for t in _SINGLE_TOKENS):
        return False
    if "セット" in n or "番手" in n:
        return True
    if re.search(r"[4-9]\s*本|1[0-2]\s*本", n):   # 4〜12本
        return True
    if _SET_RANGE.search(n):
        return True
    return False


_LOFT_PAT = re.compile(r"(\d{1,2}(?:\.\d)?)\s*[°度]")


def extract_loft(title: str) -> str:
    """タイトルからロフト角を抽出（全角『１０．５°』もNFKCで正規化して対応）。

    返り値は "10.5" のような文字列。見つからなければ ""。
    """
    t = unicodedata.normalize("NFKC", title or "")
    m = _LOFT_PAT.search(t)
    if not m:
        return ""
    val = m.group(1)
    # "10" → "10", "10.5" → "10.5"（末尾 .0 は整数化）
    if val.endswith(".0"):
        val = val[:-2]
    return val


def analyze(title: str, spec: ModelSpec) -> dict:
    """1件のタイトルを解析して機種一致・グレード・属性を返す。"""
    n = normalize(title)
    matched = is_target_model(n, spec)
    grade = classify_grade(n, spec) if matched else None
    return {
        "matched": matched,
        "grade_key": grade.key if grade else None,
        "grade_label": grade.label if grade else None,
        "head_only": detect_head_only(n),
        "used_in_title": detect_used(n),
    }
