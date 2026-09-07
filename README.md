# wechat-mp-pipeline

> 人设驱动的公众号内容流水线 Skill：选题 → 成文 → 去AI味质检 → 配图 → 内联样式 HTML → 微信草稿箱 API。
> 适用于 Cola / Claude Code / Codex / Cursor 等任何支持 SKILL.md 的 agent。

## 它解决什么

AI 写公众号最大的破绽不是文笔，是**素材来路**：通用故事、典范案例、万能金句，读者一眼识破。
本 skill 把「人设档案（世界圣经）」立为素材宪法——文章只准引用档案里的人物、年份、物件，
落点必须是角色成长的一步而不是格言。再配五道质检闸 + 官方 API 直达草稿箱（**永不代发布**）。

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
| `scripts/wechat_publish.py` | 压缩→传图→建/改草稿（stdlib only；Pillow 可选） |
| `scripts/wechat_data.py` | 拉运营数据（端点以微信官方文档为准，首用请核对） |

## 安全与边界

- 凭证只存用户本地（config.json / 环境变量）；仓库永不包含 key
- 工具只写草稿箱：发布、定时、群发、改后台设置均不代办
- 微信接口错误自带提示：40164=IP 白名单，53407=草稿被定时锁定，40007=封面必须用永久素材 media_id

## License

MIT — 随便用，别拿来生成伤害人的东西。
