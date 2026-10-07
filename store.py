"""
溯源 API — 账单存储（v4 MCP-first）
MCP 形态下每次成功 trace 同步记一条调用 + billed 金额（落盘 JSONL，便于看调用量与收入）。
生产换 DB/支付宝异步通知回写即可。
"""
import json
import threading

from config import Config

_lock = threading.Lock()


def record_call(trace_id: str, domain: str, depth: str, billed: float, status: str) -> dict:
    rec = {
        "trace_id": trace_id,
        "domain": domain,
        "depth": depth,
        "billed": billed,
        "status": status,
    }
    try:
        with _lock:
            with open(Config.BILL_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def total_calls() -> int:
    try:
        with open(Config.BILL_FILE, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0
