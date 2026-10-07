"""
源溯 API — Newsylist 免费能力客户端
白嫖 Newsylist 的 trends.json（机器可读、免费署名即可），
仅做"媒体侧首发"增强；匹配不上则优雅降级（不阻断主溯源）。
"""
import json
import urllib.request

from config import Config


def _fetch_trends():
    try:
        req = urllib.request.Request(
            Config.NEWSYLIST_TRENDS_URL,
            headers={"User-Agent": "SourceTrace-Prototype/0.1"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # 网络失败/限流 → 优雅降级
        return {"_error": str(e)}


def enrich_media_first_report(query: str, data=None):
    """
    返回 {"available", "matched", "via", "confidence", "note"}
    匹配策略：query 实词与 trends 文本做模糊重叠；匹配不上 → available=True 但 matched=False。
    """
    if data is None:
        data = _fetch_trends()

    if "_error" in data:
        return {
            "available": False,
            "matched": False,
            "via": "newsylist",
            "confidence": 0.0,
            "note": f"Newsylist 抓取失败，已降级跳过媒体首发增强：{data['_error']}",
        }

    # 简易实词提取（中文按字符 n-gram 太噪，这里用ascii词+去停用）
    keywords = [w for w in query.lower().split() if len(w) > 3]
    blob = json.dumps(data, ensure_ascii=False).lower()

    matched = False
    for kw in keywords:
        if kw in blob:
            matched = True
            break

    if matched:
        return {
            "available": True,
            "matched": True,
            "via": "newsylist",
            "confidence": 0.6,
            "note": "Newsylist 命中相关趋势，可取其 newsroom leaderboard 做媒体首发增强（原型期仅标记匹配）",
        }
    return {
        "available": True,
        "matched": False,
        "via": "newsylist",
        "confidence": 0.0,
        "note": "Newsylist 无匹配趋势，跳过媒体首发增强（不影响主溯源）",
    }
