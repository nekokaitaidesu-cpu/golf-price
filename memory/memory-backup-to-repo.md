---
name: memory-backup-to-repo
description: auto-memory はローカルにしか無いので golf-price の memory/ にコピーして引き継ぐ。scripts/backup_memory.py と RECOVERY.md
metadata: 
  node_type: memory
  type: project
  originSessionId: 99dcfbfc-5429-41ca-bb5d-61cb9a7540e1
  modified: 2026-09-19T01:05:36.982Z
---

2026-09-19、ユーザーが「PCが壊れても別PCで引き継げるか」を点検して整備した。

- **auto-memory の本体は `%USERPROFILE%\.claude\projects\C--Users-User-Claude-golf-price\memory`（ローカルのみ）**。
  `python scripts/backup_memory.py` でリポジトリの `memory/` にコピーする（公開リポなので鍵・メールの混入を検査してからコピーする作り）
- **日次の「今日の本命」手順9（メモ保存）に組み込み済み**（2026-09-19・ユーザー指示）。
  `python scripts/backup_memory.py --commit` を毎日回す。**差分が無ければ何もしない**ので毎日叩いてよい。
  `memory/` だけをパス指定で commit するので、本命メモやカタログの編集は巻き込まない
- 新PCでの復旧手順は **`RECOVERY.md`**（clone → data ブランチ取り込み → 楽天/LINEの鍵を取り直し →
  タスク `honmei-notify` を15分おきで登録 → `memory/` をローカルへ戻す）
- 初期の本命メモ 7/7〜8/11 の31本が未コミットだったので同日コミット済み

**まだバックアップされていないもの: ゴルフ利益計算.xlsm**（仕入れ台帳）。公開リポには置けないので
Googleドライブ等へ手でコピーが必要（.xlsx で保存するとマクロが消える → [[profit-calc-workbook]]）。
関連: [[honmei-notes]]
