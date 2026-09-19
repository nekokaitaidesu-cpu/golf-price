# -*- coding: utf-8 -*-
"""auto-memory（PCローカル）をリポジトリの memory/ にコピーして引き継げる形にする。

  python scripts/backup_memory.py           # 差分を表示してコピー
  python scripts/backup_memory.py --check   # コピーせず差分だけ見る
  python scripts/backup_memory.py --commit  # コピー＋ memory/ だけを commit & push

日次の「今日の本命」の最後（メモ保存と同じタイミング）に --commit で回す。
差分が無ければ何もしないので、毎日叩いて構わない。

auto-memory の実体は
`%USERPROFILE%\\.claude\\projects\\C--Users-User-Claude-golf-price\\memory` にあり、
**PCが壊れると消える**（2026-09-19にユーザーが引き継ぎを確認して判明）。
リポジトリは公開なので、**鍵・トークン・メールアドレスが入っていないかを毎回検査**してからコピーする。
ここで弾かれたら、その中身はリポジトリに入れずローカルに残すこと。
"""
import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "memory")
SRC = os.path.join(os.path.expanduser("~"), ".claude", "projects",
                   "C--Users-User-Claude-golf-price", "memory")

# 公開リポジトリに入れてはいけないものの形。originSessionId のUUIDは無害なので除く
_SECRET = re.compile(
    r"(LINE_CHANNEL_TOKEN|LINE_USER_ID|access[_-]?key|api[_-]?key|Bearer\s|pk_[A-Za-z0-9]|"
    r"password|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", re.I)


def scan(path: str) -> list[str]:
    hits = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if line.lstrip().startswith("originSessionId:"):
                continue
            m = _SECRET.search(line)
            if m:
                hits.append(f"{os.path.basename(path)}:{i} … {m.group(1)[:20]}")
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="コピーせず差分と検査だけ")
    ap.add_argument("--commit", action="store_true",
                    help="コピー後に memory/ だけを commit & push（差分が無ければ何もしない）")
    args = ap.parse_args()

    if not os.path.isdir(SRC):
        print(f"auto-memory が見つからない: {SRC}")
        sys.exit(1)
    os.makedirs(DEST, exist_ok=True)

    names = sorted(n for n in os.listdir(SRC) if n.endswith(".md"))
    bad = [h for n in names for h in scan(os.path.join(SRC, n))]
    if bad:
        print("⚠ 公開できない文字列が見つかった。コピーを中止する:")
        for h in bad:
            print("   " + h)
        sys.exit(2)

    new, changed = [], []
    for n in names:
        s, d = os.path.join(SRC, n), os.path.join(DEST, n)
        if not os.path.exists(d):
            new.append(n)
        elif not filecmp.cmp(s, d, shallow=False):
            changed.append(n)
    gone = [n for n in os.listdir(DEST) if n.endswith(".md") and n not in names]

    print(f"auto-memory {len(names)}本 / 新規 {len(new)} 更新 {len(changed)} 消滅 {len(gone)}")
    for label, xs in (("新規", new), ("更新", changed), ("消滅", gone)):
        for x in xs:
            print(f"  {label}: {x}")

    if args.check:
        return
    for n in new + changed:
        shutil.copy2(os.path.join(SRC, n), os.path.join(DEST, n))
    for n in gone:  # ローカルで削除されたメモはリポジトリからも消す
        os.remove(os.path.join(DEST, n))
    if not (new or changed or gone):
        print("差分なし。何もしない")
        return
    print(f"→ {DEST} に反映した")

    if not args.commit:
        print("   git add memory/ してコミットすること")
        return

    # memory/ だけをコミットする。本命メモやカタログの編集を巻き込まないため
    # パス指定で add → commit する（-a は使わない）
    def git(*a: str) -> int:
        return subprocess.run(["git", "-C", REPO, *a]).returncode

    msg = f"memory: バックアップ（新規{len(new)}・更新{len(changed)}・削除{len(gone)}）"
    if git("add", "--", "memory") != 0:
        sys.exit("git add に失敗")
    if git("commit", "-q", "-m", msg, "--", "memory") != 0:
        sys.exit("git commit に失敗")
    if git("push", "-q", "origin", "HEAD") != 0:
        print("⚠ push に失敗（コミットは済んでいる。あとで push すること）")
        return
    print(f"→ commit & push 済み: {msg}")


if __name__ == "__main__":
    main()
