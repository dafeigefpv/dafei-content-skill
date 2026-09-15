# -*- coding: utf-8 -*-
"""
render.py — 读取 project.json(事实) + content.json(创作) → 渲染深度报道图文
产出：dist/<repo-name>/cover.png + 01.png(深度档案) + 02.png(上手与点评) + copy.txt
封面 1080x1440 (3:4)，详情页 1080x1920 (9:16)；内置溢出检测（zoom 自动缩小，最多 5 级）。
与 github-trending-xhs 的区别：编辑部编号栏目式排版、亮点带小标题+详述、三步上手、
适合谁带说明、点评可 2-3 句、封面直接放二维码。
主题：10 套（themes.py，与 trending 共用：6 浅 + 4 深）；content.json 写 "theme":"klein" 指定，
缺省按日期轮换；命令行 --theme klein --outdir dist/xxx 可覆盖（测试用）。
"""
import argparse
import json
import re
import sys
from pathlib import Path
from string import Template

from playwright.sync_api import sync_playwright

import themes as theme_lib

BASE = Path(__file__).parent
W_COVER, H_COVER = 1080, 1440
W_DETAIL, H_DETAIL = 1080, 1920

# $token 占位由 themes.py 的令牌填充；版式/字号/行距固定，只换皮肤。
# 终端窗与封面黑卡为跨主题固定深色元素；accent2 为封面徽章/强调的第二点缀色。
CSS_TEMPLATE = """
* { margin:0; padding:0; box-sizing:border-box; }
body { margin:0; background:$bg; font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
.mono { font-family:'JetBrains Mono','Cascadia Mono',Consolas,monospace; }

/* ---- 封面：skills-daily 风（格子纸底 + 徽章 + 终端窗 + 黑卡 + 指标卡） ---- */
.cover { width:1080px; height:1440px; color:$ink; padding:52px 60px 44px; display:flex; flex-direction:column; overflow:hidden; position:relative; border:1px solid $border;
  background-color:$paper;
  background-image: repeating-linear-gradient(0deg, transparent 0 43px, $grid 43px 44px),
                    repeating-linear-gradient(90deg, transparent 0 43px, $grid 43px 44px),
                    $cover_bg; }
.cover .badge { display:flex; justify-content:center; }
.cover .badge-inner { display:flex; align-items:center; gap:18px; background:$card; border:2.5px solid $accent2; border-radius:999px; padding:18px 44px; }
.cover .badge-dot { width:46px; height:46px; border-radius:50%; background:$accent2; color:#fff; font-weight:bold; font-size:28px; display:flex; align-items:center; justify-content:center; }
.cover .badge-txt { font-size:37px; font-weight:900; color:$accent2; letter-spacing:2px; }
.cover .header { display:flex; align-items:center; justify-content:space-between; margin-top:32px; }
.cover .brand { display:flex; align-items:center; gap:16px; }
.cover .logo { width:56px; height:56px; border-radius:14px; background:#1B1B19; border:1px solid $panel_border; color:#fff; font-size:28px; font-weight:bold; display:flex; align-items:center; justify-content:center; }
.cover .brand-name { font-family:'JetBrains Mono',Consolas,monospace; font-size:30px; font-weight:bold; }
.cover .tags { border:1px solid $border2; border-radius:999px; padding:9px 20px; font-size:20px; letter-spacing:2px; color:$text2; background:$card; }
.cover .eyebrow { margin-top:30px; font-size:20px; letter-spacing:5px; color:$muted; }
.cover h1 { margin-top:12px; font-size:66px; line-height:1.24; font-weight:900; letter-spacing:-1px; }
.cover h1 .ac { color:$accent2; }
.cover .sub { margin-top:18px; font-size:24px; line-height:1.6; color:$text2; }
.cover .hero { display:flex; gap:18px; margin-top:30px; height:380px; }
.cover .term { flex:1.35; background:#17171A; border:1px solid $panel_border; border-radius:18px; overflow:hidden; display:flex; flex-direction:column; }
.cover .term-bar { display:flex; align-items:center; gap:8px; padding:15px 20px; background:#232327; }
.cover .tdot { width:13px; height:13px; border-radius:50%; }
.cover .term-title { margin-left:10px; color:#8F8D86; font-size:16px; }
.cover .term-body { padding:24px 26px; font-size:22px; line-height:2.0; }
.cover .p1 { color:#F2F1EC; }
.cover .cmd { color:#7FD1A8; word-break:break-all; }
.cover .ok { color:#8F8D86; }
.cover .ok b { color:#B9E7CB; font-weight:normal; }
.cover .darkcard { flex:1; background:#1B1B19; border:1px solid $panel_border; border-radius:18px; padding:26px 26px 22px; display:flex; flex-direction:column; }
.cover .dk-label { color:#8F8D86; font-size:18px; letter-spacing:3px; }
.cover .dk-num { color:$accent2; font-size:64px; font-weight:900; line-height:1.1; margin-top:8px; }
.cover .dk-sub { color:#C9C7C0; font-size:20px; margin-top:4px; }
.cover .dk-rows { margin-top:18px; border-top:1px solid #33332F; }
.cover .dk-row { display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #33332F; color:#A5A39B; font-size:19px; letter-spacing:1px; }
.cover .dk-row b { color:#F2F1EC; font-weight:normal; }
.cover .metrics { display:flex; gap:14px; margin-top:22px; }
.cover .mc { flex:1; background:$card; border:1px solid $border; border-radius:14px; padding:18px 20px 16px; }
.cover .mc-label { font-size:16px; letter-spacing:2px; color:$accent2; font-weight:bold; }
.cover .mc-val { font-size:30px; font-weight:900; margin-top:7px; }
.cover .mc-desc { font-size:16px; color:$muted; margin-top:5px; }
.cover .divider { margin-top:auto; border-top:1.5px solid $ink; padding-top:14px; display:flex; justify-content:space-between; align-items:center; }
.cover .dv-l { font-size:20px; color:$text2; }
.cover .dv-r { font-size:16px; letter-spacing:2px; color:$muted; }
.cover .quote { margin-top:20px; font-size:38px; font-weight:900; line-height:1.4; }
.cover .quote .ac { color:$accent2; }
.cover .footer { margin-top:20px; display:flex; justify-content:space-between; align-items:center; }
.cover .ft-l { font-size:19px; color:$muted; }
.cover .ft-r { font-family:'JetBrains Mono',Consolas,monospace; font-size:15px; letter-spacing:1px; color:$faint; }

/* ---- 详情页：编号栏目式 ---- */
.card { width:1080px; height:1920px; background:$card; padding:68px; display:flex; flex-direction:column; justify-content:space-between; color:$ink; overflow:hidden; position:relative; border:1px solid $border; }
.card .wm { position:absolute; right:20px; top:-30px; font-size:230px; font-weight:600; color:$wm; line-height:1; }
.card .head { display:flex; justify-content:space-between; align-items:center; position:relative; z-index:2; }
.card .rankline { font-family:'JetBrains Mono',Consolas,monospace; font-size:27px; letter-spacing:5px; color:$accent; font-weight:500; }
.card .headdate { font-family:'JetBrains Mono',Consolas,monospace; font-size:26px; color:$muted; }
.card .repo { font-family:'JetBrains Mono',Consolas,monospace; font-size:48px; font-weight:600; color:$ink; margin-top:30px; position:relative; z-index:2; word-break:break-all; }
.card .selling { font-size:41px; color:$ink; font-weight:500; margin-top:20px; line-height:1.4; }
.card .intro { font-size:30px; color:$sub; line-height:1.7; margin-top:18px; }
.card .chips { display:flex; gap:14px; margin-top:22px; flex-wrap:wrap; }
.card .chip { font-family:'JetBrains Mono',Consolas,monospace; font-size:25px; background:$chip_bg; padding:8px 20px; border-radius:10px; color:$chip_text; display:flex; align-items:center; }
.card .dot { display:inline-block; width:16px; height:16px; border-radius:50%; margin-right:11px; }
.card .blk { margin-top:26px; }
.card .sec .labrow { display:flex; align-items:baseline; gap:18px; border-bottom:2px solid $ink; padding-bottom:12px; margin-bottom:16px; }
.card .sec .no { font-family:'JetBrains Mono',Consolas,monospace; font-size:32px; color:$accent; font-weight:500; }
.card .sec .lab { font-size:33px; letter-spacing:4px; color:$ink; font-weight:600; }
.card .problem { font-size:30px; color:$text2; line-height:1.75; }
.card .problem .q { color:$accent; font-weight:600; }
.card .hl-item { display:flex; gap:18px; margin-bottom:14px; }
.card .hl-item .no2 { font-family:'JetBrains Mono',Consolas,monospace; font-size:28px; color:$accent; flex-shrink:0; padding-top:4px; }
.card .hl-item .ht { font-size:30px; font-weight:600; color:$ink; }
.card .hl-item .hx { font-size:26px; color:$sub; line-height:1.6; margin-top:6px; }
.card .quote { margin-top:16px; border-left:6px solid $accent; background:$comment_bg; padding:20px 26px; border-radius:0 14px 14px 0; }
.card .quote .tx { font-size:26px; color:$text2; font-style:italic; line-height:1.6; }
.card .quote .src { font-size:21px; color:$faint; margin-top:10px; letter-spacing:2px; }
.card .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; }
.card .m { background:$metric_bg; border-radius:14px; padding:22px 8px; text-align:center; }
.card .m .v { font-size:33px; font-weight:500; color:$ink; }
.card .m .v.red { color:$accent; }
.card .m .l { font-size:21px; color:$muted; margin-top:8px; }
.card .arch { margin-top:16px; font-family:'JetBrains Mono',Consolas,monospace; font-size:22px; color:$muted; letter-spacing:1px; }
.card .step { margin-bottom:18px; }
.card .step .sk { display:flex; align-items:center; gap:14px; margin-bottom:10px; }
.card .step .sk .n { font-family:'JetBrains Mono',Consolas,monospace; background:$accent; color:$accent_text; font-size:24px; padding:4px 14px; border-radius:8px; }
.card .step .sk .k { font-size:30px; font-weight:600; color:$ink; }
.card .step .cmd { background:$cmd_bg; border-radius:12px; padding:16px 24px; }
.card .step .cmd .c { font-family:'JetBrains Mono',Consolas,monospace; font-size:26px; color:$cmd_text; word-break:break-all; }
.card .step .note { font-size:25px; color:$sub; line-height:1.55; margin-top:10px; }
.card .promptbox { margin-top:24px; background:$card; border:2px dashed $accent2; border-radius:16px; padding:24px 28px; }
.card .promptbox .plab { display:flex; align-items:center; gap:12px; font-size:24px; font-weight:bold; color:$accent2; margin-bottom:12px; }
.card .promptbox .plab .ic { background:$accent2; color:#fff; border-radius:8px; padding:3px 12px; font-size:20px; }
.card .promptbox .ptx { font-size:29px; color:$ink; line-height:1.65; }
.card .promptbox .ptx b { color:$accent2; }
.card .aud-row { display:flex; gap:20px; align-items:flex-start; margin-bottom:18px; }
.card .aud-row .t { flex-shrink:0; font-size:26px; border:1.5px solid $accent; color:$accent; padding:8px 22px; border-radius:28px; white-space:nowrap; }
.card .aud-row .note { font-size:28px; color:$text2; line-height:1.6; padding-top:6px; }
.card .cmp { font-size:29px; color:$text2; line-height:1.7; background:$chip_bg; border-radius:14px; padding:22px 28px; }
.card .brow { display:flex; gap:24px; align-items:stretch; }
.card .brow .comment { flex:1; display:flex; flex-direction:column; justify-content:center; }
.card .comment { background:$comment_bg; border-left:9px solid $accent; padding:26px 32px; border-radius:0 16px 16px 0; }
.card .comment .lab { font-size:25px; color:$accent; letter-spacing:3px; margin-bottom:12px; }
.card .comment .tx { font-size:32px; color:$text2; line-height:1.65; }
.card .foot { margin-top:20px; border-top:1px solid $border; padding-top:20px; display:flex; justify-content:space-between; align-items:center; font-size:25px; color:$muted; }
.card .foot .u { font-family:'JetBrains Mono',Consolas,monospace; font-size:21px; color:$faint; }
"""

CSS = CSS_TEMPLATE  # main() 中按主题填充后回写
LANG_FALLBACK = "#8a8577"  # main() 中按主题 muted 填充

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Go": "#00ADD8", "Rust": "#dea584", "Java": "#b07219", "C++": "#f34b7d",
    "C": "#555555", "C#": "#178600", "Zig": "#ec915c", "Vue": "#41b883",
    "HTML": "#e34c26", "CSS": "#563d7c", "Shell": "#89e051", "Jupyter Notebook": "#DA5B0B",
    "Dart": "#00B4AB", "Kotlin": "#A97BFF", "Swift": "#F05138", "Ruby": "#701516",
    "PHP": "#4F5D95", "Lua": "#000080", "MDX": "#fcb32c", "Svelte": "#ff3e00",
}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt_num(n):
    if n is None:
        return "0"
    if n >= 1000:
        v = n / 1000
        return f"{v:.1f}k".replace(".0k", "k")
    return str(n)


def launch_browser(p):
    last = None
    for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kwargs)
        except Exception as e:
            last = e
    raise last


def shot_with_overflow_check(page, html, w, h, out):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.body.style.zoom='1'")
    # 卡片固定高度 + overflow:hidden 会藏住溢出，先把高度解开量真实内容高度
    natural = page.evaluate(
        "(function(){var c=document.getElementById('card')||document.querySelector('.cover');"
        "if(!c) return document.documentElement.scrollHeight;"
        "c.style.height='auto';return c.getBoundingClientRect().height;})()")
    scale = 1.0
    if natural > h + 2:
        scale = max(0.70, h / natural)
        page.evaluate(f"document.body.style.zoom='{scale:.3f}'")
        # zoom 会把宽高都同比缩小（右侧/底部留白）：反向放大卡片宽高补偿，
        # 加宽后换行减少内容变矮，高度必须钉回 h/scale 让 space-between 铺满
        comp_w = int(round(w / scale))
        comp_h = int(round(h / scale))
        page.evaluate(
            "(function(){var c=document.getElementById('card')||document.querySelector('.cover');"
            "document.body.style.width='" + str(comp_w) + "px';"
            "if(c){c.style.width='" + str(comp_w) + "px';c.style.height='" + str(comp_h) + "px';}})()")
        if scale <= 0.70 + 1e-9:
            print(f"[warn] {out.name} 内容仍超高（zoom={scale:.2f}），请精简文案", file=sys.stderr)
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
    return scale


# ---- 发布文案 / 标签格式 ----
# 小红书 / 微信贴图 用 #标签（单井号）；微头条用 #话题# 双井号
PLATFORM_FORMAT = {
    "xhs": lambda t: f"#{t}",
    "toutiao": lambda t: f"#{t}#",
}
PLATFORM_LABELS = {"xhs": "小红书 / 微信贴图", "toutiao": "微头条"}


def _norm_tag(t):
    """规范化标签词：去掉已有的 # 前缀与【】包裹，返回纯词。"""
    return (t or "").strip().lstrip("#").strip("【】").strip()


def fmt_tags(platform, tags):
    """按平台规则格式化标签词列表（tags 可为纯词或已带前缀）。"""
    fn = PLATFORM_FORMAT[platform]
    return " ".join(fn(_norm_tag(t)) for t in tags if _norm_tag(t))


def get_copy(content):
    """返回单份文案 {title, body, title_alts, tags}；兼容旧版 copies（取 xhs 作为统一正文）。"""
    if isinstance(content.get("copy"), dict):
        return content["copy"]
    if isinstance(content.get("copies"), dict):
        return content["copies"].get("xhs") or {}
    return {}


def write_copy(out_dir, copy):
    """输出：单份正文 + 两版标签（小红书/微信贴图 单#；微头条 双#）。"""
    title = copy.get("title", "")
    body = copy.get("body", "")
    tags = copy.get("tags", [])
    xhs_tags = fmt_tags("xhs", tags)
    tt_tags = fmt_tags("toutiao", tags)
    text = (
        f"{title}\n\n{body}\n\n"
        f"【小红书 / 微信贴图 标签】\n{xhs_tags}\n\n"
        f"【微头条标签】\n{tt_tags}"
    )
    (out_dir / "copy.txt").write_text(text, encoding="utf-8")


def validate(data, content):
    errs = []
    if content.get("full_name") != data["repo"]["full_name"]:
        errs.append(f"full_name 不匹配: content={content.get('full_name')} data={data['repo']['full_name']}")
    for k in ("selling", "intro_zh", "problem", "highlights", "steps", "audience", "comment"):
        if not content.get(k):
            errs.append(f"content 缺少 {k}")
    if not (content.get("copy") or content.get("copies")):
        errs.append("content 缺少 copy（发布文案）")
    if content.get("pages", 2) not in (1, 2):
        errs.append("pages 只能是 1 或 2")
    if content.get("pages", 2) == 2 and not content.get("steps"):
        errs.append("pages=2 时需要 steps")
    return errs


def arch_line(r):
    """01 页档案行：与封面/指标格错开，只放协议与最近提交。"""
    parts = []
    if r.get("license"):
        parts.append(r["license"])
    if r.get("pushed_at"):
        parts.append(f"最近提交 {r['pushed_at'][:10]}")
    return " · ".join(parts)


def page1_metrics(r):
    """01 页指标格：关注/Issues/最新版/创建年份——封面已展示的不重复。"""
    cells = [
        (fmt_num(r.get("subscribers") or 0), "Watch 关注"),
        (fmt_num(r.get("open_issues") or 0), "Open Issues"),
        (r.get("latest_release", {}).get("tag") or "—", "最新版本"),
        (f"{r['created_at'][:4]} 年" if r.get("created_at") else "—", "创建于"),
    ]
    return "".join(
        f'<div class="m"><div class="v">{esc(v)}</div><div class="l">{l}</div></div>'
        for v, l in cells)


def name_font_size(name):
    n = len(name)
    if n <= 12:
        return 110
    if n <= 18:
        return 84
    if n <= 26:
        return 62
    return 50


def accent_html(text):
    """[[...]] 标记转为橙色强调 span；<br> 允许作为换行。"""
    return (esc(text).replace("[[", '<span class="ac">').replace("]]", "</span>")
            .replace("&lt;br&gt;", "<br>"))


def cover_html(data, content):
    r = data["repo"]
    name = r["name"]
    term_lines = content.get("cover_terminal") or [
        f"$ {content['steps'][0]['cmd']}",
        "✔ Skill installed",
        "✔ Ready — just ask your agent.",
    ]
    term_html = f'<div class="p1">$ <span class="cmd">{esc(content["steps"][0]["cmd"])}</span></div>'
    for ln in term_lines[1:]:
        if ln.startswith("✔"):
            ln = "✔ " + esc(ln[1:].strip())
            term_html += f'<div class="ok">{ln}</div>'
        else:
            term_html += f'<div class="p1">{esc(ln)}</div>'
    dk_rows = (f'<div class="dk-row"><span>FORKS</span><b>{fmt_num(r["forks"])}</b></div>'
               f'<div class="dk-row"><span>贡献者</span><b>{fmt_num(r.get("contributors") or 0)}</b></div>')
    # 白色指标卡：放 README 亮点事实（cover_facts），与 01 页的仓库档案数据零重复；
    # 未提供时用 topics 兜底
    facts = content.get("cover_facts") or [
        {"label": "TOPIC", "value": t[:10], "desc": "项目标签"} for t in r.get("topics", [])[:4]]
    metrics_html = "".join(
        f'<div class="mc"><div class="mc-label mono">{esc(f.get("label", ""))}</div>'
        f'<div class="mc-val">{esc(f.get("value", ""))}</div>'
        f'<div class="mc-desc">{esc(f.get("desc", ""))}</div></div>'
        for f in facts[:4])
    headline = accent_html(content.get("cover_headline") or content["cover_tagline"])
    sub = content.get("cover_sub") or content["intro_zh"]
    quote = content.get("cover_quote") or content["cover_tagline"]
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="cover">
  <div class="badge"><div class="badge-inner"><div class="badge-dot">★</div><div class="badge-txt">项目日报 · 每天一个Github热门项目</div></div></div>
  <div class="header">
    <div class="brand"><div class="logo">G</div><div class="brand-name">{esc(name)}</div></div>
    <div class="tags mono">{esc(' · '.join(filter(None, [r['language'], r.get('license'), 'OPEN SOURCE'])))}</div>
  </div>
  <div class="eyebrow mono">{esc(r['full_name'].upper())}</div>
  <h1>{headline}</h1>
  <p class="sub">{esc(sub)}</p>
  <div class="hero">
    <div class="term">
      <div class="term-bar"><span class="tdot" style="background:#FF5F57"></span><span class="tdot" style="background:#FEBC2E"></span><span class="tdot" style="background:#28C840"></span><span class="term-title mono">Terminal — Agent CLI</span></div>
      <div class="term-body mono">{term_html}</div>
    </div>
    <div class="darkcard">
      <div class="dk-label mono">GITHUB STARS</div>
      <div class="dk-num">{fmt_num(r['stars'])}</div>
      <div class="dk-sub">GitHub Star</div>
      <div class="dk-rows mono">{dk_rows}</div>
    </div>
  </div>
  <div class="metrics">{metrics_html}</div>
  <div class="divider">
    <div class="dv-l">左滑查看「项目档案」与「上手指南」→</div>
    <div class="dv-r mono">{esc(data['date'].replace('-', '.'))} · DEEP DIVE</div>
  </div>
  <div class="quote">{accent_html(quote)}</div>
  <div class="footer">
    <div class="ft-l">{esc(content.get('brand', '@大飞的AI赋能笔记'))}</div>
    <div class="ft-r mono">github.com/{esc(r['full_name'])}</div>
  </div>
</div></body></html>"""


def sec(no, lab, inner):
    return (f'<div class="sec"><div class="labrow"><span class="no">{no}</span>'
            f'<span class="lab">{esc(lab)}</span></div>{inner}</div>')


def page1_html(data, content):
    r, c = data["repo"], content
    color = LANG_COLORS.get(r["language"], LANG_FALLBACK)
    chips = [f'<span class="chip"><span class="dot" style="background:{color}"></span>{esc(r["language"] or "Code")}</span>']
    chips += [f'<span class="chip">{esc(t)}</span>' for t in r["topics"][:3]]
    hls = "".join(
        f'<div class="hl-item"><span class="no2">{j+1:02d}</span>'
        f'<span><div class="ht">{esc(h.get("title", ""))}</div>'
        f'<div class="hx">{esc(h.get("text", ""))}</div></span></div>'
        for j, h in enumerate(c["highlights"][:4]))
    quote = c.get("quote") or ""
    quote_html = (f'<div class="quote"><div class="tx">&ldquo;{esc(quote)}&rdquo;</div>'
                  f'<div class="src">&mdash; {esc(r["owner"])} · 作者原话</div></div>') if quote else ""
    arch = f'<div class="arch">{esc(arch_line(r))}</div>' if arch_line(r) else ""
    problem = c["problem"]
    if "\n" in problem:
        q, a = problem.split("\n", 1)
        problem_html = f'<div class="problem"><span class="q">{esc(q)}</span>{esc(a)}</div>'
    else:
        problem_html = f'<div class="problem">{esc(problem)}</div>'
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card" id="card">
  <div>
  <div class="wm">档案</div>
  <div class="head"><span class="rankline">DEEP DIVE 1/2 · 项目档案</span><span class="headdate">{esc(data['date'].replace('-', '.'))}</span></div>
  <div class="repo">{esc(r['full_name'])}</div>
  <div class="selling">{esc(c['selling'])}</div>
  <div class="intro">{esc(c['intro_zh'])}</div>
  <div class="chips">{''.join(chips)}</div>
  </div>
  <div class="blk">{sec('01', '解决什么问题', problem_html)}</div>
  <div class="blk">{sec('02', '核心亮点', hls)}{quote_html}</div>
  <div class="blk">
  <div class="metrics">{page1_metrics(r)}</div>
  {arch}
  </div>
  <div class="foot"><span class="u">{esc(r['url'].replace('https://', ''))}</span><span>1 / 3 · {esc(content.get('brand', '@大飞的AI赋能笔记'))}</span></div>
</div></body></html>"""


def page2_html(data, content):
    r, c = data["repo"], content
    steps = "".join(
        f'<div class="step"><div class="sk"><span class="n mono">{i+1}</span>'
        f'<span class="k">{esc(s.get("k", ""))}</span></div>'
        f'<div class="cmd"><span class="c">{esc(s.get("cmd", ""))}</span></div>'
        + (f'<div class="note">{esc(s["note"])}</div>' if s.get("note") else "")
        + '</div>'
        for i, s in enumerate(c["steps"][:3]))
    auds = "".join(
        f'<div class="aud-row"><span class="t">{esc(a.get("tag", ""))}</span>'
        f'<span class="note">{esc(a.get("note", ""))}</span></div>'
        for a in c["audience"][:3])
    cmp_html = f'<div class="cmp">{esc(c["compare"])}</div>' if c.get("compare") else ""
    agent_prompt = c.get("agent_prompt") or f"请从 GitHub 获取并安装『{r['name']}』（{r['full_name']}）"
    prompt_html = (f'<div class="promptbox"><div class="plab"><span class="ic">小白指令</span>'
                   f'不会装？把这句话原样发给你的 AI Agent</div>'
                   f'<div class="ptx">「<b>{esc(agent_prompt)}</b>」</div></div>')
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card" id="card">
  <div>
  <div class="wm">上手</div>
  <div class="head"><span class="rankline">DEEP DIVE 2/2 · 上手与点评</span><span class="headdate">{esc(data['date'].replace('-', '.'))}</span></div>
  <div class="repo">{esc(r['full_name'])}</div>
  </div>
  <div class="blk">{sec('03', '三步上手', steps)}{prompt_html}</div>
  <div class="blk">{sec('04', '适合谁', auds)}</div>
  <div class="blk">{sec('05', '同类对比', cmp_html)}</div>
  <div class="brow">
    <div class="comment"><div class="lab">{esc(content.get('comment_label', '大飞点评'))}</div><div class="tx">{esc(c['comment'])}</div></div>
  </div>
  <div class="foot"><span class="u">{esc(r['url'].replace('https://', ''))}</span><span>2 / 3 · {esc(content.get('brand', '@大飞的AI赋能笔记'))}</span></div>
</div></body></html>"""


def apply_theme(tokens):
    """用主题令牌填充 CSS 模板（$token 占位，避免与 CSS 花括号冲突）。"""
    global CSS, LANG_FALLBACK
    CSS = Template(CSS_TEMPLATE).substitute(tokens)
    LANG_FALLBACK = tokens["muted"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", choices=theme_lib.list_themes(), default=None,
                    help="指定主题（缺省：content.json 的 theme 字段，再缺省按日期轮换）")
    ap.add_argument("--outdir", default=None, help="覆盖输出目录（默认 dist/<repo-name>）")
    args = ap.parse_args()

    data = json.loads((BASE / "project.json").read_text(encoding="utf-8"))
    content = json.loads((BASE / "content.json").read_text(encoding="utf-8"))
    errs = validate(data, content)
    if errs:
        print("content.json 校验失败:", file=sys.stderr)
        for e in errs:
            print("  -", e, file=sys.stderr)
        sys.exit(1)
    theme_name, tokens = theme_lib.resolve(data["date"], args.theme or content.get("theme"))
    apply_theme(tokens)
    print(f"主题: {theme_name}")
    r = data["repo"]
    out_dir = Path(args.outdir) if args.outdir else BASE / "dist" / r["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = content.get("pages", 2)
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page()
        shot_with_overflow_check(page, cover_html(data, content), W_COVER, H_COVER, out_dir / "cover.png")
        print("  cover.png (zoom 校验通过)")
        shot_with_overflow_check(page, page1_html(data, content), W_DETAIL, H_DETAIL, out_dir / "01.png")
        print("  01.png (深度档案)")
        if pages == 2:
            shot_with_overflow_check(page, page2_html(data, content), W_DETAIL, H_DETAIL, out_dir / "02.png")
            print("  02.png (上手与点评)")
        browser.close()
    copy = get_copy(content)
    write_copy(out_dir, copy)
    print(f"完成 → {out_dir}（copy.txt 含 小红书/微信贴图 单# 与 微头条 双# 两版标签）")


if __name__ == "__main__":
    main()
