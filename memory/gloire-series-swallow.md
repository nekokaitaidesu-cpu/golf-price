---
name: gloire-series-swallow
description: 無印SIM/ステルス等のキーが同名シリーズ「グローレ」を飲み込む。find_swallowing はショートウッドでは番手が keyword に無いため検出できない
metadata: 
  node_type: memory
  type: project
  originSessionId: 99dcfbfc-5429-41ca-bb5d-61cb9a7540e1
  modified: 2026-09-17T14:48:57.892Z
---

2026-09-17、ショートウッド部門で「SIM 7W 13,000円（69%）」が割安圏に出たが、題名は SIM GLOIRE。
`sw_tm_sim` の excludes が `sim2` だけで、SIMグローレを吸っていた。`sw_tm_stealth` もステルスグローレを吸っていた
→ 両方に `gloire|グローレ` を追加して修正済み（commit 同日）。

**Why:** グローレ（国内向け軽量シリーズ）は世代キーと同じ語（SIM／ステルス）を含むが、相場が別物。
ステルスグローレ 7W は中央24,000で無印より高く、SIMグローレは無印より安い＝混ざる向きが機種ごとに違う。

**未修正で残っている飲み込み（合成タイトルで確認）:** `yt_driver_m`・`dr_tm_mgloire`（SIMグローレ DR）／
`yt_driver_x3`（ステルスグローレ DR）／`yt_fw_x`（ステルスグローレ FW）／`yt_ut_sim`（SIMグローレ UT）／
`yt_iron_x`・`yt_iron_x2`（ステルスグローレ アイアン）。直す前に実売サンプルへの影響を測る。

**find_swallowing の盲点:** 判定は「相手の keyword を自分に当てる」だが、ショートウッドの keyword には番手が無く、
番手必須（_SW_NUM）のキー同士は必ずマッチしない＝包含ゼロと出る。

**How to apply:** 割安圏が出たらまず題名とキーが同じ機種か見る。ショートウッドの包含検査は「◯◯ 7W」の実タイトルを
`service._catalog_match` に当てて測る。新しい世代キーを足すときは同名シリーズ（グローレ等）を excludes に入れる。
関連: [[grade-split-cross-category]] [[bare-token-excludes-trap]] [[thin-denominator-fake-cheap]]
