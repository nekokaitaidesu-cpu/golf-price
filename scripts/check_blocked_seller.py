# -*- coding: utf-8 -*-
"""ブロック指定した出品者が本当にアプリから消えているかを確認する。

  python scripts/check_blocked_seller.py                    # 既定の検索語で確認
  python scripts/check_blocked_seller.py "ピン G425 MAX ドライバー" ...

ブロックは normalize.BLOCKED_SELLERS に **プロフィールURLの数字**（= sellerId）で
書く。フィルタは mercari.py のスクレイパ層（search_recent_raw と _to_listing の
両方）に入れてあるので、人気ランキング・本命候補・LINE通知・激アツの全経路に効く。

追加のしかた:
  https://jp.mercari.com/user/profile/187241371 → "187241371" を BLOCKED_SELLERS へ
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.normalize import BLOCKED_SELLERS, is_blocked_seller
from golf_price.scrapers import mercari

KWS = sys.argv[1:] or [
    "ピン G425 MAX ドライバー", "ピン G425 MAX フェアウェイウッド",
    "テーラーメイド ステルス ドライバー", "ピン G410 ユーティリティ",
    "テーラーメイド SIM2 MAX フェアウェイウッド", "ピン G430 フェアウェイウッド",
]

print(f"ブロック中の出品者: {sorted(BLOCKED_SELLERS)}\n")

leaked, total, hit_raw = [], 0, 0
for kw in KWS:
    for st in ("STATUS_ON_SALE", "STATUS_SOLD_OUT"):
        # フィルタ後（アプリが実際に見る経路）
        items, _ = mercari.search_recent_raw(kw, st, price_min=3000, max_pages=2,
                                             stop_before=time.time() - 120 * 86400)
        total += len(items)
        leaked += [i for i in items if is_blocked_seller(i.get("sellerId"))]
        # フィルタ前（生のページ）— 対象が実際に出品しているかを見る
        raw, _ = mercari._search_page(kw, st, "SORT_CREATED_TIME", "ORDER_DESC",
                                      price_min=3000)
        hits = [i for i in raw if is_blocked_seller(i.get("sellerId"))]
        hit_raw += len(hits)
        for i in hits[:3]:
            print(f"  [生] {kw} / {st[7:]:<8} ¥{int(i.get('price') or 0):>7,} "
                  f"seller={i.get('sellerId')} | {(i.get('name') or '')[:44]}")

print(f"\n生の検索で見つかったブロック対象の出品: {hit_raw}件")
print(f"フィルタ後に残ってしまった件数（0であるべき）: {len(leaked)}件")
print(f"フィルタ後の総取得件数: {total}件")
print("\nRESULT:", "PASS" if not leaked else f"FAIL — {len(leaked)}件すり抜け")
sys.exit(1 if leaked else 0)
