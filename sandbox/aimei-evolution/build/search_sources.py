#!/usr/bin/env python3
"""Search YouTube and Bilibili candidates for the Aimei project.

The script records raw search results only. It reads cookie files from the
repository root and never copies them into the sandbox.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
OUT = PROJECT / "probe" / "search_results.txt"

QUERIES = [
    ("source-cameo", "黄莺莺 情雪 官方 音频"),
    ("hou", "侯湘婷 暧昧 官方 MV"),
    ("xue", "薛之谦 暧昧 官方 MV"),
    ("rainie", "杨丞琳 暧昧 官方 MV"),
    ("faye", "王菲 暧昧 官方 MV"),
]


def run(cmd: list[str]) -> str:
    p = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=90,
    )
    return p.stdout.strip() if p.stdout.strip() else f"(exit {p.returncode}, no output)"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for key, query in QUERIES:
        chunks.append(f"## {key} / {query}")
        yt_cmd = [
            "yt-dlp",
            "--cookies",
            str(REPO / "www.youtube.com_cookies.txt"),
            "--flat-playlist",
            "--skip-download",
            "--print",
            "%(id)s | %(duration_string)s | %(channel)s | %(title)s | %(webpage_url)s",
            f"ytsearch8:{query}",
        ]
        chunks.append("### YouTube")
        chunks.append(run(yt_cmd))
        bili_cmd = [
            "python3",
            str(REPO / "tools/video/bili_search.py"),
            query,
            "8",
        ]
        chunks.append("### Bilibili")
        chunks.append(run(bili_cmd))
        chunks.append("")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
