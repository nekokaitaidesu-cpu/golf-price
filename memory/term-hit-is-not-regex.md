---
name: term-hit-is-not-regex
description: catalog の required/excludes は正規表現でない。compact が空白を除くので英字は詰めて書く
metadata:
  type: reference
---

**`catalog.py` の `required` / `excludes` に書く語は正規表現ではない。**
`service._term_hit` が `compact(title)`（空白除去・小文字化）と
`normalize(title)`（空白は残す）への**部分一致**で判定する。
OR は `|`、単語境界は先頭 `=` だけが特別扱い。

**How to apply:**
- 英字の複数語は**詰めた形**で書く。`"original one"` や `"original ?one"` は
  compact 側（`originalone`）に当たらず、**`"originalone"` が正解**
- カナ↔英字は両方書く。例 `"オリジナルワン|originalone"`
- 2026-09-07に `yt_driver_x13`（オリジナルワン ミニ）がこれで
  **30日実売0本**になっていた。実売の大半が `TaylorMade Original One Mini Driver`
  という英字表記で、カナだけの required が丸ごと落としていた（実測100件中9件しか通らず）
- 直したら必ず「キー自身の keyword に自分でマッチするか」と
  `find_duplicates()` / `find_swallowing()` を確認する

関連: [[grade-split-cross-category]] [[bare-token-excludes-trap]]
