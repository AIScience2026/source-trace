#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M2 准确率评测脚本（溯源 API 原型 v4）

目的：用「合规雷达 / 国内厂商动作」里的真实条目（人工标真一手源）验证原型溯源引擎。
指标（口径对齐 PRD §13）：
  - 有源子集命中率 = 期望命中且域名正确的 case / 有可验证一手源的子集
  - 无源子集诚实降级率 = 期望降级且确实返回 null 的 case / 无明确一手源的子集
  - 可溯源率(不编造率) = (命中 + 诚实降级) / 全部 case
说明：当前为 mock 启发式引擎，能力上限 = KB 覆盖率；真实世界准确率需接 LLM/检索后复测，
      本脚本同时输出 KB 对「合规雷达 V2 T1 一手源」的覆盖率，定位下一步扩展缺口。
"""
import json
import re
import datetime

from config import Config
from trace_engine import run_trace, _KB

Config.LLM_PROVIDER = "mock"  # 评测原型，不触真实 LLM

# ── 测试集：query → 期望权威域名（None 表示应诚实降级，不编造）──
# 正例来自合规雷达 V2 / 国内厂商动作中可标真的 T1 一手源；无源例为真实不存在官方一手源的说法。
TESTCASES = [
    # 正例（有可验证一手源，扩 KB 后应命中）
    ("中国人工智能拟人化互动服务管理暂行办法", "claim", "cac.gov.cn"),
    ("AI伴侣机器人合规要求", "claim", "cac.gov.cn"),
    ("欧盟AI法案 Art.50 透明度义务可执法", "claim", "eur-lex.europa.eu"),
    ("EU AI Act", "claim", "eur-lex.europa.eu"),
    ("Digital Omnibus 2026/1744 高风险义务推迟", "claim", "eur-lex.europa.eu"),
    ("ISO 9241-222 以人为中心设计标准发布", "claim", "iso.org"),
    ("清朗整治AI应用乱象第二阶段通报", "claim", "cac.gov.cn"),
    ("AI生成合成内容标识办法施行", "claim", "cac.gov.cn"),
    ("NIST AI 风险管理框架", "claim", "doi.org"),  # KB 一手源为 DOI(10.6028/NIST.AI.100-1)，解析至 NIST
    # 无源（应诚实降级，验证不编造）
    ("某AI伴侣App 2026年8月融资新闻", "claim", None),
    ("AI伴侣行业市场规模预测 2030", "claim", None),
    ("Character.AI 诉讼案最新进展", "claim", None),
]

# 合规雷达 V2 中提到的 T1 官方一手源（人工提取），用于 KB 覆盖缺口分析
V2_T1_SOURCES = [
    "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",                 # EU AI Act
    "https://eur-lex.europa.eu/eli/reg/2026/1744/oj",                 # Digital Omnibus
    "https://www.iso.org/ru/standard/88373.html",                     # ISO 9241-222
    "https://www.cac.gov.cn/2026-09/02/c_1790099041364574.htm",       # 清朗二阶段
    "https://www.cac.gov.cn/2026-04/10/c_1777558395284407.htm",       # 拟人化互动办法
    "https://www.cac.gov.cn/2025-03/xx/c_标识办法原文.htm",          # 标识办法（路径待核实）
]


def domain_of(url):
    if not url:
        return None
    m = re.search(r"https?://(?:www\.)?([^/]+)/?", url)
    return m.group(1).lower() if m else None


def run_eval():
    rows = []
    hits = miss = wrong = 0
    honest = fabric = 0
    for q, itype, exp_dom in TESTCASES:
        r = run_trace(q, itype, "compliance", "standard")
        ps = r.get("primary_source")
        got_dom = domain_of(ps["url"]) if ps else None
        if exp_dom is not None:
            if ps is None:
                status = "MISS(漏检)"; miss += 1
            elif got_dom == exp_dom:
                status = "HIT(命中)"; hits += 1
            else:
                status = f"WRONG(错源->{got_dom})"; wrong += 1
        else:
            if ps is None:
                status = "HONEST(诚实降级)"; honest += 1
            else:
                status = f"FABRICATED(编造->{got_dom})"; fabric += 1
        rows.append({
            "query": q, "expected_domain": exp_dom, "got_domain": got_dom,
            "got_title": ps["title"] if ps else None,
            "conf": r.get("overall_confidence"), "status": status,
        })

    positive = hits + miss + wrong
    negative = honest + fabric
    total = positive + negative

    # KB 对合规雷达 V2 T1 源的覆盖率（域名级）
    kb_domains = {domain_of(e["primary_source"]["url"]) for e in _KB}
    cov = []
    for s in V2_T1_SOURCES:
        d = domain_of(s)
        cov.append({"source": s, "domain": d, "in_kb": d in kb_domains})

    report = {
        "date": datetime.date.today().isoformat(),
        "engine": "mock heuristic (KB-driven)",
        "positive_hit_rate": round(hits / positive, 4) if positive else 0,
        "honest_degrade_rate": round(honest / negative, 4) if negative else 0,
        "traceability_rate": round((hits + honest) / total, 4) if total else 0,
        "counts": {"hits": hits, "miss": miss, "wrong": wrong,
                   "honest": honest, "fabricated": fabric, "total": total},
        "kb_t1_coverage": cov,
        "cases": rows,
    }
    return report


if __name__ == "__main__":
    rep = run_eval()
    out = "m2_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    c = rep["counts"]
    print("=" * 64)
    print(f"M2 准确率评测  |  {rep['date']}  |  引擎: {rep['engine']}")
    print("=" * 64)
    for row in rep["cases"]:
        tag = row["status"].split("(")[0]
        print(f"[{tag:>7}] {row['query']}")
        print(f"         期望={row['expected_domain']}  实得={row['got_domain']}  "
              f"置信={row['conf']}  {row['got_title'] or ''}")
    print("-" * 64)
    print(f"有源子集命中率   : {rep['positive_hit_rate']*100:.1f}%  "
          f"({c['hits']}/{c['hits']+c['miss']+c['wrong']})")
    print(f"无源子集诚实降级 : {rep['honest_degrade_rate']*100:.1f}%  "
          f"({c['honest']}/{c['honest']+c['fabricated']})")
    print(f"可溯源率(不编造) : {rep['traceability_rate']*100:.1f}%  ({c['hits']+c['honest']}/{c['total']})")
    print("-" * 64)
    if c["fabricated"]:
        print(f"[⚠] {c['fabricated']} 条 FABRICATED = mock 引擎无语义消歧：含'AI伴侣'等宽泛别名的")
        print(f"    非法规查询被误命中。属原型已知局限，真实 LLM 档（调用方/托管 LLM 语义判断）解决；")
        print(f"    不计'恶意编造'，但计入可溯源率扣分项，需在接 LLM 后复测消除。")
    print("-" * 64)
    print("KB 对合规雷达 V2 T1 一手源覆盖率:")
    for item in rep["kb_t1_coverage"]:
        print(f"  [{'✓' if item['in_kb'] else '✗'}] {item['domain']}  <- {item['source'][:55]}")
    print("=" * 64)
    print(f"报告已落盘: {out}")
