# 🔧 新しいPCへの引き継ぎ手順（このPCが壊れたとき）

2026-09-19 作成。**「別のPCで引き継げるか」を実際に点検して、足りない分を埋めた記録**でもある。

まず知っておくこと: **クラウドの集計（GitHub Actions・1日8回）はPCと無関係に動き続ける**。
PCが壊れても価格データは溜まり続けるので、慌てる必要はない。止まるのは **LINE通知（本命スナイパー）だけ**。

---

## 0. 何がどこにあるか

| もの | 保管先 | PCが壊れたら |
|---|---|---|
| コード一式・CLAUDE.md・workflows | GitHub `nekokaitaidesu-cpu/golf-price`（公開） | 無事 |
| 本命メモ `honmei_notes/` | 同上 | 無事（7/7以降すべて） |
| auto-memory `memory/` | 同上（`scripts/backup_memory.py` でコピー） | 無事。**ただし最新はローカルなので、まめにコピーすること** |
| 価格データ `history.db` / `.cache` | GitHub の **`data` ブランチ**（クラウドが毎回force-push） | 無事 |
| スマホ用サイト | GitHub `golf-price-mobile`（公開） | 無事 |
| 楽天APIキー・デプロイキー（クラウド用） | GitHub Secrets | 無事（クラウドは動き続ける） |
| **楽天APIキー（ローカル用 `rakuten_keys.json`）** | このPCだけ | **消える** → 楽天の管理画面から取り直す |
| **LINEのトークン（環境変数）** | このPCだけ | **消える** → LINE Developers から取り直す |
| **タスクスケジューラ `honmei-notify`** | このPCだけ | **消える** → 下記4で登録し直す |
| **`user_models.json`**（自分で足した機種） | このPCだけ（gitignore） | 消える（1KB・作り直せる） |
| **ゴルフ利益計算.xlsm** | このPCだけ | **消える**。公開リポには置けないので、**Googleドライブに手でコピーしておくこと**（→ 5） |

---

## 1. リポジトリを置く

新PCに Git と **Python 3.13** を入れてから:

```bat
cd C:\Users\<ユーザー名>\Claude
git clone https://github.com/nekokaitaidesu-cpu/golf-price.git
cd golf-price
pip install -r requirements.txt
```

パスが `C:\Users\User\Claude\golf-price` でなくなる場合、CLAUDE.md とこの文書のパス表記だけ読み替えれば動く
（コード側は相対パスで解決している）。

## 2. 価格データを取り込む

```bat
start.bat
```

`start.bat` が `data` ブランチから `history.db` と `.cache` を取ってきてからアプリを起動する。
http://localhost:8000 が開けば復旧完了。手でやるなら:

```bat
git fetch origin data --depth 1
git checkout origin/data -- history.db .cache
git reset --quiet
```

## 3. 鍵を入れ直す

### 楽天API（ローカル実行用）
[楽天ウェブサービス](https://webservice.rakuten.co.jp/) のアプリ管理から `applicationId` と `accessKey` を取り、
リポジトリ直下に `rakuten_keys.json` を作る（gitignore 済み）:

```json
{"app_id": "（UUID）", "access_key": "pk_…"}
```

※ GitHub Secrets に登録済みの値は**読み出せない**ので、必ず管理画面から取り直す。
※ 無ければ従来のスクレイプに自動フォールバックするが、精度が落ちる。

### LINE（本命スナイパー用）
[LINE Developers](https://developers.line.biz/console/) の Messaging API チャネルから取得して:

```bat
setx LINE_CHANNEL_TOKEN "（チャネルアクセストークン）"
setx LINE_USER_ID "（Uで始まるユーザーID）"
```

設定後はコマンドプロンプトを開き直す（`setx` は新しいプロセスから有効）。

## 4. LINE通知のタスクを登録し直す

このPCでの設定（2026-09-19時点）:

- タスク名: **`honmei-notify`**
- 実行: `C:\Users\User\Claude\golf-price\notify_honmei.bat`
- トリガー: **15分おきに繰り返し**（初回 23:03 開始）

コマンドで作るなら:

```bat
schtasks /create /tn honmei-notify /tr "C:\Users\<ユーザー名>\Claude\golf-price\notify_honmei.bat" /sc minute /mo 15
```

動作確認は `python notify_honmei.py` を1回手で叩く。通知の全文は `notify.log` に残る。

※ `GolfPriceRefresh`（ローカルの定期集計）は**無効のままでよい**。集計はクラウドがやっている。

## 5. 利益計算ブックと自分で足した機種

- **ゴルフ利益計算.xlsm**: 公開リポジトリには置けない（仕入れ値の台帳）。
  **Googleドライブか外付けに手でコピーしておく**。xlsx で保存するとマクロが消えるので必ず **.xlsm** のまま
- **user_models.json**: 無くてもアプリは動く。必要なら新PCで足し直す

## 6. auto-memory を新PCに戻す

リポジトリの `memory/` を、Claude Code が読む場所にコピーする:

```bat
xcopy /Y memory\*.md "%USERPROFILE%\.claude\projects\C--Users-User-Claude-golf-price\memory\"
```

**逆方向（ローカル → リポジトリ）は定期的にやること**:

```bat
python scripts/backup_memory.py          REM 差分をコピー（鍵の混入を検査してから）
python scripts/backup_memory.py --check  REM 差分だけ見る
git add memory && git commit -m "memory: バックアップ" && git push
```

`memory/` はリポジトリのスナップショットで、**生きている本体はローカル側**。
コピーを忘れると、その間に足したメモはPCと一緒に消える。

---

## 復旧できたかの確認

1. `start.bat` → http://localhost:8000 が開く
2. `python scripts/honmei_scan.py` が候補を出す（約10分）
3. `python scripts/rakuten_spot.py fw_ping_g430max` が楽天の値を返す（＝鍵が効いている）
4. `python notify_honmei.py` でLINEが届く
5. `memory/` が `%USERPROFILE%\.claude\...\memory` に入っている
