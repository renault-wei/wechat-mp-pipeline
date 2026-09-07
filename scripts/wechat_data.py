#!/usr/bin/env python3
"""wechat_data.py — 拉取公众号图文运营数据，输出 JSON。

注意权限门槛：datacube 系列接口对未认证个人订阅号可能返回 48001（api unauthorized）。
遇 48001 属账号类型限制，不是本脚本 bug——请改用公众号后台「数据分析」看板人工抄录，
或完成微信认证后重试。

端点（无 /cgi-bin 前缀，实测确认）：
  getarticlesummary  图文群发每日数据
  getarticletotal    图文群发总数据（官方已停维，新号可能无数据）
  getarticleread     发表内容每日阅读（新接口）
凭证解析同 wechat_publish.py。示例（Windows 用 python）：
  python3 wechat_data.py --since 2026-09-06
  python3 wechat_data.py --since 2026-09-01 --until 2026-09-07 --api getarticletotal
"""
import argparse, json, sys, urllib.request
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from wechat_publish import get_token, load_creds, die  # noqa: E402

BASE = "https://api.weixin.qq.com/datacube"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--since", default=str(date.today() - timedelta(days=1)))
    p.add_argument("--until", default=None)
    p.add_argument("--api", default="getarticlesummary",
                   choices=["getarticlesummary", "getarticletotal", "getarticleread"])
    p.add_argument("--appid")
    p.add_argument("--secret")
    a = p.parse_args()
    appid, secret = load_creds(a)
    token = get_token(appid, secret)
    body = json.dumps({"begin_date": a.since, "end_date": a.until or a.since}).encode()
    req = urllib.request.Request(f"{BASE}/{a.api}?access_token={token}", data=body,
                                 headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    if r.get("errcode", 0) != 0:
        hint = {48001: "-> 账号无此 API 权限（未认证个人订阅号常见）：改用后台「数据分析」看板",
                40164: "-> 本机 IP 不在白名单"}.get(r["errcode"], "")
        die("数据拉取失败：" + str(r) + " " + hint)
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
