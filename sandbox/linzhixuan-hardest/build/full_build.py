#!/usr/bin/env python3
"""完整片：林志炫最难的5首歌 / 倒数 5→1（#1《没离开过》压轴）。
暗夜祖母绿 + 香槟金配色，竖屏 1080x1920，女声旁白 (zf_xiaoyi)。
用户给定排名：1 没离开过 / 2 如果不是因为你 / 3 散了吧 / 4 离人 / 5 认错。揭晓倒数 05→01。
用户要求：① 片头不暴露歌曲排名(仅封面+作品描述)，留悬念；② 片尾总结再列完整榜单；③ 副歌展示给足(解说盘点≥~25s)。
封面=《没离开过》我是歌手 金光正脸特写(zoom-crop 静帧, 与压轴呼应)；intro/outro 底=《离人》ONEtake letterbox 动态。
master.wav 逐段(床→swell→展示 + 旁白 ducking + 逐首 loudnorm)，整体抬。之后 lint → render --sdr → mux。
环境变量 LZX_SAMPLE=1 → 只出 封面+intro+#5 样片。"""
import os, subprocess, wave, contextlib
from pathlib import Path

SAMPLE = bool(os.environ.get("LZX_SAMPLE"))

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
LEAD = 0.3; DIG = 1.4; SHOW_REG = 26.0; SHOW_LAST = 32.0
BED_I = 0.06; BED_N = 0.20
MGAIN = {"p4_liren": 1.58, "p1_mlkg": 1.30, "p2_rgbsywn": 0.89, "p3_sanleba": 1.06}  # 跨歌副歌响度统一(loudnorm 后离人偏轻/如果偏响)，压轴最响
MASTER_GAIN = 1.4

d_intro = dur(f"{A}/intro.wav"); d_out = dur(f"{A}/outro.wav")
INTRO_END = round(LEAD + d_intro + 1.5, 3)

# 倒数 5→1（揭晓顺序）。(key, clip, no, name, meta, tags, tagline, show)
songs = [
    ("p5_rencuo", "vert_rencuo", "05", "《认错》", "1991 · 优客李林",
     ["早期成名曲", "虚实转换", "薄而不弱"],
     "唱重了土，唱虚了飘，<b>难在干净</b>", SHOW_REG),
    ("p4_liren", "vert_liren", "04", "《离人》", "经典 · 高位弱混",
     ["透明音色", "弱声控制", "真假声无缝"],
     "不是难在吼，<b>难在高位上的轻</b>", SHOW_REG),
    ("p3_sanleba", "vert_sanleba", "03", "《散了吧》", "著名 · 折磨型高音",
     ["公认高音折磨曲", "高位反复咬字", "气与闭合不松"],
     "不是飙一下，<b>是一路顶到底</b>", SHOW_REG),
    ("p2_rgbsywn", "vert_rgbsywn", "02", "《如果不是因为你》", "强混 · 极限音准",
     ["连续中高音", "强混支撑", "音准稳如唱片"],
     "唱准一句不难，<b>难在一个字都不塌</b>", SHOW_REG),
    ("p1_mlkg", "vert_mlkg", "01", "《没离开过》", "公认天花板 · 全程混声",
     ["整首压混声区", "大线条大动态", "共鸣不停切换"],
     "不是难一句，<b>是难一整首</b>", SHOW_LAST),
]
if SAMPLE:
    songs = songs[:1]

# 完整榜单（片尾回顾，倒数顺序 5→1）
recap = [("05", "《认错》"), ("04", "《离人》"), ("03", "《散了吧》"),
         ("02", "《如果不是因为你》"), ("01", "《没离开过》")]

# ---------- 时间轴 ----------
blocks = []
t = INTRO_END
for key, clip, no, name, meta, tags, tagline, show in songs:
    dk = dur(f"{A}/{key}.wav")
    L = round(LEAD + dk + 0.2 + DIG + show, 3)
    ns = round(t + LEAD, 3); ne = round(ns + dk, 3)
    full = round(ne + 0.2 + DIG, 3); end = round(t + L, 3)
    blocks.append(dict(key=key, clip=clip, start=t, L=L, end=end, ns=ns, ne=ne, full=full,
                       no=no, name=name, meta=meta, tags=tags, tagline=tagline, show=show))
    t = end
F_start = t; F_voice = round(F_start + LEAD, 3); F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 3.4, 3); TOTAL = round(F_end + 0.4, 3)

# ---------- 音频分段 ----------
def envB(ne_loc, full_loc):
    sw = round(ne_loc, 3)
    return (f"(lt(t,0.8))*({BED_N}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED_N}"
            f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_loc}))*1.0")

segs = []
veI = (f"(lt(t,3.5))*0+(between(t,3.5,4.5))*({BED_I}*(t-3.5)/1.0)+(gte(t,4.5))*{BED_I}")
run(["ffmpeg","-v","error","-i",f"{C}/vert_intro.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{INTRO_END},volume='{veI}':eval=frame[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_intro.wav","-y"])
segs.append("seg_intro.wav")

for b in blocks:
    seg_dur = b["L"]; dk = dur(f"{A}/{b['key']}.wav")
    ne_loc = round(LEAD + dk, 3); full_loc = round(b["full"] - b["start"], 3)
    ve = envB(ne_loc, full_loc); mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['no']}.wav"
    run(["ffmpeg","-v","error","-i",f"{C}/{b['clip']}.mp4","-i",f"{A}/{b['key']}.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

segF_dur = round(F_end - F_start, 3)
run(["ffmpeg","-v","error","-i",f"{C}/vert_intro.mp4","-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{segF_dur},volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-2.6}:d=2.6[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_outro.wav","-y"])
segs.append("seg_outro.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt",
     "-af",f"volume={MASTER_GAIN},alimiter=limit=0.97","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- 时间点 ----------
COVER_END = 4.5
CHIP_IN, CHIP_OUT = 4.7, round(INTRO_END-5.4,2)
BRG_IN, BRG_OUT = round(INTRO_END-5.0,2), round(INTRO_END-0.4,2)

# footage（交替轨道 0/6）：intro底 → 5首 → 片尾复用 intro底
fc = [("vert_intro", 0.0, INTRO_END)]
for b in blocks:
    fc.append((b["clip"], b["start"], b["L"]))
fc.append(("vert_intro", F_start, round(F_end-F_start,3)))
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{round(s,3)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i%2==0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i,(src,s,dv) in enumerate(fc))

# 标签
labels, tweens = [], []
for b in blocks:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = round(b["start"]+0.2,3); lf_dur = round(b["full"]-lf_start,3)
    lm_start = b["full"]; lm_dur = round(b["end"]-b["full"]-(0.05 if b is blocks[-1] else 0),3)
    climax = ' climax' if no=="01" else ''
    crown = '<div class="crown">公认天花板</div>' if no=="01" else '<div class="lab">最难 TOP 5</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{lf_start}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{crown}</div>'
        f'<div class="meta">{b["meta"]}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>')
    labels.append(
        f'<div id="{mid}" class="clip labelMin{climax}" data-start="{lm_start}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>')
    tweens.append(f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.7,ease:"power3.out"}},{round(lf_start+0.1,3)});')
    tweens.append(f'tl.from("#{fid} .rank>div:last-child",{{x:-24,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+0.38,3)});')
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
html,body{width:1080px;height:1920px;overflow:hidden;background:#06140f;
  font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(4,12,9,.78) 0%,rgba(5,16,12,.18) 30%,rgba(5,16,12,.28) 58%,rgba(3,10,8,.9) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 38%,rgba(0,0,0,0) 38%,rgba(0,0,0,.62) 100%)}
#tint{position:absolute;inset:0;z-index:1;background:radial-gradient(92% 60% at 50% 30%,rgba(47,176,137,.12) 0%,rgba(0,0,0,0) 60%);mix-blend-mode:screen}
#grain{position:absolute;inset:0;z-index:8;opacity:.055;mix-blend-mode:soft-light;pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='280'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch' seed='11'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");background-size:280px 280px}

/* ---- 封面（首帧缩略图：金光正脸 zoom-crop 静帧；不做 fade-in；不剧透排名） ---- */
#cover{position:absolute;inset:0;z-index:6;color:#f2ebdd}
#cover .cv-photo{position:absolute;inset:0;background:url("hf/cover_assets/cover_bg.jpg") center/cover;transform-origin:52% 40%}
#cover .cv-scrim{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,16,12,.10) 0%,rgba(6,16,12,0) 34%,rgba(5,13,10,.42) 60%,rgba(4,11,8,.9) 84%,rgba(3,9,7,.97) 100%)}
#cover .cv-vig{position:absolute;inset:0;background:radial-gradient(120% 78% at 52% 36%,rgba(0,0,0,0) 44%,rgba(0,0,0,.5) 100%)}
#cover .cv-wrap{position:absolute;left:84px;right:84px;bottom:188px}
#cover .cv-kick{display:inline-flex;align-items:center;gap:13px;padding:11px 26px;border:2px solid rgba(232,200,126,.55);border-radius:999px;font-size:26px;font-weight:800;color:#e8c87e;letter-spacing:.18em;background:rgba(6,16,12,.32)}
#cover .cv-kick::before{content:"";width:12px;height:12px;border-radius:50%;background:#2fb089;box-shadow:0 0 16px #2fb089}
#cover .cv-name{margin-top:26px;font-size:70px;font-weight:900;color:#f0e9dc;letter-spacing:.1em;font-family:"Noto Sans SC",sans-serif;text-shadow:0 4px 24px rgba(0,0,0,.6)}
#cover .cv-title{margin-top:-4px;font-size:188px;font-weight:900;line-height:.92;letter-spacing:-3px;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#fbf0cf 4%,#e8c87e 46%,#bf9442 98%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 10px 40px rgba(190,150,70,.45))}
#cover .cv-en{margin-top:14px;font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:44px;color:#cdb98c;letter-spacing:.04em}
#cover .cv-sub{margin-top:22px;font-size:37px;font-weight:700;color:#e7ddcc;text-shadow:0 3px 16px rgba(0,0,0,.7)}
#cover .cv-sub b{color:#7fe0bd}

/* ---- intro: 大众印象 钩子 ---- */
.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:800;color:#e8c87e;letter-spacing:.34em}
.k::before{content:"";width:50px;height:4px;background:linear-gradient(90deg,#e8c87e,#2fb089);border-radius:2px;box-shadow:0 0 16px rgba(232,200,126,.6)}
#chips{position:absolute;top:300px;left:84px;right:84px;z-index:5;color:#f2ebdd}
.imp-list{list-style:none;margin:44px 0 0}
.imp-list li{font-size:82px;font-weight:900;line-height:1.3;color:rgba(242,235,221,.96);padding-left:40px;position:relative}
.imp-list li .strike{position:relative;display:inline-block}
.imp-list li .xln{position:absolute;left:-8px;right:-8px;top:52%;height:8px;background:linear-gradient(90deg,#e8c87e,#2fb089);border-radius:4px;box-shadow:0 0 16px rgba(47,176,137,.7);transform:scaleX(0);transform-origin:left}
.imp-list li::before{content:"";position:absolute;left:0;top:.30em;width:8px;height:.72em;background:linear-gradient(180deg,#e8c87e,#2fb089);border-radius:3px;box-shadow:0 0 12px rgba(232,200,126,.55)}
.imp-note{margin-top:34px;font-size:34px;font-weight:600;color:#8fa39a;letter-spacing:.05em}
.imp-note b{color:#f0d79a;font-weight:700}

/* ---- intro: TOP5 bridge ---- */
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#f2ebdd;text-align:center}
#bridge .big{font-size:236px;font-weight:900;line-height:.9;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#fbf0cf,#d8ad55);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 46px rgba(216,173,85,.45))}
#bridge .big small{font-size:56px;font-weight:800;color:#e8c87e;letter-spacing:.2em;display:block;margin-bottom:8px;font-family:"Noto Sans SC",sans-serif;-webkit-text-fill-color:#e8c87e}
#bridge .line{margin-top:28px;font-size:48px;font-weight:900;color:#f2ebdd;letter-spacing:.02em}
#bridge .line b{color:#7fe0bd}

/* ---- 排名大卡 ---- */
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#f2ebdd}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:33px;font-weight:800;color:#e8c87e;letter-spacing:.26em;padding-bottom:32px;font-family:"Noto Sans SC",sans-serif}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#08160f;background:linear-gradient(180deg,#f6dd9f,#d8ad55);border-radius:9px;padding:9px 22px;margin-bottom:36px;letter-spacing:.1em;box-shadow:0 0 34px rgba(216,173,85,.55)}
.labelFull .no{font-size:200px;font-weight:800;line-height:.78;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#fbf0cf,#d8ad55);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 38px rgba(216,173,85,.4))}
.labelFull.climax .no{background:linear-gradient(180deg,#fff2cc,#e8c87e 55%,#3ad6a8);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 46px rgba(232,200,126,.55))}
.labelFull .meta{margin-top:14px;font-size:29px;font-weight:700;color:#9fb3a8;letter-spacing:.14em;font-family:"JetBrains Mono",monospace}
.labelFull .song{font-size:88px;font-weight:900;margin-top:4px;color:#fff;font-family:"Noto Serif SC",serif}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:700;color:#9fe6cb;border:1.5px solid rgba(47,176,137,.5);border-radius:999px;padding:9px 22px;background:rgba(47,176,137,.07)}
.labelFull.climax .tags span{color:#f0d79a;border-color:rgba(232,200,126,.55);background:rgba(232,200,126,.07)}
.labelFull .tag{font-size:43px;font-weight:700;color:#e7ddcc;margin-top:26px;line-height:1.3}
.labelFull .tag b{color:#e8c87e;font-weight:800}
.labelFull.climax .tag b{color:#7fe0bd}

/* ---- 展示期角标 ---- */
.labelMin{position:absolute;top:118px;left:74px;z-index:5;color:#f2ebdd;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:62px;font-weight:800;color:#e8c87e;font-family:"JetBrains Mono",monospace}
.labelMin.climax .no{color:#7fe0bd}
.labelMin .song{font-size:50px;font-weight:800;font-family:"Noto Serif SC",serif}

/* ---- 片尾 + 完整榜单回顾 ---- */
#outro{position:absolute;left:72px;right:72px;top:270px;z-index:5;color:#f2ebdd;
  padding:46px 48px;border-radius:28px;border:1px solid rgba(232,200,126,.16);
  background:linear-gradient(180deg,rgba(5,14,10,.5) 0%,rgba(4,11,8,.8) 26%,rgba(4,11,8,.84) 100%);
  box-shadow:0 24px 80px rgba(0,0,0,.5)}
#outro .o2{font-size:72px;font-weight:900;line-height:1.08;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#fbf0cf,#e8c87e 52%,#bf9442);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .recap-t{margin-top:40px;font-size:30px;font-weight:800;color:#8fa39a;letter-spacing:.26em}
#outro .recap{list-style:none;margin:22px 0 0}
#outro .recap li{display:flex;align-items:baseline;gap:24px;padding:12px 0;border-bottom:1px solid rgba(232,200,126,.14)}
#outro .recap li .rn{font-size:46px;font-weight:800;font-family:"JetBrains Mono",monospace;color:#d8ad55;min-width:76px}
#outro .recap li .rs{font-size:50px;font-weight:800;font-family:"Noto Serif SC",serif;color:#ede4d3}
#outro .recap li.top{border-bottom:none}
#outro .recap li.top .rn{color:#7fe0bd}
#outro .recap li.top .rs{background:linear-gradient(100deg,#fff2cc,#e8c87e 60%,#3ad6a8);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:32px;font-size:42px;font-weight:700;color:#f0e9dc}
#outro .q b{color:#e8c87e}
#outro .bar{width:140px;height:8px;background:linear-gradient(90deg,#e8c87e,#2fb089);margin-top:22px;border-radius:4px}
"""

recap_rows = "".join(
    f'<li class="{"top" if no=="01" else ""}"><span class="rn">{no}</span><span class="rs">{nm}</span></li>'
    for no,nm in recap)

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="tint" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="grain" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9"></div>
<div id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="5">
<div class="cv-photo"></div><div class="cv-scrim"></div><div class="cv-vig"></div>
<div class="cv-wrap">
<div class="cv-kick">华语唱功盘点 · 透明音背后</div>
<div class="cv-name">林志炫</div>
<div class="cv-title">最难的5首</div>
<div class="cv-en">Terry Lin — The Hardest Five</div>
<div class="cv-sub">都说他唱高音毫不费力 · <b>其实没一首好惹</b></div></div></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci"><span class="strike">干净<i class="xln"></i></span></li><li class="ci"><span class="strike">透明好听<i class="xln"></i></span></li><li class="ci"><span class="strike">高音不费力<i class="xln"></i></span></li></ul>
<div class="imp-note">听着 <b>轻松又通透</b> · 其实每一首都难到劝退</div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="5">
<div class="big"><small>公认最难唱</small>TOP 5</div>
<div class="line">音准 · 气息 · 混声 · <b>强弱控制</b></div></div>
{chr(10).join(labels)}
<div id="outro" class="clip" data-start="{round(F_voice,3)}" data-duration="{round(F_end-F_voice+0.4,3)}" data-track-index="4">
<div class="o2">最难的技术，<br>他唱成了云淡风轻</div>
<div class="recap-t">公认最难 · 完整榜单</div>
<ul class="recap">{recap_rows}</ul>
<div class="q">你心里最难的一首，<b>是哪一首？</b></div>
<div class="bar"></div></div>
<audio id="master" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

# 片尾榜单逐行揭晓（与旁白「第五…第一」同步）
recap_in = round(F_voice + 6.6, 3)
recap_tweens = "".join(
    f'tl.from("#outro .recap li:nth-child({i+1})",{{x:-26,opacity:0,duration:.5,ease:"power2.out"}},{round(recap_in + i*1.18,3)});'
    for i in range(len(recap)))

js = f'''
tl.set("#cover",{{opacity:1}},0);
tl.set([".cv-photo",".cv-scrim",".cv-vig",".cv-kick",".cv-name",".cv-title",".cv-en",".cv-sub"],{{opacity:1}},0);
tl.fromTo("#cover .cv-photo",{{scale:1.0}},{{scale:1.07,duration:{COVER_END},ease:"sine.inOut"}},0);
tl.to("#cover",{{y:-30,opacity:0,duration:.5,ease:"power2.in"}},{round(COVER_END-0.5,2)});
tl.set("#cover",{{opacity:0}},{COVER_END});
tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{CHIP_IN+0.1});
tl.from("#chips .ci",{{x:-46,opacity:0,duration:.55,ease:"power3.out",stagger:.42}},{CHIP_IN+0.3});
tl.to("#chips .ci:nth-child(1) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+2.2});
tl.to("#chips .ci:nth-child(2) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+2.7});
tl.to("#chips .ci:nth-child(3) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+3.2});
tl.from("#chips .imp-note",{{opacity:0,y:14,duration:.5}},{CHIP_IN+3.9});
tl.to("#chips",{{opacity:0,duration:.4,ease:"power1.in"}},{round(CHIP_OUT-0.45,2)});
tl.set("#chips",{{opacity:0}},{CHIP_OUT});
tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{BRG_IN+0.1});
tl.from("#bridge .big",{{scale:.7,opacity:0,duration:.6,ease:"back.out(1.4)"}},{BRG_IN+0.2});
tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{BRG_IN+0.8});
tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{round(BRG_OUT-0.45,2)});
tl.set("#bridge",{{opacity:0}},{BRG_OUT});
{chr(10).join(tweens)}
tl.from("#outro .o2",{{y:50,opacity:0,scale:1.04,duration:.8,ease:"power4.out"}},{round(F_voice+0.4,3)});
tl.from("#outro .recap-t",{{y:18,opacity:0,duration:.5}},{round(F_voice+5.6,3)});
{recap_tweens}
tl.from("#outro .q",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{round(recap_in + len(recap)*1.18 + 0.4,3)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{round(recap_in + len(recap)*1.18 + 0.85,3)});
'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@700;800&family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet">
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
Path("meta.json").write_text('{"id":"main","name":"linzhixuan-hardest"}', encoding="utf-8")
print(("SAMPLE " if SAMPLE else "FULL ")+"TOTAL:", TOTAL, "s | INTRO_END:", INTRO_END)
for b in blocks: print(f"  {b['no']} {b['name']:14s} start={b['start']:.2f} ns={b['ns']:.2f} full={b['full']:.2f} end={b['end']:.2f} show={b['show']}  Lclip>={b['L']:.1f}s")
print(f"  outro start={F_start:.2f} end={F_end:.2f}")
