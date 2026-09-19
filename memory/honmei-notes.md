---
name: honmei-notes
description: 「今日の本命」は honmei_notes/YYYY-MM-DD.md にメモとして保存する運用
metadata: 
  node_type: memory
  type: project
  originSessionId: 06527d6b-1db1-4bbb-99a5-2582e150afeb
---

ユーザーは「今日の本命」（人気ランキング×当日価格で抽出したメルカリ/楽天の狙い目クラブ）を `honmei_notes/YYYY-MM-DD.md` に日次メモとして残したい（初回: 2026-07-07）。

**Why:** 会話で出した本命を後から見返したい。スマホ連携（GitHub Pages公開案）は「イマイチ」と判断され、Claude Codeとの会話ベースで運用する方針。

**How to apply:** 本命を聞かれて分析したら、同じフォーマット（メルカリ本命/楽天本命/値下がりウォッチ/所感、データ基準の時刻注記付き）で honmei_notes/ に保存する。**手順と道具は 2026-07-11 にリポジトリへ永続化済み: 手順書 = リポジトリ直下の CLAUDE.md、スキャン = `python scripts/honmei_scan.py`、検死 = `python scripts/honmei_autopsy.py <id>...`**（scratchpadに作り直さないこと）。抽出ロジック: 人気機種（30日15〜20本以上 or 7日4〜5本以上）×割安度、出品タイトルでヘッド単品・シャフト・ジャンク除外。関連: [[mercari-flea-source]] [[honmei-genbutsu-check]] [[flip-inventory]]
