"""
溯源 API — 合规资料数据库（SQLite + FTS5）
存储法规/标准/通知的一手源、时间线、关键词、上下文词。
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compliance.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(force: bool = False) -> None:
    """初始化表结构。force=True 时重建。"""
    conn = get_conn()
    try:
        if force:
            # 子表先删，避免 FOREIGN KEY 约束失败
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("DROP TABLE IF EXISTS fts_sources")
            conn.execute("DROP TABLE IF EXISTS timeline")
            conn.execute("DROP TABLE IF EXISTS keywords")
            conn.execute("DROP TABLE IF EXISTS source_context")
            conn.execute("DROP TABLE IF EXISTS sources")
            conn.execute("PRAGMA foreign_keys=ON")

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,           -- official_regulation / official_guideline / official_notice / official_standard
                title TEXT NOT NULL,
                confidence REAL DEFAULT 0.9,
                domain TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES sources(id),
                ts TEXT NOT NULL,              -- ISO 日期，如 2026-07-15
                event TEXT NOT NULL,
                source TEXT NOT NULL,          -- 短来源标识，如 cac.gov.cn
                tag TEXT DEFAULT 'initial_claim',  -- initial_claim / official_response / enforcement
                confidence REAL DEFAULT 0.9
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL REFERENCES sources(id),
                keyword TEXT NOT NULL,
                is_soft_alias INTEGER DEFAULT 0  -- 1=需要上下文词才触发，0=直接命中
            );

            -- 上下文词：某条资料整体需要的查询上下文词（不是绑定到某个关键词）
            CREATE TABLE IF NOT EXISTS source_context (
                source_id INTEGER NOT NULL REFERENCES sources(id),
                word TEXT NOT NULL,
                PRIMARY KEY (source_id, word)
            );
        """)

        # FTS5 虚拟表：用于全文检索标题 + 关键词
        conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_sources USING fts5(
                title,
                content='sources',
                content_rowid='id',
                tokenize='unicode61'
            );
            CREATE TRIGGER IF NOT EXISTS sources_ai AFTER INSERT ON sources BEGIN
                INSERT INTO fts_sources(rowid, title) VALUES (new.id, new.title);
            END;
            CREATE TRIGGER IF NOT EXISTS sources_ad AFTER DELETE ON sources BEGIN
                INSERT INTO fts_sources(fts_sources, rowid, title) VALUES ('delete', old.id, old.title);
            END;
        """)

        conn.commit()
    finally:
        conn.close()


def upsert_source(
    url: str,
    type: str,
    title: str,
    confidence: float = 0.9,
    domain: Optional[str] = None,
    timeline_events: Optional[list] = None,
    keywords: Optional[list] = None,
    soft_aliases: Optional[list] = None,
    context_map: Optional[dict] = None,
) -> int:
    """
    插入或更新一条合规资料。
    keywords: 硬关键词列表（直接命中）
    soft_aliases: 软别名列表（需要上下文词才触发）
    context_map: {软别名: [上下文词]} 或 全局上下文词列表
    timeline_events: [{"ts": "...", "event": "...", "source": "...", "tag": "...", "confidence": ...}]
    返回 source_id。
    """
    if domain is None:
        m = url.lower().split("//")[-1].split("/")[0]
        domain = m

    conn = get_conn()
    source_id = None
    try:
        cur = conn.execute(
            "SELECT id FROM sources WHERE url = ?", (url,)
        )
        row = cur.fetchone()
        if row:
            source_id = row["id"]
            conn.execute(
                "UPDATE sources SET type=?, title=?, confidence=?, domain=? WHERE id=?",
                (type, title, confidence, domain, source_id),
            )
            # 清旧关联
            conn.execute("DELETE FROM timeline WHERE source_id=?", (source_id,))
            conn.execute("DELETE FROM keywords WHERE source_id=?", (source_id,))
        else:
            cur = conn.execute(
                "INSERT INTO sources(url, type, title, confidence, domain) VALUES (?,?,?,?,?)",
                (url, type, title, confidence, domain),
            )
            source_id = cur.lastrowid

        # timeline
        if timeline_events:
            for ev in timeline_events:
                conn.execute(
                    """INSERT INTO timeline(source_id, ts, event, source, tag, confidence)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        source_id,
                        ev.get("ts", "—"),
                        ev.get("event", ""),
                        ev.get("source", ""),
                        ev.get("tag", "initial_claim"),
                        ev.get("confidence", 0.9),
                    ),
                )

        # keywords
        hard_keywords = keywords or []
        soft_aliases = soft_aliases or []

        seen = set()
        for kw in hard_keywords:
            if kw not in seen:
                seen.add(kw)
                conn.execute(
                    "INSERT INTO keywords(source_id, keyword, is_soft_alias) VALUES (?,?,0)",
                    (source_id, kw),
                )
        for kw in soft_aliases:
            if kw not in seen:
                seen.add(kw)
                conn.execute(
                    "INSERT INTO keywords(source_id, keyword, is_soft_alias) VALUES (?,?,1)",
                    (source_id, kw),
                )

        # 上下文词：全局上下文词（如 办法/法规/监管）绑定到 source
        if context_map:
            # 现在只认 {软别名: [上下文词]} 或 list 两种形态
            if isinstance(context_map, dict):
                ctx_words = []
                for alias, ctxs in context_map.items():
                    if isinstance(ctxs, list):
                        ctx_words.extend(ctxs)
                # 去重写入 source_context
                for w in set(ctx_words):
                    conn.execute(
                        "INSERT OR IGNORE INTO source_context(source_id, word) VALUES (?,?)",
                        (source_id, w),
                    )
            elif isinstance(context_map, list):
                for w in context_map:
                    conn.execute(
                        "INSERT OR IGNORE INTO source_context(source_id, word) VALUES (?,?)",
                        (source_id, w),
                    )

        conn.commit()
        return source_id
    finally:
        conn.close()


def search_by_keyword(query: str, limit: int = 10) -> list:
    """按关键词搜索合规资料。返回最匹配的 source 及其 timeline、keywords。"""
    conn = get_conn()
    q = query.lower()
    results = []

    try:
        # 1) 先在 keywords 表精确/包含匹配
        # 用 instr(?，keyword) 检查 query 是否包含 keyword，支持中文子串匹配
        cur = conn.execute("""
            SELECT DISTINCT s.*, 
                   GROUP_CONCAT(DISTINCT k.keyword) as matched_keywords,
                   SUM(CASE WHEN k.is_soft_alias=1 THEN 1 ELSE 0 END) as soft_hits
            FROM sources s
            JOIN keywords k ON k.source_id = s.id
            WHERE instr(?, lower(k.keyword)) > 0
            GROUP BY s.id
            ORDER BY soft_hits ASC, s.confidence DESC
            LIMIT ?
        """, (q, limit))
        rows = cur.fetchall()

        for row in rows:
            matched_kws = [k.strip() for k in (row["matched_keywords"] or "").split(",") if k.strip()]

            # 2) 区分硬关键词和软别名
            cur_kw = conn.execute(
                "SELECT keyword, is_soft_alias FROM keywords WHERE source_id=?",
                (row["id"],),
            )
            kw_rows = {r["keyword"]: r["is_soft_alias"] for r in cur_kw.fetchall()}

            hard_matched = [kw for kw in matched_kws if kw_rows.get(kw, 1) == 0]
            soft_matched = [kw for kw in matched_kws if kw_rows.get(kw, 0) == 1]

            # 3) 软别名需要上下文词验证（避免误命中）
            #    例外：如果查询文本本身已经精确包含某个软别名关键词（忽略大小写），说明用户明确意图，跳过上下文检查
            if soft_matched and not hard_matched:
                # 检查是否有软别名被查询文本精确命中（忽略大小写）
                explicit_soft_hit = any(
                    kw.lower() in q for kw in soft_matched
                )
                if not explicit_soft_hit:
                    cur_ctx = conn.execute(
                        "SELECT word FROM source_context WHERE source_id=?",
                        (row["id"],),
                    )
                    ctx_words = [r["word"].lower() for r in cur_ctx.fetchall()]
                    if not any(ctx in q for ctx in ctx_words):
                        continue  # 软别名命中但无上下文词，跳过（避免误命中）

            # 4) 获取 timeline
            cur3 = conn.execute(
                "SELECT ts, event, source, tag, confidence FROM timeline WHERE source_id=? ORDER BY ts",
                (row["id"],),
            )
            timeline = [dict(r) for r in cur3.fetchall()]

            results.append({
                "source": {
                    "url": row["url"],
                    "type": row["type"],
                    "title": row["title"],
                    "confidence": row["confidence"],
                },
                "matched_keywords": matched_kws,
                "timeline": timeline,
            })

        return results
    finally:
        conn.close()


def get_source_by_url(url: str) -> Optional[dict]:
    conn = get_conn()
    try:
        cur = conn.execute("SELECT * FROM sources WHERE url = ?", (url,))
        row = cur.fetchone()
        if not row:
            return None
        source = dict(row)
        cur2 = conn.execute(
            "SELECT ts, event, source, tag, confidence FROM timeline WHERE source_id=? ORDER BY ts",
            (source["id"],),
        )
        source["timeline"] = [dict(r) for r in cur2.fetchall()]
        return source
    finally:
        conn.close()


def import_kb_entry(entry: dict) -> int:
    """从 _KB 格式的 dict 导入一条合规资料。返回 source_id。"""
    return upsert_source(
        url=entry["primary_source"]["url"],
        type=entry["primary_source"]["type"],
        title=entry["primary_source"]["title"],
        confidence=entry["primary_source"].get("confidence", 0.9),
        timeline_events=entry.get("timeline"),
        keywords=entry.get("kw", []),
        soft_aliases=entry.get("soft_aliases"),
        context_map=entry.get("context_map"),
    )


def seed_from_kb() -> None:
    """从 trace_engine._KB 导入初始数据（如果数据库为空）。"""
    from trace_engine import _KB
    conn = get_conn()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM sources")
        if cur.fetchone()[0] > 0:
            return  # 已有数据，不重复导入
    finally:
        conn.close()

    for entry in _KB:
        # 适配 _KB 格式
        kw = entry.get("kw", [])
        req_context = entry.get("req_context", [])

        # 硬关键词：精确法规名、较长且不包含通用上下文的词
        hard_keywords = []
        soft_aliases = []
        for k in kw:
            # heuristic：如果词本身已经包含上下文词（如 "AI伴侣法规"），算软别名
            # 如果词是精确法规名（长度>6 且不含通用上下文词），算硬关键词
            if any(ctx in k for ctx in req_context) or len(k) <= 6:
                soft_aliases.append(k)
            else:
                hard_keywords.append(k)

        upsert_source(
            url=entry["primary_source"]["url"],
            type=entry["primary_source"]["type"],
            title=entry["primary_source"]["title"],
            confidence=entry["primary_source"].get("confidence", 0.9),
            timeline_events=entry.get("timeline"),
            keywords=hard_keywords,
            soft_aliases=soft_aliases,
            context_map=req_context if req_context else None,
        )


if __name__ == "__main__":
    init_db(force=False)
    seed_from_kb()
    print("done")
