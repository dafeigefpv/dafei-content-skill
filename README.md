# dafei-content-skill

GitHub → 小红书图文内容流水线技能集（@大飞的AI赋能笔记）。包含两个 WorkBuddy Agent Skill，均以单个 `SKILL.md` 固化完整执行规范。

## 技能列表

### 1. [github-trending-xhs](./github-trending-xhs/) — GitHub Trending 每日榜单快讯

每日自动化流水线：抓取 GitHub Trending 综合榜 Top5 → 撰写 content.json → 渲染 **封面 + 5 张详情卡 + copy.txt 发布文案**。

- 12 区块详情卡结构（名片/简介/topics/数据条/增速条/项目档案/亮点/作者原话/上手命令/适合谁/大飞点评/页脚）
- 封面 Top5 大字列表 + 每行红色 mono「今日+N★」
- 爆款文案框架：首行结论前置、段落【emoji+口语标签】小标题、站队式提问、播报式关注引导
- 内容红线：亮点必须依据 README 事实、install_cmd 必须可验证、数字严禁编造

### 2. [github-project-xhs](./github-project-xhs/) — GitHub 单项目深度报道

手动触发：对单个 GitHub 项目做深度图文报道，产出 **封面 + 1~2 页深度详情 + copy.txt**。

- skills-daily 风格封面：格子纸底 + 橙色项目日报徽章 + 终端窗 + 星标/Fork/贡献者黑卡 + 亮点事实白卡
- 编辑部编号栏目：01 解决什么问题 / 02 核心亮点 / 03 三步上手（含小白 agent 指令）/ 04 适合谁 / 05 同类对比
- 数据分区红线：封面与详情页信息零重复

## 定版文案规范（两技能共用）

- copy.body 1000 字以内（含换行，脚本实测），站在普通读者视角的痛点→解药结构
- 首行必须第一人称 + 具体结果，自带点击理由
- title_alts 三候选：利益结果型 / 痛点劝阻型 / 转变叙事型
- 收尾固定：【📣 关注我，每天播报 Github 最新的热门项目】
- 信任红线：数字可验证、必须有缺点段、不拉踩

## 统一标签（22 个，定版）

#GitHub #开源项目 #AI编程 #程序员日常 #AIAgent #智能体 #技能日报 #项目日报 #每天一个神仙技能 #每天一个Github热门项目 #大飞的AI赋能笔记 #AI #skill #技能 #workbuddy #codex #claudecode #opencode #openclaw #hermes #豆包 #deepseek

## 主题系统（10 套，两技能共用 `themes.py`）

`themes.py` 是语义化令牌库，render.py 的 CSS 用 `$token` 占位、渲染时按主题填充。两技能共用同一份 `themes.py`，默认随日期自动轮换，也可手动指定。

### 主题清单

| 类型 | 名称 | 风格 | 主点缀色 |
|---|---|---|---|
| 浅色 | `cream` | 奶油砖红（原默认） | 砖红 `#c7442e` |
| 浅色 | `klein` | 克莱因蓝·纸白科技感 | 克莱因蓝 `#002fa7` |
| 浅色 | `forest` | 森野墨绿·沉稳极客 | 墨绿系 |
| 浅色 | `swiss` | 瑞士现代·纯白+黑+包豪斯红 | 红 `#ff3300` |
| 浅色 | `pastel` | 粉彩几何·粉蓝底+紫 | 紫 `#7c6aad` |
| 浅色 | `split` | 双色拼接·蜜桃+薰衣草 | 薰衣草 `#8a6fb0` |
| 深色 | `terminal` | GitHub 暗底 `#0d1117`+终端绿 | 终端绿 `#39d353` |
| 深色 | `neon` | 海军蓝渐变+霓虹青/品红 | 霓虹青 `#00ffcc`·品红 `#ff00aa` |
| 深色 | `signal` | 暗底+高亮橙 | 橙 `#FF5722` |
| 深色 | `botanic` | 近黑+暖金/赤陶 | 暖金 `#d4a574` |

> 浅色 `swiss/pastel/split` 与全部深色主题，配色语言参考 [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) 的 STYLE_PRESETS（拒绝 generic AI 配色，强调有性格的大胆强调色）。

### 如何指定主题

1. **自动轮换（默认）**：不写 `theme` 时按发布日期轮换，`day_of_year % 10`，相邻两天必不同；同一期的封面与详情卡强制同一主题（一套皮肤到底）。
2. **content.json 指定**：在 content.json 顶层加 `"theme": "klein"` 即可锁定该主题（取值见上表）。
3. **命令行覆盖（测试/预览用）**：
   - trending：`python render.py --theme neon --outdir dist/preview --covers-only`（仅出封面）
   - project：`python render.py --theme neon --outdir dist/preview`

**约束**：系统使用单一 `ink` 令牌同时驱动封面与详情卡文字色，因此每套主题必须整浅或整深。frontend-slides 中「深底+浅纸」的双调签名（如 Notebook Tabs）无法干净映射，故未纳入；若需该效果，须把 `ink` 拆成 `cover_ink`/`card_ink` 两个令牌。

## 使用方式

将任一技能文件夹放入 Agent 技能目录（如 `~/.workbuddy/skills/`），即可由 AI Agent 按其中的执行规范自动完成"抓取 → 创作 → 渲染 → 交付"全流程。渲染依赖 Python venv（requests / beautifulsoup4 / lxml / playwright / qrcode / pillow）。

---

品牌：**@大飞的AI赋能笔记**
