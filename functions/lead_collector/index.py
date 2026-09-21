# -*- coding: utf-8 -*-
"""
SourceTrace 邮箱收集函数（华为云 FunctionGraph）

部署信息：
- 函数类型：Python 3.9（或更高）
- 处理程序：index.handler
- 触发器：APIG（API 网关）POST /v1/leads
- CORS：已在代码内置处理

功能：接收邮箱，写入 OBS 对象存储的 JSONL 文件，返回无跳转成功响应

环境变量（在 FunctionGraph 控制台配置）：
  LEADS_OBS_BUCKET        必填  OBS 桶名，例如 source-trace-leads
  LEADS_TABLE             可选  RDS 表名（预留，当前未用）
  ALLOWED_ORIGINS         可选  允许的跨域来源，逗号分隔；默认 * （上线后建议收紧为 https://aiscience2026.github.io）

写入的数据每条包含：ts, email, ip, ua, referrer
文件路径：leads/{yyyy-mm-dd}.jsonl （按天追加，最多同时读一天一行）
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone, timedelta

# ============ 常量 ============
CST = timezone(timedelta(hours=8))  # 北京时间

# ============ OBS 写入（用华为云官方 SDK） ============
def _get_obs_client():
    """懒加载 OBS client，避免未配置时报错影响其他逻辑"""
    from obs import ObsClient

    ak = os.environ.get("OBS_AK") or os.environ.get("HUAWEICLOUD_SDK_AK")
    sk = os.environ.get("OBS_SK") or os.environ.get("HUAWEICLOUD_SDK_SK")
    endpoint = os.environ.get("OBS_ENDPOINT")

    if not all([ak, sk, endpoint]):
        raise RuntimeError("OBS credentials missing (set OBS_AK / OBS_SK / OBS_ENDPOINT)")

    return ObsClient(ak, sk, endpoint)


def _sanitize_email(email: str) -> str:
    """基本清洗：去空格、转小写"""
    return email.strip().lower()


def _is_valid_email(email: str) -> bool:
    """宽松的邮箱格式校验（够用就好，真正校验交给确认邮件）"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def _get_client_ip(event: dict) -> str:
    """从 APIG 事件里取客户端 IP"""
    headers = event.get("headers", {}) or {}
    # APIG 可能转发 X-Forwarded-For
    xff = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return event.get("requestContext", {}).get("sourceIp", "unknown")


def _cors_headers(origin: str) -> dict:
    """构造 CORS 响应头"""
    allowed = os.environ.get("ALLOWED_ORIGINS", "*")
    if allowed == "*" or origin in allowed.split(","):
        allow_origin = origin or "*"
    else:
        allow_origin = allowed.split(",")[0]
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
    }


def _append_to_obs(bucket: str, key: str, line: str) -> None:
    """追加一行到 OBS 文件（读-改-写，适合低并发）"""
    client = _get_obs_client()

    existing = ""
    try:
        resp = client.getObject(bucket, key)
        if resp.status < 300:
            # 流式读取，逐块拼字符串（文件很小，<100KB）
            body = b""
            while True:
                chunk = resp.body.read(65536)
                if not chunk:
                    break
                body += chunk
            existing = body.decode("utf-8")
    except Exception as e:
        # 文件不存在是正常的，其他异常先放行，写入时会暴露
        if "NoSuchKey" not in str(e) and "404" not in str(e):
            raise

    new_content = existing + line + "\n"
    client.putObject(bucket, key, content=new_content.encode("utf-8"))


# ============ 主处理函数 ============
def handler(event, context):
    """
    FunctionGraph 入口
    event: APIG 触发时为 JSON body 解析后的 dict（含 body 字段为原始 JSON 字符串）
    """
    try:
        # --- 解析请求体 ---
        # APIG proxy 模式下，原始 body 在 event["body"]，需要 json.loads
        body_raw = event.get("body", "")
        if isinstance(body_raw, str):
            body = json.loads(body_raw or "{}")
        else:
            body = body_raw or {}

        email = _sanitize_email(body.get("email", ""))
        origin = event.get("headers", {}).get("Origin", "") or event.get("headers", {}).get("origin", "")

        # --- 预检请求（OPTIONS）---
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": 204,
                "headers": _cors_headers(origin),
                "body": ""
            }

        # --- 参数校验 ---
        if not email or not _is_valid_email(email):
            return {
                "statusCode": 400,
                "headers": {**_cors_headers(origin), "Content-Type": "application/json"},
                "body": json.dumps({
                    "ok": False,
                    "error": "invalid_email"
                }, ensure_ascii=False)
            }

        # --- 构造记录 ---
        record = {
            "ts": datetime.now(CST).isoformat(),
            "email": email,
            "ip": _get_client_ip(event),
            "ua": event.get("headers", {}).get("User-Agent", ""),
            "referrer": event.get("headers", {}).get("Referer", ""),
            "request_id": str(uuid.uuid4())[:8],
        }

        # --- 写入 OBS ---
        bucket = os.environ.get("LEADS_OBS_BUCKET")
        if not bucket:
            raise RuntimeError("LEADS_OBS_BUCKET not set")

        today = datetime.now(CST).strftime("%Y-%m-%d")
        key = f"leads/{today}.jsonl"
        _append_to_obs(bucket, key, json.dumps(record, ensure_ascii=False))

        # --- 成功响应 ---
        return {
            "statusCode": 200,
            "headers": {**_cors_headers(origin), "Content-Type": "application/json"},
            "body": json.dumps({
                "ok": True,
                "message": "subscribed",
                "request_id": record["request_id"]
            }, ensure_ascii=False)
        }

    except Exception as e:
        # 错误也返回 CORS，否则浏览器读不到错误信息
        origin = event.get("headers", {}).get("Origin", "")
        return {
            "statusCode": 500,
            "headers": {**_cors_headers(origin), "Content-Type": "application/json"},
            "body": json.dumps({
                "ok": False,
                "error": "internal_error",
                "detail": str(e)
            }, ensure_ascii=False)
        }
