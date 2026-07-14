# -*- coding: utf-8 -*-
"""楽天の最安個体をライブ取得してURL付きで表示する。

「今日の本命」のウォッチ品照合用。history.db の used_min は取得サイクル数時間分
遅れる（2026-07-14: G440 LST 44,980円が捕捉から確認までの間に売れた）ため、
値下がりウォッチや買いライン判定は必ずこれでライブ確認する。

  python scripts/rakuten_spot.py ping_g440lst fw_tm_qi10
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from golf_price.catalog import CATALOG_BY_KEY
from golf_price.normalize import detect_head_only, is_lefty, is_parts_junk, normalize
from golf_price.scrapers import rakuten
from golf_price.service import _catalog_match

keys = sys.argv[1:] or ["ping_g440lst"]
for key in keys:
    if key not in CATALOG_BY_KEY:
        print(f"{key}: カタログに無いキー")
        continue
    m = CATALOG_BY_KEY[key]
    print(f"\n##### {m.brand} {m.label}（{m.keyword} 中古）#####")
    out = []
    try:
        for l in rakuten.search(m.keyword + " 中古", pages=1):
            if not l.is_used or l.price < 8000:
                continue
            if is_parts_junk(l.title) or detect_head_only(normalize(l.title)) or is_lefty(l.title):
                continue
            if not _catalog_match(l.title, m):
                continue
            out.append(l)
    except Exception as e:
        print("  取得失敗:", e)
        continue
    out.sort(key=lambda l: l.price)
    for l in out[:4]:
        print(f"  ¥{l.price:,} | {l.title[:80]}")
        print(f"    {l.url}")
        print(f"    店: {l.shop}")
