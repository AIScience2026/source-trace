#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条导入信源 #51-70（Robotics 层：ISO/IEC/GB/T/IFR）"""
import sys
sys.path.insert(0, ".")
from compliance_db import get_conn, upsert_source

entries = [
    {
        "url": "https://temp.source-trace.local/51-iso-10218-1",
        "type": "official_standard",
        "title": "ISO 10218-1:2011 工业机器人安全 Part 1",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 10218", "工业机器人安全", "ISO 10218-1"],
        "soft_aliases": ["ISO 10218"],
        "context_map": {"ISO 10218": ["ISO", "工业机器人", "安全"], "工业机器人安全": ["ISO", "工业机器人"]},
        "timeline_events": [
            {"ts": "2011", "event": "ISO 发布 10218-1:2011", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/52-iso-10218-2",
        "type": "official_standard",
        "title": "ISO 10218-2:2011 工业机器人安全 Part 2",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 10218-2", "机器人系统安全", "ISO 10218-2"],
        "soft_aliases": ["ISO 10218-2"],
        "context_map": {"ISO 10218-2": ["ISO", "系统安全"], "机器人系统安全": ["ISO", "系统安全"]},
        "timeline_events": [
            {"ts": "2011", "event": "ISO 发布 10218-2:2011", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/53-iso-10218-2023",
        "type": "official_standard",
        "title": "ISO 10218-1:2023 修订版",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 10218-2023", "ISO 10218 修订", "工业机器人安全修订"],
        "soft_aliases": ["ISO 10218-2023"],
        "context_map": {"ISO 10218-2023": ["ISO", "修订"], "工业机器人安全修订": ["ISO", "修订"]},
        "timeline_events": [
            {"ts": "2023", "event": "ISO 发布 10218-1:2023 修订版", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/54-iso-15066",
        "type": "official_standard",
        "title": "ISO 15066:2016 协作机器人安全",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 15066", "协作机器人", "Cobot", "ISO 15066"],
        "soft_aliases": ["ISO 15066", "协作机器人", "Cobot"],
        "context_map": {"ISO 15066": ["ISO", "协作"], "协作机器人": ["ISO", "协作"]},
        "timeline_events": [
            {"ts": "2016", "event": "ISO 发布 15066:2016", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/55-iso-8373",
        "type": "official_standard",
        "title": "ISO 8373:2021 机器人术语",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 8373", "机器人术语", "定义", "ISO 8373"],
        "soft_aliases": ["ISO 8373"],
        "context_map": {"ISO 8373": ["ISO", "术语", "定义"], "机器人术语": ["ISO", "术语"]},
        "timeline_events": [
            {"ts": "2021", "event": "ISO 发布 8373:2021", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/56-iso-9283",
        "type": "official_standard",
        "title": "ISO 9283:1998 机器人性能规范",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9283", "机器人性能", "测试", "ISO 9283"],
        "soft_aliases": ["ISO 9283"],
        "context_map": {"ISO 9283": ["ISO", "性能", "测试"], "机器人性能": ["ISO", "性能"]},
        "timeline_events": [
            {"ts": "1998", "event": "ISO 发布 9283:1998", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/57-iso-9409",
        "type": "official_standard",
        "title": "ISO 9409-1:2004 机器人机械接口",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9409", "机械接口", "机器人安装", "ISO 9409"],
        "soft_aliases": ["ISO 9409"],
        "context_map": {"ISO 9409": ["ISO", "接口", "机械"], "机械接口": ["ISO", "接口"]},
        "timeline_events": [
            {"ts": "2004", "event": "ISO 发布 9409-1:2004", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/58-iso-9787",
        "type": "official_standard",
        "title": "ISO 9787:2023 机器人坐标系",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 9787", "机器人坐标系", "运动学", "ISO 9787"],
        "soft_aliases": ["ISO 9787"],
        "context_map": {"ISO 9787": ["ISO", "坐标", "运动学"], "机器人坐标系": ["ISO", "坐标"]},
        "timeline_events": [
            {"ts": "2023", "event": "ISO 发布 9787:2023", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/59-iso-14539",
        "type": "official_standard",
        "title": "ISO 14539:2023 机器人对象处理",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO 14539", "对象处理", "抓取", "ISO 14539"],
        "soft_aliases": ["ISO 14539"],
        "context_map": {"ISO 14539": ["ISO", "抓取", "操作"], "对象处理": ["ISO", "抓取"]},
        "timeline_events": [
            {"ts": "2023", "event": "ISO 发布 14539:2023", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/60-iec-61508-1",
        "type": "official_standard",
        "title": "IEC 61508-1:2010 功能安全基础",
        "confidence": 0.93,
        "domain": "iec.ch",
        "keywords": ["IEC 61508", "功能安全", "SIL", "IEC 61508-1"],
        "soft_aliases": ["IEC 61508"],
        "context_map": {"IEC 61508": ["IEC", "功能安全", "SIL"], "功能安全": ["IEC", "功能安全"]},
        "timeline_events": [
            {"ts": "2010", "event": "IEC 发布 61508-1:2010", "source": "iec.ch", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/61-iec-61508-2",
        "type": "official_standard",
        "title": "IEC 61508-2:2010 功能安全要求",
        "confidence": 0.93,
        "domain": "iec.ch",
        "keywords": ["IEC 61508-2", "安全要求", "IEC 61508-2"],
        "soft_aliases": ["IEC 61508-2"],
        "context_map": {"IEC 61508-2": ["IEC", "安全要求"], "安全要求": ["IEC", "安全要求"]},
        "timeline_events": [
            {"ts": "2010", "event": "IEC 发布 61508-2:2010", "source": "iec.ch", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/62-iec-62061",
        "type": "official_standard",
        "title": "IEC 62061:2021 机械安全",
        "confidence": 0.93,
        "domain": "iec.ch",
        "keywords": ["IEC 62061", "机械安全", "robotics", "IEC 62061"],
        "soft_aliases": ["IEC 62061"],
        "context_map": {"IEC 62061": ["IEC", "机械安全"], "机械安全": ["IEC", "机械安全"]},
        "timeline_events": [
            {"ts": "2021", "event": "IEC 发布 62061:2021", "source": "iec.ch", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "url": "https://temp.source-trace.local/64-gb-t-34131",
        "type": "official_standard",
        "title": "GB/T 34131-2017 工业机器人机械接口",
        "confidence": 0.90,
        "domain": "gov.cn",
        "keywords": ["GB/T 34131", "机械接口", "GB/T 34131-2017"],
        "soft_aliases": ["GB/T 34131"],
        "context_map": {"GB/T 34131": ["GB/T", "接口"], "机械接口": ["GB/T", "接口"]},
        "timeline_events": [
            {"ts": "2017", "event": "中国发布 GB/T 34131-2017", "source": "gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/65-gb-t-33240",
        "type": "official_standard",
        "title": "GB/T 33240-2016 机器人术语",
        "confidence": 0.90,
        "domain": "gov.cn",
        "keywords": ["GB/T 33240", "机器人术语", "GB/T 33240-2016"],
        "soft_aliases": ["GB/T 33240"],
        "context_map": {"GB/T 33240": ["GB/T", "术语"], "机器人术语": ["GB/T", "术语"]},
        "timeline_events": [
            {"ts": "2016", "event": "中国发布 GB/T 33240-2016", "source": "gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/66-ifr-2024",
        "type": "official_report",
        "title": "IFR World Robotics Report 2024",
        "confidence": 0.90,
        "domain": "ifr.org",
        "keywords": ["IFR", "世界机器人报告", "装机量", "IFR 2024"],
        "soft_aliases": ["IFR"],
        "context_map": {"IFR": ["IFR", "报告", "装机量"], "世界机器人报告": ["IFR", "报告"]},
        "timeline_events": [
            {"ts": "2024", "event": "IFR 发布 World Robotics Report 2024", "source": "ifr.org", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/67-ifr-2023",
        "type": "official_report",
        "title": "IFR World Robotics Report 2023",
        "confidence": 0.90,
        "domain": "ifr.org",
        "keywords": ["IFR 2023", "机器人密度", "IFR 2023"],
        "soft_aliases": ["IFR 2023"],
        "context_map": {"IFR 2023": ["IFR", "密度"], "机器人密度": ["IFR", "密度"]},
        "timeline_events": [
            {"ts": "2023", "event": "IFR 发布 World Robotics Report 2023", "source": "ifr.org", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/68-cea-2024",
        "type": "official_report",
        "title": "中国电子学会：中国机器人产业发展报告 2024",
        "confidence": 0.90,
        "domain": "cea.org.cn",
        "keywords": ["中国机器人", "产业发展", "人形机器人", "中国机器人产业报告"],
        "soft_aliases": ["中国机器人产业"],
        "context_map": {"中国机器人": ["中国电子学会", "产业"], "人形机器人": ["中国电子学会", "产业"]},
        "timeline_events": [
            {"ts": "2024", "event": "中国电子学会发布机器人产业发展报告 2024", "source": "cea.org.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/69-astm-f2992",
        "type": "official_standard",
        "title": "ASTM F2992-14 服务机器人性能测试",
        "confidence": 0.90,
        "domain": "astm.org",
        "keywords": ["ASTM F2992", "服务机器人", "测试", "ASTM F2992"],
        "soft_aliases": ["ASTM F2992"],
        "context_map": {"ASTM F2992": ["ASTM", "测试"], "服务机器人": ["ASTM", "测试"]},
        "timeline_events": [
            {"ts": "2014", "event": "ASTM 发布 F2992-14", "source": "astm.org", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "url": "https://temp.source-trace.local/70-iso-ts-15066",
        "type": "official_standard",
        "title": "ISO/TS 15066:2016 协作机器人安全技术规范",
        "confidence": 0.93,
        "domain": "iso.org",
        "keywords": ["ISO/TS 15066", "协作", "技术规范", "ISO/TS 15066"],
        "soft_aliases": ["ISO/TS 15066"],
        "context_map": {"ISO/TS 15066": ["ISO", "技术规范"], "协作": ["ISO", "技术规范"]},
        "timeline_events": [
            {"ts": "2016", "event": "ISO 发布 ISO/TS 15066:2016", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
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
