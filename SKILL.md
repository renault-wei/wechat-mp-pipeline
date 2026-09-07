---
name: wechat-mp-pipeline
description: |
  人设驱动的公众号内容流水线：从选题库取题 → 按人设档案成文 → 去AI味质检链 → 章节配图 → 公众号专用内联样式 HTML → 通过微信公众平台官方 API 一键推送到草稿箱（不自动发布）。
  Use when the user wants to run a daily WeChat Official Account article pipeline, push an article/draft to 微信公众号草稿箱, set up a persona-driven 公众号 content workflow, upload 配图 to WeChat, mentions 公众号/草稿箱/微信推文/publish draft/wechat mp, or wants to build a 选题库/人设档案/母题黑名单 for a content account.
metadata:
  author: weiwei (renault-wei)
  license: MIT
  requires: "Python 3.9+ (stdlib only) for scripts; user's own 公众号 AppID/AppSecret"
---

# WeChat MP Pipeline — 人设驱动的公众号流水线

一条把「选题 → 文章 → 配图 → 排版 → 草稿箱」串成固定工序的生产线。核心思想：**文章素材来自一份持续维护的人设档案（世界圣经），而不是临时编造**——这从根上消除 AI 味的通用鸡汤；发布只到草稿箱为止，封面/定时/发布永远留给人。

## 0. 首次使用：配置凭证（自定义 API key）

凭证绝不写进本 skill 仓库。二选一：

```bash
# 方式 A：配置文件（推荐）
mkdir -p ~/.config/wechat-mp-pipeline
cp config.example.json ~/.config/wechat-mp-pipeline/config.json
# 编辑：{"appid": "wx开头你的AppID", "secret": "你的AppSecret"}

# 方式 B：环境变量（适合临时/CI）
export WECHAT_MP_APPID=wx1234567890abcdef
export WECHAT_MP_SECRET=xxxxxxxx
# 或者已有 token 时直接：export WECHAT_MP_ACCESS_TOKEN=******
```

然后在微信公众平台后台「设置与开发 → 基本配置」把**本机公网 IP 加入白名单**（`curl https://myip.ipip.net` 查询）。跳过这步所有调用报 40164。家用宽带重拨后 IP 会变，40164 复发时先查这里。

## 1. 建工作区（新项目时）

在项目目录建四件套（模板见 [references/persona-template.md](references/persona-template.md)）：

- `世界圣经.md` — 宇宙规则、素材优先级、红线
- `人设表-<角色>.md` — 每个角色：事实表 / 时间线 / 伤疤欲望谎言 / 配角 / 物件地点 / **知情账本**
- `选题库.md` — 选题池（状态流转）+ 母题黑名单 + 素材碎片区 + 已用登记
- 排版模板目录 — 每个栏目一套专属 HTML 风格，禁止共用同一模板

## 2. 单篇生产序列（收到"跑今天的/开工"类指令时自主执行）

1. **取题**：从选题库按排期取下一条"待用"，标"使用中"
2. **成文**：单视角纪律；结构 = 1 个话题触发器 + 1 段档案往事 + 1 个当下动作落点；1000–1400 字；文中任何人/年份/物件必须能在档案中查到——查不到的不许出现
3. **质检链**（顺序固定，细则见 [references/quality-gates.md](references/quality-gates.md)）：去 AI 味 → 中文 final-QA → 母题黑名单核对 → 知情账本核对 → 红线核对
4. **配图**：3–4 张章节场景图（从角色"物件地点表"取材，保证图文咬合）+ 1 张 2.35:1 横版封面。用可用的图像生成工具产出；无图像额度时降级：封面用现有图顶替，报告注明待补
5. **排版**：生成全内联样式 HTML（`<section>` + style 属性，不用 `<style>`/`<div>`/class），浏览器可预览、可整体复制进公众号编辑器。两套出厂模板见 `assets/template-ribao.html`（观点型栏目）与 `assets/template-xinjian.html`（陪伴型栏目），同一号的不同栏目用不同模板，禁止共用
6. **推送**：`python3 scripts/wechat_publish.py --html out.html --title ... --author ... --digest ... --cover cover.png --images "img1.png img2.png"`（参数见 `--help`；只新建草稿，绝不设定时/群发）
7. **回写**：选题库登记已用、母题入库、知情账本记一笔、git commit

## 3. 异常预案（预先授权，不中断询问）

| 症状 | 处置 |
|---|---|
| API 报 40164 | 公网 IP 变了：其余步骤照跑，报告里让用户更新白名单 |
| 报 53407 | 该草稿被定时发布锁定：不解除不覆盖，新建草稿并提示 |
| 图像生成失败/无额度 | 文字+排版照常，配图降级并标注待补 |
| 热榜抓取失败 | 用选题库存量，注明"选题来源=库存" |
| 质检发现红线内容 | 自行重写至通过，报告说明改动 |

只有两种情况停下来问：需要修改人设档案/世界观；红线是否越界无法自裁。

## 4. 数据回路（可选，发布后启用）

`python wechat_data.py --since 昨日` 拉取图文阅读/分享数据，写入选题库“已用登记”，按周复盘调排期权重。
未认证个人订阅号可能报 48001（无此 API 权限）：降级为后台看板人工抄录，不影响主链路。

## 硬边界

- 只到草稿箱：发布、定时、群发、改后台设置都不属于本 skill
- 人设档案是用户的宪法：skill 只读取，改动必须用户拍板
- 凭证与 IP 白名单永远在用户本地：仓库、文档、日志里不得出现真实 AppSecret
