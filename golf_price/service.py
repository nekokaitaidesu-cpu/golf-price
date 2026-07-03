"""検索→名寄せ→グレード分類→統計集計のオーケストレーション。"""

import re
import statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from .spec import MODELS, DEFAULT_MODEL_KEY, ModelSpec
from .normalize import (analyze, normalize, detect_head_only, is_parts_junk,
                        compact, extract_loft, looks_like_iron_set)
from .scrapers import rakuten, golfpartner, yahoo_auction, mercari
from .scrapers.base import Listing
from . import flea
from .catalog import DriverModel, CATALOG, CATALOG_BY_KEY

# ドライバー本体としてあり得ない安値（部品等）を弾く下限
MIN_FLEA_PRICE = 3000
MIN_USED_PRICE = 5000

# ③メルカリ平均の採用件数（新鮮な相場にするため件数を絞る）
MERCARI_SOLD_RECENT = 5   # 売り切れ: 新着順の最新N件
MERCARI_ACTIVE_MIN = 2    # 販売中: 最安N件（現在の売値の下限）
# 上記プール(5+2)のうち安い方N件だけを平均に採用。
# 高値の売切が平均を押し上げ「実際に売れる金額より高め」になるのを防ぐ。
MERCARI_AVG_TAKE = 3

# 試算パラメータ（フリマ手数料・送料）
FEE_RATE = 0.10      # フリマ手数料10%（中古最安に対して ×0.9）
SHIPPING = 1700      # 送料（円）


def _gap(used_base, flea_base, basis="min_avg") -> dict | None:
    """試算: フリマ売値×(1−手数料) − 送料 − 中古仕入れ。

    basis="min_avg": 中古最安×フリマ平均（ドライバー等の既定）
    basis="median" : 中古中央値×フリマ中央値（アイアン用。単品/世代差にブレない）
    """
    if used_base is None or flea_base is None:
        return None
    profit = round(flea_base * (1 - FEE_RATE) - SHIPPING - used_base)
    return {
        "profit": profit,
        "used_base": used_base,
        "flea_base": flea_base,
        "basis": basis,
        "fee_rate": FEE_RATE,
        "shipping": SHIPPING,
    }


def _build_keywords(spec: ModelSpec) -> list[str]:
    """検索に投げるキーワード（代表的な表記をいくつか）。"""
    brand = spec.brand[0]
    model = spec.model[0]
    return [
        f"{brand} {model} Ai SMOKE ドライバー 中古",
        f"パラダイム Ai SMOKE ドライバー 中古",
    ]


def collect_listings(spec: ModelSpec, pages: int = 2) -> list[Listing]:
    """全ソースから出品を収集し、名寄せ・グレード判定して該当機種のみ返す。"""
    raw: list[Listing] = []
    seen = set()
    for kw in _build_keywords(spec):
        for lst in rakuten.search(kw, pages=pages):
            key = (lst.source, lst.url, lst.price)
            if key in seen:
                continue
            seen.add(key)
            raw.append(lst)

    matched: list[Listing] = []
    for lst in raw:
        info = analyze(lst.title, spec)
        if not info["matched"]:
            continue
        lst.grade_key = info["grade_key"] or ""
        lst.grade_label = info["grade_label"] or ""
        lst.head_only = info["head_only"]
        matched.append(lst)

    # --- ゴルフパートナー: model_code がある グレードは固有IDで正確に取得 ---
    for g in spec.grades:
        if not g.gp_model_code:
            continue
        for lst in golfpartner.search_by_model_code(g.gp_model_code, pages=1):
            key = (lst.source, lst.url, lst.price)
            if key in seen:
                continue
            seen.add(key)
            # model_code 一致＝グレード確定なので分類をスキップして直接付与
            lst.grade_key = g.key
            lst.grade_label = g.label
            lst.head_only = detect_head_only(normalize(lst.title))
            matched.append(lst)

    # --- フリマ実売（メルカリ売り切れ・新着順）: キーワード検索→名寄せ＆ノイズ除去 ---
    for kw in _build_keywords(spec):
        try:
            closed = mercari.search_closed(kw.replace(" 中古", ""),
                                           price_min=MIN_FLEA_PRICE)
        except mercari.MercariError:
            closed = yahoo_auction.search_closed(kw.replace(" 中古", ""), pages=2)
        for lst in closed:
            if lst.price < MIN_FLEA_PRICE or is_parts_junk(lst.title):
                continue
            key = (lst.source, lst.url, lst.price)
            if key in seen:
                continue
            info = analyze(lst.title, spec)
            if not info["matched"]:
                continue
            seen.add(key)
            lst.grade_key = info["grade_key"] or ""
            lst.grade_label = info["grade_label"] or ""
            lst.head_only = info["head_only"]
            # sold=True は scraper 側で設定済み
            matched.append(lst)

    return matched


def _stats(prices: list[int]) -> dict:
    if not prices:
        return {"count": 0, "avg": None, "min": None, "max": None, "median": None}
    return {
        "count": len(prices),
        "avg": round(statistics.mean(prices)),
        "min": min(prices),
        "max": max(prices),
        "median": round(statistics.median(prices)),
    }


def _samples(items: list[Listing], limit: int = 40) -> list[dict]:
    return sorted(
        ({"price": i.price, "title": i.title, "url": i.url, "shop": i.shop,
          "loft": i.loft, "head_only": i.head_only, "sold": i.sold}
         for i in items),
        key=lambda x: x["price"],
    )[:limit]


def summarize(listings: list[Listing]) -> dict:
    """グレード別・全体の統計を作る。

    返す3指標:
      used_avg      : ①中古価格 平均（販売中の中古出品）
      used_min      : ②最安値（中古出品の最小）
      flea_sold_avg : ③フリマ実売 平均（sold=True の実売データ。今はソース未実装なら None）
    """
    by_grade = defaultdict(list)
    for lst in listings:
        by_grade[(lst.grade_key, lst.grade_label)].append(lst)

    grades_out = []
    for (gkey, glabel), items in sorted(by_grade.items(), key=lambda kv: kv[0][0]):
        used_items = [i for i in items if i.is_used and not i.sold]
        sold_items = [i for i in items if i.sold]
        used = _stats([i.price for i in used_items])
        sold = _stats([i.price for i in sold_items])
        grades_out.append({
            "grade_key": gkey,
            "grade_label": glabel,
            "used": used,
            "flea_sold": sold,
            "gap": _gap(used["min"], sold["avg"]),
            "head_only_count": sum(1 for i in items if i.head_only),
            "used_samples": _samples(used_items),
            "flea_samples": _samples(sold_items),
        })

    all_used = _stats([i.price for i in listings if i.is_used and not i.sold])
    all_sold = _stats([i.price for i in listings if i.sold])
    return {
        "total_listings": len(listings),
        "headline": {
            "used_avg": all_used["avg"],     # ①
            "used_min": all_used["min"],     # ②
            "flea_sold_avg": all_sold["avg"],  # ③
            "gap": _gap(all_used["min"], all_sold["avg"]),
        },
        "overall_used": all_used,
        "overall_flea_sold": all_sold,
        "grades": grades_out,
    }


def _loft_sort_key(loft: str):
    try:
        return (0, float(loft))
    except ValueError:
        return (1, 0.0)  # "不明" 等は末尾


def _loft_block(loft_label: str, items: list[Listing]) -> dict:
    used_items = [i for i in items if i.is_used and not i.sold]
    sold_items = [i for i in items if i.sold]
    used = _stats([i.price for i in used_items])
    sold = _stats([i.price for i in sold_items])
    return {
        "loft": loft_label,
        "used": used,
        "flea_sold": sold,
        "gap": _gap(used["min"], sold["avg"]),
        "head_only_count": sum(1 for i in items if i.head_only),
        "used_samples": _samples(used_items),
        "flea_samples": _samples(sold_items),
    }


def _run_user_model(entry: dict, pages: int) -> dict:
    """ユーザー追加モデル（model_code固定・単一機種）をロフト別に集計。"""
    # 全ロフトを網羅するため全ページ巡回（中古ショップ＝ゴルフパートナー）
    listings = golfpartner.fetch_all(entry["gp_model_code"], path=entry.get("gp_path"))
    for l in listings:
        l.head_only = detect_head_only(normalize(l.title))

    # フリマ実売（メルカリ売り切れ）をラベルから検索して取り込み
    kw, req, brands = flea.params_from_label(entry["label"])
    sold_listings = flea.collect(kw, req, brands, min_price=MIN_FLEA_PRICE, pages=2)
    for l in sold_listings:
        l.head_only = detect_head_only(normalize(l.title))
    listings = listings + sold_listings

    by_loft = defaultdict(list)
    for l in listings:
        by_loft[l.loft or "不明"].append(l)

    # 先頭は「すべて」、以降はロフト昇順
    blocks = [_loft_block("すべて", listings)]
    for loft in sorted(by_loft.keys(), key=_loft_sort_key):
        blocks.append(_loft_block(loft, by_loft[loft]))

    return {
        "model_key": entry["key"],
        "model_label": entry["label"],
        "user_added": True,
        "mode": "loft",
        "total_listings": len(listings),
        "lofts": blocks,
        # 既定（すべて）の見出し
        "headline": {
            "used_avg": blocks[0]["used"]["avg"],
            "used_min": blocks[0]["used"]["min"],
            "flea_sold_avg": blocks[0]["flea_sold"]["avg"],
            "gap": blocks[0]["gap"],
        },
    }


# カテゴリごとの「クラブ種別」を示す語（いずれか含む必要）
CLUB_TOKENS = {
    "driver": ["ドライバー", "driver"],
    "fw": ["フェアウェイ", "フェアウエイ", "fairway"],
    "ut": ["ユーティリティ", "utility", "ハイブリッド", "hybrid", "レスキュー", "rescue"],
    "iron": ["アイアン", "iron"],
    "chipper": ["チッパー", "chipper"],
}
# どのカテゴリでも除外したい別クラブ種別
_ALWAYS_EXCLUDE_CLUB = ["ウェッジ", "wedge", "パター", "putter"]


def _term_hit(term: str, c: str, n: str) -> bool:
    """1つのキー判定。'=' 始まりは単語境界マッチ（M5/F9等の短い型番用）、
    それ以外は圧縮文字列の部分一致。"""
    if term.startswith("="):
        t = term[1:].lower()
        return re.search(r"(?<![0-9a-z])" + re.escape(t) + r"(?![0-9a-z])", n) is not None
    return compact(term) in c


# ---- 誤マッチ低減ガード（世代番号・年式） ----------------------------------
# 「シリーズ語＋世代番号」（xxio14 / ゼクシオ12 / m5 等）の検出。
# ロフト(10.5°/9度)・本数(5本/5S=5本Sフレックス)・番手(7番)・
# クラブ種別(4u/3w/7i等)の数字は世代とみなさない。
_SERIES_GEN = re.compile(
    r"([a-z]+|[ァ-ヶー]+)[ ]?(\d{1,2})"
    r"(?![\d.])(?![iuwh])(?![srxal](?![0-9a-z]))(?![ ]?[°度本番])"
)
# 同一シリーズの英字/カタカナ表記ゆれ（世代番号の照合用）
_SERIES_SYNONYMS = [
    ("xxio", "ゼクシオ"),
    ("stealth", "ステルス"),
    ("paradym", "パラダイム"),
    ("rogue", "ローグ"),
    ("epic", "エピック"),
]
_gen_expect_cache: dict[str, dict[str, set[str]]] = {}


def _gen_expectations(m: DriverModel) -> dict[str, set[str]]:
    """機種定義（label/keyword/required）から期待する世代番号を抽出（例 xxio→{14}）。"""
    exp = _gen_expect_cache.get(m.key)
    if exp is not None:
        return exp
    texts = [m.label, m.keyword]
    for r in m.required:
        texts.extend(alt.lstrip("=") for alt in r.split("|"))
    exp = {}
    for t in texts:
        for s, d in _SERIES_GEN.findall(normalize(t)):
            exp.setdefault(s, set()).add(d.lstrip("0") or "0")
    for a, b in _SERIES_SYNONYMS:
        merged = exp.get(a, set()) | exp.get(b, set())
        if merged:
            exp[a] = merged
            exp[b] = merged
    _gen_expect_cache[m.key] = exp
    return exp


def _generation_ok(n: str, m: DriverModel) -> bool:
    """タイトル中の世代番号が機種の世代と食い違っていないか
    （XXIO14 の検索結果に XXIO8 が混ざる等を除外）。番号が読めない出品は通す。"""
    exp = _gen_expectations(m)
    if not exp:
        return True
    hits = _SERIES_GEN.findall(n)
    if not hits:
        return True
    for series, gens in exp.items():
        found = {d.lstrip("0") or "0" for s, d in hits
                 if s == series or s.endswith(series)}
        if found and not (found & gens):
            return False
    return True


_YEAR_TOKEN = re.compile(r"(20[0-2][0-9])(年.*)?")
_model_words_cache: dict[str, set[str]] = {}


def _model_words(m: DriverModel) -> set[str]:
    """年式の文脈判定に使う機種側の語彙（label/keyword/required＋カテゴリ語）。"""
    ws = _model_words_cache.get(m.key)
    if ws is None:
        texts = [m.label, m.keyword, "モデル", "年式"]
        texts += CLUB_TOKENS.get(m.category, [])
        for r in m.required:
            texts.extend(alt.lstrip("=") for alt in r.split("|"))
        ws = {w for t in texts for w in normalize(t).split() if len(w) >= 2}
        _model_words_cache[m.key] = ws
    return ws


def _word_related(nb: str, words: set[str]) -> bool:
    return any(nb == w or (len(w) >= 3 and w in nb) or (len(nb) >= 3 and nb in w)
               for w in words)


def _year_ok(n: str, m: DriverModel) -> bool:
    """カタログ年式より明確に古い「モデル年」しか書かれていない出品を除外
    （2021年 APEX のページに『APEX 2014年モデル』が混ざる等）。
    シャフト等の年（Tour AD DI-6(2020) 等）と区別するため、
    『◯◯年〜』表記か、機種語/カテゴリ語に隣接した年だけをモデル年とみなす。
    カタログ年式より新しい年は購入年・セール文言があり得るため許容する。"""
    if not re.fullmatch(r"20\d\d", m.year or ""):
        return True
    toks = n.split()
    years: list[int] = []
    for i, w in enumerate(toks):
        mt = _YEAR_TOKEN.fullmatch(w)
        if not mt:
            continue
        y = int(mt.group(1))
        if mt.group(2):  # 「2014年モデル」「2014年製」等
            years.append(y)
            continue
        prev_w = toks[i - 1] if i > 0 else ""
        next_w = toks[i + 1] if i + 1 < len(toks) else ""
        words = _model_words(m)
        if _word_related(prev_w, words) or _word_related(next_w, words):
            years.append(y)
    if not years:
        return True
    return max(years) >= int(m.year) - 1


def _catalog_match(title: str, m: DriverModel) -> bool:
    """キー照合。required/excludes の各要素は '|' で代替(OR)を書ける。
    要素を '=' で始めると単語境界マッチ（例 '=m5' は SIM2 や TM50 に誤マッチしない）。
    カテゴリ（driver/fw/ut/iron）の種別語を要求し、他カテゴリ語は除外する。
    """
    c = compact(title)
    n = normalize(title)
    # 当該カテゴリの種別語が必須
    club = [compact(t) for t in CLUB_TOKENS.get(m.category, CLUB_TOKENS["driver"])]
    if not any(t in c for t in club):
        return False
    # チッパーは「アイアン型/パター型チッパー」等の表記があるためクロス除外しない
    if m.category != "chipper":
        # 他カテゴリの種別語が入っていたら別クラブ品として除外
        for cat, toks in CLUB_TOKENS.items():
            if cat == m.category:
                continue
            if any(compact(t) in c for t in toks):
                return False
        if any(compact(t) in c for t in _ALWAYS_EXCLUDE_CLUB):
            return False
    # アイアンは「セット同士」で比較したいので単品（バラ売り1本）を除外し、
    # セットらしい出品のみ採用する（最安が単品で歪むのを防ぐ）
    if m.category == "iron" and not looks_like_iron_set(title):
        return False
    for x in m.excludes:
        if any(_term_hit(alt, c, n) for alt in x.split("|")):
            return False
    for r in m.required:
        if not any(_term_hit(alt, c, n) for alt in r.split("|")):
            return False
    # 世代番号・年式の食い違いを弾く（同名の旧世代モデル混入対策）
    return _generation_ok(n, m) and _year_ok(n, m)


def _drop_low_outliers(items: list[Listing], frac: float = 0.35) -> list[Listing]:
    """中央値の frac 未満の極端な安値を除外（別モデル/部品/ジャンクの誤マッチ対策）。"""
    if len(items) < 4:
        return items
    med = statistics.median([i.price for i in items])
    floor = med * frac
    return [i for i in items if i.price >= floor]


def run_catalog_model(m: DriverModel, pages: int = 2) -> dict:
    """カタログ機種（キーワード方式）を 中古=楽天 / フリマ=メルカリ で集計。"""
    # チッパーは安価なので下限を下げる
    min_u = 2500 if m.category == "chipper" else MIN_USED_PRICE
    min_f = 1500 if m.category == "chipper" else MIN_FLEA_PRICE
    # 高速化: 楽天(中古)とメルカリ(フリマ)を並列取得（別サイトなので安全）
    def _fetch_used():
        out = []
        for l in rakuten.search(m.keyword + " 中古", pages=1):
            if (l.is_used and not is_parts_junk(l.title)
                    and l.price >= min_u and _catalog_match(l.title, m)):
                l.loft = extract_loft(l.title)
                out.append(l)
        return out

    def _flea_ok(l):
        # 採用5+2件と少数なので、ヘッドのみ出品も除外（完品の売値相場に揃える）
        return (l.price >= min_f and not is_parts_junk(l.title)
                and not detect_head_only(normalize(l.title))
                and _catalog_match(l.title, m))

    def _fetch_sold():
        """③メルカリ平均: 売り切れ最新5件＋販売中の最安2件（新鮮な実売相場）。"""
        try:
            sold_raw = mercari.search_closed(m.keyword, price_min=min_f)
            sold = [l for l in sold_raw if _flea_ok(l)][:MERCARI_SOLD_RECENT]  # 新着順
            # 販売中は「直近実売の中央値×0.45」を下限にして部品/カバー帯を飛ばす
            floor = min_f
            if sold:
                floor = max(min_f, round(statistics.median(
                    [l.price for l in sold]) * 0.45))
            active_raw = mercari.search_active(m.keyword, price_min=floor)
        except mercari.MercariError:
            # メルカリが応答しない時だけYahoo落札相場に退避
            return [l for l in yahoo_auction.search_closed(m.keyword, pages=1, per=50)
                    if _flea_ok(l)]
        active = [l for l in active_raw if _flea_ok(l)]                    # 価格昇順
        # プール(売切最新5＋販売中最安2)から安い方3件だけを平均に使う。
        # 安値側を採るためフィルタをすり抜けた部品（シャフト等）が刺さりやすく、
        # 先にプール中央値×0.5未満の極端な安値を落としてから選抜する。
        pool = _drop_low_outliers(sold + active[:MERCARI_ACTIVE_MIN], frac=0.5)
        pool.sort(key=lambda l: l.price)
        return pool[:MERCARI_AVG_TAKE]

    with ThreadPoolExecutor(max_workers=2) as ex:
        fu, fs = ex.submit(_fetch_used), ex.submit(_fetch_sold)
        used, sold = fu.result(), fs.result()

    # 極端な安値（別モデル誤マッチ・部品）を除外してから集計
    used = _drop_low_outliers(used)
    sold = _drop_low_outliers(sold)

    u = _stats([x.price for x in used])
    f = _stats([x.price for x in sold])
    # アイアンは単品/世代差にブレない「中央値ベース」、それ以外は「最安×平均」
    if m.category == "iron":
        gap = _gap(u["median"], f["median"], basis="median")
    else:
        gap = _gap(u["min"], f["avg"], basis="min_avg")
    return {
        "model_key": m.key,
        "model_label": f"{m.brand} {m.label}",
        "brand": m.brand,
        "year": m.year,
        "catalog": True,
        "mode": "single",
        "total_listings": len(used) + len(sold),
        "used": u,
        "flea_sold": f,
        "gap": gap,
        "headline": {
            "used_avg": u["avg"], "used_min": u["min"],
            "flea_sold_avg": f["avg"], "gap": gap,
        },
        "used_samples": _samples(used),
        "flea_samples": _samples(sold),
    }


def run(model_key: str = DEFAULT_MODEL_KEY, pages: int = 2,
        grade_filter: list[str] | None = None) -> dict:
    if model_key in CATALOG_BY_KEY:
        return run_catalog_model(CATALOG_BY_KEY[model_key], pages=pages)
    if model_key in MODELS:
        spec = MODELS[model_key]
        listings = collect_listings(spec, pages=pages)
        if grade_filter:
            listings = [l for l in listings if l.grade_key in grade_filter]
        result = summarize(listings)
        result["model_key"] = spec.key
        result["model_label"] = spec.label
        return result

    # ユーザー追加モデル
    from . import registry
    user = registry.load()
    if model_key in user:
        return _run_user_model(user[model_key], pages)
    raise KeyError(f"unknown model: {model_key}")
