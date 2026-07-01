@echo off
rem クラウド(GitHub Actions)が毎日更新したデータをPCに取り込む。
rem ローカルアプリを開く前にこれを実行すると、PC側も最新の価格・履歴になる。
cd /d "%~dp0"
echo クラウドの最新データを取得中...
git fetch origin data --depth 1 --quiet
if errorlevel 1 (
  echo [!] data ブランチがまだありません（初回クラウド実行の完了後に使えます）
  exit /b 1
)
git checkout origin/data -- history.db .cache
git reset --quiet
echo 同期完了。ローカルアプリも最新データになりました。
