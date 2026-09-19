---
name: grade-split-cross-category
description: 分母の混在は年式だけでなく「同年式のグレード（無印/MAX/LS/TOUR）」でも起き、カテゴリ横断で抜けやすい
metadata: 
  node_type: memory
  type: project
  originSessionId: d4f8fc12-6dd5-44be-90a6-aac46d3de627
  modified: 2026-08-30T09:20:18.511Z
---

2026-08-30に `ut_tm_qi10`（Qi10 レスキュー）で発覚。ドライバー `tm_qi10` は
excludes=["max","ls"]、FW `fw_tm_qi10` は excludes=["max"] と分けてあったのに、
**UTだけ excludes=[] のまま**で MAX を飲み込んでいた。
120日実売59件が 無印 n=32 中央20,300 ／ MAX n=25 中央25,000 の二層で、
全体中央23,800 はどちらでもない中間値。楽天照合で +1,840 の粗利が出ていたが、
無印中央で計算し直すと **−1,310の赤字**だった。→ `ut_tm_qi10max` を新設して分割。

**Why:** 国内メーカーは「同名で年式が進む」（プロギアRS・オノフKURO）のに対し、
**海外メーカーは同年式内で 無印/MAX/LS/TOUR/SFT に枝分かれする**。裏返しの穴。
しかも修正は driver → fw → ut → shortwood と**カテゴリごとに手作業**なので、
「見落とし」ではなく「1カテゴリだけ直し忘れる」という作業の抜けとして発生する。

**How to apply:** 個別に見つけるのでなく、**ドライバーで excludes を持つキーを起点に、
同ブランド・同年式の fw / ut / shortwood のキーを並べて excludes を突き合わせる**。
分割か mixed_median かの判断は既存ルールどおり（両層とも母数があるなら分割）。
安全装置も既存どおり: ①除外を足してもキー自身の keyword にマッチし続けるか
②受け皿キーの実売がゼロでないか ③`find_duplicates()` と `find_swallowing()` を実行。

関連: [[putter-denominator-caution]] [[silent-head-only-price-ratio]]
