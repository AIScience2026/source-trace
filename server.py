"""
源溯 API — 原型 HTTP 服务（stdlib，零依赖，本机即跑）
路由：
  POST /v1/trace           阶段一·询价（轻量，不跑溯源）
  POST /v1/pay/{trace_id}  mock 模拟支付成功（生产由支付宝异步通知触发）
  GET  /v1/trace/{trace_id}阶段二·交付（支付成功后执行溯源并返回报告）
"""
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from store import auth_api_key, create_trace, get_trace, mark_paid, set_report
from alipay import create_payment
from trace_engine import run_trace


def _send(handler, code, obj):
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(handler.rfile.read(length).decode("utf-8"))
    except Exception:
        return {}


def _auth(handler):
    key = (handler.headers.get("Authorization") or "").replace("Bearer ", "").strip()
    ok, rec = auth_api_key(key)
    if not ok:
        _send(handler, 401, {"error": "invalid_api_key"})
        return None
    return key


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # 静默

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if parsed.path.rstrip("/") == "/v1/trace":
            self._post_trace(_read_json(self))
            return
        if len(parts) == 3 and parts[0] == "v1" and parts[1] == "pay":
            self._post_pay(parts[2])
            return
        _send(self, 404, {"error": "not_found"})

    def do_GET(self):
        parts = [p for p in self.path.split("/") if p]
        if len(parts) == 3 and parts[0] == "v1" and parts[1] == "trace":
            self._get_trace(parts[2])
            return
        _send(self, 404, {"error": "not_found"})

    # ---- 阶段一：询价 ----
    def _post_trace(self, body):
        key = _auth(self)
        if key is None:
            return
        inp = (body.get("input") or "").strip()
        if not inp:
            _send(self, 400, {"error": "missing_input"})
            return
        input_type = body.get("input_type", "claim")
        domain = body.get("domain", "compliance")
        depth = body.get("depth", "standard")
        if depth not in ("standard", "deep"):
            depth = "standard"
        rec = create_trace(key, inp, input_type, domain, depth)
        pay = create_payment(rec["trace_id"], rec["price"])
        rec["payment"] = pay
        _send(self, 200, {
            "trace_id": rec["trace_id"],
            "price": rec["price"],
            "status": rec["status"],
            "payment": pay,
        })

    # ---- mock 模拟支付 ----
    def _post_pay(self, trace_id):
        rec = mark_paid(trace_id)
        if not rec:
            _send(self, 404, {"error": "trace_not_found"})
            return
        _send(self, 200, {"trace_id": trace_id, "status": "paid", "billed_amount": rec["price"]})

    # ---- 阶段二：交付（支付成功后执行溯源）----
    def _get_trace(self, trace_id):
        rec = get_trace(trace_id)
        if not rec:
            _send(self, 404, {"error": "trace_not_found"})
            return
        if not rec["paid"]:
            _send(self, 402, {"trace_id": trace_id, "status": "awaiting_payment",
                               "payment": rec.get("payment")})
            return
        if rec["report"] is None:
            report = run_trace(rec["input"], rec["input_type"], rec["domain"], rec["depth"])
            set_report(trace_id, report)
            rec = get_trace(trace_id)
        _send(self, 200, {
            "trace_id": trace_id,
            "status": rec["status"],
            "query": rec["input"],
            **rec["report"],
            "billed_amount": rec["price"],
        })


def main():
    from config import Config
    srv = HTTPServer((Config.HOST, Config.PORT), Handler)
    print(f"源溯 API 原型 监听 http://{Config.HOST}:{Config.PORT}  (mock支付={Config.ALIPAY_MOCK})")
    print("试用: python demo.py")
    srv.serve_forever()


if __name__ == "__main__":
    main()
