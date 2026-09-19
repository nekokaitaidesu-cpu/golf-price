---
name: denominator-two-stage-split
description: 分母は「グレード→番手」の2段階で割れる。分けた先でさらに割れないか必ず見る
metadata: 
  node_type: memory
  type: project
  originSessionId: d4f8fc12-6dd5-44be-90a6-aac46d3de627
  modified: 2026-08-31T11:45:29.766Z
---

同じキーを2日連続で、**違う軸**で割ることになった。

| 日 | キー | 割れた軸 | 結果 |
|---|---|---|---|
| 2026-08-30 | `ut_tm_qi10` | **グレード** | 無印 20,300 / MAX 25,800 → 分割 |
| 2026-08-31 | `ut_tm_qi10max` | **番手** | 3U 20,000 / 4U 24,200 / 5U 22,000 / 6U 28,300 |

8/31の楽天照合で「Qi10 MAX レスキュー 18,080 → 粗利+3,440・倍率1.43倍」が出たが、
楽天の玉は **U5** で、5Uの真値22,000で計算すると **+20円**。幻だった。

**Why:** グレードで分けても、FW/UT は番手（3U〜6U / 3W〜9W）で20〜40%動く。
グレード分割で満足すると、その先の番手混在が残る。

**How to apply:** FW・UT・ショートウッドの分母を見るときは
**「グレードで分ける → 分けた先を番手で見る」を1セット**にする。
`denominator_check` の「③番手・長さ別」を必ず読み、楽天やフリマの個別の玉は
**その玉の番手のバケツ**と突き合わせる（全体中央で計算しない）。
カタログを分割したら、翌日以降にもう一段割れないか確認する。

関連: [[grade-split-cross-category]] [[bare-token-excludes-trap]] [[thin-denominator-fake-cheap]]

**required に番手が無いキーは同シリーズの別クラブを吸う**（2026-09-12）。
`mn_ym_rmxvdm_steady` の required が `["rmx","steady|ステディ|短尺|43.5"]` だけで、
**RMX VD/U（UT）2件・VD FW 1件・VD/X（別ドライバー）1件・4本セット1件**を吸っていた。
30日窓が薄い日に効いて中央値が **25,000 → 17,500** に落ちて見え、
ユーザーの在庫機種の出口判断が狂いかけた。
対策は excludes を並べるより **required に番手トークン（`vdm`）を足す**方が確実。
compact が `/` を消すので `vd/m` でなく **`vdm`** と詰めて書く（[[term-hit-is-not-regex]]）。
**自分の在庫機種こそ分母を疑う**（[[thin-denominator-fake-cheap]]）。
