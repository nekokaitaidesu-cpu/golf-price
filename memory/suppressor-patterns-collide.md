---
name: suppressor-patterns-collide
description: 誤検出対策で入れた「抑止」が、別の正しい検出を打ち消す。すり抜けは未知パターンとは限らない
metadata: 
  node_type: memory
  type: project
  originSessionId: 24597095-3206-4f85-800d-cd867d5a53c6
  modified: 2026-09-10T11:55:31.883Z
---

normalize.py のすり抜けを追うとき、**検出パターンが無いとは限らない**。
過去に完品を守るために入れた**抑止条件が、正しく当たっている検出を打ち消している**
ことがある。まず「どのパターンが当たり、何が抑止したか」を個別に print して切り分ける。

**Why:** 2026-09-10、PING G425 MAX 5W 13,000円（m80246088189）が完品として
候補に出た。写真5枚すべてヘッド単体でホーゼルが空いている本物のヘッド単品。
`_HEAD_NOUN_DESC_PAT` は説明文の「フェアウェイウッドヘッドです」に**正しく当たって
いた**のに、`_SHAFT_SPEC_PAT`（2026-07-30に完品G440 MAXの誤検出を止めるため導入）が
スペック欄の「-シャフト:ピンツアー173-65 X」に反応して打ち消していた。
**元のシャフトの型番を書き残したままヘッドだけ売る出品が実在する**＝
「シャフト:◯◯」は完品の証拠にならない。

**How to apply:** 切り分けは `n._HEAD_ONLY_DESC_PAT.search(d)` /
`n._HEAD_NOUN_DESC_PAT.search(d)` / `n._SHAFT_SPEC_PAT.search(d)` を個別に叩く。
抑止に打ち消されている型は、抑止より手前の**無条件段**（`_HEAD_ONLY_DESC_PAT`）に、
元の誤検出例に当たらない形で足す。今回は「番手が直前に付く◯番◯◯ヘッドです」
（元の誤検出例は番手を伴わない）で分離できた。
検証は [[corpus-not-enough-for-false-positives]] のとおりコーパスと自作反例の両方。
