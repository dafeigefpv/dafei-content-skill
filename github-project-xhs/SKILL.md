---
name: github-project-xhs
description: GitHub 单项目深度报道 → 小红书图文的执行规范。当用户要求对某个 GitHub 项目做重点报道/深度报道/单项目图文（区别于每日 trending 榜单）时使用。产出封面 + 1~2 页深度详情 + 发布文案。固化深度档案版式、内容撰写红线和已知坑位。
---

# GitHub 单项目深度报道 → 小红书图文 · 规范

项目目录：工作区中的 `github-project-xhs`（fetch_project.py / content.json / render.py / project.json）。
运行环境：`C:\Users\lgs\.workbuddy\binaries\python\envs\default\Scripts\python.exe`（venv：requests / beautifulsoup4 / lxml / playwright / qrcode / pillow）。
姊妹技能：`github-trending-xhs`（每日榜单快讯）。**两者定位必须区分**：本技能是"深度档案"，不是榜单卡的放大版——栏目式编号排版、亮点带小标题+详述、三步上手、适合谁带说明、可写同类对比、点评可 2-3 句。

## 触发与输入

- 用户说"重点报道 xxx/yyy""把 <repo> 做成图文"或给仓库 URL
- 任一步失败重试一次，仍失败报告失败环节，不输出半成品

## 执行流程

1. **抓取**：`fetch_project.py <owner/repo 或 URL>` → `project.json`（API 档案 + contributors 翻页计数 + latest release + **README 全文清洗版 12000 字符**）。
2. **创作**：通读 README 全文后写 `content.json`（规则见下）。
3. **渲染**：`render.py` → `dist/<repo-name>/cover.png + 01.png + 02.png(pages=1 时无) + copy.txt`。
4. **交付**：present_files 展示全部图 + copy.txt，配一句话总结。

## content.json 撰写规则

- `date` 与 project.json 一致；`full_name` 必须与 project.json 一致（render 会校验）
- `theme`（可选）：指定视觉主题，取值共 10 套（定义在项目 `themes.py`，与 trending 共用主题库）——浅色 6：`cream / klein / forest / swiss / pastel / split`，深色 4（参考 zarazhangrui/frontend-slides 风格）：`terminal`（GitHub 暗+终端绿）/ `neon`（海军蓝渐变+霓虹青/品红）/ `signal`（暗底+高亮橙）/ `botanic`（近黑+暖金/赤陶）；缺省按日期自动轮换。封面徽章/强调用第二点缀色 accent2，详情页编号/引用/点评用主点缀色 accent——两色已按主题配好，勿在 content.json 里手写颜色。深色主题下封面用 `$cover_bg` 渐变（叠加在格子纸网格之下），终端窗/黑卡/logo 自动带 $panel_border 描边（浅色主题为透明）。命令行可覆盖：`render.py --theme neon --outdir dist/xxx`
- `brand="@大飞的AI赋能笔记"`；`comment_label="大飞点评"`；`pages` 默认 2（内容单薄可 1）
- `cover_headline`：封面主标题（1-2 行，含 `[[...]]` 标记的词组会渲染成橙色强调，`<br>` 手动换行）；`cover_sub` 封面副文案（缺省用 intro_zh）；`cover_quote` 封面底部大字金句（可用项目信条/作者原话，缺省用 cover_tagline）；`cover_terminal`（可选）终端窗命令行，缺省取 steps[0].cmd + 固定 ok 行
- `agent_prompt`（可选）：**小白指令**——不会装的用户可原样复制发给 AI Agent 的一句话，如「请从 GitHub 获取并安装 diagram-design 画图技能（cathrynlavery/diagram-design）」；缺省自动生成同款句式；渲染在 03 三步上手下方的橙色虚线框内
- `selling` 一句话卖点；`intro_zh` 中文简介 1-2 行（01 页放不下长文，宁短勿溢出）
- `problem`：**两段式**——第一行以红色强调呈现读者痛点（"每次让 AI 画图……"），换行后是项目来历/解法
- `highlights` 3-4 条，每条 {title, text}：title 是小标题，text 一句话详述；**必须依据 README 事实，严禁编造数字**；README 缺失时只用 project.json 事实字段
- `quote`（可选）作者原话，必须 README 原句；缺省则 01 页不显示引用块
- `steps` 2-3 步 {k, cmd, note}：**cmd 必须来自 README 原文**（无法验证时用 `git clone <url>`，严禁虚构）；note 补充说明
- `audience` 3 个 {tag, note}：tag 是短标签，note 说"为什么适合"
- `cover_facts`（可选，**建议必填**）：封面 4 张白色指标卡的内容——放 **README 亮点事实**（如"39 种图示 / 3 种风格 / 60 秒配色 / 2 条命令上手"），每条 {label, value, desc}；**严禁放星标/Fork/贡献者等仓库统计**（那是封面黑卡和 01 页的领地）。缺省用 topics 兜底
- **数据分区红线（2026-09-09 用户要求，封面与详情页信息零重复）**：
  - **封面**：黑卡 = 总星标大数 + Fork + 贡献者（社交证明钩子）；白色指标卡 = cover_facts 亮点事实；胶囊行 = 语言·license
  - **01 页**：指标格 = Watch 关注 / Open Issues / 最新版本 / 创建年份；档案行 = license · 最近提交；这两块只属于 01 页
  - **02 页**：不放任何统计数据
- `compare`（可选）：同类对比，只写 README/事实支撑的内容
- `comment`：大飞点评 2-3 句（深度报道可放长，仍要带观点）
- `copy` 发布文案（**只写一份**）`{title, body, title_alts, tags}`，**与 trending 版同一套基础红线**（body 700-900 字内、少黑话多"你"口吻、数字与事实一致）；render.py 输出单份正文 + 两版标签：小红书 / 微信贴图 `#词`（单井号）、微头条 `#词#`（双井号）；兼容旧字段 `copies`（取 xhs 为统一正文）。tags 写**纯词不带前缀**，统一 22 个定版清单（2026-09-09）：GitHub / 开源项目 / AI编程 / 程序员日常 / AIAgent / 智能体 / 技能日报 / 项目日报 / 每天一个神仙技能 / 每天一个Github热门项目 / 大飞的AI赋能笔记 / AI / skill / 技能 / workbuddy / codex / claudecode / opencode / openclaw / hermes / 豆包 / deepseek（整份照抄不增不减）
- **爆款文案框架（2026-09-09 定版，骨架 = 人→物→你）**，700-900 字为宜：
  1. **开头钩子**（2-3 句）：**首行 = 折叠线以上唯一曝光，必须自带点击理由——第一人称 + 具体结果/动作前置（如"装上它的第一周，我把方案里的丑图全换掉了"），观点句、感叹句禁止当首行（2026-09-09 用户反馈）**；第二行再接数字背书/悬念。钩子池四型轮换（结果前置 / 反常识 / 损失厌恶 / 场景痛点），执行前先看上一篇用了哪种，禁止连续重复；禁止"今天给大家介绍"式开头
  2. **故事段**：先讲人再讲物——作者来历 + 项目信条 + 规则之狠（讲"为什么做"而非"是什么"）；**小标题 = 正文段落标题统一【emoji + 文案】加粗样式**（如【📖 故事得从一张丑图说起】【🎁 装上之后你会得到什么】），标题要口语化有画面感，不用"先讲人，再讲项目"这类平铺直叙（2026-09-09 用户要求）
  3. **干货段**（主体）：3-4 个点，每点 = 具体场景 + 结果，可带编号
  4. **缺点段**（必须）：主动说 1 个真实局限——自曝缺点建立信任，减少评论区抬杠
  5. **收尾**：一句观点总结 + 二选一式站队提问（比开放式更易评论）+ 空一行 + 关注引导「【📣 关注我，每天播报 Github 最新的热门项目】」——关注引导同样用【emoji + 文案】加粗样式，与站队提问之间必须空一行（2026-09-09 定版，替换原"每天定点"表述）
- **三候选标题**：`title_alts` 必填 3 个。**标题必须有"利益点或痛点词"+ 悬念/数字缺口（2026-09-09 用户反馈：抽象表述如"信条只有一句话"不够爆款——文艺但无点击理由）**。公式：① 利益结果型（"AI 画图终于能放进方案里了：一条命令装好的 33.5k★ 外挂"）② 痛点劝阻型（"别再忍 XX 了：…"）③ 转变叙事型（"我给 AI 装了个『审美外挂』，39 种图示随口就有"）；`title` 取其一；标题数字必须与封面 headline、卡片、正文三处一致（写完逐一核对）
- **信任红线**：所有数字 ≤ project.json 可验证范围；作者原话必须真引（quote 机制）；不碰"吊打/碾压"拉踩表述，对比只摆事实
- 用户对具体项目的文案禁用偏好（如 hermes-agent 禁提"5 美元 VPS"）同样适用

## 版式规范（已定型）

- 封面 1080×1440（**skills-daily 风格，2026-09-09 改版**）：格子纸底纹 → 顶部橙色药丸徽章「项目日报 · 每天一个Github热门项目」（**栏目名是品牌位，必须大而醒目：37px/900 加粗、46px 星标圆点、加粗描边，2026-09-09 用户要求放大**）→ 品牌行（logo G + 项目名 + 语言·license·OPEN SOURCE 胶囊）→ eyebrow 全大写仓库名 → 大标题（[[..]]橙色强调）→ 副文案 → **终端模拟窗（$ 命令绿字 + ✔ ok 行）+ 黑卡（GITHUB STARS 大数字 + Fork/贡献者行）** → 4 张白色指标卡（cover_facts 亮点事实，禁放仓库统计，见数据分区红线）→ 分隔线（左滑引导 + 日期·DEEP DIVE）→ 底部大字金句 → 页脚（品牌 + 仓库地址）。**不放二维码（2026-09-09 用户要求，封面和详情页均不放）**
- 小白指令块：03 三步下方橙色虚线框「小白指令｜不会装？把这句话原样发给你的 AI Agent」+「」括起的指令句（agent_prompt 字段，缺省自动生成「请从 GitHub 获取并安装『名称』（owner/repo）」句式）
- 详情页 1080×1920，编辑部编号栏目风：`01 解决什么问题` / `02 核心亮点`（小标题+详述+引用块）/ 数据条+档案行（license·创建·最近提交·最新版·Issues）；`03 三步上手`（编号+黑底命令块+note）/ `04 适合谁`（药丸标签+说明）/ `05 同类对比`（可选灰底块）/ 大飞点评 / 页脚仓库地址
- 固定行距：flex + space-between 分组，组间距离一致；禁止弹性间隔+钉底混用
- **不放二维码**（2026-09-09 用户要求）：仓库入口靠页脚 mono 小字 `github.com/owner/repo`，封面黑卡只剩星标 + Fork + 贡献者行
- 字号档位已调定（selling 41 / 亮点 title 30 / text 26 / 命令 26），文案长度按"每条亮点 text ≤1-2 行"控制

## 已知坑位（改 render.py 前必读）

1. **溢出检测必须量卡片内部**：`.card` 是固定高度 + overflow:hidden，body scrollHeight 量不到裁切。现方案：截图前把卡片 height 设为 auto 实测内容高，一步算出 zoom（低于 0.70 告警）。卡片 div 必须带 `id="card"`
2. 二维码已整体移除（2026-09-09）；若将来要恢复，必须 base64 data URI 内嵌（Chromium 禁止截图页加载 file:// 图片）。3. README 抓取走 API `/readme`（raw accept），失败不阻塞，创作降级用 description/事实字段；4. 渲染后**必须目检至少 01 页**——chips/topics 样式曾因漏 CSS 缩成小字，zoom 校验发现不了这类问题；5. 封面 `cover_headline`/`cover_quote` 里的换行写 `<br>`（accent_html 会放行），但**尖括号其他用途会被转义成字面量**
