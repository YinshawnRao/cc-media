#!/usr/bin/env python3
"""Download selected Bilibili candidates using the repo helper."""

from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
RAW = PROJECT / "raw"
LOG = PROJECT / "probe" / "download_bili_sources.log"

ITEMS = [
    ("qingxue", "BV1Po4y1g7w6"),
    ("hou", "BV197ffYkESq"),
    ("xue", "BV1rp4y1h7H5"),
    ("rainie", "BV16J411x7TE"),
    ("faye", "BV1W64y1F7sP"),
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for key, bvid in ITEMS:
        out = RAW / f"{key}_bilibili.mp4"
        cmd = [
            "python3",
            str(REPO / "tools/video/bili_dl.py"),
            bvid,
            str(out),
            "--max-h",
            "1080",
        ]
        chunks.append(f"## {key} / {bvid}\n$ {' '.join(cmd)}")
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
