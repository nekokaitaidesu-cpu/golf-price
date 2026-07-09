# -*- coding: utf-8 -*-
"""本命スナイパー: 人気加速中の機種に「新着の割安出品」が出た瞬間LINEに通知。

夜間バッチの本命抽出は逆選択（残っている割安 = 訳あり）に勝てないため、
こちらは速度で勝負する:
  1. .cache/popularity.json から回転のいい機種をウォッチリスト化（毎朝自動更新）
  2. 各機種の販売中を新着順に取得し、直近に出品されたものだけを見る
  3. 実売中央値に対して十分安い・状態ランク良好・ヘッド単品でない出品を抽出
  4. 既知IDを .cache/notify_state.json に記録し、初見のみ LINE にプッシュ

いいね勢が値下げ待ちを始める前の「出品直後」だけが対象。
写真の傷までは見られないので、通知には必ず「現物写真を確認」と添える。

LINE は TP07ハンターと同じ Messaging API push。
環境変数 LINE_CHANNEL_TOKEN / LINE_USER_ID が無ければ通知内容を表示するだけ（ドライラン）。

使い方:
  python notify_honmei.py            # 1回スキャン（タスクスケジューラ向け）
  python notify_honmei.py --dry-run  # LINE送信せず表示のみ・stateも更新しない
初回実行は現在の出品を既知登録するだけで通知しない（シード）。
"""

import argparse
import json
import os
import time

import requests

from golf_price.cache import CACHE_DIR
from golf_price.catalog import CATALOG
from golf_price.normalize import compact, detect_head_only_desc, normalize
from golf_price.popularity import (
    ITEM_URL, MIN_PRICE, MIN_PRICE_CHIPPER, _pick)
from golf_price.scrapers import mercari
from golf_price.scrapers.mercari import _dpop

HERE = os.path.dirname(os.path.abspath(__file__))
POP_PATH = os.path.join(CACHE_DIR, "popularity.json")
STATE_PATH = os.path.join(CACHE_DIR, "notify_state.json")

# --- ウォッチリスト選定 ---
MIN_SOLD_30D = 15       # 30日でこれ以上売れている、または
MIN_SOLD_7D = 4         # 直近7日でこれ以上売れている機種を監視
MIN_SELL_RATE = 0.55    # 売切率の下限（在庫過多の機種は除外）
MIN_MEDIAN = 8000       # 実売中央値がこれ未満の機種はノイズが多いので対象外
MAX_MODELS = 20         # 1スキャンあたりの監視機種数（API負荷の上限）

# --- 割安判定 ---
RATIO_MAX = 0.72        # 実売中央値のこの割合以下なら「割安」
RATIO_MIN = 0.35        # これ未満はほぼ確実に部品・別物（経験則）なので鳴らさない
COND_MAX = 6            # itemConditionId の許容上限。6=全部通知（傷ありも欲しい方針）。
                        # 絞りたくなったら 4（やや傷あり まで）に戻す
LOOKBACK_SEC = 2 * 3600  # 出品からこの時間以内の新着だけを見る（実行間隔より長めに）
MAX_ALERTS = 8          # 1回の通知に載せる最大件数

COND_LABEL = {1: "新品・未使用", 2: "未使用に近い", 3: "目立った傷なし",
              4: "やや傷あり", 5: "傷あり", 6: "状態悪い"}


def load_watchlist() -> list[dict]:
    """popularity.json から「回転がよく相場が立っている機種」を選ぶ。

    優先順: 直近7日の勢い（7日ペース/30日ペース比）→ 売切率。
    同一機種が複数キーで載っている場合は先勝ちで1つに絞る。
    重複判定は (カテゴリ, 圧縮ラベル)。ラベル文字列そのままだと
    「Qi10」(driver/fw同名) を潰しすぎ、「G430 ハイブリッド/G430ハイブリッド」
    (スペース違い) を見逃す。
    """
    with open(POP_PATH, encoding="utf-8") as f:
        pop = json.load(f)
    by_key = {m.key: m for m in CATALOG}
    picked: list[tuple[float, float, dict]] = []
    seen: set[tuple[str, str]] = set()
    for r in pop.get("rows", []):
        w7 = r.get("w7") or {}
        med = r.get("sold_price_median") or 0
        dedup = (r.get("category") or "", compact(r["label"]))
        if r["key"] not in by_key or dedup in seen:
            continue
        if med < MIN_MEDIAN or (r.get("sell_rate") or 0) < MIN_SELL_RATE:
            continue
        if r.get("sold", 0) < MIN_SOLD_30D and w7.get("sold", 0) < MIN_SOLD_7D:
            continue
        seen.add(dedup)
        pace30 = r["sold"] / 30 if r.get("sold") else 0
        momentum = (w7.get("sold", 0) / 7) / pace30 if pace30 else 0
        picked.append((momentum, r.get("sell_rate") or 0,
                       {"row": r, "model": by_key[r["key"]]}))
    picked.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [p[2] for p in picked[:MAX_MODELS]]


def scan_model(entry: dict, since: float) -> list[dict]:
    """1機種の販売中新着から通知候補を返す。"""
    m, row = entry["model"], entry["row"]
    median = row["sold_price_median"]
    min_price = MIN_PRICE_CHIPPER if m.category == "chipper" else MIN_PRICE
    raws, _ = mercari.search_recent_raw(
        m.keyword, "STATUS_ON_SALE", price_min=min_price,
        max_pages=1, stop_before=since)
    raw_by_id = {r.get("id"): r for r in raws}
    out = []
    for p in _pick(raws, m, min_price, since):
        if p["head_only"]:
            continue
        ratio = p["price"] / median
        if not (RATIO_MIN <= ratio <= RATIO_MAX):
            continue
        raw = raw_by_id.get(p["id"], {})
        cond = int(raw.get("itemConditionId") or 0)
        if cond > COND_MAX:
            continue
        out.append({
            "id": p["id"], "title": p["title"], "price": p["price"],
            "created": p["created"], "label": row["label"],
            "median": median, "ratio": ratio, "cond": cond,
            "sell_rate": row.get("sell_rate"),
            "w7_sold": (row.get("w7") or {}).get("sold"),
            # オークション形式（入札制）。即決購入できないので通知に明記する
            # （2026-07-09: SIM2がオークションだと知らずに通知してしまった）
            "auction": bool(raw.get("auction")),
        })
    return out


def item_detail(item_id: str) -> dict:
    """商品詳細（説明文・いいね数・販売状態）。失敗時は空dict。"""
    url = "https://api.mercari.jp/items/get"
    try:
        r = requests.get(
            url, params={"id": item_id},
            headers={"DPoP": _dpop(url, "GET"), "X-Platform": "web",
                     "User-Agent": "Mozilla/5.0"},
            timeout=15)
        r.raise_for_status()
        return r.json().get("data") or {}
    except (requests.RequestException, ValueError):
        return {}


def verify_candidate(c: dict) -> bool:
    """通知直前の最終チェック。落とすべき候補なら False。

    タイトルは実クラブ風でも説明文にだけ「ヘッド単品」と書く出品が多く
    （2026-07-08: 割安候補6件中3件）、タイトル検査だけでは罠を鳴らしてしまう。
    詳細が取れなかった場合は通知する（機会損失より未検証マーク付きで知らせる）。
    """
    d = item_detail(c["id"])
    if not d:
        c["likes"] = None
        return True
    if d.get("status") and d["status"] != "on_sale":
        return False
    if detect_head_only_desc(normalize(d.get("description") or "")):
        print(f"  除外（説明文がヘッド単品）: {c['title'][:40]}")
        return False
    c["likes"] = d.get("num_likes")
    return True


def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {"seen": {}}


def save_state(state: dict) -> None:
    # 古い既知IDは30日で掃除（無限に肥大しないように）
    cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    state["seen"] = {k: v for k, v in state["seen"].items() if v >= cutoff}
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def format_alert(a: dict) -> str:
    ago = int((time.time() - a["created"]) / 60)
    cond = COND_LABEL.get(a["cond"], "状態不明")
    likes = "説明文未検証" if a.get("likes") is None else f"いいね{a['likes']}"
    warns = ""
    if a.get("auction"):
        warns += "\n🔨オークション形式（即決不可・入札制）"
    # タイトルに「シャフト」を含む出品はシャフト単品の可能性がある
    # （2026-07-09: 「純正SRシャフト」表記のシャフト単品が通知をすり抜けた。
    #   カスタムシャフト装着の完品も同語を使うため、除外ではなく注意喚起に留める）
    if "シャフト" in a["title"]:
        warns += "\n⚠タイトルにシャフト表記 → 単品出品でないか説明文を確認"
    return (f"\n▼{a['label']}\n"
            f"¥{a['price']:,}（実売中央¥{a['median']:,}の{a['ratio']:.0%}）\n"
            f"{cond}｜{ago}分前出品｜{likes}｜7日{a['w7_sold']}本売れ{warns}\n"
            f"{a['title'][:40]}\n{ITEM_URL.format(id=a['id'])}")


def notify_line(alerts: list[dict]) -> bool:
    """TP07ハンターと同じ LINE Messaging API push。未設定なら False。"""
    token = os.environ.get("LINE_CHANNEL_TOKEN", "").strip()
    user = os.environ.get("LINE_USER_ID", "").strip()
    if not token or not user:
        return False
    text = ("⛳割安の新着出品！（写真の傷は必ず確認）"
            + "".join(format_alert(a) for a in alerts[:MAX_ALERTS]))[:4900]
    r = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json={"to": user, "messages": [{"type": "text", "text": text}]},
        timeout=20,
    )
    if r.status_code != 200:
        print(f"  LINE通知: 失敗 {r.status_code} {r.text[:120]}")
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="LINE送信せず表示のみ。stateも更新しない")
    args = ap.parse_args()

    watch = load_watchlist()
    print(f"監視 {len(watch)} 機種: "
          + " / ".join(e["row"]["label"] for e in watch[:5]) + " …")

    seeding = not os.path.exists(STATE_PATH)
    state = load_state()
    since = time.time() - LOOKBACK_SEC
    today = time.strftime("%Y-%m-%d")

    alerts: list[dict] = []
    for entry in watch:
        try:
            cands = scan_model(entry, since)
        except mercari.MercariError as e:
            print(f"  {entry['row']['label']}: スキップ（{e}）")
            continue
        for c in cands:
            if c["id"] in state["seen"]:
                continue
            state["seen"][c["id"]] = today
            if not seeding and verify_candidate(c):
                alerts.append(c)

    if seeding:
        print(f"初回シード: 既知 {len(state['seen'])} 件を登録（通知なし）")
    for a in alerts:
        print(format_alert(a))
    if alerts and not args.dry_run:
        if notify_line(alerts):
            print(f"LINE通知: 送信OK（{len(alerts)}件）")
        else:
            print(f"LINE通知: 未設定のため表示のみ（LINE_CHANNEL_TOKEN/LINE_USER_ID）")
    if not alerts and not seeding:
        print("新着の割安出品なし")
    if not args.dry_run:
        save_state(state)


if __name__ == "__main__":
    main()
