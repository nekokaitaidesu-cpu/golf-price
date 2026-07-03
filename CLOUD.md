# ☁ クラウド自動更新（GitHub Actions）

毎日の価格取得を**クラウドで自動実行**するようにした記録。PCの電源に依存しない。

## 仕組み
- `.github/workflows/refresh.yml` が**1日8回(2/10/12/14/16/18/20/22時 JST)**に起動
- 全機種を取得（中古＝**楽天公式API**／フリマ＝**メルカリ検索API**（障害時Yahoo落札に退避）／一部ゴルフパートナー）
- スマホ用サイトを生成し **`golf-price-mobile`** へ自動push（デプロイキー使用）
  → https://nekokaitaidesu-cpu.github.io/golf-price-mobile/
- **前日比の基準は「2:00の回だけ」記録**（`--record-history`）。10:00〜22:00の回は価格・サイトを
  更新するが履歴には触れない＝前日比の基準は2:00のまま不動。基準回の判定は cron `0 17 * * *`。
- `history.db` と `.cache/` を **`data` ブランチ**に保存（force-push、空DBなら保護のためスキップ）
- 所要 約40分/回（実測）。公開リポなので Actions は無料・無制限

## 楽天API（2026新版）
- 楽天は検索ページを datacenter IP からブロックするため、公式API `openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search` を使用
- 認証：`applicationId`（UUID）＋ `accessKey`（`pk_…`）＋ Referer/Origin ヘッダ（アプリ登録の許可ドメイン `nekokaitaidesu-cpu.github.io`）
- GitHub Secrets：`RAKUTEN_APP_ID` / `RAKUTEN_ACCESS_KEY`
- ローカル実行時は `rakuten_keys.json`（gitignore）から読む。無ければ従来スクレイプにフォールバック
- relevance＋価格昇順のハイブリッド取得で、旧スクレイプと近い数字（中古最安・平均・中央値）を維持

## PCのローカルアプリを最新にする
**`start.bat` を実行するだけ**。起動時にクラウドの最新データ（`data` ブランチの `history.db` と `.cache`）を
自動で取り込んでからアプリを立ち上げる（オフライン時は既存データで起動）。

## 注意
- **ローカルの毎日2:00タスク「GolfPriceRefresh」は無効化済み**（クラウドと二重にpushすると競合するため）。
  戻したい場合：`Enable-ScheduledTask -TaskName GolfPriceRefresh`
- 手動でクラウド実行：GitHubの Actions →「refresh」→ Run workflow（`limit` に数字を入れると先頭N機種だけのテスト実行）
- `mobile/index.html` や `build_site.py` を更新したら**コミット＆push**すればクラウドの出力に反映される
