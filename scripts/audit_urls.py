#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出全部信源 + HTTP 验证现有 URL
输出：scripts/url_audit.json
"""
import sqlite3, json, urllib.request, urllib.error, ssl, socket
from concurrent.futures import ThreadPoolExecutor

DB = "compliance.db"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

socket.setdefaulttimeout(12)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*",
}

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT id, title, url FROM sources ORDER BY id")
rows = c.fetchall()


def check(row):
    sid, title, url = row
    if "temp.source-trace.local" in (url or ""):
        return {"id": sid, "title": title, "url": url,
                "status": "placeholder", "http": None}
    # npc.gov.cn 等站点对 UA 敏感，且部分 URL 含中文需 quote 处理
    try:
        from urllib.parse import urlparse, urlunparse, quote
        p = urlparse(url)
        fixed = urlunparse((
            p.scheme, p.netloc,
            quote(p.path, safe="/%-._~!$&'()*+,;=:@"),
            p.params, quote(p.query, safe="=&%/"), p.fragment,
        ))
    except Exception:
        fixed = url
    try:
        req = urllib.request.Request(fixed, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, context=ctx) as resp:
            body_head = resp.read(2048)
            return {"id": sid, "title": title, "url": url,
                    "status": "ok", "http": resp.status, "bytes": len(body_head)}
    except urllib.error.HTTPError as e:
        # 403/404/503 等：站点活着但拒绝 —— 需要人工判断
        return {"id": sid, "title": title, "url": url,
                "status": "http_%d" % e.code, "http": e.code}
    except Exception as e:
        return {"id": sid, "title": title, "url": url,
                "status": "err", "detail": "%s: %s" % (type(e).__name__, str(e)[:120])}


with ThreadPoolExecutor(max_workers=8) as ex:
    results = list(ex.map(check, rows))

with open("scripts/url_audit.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 汇总
from collections import Counter
summary = Counter(r["status"] for r in results)
print("总计: %d 条" % len(results))
for k, v in summary.most_common():
    print("  %-12s %d" % (k, v))

print()
print("=== 非 placeholder 明细 ===")
for r in results:
    if r["status"] != "placeholder":
        print("  #%-3d %-45s -> %s %s" % (
            r["id"], r["title"][:45], r["status"], str(r.get("detail", ""))))
