# -*- coding: utf-8 -*-
"""
render.py — 读取 data.json(事实) + content.json(创作) → 渲染 1 封面 + 5 详情卡 PNG + copy.txt
封面 1080x1440 (3:4)，详情卡 1080x1920 (9:16)
内置溢出检测：内容超出画布时自动逐级缩小字号。
主题：10 套（themes.py，6 浅 + 4 深），content.json 写 "theme":"klein" 指定，缺省按日期轮换；
命令行 --theme klein --outdir dist/xxx 可覆盖（测试用）。
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

# $token 占位由 themes.py 的令牌填充；版式/字号/行距固定，只换皮肤
CSS_TEMPLATE = """
* { margin:0; padding:0; box-sizing:border-box; }
body { margin:0; background:$bg; font-family:'Microsoft YaHei','PingFang SC',sans-serif; }
.mono { font-family:'JetBrains Mono','Cascadia Mono',Consolas,monospace; }
.cover { width:1080px; height:1440px; background:$cover_bg; padding:72px; display:flex; flex-direction:column; color:$ink; overflow:hidden; position:relative; border:1px solid $border; }
.cover .top { display:flex; justify-content:space-between; align-items:center; }
.cover .tag { font-family:'JetBrains Mono',Consolas,monospace; font-size:26px; letter-spacing:6px; color:$muted; }
.cover .date { font-family:'JetBrains Mono',Consolas,monospace; font-size:26px; color:$ink; border-bottom:4px solid $accent; padding-bottom:6px; }
.cover .hook { font-size:40px; color:$accent; font-weight:500; letter-spacing:3px; margin-top:120px; }
.cover .title { font-size:132px; font-weight:500; line-height:1.22; margin-top:28px; color:$ink; }
.cover .title .hl { background:$accent; color:$accent_text; padding:0 26px; }
.cover .list { margin-top:auto; border-top:1.5px solid $border2; padding-top:40px; display:flex; flex-direction:column; gap:30px; }
.cover .list .row { display:flex; gap:26px; align-items:baseline; }
.cover .list .rk { font-family:'JetBrains Mono',Consolas,monospace; font-size:40px; color:$accent; }
.cover .list .rk2 { color:$muted; }
.cover .list .nm { font-family:'JetBrains Mono',Consolas,monospace; font-size:44px; font-weight:500; color:$ink; }
.cover .list .st { margin-left:auto; font-family:'JetBrains Mono',Consolas,monospace; font-size:30px; color:$accent; flex-shrink:0; }
.cover .foot { margin-top:38px; display:flex; justify-content:space-between; font-size:26px; color:$muted; }
.card { width:1080px; height:1920px; background:$card; padding:68px; display:flex; flex-direction:column; justify-content:space-between; color:$ink; overflow:hidden; position:relative; border:1px solid $border; }
.card .wm { position:absolute; right:28px; top:-20px; font-family:'JetBrains Mono',Consolas,monospace; font-size:280px; font-weight:500; color:$wm; line-height:1; }
.card .head { display:flex; justify-content:space-between; align-items:center; position:relative; z-index:2; }
.card .rankline { font-family:'JetBrains Mono',Consolas,monospace; font-size:27px; letter-spacing:5px; color:$accent; }
.card .headdate { font-family:'JetBrains Mono',Consolas,monospace; font-size:26px; color:$muted; }
.card .repo { font-family:'JetBrains Mono',Consolas,monospace; font-size:56px; font-weight:500; color:$ink; margin-top:38px; position:relative; z-index:2; word-break:break-all; }
.card .selling { font-size:46px; color:$ink; font-weight:500; margin-top:26px; line-height:1.4; }
.card .intro { font-size:33px; color:$sub; line-height:1.65; margin-top:20px; }
.card .chips { display:flex; gap:14px; margin-top:26px; }
.card .chip { font-family:'JetBrains Mono',Consolas,monospace; font-size:26px; background:$chip_bg; padding:9px 22px; border-radius:10px; color:$chip_text; display:flex; align-items:center; }
.card .dot { display:inline-block; width:17px; height:17px; border-radius:50%; margin-right:12px; }
.card .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; }
.card .blk { margin-top:30px; }
.card .m { background:$metric_bg; border-radius:14px; padding:24px 8px; text-align:center; }
.card .m .v { font-size:38px; font-weight:500; color:$ink; }
.card .m .v.red { color:$accent; }
.card .m .l { font-size:22px; color:$muted; margin-top:8px; }
.card .sec { }
.card .sec .lab { font-size:29px; letter-spacing:5px; color:$accent; font-weight:500; margin-bottom:18px; }
.card .hl-item { display:flex; gap:20px; margin-bottom:16px; }
.card .hl-item .no { font-family:'JetBrains Mono',Consolas,monospace; font-size:29px; color:$accent; flex-shrink:0; }
.card .hl-item .tx { font-size:33px; color:$text2; line-height:1.5; }
.card .trend { display:flex; align-items:center; gap:16px; margin-top:20px; }
.card .trend .k { font-size:22px; color:$muted; letter-spacing:2px; flex-shrink:0; }
.card .trend .bar { flex:1; height:14px; background:$chip_bg; border-radius:7px; overflow:hidden; }
.card .trend .fill { height:100%; background:$accent; border-radius:7px; }
.card .trend .v { font-family:'JetBrains Mono',Consolas,monospace; font-size:24px; color:$accent; flex-shrink:0; }
.card .arch { margin-top:14px; font-family:'JetBrains Mono',Consolas,monospace; font-size:22px; color:$muted; letter-spacing:1px; }
.card .quote { margin-top:20px; border-left:6px solid $border2; padding:4px 0 4px 22px; }
.card .quote .tx { font-size:27px; color:$sub; font-style:italic; line-height:1.55; }
.card .quote .src { font-size:20px; color:$faint; margin-top:8px; letter-spacing:2px; }
.card .cmd { margin-top:30px; background:$cmd_bg; border-radius:14px; padding:26px 32px; display:flex; align-items:center; gap:22px; }
.card .cmd .k { font-size:22px; color:$muted; letter-spacing:3px; flex-shrink:0; }
.card .cmd .c { font-family:'JetBrains Mono',Consolas,monospace; font-size:30px; color:$cmd_text; word-break:break-all; }
.card .aud { display:flex; gap:14px; margin-top:30px; align-items:center; }
.card .aud .k { font-size:25px; color:$muted; flex-shrink:0; }
.card .aud .t { font-size:26px; border:1.5px solid $accent; color:$accent; padding:8px 22px; border-radius:28px; }
.card .bottom { margin-top:30px; }
.card .comment { background:$comment_bg; border-left:9px solid $accent; padding:26px 32px; border-radius:0 16px 16px 0; }
.card .comment .lab { font-size:25px; color:$accent; letter-spacing:3px; margin-bottom:12px; }
.card .comment .tx { font-size:32px; color:$text2; line-height:1.6; }
.card .foot { margin-top:22px; border-top:1px solid $border; padding-top:22px; display:flex; justify-content:space-between; align-items:center; font-size:25px; color:$muted; }
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


# ---- 三平台发布文案 / 标签格式 ----
# 小红书用 #标签；微头条用 #话题# 双井号；微信贴图用【话题】（不堆 # 号）
PLATFORM_FORMAT = {
    "xhs": lambda t: f"#{t}",
    "toutiao": lambda t: f"#{t}#",
    "wechat": lambda t: f"【{t}】",
}
PLATFORM_LABELS = {"xhs": "小红书", "toutiao": "微头条", "wechat": "微信贴图"}


def _norm_tag(t):
    """规范化标签词：去掉已有的 # 前缀与【】包裹，返回纯词。"""
    return (t or "").strip().lstrip("#").strip("【】").strip()


def fmt_tags(platform, tags):
    """按平台规则格式化标签词列表（tags 可为纯词或已带前缀）。"""
    fn = PLATFORM_FORMAT[platform]
    return " ".join(fn(_norm_tag(t)) for t in tags if _norm_tag(t))


def get_copies(content):
    """返回三平台文案 dict；兼容旧版单份 copy（自动复制到三平台）。"""
    if "copies" in content and isinstance(content["copies"], dict):
        c = content["copies"]
        xhs = c.get("xhs") or content.get("copy")
        toutiao = c.get("toutiao") or xhs
        wechat = c.get("wechat") or xhs
    else:
        xhs = content.get("copy")
        toutiao = xhs
        wechat = xhs
    return {"xhs": xhs, "toutiao": toutiao, "wechat": wechat}


def write_copy(out_dir, copies):
    """输出三段式 copy.txt：小红书 / 微头条 / 微信贴图。"""
    parts = []
    for plat in ("xhs", "toutiao", "wechat"):
        cp = copies.get(plat) or {}
        title = cp.get("title", "")
        body = cp.get("body", "")
        tags = fmt_tags(plat, cp.get("tags", []))
        parts.append(f"========== {PLATFORM_LABELS[plat]} ==========\n{title}\n\n{body}\n\n{tags}")
    text = "\n\n".join(parts)
    (out_dir / "copy.txt").write_text(text, encoding="utf-8")


def validate(data, content):
    errs = []
    repo_names = [r["full_name"] for r in data["repos"]]
    cr = content.get("repos", [])
    if len(cr) != len(repo_names):
        errs.append(f"content.repos 数量({len(cr)}) != data.repos 数量({len(repo_names)})")
    for i, c in enumerate(cr):
        for k in ("selling", "intro_zh", "highlights", "install_cmd", "audience", "comment"):
            if not c.get(k):
                errs.append(f"repos[{i}] 缺少 {k}")
        if c.get("full_name") != repo_names[i]:
            errs.append(f"repos[{i}] full_name 不匹配: {c.get('full_name')} != {repo_names[i]}")
    if not (content.get("copies") or content.get("copy")):
        errs.append("content 缺少 copy 或 copies（三平台文案）")
    for k in ("cover_title",):
        if not content.get(k):
            errs.append(f"content 缺少 {k}")
    return errs


def cover_html(data, content):
    rows = []
    for i, r in enumerate(data["repos"]):
        cls = "" if i == 0 else " rk2"
        rows.append(f'<div class="row"><span class="rk mono{cls}">{i+1:02d}</span>'
                    f'<span class="nm">{esc(r["full_name"])}</span>'
                    f'<span class="st">今日+{r["stars_today"]}★</span></div>')
    title = content["cover_title"]
    title_html = "<br>".join(esc(t) for t in title) + f'<br><span class="hl">TOP {len(data["repos"])}</span>'
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card-root"><div class="cover">
  <div class="top"><span class="tag">GITHUB TRENDING · DAILY</span><span class="date">{esc(data['date'].replace('-', '.'))}</span></div>
  <div class="title">{title_html}</div>
  <div class="list">{''.join(rows)}</div>
  <div class="foot"><span>左滑查看每个项目详情</span><span>{esc(content.get('brand', '@大飞的AI赋能笔记'))}</span></div>
</div></div></body></html>"""


def extract_quote(snippet):
    """从 README 摘录自动提炼一句作者原话（content.quote 优先，此为兜底）。"""
    if not snippet:
        return ""
    s = re.sub(r"<[^>]+>", " ", snippet)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[#*`>|_{}\[\]()]", " ", s)
    s = re.sub(r"&[a-z]+;", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for p in re.split(r"(?<=[.!?。])\s+", s):
        if 40 <= len(p) <= 200 and len(re.findall(r"[A-Za-z\u4e00-\u9fff]", p)) >= 20:
            return p
    return ""


def arch_line(r):
    """项目档案行：license · 创建年份 · 最近提交 · Issues。缺啥跳啥。"""
    parts = []
    if r.get("license"):
        parts.append(r["license"])
    if r.get("created_at"):
        parts.append(f"创建于 {r['created_at'][:4]}")
    if r.get("pushed_at"):
        parts.append(f"最近提交 {r['pushed_at'][:10]}")
    if r.get("open_issues"):
        parts.append(f"Issues {fmt_num(r['open_issues'])}")
    return " · ".join(parts)


def detail_html(data, content, i, max_today=1):
    r = data["repos"][i]
    c = content["repos"][i]
    color = LANG_COLORS.get(r["language"], LANG_FALLBACK)
    chips = [f'<span class="chip"><span class="dot" style="background:{color}"></span>{esc(r["language"] or "Code")}</span>']
    chips += [f'<span class="chip">{esc(t)}</span>' for t in r["topics"][:3]]
    hls = "".join(f'<div class="hl-item"><span class="no">{j+1:02d}</span>'
                  f'<span class="tx">{esc(h)}</span></div>' for j, h in enumerate(c["highlights"][:4]))
    auds = "".join(f'<span class="t">{esc(a)}</span>' for a in c["audience"][:3])
    name_len = len(r["full_name"])
    repo_size = 56 if name_len <= 18 else (46 if name_len <= 24 else 38)
    # 今日增速条：以今日 Top5 中最高增速为满格
    pct = max(6, round(r["stars_today"] / max(max_today, 1) * 100))
    quote = c.get("quote") or extract_quote(r.get("readme_snippet") or "")
    quote_html = (f'<div class="quote"><div class="tx">&ldquo;{esc(quote)}&rdquo;</div>'
                  f'<div class="src">&mdash; {esc(r["owner"])} · 作者原话</div></div>') if quote else ""
    arch = f'<div class="arch">{esc(arch_line(r))}</div>' if arch_line(r) else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card" id="card">
  <div>
  <div class="wm">{i+1:02d}</div>
  <div class="head"><span class="rankline">RANK {i+1:02d} · 今日 +{r['stars_today']} ★</span><span class="headdate">{esc(data['date'].replace('-', '.'))}</span></div>
  <div class="repo" style="font-size:{repo_size}px">{esc(r['full_name'])}</div>
  <div class="selling">{esc(c['selling'])}</div>
  <div class="intro">{esc(c['intro_zh'])}</div>
  <div class="chips">{''.join(chips)}</div>
  </div>
  <div class="blk">
  <div class="metrics">
    <div class="m"><div class="v">{fmt_num(r['stars'])}</div><div class="l">总星标</div></div>
    <div class="m"><div class="v red">+{r['stars_today']}</div><div class="l">今日新增</div></div>
    <div class="m"><div class="v">{fmt_num(r['forks'])}</div><div class="l">Fork</div></div>
    <div class="m"><div class="v">{fmt_num(r['contributors'])}</div><div class="l">贡献者</div></div>
  </div>
  <div class="trend"><span class="k">今日增速</span><div class="bar"><div class="fill" style="width:{pct}%"></div></div><span class="v">+{r['stars_today']} ★</span></div>
  {arch}
  </div>
  <div class="blk">
  <div class="sec"><div class="lab">核心亮点</div>{hls}</div>
  {quote_html}
  </div>
  <div class="cmd"><span class="k">上手</span><span class="c">{esc(c['install_cmd'])}</span></div>
  <div class="aud"><span class="k">适合谁</span>{auds}</div>
  <div class="bottom">
    <div class="comment"><div class="lab">{esc(content.get('comment_label', '大飞点评'))}</div><div class="tx">{esc(c['comment'])}</div></div>
    <div class="foot"><span class="u">{esc(r['url'].replace('https://', ''))}</span><span>{i+2} / {len(data['repos'])+1}</span><span>{esc(content.get('brand', '@大飞的AI赋能笔记'))} · 每日更新</span></div>
  </div>
</div></body></html>"""


def shot_with_overflow_check(page, html, w, h, out):
    page.set_viewport_size({"width": w, "height": h})
    page.set_content(html, wait_until="networkidle")
    page.evaluate("document.body.style.zoom='1'")
    scale = 1.0
    for _ in range(5):
        sh = page.evaluate("document.documentElement.scrollHeight")
        if sh <= h + 2:
            break
        scale *= 0.94
        page.evaluate(f"document.body.style.zoom='{scale:.3f}'")
    else:
        print(f"[warn] {out.name} 内容仍超高（zoom={scale:.2f}），请检查文案长度", file=sys.stderr)
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
    return scale


def launch_browser(p):
    """优先复用系统浏览器（免下载），最后才用 playwright 内置 chromium。"""
    last = None
    for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kwargs)
        except Exception as e:
            last = e
    raise last


def apply_theme(tokens):
    """用主题令牌填充 CSS 模板（$token 占位，避免与 CSS 花括号冲突）。"""
    global CSS, LANG_FALLBACK
    CSS = Template(CSS_TEMPLATE).substitute(tokens)
    LANG_FALLBACK = tokens["muted"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", choices=theme_lib.list_themes(), default=None,
                    help="指定主题（缺省：content.json 的 theme 字段，再缺省按日期轮换）")
    ap.add_argument("--outdir", default=None, help="覆盖输出目录（默认 dist/<日期>）")
    ap.add_argument("--covers-only", action="store_true", help="只渲染封面（主题预览用）")
    args = ap.parse_args()

    data = json.loads((BASE / "data.json").read_text(encoding="utf-8"))
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
    out_dir = Path(args.outdir) if args.outdir else BASE / "dist" / data["date"]
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page()
        shot_with_overflow_check(page, cover_html(data, content), W_COVER, H_COVER, out_dir / "cover.png")
        print(f"  cover.png (zoom 校验通过)")
        if not args.covers_only:
            max_today = max((r.get("stars_today") or 0) for r in data["repos"])
            for i in range(len(data["repos"])):
                out = out_dir / f"{i+1:02d}.png"
                s = shot_with_overflow_check(page, detail_html(data, content, i, max_today),
                                             W_DETAIL, H_DETAIL, out)
                print(f"  {out.name} (zoom={s:.2f})")
        browser.close()
    if args.covers_only:
        print(f"完成（仅封面）→ {out_dir}")
        return
    copies = get_copies(content)
    write_copy(out_dir, copies)
    print(f"完成 → {out_dir}（copy.txt 含 小红书/微头条/微信贴图 三段）")


if __name__ == "__main__":
    main()
