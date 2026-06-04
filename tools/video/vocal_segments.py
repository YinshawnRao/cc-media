#!/usr/bin/env python3
"""人声段检测：找出音频里"实际有人在唱"的时间段，用于精确定位 verse/chorus 入口。

用法:
  tools/tts/venv/bin/python tools/video/vocal_segments.py <audio.wav> [audio2.wav ...]
    -> 在每个 wav 同目录写出 <name>.vocal.json
  或 -o vocal_analysis.json 把多个文件合并到一个 JSON。

输出格式:
  {
    "name": <file stem>,
    "duration": <total seconds>,
    "vocal_segments": [[t_start, t_end], ...]    # 连续有人声的段
  }

方法:
  1. HPSS 谐波分离去打击乐
  2. 取人声频带 (200-3000Hz) RMS
  3. 1s 平滑 + 60th percentile 阈值判活动
  4. 连续 >=2s active 视为有效段, <=1.5s gap 容忍同段

适用：AI 跨时空同台类项目（详见 CONVENTIONS.md "格式之二：AI 跨时空同台"）。
找到 verse 1 / verse 2 / final chorus 的入口时间码后,让 A 唱第一段 -> B 接第二段 -> C 接最后段。
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import librosa

SR = 22050


def detect(path: Path, min_dur: float = 2.0, gap_tol: float = 1.5,
           percentile: float = 60) -> dict:
    y, sr = librosa.load(str(path), sr=SR, mono=True)
    dur = len(y) / sr

    y_harm, _ = librosa.effects.hpss(y, margin=3.0)
    S = np.abs(librosa.stft(y_harm, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    voice_mask = (freqs >= 200) & (freqs <= 3000)
    voice_rms = np.sqrt(np.mean(S[voice_mask, :] ** 2, axis=0))
    times = librosa.frames_to_time(np.arange(len(voice_rms)), sr=sr, hop_length=512)

    win = int(1.0 / (times[1] - times[0]))
    smoothed = np.convolve(voice_rms, np.ones(win) / win, mode='same')
    thresh = np.percentile(smoothed, percentile)
    active = smoothed > thresh

    segments = []
    in_seg = False
    seg_start = 0.0
    last_active = None
    for i, a in enumerate(active):
        t = times[i]
        if a:
            if not in_seg:
                seg_start = t
                in_seg = True
            last_active = t
        else:
            if in_seg and last_active is not None and (t - last_active) > gap_tol:
                if last_active - seg_start >= min_dur:
                    segments.append([round(seg_start, 2), round(last_active, 2)])
                in_seg = False
    if in_seg and last_active and (last_active - seg_start) >= min_dur:
        segments.append([round(seg_start, 2), round(last_active, 2)])

    return {
        "name": path.stem,
        "duration": round(dur, 2),
        "vocal_segments": segments,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="audio file(s) — wav/mp3/m4a 均可，librosa 解码")
    ap.add_argument("-o", "--out", help="合并 JSON 输出路径；缺省时按文件分别输出 <name>.vocal.json")
    ap.add_argument("--min-dur", type=float, default=2.0, help="最短有效段时长 (s)")
    ap.add_argument("--gap-tol", type=float, default=1.5, help="同段内可容忍的最大静音 gap (s)")
    ap.add_argument("--percentile", type=float, default=60, help="人声活动阈值百分位")
    args = ap.parse_args()

    combined = {}
    for p in args.inputs:
        path = Path(p)
        if not path.exists():
            print(f"skip {p} (not found)", file=sys.stderr)
            continue
        print(f"分析 {path.name} ...", flush=True)
        result = detect(path, args.min_dur, args.gap_tol, args.percentile)
        print(f"  dur={result['duration']}s  vocal_segments={len(result['vocal_segments'])}")
        for s, e in result["vocal_segments"]:
            print(f"    {s:6.2f}-{e:6.2f}  ({e - s:.1f}s)")
        if args.out:
            combined[path.stem] = result
        else:
            outp = path.with_suffix(".vocal.json")
            outp.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"  -> {outp}")
    if args.out:
        Path(args.out).write_text(json.dumps(combined, ensure_ascii=False, indent=2))
        print(f"-> {args.out}")


if __name__ == "__main__":
    main()
