---
name: catalog-comment-belongs-to-next-key
description: catalog.py のコメントは直後のキーの根拠。前のキーの話と読み違えない。分割は機種ごとに実測
metadata:
  type: reference
---

**`catalog.py` のコメントブロックは「直後の DriverModel」の根拠として書かれている。
直前のキーの説明ではない。**

**Why:** 2026-09-09、`sw_tm_qi10` の直後にあった
「2026-08-31実測: **MAX は無印とほぼ同値なので分けない**」というコメントを
Qi10 のものと読み違え、宿題（MAX分割）を取り下げかけた。
実際は**次行の `sw_tm_qi35` の根拠**で、Qi10 は未実測だった。

測ったら差は実在した:
```
Qi10  無印7W n=47 中央28,000 ／ MAX 7W n=49 中央25,000（1.12倍）→ 分割した
Qi35  無印   と MAX が同値                                      → 分けない
```

**How to apply:**
- コメントを根拠に使う前に、**そのブロックの直後にあるキー名**を確認する
- **グレード分割は機種ごとに実測する。** 「同じブランドの隣のモデルがこうだから」は
  根拠にならない。差が無ければ触らない（Qi35）、あるなら分ける（Qi10）
- 分割時の安全装置は CLAUDE.md のとおり。自己マッチ失敗数の**基準値との差**を見る
  （shortwood は keyword に番手が入らないため全キーが元から失敗する。
   絶対数でなく増分1件＝新キー分だけかを見る）

関連: [[grade-split-cross-category]] [[denominator-two-stage-split]] [[thin-denominator-fake-cheap]]
