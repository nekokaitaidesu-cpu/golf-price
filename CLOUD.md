# ☁ クラウド自動更新（GitHub Actions）

毎日の価格取得を**クラウドで自動実行**するようにした記録。PCの電源に依存しない。

## 仕組み
- `.github/workflows/refresh.yml` が**毎日2:00(JST)**に起動（cron `0 17 * * *` UTC）
- 全機種を取得（中古＝**楽天公式API**／フリマ＝Yahoo落札／一部ゴルフパートナー）
- スマホ用サイトを生成し **`golf-price-mobile`** へ自動push（デプロイキー使用）
  → https://nekokaitaidesu-cpu.github.io/golf-price-mobile/
- 前日比の基準 `history.db` と `.cache/` を **`data` ブランチ**に保存（force-push）
- 所要 約40分（実測）

## 楽天API（2026新版）
- 楽天は検索ページを datacenter IP からブロックするため、公式API `openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search` を使用
- 認証：`applicationId`（UUID）＋ `accessKey`（`pk_…`）＋ Referer/Origin ヘッダ（アプリ登録の許可ドメイン `nekokaitaidesu-cpu.github.io`）
- GitHub Secrets：`RAKUTEN_APP_ID` / `RAKUTEN_ACCESS_KEY`
- ローカル実行時は `rakuten_keys.json`（gitignore）から読む。無ければ従来スクレイプにフォールバック
- relevance＋価格昇順のハイブリッド取得で、旧スクレイプと近い数字（中古最安・平均・中央値）を維持

## PCのローカルアプリを最新にする
クラウドが更新したデータをPCに取り込む：
```
sync.bat
```
（`data` ブランチから `history.db` と `.cache` を取得。ローカルアプリを開く前に実行）

## 注意
- **ローカルの毎日2:00タスク「GolfPriceRefresh」は無効化済み**（クラウドと二重にpushすると競合するため）。
  戻したい場合：`Enable-ScheduledTask -TaskName GolfPriceRefresh`
- 手動でクラウド実行：GitHubの Actions →「refresh」→ Run workflow（`limit` に数字を入れると先頭N機種だけのテスト実行）
- `mobile/index.html` や `build_site.py` を更新したら**コミット＆push**すればクラウドの出力に反映される
