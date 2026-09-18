# -*- coding: utf-8 -*-
"""
视频合成装配器（3:4 / 1440×1920 / 一屏一块）。

职责
----
1. 读 storyboard.json（文案 + 音色）与 timeline.json（旁白实测时间）
2. 从 audio/*.marks.json 取**字级时间戳**，把动画触发点绑到具体的词上
3. 拼出 index.html：HUD / 进度轨 / 12 屏画面 / 独占字幕带 / 底栏
4. 用浏览器校验：每块都有画面、画面里有关键词、内容不溢出、字体可用
5. 写 hyperframes 需要的 meta.json / hyperframes.json

与旧版（卡片 + 锚点映射）的根本区别
----------------------------------
旧版把 github-project-xhs 的静态卡片搬进视频，再用「锚点」把动画挂到卡片里
已有的元素上。卡片的排版是为图文服务的（一页塞满、可停留回看），所以画面
永远在讲它自己那套内容 —— 文案改了、画面跟不上，是结构性的，不是手误。

本版为每一句口播单独设计一屏画面（见 video_boards.py），并把触发点绑到
**字级时间戳**上：说「五个月」时时间轴才划出，说「两万九千八百」时数字才
开始滚，说「克隆」时六宫格第一格才亮。映射关系不复存在，也就无从错位。

用法
----
    python scripts/build_video.py            # 生成 + 校验
    python scripts/build_video.py --no-check # 跳过浏览器校验（快）
"""
import json
import re
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "video"
sys.path.insert(0, str(HERE))

from board_css import BOARD_CSS
from scene_kit import (COMP_CSS, FOOT_TOP, H, MARGIN, SHELL_CSS,
                       STAGE_H, STAGE_W, TOKENS, W)
import video_boards
from video_boards import BOARDS, build_html, fill  # noqa: E402

NO_CHECK = "--no-check" in sys.argv

# ------------------------------------------------------------------ 标点口径
# 必须与 voice_synth.py 完全一致，否则块边界会错位
PUNCT = "，。、；：！？""''（）《》〈〉——…·,.!?;:\"'()[]{}<>-~　 \n\r\t"
CLEAN = str.maketrans("", "", PUNCT)


def clean(s: str) -> str:
    return s.translate(CLEAN)


# --------------------------------------------------------------- 载入输入
def find_storyboard(root: Path) -> Path:
    # 目录名历史上叫过 script/，现为 scripts/。四种都认，任何一个位置放对就行。
    for c in (root / "storyboard.json",
              root / "scripts" / "storyboard.json",
              root / "script" / "storyboard.json",
              HERE / "storyboard.json"):
        if c.exists():
            return c
    raise SystemExit(f"[x] 在 {root} 找不到 storyboard.json")


SB = json.loads(find_storyboard(ROOT).read_text(encoding="utf-8"))
TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))

PJ = Path(SB.get("source_project") or (ROOT.parent / "github-project-xhs")).resolve()
content = json.loads((PJ / "content.json").read_text(encoding="utf-8"))
try:
    proj = json.loads((PJ / "project.json").read_text(encoding="utf-8"))
except Exception:  # noqa: BLE001
    proj = {}

repo = content.get("full_name") or SB.get("repo", "")
# ⚠️ fetch_project.py 写出的 project.json 是 {"date":…, "repo":{…, "stars":N}}，
# 星数在 repo.stars 下。旧代码读的是顶层 stargazers_count —— 永远读不到，
# 于是**所有项目都会静默显示 29,788**（那恰好是 VoiceStudio 的星数，看着对，
# 其实纯属巧合）。这种"错得刚好看不出来"的默认值比报错危险得多，所以：
# 读不到就显式失败，不要兜底。
_r = proj.get("repo") if isinstance(proj.get("repo"), dict) else {}
_stars = proj.get("stargazers_count") or _r.get("stars") or SB.get("stars")
if not _stars:
    raise SystemExit(
        f"[x] 读不到星数：请在 {PJ / 'project.json'} 里补 repo.stars，"
        f"或给 storyboard.json 加 stars 字段")
stars = int(_stars)
DATA = dict(
    repo=repo,
    repo_short=repo.split("/")[-1],
    brand=content.get("brand", "@大飞的AI赋能笔记"),
    stars=stars,
    stars_k=(f"{stars/1000:.1f}k" if stars >= 1000 else str(stars)),
    quote_en=content.get("quote", ""),
    cmd=content["steps"][0]["cmd"],
    typewriter_cmd=True,
)
print(f"[数据] repo={repo} stars={stars:,} brand={DATA['brand']}")


# --------------------------------------------------- 字级时间戳 → 词级时刻
def scene_index():
    """场景 id -> (marks 列表, {块 id: 块内首个 mark 的下标范围})"""
    out = {}
    for sc in TL["scenes"]:
        mj = ROOT / sc["audio"].replace(".mp3", ".marks.json")
        if not mj.exists():
            out[sc["id"]] = (None, {})
            continue
        marks = json.loads(mj.read_text(encoding="utf-8"))
        joined = "".join(m["text"] for m in marks)
        # 每个词 mark 覆盖的字符区间
        acc, spans = 0, []
        for m in marks:
            spans.append((acc, acc + len(m["text"])))
            acc += len(m["text"])
        # 每块在 joined 里的字符区间（与 voice_synth.locate_blocks 同口径）
        pos, blocks = 0, {}
        sb_sc = next(s for s in SB["scenes"] if s["id"] == sc["id"])
        for b in sb_sc["blocks"]:
            n = len(clean(b["text"]))
            j0 = next((i for i, (s, e) in enumerate(spans) if e > pos), 0)
            blocks[b["id"]] = (pos, pos + n, j0)
            pos += n
        if pos != len(joined):
            print(f"    ! [{sc['id']}] 字符合计 {pos} vs 配音 {len(joined)}")
        out[sc["id"]] = (marks, blocks)
    return out


IDX = scene_index()
# 块 id -> 该块各关键词的绝对时刻（秒）
WORD_T: dict[str, dict[str, float]] = {}

for sc in TL["scenes"]:
    marks, blocks = IDX.get(sc["id"], (None, {}))
    for b in sc["blocks"]:
        bid = b["id"]
        WORD_T[bid] = {}
        if not marks or bid not in blocks:
            continue
        c0, c1, j0 = blocks[bid]
        joined = "".join(m["text"] for m in marks)
        spans, acc = [], 0
        for m in marks:
            spans.append((acc, acc + len(m["text"])))
            acc += len(m["text"])
        # 该块覆盖的 marks
        rel_marks = [m for m, (s, e) in zip(marks, spans) if s >= c0 and e <= c1]
        if not rel_marks:
            continue
        # 逐关键词定位（按出现顺序推进游标，避免重复命中同一个词）
        kws = re.findall(r"@@W:([^@|]+?)(?:\|[0-9.]+)?@@", video_boards.BOARDS[bid]["js"])
        cursor = c0
        for kw in kws:
            p = joined.find(kw, cursor, c1)
            if p < 0:
                p = joined.find(kw, c0, c1)
            if p < 0:
                continue
            cursor = p + len(kw)
            hit = next((i for i, (s, e) in enumerate(spans) if s <= p < e), None)
            if hit is None:
                continue
            t_rel = marks[hit]["start"] - marks[j0]["start"]
            WORD_T[bid][kw] = round(b["start"] + max(0.0, t_rel), 3)

# 报告词级命中情况
tot_kw = sum(len(WORD_T[b]) for b in WORD_T)
all_kw = sum(len(set(re.findall(r"@@W:([^@|]+?)(?:\|[0-9.]+)?@@", BOARDS[b]["js"])))
             for b in BOARDS)
print(f"[字级] 关键词命中 {tot_kw}/{all_kw}")
for sc in TL["scenes"]:
    for b in sc["blocks"]:
        keys = WORD_T.get(b["id"], {})
        if keys:
            rel = "  ".join(f"{k}=+{v-b['start']:.2f}s" for k, v in keys.items())
            print(f"    {b['id']:<3} {rel}")


def resolve_tokens(js: str, bid: str, bstart: float, bdur: float) -> str:
    """把 @@S@@ / @@W:关键词|fallback@@ 解析成秒数。"""
    js = js.replace("@@S@@", f"{bstart:.3f}")

    def rep(m):
        kw, fb = m.group(1), m.group(2)
        t = WORD_T.get(bid, {}).get(kw)
        if t is None:
            t = bstart + (float(fb) if fb else 0.5) * bdur
            return f"{t:.3f}  /* !未命中:{kw}->比例 */"
        return f"{t:.3f}"

    return re.sub(r"@@W:([^@|]+?)(?:\|([0-9.]+))?@@", rep, js)


# --------------------------------------------------------- 拼装 12 屏画面
board_html, board_js, anim_end_warn = [], [], []
blocks_all = [(sc, b) for sc in TL["scenes"] for b in sc["blocks"]]
ids_sb = [b["id"] for _, b in blocks_all]

missing = [i for i in ids_sb if i not in BOARDS]
orphan = [k for k in BOARDS if k not in ids_sb]
if missing:
    raise SystemExit(f"[x] 这些块没有对应的画面定义: {missing}")
if orphan:
    print(f"[!] 有画面定义但不在分镜里（不会渲染）: {orphan}")

for i, (sc, b) in enumerate(blocks_all):
    bid = b["id"]
    spec = BOARDS[bid]
    cls = (" " + spec["cls"]) if spec["cls"] else ""
    html = build_html(bid, DATA)
    # 校验：画面里必须出现该块口播的关键词
    txt = re.sub(r"<[^>]+>", "", html)
    gone = [k for k in spec["expect"] if k not in txt]
    if gone:
        print(f"[!] {bid} 画面缺少关键词 {gone} —— 文案与画面可能已脱节")
    board_html.append(
        f'<div class="board b-{bid}{cls}" data-b="{bid}" '
        f'data-start="{b["start"]}" aria-label="{bid}">\n{html}\n</div>')
    js = fill(spec["js"].strip(), DATA)
    js = resolve_tokens(js, bid, b["start"], b["end"] - b["start"])
    left = re.findall(r"@@[^@]+@@", js)
    if left:
        raise SystemExit(f"[x] {bid} 的 JS 里还有未解析的令牌 {left}"
                         f" —— 生成的 JS 会语法错误、时间轴不注册")
    board_js.append(f"/* ---------------- {bid}  {b['text'][:26]} */\n{js}")

    # 起始时刻粗筛：动画的**起始**位置参数若已晚于块末+停顿，肯定有问题。
    # ⚠️ 这只是粗筛。「起始 + 时长」才是一次补间的真正结束时刻，而时长写在
    # vars 对象里、起始写在末尾位置参数里，正则无法可靠配对 —— 曾经因此漏掉
    # c3 星数滚动（起 +4.29s、时长 1.7s）溢出块末 0.37s 的缺陷：
    # 观众看到的数字停在 26k 就切屏了，永远到不了 29,788。
    # 真正的「结束时刻」检查交给浏览器侧的 GSAP introspection（见文件末尾）。
    tail = b["end"] + b.get("gap_to_next", 0)
    starts = [float(x) for x in re.findall(r",\s*(-?[0-9]+\.[0-9]+)\)", js)]
    if starts and max(starts) > tail + 0.35:
        anim_end_warn.append((bid, max(starts), round(tail, 2)))

if anim_end_warn:
    print("[!] 动画起始时刻已越界（起始 > 块结束+停顿）:")
    for bid, mx, tail in anim_end_warn:
        print(f"    {bid}: 最晚起始 {mx:.2f}s > {tail}s")


# -------------------------------------------------------------- 进度轨分幕
ACTS = [("开场", 0, 3), ("定位", 3, 4), ("能力", 4, 7), ("上手", 7, 12)]
rail_html, rail_js = [], []
for name, i0, i1 in ACTS:
    rail_html.append(f'<div class="rag" data-rag="{name}">'
                     f'<div class="rag-k">{name}</div><div class="rag-b"><i></i></div></div>')
    t0 = blocks_all[i0][1]["start"]
    t1 = blocks_all[i1 - 1][1]["end"] + blocks_all[i1 - 1][1].get("gap_to_next", 0)
    # 用 % 格式化而不是 f-string：JS 里大量花括号，f-string 转义极易出错
    rail_js.append(
        "tl.to('[data-rag=\"%s\"] .rag-b > i',"
        "{width:'100%%',duration:%.2f,ease:'none'},%.3f);\n"
        "tl.to('[data-rag=\"%s\"] .rag-k',"
        "{color:'#002fa7',duration:.3,ease:'none'},%.3f);"
        % (name, max(0.4, t1 - t0 - 0.5), t0, name, t0))

rail_start = blocks_all[0][1]["start"]


# -------------------------------------------------------------- 字幕时间轴
subs = [(b["text"], b["start"], b["end"]) for _, b in blocks_all]
subs_html = "\n".join(
    f'<div class="cap" data-i="{i}"><span>{t}</span></div>'
    for i, (t, _, _) in enumerate(subs))
sub_js = "\n".join(
    f"tl.fromTo(subs[{i}],{{opacity:0}},{{opacity:1,duration:0.12}},{st:.3f});\n"
    f"tl.to(subs[{i}],{{opacity:0,duration:0.14}},{en + 0.28:.3f});"
    for i, (_, st, en) in enumerate(subs))


# --------------------------------------------------------- 板间切换 + 外壳
fade_js = []
for i, (sc, b) in enumerate(blocks_all):
    if i == 0:
        fade_js.append(f"tl.set('[data-b=\"{b['id']}\"]',{{opacity:1}},0);")
        continue
    prev = blocks_all[i - 1][1]["id"]
    st = b["start"]
    fade_js.append(
        f"tl.to('[data-b=\"{prev}\"]',{{opacity:0,duration:0.20,ease:'power1.in'}},"
        f"{max(0.0, st - 0.20):.3f});\n"
        f"tl.set('[data-b=\"{b['id']}\"]',{{opacity:1}},{st:.3f});")
fade_js = "\n".join(fade_js)

SHELL_ANIM = f"""
/* ---------------- 外壳：顶栏 / 进度轨 / 底栏 ---------------- */
tl.from('.hud-badge',{{opacity:0,y:-18,duration:.5,ease:'power2.out'}},0.10);
tl.from('.hud-r > *',{{opacity:0,y:-14,duration:.44,stagger:.12}},0.34);
tl.from('.rag',{{opacity:0,duration:.4,stagger:.08}},0.5);
tl.from('.footbar > span',{{opacity:0,duration:.5,stagger:.2}},0.7);
"""

# 「念到哪一项哪一项亮」的统一入口：各块 JS 里写 mark(sel, @@W:关键词@@)，
# 到点给元素加 .on 类，颜色由 board_css 里的 transition 平滑过渡。
# 不直接在 JS 里 tween 颜色，是因为颜色值分散在多条 CSS 规则里（含后代选择器），
# 用类切换才能一处定义、整体生效。
JS_PRELUDE = """
function mark(sel, t){
  tl.call(function(){
    var e = document.querySelector(sel);
    if (e && e.classList) e.classList.add('on');
  }, null, t);
}
"""

TIMELINE_JS = f"""
var TOTAL = {TL['total_duration']:.3f};
var tl = gsap.timeline({{ paused:true }});
{JS_PRELUDE}
{SHELL_ANIM}
{''.join(rail_js)}

/* ---------------- 板间切换（一屏一块） ---------------- */
{fade_js}

/* ---------------- 各块画面编排 ---------------- */
{chr(10).join(board_js)}

/* ---------------- 字幕 ---------------- */
var subs = Array.from(document.querySelectorAll('#subs .cap'));
{sub_js}

window.__timelines = window.__timelines || {{}};
window.__timelines['repo-video'] = tl;
tl.seek(0);
"""

BOARD_CLS_CSS = "\n".join(
    f'.b-{bid}{(" " + BOARDS[bid]["cls"]) if BOARDS[bid]["cls"] else ""}'
    + (f' {{ display:flex; }}')
    for bid in BOARDS)

INDEX = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <script src="./assets/gsap.min.js"></script>
    <style>
{TOKENS}
{SHELL_CSS}
{COMP_CSS}
{''.join(BOARD_CSS[k] for k in BOARDS)}
    </style>
  </head>
  <body>
    <div id="stage" data-composition-id="repo-video" data-start="0"
         data-duration="{TL['total_duration']:.3f}"
         data-width="{W}" data-height="{H}">
      <div class="hud">
        <span class="hud-badge">每天一个Github热门项目</span>
        <div class="hud-r">
          <span class="hud-repo">{DATA['repo']}</span>
          <span class="hud-star">★ {DATA['stars_k']}</span>
        </div>
      </div>
      <div class="rail">{''.join(rail_html)}</div>
{chr(10).join(board_html)}
      <div id="subs">
{subs_html}
      </div>
      <div class="footbar">
        <span>{DATA['brand']}</span>
        <span>github.com/{DATA['repo']}</span>
      </div>
    </div>
    <script>
{TIMELINE_JS}
    </script>
  </body>
</html>
"""

OUT.mkdir(parents=True, exist_ok=True)
ASSETS = OUT / "assets"
ASSETS.mkdir(exist_ok=True)
gsap_dst = ASSETS / "gsap.min.js"
if not gsap_dst.exists() or gsap_dst.stat().st_size < 10000:
    for c in (ROOT / "video" / "assets" / "gsap.min.js",
              ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"):
        if c.exists() and c.stat().st_size > 10000 and c != gsap_dst:
            shutil.copyfile(c, gsap_dst)
            break
assert gsap_dst.exists() and gsap_dst.stat().st_size > 10000, \
    "[x] assets/gsap.min.js 缺失或异常 —— 时间轴会静默失效（画面全静态、字幕全不可见）"
(OUT / "index.html").write_text(INDEX, encoding="utf-8")
print(f"\n[写出] {OUT/'index.html'}  ({len(INDEX)/1024:.0f} KB)")

# 语法预检：inline JS 里任何一个错字都会让整条时间轴不注册，
# 而表现只是「画面全静态、字幕全不可见」，从渲染日志里完全看不出原因。
def node_check(js: str) -> bool:
    node = shutil.which("node") or str(Path(
        r"C://Users//lgs//.workbuddy//binaries//node//versions//22.22.2-3//node.exe"))
    if not Path(node).exists() and not shutil.which("node"):
        print("[语法] 跳过（找不到 node）")
        return True
    tmp = OUT / "_timeline_check.js"
    tmp.write_text(js, encoding="utf-8")
    import subprocess as sp
    r = sp.run([node, "--check", str(tmp)], capture_output=True, text=True)
    tmp.unlink(missing_ok=True)
    if r.returncode == 0:
        print("[语法] inline JS 通过 node --check")
        return True
    print("[语法] inline JS 有错：\n" + (r.stdout + r.stderr)[:900])
    return False


_tl_ok = node_check(TIMELINE_JS)
if not _tl_ok:
    raise SystemExit("[x] 时间轴 JS 语法检查失败，先修再渲染")

(OUT / "meta.json").write_text(json.dumps(
    {"id": "repo-video", "name": f"{DATA['repo_short']} · 每天一个Github热门项目"},
    ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "hyperframes.json").write_text(json.dumps({
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "paths": {"blocks": "compositions", "components": "compositions/components",
              "assets": "assets"},
    "media": {"autoProxy": True},
}, indent=2), encoding="utf-8")

print(f"[规格] {W}x{H} (3:4) | 总时长 {TL['total_duration']}s | "
      f"{len(blocks_all)} 块 / {len(set(b['id'] for _, b in blocks_all))} 屏")


# ------------------------------------------------------- 浏览器侧校验
def launch(p):
    last = None
    for kw in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


if NO_CHECK:
    sys.exit(0)

print("\n[校验] 启动浏览器核对版面 ...")
with sync_playwright() as p:
    br = launch(p)
    pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    pg.goto("file:///" + str(OUT / "index.html").replace("\\", "/"))
    pg.wait_for_timeout(1200)

    fonts = pg.evaluate("""() => {
      const f = ['Bahnschrift','Microsoft YaHei','Cascadia Mono','Consolas'];
      return f.map(n => [n, document.fonts.check('900 60px "'+n+'"')]);
    }""")
    print("[字体] " + "  ".join(f"{n}={'OK' if ok else '缺失'}" for n, ok in fonts))

    rep = pg.evaluate("""(ids) => ids.map(id => {
      const el = document.querySelector('[data-b="'+id+'"]');
      // ⚠️ 必须用 offsetTop/offsetHeight，不能用 getBoundingClientRect：
      // 页面加载时 tl.seek(0)，所有 from 补间的「起始态」已被应用
      // （y:30 之类），包围盒会被位移撑大，报出并不存在的溢出。
      // offset* 是布局值，与 transform 无关。
      let bot = 0, right = 0;
      for (const c of el.children) {
        if (c.hasAttribute('data-deco')) continue;   // 装饰层（整屏色块）不计
        if (!c.offsetParent || c.offsetWidth === 0 && c.offsetHeight === 0) continue;
        bot   = Math.max(bot,   c.offsetTop  + c.offsetHeight);
        right = Math.max(right, c.offsetLeft + c.offsetWidth);
      }
      return { id: id, h: el.offsetHeight, need: Math.round(bot),
               over: Math.round(bot - el.offsetHeight),
               wide: Math.round(right - el.offsetWidth) };
    })""", [b["id"] for _, b in blocks_all])

    # ------------------------------------------------ 动画结束时刻（真检）
    # 用 GSAP 自己的时间轴做 introspection：「起始 + 时长」才是补间的结束时刻。
    # 归属规则：DOM 目标取其最近的 [data-b] 祖先；普通对象目标（数字滚动那种
    # {v:0}）按其起始时刻落在哪一块里来归属。
    # 板间淡入淡出（目标是 .board 本身）不计 —— 它本来就跨块边界。
    ANIM = pg.evaluate("""(blocks) => {
      const tl = (window.__timelines || {})['repo-video'];
      if (!tl) return { err: 'no timeline' };
      const hit = {}, orphan = [];
      for (const ch of tl.getChildren(true, true, true)) {
        if (typeof ch.startTime !== 'function' ||
            typeof ch.duration  !== 'function') continue;
        const d = ch.duration();
        if (!d) continue;                      // 零时长的 callback（mark）跳过
        const t0 = ch.startTime(), t1 = t0 + d;
        const tg = (typeof ch.targets === 'function') ? ch.targets() : [];
        let bid = null, sel = '', isDom = false;
        for (const el of tg) {
          if (!el || el.nodeType !== 1) continue;
          isDom = true;
          // 目标是 .board 本身 = 板间淡入淡出，本来就跨块边界，不算
          if (el.classList && el.classList.contains('board')) break;
          const bd = el.closest('[data-b]');
          if (bd) { bid = bd.dataset.b; sel = String(el.className).slice(0, 28); break; }
        }
        // ⚠️ 只有**普通对象**目标（数字滚动的 {v:0}）才按起始时刻归属。
        // DOM 目标若找不到所属块（进度轨 / 顶栏 / 底栏这类外壳元素），
        // 必须直接跳过 —— 否则会被按时刻误算到某一块头上，
        // 报出「进度轨补间超出 c1 11 秒」这种假警报。
        if (!isDom) {
          sel = '(plain object)';
          for (const b of blocks) {
            if (t0 >= b.start - 0.001 && t0 <= b.end + 0.001) {
              bid = b.id; break;
            }
          }
        }
        if (!bid) { orphan.push([+t0.toFixed(2), +t1.toFixed(2), sel || 'dom-outside']); continue; }
        if (!hit[bid] || t1 > hit[bid].end) {
          hit[bid] = { end: t1, start: t0, dur: d, sel: sel };
        }
      }
      return { hit: hit, orphan: orphan };
    }""", [{"id": b["id"], "start": b["start"], "end": b["end"]}
           for _, b in blocks_all])
    br.close()

bad = []
for r in rep:
    flag = ""
    if r["over"] > 2 or r["wide"] > 2:
        flag = "  <== 溢出"
        bad.append(r)
    print(f"  {r['id']:<3} 高 {r['h']:>4}  内容 {r['need']:>4}  "
          f"越底 {r['over']:>5}  越右 {r['wide']:>4}{flag}")
if bad:
    print(f"\n[!] {len(bad)} 块内容溢出舞台 —— 需调版面或字号"
          f"（越底正值 = 超出舞台下沿的像素）")
else:
    print("\n[OK] 12 块内容全部落在舞台内")

# ------------------------------------------------- 动画是否在切屏前演完
if ANIM.get("err"):
    print(f"\n[!] 动画结束时刻检查跳过：{ANIM['err']}")
else:
    hit, orphan = ANIM["hit"], ANIM["orphan"]
    print("\n[动画] 每块最晚结束时刻 vs 切屏时刻（正值 = 演不完就切走）")
    late = []
    for _, b in blocks_all:
        bid = b["id"]
        limit = b["end"] + b.get("gap_to_next", 0)
        h = hit.get(bid)
        if not h:
            print(f"  {bid:<3}  （无补间）")
            continue
        over = h["end"] - limit
        flag = ""
        if over > 0.05:
            flag = "  <== 演不完"
            late.append((bid, h, limit, over))
        print(f"  {bid:<3} 起 {h['start']:>6.2f}  时长 {h['dur']:>4.2f}  "
              f"止 {h['end']:>6.2f}  切屏 {limit:>6.2f}  余 {limit - h['end']:>6.2f}"
              f"{flag}   {h['sel']}")
    if orphan:
        print(f"  （{len(orphan)} 条补间无法归属到任何块，已跳过）")
    if late:
        print(f"\n[!] {len(late)} 块的动画演不完就被切走 —— 观众看不到最终态。"
              f"三条修法：缩短时长 / 提前起点 / 延长该块旁白。")
        for bid, h, limit, over in late:
            print(f"    {bid}: {h['sel']} 止于 {h['end']:.2f}s，"
                  f"超切屏 {over:.2f}s")
    else:
        print("[OK] 所有块的动画都在切屏前演完")
