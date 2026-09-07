# wechat-mp-pipeline

> 人设驱动的公众号内容流水线 Skill：选题 → 成文 → 去AI味质检 → 配图 → 内联样式 HTML → 微信草稿箱 API。
> 适用于 Cola / Claude Code / Codex / Cursor 等任何支持 SKILL.md 的 agent。

## 它解决什么（以及一个丑话先说）

AI 写公众号最大的破绽不是文笔，是**素材来路**：通用故事、典范案例、万能金句，读者一眼识破。
本 skill 把「人设档案（世界圣经）」立为素材宪法——文章只准引用档案里的人物、年份、物件，
落点必须是角色成长的一步而不是格言。再配五道质检闸 + 官方 API 直达草稿箱（**永不代发布**）。

> ⚠️ **档案先行**：不花一小时按 `references/persona-template.md` 建好世界圣经和选题库，
> 这个 skill 和直接喊“帮我写篇公众号”没有区别。工序是骨架，档案才是弹药。

## 快速开始

1. 把本目录放进你的 skills 目录（如 `~/.claude/skills/` 或 `~/.cola/skills/`）
2. 配置你自己的公众号凭证（**不要提交到任何仓库**）：
   ```bash
   mkdir -p ~/.config/wechat-mp-pipeline
   cp config.example.json ~/.config/wechat-mp-pipeline/config.json   # 填入 AppID/Secret
   ```
   公众号后台「设置与开发 → 基本配置」→ 把你本机公网 IP 加入白名单（`curl https://myip.ipip.net`）。
3. 对 agent 说："按 wechat-mp-pipeline 帮我搭一个公众号流水线，赛道是 XX"——它会按
   `references/persona-template.md` 建档案四件套，之后每天一句"跑今天的"即可。

## 组成

| 路径 | 作用 |
|---|---|
| `SKILL.md` | 主工序（七步）+ 异常预案 + 硬边界 |
| `references/persona-template.md` | 世界圣经/人设表七张表/选题库模板 |
| `references/quality-gates.md` | 五道质检闸细则（去AI味/结构QA/母题黑名单/知情账本/红线） |
| `scripts/wechat_publish.py` | 压缩→传图→建/改草稿（stdlib only；大图需 Pillow） |
| `scripts/wechat_data.py` | 拉运营数据（端点实测确认；未认证个人号可能 48001，见下） |
| `assets/template-ribao.html` · `template-xinjian.html` | 两套中性排版模板（观点小报体 / 暖心信笺体），替换 `{{...}}` 即用 |

## 微信的三个坑（实测踩过，先知道少踩）

1. **IP 白名单**：所有 API 报 40164 都是它；家用宽带重拨后 IP 会变，需重新加白
2. **草稿会过期**：新建的草稿放着不管可能被微信自行清理，之后 draft/update/get 全部 40007——脚本已自动降级为新建，但别把草稿箱当仓库
3. **定时即锁死**：草稿设了定时发布（53407）就无法 API 修改，要改稿先取消定时
4. **数据接口权限**：未认证个人订阅号大概率拿不到 datacube 数据（48001），用后台「数据分析」看板人工抄录即可，不影响发布链路

环境要求：Python 3.9+；Windows 用 `python` 命令（无 `python3`）；配图超 1MB 时需 `pip install pillow`。

## 安全与边界

- 凭证只存用户本地（config.json / 环境变量）；仓库永不包含 key
- 工具只写草稿箱：发布、定时、群发、改后台设置均不代办
- 微信接口错误自带提示：40164=IP 白名单，53407=草稿被定时锁定，40007=封面必须用永久素材 media_id

## License

MIT — 随便用，别拿来生成伤害人的东西。
