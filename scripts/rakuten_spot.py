# -*- coding: utf-8 -*-
"""楽天の最安個体をライブ取得してURL付きで表示する。

「今日の本命」のウォッチ品照合用。history.db の used_min は取得サイクル数時間分
遅れる（2026-07-14: G440 LST 44,980円が捕捉から確認までの間に売れた）ため、
値下がりウォッチや買いライン判定は必ずこれでライブ確認する。

  python scripts/rakuten_spot.py ping_g440lst fw_tm_qi10
  python scripts/rakuten_spot.py ping_g440lst --no-spec   # 商品ページを見ない(速い)

**安い順5件は商品ページの「種別」欄まで開く**（2026-09-11に足した）。
中古ショップの商品ページには「種別: ヘッド単品／完品」がそのまま書いてあり、
題名にも検索APIの返り値にも出てこない。ここを見ずに 2026-09-04 と 09-10 の
2回、ピン G410 UT 10,450円を「シャフト欄が『-』＝情報不足だが1.76倍」として
推奨しかけた。実際は 種別=ヘッド単品・重量246g（完品なら約370g）で、
『-』は情報が無いのではなく**該当する部品が無い**という意味だった。
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from golf_price.catalog import CATALOG_BY_KEY
from golf_price.normalize import detect_head_only, is_lefty, is_parts_junk, normalize
from golf_price.scrapers import rakuten
from golf_price.scrapers.base import make_session
from golf_price.service import _catalog_match

# 商品ページのスペック表。「商品詳細 種別 ◯◯」「重量 ◯g」「ランク ◯」の形で入る。
# 種別が「ヘッド単品」なら完品の分母で測ってはいけない。
_SHUBETSU = re.compile(r"商品詳細\s*種別\s*(\S+)")
_WEIGHT = re.compile(r"重量\s*([0-9]{2,3})\s*g")
_HEADLESS_HINT = re.compile(r"ヘッド単品|ヘッドのみ|ヘッド単体|シャフト無し|シャフトなし")


def page_spec(url: str) -> str:
    """商品ページから 種別／重量 を引く。取れなければ空文字。"""
    try:
        html = make_session().get(url, timeout=30).text
    except Exception as e:
        return f"    ⚠ ページ取得失敗: {e}"
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    kind = _SHUBETSU.search(text)
    gram = _WEIGHT.search(text)
    bits = []
    if kind:
        bits.append(f"種別={kind.group(1)}")
    if gram:
        bits.append(f"重量={gram.group(1)}g")
    if not bits:
        return "    種別: ページから読めず（自分でURLを開くこと）"
    line = "    " + " / ".join(bits)
    kindtxt = kind.group(1) if kind else ""
    if _HEADLESS_HINT.search(kindtxt):
        line += ("\n    🔴 ヘッド単品。完品の中央値で割らないこと"
                 "（分母をヘッド側に切り替える）")
    elif gram and int(gram.group(1)) < 300:
        line += ("\n    ⚠ 300g未満。完品にしては軽い"
                 "（ヘッド単体はDR約200g・FW/UT約240g）")
    return line


ap = argparse.ArgumentParser()
ap.add_argument("keys", nargs="*", default=["ping_g440lst"])
ap.add_argument("--no-spec", action="store_true", help="商品ページを開かない")
args = ap.parse_args()
keys = args.keys or ["ping_g440lst"]
for key in keys:
    if key not in CATALOG_BY_KEY:
        print(f"{key}: カタログに無いキー")
        continue
    m = CATALOG_BY_KEY[key]
    print(f"\n##### {m.brand} {m.label}（{m.keyword} 中古）#####")
    out = []
    try:
        # 2026-08-22修正: pages=1 だと**最安を取りこぼす**。楽天の既定並びは価格順では
        # ないため、1ページ(30件)では価格分布の下端に届かない。実際この日、
        # history.db が2日continuedで 24,970円を記録していた G430 MAX に対し、
        # pages=1 の本スクリプトは 35,080円を「最安」と表示していた
        # （集計側は同機種で28〜41件を見ている）。買いライン判定の入口なので母数を揃える
        for l in rakuten.search(m.keyword + " 中古", pages=3):
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
    print(f"  （該当 {len(out)}件 / 安い順5件）")
    for l in out[:5]:
        print(f"  ¥{l.price:,} | {l.title[:80]}")
        print(f"    {l.url}")
        print(f"    店: {l.shop}")
        if not args.no_spec:
            print(page_spec(l.url))
