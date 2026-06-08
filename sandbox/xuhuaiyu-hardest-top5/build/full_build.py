#!/usr/bin/env python3
"""完整片：徐怀钰最难的5首歌 / 倒数 5→1（#1《飞起来》压轴）。
竖屏 1080x1920，女声旁白 (zf_xiaoyi)。
结构：封面(首帧可作缩略图, 不剧透排名) + intro钩子 → 5首(介绍旁白+消化位+swell+连续展示段) → 片尾完整榜单回顾。
运行：python build/full_build.py -> master.wav + index.html；随后 npx hyperframes lint/render --sdr，再用 master.wav 后期 mux。
环境变量 XHY_SAMPLE=1 -> 只出 封面+intro+#5 样片。
"""
import contextlib
import os
import subprocess
import wave
from pathlib import Path

SAMPLE = bool(os.environ.get("XHY_SAMPLE"))


def dur(wav):
    with contextlib.closing(wave.open(str(wav), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, check=True)


A = "audio"
C = "clips"
LEAD = 0.3
DIG = 1.4
SHOW_REG = 27.0
SHOW_LAST = 32.0
BED_I = 0.06
BED_N = 0.20
MASTER_GAIN = 1.15

# 按最终 volumedetect 回调：#4/#2 源响度偏热，降低后让五首展示段更接近。
MGAIN = {"p4_yihan": 0.72, "p2_callme": 0.90}

d_intro = dur(f"{A}/intro.wav")
d_out = dur(f"{A}/outro.wav")
INTRO_END = round(LEAD + d_intro + 1.5, 3)

# 倒数 5→1（揭晓顺序）。(key, clip, no, name, meta, tags, tagline, show)
songs = [
    (
        "p5_miaomiao",
        "vert_miaomiao",
        "05",
        "《妙妙妙》",
        "元气舞曲 · 节奏压力",
        ["快节奏推进", "气口密", "明亮弹性"],
        "洗脑只是表面，<b>身体一直在高速运转</b>",
        SHOW_REG,
    ),
    (
        "p4_yihan",
        "vert_yihan",
        "04",
        "《心中的遗憾》",
        "成熟表达 · 中高区推进",
        ["成熟声线", "情绪厚度", "长句尾音"],
        "要有力量，<b>但绝不能粗</b>",
        SHOW_REG,
    ),
    (
        "p3_fenfei",
        "vert_fenfei",
        "03",
        "《分飞》",
        "抒情代表 · 稳定性考验",
        ["高位稳定", "长气息", "破碎但不散"],
        "不是炫技，<b>是细腻里撑得住</b>",
        SHOW_REG,
    ),
    (
        "p2_callme",
        "vert_callme",
        "02",
        "《Call Me》",
        "快歌高压 · 甜感不能塌",
        ["位置偏高", "歌词密", "甜感弹性"],
        "前面还可爱，<b>后面气也接不上</b>",
        SHOW_REG,
    ),
    (
        "p1_feilai",
        "vert_feilai",
        "01",
        "《飞起来》",
        "被低估的难歌 · 气口地狱",
        ["快亮密", "连续咬字", "轻盈不喘"],
        "最难不是飙高音，<b>是快、亮、密</b>",
        SHOW_LAST,
    ),
]
if SAMPLE:
    songs = songs[:1]

recap = [
    ("05", "《妙妙妙》"),
    ("04", "《心中的遗憾》"),
    ("03", "《分飞》"),
    ("02", "《Call Me》"),
    ("01", "《飞起来》"),
]

# ---------- 时间轴 ----------
blocks = []
t = INTRO_END
for key, clip, no, name, meta, tags, tagline, show in songs:
    dk = dur(f"{A}/{key}.wav")
    L = round(LEAD + dk + 0.2 + DIG + show, 3)
    ns = round(t + LEAD, 3)
    ne = round(ns + dk, 3)
    full = round(ne + 0.2 + DIG, 3)
    end = round(t + L, 3)
    blocks.append(
        dict(
            key=key,
            clip=clip,
            no=no,
            name=name,
            meta=meta,
            tags=tags,
            tagline=tagline,
            show=show,
            start=t,
            L=L,
            end=end,
            ns=ns,
            ne=ne,
            full=full,
        )
    )
    t = end
F_start = t
F_voice = round(F_start + LEAD, 3)
F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 3.6, 3)
TOTAL = round(F_end + 0.4, 3)


# ---------- 音频分段 ----------
def env_block(narr_end_local, full_local):
    sw = round(narr_end_local + 0.2, 3)
    return (
        f"(lt(t,0.8))*({BED_N}*t/0.8)"
        f"+(between(t,0.8,{sw}))*{BED_N}"
        f"+(between(t,{sw},{full_local}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
        f"+(gte(t,{full_local}))*1.0"
    )


segs = []
ve_intro = (
    f"(lt(t,3.5))*0"
    f"+(between(t,3.5,4.5))*({BED_I}*(t-3.5)/1.0)"
    f"+(gte(t,4.5))*{BED_I}"
)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_intro.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{INTRO_END},volume='{ve_intro}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        "seg_intro.wav",
        "-y",
    ]
)
segs.append("seg_intro.wav")

for b in blocks:
    dk = dur(f"{A}/{b['key']}.wav")
    narr_end_local = round(LEAD + dk, 3)
    full_local = round(b["full"] - b["start"], 3)
    ve = env_block(narr_end_local, full_local)
    mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['no']}.wav"
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            f"{C}/{b['clip']}.mp4",
            "-i",
            f"{A}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
            f"atrim=0:{b['L']},volume='{ve}':eval=frame,volume={mg}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['L']},alimiter=limit=0.95[out]",
            "-map",
            "[out]",
            "-ac",
            "2",
            "-ar",
            "48000",
            out,
            "-y",
        ]
    )
    segs.append(out)

segF_dur = round(F_end - F_start, 3)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_intro.mp4",
        "-i",
        f"{A}/outro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{segF_dur},volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-2.6}:d=2.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        "seg_outro.wav",
        "-y",
    ]
)
segs.append("seg_outro.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "seglist.txt",
        "-af",
        f"volume={MASTER_GAIN},alimiter=limit=0.97",
        "-ac",
        "2",
        "-ar",
        "48000",
        "master.wav",
        "-y",
    ]
)
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)


# ---------- HTML ----------
COVER_END = 4.5
CHIP_IN = 4.8
CHIP_OUT = round(max(CHIP_IN + 2.0, INTRO_END - 5.6), 2)
BRG_IN = round(max(CHIP_OUT + 0.2, INTRO_END - 5.0), 2)
BRG_OUT = round(INTRO_END - 0.4, 2)

footage = [("vert_intro", 0.0, INTRO_END)]
for b in blocks:
    footage.append((b["clip"], b["start"], b["L"]))
footage.append(("vert_intro", F_start, round(F_end - F_start, 3)))
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{round(s,3)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i % 2 == 0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i, (src, s, dv) in enumerate(footage)
)

labels = []
tweens = []
for b in blocks:
    no = b["no"]
    fid = f"lf{no}"
    mid = f"lm{no}"
    lf_start = round(b["start"] + 0.2, 3)
    lf_dur = round(b["full"] - lf_start, 3)
    lm_start = b["full"]
    lm_dur = round(b["end"] - b["full"] - (0.05 if b is blocks[-1] else 0), 3)
    climax = " climax" if no == "01" else ""
    crown = '<div class="crown">最容易被低估</div>' if no == "01" else '<div class="lab">最难 TOP 5</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{lf_start}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{crown}</div>'
        f'<div class="meta">{b["meta"]}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>'
    )
    labels.append(
        f'<div id="{mid}" class="clip labelMin{climax}" data-start="{lm_start}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>'
    )
    tweens.append(f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.7,ease:"power3.out"}},{round(lf_start+0.1,3)});')
    tweens.append(f'tl.from("#{fid} .rank>div:last-child",{{x:-24,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+0.36,3)});')
    tweens.append(f'tl.from("#{fid} .meta",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{round(lf_start+0.5,3)});')
    tweens.append(f'tl.from("#{fid} .song",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{round(lf_start+0.62,3)});')
    tweens.append(f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{round(lf_start+0.95,3)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+1.35,3)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["full"]-0.4,3)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{b["full"]});')
    tweens.append(f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{round(lm_start+0.1,3)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["end"]-0.35,3)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{round(b["end"],3)});')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#09090d;
  font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,8,13,.70) 0%,rgba(8,8,13,.18) 30%,rgba(8,8,13,.22) 56%,rgba(8,8,13,.88) 100%)}
#tint{position:absolute;inset:0;z-index:1;background:radial-gradient(95% 58% at 52% 26%,rgba(255,63,149,.16) 0%,rgba(0,0,0,0) 60%),radial-gradient(90% 62% at 25% 72%,rgba(70,230,182,.11) 0%,rgba(0,0,0,0) 58%);mix-blend-mode:screen}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 38%,rgba(0,0,0,0) 38%,rgba(0,0,0,.64) 100%)}
#grain{position:absolute;inset:0;z-index:8;opacity:.06;mix-blend-mode:soft-light;pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.86' numOctaves='2' stitchTiles='stitch' seed='19'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");background-size:260px 260px}

#cover{position:absolute;inset:0;z-index:6;color:#fff}
#cover .cv-photo{position:absolute;inset:0;background:url("hf/cover_assets/cover_bg.jpg") center/cover;transform-origin:52% 36%}
#cover .cv-scrim{position:absolute;inset:0;background:linear-gradient(180deg,rgba(9,9,13,.08) 0%,rgba(9,9,13,.14) 36%,rgba(9,9,13,.62) 67%,rgba(9,9,13,.96) 100%)}
#cover .cv-vig{position:absolute;inset:0;background:radial-gradient(118% 76% at 52% 34%,rgba(0,0,0,0) 42%,rgba(0,0,0,.58) 100%)}
#cover .cv-wrap{position:absolute;left:82px;right:82px;bottom:186px}
#cover .cv-kick{display:inline-flex;align-items:center;gap:13px;padding:11px 26px;border:2px solid rgba(248,229,138,.58);border-radius:999px;font-size:26px;font-weight:850;color:#f8e58a;letter-spacing:.16em;background:rgba(9,9,13,.34)}
#cover .cv-kick::before{content:"";width:12px;height:12px;border-radius:50%;background:#46e6b6;box-shadow:0 0 16px #46e6b6}
#cover .cv-name{margin-top:28px;font-size:72px;font-weight:900;color:#fff;letter-spacing:.1em;text-shadow:0 4px 26px rgba(0,0,0,.68)}
#cover .cv-title{margin-top:-2px;font-size:186px;font-weight:950;line-height:.92;letter-spacing:-2px;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#fff7d0 4%,#f8e58a 34%,#ff3f95 78%,#46e6b6 100%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 10px 42px rgba(255,63,149,.42))}
#cover .cv-en{margin-top:14px;font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:43px;color:#f0d6df;letter-spacing:.04em}
#cover .cv-sub{margin-top:22px;font-size:37px;font-weight:750;color:#f3eef2;text-shadow:0 3px 16px rgba(0,0,0,.72)}
#cover .cv-sub b{color:#46e6b6}

.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:850;color:#f8e58a;letter-spacing:.32em}
.k::before{content:"";width:50px;height:4px;background:linear-gradient(90deg,#ff3f95,#f8e58a,#46e6b6);border-radius:2px;box-shadow:0 0 16px rgba(255,63,149,.62)}
#chips{position:absolute;top:300px;left:84px;right:84px;z-index:5;color:#fff}
.imp-list{list-style:none;margin:44px 0 0}
.imp-list li{font-size:78px;font-weight:950;line-height:1.32;color:rgba(255,255,255,.96);padding-left:40px;position:relative;text-shadow:0 6px 28px rgba(0,0,0,.45)}
.imp-list li .strike{position:relative;display:inline-block}
.imp-list li .xln{position:absolute;left:-8px;right:-8px;top:52%;height:8px;background:linear-gradient(90deg,#ff3f95,#46e6b6);border-radius:4px;box-shadow:0 0 16px rgba(70,230,182,.65);transform:scaleX(0);transform-origin:left}
.imp-list li::before{content:"";position:absolute;left:0;top:.33em;width:8px;height:.72em;background:linear-gradient(180deg,#ff3f95,#f8e58a,#46e6b6);border-radius:3px}
.imp-note{margin-top:34px;font-size:34px;font-weight:650;color:#c8c0ca;letter-spacing:.05em}
.imp-note b{color:#f8e58a;font-weight:800}

#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#fff;text-align:center}
#bridge .big{font-size:236px;font-weight:950;line-height:.9;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#fff7d0,#f8e58a 50%,#ff3f95);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 46px rgba(255,63,149,.45))}
#bridge .big small{font-size:56px;font-weight:850;color:#f8e58a;letter-spacing:.2em;display:block;margin-bottom:8px;font-family:"Noto Sans SC",sans-serif;-webkit-text-fill-color:#f8e58a}
#bridge .line{margin-top:28px;font-size:48px;font-weight:950;color:#fff;letter-spacing:.02em}
#bridge .line b{color:#46e6b6}

.labelFull{position:absolute;left:84px;right:84px;bottom:292px;z-index:5;color:#fff}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:33px;font-weight:850;color:#f8e58a;letter-spacing:.24em;padding-bottom:32px}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#0b0b10;background:linear-gradient(100deg,#f8e58a,#ff7bb8 62%,#46e6b6);border-radius:9px;padding:9px 22px;margin-bottom:36px;letter-spacing:.08em;box-shadow:0 0 34px rgba(255,63,149,.55)}
.labelFull .no{font-size:200px;font-weight:850;line-height:.78;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#fff7d0,#f8e58a 52%,#ff3f95);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 38px rgba(255,63,149,.4))}
.labelFull.climax .no{background:linear-gradient(180deg,#fff7d0,#f8e58a 38%,#ff3f95 72%,#46e6b6);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 48px rgba(70,230,182,.45))}
.labelFull .meta{margin-top:14px;font-size:29px;font-weight:750;color:#c9bec9;letter-spacing:.12em;font-family:"JetBrains Mono",monospace}
.labelFull .song{font-size:88px;font-weight:950;margin-top:4px;color:#fff;font-family:"Noto Serif SC",serif;text-shadow:0 8px 38px rgba(0,0,0,.55)}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:750;color:#bdf9ea;border:1.5px solid rgba(70,230,182,.52);border-radius:999px;padding:9px 22px;background:rgba(70,230,182,.08)}
.labelFull.climax .tags span{color:#fff0b7;border-color:rgba(248,229,138,.58);background:rgba(248,229,138,.08)}
.labelFull .tag{font-size:43px;font-weight:760;color:#f1edf1;margin-top:26px;line-height:1.3}
.labelFull .tag b{color:#f8e58a;font-weight:850}
.labelFull.climax .tag b{color:#46e6b6}

.labelMin{position:absolute;top:118px;left:74px;z-index:5;color:#fff;display:flex;align-items:center;gap:18px;text-shadow:0 4px 18px rgba(0,0,0,.65)}
.labelMin .no{font-size:62px;font-weight:850;color:#f8e58a;font-family:"JetBrains Mono",monospace}
.labelMin.climax .no{color:#46e6b6}
.labelMin .song{font-size:50px;font-weight:850;font-family:"Noto Serif SC",serif}

#outro{position:absolute;left:72px;right:72px;top:246px;z-index:5;color:#fff;
  padding:46px 48px;border-radius:28px;border:1px solid rgba(248,229,138,.18);
  background:linear-gradient(180deg,rgba(12,12,18,.56) 0%,rgba(10,10,15,.86) 28%,rgba(10,10,15,.90) 100%);
  box-shadow:0 24px 80px rgba(0,0,0,.52)}
#outro .o2{font-size:70px;font-weight:950;line-height:1.08;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#fff7d0,#f8e58a 42%,#ff3f95 72%,#46e6b6);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .recap-t{margin-top:38px;font-size:30px;font-weight:850;color:#c8c0ca;letter-spacing:.24em}
#outro .recap{list-style:none;margin:22px 0 0}
#outro .recap li{display:flex;align-items:baseline;gap:24px;padding:12px 0;border-bottom:1px solid rgba(248,229,138,.16)}
#outro .recap li .rn{font-size:46px;font-weight:850;font-family:"JetBrains Mono",monospace;color:#f8e58a;min-width:76px}
#outro .recap li .rs{font-size:48px;font-weight:850;font-family:"Noto Serif SC",serif;color:#f5eff3}
#outro .recap li.top{border-bottom:none}
#outro .recap li.top .rn{color:#46e6b6}
#outro .recap li.top .rs{background:linear-gradient(100deg,#fff7d0,#ff3f95 58%,#46e6b6);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:30px;font-size:40px;font-weight:750;color:#f5eff3;line-height:1.34}
#outro .q b{color:#f8e58a}
#outro .bar{width:140px;height:8px;background:linear-gradient(90deg,#ff3f95,#f8e58a,#46e6b6);margin-top:22px;border-radius:4px}
"""

recap_rows = "".join(
    f'<li class="{"top" if no == "01" else ""}"><span class="rn">{no}</span><span class="rs">{nm}</span></li>'
    for no, nm in recap
)

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="tint" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="grain" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9"></div>
<div id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="5">
<div class="cv-photo"></div><div class="cv-scrim"></div><div class="cv-vig"></div>
<div class="cv-wrap"><div class="cv-kick">华语唱功盘点 · 元气背后</div>
<div class="cv-name">徐怀钰</div>
<div class="cv-title">最难的5首</div>
<div class="cv-en">Yuki Hsu — The Hardest Five</div>
<div class="cv-sub">别被青春感骗了 · <b>这些歌一点都不好唱</b></div></div></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci">青春元气</li><li class="ci">甜美可爱</li><li class="ci"><span class="strike">洗脑神曲<i class="xln"></i></span></li></ul>
<div class="imp-note">但真正难的，是<b>轻松感背后的控制</b></div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="4">
<div class="big"><small>倒数揭晓</small>TOP 5</div>
<div class="line">从第五名开始，<b>越往后越硬</b></div></div>
{chr(10).join(labels)}
<div id="outro" class="clip" data-start="{round(F_voice+0.15,3)}" data-duration="{round(F_end-F_voice-0.15,3)}" data-track-index="4">
<div class="o2">徐怀钰的难，<br>不是只有高音</div>
<div class="recap-t">完整榜单回顾</div>
<ul class="recap">{recap_rows}</ul>
<div class="q">你心里她最难的一首，<b>是哪一首？</b></div>
<div class="bar"></div></div>
<audio id="master" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

js = f'''
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .cv-wrap",{{opacity:1}},0);
tl.to("#cover .cv-photo",{{scale:1.035,duration:4.4,ease:"sine.inOut"}},0);
tl.to("#cover",{{opacity:0,duration:.45,ease:"power1.in"}},{round(COVER_END-0.45,2)});
tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{CHIP_IN+0.1});
tl.from("#chips .ci",{{x:-40,opacity:0,duration:.5,ease:"power3.out",stagger:.13}},{CHIP_IN+0.35});
tl.fromTo("#chips .xln",{{scaleX:0}},{{scaleX:1,duration:.42,ease:"power2.inOut"}},{CHIP_IN+1.25});
tl.from("#chips .imp-note",{{opacity:0,y:16,duration:.5}},{CHIP_IN+1.45});
tl.to("#chips",{{opacity:0,duration:.35,ease:"power1.in"}},{round(CHIP_OUT-0.35,2)});
tl.from("#bridge .big",{{y:70,opacity:0,scale:1.08,duration:.75,ease:"power4.out"}},{BRG_IN+0.15});
tl.from("#bridge .line",{{y:28,opacity:0,duration:.55,ease:"power2.out"}},{BRG_IN+0.75});
tl.to("#bridge",{{opacity:0,duration:.42,ease:"power1.in"}},{round(BRG_OUT-0.42,2)});
{chr(10).join(tweens)}
tl.from("#outro",{{y:30,opacity:0,duration:.55,ease:"power2.out"}},{round(F_voice+0.2,3)});
tl.from("#outro .o2",{{y:36,opacity:0,duration:.65,ease:"power3.out"}},{round(F_voice+0.45,3)});
tl.from("#outro .recap-t",{{opacity:0,duration:.4}},{round(F_voice+1.2,3)});
tl.from("#outro .recap li",{{x:-26,opacity:0,duration:.42,ease:"power2.out",stagger:.11}},{round(F_voice+1.45,3)});
tl.from("#outro .q",{{y:20,opacity:0,duration:.45,ease:"power2.out"}},{round(F_voice+2.35,3)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{round(F_voice+2.75,3)});
'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>'''

Path("index.html").write_text(html, encoding="utf-8")
Path("meta.json").write_text('{"id":"main","name":"xuhuaiyu-hardest-top5"}', encoding="utf-8")
print("TOTAL:", TOTAL, "s  blocks:", [(b["key"], b["start"], b["end"], b["full"]) for b in blocks], "F:", F_start, F_end)
