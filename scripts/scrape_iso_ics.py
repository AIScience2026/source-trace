#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 iso.org 的 ICS 分类页批量提取「标准号 -> standard/xxx.html」映射。
比逐条 web_search 快得多，且 URL 直接从官网来，可信。
"""
import urllib.request, ssl, socket, re, json

socket.setdefaulttimeout(25)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
}

ICS_PAGES = {
    # 人因工程 / 人机交互
    "13.180": "https://www.iso.org/ics/13.180.html",
    # IT 终端（9241 有一部分归这里）
    "35.080": "https://www.iso.org/ics/35.080.html",
    "35.180": "https://www.iso.org/ics/35.180.html",
    # 工业机器人 / 制造
    "25.040.30": "https://www.iso.org/ics/25.040.30.html",
    # 机械安全
    "13.110": "https://www.iso.org/ics/13.110.html",
}

# 我们关心的标准号（会从页面里找这些）
WANTED = [
    "9241-210", "9241-211", "9241-220", "9241-230", "9241-240", "9241-280", "9241-222",
    "10218-1", "10218-2", "15066", "8373", "9283", "9409-1", "9787", "14539",
    "61508-1", "61508-2", "62061",
]

found = {}

for ics, url in ICS_PAGES.items():
    try:
        req = urllib.request.Request(url, headers=H, method="GET")
        html = urllib.request.urlopen(req, context=ctx).read().decode("utf-8", "ignore")
    except Exception as e:
        print("❌ 抓取 %s 失败: %s" % (ics, e))
        continue

    # 页面结构：<a href="/standard/77520.html">ISO 9241-210:2019 ...</a>
    links = re.findall(
        r'href="(/standard/(\d+)\.html[^"]*)"[^>]*>\s*(ISO[^<]{5,120})<', html)

    for path, sid, label in links:
        label_clean = re.sub(r"\s+", " ", label).strip()
        for w in WANTED:
            # 匹配 ISO 9241-210 / ISO/TS 15066 / ISO 10218-1 等
            if w in label_clean:
                # 同一标准可能多个版本，保留第一个（页面上通常把最新版放前面）
                if w not in found:
                    found[w] = {
                        "standard": label_clean,
                        "url": "https://www.iso.org" + path,
                        "ics": ics,
                    }
    print("  [%s] 页内链接 %d 条，累计命中 %d" % (ics, len(links), len(found)))

print()
print("=== 命中 %d / %d 个标准 ===" % (len(found), len(WANTED)))
for w in WANTED:
    if w in found:
        f = found[w]
        print("✅ %-10s %-55s %s" % (w, f["standard"][:55], f["url"]))
    else:
        print("❌ %-10s 未在分类页找到（需单独 search）" % w)

with open("scripts/iso_url_map.json", "w", encoding="utf-8") as fp:
    json.dump(found, fp, ensure_ascii=False, indent=2)
print()
print("已存 scripts/iso_url_map.json")
