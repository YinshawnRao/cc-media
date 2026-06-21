#!/usr/bin/env python3
"""校验 YouTube cookies.txt 是否含有效登录态（不用跑 yt-dlp 就能秒判）。
用法: python3 tools/video/check_yt_cookie.py [cookie文件]  (默认仓库根目录 www.youtube.com_cookies.txt)

判定逻辑（基于实战）：
- yt-dlp 过 YouTube bot 检查需要"已登录"的 cookie 集合。
- 必需(任缺其一基本会被 bot 拦)：LOGIN_INFO + SID + HSID + SSID + SAPISID + APISID
  （这些是首登录态 cookie；只有登录后才会出现。也可能在 .google.com 域上。）
- 可计算 auth hash 的：SAPISID 或 __Secure-3PAPISID（至少一个）。
- 任何必需 cookie 已过期同样视为失败。
"""
import sys, time
from pathlib import Path

REQUIRED = ["LOGIN_INFO", "SID", "HSID", "SSID", "SAPISID", "APISID"]
HELPFUL  = ["__Secure-1PSID", "__Secure-3PSID", "__Secure-1PAPISID", "__Secure-3PAPISID",
            "__Secure-1PSIDTS", "__Secure-3PSIDTS"]

def load(path):
    rows = []
    for ln in Path(path).read_text(errors="ignore").splitlines():
        if ln.startswith("#") or not ln.strip():
            continue
        f = ln.split("\t")
        if len(f) >= 7:
            rows.append((f[0], f[5], f[4]))  # domain, name, expiry
    return rows

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "www.youtube.com_cookies.txt"
    if not Path(path).exists():
        print(f"✗ 文件不存在: {path}"); return 2
    rows = load(path)
    now = int(time.time())
    domains = sorted({d for d, _, _ in rows})
    by_name = {}
    for d, n, e in rows:
        by_name.setdefault(n, []).append((d, e))
    print(f"文件: {path}")
    print(f"cookie 总数: {len(rows)} | 域: {', '.join(domains)}")
    has_google = any(".google.com" in d for d in domains)
    print(f".google.com 行: {'有' if has_google else '无（注意：SID/HSID/SSID/SAPISID 多在 .google.com 上）'}")
    print("-" * 52)
    ok = True
    def check(name, required):
        global_ok = True
        if name not in by_name:
            print(f"  {'✗' if required else '·'} {name:20s} 缺失")
            return not required
        entries = by_name[name]
        live = [e for _, e in entries if int(e or 0) == 0 or int(e or 0) > now]
        if not live:
            print(f"  ✗ {name:20s} 已过期")
            return not required
        exp = min((int(e) for _, e in entries if int(e or 0) > 0), default=0)
        when = time.strftime("%Y-%m-%d", time.localtime(exp)) if exp else "session"
        print(f"  ✓ {name:20s} 在 (exp {when})")
        return True
    print("必需（登录态）:")
    for n in REQUIRED:
        if not check(n, True): ok = False
    print("辅助:")
    for n in HELPFUL:
        check(n, False)
    # auth hash 能力
    can_hash = any(x in by_name for x in ["SAPISID", "__Secure-3PAPISID", "__Secure-1PAPISID"])
    print("-" * 52)
    if not can_hash:
        print("✗ 无 SAPISID / __Secure-*APISID → yt-dlp 无法算 auth hash"); ok = False
    print("结果:", "✓ 合格，应该能过 bot 检查" if ok else "✗ 不合格——缺登录态 cookie，会被 bot 拦")
    if not ok:
        print("\n修复：无痕窗口登录 youtube.com → 用扩展导出（确保含 LOGIN_INFO/SID/HSID/SSID/SAPISID）")
        print("      → 覆盖该文件 → 直接关无痕窗口（别登出，避免 cookie 被轮换作废）")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
