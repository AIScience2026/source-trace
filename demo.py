#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""溯源 API — MCP client demo（stdlib，零依赖）

两种用法：
  1) 跑内置 4 案例：      python demo.py
  2) 试你自己的句子：      python demo.py --input "你的说法或URL"

第 2 种会打印**完整审计 JSON**（一手源 + 时间线 + 污染链 + 媒体首发 + 计费）。

原理：启动 mcp_server.py 子进程，走完整 MCP 握手（initialize → initialized → tools/list），
再调用 trace 工具，验证全链路。

⚠️ 帧格式：按 MCP stdio 规范用**换行分隔 JSON**（不是 LSP 的 Content-Length 帧）。
   注意本脚本与 mcp_server.py 同源，属于"自家方言自测"；要独立验证请用 `python selftest_official_sdk.py`
   或官方 MCP SDK / 真实 MCP 宿主，避免自证循环。
"""
import argparse
import json
import os
import subprocess
import sys

SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")
PY = sys.executable


def _start():
    return subprocess.Popen([PY, SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def _send(p, msg):
    """发一条 JSON-RPC 消息：单行 JSON + 换行（MCP stdio 规范）。"""
    p.stdin.write(json.dumps(msg, ensure_ascii=False).encode("utf-8") + b"\n")
    p.stdin.flush()


def _recv(p):
    """读一条消息：读一行 JSON，跳过空行。"""
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if line:
            return json.loads(line.decode("utf-8"))


def _call(p, method, params=None, msg_id=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if msg_id is not None:
        msg["id"] = msg_id
    _send(p, msg)
    return _recv(p)


def _handshake(p):
    r = _call(p, "initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "suyuan-demo", "version": "0.1"},
    }, msg_id=1)
    print("initialize → serverInfo:", r.get("result", {}).get("serverInfo"))
    _send(p, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    r = _call(p, "tools/list", {}, msg_id=2)
    print("tools/list →", [t["name"] for t in r.get("result", {}).get("tools", [])])


def _trace(p, args, msg_id):
    r = _call(p, "tools/call", {"name": "trace", "arguments": args}, msg_id=msg_id)
    res = r.get("result", {}) or {}
    text = (res.get("content") or [{}])[0].get("text")
    if not text:
        return None, r.get("error")
    return json.loads(text), None


BUILTIN_CASES = [
    ("案例A·合规命中(KB)", {"input": "中国拟出台人工智能拟人化互动服务管理暂行办法",
                            "input_type": "claim", "domain": "compliance", "depth": "deep"}),
    ("案例B·无源降级", {"input": "据说某科技公司下周要发布新机器人",
                        "input_type": "claim", "domain": "robotics", "depth": "standard"}),
    ("案例C·URL输入", {"input": "https://www.cac.gov.cn/2026/notice.pdf",
                       "input_type": "url", "domain": "compliance", "depth": "standard"}),
    ("案例D·调用方候选源", {"input": "AI Act 已生效", "input_type": "claim", "domain": "compliance",
                            "depth": "standard",
                            "candidate_sources": ["https://eur-lex.europa.eu/eli/reg/2024/1689/oj"]}),
]


def main():
    ap = argparse.ArgumentParser(description="溯源 API — MCP client 试跑")
    ap.add_argument("--input", "-i", help="要溯源的句子 / URL / 新闻文本（给了就跑单案例）")
    ap.add_argument("--type", default="claim", choices=["claim", "url", "text"], help="输入类型")
    ap.add_argument("--domain", default="compliance",
                    choices=["compliance", "ai", "robotics", "general"], help="垂直领域")
    ap.add_argument("--depth", default="standard", choices=["standard", "deep"], help="深度（deep=¥0.10）")
    ap.add_argument("--candidate", action="append", help="调用方已检索到的候选源 URL（可多次）")
    a = ap.parse_args()

    p = _start()
    try:
        _handshake(p)

        if a.input:
            args = {"input": a.input, "input_type": a.type, "domain": a.domain, "depth": a.depth}
            if a.candidate:
                args["candidate_sources"] = a.candidate
            print("\n=== 你的输入 ===")
            print("参数:", json.dumps(args, ensure_ascii=False))
            out, err = _trace(p, args, 10)
            print("\n--- 完整审计 JSON ---")
            print(json.dumps(out if out else {"error": err}, ensure_ascii=False, indent=2))
        else:
            for i, (label, args) in enumerate(BUILTIN_CASES):
                out, err = _trace(p, args, 10 + i)
                print("\n=== %s ===" % label)
                if out:
                    print(json.dumps({
                        "trace_id": out.get("trace_id"),
                        "primary_source": out.get("primary_source"),
                        "overall_confidence": out.get("overall_confidence"),
                        "degradation_note": out.get("degradation_note"),
                        "media_note": (out.get("media_first_report") or {}).get("note"),
                        "billed_amount": out.get("billed_amount"),
                    }, ensure_ascii=False, indent=2))
                else:
                    print("error:", err)
            print("\n提示：想试自己的句子 → python demo.py --input \"你的说法\"")
    finally:
        p.terminate()


if __name__ == "__main__":
    main()
