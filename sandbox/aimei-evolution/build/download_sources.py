#!/usr/bin/env python3
"""Download selected official source videos/audio from YouTube."""

from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
RAW = PROJECT / "raw"
LOG = PROJECT / "probe" / "download_sources.log"

ITEMS = [
    ("qingxue", "https://www.youtube.com/watch?v=YrMuWpq4U5Y"),
    ("hou", "https://www.youtube.com/watch?v=tDN_9TQ-tzo"),
    ("xue", "https://www.youtube.com/watch?v=rK1G8_E8Lb0"),
    ("rainie", "https://www.youtube.com/watch?v=mebzXfWi87E"),
    ("faye", "https://www.youtube.com/watch?v=bR8u65g_t7o"),
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for key, url in ITEMS:
        out = RAW / f"{key}_youtube.%(ext)s"
        cmd = [
            "yt-dlp",
            "--cookies",
            str(REPO / "www.youtube.com_cookies.txt"),
            "--no-playlist",
            "--merge-output-format",
            "mp4",
            "-f",
            "bv*[height<=1080]+ba/b[height<=1080]",
            "-o",
            str(out),
            url,
        ]
        chunks.append(f"## {key}\n$ {' '.join(cmd)}")
        p = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
        )
        chunks.append(p.stdout)
        if p.returncode != 0:
            LOG.write_text("\n".join(chunks), encoding="utf-8")
            raise SystemExit(p.returncode)
    LOG.write_text("\n".join(chunks), encoding="utf-8")
    print(LOG)


if __name__ == "__main__":
    main()
