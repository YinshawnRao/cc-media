#!/usr/bin/env python3
"""静态预检 YouTube Netscape cookie jar 的结构、过期时间和文件权限。

用法：
    python3 tools/video/check_yt_cookie.py [cookie文件]

未显式传文件时，始终从仓库根目录选择 ``all_cookies.txt``；仅当它不存在时，
才回退旧的 ``www.youtube.com_cookies.txt``。本工具不会联网，因此通过只表示：
所需字段存在、按文件内时间戳尚未过期、文件未向 group/other 开放。它不能证明
YouTube 服务端仍接受这份会话；解析时不会保留或输出 cookie value。
"""

from __future__ import annotations

import stat
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HTTPONLY_PREFIX = "#HttpOnly_"
REQUIRED = [
    "LOGIN_INFO",
    "SID",
    "HSID",
    "SSID",
    "SAPISID",
    "APISID",
    "__Secure-3PSID",
]
HELPFUL = [
    "__Secure-1PSID",
    "__Secure-1PAPISID",
    "__Secure-3PAPISID",
    "__Secure-1PSIDTS",
    "__Secure-3PSIDTS",
]
AUTH_HASH_NAMES = {"SAPISID", "__Secure-3PAPISID", "__Secure-1PAPISID"}
ALLOWED_DOMAIN_SUFFIXES = ("youtube.com", "google.com", "bilibili.com")


def default_cookie_path(repo_root: Path | None = None) -> Path:
    """Return the repository-anchored preferred jar, with legacy fallback."""

    root = REPO_ROOT if repo_root is None else Path(repo_root)
    preferred = root / "all_cookies.txt"
    if preferred.is_file():
        return preferred
    return root / "www.youtube.com_cookies.txt"


def _parse_netscape_line(line: str) -> tuple[str, str, str] | None:
    """Parse only domain/name/expiry, preserving Netscape HttpOnly records."""

    if not line.strip():
        return None
    if line.startswith(HTTPONLY_PREFIX):
        line = line[len(HTTPONLY_PREFIX) :]
    elif line.startswith("#"):
        return None

    fields = line.split("\t")
    if len(fields) < 7:
        return None
    return fields[0], fields[5], fields[4]


def load(path: Path | str) -> list[tuple[str, str, str]]:
    """Load non-secret metadata from a Netscape jar; cookie values are discarded."""

    rows: list[tuple[str, str, str]] = []
    for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        row = _parse_netscape_line(line)
        if row is not None:
            rows.append(row)
    return rows


def _expiry_epoch(value: str) -> int | None:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return None


def _is_live(expiry: str, now: int) -> bool:
    epoch = _expiry_epoch(expiry)
    return epoch is not None and (epoch == 0 or epoch > now)


def _permission_check(path: Path) -> tuple[bool, str]:
    mode = stat.S_IMODE(path.stat().st_mode)
    safe = mode & 0o077 == 0
    return safe, f"{mode:04o}"


def _allowed_domain(domain: str) -> bool:
    normalized = domain.removeprefix("#HttpOnly_").lstrip(".").lower()
    return any(
        normalized == suffix or normalized.endswith(f".{suffix}")
        for suffix in ALLOWED_DOMAIN_SUFFIXES
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("用法: python3 tools/video/check_yt_cookie.py [cookie文件]")
        return 2

    path = Path(args[0]).expanduser() if args else default_cookie_path()
    if not path.is_file():
        print(f"✗ 文件不存在: {path}")
        return 2

    rows = load(path)
    now = int(time.time())
    domains = {domain for domain, _, _ in rows}
    by_name: dict[str, list[tuple[str, str]]] = {}
    for domain, name, expiry in rows:
        by_name.setdefault(name, []).append((domain, expiry))

    permission_ok, mode_text = _permission_check(path)
    print(f"文件: {path}")
    print(f"cookie 元数据条目: {len(rows)}（不保留、不输出 value）")
    print(
        f"文件权限: {mode_text} "
        + ("✓ 仅当前用户可访问" if permission_ok else "✗ group/other 可访问；请 chmod 600")
    )
    has_google = any(
        domain.lstrip(".").lower() == "google.com"
        or domain.lstrip(".").lower().endswith(".google.com")
        for domain in domains
    )
    print(
        ".google.com 元数据: "
        + ("有" if has_google else "无（SID/HSID/SSID/SAPISID 通常需要该域）")
    )
    print("-" * 52)

    unexpected_domains = {domain for domain in domains if not _allowed_domain(domain)}
    allowlist_ok = not unexpected_domains
    print(
        "目标域 allowlist: "
        + (
            "✓ 仅含 YouTube / Google / B站"
            if allowlist_ok
            else f"✗ 含 {len(unexpected_domains)} 个非目标域"
        )
    )

    ok = permission_ok and allowlist_ok

    def check(name: str, required: bool) -> bool:
        entries = by_name.get(name)
        if not entries:
            print(f"  {'✗' if required else '·'} {name:20s} 缺失")
            return not required
        live_expiries = [expiry for _, expiry in entries if _is_live(expiry, now)]
        if not live_expiries:
            print(f"  ✗ {name:20s} 已过期或 expiry 格式无效")
            return not required
        dated = [
            epoch
            for expiry in live_expiries
            if (epoch := _expiry_epoch(expiry)) is not None and epoch > 0
        ]
        earliest = min(dated, default=0)
        when = time.strftime("%Y-%m-%d", time.localtime(earliest)) if earliest else "session"
        print(f"  ✓ {name:20s} 在 (exp {when})")
        return True

    print("必需（静态登录态字段）:")
    for name in REQUIRED:
        if not check(name, True):
            ok = False
    print("辅助:")
    for name in HELPFUL:
        check(name, False)

    can_hash = any(
        name in by_name
        and any(_is_live(expiry, now) for _, expiry in by_name[name])
        for name in AUTH_HASH_NAMES
    )
    print("-" * 52)
    if not can_hash:
        print("✗ 无未过期的 SAPISID / __Secure-*APISID，无法计算 auth hash")
        ok = False

    if ok:
        print("静态预检结果: ✓ 结构、文件内过期时间与权限检查通过")
    else:
        print("静态预检结果: ✗ 结构、目标域 allowlist、文件内过期时间或权限不合格")
    print("注意: 静态预检不验证服务端会话新鲜度；实际 yt-dlp 请求仍可能被拒绝。")
    if not ok:
        print(
            "修复: 在仓库外准备 0600 原始导出，再运行 tools/video/filter_cookie_jar.py "
            "过滤目标域并原子覆盖 all_cookies.txt。"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
