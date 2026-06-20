"""取得結果を時系列で蓄積する（SQLite ＋ CSV）。

毎日の自動更新（refresh_rankings.py）から呼ばれ、1日1行/機種で履歴を残す。
同じ日に再実行した場合は (date, key) で上書き（その日の最新値）。
history.csv は Google スプレッドシート等にそのまま取り込める。
"""

import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "history.db"
CSV_PATH = BASE / "history.csv"

COLUMNS = [
    "date", "key", "category", "label", "year",
    "used_count", "used_min", "used_avg", "used_median",
    "flea_count", "flea_avg", "profit", "fetched_at",
]


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS price_history (
            {", ".join(f'{col} TEXT' if col in ('date','key','category','label','year','fetched_at') else f'{col} INTEGER' for col in COLUMNS)},
            PRIMARY KEY (date, key)
        )
    """)
    return c


def summarize(key: str, category: str, label: str, year: str, d: dict) -> dict:
    """run() の結果から履歴1行ぶんの数値を抽出（mode差を吸収）。"""
    if "used" in d and "flea_sold" in d:                 # catalog single
        used, flea = d["used"], d["flea_sold"]
    elif "overall_used" in d:                            # 組み込み（グレード）
        used, flea = d["overall_used"], d["overall_flea_sold"]
    elif d.get("lofts"):                                 # ユーザー（ロフト）= すべて
        used, flea = d["lofts"][0]["used"], d["lofts"][0]["flea_sold"]
    else:
        used = flea = {"count": 0, "min": None, "avg": None, "median": None}
    gap = (d.get("headline") or {}).get("gap") or {}
    return {
        "key": key, "category": category, "label": label, "year": year,
        "used_count": used.get("count"), "used_min": used.get("min"),
        "used_avg": used.get("avg"), "used_median": used.get("median"),
        "flea_count": flea.get("count"), "flea_avg": flea.get("avg"),
        "profit": gap.get("profit"),
        "fetched_at": d.get("_fetched_at", ""),
    }


def record(date_str: str, rows: list[dict]):
    """その日のぶんを保存（(date,key)で上書き）。"""
    con = _conn()
    with con:
        for r in rows:
            vals = {"date": date_str, **r}
            con.execute(
                f"INSERT OR REPLACE INTO price_history ({', '.join(COLUMNS)}) "
                f"VALUES ({', '.join(':' + c for c in COLUMNS)})",
                {c: vals.get(c) for c in COLUMNS},
            )
    con.close()
    export_csv()


def export_csv():
    """全履歴を history.csv に書き出す（Googleスプレッドシート取り込み用）。"""
    con = _conn()
    rows = con.execute(
        f"SELECT {', '.join(COLUMNS)} FROM price_history ORDER BY date, category, key"
    ).fetchall()
    con.close()
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)


def count() -> int:
    con = _conn()
    n = con.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
    con.close()
    return n
