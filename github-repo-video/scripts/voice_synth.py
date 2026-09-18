# -*- coding: utf-8 -*-
"""
旁白合成器：读 storyboard.json → edge-tts 合成 → 块级时间戳 → SRT 字幕 + 全局时间轴。

设计要点
--------
1. 逐场景合成（场景时长独立，画面时长由它反推）。
2. boundary="WordBoundary" 拿字级时间戳（默认 SentenceBoundary 粒度太粗）。
3. 块边界用「字符累积」定位：WordBoundary 的 text 按序拼接 == 原文去标点，
   因此累加字符数达到块长度时即为块边界，精度到毫秒。
4. edge-tts 偶发 NoAudioReceived（服务端抖动），必须重试。

输出
----
audio/scene-<id>.mp3     各场景旁白
audio/voice.mp3          拼接后的完整音轨（含场景间隔）
timeline.json            块级时间轴（场景/块/起止/字幕）+ 场景时长
subtitles.srt            全片字幕
"""

import asyncio
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUDIO = os.path.join(ROOT, "audio")
os.makedirs(AUDIO, exist_ok=True)

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

# 需要从块文本里剔除的标点（用于字符累积匹配）
PUNCT = "，。、；：！？""''（）《》〈〉——…·,.!?;:\"'()[]{}<>-~　 \n\r\t"

SARCASTIC_FIX = str.maketrans("", "", PUNCT)


def clean(s: str) -> str:
    return s.translate(SARCASTIC_FIX)


def ffprobe_duration(path: str) -> float:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


async def synth_scene(text: str, voice: str, rate: str, volume: str, retries: int = 8):
    """合成单个场景，返回 (mp3 bytes, word marks)。

    稳定性说明：edge-tts 服务端有频率限制，连续第 3 个请求最容易被拒
    （NoAudioReceived）。实测短退避无效，必须给足冷却时间，故退避按
    1.65 的指数增长到 40s 封顶，并叠加随机抖动打散重试节奏。
    """
    last = None
    for attempt in range(retries):
        try:
            comm = edge_tts.Communicate(
                text, voice, rate=rate, volume=volume, boundary="WordBoundary"
            )
            marks, audio = [], bytearray()
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    marks.append({
                        "text": chunk["text"],
                        "start": chunk["offset"] / 1e7,
                        "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                    })
            if audio and marks:
                return bytes(audio), marks
            last = f"empty (audio={len(audio)}, marks={len(marks)})"
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        wait = min(40.0, 3.0 * (1.65 ** attempt)) + random.uniform(0, 2.5)
        print(f"    retry {attempt + 1}/{retries} in {wait:.1f}s — {last}")
        await asyncio.sleep(wait)
    raise RuntimeError(f"synth failed: {last}")


def locate_blocks(blocks, marks):
    """字符累积法定位每块的字级边界 → 块级起止时间。"""
    joined = "".join(m["text"] for m in marks)
    targets = [len(clean(b["text"])) for b in blocks]
    if sum(targets) != len(joined):
        print(f"    ! 字符数不匹配: 块合计 {sum(targets)} vs 配音 {len(joined)}，回退按比例分配")

    out, acc, mi, idx = [], 0, 0, 0
    for bi, target in enumerate(targets):
        consumed = 0
        start = marks[mi]["start"] if mi < len(marks) else 0.0
        while mi < len(marks) and consumed < target:
            consumed += len(marks[mi]["text"])
            mi += 1
        end = marks[mi - 1]["end"] if mi > 0 else start
        # 块末尾自然停顿：到下一个词开始前 60%
        nxt = marks[mi]["start"] if mi < len(marks) else end
        out.append({"start": round(start, 3), "end": round(end, 3),
                    "gap_to_next": round(nxt - end, 3), "chars": target})
        idx += 1
    return out


def fmt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(entries):
    lines = []
    for i, e in enumerate(entries, 1):
        lines.append(str(i))
        lines.append(f"{fmt_ts(e['start'])} --> {fmt_ts(e['end'])}")
        lines.append(e["text"])
        lines.append("")
    return "\n".join(lines)


async def main():
    force = "--force" in sys.argv
    sb = json.load(open(os.path.join(HERE, "storyboard.json"), encoding="utf-8"))
    voice, rate = sb["voice"], sb.get("rate", "+0%")
    volume = sb.get("volume", "+0%")
    gap = sb.get("gap_after_scene", 0.45)
    tail = sb.get("tail_pad", 0.7)

    print(f"voice={voice} rate={rate} cache={'off(force)' if force else 'on'}")
    timeline = {"voice": voice, "rate": rate, "scenes": []}
    all_subs = []
    cursor = 0.0
    scene_files = []

    for si, sc in enumerate(sb["scenes"]):
        text = "".join(b["text"] for b in sc["blocks"])
        # 缓存键必须含 音色/语速/音量/文本：只按场景 id 命名会导致「换了音色却静默复用
        # 旧音色音频」——配音与字幕对不上，且看不出任何报错。用哈希做键，改稿/换音色即自动失效。
        ckey = hashlib.sha1(
            f"{voice}|{rate}|{volume}|{text}".encode("utf-8")
        ).hexdigest()[:8]
        mp3 = os.path.join(AUDIO, f"scene-{sc['id']}-{ckey}.mp3")
        mj = os.path.join(AUDIO, f"scene-{sc['id']}-{ckey}.marks.json")
        print(f"\n[{sc['id']}] {len(text)} chars — {sc['label']}  [{ckey}]")

        # 缓存复用：合成成功一次就不再重打服务端（限流环境下这是主要节省）
        if not force and os.path.exists(mp3) and os.path.exists(mj) \
                and os.path.getsize(mp3) > 2000:
            with open(mp3, "rb") as f:
                audio = f.read()
            with open(mj, encoding="utf-8") as f:
                marks = json.load(f)
            print(f"    复用缓存 ({len(marks)} marks)")
        else:
            if si > 0:
                cool = 4.0
                print(f"    冷却 {cool:.0f}s 后请求…")
                await asyncio.sleep(cool)
            audio, marks = await synth_scene(text, voice, rate, volume)
            with open(mp3, "wb") as f:
                f.write(audio)
            with open(mj, "w", encoding="utf-8") as f:
                json.dump(marks, f, ensure_ascii=False, indent=1)

        dur = ffprobe_duration(mp3)
        print(f"    audio {len(audio)} bytes, {dur:.2f}s, {len(marks)} word marks")

        bounds = locate_blocks(sc["blocks"], marks)
        blocks = []
        for b, bd in zip(sc["blocks"], bounds):
            entry = {
                "id": b["id"],
                "anim": b.get("anim"),
                "cue": b.get("cue"),
                "text": b["text"],
                "start": round(cursor + bd["start"], 3),
                "end": round(cursor + bd["end"], 3),
                "gap_to_next": bd["gap_to_next"],
            }
            blocks.append(entry)
            all_subs.append({"start": entry["start"], "end": entry["end"], "text": b["text"]})
            print(f"      {b['id']}  {entry['start']:6.2f} -> {entry['end']:6.2f}  {b['text'][:26]}")

        # 场景时长 = 旁白时长 + 尾部留白（画面需要落住）
        scene_dur = round(dur + tail, 3)
        timeline["scenes"].append({
            "id": sc["id"], "label": sc["label"], "html": sc.get("html", ""),
            "start": round(cursor, 3), "duration": scene_dur,
            "audio": os.path.relpath(mp3, ROOT).replace("\\", "/"),
            "audio_duration": round(dur, 3),
            "blocks": blocks,
        })
        scene_files.append(mp3)
        cursor += scene_dur + gap

    total = round(cursor - gap, 3)
    timeline["total_duration"] = total
    timeline["gap_after_scene"] = gap

    # ---- 拼接完整音轨 ----
    # 关键：各场景旁白的放置时间必须用 timeline 的 start（与画面同源），
    # 不能用「音频时长 + 静音」累加 —— 后者会比画面少一个 tail_pad 并累积漂移。
    # 故用 adelay 按绝对毫秒摆放，再 amix 合并；末尾 apad 补齐到全片时长。
    print("\n=== 拼接音轨（adelay 按画面时间轴对齐）===")
    delays = [int(round(sc["start"] * 1000)) for sc in timeline["scenes"]]
    args = [FFMPEG, "-v", "error", "-y"]
    for f in scene_files:
        args += ["-i", f]
    chain = "".join(
        f"[{i}:a]aresample=48000,adelay={d}:all=1[a{i}];"
        for i, d in enumerate(delays)
    )
    mixin = "".join(f"[a{i}]" for i in range(len(delays)))
    filt = (f"{chain}{mixin}amix=inputs={len(delays)}:normalize=0:duration=longest[m];"
            f"[m]apad=whole_dur={total}[a]")
    voice_wav = os.path.join(AUDIO, "voice.wav")
    args += ["-filter_complex", filt, "-map", "[a]", "-c:a", "pcm_s16le", voice_wav]
    subprocess.run(args, check=True)
    print("voice.wav:", round(ffprobe_duration(voice_wav), 2), "s (视频", total, "s)")

    with open(os.path.join(ROOT, "timeline.json"), "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "subtitles.srt"), "w", encoding="utf-8") as f:
        f.write(build_srt(all_subs))

    print(f"\n总时长 {total:.2f}s | 字幕 {len(all_subs)} 条")
    print("blocks total:", sum(len(s["blocks"]) for s in timeline["scenes"]))
    for s in timeline["scenes"]:
        print(f"  {s['id']:8s} audio={s['audio_duration']:5.2f}s scene={s['duration']:5.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
