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
from golf_price.scrapers.mercari import _dpop

PHOTO_DIR = os.path.join(CACHE_DIR, "photos")


def item_detail(item_id: str) -> dict:
    url = "https://api.mercari.jp/items/get"
    r = requests.get(url, params={"id": item_id},
                     headers={"DPoP": _dpop(url, "GET"), "X-Platform": "web",
                              "User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    return r.json().get("data") or {}


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
        auction = {k: v for k, v in d.items() if "auction" in k.lower() and v}
        print(f"== {d.get('name', '')[:48]} [{mid}]")
        print(f"   ¥{int(d.get('price') or 0):,} status={d.get('status')} "
              f"いいね={d.get('num_likes')} 状態={cond} 出品{hours}h前 "
              f"写真{len(photos)}枚 部品検出={'★単品!' if head else 'なし'}")
        if auction:
            print(f"   auction: {json.dumps(auction, ensure_ascii=False)[:160]}")
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
