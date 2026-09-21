#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条导入信源 #14-#25"""
import sys
sys.path.insert(0, ".")
from compliance_db import get_conn, upsert_source

entries = [
    {
        "url": "https://temp.source-trace.local/14-nist-ai-600-1",
        "type": "official_guideline",
        "title": "NIST AI 600-1",
        "confidence": 0.90,
        "domain": "nist.gov",
        "keywords": ["NIST AI 600-1", "生成式AI风险管理", "GPAI", "NIST AI 600-1"],
        "soft_aliases": ["生成式AI风险管理"],
        "context_map": {"NIST AI 600-1": ["NIST", "生成式", "风险管理"], "生成式AI风险管理": ["NIST", "生成式"]},
        "timeline_events": [
            {"ts": "2024", "event": "NIST 发布 AI 600-1（生成式AI风险管理）", "source": "nist.gov", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/15-nist-ai-700-1",
        "type": "official_guideline",
        "title": "NIST AI 700-1",
        "confidence": 0.90,
        "domain": "nist.gov",
        "keywords": ["NIST AI 700-1", "AI安全测试", "AI评估", "red teaming", "NIST AI 700-1"],
        "soft_aliases": ["AI安全测试"],
        "context_map": {"NIST AI 700-1": ["NIST", "安全", "测试"], "AI安全测试": ["NIST", "安全"]},
        "timeline_events": [
            {"ts": "2024", "event": "NIST 发布 AI 700-1（AI安全测试）", "source": "nist.gov", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/16-oecd-ai",
        "type": "official_guideline",
        "title": "OECD AI 原则",
        "confidence": 0.92,
        "domain": "oecd.org",
        "keywords": ["OECD AI", "AI原则", "可信AI", "OECD AI 原则"],
        "soft_aliases": ["OECD AI", "可信AI"],
        "context_map": {"OECD AI": ["OECD", "原则", "可信"], "可信AI": ["OECD", "原则"]},
        "timeline_events": [
            {"ts": "2019-05-22", "event": "OECD 发布 AI 原则", "source": "oecd.org", "tag": "initial_claim", "confidence": 0.92},
        ],
    },
    {
        "url": "https://temp.source-trace.local/17-unesco-ai",
        "type": "official_guideline",
        "title": "UNESCO AI 伦理建议书",
        "confidence": 0.92,
        "domain": "unesco.org",
        "keywords": ["UNESCO AI伦理", "AI伦理", "伦理框架", "UNESCO AI 伦理建议书"],
        "soft_aliases": ["UNESCO AI伦理", "AI伦理"],
        "context_map": {"UNESCO AI伦理": ["UNESCO", "伦理", "建议书"], "AI伦理": ["UNESCO", "伦理"]},
        "timeline_events": [
            {"ts": "2021-11-30", "event": "UNESCO 通过 AI 伦理建议书", "source": "unesco.org", "tag": "initial_claim", "confidence": 0.92},
        ],
    },
    {
        "url": "https://temp.source-trace.local/18-iso-9241-210",
        "type": "official_standard",
        "title": "ISO 9241-210 人因工程设计",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-210", "以人为中心设计", "HCD", "UCD", "ISO 9241-210"],
        "soft_aliases": ["以人为中心设计", "HCD", "UCD"],
        "context_map": {"ISO 9241-210": ["ISO", "设计", "人因"], "以人为中心设计": ["ISO", "设计"]},
        "timeline_events": [
            {"ts": "2019", "event": "ISO 发布 9241-210:2019", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/19-iso-9241-211",
        "type": "official_standard",
        "title": "ISO 9241-211 设计规范",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-211", "HCD设计规范", "可用性工程", "ISO 9241-211"],
        "soft_aliases": ["HCD设计规范"],
        "context_map": {"ISO 9241-211": ["ISO", "设计规范"], "HCD设计规范": ["ISO", "设计"]},
        "timeline_events": [
            {"ts": "2019", "event": "ISO 发布 9241-211:2019", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/20-iso-9241-220",
        "type": "official_standard",
        "title": "ISO 9241-220 用户体验度量",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-220", "UX度量", "用户体验", "可用性度量", "ISO 9241-220"],
        "soft_aliases": ["UX度量", "用户体验"],
        "context_map": {"ISO 9241-220": ["ISO", "度量", "用户体验"], "UX度量": ["ISO", "度量"]},
        "timeline_events": [
            {"ts": "2019", "event": "ISO 发布 9241-220:2019", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/21-iso-9241-230",
        "type": "official_standard",
        "title": "ISO 9241-230 语音交互",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-230", "语音交互", "VUI", "语音界面", "ISO 9241-230"],
        "soft_aliases": ["语音交互", "VUI"],
        "context_map": {"ISO 9241-230": ["ISO", "语音", "交互"], "语音交互": ["ISO", "语音"]},
        "timeline_events": [
            {"ts": "2018", "event": "ISO 发布 9241-230:2018", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/22-iso-9241-240",
        "type": "official_standard",
        "title": "ISO 9241-240 人因工效学",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-240", "人因工效学", "工效学设计", "ISO 9241-240"],
        "soft_aliases": ["人因工效学"],
        "context_map": {"ISO 9241-240": ["ISO", "工效学"], "人因工效学": ["ISO", "工效学"]},
        "timeline_events": [
            {"ts": "2022", "event": "ISO 发布 9241-240:2022", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/23-iso-9241-280",
        "type": "official_standard",
        "title": "ISO 9241-280 无障碍设计",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-280", "无障碍", "可访问性", "WCAG", "ISO 9241-280"],
        "soft_aliases": ["无障碍", "可访问性"],
        "context_map": {"ISO 9241-280": ["ISO", "无障碍"], "无障碍": ["ISO", "无障碍"]},
        "timeline_events": [
            {"ts": "2020", "event": "ISO 发布 9241-280:2020", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/24-gb-t-41870-2022",
        "type": "official_standard",
        "title": "GB/T 41870-2022 社交机器人",
        "confidence": 0.90,
        "domain": "gov.cn",
        "keywords": ["GB/T 41870", "社交机器人", "chatbot", "对话系统", "GB/T 41870-2022"],
        "soft_aliases": ["社交机器人", "chatbot"],
        "context_map": {"GB/T 41870": ["GB/T", "机器人", "社交"], "社交机器人": ["GB/T", "机器人"]},
        "timeline_events": [
            {"ts": "2022", "event": "中国发布 GB/T 41870-2022《社交机器人》", "source": "gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/25-gb-t-36430-2018",
        "type": "official_standard",
        "title": "GB/T 36430-2018 服务机器人性能",
        "confidence": 0.90,
        "domain": "gov.cn",
        "keywords": ["GB/T 36430", "服务机器人", "性能测试", "机器人评价", "GB/T 36430-2018"],
        "soft_aliases": ["服务机器人"],
        "context_map": {"GB/T 36430": ["GB/T", "服务机器人"], "服务机器人": ["GB/T", "服务机器人"]},
        "timeline_events": [
            {"ts": "2018", "event": "中国发布 GB/T 36430-2018《服务机器人性能》", "source": "gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
]

conn = get_conn()
for e in entries:
    sid = upsert_source(
        url=e["url"],
        type=e["type"],
        title=e["title"],
        confidence=e["confidence"],
        domain=e.get("domain"),
        timeline_events=e.get("timeline_events"),
        keywords=e.get("keywords"),
        soft_aliases=e.get("soft_aliases"),
        context_map=e.get("context_map"),
    )
    print(f"✅ {e['title'][:30]:<30} -> id={sid}")

cur = conn.execute("SELECT COUNT(*) FROM sources")
print(f"\n总条数: {cur.fetchone()[0]}")
conn.close()
