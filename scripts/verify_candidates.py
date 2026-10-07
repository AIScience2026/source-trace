#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证候选 URL，返回真实可达的地址。
按优先级：发布部门官网 > 政府门户 > 维基文库（兜底）
"""
import urllib.request, urllib.error, ssl, socket
from concurrent.futures import ThreadPoolExecutor

socket.setdefaulttimeout(15)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# key = compliance.db 里的 id，value = 候选 URL 列表（按优先级）
CANDIDATES = {
    8: [  # 生成式人工智能服务管理暂行办法
        "https://www.cac.gov.cn/2023-07/13/c_1690898327029107.htm",
    ],
    9: [  # 互联网信息服务深度合成管理规定
        "https://www.cac.gov.cn/2022-12/11/c_1672221949318230.htm",
        "https://www.moj.gov.cn/pub/sfbgw/flfggz/flfggzbmgz/202307/t20230705_482071.html",
    ],
    11: [  # 数据安全法
        "https://papers.gov.cn/attachments/file/2021/DBMFZVER22.pdf",
    ],
    12: [  # 个人信息保护法
        "https://www.gov.cn/xinwen/2021-08/20/content_5632486.htm",
    ],
    13: [  # 网络安全法
        "https://www.gov.cn/xinwen/2016-11/07/content_5129723.htm",
    ],
}


def check_one(args):
    sid, url = args
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, context=ctx) as resp:
            resp.read(1024)
            return (sid, url, resp.status)
    except urllib.error.HTTPError as e:
        return (sid, url, e.code)
    except Exception as e:
        return (sid, url, "%s: %s" % (type(e).__name__, str(e)[:80]))


jobs = [(sid, u) for sid, urls in CANDIDATES.items() for u in urls]

with ThreadPoolExecutor(max_workers=6) as ex:
    results = list(ex.map(check_one, jobs))

print("=== 验证结果 ===")
ok = {}
for sid, url, status in results:
    mark = "✅" if status == 200 else "❌"
    print("%s #%-3d %-4s %s" % (mark, sid, status, url[:95]))
    if status == 200 and sid not in ok:
        ok[sid] = url

print()
print("=== 可直接写库的地址 ===")
for sid, url in sorted(ok.items()):
    print("  #%d -> %s" % (sid, url))
