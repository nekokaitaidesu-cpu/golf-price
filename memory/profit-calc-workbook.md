---
name: profit-calc-workbook
description: 利益計算は ゴルフ利益計算.xlsm（マクロ付き）を使う。旧xlsxは廃止
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 446e2fe3-980f-4393-946c-ab3e96ae6898
  modified: 2026-07-19T01:27:25.302Z
---

利益計算のワークブックは `C:\Users\User\Claude\golf-price\ゴルフ利益計算.xlsm` を使う（ユーザー指定 2026-07-19）。ユーザーがフィルター解除ボタン（マクロ）を追加したため、旧 `ゴルフ利益計算.xlsx` は廃止済み。

**Why:** マクロ（フィルター解除ボタン）が入っているのは .xlsm のみ。xlsx に書き戻すとマクロが消える。

**How to apply:** 利益計算・在庫の損益更新でブックを読み書きする際は必ず .xlsm を対象にする。保存時も .xlsm 形式を維持（xlsx で保存し直さない）。在庫台帳は [[flip-inventory]] と併用。
