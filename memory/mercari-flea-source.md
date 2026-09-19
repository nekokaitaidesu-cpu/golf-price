---
name: mercari-flea-source
description: ③フリマ実売はメルカリ検索API直叩き（DPoP自己署名）に置換済み。仕組みと調整ポイント
metadata: 
  node_type: memory
  type: project
  originSessionId: 8a2d3f2f-3ba0-4d81-b096-2e7f82575d38
---

2026-07-03、③フリマ実売のソースをYahoo落札相場からメルカリに置き換えた（ユーザーの希望。ヤフオク/ヤフーフリマ/ラクマは不要とのこと）。

- 取得は `golf_price/scrapers/mercari.py`。Playwright不要で、jp.mercari.com のフロントが使う
  `https://api.mercari.jp/v2/entities:search` をPOST（匿名・使い捨てES256鍵でDPoP JWTを自己署名、
  `cryptography` 依存）。1機種2リクエスト・約3秒。メルカリShops(BEYOND)は相場が歪むため除外。
- メルカリ平均の構成（ユーザー指定）: 「売り切れ最新5件＋販売中の最安2件」のプールから
  **安い方3件だけ**を平均に採用（2026-07-04、「平均が実際に売れる金額より高め」との指摘で変更）。
  定数は `service.py` の `MERCARI_SOLD_RECENT` / `MERCARI_ACTIVE_MIN` / `MERCARI_AVG_TAKE`。
  販売中の下限は売切中央値×0.45。さらに安値選抜の前にプール中央値×0.5未満を除外
  （安値側を採るとフィルタをすり抜けたシャフト単体等が刺さりやすいため）。
- 売り切れはAPIの新着順（＝出品日時順）ではなく `updated` 降順に並べ替えて「最近売れた順」にしている。
- メルカリ特有の「〜ドライバー ヘッド」（のみ、と書かないヘッド単体出品）が多いので
  `normalize.detect_head_only` を末尾ヘッド/ヘッド＋にも反応するよう拡張済み。
- API失敗時（ブロック等）は機種ごとにYahoo落札相場へ自動退避。連続5回失敗で
  サーキットブレーカーが作動し以降は即Yahoo退避（`mercari._FAIL_STREAK`）。
- GitHub Actions からのAPI疎通は 2026-07-03 に実証済み（件数パターン5+2で確認）。
  ブロックされた場合はログに「メルカリ検索失敗」が並び、shop欄が「ヤフオク落札」になる。
- 🔥激アツピックアップ（2026-07-04）: 販売中最安が直近売切中央値より大幅に安い出品＝
  メルカリ→メルカリ転売候補。`service.py` の hot_picks（益1,000円以上・売切3件以上の機種のみ）、
  `/api/hot`（PC）、data.json の `mercari_hot`（スマホ #hot=1）。
  ランキング列は「せどり益」という名前（ユーザー命名リクエストによる）。
- ヘッド単体出品の検出は normalize.detect_head_only に集約
  （末尾ヘッド/ヘッド＋/ヘッド本体/ヘッド+ロフト度数）。すり抜けを見つけたらここに追加する。
- 定番の誤マッチパターン（2026-07-04にTS3←GTS3で発覚、26機種修正）:
  required の圧縮キーが「別モデル名やシャフト名の内側」に部分一致する
  （ts3⊂gts3、speed⊂speeder、05⊂tour105、02⊂2023）。対策は catalog.py で
  ①excludes に上位語を追加（gts3等）②短い/数字キーは「=キー」の単語境界マッチに変える。
  横断検出は「.cacheのサンプルタイトルで、キーが単一トークン内の英数字列の内側でのみ
  ヒットしているものを列挙」するスキャナで可能（過検出が多いので目視で仕分ける）。
