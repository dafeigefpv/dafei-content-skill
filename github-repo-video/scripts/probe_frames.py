# -*- coding: utf-8 -*-
"""
seek 抓帧探针（3:4 版）。

整条渲染要 90 秒，而「某一瞬间长什么样」用 seek 只要 2 秒 —— 把静态问题
（元素缺失、遮挡、溢出、行数不对）在探针阶段清完，再进渲染。

用法
----
    python scripts/probe_frames.py 6.4 25.0        # 指定时刻
    python scripts/probe_frames.py --blocks        # 每块中点
    python scripts/probe_frames.py --blocks --sync  # 附带「本块新亮了什么」

--sync 会沿时间轴密集采样，算出每个子元素的首次可见时刻，归属到所在块，
从而回答「这一块口播时，画面上到底新出现了什么」。
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "video"
TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
W, H = 1440, 1920
SHOT = OUT / "probe"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
FLAGS = {a for a in sys.argv[1:] if a.startswith("--")}

blocks = [(sc, b) for sc in TL["scenes"] for b in sc["blocks"]]
if "--blocks" in FLAGS or not args:
    times = [(b["id"], round((b["start"] + b["end"]) / 2, 2)) for _, b in blocks]
else:
    times = [("t", float(a)) for a in args]

JS_SEEK = """
(t) => {
  const tl = (window.__timelines || {})['repo-video'];
  if (!tl) return 'NO_TIMELINE';
  tl.pause();
  tl.time(t, false);
  return 'ok';
}
"""

JS_SYNC = """
({total, step}) => {
  const tl = (window.__timelines || {})['repo-video'];
  if (!tl) return null;
  const boards = Array.from(document.querySelectorAll('.board'));
  const res = {};
  for (const bd of boards) res[bd.dataset.b] = [];
  const snap = () => {
    const m = {};
    for (const bd of boards) {
      const bid = bd.dataset.b;
      const list = [];
      bd.querySelectorAll('*').forEach((el, i) => {
        const cs = getComputedStyle(el);
        list.push([i, parseFloat(cs.opacity) || 0]);
      });
      m[bid] = list;
    }
    return m;
  };
  const first = {};
  let prev = null;
  for (let t = 0; t <= total + 1e-6; t += step) {
    tl.time(t, false);
    const cur = snap();
    for (const bid in cur) {
      cur[bid].forEach(([i, op], k) => {
        const key = bid + '#' + i;
        if (first[key] === undefined && op > 0.5 && prev && prev[bid] &&
            prev[bid][k][1] <= 0.5) {
          const el = document.querySelectorAll('.board[data-b="' + bid + '"] *')[i];
          first[key] = [t, (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 30)];
        }
      });
    }
    prev = cur;
  }
  return first;
}
"""


def launch(p):
    last = None
    for kw in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


SHOT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    br = launch(p)
    pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    pg.goto("file:///" + str(OUT / "index.html").replace("\\", "/"))
    pg.wait_for_timeout(1200)

    for tag, t in times:
        r = pg.evaluate(JS_SEEK, t)
        if r != "ok":
            print(f"[x] 无法 seek：{r}（index.html 里没有注册 __timelines）")
            break
        pg.wait_for_timeout(90)
        fp = SHOT / f"{tag}-{t:07.2f}.png"
        pg.screenshot(path=str(fp))
        print(f"  {tag:<4} t={t:>6.2f}s  ->  {fp.name}")

    if "--sync" in FLAGS:
        print("\n沿时间轴采样中（步长 0.1s）...")
        first = pg.evaluate(JS_SYNC, {"total": TL["total_duration"], "step": 0.1})
        br.close()
        if first:
            def owner(t):
                for sc, b in blocks:
                    if b["start"] - 1e-6 <= t < b["end"] - 1e-6:
                        return b
                return None
            per = {}
            for key, (t, txt) in first.items():
                b = owner(t)
                if b is None:
                    continue
                per.setdefault(b["id"], []).append((t, txt))
            print("=" * 74)
            for sc, b in blocks:
                items = sorted(per.get(b["id"], []))
                print(f"\n[{b['id']}] +{b['start']:.2f}s  {b['text'][:30]}")
                if not items:
                    print("    ⚠️ 本块期间画面没有任何新元素出现")
                for t, txt in items:
                    label = txt if txt else "(图形/装饰)"
                    print(f"    +{t-b['start']:5.2f}s  {label}")
            print("\n" + "=" * 74)
            never = [k for k in first if first[k] is None]
            print(f"检出首亮的元素数：{len(first)}；全程未亮的：{len(never)}")
        else:
            print("[x] 同步采样失败")
    else:
        br.close()
