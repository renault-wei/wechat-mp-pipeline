#!/usr/bin/env python3
"""wechat_data.py — 拉取公众号图文运营数据（getarticledaily 等），输出 JSON/表格。
凭证解析同 wechat_publish.py。示例：
  python3 wechat_data.py --since 2026-09-06            # 图文群发每日数据
  python3 wechat_data.py --since 2026-09-01 --until 2026-09-07 --cumulate
"""
import argparse, json, os, sys, urllib.request
from datetime import date, timedelta
from pathlib import Path

API = "https://api.weixin.qq.com/cgi-bin"
sys.path.insert(0, str(Path(__file__).parent))
from wechat_publish import get_token, load_creds, _post_json, die  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--since", default=str(date.today() - timedelta(days=1)))
    p.add_argument("--until", default=None)
    p.add_argument("--cumulate", action="store_true", help="拉图文总数据(累计阅读)而非每日")
    p.add_argument("--appid"), p.add_argument("--secret")
    a = p.parse_args()
    appid, secret = load_creds(a)
    token = get_token(appid, secret)
    api = "getarticletotal" if a.cumulate else "getarticledetail"
    body = {"begin_date": a.since, "end_date": a.until or a.since}
    r = _post_json(f"{API}/datacube/{api}?access_token={token}", body)
    if r.get("errcode", 0) != 0 and "list" not in r:
        die(f"数据拉取失败：{r}")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
