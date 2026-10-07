#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案1 演示：调用方 Agent 自带大模型做意图消歧（v4「调用方自带算力」）

核心问题：mock 引擎无语义消歧，曾把「某AI伴侣App融资新闻」这类厂商动态误命中为法规一手源。
方案1 的治本思路 = 语义判断由「调用方 Agent 自带的大模型」完成，server 只做审计+计量+收费。
  - 调用方（如 workBuddy，运行在大模型上）先判断 query 意图：regulation / other
  - 把判断作为 caller_judgment 透传给 trace 工具
  - 工具收到 other 直接诚实降级，不查 KB、不误命中

本演示用规则近似「大模型语义判断」（真实部署时由调用方 Agent 的大模型产出该字段）。
走完整 MCP 握手（新 spawn server 子进程），与真实挂载行为一致。
"""
import json
import subprocess
import sys

PY = r"C:\Users\heatonyu\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SERVER = r"D:\self-development\WorkBuddy开发者\人因工程师副业睡后收入\source_trace\mcp_server.py"


def _caller_llm_intent(query: str) -> str:
    """近似「调用方大模型」的语义意图判断。真实场景由调用方 Agent 的大模型产出。
    这里用规则演示：含厂商动态/市场类信号 → other；否则 regulation。"""
    q = query.lower()
    other_signals = ["融资", "市场", "规模", "预测", "诉讼", "新闻", "动态",
                     "进展", "股价", "估值", "营收", "发布", "上线", "融资额"]
    if any(s in q for s in other_signals):
        return "other"
    return "regulation"


def _rpc(p, method, params=None, msg_id=1):
    req = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        req["params"] = params
    p.stdin.write((json.dumps(req) + "\n").encode("utf-8"))
    p.stdin.flush()
    # 读取一行（换行分隔 JSON）
    line = p.stdout.readline()
    return json.loads(line.decode("utf-8"))


def main():
    p = subprocess.Popen([PY, SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=False)
    _rpc(p, "initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {}, "clientInfo": {"name": "demo-caller", "version": "1.0"}})
    _rpc(p, "notifications/initialized", {}, msg_id=None) if False else None
    # initialized 通知
    p.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n").encode("utf-8"))
    p.stdin.flush()

    queries = [
        "某AI伴侣App 2026年8月融资新闻",          # 原 FABRICATED：厂商动态
        "AI伴侣行业市场规模预测 2030",            # 原 FABRICATED：市场预测
        "AI伴侣机器人合规要求",                    # 正例：法规诉求
        "人工智能拟人化互动服务管理暂行办法",       # 正例：全称
    ]

    print("=" * 70)
    print("方案1 演示：调用方 Agent（大模型）意图消歧 → trace 工具 caller_judgment")
    print("=" * 70)
    for q in queries:
        intent = _caller_llm_intent(q)
        resp = _rpc(p, "tools/call", {
            "name": "trace",
            "arguments": {"input": q, "input_type": "claim", "domain": "compliance",
                          "depth": "standard", "caller_judgment": intent},
        })
        res = json.loads(resp["result"]["content"][0]["text"])
        ps = res.get("primary_source")
        verdict = f"诚实降级(null)" if ps is None else f"命中 {ps['url']}"
        print(f"\n查询 : {q}")
        print(f"  ├─ 调用方(大模型)判断 : {intent}")
        print(f"  └─ trace 结果         : {verdict}")
        print(f"      计费 ¥{res['billed_amount']}  | 备注: {res.get('degradation_note') or '法规一手源命中'}")
    p.terminate()
    print("\n" + "=" * 70)
    print("结论：调用方大模型做语义判断(other)后，工具不再误命中厂商动态；")
    print("      这正是 v4「调用方自带算力」治本路径——server 不必自己跑 LLM。")
    print("=" * 70)


if __name__ == "__main__":
    main()
