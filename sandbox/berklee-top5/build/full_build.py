#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""华人歌手伯克利校友 TOP5（倒序揭晓 第5→第1）竖屏 1080×1920 完整片构建。
产物：master.wav（逐段 床→swell→展示 + 旁白 ducking）+ hf/index.html + hf/clips_seg/*.mp4。
渲染后必须 ffmpeg mux master.wav（HyperFrames 会压平音频动态）。
封面/片头不泄露名单与排名（brief 硬约束）。
"""
import subprocess, wave, contextlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import os; os.chdir(ROOT)
A = "audio"

def wdur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

NARR = json.loads(Path(f"{A}/narration.json").read_text(encoding="utf-8"))
ND = {k: v["dur"] for k, v in NARR.items()}
print("NARR:", {k: round(v,1) for k,v in ND.items()})

# ============ 节奏常量 ============
LEAD, PRE, POST, SWELL, TAIL = 0.3, 0.6, 1.0, 1.4, 1.6
BED, VG = 0.20, 2.0          # 旁白期音乐床增益 / 旁白增益
COVER_D = 3.4
ILEAD = 0.4                  # intro voice 前 lead
ITAIL = 2.4                  # intro 尾
TLEAD, TTAIL = 0.4, 1.7      # 转场 lead/tail
OLEAD, OTAIL = 0.4, 4.2      # outro lead/tail

# ============ 章节定义（出场顺序 r5→r1） ============
CH = [
  dict(key="r5", rankno="05", rank="5", name="欧阳娜娜", en="OUYANG NANA",
       hook="她，争议最大", tags=["大提琴少女","伯克利标签","跨界音乐人"],
       rel="伯克利校友 · 古典与流行之间", song="温暖你的冬", song_en="Warm Winter", year="2017",
       review="不是最炸的歌，<br>却是她音乐身份的起点。", kw="跨界",
       vsrc="raw/onn_golden.mkv", vcrop="1920:1080:0:0", vseek=6.0,
       asrc="raw/onn_studio_audio.wav", aseek=25.0, show=28.0, mgain=1.30,
       pri="#E7C9A2", acc="#F3E7D2", tintc="231,201,162"),
  dict(key="r4", rankno="04", rank="4", name="刘宪华", en="HENRY LAU",
       hook="他，最全能", tags=["小提琴","唱跳","作曲制作"],
       rel="伯克利校友 · 科班全能型", song="Trap", song_en="Trap", year="2013",
       review="一首歌里，<br>装下唱、跳、器乐和舞台。", kw="全能",
       vsrc="raw/henry_trap.webm", vcrop="1920:915:0:165", vseek=168.0,
       asrc="raw/henry_trap.webm", aseek=168.0, show=29.0, mgain=0.85,
       pri="#7FB3E8", acc="#CFE6FF", tintc="120,168,232"),
  dict(key="r3", rankno="03", rank="3", name="张杰", en="JASON ZHANG",
       hook="他，最能唱", tags=["实力唱将","现场型歌手","伯克利进修"],
       rel="曾赴伯克利进修", song="逆战", song_en="Fighter", year="2011",
       review="前奏一响，<br>很多人的青春自动冲锋。", kw="现场",
       vsrc="raw/zhangjie_nizhan.mp4", vcrop="1920:775:0:0", vseek=226.0,
       asrc="raw/zhangjie_nizhan.mp4", aseek=226.0, show=30.0, mgain=1.15,
       pri="#F08A4B", acc="#FFD9B0", tintc="240,138,75"),
  dict(key="r2", rankno="02", rank="2", name="王力宏", en="LEEHOM WANG",
       hook="他，最经典", tags=["伯克利'99","创作才子","华语R&B代表"],
       rel="Berklee '99 · 学院派 × 华语流行", song="唯一", song_en="The One and Only", year="2001",
       review="旋律不复杂，<br>一开口就是黄金年代。", kw="经典",
       vsrc="raw/wanglihong_weiyi.mp4", vcrop="1920:885:0:0", vseek=50.0,
       asrc="raw/wanglihong_weiyi.mp4", aseek=50.0, show=30.0, mgain=0.90,
       pri="#E9C46A", acc="#F6E6BF", tintc="233,196,106"),
  dict(key="r1", rankno="01", rank="1", name="王源", en="ROY WANG",
       hook="他，最出圈", tags=["顶流少年","伯克利音乐人","从偶像到原创"],
       rel="新生代伯克利音乐人", song="因为遇见你", song_en="Cause of You", year="2018",
       review="从偶像，<br>到原创歌手。", kw="出圈",
       vsrc="raw/wangyuan_yt.mkv", vcrop="1280:640:0:0", vseek=40.0,
       asrc="raw/wangyuan_yt.mkv", aseek=40.0, show=34.0, mgain=1.0,
       pri="#F2A8C4", acc="#FFD6E6", tintc="242,168,196"),
]
# 转场（出现在对应歌手之后；最后一首无转场，直接 outro）
TRANS = {"r5":"t54","r4":"t43","r3":"t32","r2":"t21"}  # r1 无转场

def ch_secdur(c):
    return LEAD + PRE + ND[c["key"]] + POST + SWELL + c["show"] + TAIL
def ch_anchors(c):
    v0 = LEAD + PRE
    v1 = v0 + ND[c["key"]]
    sw0 = v1 + POST
    full0 = sw0 + SWELL
    full1 = full0 + c["show"]
    return dict(v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1, end=ch_secdur(c))
def tr_secdur(tk):
    return TLEAD + ND[tk] + TTAIL

# ============ 绝对时间轴 ============
seg_order = []   # (kind, key)
seg_dur = {}
seg_order.append(("cover","cover")); seg_dur[("cover","cover")] = COVER_D
intro_d = ILEAD + ND["intro"] + ITAIL
seg_order.append(("intro","intro")); seg_dur[("intro","intro")] = intro_d
for c in CH:
    seg_order.append(("chapter", c["key"])); seg_dur[("chapter", c["key"])] = ch_secdur(c)
    if c["key"] in TRANS:
        tk = TRANS[c["key"]]
        seg_order.append(("trans", tk)); seg_dur[("trans", tk)] = tr_secdur(tk)
outro_d = OLEAD + ND["outro"] + OTAIL
seg_order.append(("outro","outro")); seg_dur[("outro","outro")] = outro_d

starts = {}
t = 0.0
for so in seg_order:
    starts[so] = round(t, 3); t += seg_dur[so]
TOTAL = round(t, 3)
print(f"TOTAL: {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")
def fmt(x): return f"{round(float(x),3)}"

# 便捷查找
CHByKey = {c["key"]: c for c in CH}
def chap_start(k): return starts[("chapter", k)]
def trans_start(tk): return starts[("trans", tk)]

# ============================================================
# PART B — footage 预切（letterbox 竖屏，video-only，密集关键帧）
# ============================================================
Path("hf/clips_seg").mkdir(parents=True, exist_ok=True)
def letterbox_cut(vsrc, vcrop, vseek, secdur, out):
    vf = (f"crop={vcrop},split=2[bg][fg];"
          f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"gblur=sigma=28,eq=brightness=-0.34:saturation=1.04[bgb];"
          f"[fg]scale=1080:-2[fgs];"
          f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    run(["ffmpeg","-v","error","-i",vsrc,"-ss",fmt(vseek),"-t",fmt(secdur),
         "-filter_complex",vf,"-map","[v]","-an",
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
         "-pix_fmt","yuv420p", out,"-y"])

import sys
STEP = sys.argv[1] if len(sys.argv) > 1 else "all"

if STEP in ("all","clips"):
    for c in CH:
        sd = ch_secdur(c)
        out = f"hf/clips_seg/{c['key']}.mp4"
        print(f"cut {c['key']} ({c['name']}) seek={c['vseek']} dur={sd:.1f} -> {out}")
        letterbox_cut(c["vsrc"], c["vcrop"], c["vseek"], sd, out)
    print("clips_seg done")

# ============================================================
# PART C — 音频 master
# ============================================================
Path("build/segs").mkdir(parents=True, exist_ok=True)
def ms(x): return int(round(x*1000))

def build_chapter_audio(c):
    k = c["key"]; a = ch_anchors(c); sd = ch_secdur(c)
    v0, sw0, full0, full1 = a["v0"], a["sw0"], a["full0"], a["full1"]
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
          f"+(between(t,{v0},{sw0}))*{BED}"
          f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
          f"+(gte(t,{full0}))*1.0")
    out = f"build/segs/seg_{k}.wav"
    run(["ffmpeg","-v","error","-i", c["asrc"], "-i", f"{A}/{k}.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms(v0)}|{ms(v0)},volume={VG}[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,"
         f"loudnorm=I=-14:TP=-1.0:LRA=11,atrim={c['aseek']}:{c['aseek']+sd},asetpts=PTS-STARTPTS,"
         f"volume='{ve}':eval=frame,volume={c['mgain']},afade=t=out:st={full1}:d={sd-full1}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{sd},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    return out

def build_bed_voice(key, seglen, voice_at, bedsrc, bedseek, bedgain, fin, fout, out, voicegain=VG):
    """通用：低音量 cello 床 + 一段旁白（cover/intro/trans/outro 用）。"""
    run(["ffmpeg","-v","error","-i", bedsrc, "-i", f"{A}/{key}.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms(voice_at)}|{ms(voice_at)},volume={voicegain}[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim={bedseek}:{bedseek+seglen},asetpts=PTS-STARTPTS,volume={bedgain},"
         f"afade=t=in:st=0:d={fin},afade=t=out:st={max(seglen-fout,0.1)}:d={fout}[bed];"
         f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seglen},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])

CELLO = "raw/cello_bed.wav"
if STEP in ("all","audio"):
    # cover：纯 cello 床（无旁白），用 intro 的极前段做静态
    run(["ffmpeg","-v","error","-i",CELLO,"-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=8:{8+COVER_D},asetpts=PTS-STARTPTS,volume=0.22,afade=t=in:st=0:d=1.0,"
         f"afade=t=out:st={COVER_D-0.6}:d=0.6[out]",
         "-map","[out]","-ac","2","-ar","48000","build/segs/seg_cover.wav","-y"])
    # intro：cello 床 + intro 旁白
    build_bed_voice("intro", intro_d, ILEAD+0.3, CELLO, 12.0, 0.26, 1.0, 1.6, "build/segs/seg_intro.wav")
    # chapters
    for c in CH:
        print(f"audio seg {c['key']}...")
        build_chapter_audio(c)
        if c["key"] in TRANS:
            tk = TRANS[c["key"]]
            # 转场床：用下一首歌曲源的极前段(低)做预热，避免死静
            nxt = CH[CH.index(c)+1]
            tsd = tr_secdur(tk)
            build_bed_voice(tk, tsd, TLEAD, CELLO, 40.0, 0.24, 0.5, 1.0, f"build/segs/seg_{tk}.wav")
    # outro：cello 床 + outro 旁白
    build_bed_voice("outro", outro_d, OLEAD, CELLO, 60.0, 0.26, 1.2, 3.0, "build/segs/seg_outro.wav")

    # 拼接 master
    order = []
    for kind,key in seg_order:
        order.append(f"seg_{key}.wav")
    Path("build/segs/seglist.txt").write_text("".join(f"file '{n}'\n" for n in order), encoding="utf-8")
    run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/seglist.txt",
         "-ac","2","-ar","48000","master.wav","-y"])
    print("master dur:", wdur("master.wav"), "planned:", TOTAL)
    shutil.copy("master.wav","hf/master.wav")

# ============================================================
# PART D — cover_assets（5 张暗化神秘卡 + 用于卡片的局部）
# ============================================================
if STEP in ("all","cover"):
    Path("hf/cover_assets").mkdir(parents=True, exist_ok=True)
    # (src, seek, crop WxH+X+Y 在源坐标) 取一帧 → 暗化竖卡 360x480
    CARDS = [
      ("raw/onn_golden.mkv", 22, "760:1014:1100:66"),     # 欧阳娜娜+大提琴(右)
      ("raw/henry_trap.webm", 30, "720:960:760:120"),     # 刘宪华面部
      ("raw/zhangjie_nizhan.mp4", 300, "720:960:600:40"), # 张杰特写
      ("raw/wanglihong_weiyi.mp4", 95, "620:826:640:8"),  # 王力宏特写(避底部歌词)
      ("raw/wangyuan_yt.mkv", 260, "470:588:395:8"),     # 王源特写(避底部歌词)
    ]
    for i,(src,seek,crop) in enumerate(CARDS):
        out = f"hf/cover_assets/card{i+1}.jpg"
        run(["ffmpeg","-v","error","-i",src,"-ss",str(seek),
             "-vf",f"crop={crop},scale=360:480,eq=brightness=-0.42:contrast=1.32:saturation=0.34,"
             f"colorbalance=rs=-0.1:bs=0.12",
             "-frames:v","1",out,"-y"])
    print("cover_assets done")

# ============================================================
# CSS + JS（设计：名校音乐感，暗底 + 金/红学院色 + 每章强调色）
# ============================================================
CSS_TEXT = r'''
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06080F;color:#F4EEE2;
  font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0}
.tint{position:absolute;inset:0;z-index:2;opacity:0}
.chrome{position:absolute;inset:0;z-index:6;pointer-events:none}

/* 大号排名水印 */
.bignum{position:absolute;top:18px;right:30px;font-family:"Oswald",sans-serif;font-weight:700;
  font-size:560px;line-height:.8;color:var(--pri);opacity:0;letter-spacing:-12px;
  -webkit-text-stroke:2px rgba(255,255,255,.10);text-shadow:0 0 80px rgba(0,0,0,.5)}

/* 左侧排名进度轨（只显示名次，不泄露名字） */
.rail{position:absolute;left:46px;top:760px;width:60px;display:flex;flex-direction:column;gap:26px;opacity:0;z-index:7}
.rdot{width:54px;height:54px;border-radius:50%;background:rgba(18,20,30,.78);border:2px solid rgba(255,255,255,.22);
  display:flex;align-items:center;justify-content:center}
.rdot span{font-family:"Oswald",sans-serif;font-weight:600;font-size:24px;color:rgba(255,255,255,.55)}
.rdot.done{background:rgba(70,72,86,.6);border-color:rgba(255,255,255,.3)}
.rdot.active{background:var(--pri);border-color:var(--pri);transform:scale(1.18);
  box-shadow:0 0 30px var(--pri),0 0 64px rgba(255,255,255,.18)}
.rdot.active span{color:#0A0C14}

/* 顶部 badge：名次 + 姓名（章内可现名） */
.badge{position:absolute;top:96px;left:64px;display:flex;flex-direction:column;gap:8px;opacity:0;z-index:8}
.b-top{font-family:"Noto Sans SC",sans-serif;font-weight:800;font-size:28px;letter-spacing:.16em;color:var(--pri)}
.b-name{font-family:"Noto Serif SC",serif;font-weight:900;font-size:96px;line-height:.98;color:#FFFDF7;
  letter-spacing:1px;text-shadow:0 6px 40px rgba(0,0,0,.7)}
.b-en{font-family:"Oswald",sans-serif;font-weight:500;font-size:26px;letter-spacing:.36em;color:rgba(255,255,255,.5)}

/* 大钩子 */
.hook{position:absolute;left:64px;right:64px;top:560px;font-family:"Noto Serif SC",serif;font-weight:800;
  font-size:88px;line-height:1.1;color:#FFFDF7;opacity:0;text-shadow:0 8px 50px rgba(0,0,0,.8)}
.hook::before{content:"";display:block;width:90px;height:8px;border-radius:4px;background:var(--pri);margin-bottom:30px;
  box-shadow:0 0 24px var(--pri)}

/* 信息卡（标签 + 伯克利关系） */
.infocard{position:absolute;left:64px;right:64px;bottom:300px;opacity:0}
.chips{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:28px}
.chip{font-family:"Noto Sans SC",sans-serif;font-weight:700;font-size:32px;color:#F4EEE2;
  padding:12px 26px;border-radius:999px;background:rgba(255,255,255,.08);
  border:1.5px solid rgba(255,255,255,.2);backdrop-filter:blur(10px)}
.rel{font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:34px;color:var(--acc);
  display:flex;align-items:center;gap:18px;letter-spacing:.02em}
.rel-dot{width:14px;height:14px;border-radius:50%;background:var(--pri);box-shadow:0 0 16px var(--pri)}

/* 展示段大关键词 */
.kw{position:absolute;left:0;right:0;top:430px;text-align:center;font-family:"Noto Serif SC",serif;font-weight:900;
  font-size:340px;line-height:.9;color:var(--pri);opacity:0;letter-spacing:8px;mix-blend-mode:screen;
  filter:drop-shadow(0 10px 70px rgba(0,0,0,.4))}

/* 代表曲卡 */
.songcard{position:absolute;left:64px;right:64px;bottom:300px;display:flex;flex-direction:column;gap:12px;opacity:0}
.sc-label{font-family:"Noto Sans SC",sans-serif;font-weight:800;font-size:26px;letter-spacing:.4em;color:var(--pri)}
.sc-name{font-family:"Noto Serif SC",serif;font-weight:900;font-size:104px;line-height:1.0;color:#FFFDF7;
  letter-spacing:-1px;text-shadow:0 6px 44px rgba(0,0,0,.7)}
.sc-meta{font-family:"Oswald",sans-serif;font-weight:500;font-size:30px;letter-spacing:.18em;color:rgba(255,255,255,.62)}

/* 短评金句 */
.review{position:absolute;left:64px;right:64px;bottom:150px;font-family:"Noto Serif SC",serif;font-weight:500;
  font-size:50px;line-height:1.34;color:rgba(244,238,226,.95);opacity:0;letter-spacing:.01em}

/* 来源小字 */
.src{position:absolute;left:0;right:0;bottom:54px;text-align:center;font-family:"Noto Sans SC",sans-serif;
  font-weight:400;font-size:22px;letter-spacing:.22em;color:rgba(255,255,255,.34);opacity:0}

/* ============ 封面 ============ */
.cover{position:absolute;inset:0;z-index:50;background:radial-gradient(ellipse at 50% 22%,#15233E 0%,#070A12 62%);overflow:hidden}
.cv-beams{position:absolute;inset:0;background:
  conic-gradient(from 200deg at 50% 8%, rgba(233,196,106,.0) 0deg, rgba(233,196,106,.16) 18deg, rgba(233,196,106,0) 36deg,
  rgba(127,179,232,.12) 60deg, rgba(127,179,232,0) 84deg, rgba(200,69,59,.14) 120deg, rgba(200,69,59,0) 150deg);
  mix-blend-mode:screen;opacity:.9}
.cv-staff{position:absolute;left:0;right:0;top:0;bottom:0;background:repeating-linear-gradient(0deg,
  transparent 0 38px, rgba(255,255,255,.05) 38px 40px);opacity:.5}
.cv-grain{position:absolute;inset:0;background-image:radial-gradient(circle at 20% 30%,rgba(255,255,255,.05) 0 .5px,transparent .8px),
  radial-gradient(circle at 75% 65%,rgba(255,255,255,.05) 0 .5px,transparent .8px);background-size:180px 180px,220px 220px;opacity:.5}
.cv-top{position:absolute;top:88px;left:0;right:0;display:flex;flex-direction:column;align-items:center;gap:12px}
.cv-berklee{font-family:"Oswald",sans-serif;font-weight:700;font-size:74px;letter-spacing:.22em;color:#E9C46A;
  text-shadow:0 0 40px rgba(233,196,106,.35)}
.cv-cn{font-family:"Noto Sans SC",sans-serif;font-weight:700;font-size:30px;letter-spacing:.5em;color:rgba(255,255,255,.6)}
.cv-cards{position:absolute;top:330px;left:0;right:0;height:560px;display:flex;align-items:center;justify-content:center}
.cv-card{position:absolute;width:300px;height:400px;border-radius:22px;overflow:hidden;
  border:2px solid rgba(255,255,255,.28);box-shadow:0 30px 80px rgba(0,0,0,.7);background:#0B0E18}
.cv-card .cv-img{position:absolute;inset:0;background-size:cover;background-position:center top}
.cv-card .cv-q{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-family:"Oswald",sans-serif;font-weight:700;font-size:150px;color:rgba(255,255,255,.78);
  background:linear-gradient(180deg,rgba(8,10,20,.35),rgba(8,10,20,.78));text-shadow:0 0 30px rgba(0,0,0,.6)}
.cv-c1{transform:translateX(-460px) rotate(-13deg) scale(.86)}
.cv-c2{transform:translateX(-235px) rotate(-6deg) scale(.93)}
.cv-c3{transform:translateX(0) rotate(0deg) scale(1.04);z-index:3}
.cv-c4{transform:translateX(235px) rotate(6deg) scale(.93)}
.cv-c5{transform:translateX(460px) rotate(13deg) scale(.86)}
.cv-main{position:absolute;bottom:96px;left:64px;right:64px;text-align:center}
.cv-title{font-family:"Noto Serif SC",serif;font-weight:900;font-size:98px;line-height:1.06;color:#FFFDF7;letter-spacing:1px}
.cv-big{font-family:"Oswald",sans-serif;font-weight:700;font-size:118px;line-height:1.0;color:#E9C46A;letter-spacing:.06em;margin:8px 0}
.cv-big span{color:#C8453B;margin-left:14px;-webkit-text-stroke:0;text-shadow:0 0 40px rgba(200,69,59,.5)}
.cv-sub{font-family:"Noto Sans SC",sans-serif;font-weight:700;font-size:42px;color:rgba(255,255,255,.82);letter-spacing:.04em}

/* ============ 片头 montage ============ */
.introblk{position:absolute;inset:0;z-index:49;background:radial-gradient(ellipse at 50% 40%,#101A30 0%,#06080F 70%);overflow:hidden}
.in-beams{position:absolute;left:-20%;right:-20%;top:-30%;bottom:-30%;background:
  conic-gradient(from 0deg at 50% 50%, rgba(233,196,106,.10) 0deg,transparent 30deg,rgba(127,179,232,.10) 90deg,
  transparent 130deg,rgba(200,69,59,.10) 200deg,transparent 250deg,rgba(233,196,106,.08) 320deg,transparent 360deg);
  mix-blend-mode:screen;opacity:.8}
.in-staff{position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent 0 46px,rgba(255,255,255,.045) 46px 48px);opacity:.5}
.in-eq{position:absolute;left:0;right:0;bottom:0;height:420px;display:flex;align-items:flex-end;justify-content:center;gap:16px;opacity:.55}
.in-eq span{width:30px;height:100%;transform-origin:bottom;transform:scaleY(.15);border-radius:8px 8px 0 0;
  background:linear-gradient(180deg,#E9C46A,#C8453B);opacity:.65}
.in-notes{position:absolute;inset:0}
.in-notes .nt{position:absolute;font-size:60px;color:rgba(233,196,106,.5);opacity:0}
.nt0{left:14%;top:60%}.nt1{left:30%;top:40%}.nt2{left:48%;top:66%}.nt3{left:62%;top:36%}
.nt4{left:78%;top:58%}.nt5{left:22%;top:24%}.nt6{left:70%;top:22%}
.in-line{position:absolute;left:80px;right:80px;top:780px;text-align:center;opacity:0}
.in-a{display:block;font-family:"Noto Serif SC",serif;font-weight:800;font-size:78px;line-height:1.1;color:#FFFDF7;text-shadow:0 6px 40px rgba(0,0,0,.7)}
.in-b{display:block;margin-top:22px;font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:34px;letter-spacing:.1em;color:var(--acc,#E9C46A);color:#E9C46A}

/* ============ 转场 ============ */
.transblk{position:absolute;inset:0;z-index:44;background:radial-gradient(ellipse at 50% 50%,#121A2C 0%,#06080F 72%);overflow:hidden}
.tr-sweep{position:absolute;top:0;bottom:0;width:60%;left:0;
  background:linear-gradient(100deg,transparent,rgba(233,196,106,.18),transparent);transform:translateX(-120%)}
.tr-row{position:absolute;top:50%;left:0;right:0;transform:translateY(-50%);display:flex;align-items:center;justify-content:center;gap:50px}
.tr-cell{display:flex;flex-direction:column;align-items:center;gap:14px;opacity:0}
.tr-no{font-family:"Oswald",sans-serif;font-weight:700;font-size:150px;line-height:.9;color:#E9C46A}
.tr-cell.to .tr-no{color:#C8453B}
.tr-tx{font-family:"Noto Serif SC",serif;font-weight:700;font-size:46px;color:#FFFDF7}
.tr-arrow{font-family:"Noto Sans SC",sans-serif;font-weight:300;font-size:90px;color:rgba(255,255,255,.5);opacity:0}

/* ============ 片尾 ============ */
.outroblk{position:absolute;inset:0;z-index:45;background:radial-gradient(ellipse at 50% 30%,#15233E 0%,#06080F 66%);overflow:hidden}
.ot-beams{position:absolute;inset:0;background:conic-gradient(from 210deg at 50% 6%,rgba(233,196,106,0) 0deg,
  rgba(233,196,106,.12) 16deg,transparent 34deg,rgba(127,179,232,.10) 70deg,transparent 100deg);mix-blend-mode:screen;opacity:.8}
.ot-h{position:absolute;top:150px;left:72px;right:72px;font-family:"Noto Serif SC",serif;font-weight:900;
  font-size:90px;line-height:1.1;color:#FFFDF7;opacity:0;text-align:center}
.ot-rail{position:absolute;top:560px;left:96px;right:96px}
.ot-line{display:flex;align-items:baseline;gap:26px;padding:20px 0;border-bottom:1px solid rgba(255,255,255,.1);opacity:0}
.ot-n{font-family:"Noto Serif SC",serif;font-weight:800;font-size:52px;color:#E9C46A;min-width:230px}
.ot-d{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:34px;color:rgba(244,238,226,.8)}
.ot-cta{position:absolute;bottom:150px;left:72px;right:72px;text-align:center}
.ot-q{font-family:"Noto Serif SC",serif;font-weight:800;font-size:62px;color:#FFFDF7;opacity:0;margin-bottom:24px}
.ot-q2{font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:34px;color:#E9C46A;opacity:0;letter-spacing:.04em}
'''

def build_js():
    P=[]
    A_=P.append
    # ---- 封面（首帧静态可见，不 fade-in） ----
    A_(f'tl.set("#cover",{{opacity:1}},0);')
    A_(f'tl.set(".cv-card",{{opacity:1}},0);')
    A_(f'tl.to(".cv-cards",{{scale:1.03,duration:2.4,ease:"sine.inOut",transformOrigin:"50% 50%"}},0.6);')
    A_(f'tl.to(".cv-beams",{{rotate:10,duration:{COVER_D},ease:"sine.inOut",transformOrigin:"50% 8%"}},0);')
    A_(f'tl.to("#cover",{{opacity:0,duration:.5,ease:"power2.in"}},{fmt(COVER_D-0.5)});')
    A_(f'tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});')
    # ---- 片头 montage ----
    ib = starts[("intro","intro")]; ie = ib + intro_d
    A_(f'tl.set("#intro",{{opacity:1}},{fmt(ib)});')
    A_(f'tl.to(".in-beams",{{rotate:30,duration:{fmt(intro_d)},ease:"none",transformOrigin:"50% 50%"}},{fmt(ib)});')
    A_(f'tl.to(".in-eq span",{{scaleY:1,duration:.42,ease:"sine.inOut",stagger:{{each:.09,from:"center",yoyo:true,repeat:40}}}},{fmt(ib)});')
    A_(f'tl.to(".in-notes .nt",{{opacity:.7,y:-40,duration:1.6,ease:"sine.out",stagger:{{each:.5,yoyo:true,repeat:20}}}},{fmt(ib)});')
    for i in range(4):
        at = ib + 0.5 + i*((intro_d-1.2)/4)
        A_(f'tl.fromTo("#inl_{i}",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.55,ease:"power3.out"}},{fmt(at)});')
        if i < 3:
            A_(f'tl.to("#inl_{i}",{{opacity:0,y:-22,duration:.45,ease:"power2.in"}},{fmt(at+(intro_d-1.2)/4-0.4)});')
    A_(f'tl.to("#intro",{{opacity:0,duration:.55,ease:"power2.in"}},{fmt(ie-0.55)});')
    A_(f'tl.set("#intro",{{opacity:0}},{fmt(ie)});')
    # ---- 章节 ----
    for c in CH:
        k=c["key"]; base=chap_start(k); a=ch_anchors(c)
        v0=base+a["v0"]; sw0=base+a["sw0"]; full0=base+a["full0"]; full1=base+a["full1"]; end=base+a["end"]
        fo=end-1.5
        A_(f'// ---- {c["name"]} ----')
        A_(f'tl.fromTo("#fv_{k}",{{opacity:0,scale:1.07}},{{opacity:1,scale:1,duration:1.3,ease:"power2.out"}},{fmt(base)});')
        A_(f'tl.to("#tint_{k}",{{opacity:1,duration:1.1,ease:"power1.out"}},{fmt(base)});')
        # 排名水印 slam + rail + badge
        A_(f'tl.fromTo("#bn_{k}",{{opacity:0,scale:1.5}},{{opacity:.14,scale:1,duration:.7,ease:"power3.out"}},{fmt(base+0.15)});')
        A_(f'tl.fromTo("#rail_{k}",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:.7,ease:"power2.out"}},{fmt(base+0.35)});')
        A_(f'tl.fromTo("#bg_{k}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:.7,ease:"power3.out"}},{fmt(base+0.5)});')
        # hook 进/出
        A_(f'tl.fromTo("#hk_{k}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{fmt(base+0.95)});')
        A_(f'tl.to("#hk_{k}",{{opacity:0,y:-26,duration:.5,ease:"power2.in"}},{fmt(base+3.6)});')
        # infocard 进（hook 退后）/ 出（SHOW 前）
        A_(f'tl.fromTo("#ic_{k}",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{fmt(base+4.0)});')
        A_(f'tl.fromTo("#src_{k}",{{opacity:0}},{{opacity:1,duration:.6}},{fmt(base+1.4)});')
        A_(f'tl.to("#ic_{k}",{{opacity:0,y:-20,duration:.5,ease:"power2.in"}},{fmt(sw0-0.1)});')
        # SHOW：大关键词 + 代表曲卡 + 短评
        A_(f'tl.fromTo("#kw_{k}",{{opacity:0,scale:.92}},{{opacity:.30,scale:1,duration:1.4,ease:"power3.out"}},{fmt(full0-0.5)});')
        A_(f'tl.to("#kw_{k}",{{opacity:.42,duration:1.2,ease:"sine.inOut"}},{fmt(full0+1.0)});')
        A_(f'tl.fromTo("#sc_{k}",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{fmt(sw0+0.2)});')
        A_(f'tl.fromTo("#rv_{k}",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(full0+5.0)});')
        A_(f'tl.to("#rv_{k}",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(end-1.6)});')
        A_(f'tl.to("#sc_{k}",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(end-1.6)});')
        A_(f'tl.to("#kw_{k}",{{opacity:0,duration:.8,ease:"power1.in"}},{fmt(end-1.6)});')
        # 收尾 hard kill
        for sel in [f'#fv_{k}',f'#tint_{k}',f'#bn_{k}',f'#rail_{k}',f'#bg_{k}']:
            A_(f'tl.to("{sel}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(fo)});')
            A_(f'tl.set("{sel}",{{opacity:0}},{fmt(end)});')
        A_(f'tl.set("#src_{k}",{{opacity:0}},{fmt(end)});')
        A_(f'tl.set("#hk_{k}",{{opacity:0}},{fmt(end)});')
        A_(f'tl.set("#ic_{k}",{{opacity:0}},{fmt(end)});')
        # ---- 转场 ----
        if k in TRANS:
            tk=TRANS[k]; ts=trans_start(tk); td=tr_secdur(tk); te=ts+td
            A_(f'tl.fromTo("#tr_{tk}",{{opacity:0}},{{opacity:1,duration:.35,ease:"power2.out"}},{fmt(ts)});')
            A_(f'tl.fromTo("#tr_{tk} .tr-sweep",{{xPercent:-120}},{{xPercent:240,duration:1.4,ease:"power2.inOut"}},{fmt(ts)});')
            A_(f'tl.fromTo("#tr_{tk} .from",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.45,ease:"power2.out"}},{fmt(ts+0.15)});')
            A_(f'tl.fromTo("#tr_{tk} .tr-arrow",{{opacity:0,scale:.5}},{{opacity:1,scale:1,duration:.4,ease:"back.out(2)"}},{fmt(ts+0.45)});')
            A_(f'tl.fromTo("#tr_{tk} .to",{{opacity:0,x:26}},{{opacity:1,x:0,duration:.45,ease:"power2.out"}},{fmt(ts+0.7)});')
            A_(f'tl.to("#tr_{tk}",{{opacity:0,duration:.5,ease:"power2.in"}},{fmt(te-0.5)});')
            A_(f'tl.set("#tr_{tk}",{{opacity:0}},{fmt(te)});')
    # ---- 片尾 ----
    ob=starts[("outro","outro")]; oe=ob+outro_d
    A_(f'tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{fmt(ob)});')
    A_(f'tl.to("#outro .ot-beams",{{rotate:8,duration:{fmt(outro_d)},ease:"sine.inOut",transformOrigin:"50% 6%"}},{fmt(ob)});')
    A_(f'tl.fromTo(".ot-h",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(ob+0.4)});')
    for i in range(5):
        A_(f'tl.fromTo(".ot-rail .ot-line:nth-child({i+1})",{{opacity:0,x:-22}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{fmt(ob+1.4+i*0.32)});')
    A_(f'tl.fromTo(".ot-q",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{fmt(ob+3.4)});')
    A_(f'tl.fromTo(".ot-q2",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6,ease:"power2.out"}},{fmt(ob+4.3)});')
    A_(f'tl.to("#outro",{{opacity:1,duration:.1}},{fmt(oe-0.2)});')
    return "\n".join(P)

# ============================================================
# PART E — HTML composition
# ============================================================
if STEP in ("all","html"):
    foot_tracks = {"r5":0,"r4":6,"r3":0,"r2":6,"r1":0}
    foot_html, tint_html, chrome_html = [], [], []
    for c in CH:
        k = c["key"]; base = chap_start(k); a = ch_anchors(c); sd = a["end"]
        foot_html.append(
            f'<video id="fv_{k}" class="fv clip" data-start="{fmt(base)}" '
            f'data-duration="{fmt(sd)}" data-track-index="{foot_tracks[k]}" '
            f'src="clips_seg/{k}.mp4" muted playsinline></video>')
        tint_html.append(
            f'<div id="tint_{k}" class="clip tint" data-start="{fmt(base)}" '
            f'data-duration="{fmt(sd)}" data-track-index="{12+CH.index(c)}" '
            f'style="background:linear-gradient(180deg, rgba({c["tintc"]},.10) 0%, '
            f'rgba(6,9,16,.30) 38%, rgba(6,9,16,.86) 100%);"></div>')
        dots = "".join(
            f'<div class="rdot{" active" if CH[i]["key"]==k else ""}{" done" if i<CH.index(c) else ""}">'
            f'<span>{CH[i]["rank"]}</span></div>' for i in range(5))
        chips = "".join(f'<span class="chip">{t}</span>' for t in c["tags"])
        chrome_html.append(f'''<div id="ch_{k}" class="clip chrome" data-start="{fmt(base)}" data-duration="{fmt(sd)}" data-track-index="{20+CH.index(c)}" style="--pri:{c['pri']};--acc:{c['acc']};">
  <div class="bignum" id="bn_{k}">{c['rankno']}</div>
  <div class="rail" id="rail_{k}">{dots}</div>
  <div class="badge" id="bg_{k}"><span class="b-top">TOP 5 · 第 {c['rank']} 名</span><span class="b-name">{c['name']}</span><span class="b-en">{c['en']}</span></div>
  <div class="hook" id="hk_{k}">{c['hook']}</div>
  <div class="infocard" id="ic_{k}">
    <div class="chips">{chips}</div>
    <div class="rel"><span class="rel-dot"></span>{c['rel']}</div>
  </div>
  <div class="kw" id="kw_{k}">{c['kw']}</div>
  <div class="songcard" id="sc_{k}">
    <span class="sc-label">代表曲</span>
    <span class="sc-name">《{c['song']}》</span>
    <span class="sc-meta">{c['song_en']} · {c['year']}</span>
  </div>
  <div class="review" id="rv_{k}">{c['review']}</div>
  <div class="src" id="src_{k}">素材：官方 MV / 现场 · 仅作盘点介绍</div>
</div>''')

    # ---- 封面（神秘卡牌，不泄露名单/排名） ----
    cover_cards = "".join(
        f'<div class="cv-card cv-c{i+1}"><div class="cv-img" style="background-image:url(cover_assets/card{i+1}.jpg)"></div><div class="cv-q">?</div></div>'
        for i in range(5))
    cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="40">
  <div class="cv-beams"></div>
  <div class="cv-staff"></div>
  <div class="cv-grain"></div>
  <div class="cv-top"><span class="cv-berklee">BERKLEE</span><span class="cv-cn">伯克利 · 校友盘点</span></div>
  <div class="cv-cards">{cover_cards}</div>
  <div class="cv-main">
    <div class="cv-title">华人歌手<br>伯克利校友</div>
    <div class="cv-big">TOP<span>5</span></div>
    <div class="cv-sub">谁才是 · 最出圈的那一个？</div>
  </div>
</div>'''

    # ---- 片头 montage（学院感动效，无名单） ----
    intro_base = starts[("intro","intro")]
    intro_lines = [
        ("一所学校", "出现频率高到离谱"),
        ("有人完成转型", "有人把学院派玩成爆款"),
        ("5 位华人校友", "BERKLEE ALUMNI"),
        ("第一名没有悬念", "但前面几位 · 更有故事"),
    ]
    intro_html = f'''<div id="intro" class="clip introblk" data-start="{fmt(intro_base)}" data-duration="{fmt(intro_d)}" data-track-index="41">
  <div class="in-beams"></div>
  <div class="in-staff"></div>
  <div class="in-eq">{''.join('<span></span>' for _ in range(13))}</div>
  <div class="in-notes">{''.join(f'<span class="nt nt{i}">♪</span>' for i in range(7))}</div>
  {''.join(f'<div class="in-line" id="inl_{i}"><span class="in-a">{x[0]}</span><span class="in-b">{x[1]}</span></div>' for i,x in enumerate(intro_lines))}
</div>'''

    # ---- 转场卡 ----
    trans_meta = {
        "t54": ("5","跨界感","4","全能感"),
        "t43": ("4","全能型","3","唱功型"),
        "t32": ("3","靠现场","2","学院派 × 爆款"),
        "t21": ("2","经典答案","1","流量新答案"),
    }
    trans_html = []
    for tk,(fa,fb,ta,tb) in trans_meta.items():
        tb_start = trans_start(tk); td = tr_secdur(tk)
        trans_html.append(f'''<div id="tr_{tk}" class="clip transblk" data-start="{fmt(tb_start)}" data-duration="{fmt(td)}" data-track-index="42">
  <div class="tr-sweep"></div>
  <div class="tr-row">
    <div class="tr-cell from"><span class="tr-no">{fa}</span><span class="tr-tx">{fb}</span></div>
    <div class="tr-arrow">→</div>
    <div class="tr-cell to"><span class="tr-no">{ta}</span><span class="tr-tx">{tb}</span></div>
  </div>
</div>''')

    # ---- 片尾 recap + CTA ----
    outro_base = starts[("outro","outro")]
    routes = [
        ("欧阳娜娜","古典 → 流行的跨界"),
        ("刘宪华","唱跳 · 器乐 · 制作全能"),
        ("张杰","成熟歌手打磨现场"),
        ("王力宏","学院派 × 华语流行经典"),
        ("王源","偶像 → 原创音乐人"),
    ]
    outro_html = f'''<div id="outro" class="clip outroblk" data-start="{fmt(outro_base)}" data-duration="{fmt(outro_d)}" data-track-index="43">
  <div class="ot-beams"></div>
  <div class="ot-h">五个人，<br>五种伯克利路线</div>
  <div class="ot-rail">
    {''.join(f'<div class="ot-line"><span class="ot-n">{n}</span><span class="ot-d">{d}</span></div>' for n,d in routes)}
  </div>
  <div class="ot-cta">
    <div class="ot-q">你心里的 TOP 1 是谁？</div>
    <div class="ot-q2">评论区重新排一次 · 看看谁的粉丝最能打</div>
  </div>
</div>'''

    audio_html = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

    CSS = CSS_TEXT
    JS = build_js()

    html = f'''<!doctype html>
<html lang="zh">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;800;900&family=Oswald:wght@500;600;700&family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
{chr(10).join(foot_html)}
{chr(10).join(tint_html)}
{chr(10).join(chrome_html)}
{cover_html}
{intro_html}
{chr(10).join(trans_html)}
{outro_html}
{audio_html}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{JS}
window.__timelines["main"] = tl;
</script>
</body>
</html>'''
    Path("hf/index.html").write_text(html, encoding="utf-8")
    Path("hf/meta.json").write_text('{"id":"main","name":"berklee-top5"}', encoding="utf-8")
    print("index.html written:", len(html), "bytes")

print("BUILD STEP", STEP, "OK  TOTAL", TOTAL)
