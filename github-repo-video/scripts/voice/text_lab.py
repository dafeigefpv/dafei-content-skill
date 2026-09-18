# -*- coding: utf-8 -*-
"""文本口语化对照：同一音色、同一语速，只改文本，听「AI 味」有多少来自稿子本身。

三个语义块，各做「书面稿 / 口语稿」两版，交替拼接成一条对照音频。
音色固定云希、语速固定 +8%，确保变量只有文本。
"""

import asyncio
import os
import random
import subprocess

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # scripts/voice/ -> 项目根
LAB = os.path.join(ROOT, "audio", "textlab")
os.makedirs(LAB, exist_ok=True)

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
VOICE = "zh-CN-YunxiNeural"
LABEL_VOICE = "zh-CN-YunyangNeural"
RATE = "+8%"

# (块名, 书面稿, 口语稿)
PAIRS = [
    (
        "c3 星标段",
        "现在有人把整套流程搬回了你自己的电脑，五个月涨到两万九千八百星。",
        "现在呢，有人干脆把这一整套，都搬回了你自己的电脑上。五个月，两万九千八百星。",
    ),
    (
        "p2 亮点段",
        "一套软件干六种活，克隆、设计、配音、听写、转录、有声书全在里面。",
        "一个软件，六件事全包了——克隆、配音、听写、转录，还有有声书。",
    ),
    (
        "s4 收尾段",
        "想要一个不限字数的配音方案，这个值得先收藏。",
        "要是不想再按字数花钱，这个，先存着。",
    ),
]


async def synth(text, voice, out, rate="+0%", retries=4):
    for attempt in range(retries):
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate)
            audio = bytearray()
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    audio.extend(ch["data"])
            if len(audio) > 1500:
                with open(out, "wb") as f:
                    f.write(audio)
                return True
        except Exception as exc:  # noqa: BLE001
            print(f"      retry {attempt+1} — {type(exc).__name__}")
        if attempt < retries - 1:
            await asyncio.sleep(min(30, 2.5 * (1.7 ** attempt)) + random.uniform(0, 2))
    return False


def sil(path, d):
    if not (os.path.exists(path) and os.path.getsize(path) > 100):
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi",
                        "-i", "anullsrc=r=24000:cl=mono", "-t", str(d),
                        "-c:a", "libmp3lame", "-b:a", "64k", path], check=True)


async def main():
    sil(os.path.join(LAB, "_s035.mp3"), 0.35)
    sil(os.path.join(LAB, "_s075.mp3"), 0.75)
    sil(os.path.join(LAB, "_s100.mp3"), 1.00)

    seq = []   # (报幕文本, 音频路径)

    for i, (name, written, spoken) in enumerate(PAIRS):
        for tag, text, label in (("a", written, f"第{['一','二','三'][i]}组，书面稿。"),
                                 ("b", spoken,  f"第{['一','二','三'][i]}组，口语稿。")):
            key = f"{i+1}{tag}"
            mp3 = os.path.join(LAB, f"{key}.mp3")
            lp = os.path.join(LAB, f"{key}-label.mp3")
            if i or tag == "b":
                await asyncio.sleep(3.0)
            ok = await synth(text, VOICE, mp3, RATE)
            n = len(text.replace("，", "").replace("。", "").replace("、", ""))
            print(f"  {key} {name:10s} {tag} {n:3d}字 {'OK' if ok else 'FAIL'}  {text}")
            await asyncio.sleep(1.0)
            await synth(label, LABEL_VOICE, lp)
            await asyncio.sleep(1.0)
            seq.append((lp, mp3))

    lst = os.path.join(LAB, "_list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for lp, mp3 in seq:
            f.write(f"file '{lp.replace(chr(92), '/')}'\n")
            f.write(f"file '{os.path.join(LAB, '_s035.mp3').replace(chr(92), '/')}'\n")
            f.write(f"file '{mp3.replace(chr(92), '/')}'\n")
            f.write(f"file '{os.path.join(LAB, '_s100.mp3').replace(chr(92), '/')}'\n")

    out = os.path.join(LAB, "00-文本对照.mp3")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c:a", "libmp3lame", "-b:a", "128k",
                    "-ar", "24000", out], check=True)
    print(f"\n对照音频: {out}  {os.path.getsize(out)/1024:.0f} KB")


if __name__ == "__main__":
    asyncio.run(main())
