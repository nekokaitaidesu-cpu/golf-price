# -*- coding: utf-8 -*-
"""説明文パターンの誤検出テスト用コーパスを作る／検査する。

部品単品の検出パターン（normalize.detect_head_only_desc）は
2026-07から何度もすり抜け修正を入れているが、**完品を落とす方が痛い**ため
「新パターンが完品を巻き込まないか」を実データで測る必要がある。

使い方:

  # 1) コーパス採取（販売中の出品の説明文を .cache/descs.json に貯める）
  python scripts/desc_corpus.py fetch "PING G410 ドライバー" "Qi10 MAX ドライバー" -n 20

  # 2) 現行検出器でコーパスを判定（★が付いた件を目視して正誤を確かめる）
  python scripts/desc_corpus.py check

  # 3) 任意の正規表現を現行と比較（新パターンの誤検出候補だけを出す）
  python scripts/desc_corpus.py diff "(ドライバー|ウッド)\\s*の?\\s*ヘッドで[、,]"

キャッシュは追記式なので、fetch を重ねるほどテストが強くなる。
"""
import argparse
import json
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from golf_price.cache import CACHE_DIR
from golf_price.normalize import detect_head_only_desc, normalize
from golf_price.scrapers.mercari import _dpop, search_recent_raw

CORPUS = os.path.join(CACHE_DIR, "descs.json")


def load() -> dict:
    if os.path.exists(CORPUS):
        with open(CORPUS, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(d: dict) -> None:
    with open(CORPUS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def item_detail(item_id: str) -> dict:
    url = "https://api.mercari.jp/items/get"
    r = requests.get(url, params={"id": item_id},
                     headers={"DPoP": _dpop(url, "GET"), "X-Platform": "web",
                              "User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    return r.json().get("data") or {}


def cmd_fetch(args) -> None:
    corpus = load()
    todo: list[tuple[str, str]] = []
    for kw in args.keywords:
        items, _ = search_recent_raw(kw, "STATUS_ON_SALE", max_pages=1,
                                     stop_before=time.time() - 120 * 86400)
        got = 0
        for i in items:
            iid = i.get("id") or ""
            if not iid.startswith("m") or iid in corpus:
                continue
            todo.append((iid, i.get("name") or ""))
            got += 1
            if got >= args.n:
                break
        print(f"{kw}: 新規{got}件")

    for iid, title in todo:
        try:
            d = item_detail(iid)
        except requests.RequestException as e:
            print(f"  {iid} 取得失敗 {e}")
            continue
        corpus[iid] = {"title": title, "price": d.get("price"),
                       "desc": d.get("description") or ""}
        time.sleep(1.2)
    save(corpus)
    print(f"コーパス合計 {len(corpus)} 件 → {CORPUS}")


def cmd_check(args) -> None:
    corpus = load()
    hit = [(k, v) for k, v in corpus.items()
           if detect_head_only_desc(normalize(v["desc"]))]
    print(f"コーパス {len(corpus)} 件 / 現行検出器が単品と判定 {len(hit)} 件")
    for k, v in hit:
        print(f"  ★ {v['title'][:52]} | {k}")
        print(f"     {' '.join(v['desc'].split())[:150]}")


def cmd_diff(args) -> None:
    pat = re.compile(args.pattern)
    corpus = load()
    new_only = []
    for k, v in corpus.items():
        nd = normalize(v["desc"])
        old = detect_head_only_desc(nd)
        if pat.search(nd) and not old:
            new_only.append((k, v))
    print(f"コーパス {len(corpus)} 件 / 新パターンだけが拾う（＝誤検出候補）"
          f" {len(new_only)} 件")
    for k, v in new_only:
        print(f"  ? {v['title'][:52]} | ¥{v['price']} | {k}")
        m = pat.search(normalize(v["desc"]))
        s = normalize(v["desc"])
        print(f"     …{s[max(0, m.start() - 60):m.end() + 40]}…")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("keywords", nargs="+")
    f.add_argument("-n", type=int, default=15, help="1キーワードあたり採取数")
    f.set_defaults(func=cmd_fetch)
    c = sub.add_parser("check")
    c.set_defaults(func=cmd_check)
    d = sub.add_parser("diff")
    d.add_argument("pattern")
    d.set_defaults(func=cmd_diff)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
