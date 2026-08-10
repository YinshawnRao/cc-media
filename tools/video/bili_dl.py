#!/usr/bin/env python3
"""B站下载救场（yt-dlp 报 HTTP 412 风控时用）。

yt-dlp 的 BiliBili extractor 会被 B站对其请求签名做 412 风控，但**普通浏览器式 curl
(--compressed + 桌面UA + referer + Netscape cookie jar) 仍能取到视频页**，页里内嵌 window.__playinfo__
(DASH m4s 直链)。本脚本据此取直链、curl 下载视频/音频流、ffmpeg mux 成 mp4。

用法：
    python tools/video/bili_dl.py <bvid> <out.mp4> [--max-h 1080] [--cookies path]
默认读取仓库根目录过滤后的 all_cookies.txt（含 B站登录态）；缺则回退旧
www.bilibili.com_cookies.txt。cookie jar 必须为 0600；脚本只把文件路径交给 curl，
不会把 cookie value 拼进进程参数。优先 AVC(h264) ≤max-h，便于下游重剪。
"""
import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
REPO = Path(__file__).resolve().parents[2]


def default_cookie_path(repo_root: Path | None = None) -> Path:
    root = REPO if repo_root is None else Path(repo_root)
    preferred = root / "all_cookies.txt"
    if preferred.is_file():
        return preferred
    return root / "www.bilibili.com_cookies.txt"


DEF_CK = default_cookie_path()


def validate_cookie_jar(path: Path | str) -> Path:
    jar = Path(path).expanduser()
    if "=" in str(jar):
        raise SystemExit(
            "!! cookie jar 路径不能包含 '='；curl 会把该参数误判为内联 cookie data"
        )
    if not jar.is_file():
        raise SystemExit(f"!! cookie jar 不存在: {jar}")
    mode = stat.S_IMODE(jar.stat().st_mode)
    if mode & 0o077:
        raise SystemExit(f"!! cookie jar 权限为 {mode:04o}，请先 chmod 600 {jar}")
    return jar


def build_curl_command(
    url: str, cookie_jar: Path | str, out: str | None = None
) -> list[str]:
    """Build curl argv containing only the jar path, never cookie values."""

    cmd = [
        "curl",
        "-sL",
        "--compressed",
        "--cookie",
        str(cookie_jar),
        "-A",
        UA,
        "-e",
        "https://www.bilibili.com/",
    ]
    if out:
        cmd.extend(["-o", out, "-w", "%{http_code}"])
    cmd.append(url)
    return cmd


def curl(url: str, cookie_jar: Path, out: str | None = None):
    cmd = build_curl_command(url, cookie_jar, out)
    if out:
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


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("bvid")
    ap.add_argument("out")
    ap.add_argument("--max-h", type=int, default=1080)
    ap.add_argument("--cookies", default=str(DEF_CK))
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)

    cookie_jar = validate_cookie_jar(a.cookies)
    html = curl(f"https://www.bilibili.com/video/{a.bvid}/", cookie_jar).decode("utf-8", "replace")
    m = re.search(r"window\.__playinfo__=(\{.*?\})</script>", html)
    if not m:
        sys.exit(f"!! no playinfo for {a.bvid} (可能风控页/需登录/番剧)")
    info = json.loads(m.group(1))
    data = info.get("data") or info.get("result") or {}
    dash = data.get("dash")
    with tempfile.TemporaryDirectory(prefix="bili_") as tmp:
        if dash:
            v = pick(dash["video"], a.max_h)
            au = pick(dash["audio"], 99999)
            vh = v.get("height"); vc = v.get("codecs"); ac = au.get("codecs")
            print(f"[{a.bvid}] video {v.get('width')}x{vh} {vc} {v.get('bandwidth')//1000}kbps ; audio {ac} {au.get('bandwidth')//1000}kbps")
            vf = os.path.join(tmp, "v.m4s"); af = os.path.join(tmp, "a.m4s")
            for url, dst in [(v["baseUrl"], vf), (au["baseUrl"], af)]:
                code = curl(url, cookie_jar, dst)
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
            code = curl(u, cookie_jar, mf)
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
