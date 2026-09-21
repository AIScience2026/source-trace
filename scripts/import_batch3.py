#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条导入信源 #26-40（AI 层：伦理/安全/风险管理）"""
import sys
sys.path.insert(0, ".")
from compliance_db import get_conn, upsert_source

entries = [
    {
        "url": "https://temp.source-trace.local/26-transformer",
        "type": "official_paper",
        "title": "Transformer: Attention is All You Need",
        "confidence": 0.95,
        "domain": "arxiv.org",
        "keywords": ["Transformer", "attention", "自注意力", "Transformer论文"],
        "soft_aliases": ["Transformer", "attention"],
        "context_map": {"Transformer": ["论文", "架构", "NLP"], "attention": ["论文", "架构"]},
        "timeline_events": [
            {"ts": "2017-06-12", "event": "Vaswani et al. 发布 Transformer 论文", "source": "arxiv.org", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/27-gpt-1",
        "type": "official_paper",
        "title": "GPT-1: Improving Language Understanding",
        "confidence": 0.95,
        "domain": "openai.com",
        "keywords": ["GPT-1", "生成式预训练", "语言模型", "GPT-1论文"],
        "soft_aliases": ["GPT-1"],
        "context_map": {"GPT-1": ["GPT", "预训练", "语言模型"], "生成式预训练": ["GPT", "语言模型"]},
        "timeline_events": [
            {"ts": "2018-06-11", "event": "OpenAI 发布 GPT-1", "source": "openai.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/28-gpt-2",
        "type": "official_paper",
        "title": "GPT-2: Language Models are Unsupervised Multitask Learners",
        "confidence": 0.95,
        "domain": "openai.com",
        "keywords": ["GPT-2", "zero-shot", "语言模型", "GPT-2论文"],
        "soft_aliases": ["GPT-2"],
        "context_map": {"GPT-2": ["GPT", "zero-shot"], "zero-shot": ["GPT", "语言模型"]},
        "timeline_events": [
            {"ts": "2019-02-14", "event": "OpenAI 发布 GPT-2", "source": "openai.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/29-gpt-3",
        "type": "official_paper",
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "confidence": 0.95,
        "domain": "openai.com",
        "keywords": ["GPT-3", "few-shot", "大语言模型", "GPT-3论文"],
        "soft_aliases": ["GPT-3"],
        "context_map": {"GPT-3": ["GPT", "few-shot"], "few-shot": ["GPT", "大语言模型"]},
        "timeline_events": [
            {"ts": "2020-05-28", "event": "OpenAI 发布 GPT-3", "source": "openai.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/30-gpt-4",
        "type": "official_paper",
        "title": "GPT-4 Technical Report",
        "confidence": 0.95,
        "domain": "openai.com",
        "keywords": ["GPT-4", "多模态", "AGI", "GPT-4技术报告"],
        "soft_aliases": ["GPT-4"],
        "context_map": {"GPT-4": ["GPT", "多模态"], "多模态": ["GPT-4", "多模态"]},
        "timeline_events": [
            {"ts": "2023-03-15", "event": "OpenAI 发布 GPT-4 Technical Report", "source": "openai.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/31-claude",
        "type": "official_paper",
        "title": "Claude: Constitutional AI",
        "confidence": 0.95,
        "domain": "anthropic.com",
        "keywords": ["Claude", "Constitutional AI", "RLHF", "AI安全", "Claude论文"],
        "soft_aliases": ["Claude"],
        "context_map": {"Claude": ["安全", "对齐"], "Constitutional AI": ["AI安全", "对齐"]},
        "timeline_events": [
            {"ts": "2022-12-15", "event": "Anthropic 发布 Constitutional AI", "source": "anthropic.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/32-llama",
        "type": "official_paper",
        "title": "LLaMA: Open and Efficient Foundation Language Models",
        "confidence": 0.95,
        "domain": "ai.meta.com",
        "keywords": ["LLaMA", "开源大模型", "Meta", "LLaMA论文"],
        "soft_aliases": ["LLaMA"],
        "context_map": {"LLaMA": ["开源", "Meta"], "开源大模型": ["Meta", "开源"]},
        "timeline_events": [
            {"ts": "2023-02-27", "event": "Meta 发布 LLaMA", "source": "ai.meta.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/33-alphafold",
        "type": "official_paper",
        "title": "AlphaFold 2: Highly Accurate Protein Structure Prediction",
        "confidence": 0.95,
        "domain": "nature.com",
        "keywords": ["AlphaFold", "蛋白质结构", "DeepMind", "AlphaFold 2"],
        "soft_aliases": ["AlphaFold"],
        "context_map": {"AlphaFold": ["蛋白质", "DeepMind"], "蛋白质结构": ["AlphaFold", "DeepMind"]},
        "timeline_events": [
            {"ts": "2021-07-15", "event": "DeepMind 发布 AlphaFold 2", "source": "nature.com", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/34-diffusion",
        "type": "official_paper",
        "title": "Diffusion Models Beat GANs",
        "confidence": 0.95,
        "domain": "arxiv.org",
        "keywords": ["Diffusion", "扩散模型", "Stable Diffusion", "Diffusion模型"],
        "soft_aliases": ["Diffusion", "扩散模型"],
        "context_map": {"Diffusion": ["生成模型", "扩散"], "扩散模型": ["Diffusion", "生成模型"]},
        "timeline_events": [
            {"ts": "2021-06-15", "event": "Diffusion 模型论文发布", "source": "arxiv.org", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/35-cot",
        "type": "official_paper",
        "title": "Chain-of-Thought Prompting",
        "confidence": 0.95,
        "domain": "arxiv.org",
        "keywords": ["CoT", "思维链", "提示工程", "Chain-of-Thought"],
        "soft_aliases": ["CoT", "思维链"],
        "context_map": {"CoT": ["思维链", "推理"], "思维链": ["CoT", "推理"]},
        "timeline_events": [
            {"ts": "2022-01-28", "event": "Chain-of-Thought Prompting 论文发布", "source": "arxiv.org", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/36-react",
        "type": "official_paper",
        "title": "ReAct: Synergizing Reasoning and Acting",
        "confidence": 0.95,
        "domain": "arxiv.org",
        "keywords": ["ReAct", "推理+行动", "Agent", "ReAct论文"],
        "soft_aliases": ["ReAct"],
        "context_map": {"ReAct": ["Agent", "推理"], "推理+行动": ["Agent", "推理"]},
        "timeline_events": [
            {"ts": "2022-02-17", "event": "ReAct 论文发布", "source": "arxiv.org", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
    {
        "url": "https://temp.source-trace.local/37-toolformer",
        "type": "official_paper",
        "title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "confidence": 0.95,
        "domain": "arxiv.org",
        "keywords": ["Toolformer", "工具使用", "Function Calling", "Toolformer论文"],
        "soft_aliases": ["Toolformer"],
        "context_map": {"Toolformer": ["工具", "Function Calling"], "工具使用": ["Toolformer", "Function Calling"]},
        "timeline_events": [
            {"ts": "2023-02-07", "event": "Toolformer 论文发布", "source": "arxiv.org", "tag": "initial_claim", "confidence": 0.95},
        ],
    },
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
