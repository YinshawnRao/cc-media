#!/usr/bin/env python3
"""Audio-only rebuild of master.wav with tuned per-song showcase gains.
Independent of the running video render (which uses a silent placeholder).
Mirrors full_build.py audio logic; only MGAIN differs."""
import json
import subprocess
from pathlib import Path
import song_config as cfg

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"; ASRC = ROOT / "audio_src"; SEG = ROOT / "build" / "segs"

# tuned to converge each showcase window to ~-15 dB (from volumedetect)
MGAIN = {"p5_yishu": 0.88, "p4_shileyuan": 1.07, "p3_youxianquan": 1.20,
         "p2_shui": 1.15, "p1_domino": 1.22}


def run(cmd): subprocess.run([str(c) for c in cmd], check=True)
def dur(p): return round(float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)])), 3)


meta = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
for s in cfg.SONGS:
    s["voice"] = meta[s["key"]]["dur"]
d_intro = dur(A / "intro.wav"); d_outro = dur(A / "outro.wav"); d_cta = dur(A / "outro_cta.wav")

intro_end = round(cfg.INTRO_VOICE_START + d_intro + cfg.INTRO_GAP, 3)
t = intro_end
for s in cfg.SONGS:
    s["start"] = round(t, 3)
    s["full_start"] = round(t + cfg.LEAD + s["voice"] + 0.25 + cfg.DIG, 3)
    s["end"] = round(s["full_start"] + s["show"], 3)
    s["seg_dur"] = round(s["end"] - s["start"], 3)
    s["full_local"] = round(s["full_start"] - s["start"], 3)
    t = s["end"]
outro_start = round(t, 3)
outro_dur = round(round(outro_start + cfg.LEAD + d_outro + cfg.DIGEST_O + d_cta + cfg.OUTRO_TAIL, 3) - outro_start, 3)
cta_local = round(cfg.LEAD + d_outro + cfg.DIGEST_O, 3)

INTRO_BED = ASRC / "p5_yishu.wav"; OUTRO_BED = ASRC / "p1_domino.wav"


def env_expr(narr_end_local, full_local):
    swell = round(narr_end_local + 0.25, 3)
    return (f"(lt(t,0.8))*({cfg.BED}*t/0.8)+(between(t,0.8,{swell}))*{cfg.BED}"
            f"+(between(t,{swell},{full_local}))*({cfg.BED}+{1.0-cfg.BED}*(t-{swell})/{cfg.DIG})"
            f"+(gte(t,{full_local}))*1.0")


run(["ffmpeg", "-v", "error", "-i", INTRO_BED, "-i", A / "intro.wav", "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cfg.INTRO_VOICE_START*1000)}|{int(cfg.INTRO_VOICE_START*1000)},volume={cfg.VOICE_GAIN}[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},asetpts=PTS-STARTPTS,volume=0.12,afade=t=in:st=0:d=1.0,afade=t=out:st={intro_end-1.0}:d=1.0[m];"
     f"[voice][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=limit=0.95:level=disabled[out]",
     "-map", "[out]", "-ac", "2", "-ar", "48000", SEG / "seg_intro.wav", "-y"])

for s in cfg.SONGS:
    seg = s["seg_dur"]; nel = round(cfg.LEAD + s["voice"], 3)
    env = env_expr(nel, s["full_local"]); g = MGAIN[s["key"]]
    run(["ffmpeg", "-v", "error", "-i", ASRC / f"{s['key']}.wav", "-i", A / f"{s['key']}.wav", "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cfg.LEAD*1000)}|{int(cfg.LEAD*1000)},volume={cfg.VOICE_GAIN}[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg},asetpts=PTS-STARTPTS,volume='{env}':eval=frame,volume={g},afade=t=out:st={seg-1.2}:d=1.2[m];"
         f"[voice][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95:level=disabled[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", SEG / f"seg_{s['key']}.wav", "-y"])

run(["ffmpeg", "-v", "error", "-i", OUTRO_BED, "-i", A / "outro.wav", "-i", A / "outro_cta.wav", "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cfg.LEAD*1000)}|{int(cfg.LEAD*1000)},volume={cfg.VOICE_GAIN}[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)},volume={cfg.VOICE_GAIN}[v2];"
     f"[v1][v2]amix=inputs=2:normalize=0:duration=longest[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},asetpts=PTS-STARTPTS,volume=0.18,afade=t=in:st=0:d=1.2,afade=t=out:st={outro_dur-1.6}:d=1.6[m];"
     f"[voice][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95:level=disabled[out]",
     "-map", "[out]", "-ac", "2", "-ar", "48000", SEG / "seg_outro.wav", "-y"])

names = ["seg_intro.wav"] + [f"seg_{s['key']}.wav" for s in cfg.SONGS] + ["seg_outro.wav"]
(SEG / "list.txt").write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", SEG / "list.txt", "-ac", "2", "-ar", "48000", ROOT / "master.wav", "-y"])
print("master rebuilt:", dur(ROOT / "master.wav"))
