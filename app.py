"""ゴルフクラブ中古価格調査アプリ — Webサーバー（FastAPI）。

起動: python -m uvicorn app:app --reload --port 8000
ブラウザで http://localhost:8000 を開く（PC・スマホ両対応のレスポンシブUI）。
"""

import time
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from golf_price import service, cache, registry
from golf_price.spec import MODELS, DEFAULT_MODEL_KEY
from golf_price.catalog import CATALOG, CATALOG_BY_KEY, CATEGORIES

app = FastAPI(title="ゴルフクラブ中古価格調査")

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/api/models")
def api_models():
    """利用可能な機種一覧（カタログ＋組み込み＋ユーザー追加）。"""
    out = [{"key": m.key, "label": f"{m.brand} {m.label}", "user_added": False,
            "catalog": True, "category": m.category, "grades": []} for m in CATALOG]
    out += [{"key": k, "label": m.label, "user_added": False, "catalog": False,
             "category": "driver", "grades": [{"key": g.key, "label": g.label} for g in m.grades]}
            for k, m in MODELS.items()]
    for k, e in registry.load().items():
        out.append({"key": k, "label": e["label"], "user_added": True, "catalog": False,
                    "category": "driver", "grades": []})
    return out


@app.get("/api/categories")
def api_categories():
    """カテゴリ一覧（キー・表示名・カタログ機種数）。"""
    counts = {}
    for m in CATALOG:
        counts[m.category] = counts.get(m.category, 0) + 1
    return [{"key": k, "label": lbl, "count": counts.get(k, 0)} for k, lbl in CATEGORIES]


@app.get("/api/ranking")
def api_ranking():
    """カタログ全機種の試算損益（キャッシュ利用、無ければ計算）を良い順に返す。"""
    rows = []
    for m in CATALOG:
        key = f"{m.key}_p2"
        d = cache.get(key)
        if not d:
            d = service.run(model_key=m.key, pages=2)
            cache.put(key, d)
        g = d.get("gap") or {}
        rows.append({
            "key": m.key, "label": f"{m.brand} {m.label}", "brand": m.brand, "year": m.year,
            "used_min": d["used"]["min"], "used_avg": d["used"]["avg"],
            "used_count": d["used"]["count"],
            "flea_avg": d["flea_sold"]["avg"], "flea_count": d["flea_sold"]["count"],
            "profit": g.get("profit"),
        })
    # 損益の良い順（profit降順）。Noneは末尾。
    rows.sort(key=lambda r: (r["profit"] is None, -(r["profit"] or 0)))
    return {"fee_rate": service.FEE_RATE, "shipping": service.SHIPPING, "rows": rows}


@app.get("/api/ranking/one")
def api_ranking_one(key: str, refresh: bool = False):
    """ランキング1機種ぶんを計算（フロントの逐次ロード用）。refresh=trueでキャッシュ無視。"""
    if key not in CATALOG_BY_KEY:
        return JSONResponse({"error": "unknown"}, status_code=400)
    ck = f"{key}_p2"
    d = None if refresh else cache.get(ck)
    if not d:
        d = service.run(model_key=key, pages=2)
        d["_fetched_at"] = __import__("time").strftime("%Y-%m-%d %H:%M")
        cache.put(ck, d)
    m = CATALOG_BY_KEY[key]
    g = d.get("gap") or {}
    cheapest = (d.get("used_samples") or [{}])[0]   # 最安の出品（価格昇順の先頭）
    return {
        "key": key, "label": f"{m.brand} {m.label}", "brand": m.brand, "year": m.year,
        "category": m.category,
        "used_min": d["used"]["min"], "used_avg": d["used"]["avg"], "used_count": d["used"]["count"],
        "used_min_shop": cheapest.get("shop", ""),
        "used_min_url": cheapest.get("url", ""),
        "used_min_head_only": cheapest.get("head_only", False),
        "flea_avg": d["flea_sold"]["avg"], "flea_count": d["flea_sold"]["count"],
        "profit": g.get("profit"),
    }


@app.post("/api/models/add")
def api_add_model(url: str = Query(...)):
    """ゴルフパートナーURLからモデルを追加。"""
    try:
        entry = registry.add_from_url(url.strip())
        return {"ok": True, "model": entry}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.delete("/api/models/{key}")
def api_remove_model(key: str):
    registry.remove(key)
    return {"ok": True}


@app.get("/api/search")
def api_search(
    model: str = Query(DEFAULT_MODEL_KEY),
    pages: int = Query(2, ge=1, le=5),
    refresh: bool = Query(False),
):
    """検索して①中古平均・②最安値・③フリマ実売平均を集計して返す。"""
    if model not in CATALOG_BY_KEY and model not in MODELS and model not in registry.load():
        return JSONResponse({"error": f"unknown model: {model}"}, status_code=400)

    key = f"{model}_p{pages}"
    if not refresh:
        cached = cache.get(key)
        if cached:
            cached["_cached"] = True
            return cached

    t0 = time.time()
    result = service.run(model_key=model, pages=pages)
    result["_cached"] = False
    result["_elapsed_sec"] = round(time.time() - t0, 1)
    result["_fetched_at"] = time.strftime("%Y-%m-%d %H:%M")
    cache.put(key, result)
    return result


@app.get("/history.csv")
def history_csv():
    """蓄積した価格履歴CSVをダウンロード（Googleスプレッドシート取り込み用）。"""
    from golf_price.history import CSV_PATH
    if CSV_PATH.exists():
        return FileResponse(CSV_PATH, media_type="text/csv", filename="golf_price_history.csv")
    return JSONResponse({"error": "履歴がまだありません"}, status_code=404)


@app.get("/api/history")
def api_history(key: str):
    """1機種の価格推移（日付順）を返す。"""
    import sqlite3
    from golf_price.history import DB_PATH, COLUMNS
    if not DB_PATH.exists():
        return {"key": key, "rows": []}
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        f"SELECT {', '.join(COLUMNS)} FROM price_history WHERE key=? ORDER BY date", (key,)
    ).fetchall()
    con.close()
    return {"key": key, "rows": [dict(zip(COLUMNS, r)) for r in rows]}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
