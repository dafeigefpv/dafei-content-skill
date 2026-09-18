# -*- coding: utf-8 -*-
"""封面后期：去水印 + 补项目名/系列徽章 + 3:4 成图 + 版式体检。

生图模型只会画「标题 + 星数 + 主视觉」，**不会写项目名**——截屏给观众不知道讲的是哪个项目，
所以页脚必须后期补。平台还会在右下角盖自己的水印，一并去掉。

用法（默认全部走约定，通常不用带参数）：
    python scripts/fix_cover.py
    python scripts/fix_cover.py --slug=VoiceStudio --badge="项目日报 · 每天一个Github热门项目"
    python scripts/fix_cover.py --no-wm                 # 画面本来就干净时跳过去水印
    python scripts/fix_cover.py --wm-roi=0.78,0.90      # 水印位置和默认不一样时

输入约定：`cover/raw.png`（生图产物**必须改名成 raw.png**，见坑位 16）
输出：`cover/cover.png`（原生 3:4）、`cover/cover-1440x1920.png`（对齐成片）、
      `cover/crop-1to1-preview.png`（小红书个人主页 1:1 网格的裁切预判）
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_BADGE = "项目日报 · 每天一个Github热门项目"
FONT_BD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_RG = r"C:\Windows\Fonts\msyh.ttc"
SAFE = 0.10          # 左右安全区（占画幅宽）
BOTTOM_MIN = 0.10    # 底部净空下限（页脚要落在这条带子里）
CROP_LINE = 0.125    # 1:1 中心裁切会切掉上下的比例（(4-3)/2/4）


def arg_parser():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--raw", default=None, help="生图原图，默认 <proj>/cover/raw.png")
    p.add_argument("--out", default=None, help="输出目录，默认 <proj>/cover")
    p.add_argument("--slug", default=None, help="项目名（页脚左），默认读 storyboard.json 的 slug")
    p.add_argument("--badge", default=DEFAULT_BADGE, help="系列徽章（页脚右）")
    p.add_argument("--no-wm", action="store_true", help="跳过去水印")
    p.add_argument("--wm-roi", default="0.80,0.885",
                   help="水印 ROI 左上角的相对坐标 x0,y0（默认 0.80,0.885＝右下角）")
    return p.parse_args()


def rel(path):
    return os.path.relpath(path, os.getcwd())


def resolve_slug(explicit, proj):
    if explicit:
        return explicit
    # 目录名历史上叫过 script/，现为 scripts/；根目录也认。
    for sub in ("scripts", "script", ""):
        sb = os.path.join(proj, sub, "storyboard.json")
        if os.path.exists(sb):
            try:
                return json.load(open(sb, encoding="utf-8")).get("slug") or "Unknown"
            except Exception:
                pass
    return "Unknown"


# ---------------------------------------------------------------- 水印
def neighbours(a):
    """四邻域均值。**不能用 np.roll**——它会在数组边界环绕，把对边像素拉过来，
    在 ROI 边缘留下一块明显热点（实测）。np.pad(mode='edge') 钳制边界才干净。"""
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    return (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4.0


def strip_watermark(im, roi_xy):
    W, H = im.size
    x0, y0 = int(W * roi_xy[0]), int(H * roi_xy[1])
    roi = np.asarray(im.crop((x0, y0, W, H))).astype(np.float32)

    # 水印是浅灰白字（灰度峰值 ~154），背景深蓝仅 ~33。用「中值差分」而非绝对阈值：
    # 绝对阈值会漏掉抗锯齿的过渡像素（实测只命中 8px），差分法只问「比周围亮多少」，
    # 对渐变背景同样稳。
    gray = roi.mean(axis=2)
    med = np.asarray(
        Image.fromarray(gray.astype(np.uint8)).filter(ImageFilter.MedianFilter(15)),
        dtype=np.float32)
    hit = (gray - med) > 9
    ratio = hit.mean()
    if ratio > 0.12:
        print(f"[水印] ! ROI 内 {ratio:.1%} 像素被判为笔画，疑似把真实内容当成了水印，"
              f"已跳过。请核对 --wm-roi，或加 --no-wm。")
        return im
    if hit.sum() == 0:
        print("[水印] 未检出（画面可能本来就干净）")
        return im

    mask_im = Image.fromarray((hit * 255).astype(np.uint8))
    mask_im = mask_im.filter(ImageFilter.MaxFilter(11))   # 膨胀 5px，吃掉抗锯齿边缘
    mask = np.asarray(mask_im) > 0
    print(f"[水印] 笔画 {int(hit.sum())} px，膨胀后 {int(mask.sum())} px")

    # Jacobi 扩散修补
    filled = roi.copy()
    filled[mask] = roi[~mask].mean(axis=0)
    for _ in range(900):
        filled[mask] = neighbours(filled)[mask]
    filled[~mask] = roi[~mask]        # 非水印像素原样回贴，保证接缝连续

    # 补颗粒：只统计「干净背景」的高频残差，且排除边缘（边缘会让 sigma 虚高、修完发麻）
    hp = roi - np.asarray(
        Image.fromarray(roi.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)),
        dtype=np.float32)
    inner = np.zeros_like(mask)
    inner[10:-10, 10:-10] = True
    sigma = float(np.clip(hp[~mask & inner].std(), 0.8, 3.0))
    rng = np.random.default_rng(20260917)
    filled = np.clip(filled + rng.normal(0, sigma, size=filled.shape) * mask[..., None], 0, 255)
    filled[~mask] = roi[~mask]
    print(f"[颗粒] sigma={sigma:.2f}")

    out = im.copy()
    out.paste(Image.fromarray(filled.astype(np.uint8)), (x0, y0))
    return out


# ---------------------------------------------------------------- 体检
def measure(im):
    """量主体版式。**必须在画页脚之前调用**——否则页脚字会被当成主体内容，
    底部净空必然报 2%（实测踩过这个假阴性）。"""
    W, H = im.size
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    g = a.mean(axis=2)
    m = {"size": (W, H)}

    white = (g > 200) & (a.max(axis=2) - a.min(axis=2) < 40)
    rows = np.where(white.sum(axis=1) > 18)[0]
    m["title_top"] = int(rows.min()) if len(rows) else None

    yellow = (a[:, :, 0] > 200) & (a[:, :, 1] > 170) & (a[:, :, 2] < 90)
    yr = np.where(yellow.sum(axis=1) > 40)[0]
    m["label"] = (int(yr.min()), int(yr.max())) if len(yr) else None

    # 底部净空：阈值必须按背景自适应，且不能用固定值。
    #   固定 g>60  → 把「地面反光」当主体，报到净空 2.5%（实测噪声）
    #   bg+45      → 仍被反光拖到 9.0%
    #   bg+55      → 正好卡在实体边缘（实测 13.2%，与肉眼判断一致）✔
    #   高频对比度也试过，分不开——地面反光带木纹质感，本身就有高频。
    bg = float(np.median(g))
    th = bg + 55
    body = g > th
    body[int(H * 0.86):, int(W * 0.78):] = False     # 右下角水印 ROI 不计
    nb = np.where(body.sum(axis=1) > 10)[0]
    m["content_bottom"] = int(nb.max()) if len(nb) else -1
    m["bottom_clear"] = H - 1 - m["content_bottom"] if len(nb) else H
    m["bg"] = bg
    m["th"] = th
    return m


def qa_report(im, m, out_dir):
    W, H = m["size"]
    print("\n[体检] 版式")
    print(f"  画幅 {W}×{H}  ratio {W/H:.4f}（3:4 = 0.7500）")
    ok = True

    t0 = m["title_top"]
    line = round(H * CROP_LINE)
    if t0 is None:
        print("  [!] 未检出白色标题文字，请人工确认")
        ok = False
    else:
        print(f"  标题顶距 y={t0}（{t0/H:.1%}）  1:1 裁切线 y={line}  余量 {t0-line} px")
        if t0 < line:
            print(f"  [!] 标题会被 1:1 中心裁切切掉 {line-t0} px"
                  f"（小红书个人主页网格）——重跑生图，把提示词顶部留白再加大")
            ok = False
        elif t0 - line < 8:
            print(f"  [~] 余量仅 {t0-line} px，卡在裁切线上；提示词顶部留白建议再加大一档")
    if m["label"]:
        a, b = m["label"]
        print(f"  黄标签 y {a}~{b}（{a/H:.1%}~{b/H:.1%}）")
    else:
        print("  [!] 未检出黄色标签")

    bc = m["bottom_clear"]
    print(f"  底部净空 {bc} px（{bc/H:.1%}）  判据 g>{m['th']:.0f}"
          f"（背景中位数 {m['bg']:.0f}+55），主体下沿 y={m['content_bottom']}")
    # 硬判据是「页脚能不能落在干净地面上」，不是「净空 ≥10%」——后者只是美观余量。
    footer_top = H - round(H * 0.022) - round(H * 0.0234)
    if m["content_bottom"] >= footer_top:
        print(f"  [!] 主体侵入页脚带（页脚文字顶端 y={footer_top}）——"
              f"缩小主体、或把页脚字号/基线再贴底一点")
        ok = False
    elif bc / H < BOTTOM_MIN:
        print(f"  [~] 净空 {bc/H:.1%} 低于 {BOTTOM_MIN:.0%}（页脚仍落得下，但偏挤）")

    c = (H - W) // 2
    im.crop((0, c, W, H - c)).resize((420, 420), Image.LANCZOS)\
      .save(os.path.join(out_dir, "crop-1to1-preview.png"))
    print(f"  1:1 裁切预览 -> {rel(os.path.join(out_dir, 'crop-1to1-preview.png'))}")
    return ok


def main():
    args = arg_parser()
    proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = args.out or os.path.join(proj, "cover")
    raw = args.raw or os.path.join(out_dir, "raw.png")
    if not os.path.exists(raw):
        sys.exit(f"[X] 找不到原图 {raw}\n    生图后请把产物改名成 raw.png（坑位 16）")

    im = Image.open(raw).convert("RGB")
    W, H = im.size
    if abs(W / H - 3 / 4) > 0.01:            # 不是 3:4 就中心裁到 3:4
        if W / H > 3 / 4:
            w = round(H * 3 / 4)
            im = im.crop(((W - w) // 2, 0, (W - w) // 2 + w, H))
        else:
            h = round(W * 4 / 3)
            im = im.crop((0, (H - h) // 2, W, (H - h) // 2 + h))
        print(f"[裁切] {W}×{H} 非 3:4，已中心裁到 {im.size[0]}×{im.size[1]}")
        W, H = im.size

    if not args.no_wm:
        im = strip_watermark(im, tuple(float(x) for x in args.wm_roi.split(",")))

    m = measure(im)          # 必须先量主体再画页脚（见 measure() 注释）

    # ---------- 页脚：项目名 + 系列徽章 ----------
    # 贴底处理（底边距 H*0.022），**不套 10% 安全区**——主体下沿离底边通常不足 10%，
    # 按 10% 放字会直接压在主体上（实测踩过）。
    d = ImageDraw.Draw(im)
    f_name = ImageFont.truetype(FONT_BD, round(H * 0.0234), index=0)
    f_badge = ImageFont.truetype(FONT_RG, round(H * 0.0130), index=0)
    side = round(W * SAFE)
    base = H - round(H * 0.022)
    slug = resolve_slug(args.slug, proj)
    d.text((side, base), slug, font=f_name, fill=(255, 255, 255), anchor="ls")
    d.text((W - side, base - 1), args.badge, font=f_badge,
           fill=(170, 188, 216), anchor="rs")
    print(f"\n[页脚] 左 {slug} / 右 {args.badge}（基线 y={base}，字号 "
          f"{round(H*0.0234)}/{round(H*0.0130)}）")

    ok = qa_report(im, m, out_dir)

    im.save(os.path.join(out_dir, "cover.png"))
    im.resize((1440, 1920), Image.LANCZOS).save(os.path.join(out_dir, "cover-1440x1920.png"))
    print(f"\n[OK] cover.png {W}×{H} / cover-1440x1920.png 1440×1920"
          f"{'' if ok else '   —— 体检有告警，见上'}")


if __name__ == "__main__":
    main()
