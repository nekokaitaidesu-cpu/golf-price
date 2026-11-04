---
name: putter-title-omits-putter-word
description: ゼロトルク系パターは題名に「パター」が無い出品が多く、種別語必須の照合で大量に取りこぼす。club= で型名を種別語に認めて解決（2026-11-04）
metadata:
  node_type: memory
  type: project
  originSessionId: 4d9f5f01-7cba-44c5-bcc9-a1ca36cf1104
  modified: 2026-11-04T12:30:50.365Z
---

2026-11-04にゼロトルク系パター12キー（LAB OZ.1/LINK.1/LINK.2/DF2.1/DF3i、S2S Ai-ONE/Ai-DUAL/TRI-HOT、Spider ZT/ZT MAX、キャメロン OC、Evnroll ZERO）を追加した。
実在題名115件を照合したら、「Spider ZT 36インチ」「LAB GOLF OZ.1i STOCK」「Studio Style Fastback OC」のように**「パター」を書かない題名が大半**で、putter の種別語必須チェックで落ちていた。既存の DF3/Mezz.1 MAX も同じ漏れがあった。

**Why:** 型名だけでパターと分かるので出品者が種別語を省く。カタログ側は CLUB_TOKENS["putter"]=パター/putter を必須にしている。
**How to apply:** パター専業ブランド（LAB/Odyssey S2S/Evnroll）や専用型名（ZT）は `club=` にその語を入れる。ただし**OC のように部品名にも付く語は種別語にしない**（グリップ「マタドール OC」単品が5,500〜15,000円で売れている）。キャメロン OC はヘッド名（ファントム/ファストバック）を種別語にした。
代償として裸のカバー（「LAB GOLF カバー DF3」15,000）は通り得るが、_drop_low_outliers（中央の35%未満）で落ちる。
ほかの罠: OZ.1 の `oz1` が「ZERO Z1」（compact で zeroz1）を吸う → LAB必須＋evnroll除外。S2Sは世代で値段が倍違う（Ai-ONE 2万/Ai-DUAL 3万/TRI-HOT 6万）ので世代語を書かない題名はどこにも入れない。関連 [[wedge-putter-dept]] [[putter-denominator-caution]] [[search-keyword-misses-listings]]
