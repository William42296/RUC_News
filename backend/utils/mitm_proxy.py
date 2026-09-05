"""独立 mitmproxy 脚本：拦截微信流量，自动更新 session.json 并触发抓取。

运行：mitmdump -s utils/mitm_proxy.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mitmproxy import http  # noqa: E402

from config import CRAWLER_SESSION_FILE, SESSION_COOKIE_NAME  # noqa: E402

# 兼容文档别名 ys7_ysxy_session（真实 cookie 名 ys_ysxy_sess）
_COOKIE_RE = re.compile(rf"{SESSION_COOKIE_NAME}(?:ion)?=([^;,\s]+)")

# 心跳包（keep-alive / ping）路径特征：命中则丢弃，不参与 Cookie 提取与抓取触发
_HEARTBEAT_RE = re.compile(
    r"(heartbeat|heart_beat|keepalive|keep-alive|/ping\b|/beat\b|/hb\b|/health\b)",
    re.IGNORECASE,
)

_current = None


def _is_heartbeat(url: str) -> bool:
    return bool(_HEARTBEAT_RE.search(url))


def response(flow: http.HTTPFlow):
    if _is_heartbeat(flow.request.pretty_url):
        return  # 丢弃心跳包
    global _current
    for headers in (flow.request.headers, flow.response.headers):
        if headers is None:
            continue
        cookie = headers.get("cookie") or headers.get("set-cookie")
        if not cookie:
            continue
        m = _COOKIE_RE.search(cookie)
        if m and m.group(1) != _current:
            _current = m.group(1)
            _save(_current)
            return


def _save(session):
    with open(CRAWLER_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({SESSION_COOKIE_NAME: session}, f, ensure_ascii=False)
    print("Cookie 已自动更新")
    try:
        from utils import crawler
        crawler.run()
    except Exception as e:  # 抓取失败不影响代理本身
        print(f"[mitm] 触发抓取失败: {e}")
