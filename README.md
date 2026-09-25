# SourceTrace — Compliance Provenance MCP Server

> **AI agents hallucinate regulation URLs, dates and clause numbers.** SourceTrace gives an agent a
> tool that traces a claim back to its verified primary source, or honestly says it cannot find one.

`mcp-name: io.github.AIScience2026/source-trace`

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)

**Landing page**: https://aiscience2026.github.io/source-trace/

---

## Why this exists

When an AI agent cites a regulation, three failure modes show up over and over:

| Failure | Example |
|---|---|
| **Fabricated URL / date** | Training-data cutoff means a "2024 regulation" link is actually a 404 or points at the wrong document |
| **Primary source confused with secondary coverage** | A news article about a standard is cited as the standard itself |
| **Opaque provenance** | No way to audit where the answer came from, so nothing can be checked by a third party |

SourceTrace attacks exactly these. It is an **MCP-first** tool: your agent brings its own LLM and
web-search reasoning; the server provides orchestration, media-first-report enrichment, vertical
corpus validation, an audit-grade JSON payload and metering.

## What it returns

A single tool, `trace`, returns a machine-consumable JSON payload:

```json
{
  "trace_id": "st_9f2c1d4e8a7b",
  "status": "fulfilled",
  "query": "EU AI Act entered into force",
  "primary_source": {
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "type": "official_or_scholar",
    "title": "Regulation (EU) 2024/1689",
    "confidence": 0.88
  },
  "timeline": [ ... ],
  "contamination_chain": [ ... ],
  "media_first_report": null,
  "overall_confidence": 0.88,
  "degradation_note": null,
  "billed_amount": 0.05
}
```

**When no primary source can be established, it returns `primary_source: null`** — it does not
invent one. This "honest degradation" contract is the whole point of the tool.

### Tool signature

| Field | Values | Notes |
|---|---|---|
| `input` | string | the claim / URL / text to trace (**required**) |
| `input_type` | `claim` \| `url` \| `text` | default `claim` |
| `domain` | `compliance` \| `ai` \| `robotics` \| `general` | default `compliance` |
| `depth` | `standard` \| `deep` | `¥0.05` / `¥0.10` (sandbox free, see Pricing) |
| `candidate_sources` | string[] | sources your agent already retrieved; lets the caller supply the search |

### `caller_judgment` — the anti-false-positive hook

The mock heuristic engine cannot disambiguate intent, and once matched a company funding round to
the wrong regulation clause. The v4 fix puts semantic judgment on the **caller** side: a
model-driven agent passes `caller_judgment: "regulation" | "other"` and the tool degrades honestly
on `other` instead of guessing. In M2 evaluation this took traceable accuracy to 12/12.

## Install

### As an MCP server (stdio)

```json
{
  "mcpServers": {
    "source-trace": {
      "command": "python",
      "args": ["D:/path/to/source_trace/mcp_server.py"]
    }
  }
}
```

On Windows, use the **absolute path** to a Python interpreter — hosts often do not have the
runtime directory on `PATH`, and a bare `python` fails with `ENOENT`.

### From PyPI

```bash
pip install source-trace
source-trace     # starts the stdio server
```

### Docker

```bash
docker build -t source-trace .
docker run -i source-trace
```

## Coverage

56 verified sources spanning ISO/IEC standards, EU AI Act, NIST AI RMF, UNESCO/OECD instruments,
and Chinese regulations (CAC, NPC, MOST). Types: `official_standard` 28, `official_regulation` 11,
`official_guideline` 9, `official_report` 7, `official_notice` 1.

Domains: **compliance** (regulations/regulators), **robotics** (ISO 10218/15066/8373,
IEC 61508/62061, GB/T 36430/41870), **ai** (IEEE P7000/P2864, UNESCO, OECD, Asilomar,
Beijing AI Principles).

> **Honest scope statement.** 56 sources is a prototype corpus, not market coverage. Unmatched
> queries degrade to `primary_source: null` — by design, not by accident.

## Pricing

| Tier | Price | Includes |
|---|---|---|
| Standard | ¥0.05 / call | DB precision match, `primary_source` + `timeline`, honest degradation, audit JSON |
| Deep | ¥0.10 / call | + soft-alias defence, context-word validation, contamination analysis |
| Sandbox | free | developer sandbox, no real charge |
| Hosted LLM | +¥0.05 | our backend LLM fallback for callers without a strong agent |
| Enterprise | custom | private deployment, custom source corpus, SLA |

Billing is currently **mocked** (`payment_mock: true`) — the Alipay "AI 收" integration is wired
but not yet live in production. Metering still records every call to `billing.jsonl` so the
contract, accounting and degradation paths are all exercised end to end.

## Current limitations (read this before trusting it)

| Limitation | Detail |
|---|---|
| **Mock heuristic engine** | Matching is built-in compliance knowledge + domain heuristics. It proves the pipe, the contract, the billing and the degradation are right — **it does not prove trace accuracy** |
| **M2 100% is a ceiling, not a score** | 12/12 traceable reflects knowledge-base coverage, not real-world accuracy. Real accuracy requires an LLM/retrieval backend |
| **`contamination_chain` uses placeholders** | `media_x` entries are examples, not a genuinely scraped propagation chain |
| **Chinese segmentation is naive** | Newsylist Chinese matching largely misses; English topics hit far more often |
| **Landing-page demo is front-end only** | The demo box on the landing page does local keyword matching in the browser over `sources.json`. It is **not** the MCP server's behaviour |

## Verification

Two layers, deliberately — a self-test that speaks the project's own dialect would have passed
while a real host could not mount the server (an early build used LSP `Content-Length` framing
instead of newline-delimited JSON-RPC, so `demo.py` and `selftest_mcp.py` were both green while
the connection sat at `connecting` forever).

| Layer | Command | What it proves |
|---|---|---|
| Self-check | `python selftest_mcp.py` | mounts from an absolute path, outside the project cwd |
| **Independent check** | `node official_sdk_check.mjs` | the official `@modelcontextprotocol/sdk` `StdioClientTransport` can mount and call it — i.e. spec compliance from outside the project |

## Privacy Policy

SourceTrace processes **no personal data**.

- The stdio server runs locally on your machine; it is not a hosted service.
- A call sends only the `input` string you pass. No telemetry, no analytics, no account required.
- Billing records (`trace_id`, `domain`, `depth`, `amount`, `status`) are appended to a local
  `billing.jsonl` file inside the server directory. No recipient or payer identity is stored.
- When the Alipay "AI 收" integration goes live, the payment provider will receive only what a
  payment transaction requires (amount, order reference). This section will be updated before
  that changes.
- The only optional outbound request is to `api.newsylist.com/api/trends.json` for
  media-first-report enrichment; when it is unreachable the tool degrades gracefully and never
  blocks the main trace.

For questions about this policy, open an issue in this repository.

## License

[MIT](LICENSE)

## Links

- Landing page — https://aiscience2026.github.io/source-trace/
- Issues — https://github.com/AIScience2026/source-trace/issues
- MCP protocol — https://modelcontextprotocol.io/

---

<details>
<summary>中文说明（折叠）</summary>

## 溯源 API（SourceTrace）— 原型（v4 MCP-first）

一个 **MCP 工具服务**，被别的 AI Agent 调用。调用方 Agent 自带 LLM + Web 搜索算力完成溯源推理；
本服务提供「编排 + Newsylist 媒体首发增强 + 垂直合规语料校验 + 审计级 JSON + 计量 + 支付宝
「AI 收」按次收款」。

- 运行：`python mcp_server.py`（stdio，零三方依赖，Python 标准库）
- 传输：换行分隔 JSON-RPC。**不是** LSP 的 `Content-Length` 帧（踩过坑，会导致连接永远停在
  `connecting`）
- `trace` 工具入参：`input`（必填）· `input_type`(claim/url/text) · `domain`
  (compliance/ai/robotics/general) · `depth`(standard/deep) · `candidate_sources`（可选）
- 查不到一手源时**诚实返回 `primary_source=null`**，不编造

详细工程说明见仓库内 `README-zh` 历史版本与确认记录文档；本 README 以英文为主，便于目录站收录。

</details>
