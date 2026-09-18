---
name: github-repo-video
description: 把 github-project-xhs / github-trending-xhs 的文案转成带 AI 旁白、同步字幕、逐块动画的 3:4 竖屏 MP4（1440×1920），并配套产出 3:4 封面（去水印 + 补页脚 + 版式体检）。画面为「一个口播语义块 = 一屏」的原创版式，不复用静态卡片。当用户要求把图文变成视频、做 GitHub 项目介绍短视频、给图文加配音与字幕、做"每日开源项目"口播视频、给视频配封面，或提到 hyperframes / 卡片转视频时使用。
agent_created: true
---

# GitHub 项目短视频生成

把已经写好的**口播稿**变成一条 **60 秒左右、带中文旁白与同步字幕的 3:4 竖屏视频**（1440×1920），
再配一张 3:4 封面。

核心设计只有一条：**旁白驱动一切** —— 不只是时间，还包括**画面内容本身**。
场景时长由旁白实测长度决定，动画触发点绑定到旁白的**字级时间戳**，
**一个口播语义块 = 一屏画面**。

```
storyboard.json          ← 口播稿 + 分镜（唯一需要创作的输入）
   │
   ├─ scripts/voice_synth.py   → audio/*.mp3 + timeline.json + subtitles.srt
   │                             (edge-tts 合成，字级时间戳，块边界定位)
   ├─ scripts/build_video.py   → video/index.html
   │   ├─ scripts/video_boards.py   各屏的 HTML / JS / cls / expect
   │   └─ scripts/board_css.py      各屏的局部样式
   ├─ scripts/check_fill.py    → 占位图（查「半屏空」）
   ├─ scripts/measure_subs.py  → 字幕行数与宽度（查折行）
   ├─ scripts/probe_frames.py  → seek 抓帧（查遮挡 / 显隐）
   ├─ hyperframes              → video/out/render.mp4  (无声画面，字幕已烧入)
   ├─ scripts/mux.py           → out/final.mp4         (混入旁白 + 响度标准化)
   └─ scripts/fix_cover.py     → cover/cover.png       (封面后期 + 版式体检)
                                输入 cover/raw.png ← gbro-cover-design + 内置生图
```

## 何时用 / 不用

**用**：已有口播稿，要出竖屏口播短视频；要批量产出系列视频（每日一个项目）。
**不用**：需要实拍素材剪辑、需要复杂转场特效 —— 那些场景 HyperFrames
的逐帧 seek 模型会成为负担。

---

## ⚠️ 五条最容易翻车的红线

这五条**每一次都要照做**，其余细节按需查参考文档：

1. **渲染必带 `--no-browser-gpu`**，且**日志绝不走管道**（`> render.log 2>&1`）。
   不加会永久卡在 25%；走管道会把进度憋住、看起来像卡死。
2. **每次跑 HyperFrames 前先清孤儿浏览器进程**（`chrome-headless-shell`），
   用 PowerShell 的 `Stop-Process`（Git Bash 的 `taskkill` 会被路径转换破坏）。
3. **打底帧 ≠ 内容**。框 / 栏头 / 网格在块起始 **0.3s 内就位**，内容才随关键词点亮。
   判据：把块起始那一帧单独截出来，应该已经能看出「这一屏要讲什么结构」。
4. **动画必须在切屏前演完**。看 `build_video.py` 的 `[动画]` 报表，**「余」必须为正**；
   为负就是观众看不到最终态（曾漏检 c3 星数，观众只看到 26k 而非 29,788）。
5. **改脚本要防两份副本不同步**。本项目脚本有 skill 与项目**两份**，
   改完必须 `cp` + `diff -q` 逐个核对。

---

## 一、先读哪份文档（按需加载，不要一次全看）

主文档只保留**每次都要执行**的流程。下面这些是「用到才查」的参考资料：

| 你要做的事 | 读这份 | 内容 |
|---|---|---|
| 设计 / 修改某一屏画面 | `references/boards.md` | 四条排版规矩、块内两个节拍层、时间令牌、12 屏清单、占位探针判读、反模式清单 |
| 写或改口播稿 | `references/copywriting.md` | 六段式骨架、写作红线、块长硬约束、总长估算、评论区钩子、口语化改写 |
| 出问题 / 报错 / 结果不对 | `references/pitfalls.md` | 26 条坑位，按「症状 → 定位 → 根因 → 修复」，含原始报错样本 |
| 换音色 / 觉得「AI 味」重 | `references/voice.md` | 三条路径对比、6 个可用音色实测清单、参数与文本杠杆、试听台 |
| 做封面 | `references/cover.md` | 固定版式六条、垂直空间预算、三版实测留档、提示词要写死的四件事 |
| 要一份完整定稿示例 | `references/example-copy-voicestudio.md` | VoiceStudio 的定稿文案 + 钩子候选池 |

---

## 二、画面架构要点

**为什么是 3:4 而不是 9:16**：9:16 的舞台宽 1080，一屏讲一件事时信息很快排不下；
3:4 的 1440 宽能并排两张卡、放得下代码行和波形带，同时仍是竖屏（信息流友好）。
1440×1920 不在 HyperFrames 的 6 个预设里，但 `readCompositionDimensions()` 直接读根节点的
`data-width` / `data-height`，**任意值都认** —— 只要不传 `--resolution`，就按原生尺寸渲染。

**画幅分区**：

```
y    0 ..  150   顶栏 HUD      系列徽章（左） / 仓库名 + ★（右）
y  158 ..  202   进度轨        4 段（开场 / 定位 / 能力 / 上手）
y  240 .. 1520   舞台 Stage    1224×1280，一块一屏（左右各留 108）
y 1552 .. 1788   字幕带        独占 236px，深色胶囊，两行容量
y 1822 .. 1882   底栏          品牌 + 项目地址
```

**字幕带独占**是最重要的结构改动：旧版字幕无处可放、只能压在内容上，
由此引出字号、折行、页脚让位一整套坑。现在字幕有 236px 专属高度，**折行不再致命**。

**块内只有两个节拍层**：打底帧（`@@S@@` 起的补间）+ 关键词点亮（`mark(sel, t)` 加 `.on` 类）。
排版四条规矩、时间令牌、12 屏清单与反模式表 —— 见 `references/boards.md`。

---

## 三、环境准备（一次性）

| 依赖 | 要求 | 说明 |
|---|---|---|
| node | ≥ 20 | 路径见 `<binary_context>`，用托管版本 |
| hyperframes | **pin `0.8.44`** | 半年发了 397 个版本，绝不能跟 `@latest` |
| ffmpeg / ffprobe | ≥ 5 | `mux.py` 顶部常量指向 `C:\ffmpeg\bin` |
| edge-tts | ≥ 7.2.8 | 装在隔离 venv 里 |
| playwright | 任意 | `build_video` 版面校验 / `check_fill` / `measure_subs` |

```bash
# hyperframes 装到项目自己的 node_modules（约 3 分钟 / 139 个包）
cd <project> && npm install hyperframes@0.8.44 --save-exact --no-audit --no-fund
python -m pip install edge-tts
```

装完后 CLI 在 **`<project>/node_modules/hyperframes/bin/hyperframes.mjs`**。
⚠️ 它**不是**共享位置 —— 换项目要重新装，或把 `node_modules` 一起拷过去。
调用时务必用绝对路径，写成 `<vendor>/...` 会 `MODULE_NOT_FOUND`。

`hyperframes doctor` 显示全绿**不代表能渲染**（见 `pitfalls.md` P1）。

⚠️ **本机跑脚本必须用带 playwright 的那个解释器**：

```
C:/Users/lgs/.workbuddy/binaries/python/envs/default/Scripts/python.exe
```

裸 `python` 是另一个环境，`import playwright` 直接 `ModuleNotFoundError`。

---

## 四、项目目录约定

```
<project>/
├── storyboard.json          # 分镜脚本（根目录或 scripts/ 下都可，脚本自动找）
├── audio/                   # 旁白产物（含缓存）；audio/lab、audio/textlab 是试听台产物
├── video/                   # HyperFrames 合成
│   ├── index.html           # 由 build_video.py 生成
│   ├── assets/gsap.min.js   # 必须本地化
│   └── out/render.mp4
├── cover/                   # 封面（见 references/cover.md）
│   ├── raw.png              # 生图原图，**必须叫这个名字**（pitfalls.md P19）
│   ├── cover.png            # 后期完成（1152×1536）
│   ├── cover-1440x1920.png  # 与成片同规格
│   └── crop-1to1-preview.png
├── scripts/                 # 流水线脚本（含 scripts/voice/ 试听台）
└── out/final.mp4            # 成片
```

`build_video.py` 从 `storyboard.json` 的 `source_project` 读**数据来源**工程
（取 `content.json` 的 `full_name` / `brand` / `quote` / `steps[0].cmd`，
以及 `project.json` 的 `stargazers_count`）；缺省取 `<project>/../github-project-xhs`。

⚠️ 现在只借用它的**数据**，不再复用它的卡片 HTML（那正是旧版错位的根因）。

---

## 五、storyboard.json：唯一需要创作的文件

```json
{
  "slug": "VoiceStudio",
  "voice": "zh-CN-YunjianNeural",
  "rate": "+8%",
  "gap_after_scene": 0.4,
  "tail_pad": 0.35,
  "source_project": "D:/.../github-project-xhs",
  "scenes": [
    {
      "id": "cover",
      "label": "封面 / 钩子",
      "blocks": [
        { "id": "c1", "text": "每天一个Github热门项目，今天讲VoiceStudio。" },
        { "id": "c2", "text": "给视频配个音，云端按字扣费；想克隆声音，又怕素材传上去，对吧？" }
      ]
    }
  ]
}
```

**块 `id` 是画面定义的索引键**：`video_boards.BOARDS[id]` 提供该屏的 `html` / `js` /
`cls` / `expect`。所以：

- 分镜里有、`BOARDS` 里没有 → 直接 `SystemExit`（缺画面）。
- `BOARDS` 里有、分镜里没有 → 只打印警告，不渲染。
- `expect` 是关键词语料：构建时把该屏 HTML 转纯文本，检查这些词在不在，
  不在就提示「文案与画面可能已脱节」—— 这是防错位的第一道闸。

⚠️ 旧版 storyboard 里的 `anim` / `cue` 字段**已不再被读取**（那是锚点时代的产物，
且当年就没人读 —— 见 `pitfalls.md` P22）。
新增一屏时，改的是 `video_boards.py` + `board_css.py`，**不是** storyboard。

**硬约束**：`blocks` 里所有 `text` 顺序拼接后，去掉标点必须与配音文本逐字一致 ——
块边界定位靠字符累积匹配，不一致就只能回退按比例分配（精度下降）。

写作要点（完整规范见 `references/copywriting.md`）：

- **一个 block = 一个语义块 = 一条字幕 = 一屏画面 = 一个动画触发点**。五者合一，改稿时不会错位。
- 每块 **20–31 字**最舒服（单行上限 ≈31 汉字当量）。
- 参考语速：中文 TTS 约 5 字/秒，`rate:"+8%"` 后约 4.8 字/秒。
  总长 ≈ Σ字数 / 4.8 + 场景数 × (tail_pad + gap)，**60 秒对应约 320 字**。
- 数字写成中文（"两万九千八百星"），不要让 TTS 去读 `29.8k`。
- 英文词（Docker / beta / MCP Server）可直接写，TTS 读得对。

---

## 六、八步流水线（含两个强制确认节点）

```bash
PY=<venv python>;  NODE=<node.exe>;  HF=<project>/node_modules/hyperframes/bin/hyperframes.mjs
P=<project dir>

# 0) 清理孤儿浏览器进程 —— 每次跑 HyperFrames 前都要做（pitfalls.md P6）
#    PowerShell（Git Bash 的 taskkill 会被路径转换破坏）：
#    Get-Process chrome-headless-shell -ErrorAction SilentlyContinue | Stop-Process -Force
```

### ⚠️ 确认节点 A：口播稿定稿

写完 `storyboard.json`（含所有场景 + blocks）之后，**必须暂停并向用户展示完整口播稿**，
格式如下：

```
【口播稿 · 共 N 块，约 X 字】

[封面/钩子]
  c1：每天一个Github热门项目，今天讲{slug}。
  c2：三天建模比赛，前两天全在调代码；最后一天，全用来排版，对吧？

[定位]
  p1：它不是帮你查资料的工具，是一个能把全程跑完的建模队。
  ...

[上手/CTA]
  s4：这个先收藏，赛前装一遍。点个关注，每天一个Github热门项目。
```

**等用户明确确认（说"确认"/"OK"/"继续"等）后，才进入步骤 1。**
用户要求修改时，改完再次展示直到用户满意。

```bash
# 1) 旁白 + 时间轴 + 字幕（缓存键 = sha1(音色|语速|音量|文本)，改任一项自动失效）
"$PY" "$P/scripts/voice_synth.py"

# 2) 生成合成（内置四道校验：字体 / 逐屏越界 / 动画结束时刻 / node --check 语法）
"$PY" "$P/scripts/build_video.py"
#    末尾的 [动画] 报表逐屏给出「最晚补间结束 → 切屏时刻 → 余量」。
#    余量为负 = 这一屏的动画没演完就被切走（pitfalls.md P12）。

# 3) 占位体检 —— 查「半屏空」（pitfalls.md P4，判读口径见 references/boards.md）
"$PY" "$P/scripts/check_fill.py"
#    不传参＝全部屏；每屏在块内 35% / 85% 两个时刻各出一张 12×16 占位图。
#    脚本自动标出占位率 <45% 的屏；左右占比 <35% 或 >65% 需人工判读。

# 4) 字幕量尺 —— 确认每块 ≤ 2 行（pitfalls.md P16）
"$PY" "$P/scripts/measure_subs.py"

# 5) 字幕探针 —— 查字幕遮挡 / 元素显隐；--sync 报「本块新亮了什么」
"$PY" "$P/scripts/probe_frames.py" --all

# 6) 渲染 —— 日志重定向到文件，绝不走管道（pitfalls.md P7）
cd "$P/video"
"$NODE" "$HF" lint
"$NODE" "$HF" render -o out/render.mp4 --fps 30 --quality standard \
    --workers 4 --no-browser-gpu > render.log 2>&1

# 7) 混音（含 loudnorm 到 -16 LUFS）
#    ⚠️ render 的 -o 与 mux 的 --video 必须指向**同一个文件**（pitfalls.md P24）。
#    mux.py 已改为自动取 mtime 最新的候选渲染产物；但改稿重渲后仍必须
#    从 final.mp4 抽帧核对内容（不能只看渲染成功 —— 旧产物时长/体积几乎一样）：
#    ffmpeg -ss <块中点> -i out/final.mp4 -frames:v 1 frame.png
"$PY" "$P/scripts/mux.py"
```

**先体检、再探针、最后渲染**是这一版最重要的流程改进：

- **占位体检**查的是**画面空不空**。这类问题整条渲染完也未必看得出来
  （人眼会跟着字幕走），只有把每一屏单独拎出来看才知道。
- **字幕探针**查的是**位置撞不撞**。2 秒/帧，比整条渲染快 40 倍。

把这两类静态问题在渲染前清完，本项目因此省掉了至少四轮完整渲染（每轮约 90 秒）。

⚠️ 本机实测 **`check` 子命令会永久挂起**（即使加了 `--no-browser-gpu`），
所以流水线里不再调它，改用 `render` 作为最终判据（render 内部含 artifact validated 校验）。
GSAP 是否加载改由两道替代检查覆盖：`build_video.py` 的 `node --check` 语法预检 +
`assets/gsap.min.js` 存在且 >10KB 的断言。

可选 BGM：`mux.py --bgm music.mp3 --bgm-gain 0.16`，会自动做 sidechain 压低
（说话时音乐让路）。

```bash
# 8) 封面（可选，但要发小红书就必做）—— 详见 references/cover.md
```

### ⚠️ 确认节点 B：封面生图前

生成封面时，**必须先展示封面提示词给用户确认，并告知积分消耗**（单张约 5–10 积分），
等用户明确确认后，才调用 ImageGen 生图。

展示格式：

```
【封面生图确认】
尺寸：1152×1536（3:4）  质量：high
预计消耗：约 5–10 积分

提示词摘要：
  3:4 竖版构图，深藏青→克莱因蓝渐变背景
  中文大字「{标题}」横排居中，超粗黑体，纯白色，只出现一次
  下方亮黄色标签：「{数据标签}」
  主视觉：{主视觉道具描述}
  底座：{底座描述}
  细密声波弧线，蓝色细线
  🚫 页脚 / 徽章 / 水印一律不写进提示词（fix_cover.py 统一补，
     写了就会双份 —— pitfalls.md P26）；末尾带否定句
     「无页脚，无徽章，无水印」
  ...

确认生图请说「确认」或「继续」。
```

生图完成后，产物**立刻改名 `cover/raw.png`**，再跑 `fix_cover.py`。

---

## 七、验收标准

- [ ] `build_video.py`：`[字级] 关键词命中 N/N`（必须全中）、12 屏全部落在舞台内、
      `[动画] 所有块的动画都在切屏前演完`、`[语法] inline JS 通过 node --check`
- [ ] `check_fill.py`：每屏占位率 ≥ 45%，左右占比在 35%–65% 之间
- [ ] `measure_subs.py`：**每块字幕 ≤ 2 行**
- [ ] `probe_frames.py --all`：每块中间时刻字幕无遮挡、元素显隐符合预期
- [ ] `lint`：**0 errors**。⚠️ 实测会有约 14 条 warning，全是 Studio 可编辑性建议
      （board 缺 `id`、缺 `class="clip"`、单文件偏大），**非阻塞，不必为它改结构**。
      ⚠️ 不要为消 `clip` 警告去给 `.board` 加 `class="clip"` —— 我们的板间切换是
      GSAP 控 opacity，加了 `clip` 会让 runtime 再叠一层按时间范围隐藏，两套机制打架。
- [ ] `ffprobe`：1440×1920 / 30fps / H.264 + AAC，**音视频时长差 < 0.1s**
- [ ] 音轨电平：`volumedetect` 的 mean ≈ −17 dB、max 接近但不超过 −1 dB，无整段静音
- [ ] **从成片（`final.mp4`）抓帧复核**：探针查的是 HTML，编码后的真实像素要再确认一次
- [ ] 听一遍：确认配音与字幕一致（换音色时尤其重要，见 `pitfalls.md` P9）
- [ ] **封面** `fix_cover.py`：无 `[!]` 告警（标题顶距 ≥12.5% 且有余量、主体未侵入页脚带）、
      逐字核对画面文字（错字即重跑生图）、`crop-1to1-preview.png` 里标题完整

`contrast` 警告（WCAG AA）来自设计令牌的浅色系配色，PNG 静态卡片版本同样存在，
属已知情况；**不要为了消警告去改配色** —— 改了会破坏与图文版的一致性。

---

## 八、产出规格（实测）

| 指标 | 值 |
|---|---|
| 分辨率 / 帧率 | **1440×1920（3:4）** / 30fps |
| 时长 | 62.0s（12 个块，3 场景，≈320 字旁白 @ 云健 +8%） |
| 帧数 | 1862 帧 |
| 渲染耗时 | 约 1m（软件渲染 SwiftShader；`--workers 4`） |
| 成片体积 | 8.15MB |
| 旁白 | **zh-CN-YunjianNeural，rate +8%**，loudnorm 至 −16 LUFS（实测 mean −17.0dB / max −1.5dB） |
| 字幕 | 40px 白字深底胶囊，max-width 1330px，字幕带 y 1552–1788 |
| 封面 | 1152×1536 出图 → `cover-1440x1920.png` 交付；标题顶距 20.5%、底部净空 5.8%、主体下沿 y=1446（v3 实测） |

⚠️ 时长对音色/语速强敏感：同一份稿子，`Yunxi +18%` 为 50.7s，`Yunjian +8%` 为 55.7s
（旧 11 块版），换成 12 块（加评论区钩子）后为 62.0s。**换音色或改稿后必须重估时长**，
不要沿用旧数字。`timeline.json` 的 `total_duration` 是唯一权威值。
