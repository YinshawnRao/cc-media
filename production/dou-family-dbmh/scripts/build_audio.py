#!/usr/bin/env python3
"""构建 master.wav（298s，与 index.html 时间线对齐）。
- 各段音乐床（原片音频，loudnorm 统一）
- TTS 旁白按时间戳插入，旁白期间音乐 ducking 到 -18~-22dB
- 三人同屏段原声接力 3-5s 交替
- 输出 audio/master.wav；最后 mux 进 renders/full_draft.mp4
"""
import json, os, subprocess, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
NARR = json.loads((PROJ / 'narration.json').read_text())
os.chdir(PROJ)

SR = 48000
TOTAL = 289.5  # V4: 封面压到 5.5s，整体 -8.5s

# V4 section starts (与 build.py SECTIONS 保持一致)
S = {
    'cover':   0.0,
    'open3':   5.5,
    'title':  15.5,
    'ch1':    29.5,
    'trans1': 76.5,
    'ch2':    89.5,
    'trans2':143.5,
    'ch3':   156.5,
    'three': 203.5,
    'outro': 246.5,
    'cta':   276.5,
}

def run(argv, check=True):
    """argv: list[str] — no shell, no injection risk."""
    print(">>", " ".join(argv[:8]), "..." if len(argv) > 8 else "")
    r = subprocess.run(argv, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("STDOUT:", r.stdout[-800:]); print("STDERR:", r.stderr[-1500:])
        sys.exit(1)
    return r

# ====================== 1. 从 clips 抽干净音轨 ======================
# 用输出端 seek 避免 webm/opus 截断（其实 vfill 已 AAC，但保险）
clips = {
    'dw_main':  ('clips/clip_dw_main.mp4',  50),
    'fw_main':  ('clips/clip_fw_main.mp4',  60),
    'jt_main':  ('clips/clip_jt_main.mp4',  50),
    'dw_open':  ('clips/clip_dw_open.mp4',  4),
    'fw_open':  ('clips/clip_fw_open.mp4',  4),
    'jt_open':  ('clips/clip_jt_open.mp4',  4),
    'dw_three': ('clips/clip_dw_three.mp4', 43),
    'fw_three': ('clips/clip_fw_three.mp4', 43),
    'jt_three': ('clips/clip_jt_three.mp4', 43),
}
Path('audio').mkdir(exist_ok=True)
for key, (src, dur) in clips.items():
    out = f'audio/src_{key}.wav'
    run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vn',
         '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s16le', '-t', str(dur),
         '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11', out])

# ====================== 2. TTS 改为 48kHz stereo 对齐 ======================
for key in NARR:
    src = f'voice/{key}.wav'
    out = f'audio/tts_{key}.wav'
    run(['ffmpeg', '-y', '-v', 'error', '-i', src,
         '-ac', '2', '-ar', str(SR),
         '-af', 'loudnorm=I=-13:TP=-1.5:LRA=8', out])

# ====================== 3. 构建 298s silent canvas ======================
run(['ffmpeg', '-y', '-v', 'error',
     '-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate={SR}',
     '-t', str(TOTAL), '-c:a', 'pcm_s16le', 'audio/silent.wav'])

# V4: 完全去掉 base_pad — 用户明确要求无背景白噪音
# 静音由 chapter bed 的长尾 fade-out 自然衔接，间隙就让它静下来

# ====================== 4. 各段音乐床（V4 时间线）======================
# (start_abs, dur, src_audio_wav, music_gain_dB, fade_in, fade_out)
beds = [
    # cold open 三连切（5.5/8.2/10.9）— jt 延长 5s 覆盖 freeze-trio (13.6-15.5)
    (S['open3'] + 0.0, 3.0,  'audio/src_dw_open.wav', -10, 0.25, 0.7),  # 5.5
    (S['open3'] + 2.7, 3.0,  'audio/src_fw_open.wav', -10, 0.35, 0.7),  # 8.2
    (S['open3'] + 5.4, 4.0,  'audio/src_jt_open.wav', -10, 0.45, 0.8),  # 10.9-14.9（jt_open 源仅 4s）
    # 桥：cold open 末 → title 卡末（14.5-30，覆盖 freeze-trio→title 全程，低音乐床）
    (14.5, 15.5, 'audio/src_dw_main.wav', -14, 1.5, 1.5),  # 14.5-30
    # 章 1 → 长尾溢出至 trans1
    (S['ch1'],  49.5, 'audio/src_dw_main.wav', -7, 0.9, 2.5),  # 29.5-79
    # trans1: TTS 结束后 (~81.8) 用 fw_main lead-in 桥到 ch2
    (S['trans1'] + 4.5, 8.5, 'audio/src_fw_main.wav', -14, 1.0, 1.5),  # 81-89.5
    # 章 2 → 长尾溢出至 trans2
    (S['ch2'],  56.5, 'audio/src_fw_main.wav', -7, 0.9, 2.5),  # 89.5-146
    # trans2: TTS 结束后 (~148.7) 用 jt_main lead-in 桥到 ch3
    (S['trans2'] + 4.5, 8.5, 'audio/src_jt_main.wav', -14, 1.0, 1.5),  # 148-156.5
    # 章 3 → 长尾溢出至 three
    (S['ch3'],  49.5, 'audio/src_jt_main.wav', -7, 0.9, 2.5),  # 156.5-206
    # outro 246.5-276.5（30s）：3 段 crossfade overlap
    (S['outro'] + 0.0,  12.0, 'audio/src_dw_main.wav', -9,  1.0, 2.0),  # 246.5-258.5
    (S['outro'] + 10.0, 12.0, 'audio/src_fw_main.wav', -9,  1.5, 2.0),  # 256.5-268.5
    (S['outro'] + 19.0, 11.0, 'audio/src_jt_main.wav', -9,  1.5, 2.5),  # 265.5-276.5
    # CTA 276.5-289.5：极低 jingtong 床
    (S['cta'],          13.0, 'audio/src_jt_main.wav', -16, 1.5, 2.5),  # 276.5-289.5
]

# ====================== 5. TTS 时间戳（V4 同步 build.py 的 TTS_AT）======================
TTS_AT = {
    's01_open':     S['cover']  + 1.0,    # 1.0
    's02_three':    S['open3']  + 0.5,    # 6.0
    's03_title':    S['title']  + 1.0,    # 16.5
    's04_douwei':   S['ch1']    + 1.8,    # 31.3
    's05_trans1':   S['trans1'] + 1.2,    # 77.7
    's06_faye':     S['ch2']    + 1.8,    # 91.3
    's07_trans2':   S['trans2'] + 1.2,    # 144.7
    's08_jingtong': S['ch3']    + 1.8,    # 158.3
    's09_three_p':  S['three']  + 1.0,    # 204.5
    's10_outro':    S['outro']  + 1.5,    # 248.0
    's11_cta':      S['cta']    + 0.8,    # 277.3
}

# ====================== 6. 三人接力（V4: three 段 203.5-246.5）======================
relay_segs = []
order = ['dw_three', 'fw_three', 'jt_three']
slot = 5.0
relay_start = S['three']        # 203.5
relay_end = S['outro']          # 246.5 = 43s
tts09_end = TTS_AT['s09_three_p'] + NARR['s09_three_p']['dur']  # 204.5 + 15.18 ≈ 219.7
n = 0
t = relay_start
while t < relay_end:
    actual = min(slot, relay_end - t)
    src = f'audio/src_{order[n % 3]}.wav'
    src_off = (t - relay_start) % 43
    gain = -8 if t < tts09_end else -4
    relay_segs.append((t, actual, src, src_off, gain, 0.35, 0.45))
    n += 1
    t += slot

# ====================== 7. 构建 filter_complex ======================
# 我们用 amix 合并所有音轨，每条音轨独立 atrim + adelay + volume(envelope)
# 单大 graph：
#  inputs:
#    [0] silent canvas
#    [1..N] beds
#    [N+1..] TTS
#    [..] relay
#  filters:
#    each src: atrim + asetpts + volume + adelay + apad
#  amix all

inputs = ['audio/silent.wav']
parts = []
# V4: 删除 base_pad；间隙就让它静音

# bed parts
for i, (start, dur, src, gain_db, fin, fout) in enumerate(beds):
    inputs.append(src)
    idx = len(inputs) - 1
    delay_ms = int(start * 1000)
    gain_lin = 10 ** (gain_db / 20)
    parts.append(
        f'[{idx}:a]atrim=0:{dur},asetpts=PTS-STARTPTS,'
        f'afade=t=in:st=0:d={fin},afade=t=out:st={max(dur-fout,0):.3f}:d={fout},'
        f'volume={gain_lin:.4f},adelay={delay_ms}|{delay_ms},apad=pad_dur={TOTAL}[bed{i}]'
    )

# TTS parts
tts_labels = []
for key, t_abs in TTS_AT.items():
    inputs.append(f'audio/tts_{key}.wav')
    idx = len(inputs) - 1
    delay_ms = int(t_abs * 1000)
    parts.append(
        f'[{idx}:a]volume=1.0,adelay={delay_ms}|{delay_ms},apad=pad_dur={TOTAL}[tts{key}]'
    )
    tts_labels.append(f'tts{key}')

# Relay parts
relay_labels = []
for i, (start, dur, src, src_off, gain_db, fin, fout) in enumerate(relay_segs):
    inputs.append(src)
    idx = len(inputs) - 1
    delay_ms = int(start * 1000)
    gain_lin = 10 ** (gain_db / 20)
    parts.append(
        f'[{idx}:a]atrim={src_off}:{src_off+dur},asetpts=PTS-STARTPTS,'
        f'afade=t=in:st=0:d={fin},afade=t=out:st={max(dur-fout,0):.3f}:d={fout},'
        f'volume={gain_lin:.4f},adelay={delay_ms}|{delay_ms},apad=pad_dur={TOTAL}[rly{i}]'
    )
    relay_labels.append(f'rly{i}')

# DUCKING via volume envelope：在每条 bed 上叠一个时间分段表达式
# 简化：sidechain 太复杂，改用静态 volume 包络
# 在 TTS 起点前 0.15s 落到 -16dB，TTS 终点后 0.3s 抬回原值
# 实现：对每条 bed[i] 后接一个 volume=eval=frame 包络
def duck_envelope(label_in, label_out, bed_start, bed_end, duck_dB=-12):
    """对 [label_in] 在 TTS 时间窗内压 duck_dB；写成 volume='if(...,duck,1)':eval=frame"""
    duck_lin = 10 ** (duck_dB / 20)
    conds = []
    for key, t_abs in TTS_AT.items():
        d = NARR[key]['dur']
        # 时间窗：TTS 起前 0.1s 落，终后 0.3s 回
        a = t_abs - 0.1
        b = t_abs + d + 0.3
        # 与 bed 时间窗交集才有效
        if b < bed_start or a > bed_end:
            continue
        conds.append(f'between(t,{a:.3f},{b:.3f})')
    if not conds:
        # 没有 TTS 时间窗与此 bed 重叠 → passthrough
        return f'[{label_in}]anull[{label_out}]'
    expr = '+'.join(conds)
    # if (any cond) → duck else 1
    return (f"[{label_in}]volume=eval=frame:volume='if(gt({expr},0),{duck_lin:.4f},1)'"
            f"[{label_out}]")

ducked_beds = []
for i, (start, dur, *_rest) in enumerate(beds):
    new_label = f'bedD{i}'
    parts.append(duck_envelope(f'bed{i}', new_label, start, start + dur))
    ducked_beds.append(new_label)

# Relay 也要在 s09_three_p TTS 期间 duck
ducked_relays = []
for i, (start, dur, *_rest) in enumerate(relay_segs):
    new_label = f'rlyD{i}'
    parts.append(duck_envelope(f'rly{i}', new_label, start, start + dur))
    ducked_relays.append(new_label)

# 合并所有：silent canvas + ducked beds + ducked relays + TTS（无 base_pad）
amix_inputs = ['[0:a]'] + [f'[{lbl}]' for lbl in ducked_beds + ducked_relays + tts_labels]
n_inputs = len(amix_inputs)
parts.append(
    f'{"".join(amix_inputs)}amix=inputs={n_inputs}:normalize=0:duration=longest[mix]'
)
# 整体响度归一 + 限幅
parts.append(f'[mix]loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.95[out]')

filter_complex = ';'.join(parts)
argv = ['ffmpeg', '-y', '-v', 'error']
for p in inputs:
    argv += ['-i', p]
argv += ['-filter_complex', filter_complex,
        '-map', '[out]', '-t', str(TOTAL),
        '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le',
        'audio/master.wav']
print(f"\n[building master.wav, {len(inputs)} inputs, {len(parts)} filter chunks]")
run(argv)

# Quick stats
r = run(['ffprobe', '-v', 'error',
         '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1',
         'audio/master.wav'], check=False)
print(f"\n✅ master.wav duration: {r.stdout.strip()}s (target {TOTAL}s)")
