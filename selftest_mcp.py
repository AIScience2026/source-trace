#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""挂载前自检：模拟 MCP 宿主的行为启动 server（绝对路径 + 非项目 cwd）。

用途：确认 mcp.json 里写的那两行（python 绝对路径 + mcp_server.py 绝对路径）
在"cwd 不是 source_trace"的情况下依然能握手 + 调用成功。
挂载失败（ENOENT / ImportError）时先跑这个，能立刻定位是路径问题还是协议问题。

⚠️ 帧格式必须与 mcp_server.py 一致：MCP stdio 规范 = **换行分隔 JSON**。
   本脚本与 server 同源，属于"自家方言自测"；**独立验证**请跑
   `node official_sdk_check.mjs`（官方 MCP SDK 作为客户端）或直接用真实宿主。

用法：python selftest_mcp.py
"""
import json
import os
import subprocess
import sys

PY = sys.executable
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "mcp_server.py")
FAKE_CWD = os.environ.get("SystemDrive", "C:") + os.sep  # 用一个跟项目无关的目录当 cwd


def send(p, msg):
    """单行 JSON + 换行（MCP stdio 规范）。"""
    p.stdin.write(json.dumps(msg, ensure_ascii=False).encode("utf-8") + b"\n")
    p.stdin.flush()


def recv(p):
    """读一行 JSON，跳过空行。"""
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if line:
            return json.loads(line.decode("utf-8"))


def main():
    print("python  :", PY)
    print("server  :", SERVER, "(exists=%s)" % os.path.exists(SERVER))
    print("fake cwd:", FAKE_CWD)
    print("-" * 60)

    p = subprocess.Popen([PY, SERVER], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=FAKE_CWD)
    try:
        send(p, {"jsonrpc": "2.0", "method": "initialize", "id": 1,
                 "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                            "clientInfo": {"name": "selftest", "version": "0.1"}}})
        r = recv(p)
        if not r:
            print("[FAIL] 握手无响应。stderr:")
            print(p.stderr.read().decode("utf-8", "replace"))
            return 1
        print("[OK] initialize →", r["result"]["serverInfo"],
              "| proto:", r["result"].get("protocolVersion"))

        send(p, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        send(p, {"jsonrpc": "2.0", "method": "tools/list", "id": 2, "params": {}})
        r = recv(p)
        print("[OK] tools/list →", [t["name"] for t in r["result"]["tools"]])

        send(p, {"jsonrpc": "2.0", "method": "tools/call", "id": 3,
                 "params": {"name": "trace", "arguments": {
                     "input": "AI Act 已生效", "input_type": "claim",
                     "domain": "compliance", "depth": "standard",
                     "candidate_sources": ["https://eur-lex.europa.eu/eli/reg/2024/1689/oj"]}}})
        r = recv(p)
        o = json.loads(r["result"]["content"][0]["text"])
        print("[OK] tools/call → primary_source:", o.get("primary_source", {}).get("title"),
              "| conf:", o.get("overall_confidence"), "| billed:", o.get("billed_amount"))
        print("\n结论：可以挂载到 mcp.json（宿主这样启动没问题）。")
        return 0
    finally:
        p.terminate()


if __name__ == "__main__":
    sys.exit(main())
