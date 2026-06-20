#!/usr/bin/env python3
"""B站下载救场（yt-dlp 报 HTTP 412 风控时用）。

yt-dlp 的 BiliBili extractor 会被 B站对其请求签名做 412 风控，但**普通浏览器式 curl
(--compressed + 桌面UA + referer + cookie) 仍能取到视频页**，页里内嵌 window.__playinfo__
(DASH m4s 直链)。本脚本据此取直链、curl 下载视频/音频流、ffmpeg mux 成 mp4。

用法：
    python tools/video/bili_dl.py <bvid> <out.mp4> [--max-h 1080] [--cookies path]
读 sandbox/www.bilibili.com_cookies.txt（默认）。优先 AVC(h264) ≤max-h，便于下游重剪。
"""
import sys, re, json, subprocess, argparse, tempfile, os
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
REPO = Path(__file__).resolve().parents[2]
DEF_CK = REPO / "sandbox" / "www.bilibili.com_cookies.txt"


def cookie_header(ck_path: Path) -> str:
    parts = []
    for ln in ck_path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        f = ln.split("\t")
        if len(f) >= 7:
            parts.append(f"{f[5]}={f[6]}")
    return "; ".join(parts)


def curl(url: str, ckhdr: str, out: str = None) -> bytes:
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
    # 优先 avc(h264)，再按 bandwidth
    cand.sort(key=lambda s: (("avc1" in s.get("codecs", "")) * 1, s.get("bandwidth", 0)), reverse=True)
    return cand[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bvid")
    ap.add_argument("out")
    ap.add_argument("--max-h", type=int, default=1080)
    ap.add_argument("--cookies", default=str(DEF_CK))
    a = ap.parse_args()

    ckhdr = cookie_header(Path(a.cookies))
    html = curl(f"https://www.bilibili.com/video/{a.bvid}/", ckhdr).decode("utf-8", "replace")
    m = re.search(r"window\.__playinfo__=(\{.*?\})</script>", html)
    if not m:
        sys.exit(f"!! no playinfo for {a.bvid} (可能风控页/需登录/番剧)")
    info = json.loads(m.group(1))
    data = info.get("data") or info.get("result") or {}
    dash = data.get("dash")
    tmp = tempfile.mkdtemp(prefix="bili_")
    if dash:
        v = pick(dash["video"], a.max_h)
        au = pick(dash["audio"], 99999)
        vh = v.get("height"); vc = v.get("codecs"); ac = au.get("codecs")
        print(f"[{a.bvid}] video {v.get('width')}x{vh} {vc} {v.get('bandwidth')//1000}kbps ; audio {ac} {au.get('bandwidth')//1000}kbps")
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
    else:
        durl = data.get("durl")
        if not durl:
            sys.exit(f"!! no dash/durl for {a.bvid}")
        u = durl[0]["url"]
        mf = os.path.join(tmp, "m.mp4")
        code = curl(u, ckhdr, mf)
        print(f"[{a.bvid}] durl(mp4) HTTP {code} size {os.path.getsize(mf)//1024}KB")
        subprocess.run(["ffmpeg", "-v", "error", "-i", mf, "-c", "copy",
                        "-movflags", "+faststart", a.out, "-y"], check=True)
    r = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                 "-show_entries", "stream=width,height,codec_name",
                                 "-of", "csv=p=0:s=x", a.out]).decode().strip()
    dur = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration", "-of", "csv=p=0", a.out]).decode().strip()
    print(f"[{a.bvid}] OK -> {a.out}  {r}  dur={dur}s")


if __name__ == "__main__":
    main()
