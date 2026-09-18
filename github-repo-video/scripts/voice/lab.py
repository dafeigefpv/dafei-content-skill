# -*- coding: utf-8 -*-
"""音色试听台：同一句真实台词，用多个候选音色 + 参数组合各合成一版。

用途：选出「AI 味最淡」的配音方案。输出 audio/lab/<label>.mp3 便于试听。

用法：
    python voice/lab.py probe          # 只探测哪些音色名可用
    python voice/lab.py render         # 合成全部候选
    python voice/lab.py render --only a1,b2
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
os.makedirs(LAB, exist_ok=True)

FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

# 试听台词：取真实脚本里信息密度最高的一句（含数字、逗号停顿、口语连接词）
TEXT = "现在有人把整套流程搬回了你自己的电脑，五个月涨到两万九千八百星。"

# 官方列表内的普通话/方言音色
OFFICIAL = [
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-YunjianNeural",
    "zh-CN-YunyangNeural",
    "zh-CN-YunxiaNeural",
    "zh-CN-liaoning-XiaobeiNeural",
    "zh-CN-shaanxi-XiaoniNeural",
]

# 官方列表外、值得一试的多语言/新音色（edge 端点可能透传可用）
EXTRA = [
    "zh-CN-XiaoxiaoMultilingualNeural",
    "zh-CN-XiaochenMultilingualNeural",
    "zh-CN-XiaoyuMultilingualNeural",
    "zh-CN-YunyiMultilingualNeural",
    "zh-CN-YunxiaoMultilingualNeural",
    "zh-CN-XiaobeiMultilingualNeural",
    "zh-CN-XiaoxiaoDialectsNeural",
    "zh-CN-XiaoshuangNeural",
    "zh-CN-XiaozhenNeural",
]

# 候选方案：label -> (voice, rate, pitch, volume)
CANDS = {
    # —— 基准：当前线上方案 ——
    "A0-current-yunxi18":   ("zh-CN-YunxiNeural",    "+18%", "+0Hz",  "+0%"),
    # —— 同音色、放缓语速（放慢通常显著降低机械感）——
    "A1-yunxi-0":           ("zh-CN-YunxiNeural",    "+0%",  "+0Hz",  "+0%"),
    "A2-yunxi-8":           ("zh-CN-YunxiNeural",    "+8%",  "+0Hz",  "+0%"),
    # —— 云健：情绪更饱满（体育解说底色，起伏大）——
    "B1-yunjian-8":         ("zh-CN-YunjianNeural",  "+8%",  "+0Hz",  "+0%"),
    "B2-yunjian-0-low":     ("zh-CN-YunjianNeural",  "+0%",  "-3Hz",  "+0%"),
    # —— 晓晓：温暖女声，最不像播报 ——
    "C1-xiaoxiao-8":        ("zh-CN-XiaoxiaoNeural", "+8%",  "+0Hz",  "+0%"),
    "C2-xiaoxiao-0":        ("zh-CN-XiaoxiaoNeural", "+0%",  "+0Hz",  "+0%"),
    # —— 晓伊：活泼，偏口语 ——
    "D1-xiaoyi-8":          ("zh-CN-XiaoyiNeural",   "+8%",  "+0Hz",  "+0%"),
    # —— 云扬：新闻播报（预期最"AI"，作为对照组）——
    "E1-yunyang-8":         ("zh-CN-YunyangNeural",  "+8%",  "+0Hz",  "+0%"),
    # —— 语气微调：略降调门显得更松弛 ——
    "F1-yunxi-8-low":       ("zh-CN-YunxiNeural",    "+8%",  "-4Hz",  "+0%"),
    "F2-yunjian-8-low":     ("zh-CN-YunjianNeural",  "+8%",  "-4Hz",  "+0%"),
}


def dur(path):
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return -1.0


async def try_voice(voice, rate="+0%", pitch="+0Hz", volume="+0%",
                    text=TEXT, retries=3, cool=0.0):
    """试合一段，返回 (ok, bytes, marks, err)。"""
    last = ""
    for attempt in range(retries):
        try:
            comm = edge_tts.Communicate(
                text, voice, rate=rate, pitch=pitch, volume=volume,
                boundary="WordBoundary",
            )
            audio, marks = bytearray(), []
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    audio.extend(ch["data"])
                elif ch["type"] == "WordBoundary":
                    marks.append(ch)
            if len(audio) > 2000:
                return True, bytes(audio), marks, ""
            last = f"empty audio={len(audio)} marks={len(marks)}"
            if marks:  # 有 marks 无音频 → 该音色大概率不被支持
                last += " (voice unsupported?)"
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        if attempt < retries - 1:
            wait = min(30.0, 2.5 * (1.7 ** attempt)) + random.uniform(0, 2)
            if cool:
                wait = max(wait, cool)
            print(f"      retry {attempt+1} in {wait:.1f}s — {last}")
            await asyncio.sleep(wait)
    return False, b"", [], last


async def probe():
    print("=== 探测音色可用性（edge 端点是否透传）===")
    ok, bad = [], []
    for v in OFFICIAL + EXTRA:
        success, audio, marks, err = await try_voice(v, retries=1)
        tag = "OK  " if success else "FAIL"
        print(f"  {tag} {v:38s} {len(audio):>7d}B marks={len(marks):>3d}  {err}")
        (ok if success else bad).append(v)
        await asyncio.sleep(1.2)
    print(f"\n可用 {len(ok)}: {ok}")
    print(f"不可用 {len(bad)}: {bad}")
    json.dump({"ok": ok, "bad": bad}, open(os.path.join(LAB, "probe.json"), "w"),
              ensure_ascii=False, indent=1)


async def render(only=None):
    print(f"=== 合成候选项（台词 {len(TEXT)} 字）===")
    report = []
    items = [(k, v) for k, v in CANDS.items() if not only or k in only]
    for i, (label, (voice, rate, pitch, volume)) in enumerate(items):
        out = os.path.join(LAB, f"{label}.mp3")
        if os.path.exists(out) and os.path.getsize(out) > 2000:
            print(f"  [{i+1}/{len(items)}] {label:24s} 复用")
            report.append({"label": label, "voice": voice, "rate": rate,
                           "pitch": pitch, "dur": dur(out), "bytes": os.path.getsize(out)})
            continue
        if i > 0:
            await asyncio.sleep(3.5)   # 冷却，规避限流
        success, audio, marks, err = await try_voice(voice, rate, pitch, volume)
        if success:
            with open(out, "wb") as f:
                f.write(audio)
            d = dur(out)
            # 语速体检：字/秒
            cps = len(TEXT.replace("，", "").replace("。", "")) / d if d > 0 else 0
            print(f"  [{i+1}/{len(items)}] {label:24s} {d:5.2f}s  {cps:4.2f}字/s  {len(marks)} marks")
            report.append({"label": label, "voice": voice, "rate": rate,
                           "pitch": pitch, "dur": round(d, 2),
                           "cps": round(cps, 2), "bytes": len(audio)})
        else:
            print(f"  [{i+1}/{len(items)}] {label:24s} 失败: {err}")
            report.append({"label": label, "voice": voice, "rate": rate,
                           "pitch": pitch, "error": err})
        await asyncio.sleep(0.8)
    json.dump(report, open(os.path.join(LAB, "report.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"\n输出目录: {LAB}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    if mode == "probe":
        asyncio.run(probe())
    else:
        asyncio.run(render(only))
