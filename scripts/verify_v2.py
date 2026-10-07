#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 核实 v2：HTTP 200 + 内容关键词双重校验。
避免出现"URL 可达但内容不是那条信源"的假阳性。
"""
import urllib.request, ssl, socket, re, sys

socket.setdefaulttimeout(20)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# id -> (候选 URL, 内容必须包含的关键词列表)
TESTS = {
    11: [
        ("https://www.stats.gov.cn/gk/tjfg/xgfxfg/202503/t20250310_1958928.html",
         ["数据安全法"], [])
    ],
    12: [
        ("https://www.stats.gov.cn/gk/tjfg/xgfxfg/202503/t20250310_1958923.html",
         ["个人信息保护法"], [])
    ],
    13: [
        ("https://www.cac.gov.cn/2016-11/07/c_1119867116.htm",
         ["网络安全法"], [])
    ],
}


def fetch(url):
    req = urllib.request.Request(url, headers=H, method="GET")
    with urllib.request.urlopen(req, context=ctx) as resp:
        return resp.status, resp.read().decode("utf-8", "ignore")


def main():
    verified = {}
    for sid, cases in TESTS.items():
        for url, must_have, must_not in cases:
            try:
                status, html = fetch(url)
            except urllib.error.HTTPError as e:
                print("❌ #%d HTTP %d  %s" % (sid, e.code, url[:85]))
                continue
            except Exception as e:
                print("❌ #%d %s  %s" % (sid, type(e).__name__, url[:85]))
                continue

            title_m = re.search(r"<title>(.*?)</title>", html, re.S)
            title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""

            bad = [k for k in must_have if k not in html and k not in title]
            wrong = [k for k in must_not if k in html]
            if bad or wrong:
                print("⚠️  #%d 内容不符 (缺:%s / 误含:%s)  title=%r" % (sid, bad, wrong, title[:40]))
                continue

            if status == 200:
                print("✅ #%d 内容核实通过  title=%r" % (sid, title[:45]))
                print("        %s" % url)
                verified[sid] = url
            else:
                print("❌ #%d HTTP %d" % (sid, status))

    print()
    print("=== 可写入 compliance.db ===")
    for sid, url in sorted(verified.items()):
        print("  %d -> %s" % (sid, url))


if __name__ == "__main__":
    main()
