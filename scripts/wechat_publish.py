#!/usr/bin/env python3
"""wechat_publish.py — 推送图文到微信公众号草稿箱（只建/改草稿，绝不发布、绝不设定时）。

凭证解析顺序：--appid/--secret > 环境变量 WECHAT_MP_APPID/WECHAT_MP_SECRET
             > ~/.config/wechat-mp-pipeline/config.json
已有 token 可直接设环境变量 WECHAT_MP_ACCESS_TOKEN（跳过换取，适合 CI）。

用法示例：
  python3 wechat_publish.py --html article.html --title "标题" --author 半糖姐 \
      --digest "一行摘要" --cover cover.png \
      --map "assets/a.png=a.png" --map "assets/b.png=b.png"
  # --map 左边是 HTML 里的 <img src> 相对路径，右边是本地文件；自动上传并替换
  # 更新既有草稿：追加 --media-id <draft media_id>
仅标准库；有 Pillow 时自动压缩大图（长边<=1400, jpeg q85），无 Pillow 则原样上传
（微信正文图限制 1MB，超限会报错并提示）。
"""
import argparse, json, os, re, sys, time, urllib.request
from pathlib import Path

API = "https://api.weixin.qq.com/cgi-bin"
CONF_DIR = Path(os.path.expanduser("~/.config/wechat-mp-pipeline"))
TOKEN_CACHE = CONF_DIR / ".token.json"


def load_creds(args):
    appid = args.appid or os.getenv("WECHAT_MP_APPID")
    secret = args.secret or os.getenv("WECHAT_MP_SECRET")
    cfg = CONF_DIR / "config.json"
    if (not appid or not secret) and cfg.exists():
        j = json.loads(cfg.read_text(encoding="utf-8-sig"))
        appid = appid or j.get("appid")
        secret = secret or j.get("secret")
    return appid, secret


def get_token(appid, secret, force=False):
    if os.getenv("WECHAT_MP_ACCESS_TOKEN") and not force:
        return os.environ["WECHAT_MP_ACCESS_TOKEN"]
    if TOKEN_CACHE.exists() and not force:
        try:
            c = json.loads(TOKEN_CACHE.read_text(encoding="utf-8-sig"))
            if c.get("appid") == appid and c.get("expires_at", 0) > time.time() + 60:
                return c["token"]
        except Exception:
            pass
    u = f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}"
    j = json.loads(_raw(u))
    if "access_token" not in j:
        die("token 获取失败：" + str(j) + "（40164=本机IP不在白名单，去公众号后台基本配置添加）")
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE.write_text(json.dumps({"appid": appid, "token": j["access_token"],
                                       "expires_at": time.time() + j.get("expires_in", 7200) - 300}))
    return j["access_token"]


def _raw(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def _post_json(url, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return json.loads(_raw(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"}))


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def shrink(path: Path) -> Path:
    """Pillow 可用则压缩为 jpg；否则原样返回（超 1MB 会要求装 Pillow）。"""
    if path.stat().st_size <= 950_000 and path.suffix.lower() in (".jpg", ".jpeg"):
        return path
    try:
        from PIL import Image
    except ImportError:
        if path.stat().st_size > 1_000_000:
            die(str(path) + " 超过 1MB 且未安装 Pillow（pip install pillow 可自动压缩）")
        return path
    from PIL import Image
    im = Image.open(path)
    im.thumbnail((1400, 1400))
    out = path.with_name(path.stem + ".pipeline.jpg")
    im.convert("RGB").save(out, "JPEG", quality=85)
    return out


def multipart(path: Path, field="media"):
    import uuid
    boundary = uuid.uuid4().hex
    head = ('--' + boundary + '\r\nContent-Disposition: form-data; name="' + field +
            '"; filename="' + path.name + '"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
    body = head + path.read_bytes() + ('\r\n--' + boundary + '--\r\n').encode()
    return body, {"Content-Type": "multipart/form-data; boundary=" + boundary}


def upload_permanent(token, path):
    """封面：永久素材，返回 media_id。"""
    body, hdr = multipart(shrink(Path(path)))
    j = json.loads(_raw(API + "/material/add_material?access_token=" + token + "&type=image",
                        data=body, headers=hdr))
    if "media_id" not in j:
        die("封面上传失败：" + str(j))
    return j["media_id"], j.get("url", "")


def upload_inline(token, path):
    """正文图：uploadimg，返回正文可用 URL（限 1MB）。"""
    body, hdr = multipart(shrink(Path(path)))
    j = json.loads(_raw(API + "/media/uploadimg?access_token=" + token, data=body, headers=hdr))
    if "url" not in j:
        die("正文图上传失败 " + str(path) + "：" + str(j))
    return j["url"]


def main():
    p = argparse.ArgumentParser(description="推送草稿到微信公众号（不发布不定时）")
    p.add_argument("--html", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--author", default="")
    p.add_argument("--digest", default="")
    p.add_argument("--cover", help="封面图本地路径（自动上传为永久素材做 thumb_media_id）")
    p.add_argument("--map", action="append", default=[], help="相对路径=本地文件，可多次")
    p.add_argument("--source-url", default="")
    p.add_argument("--media-id", help="给定时更新该草稿而非新建")
    p.add_argument("--appid")
    p.add_argument("--secret")
    args = p.parse_args()

    appid, secret = load_creds(args)
    if not os.getenv("WECHAT_MP_ACCESS_TOKEN") and not (appid and secret):
        die("缺少凭证：设 WECHAT_MP_APPID/SECRET 环境变量、--appid/--secret、"
            "或写 ~/.config/wechat-mp-pipeline/config.json")
    token = get_token(appid, secret)

    html = Path(args.html).read_text(encoding="utf-8-sig")
    for pair in args.map:
        rel, local = pair.split("=", 1)
        url = upload_inline(token, local)
        html = html.replace('src="' + rel + '"', 'src="' + url + '"')
        print("[map] " + rel + " -> ok")
    leftovers = re.findall(r'src="(?!http)[^"]+"', html)
    if leftovers:
        print("WARN 仍有未上传的本地图片引用：" + str(leftovers[:3]) + "（微信正文不能显示本地图）")

    art = {"title": args.title, "author": args.author, "digest": args.digest,
           "content": html, "content_source_url": args.source_url,
           "need_open_comment": 1, "only_fans_can_comment": 0}
    if args.cover:
        mid, _ = upload_permanent(token, args.cover)
        art["thumb_media_id"] = mid
        print("[cover] thumb_media_id ok")
    elif not args.media_id:
        die("新建草稿必须提供 --cover（微信草稿接口要求 thumb_media_id）")

    if args.media_id:
        art["media_id"] = args.media_id
        url, payload = API + "/draft/update?access_token=" + token, art
    else:
        url, payload = API + "/draft/add?access_token=" + token, {"articles": [art]}
    r = _post_json(url, payload)

    if r.get("errcode") == 40001 and not os.getenv("WECHAT_MP_ACCESS_TOKEN"):  # token 过期重试一次
        token = get_token(appid, secret, force=True)
        url = (API + "/draft/update?access_token=" + token) if args.media_id else (API + "/draft/add?access_token=" + token)
        r = _post_json(url, payload)

    if r.get("errcode", 0) != 0:
        if args.media_id and r.get("errcode") in (40003, 40007, 45166):
            # 实测：草稿可能已被清理或结构不兼容 update；降级为新建草稿，旧条交由用户处理
            print("WARN 草稿不可更新（" + str(r) + "），改走新建草稿")
            art.pop("media_id", None)
            if "thumb_media_id" not in art:
                die("新建需封面：追加 --cover")
            r = _post_json(API + "/draft/add?access_token=" + token, {"articles": [art]})
    if r.get("errcode", 0) != 0:
        hint = {40164: "-> 更新后台 IP 白名单",
                53407: "-> 该草稿已设定时发布被锁定；请先在后台取消定时",
                40007: "-> thumb_media_id 无效，必须来自永久素材接口"}.get(r.get("errcode"), "")
        die("草稿操作失败：" + str(r) + " " + hint)
    print("DRAFT OK: " + json.dumps(r, ensure_ascii=False))
    print("提示：发布/定时请在公众号后台人工操作，本工具不代劳。")


if __name__ == "__main__":
    main()
