# SourceTrace 现状客观分析

> **文档定位**：本文只记录可核验的事实，以及从这些事实推出的判断。推测部分全部标注「推测」。
> **数据核验日期**：2026-09-25
> **数据来源**：本地仓库文件系统检查、GitHub REST API（traffic 端点）、线上页面 HTTP 抓取、本地 git 历史、SQLite 库内容统计。

---

## 一、一句话结论

**SourceTrace 目前是一个「技术管道已通、产品尚未成型、零外部验证」的原型。当前最缺的不是流量或埋点，是「谁真的会调这个 API」这个问题的答案。**

---

## 二、已验证的事实（可复现）

### 2.1 产品形态：MCP-first，本地可用

| 项目 | 事实 | 来源 |
|---|---|---|
| 架构 | stdio MCP server（`mcp_server.py`），零三方依赖（纯 Python 标准库） | `README.md` L13 |
| 工具 | 单一工具 `trace`，入参 input/input_type/domain/depth/candidate_sources/caller_judgment | `README.md` L50-53 |
| 传输协议 | 换行分隔 JSON-RPC（**不是** LSP 的 Content-Length 帧） | `README.md` L7-11 |
| 规范合规 | 官方 `@modelcontextprotocol/sdk` 可独立挂载调用（`official_sdk_check.mjs`） | `README.md` L45 |
| 分层验证 | 自检（`selftest_mcp.py`，自家方言）+ 官方 SDK 独立验证，两层都跑过 | `README.md` L42-48 |

**这是个真实的工程成果**：换行 JSON 帧这个坑是真实踩过并记录在案的（Content-Length 帧导致宿主永久停留在 `connecting`），两层验证的做法也是对的——自测通过 ≠ 能挂载。

### 2.2 溯源能力：mock 启发式，不是真溯源

| 项目 | 事实 | 来源 |
|---|---|---|
| 引擎本质 | **mock 启发式引擎**：命中靠内置合规知识库 + 域名启发式 | `README.md` L70-74 |
| 知识库规模 | **56 条**信源（sources.json / compliance.db，两处一致） | 本地统计 |
| 领域分布 | 按域名：ISO 17、gov.cn 系（含 cac/npc/most/cea）10、cac.gov.cn 5、npc.gov.cn 3、eur-lex 2、nist 2、iec 3 等 | 本地统计 |
| 类型分布 | official_standard 28、official_regulation 11、official_guideline 9、official_report 7、official_notice 1 | 本地统计 |
| 中文分词 | Newsylist 中文「当前是 naive 分词，基本匹配不上；想看效果用英文话题」 | `README.md` L62 |
| 污染链 | `contamination_chain` 里的 `media_x` 仍是**占位示例**，非真实抓取 | `README.md` L72 |
| 计费 | mock，不真扣钱（返回 `payment_mock: true`） | `README.md` L73 |
| M2 自评 | 可溯源率 100%（12/12），但 README 自己说明「这是 KB 覆盖率上限」 | `README.md` L74 |

**自我评价很诚实，这一点值得肯定**：README 明确写了「本 demo 证明管道通、契约对、计费对、降级对，不证明溯源准」。

### 2.3 收款：本地 mock，未接真钱

| 项目 | 事实 | 来源 |
|---|---|---|
| 支付宝 SDK | `@alipay/alipay-aipay@1.6.9` 已装（npm，Alipay 官方） | `支付宝AI付接入记录-2026-09-20.md` |
| 签约状态 | 记录文档写「用户确认已完成签约入驻」（2026-09-20 更新） | 同上 L35 |
| 真实联调 | 待提供 APPID + 应用私钥 + 公网回调地址 | `ASK.md` L19-22 |
| 额度限制 | 单笔 ≤50，单日 ≤1000 | `USER-TODO-2026-09-17.md` L16 |

### 2.4 落地页：已上线，功能可用

| 项目 | 事实 | 核验方式 |
|---|---|---|
| URL | `https://aiscience2026.github.io/source-trace/` | `curl -o /dev/null -w` |
| HTTP 状态 | **200**，0.78s（可达，无需代理） | `curl` 实测 |
| 邮箱方案 | mailto 直连 `yuanting7971@agent.qq.com`，零第三方、零后端 | 线上 HTML grep 实测到 2 处 mailto + 邮箱地址 |
| 页面 demo | 纯前端 JS，`fetch('sources.json')` 后本地关键词匹配 | `index.html` L288-376 |
| 定价展示 | Standard ¥0.05 / Deep ¥0.10 / Enterprise 定制 | `index.html` L221-257 |
| 隐私设计 | 页面明确写「不经过第三方表单服务，邮箱地址只进入我们的收件箱」 | `index.html` L269-273 |

### 2.5 流量：真实数据（GitHub REST API 实测）

近 14 天（2026-09-10 → 2026-09-23）：

| 指标 | 数值 | 说明 |
|---|---|---|
| **页面 views** | **5 次，1 个独立访客** | 9/21 有 4 次，9/23 有 1 次，其余 12 天全 0 |
| **仓库 clones** | **51 次，25 个独立访客** | 9/21 有 30 次/15 人，9/22 有 19 次/11 人，9/23 有 2 次/2 人 |
| **来源 referrers** | github.com → 3 次 | 唯一来源 |
| **热门路径** | `/AIScience2026/source-trace` → 3 次 | Overview 页，不是 Pages 路径 |

**clones : views ≈ 10 : 1**。所有已知流量都来自 GitHub 站内（有人从仓库页点进来），**没有任何站外来源**。

### 2.6 仓库状态

| 项目 | 事实 |
|---|---|
| 本地 commit | `682c3bb docs: 邮箱收集方案说明`，7 个 commit |
| 与远程同步 | `git log origin/main..main` 为空，**已完全同步** |
| 未跟踪文件 | `demo.py`、`m2_eval.py`、`selftest_mcp.py`、`server.py`（旧版 HTTP，README 标注「已废弃，可删」）等 10 个 |
| `.gitignore` | 已排除 `compliance.db`、`billing.jsonl`、`.env`、`*.jsonl` |

---

## 三、从事实推出的判断

### 3.1 流量为 0 不是bug，是**没有分发**

站是好的：HTTP 200、0.78s、mailto 逻辑线上真实存在。但流量数据里 **referrers 只有 github.com**——说明没有任何人从站外点进来。

没有站外来源的原因是：**还没有往任何站外渠道投过链接**。

所以「流量为 0」这个现象本身不构成需要诊断的问题，它只是「还没开始推」的客观反映。

### 3.2 clones 远多于 views，说明被当代码仓库而非产品看

10:1 的比例 + 来源 100% 是 GitHub 站内，指向一个判断：**看到这个仓库的人，行为是 clone 下来看代码，不是访问落地页留邮箱。**

对副业收入目标来说这是个**中性偏负面**的信号：
- 正面：50 次 clone 说明技术实现有人认可，工程质量过了第一眼关；
- 负面：没有任何证据表明有人把这个当成「愿意付费的服务」。

### 3.3 页面 demo 会制造错误预期（这是我最在意的一条）

`index.html` 的 demo 是**纯前端 JS 关键词匹配**，跑在 `sources.json` 的 56 条上。

问题在于：**页面 demo 的效果 ≠ MCP server 的效果**。前端 demo 是浏览器里的字符串匹配；真实产品是带 `caller_judgment`、时间线、污染链、审计 JSON 的 MCP 工具。

后果是：一个潜在客户试了页面 demo，觉得「就是个关键词搜索」，然后离开——**而真实能力被这个 demo 拉低了**。反过来，如果他试了觉得不错，接真实 MCP 又会发现不是一回事。

页面上的数字「信源入库 56」「覆盖领域 3」「诚实降级 100%」也在做同样的事：把原型期的覆盖率当成产品指标展示。

> 页面 v0.1-prototype 的自我标注是对的（footer 写了 `v0.1-prototype`），但 demo 区没有对应的提示。

### 3.4 「56 条信源」和「合规刚需」之间有真实落差

README 和落地的定位是「AI 合规溯源」，业务文档（《目标用户与micro-payment可行性分析》）判断的真实付费方是：**面临《拟人化互动办法》deadline 的 AI 伴侣/机器人厂商、整机厂、UX 团队**。

但知识库 56 条的领域分布是：**ISO 标准 17 条 + 各国政府法规约 20 条 + 学术/伦理报告 7 条**。

也就是说：
- 覆盖的是「通用 AI/机器人标准与法规」；
- 付费方要的是「我这个产品在《拟人化互动办法》第几条上不过关」；
- **两者的交集有多大，没有验证过。**

这是产品定位和资产之间最需要交叉核验的一条。业务文档自己写的顺序是「先吃紧急刚需（C/A）验证付费意愿，再把权威沉淀成 B 的 micro-payment API」——按这个顺序，56 条的 KB 对第一阶段的付费验证**不构成直接支撑**。

---

## 四、真正卡住的问题（按阻塞程度排）

| # | 问题 | 症状 | 是否已在待办里 |
|---|---|---|---|
| **P0** | **没有外部验证过需求** | 0 留联、0 付费意向、0 站外来源。所有「用户会为此付钱」的判断都来自文档推演，无一是外部证实的 | ❌ 不在任何待办 |
| **P0** | **知识库与付费方需求错配未核验** | 56 条通用标准 vs 付费方要的具体合规缺口判断 | ❌ 不在任何待办 |
| **P1** | **页面 demo 拉低产品感知** | 前端关键词匹配被当成产品能力 | ❌ 不在任何待办 |
| **P1** | **真实收款未打通** | 签约了但 APPID/私钥/回调未给，计费还是 mock | 🟡 在 USER-TODO（不阻塞当前阶段） |
| **P2** | **流量数据不积累** | GitHub traffic 只留 14 天，9/21 那 5 次 views 下周就永久丢失 | 🟡 在我创建的两个待办里 |
| **P2** | **站点无任何埋点** | 无法区分「访问了」和「点了订阅但没发出去」 | 🟡 同上 |

---

## 五、我对「两个 SourceTrace 待办」的判断

这两条现在写的是：
1. 「选流量方案并落地（下午）」—— A.定时抓流量 / B.页面埋点 / C.推流量入口
2. 「推流量入口（公众号/社群/HRI社群）」

**我的建议是把这两条降级为 P2，理由如下：**

**P0 优先级应是「先确认有没有人愿意付钱」，不是「先让更多人看到」。**

对一个还没验证需求的服务投流量，本质是**把没验证的假设放大**。当前证据链是：
- 页面 demo 拉低产品感知（3.3）
- knowledge base 和付费方需求可能错配（3.4）
- 已知唯一行为信号是「clone 代码」，不是「留邮箱」（3.2）

在这三条没解决前推流量，进来的量不会变成留联，只会变成「页面浏览后离开」。

**但这不意味着什么都不做。**数据分析、埋点、分发仍然有价值——它们的价值定位不是「提升转化」，而是**「降低错误判断的概率」**：

- **P2 保留**：定时抓流量（绕开 14 天窗口）+ 页面埋点（区分访问/点击）——这是**给 P0 服务的观测设施**，让「投了多少、有没有人点」变成可量化的事实，而不是猜。成本低（纯脚本，零 token），做了不亏。
- **P2 延后**：推流量入口——等 P0 的答案出来再决定往哪推、推什么。**推的方向取决于「谁会付钱」的答案**，现在推可能推错地方。

### 建议的执行顺序

```
第 1 步（P0，需本人）：找 3-5 个目标付费方类型的人聊一次，
                        问「你会用什么方式判断一个合规问题的答案」，
                        不问「你觉得我的产品怎么样」
    ↓ 判断是 / 否
第 2 步（P2，AI 可做）：建定时抓流量 + 页面埋点，攒观测数据
第 3 步（P0 → 若第 1 步有正面信号）：
        修页面 demo 的产品感知问题（标注 demo 能力边界）
        校验 KB 与目标合规场景的覆盖率
        确定分发渠道后，再执行原「推流量入口」待办
```

---

## 六、需要你拍板的问题

1. **P0 需求验证是否现在启动？** 我建议是。具体可以是我起草一份 5 问的访谈提纲，你去聊；或者先小范围发到已有的 HRI/AI 合规社群。
2. **页面 demo 的处理**：是保留（接受它拉低产品感知），还是在页面上明确标注「这是前端简化演示，真实能力通过 MCP 工具提供」？我建议后者，改动很小。
3. **那两个 SourceTrace 待办**：降级为 P2、保留但改描述，还是维持原样？我建议降级并改写描述（见上）。

---

## 附录：本文所有数字的复现方式

```bash
# 页面可达性
curl -o /dev/null -w "HTTP %{http_code} | %{time_total}s\n" https://aiscience2026.github.io/source-trace/

# 邮箱方案在线上确实存在
curl -s https://aiscience2026.github.io/source-trace/ | grep -c "mailto:"

# GitHub 流量（需 GITHUB_TOKEN2）
for ep in traffic/views traffic/clones traffic/popular/referrers traffic/popular/paths; do
  curl -s -H "Authorization: token $GITHUB_TOKEN2" \
    "https://api.github.com/repos/AIScience2026/source-trace/$ep"; echo; done

# 知识库规模
python -c "import json;print(len(json.load(open('sources.json',encoding='utf-8'))['sources']))"

# 本地与远程同步状态
git log origin/main..main --oneline
```
