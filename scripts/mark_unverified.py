#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为剩余 unverified 信源写诚实的 url_note（说明为什么没核实到 / 库内可能的错误）。
不造假 URL，不删除数据 —— 只是让下游看到真实状态。
"""
import sqlite3

DB = "compliance.db"

# id -> 说明（这些保持 unverified，不编造 URL）
NOTES = {
    23: "ISO 9241-280 —— 编号未在 ISO 官网确认存在，疑为非标准编号；需人工核实（勿直接引用）",
    24: "GB/T 41870-2022 —— 国标号待核实；国标全文公开系统为 SPA，无法提供静态详情 URL",
    27: "IEEE P2864 —— P 开头为草案号；正式标准号与发布状态待核实，勿对外引用",
    30: "ISO 10218-1 新版 —— 实际已发布为 ISO 10218-1:2025，库内写的 2023 修订版有误；2025 版 URL 未取到",
    33: "ISO 9283 —— 实际为 ISO 9283:1998（1990 版已作废）；具体 standard ID 未取到",
    40: "GB/T 34131-2017 —— 国标号待核实；无静态详情 URL",
    41: "GB/T 33240-2016 —— 国标号待核实；无静态详情 URL",
    43: "IFR World Robotics 2023 —— 官方新闻稿地址未取到（2024 版已核实，#42）",
    44: "中国电子学会中国机器人产业发展报告 2024 —— 发布方官网未确认稳定 URL，多为PDF托管页",
    45: "ASTM F2992 —— 版本与标题待核实（compass.astm.org 需订阅，无公开静态页）",
    56: "上海AI实验室 AI for Science —— 机构成果页非单一标准/法规，缺稳定权威 URL",
}

conn = sqlite3.connect(DB)
c = conn.cursor()
for sid, note in NOTES.items():
    c.execute("UPDATE sources SET url_note=? WHERE id=?", (note, sid))

conn.commit()
conn.close()

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT url_status, COUNT(*) FROM sources GROUP BY url_status ORDER BY 2 DESC")
print("=== 最终 URL 状态 ===")
for st, n in c.fetchall():
    label = {
        "verified": "✅ 已核实（HTTP+内容双重校验）",
        "verified_withdrawn": "⚠️ 已核实但标准已作废/被取代",
        "unverified": "❌ 未核实（已标注原因，未造假URL）",
    }.get(st, st)
    print("  %-12s %2d 条  %s" % (st, n, label))
c.execute("SELECT COUNT(*) FROM sources")
print("\n总信源数：%d" % c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM sources WHERE url LIKE '%temp.source-trace.local%'")
print("仍为占位假URL：%d 条" % c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM sources WHERE url_status != 'unverified'")
print("可用于对外溯源的条目：%d" % c.fetchone()[0])
conn.close()
