#!/usr/bin/env python3
"""完整片：谭咏麟最被低估的5首歌 / 倒数 5→1（#1《还是你懂得爱我》压轴）。
暮色暖调（深茄紫夜 + 暮光铜玫瑰 + 古铜金，呼应黄昏/暗色画意象），竖屏 1080x1920，女声旁白 (zf_xiaoyi)。
结构：封面(首帧可作缩略图，不剧透排名) + intro钩子(校长金曲太多→最好的藏在专辑深处→遗珠5桥) → 5首(介绍旁白+消化位+加长副歌展示) → 片尾(完整榜单回顾 + 提问)。
用户要求：① 片头不暴露排名(仅封面+作品描述)，留悬念；② 片尾再列完整榜单；③ 副歌展示给足；④ 全程女声。
音频解耦：见 MUSIC 字典（synced=画面源自带音轨；decoupled=干净棚版录音）。
master.wav 逐段(床→swell→展示 + 旁白 ducking + 逐首 loudnorm)，整体抬。之后 lint → render --sdr → mux。
环境变量 TYL_SAMPLE=1 → 只出 封面+intro+#5 样片。"""
import os, subprocess, wave, contextlib
from pathlib import Path

SAMPLE = bool(os.environ.get("TYL_SAMPLE"))

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
LEAD = 0.3; DIG = 1.4; SHOW_REG = 27.0; SHOW_LAST = 33.0
BED_I = 0.13; BED_N = 0.20
MASTER_GAIN = 1.08
# 逐首响度微调（loudnorm 后仍有差，QA volumedetect 后回填）
MGAIN = {}
# 每首 music 段来源 (source_wav, start_sec)。全部 decoupled = 棚版录音副歌（画面单剪 Live）。
# start_sec 由 RMS 副歌定位推算：mstart = chorus_start - full_loc(≈LEAD+narr+0.2+DIG)；QA volumedetect 后微调。
MUSIC = {
    "p5_hhdsy":  ("raw/aud_p5.wav",  86.0),   # 1987 棚版【无损】首段大副歌(源105-141)
    "p4_cknzhc": ("raw/aud_p4.wav", 178.0),   # 1985 棚版无损 结尾大副歌(源200-227)
    "p3_ybxn":   ("raw/aud_p3.wav", 189.0),   # 1986 棚版 末段最饱满副歌(源210-237)
    "p2_qsdxx":  ("raw/aud_p2.wav", 169.0),   # 1987 棚版 Universal 强副歌(源192-219)
    "p1_hsndd":  ("raw/aud_p1.wav", 178.0),   # 棚版 Album Ver 压轴终段副歌(源199-232)
}
# intro/outro 音乐床：用 #1《还是你懂得爱我》(emotional anchor)
BED_INTRO = ("raw/aud_p1.wav", 24.0)
BED_OUTRO = ("raw/aud_p1.wav", 95.0)

d_intro = dur(f"{A}/intro.wav"); d_out = dur(f"{A}/outro.wav")
INTRO_END = round(LEAD + d_intro + 1.5, 3)

# 倒数 5→1（揭晓顺序）。(key, clip, no, name, meta, tags, tagline, show)
songs = [
    ("p5_hhdsy", "vert_p5_hhdsy", "05", "《黄昏的声音》", "再见吧!?浪漫 · 1987",
     ["被强曲掩盖", "黄昏氛围", "老港乐余味"],
     "像黄昏里的<b>一段自言自语</b>", SHOW_REG),
    ("p4_cknzhc", "vert_p4_cknzhc", "04", "《此刻你在何处》", "爱情陷阱 · 1985",
     ["巅峰专辑遗珠", "完整电影情歌", "被同名主打盖住"],
     "大热的光芒里，<b>被遗忘的一颗遗珠</b>", SHOW_REG),
    ("p3_ybxn", "vert_p3_ybxn", "03", "《永不想你》", "第一滴泪 · 1986",
     ["林敏骢词曲", "成熟情歌", "懂了却放不下"],
     "成年人的失恋，<b>是懂了还放不下</b>", SHOW_REG),
    ("p2_qsdxx", "vert_p2_qsdxx", "02", "《墙上的肖像》", "墙上的肖像 · 1987",
     ["老歌迷私藏", "阴郁都市感", "点题之作"],
     "藏在专辑深处的<b>一幅暗色画</b>", SHOW_REG),
    ("p1_hsndd", "vert_p1_hsndd", "01", "《还是你懂得爱我》", "笑看人生 · 1991",
     ["慢歌首选佳作", "越听越有厚度", "乐评点名"],
     "最深的情，<b>从来不是喊出来的</b>", SHOW_LAST),
]
if SAMPLE:
    songs = songs[:1]

# 完整榜单（片尾回顾，倒数顺序 5→1）
recap = [("05", "《黄昏的声音》"), ("04", "《此刻你在何处》"), ("03", "《永不想你》"),
         ("02", "《墙上的肖像》"), ("01", "《还是你懂得爱我》")]

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

# ---------- 分段渲染（HF >240s 关 streaming + ≥7 video setup 超时 → 切两段各 <240s/≤4 video）----------
# master.wav 始终建全片（每段共用同一条 master，最后整片 mux）。PART 只改 HTML 发哪些元素 + 时间偏移。
PART = os.environ.get("TYL_PART", "")    # "" 全片 | "A" 封面+intro+#5/#4/#3 | "B" #2/#1+outro
SPI = 3                                   # blocks[:3]=A（#5/#4/#3），blocks[3:]=B（#2/#1）；切点=#3→#2
if PART == "A":
    OFF = 0.0; INC_INTRO = True; INC_OUTRO = False; BLK = blocks[:SPI]
    PART_DUR = blocks[SPI-1]["end"]; OUTFILE = "partA.html"
elif PART == "B":
    OFF = blocks[SPI]["start"]; INC_INTRO = False; INC_OUTRO = True; BLK = blocks[SPI:]
    PART_DUR = round(TOTAL - OFF, 3); OUTFILE = "partB.html"
else:
    OFF = 0.0; INC_INTRO = True; INC_OUTRO = True; BLK = blocks
    PART_DUR = TOTAL; OUTFILE = "index.html"
def E(x): return round(x - OFF, 3)        # emit-time：整体左移 OFF（part 内归零）

# ---------- 音频分段 ----------
def envB(ne_loc, full_loc):
    sw = round(ne_loc, 3)
    return (f"(lt(t,0.8))*({BED_N}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED_N}"
            f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_loc}))*1.0")

segs = []
veI = (f"(lt(t,3.5))*0+(between(t,3.5,4.5))*({BED_I}*(t-3.5)/1.0)+(gte(t,4.5))*{BED_I}")
run(["ffmpeg","-v","error","-ss",str(BED_INTRO[1]),"-i",BED_INTRO[0],"-i",f"{A}/intro.wav","-filter_complex",
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
    msrc, mstart = MUSIC[b["key"]]
    out = f"seg_{b['no']}.wav"
    run(["ffmpeg","-v","error","-ss",str(mstart),"-i",msrc,"-i",f"{A}/{b['key']}.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

segF_dur = round(F_end - F_start, 3)
run(["ffmpeg","-v","error","-ss",str(BED_OUTRO[1]),"-i",BED_OUTRO[0],"-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{segF_dur},volume=0.20,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-2.6}:d=2.6[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_outro.wav","-y"])
segs.append("seg_outro.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt",
     "-af",f"volume={MASTER_GAIN},alimiter=limit=0.97","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- 时间点 ----------
COVER_END = 4.2
CHIP_IN, CHIP_OUT = 4.4, round(INTRO_END-5.6,2)
BRG_IN, BRG_OUT = round(INTRO_END-5.2,2), round(INTRO_END-0.4,2)

# footage（交替轨道 0/6）：cover/intro底 → 本段歌 → 片尾复用 intro底。仅发本段需要的 video（≤4 个，避免 setup 超时）
fc = []
if INC_INTRO: fc.append(("vert_intro", 0.0, INTRO_END))
for b in BLK:
    fc.append((b["clip"], b["start"], b["L"]))
if INC_OUTRO: fc.append(("vert_intro", F_start, round(F_end-F_start,3)))
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{E(s)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i%2==0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i,(src,s,dv) in enumerate(fc))

# 标签
labels, tweens = [], []
for b in BLK:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = round(b["start"]+0.2,3); lf_dur = round(b["full"]-lf_start,3)
    lm_start = b["full"]; lm_dur = round(b["end"]-b["full"]-(0.05 if b is blocks[-1] else 0),3)
    climax = ' climax' if no=="01" else ''
    crown = '<div class="crown">遗珠之首</div>' if no=="01" else '<div class="lab">被低估 · 遗珠</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{E(lf_start)}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{crown}</div>'
        f'<div class="meta">{b["meta"]}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>')
    labels.append(
        f'<div id="{mid}" class="clip labelMin{climax}" data-start="{E(lm_start)}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>')
    tweens.append(f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.7,ease:"power3.out"}},{E(lf_start+0.1)});')
    tweens.append(f'tl.from("#{fid} .rank>div:last-child",{{x:-24,opacity:0,duration:.5,ease:"power2.out"}},{E(lf_start+0.38)});')
    tweens.append(f'tl.from("#{fid} .meta",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{E(lf_start+0.5)});')
    tweens.append(f'tl.from("#{fid} .song",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{E(lf_start+0.62)});')
    tweens.append(f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{E(lf_start+0.95)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{E(lf_start+1.35)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{E(b["full"]-0.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{E(b["full"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{E(lm_start+0.1)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.4,ease:"power1.in"}},{E(b["end"]-0.35)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{E(b["end"])});')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#120e18;
  font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(12,9,18,.82) 0%,rgba(14,10,20,.18) 32%,rgba(12,9,18,.32) 58%,rgba(8,6,12,.94) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(118% 80% at 50% 36%,rgba(0,0,0,0) 38%,rgba(0,0,0,.66) 100%)}
#dusk{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 56% at 50% 104%,rgba(224,147,108,.20) 0%,rgba(0,0,0,0) 60%);mix-blend-mode:screen}
#grain{position:absolute;inset:0;z-index:9;opacity:.05;mix-blend-mode:soft-light;pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='280'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch' seed='11'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");background-size:280px 280px}

/* ---- 封面（首帧缩略图，不做 fade-in；不剧透排名） ---- */
#cover{position:absolute;left:84px;right:84px;bottom:286px;z-index:6;color:#f0e8df}
#cover .cv-kick{display:inline-flex;align-items:center;gap:13px;padding:11px 26px;border:2px solid rgba(216,168,106,.55);border-radius:999px;font-size:26px;font-weight:800;color:#d8a86a;letter-spacing:.18em}
#cover .cv-kick::before{content:"";width:12px;height:12px;border-radius:50%;background:#e0936c;box-shadow:0 0 16px #e0936c}
#cover .cv-name{margin-top:28px;font-size:64px;font-weight:900;color:#f0e8df;letter-spacing:.12em;font-family:"Noto Sans SC",sans-serif}
#cover .cv-title{margin-top:-2px;font-size:156px;font-weight:900;line-height:.92;letter-spacing:-3px;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#f7e6cf 4%,#e6a878 48%,#c47a52 98%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 10px 40px rgba(196,122,82,.42))}
#cover .cv-en{margin-top:14px;font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:44px;color:#cdb08c;letter-spacing:.04em}
#cover .cv-sub{margin-top:22px;font-size:36px;font-weight:700;color:#dccdbb}
#cover .cv-sub b{color:#e8a486}

/* ---- intro: 大众印象 钩子 ---- */
.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:800;color:#d8a86a;letter-spacing:.32em}
.k::before{content:"";width:50px;height:4px;background:linear-gradient(90deg,#d8a86a,#e0936c);border-radius:2px;box-shadow:0 0 16px rgba(216,168,106,.6)}
#chips{position:absolute;top:300px;left:84px;right:84px;z-index:5;color:#f0e8df}
.imp-list{list-style:none;margin:44px 0 0}
.imp-list li{font-size:78px;font-weight:900;line-height:1.3;color:rgba(240,232,223,.96);padding-left:40px;position:relative}
.imp-list li .strike{position:relative;display:inline-block}
.imp-list li .xln{position:absolute;left:-8px;right:-8px;top:52%;height:8px;background:linear-gradient(90deg,#d8a86a,#e0936c);border-radius:4px;box-shadow:0 0 16px rgba(224,147,108,.7);transform:scaleX(0);transform-origin:left}
.imp-list li::before{content:"";position:absolute;left:0;top:.30em;width:8px;height:.72em;background:linear-gradient(180deg,#d8a86a,#e0936c);border-radius:3px;box-shadow:0 0 12px rgba(216,168,106,.55)}
.imp-note{margin-top:34px;font-size:34px;font-weight:600;color:#9b8fa0;letter-spacing:.05em}
.imp-note b{color:#ecc79a;font-weight:700}

/* ---- intro: 被低估 bridge ---- */
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#f0e8df;text-align:center}
#bridge .big{font-size:232px;font-weight:900;line-height:.9;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#f7e6cf,#d8a86a);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 46px rgba(216,168,106,.45))}
#bridge .big small{font-size:56px;font-weight:800;color:#d8a86a;letter-spacing:.22em;display:block;margin-bottom:8px;font-family:"Noto Sans SC",sans-serif;-webkit-text-fill-color:#d8a86a}
#bridge .line{margin-top:28px;font-size:46px;font-weight:900;color:#f0e8df;letter-spacing:.02em}
#bridge .line b{color:#e8a486}

/* ---- 排名大卡 ---- */
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#f0e8df}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:31px;font-weight:800;color:#d8a86a;letter-spacing:.24em;padding-bottom:32px;font-family:"Noto Sans SC",sans-serif}
.labelFull .rank .crown{font-size:33px;font-weight:900;color:#1a0e08;background:linear-gradient(180deg,#f6dd9f,#d8a86a);border-radius:9px;padding:9px 22px;margin-bottom:36px;letter-spacing:.08em;box-shadow:0 0 34px rgba(216,168,106,.55)}
.labelFull .no{font-size:198px;font-weight:800;line-height:.78;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#f7e6cf,#d8a86a);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 38px rgba(216,168,106,.4))}
.labelFull.climax .no{background:linear-gradient(180deg,#fff0d8,#f0b48c 55%,#e0795a);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 46px rgba(240,160,120,.55))}
.labelFull .meta{margin-top:14px;font-size:29px;font-weight:700;color:#a89b92;letter-spacing:.14em;font-family:"JetBrains Mono",monospace}
.labelFull .song{font-size:84px;font-weight:900;margin-top:6px;color:#fff;font-family:"Noto Serif SC",serif;line-height:1.05}
.labelFull.climax .song{font-size:74px}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:29px;font-weight:700;color:#ecd4a8;border:1.5px solid rgba(216,168,106,.5);border-radius:999px;padding:9px 22px;background:rgba(216,168,106,.07)}
.labelFull.climax .tags span{color:#f3c7b0;border-color:rgba(240,160,120,.55);background:rgba(240,160,120,.08)}
.labelFull .tag{font-size:43px;font-weight:700;color:#e9dccb;margin-top:26px;line-height:1.32}
.labelFull .tag b{color:#d8a86a;font-weight:800}
.labelFull.climax .tag b{color:#e8a486}

/* ---- 展示期角标 ---- */
.labelMin{position:absolute;top:118px;left:74px;z-index:5;color:#f0e8df;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:60px;font-weight:800;color:#d8a86a;font-family:"JetBrains Mono",monospace}
.labelMin.climax .no{color:#e8a486}
.labelMin .song{font-size:46px;font-weight:800;font-family:"Noto Serif SC",serif}

/* ---- 片尾 + 完整榜单回顾 ---- */
#outro{position:absolute;left:72px;right:72px;top:268px;z-index:5;color:#f0e8df;
  padding:46px 48px;border-radius:28px;border:1px solid rgba(216,168,106,.16);
  background:linear-gradient(180deg,rgba(14,10,20,.5) 0%,rgba(10,7,15,.82) 26%,rgba(10,7,15,.86) 100%);
  box-shadow:0 24px 80px rgba(0,0,0,.5)}
#outro .o2{font-size:68px;font-weight:900;line-height:1.1;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#f7e6cf,#e6a878 52%,#c47a52);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .recap-t{margin-top:40px;font-size:29px;font-weight:800;color:#a89b92;letter-spacing:.26em}
#outro .recap{list-style:none;margin:22px 0 0}
#outro .recap li{display:flex;align-items:baseline;gap:22px;padding:12px 0;border-bottom:1px solid rgba(216,168,106,.14)}
#outro .recap li .rn{font-size:46px;font-weight:800;font-family:"JetBrains Mono",monospace;color:#d8a86a;min-width:74px}
#outro .recap li .rs{font-size:46px;font-weight:800;font-family:"Noto Serif SC",serif;color:#ede1d3}
#outro .recap li.top{border-bottom:none}
#outro .recap li.top .rn{color:#e8a486}
#outro .recap li.top .rs{background:linear-gradient(100deg,#fff0d8,#f0b48c 60%,#e0795a);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:32px;font-size:40px;font-weight:700;color:#f0e8df}
#outro .q b{color:#d8a86a}
#outro .bar{width:140px;height:8px;background:linear-gradient(90deg,#d8a86a,#e0936c);margin-top:24px;border-radius:4px}
"""

recap_rows = "".join(
    f'<li class="{"top" if no=="01" else ""}"><span class="rn">{no}</span><span class="rs">{nm}</span></li>'
    for no,nm in recap)

cover_html = (f'''<div id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="5">
<div class="cv-kick">华语遗珠盘点 · 被低估的校长</div>
<div class="cv-name">谭咏麟</div>
<div class="cv-title">最被低估的5首</div>
<div class="cv-en">Alan Tam — The Underrated Five</div>
<div class="cv-sub">都说他的金曲就那几首 · <b>最好的，藏在专辑最深处</b></div></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci"><span class="strike">就那几首<i class="xln"></i></span></li><li class="ci"><span class="strike">金曲太多<i class="xln"></i></span></li><li class="ci"><span class="strike">听过就忘<i class="xln"></i></span></li></ul>
<div class="imp-note">最耐听的那几首 · <b>从没上过热门</b></div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="5">
<div class="big"><small>公认被低估</small>遗珠 5</div>
<div class="line">不是主打 · 不上热门 · <b>却最舍不得跳过</b></div></div>''') if INC_INTRO else ""
outro_html = (f'''<div id="outro" class="clip" data-start="{E(F_voice)}" data-duration="{round(F_end-F_voice+0.4,3)}" data-track-index="4">
<div class="o2">最好的谭咏麟，<br>一直安静地躺在专辑最深处</div>
<div class="recap-t">被低估 · 完整榜单</div>
<ul class="recap">{recap_rows}</ul>
<div class="q">这五首里，<b>哪一首最舍不得被埋没？</b></div>
<div class="bar"></div></div>''') if INC_OUTRO else ""

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{PART_DUR}" data-track-index="1"></div>
<div id="dusk" class="clip" data-start="0" data-duration="{PART_DUR}" data-track-index="8"></div>
<div id="vig" class="clip" data-start="0" data-duration="{PART_DUR}" data-track-index="7"></div>
<div id="grain" class="clip" data-start="0" data-duration="{PART_DUR}" data-track-index="9"></div>
{cover_html}
{chr(10).join(labels)}
{outro_html}
<audio id="master" data-start="0" data-duration="{PART_DUR}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

# 片尾榜单逐行揭晓（与旁白「第五…第一」同步）
recap_in = round(F_voice + 6.6, 3)
recap_tweens = "".join(
    f'tl.from("#outro .recap li:nth-child({i+1})",{{x:-26,opacity:0,duration:.5,ease:"power2.out"}},{E(recap_in + i*1.18)});'
    for i in range(len(recap)))

intro_js = f'''
tl.set("#cover",{{opacity:1}},{E(0)});
tl.set(["#cover .cv-kick","#cover .cv-name","#cover .cv-title","#cover .cv-en","#cover .cv-sub"],{{opacity:1}},{E(0)});
tl.to("#cover .cv-title",{{scale:1.03,duration:3.2,transformOrigin:"left center",ease:"sine.inOut",yoyo:true,repeat:1}},{E(0.6)});
tl.to("#cover",{{y:-30,opacity:0,duration:.5,ease:"power2.in"}},{E(COVER_END-0.55)});
tl.set("#cover",{{opacity:0}},{E(COVER_END)});
tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{E(CHIP_IN+0.1)});
tl.from("#chips .ci",{{x:-46,opacity:0,duration:.55,ease:"power3.out",stagger:.42}},{E(CHIP_IN+0.3)});
tl.to("#chips .ci:nth-child(1) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{E(CHIP_IN+2.2)});
tl.to("#chips .ci:nth-child(2) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{E(CHIP_IN+2.7)});
tl.to("#chips .ci:nth-child(3) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{E(CHIP_IN+3.2)});
tl.from("#chips .imp-note",{{opacity:0,y:14,duration:.5}},{E(CHIP_IN+3.9)});
tl.to("#chips",{{opacity:0,duration:.4,ease:"power1.in"}},{E(CHIP_OUT-0.45)});
tl.set("#chips",{{opacity:0}},{E(CHIP_OUT)});
tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{E(BRG_IN+0.1)});
tl.from("#bridge .big",{{scale:.7,opacity:0,duration:.6,ease:"back.out(1.4)"}},{E(BRG_IN+0.2)});
tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{E(BRG_IN+0.8)});
tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{E(BRG_OUT-0.45)});
tl.set("#bridge",{{opacity:0}},{E(BRG_OUT)});
''' if INC_INTRO else ""
outro_js = f'''
tl.from("#outro .o2",{{y:50,opacity:0,scale:1.04,duration:.8,ease:"power4.out"}},{E(F_voice+0.4)});
tl.from("#outro .recap-t",{{y:18,opacity:0,duration:.5}},{E(F_voice+5.6)});
{recap_tweens}
tl.from("#outro .q",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{E(recap_in + len(recap)*1.18 + 0.4)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{E(recap_in + len(recap)*1.18 + 0.85)});
''' if INC_OUTRO else ""

js = f'''{intro_js}
{chr(10).join(tweens)}
{outro_js}'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@700;800&family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{PART_DUR}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>'''

Path(OUTFILE).write_text(html, encoding="utf-8")
Path("meta.json").write_text('{"id":"main","name":"tanyonglin-underrated"}', encoding="utf-8")
print((f"PART {PART} " if PART else ("SAMPLE " if SAMPLE else "FULL "))+f"-> {OUTFILE} | PART_DUR={PART_DUR} OFF={OFF} blocks={len(BLK)} intro={INC_INTRO} outro={INC_OUTRO}")
print("TOTAL:", TOTAL, "s | INTRO_END:", INTRO_END)
for b in blocks: print(f"  {b['no']} {b['name']:18s} start={b['start']:.2f} ns={b['ns']:.2f} full={b['full']:.2f} end={b['end']:.2f} show={b['show']}  Lclip>={b['L']:.1f}s")
print(f"  outro start={F_start:.2f} end={F_end:.2f}")
