#!/usr/bin/env python3
"""Filter an external browser Netscape jar into an external candidate jar.

The source must be outside this repository and mode 0600. Only YouTube, Google,
and Bilibili domains are retained. The output must be explicitly selected outside
the repository; this tool never writes or replaces repository-root
``all_cookies.txt``. The candidate is replaced atomically with mode 0600. Cookie
values are never printed.

Usage:
    python3 tools/video/filter_cookie_jar.py /outside/repo/raw.txt \
        --output /outside/repo/candidate.txt
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HTTPONLY_PREFIX = b"#HttpOnly_"
ALLOWED_DOMAIN_SUFFIXES = (b"youtube.com", b"google.com", b"bilibili.com")
REQUIRED_YOUTUBE_NAMES = {
    b"LOGIN_INFO",
    b"SID",
    b"HSID",
    b"SSID",
    b"SAPISID",
    b"APISID",
    b"__Secure-3PSID",
}
REQUIRED_BILIBILI_NAMES = {b"SESSDATA", b"bili_jct", b"DedeUserID"}


@dataclass(frozen=True)
class FilterResult:
    output: Path
    retained: int
    discarded: int


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _metadata_from_line(raw_line: bytes) -> tuple[bytes, bytes, int] | None:
    line = raw_line.rstrip(b"\r\n")
    if not line:
        return None
    if line.startswith(HTTPONLY_PREFIX):
        line = line[len(HTTPONLY_PREFIX) :]
    elif line.startswith(b"#"):
        return None
    fields = line.split(b"\t")
    if len(fields) < 7:
        return None
    try:
        expiry = int(fields[4] or b"0")
    except ValueError:
        return None
    return fields[0].lstrip(b".").lower(), fields[5], expiry


def _allowed_domain(domain: bytes) -> bool:
    return any(
        domain == suffix or domain.endswith(b"." + suffix)
        for suffix in ALLOWED_DOMAIN_SUFFIXES
    )


def _domain_service(domain: bytes) -> str | None:
    if domain == b"bilibili.com" or domain.endswith(b".bilibili.com"):
        return "bilibili"
    if any(
        domain == suffix or domain.endswith(b"." + suffix)
        for suffix in (b"youtube.com", b"google.com")
    ):
        return "youtube"
    return None


def _is_live(expiry: int, now: int) -> bool:
    return expiry == 0 or expiry > now


def _validate_source(source: Path, repo_root: Path) -> Path:
    lexical_source = Path(os.path.abspath(source.expanduser()))
    lexical_root = Path(os.path.abspath(repo_root))
    if _is_within(lexical_source, lexical_root):
        raise ValueError("原始 cookie 源文件必须位于仓库外")

    resolved_source = source.expanduser().resolve(strict=True)
    resolved_root = repo_root.resolve(strict=True)
    if _is_within(resolved_source, resolved_root):
        raise ValueError("原始 cookie 源文件必须位于仓库外")
    if not resolved_source.is_file():
        raise ValueError(f"源文件不是普通文件: {resolved_source}")
    mode = stat.S_IMODE(resolved_source.stat().st_mode)
    if mode & 0o077:
        raise ValueError(f"原始 cookie 源文件权限为 {mode:04o}，请先 chmod 600")
    return resolved_source


def _validate_output(output: Path, repo_root: Path, source: Path) -> Path:
    lexical_output = Path(os.path.abspath(output.expanduser()))
    lexical_root = Path(os.path.abspath(repo_root))
    resolved_root = repo_root.resolve(strict=True)

    if _is_within(lexical_output, lexical_root):
        raise ValueError("候选输出必须位于仓库外，禁止写入 all_cookies.txt")
    if lexical_output == source:
        raise ValueError("候选输出不能与原始 cookie 源文件相同")
    if lexical_output.is_symlink():
        raise ValueError("候选输出不能是符号链接")

    parent = lexical_output.parent
    if parent.is_symlink():
        raise ValueError("候选输出目录不能是符号链接")
    if not parent.is_dir():
        raise ValueError("候选输出目录不存在或不是目录")

    common = Path(os.path.commonpath((lexical_root, lexical_output)))
    cursor = common
    for component in parent.relative_to(common).parts:
        cursor /= component
        if cursor.is_symlink():
            raise ValueError("候选输出路径不能经过符号链接")

    resolved_parent = parent.resolve(strict=True)
    resolved_output = resolved_parent / lexical_output.name
    if _is_within(resolved_output, resolved_root):
        raise ValueError("候选输出的解析路径必须位于仓库外")
    if resolved_output == source:
        raise ValueError("候选输出不能与原始 cookie 源文件相同")

    try:
        output_stat = lexical_output.lstat()
    except FileNotFoundError:
        pass
    else:
        if not stat.S_ISREG(output_stat.st_mode):
            raise ValueError("候选输出已存在且不是普通文件")
        if os.path.samefile(lexical_output, source):
            raise ValueError("候选输出不能与原始 cookie 源文件相同")

    return lexical_output


def filter_cookie_jar(
    source: Path | str,
    *,
    output: Path | str,
    repo_root: Path | str = REPO_ROOT,
) -> FilterResult:
    repo_path = Path(repo_root).expanduser()
    source_path = _validate_source(Path(source), repo_path)
    destination = _validate_output(Path(output), repo_path, source_path)

    retained_lines: list[bytes] = []
    discarded = 0
    now = int(time.time())
    live_names = {"youtube": set(), "bilibili": set()}
    with source_path.open("rb") as handle:
        for raw_line in handle:
            metadata = _metadata_from_line(raw_line)
            if metadata is None:
                continue
            domain, name, expiry = metadata
            if _allowed_domain(domain):
                retained_lines.append(raw_line.rstrip(b"\r\n") + b"\n")
                service = _domain_service(domain)
                if service is not None and _is_live(expiry, now):
                    live_names[service].add(name)
            else:
                discarded += 1
    if not retained_lines:
        raise ValueError("过滤后没有 YouTube / Google / B站 cookie，拒绝生成候选文件")

    missing_youtube = REQUIRED_YOUTUBE_NAMES - live_names["youtube"]
    missing_bilibili = REQUIRED_BILIBILI_NAMES - live_names["bilibili"]
    if missing_youtube or missing_bilibili:
        parts = []
        if missing_youtube:
            parts.append(
                "YouTube/Google 缺 "
                + ",".join(sorted(name.decode("ascii") for name in missing_youtube))
            )
        if missing_bilibili:
            parts.append(
                "Bilibili 缺 "
                + ",".join(sorted(name.decode("ascii") for name in missing_bilibili))
            )
        raise ValueError("过滤结果关键字段不完整，拒绝生成候选文件: " + "；".join(parts))

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.next.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(b"# Netscape HTTP Cookie File\n")
            handle.write(b"# Filtered target domains only; do not commit.\n")
            for line in retained_lines:
                handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        os.chmod(destination, 0o600)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise

    return FilterResult(
        output=destination,
        retained=len(retained_lines),
        discarded=discarded,
    )


def main(argv: list[str] | None = None, *, repo_root: Path | str = REPO_ROOT) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3 or args[1] != "--output":
        print(
            "用法: python3 tools/video/filter_cookie_jar.py "
            "/outside/repo/raw.txt --output /outside/repo/candidate.txt",
            file=sys.stderr,
        )
        return 2
    try:
        result = filter_cookie_jar(args[0], output=args[2], repo_root=repo_root)
    except ValueError as error:
        print(f"COOKIE FILTER: FAIL — {error}", file=sys.stderr)
        return 1
    except OSError as error:
        detail = error.strerror or error.__class__.__name__
        print(f"COOKIE FILTER: FAIL — 文件系统错误: {detail}", file=sys.stderr)
        return 1
    print(
        f"COOKIE FILTER: PASS retained={result.retained} discarded={result.discarded} "
        f"output={result.output.name} mode=0600"
    )
    print("未输出任何 cookie value；请继续运行 check_yt_cookie.py 静态预检。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
