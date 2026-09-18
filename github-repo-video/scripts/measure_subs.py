# -*- coding: utf-8 -*-
"""量字幕折行：报每条字幕实际占几行、最长单行占框比。

背景（2026-09-17 一屏一块改版）
-------------------------------
旧版（卡片 + 锚点 / 1080×1920）字幕**没有专属位置**，只能压在卡片内容上，
净空约 54px —— 折一行就掉进指标格，所以当时的目标是「找出能全部单行的最大字号」，
选择器是 `.sub > span`、视口是 1080。

新版（一屏一块 / 1440×1920）字幕带**独占 236px**（y 1552–1788），
字号 40px、max-width 1330px，**两行容量**。折行不再致命，本脚本的目标随之变成：

    确认每块字幕 ≤ 2 行，且最长单行不顶满框（留折行余量）。

⚠️ 选择器和视口必须跟当前架构一致，否则 `querySelectorAll` 返回空数组、
脚本会静默打印「0 条」。旧版参数（`.sub` / 1080）已随卡片版一起淘汰。
"""

import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "video", "index.html")

W, H = 1440, 1920          # 必须与 scene_kit.py 的 W/H 一致
CAP_CLASS = ".cap > span"  # 必须与 scene_kit.py 的 SHELL_CSS 一致

# 候选：字号 / max-width（px）。当前定版是 (40, 1330)，其余是「再收紧一档」的备选。
# box-sizing:border-box —— 实际文本宽度 = max-width − 左右 padding(32×2)。
CANDS = [
    (40, 1330),   # ← 当前定版
    (38, 1330),
    (36, 1330),
    (34, 1330),
    (40, 1200),
]

JS = """
(sel) => {
  const subs = [...document.querySelectorAll(sel)];
  return subs.map((el, i) => {
    const cs = getComputedStyle(el);
    const lh = parseFloat(cs.lineHeight);
    const padV = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
    const box = el.getBoundingClientRect();
    const h = el.offsetHeight - padV;          // 去掉上下 padding 的文本高度
    // 单行自然宽度：必须**同时**解封 white-space 与 max-width，
    // 否则 max-content 会被 max-width 截断，量到的永远是框宽（饱和值）。
    const oldWs = el.style.whiteSpace, oldMw = el.style.maxWidth;
    el.style.whiteSpace = 'nowrap';
    el.style.maxWidth = 'none';
    const naturalW = el.getBoundingClientRect().width
                     - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    el.style.whiteSpace = oldWs;
    el.style.maxWidth = oldMw;
    return {
      i,
      text: el.textContent.trim(),
      lines: Math.max(1, Math.round(h / lh)),
      boxW: Math.round(box.width),
      capW: parseFloat(cs.maxWidth),
      padH: parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight),
      naturalW: Math.round(naturalW),
    };
  });
}
"""


def launch(p):
    """与 build_video.py 一致的浏览器回退链：Playwright 自带 chromium 常缺失。"""
    last = None
    for kw in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def main():
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto("file:///" + INDEX.replace("\\", "/"))
        pg.wait_for_timeout(1200)
        rows = pg.evaluate(JS, CAP_CLASS)
        b.close()

    if not rows:
        print(f"[x] 没找到字幕元素（选择器 {CAP_CLASS}）—— "
              f"检查 scene_kit.SHELL_CSS 的类名是否变了")
        return

    print(f"共 {len(rows)} 条字幕（选择器 {CAP_CLASS}，视口 {W}×{H}）")
    print("-" * 88)
    print(f"{'#':>2} {'行数':>4} {'单行宽':>7} {'文本净宽':>8} {'占净宽':>7}  文案")
    print("-" * 88)
    over2, tight, longest = [], [], None
    for r in rows:
        room = r["capW"] - r["padH"]        # 真正的文本可用宽（扣掉左右 padding）
        ratio = r["naturalW"] / room if room else 0
        flag = ""
        if r["lines"] > 2:
            flag = "  <== 超 2 行"
            over2.append(r)
        elif r["naturalW"] > room and r["lines"] == 1:
            flag = "  <== 行数/宽度不自洽"
        if ratio > 0.96:
            tight.append(r)
        if longest is None or r["naturalW"] > longest["naturalW"]:
            longest = r
        print(f"{r['i']:>2} {r['lines']:>4} {r['naturalW']:>7} "
              f"{round(room):>8} {ratio:>6.2f}  {r['text'][:30]}{flag}")
    print("-" * 88)

    n2 = sum(1 for r in rows if r["lines"] == 2)
    print(f"单行 {len(rows)-n2} 条 / 双行 {n2} 条")
    if longest:
        print(f"最长单行 #{longest['i']}：{longest['naturalW']}px "
              f"（净宽 {round(longest['capW']-longest['padH'])}px，"
              f"占 {longest['naturalW']/(longest['capW']-longest['padH']):.2f}）")
    if over2:
        print(f"[!] {len(over2)} 条超过 2 行 —— 字幕带会顶满，需缩短文案或降字号")
    elif tight:
        print(f"[!] {len(tight)} 条单行宽已占净宽 96% 以上 —— 换词或降一档字号更稳")
    else:
        print("[OK] 全部 ≤ 2 行，且单行宽度有余量")


if __name__ == "__main__":
    main()
