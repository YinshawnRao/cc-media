#!/usr/bin/env python3
"""B站视频搜索（WBI 签名），Cookie jar 仅在实际搜索时加载。

用法：
    python3 tools/video/bili_search.py "关键词" [n] [--cookies FILE]

默认在调用阶段选择仓库根目录 ``all_cookies.txt``，缺失时才回退旧
``www.bilibili.com_cookies.txt``。jar 必须为 0600，路径不得包含 ``=``。
导入本模块不会查找、打开或解析任何真实 Cookie 文件。
"""

from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import re
import stat
import time
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]


def default_cookie_path(repo_root: Path | None = None) -> Path:
    root = REPO_ROOT if repo_root is None else Path(repo_root)
    preferred = root / "all_cookies.txt"
    if preferred.is_file():
        return preferred
    return root / "www.bilibili.com_cookies.txt"


def validate_cookie_jar(path: Path | str) -> Path:
    jar = Path(path).expanduser()
    if "=" in str(jar):
        raise ValueError(
            "cookie jar 路径不能包含 '='；命令行消费者可能把它误判为内联数据"
        )
    if not jar.is_file():
        raise ValueError(f"cookie jar 不存在: {jar}")
    mode = stat.S_IMODE(jar.stat().st_mode)
    if mode & 0o077:
        raise ValueError(f"cookie jar 权限为 {mode:04o}，请先 chmod 600")
    return jar


def load_cookie_jar(path: Path | str) -> http.cookiejar.MozillaCookieJar:
    jar_path = validate_cookie_jar(path)
    jar = http.cookiejar.MozillaCookieJar(str(jar_path))
    # stdlib MozillaCookieJar 原生识别 Netscape #HttpOnly_，并保留 HTTPOnly rest。
    jar.load(ignore_discard=True, ignore_expires=False)
    return jar


def build_opener(path: Path | str):
    jar = load_cookie_jar(path)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [
        ("User-Agent", UA),
        ("Referer", "https://www.bilibili.com/"),
    ]
    return opener


def get_json(url: str, opener):
    with opener.open(url, timeout=20) as response:
        return json.load(response)


def mixin_key(original: str) -> str:
    return "".join(original[index] for index in MIXIN_TAB)[:32]


def get_keys(opener) -> tuple[str, str]:
    nav = get_json("https://api.bilibili.com/x/web-interface/nav", opener)
    wbi = nav["data"]["wbi_img"]
    image_key = wbi["img_url"].rsplit("/", 1)[1].split(".")[0]
    sub_key = wbi["sub_url"].rsplit("/", 1)[1].split(".")[0]
    return image_key, sub_key


def enc_wbi(params: dict, image_key: str, sub_key: str) -> dict:
    mixin = mixin_key(image_key + sub_key)
    signed = {**params, "wts": round(time.time())}
    signed = dict(sorted(signed.items()))
    signed = {
        key: "".join(char for char in str(value) if char not in "!'()*")
        for key, value in signed.items()
    }
    query = urllib.parse.urlencode(signed)
    signed["w_rid"] = hashlib.md5((query + mixin).encode()).hexdigest()
    return signed


def search(
    keyword: str,
    n: int = 8,
    *,
    cookie_path: Path | str | None = None,
    opener=None,
) -> list[dict]:
    if opener is None:
        selected = default_cookie_path() if cookie_path is None else cookie_path
        opener = build_opener(selected)

    image_key, sub_key = get_keys(opener)
    params = enc_wbi(
        {"search_type": "video", "keyword": keyword, "page": 1},
        image_key,
        sub_key,
    )
    url = (
        "https://api.bilibili.com/x/web-interface/wbi/search/type?"
        + urllib.parse.urlencode(params)
    )
    data = get_json(url, opener)
    if data.get("code") != 0:
        print("ERR", data.get("code"), data.get("message"))
        return []
    results = (data.get("data") or {}).get("result") or []
    selected_results = results[:n]
    for result in selected_results:
        title = re.sub("<[^>]+>", "", result.get("title", ""))
        print(
            f'{result.get("bvid")} | {result.get("duration")} | '
            f'{result.get("author")} | {title}'
        )
    return selected_results


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keyword")
    parser.add_argument("n", nargs="?", type=int, default=8)
    parser.add_argument("--cookies")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cookie_path = default_cookie_path() if args.cookies is None else args.cookies
    try:
        opener = build_opener(cookie_path)
    except ValueError as error:
        print(f"COOKIE PRECHECK: FAIL — {error}")
        return 2
    except http.cookiejar.LoadError:
        print("COOKIE PRECHECK: FAIL — Netscape cookie jar 格式无效")
        return 2
    except OSError as error:
        detail = error.strerror or error.__class__.__name__
        print(f"COOKIE PRECHECK: FAIL — 文件读取错误: {detail}")
        return 2
    time.sleep(0.3)
    search(args.keyword, args.n, opener=opener)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
