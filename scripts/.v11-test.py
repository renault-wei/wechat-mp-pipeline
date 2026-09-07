import sys, json, argparse, urllib.request
sys.path.insert(0, r'C:\Users\12230\code\wechat-mp-pipeline\scripts')
from wechat_publish import get_token, load_creds, upload_placeholder_cover, _post_json, API
from pathlib import Path
a = argparse.Namespace(appid=None, secret=None)
ap, se = load_creds(a)
t = get_token(ap, se)
mid = upload_placeholder_cover(t)
print("PLACEHOLDER COVER OK:", mid[:20], "...")
html = Path(r'C:\Users\12230\code\wechat-mp-pipeline\assets\template-ribao.html').read_text(encoding='utf-8')[:1500]
r = _post_json(API + "/draft/add?access_token=" + t, {"articles": [{"title": "v1.1\u5360\u4f4d\u5c01\u9762\u6d4b\u8bd5\uff0c\u7a0d\u540e\u5220\u9664", "author": "test", "digest": "d", "content": "<section>" + html + "</section>", "thumb_media_id": mid, "need_open_comment": 1, "only_fans_can_comment": 0}]})
print("ADD RESULT:", json.dumps(r, ensure_ascii=False))
if r.get("media_id"):
    d = _post_json(API + "/draft/delete?access_token=" + t, {"media_id": r["media_id"]})
    print("CLEANUP:", json.dumps(d, ensure_ascii=False))
