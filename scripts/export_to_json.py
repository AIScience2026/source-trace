#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出 compliance.db 为前端可用的 JSON"""
import sqlite3
import json
from datetime import datetime

DB_PATH = "compliance.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sources = []
cur = conn.execute("SELECT * FROM sources ORDER BY id")
for row in cur.fetchall():
    sid = row["id"]
    
    # timeline
    timeline = []
    cur_t = conn.execute("SELECT * FROM timeline WHERE source_id=? ORDER BY ts", (sid,))
    for t in cur_t.fetchall():
        timeline.append({"ts": t["ts"], "event": t["event"], "source": t["source"], "tag": t["tag"], "confidence": t["confidence"]})
    
    # keywords
    keywords = []
    soft_aliases = []
    cur_k = conn.execute("SELECT keyword, is_soft_alias FROM keywords WHERE source_id=? ORDER BY is_soft_alias, keyword", (sid,))
    for k in cur_k.fetchall():
        if k["is_soft_alias"]:
            soft_aliases.append(k["keyword"])
        else:
            keywords.append(k["keyword"])
    
    # context
    context = []
    cur_c = conn.execute("SELECT word FROM source_context WHERE source_id=? ORDER BY word", (sid,))
    for c in cur_c.fetchall():
        context.append(c["word"])
    
    sources.append({
        "id": sid,
        "url": row["url"],
        "type": row["type"],
        "title": row["title"],
        "confidence": row["confidence"],
        "domain": row["domain"],
        "timeline": timeline,
        "keywords": keywords,
        "soft_aliases": soft_aliases,
        "context": context,
    })

conn.close()

output = {
    "exported_at": datetime.now().isoformat(),
    "total": len(sources),
    "sources": sources,
}

with open("web/sources.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"导出完成：{len(sources)} 条 -> web/sources.json")
