"""
溯源 API (SourceTrace) — 原型配置（v4 MCP-first）
所有外部依赖（可选托管 LLM / 支付宝）均可通过环境变量切换；缺失时走 mock，保证原型零依赖可跑。
"""
import os


class Config:
    # ---- Newsylist 免费能力（白嫖，不自建聚合）----
    NEWSYLIST_TRENDS_URL = "https://www.newsylist.com/api/trends.json"
    NEWSYLIST_MATCH_MIN_OVERLAP = 1

    # ---- 可选托管 LLM 档（默认 mock；配置后启用我们后端 LLM 兜底，覆盖无强 Agent 的调用方）----
    LLM_PROVIDER = os.getenv("ST_LLM_PROVIDER", "mock")  # mock | openai_compatible
    LLM_API_KEY = os.getenv("ST_LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("ST_LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("ST_LLM_MODEL", "gpt-4o-mini")
    SEARCH_API_KEY = os.getenv("ST_SEARCH_API_KEY", "")  # 服务端检索兜底（Brave/Tavily，Bing 已停售）

    # ---- 支付宝「AI 收」（mock 默认；真实需 APPID/私钥/公网回调）----
    ALIPAY_MOCK = os.getenv("ST_ALIPAY_MOCK", "true").lower() == "true"
    ALIPAY_APP_ID = os.getenv("ST_ALIPAY_APP_ID", "")
    ALIPAY_GATEWAY = os.getenv("ST_ALIPAY_GATEWAY", "https://openapi-sandbox.dl.alipaydev.com/gateway.do")

    # ---- 定价（标准/深度；开发者沙箱免费；可选托管 LLM 档 +0.05）----
    PRICE = {"standard": 0.05, "deep": 0.10}
    HOSTED_LLM_SURCHARGE = 0.05

    # ---- 路径 ----
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BILL_FILE = os.path.join(BASE_DIR, "billing.jsonl")
