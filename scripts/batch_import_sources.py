#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入信源到 compliance_db
支持多线程 URL 验证 + 批量 upsert
"""
import json
import os
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "compliance.db")
DB_PATH = os.path.normpath(DB_PATH)
MAX_WORKERS = 5

# 信源数据（从信源清单-Phase1.md 提取）
SOURCES = [
    # Compliance 层（18 条新数据）
    {
        "id": 2,
        "title": "生成式人工智能服务管理暂行办法",
        "type": "official_regulation",
        "url": "https://www.cac.gov.cn/2023-08/15/c_XXXX.htm",
        "date": "2023-08-15",
        "confidence": 0.92,
        "keywords": ["生成式AI", "AIGC", "生成式人工智能服务"],
        "soft_aliases": ["生成式AI", "AIGC"],
        "context_map": ["服务", "管理", "暂行办法"],
        "timeline": [
            {"ts": "2023-08-15", "event": "网信办等发布《生成式AI服务管理暂行办法》", "source": "cac.gov.cn", "tag": "initial_claim", "confidence": 0.92},
        ],
    },
    {
        "id": 3,
        "title": "互联网信息服务深度合成管理规定",
        "type": "official_regulation",
        "url": "https://www.cac.gov.cn/2023-01/10/c_XXXX.htm",
        "date": "2023-01-10",
        "confidence": 0.92,
        "keywords": ["深度合成", "deepfake", "AI换脸", "深度合成服务"],
        "soft_aliases": ["深度合成", "deepfake", "AI换脸"],
        "context_map": ["规定", "服务", "管理"],
        "timeline": [
            {"ts": "2023-01-10", "event": "网信办等发布《互联网信息服务深度合成管理规定》", "source": "cac.gov.cn", "tag": "initial_claim", "confidence": 0.92},
        ],
    },
    {
        "id": 4,
        "title": "科技伦理审查办法（试行）",
        "type": "official_regulation",
        "url": "https://www.most.gov.cn/...",
        "date": "2023-12-01",
        "confidence": 0.90,
        "keywords": ["科技伦理", "伦理审查", "AI伦理", "科技伦理审查"],
        "soft_aliases": ["科技伦理", "伦理审查"],
        "context_map": ["办法", "审查", "科技部"],
        "timeline": [
            {"ts": "2023-12-01", "event": "科技部等发布《科技伦理审查办法（试行）》", "source": "most.gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "id": 5,
        "title": "数据安全法",
        "type": "official_regulation",
        "url": "https://www.npc.gov.cn/...",
        "date": "2021-09-01",
        "confidence": 0.95,
        "keywords": ["数据安全", "数据出境", "数据分类分级", "数据安全法"],
        "soft_aliases": ["数据安全"],
        "context_map": ["法", "安全", "数据"],
        "timeline": [
            {"ts": "2021-09-01", "event": "全国人大通过《数据安全法》", "source": "npc.gov.cn", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "id": 6,
        "title": "个人信息保护法",
        "type": "official_regulation",
        "url": "https://www.npc.gov.cn/...",
        "date": "2021-11-01",
        "confidence": 0.95,
        "keywords": ["个人信息保护", "隐私", "PIPL", "个人信息保护法"],
        "soft_aliases": ["个人信息保护", "隐私"],
        "context_map": ["法", "保护", "个人信息"],
        "timeline": [
            {"ts": "2021-11-01", "event": "全国人大通过《个人信息保护法》", "source": "npc.gov.cn", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "id": 7,
        "title": "网络安全法",
        "type": "official_regulation",
        "url": "https://www.npc.gov.cn/...",
        "date": "2017-06-01",
        "confidence": 0.95,
        "keywords": ["网络安全", "关键信息基础设施", "网络安全法"],
        "soft_aliases": ["网络安全"],
        "context_map": ["法", "安全", "网络"],
        "timeline": [
            {"ts": "2017-06-01", "event": "全国人大通过《网络安全法》", "source": "npc.gov.cn", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "id": 12,
        "title": "EU AI Liability Directive",
        "type": "official_regulation",
        "url": "https://eur-lex.europa.eu/...",
        "date": "2024",
        "confidence": 0.90,
        "keywords": ["AI责任", "AI赔偿", "产品责任", "AI Liability Directive"],
        "soft_aliases": ["AI责任", "AI赔偿"],
        "context_map": ["指令", "责任", "赔偿"],
        "timeline": [
            {"ts": "2024", "event": "EU 发布 AI Liability Directive", "source": "eur-lex.europa.eu", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "id": 14,
        "title": "NIST AI 600-1",
        "type": "official_guideline",
        "url": "https://nist.gov/...",
        "date": "2024",
        "confidence": 0.90,
        "keywords": ["NIST AI 600-1", "生成式AI风险管理", "GPAI"],
        "soft_aliases": ["生成式AI风险管理"],
        "context_map": ["NIST", "生成式", "风险管理"],
        "timeline": [
            {"ts": "2024", "event": "NIST 发布 AI 600-1（生成式AI风险管理）", "source": "nist.gov", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "id": 15,
        "title": "NIST AI 700-1",
        "type": "official_guideline",
        "url": "https://nist.gov/...",
        "date": "2024",
        "confidence": 0.90,
        "keywords": ["NIST AI 700-1", "AI安全测试", "AI评估", "red teaming"],
        "soft_aliases": ["AI安全测试"],
        "context_map": ["NIST", "安全", "测试"],
        "timeline": [
            {"ts": "2024", "event": "NIST 发布 AI 700-1（AI安全测试）", "source": "nist.gov", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "id": 16,
        "title": "OECD AI 原则",
        "type": "official_guideline",
        "url": "https://oecd.org/...",
        "date": "2019-05-22",
        "confidence": 0.92,
        "keywords": ["OECD AI", "AI原则", "可信AI", "OECD AI 原则"],
        "soft_aliases": ["OECD AI", "可信AI"],
        "context_map": ["OECD", "原则", "可信"],
        "timeline": [
            {"ts": "2019-05-22", "event": "OECD 发布 AI 原则", "source": "oecd.org", "tag": "initial_claim", "confidence": 0.92},
        ],
    },
    {
        "id": 17,
        "title": "UNESCO AI 伦理建议书",
        "type": "official_guideline",
        "url": "https://unesco.org/...",
        "date": "2021-11-30",
        "confidence": 0.92,
        "keywords": ["UNESCO AI伦理", "AI伦理", "伦理框架", "UNESCO"],
        "soft_aliases": ["UNESCO AI伦理", "AI伦理"],
        "context_map": ["UNESCO", "伦理", "建议书"],
        "timeline": [
            {"ts": "2021-11-30", "event": "UNESCO 通过 AI 伦理建议书", "source": "unesco.org", "tag": "initial_claim", "confidence": 0.92},
        ],
    },
    {
        "id": 18,
        "title": "ISO 9241-210 人因工程设计",
        "type": "official_standard",
        "url": "https://www.iso.org/...",
        "date": "2019",
        "confidence": 0.93,
        "keywords": ["ISO 9241-210", "以人为中心设计", "HCD", "UCD"],
        "soft_aliases": ["以人为中心设计", "HCD", "UCD"],
        "context_map": ["ISO", "设计", "人因"],
        "timeline": [
            {"ts": "2019", "event": "ISO 发布 9241-210:2019", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "id": 19,
        "title": "ISO 9241-211 设计规范",
        "type": "official_standard",
        "url": "https://www.iso.org/...",
        "date": "2019",
        "confidence": 0.93,
        "keywords": ["ISO 9241-211", "HCD设计规范", "可用性工程"],
        "soft_aliases": ["HCD设计规范"],
        "context_map": ["ISO", "设计规范"],
        "timeline": [
            {"ts": "2019", "event": "ISO 发布 9241-211:2019", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "id": 20,
        "title": "ISO 9241-220 用户体验度量",
        "type": "official_standard",
        "url": "https://www.iso.org/...",
        "date": "2019",
        "confidence": 0.93,
        "keywords": ["ISO 9241-220", "UX度量", "用户体验", "可用性度量"],
        "soft_aliases": ["UX度量", "用户体验"],
        "context_map": ["ISO", "度量", "用户体验"],
        "timeline": [
            {"ts": "2019", "event": "ISO 发布 9241-220:2019", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "id": 21,
        "title": "ISO 9241-230 语音交互",
        "type": "official_standard",
        "url": "https://www.iso.org/...",
        "date": "2018",
        "confidence": 0.93,
        "keywords": ["ISO 9241-230", "语音交互", "VUI", "语音界面"],
        "soft_aliases": ["语音交互", "VUI"],
        "context_map": ["ISO", "语音", "交互"],
        "timeline": [
            {"ts": "2018", "event": "ISO 发布 9241-230:2018", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "id": 22,
        "title": "ISO 9241-240 人因工效学",
        "type": "official_standard",
        "url": "https://www.iso.org/...",
        "date": "2022",
        "confidence": 0.93,
        "keywords": ["ISO 9241-240", "人因工效学", "工效学设计"],
        "soft_aliases": ["人因工效学"],
        "context_map": ["ISO", "工效学"],
        "timeline": [
            {"ts": "2022", "event": "ISO 发布 9241-240:2022", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "id": 23,
        "title": "ISO 9241-280 无障碍设计",
        "type": "official_standard",
        "url": "https://www.iso.org/...",
        "date": "2020",
        "confidence": 0.93,
        "keywords": ["ISO 9241-280", "无障碍", "可访问性", "WCAG"],
        "soft_aliases": ["无障碍", "可访问性"],
        "context_map": ["ISO", "无障碍"],
        "timeline": [
            {"ts": "2020", "event": "ISO 发布 9241-280:2020", "source": "iso.org", "tag": "initial_claim", "confidence": 0.93},
        ],
    },
    {
        "id": 24,
        "title": "GB/T 41870-2022 社交机器人",
        "type": "official_standard",
        "url": "https://www.gov.cn/...",
        "date": "2022",
        "confidence": 0.90,
        "keywords": ["GB/T 41870", "社交机器人", "chatbot", "对话系统"],
        "soft_aliases": ["社交机器人", "chatbot"],
        "context_map": ["GB/T", "机器人", "社交"],
        "timeline": [
            {"ts": "2022", "event": "中国发布 GB/T 41870-2022《社交机器人》", "source": "gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
    {
        "id": 25,
        "title": "GB/T 36430-2018 服务机器人性能",
        "type": "official_standard",
        "url": "https://www.gov.cn/...",
        "date": "2018",
        "confidence": 0.90,
        "keywords": ["GB/T 36430", "服务机器人", "性能测试", "机器人评价"],
        "soft_aliases": ["服务机器人"],
        "context_map": ["GB/T", "服务机器人"],
        "timeline": [
            {"ts": "2018", "event": "中国发布 GB/T 36430-2018《服务机器人性能》", "source": "gov.cn", "tag": "initial_claim", "confidence": 0.90},
        ],
    },
]


def verify_url(url: str, timeout: int = 10) -> dict:
    """验证 URL 是否可访问，返回 {url, ok, status_code, title}"""
    try:
        import urllib.request
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=timeout)
        return {"url": url, "ok": True, "status_code": resp.status}
    except Exception as e:
        return {"url": url, "ok": False, "error": str(e)}


def _normalize_url(entry: dict) -> str:
    """如果 URL 是占位符，生成临时唯一 URL；否则返回原 URL。"""
    url = entry.get("url", "")
    if not url or url.endswith("...") or "XXXX" in url:
        # 生成基于 title 的临时 URL
        slug = re.sub(r"[^a-z0-9]+", "-", entry["title"].lower())
        slug = slug.strip("-")[:60]
        return f"https://temp.source-trace.local/{entry['id']}-{slug}"
    return url


def upsert_source(conn, entry: dict) -> int:
    """导入单条信源（用 title+type+confidence 做唯一性判断；占位 URL 自动生成临时唯一 URL）"""
    url = _normalize_url(entry)
    domain = re.search(r"https?://([^/]+)/?", url)
    domain = domain.group(1).lower() if domain else ""

    # 用 title + type + confidence 组合判断是否已存在
    cur = conn.execute(
        "SELECT id, url FROM sources WHERE title = ? AND type = ? AND confidence = ?",
        (entry["title"], entry["type"], entry["confidence"]),
    )
    row = cur.fetchone()
    if row:
        source_id = row[0]
        conn.execute("UPDATE sources SET url=?, domain=? WHERE id=?",
                     (url, domain, source_id))
        conn.execute("DELETE FROM timeline WHERE source_id=?", (source_id,))
        conn.execute("DELETE FROM keywords WHERE source_id=?", (source_id,))
        conn.execute("DELETE FROM source_context WHERE source_id=?", (source_id,))
    else:
        cur = conn.execute(
            "INSERT INTO sources(url, type, title, confidence, domain) VALUES (?,?,?,?,?)",
            (url, entry["type"], entry["title"], entry["confidence"], domain),
        )
        source_id = cur.lastrowid

    # timeline
    for ev in entry.get("timeline", []):
        conn.execute(
            "INSERT INTO timeline(source_id, ts, event, source, tag, confidence) VALUES (?,?,?,?,?,?)",
            (source_id, ev.get("ts", "—"), ev.get("event", ""), ev.get("source", ""),
             ev.get("tag", "initial_claim"), ev.get("confidence", 0.9)),
        )

    # keywords
    seen = set()
    for kw in entry.get("keywords", []):
        if kw not in seen:
            seen.add(kw)
            conn.execute("INSERT INTO keywords(source_id, keyword, is_soft_alias) VALUES (?,?,0)",
                         (source_id, kw))
    for kw in entry.get("soft_aliases", []):
        if kw not in seen:
            seen.add(kw)
            conn.execute("INSERT INTO keywords(source_id, keyword, is_soft_alias) VALUES (?,?,1)",
                         (source_id, kw))

    # context_map
    for w in entry.get("context_map", []):
        conn.execute("INSERT OR IGNORE INTO source_context(source_id, word) VALUES (?,?)",
                     (source_id, w))

    conn.commit()
    return source_id


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 1. 并行验证 URL
    print("=== 验证 URL ===")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(verify_url, s["url"]): s for s in SOURCES}
        for future in as_completed(futures):
            entry = futures[future]
            result = future.result()
            status = "✅" if result["ok"] else "❌"
            print(f"{status} [{entry['id']:2d}] {entry['title'][:30]:<30} {result['url'][:50]}")
            if not result["ok"]:
                print(f"    错误: {result.get('error', 'unknown')}")

    # 2. 批量导入
    print("\n=== 导入数据库 ===")
    count = 0
    for entry in SOURCES:
        try:
            source_id = upsert_source(conn, entry)
            print(f"✅ [{entry['id']:2d}] {entry['title'][:30]:<30} -> id={source_id}")
            count += 1
        except Exception as e:
            print(f"❌ [{entry['id']:2d}] {entry['title'][:30]:<30} 错误: {e}")

    conn.close()
    print(f"\n完成：导入 {count}/{len(SOURCES)} 条")


if __name__ == "__main__":
    main()
