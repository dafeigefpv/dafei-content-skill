# -*- coding: utf-8 -*-
"""
版面占位探针 —— 用文字把每一屏「哪块地方有东西」画出来。

为什么需要它
------------
build_video.py 的越界检查只能回答「有没有溢出」，回答不了「有没有空」。
而「口播念前半句时画面只有半张」正是这一版要根治的问题，它既不溢出、
也不报错，只在人的眼睛里才是毛病 —— 所以得能把它量出来。

做法
----
把舞台 1224×1280 切成 12×16 的格子，把「可见元素」投影上去，打出 ASCII 图：

    .  空     -  有内容（淡）     #  有内容（实）
    L  左半有 / 右半空           （见每屏下方的左右占比）

可见 = 自身与所有祖先的 opacity ≥ 0.06，且 display/visibility 正常；
内容 = 有直接文字的（按文字实际包围盒算）或 有背景/边框的盒子。
装饰层（data-deco，如 s3 的整屏色块）与透明容器不计。

用法
----
    python scripts/check_fill.py                    # 每屏取 35% / 85% 两个时刻
    python scripts/check_fill.py --at 0.3,0.6,0.9
    python scripts/check_fill.py --blocks c2,s5     # 只看某几屏
"""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "video"

COLS, ROWS = 12, 16
AT = [0.35, 0.85]
ONLY = None
for a in sys.argv[1:]:
    if a.startswith("--at="):
        AT = [float(x) for x in a.split("=", 1)[1].split(",")]
    elif a.startswith("--blocks="):
        ONLY = set(a.split("=", 1)[1].split(","))

TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
BLOCKS = [(b["id"], b["start"], b["end"]) for sc in TL["scenes"] for b in sc["blocks"]]

# ---------------------------------------------------------------- 浏览器侧
JS_MAP = r"""
([bid, t, cols, rows]) => {
  const tl = (window.__timelines || {})['repo-video'];
  if (!tl) return {err: 'no timeline'};
  tl.time(t, false);

  const board = document.querySelector('[data-b="' + bid + '"]');
  if (!board) return {err: 'no board ' + bid};
  const br = board.getBoundingClientRect();

  const vis = e => {
    let n = e;
    while (n && n !== document.documentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return false;
      if (parseFloat(cs.opacity) < 0.06) return false;
      n = n.parentElement;
    }
    return true;
  };
  const alphaOf = c => {
    const m = /rgba?\(([^)]+)\)/.exec(c);
    if (!m) return 0;
    const p = m[1].split(',').map(s => parseFloat(s));
    return p.length > 3 ? p[3] : 1;
  };
  const textRect = e => {
    const r = document.createRange();
    for (const n of e.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim()) {
        r.selectNodeContents(n);
        const b = r.getBoundingClientRect();
        if (b.width > 1 && b.height > 1) return b;
      }
    }
    return null;
  };

  const grid = Array.from({length: rows}, () => new Array(cols).fill(0));
  const others = [];
  let painted = 0;
  // 整屏底色（如 s3 的克莱因蓝 veil）：它铺满舞台却被排除在占位率之外，
  // 会让「纯色打底 + 少量文字」的屏被误报成「半屏空」（s3 实测 12.5%）。
  // 检出后单独标注，让判读的人知道这一屏的低占位是统计口径造成的。
  let decoFull = false;

  for (const e of board.querySelectorAll('*')) {
    if (e.classList.contains('board')) continue;
    if (e.hasAttribute('data-deco')) {
      if (vis(e)) {
        const b = e.getBoundingClientRect();
        const w = Math.max(0, Math.min(b.right, br.right) - Math.max(b.left, br.left));
        const h = Math.max(0, Math.min(b.bottom, br.bottom) - Math.max(b.top, br.top));
        const cs2 = getComputedStyle(e);
        // ⚠️ 只看 backgroundColor 会漏掉渐变底（s3 的 veil 就是 linear-gradient，
        // 此时 backgroundColor 是 rgba(0,0,0,0)，检查会静默失效）。
        const painted = alphaOf(cs2.backgroundColor) > 0.04 ||
                        (cs2.backgroundImage && cs2.backgroundImage !== 'none');
        if (w * h / (br.width * br.height) >= 0.7 && painted) decoFull = true;
      }
      continue;
    }
    if (!vis(e)) continue;
    const cs = getComputedStyle(e);

    let rects = [];
    const tr = textRect(e);
    if (tr) rects.push(tr);
    const bg = alphaOf(cs.backgroundColor) > 0.04 && cs.backgroundColor !== 'transparent';
    const bs = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderLeftWidth)
             + parseFloat(cs.borderRightWidth) + parseFloat(cs.borderBottomWidth);
    if (bg || bs > 0) {
      const b = e.getBoundingClientRect();
      if (b.width > 1 && b.height > 1) rects.push(b);
    }
    for (const b of rects) {
      if (b.width * b.height < 260) continue;
      painted++;
      // 投影到网格（clip 到舞台）
      const x0 = Math.max(0, Math.min(cols - 1, Math.floor((b.left - br.left) / br.width * cols)));
      const x1 = Math.max(0, Math.min(cols - 1, Math.floor((b.right - br.left) / br.width * cols)));
      const y0 = Math.max(0, Math.min(rows - 1, Math.floor((b.top - br.top) / br.height * rows)));
      const y1 = Math.max(0, Math.min(rows - 1, Math.floor((b.bottom - br.top) / br.height * rows)));
      if (b.right < br.left - 2 || b.left > br.right + 2) continue;
      if (b.bottom < br.top - 2 || b.top > br.bottom + 2) continue;
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) grid[y][x] = 1;
    }
    // 记录「有文字」的元素名，便于定位
    if (tr && tr.width * tr.height > 600) others.push(e.className.toString().slice(0, 22));
  }

  const filled = grid.flat().reduce((a, b) => a + b, 0);
  let left = 0, right = 0, top = 0, bottom = 0;
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
    if (!grid[y][x]) continue;
    if (x < cols / 2) left++; else right++;
    if (y < rows / 2) top++; else bottom++;
  }
  const rowsStr = grid.map((r, i) =>
    String(i).padStart(2, '0') + ' ' + r.map(v => v ? '#' : '.').join(' '));
  return {pid: bid, t: +t.toFixed(2), filled: filled, total: cols * rows,
          left: left, right: right, top: top, bottom: bottom,
          painted: painted, rows: rowsStr, kinds: [...new Set(others)],
          decoFull: decoFull};
}
"""

if __name__ == "__main__":
    targets = [b for b in BLOCKS if not ONLY or b[0] in ONLY]
    print(f"占位探针：{len(targets)} 屏 × {len(AT)} 时刻，网格 {COLS}×{ROWS}\n")
    with sync_playwright() as p:
        last = None
        for kw in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
            try:
                br = p.chromium.launch(**kw)
                break
            except Exception as e:  # noqa: BLE001
                last = e
        else:
            raise last
        pg = br.new_page(viewport={"width": 1440, "height": 1920}, device_scale_factor=1)
        pg.goto("file:///" + str(OUT / "index.html").replace("\\", "/"))
        pg.wait_for_timeout(1000)

        worst = []
        for bid, st, en in targets:
            dur = en - st
            for frac in AT:
                r = pg.evaluate(JS_MAP, [bid, st + dur * frac, COLS, ROWS])
                if r.get("err"):
                    print(f"[x] {bid}: {r['err']}")
                    continue
                pct = r["filled"] / r["total"] * 100
                lr = r["left"] / max(1, r["right"] + r["left"]) * 100
                tag = "  [整屏底色，占位率不可比]" if r.get("decoFull") else ""
                print(f"── {bid}  t={r['t']:>6.2f}s（块内 {frac:.0%}）"
                      f"  占位 {pct:>5.1f}%  左占比 {lr:>5.1f}%{tag}")
                for line in r["rows"]:
                    print("     " + line)
                print(f"     含文字元素: {', '.join(r['kinds'][:9])}")
                print()
                # 整屏底色的屏不参与低占位告警 —— 它整屏都被颜色铺满了，
                # 只是那块颜色按定义算作装饰、不进占位统计。
                if pct < 45 and not r.get("decoFull"):
                    worst.append((pct, bid, frac))
        br.close()

    print("=" * 62)
    if worst:
        print("占位偏低（<45%）的屏/时刻 —— 可能就是「半屏空」：")
        for pct, bid, frac in sorted(worst):
            print(f"   {bid} @ {frac:.0%}  占位 {pct:.1f}%")
    else:
        print("各屏在各时刻占位均 ≥45%，无明显空白区。")
