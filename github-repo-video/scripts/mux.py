# -*- coding: utf-8 -*-
"""
混音器：把 HyperFrames 渲染的无声画面 + 旁白音轨合成最终成片。

为什么画面里已经烧了字幕、还要单独混音：
  HyperFrames 的 render 只逐帧输出画面，音频在它那层不可靠；
  而字幕用 HTML 渲染（可复用主题配色、逐帧 seek 精确）比 ffmpeg 的
  subtitles 滤镜更可控，所以分工是 —— 画面(含字幕) tf 渲染，声音 ffmpeg 合。

用法
----
  python mux.py                       # 用 video/out/render.mp4 + audio/voice.wav
  python mux.py --video xxx.mp4 --audio xxx.wav -o out/final.mp4
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"


def probe(path, *entries):
    out = subprocess.run(
        [FFPROBE, "-v", "error", *entries, "-of", "default=noprint_wrappers=1", path],
        capture_output=True, text=True, check=True,
    )
    return dict(
        line.split("=", 1) for line in out.stdout.strip().splitlines() if "=" in line
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=os.path.join(ROOT, "video", "out", "render.mp4"))
    ap.add_argument("--audio", default=os.path.join(ROOT, "audio", "voice.wav"))
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "out", "final.mp4"))
    ap.add_argument("--bgm", default=None, help="可选背景音乐（会做 sidechain 压低）")
    ap.add_argument("--bgm-gain", type=float, default=0.16, help="BGM 音量 0-1")
    ap.add_argument("--crf", default="18")
    ap.add_argument("--preset", default="medium")
    args = ap.parse_args()

    # 兜底：在候选渲染产物里取**修改时间最新**的一个（video/out/render.mp4 与
    # renders/raw.mp4）。此前固定用前者的默认值，会让混音静默拿到上一次会话的
    # 旧渲染产物 —— 视频内容全对不上文案。
    cands = [args.video,
             os.path.join(ROOT, "renders", "raw.mp4"),
             os.path.join(ROOT, "video", "out", "render.mp4")]
    cands = [c for c in cands if os.path.exists(c)]
    if cands:
        newest = max(cands, key=os.path.getmtime)
        if newest != args.video:
            print(f"[!] 改用更新的渲染产物 {newest}（{args.video} 更旧）")
            args.video = newest

    for p, label in ((args.video, "video"), (args.audio, "audio")):
        if not os.path.exists(p):
            sys.exit(f"[x] 缺少{label}: {p}")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    vinfo = probe(args.video, "-show_entries", "stream=width,height,r_frame_rate,nb_frames")
    ainf = probe(args.audio, "-show_entries", "format=duration")
    print(f"video: {vinfo.get('width')}x{vinfo.get('height')} "
          f"{vinfo.get('r_frame_rate')} frames={vinfo.get('nb_frames')}")
    print(f"audio: {ainf.get('duration')}s")

    tl_path = os.path.join(ROOT, "timeline.json")
    total = None
    if os.path.exists(tl_path):
        total = json.load(open(tl_path, encoding="utf-8"))["total_duration"]
        print(f"timeline total_duration: {total}s")

    cmd = [FFMPEG, "-v", "error", "-y", "-i", args.video, "-i", args.audio]

    # 旁白响度标准化：edge-tts 原始输出 mean 约 -24 dB，手机上偏轻；
    # 短视频平台习惯 -14 ~ -16 LUFS，这里压到 -16 LUFS / TP -1.5 dB。
    LN = "loudnorm=I=-16:TP=-1.5:LRA=11"

    if args.bgm:
        # 旁白为钥匙，BGM 被 sidechain 压低 → 说话时音乐自动让路
        cmd += ["-i", args.bgm]
        fc = (
            f"[1:a]{LN},asplit=2[nar][key];"
            f"[2:a]volume={args.bgm_gain},aloop=loop=-1:size=2e9[bg];"
            f"[bg][key]sidechaincompress=threshold=0.03:ratio=8:attack=8:release=280[bgd];"
            f"[nar][bgd]amix=inputs=2:normalize=0:duration=first[a]"
        )
    else:
        fc = f"[1:a]{LN}[a]"

    cmd += [
        "-filter_complex", fc,
        "-map", "0:v:0", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        args.out,
    ]
    print("muxing…")
    subprocess.run(cmd, check=True)

    oinfo = probe(args.out, "-show_entries",
                  "format=duration,size,bit_rate",
                  "-show_entries", "stream=codec_name,width,height,r_frame_rate")
    dur = float(oinfo.get("duration", 0))
    size = int(oinfo.get("size", 0))
    print(f"\n[done] {args.out}")
    print(f"  {oinfo.get('width')}x{oinfo.get('height')} @ {oinfo.get('r_frame_rate')} "
          f"{oinfo.get('codec_name')}  {dur:.2f}s  {size/1024/1024:.2f}MB")
    if total:
        print(f"  时长校验: 输出 {dur:.2f}s vs 时间轴 {total}s "
              f"(差 {abs(dur-total):.2f}s)")


if __name__ == "__main__":
    main()
