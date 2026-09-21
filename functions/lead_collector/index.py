# -*- coding: utf-8 -*-
"""
SourceTrace 邮箱收集函数 v2（SMTP 转发版）

相比 v1（OBS 版）的优势：
- 零第三方依赖：只用 Python 标准库 smtplib，不用装 esdk-obs-python
- 零基础设施：不用建 OBS 桶、不用拿 AK/SK、不用担心欠费删数据
- 每条订阅实时发一封邮件到你自己的邮箱 —— 收件箱就是数据库

华为云 FunctionGraph 部署：
- 运行时：Python 3.9
- 处理程序：index.handler
- 触发器：APIG → POST /v1/leads

环境变量（控制台配置，共 4 个）：
  SMTP_USER        必填  发件邮箱（例如你的 QQ 邮箱）
  SMTP_PASS        必填  邮箱授权码（不是登录密码！QQ 邮箱里单独生成）
  LEAD_TO          可选  收件地址，默认同 SMTP_USER。填 agent 邮箱即"转发到 agent 邮箱"
  ALLOWED_ORIGINS  可选  允许跨域的来源，默认 *；上线后建议收紧为落地页域名
  SMTP_HOST/PORT   可选  默认 smtp.qq.com / 465，用别的邮箱服务時改
"""

import json
import os
import re
import smtplib
from datetime import datetime, timezone, timedelta
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

CST = timezone(timedelta(hours=8))  # 北京时间

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


# ============ 工具函数 ============

def _header(event: dict, name: str) -> str:
    """大小写不敏感地取 header"""
    headers = event.get("headers") or {}
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v or ""
    return ""


def _cors_headers(origin: str) -> dict:
    """构造 CORS 响应头"""
    allowed = os.environ.get("ALLOWED_ORIGINS", "*")
    if allowed == "*" or (origin and origin in allowed.split(",")):
        allow_origin = origin or "*"
    else:
        allow_origin = allowed.split(",")[0]
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
    }


def _is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def _client_ip(event: dict) -> str:
    xff = _header(event, "X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return _header(event, "X-Real-IP") or event.get("requestContext", {}).get("sourceIp", "unknown")


# ============ 核心：发邮件 ============

def _send_lead_email(record: dict) -> None:
    """
    把订阅记录发一封邮件到 LEAD_TO。
    发信失败会抛异常，由上层转成 500 —— 宁可让用户看到提交失败，
    也不要谎报"已订阅"却什么都没留下。
    """
    smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    lead_to = os.environ.get("LEAD_TO") or smtp_user

    missing = [k for k, v in {
        "SMTP_USER": smtp_user, "SMTP_PASS": smtp_pass, "LEAD_TO": lead_to
    }.items() if not v]
    if missing:
        raise RuntimeError(f"missing env vars: {','.join(missing)}")

    subject = f"[SourceTrace] 新订阅：{record['email']}"
    body = "\n".join([
        "SourceTrace 落地页新订阅",
        "",
        f"邮箱：{record['email']}",
        f"时间：{record['ts']}（北京时间）",
        f"IP：{record['ip']}",
        f"UA：{record['ua']}",
        f"来源：{record['referrer'] or '-'}",
        f"请求ID：{record['request_id']}",
    ])

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr(("SourceTrace", smtp_user))
    msg["To"] = formataddr(("Owner", lead_to))
    msg["Date"] = formatdate(localtime=True)

    # 465 走 SSL，587 走 STARTTLS
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
        server.starttls()

    try:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [lead_to], msg.as_string())
    finally:
        try:
            server.quit()
        except Exception:
            pass


# ============ 主入口 ============

def handler(event, context):
    """
    FunctionGraph 入口。
    APIG proxy 模式下：原始 body 在 event["body"]（JSON 字符串），需二次解析。
    """
    origin = _header(event, "Origin")

    # 浏览器预检
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 204, "headers": _cors_headers(origin), "body": ""}

    try:
        # --- 解析 body ---
        body_raw = event.get("body", "")
        if isinstance(body_raw, str):
            body = json.loads(body_raw or "{}")
        else:
            body = body_raw or {}

        email = (body.get("email") or "").strip().lower()

        # --- 校验 ---
        if not email or not _is_valid_email(email):
            return {
                "statusCode": 400,
                "headers": {**_cors_headers(origin), "Content-Type": "application/json"},
                "body": json.dumps({"ok": False, "error": "invalid_email"}, ensure_ascii=False),
            }

        # --- 构造记录 ---
        record = {
            "ts": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
            "email": email,
            "ip": _client_ip(event),
            "ua": _header(event, "User-Agent"),
            "referrer": _header(event, "Referer"),
            "request_id": datetime.now(CST).strftime("%H%M%S") + "-" + email.split("@")[0][:8],
        }

        # --- 发邮件 ---
        _send_lead_email(record)

        # 邮件发出后，日志里也留一份（LTS 可查 7 天，作最后兜底）
        print(f"[lead] subscribed: {json.dumps(record, ensure_ascii=False)}")

        return {
            "statusCode": 200,
            "headers": {**_cors_headers(origin), "Content-Type": "application/json"},
            "body": json.dumps({
                "ok": True,
                "message": "subscribed",
                "request_id": record["request_id"],
            }, ensure_ascii=False),
        }

    except Exception as e:
        # 错误也带 CORS，否则浏览器读不到错误信息
        print(f"[lead] ERROR: {e!r}")
        return {
            "statusCode": 500,
            "headers": {**_cors_headers(origin), "Content-Type": "application/json"},
            "body": json.dumps({
                "ok": False,
                "error": "internal_error",
                "detail": str(e),
            }, ensure_ascii=False),
        }
