// 官方 MCP SDK 独立验证脚本（不是自家方言自测）
//
// 为什么需要它：demo.py / selftest_mcp.py 与 mcp_server.py 同源，曾因双方都用
// 非规范的 Content-Length 帧而"自测通过、实际挂不上"。本脚本用 @modelcontextprotocol/sdk
// 的官方 StdioClientTransport 当客户端，只认 MCP 规范（换行分隔 JSON），
// 能真正证明这个 server 可以被真实 MCP 宿主挂载。
//
// 运行：
//   node official_sdk_check.mjs
// （依赖装在 C:\Users\heatonyu\.workbuddy\binaries\node\workspace\node_modules）

import { createRequire } from "node:module";

const SDK_ROOT = "C:/Users/heatonyu/.workbuddy/binaries/node/workspace/package.json";
const require = createRequire(SDK_ROOT);
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

const PY = "C:\\Users\\heatonyu\\.workbuddy\\binaries\\python\\versions\\3.13.12\\python.exe";
const SERVER = "D:\\self-development\\WorkBuddy开发者\\人因工程师副业睡后收入\\source_trace\\mcp_server.py";

const CASES = [
  ["合规命中", { input: "中国拟出台人工智能拟人化互动服务管理暂行办法", input_type: "claim", domain: "compliance", depth: "deep" }],
  ["无源降级", { input: "据说某科技公司下周要发布新机器人", input_type: "claim", domain: "robotics", depth: "standard" }],
  ["候选源", { input: "AI Act 已生效", input_type: "claim", domain: "compliance", depth: "standard",
               candidate_sources: ["https://eur-lex.europa.eu/eli/reg/2024/1689/oj"] }],
];

const transport = new StdioClientTransport({
  command: PY,
  args: [SERVER],
  cwd: "C:\\",              // 故意用非项目目录，模拟宿主启动
  stderr: "pipe",
});

const client = new Client({ name: "official-sdk-check", version: "0.1" }, { capabilities: {} });

try {
  await client.connect(transport);
  console.log("[OK] 官方 SDK 握手成功 →", client.getServerVersion());
  console.log("[OK] 协商协议版本 →", client.getNegotiatedProtocolVersion?.() ?? "(n/a)");

  const tools = await client.listTools();
  console.log("[OK] tools/list →", tools.tools.map((t) => t.name));

  for (const [label, args] of CASES) {
    const r = await client.callTool({ name: "trace", arguments: args });
    const o = JSON.parse(r.content[0].text);
    console.log(`\n=== ${label} ===`);
    console.log(JSON.stringify({
      primary_source: o.primary_source,
      overall_confidence: o.overall_confidence,
      degradation_note: o.degradation_note,
      billed_amount: o.billed_amount,
    }, null, 2));
  }
  console.log("\n结论：官方 SDK 能正常挂载并调用，mcp.json 配置可用。");
  process.exitCode = 0;
} catch (e) {
  console.error("[FAIL]", e?.message || e);
  process.exitCode = 1;
} finally {
  await client.close().catch(() => {});
}
