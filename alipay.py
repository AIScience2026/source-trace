"""
溯源 API — 支付宝「AI 收」计费层（v4 MCP-first）
MCP 形态下无法中途弹窗支付，收费改为「A2A 预授权/余额/交易凭证自动结算」：
调用方 Agent 已在 A2A 协议层完成支付并携带交易凭证调用 trace，本层校验凭证后履约。
mock 模式：记 billed 金额、不接真钱，跑通全链路。
参考：https://a2a.alipay.com/merchant-guide
"""
from config import Config


def charge(depth: str, use_hosted_llm: bool = False) -> dict:
    """每次成功 trace 计一次费。返回 {billed, mock, note}。"""
    amount = Config.PRICE.get(depth, Config.PRICE["standard"])
    if use_hosted_llm:
        amount += Config.HOSTED_LLM_SURCHARGE

    if Config.ALIPAY_MOCK:
        return {
            "billed": amount,
            "mock": True,
            "note": "mock 计费（本地）；真实环境经支付宝「AI 收」A2A 自动结算",
        }

    # —— 生产接入点（待你提供 APPID + 应用私钥 + 公网回调后启用）——
    # 1) 校验调用方 Agent 带来的 A2A 交易凭证（transcation_voucher）：金额 + app_id + trace_id 验签
    # 2) 通过则履约（返回溯源报告）；失败抛错不计费
    # 3) 异步 notify_url 验签回写账单（verify_notify）
    raise NotImplementedError(
        "生产支付需 ST_ALIPAY_APP_ID / 应用私钥 + A2A 交易凭证校验；当前为 mock"
    )


def verify_notify(params: dict) -> bool:
    """异步通知验签（生产用）。mock 恒 True。"""
    if Config.ALIPAY_MOCK:
        return True
    raise NotImplementedError("生产验签需支付宝公钥配置")
