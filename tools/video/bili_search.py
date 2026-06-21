#!/usr/bin/env python3
"""B站视频搜索（WBI 签名）。用法: python bili_search.py "关键词" [n]
读仓库根目录 www.bilibili.com_cookies.txt (Netscape) 做登录态 + 风控通过。"""
import sys, time, hashlib, urllib.parse, urllib.request, json, http.cookiejar
from pathlib import Path

CK = Path(__file__).resolve().parents[2] / "www.bilibili.com_cookies.txt"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

MIXIN_TAB = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,
             29,28,14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,
             22,25,54,21,56,59,6,63,57,62,11,36,20,34,44,52]

cj = http.cookiejar.MozillaCookieJar(str(CK))
cj.load(ignore_discard=True, ignore_expires=True)
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", UA), ("Referer", "https://www.bilibili.com/")]

def get_json(url):
    with opener.open(url, timeout=20) as r:
        return json.load(r)

def mixin_key(orig):
    return "".join(orig[i] for i in MIXIN_TAB)[:32]

def get_keys():
    nav = get_json("https://api.bilibili.com/x/web-interface/nav")
    wi = nav["data"]["wbi_img"]
    ik = wi["img_url"].rsplit("/", 1)[1].split(".")[0]
    sk = wi["sub_url"].rsplit("/", 1)[1].split(".")[0]
    return ik, sk

def enc_wbi(params, ik, sk):
    mk = mixin_key(ik + sk)
    params["wts"] = round(time.time())
    params = dict(sorted(params.items()))
    params = {k: "".join(c for c in str(v) if c not in "!'()*") for k, v in params.items()}
    q = urllib.parse.urlencode(params)
    params["w_rid"] = hashlib.md5((q + mk).encode()).hexdigest()
    return params

def search(keyword, n=8):
    ik, sk = get_keys()
    params = enc_wbi({"search_type": "video", "keyword": keyword, "page": 1}, ik, sk)
    url = "https://api.bilibili.com/x/web-interface/wbi/search/type?" + urllib.parse.urlencode(params)
    d = get_json(url)
    if d.get("code") != 0:
        print("ERR", d.get("code"), d.get("message")); return
    res = d.get("data", {}).get("result", []) or []
    import re
    for r in res[:n]:
        title = re.sub("<[^>]+>", "", r.get("title", ""))
        print(f'{r.get("bvid")} | {r.get("duration")} | {r.get("author")} | {title}')

if __name__ == "__main__":
    kw = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    time.sleep(0.3)
    search(kw, n)
