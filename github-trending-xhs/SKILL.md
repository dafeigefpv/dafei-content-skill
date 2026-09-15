---
name: github-trending-xhs
description: GitHub Trending → 小红书图文每日流水线的执行规范。当自动化任务或用户要求运行 github-trending-xhs 项目（抓取 Trending Top5、撰写 content.json、渲染封面+详情卡+发布文案）时使用。固化了 12 区块卡片结构、固定行距方案、内容撰写红线和已知坑位。
---

# GitHub Trending → 小红书图文 · 流水线规范

项目目录：以工作区中的 `github-trending-xhs` 为准（含 fetch_trending.py / content.json / render.py / README.md）。
运行环境：`C:\Users\lgs\.workbuddy\binaries\python\envs\default\Scripts\python.exe`（venv，依赖 requests / beautifulsoup4 / lxml / playwright / qrcode / pillow）。

## 执行流程（顺序固定，任一步失败重试一次，仍失败则报告失败环节，不输出半成品）

1. **抓取**：venv python 运行 `fetch_trending.py` → `data.json`（全语言综合榜 Top5 + API 补全 + README 摘录）。
   - 网络偶发 ConnectionReset / raw.githubusercontent 超时：脚本自带重试，README 摘录可能为空，不阻塞出图。
2. **创作**：读 `data.json`（含 README 摘录），撰写 `content.json`。规则见下。
3. **渲染**：venv python 运行 `render.py` → `dist/<日期>/cover.png + 01~05.png + copy.txt`。内置溢出检测（zoom 自动缩小，最多 5 级）。
4. **交付**：present_files 展示 6 张图 + copy.txt，配一句话榜单亮点总结。

## content.json 撰写规则

- `date` 必须与 data.json 一致；`brand="@大飞的AI赋能笔记"`；`comment_label="大飞点评"`
- `theme`（可选）：指定视觉主题，取值共 10 套（定义在项目 `themes.py`）——浅色 6：`cream / klein / forest / swiss / pastel / split`，深色 4（参考 zarazhangrui/frontend-slides 风格）：`terminal`（GitHub 暗+终端绿）/ `neon`（海军蓝渐变+霓虹青/品红）/ `signal`（暗底+高亮橙）/ `botanic`（近黑+暖金/赤陶）；缺省按日期自动轮换（年内天数 % 10）。同一期封面与 5 张详情卡强制同主题。深色主题封面用 `$cover_bg` 渐变（浅色为平铺同色渐变，肉眼等同纯色）。命令行可覆盖：`render.py --theme neon --outdir dist/xxx --covers-only`（测试/预览用）
- ~~`hook`~~：**封面引导语已取消（2026-09-07 用户要求）**，封面不再显示 hook 行，render.py 也不再校验该字段（content.json 里残留的 hook 字段会被忽略）
- `cover_title`：两行大标题，可适度变化
- 每仓库字段：
  - `selling` 一句话卖点（口语化有钩子）
  - `intro_zh` 中文简介 2-3 行
  - `highlights` 3-4 条，**必须依据 README 摘录或 description，严禁编造数字**；README 为空时依据 data.json 事实字段（stars/贡献者等）
  - `install_cmd` 必须来自 README 原文或通用包管理器（vcpkg/pip/npx 等可验证命令）；**README 缺失或无法验证时一律用 `git clone <repo_url>`，严禁虚构**
  - `audience` 3 个受众标签
  - `comment` 大飞点评（一句话，带观点）
  - `quote`（可选）：作者原话（README 原句或 repo description 原文），缺省时 render.py 会从 readme_snippet 自动提炼
- `copy`：发布文案（**只写一份**），结构 `{title, body, title_alts, tags}`。render.py 输出单份正文 + 两版标签：**小红书 / 微信贴图用 `#标签`（单井号）**、**微头条用 `#话题#`（双井号）**。正文三平台通用，调性按小红书口吻（口语+emoji，1000 字以内含换行符按最严口径，写完用脚本实测字符数）；兼容旧字段 `copies`（仍写三平台结构时取 xhs 为统一正文）。
  - **爆款框架（2026-09-09 定版，与 github-project-xhs 同源）**：
    1. **首行 = 折叠线以上唯一曝光，必须自带点击理由**：结论前置/数据冲击（如"今天不绕弯子，先说结论：榜单第一的项目，写 HTML 就能出视频"），第一人称优先；观点句、"你有没有过这种体验"式提问禁止当首行
    2. **5 个项目段，每段配【emoji + 口语化标签】小标题**（如【💊 AI 废话终结者】【📐 丑图救星】），标题 = 给读者的好处/人设，不是项目分类；段内：项目名 + 今日星数 + 怎么解决（1-2 句）；新面孔/争议（如官方废弃）要点出
    3. **结尾**：左滑引导 + 站队/选择式提问（"今天哪一个戳中了你？"）+ 空一行 + 关注引导「【📣 关注我，每天播报 Github 最新的热门项目】」（【emoji+文案】加粗样式，2026-09-09 定版）
  - **写作视角（2026-09-07 用户要求）：站在普通公众号读者的角度，从"用户最关心什么"出发**——不要写成项目说明书。少用专业黑话，多用"你"的口吻；数字仍须与 data.json 一致，严禁编造
- `title_alts` 必填 3 个候选标题：利益结果型 / 痛点劝阻型 / 转变叙事型，**必须有利益点或痛点词 + 悬念/数字缺口，纯抽象文艺表述禁止**；`title` 取其一，标题数字与封面、卡片、正文三处一致（写完逐一核对）
- tags（三平台共用同一组词，仅格式不同）：统一 22 个定版清单（2026-09-09）——GitHub / 开源项目 / AI编程 / 程序员日常 / AIAgent / 智能体 / 技能日报 / 项目日报 / 每天一个神仙技能 / 每天一个Github热门项目 / 大飞的AI赋能笔记 / AI / skill / 技能 / workbuddy / codex / claudecode / opencode / openclaw / hermes / 豆包 / deepseek。content.json 里写**纯词**（不带前缀），render.py 自动套两版格式：小红书 / 微信贴图 `#词`（单井号）、微头条 `#词#`（双井号）。整份照抄不增不减
- 字段不齐 render.py 会校验报错

## 详情卡版式（已定型，改动需谨慎）

- 尺寸：封面 1080×1440 (3:4)，详情卡 1080×1920 (9:16)；浅色杂志风（奶油底 #faf7f1 / 墨色 #1c1b18 / 砖红 #c7442e）
- **封面结构**（2026-09-07 改版）：顶部 tag+日期 → 两行大标题+TOP5 色块 → **01~05 榜单列表（醒目大字：序号 40px / 仓库名 44px 加粗，行间 30px）→ 每行右侧红色 mono「今日+N★」（30px，数据来自 stars_today）** → 页脚（左滑引导 + 品牌）。**不放 hook 引导语**。上下两段间距（2026-09-15 定版）：`.cover .title` margin-top 96px、`.cover .list` margin-bottom 52px（保留 margin-top:auto 钉底），实测 标题→列表 82px / 列表→页脚 90px；改间距用 Playwright 读 `.top/.title/.list/.foot` 的 getBoundingClientRect 精确校准
- **12 区块结构**：名片 / 简介 / topics / 数据条(4格) / 今日增速条 / 项目档案行(license·创建年份·最近提交·Issues) / 核心亮点 / 作者原话 / 上手命令 / 适合谁 / 大飞点评 / 仓库地址页脚。**不放二维码（2026-09-09 用户要求）**
- **固定行距方案**（用户明确要求"整体行距一致，不要有的紧有的宽"）：
  - 卡片 flex 列 + `justify-content:space-between`，内容分 6 组：头部块 → 数据块 → 亮点块 → 上手命令 → 适合谁 → 点评底块
  - 组间距 = 30px 基础 margin + 剩余空间五等分，**任意相邻组间距完全相等**
  - 禁止回到旧方案：`.sp` 弹性间隔 + `margin-top:auto` 钉底混用（会导致空隙集中一处或忽紧忽宽）
- **二维码已整体移除（2026-09-09）**：make_qr/qrbox 均已删除，仓库入口靠页脚 mono 地址。若将来恢复：必须 base64 data URI 内嵌（Chromium 禁止 about:blank 截图页加载 file:// 图片，文件路径会显示破图），失败优雅降级隐藏
- data.json 档案字段：license / created_at / pushed_at / open_issues / subscribers（fetch_trending.py 已抓；旧 data.json 缺字段时 render.py 需 `.get()` 容错、缺啥跳啥）

## 失败兜底

- trending 抓取重试 3 次；解析仓库数 <5 直接报错（解析器失效需人工修）
- GitHub API 限流时字段降级为 0/空，卡片仍可出图
- render 溢出自动缩放最多 5 级，仍超限则在 stderr 告警——告警时应精简文案而非改版式
- 执行记录写入 `.workbuddy/memory/automations/<automation-id>/memory.md`（只记摘要，不贴全文）
