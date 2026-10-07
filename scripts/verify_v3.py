#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 核实 v3：用已搜到的候选地址做 HTTP + 内容校验（不再调 web_search）
"""
import urllib.request, ssl, socket, re, json

socket.setdefaulttimeout(20)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/pdf,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# id -> (url, 必须出现的关键词)
TESTS = {
    15: ("https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.700-1.pdf", ["Red-Teaming"]),
    54: ("https://www.technologyreview.com/supertopic/innovators-under-35-2025",
         ["Innovators Under 35"]),
    50: ("https://montrealethics.ai", ["Montreal AI Ethics Institute"]),
    51: ("https://montrealethics.ai/ai-policy-corner-frontier-ai-safety-commitments-ai-seoul-summit-2024",
         ["Frontier AI Safety Commitments"]),
    25: ("https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=F75971615787A4B9C3C08AEE76A421FC",
         ["GB/T 36530", "个人助理机器人"]),
    55: ("https://www.iso.org/standard/88373.html", ["9241-222"]),
}

ok = {}
for sid, (url, kws) in TESTS.items():
    try:
        req = urllib.request.Request(url, headers=H, method="GET")
        with urllib.request.urlopen(req, context=ctx) as resp:
            body = resp.read(4000)
            head = body[:8]
            is_pdf = head.startswith(b"%PDF")
            text = "" if is_pdf else body.decode("utf-8", "ignore")
            title = re.search(r"<title>(.*?)</title>", text, re.S)
            title = re.sub(r"\s+", " ", title.group(1)).strip()[:60] if title else ("(PDF)" if is_pdf else "?")

            missing = [k for k in kws
                       if not (is_pdf or k in text or k in (title or ""))]
            if resp.status == 200 and not missing:
                print("✅ #%-3d %-58s title=%s" % (sid, url[:58], title))
                ok[sid] = url
            else:
                print("⚠️  #%-3d 内容缺 %s title=%s" % (sid, missing, title))
    except urllib.error.HTTPError as e:
        print("❌ #%-3d HTTP %d %s" % (sid, e.code, url[:60]))
    except Exception as e:
        print("❌ #%-3d %s %s" % (sid, type(e).__name__, url[:60]))

print()
print("=== 本轮通过 %d 条 ===" % len(ok))
for sid, url in sorted(ok.items()):
    print("  %d -> %s" % (sid, url))

with open("scripts/verified_v3.json", "w", encoding="utf-8") as f:
    json.dump(ok, f, ensure_ascii=False, indent=2)
print("\n已存 scripts/verified_v3.json")
