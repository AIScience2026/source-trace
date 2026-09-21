#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""溯源 API (SourceTrace) — MCP server（stdio，零依赖）

暴露工具 `trace`：输入 claim/url/text（+ 可选 candidate_sources）→ 审计级溯源 JSON
（一手源 + 时间线 + 污染链 + 置信度 + 媒体首发增强 + 计费）。

形态：MCP-first。调用方 Agent 自带 LLM + Web 搜索算力完成"追到哪个原始文件"的推理；
本 server 负责编排 + Newsylist 媒体首发增强 + 垂直语料校验 + 审计 JSON 组装 + 计量 +
支付宝「AI 收」计费（mock 默认，A2A 自动结算待真实凭证）。

兼容任何 MCP client（Claude Desktop / Cursor / Codex / 自研）。协议：MCP，stdio 传输。

⚠️ 传输帧格式（踩过的坑，别改回去）：
   MCP stdio 规范 = **换行分隔 JSON**（每行一条完整 JSON-RPC 消息，不得含内嵌换行）。
   **不是** LSP 的 `Content-Length: N` + 空行 帧。用 Content-Length 会导致宿主发来的
   JSON 首行被当成 header 吞掉 → 永久等待永不到来的空行 → 连接永远停在 "connecting"。
   stdout 只允许输出协议消息；任何日志必须走 stderr。
"""
import json
import os
import sys
import uuid

from config import Config
from trace_engine import run_trace
from alipay import charge
from store import record_call

# 首选协议版本；实际回包时优先回显 client 请求的版本，最大化兼容性
PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "suyuan-trace"
SERVER_VERSION = "0.4.1-mcp"

TOOLS = [
    {
        "name": "trace",
        "description": (
            "将一条信息溯源到原始出处，输出审计级 JSON（一手源+时间线+污染链+置信度）。"
            "调用方 Agent 自带 LLM/Web 搜索算力；本工具做编排 + Newsylist 媒体首发增强"
            " + 垂直语料校验 + 审计组装。无明确原始文件时诚实返回 primary_source=null。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "说法 / URL / 新闻文本"},
                "input_type": {"type": "string", "enum": ["claim", "url", "text"], "default": "claim"},
                "domain": {"type": "string", "enum": ["compliance", "ai", "robotics", "general"], "default": "compliance"},
                "depth": {"type": "string", "enum": ["standard", "deep"], "default": "standard"},
                "candidate_sources": {
                    "type": "array", "items": {"type": "string"},
                    "description": "调用方 Agent 已检索到的候选源（可选，启用托管 LLM 时忽略）",
                },
            },
            "required": ["input"],
        },
    }
]


def _read_message(stream):
    """按 MCP stdio 规范读取一条消息：一行一条 JSON；跳过空行；EOF 返回 None。"""
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            continue
        if line.startswith(b"\xef\xbb\xbf"):  # 去 UTF-8 BOM
            line = line[3:]
        return json.loads(line.decode("utf-8"))


def _write_message(stream, msg):
    """写出一条 JSON-RPC 消息：单行 JSON + 换行（ensure_ascii=False 保留中文）。"""
    data = json.dumps(msg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


def _log(msg):
    """诊断日志只能走 stderr —— stdout 是协议专用通道。"""
    sys.stderr.write("[suyuan-trace] %s\n" % msg)
    sys.stderr.flush()


def _handle(msg, stream):
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        params = msg.get("params") or {}
        proto = params.get("protocolVersion") or PROTOCOL_VERSION
        _write_message(stream, {
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "protocolVersion": proto,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        })
        return
    if method in ("notifications/initialized", "notifications/cancelled"):
        return  # 通知不回
    if method == "ping":
        _write_message(stream, {"jsonrpc": "2.0", "id": msg_id, "result": {}})
        return
    if method == "tools/list":
        _write_message(stream, {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}})
        return
    if method == "tools/call":
        _tools_call(msg, msg_id, stream)
        return
    if msg_id is not None:
        _write_message(stream, {"jsonrpc": "2.0", "id": msg_id,
                                 "error": {"code": -32601, "message": "unknown method: %s" % method}})


def _tools_call(msg, msg_id, stream):
    params = msg.get("params", {})
    if params.get("name") != "trace":
        _write_message(stream, {"jsonrpc": "2.0", "id": msg_id,
                                 "error": {"code": -32602, "message": "unknown tool"}})
        return
    args = params.get("arguments", {})
    inp = (args.get("input") or "").strip()
    if not inp:
        _write_message(stream, {"jsonrpc": "2.0", "id": msg_id,
                                 "error": {"code": -32602, "message": "missing input"}})
        return

    input_type = args.get("input_type", "claim")
    domain = args.get("domain", "compliance")
    depth = args.get("depth", "standard")
    candidate_sources = args.get("candidate_sources") or None
    caller_judgment = args.get("caller_judgment") or None

    report = run_trace(inp, input_type, domain, depth, candidate_sources, caller_judgment)
    use_hosted = Config.LLM_PROVIDER != "mock"
    pay = charge(depth, use_hosted_llm=use_hosted)
    trace_id = "st_" + uuid.uuid4().hex[:12]
    record_call(trace_id, domain, depth, pay["billed"], "fulfilled")

    result = {
        "trace_id": trace_id,
        "status": "fulfilled",
        "query": inp,
        **report,
        "billed_amount": pay["billed"],
        "payment_mock": pay.get("mock", False),
    }
    _write_message(stream, {
        "jsonrpc": "2.0", "id": msg_id,
        "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]},
    })


def main():
    _log("started (stdio, newline-delimited JSON), pid=%d" % os.getpid())
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        try:
            msg = _read_message(stdin)
        except Exception as e:
            _log("parse error: %s" % e)
            return
        if msg is None:
            break
        try:
            _handle(msg, stdout)
        except Exception as e:  # 单条错误不退出进程
            if msg.get("id") is not None:
                _write_message(stdout, {"jsonrpc": "2.0", "id": msg.get("id"),
                                         "error": {"code": -32603, "message": str(e)}})


if __name__ == "__main__":
    main()
