---
name: always-include-item-url
description: 候補・本命をユーザーに出すときは必ずメルカリのURLを添える。品名と価格だけでは辿り着けない
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d4f8fc12-6dd5-44be-90a6-aac46d3de627
  modified: 2026-09-06T11:55:30.225Z
---

**候補・本命・ウォッチ品をユーザーに提示するときは、必ず
`https://jp.mercari.com/item/<id>` を並べて書く。**

**Why:** 2026-09-05に「本命: SIM2 MAX レスキュー 4番22° テンセイR 11,500円」と
品名・価格・条件だけを出したところ、**ユーザーは探したが見つけられなかった**。
翌日その玉は他の人に買われていた（status=trading）。

> 「実はSIM2MAX 4U、Linkがわからなかったんだよね。探したけどわからなかった！」

分析が正しくても**URLが無いと行動に移せない**。メルカリは同一モデルの出品が多数あり、
品名と価格で検索しても目的の1件には辿り着かない。**分析の価値がゼロになる。**

**How to apply:**
- `.cache/honmei_candidates.json` の各候補は `id` を持っている。
  提示するときは `https://jp.mercari.com/item/{id}` を必ず添える
- 楽天は `rakuten_spot.py` が最初からURLを出す。**メルカリ側だけ抜けていた**
- 見送った玉でも「値下がりしたら買える」ものはURLを残す（翌日の追跡に使う）
- 2026-09-06に `scripts/honmei_scan.py` の候補出力にURL行を追加し、
  `CLAUDE.md` の手順3にも明記した

## 出し方の型（2026-09-06にユーザーが「こういう感じで出してくれたほうが嬉しい」と確認）

**判定ごとにグルーピングして、各行の下にURLを1行**で置く。

```
## 🎯 見る価値があるもの
**① 品名 価格**（前日比があれば添える）
https://jp.mercari.com/item/xxxx
→ 判定理由を1〜2行

## 🔨 オークション（上限を決めて機械的に）
**品名 現在価格**
https://jp.mercari.com/item/xxxx
→ 買い上限◯◯円。超えたら降りる

## ⚠ 部品なので手を出さないもの
**品名 価格**
https://jp.mercari.com/item/xxxx
→ なぜ部品か
```

・**見送った玉もURLを載せる**（値下がり待ちの追跡に使う／判断の再検証にも要る）
・「◯◯まで下がれば買える」は**必ず金額を書く**（ウォッチの発火条件になる）

関連: [[honmei-notes]] [[which-denominator-not-whether]] [[speech-style-polite]]
