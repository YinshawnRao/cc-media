#!/usr/bin/env python3
"""B站视频搜索（WBI 签名），Cookie jar 仅在实际搜索时加载。

用法：
    python3 tools/video/bili_search.py "关键词" [n] [--cookies FILE]

默认在调用阶段只选择仓库根目录 ``all_cookies.txt``，不回退旧
``www.bilibili.com_cookies.txt``。jar 必须为 0600，路径不得包含 ``=``；其
安装、覆盖与权限只由用户本人维护。导入本模块不会查找、打开或解析
任何真实 Cookie 文件。
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import http.cookiejar
import json
import re
import stat
import time
import urllib.error
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

EXIT_EMPTY = 1
EXIT_COOKIE_PRECHECK = 2
EXIT_API_ERROR = 3
EXIT_RESPONSE_INVALID = 4
EXIT_REQUEST_FAILED = 5


class BiliSearchError(Exception):
    """Base class for safe, classified remote-search failures."""


class ApiResponseError(BiliSearchError):
    def __init__(self, stage: str, code: int):
        super().__init__(f"{stage}:{code}")
        self.stage = stage
        self.code = code


class ResponseParseError(BiliSearchError):
    def __init__(self, stage: str):
        super().__init__(stage)
        self.stage = stage


class SearchRequestError(BiliSearchError):
    def __init__(self, stage: str):
        super().__init__(stage)
        self.stage = stage


def default_cookie_path(repo_root: Path | None = None) -> Path:
    root = REPO_ROOT if repo_root is None else Path(repo_root)
    return root / "all_cookies.txt"


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
        raise ValueError(
            "cookie jar 权限不符合要求；canonical 只允许用户本人维护，"
            "请由用户检查文件权限"
        )
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


def get_json(url: str, opener, *, stage: str = "response"):
    try:
        with opener.open(url, timeout=20) as response:
            return json.load(response)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        # Never attach the response body to an error: API/edge responses can
        # contain account or anti-bot details that must not reach CLI output.
        # ``json`` may also raise a plain ValueError for oversized integer
        # tokens, so classify that as malformed remote data instead of
        # leaking a traceback and stopping the surrounding goal.
        raise ResponseParseError(stage) from None
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        http.client.HTTPException,
    ):
        raise SearchRequestError(stage) from None


def api_data(payload, *, stage: str) -> dict:
    if not isinstance(payload, dict):
        raise ResponseParseError(stage)
    code = payload.get("code")
    if isinstance(code, bool) or not isinstance(code, int):
        raise ResponseParseError(stage)
    if code != 0:
        # Bilibili's numeric business code is safe and useful for recovery;
        # its free-form message and the original payload are deliberately not
        # retained or printed.
        raise ApiResponseError(stage, code)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ResponseParseError(stage)
    return data


def mixin_key(original: str) -> str:
    return "".join(original[index] for index in MIXIN_TAB)[:32]


def get_keys(opener) -> tuple[str, str]:
    nav = get_json(
        "https://api.bilibili.com/x/web-interface/nav",
        opener,
        stage="nav",
    )
    data = api_data(nav, stage="nav")
    wbi = data.get("wbi_img")
    if not isinstance(wbi, dict):
        raise ResponseParseError("nav")
    image_url = wbi.get("img_url")
    sub_url = wbi.get("sub_url")
    if not isinstance(image_url, str) or not isinstance(sub_url, str):
        raise ResponseParseError("nav")
    image_key = image_url.rsplit("/", 1)[-1].split(".", 1)[0]
    sub_key = sub_url.rsplit("/", 1)[-1].split(".", 1)[0]
    if not re.fullmatch(r"[0-9a-fA-F]{32}", image_key) or not re.fullmatch(
        r"[0-9a-fA-F]{32}", sub_key
    ):
        raise ResponseParseError("nav")
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


def result_line(result: object) -> str:
    if not isinstance(result, dict):
        raise ResponseParseError("search")
    fields = {
        "bvid": result.get("bvid"),
        "duration": result.get("duration"),
        "author": result.get("author"),
        "title": result.get("title"),
    }
    if not all(isinstance(value, str) for value in fields.values()):
        raise ResponseParseError("search")
    fields["title"] = re.sub("<[^>]+>", "", fields["title"])
    for key, value in fields.items():
        # Collapse line breaks and remove control/ANSI characters so remote
        # fields cannot forge additional CLI status lines.
        printable = "".join(char if char.isprintable() else " " for char in value)
        fields[key] = " ".join(printable.split())
    return (
        f"{fields['bvid'][:64]} | {fields['duration'][:32]} | "
        f"{fields['author'][:160]} | {fields['title'][:240]}"
    )


def search(
    keyword: str,
    n: int = 8,
    *,
    cookie_path: Path | str | None = None,
    opener=None,
) -> list[dict]:
    if n <= 0:
        raise ValueError("result count must be positive")
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
    payload = get_json(url, opener, stage="search")
    data = api_data(payload, stage="search")
    results = data.get("result")
    if not isinstance(results, list):
        raise ResponseParseError("search")
    # Only an actual empty list is an EMPTY result. Missing/null/malformed
    # result fields are response failures and must not be reported as no hits.
    if not results:
        return []
    selected_results = results[:n]
    lines = [result_line(result) for result in selected_results]
    for line in lines:
        print(line)
    return selected_results


def positive_result_count(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError("n 必须是正整数") from None
    if value <= 0:
        raise argparse.ArgumentTypeError("n 必须是正整数")
    return value


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keyword")
    parser.add_argument("n", nargs="?", type=positive_result_count, default=8)
    parser.add_argument("--cookies")
    return parser.parse_args(argv)


def print_recovery_hint() -> None:
    print(
        "RECOVERY: goal 应自动换关键词重试；已有 BV/URL 时直接按 BV 验证或下载；"
        "同时继续另一平台（YouTube）检索，不因单次 B站搜索失败停止整个 goal。"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cookie_path = default_cookie_path() if args.cookies is None else args.cookies
    try:
        opener = build_opener(cookie_path)
    except ValueError:
        # The rejected CLI value may itself be an accidentally pasted cookie
        # token. Never echo it or a user-local path back to logs.
        print(
            "COOKIE PRECHECK: FAIL — 路径/存在性/权限检查未通过；"
            "请使用现有 Netscape jar 且路径不含 '='；"
            "canonical 只允许用户本人维护，请由用户检查文件与权限"
        )
        return EXIT_COOKIE_PRECHECK
    except http.cookiejar.LoadError:
        print("COOKIE PRECHECK: FAIL — Netscape cookie jar 格式无效")
        return EXIT_COOKIE_PRECHECK
    except OSError as error:
        detail = error.strerror or error.__class__.__name__
        print(f"COOKIE PRECHECK: FAIL — 文件读取错误: {detail}")
        return EXIT_COOKIE_PRECHECK
    time.sleep(0.3)
    try:
        results = search(args.keyword, args.n, opener=opener)
    except ApiResponseError as error:
        print(f"BILI SEARCH: API_ERROR stage={error.stage} code={error.code}")
        print_recovery_hint()
        return EXIT_API_ERROR
    except ResponseParseError as error:
        print(f"BILI SEARCH: RESPONSE_INVALID stage={error.stage}")
        print_recovery_hint()
        return EXIT_RESPONSE_INVALID
    except SearchRequestError as error:
        print(f"BILI SEARCH: REQUEST_FAILED stage={error.stage}")
        print_recovery_hint()
        return EXIT_REQUEST_FAILED
    if not results:
        print("BILI SEARCH: EMPTY")
        print_recovery_hint()
        return EXIT_EMPTY
    print(f"BILI SEARCH: PASS results={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
