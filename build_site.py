"""キャッシュ済みデータから スマホ用静的サイト site/ を生成する。

毎日の自動取得(refresh_rankings.py)の最後に呼ばれ、再スクレイピングせず
キャッシュ(.cache/*_p2.json)を読んで site/data.json と site/index.html を書き出す。
site/ をそのまま無料ホスティング(GitHub Pages/Cloudflare Pages)へ上げればスマホで閲覧可。

手動実行: python build_site.py
"""

import json
import time
from pathlib import Path

from golf_price import cache, service, history
from golf_price.catalog import CATALOG, CATEGORIES

BASE = Path(__file__).resolve().parent
SITE = BASE / "site"
MOBILE_HTML = BASE / "mobile" / "index.html"
LONG_TTL = 10 ** 9   # キャッシュのTTLを無視して読む


def _model_entry(m, d: dict) -> dict:
    used = d.get("used") or {}
    flea = d.get("flea_sold") or {}
    gap = d.get("gap") or {}
    cheapest = (d.get("used_samples") or [{}])[0]
    # 前日（前回取得日）の最安値との比較（％）
    cur_min = used.get("min")
    cur_date = (d.get("_fetched_at") or "")[:10] or time.strftime("%Y-%m-%d")
    prev_min = history.last_min_before(m.key, cur_date)
    prev_pct = round((cur_min - prev_min) / prev_min * 100) if (prev_min and cur_min) else None
    return {
        "key": m.key, "label": f"{m.brand} {m.label}", "brand": m.brand,
        "year": m.year, "category": m.category,
        "used": {k: used.get(k) for k in ("count", "min", "avg", "median", "max")},
        "flea": {k: flea.get(k) for k in ("count", "avg", "median")},
        "profit": gap.get("profit"),
        "gap_basis": gap.get("basis", "min_avg"),
        "gap_used": gap.get("used_base"),
        "gap_flea": gap.get("flea_base"),
        "prev_pct": prev_pct,
        "used_min_shop": cheapest.get("shop", ""),
        "used_min_url": cheapest.get("url", ""),
        "used_min_head_only": cheapest.get("head_only", False),
        "used_samples": (d.get("used_samples") or [])[:20],
        "flea_samples": (d.get("flea_samples") or [])[:20],
    }


def build() -> int:
    SITE.mkdir(exist_ok=True)
    models = []
    for m in CATALOG:
        d = cache.get(f"{m.key}_p2", ttl=LONG_TTL)
        if not d:
            continue
        models.append(_model_entry(m, d))

    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "fee_rate": service.FEE_RATE,
        "shipping": service.SHIPPING,
        "categories": [
            {"key": k, "label": lbl,
             "count": sum(1 for x in models if x["category"] == k)}
            for k, lbl in CATEGORIES
        ],
        "models": models,
    }
    (SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    if MOBILE_HTML.exists():
        (SITE / "index.html").write_text(MOBILE_HTML.read_text(encoding="utf-8"), encoding="utf-8")
    return len(models)


def publish() -> str:
    """site/ をGitHub Pages用リポジトリへコミット＆プッシュ（毎日の自動アップ用）。

    初回に gh で作成済みの site/.git（remote=origin）が前提。未設定ならスキップ。
    """
    import subprocess
    if not (SITE / ".git").exists():
        return "site/ は未公開設定（git未初期化）のためスキップ"

    def git(*args):
        return subprocess.run(["git", "-C", str(SITE), *args],
                              capture_output=True, text=True)

    git("add", "-A")
    st = git("status", "--porcelain")
    if not st.stdout.strip():
        return "変更なし（公開スキップ）"
    git("-c", "user.name=nekokaitaidesu-cpu",
        "-c", "user.email=takeogonzaless@gmail.com",
        "commit", "-m", f"update {time.strftime('%Y-%m-%d %H:%M')}")
    p = git("push", "origin", "main")
    return "公開プッシュ完了" if p.returncode == 0 else f"公開プッシュ失敗: {p.stderr.strip()[:200]}"


if __name__ == "__main__":
    n = build()
    print(f"site/ を生成しました（{n}機種）→ {SITE}")
    print(publish())
