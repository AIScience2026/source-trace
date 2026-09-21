# 溯源 API (SourceTrace) — 原型（v4 MCP-first）

> 配套 PRD：`源溯API-PRD-v0-初稿.md`（v4 定稿：MCP-first 架构）
> 定位：一个 **MCP 工具服务**，被别的 AI Agent 调用；调用方 Agent 自带 LLM + Web 搜索算力完成溯源推理，
> 我们提供「编排 + Newsylist 媒体首发增强 + 垂直合规语料校验 + 审计级 JSON + 计量 + 支付宝「AI 收」按次收款」。

## ⚠️ 传输帧格式（踩过大坑，改回 Content-Length 会直接挂不上）
MCP stdio 规范 = **换行分隔 JSON**：每行一条完整 JSON-RPC 消息，不得含内嵌换行。
**不是** LSP 的 `Content-Length: N` + 空行 帧。
曾用 Content-Length 帧 → 宿主发来的 JSON 首行被当成 header 吞掉 → 永久等待空行 → 连接永远停在 `connecting`。
`stdout` 只许输出协议消息，任何日志必须走 **stderr**。

## 运行（零依赖，stdlib）

### 方式一：命令行自测
```bash
cd source_trace

# 内置 4 案例（合规命中 / 无源降级 / URL / 调用方候选源），看链路是否通
python demo.py

# 试自己的句子 —— 打印完整审计 JSON
python demo.py --input "AI伴侣相关的国家法规" --depth deep
python demo.py --input "https://www.cac.gov.cn/xxx.pdf" --type url
python demo.py -i "AI Act 已生效" --candidate "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
```
参数：`--input/-i` · `--type claim|url|text` · `--domain compliance|ai|robotics|general`
· `--depth standard|deep`（¥0.05/¥0.10）· `--candidate`（可重复）。

### 方式二：挂到 MCP client（真实形态）
```json
{ "mcpServers": { "suyuan-trace": {
  "command": "C:\\Users\\heatonyu\\.workbuddy\\binaries\\python\\versions\\3.13.12\\python.exe",
  "args": ["D:\\self-development\\WorkBuddy开发者\\人因工程师副业睡后收入\\source_trace\\mcp_server.py"],
  "disabled": false } } }
```
> Windows 上 `command` 必须写**绝对路径** python（宿主 PATH 不含托管运行时目录，裸 `python` 会 ENOENT）。
> 配置：`~/.workbuddy/mcp.json`。写完不会自动生效，需在连接器管理页点 **Trust**；
> **改完 server 代码后需重启应用**（宿主的工具索引在会话启动时固化，热改文件不会重新枚举工具）。

## 两层验证（别只跑第一层）
| 验证 | 命令 | 能证明 | 局限 |
|---|---|---|---|
| 自检（自家方言） | `python selftest_mcp.py` | 绝对路径 + 非项目 cwd 下能握手/调用 | **与 server 同源，会自证循环** |
| 独立验证（官方 SDK） | `node official_sdk_check.mjs` | 官方 `@modelcontextprotocol/sdk` 能挂载调用 = 规范合规 | 需 workspace 内已装 SDK |

> 教训：早期 demo 与 server 都用非规范的 Content-Length 帧，**自测全绿但真实宿主挂不上**。
> 自测通过 ≠ 能挂载；必须有独立于自己实现的验证方。

## MCP 工具
### `trace`
入参：`input`(说法/URL/文本) · `input_type`(claim|url|text) · `domain`(compliance|ai|robotics|general) · `depth`(standard|deep) · `candidate_sources`(可选，调用方已检索到的候选源) · `caller_judgment`(可选，`regulation`/`other`——**调用方 Agent 自带大模型的意图语义判断**，v4 治本路径：`other` 时工具直接诚实降级不查 KB)
出参（机器可消费 JSON）：`primary_source`(一手源，无则 null) + `timeline` + `contamination_chain` + `media_first_report`(Newsylist) + `overall_confidence` + `billed_amount`

> **为什么有 caller_judgment**：mock 引擎无语义消歧，曾把厂商融资/市场动态误命中为法规一手源（M2 的 FABRICATED 项）。
> v4 设计即"调用方 Agent 自带算力"——调用方（如 workBuddy）运行在大模型上，由模型先判断 query 意图，
> 把 `regulation`/`other` 透传给工具。server 子进程本身无模型访问权（需 `ST_LLM_API_KEY` 才能 server 侧跑 LLM），
> 所以语义消歧天然在调用方侧完成。这从根上消除误命中（M2 可溯源率 100%）。

## 白嫖的免费能力
- **Newsylist** `api/trends.json`：媒体首发增强（匹配不上优雅降级，不阻断主溯源）。
  ⚠️ 中文当前是 naive 分词，基本匹配不上；想看点效果用**英文话题**命中率更高。

## 待接入（见 ASK.md，不阻塞本地调通）
- 可选托管 LLM 档：配置 `ST_LLM_API_KEY` 启用我们后端 LLM 兜底（覆盖无强 Agent 的调用方，+¥0.05）。
- 服务端检索兜底：配置 `ST_SEARCH_API_KEY`（Brave/Tavily；**Bing 已 2025-08-11 停售**）。
- 支付宝「AI 收」真实收款：提供 `ST_ALIPAY_APP_ID` + 应用私钥 + 公网回调，切 A2A 自动结算。

## ⚠️ 原型期诚实声明（别把 demo 当准确率证明）
当前是 **mock 启发式引擎**：命中靠内置合规知识库 + 域名启发式。
- 「AI伴侣 / 拟人化互动」条目已用**老板自己核过的语料**校准（2026-04-10 公布、2026-07-15 施行、cac.gov.cn 原始 URL）。
- `contamination_chain` 里的 `media_x` 仍是**占位示例**，非真实抓取的污染链。
- 计费是 mock，不真扣钱（返回 `payment_mock: true`）。
- **本 demo 证明"管道通、契约对、计费对、降级对"，不证明"溯源准"。** M2 当前可溯源率 100%(12/12)，但这是 KB 覆盖率上限，真实世界准确率需接 LLM/检索后复测。

## 文件
- `mcp_server.py` MCP server（stdio，换行分隔 JSON）— 主入口
- `trace_engine.py` 溯源核心（mock 启发式 + 真实 LLM 占位 + 垂直知识库）
- `newsylist_client.py` Newsylist 免费能力客户端
- `alipay.py` 支付宝「AI 收」计费层（mock + 生产占位）
- `store.py` 账单存储（落盘 billing.jsonl）
- `config.py` 配置（所有外部依赖可切换/mock）
- `demo.py` MCP client 演示（内置 4 案例 / `--input` 自定义）— 自家方言
- `demo_caller_llm.py` 方案1 演示：调用方大模型意图消歧 → `caller_judgment` → 工具诚实降级（真实 MCP 握手，治本验证）
- `selftest_mcp.py` 挂载前自检（绝对路径 + 非项目 cwd）— 自家方言
- `official_sdk_check.mjs` **官方 SDK 独立验证** — 规范合规的证明
- `m2_eval.py` M2 准确率评测（直接 import 引擎，对齐 PRD §13 口径）
- `server.py` ⚠️ 旧版 HTTP 两阶段服务（已废弃，v4 改 MCP 形态，可删）
