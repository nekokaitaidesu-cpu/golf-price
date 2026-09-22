---
name: catalog-duplicate-detectors-blind
description: 重複・包含の検査はアイアンとショートウッドで空振りしていた。相互マッチの双子キーも素通り。修正後に相互重複42対・包含75対が表面化（大半がアイアン）
metadata: 
  node_type: memory
  type: project
  originSessionId: 99dcfbfc-5429-41ca-bb5d-61cb9a7540e1
  modified: 2026-09-22T15:50:12.957Z
---

2026-09-23、楽天表に T100 が中央82,750と76,000の2行、G410 PLUS も2行出ていたのを追って判明。

**2つの穴（両方修正済み・commit 682b5c86）:**
1. **相互マッチの双子キー**は `find_duplicates()`（条件の完全一致のみ）にも
   `find_swallowing()`（`not` 条件で相互マッチが落ちる）にも掛からない → `find_mutual_duplicates()` を新設
2. **keyword をそのまま当てる検査は、アイアンとショートウッドで常に False**。
   `_catalog_match` がアイアンに `looks_like_iron_set()`（「5-P」「6本セット」等）、
   ショートウッドに番手を要求するため → `_probe_title()` を挟んで当てる形に修正

**修正後の実数: 相互重複 42対（driver19／iron19／fw2／ut2）・包含 75対（iron71／fw3／ut1）。
アイアンだけで約90対が未着手**（1対ずつ「どちらを残すか」を実売で確かめる必要があるので日次の片手間では危険）。

**Why:** 双子キーは実売本数・販売中を二重計上し、同じ機種で中央値が2つ出る。
アイアンの中央値が日ごとに振れていた一因（T100 は 66,000⇔82,750）。

**How to apply:** カタログに行を足したら `find_duplicates()` / `find_swallowing()` /
`find_mutual_duplicates()` の**3つ**を見る。検査を書いたら「既知の1件を入れて検出されるか」を必ず確かめる
（8月から動いていた検査が、実は1件も拾えていなかった）。
関連: [[gloire-series-swallow]] [[bare-token-excludes-trap]] [[thin-denominator-fake-cheap]]
