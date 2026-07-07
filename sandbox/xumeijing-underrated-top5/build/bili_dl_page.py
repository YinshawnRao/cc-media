#!/usr/bin/env python3
"""bili_dl.py variant supporting multi-P videos via ?p=N (donor footage from compilations)."""
import sys, re, json, subprocess, argparse, tempfile, os
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
REPO = Path(__file__).resolve().parents[3]
DEF_CK = REPO / "all_cookies.txt"


def cookie_header(ck_path: Path) -> str:
    parts = []
    for ln in ck_path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        f = ln.split("\t")
        if len(f) >= 7 and "bilibili" in f[0]:
            parts.append(f"{f[5]}={f[6]}")
    return "; ".join(parts)


def curl(url, ckhdr, out=None):
    cmd = ["curl", "-sL", "--compressed", "-A", UA, "-e", "https://www.bilibili.com/",
           "-H", f"Cookie: {ckhdr}", url]
    if out:
        cmd[1:1] = ["-o", out, "-w", "%{http_code}"]
        code = subprocess.check_output(cmd).decode().strip()
        return code
    return subprocess.check_output(cmd)


def pick(streams, max_h):
    cand = [s for s in streams if s.get("height", 0) <= max_h]
    if not cand:
        cand = streams
    cand.sort(key=lambda s: (("avc1" in s.get("codecs", "")) * 1, s.get("bandwidth", 0)), reverse=True)
    return cand[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bvid")
    ap.add_argument("page", type=int)
    ap.add_argument("out")
    ap.add_argument("--max-h", type=int, default=1080)
    a = ap.parse_args()

    ckhdr = cookie_header(DEF_CK)
    html = curl(f"https://www.bilibili.com/video/{a.bvid}/?p={a.page}", ckhdr).decode("utf-8", "replace")
    m = re.search(r"window\.__playinfo__=(\{.*?\})</script>", html)
    if not m:
        sys.exit(f"!! no playinfo for {a.bvid} p{a.page}")
    info = json.loads(m.group(1))
    data = info.get("data") or info.get("result") or {}
    dash = data.get("dash")
    tmp = tempfile.mkdtemp(prefix="bili_")
    v = pick(dash["video"], a.max_h)
    au = pick(dash["audio"], 99999)
    print(f"[{a.bvid} p{a.page}] video {v.get('width')}x{v.get('height')} {v.get('codecs')} ; audio {au.get('codecs')}")
    vf = os.path.join(tmp, "v.m4s"); af = os.path.join(tmp, "a.m4s")
    for url, dst in [(v["baseUrl"], vf), (au["baseUrl"], af)]:
        code = curl(url, ckhdr, dst)
        sz = os.path.getsize(dst) if os.path.exists(dst) else 0
        print(f"   dl {os.path.basename(dst)} HTTP {code} size {sz//1024}KB")
        if sz < 10000:
            sys.exit(f"!! stream too small ({dst}), likely blocked")
    subprocess.run(["ffmpeg", "-v", "error", "-i", vf, "-i", af,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", a.out, "-y"], check=True)
    r = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                 "-show_entries", "stream=width,height,codec_name",
                                 "-of", "csv=p=0:s=x", a.out]).decode().strip()
    print(f"[{a.bvid} p{a.page}] OK -> {a.out}  {r}")


if __name__ == "__main__":
    main()
