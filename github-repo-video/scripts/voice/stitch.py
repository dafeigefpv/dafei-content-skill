# -*- coding: utf-8 -*-
"""把试听样本拼成一条带语音报幕的合集，方便一次听完对比。

结构：[报幕][0.35s][样本][0.8s] x N
报幕用云扬（新闻腔），与所有候选音色都能区分开。
"""

import asyncio
import json
import os
import random
import subprocess
import sys

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # scripts/voice/ -> 项目根
LAB = os.path.join(ROOT, "audio", "lab")
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"

LABEL_VOICE = "zh-CN-YunyangNeural"

# 报幕文案：序号 + 音色 + 特点
ANNOUNCE = {
    "A0-current-yunxi18": "第一款，云希，当前线上方案，语速加十八。",
    "A1-yunxi-0":         "第二款，云希，原速。",
    "A2-yunxi-8":         "第三款，云希，语速加八。",
    "B1-yunjian-8":       "第四款，云健，语速加八。",
    "B2-yunjian-0-low":   "第五款，云健，原速，音调降三。",
    "C1-xiaoxiao-8":      "第六款，晓晓，语速加八。",
    "C2-xiaoxiao-0":      "第七款，晓晓，原速。",
    "D1-xiaoyi-8":        "第八款，晓伊，语速加八。",
    "E1-yunyang-8":       "第九款，云扬，语速加八。",
    "F1-yunxi-8-low":     "第十款，云希，语速加八，音调降四。",
    "F2-yunjian-8-low":   "第十一款，云健，语速加八，音调降四。",
}

ORDER = list(ANNOUNCE.keys())


async def synth(text, voice, out, retries=4):
    for attempt in range(retries):
        try:
            comm = edge_tts.Communicate(text, voice)
            audio = bytearray()
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    audio.extend(ch["data"])
            if len(audio) > 1500:
                with open(out, "wb") as f:
                    f.write(audio)
                return True
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1} — {type(exc).__name__}")
        if attempt < retries - 1:
            await asyncio.sleep(min(30, 2.5 * (1.7 ** attempt)) + random.uniform(0, 2))
    return False


async def main():
    labels_dir = os.path.join(LAB, "labels")
    os.makedirs(labels_dir, exist_ok=True)
    existing = [k for k in ORDER
                if os.path.exists(os.path.join(LAB, f"{k}.mp3"))]
    print(f"样本 {len(existing)}/{len(ORDER)} 就绪")

    # ---- 1) 报幕音 ----
    print("=== 生成报幕 ===")
    for i, key in enumerate(existing):
        lp = os.path.join(labels_dir, f"{key}.mp3")
        if os.path.exists(lp) and os.path.getsize(lp) > 1500:
            print(f"  {key:24s} 复用")
            continue
        if i > 0:
            await asyncio.sleep(3.0)
        ok = await synth(ANNOUNCE[key], LABEL_VOICE, lp)
        print(f"  {key:24s} {'OK' if ok else 'FAIL'}")
        await asyncio.sleep(1.0)

    # ---- 2) 拼接 ----
    print("=== 拼接合集 ===")
    silence_a = os.path.join(LAB, "_sil035.mp3")
    silence_b = os.path.join(LAB, "_sil080.mp3")
    for path, d in ((silence_a, 0.35), (silence_b, 0.80)):
        if not (os.path.exists(path) and os.path.getsize(path) > 100):
            subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi",
                            "-i", f"anullsrc=r=24000:cl=mono", "-t", str(d),
                            "-c:a", "libmp3lame", "-b:a", "64k", path], check=True)

    lst = os.path.join(LAB, "_list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for key in existing:
            for p in (os.path.join(labels_dir, f"{key}.mp3"),
                      silence_a,
                      os.path.join(LAB, f"{key}.mp3"),
                      silence_b):
                f.write(f"file '{p.replace(chr(92), '/')}'\n")

    out = os.path.join(LAB, "00-试听合集.mp3")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c:a", "libmp3lame", "-b:a", "128k",
                    "-ar", "24000", out], check=True)
    size = os.path.getsize(out)
    print(f"合集: {out}  {size/1024:.0f} KB")

    # 索引清单
    index = [(i + 1, k) for i, k in enumerate(existing)]
    with open(os.path.join(LAB, "00-索引.txt"), "w", encoding="utf-8") as f:
        for n, k in index:
            f.write(f"{n:2d}. {k}\n")
    print("索引已写入 00-索引.txt")


if __name__ == "__main__":
    asyncio.run(main())
