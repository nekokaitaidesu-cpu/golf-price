"""機種スペック定義（名寄せルール）。

各サイト・ページで表記がバラバラなので、ここで「同じ機種」と見なすための
別名（エイリアス）と、グレード（MAX / Triple Diamond など）の判定ルールを一元管理する。
新しい機種を追加したいときは MODELS に1エントリ足すだけで対応できる。
"""

from dataclasses import dataclass, field


@dataclass
class Grade:
    """グレード（モデル内の細分）。"""
    key: str                       # 内部キー
    label: str                     # 表示名
    aliases: list[str]             # このグレードを示す表記（正規化後でマッチ）
    excludes: list[str] = field(default_factory=list)  # これがあれば別グレード扱い
    gp_model_code: str = ""        # ゴルフパートナーの機種固有ID（あれば正確に取得できる）


@dataclass
class ModelSpec:
    key: str
    label: str
    # 「この機種」と判定するために必須のトークン群。各要素は any（どれか1つ該当でOK）
    brand: list[str]
    model: list[str]
    series: list[str]
    club_type: list[str]
    grades: list[Grade]
    # 機種全体の除外（明らかに別物のときに弾く）
    excludes: list[str] = field(default_factory=list)


# === キャロウェイ PARADYM Ai SMOKE ドライバー ===
PARADYM_AI_SMOKE_DRIVER = ModelSpec(
    key="callaway_paradym_ai_smoke_driver",
    label="キャロウェイ PARADYM Ai SMOKE ドライバー",
    brand=["callaway", "キャロウェイ", "ｷｬﾛｳｪｲ"],
    model=["paradym", "パラダイム"],
    series=["ai smoke", "aismoke", "aiスモーク", "ai スモーク",
            "エーアイスモーク", "エーアイ スモーク", "スモーク"],
    club_type=["ドライバー", "driver", " dr ", "1w", "1ｗ"],
    grades=[
        # 判定は上から順に評価し、最初に当たったグレードを採用する（順序が重要）。
        # ◆◆◆MAX は ◆◆◆ を含むので、必ず triple_diamond より前に置く。
        Grade("triple_diamond_max", "◆◆◆ MAX（Triple Diamond MAX・本命）",
              aliases=["◆◆◆max", "◆◆◆ max", "◆◆◆ｍａｘ",
                       "triple diamond max", "トリプルダイヤ max",
                       "トリプルダイヤモンド max", "td max"],
              gp_model_code="460220"),
        Grade("triple_diamond", "◆◆◆ Triple Diamond",
              aliases=["◆◆◆", "triple diamond", "tripple diamond",
                       "トリプルダイヤ", "トリプルダイアモンド", "3diamond",
                       "diamond ◆◆◆", " td "]),
        Grade("double_diamond", "◆◆ Double Diamond",
              aliases=["◆◆", "double diamond", "ダブルダイヤ", "2diamond"]),
        Grade("max_fast", "MAX FAST（軽量・別モデル）",
              aliases=["max fast", "maxfast", "max ファスト", "maxファスト"]),
        Grade("max_d", "MAX D（ドロー・別モデル）",
              aliases=["max d ", "max d　", "maxd", "max draw"]),
        Grade("max", "MAX（標準）",
              aliases=["max", "マックス"],
              excludes=["max fast", "max d ", "maxd", "max draw"]),
        Grade("ti_340mini", "Ti 340 Mini（ミニドライバー・別モデル）",
              aliases=["340 mini", "340mini", "340 mid", "ti 340", "340 ミニ"]),
        Grade("standard", "無印 / その他",
              aliases=[""]),  # 何にも当たらなければここ（空文字は常にマッチ）
    ],
    # PARADYM(無印・2023)やROGUEなど別世代を弾く語があれば追加できる
    excludes=[],
)

MODELS: dict[str, ModelSpec] = {
    PARADYM_AI_SMOKE_DRIVER.key: PARADYM_AI_SMOKE_DRIVER,
}

DEFAULT_MODEL_KEY = PARADYM_AI_SMOKE_DRIVER.key
