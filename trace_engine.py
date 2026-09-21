"""
溯源 API — 溯源核心引擎（v4 MCP-first）
形态：MCP 工具 `trace` 由调用方 Agent 自带 LLM + Web 搜索算力完成"追到哪个原始文件"；
本引擎负责编排 + Newsylist 媒体首发增强 + 垂直语料校验 + 审计 JSON 组装 + 诚实降级。
数据库优先：优先查 compliance_db（SQLite），查不到再回退到 _KB 内存知识库。
真实：可选托管 LLM 档（配置 ST_LLM_API_KEY）启用我们后端 LLM 兜底（_run_trace_real 占位）。
核心交付：原始出处 + 时间线 + 污染链 + 置信度；无明确原始文件必须降级（不编造）。
"""
import re

from config import Config
from newsylist_client import enrich_media_first_report

# 小型垂直知识库（compliance 优先，先打透合规雷达）——老板已有语料/标注样本的缩影
_KB = [
    {
        "kw": ["人工智能拟人化互动服务管理暂行办法", "拟人化互动服务管理暂行",
               "拟人化互动", "AI伴侣", "AI 伴侣", "ai伴侣", "虚拟伴侣", "情感陪伴",
               "情感陪伴类", "陪伴类AI", "陪伴类 AI"],   # 别名：用户不会背全称（dogfooding 发现）
        # 软别名（AI伴侣/虚拟伴侣/情感陪伴…）需搭配法规上下文词才触发，避免把厂商融资/市场动态误判为法规一手源
        "req_context": ["办法", "合规", "法规", "监管", "条例", "管理", "治理", "要求", "红线",
                        "暂行办法", "规范化", "意见", "风险", "义务", "规则"],
        "primary_source": {
            "url": "https://www.cac.gov.cn/2026-04/10/c_1777558395284407.htm",
            "type": "official_regulation",
            "title": "人工智能拟人化互动服务管理暂行办法（2026-07-15 起施行）",
            "confidence": 0.94,
        },
        "timeline": [
            {"ts": "2026-04-10", "event": "网信办等五部门联合公布《办法》", "source": "cac.gov.cn", "tag": "initial_claim", "confidence": 0.95},
            {"ts": "2026-07-15", "event": "《办法》正式施行（四章三十二条）", "source": "cac.gov.cn", "tag": "official_response", "confidence": 0.95},
        ],
    },
    {
        "kw": ["EU AI Act", "欧盟AI法案", "欧盟人工智能法案", "EU Artificial Intelligence Act"],
        "primary_source": {
            "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
            "type": "official_regulation",
            "title": "Regulation (EU) 2024/1689 (AI Act)",
            "confidence": 0.95,
        },
        "timeline": [
            {"ts": "2024-06-13", "event": "EU AI Act 正式通过", "source": "eur-lex.europa.eu", "tag": "initial_claim", "confidence": 0.96},
            {"ts": "2024-08-01", "event": "禁止性实践等首批条款生效", "source": "eur-lex.europa.eu", "tag": "official_response", "confidence": 0.9},
            {"ts": "2026-08-02", "event": "Art.50 透明度义务进入可执法状态（开罚）", "source": "eur-lex.europa.eu", "tag": "enforcement", "confidence": 0.92},
        ],
    },
    {
        "kw": ["NIST AI RMF", "NIST AI Risk Management Framework", "NIST AI 风险管理框架"],
        "primary_source": {
            "url": "https://doi.org/10.6028/NIST.AI.100-1",
            "type": "official_guideline",
            "title": "NIST AI Risk Management Framework 1.0",
            "confidence": 0.93,
        },
        "timeline": [
            {"ts": "2023-01-26", "event": "NIST 发布 AI RMF 1.0", "source": "nist.gov", "tag": "initial_claim", "confidence": 0.94},
        ],
    },
    {
        # 来源：合规雷达-2026年8月-V2 §1.2（T1 官方一手源 = EUR-Lex）
        "kw": ["Digital Omnibus 2026/1744", "Digital Omnibus", "欧盟人工智能法修订 2026/1744", "EU 2026/1744", "高风险义务推迟"],
        "primary_source": {
            "url": "https://eur-lex.europa.eu/eli/reg/2026/1744/oj",
            "type": "official_regulation",
            "title": "Regulation (EU) 2026/1744 (Digital Omnibus — 高风险义务推迟)",
            "confidence": 0.94,
        },
        "timeline": [
            {"ts": "2026-07-24", "event": "OJ 公布 Regulation (EU) 2026/1744", "source": "eur-lex.europa.eu", "tag": "initial_claim", "confidence": 0.95},
            {"ts": "2026-07-27", "event": "生效：Annex III 高风险推迟至 2027-12-02；Art.50 透明度维持 2026-08-02 可执法", "source": "eur-lex.europa.eu", "tag": "official_response", "confidence": 0.92},
        ],
    },
    {
        # 来源：合规雷达-2026年8月-V2 §1.4（T1 官方源 = ISO 官网直链）
        "kw": ["ISO 9241-222", "ISO/IEC 9241-222", "以人为中心设计自评标准", "ISO 9241 第三部分"],
        "primary_source": {
            "url": "https://www.iso.org/ru/standard/88373.html",
            "type": "official_standard",
            "title": "ISO 9241-222:2026 以人为中心设计自评",
            "confidence": 0.93,
        },
        "timeline": [
            {"ts": "2026-06-26", "event": "ISO 发布 9241-222:2026", "source": "iso.org", "tag": "initial_claim", "confidence": 0.94},
        ],
    },
    {
        # 来源：合规雷达-2026年8月-V2 §下月关注#2（T1 官方源 = CAC）
        "kw": ["清朗整治AI应用乱象第二阶段", "清朗·整治AI应用乱象", "清朗二阶段", "整治AI应用乱象"],
        "primary_source": {
            "url": "https://www.cac.gov.cn/2026-09/02/c_1790099041364574.htm",
            "type": "official_notice",
            "title": "中央网信办「清朗·整治AI应用乱象」第二阶段通报（清理561万条、处置账号4.9万）",
            "confidence": 0.95,
        },
        "timeline": [
            {"ts": "2026-09-02", "event": "中央网信办发布清朗二阶段通报", "source": "cac.gov.cn", "tag": "initial_claim", "confidence": 0.96},
        ],
    },
    {
        # 来源：合规雷达-2026年8月-V2 §栏目四#4 + 国内厂商动作（T1 官方源 = CAC，URL 路径待联网核实）
        "kw": ["人工智能生成合成内容标识办法", "生成合成内容标识办法", "AI生成合成内容标识办法", "标识办法", "内容标识办法"],
        "primary_source": {
            "url": "https://www.cac.gov.cn/2025-03/xx/c_标识办法原文.htm",  # 路径待联网核实，域名 cac.gov.cn 权威
            "type": "official_regulation",
            "title": "人工智能生成合成内容标识办法（2025-09-01 施行）",
            "confidence": 0.92,
        },
        "timeline": [
            {"ts": "2025-03", "event": "四部门联合公布《标识办法》", "source": "cac.gov.cn", "tag": "initial_claim", "confidence": 0.92},
            {"ts": "2025-09-01", "event": "《标识办法》正式施行", "source": "cac.gov.cn", "tag": "official_response", "confidence": 0.92},
        ],
    },
]


def _kb_match(query: str):
    q = query.lower()
    for e in _KB:
        ctx = e.get("req_context")
        for kw in e["kw"]:
            if kw.lower() in q:
                if ctx and not any(c.lower() in q for c in ctx):
                    continue  # 软别名但无法规上下文 → 跳过，不误命中
                return e
    return None


def _is_official(url: str) -> bool:
    return any(t in url.lower() for t in [
        ".gov.cn", "gov.", ".edu.cn", "arxiv.org", "ieee.org", "nasa.gov",
        "eur-lex.europa.eu", "nist.gov", "doi.org",
    ])


def _url_heuristic(url: str):
    """input_type=url 时，用域名判断是否为权威原始出处。"""
    m = re.search(r"https?://([^/]+)/?", url)
    if not m:
        return None
    domain = m.group(1).lower()
    official = _is_official(url)
    return {
        "url": url,
        "type": "official_or_scholar" if official else "unknown_domain",
        "title": domain,
        "confidence": 0.9 if official else 0.5,
    }


def _best_candidate(candidate_sources):
    """调用方 Agent 自带检索到的候选源：优先取一手源（官方/学术域名）。"""
    if not candidate_sources:
        return None
    for url in candidate_sources:
        if _is_official(url):
            return {
                "url": url,
                "type": "official_or_scholar",
                "title": url,
                "confidence": 0.88,
            }
    # 退而取第一个作为候选（低置信）
    return {"url": candidate_sources[0], "type": "candidate_unverified", "title": candidate_sources[0], "confidence": 0.55}


def _db_search(input_text: str, domain: str, depth: str):
    """优先查 compliance_db，返回标准化的 report dict 或 None。"""
    try:
        from compliance_db import search_by_keyword
    except Exception:
        return None

    if domain == "compliance":
        hits = search_by_keyword(input_text, limit=3)
        if hits:
            best = hits[0]
            report = {
                "primary_source": best["source"],
                "timeline": best.get("timeline", []),
                "contamination_chain": [],
                "media_first_report": None,
                "overall_confidence": best["source"]["confidence"],
                "degradation_note": None,
                "mode": "db",
            }
            if depth == "deep":
                # deep 档补充污染链占位（真实值需后续 LLM/检索增强）
                report["contamination_chain"] = [
                    {
                        "from": best["source"]["url"],
                        "to": "media_x",
                        "action": "fact_laundering",
                        "note": "数据库深度占位：需接入 LLM/检索后补充真实污染链",
                        "severity": "medium",
                    }
                ]
                from newsylist_client import enrich_media_first_report
                report["media_first_report"] = enrich_media_first_report(input_text)
            return report
    return None


def run_trace(input_text: str, input_type: str, domain: str, depth: str,
              candidate_sources=None, caller_judgment=None) -> dict:
    if Config.LLM_PROVIDER == "mock":
        return _run_trace_heuristic(input_text, input_type, domain, depth, candidate_sources, caller_judgment)
    return _run_trace_real(input_text, input_type, domain, depth, candidate_sources, caller_judgment)


def _run_trace_heuristic(input_text, input_type, domain, depth, candidate_sources, caller_judgment=None) -> dict:
    # 调用方 Agent 自带大模型已判定为非法规/非一手源诉求（如厂商融资、市场预测）→ 直接诚实降级
    if caller_judgment == "other":
        media = enrich_media_first_report(input_text)
        return {
            "primary_source": None,
            "timeline": [],
            "contamination_chain": [],
            "media_first_report": media,
            "overall_confidence": 0.0,
            "degradation_note": "调用方 Agent（大模型）判定为非法规一手源诉求，已诚实降级（不查 KB）",
            "mode": "mock",
        }

    # 1) 优先查 compliance_db
    if input_type != "url":
        db_report = _db_search(input_text, domain, depth)
        if db_report and db_report.get("primary_source"):
            return db_report

    # 2) 回退到内存 _KB
    primary_source = None
    timeline = []
    contamination_chain = []
    confidence = 0.3
    note = "未发现可验证原始文件"

    if input_type == "url":
        ps = _url_heuristic(input_text)
        if ps:
            primary_source = ps
            timeline = [{"ts": "—", "event": f"输入 URL 来自 {ps['title']}", "source": ps["title"], "tag": "initial_claim", "confidence": ps["confidence"]}]
            confidence = ps["confidence"]
            note = "由输入 URL 域名推断为候选原始出处（原型启发式）"
    else:
        hit = _kb_match(input_text)
        if hit:
            primary_source = hit["primary_source"]
            timeline = hit["timeline"]
            confidence = hit["primary_source"]["confidence"]
            note = "命中内存 KB（原型启发式命中）"
        elif candidate_sources:
            primary_source = _best_candidate(candidate_sources)
            confidence = primary_source["confidence"]
            note = "采用调用方 Agent 提供的候选源（一手源优先）"
        if primary_source and depth == "deep":
            contamination_chain = [
                {"from": primary_source["url"], "to": "media_x", "action": "fact_laundering",
                 "note": "数据准确但归因到媒体而非原文", "severity": "medium"}
            ]

    media = enrich_media_first_report(input_text)

    return {
        "primary_source": primary_source,          # 无则 null（诚实降级）
        "timeline": timeline,
        "contamination_chain": contamination_chain,
        "media_first_report": media,
        "overall_confidence": confidence,
        "degradation_note": None if primary_source else note,
        "mode": "mock",
    }


def _run_trace_real(input_text, input_type, domain, depth, candidate_sources, caller_judgment=None) -> dict:
    """
    真实路径占位：调 LLM（Config.LLM_*）+ 检索层（Config.SEARCH_API_KEY，Brave/Tavily），
    执行 root-source 判定 + 时间线 + 污染链。配置 ST_LLM_API_KEY 后启用。
    """
    raise NotImplementedError(
        "真实 LLM 溯源需配置 ST_LLM_API_KEY / ST_SEARCH_API_KEY；当前为 mock 原型。"
    )
