# -*- coding: utf-8 -*-
"""本命候補の検死: items/get で説明文・いいね・状態を確認し、写真もDLする。

「今日の本命教えて」ワークフローの第2段。使い方:

  python scripts/honmei_autopsy.py m12345 m67890 ...
  python scripts/honmei_autopsy.py m12345 --photos 8   # 写真DL枚数(既定5)

- 説明文の部品単品判定（detect_head_only_desc）と売却済みを表示
- 写真を .cache/photos/<id>_<n>.jpg に保存 → Readツールで目視すること
  （説明文に何も書かないヘッド単品が実在する。ホーゼルの空きが最終判定）
"""
import argparse
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.normalize import detect_head_only_desc, normalize
from golf_price.scrapers.mercari import _dpop, search_recent_raw

PHOTO_DIR = os.path.join(CACHE_DIR, "photos")


def item_detail(item_id: str) -> dict:
    url = "https://api.mercari.jp/items/get"
    r = requests.get(url, params={"id": item_id},
                     headers={"DPoP": _dpop(url, "GET"), "X-Platform": "web",
                              "User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    return r.json().get("data") or {}


def auction_info(item_id: str, name: str) -> dict:
    """オークション形式かどうかを検索APIの raw から引く。

    **items/get には auction フィールドが無い**（2026-09-11に判明）。
    検索APIの raw にだけ {bidDeadline, totalBid, highestBid, initialPrice} が入る。
    そのため ID指定の検死だけで追いかけると 🔨 が落ち、入札で競り上がった価格を
    「出品者が値上げした」と読み違える。実際に2026-09-08〜09のPARADYM 7Wで
    2日連続やらかした（13,001→14,001→14,201 は入札。ユーザーが落札した）。

    商品名をそのまま検索語にして id 一致で拾う。見つからなければ空 dict。
    """
    try:
        rows, _ = search_recent_raw(" ".join((name or "").split())[:60],
                                    "STATUS_ON_SALE", max_pages=1)
    except Exception:
        return {}
    for raw in rows:
        if raw.get("id") == item_id:
            return raw.get("auction") or {}
    return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+", help="メルカリ商品ID (m...)")
    ap.add_argument("--photos", type=int, default=5, help="写真DL枚数")
    args = ap.parse_args()
    os.makedirs(PHOTO_DIR, exist_ok=True)

    for mid in args.ids:
        try:
            d = item_detail(mid)
        except requests.RequestException as e:
            print(f"== {mid}: 取得失敗 {e}")
            continue
        desc = d.get("description") or ""
        head = detect_head_only_desc(normalize(desc))
        photos = d.get("photos") or []
        hours = round((time.time() - int(d.get("created") or 0)) / 3600, 1)
        cond = (d.get("item_condition") or {}).get("name")
        # items/get には auction が無いので検索raw側から引く（auction_info 参照）
        auction = auction_info(mid, d.get("name") or "")
        print(f"== {d.get('name', '')[:48]} [{mid}]")
        print(f"   ¥{int(d.get('price') or 0):,} status={d.get('status')} "
              f"いいね={d.get('num_likes')} 状態={cond} 出品{hours}h前 "
              f"写真{len(photos)}枚 部品検出={'★単品!' if head else 'なし'}")
        # 出品者の出品数。2026-09-12実測(n=13)で、ヘッド単品と判定した8件は中央386件・
        # 200件以上が6/8、完品と判定した5件は中央59件・200件以上が0/5に分かれた。
        # とくに**説明文が無言だったヘッド単品3件は全て249件以上**で、
        # 業者アカウントはテンプレ説明を使い開示しない傾向がある。
        # まだ n=13 なので落とす条件には使わず、**写真を見る優先度**として出す。
        seller = d.get("seller") or {}
        nsell = seller.get("num_sell_items") or 0
        mark = "  ⚠業者級（説明文が短いなら写真を必ず見る）" if nsell >= 200 else ""
        print(f"   出品者: {(seller.get('name') or '')[:16]} / 出品中{nsell}件{mark}")
        if auction:
            print(f"   🔨オークション（即決不可・入札制） 締切={auction.get('bidDeadline')} "
                  f"入札{auction.get('totalBid')}件 現在額={auction.get('highestBid')} "
                  f"開始額={auction.get('initialPrice')}")
            print("      ※価格の上昇は『出品者の値上げ』ではなく入札。"
                  "上限は 実売中央×0.9−送料 から先に決めて機械的に")
        print(f"   説明: {' '.join(desc.split())[:260]}")
        for i, url in enumerate(photos[:args.photos]):
            path = os.path.join(PHOTO_DIR, f"{mid}_{i}.jpg")
            try:
                r = requests.get(url, timeout=20,
                                 headers={"User-Agent": "Mozilla/5.0",
                                          "Referer": "https://jp.mercari.com/"})
                r.raise_for_status()
                with open(path, "wb") as f:
                    f.write(r.content)
            except requests.RequestException as e:
                print(f"   写真{i}: 失敗 {e}")
        print(f"   写真 → {PHOTO_DIR}\\{mid}_*.jpg")
        time.sleep(1.2)


if __name__ == "__main__":
    main()
