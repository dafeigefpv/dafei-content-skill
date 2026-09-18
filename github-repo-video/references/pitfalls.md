# 坑位手册

按「症状 → 定位 → 根因 → 修复」记录实测踩到的每一个坑，附原始报错样本。

**适用架构：一屏一块（2026-09-17 起）**。若看到 `SCENE_JS` / 锚点 / `t1..t5` /
`verify_pins` / `zoom` 缩放 / `caption-zone` 这些词，说明读到的是**旧「卡片+锚点」版**，
那份已作废 —— 本文档是唯一有效的坑位记录。

环境：Windows / node 22.22.2 / hyperframes 0.8.44 pin / ffmpeg（`C:\ffmpeg\bin`）/
edge-tts 7.2.8 / Python 3.13（venv 见 P23）。

**按阶段速查**：

| 阶段 | 相关坑位 |
|---|---|
| 搭环境 | P1 P3 P23 |
| 写稿 / 分镜 | P22 |
| 合成旁白 | P8 P9 P10 |
| 画面与动画 | P4 P12 P13 P14 P15 P17 |
| 字幕 | P16 |
| 渲染 / 校验 | P1 P2 P5 P6 P7 |
| 成片 | P11 |
| 封面 | P19 P20 P21 |
| 改脚本 / 工程 | P18 |

---

## P1 渲染永久卡在 25% —— 必须 `--no-browser-gpu`

**症状**：`render` 停在 `25% Starting frame capture` 后再无进展。日志零增长、
事务目录 0 字节且 12 秒无变化、CPU 时间为 0、没有 ffmpeg 进程。

**定位**：两次采样看 CPU 时间是否变化（不变即卡死，不是慢）：

```bash
tasklist /FI "IMAGENAME eq chrome-headless-shell.exe" /FO CSV | tr -d '"' | awk -F, '{print $2, $5}'
sleep 20
tasklist /FI "IMAGENAME eq chrome-headless-shell.exe" /FO CSV | tr -d '"' | awk -F, '{print $2, $5}'
```

**根因**：默认走硬件 GPU（Intel 集显）截图路径，在此环境死锁。

**修复**：加 `--no-browser-gpu`（走 SwiftShader 软件渲染）。

| 模式 | 结果 |
|---|---|
| hardware GPU | 25% 处永久卡死（白等 17 分钟） |
| 软件渲染 | 1862 帧 / 62s 视频，**约 1m** 跑完 |

⚠️ `hyperframes doctor` 全绿、`snapshot` 也能正常跑 —— **只有 `render` 这条路径会死**。
不实测渲染就发现不了。

---

## P2 GSAP 没加载，整条时间轴不执行（lint 查不出）

**症状**：画面全静态，且字幕因初始 `opacity:0` **全部不可见**（看起来像"字幕功能没做"）。
报错样本（旧版 `check` 的 Runtime 段）：

```
✗ http_error: 404 loading assets/gsap.min.js
✗ page_error: gsap is not defined
```

**根因**：`<script src="./assets/gsap.min.js">` 指向的文件不存在。
`lint` 只做结构校验，**完全查不出资源加载失败**。

**修复**：`build_video.py` 每次运行都断言该文件存在且 >10KB，缺失则从
`video/assets/` 或 `node_modules/gsap/dist/` 拷一份。

**教训**：`lint` 通过 ≠ 能跑。（本机 `check` 挂起见 P5，所以改由构建期断言兜底。）

---

## P3 系统字体必须显式声明，否则中文回退

**症状**：`lint` 直接报错，中文排版走样（回退成通用字体）。

**根因**：CSS 用微软雅黑 / Bahnschrift 等系统字体时，渲染器认为"无法供给字型"。

**修复**：

```css
@font-face { font-family:'Microsoft YaHei'; src:local('Microsoft YaHei'), local('微软雅黑'); }
@font-face { font-family:'Bahnschrift';    src:local('Bahnschrift'), local('Bahnschrift SemiBold'); }
```

⚠️ **字体没生效时，所有实测宽度都是假的**。`measure_subs.py` / `check_fill.py`
量到的数字只有在字体正确加载时才可信 —— 所以构建期的字体检查
（`document.fonts.check`）是这两个探针的前置条件。

---

## P4 越界校验回答不了「空不空」——必须另配占位探针

**症状**：构建校验全绿（12 屏都不溢出），渲染出来才发现**半屏是白的**。

**根因**：`build_video.py` 的校验只能回答「有没有溢出」（越底 / 越右），
**回答不了「有没有半屏空」**。而一屏一块最容易犯的错恰恰是空：

- 框没提前就位（等关键词才飞入）；
- 内容等关键词点亮，前半块只有个孤立标题；
- `flex:1` 撑成 600×1200 的瘦长条；
- `margin:auto` 撑出整片空洞。

**这四种全都不越界**，所以构建校验一律通过。

**修复**：`check_fill.py` —— 把舞台 1224×1280 投到 **12×16 网格**，
逐屏输出 ASCII 占位图 + 占位率 + 左右占比。判读口径见 `boards.md`。

---

## P5 `check` 不传 `--no-browser-gpu` 会永久挂起（P1 的同一个病根）

**症状**：`hyperframes check` 输出停在

```
◆  Checking video
[INFO] [Compiler] Fetched 60 font face(s) for "JetBrains Mono" from Google Fonts …
```

之后**再无任何输出**，进程不退出、CPU 时间为 0。实测连续两次各挂 12m47s / 7m32s。

**根因**：`check --help` 写明 browser-GPU 是 `auto-detect`（默认），auto 这条路径
撞上 P1 那个硬件 GPU 死锁 —— 和 `render` 是同一个病根。

**修复（本项目定版）**：**本机直接不调 `check`**，改用 `render` 作为最终判据
（render 内部已含 artifact validated 校验）。GSAP 是否加载改由两道替代检查覆盖：
`build_video.py` 的 `node --check` 语法预检 + `assets/gsap.min.js` 存在且 >10KB 的断言。

---

## P6 孤儿浏览器进程会让下一次运行挂死

**症状**：上一次渲染明明跑完了，下一次 `render` 却一启动就卡住。

**根因**：`render` 日志里有一行
`[FrameCapture] Timed out closing browser; forcing browser process shutdown`
—— HyperFrames 关闭浏览器会超时，**每次跑完都会残留 `chrome-headless-shell.exe`**。
残留进程占着 profile / 资源，让下一次运行直接挂死。

**修复**：**每次跑 HyperFrames 之前先清一遍**（流水线第 0 步）：

```powershell
Get-Process chrome-headless-shell -ErrorAction SilentlyContinue | Stop-Process -Force
```

⚠️ Git Bash 下 `taskkill /F /IM` 会被 MSYS 路径转换破坏（报 `无效参数 '//F'`），
必须用 PowerShell 的 `Stop-Process`。

---

## P7 渲染输出不能走管道

**症状**：`render 2>&1 | tail -25` 时看不到任何进度输出，看起来像卡死（曾因此白等 17 分钟）。

**根因**：进度输出依赖 TTY，被管道缓冲憋住。

**修复**：一律 `> render.log 2>&1`，再用 `tail` / `grep` 读文件。

---

## P8 edge-tts 有频率限制，必须指数退避 + 缓存

**症状**：

```
edge_tts.exceptions.NoAudioReceived: No audio was received.
```

**规律（实测）**：连续请求时**第 3 个请求最容易被拒**。短退避（1.5/3/4.5s）连续 6 次
全败；同一文本单独重试 6 次全过 —— 说明是**限流窗口**，不是参数错误。

**修复（两条都要）**：

1. 退避按 **1.65 指数增长到 40s 封顶 + 随机抖动**，最多 8 次。
2. **缓存**：合成成功一次就把 mp3 与 marks 落盘，重跑直接复用。
   限流环境下这是主要的节省来源（调字幕时不必反复求服务端）。

另：场景之间加 4s 冷却也有帮助。

---

## P9 旁白缓存必须按「音色+语速+文本」做键，不能只按场景 id

**症状**：改了 `storyboard.json` 里的 `voice` / `rate`，重跑 `voice_synth.py` 后
字幕和动画时间轴都更新了，**但配音还是旧音色的** —— 而且**不报任何错**。

**根因**：缓存文件名若只含场景 id，只要 id 没变就 `os.path.exists(mp3)` 命中，
直接复用上一个音色的音频。改稿改了文本也一样，配音与字幕从此对不上。

**修复**：缓存键取 `sha1(voice|rate|volume|text)[:8]` 拼进文件名：

```python
ckey = hashlib.sha1(f"{voice}|{rate}|{volume}|{text}".encode("utf-8")).hexdigest()[:8]
mp3 = os.path.join(AUDIO, f"scene-{sc['id']}-{ckey}.mp3")
```

改音色 / 改语速 / 改一个字，缓存自动失效；什么都没改则照常命中。
**不要用 `--force` 绕过这个问题** —— `--force` 每次都重打服务端，限流环境下代价很高。

⚠️ 最危险的场景是「**看起来一切正常**」：画面、字幕、时长全部正确，只有人声是错的。
验收时必须**听一遍**，或核对 `timeline.json` 的 `voice` 与 `audio/` 下实际文件同批生成。

---

## P10 `boundary="WordBoundary"` 才拿得到字级时间戳

**症状**：`marks` 数量总是 0（用 `chunk["type"] == "WordBoundary"` 过滤时）。

**根因**：`Communicate` 默认 `boundary=SentenceBoundary`，只回句级标记（粒度太粗）。

**定位**：打印真实 chunk 类型，而不是猜：

```python
kinds = collections.Counter()
async for c in comm.stream():
    kinds[c.get("type")] += 1
print(kinds)   # {'SentenceBoundary': 2, 'audio': 73}
```

**修复**：`edge_tts.Communicate(text, voice, boundary="WordBoundary")`。
实测可拿到毫秒级词级标记（23 个词覆盖 8.6 秒）。

**块边界定位算法**：WordBoundary 的 `text` 顺序拼接 == 原文去标点，
因此累加字符数达到块长度时即块边界，精度到毫秒 —— 比按比例估算可靠得多。

⚠️ 改了文案必须 `voice_synth.py --force`，否则命中旧缓存、块边界与画面时间全部错位。

---

## P11 音轨必须用 `adelay` 按画面时间轴摆放，不要用 concat 累加

**症状**：音轨比视频短 1.05s（= 场景数 × `tail_pad`），且各场景旁白比画面**早**
一个 `tail_pad` 开始，越到后面漂移越大。

**根因**：画面场景起点 = `audio + tail_pad + gap`，而简单拼接的音频起点 = `audio + gap`。

**修复**：用 `adelay` 按绝对毫秒摆放（毫秒值直接取自 timeline 的 `scene.start`，
与画面同源），再 `amix` 合并，末尾 `apad` 补齐：

```
[i:a]aresample=48000,adelay=<start_ms>:all=1[a_i]; … amix=inputs=N:normalize=0:duration=longest[m];
[m]apad=whole_dur=<total_duration>[a]
```

**验收**：`ffprobe` 比音视频时长，差应 < 0.1s（实测 0.01s）。

---

## P12 动画必须「起始 + 时长」都落在块内 —— 正则检查抓不住

**症状**：画面不溢出、日志无报错、lint 全绿，但**观众看不到这一屏的最终态**。

**实例（真事故）**：c3 星数滚动在 `+4.29s` 起、时长 `1.7s` → 止于 15.63s，
而该屏 **15.27s 就切走了**。观众看到的数字停在 **26k** 左右，
**永远不会出现那个正是全片卖点的 29,788**。

**根因**：`build_video.py` 早期用一条正则扫生成的 JS，抓末尾位置参数当「动画时刻」——
但那只拿到补间的**起始**时间。时长写在 vars 对象里、起始写在尾部位置参数里，
正则无法可靠配对，于是**「起始 + 时长」超过块末**这一类缺陷全部漏掉。

**修复**：**问 GSAP 自己**。构建后到浏览器里遍历 `tl.getChildren()`，
对每条补间取 `startTime() + duration()` 得真实结束时刻，再按目标归属到块：

- DOM 目标 → 取最近的 `[data-b]` 祖先；
- 普通对象目标（数字滚动的 `{v:0}`）→ 按其起始时刻落在哪一块里；
- 目标是 `.board` 本身（板间淡入淡出）或外壳元素（进度轨 / 顶栏 / 底栏）→ **跳过**。

⚠️ 外壳元素不跳过会被按时刻误算到某一块头上，报出「进度轨补间超出 c1 十一秒」这种假警报。

**修法只有三条**：缩短时长 / 提前起点 / 延长该块旁白。
改完必须看 `[动画]` 报表里该块的「余」为正（逐屏给「起 / 时长 / 止 / 切屏 / 余」）。

**排动画的顺序**：先算剩余时间，再定时长 —— 从关键词被念到的时刻到块末，
就是这条动画的时间预算。

---

## P13 灰调占位不能用 `gsap.from({opacity:0})`

**症状**：给「打底帧」的灰调占位（如 s4 关注条 `opacity:.28`、p4 徽标 `opacity:.26`）
写了 `tl.from(el, {opacity:0})` 之后，**占位态整个消失，前半块又空了**。

**根因**：GSAP 的 `from()` 默认 `immediateRender:true`，tween 一创建就立即把元素
设成起始值 —— `tl.seek(0)` 时它就已经是 **opacity:0**。

**修复**：

```js
gsap.set(el, {opacity:.28});              // 定住占位态
tl.to(el, {opacity:1, duration:.4}, @@W:关键词@@);   // 念到才转实
```

⚠️ 同源的坑：波形用 `from({scaleY:.05})` 在 seek(0) 时会被压成一条几乎不可见的细线，
看起来像虚线分割线 —— 所以要显式 `gsap.set(..., {backgroundColor:'#e4e8f1'})`
给一个可见的灰调底色，点亮时 `tl.to(..., {backgroundColor:'#002fa7'})`。

---

## P14 容器级 `from(opacity:0)` 会吞掉子元素的逐条动画

**症状**：给整块容器做淡入后，里面几条子元素同时全部可见；
后面给子元素写的逐条动画只是**重复淡入一次**，观众看不出任何新信息。

**根因**：父容器 opacity 0→1 之后，子元素自己的 opacity 动画即使没跑，也随父容器可见。

**修复**：容器常驻，**逐个子元素控制**：

```js
// ✗ 不要
tl.from(container, {opacity:0, y:24, duration:.44}, @@S@@);
// ✓ 改为：容器不动，只对子元素做
tl.from(c + '.label', {opacity:0, y:-12, duration:.36}, @@S@@);
mark(c + '.item1', @@W:第一项@@);
```

---

## P15 动画落在「本屏看不见的元素」上 ＝ 静默空转

**症状**：`[动画]` 报表显示某块动画正常演完，但画面上什么都没发生。

**根因**：GSAP 对不可见元素照样跑（computed opacity 真的变了），
但元素本身在别的板里、或被 `visibility:hidden` / `opacity:0` 按住，
**用户永远看不到**。这类空转不报错，lint 也查不出。

**定位**：用 `probe_frames.py --sync` —— 它输出每块「新亮了什么」，
若某块显示「本块期间画面没有任何元素新亮起」，就是空播或空转。

**修复**：换一个「还在本屏画面上」的目标。选目标时的判据：
**它是本块语义的行动指引吗？** 是，才配得上做点亮目标。

---

## P16 字幕：独占一条带 + 单行上限 ≈31 汉字当量

**症状（旧版）**：字幕在某些时刻折成两行，第二行掉进底部内容里压住东西；
而别的时刻又是单行 —— 抽查几帧未必发现。

**新版已从结构上解决**：字幕带独占 y 1552–1788（236px），舞台在 y 1520 就结束，
**两者物理隔离，不存在遮挡的可能**。代价是舞台矮了 236px，这是值得付的。

**剩余约束：单行上限 ≈31 汉字当量**。40px + `letter-spacing:.3px`、
净宽 1266px（`max-width` 1330 − 左右 padding 64）下，实测
**31 个汉字 = 1249px（占 99%）**，第 32 个汉字就折行。

- 单行最好看；折成两行仍放得下（带高 236px，两行约 137px），所以不算致命。
- **超限时换更短的口语词，不要缩字号**（字号是量过的硬约束）。
- 写完用 `measure_subs.py` 逐条核，别肉眼估。

⚠️ `measure_subs.py` 量「单行自然宽度」时必须**同时解封 `white-space` 和 `max-width`**，
否则 `max-content` 被 `max-width` 截断，量到的永远是框宽这个饱和值。

**字幕类名必须用 `.cap`，不要用 `.sub`**。旧版用 `.sub`，与卡片封面副标题的
`<p class="sub">` 撞名 —— 字幕规则的 `opacity:0` 生效，导致封面副标题
**从来没在视频里出现过**（特异性更高的 `.cover .sub` 没声明 opacity，压不住）。
`probe_frames.py` 里的选择器也要同步，漏了就探针失效。

---

## P17 布局问题只能在布局层解决，不要用 `zoom` / 整体缩放兜底

**症状**：内容溢出画布，或补间位置整体偏移。

**根因**：旧卡片版靠 `document.body.style.zoom` 把超长内容塞进画布，结果
**`zoom` 与 GSAP 的 `transform` 互相污染**：补间位置全偏，且偏移量随缩放比变化，极难定位。

**修复**：新版的边界是**硬边界** —— 舞台固定 1224×1280，`*{box-sizing:border-box}`，
内容排不下就改版面（缩字号、换横排、拆屏），**不引入任何全局缩放**。

⚠️ 越界检查**必须用 `offsetTop` / `offsetHeight` 而不是 `getBoundingClientRect()`**：
页面加载时 `tl.seek(0)`，所有 `from` 补间的「起始态」已被应用（`y:30` 之类），
包围盒会被位移撑大，报出并不存在的溢出。`offset*` 是布局值，与 transform 无关。

---

## P18 编辑这类构建脚本时，不要只信编辑器的"成功"

**症状**：`Edit` 工具对本项目的脚本**多次报成功但内容未落盘**。

**修复**：

- 改完立即 `grep` 核对目标字符串确实在文件里。
- 关键改动直接用 Python 读写文件替换，并 `assert old in s`。
- 含 `\n` 的字符串在多层转义（JSON → shell heredoc → Python 源码）下极易被写成
  **真实换行**，导致字符串跨行截断。写完必须 `python -m py_compile` 验语法。

⚠️ 两个真实事故：

1. `board_css.py` 写好后 `build_video.py` **仍在从 `scene_kit` 导入旧的 `BOARD_CSS`**，
   于是新样式一行都没生效，且没有任何报错。**新增模块后要确认导入点真的换了。**
2. 脚本有**两份副本**（skill 与项目）。Edit 落在 skill 副本、项目跑的是旧脚本 ——
   改完必须 `cp` + `diff -q` 逐个核对。

---

## P19 封面源图必须固定叫 `raw.png`，不能用 glob 排序去找

**症状**：重跑封面后，输出的是**上一版的图**。

**根因**：生图产物的文件名带时间戳（`3_4_竖版构图_..._2026-09-17T09-31-20.png`）。
`sorted(glob.glob("3_4_竖版构图*.png"))[0]` **比的是文件名字符串，不是时间** ——
旧图时间戳数字更小，反而排在前面，于是脚本拿上一版当输入重跑一遍，
输出却是新文件名，看不出任何异常。实测差点中招。

**修复**：约定 —— 生图后第一件事就是把产物改名为 **`cover/raw.png`**，
`fix_cover.py` 固定读它（不再 glob）。

---

## P20 去平台水印要用「中值差分」，扩散不能用 `np.roll`

**症状**：水印去不干净，或去完留下热点 / 暗斑。

**定位与修复**：

- **定位**：水印是浅灰白字（灰度峰值 ~154），深蓝背景仅 ~33。
  但**绝对阈值**（如 `min(channel) > 140`）只命中 **8 px** —— 被抗锯齿的过渡像素绕过。
  改用**中值差分**（`gray − MedianFilter(15) > 9`）只问「比周围亮多少」，对渐变背景也稳。
  另加一道保险：ROI 内命中率 >12% 时判定「可能把真实内容当成了水印」并跳过。
- **修补**：Jacobi 扩散（900 轮）+ 补回背景颗粒（sigma 从干净区实测）。

⚠️ **邻居计算不能用 `np.roll`** —— 它会在数组边界**环绕**、把对边像素拉过来，
在右下角留下一块热点 + 一排暗像素。必须用 `np.pad(mode='edge')` 钳制边界。

---

## P21 页脚不能套 10% 安全区，必须贴底；体检要在画页脚**之前**做

**症状**：页脚文字压在主体上；或体检报「底部净空 2%」这个假警报。

**背景**：生图模型只画「标题 + 星数 + 主视觉」，**不会写项目名** ——
观众不知道讲哪个项目，必须后期补。

**三条修法**：

- **贴底**：主体下沿离底边通常远不到 10%（实测 v2 只有 13.2%），按 10% 安全区放字
  **会直接压在主体上**。页脚按「基线 `H − 2.2%H`」贴底，字号取 `H` 的 2.3% / 1.3%。
- **体检顺序**：底部净空必须在**画页脚之前**测量，否则页脚自己的字会被当成主体内容，
  净空必然报成 2%（实测踩过这个假阴性）。
- **判据**：不要用固定亮度阈值（`g>60` 会把**地面反光**当主体，报净空 2.5%）。
  用**背景中位数 + 55**，正好卡在实体边缘。硬判据是「**主体是否侵入页脚带**」，
  净空 <10% 只作美观提示 —— 页脚落得下就是合格。

---

## P22 假接口：storyboard 里的 `anim` / `cue` 不被任何代码读取

**症状**：写稿的人以为 `anim` / `cue` 就是画面锚点声明，改了之后画面毫无变化。

**根因**：`build_video.py` **从不读取这两个字段**，旧版的真实映射是硬编码的块序号
（`t1..t5`）。**这是「文案与画面不匹配」的制度性根源** —— 文案变了，画面不会跟着变。

****新架构的解法**：这两个字段**已从 storyboard 删除**，画面改由
`video_boards.BOARDS[id]` 按块 id 索引，一个语义块一句一屏，映射关系不复存在。
`expect` 字段承载「这一屏该出现哪些关键词」，逐屏校验，是防错位的第一道闸。

⚠️ **不要重新引入声明式画面字段**。若将来要加，加的方式必须是
「**代码真的读它**」——否则又是一个假接口。

---

## P23 环境：解释器、PATH shim、HyperFrames 位置

```bash
# 本机 bash 的 PATH 被裁剪，dirname/tail/head 会报 command not found。
# 每条命令开头加：
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
```

**必须用带 playwright 的解释器**：

```
C:/Users/lgs/.workbuddy/binaries/python/envs/default/Scripts/python.exe
```

裸 `python` 是另一个环境（3.13.12），`import playwright` 直接 `ModuleNotFoundError`。

**HyperFrames 装在项目自己的 `node_modules`**，**不是**共享位置：

```
<project>/node_modules/hyperframes/bin/hyperframes.mjs
```

换项目要重新 `npm install hyperframes@0.8.44 --save-exact`，或把 `node_modules`
一起拷过去。调用时务必用绝对路径，写成 `<vendor>/...` 会 `MODULE_NOT_FOUND`。

**环境探测结果（首版实测）**：

```
node                22.22.2（托管版）
hyperframes         0.8.44（半年发了 397 个版本，务必 pin）
Chrome              复用系统 Chrome（无需下载 114MB 无头浏览器）
CPU                 Intel Core 5 220H / 16 逻辑核
内存                31.7 GB
GPU                 ⚠️ 无独显（Intel 集显 + Honor 虚拟显示器）
                    → 本地开源 TTS（IndexTTS2 / CosyVoice2）不可行，需租云 GPU
edge-tts zh-CN 语音  6 个普通话 + 2 方言 + 6 港台；Azure 专属音色全不可用
ffmpeg              C:\ffmpeg\bin\ffmpeg.exe
python venv         C:\Users\lgs\.workbuddy\binaries\python\envs\default
```

## P24 · mux 静默拿到旧渲染产物（2026-09-18 MathModelAgent 实测）

`mux.py` 默认读 `video/out/render.mp4`。若本次 render 用 `-o renders/raw.mp4` 输出，
混音仍会拿**上一次会话的旧视频**——体积/时长恰好接近（新旧文案总时长差 <1s），
`[done]` 一切正常，但成片画面全是旧的（字幕和画面都对新稿）。

- **判据**：从 final.mp4 用 ffmpeg 抽帧（-ss 块中点）人眼核对；时间戳相同不代表内容相同。
- **修复**：mux.py 已改为在候选（video/out/render.mp4、renders/raw.mp4）里取
  os.path.getmtime **最新**者，并打印 `[!] 改用更新的渲染产物`。
- **纪律**：render 的 `-o` 与 mux 的 `--video` 必须指向同一文件；改完文案必须抽帧验证，不能只看渲染成功。

## P25 · chars() 拆字吞空格（终端命令显示成 npxskillsadd…）

`scene_kit.chars()` 把每个字符包成 `<span class="tm"> </span>`，夹在 inline span
之间的普通空格被 HTML 折叠，`npx skills add xxx --all` 显示成 `npxskillsaddxxx--all`。

- **修复**：chars() 里空格输出 `&nbsp;`（scene_kit.py 已改，2026-09-18）。
- **同族排查**：任何逐字拆分（typewriter/逐字入场）凡含空格的拉丁串都要用 NBSP。
## P26 · 生图提示词含页脚 → 成图双份页脚/徽章（2026-09-18 MathModelAgent 实测）

封面提示词里写了「页脚左=项目名、右=系列徽章」，生图模型把它画进图里；
随后 `fix_cover.py` 又按规范补了一次页脚 —— 成图上标题画两遍、徽章两份，
右下水印还被模型仿了个假的。

- **分工铁律**：页脚 / 徽章 / 水印**只出现在 fix_cover.py 的后期里**，
  生图提示词一律不写，且末尾带否定句「无页脚，无徽章，无水印」；
  标题要写「只出现一次」（模型有画两遍标题的倾向）。
- **修复**：重跑生图（提示词去掉页脚）→ 改名 raw.png → fix_cover.py。
  体检通过：标题顶距 15.4%、底部净空 16.5%。
