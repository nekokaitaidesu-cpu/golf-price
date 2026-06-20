"""人気ドライバーのカタログ（2021〜現行・テーラーメイド/キャロウェイ/ピン）。

model_code不要のキーワード方式。各機種は検索KWと圧縮キー（required/excludes）で
派生（兄弟）モデルを分離してマッチする。新機種はここに1行足すだけ。
"""

from dataclasses import dataclass, field


@dataclass
class DriverModel:
    key: str
    brand: str
    label: str
    year: str
    keyword: str                       # 楽天/Yahoo共通の検索KW
    required: list[str]                # 全て圧縮キーに含む必要
    excludes: list[str] = field(default_factory=list)  # 含んだら除外（兄弟分離）
    category: str = "driver"           # driver / fw / ut / iron


# カテゴリの表示名
CATEGORIES = [
    ("driver", "ドライバー"),
    ("fw", "フェアウェイウッド"),
    ("ut", "ユーティリティ"),
    ("iron", "アイアン"),
]
CATEGORY_LABEL = dict(CATEGORIES)


CATALOG: list[DriverModel] = [
    # ============ テーラーメイド ============
    # --- SIM2 (2021) ---
    DriverModel("tm_sim2", "テーラーメイド", "SIM2", "2021",
                "テーラーメイド SIM2 ドライバー", ["sim2"], ["max", "fast", "mini", "ti"]),
    DriverModel("tm_sim2max", "テーラーメイド", "SIM2 MAX", "2021",
                "テーラーメイド SIM2 MAX ドライバー", ["sim2max"], ["maxd", "fast"]),
    DriverModel("tm_sim2maxd", "テーラーメイド", "SIM2 MAX-D", "2021",
                "テーラーメイド SIM2 MAX-D ドライバー", ["sim2maxd"], []),
    # --- STEALTH (2022) ---
    DriverModel("tm_stealth", "テーラーメイド", "STEALTH", "2022",
                "テーラーメイド ステルス ドライバー", ["stealth"], ["stealth2", "plus", "hd"]),
    DriverModel("tm_stealthplus", "テーラーメイド", "STEALTH Plus", "2022",
                "テーラーメイド ステルス プラス ドライバー", ["stealthplus"], ["stealth2"]),
    DriverModel("tm_stealthhd", "テーラーメイド", "STEALTH HD", "2022",
                "テーラーメイド ステルス HD ドライバー", ["stealthhd"], ["stealth2"]),
    # --- STEALTH2 (2023) ---
    DriverModel("tm_stealth2", "テーラーメイド", "STEALTH2", "2023",
                "テーラーメイド ステルス2 ドライバー", ["stealth2"], ["plus", "hd"]),
    DriverModel("tm_stealth2plus", "テーラーメイド", "STEALTH2 Plus", "2023",
                "テーラーメイド ステルス2 プラス ドライバー", ["stealth2plus"], []),
    DriverModel("tm_stealth2hd", "テーラーメイド", "STEALTH2 HD", "2023",
                "テーラーメイド ステルス2 HD ドライバー", ["stealth2hd"], []),
    # --- Qi10 (2024) ---
    DriverModel("tm_qi10", "テーラーメイド", "Qi10", "2024",
                "テーラーメイド Qi10 ドライバー", ["qi10"], ["max", "ls"]),
    DriverModel("tm_qi10max", "テーラーメイド", "Qi10 MAX", "2024",
                "テーラーメイド Qi10 MAX ドライバー", ["qi10max"], []),
    DriverModel("tm_qi10ls", "テーラーメイド", "Qi10 LS", "2024",
                "テーラーメイド Qi10 LS ドライバー", ["qi10ls"], []),

    # ============ キャロウェイ ============
    # --- ROGUE ST (2022) ---
    DriverModel("cw_roguestmax", "キャロウェイ", "ROGUE ST MAX", "2022",
                "キャロウェイ ROGUE ST MAX ドライバー", ["roguestmax"], ["maxd", "maxls", "maxfast"]),
    DriverModel("cw_roguestmaxd", "キャロウェイ", "ROGUE ST MAX D", "2022",
                "キャロウェイ ROGUE ST MAX D ドライバー", ["roguestmaxd"], []),
    DriverModel("cw_roguestmaxls", "キャロウェイ", "ROGUE ST MAX LS", "2022",
                "キャロウェイ ROGUE ST MAX LS ドライバー", ["roguestmaxls"], []),
    DriverModel("cw_roguestmaxfast", "キャロウェイ", "ROGUE ST MAX FAST", "2022",
                "キャロウェイ ROGUE ST MAX FAST ドライバー", ["roguestmaxfast"], []),
    # --- PARADYM (2023) ---
    DriverModel("cw_paradym", "キャロウェイ", "PARADYM", "2023",
                "キャロウェイ パラダイム ドライバー", ["paradym"],
                ["paradymx", "smoke", "◆", "triplediamond"]),
    DriverModel("cw_paradymx", "キャロウェイ", "PARADYM X", "2023",
                "キャロウェイ パラダイム X ドライバー", ["paradymx"], ["smoke"]),
    DriverModel("cw_paradym_td", "キャロウェイ", "PARADYM ◆◆◆", "2023",
                "キャロウェイ パラダイム トリプルダイヤモンド ドライバー",
                ["paradym", "◆◆◆"], ["smoke", "◆◆◆max"]),
    # --- PARADYM Ai SMOKE (2024) ---
    DriverModel("cw_aismoke_max", "キャロウェイ", "PARADYM Ai SMOKE MAX", "2024",
                "キャロウェイ パラダイム Ai SMOKE MAX ドライバー", ["aismoke", "max"],
                ["maxd", "maxfast", "fast", "◆", "triplediamond", "mini", "340"]),
    DriverModel("cw_aismoke_maxd", "キャロウェイ", "PARADYM Ai SMOKE MAX D", "2024",
                "キャロウェイ パラダイム Ai SMOKE MAX D ドライバー", ["aismoke", "maxd"], ["◆"]),
    DriverModel("cw_aismoke_maxfast", "キャロウェイ", "PARADYM Ai SMOKE MAX FAST", "2024",
                "キャロウェイ パラダイム Ai SMOKE MAX FAST ドライバー", ["aismoke", "maxfast"], []),
    DriverModel("cw_aismoke_td", "キャロウェイ", "PARADYM Ai SMOKE ◆◆◆", "2024",
                "キャロウェイ パラダイム Ai SMOKE トリプルダイヤモンド ドライバー",
                ["aismoke", "◆◆◆"], ["◆◆◆max"]),
    DriverModel("cw_aismoke_tdmax", "キャロウェイ", "PARADYM Ai SMOKE ◆◆◆ MAX", "2024",
                "キャロウェイ パラダイム Ai SMOKE ◆◆◆ MAX ドライバー", ["aismoke", "◆◆◆max"], []),

    # ============ ピン ============
    # --- G425 (2021) ---
    DriverModel("ping_g425max", "ピン", "G425 MAX", "2021",
                "ピン G425 MAX ドライバー", ["g425max"], []),
    DriverModel("ping_g425lst", "ピン", "G425 LST", "2021",
                "ピン G425 LST ドライバー", ["g425lst"], []),
    DriverModel("ping_g425sft", "ピン", "G425 SFT", "2021",
                "ピン G425 SFT ドライバー", ["g425sft"], []),
    # --- G430 (2023) ---
    DriverModel("ping_g430max", "ピン", "G430 MAX", "2023",
                "ピン G430 MAX ドライバー", ["g430max"], ["10k"]),
    DriverModel("ping_g430lst", "ピン", "G430 LST", "2023",
                "ピン G430 LST ドライバー", ["g430lst"], []),
    DriverModel("ping_g430sft", "ピン", "G430 SFT", "2023",
                "ピン G430 SFT ドライバー", ["g430sft"], []),
    # --- G440 (2024) ---
    DriverModel("ping_g440max", "ピン", "G440 MAX", "2024",
                "ピン G440 MAX ドライバー", ["g440max"], ["10k"]),
    DriverModel("ping_g440lst", "ピン", "G440 LST", "2024",
                "ピン G440 LST ドライバー", ["g440lst"], []),
    DriverModel("ping_g440sft", "ピン", "G440 SFT", "2024",
                "ピン G440 SFT ドライバー", ["g440sft"], []),
    # --- G410 (2019) ※写真より ---
    DriverModel("ping_g410plus", "ピン", "G410 PLUS", "2019",
                "ピン G410 PLUS ドライバー", ["g410plus"], []),
    DriverModel("ping_g410lst", "ピン", "G410 LST", "2019",
                "ピン G410 LST ドライバー", ["g410lst"], []),
    DriverModel("ping_g410sft", "ピン", "G410 SFT", "2019",
                "ピン G410 SFT ドライバー", ["g410sft"], []),

    # ============ キャロウェイ EPIC（2021）※写真より ============
    DriverModel("cw_epicspeed", "キャロウェイ", "EPIC SPEED", "2021",
                "キャロウェイ EPIC SPEED ドライバー", ["epicspeed"], []),
    DriverModel("cw_epicmax", "キャロウェイ", "EPIC MAX", "2021",
                "キャロウェイ EPIC MAX ドライバー", ["epicmax"], ["epicmaxls", "fast"]),
    DriverModel("cw_epicmaxls", "キャロウェイ", "EPIC MAX LS", "2021",
                "キャロウェイ EPIC MAX LS ドライバー", ["epicmaxls"], []),

    # ============ タイトリスト ※写真(TS2/TSi3)＋主要 ============
    DriverModel("ti_ts2", "タイトリスト", "TS2", "2018",
                "タイトリスト TS2 ドライバー", ["タイトリスト|titleist", "ts2"], ["tsi2", "tsr2"]),
    DriverModel("ti_tsi2", "タイトリスト", "TSi2", "2021",
                "タイトリスト TSi2 ドライバー", ["tsi2"], []),
    DriverModel("ti_tsi3", "タイトリスト", "TSi3", "2021",
                "タイトリスト TSi3 ドライバー", ["tsi3"], []),
    DriverModel("ti_tsr2", "タイトリスト", "TSR2", "2022",
                "タイトリスト TSR2 ドライバー", ["tsr2"], []),
    DriverModel("ti_tsr3", "タイトリスト", "TSR3", "2022",
                "タイトリスト TSR3 ドライバー", ["tsr3"], []),
    DriverModel("ti_gt2", "タイトリスト", "GT2", "2024",
                "タイトリスト GT2 ドライバー", ["タイトリスト|titleist", "gt2"], []),
    DriverModel("ti_gt3", "タイトリスト", "GT3", "2024",
                "タイトリスト GT3 ドライバー", ["タイトリスト|titleist", "gt3"], []),

    # ============ ブリヂストン ============
    DriverModel("bs_jgr", "ブリヂストン", "TOUR B JGR", "2021",
                "ブリヂストン TOUR B JGR ドライバー", ["jgr"], []),
    DriverModel("bs_b1", "ブリヂストン", "B1", "2022",
                "ブリヂストン B1 ドライバー", ["ブリヂストン|bridgestone", "b1"], ["b1st"]),
    DriverModel("bs_b2", "ブリヂストン", "B2", "2022",
                "ブリヂストン B2 ドライバー", ["ブリヂストン|bridgestone", "b2"], ["b2ht"]),
    DriverModel("bs_b1st", "ブリヂストン", "B1ST", "2022",
                "ブリヂストン B1ST ドライバー", ["b1st"], []),
    DriverModel("bs_b3", "ブリヂストン", "B3", "2024",
                "ブリヂストン B3 ドライバー", ["ブリヂストン|bridgestone", "b3"], []),

    # ============ ダンロップ スリクソン ZX ============
    DriverModel("sx_zx5", "スリクソン", "ZX5", "2021",
                "スリクソン ZX5 ドライバー", ["zx5"], ["mk"]),
    DriverModel("sx_zx7", "スリクソン", "ZX7", "2021",
                "スリクソン ZX7 ドライバー", ["zx7"], ["mk"]),
    DriverModel("sx_zx5mk2", "スリクソン", "ZX5 MkII", "2023",
                "スリクソン ZX5 MkII ドライバー", ["zx5mk"], []),
    DriverModel("sx_zx7mk2", "スリクソン", "ZX7 MkII", "2023",
                "スリクソン ZX7 MkII ドライバー", ["zx7mk"], []),

    # ============ ダンロップ ゼクシオ ============
    DriverModel("xx_xxio12", "ゼクシオ", "ゼクシオ12", "2021",
                "ゼクシオ12 ドライバー", ["xxio12|ゼクシオ12"], []),
    DriverModel("xx_xxio13", "ゼクシオ", "ゼクシオ13", "2023",
                "ゼクシオ13 ドライバー", ["xxio13|ゼクシオ13"], []),

    # ============ コブラ ============
    DriverModel("cb_radspeed", "コブラ", "RADSPEED", "2021",
                "コブラ RADSPEED ドライバー", ["radspeed"], ["radspeedxb", "radspeedxd"]),
    DriverModel("cb_radspeedxb", "コブラ", "RADSPEED XB", "2021",
                "コブラ RADSPEED XB ドライバー", ["radspeedxb"], []),
    DriverModel("cb_radspeedxd", "コブラ", "RADSPEED XD", "2021",
                "コブラ RADSPEED XD ドライバー", ["radspeedxd"], []),
    DriverModel("cb_ltdx", "コブラ", "KING LTDx", "2022",
                "コブラ KING LTDx ドライバー", ["ltdx"], ["ltdxls", "ltdxmax"]),
    DriverModel("cb_ltdxls", "コブラ", "KING LTDx LS", "2022",
                "コブラ KING LTDx LS ドライバー", ["ltdxls"], []),
    DriverModel("cb_ltdxmax", "コブラ", "KING LTDx MAX", "2022",
                "コブラ KING LTDx MAX ドライバー", ["ltdxmax"], []),
    DriverModel("cb_aerojet", "コブラ", "AEROJET", "2023",
                "コブラ AEROJET ドライバー", ["aerojet"], ["aerojetls", "aerojetmax"]),
    DriverModel("cb_aerojetls", "コブラ", "AEROJET LS", "2023",
                "コブラ AEROJET LS ドライバー", ["aerojetls"], []),
    DriverModel("cb_aerojetmax", "コブラ", "AEROJET MAX", "2023",
                "コブラ AEROJET MAX ドライバー", ["aerojetmax"], []),
    DriverModel("cb_darkspeed", "コブラ", "DARKSPEED", "2024",
                "コブラ DARKSPEED ドライバー", ["darkspeed"], ["darkspeedls", "darkspeedmax", "darkspeedx"]),
    DriverModel("cb_darkspeedls", "コブラ", "DARKSPEED LS", "2024",
                "コブラ DARKSPEED LS ドライバー", ["darkspeedls"], []),
    DriverModel("cb_darkspeedmax", "コブラ", "DARKSPEED MAX", "2024",
                "コブラ DARKSPEED MAX ドライバー", ["darkspeedmax"], []),
    DriverModel("cb_darkspeedx", "コブラ", "DARKSPEED X", "2024",
                "コブラ DARKSPEED X ドライバー", ["darkspeedx"], []),

    # ============ ミズノ ST ============
    DriverModel("mz_stz", "ミズノ", "ST-Z", "2021",
                "ミズノ ST-Z ドライバー", ["ミズノ|mizuno", "stz"], ["stz220", "stz230"]),
    DriverModel("mz_stx", "ミズノ", "ST-X", "2021",
                "ミズノ ST-X ドライバー", ["ミズノ|mizuno", "stx"], ["stx220", "stx230"]),
    DriverModel("mz_stz220", "ミズノ", "ST-Z 220", "2022",
                "ミズノ ST-Z 220 ドライバー", ["stz220"], []),
    DriverModel("mz_stx220", "ミズノ", "ST-X 220", "2022",
                "ミズノ ST-X 220 ドライバー", ["stx220"], []),
    DriverModel("mz_stz230", "ミズノ", "ST-Z 230", "2023",
                "ミズノ ST-Z 230 ドライバー", ["stz230"], []),
    DriverModel("mz_stx230", "ミズノ", "ST-X 230", "2023",
                "ミズノ ST-X 230 ドライバー", ["stx230"], []),
    DriverModel("mz_stmax230", "ミズノ", "ST-MAX 230", "2023",
                "ミズノ ST-MAX 230 ドライバー", ["stmax230"], []),

    # ============ プロギア PRGR ============
    DriverModel("pr_rs5", "プロギア", "RS5", "2022",
                "プロギア RS5 ドライバー", ["プロギア|prgr", "rs5"], []),
    DriverModel("pr_rsjust", "プロギア", "RS JUST", "2023",
                "プロギア RS JUST ドライバー", ["rsjust"], []),

    # ============ ヤマハ ※写真より ============
    DriverModel("ym_rmxvd59", "ヤマハ", "RMX VD59", "2023",
                "ヤマハ RMX VD59 ドライバー", ["vd59"], []),
    DriverModel("ym_rmxvd40", "ヤマハ", "RMX VD40", "2023",
                "ヤマハ RMX VD40 ドライバー", ["vd40"], []),
    DriverModel("ym_inpresud2", "ヤマハ", "inpres UD+2", "2021",
                "ヤマハ インプレス UD+2 ドライバー", ["ud+2"], []),
    DriverModel("ym_drivestar", "ヤマハ", "inpres DRIVESTAR", "2022",
                "ヤマハ インプレス ドライブスター ドライバー", ["drivestar|ドライブスター"], []),

    # ============ 本間 HONMA ※写真より ============
    DriverModel("hm_twgs", "本間", "TOUR WORLD GS", "2022",
                "本間 ツアーワールド GS ドライバー", ["本間|ホンマ|honma", "gs"], []),
    DriverModel("hm_tw757", "本間", "TW757", "2022",
                "本間 TW757 ドライバー", ["tw757"], []),

    # ============ NEXGEN（ゴルフパートナー）※写真より ============
    DriverModel("nx_ns210", "NEXGEN", "NEXGEN NS210", "2022",
                "NEXGEN NS210 ドライバー", ["ns210"], []),
    DriverModel("nx_ns220", "NEXGEN", "NEXGEN NS220", "2023",
                "NEXGEN NS220 ドライバー", ["ns220"], []),
    DriverModel("nx_type460", "NEXGEN", "NEXGEN TYPE-460", "2019",
                "NEXGEN TYPE-460 ドライバー", ["type460|タイプ460"], []),

    # ============ PXG ※指定より ============
    DriverModel("pxg_blackops", "PXG", "0311 BLACK OPS", "2024",
                "PXG 0311 ブラックオプス ドライバー", ["blackops|ブラックオプス"], []),

    # ==================== フェアウェイウッド ====================
    DriverModel("fw_tm_sim2max", "テーラーメイド", "SIM2 MAX", "2021",
                "テーラーメイド SIM2 MAX フェアウェイウッド", ["sim2max"], ["maxd"], category="fw"),
    DriverModel("fw_tm_stealth2", "テーラーメイド", "STEALTH2", "2023",
                "テーラーメイド ステルス2 フェアウェイウッド", ["stealth2"], ["plus", "hd"], category="fw"),
    DriverModel("fw_tm_qi10", "テーラーメイド", "Qi10", "2024",
                "テーラーメイド Qi10 フェアウェイウッド", ["qi10"], ["max"], category="fw"),
    DriverModel("fw_cw_paradym", "キャロウェイ", "PARADYM", "2023",
                "キャロウェイ パラダイム フェアウェイウッド", ["paradym"], ["smoke", "x"], category="fw"),
    DriverModel("fw_cw_aismoke", "キャロウェイ", "PARADYM Ai SMOKE", "2024",
                "キャロウェイ パラダイム Ai SMOKE フェアウェイウッド", ["aismoke"], [], category="fw"),
    DriverModel("fw_ping_g425max", "ピン", "G425 MAX", "2021",
                "ピン G425 MAX フェアウェイウッド", ["g425"], [], category="fw"),
    DriverModel("fw_ping_g430max", "ピン", "G430", "2023",
                "ピン G430 フェアウェイウッド", ["g430"], [], category="fw"),
    DriverModel("fw_ping_g440", "ピン", "G440", "2024",
                "ピン G440 フェアウェイウッド", ["g440"], [], category="fw"),
    DriverModel("fw_sx_zx", "スリクソン", "ZX", "2021",
                "スリクソン ZX フェアウェイウッド", ["スリクソン|srixon", "zx"], [], category="fw"),
    DriverModel("fw_xx_xxio12", "ゼクシオ", "ゼクシオ12", "2021",
                "ゼクシオ12 フェアウェイウッド", ["xxio12|ゼクシオ12"], [], category="fw"),
    DriverModel("fw_cb_aerojet", "コブラ", "AEROJET", "2023",
                "コブラ AEROJET フェアウェイウッド", ["aerojet"], [], category="fw"),
    DriverModel("fw_cb_darkspeed", "コブラ", "DARKSPEED", "2024",
                "コブラ DARKSPEED フェアウェイウッド", ["darkspeed"], [], category="fw"),
    DriverModel("fw_mz_st", "ミズノ", "ST-Z/X", "2022",
                "ミズノ ST フェアウェイウッド", ["ミズノ|mizuno", "st"], [], category="fw"),
    DriverModel("fw_ti_tsr", "タイトリスト", "TSR", "2022",
                "タイトリスト TSR フェアウェイウッド", ["tsr"], [], category="fw"),

    # ==================== ユーティリティ ====================
    DriverModel("ut_tm_sim2max", "テーラーメイド", "SIM2 MAX レスキュー", "2021",
                "テーラーメイド SIM2 MAX レスキュー ユーティリティ", ["sim2max"], [], category="ut"),
    DriverModel("ut_tm_stealth2", "テーラーメイド", "STEALTH2 レスキュー", "2023",
                "テーラーメイド ステルス2 レスキュー ユーティリティ", ["stealth2"], [], category="ut"),
    DriverModel("ut_tm_qi10", "テーラーメイド", "Qi10 レスキュー", "2024",
                "テーラーメイド Qi10 レスキュー ユーティリティ", ["qi10"], [], category="ut"),
    DriverModel("ut_cw_paradym", "キャロウェイ", "PARADYM UT", "2023",
                "キャロウェイ パラダイム ユーティリティ", ["paradym"], ["smoke"], category="ut"),
    DriverModel("ut_cw_aismoke", "キャロウェイ", "Ai SMOKE UT", "2024",
                "キャロウェイ パラダイム Ai SMOKE ユーティリティ", ["aismoke"], [], category="ut"),
    DriverModel("ut_ping_g425", "ピン", "G425 ハイブリッド", "2021",
                "ピン G425 ハイブリッド ユーティリティ", ["g425"], [], category="ut"),
    DriverModel("ut_ping_g430", "ピン", "G430 ハイブリッド", "2023",
                "ピン G430 ハイブリッド ユーティリティ", ["g430"], [], category="ut"),
    DriverModel("ut_sx_zx", "スリクソン", "ZX ユーティリティ", "2021",
                "スリクソン ZX ユーティリティ", ["スリクソン|srixon", "zx"], [], category="ut"),
    DriverModel("ut_xx_xxio12", "ゼクシオ", "ゼクシオ12 UT", "2021",
                "ゼクシオ12 ユーティリティ", ["xxio12|ゼクシオ12"], [], category="ut"),
    DriverModel("ut_mz_flihi", "ミズノ", "Fli-Hi / ST UT", "2022",
                "ミズノ ユーティリティ", ["ミズノ|mizuno", "st|flihi"], [], category="ut"),
    DriverModel("ut_ti_tsr", "タイトリスト", "TSR ユーティリティ", "2022",
                "タイトリスト TSR ユーティリティ", ["tsr"], [], category="ut"),

    # ==================== アイアン ====================
    DriverModel("ir_tm_p790", "テーラーメイド", "P790", "2023",
                "テーラーメイド P790 アイアン", ["p790"], [], category="iron"),
    DriverModel("ir_tm_stealth", "テーラーメイド", "STEALTH アイアン", "2022",
                "テーラーメイド ステルス アイアン", ["stealth"], ["stealth2"], category="iron"),
    DriverModel("ir_tm_qi", "テーラーメイド", "Qi アイアン", "2024",
                "テーラーメイド Qi10 アイアン", ["qi"], [], category="iron"),
    DriverModel("ir_cw_apex", "キャロウェイ", "APEX", "2021",
                "キャロウェイ APEX アイアン", ["キャロウェイ|callaway", "apex"], ["pro", "tcb", "mb"], category="iron"),
    DriverModel("ir_cw_paradym", "キャロウェイ", "PARADYM アイアン", "2023",
                "キャロウェイ パラダイム アイアン", ["paradym"], ["smoke"], category="iron"),
    DriverModel("ir_cw_aismoke", "キャロウェイ", "Ai SMOKE アイアン", "2024",
                "キャロウェイ パラダイム Ai SMOKE アイアン", ["aismoke|ai"], [], category="iron"),
    DriverModel("ir_ping_i525", "ピン", "i525", "2022",
                "ピン i525 アイアン", ["i525"], [], category="iron"),
    DriverModel("ir_ping_i230", "ピン", "i230", "2023",
                "ピン i230 アイアン", ["i230"], [], category="iron"),
    DriverModel("ir_ping_g430", "ピン", "G430 アイアン", "2023",
                "ピン G430 アイアン", ["g430"], [], category="iron"),
    DriverModel("ir_ti_t100", "タイトリスト", "T100", "2023",
                "タイトリスト T100 アイアン", ["t100"], [], category="iron"),
    DriverModel("ir_ti_t200", "タイトリスト", "T200", "2023",
                "タイトリスト T200 アイアン", ["t200"], [], category="iron"),
    DriverModel("ir_sx_zx5", "スリクソン", "ZX5 アイアン", "2021",
                "スリクソン ZX5 アイアン", ["zx5"], ["mk"], category="iron"),
    DriverModel("ir_sx_zx5mk2", "スリクソン", "ZX5 MkII アイアン", "2023",
                "スリクソン ZX5 MkII アイアン", ["zx5mk"], [], category="iron"),
    DriverModel("ir_mz_jpx923", "ミズノ", "JPX923", "2022",
                "ミズノ JPX923 アイアン", ["jpx923"], [], category="iron"),
    DriverModel("ir_mz_jpx925", "ミズノ", "JPX925", "2024",
                "ミズノ JPX925 アイアン", ["jpx925"], [], category="iron"),
    DriverModel("ir_mz_pro", "ミズノ", "Pro 241/243/245", "2023",
                "ミズノ Pro アイアン", ["ミズノ|mizuno", "pro24"], [], category="iron"),
]

CATALOG_BY_KEY = {m.key: m for m in CATALOG}
