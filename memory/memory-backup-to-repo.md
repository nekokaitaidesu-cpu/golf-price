---
name: memory-backup-to-repo
description: auto-memory はローカルにしか無いので golf-price の memory/ にコピーして引き継ぐ。scripts/backup_memory.py と RECOVERY.md
metadata: 
  node_type: memory
  type: project
  originSessionId: 99dcfbfc-5429-41ca-bb5d-61cb9a7540e1
  modified: 2026-09-19T01:03:54.181Z
---

2026-09-19、ユーザーが「PCが壊れても別PCで引き継げるか」を点検して整備した。

- **auto-memory の本体は `%USERPROFILE%\.claude\projects\C--Users-User-Claude-golf-price\memory`（ローカルのみ）**。
  `python scripts/backup_memory.py` でリポジトリの `memory/` にコピーする（公開リポなので鍵・メールの混入を検査してからコピーする作り）
- メモを書き足した日は、ついでにこれを回して `git add memory && commit && push` する
- 新PCでの復旧手順は **`RECOVERY.md`**（clone → data ブランチ取り込み → 楽天/LINEの鍵を取り直し →
  タスク `honmei-notify` を15分おきで登録 → `memory/` をローカルへ戻す）
- 初期の本命メモ 7/7〜8/11 の31本が未コミットだったので同日コミット済み

**まだバックアップされていないもの: ゴルフ利益計算.xlsm**（仕入れ台帳）。公開リポには置けないので
Googleドライブ等へ手でコピーが必要（.xlsx で保存するとマクロが消える → [[profit-calc-workbook]]）。
関連: [[honmei-notes]]
