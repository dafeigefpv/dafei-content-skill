# GitHub Trending → 小红书图文 · 每日自动化

每天自动抓取 GitHub Trending 全语言综合榜 Top5，生成 1 张封面 + 5 张信息图详情卡 + 1 段发布文案。

## 产物规格

| 文件 | 说明 | 规格 |
|---|---|---|
| `dist/<日期>/cover.png` | 封面：大字标题 + 5 项目名预览 | 1080×1440 (3:4) |
| `dist/<日期>/01~05.png` | 详情卡：12 区块信息图（名片/简介/topics/数据条/今日增速条/项目档案/亮点/作者原话/上手命令/适合谁/点评+二维码/仓库地址页脚） | 1080×1920 (9:16) |
| `dist/<日期>/copy.txt` | 发布文案（标题+正文+标签） | 纯文本 |

视觉：浅色杂志风（奶油底 #faf7f1 + 墨色 #1c1b18 + 砖红 #c7442e），落款 @大飞的AI赋能笔记。

## 文件说明

| 文件 | 作用 |
|---|---|
| `fetch_trending.py` | 抓取 github.com/trending Top5 + GitHub API 补全（topics/Fork/贡献者/license/created_at/pushed_at/open_issues/subscribers）+ README 摘录 → `data.json` |
| `content.json` | LLM 生成的创作层（卖点/亮点/点评/文案/可选 quote 作者原话），由 Agent 每日基于 data.json 重新撰写 |
| `render.py` | 合并事实+创作 → Playwright 截图 → PNG。**内置溢出检测**：内容超高自动 zoom 缩小 |
| `data.json` | 每日事实数据（脚本产出，勿手改） |

## 每日运行流程（自动化按此执行）

1. `python fetch_trending.py` — 产出 data.json
2. **Agent 读 data.json**（含 README 摘录），撰写 content.json：
   - `hook`（封面引导语，从钩子池轮换避免重复）、`cover_title`
   - 每仓库：`selling` 一句话卖点 / `intro_zh` 中文简介 / `highlights` 3-4 条（依据 README，不得编造数据）/ `install_cmd`（必须来自 README 或通用包管理器，README 缺失时用 git clone，严禁虚构）/ `audience` 3 个标签 / `comment` 大飞点评
   - `copy`：发布文案 title/body/tags
   - 字段不齐 render.py 会校验报错
3. `python render.py` — 渲染 PNG + copy.txt
4. present_files 展示 6 张图 + 文案

## 环境依赖

- venv: `C:\Users\lgs\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
- 包：requests / beautifulsoup4 / lxml / playwright（已装 chromium）/ qrcode + pillow（仓库二维码，失败时卡片自动隐藏二维码块）
- 已知问题：raw.githubusercontent.com 偶发超时，README 摘录可能为空，不影响出图，仅影响亮点精度
- 注意：卡片二维码以 base64 data URI 内嵌（Chromium 禁止 about:blank 页面加载 file:// 图片，勿改回文件路径）

## 失败兜底

- trending 抓取重试 3 次；解析仓库数 <5 直接报错（解析器失效需人工修）
- GitHub API 限流时字段降级为 0，卡片仍可出图
- render 溢出自动缩放最多 5 级，仍超限则在 stderr 告警
