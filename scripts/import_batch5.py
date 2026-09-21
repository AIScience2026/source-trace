#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条导入信源 #38-40 + 剩余 AI 层 + 补充条目"""
import sys
sys.path.insert(0, ".")
from compliance_db import get_conn, upsert_source

entries = [
    {
        "url": "https://temp.source-trace.local/38-ieee-p7000",
        "type": "official_standard",
        "title": "IEEE P7000 - Model Standard for Trustworthy Autonomous Systems",
        "confidence": 0.93,
        "domain": "ieee.org",
        "keywords": ["IEEE P7000", "可信AI", "自主系统", "IEEE P7000"],
        "soft_aliases": ["IEEE P7000"],
        "context_map": {"IEEE P7000": ["IEEE", "可信", "自主"], "可信AI": ["IEEE", "可信"]},
        "timeline_events": [
            {"ts": "2022", "event": "IEEE 发布 P7000 标准", "source": "ieee.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/39-ieee-p2864",
        "type": "official_standard",
        "title": "IEEE P2864 - AI System Lifecycle",
        "confidence": 0.93,
        "domain": "ieee.org",
        "keywords": ["IEEE 2864", "AI生命周期", "RMF", "IEEE P2864"],
        "soft_aliases": ["IEEE 2864"],
        "context_map": {"IEEE 2864": ["IEEE", "生命周期"], "AI生命周期": ["IEEE", "生命周期"]},
        "timeline_events": [
            {"ts": "2023", "event": "IEEE 发布 P2864 标准", "source": "ieee.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://www.europarl.europa.eu/topics/en/article/20230601STO93804/eu-ai-act-first-regulation-on-artificial-intelligence",
        "type": "official_regulation",
        "title": "EU Ethics Guidelines for Trustworthy AI",
        "confidence": 0.90,
        "domain": "europarl.europa.eu",
        "keywords": ["EU可信AI", "伦理指南", "可信AI", "EU Ethics Guidelines"],
        "soft_aliases": ["EU可信AI"],
        "context_map": {"EU可信AI": ["EU", "伦理", "可信"], "可信AI": ["EU", "伦理"]},
        "timeline_events": [
            {"ts": "2019", "event": "EU 发布可信 AI 伦理指南", "source": "europarl.europa.eu", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/41-asilomar",
        "type": "official_guideline",
        "title": "Asilomar AI Principles",
        "confidence": 0.90,
        "domain": "futureoflife.org",
        "keywords": ["Asilomar", "AI原则", "beneficial AI", "Asilomar AI Principles"],
        "soft_aliases": ["Asilomar"],
        "context_map": {"Asilomar": ["原则", "beneficial AI"], "AI原则": ["Asilomar", "原则"]},
        "timeline_events": [
            {"ts": "2017", "event": "Future of Life Institute 发布 Asilomar AI 原则", "source": "futureoflife.org", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/42-beijing-ai",
        "type": "official_guideline",
        "title": "Beijing AI Principles",
        "confidence": 0.90,
        "domain": "baai.ac.cn",
        "keywords": ["北京智源", "AI原则", "中国AI伦理", "Beijing AI Principles"],
        "soft_aliases": ["北京智源"],
        "context_map": {"北京智源": ["北京", "原则"], "中国AI伦理": ["北京", "原则"]},
        "timeline_events": [
            {"ts": "2019", "event": "北京智源发布 AI 原则", "source": "baai.ac.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/43-montreal",
        "type": "official_guideline",
        "title": "Montreal AI Ethics Institute Principles",
        "confidence": 0.90,
        "domain": "montrealethics.ai",
        "keywords": ["Montreal AI Ethics", "AI伦理原则", "Montreal AI Ethics Institute"],
        "soft_aliases": ["Montreal AI Ethics"],
        "context_map": {"Montreal AI Ethics": ["Montreal", "伦理"], "AI伦理原则": ["Montreal", "伦理"]},
        "timeline_events": [
            {"ts": "2018", "event": "Montreal AI Ethics Institute 发布 AI 伦理原则", "source": "montrealethics.ai", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/44-ai-safety",
        "type": "official_report",
        "title": "AI Safety Institute: Frontier AI Safety Commitments",
        "confidence": 0.90,
        "domain": "aisafety.gov",
        "keywords": ["AI安全", "Frontier AI", "AI安全承诺", "Frontier AI Safety"],
        "soft_aliases": ["AI安全"],
        "context_map": {"AI安全": ["AI安全", "Frontier AI"], "Frontier AI": ["AI安全", "Frontier"]},
        "timeline_events": [
            {"ts": "2023", "event": "AI Safety Institute 发布 Frontier AI 安全承诺", "source": "aisafety.gov", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/45-openai-charter",
        "type": "official_guideline",
        "title": "OpenAI Charter",
        "confidence": 0.90,
        "domain": "openai.com",
        "keywords": ["OpenAI Charter", "AGI", "AI原则", "OpenAI 宪章"],
        "soft_aliases": ["OpenAI Charter"],
        "context_map": {"OpenAI Charter": ["OpenAI", "AGI"], "AGI": ["OpenAI", "AGI"]},
        "timeline_events": [
            {"ts": "2018", "event": "OpenAI 发布 Charter", "source": "openai.com", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/46-stanford-ai-index",
        "type": "official_report",
        "title": "Stanford AI Index Report 2024",
        "confidence": 0.90,
        "domain": "aiindex.stanford.edu",
        "keywords": ["AI Index", "Stanford", "AI报告", "Stanford AI Index"],
        "soft_aliases": ["AI Index"],
        "context_map": {"AI Index": ["Stanford", "报告"], "Stanford AI Index": ["Stanford", "报告"]},
        "timeline_events": [
            {"ts": "2024", "event": "Stanford 发布 AI Index Report 2024", "source": "aiindex.stanford.edu", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/47-mit-tr35",
        "type": "official_report",
        "title": "MIT Technology Review 35 Innovators Under 35",
        "confidence": 0.90,
        "domain": "technologyreview.com",
        "keywords": ["MIT TR35", "35 Innovators Under 35", "青年 innovators", "MIT Technology Review"],
        "soft_aliases": ["MIT TR35"],
        "context_map": {"MIT TR35": ["MIT", " innovators"], "35 Innovators Under 35": ["MIT", " innovators"]},
        "timeline_events": [
            {"ts": "2024", "event": "MIT Technology Review 发布 35 Innovators Under 35", "source": "technologyreview.com", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/48-iso-9241-222",
        "type": "official_standard",
        "title": "ISO 9241-222:2026 以人为中心设计自评",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9241-222", "以人为中心设计自评", "HCD 自评", "ISO 9241-222"],
        "soft_aliases": ["ISO 9241-222", "以人为中心设计自评"],
        "context_map": {"ISO 9241-222": ["ISO", "自评", "人因"], "以人为中心设计自评": ["ISO", "自评"]},
        "timeline_events": [
            {"ts": "2026-06-26", "event": "ISO 发布 9241-222:2026", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
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
    print(f"✅ {e['title'][:35]:<35} -> id={sid}")

cur = conn.execute("SELECT COUNT(*) FROM sources")
print(f"\n总条数: {cur.fetchone()[0]}")
conn.close()
