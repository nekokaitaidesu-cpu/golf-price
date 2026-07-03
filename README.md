# ⛳ ゴルフクラブ中古価格調査アプリ

サイト横断でモデル名の表記ゆれを**名寄せ**し、グレード別に
**①中古価格の平均 ②最安値 ③メルカリ平均**を集計するWebアプリ。

対象機種（第1弾）: **キャロウェイ PARADYM Ai SMOKE ドライバー**
（MAX / MAX D / MAX FAST / ◆◆◆ Triple Diamond / Ti 340 Mini を自動分類）

## 特長
- **呼び名のバラつきを吸収**: `キャロウェイ/Callaway`、`パラダイム/PARADYM`、
  `Ai SMOKE/Aiスモーク`、`◆◆◆/トリプルダイヤモンド/Triple Diamond` などを同一視。
- **別モデルの混入を除外**: 「MAX」と「MAX FAST」「MAX D」「340 Mini」を区別して集計。
- **PC・スマホ両対応**（レスポンシブ。1つのアプリで両方使える）。
- 取得結果は30分キャッシュ（毎回スクレイピングしない）。

## セットアップ
```bash
pip install -r requirements.txt
```

## 起動
```bash
python -m uvicorn app:app --port 8000
```
ブラウザで http://localhost:8000 を開く。

### スマホからも使う（同じWi-Fi内）
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```
スマホのブラウザで `http://<PCのIPアドレス>:8000` を開く
（PCのIPは `ipconfig` で確認）。

## 構成
```
app.py                     FastAPI（/api/search, /api/models, 静的配信）
golf_price/
  spec.py                  機種・グレードの名寄せルール（機種追加はここ）
  normalize.py             文字列正規化＋機種/グレード判定（名寄せの中核）
  service.py               検索→名寄せ→分類→統計集計
  cache.py                 結果の簡易ファイルキャッシュ
  scrapers/
    base.py                共通の型・HTTPセッション・レート制御
    rakuten.py             楽天市場 検索スクレイパー（data-track-price を利用）
static/index.html          フロントエンド（グレード別カードUI）
test_live.py               実データでの動作確認スクリプト
```

## データソースの状況
| 指標 | ソース | 状態 |
|---|---|---|
| ①中古平均 / ②最安値 | 楽天市場（中古出品・キーワード名寄せ） | ✅ 実装済み |
| ①中古平均 / ②最安値 | ゴルフパートナー（model_codeで機種固有・高精度） | ✅ 実装済み |
| ③メルカリ平均 | メルカリ「売り切れ 最新5件」＋「販売中の最安2件」（障害時はYahoo落札相場に退避） | ✅ 実装済み |
| 差額（買→売） | ①中古ショップ平均 − ③メルカリ平均 を自動計算 | ✅ 実装済み |

③は落札相場ページ内の `__NEXT_DATA__` JSON を解析（ブラウザ不要）。
スリーブ/tip/アダプター等の部品・スパムは除外し、圧縮キー照合で当該機種の本体のみ集計。

### グレード（自動分類）
MAX / MAX D / MAX FAST / **◆◆◆ MAX（Triple Diamond MAX）** /
◆◆◆ Triple Diamond / Ti 340 Mini / 無印
※ ゴルフパートナーの `model_code` を `spec.py` の各 `Grade.gp_model_code` に
登録すると、そのグレードを機種固有IDでピンポイント取得できる（現在 ◆◆◆ MAX = 460220）。

## 損益ランキング（カテゴリ選択式）
画面の「📊 損益ランキング」→ **カテゴリ（ドライバー / フェアウェイウッド / ユーティリティ /
アイアン / すべて）を選択** → そのカテゴリだけ試算損益の良い順に一覧表示。
機種数が多いほど取得に時間がかかるため、必要なカテゴリだけ取得できる。行クリックで詳細へ。
対象ブランド：テーラーメイド/キャロウェイ/ピン/タイトリスト/ブリヂストン/スリクソン/
ゼクシオ/コブラ/ミズノ/プロギア/ヤマハ/本間/PXG/NEXGEN（2019〜現行・計約130機種）。
各機種は `golf_price/catalog.py` の `CATALOG` に `category="fw"` 等を付けて追加できる。
- 試算 = メルカリ平均 × 0.9 − 送料1700 − 中古最安値
- 集計はキーワード方式（楽天=中古／メルカリ=実売）＋圧縮キー照合で派生モデルを分離
- 各機種30分キャッシュ。初回は順次計算して表示（数分）

機種の追加・編集は `golf_price/catalog.py` の `CATALOG` に1行足すだけ
（ブランド・検索KW・required/excludes 圧縮キー）。

## 毎日の自動取得＆履歴蓄積
- Windowsタスクスケジューラ「**GolfPriceRefresh**」が**毎日2:00**に `refresh_rankings.py` を実行し、
  全機種の価格を取得して30分かけてキャッシュを更新（`StartWhenAvailable`で取りこぼし時は次回起動時に実行）。
- キャッシュ保持は約26時間。日中はランキング・詳細が**待ち時間ゼロ**で表示される。
- 取得結果は **`history.db`（SQLite）＋ `history.csv`** に1日1行/機種で**蓄積**（時系列）。
  - CSVダウンロード：`http://localhost:8000/history.csv`（BOM付きUTF-8）
  - 機種別の推移API：`/api/history?key=<機種キー>`
- 手動実行：`python refresh_rankings.py`（ログは `refresh.log`）
- タスク削除：`Unregister-ScheduledTask -TaskName GolfPriceRefresh`

### Googleスプレッドシートに取り込む（任意）
`history.csv` を Google スプレッドシートで「ファイル → インポート」するだけ。
（毎日自動で値が増えるので、最新を見たい時に取り込み直す）

## 機種の追加方法

### A. 画面からURLで追加（おすすめ・コード不要）
画面上部の入力欄に、**ゴルフパートナーの `model_code` 付きURL**を貼って「＋モデル追加」。
- URLから `model_code` を抽出し、その機種だけをピンポイント取得（名寄せ不要）
- モデル名はページから自動命名、`user_models.json` に保存され次回も残る
- 例: `https://www.golfpartner.jp/shop/usedgoods/h010001_m9_b156522/?search=x&model_code=460220`

### B. コードで組み込みモデルを追加（多サイト横断・グレード分類が必要なとき）
`golf_price/spec.py` の `MODELS` に `ModelSpec` を1つ追加。
ブランド/モデル/シリーズ/種別の別名と、グレード判定ルールを書けば、
楽天のキーワード検索を名寄せしつつグレード自動分類できる。

## 注意
各サイトの利用規約に従い、**個人利用・低頻度アクセス**（数秒に1回・キャッシュ活用）で
運用すること。商用公開時は各サイトの規約・公式API利用を別途確認のこと。
