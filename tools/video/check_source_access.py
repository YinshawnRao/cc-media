#!/usr/bin/env python3
"""Read-only source startup check; a nonzero result must not start production.

Usage: python3 tools/video/check_source_access.py --query '本期歌手 歌名'

Cookie reads go through the existing check_yt_cookie/bili_search readers and
yt_dlp_readonly wrapper. Output contains only classified, non-secret evidence.
This checks login and search/metadata access, not every video's downloadable bytes.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import http.client
import http.cookiejar
import io
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

if __package__:
    from . import bili_search, check_yt_cookie, yt_dlp_readonly
else:
    import bili_search
    import check_yt_cookie
    import yt_dlp_readonly


EXIT_CODES = {"PASS": 0, "CONFIRM_REQUIRED": 10, "ENVIRONMENT_BLOCKED": 11,
              "RETRY_REQUIRED": 12}
DENIED_HTTP = {401, 403, 412, 429}


@dataclass(frozen=True)
class Result:
    platform: str
    status: str
    stage: str
    reason: str


def request_failure(platform: str, stage: str, error: Exception) -> Result:
    if isinstance(error, urllib.error.HTTPError):
        status = "CONFIRM_REQUIRED" if error.code in DENIED_HTTP else "RETRY_REQUIRED"
        error.close()
        return Result(platform, status, stage, f"http_{error.code}")
    if isinstance(error, bili_search.SearchRequestError):
        if error.http_status is not None:
            status = "CONFIRM_REQUIRED" if error.http_status in DENIED_HTTP else "RETRY_REQUIRED"
            return Result(platform, status, stage, f"http_{error.http_status}")
        denied = error.permission_denied
    else:
        reason = error.reason if isinstance(error, urllib.error.URLError) else error
        denied = isinstance(reason, OSError) and reason.errno in (errno.EACCES, errno.EPERM)
    return Result(platform, "ENVIRONMENT_BLOCKED" if denied else "RETRY_REQUIRED",
                  stage, "local_permission_denied" if denied else "transport_unresolved")


def load_opener(platform: str):
    # Loading is read-only: never save the in-memory jar. Suppress stdlib's
    # malformed-jar warnings, which can include the offending secret-bearing row.
    path = (check_yt_cookie.default_cookie_path() if platform == "youtube"
            else bili_search.default_cookie_path())
    try:
        # Path.is_file() can turn EACCES into False; stat first so an internal
        # permission failure cannot masquerade as a missing/invalid Cookie file.
        path.stat()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            opener = bili_search.build_opener(path)
        rows = check_yt_cookie.load(path)
    except PermissionError:
        return Result(platform, "ENVIRONMENT_BLOCKED", "cookie", "local_permission_denied")
    except FileNotFoundError:
        return Result(platform, "CONFIRM_REQUIRED", "cookie", "cookie_file_missing")
    except (ValueError, http.cookiejar.LoadError):
        return Result(platform, "CONFIRM_REQUIRED", "cookie", "cookie_file_invalid_or_unavailable")
    except OSError as error:
        return request_failure(platform, "cookie", error)
    if platform == "youtube":
        required = check_yt_cookie.REQUIRED
        suffixes = ("youtube.com", "google.com")
        opener.addheaders = [("User-Agent", bili_search.UA)]
    else:
        required = ["SESSDATA"]
        suffixes = ("bilibili.com",)
    now = int(time.time())
    live_names = {
        name for domain, name, expiry in rows
        if any(domain.lstrip(".").lower() == suffix
               or domain.lstrip(".").lower().endswith("." + suffix)
               for suffix in suffixes)
        and check_yt_cookie._is_live(expiry, now)
    }
    if not set(required).issubset(live_names):
        return Result(platform, "CONFIRM_REQUIRED", "cookie", "auth_fields_missing_or_expired")
    return opener


def youtube_session(opener) -> Result:
    try:
        with opener.open("https://www.youtube.com/feed/subscriptions", timeout=20) as response:
            host = urllib.parse.urlsplit(response.geturl()).hostname
            body = response.read(8 * 1024 * 1024).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, http.client.HTTPException) as error:
        return request_failure("youtube", "session", error)
    states = set(re.findall(r'"LOGGED_IN"\s*:\s*(true|false)', body))
    if host == "accounts.google.com" or states == {"false"}:
        return Result("youtube", "CONFIRM_REQUIRED", "session", "server_not_logged_in")
    if re.search(r"sign in to confirm you[’']?re not a bot|unusual traffic", body, re.I):
        return Result("youtube", "CONFIRM_REQUIRED", "session", "platform_challenge")
    if host not in {"www.youtube.com", "youtube.com"} or states != {"true"}:
        return Result("youtube", "RETRY_REQUIRED", "session", "login_response_unrecognized")
    return Result("youtube", "PASS", "session", "server_logged_in")


def youtube_search(query: str) -> Result:
    captured = []

    def runner(command, **kwargs):
        completed = subprocess.run(command, capture_output=True, text=True, errors="replace",
                                   timeout=90, **kwargs)
        captured.append(completed)
        return completed

    try:
        code = yt_dlp_readonly.run_yt_dlp([
            "--simulate", "--no-playlist", "--no-progress",
            "--socket-timeout", "15", "--retries", "0", "--extractor-retries", "0",
            "--print", "%(id)s", "--", "ytsearch1:" + query,
        ], runner=runner)
    except yt_dlp_readonly.CookieGuardError as error:
        # Guard errors may wrap a sandbox-denied open; retain that distinction.
        if isinstance(error.__cause__, OSError):
            return request_failure("youtube", "cookie", error.__cause__)
        return Result("youtube", "CONFIRM_REQUIRED", "cookie", "cookie_guard_failed")
    except (OSError, subprocess.TimeoutExpired) as error:
        if isinstance(error, FileNotFoundError):
            return Result("youtube", "ENVIRONMENT_BLOCKED", "search", "yt_dlp_missing")
        return request_failure("youtube", "search", error)
    completed = captured[0]
    # Never return raw stderr/stdout, URLs, headers, or info JSON.
    detail = completed.stderr.casefold()
    if re.search(r"operation not permitted|permission denied|sandbox|approval required", detail):
        return Result("youtube", "ENVIRONMENT_BLOCKED", "search", "local_execution_denied")
    if re.search(r"cookies?[^\n]*(no longer valid|expired|rotated)", detail):
        return Result("youtube", "CONFIRM_REQUIRED", "search", "cookie_rejected")
    if re.search(r"not a bot|sign in to confirm|http error (412|429)\b", detail):
        return Result("youtube", "CONFIRM_REQUIRED", "search", "platform_denied_or_challenged")
    if re.search(r"http error (401|403)\b", detail):
        return Result("youtube", "RETRY_REQUIRED", "search", "candidate_or_client_denied")
    if code != 0:
        return Result("youtube", "RETRY_REQUIRED", "search", "extractor_or_candidate_unresolved")
    if not re.search(r"(?m)^[A-Za-z0-9_-]{11}$", completed.stdout):
        return Result("youtube", "RETRY_REQUIRED", "search", "no_probe_candidate")
    return Result("youtube", "PASS", "session_and_search", "login_and_metadata_accessible")


def bilibili_session_and_search(opener, query: str) -> Result:
    stage = "session"
    try:
        payload = bili_search.get_json("https://api.bilibili.com/x/web-interface/nav",
                                       opener, stage="nav")
        data = bili_search.api_data(payload, stage="nav")
        if data.get("isLogin") is False:
            return Result("bilibili", "CONFIRM_REQUIRED", stage, "server_not_logged_in")
        if data.get("isLogin") is not True:
            return Result("bilibili", "RETRY_REQUIRED", stage, "login_response_unrecognized")
        stage = "search"
        # Reuse existing WBI signing and parsing; capture only its public candidate
        # lines so the preflight report has a stable, minimal evidence surface.
        with contextlib.redirect_stdout(io.StringIO()):
            results = bili_search.search(query, 1, opener=opener)
    except bili_search.ApiResponseError as error:
        status = ("CONFIRM_REQUIRED" if error.code in {-101, -352, -412, -509}
                  else "RETRY_REQUIRED")
        return Result("bilibili", status, stage, f"api_{error.code}")
    except bili_search.ResponseParseError:
        return Result("bilibili", "RETRY_REQUIRED", stage, "response_unrecognized")
    except bili_search.SearchRequestError as error:
        return request_failure("bilibili", stage, error)
    return Result("bilibili", "PASS", "session_and_search",
                  "login_and_search_accessible" if results else "login_and_search_accessible_empty")


def probe(platform: str, query: str) -> Result:
    opener = load_opener(platform)
    if isinstance(opener, Result):
        return opener
    if platform == "bilibili":
        return bilibili_session_and_search(opener, query)
    session = youtube_session(opener)
    return youtube_search(query) if session.status == "PASS" else session


def verdict(results: list[Result]) -> str:
    for status in ("CONFIRM_REQUIRED", "ENVIRONMENT_BLOCKED", "RETRY_REQUIRED"):
        if any(result.status == status for result in results):
            return status
    return "PASS"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="音乐 official MV", help="本期代表性搜索词")
    parser.add_argument("--platform", choices=("youtube", "bilibili"), action="append",
                        help="仅限用户明确指定来源例外；默认检查两平台")
    args = parser.parse_args(argv)
    if not args.query.strip():
        parser.error("--query must not be blank")
    platforms = list(dict.fromkeys(args.platform or ["youtube", "bilibili"]))
    results = [probe(platform, args.query) for platform in platforms]
    status = verdict(results)
    print(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(),
                      "status": status, "results": [asdict(result) for result in results]},
                     ensure_ascii=False, indent=2))
    print(f"SOURCE ACCESS: {status}")
    if status == "CONFIRM_REQUIRED":
        print("ACTION: 暂停本期制作并等待用户确认；不得自动切到另一平台或公开下载继续制作。")
    elif status == "ENVIRONMENT_BLOCKED":
        print("ACTION: 先恢复代理授权/本地执行环境后重测；此结果不能证明平台不通。")
    elif status == "RETRY_REQUIRED":
        print("ACTION: 尚未通过；先排查执行权限，再做最小复测，不能将未知原因写成 Cookie 过期。")
    return EXIT_CODES[status]


if __name__ == "__main__":
    raise SystemExit(main())
