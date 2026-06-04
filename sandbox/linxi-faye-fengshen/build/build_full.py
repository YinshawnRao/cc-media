#!/usr/bin/env python3
"""全片构建：开头 + 10首(10→1) + 结尾。按 BLOCK 生成独立 HF 合成（每块≤4 video、<240s，
本机渲染器才稳）+ 各块 seg 音频 → master.wav。渲染各块→concat→mux master。
从项目根运行：python3 build/build_full.py
依赖：audio_full/<line>.wav (narrate_full.py)、hf_full/clips_seg/<key>_show.mp4 (prep_full.sh)、
      raw/img_<theme>.mp4、raw/renjian_full.wav、hf/clips_seg/renjian_img.mp4。
"""
import subprocess, wave, contextlib, json, shutil
from pathlib import Path

ROOT = Path(".")
HF = Path("hf_full"); CS = HF/"clips_seg"; AUD = HF/"audio"
HF.mkdir(exist_ok=True); CS.mkdir(exist_ok=True); AUD.mkdir(exist_ok=True)
(HF/"cover_assets").mkdir(exist_ok=True)

def dur(p):
    with contextlib.closing(wave.open(str(p),'r')) as w: return round(w.getnframes()/w.getframerate(),3)
def run(c): subprocess.run(c, check=True)
def f(x): return f"{round(float(x),3)}"

D = json.loads(Path("audio_full/durs.json").read_text())  # narration line durations

# ---------- phase constants (block-local) ----------
LEAD=0.4; PRE=0.5; GAP=0.55; POST=1.0; SWELL=1.5
B=0.28; Fmus=1.0; TRLOW=0.42
MGAIN={"s7":3.0}  # 暗涌等安静曲副歌补偿(dB)，loudnorm 后偏低
RAMP=0.8

# ---------- per-song config (order 10→1) ----------
# s0 = source time at show clip local0 ; show = showcase seconds ; img = clips_seg/<img>.mp4
SONGS = [
 dict(key="s10", no="10", name="人间", year="1997", album="《王菲》", credit="词 · 林夕　唱 · 王菲　曲 · 中岛美雪",
      tag="人间", scr1="她不是不在人间", scr2a="她只是把人间", scr2b="唱得很远",
      audio="raw/renjian_full.wav", show="s10_show.mp4", s0=70, showd=28, grade="g-warm", tint="red",
      img="img_renjian.mp4", narr=["s10_1","s10_2","s10_3","s10_4"], tr="tr10"),
 dict(key="s9", no="9", name="红豆", year="1998", album="《唱游》", credit="词 · 林夕　唱 · 王菲　曲 · 柳重言",
      tag="相思", scr1="还没好好感受", scr2a="就已经", scr2b="开始怀念",
      audio="raw/hongdou_audio.wav", show="hongdou_show.mp4", s0=115, showd=28, grade="g-warm", tint="red",
      img="img_rain.mp4", narr=["s9_1","s9_2","s9_3"], tr="tr9"),
 dict(key="s8", no="8", name="约定", year="1997", album="《玩具》EP", credit="词 · 林夕　唱 · 王菲　曲 · 陈小霞",
      tag="时间", scr1="真正的约定", scr2a="不是当下说了什么，是", scr2b="多年以后还记得",
      audio="raw/yueding_audio.wav", show="yueding_show.mp4", s0=65, showd=26, grade="g-cool", tint="blue",
      img="img_clock.mp4", narr=["s8_1","s8_2","s8_3"], tr="tr8"),
 dict(key="s7", no="7", name="暗涌", year="1997", album="《玩具》EP", credit="词 · 林夕　唱 · 王菲　曲 · 陈辉阳",
      tag="暗涌", scr1="表面风平浪静", scr2a="心里", scr2b="早有暗涌",
      audio="raw/anyong_audio.wav", show="anyong_show.mp4", s0=127, showd=26, grade="g-cool", tint="blue",
      img="img_sea.mp4", narr=["s7_1","s7_2","s7_3"], tr="tr7"),
 dict(key="s6", no="6", name="流年", year="2001", album="《王菲》", credit="词 · 林夕　唱 · 王菲　曲 · 陈晓娟",
      tag="命运", scr1="当时只是经过", scr2a="后来才知道，是", scr2b="命运",
      audio="raw/liunian_audio.wav", show="liunian_show.mp4", s0=93, showd=28, grade="g-cool", tint="red",
      img="img_train.mp4", narr=["s6_1","s6_2","s6_3"], tr="tr6"),
 dict(key="s5", no="5", name="邮差", year="1999", album="《只爱陌生人》", credit="词 · 林夕　唱 · 王菲　曲 · 陈伟文",
      tag="错过", scr1="有些话不是没说", scr2a="是", scr2b="送不到了",
      audio="raw/youchai_audio.wav", show="youchai_show.mp4", s0=53, showd=28, grade="g-warm", tint="red",
      img="img_letter.mp4", narr=["s5_1","s5_2","s5_3"], tr="tr5"),
 dict(key="s4", no="4", name="给自己的情书", year="2000", album="《寓言》", credit="词 · 林夕　唱 · 王菲　曲 · 江志仁",
      tag="自爱", scr1="最好的情书", scr2a="有时是", scr2b="写给自己的", namesm=True,
      audio="raw/qingshu_audio.wav", show="qingshu_show.mp4", s0=116, showd=25, grade="g-warm", tint="warm",
      img="img_room.mp4", narr=["s4_1","s4_2","s4_3"], tr="tr4"),
 dict(key="s3", no="3", name="百年孤寂", year="1999", album="《只爱陌生人》", credit="词 · 林夕　唱 · 王菲　曲 · 江志仁／陈伟文",
      tag="孤寂", scr1="最深的孤独不是没人爱", scr2a="是放不下", scr2b="执念里的自己",
      audio="raw/bainian_audio.wav", show="bainian_show.mp4", s0=93, showd=28, grade="g-cool", tint="blue",
      img="img_temple.mp4", narr=["s3_1","s3_2","s3_3"], tr="tr3"),
 dict(key="s2", no="2", name="开到荼蘼", year="1999", album="《只爱陌生人》", credit="词 · 林夕　唱 · 王菲　曲 · 江志仁",
      tag="盛放", scr1="花开到最盛", scr2a="也就离", scr2b="结束最近",
      audio="raw/kaidao_audio.wav", show="kaidao_show.mp4", s0=89, showd=28, grade="g-warm", tint="red",
      img="img_neon.mp4", narr=["s2_1","s2_2","s2_3"], tr="tr2"),
 dict(key="s1", no="1", name="彼岸花", year="2000", album="《寓言》", credit="词 · 林夕　唱 · 王菲　曲 · 王菲",
      tag="彼岸", scr1="别人唱情歌", scr2a="王菲唱", scr2b="情歌之后的世界",
      audio="raw/bianhua_audio.wav", show="bianhua_show.mp4", s0=149, showd=30, grade="g-cool", tint="red",
      img="img_lycoris.mp4", narr=["s1_1","s1_2","s1_3","s1_4","s1_5"], tr=None),
]

# ============================================================
# 1) 计算每块时长 + 块内锚点
# ============================================================
def song_layout(s):
    a = {}
    a["ramp"]=RAMP
    cur = RAMP + 0.1
    lines=[]
    for k in s["narr"]:
        lines.append((k, round(cur,3)))
        cur += D[k] + GAP
    a["lines"]=lines
    last_end = cur - GAP
    a["sw0"]=round(last_end+POST,3)
    a["show_start"]=round(a["sw0"]+SWELL,3)
    a["show_end"]=round(a["show_start"]+s["showd"],3)
    if s["tr"]:
        a["tr_voice"]=round(a["show_end"]+0.3,3)
        a["tr_end"]=round(a["tr_voice"]+D[s["tr"]],3)
        a["block_end"]=round(a["tr_end"]+0.9,3)
    else:
        a["block_end"]=round(a["show_end"]+1.8,3)
    a["mo"]=round(s["s0"]-a["show_start"],3)   # music offset into _audio.wav
    assert a["mo"]>=0, f'{s["key"]} mo<0'
    return a

# intro layout (cover + opening), reuse sample timing
IN = ["in1","in2","in3","in4","in5","in6"]
def intro_layout():
    a={}; cur=5.8
    gaps=[0.9,0.8,0.55,0.7,1.5,1.3]
    L=[]
    for k,g in zip(IN,gaps):
        L.append((k,round(cur,3))); cur+=D[k]+g
    a["lines"]=L; a["cover"]=5.0; a["end"]=round(cur+0.4,3)
    return a

# outro layout
OT=["ot1","ot2","ot3","ot4","ot5","ot6"]
def outro_layout():
    a={}; cur=1.2; gaps=[0.7,0.6,0.9,0.7,1.3,1.0]; L=[]
    for k,g in zip(OT,gaps):
        L.append((k,round(cur,3))); cur+=D[k]+g
    a["lines"]=L; a["end"]=round(cur+1.6,3)
    return a

IL = intro_layout(); OL = outro_layout()
LAY = {s["key"]: song_layout(s) for s in SONGS}

BLOCKS = ["intro"]+[s["key"] for s in SONGS]+["outro"]
BDUR = {"intro": IL["end"], "outro": OL["end"]}
for s in SONGS: BDUR[s["key"]] = LAY[s["key"]]["block_end"]
TOTAL = round(sum(BDUR[b] for b in BLOCKS),3)
print("block durations:", {b: BDUR[b] for b in BLOCKS})
print(f"TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ============================================================
# 2) 音频：每块 seg wav（staged voice+music+mix）→ master.wav
# ============================================================
AF = "audio_full"
SEGD = Path("build/segs_full"); SEGD.mkdir(parents=True, exist_ok=True)

def build_seg(out, music, mo, length, ve, lines, ln_loud=True):
    """lines = [(key, start_sec), ...] from AF/<key>.wav ; music = path ; mo = trim offset."""
    voice_wav = str(SEGD/"_voice.wav"); music_wav = str(SEGD/"_music.wav")
    # voice
    vin = sum([["-i", f"{AF}/{k}.wav"] for k,_ in lines], [])
    vfc=[]; labs=[]
    for i,(k,st) in enumerate(lines):
        ms=int(round(st*1000))
        vfc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,adelay={ms}|{ms}[a{i}]")
        labs.append(f"[a{i}]")
    vfc.append(f"{''.join(labs)}amix=inputs={len(lines)}:normalize=0:duration=longest[v]")
    run(["ffmpeg","-v","error",*vin,"-filter_complex",";".join(vfc),"-map","[v]","-ac","2","-ar","48000",voice_wav,"-y"])
    # music
    ln = "loudnorm=I=-14:TP=-1.0:LRA=11," if ln_loud else ""
    run(["ffmpeg","-v","error","-i",music,"-filter_complex",
         f"[0:a]atrim={mo}:{round(mo+length,3)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,{ln}volume='{ve}':eval=frame[m]",
         "-map","[m]","-ac","2","-ar","48000",music_wav,"-y"])
    # mix
    run(["ffmpeg","-v","error","-i",voice_wav,"-i",music_wav,"-filter_complex",
         f"[0:a][1:a]amix=inputs=2:normalize=0:duration=longest,atrim=0:{length},alimiter=limit=0.95[o]",
         "-map","[o]","-ac","2","-ar","48000",out,"-y"])

# intro
e=IL["end"]
intro_ve=(f"(lt(t,1.5))*({B}*t/1.5)+(between(t,1.5,{round(e-2.0,3)}))*{B}"
          f"+(gte(t,{round(e-2.0,3)}))*max(0,{B}-{B}*(t-{round(e-2.0,3)})/2.0)")
build_seg(str(SEGD/"seg_intro.wav"), "raw/renjian_full.wav", 8.0, e, intro_ve, IL["lines"])
print("seg_intro", dur(SEGD/"seg_intro.wav"))

# songs
for s in SONGS:
    a=LAY[s["key"]]; be=a["block_end"]; sw0=a["sw0"]; ss=a["show_start"]; se=a["show_end"]
    if s["tr"]:
        f1=round(se+1.2,3)
        ve=(f"(lt(t,{RAMP}))*({B}*t/{RAMP})+(between(t,{RAMP},{sw0}))*{B}"
            f"+(between(t,{sw0},{ss}))*({B}+({Fmus}-{B})*(t-{sw0})/{SWELL})"
            f"+(between(t,{ss},{se}))*{Fmus}"
            f"+(between(t,{se},{f1}))*({Fmus}+({TRLOW}-{Fmus})*(t-{se})/1.2)"
            f"+(between(t,{f1},{round(be-0.5,3)}))*{TRLOW}"
            f"+(gte(t,{round(be-0.5,3)}))*max(0,{TRLOW}-{TRLOW}*(t-{round(be-0.5,3)})/0.5)")
        lines=[(k,st) for k,st in a["lines"]]+[(s["tr"], a["tr_voice"])]
    else:
        ve=(f"(lt(t,{RAMP}))*({B}*t/{RAMP})+(between(t,{RAMP},{sw0}))*{B}"
            f"+(between(t,{sw0},{ss}))*({B}+({Fmus}-{B})*(t-{sw0})/{SWELL})"
            f"+(between(t,{ss},{se}))*{Fmus}"
            f"+(gte(t,{se}))*max(0,{Fmus}-{Fmus}*(t-{se})/{round(be-se,3)})")
        lines=[(k,st) for k,st in a["lines"]]
    build_seg(str(SEGD/f"seg_{s['key']}.wav"), s["audio"], a["mo"], be, (("("+ve+")*pow(10,%f/20)"%MGAIN[s["key"]]) if s["key"] in MGAIN else ve), lines)
    print("seg",s["key"], dur(SEGD/f"seg_{s['key']}.wav"))

# outro
eo=OL["end"]; B2=0.42
outro_ve=(f"(lt(t,1.2))*({B2}*t/1.2)+(between(t,1.2,{round(eo-2.5,3)}))*{B2}"
          f"+(gte(t,{round(eo-2.5,3)}))*max(0,{B2}-{B2}*(t-{round(eo-2.5,3)})/2.5)")
build_seg(str(SEGD/"seg_outro.wav"), "raw/renjian_full.wav", 170.0, eo, outro_ve, OL["lines"])
print("seg_outro", dur(SEGD/"seg_outro.wav"))

# concat → master.wav
seglist = SEGD/"list.txt"
seglist.write_text("".join(f"file 'seg_{b}.wav'\n" for b in BLOCKS), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(seglist),"-ac","2","-ar","48000","master_full.wav","-y"])
print("master_full.wav", dur("master_full.wav"), "planned", TOTAL)
shutil.copy("master_full.wav", str(HF/"master.wav"))
# per-block seg into hf_full/audio for per-block composition <audio>
for b in BLOCKS: shutil.copy(str(SEGD/f"seg_{b}.wav"), str(AUD/f"{b}.wav"))

# ============================================================
# 3) HTML：每块独立 HF 合成（≤4 video）
# ============================================================
GRAIN=("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E"
 "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E"
 "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.9'/%3E%3C/svg%3E")
TINTS={"red":"linear-gradient(180deg,rgba(140,30,36,.16) 0%,rgba(8,8,11,.0) 42%,rgba(8,8,11,.0) 60%,rgba(140,30,36,.10) 100%)",
       "blue":"linear-gradient(180deg,rgba(40,58,80,.20) 0%,rgba(8,8,11,.0) 45%,rgba(40,58,80,.12) 100%)",
       "warm":"linear-gradient(180deg,rgba(150,110,60,.16) 0%,rgba(8,8,11,.0) 45%,rgba(120,90,50,.10) 100%)"}

CSS = '''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08080b;font-family:"Noto Serif SC",serif;color:#ece4d6;-webkit-font-smoothing:antialiased;}
.foot{position:absolute;opacity:0;will-change:opacity,transform;}
.imgbg{inset:0;width:1080px;height:1920px;object-fit:cover;}
.show{left:0;width:1080px;height:auto;top:50%;transform:translateY(-50%);}
.g-warm{filter:saturate(.9) brightness(1.04) contrast(1.05) sepia(.05);}
.g-cool{filter:grayscale(.5) saturate(.7) brightness(1.0) contrast(1.1);}
.g-img{filter:saturate(.6) brightness(.5) contrast(1.08);}
.tintl{position:absolute;inset:0;z-index:3;pointer-events:none;opacity:0;mix-blend-mode:soft-light;}
.cinetop{position:absolute;top:0;left:0;right:0;height:660px;z-index:6;pointer-events:none;background:linear-gradient(180deg,rgba(8,8,11,.94) 0%,rgba(8,8,11,.55) 52%,rgba(8,8,11,0) 100%);}
.cinebot{position:absolute;bottom:0;left:0;right:0;height:720px;z-index:6;pointer-events:none;background:linear-gradient(0deg,rgba(8,8,11,.96) 0%,rgba(8,8,11,.62) 48%,rgba(8,8,11,0) 100%);}
.vignette{position:absolute;inset:0;z-index:7;pointer-events:none;background:radial-gradient(ellipse 78% 62% at 50% 46%,rgba(0,0,0,0) 38%,rgba(0,0,0,.5) 100%);}
.grain{position:absolute;inset:0;z-index:9;pointer-events:none;opacity:.09;mix-blend-mode:overlay;background-image:url("''' + "".join(GRAIN) + '''");background-size:220px 220px;}
.sub{position:absolute;left:90px;right:90px;bottom:300px;z-index:13;text-align:center;font-family:"Noto Serif SC",serif;font-weight:500;font-size:46px;line-height:1.5;color:rgba(236,228,214,.97);letter-spacing:.02em;opacity:0;text-shadow:0 2px 24px rgba(0,0,0,.85),0 1px 4px rgba(0,0,0,.9);}
.acc{color:#c0413f;}
.songcard{position:absolute;left:0;right:0;top:286px;z-index:15;text-align:center;opacity:0;}
.sc-no{font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:500;font-size:108px;line-height:.8;color:rgba(192,65,63,.92);letter-spacing:.02em;}
.sc-name{font-family:"Noto Serif SC",serif;font-weight:900;font-size:150px;line-height:1.0;color:#ece4d6;letter-spacing:.06em;margin:4px 0 24px;text-shadow:0 6px 50px rgba(0,0,0,.6);}
.sc-name.sm{font-size:104px;}
.sc-credit{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:30px;letter-spacing:.14em;color:rgba(236,228,214,.72);margin-bottom:14px;}
.sc-album{font-family:"JetBrains Mono",monospace;font-weight:400;font-size:24px;letter-spacing:.2em;color:rgba(91,110,128,.95);}
.corner{position:absolute;top:96px;left:64px;z-index:16;display:flex;align-items:center;gap:18px;opacity:0;}
.cn-no{font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:46px;color:#c0413f;}
.cn-line{width:46px;height:2px;background:rgba(236,228,214,.4);}
.cn-tag{font-family:"Noto Serif SC",serif;font-weight:700;font-size:40px;color:rgba(236,228,214,.92);letter-spacing:.14em;}
.screen2{position:absolute;left:80px;right:80px;top:430px;z-index:17;text-align:center;opacity:0;}
.sb-1{font-family:"Noto Serif SC",serif;font-weight:500;font-size:50px;color:rgba(236,228,214,.85);margin-bottom:18px;letter-spacing:.04em;}
.sb-2{font-family:"Noto Serif SC",serif;font-weight:700;font-size:66px;line-height:1.28;color:#ece4d6;letter-spacing:.02em;}
.transcard{position:absolute;left:0;right:0;top:0;bottom:0;z-index:18;opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.tc-bg{position:absolute;inset:0;z-index:-1;background:radial-gradient(ellipse 70% 50% at 50% 50%,rgba(140,30,36,.3) 0%,rgba(8,8,11,0) 60%);}
.tc-rule{width:60px;height:2px;background:#c0413f;margin:0 0 38px;opacity:.9;}
.tc-text{font-family:"Noto Serif SC",serif;font-weight:600;font-size:72px;line-height:1.36;text-align:center;color:#ece4d6;letter-spacing:.02em;padding:0 80px;}
/* 封面 */
.cover{position:absolute;inset:0;z-index:50;background:#08080b;overflow:hidden;}
.cv-veil{position:absolute;inset:0;z-index:1;background:radial-gradient(ellipse 90% 70% at 50% 38%,rgba(40,20,22,.5) 0%,rgba(8,8,11,.9) 62%,#08080b 100%);}
.cv-film{position:absolute;top:0;bottom:0;left:30px;width:46px;z-index:2;opacity:.5;background:repeating-linear-gradient(180deg,transparent 0 8px,rgba(236,228,214,.16) 8px 24px,transparent 24px 40px);}
.cv-flower{position:absolute;right:-120px;bottom:-140px;width:560px;height:560px;z-index:2;opacity:.5;background:radial-gradient(circle at 50% 50%,rgba(176,40,46,.55) 0%,rgba(120,20,26,.32) 26%,rgba(60,10,14,.12) 46%,transparent 62%);filter:blur(2px);}
.cv-col{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);z-index:5;display:flex;flex-direction:column;align-items:center;}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:30px;letter-spacing:.42em;color:rgba(192,65,63,.9);margin-bottom:34px;padding-left:.42em;}
.cv-pwrap{position:relative;width:470px;height:560px;margin-bottom:46px;}
.cv-vinyl{position:absolute;right:-66px;top:120px;width:300px;height:300px;border-radius:50%;z-index:1;background:radial-gradient(circle at 50% 50%,#b0282e 0 8%,#1a1216 9% 12%,#0e0c10 13% 100%);box-shadow:0 0 0 1px rgba(236,228,214,.1);opacity:.85;filter:brightness(.9);}
.cv-portrait{position:absolute;inset:0;z-index:2;border-radius:8px;background-image:url("cover_assets/faye_wide.jpg");background-size:cover;background-position:50% 38%;filter:grayscale(.85) contrast(1.16) brightness(1.05);border:1px solid rgba(236,228,214,.14);box-shadow:0 40px 90px rgba(0,0,0,.6);}
.cv-ptint{position:absolute;inset:0;z-index:3;border-radius:8px;mix-blend-mode:soft-light;background:linear-gradient(155deg,rgba(176,40,46,.42) 0%,rgba(8,8,11,0) 50%,rgba(70,90,110,.3) 100%);}
.cv-title{font-family:"Noto Serif SC",serif;font-weight:900;font-size:118px;line-height:1.06;text-align:center;color:#ece4d6;letter-spacing:.04em;text-shadow:0 8px 50px rgba(0,0,0,.55);}
.cv-title .acc{color:#c0413f;}
.cv-sub{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:42px;letter-spacing:.28em;color:rgba(236,228,214,.82);margin-top:34px;padding-left:.28em;border-top:1px solid rgba(236,228,214,.16);padding-top:30px;}
.opvinyl{position:absolute;inset:0;z-index:5;pointer-events:none;opacity:0;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 50%,rgba(8,8,11,.62) 0%,rgba(8,8,11,.2) 32%,rgba(8,8,11,0) 52%);}
.ov-disc{width:520px;height:520px;border-radius:50%;background:radial-gradient(circle at 50% 50%,#2a2530 0 5.5%,#7d1f24 5.5% 6.2%,#1e1a24 6.6% 9%,rgba(0,0,0,0) 9%),radial-gradient(circle at 40% 36%,rgba(236,228,214,.12) 0%,rgba(236,228,214,0) 46%),repeating-radial-gradient(circle at 50% 50%,rgba(236,228,214,.06) 0 1.4px,rgba(0,0,0,.18) 1.4px 6px),radial-gradient(circle at 50% 50%,#181420 0 100%);box-shadow:0 0 0 2px rgba(236,228,214,.10),inset 0 0 70px rgba(0,0,0,.55);opacity:.5;}
.screen{position:absolute;left:80px;right:80px;top:560px;z-index:14;text-align:center;opacity:0;}
.sa-1{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:40px;letter-spacing:.06em;color:rgba(236,228,214,.5);margin-bottom:26px;text-decoration:line-through;text-decoration-color:rgba(180,55,59,.7);}
.sa-2{font-family:"Noto Serif SC",serif;font-weight:700;font-size:62px;line-height:1.34;color:#ece4d6;}
/* outro */
.otblk{position:absolute;left:0;right:0;top:0;bottom:0;z-index:18;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;}
.ot-bg{position:absolute;inset:0;z-index:-1;background:radial-gradient(ellipse 80% 55% at 50% 50%,rgba(140,30,36,.26) 0%,rgba(8,8,11,0) 62%);}
.ot-rule{width:60px;height:2px;background:#c0413f;margin:0 0 36px;opacity:.9;}
.ot-1{font-family:"Noto Serif SC",serif;font-weight:500;font-size:52px;color:rgba(236,228,214,.86);margin-bottom:18px;letter-spacing:.04em;text-align:center;}
.ot-2{font-family:"Noto Serif SC",serif;font-weight:800;font-size:78px;line-height:1.3;color:#ece4d6;text-align:center;letter-spacing:.02em;}
.ot-cta{position:absolute;left:90px;right:90px;bottom:210px;z-index:19;text-align:center;font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:38px;line-height:1.5;color:rgba(236,228,214,.92);letter-spacing:.04em;opacity:0;text-shadow:0 2px 20px rgba(0,0,0,.8);}
'''

HEAD = '''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@400;500;600;700&family=Cormorant+Garamond:ital,wght@1,400;1,500;1,600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>__CSS__</style></head><body>'''

def comp(cid, dur, body, js):
    return (HEAD.replace("__CSS__",CSS) +
      f'<div id="root" data-composition-id="{cid}" data-start="0" data-duration="{f(dur)}" data-width="1080" data-height="1920">\n'
      f'{body}\n'
      f'<div class="cinetop"></div><div class="cinebot"></div><div class="vignette"></div><div class="grain"></div>\n'
      f'<audio id="aud" data-start="0" data-duration="{f(dur)}" data-track-index="3" src="audio/{cid}.wav" data-volume="1"></audio>\n'
      f'</div>\n<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});\n'
      f'{js}\ntl.fromTo("#root>.grain",{{opacity:.07}},{{opacity:.12,duration:2.2,yoyo:true,repeat:{max(0,int(dur/2.2)-1)},ease:"sine.inOut"}},0);\n'
      f'window.__timelines["{cid}"]=tl;</script></body></html>')

def sub_js(lines):
    js=""
    for k,st in lines:
        d=D[k]
        js+=(f'tl.fromTo("#sub_{k}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.45,ease:"power2.out"}},{f(st)});'
             f'tl.to("#sub_{k}",{{opacity:0,y:-8,duration:0.45,ease:"power1.in"}},{f(st+d+0.05)});'
             f'tl.set("#sub_{k}",{{opacity:0}},{f(st+d+0.5)});\n')
    return js
def sub_html(lines, subsmap):
    return "\n".join(f'<div id="sub_{k}" class="sub clip" data-start="{f(st)}" data-duration="{f(D[k]+0.5)}" data-track-index="12">{subsmap[k]}</div>' for k,st in lines)

# JS helpers (%-format to avoid f-string brace escaping; auto-quote GSAP ease values)
import re as _re
def _qe(s): return _re.sub(r'ease:([A-Za-z][A-Za-z0-9.]*)', r'ease:"\1"', s)
def TW(el,a,b,at): return 'tl.fromTo("%s",{%s},{%s},%s);\n'%(el,_qe(a),_qe(b),f(at))
def TO(el,b,at):   return 'tl.to("%s",{%s},%s);\n'%(el,_qe(b),f(at))
def TS(el,b,at):   return 'tl.set("%s",{%s},%s);\n'%(el,_qe(b),f(at))

def song_html(s):
    a=LAY[s["key"]]; ss=a["show_start"]; se=a["show_end"]; be=a["block_end"]; k=s["key"]
    showvid=min(s["showd"]+3.5, 39.0)
    imgdur=round(ss+1.2,3)
    nm_cls="sc-name sm" if s.get("namesm") else "sc-name"
    subs={kk:None for kk,_ in a["lines"]}
    SUBMAP={
      "s10_1":"林夕写给王菲的第一层，是人间。","s10_2":"这首歌没有锋利的隐喻，<br>反而像一句很轻的祝福。","s10_3":"王菲一开口，那种疏离感忽然落地了。","s10_4":"她不是不食人间烟火，<br>她只是把人间唱得很远，也很温柔。","tr10":"但林夕真正厉害的地方，<br>是他写爱，从来不只写甜。",
      "s9_1":"《红豆》动人的不是爱得多热烈，","s9_2":"而是还没来得及失去，<br>就已经开始怀念。","s9_3":"明明一切都还在发生，<br>歌词里却已经有了时间的回声。","tr9":"到了《约定》，怀念不再是遗憾，<br>而变成了时间的考验。",
      "s8_1":"《约定》写的不是我爱你，<br>而是多年以后你还认不认得我。","s8_2":"林夕把承诺写得很轻，<br>却把时间写得很重。","s8_3":"她不用把情绪唱满，<br>反而让空出来的地方长出回忆。","tr8":"如果《约定》还有温度，<br>那从下一首开始，情绪潜到了水面以下。",
      "s7_1":"《暗涌》最典型的气质：<br>不解释，不崩溃，不喊痛。","s7_2":"所有情绪，都在水面以下。","s7_3":"不是失恋现场，<br>是早已预感到结局，却还安静站着。","tr7":"暗涌之后，爱不再只是两个人的事，<br>它开始变成命运。",
      "s6_1":"《流年》把一次相遇，<br>写成了一种命。","s6_2":"不是普通情歌，<br>而是回头看才知道被改变的节点。","s6_3":"她不像在回忆一个人，<br>更像在回忆命运拐弯的那一秒。","tr6":"可命运不是每次都有回应。<br>有些信，寄出去时就已经迟了。",
      "s5_1":"《邮差》写的不是我还爱你，<br>而是有些东西，送不到了。","s5_2":"林夕把错过写得特别体面，<br>没有哭喊，也没有责怪。","s5_3":"只剩一封过期的信，<br>和一个不再追问答案的人。","tr5":"到了这里，王菲开始从爱情里退出来，<br>转身，看自己。",
      "s4_1":"《给自己的情书》，<br>写给每个在爱情里清醒的人。","s4_2":"它没有把自爱写成口号。","s4_3":"最该学会的，不是等谁来爱你，<br>而是失去之后把自己郑重收回来。","tr4":"但封神不止于自爱。<br>再往后，他们写孤独，写空，写放下执念。",
      "s3_1":"《百年孤寂》，<br>不是普通的孤独。","s3_2":"困住自己的不是对方，<br>而是自己。","s3_3":"你越想抓住什么，<br>越发现世界空得只剩回音。","tr3":"如果《百年孤寂》是被困住，<br>《开到荼蘼》就是盛放之后的坍塌。",
      "s2_1":"《开到荼蘼》，<br>是这十首里最有末世感的一首。","s2_2":"写的不是花开，而是开到尽头。<br>越华丽，越接近荒凉。","s2_3":"不再只是冷，<br>而是旁观繁华崩塌的清醒。","tr2":"所以最后一首，必须走到彼岸。<br>写到最后，已经不只是爱，而是无常。",
      "s1_1":"把《彼岸花》放在第一，<br>不只因为它好听，","s1_2":"而是它最能说明：<br>林夕写到最后，已不只是写爱情。","s1_3":"他写轮回，写无常，<br>写人在欲望里来回，最后学会放下。","s1_4":"王菲唱这首歌，<br>像站在岸边看自己，也看众生。","s1_5":"别人唱情歌，<br>她唱的是情歌之后的世界。",
    }
    body=[]
    body.append(f'<video id="img_{k}" class="foot imgbg g-img clip" data-start="0" data-duration="{f(imgdur)}" data-track-index="0" src="clips_seg/{s["img"]}" muted playsinline preload="auto"></video>')
    body.append(f'<video id="show_{k}" class="foot show {s["grade"]} clip" data-start="{f(ss)}" data-duration="{f(showvid)}" data-track-index="1" src="clips_seg/{s["show"]}" muted playsinline preload="auto"></video>')
    body.append(f'<div id="tint_{k}" class="tintl clip" style="background:{TINTS[s["tint"]]}" data-start="{f(ss)}" data-duration="{f(showvid)}" data-track-index="8"></div>')
    body.append(f'<div id="card_{k}" class="songcard clip" data-start="0.4" data-duration="9.2" data-track-index="15"><div class="sc-no">{s["no"]}</div><div class="{nm_cls}">{s["name"]}</div><div class="sc-credit">{s["credit"]}</div><div class="sc-album">{s["year"]} ·{s["album"]}</div></div>')
    tag_start=9.6; tag_dur=round(be-0.5-tag_start,3)
    body.append(f'<div id="tag_{k}" class="corner clip" data-start="{f(tag_start)}" data-duration="{f(tag_dur)}" data-track-index="16"><span class="cn-no">{s["no"]}</span><span class="cn-line"></span><span class="cn-tag">{s["tag"]}</span></div>')
    sb_start=round(ss+1.5,3)
    body.append(f'<div id="scr_{k}" class="screen2 clip" data-start="{f(sb_start)}" data-duration="8.6" data-track-index="17"><div class="sb-1">{s["scr1"]}</div><div class="sb-2">{s["scr2a"]}<span class="acc">{s["scr2b"]}</span></div></div>')
    # subtitles
    sublines=list(a["lines"])
    if s["tr"]: sublines=sublines+[(s["tr"], a["tr_voice"])]
    for kk,st in sublines:
        body.append(f'<div id="sub_{kk}" class="sub clip" data-start="{f(st)}" data-duration="{f(D[kk]+0.5)}" data-track-index="12">{SUBMAP[kk]}</div>')
    # transition card
    if s["tr"]:
        tcs=round(se-0.2,3)
        body.append(f'<div id="trans_{k}" class="transcard clip" data-start="{f(tcs)}" data-duration="{f(be-tcs)}" data-track-index="18"><div class="tc-bg"></div><div class="tc-rule"></div><div class="tc-text">{SUBMAP[s["tr"]]}</div></div>')
    # JS
    js=""
    js+=TW(f"#img_{k}","opacity:0","opacity:1,duration:1.2,ease:power1.inOut",0)
    js+=TO(f"#img_{k}","opacity:0,duration:1.2,ease:power1.in",round(imgdur-1.2,3))
    js+=TS(f"#img_{k}","opacity:0",imgdur)
    js+='tl.fromTo("#img_%s",{scale:1.07},{scale:1.0,duration:%s,ease:"none"},0);\n'%(k,f(imgdur))
    js+=TW(f"#show_{k}","opacity:0","opacity:1,duration:0.9,ease:power1.inOut",ss)
    js+=TO(f"#show_{k}","opacity:0,duration:1.5,ease:power1.in",round(ss+showvid-1.5,3))
    js+=TS(f"#show_{k}","opacity:0",round(ss+showvid,3))
    js+='tl.fromTo("#show_%s",{scale:1.05},{scale:1.0,duration:%s,ease:"none"},%s);\n'%(k,f(showvid),f(ss))
    js+=TW(f"#tint_{k}","opacity:0","opacity:1,duration:1.2",ss)
    js+=TO(f"#tint_{k}","opacity:0,duration:1.2",round(ss+showvid-1.2,3)); js+=TS(f"#tint_{k}","opacity:0",round(ss+showvid,3))
    js+=TW(f"#card_{k}","opacity:0,y:18","opacity:1,y:0,duration:0.8,ease:power2.out",0.5)
    js+='tl.fromTo("#card_%s .sc-name",{letterSpacing:"0.22em",opacity:0},{letterSpacing:"0.06em",opacity:1,duration:1.0,ease:"power3.out"},0.7);\n'%k
    js+=TO(f"#card_{k}","opacity:0,y:-12,duration:0.7,ease:power2.in",8.8); js+=TS(f"#card_{k}","opacity:0",9.6)
    js+=TW(f"#tag_{k}","opacity:0,x:-14","opacity:1,x:0,duration:0.7,ease:power2.out",tag_start)
    js+=TO(f"#tag_{k}","opacity:0,duration:0.7",round(be-0.6,3)); js+=TS(f"#tag_{k}","opacity:0",round(be-0.3,3))
    js+=TW(f"#scr_{k}","opacity:0,y:16","opacity:1,y:0,duration:0.8,ease:power2.out",sb_start)
    js+=TO(f"#scr_{k}","opacity:0,y:-10,duration:0.9,ease:power1.in",round(sb_start+7.0,3)); js+=TS(f"#scr_{k}","opacity:0",round(sb_start+8.6,3))
    js+=sub_js(sublines)
    if s["tr"]:
        tcs=round(se-0.2,3)
        js+=TW(f"#trans_{k}","opacity:0,y:18","opacity:1,y:0,duration:0.7,ease:power2.out",round(tcs+0.1,3))
        js+=TO(f"#trans_{k}","opacity:1,duration:0.1",round(be-0.25,3))
    return comp(k, be, "\n".join(body), js)

def sub_js2(lines):  # alias used above
    return sub_js(lines)

def intro_html():
    e=IL["end"]
    SUB={"in1":"王菲，当然有很多好歌。","in2":"但有一种王菲，<br>是林夕写出来的。","in3":"他写给她的，不只是爱情；","in4":"还有孤独，还有放下，还有无常。","in5":"还有一个人走到世界尽头以后，<br>仍然不解释自己的样子。","in6":"今天这十首，不只听旋律，<br>更听林夕怎么把王菲写成传奇。"}
    body=[]
    body.append('<video id="city" class="foot imgbg g-city clip" data-start="4.5" data-duration="25.5" data-track-index="0" src="clips_seg/city.mp4" muted playsinline preload="auto"></video>')
    body.append('<video id="fopen" class="foot show g-cool clip" data-start="26.0" data-duration="%s" data-track-index="1" src="clips_seg/faye_open.mp4" muted playsinline preload="auto"></video>'%f(e-26.0))
    body.append('<div id="opvinyl" class="opvinyl clip" data-start="13.0" data-duration="13.5" data-track-index="8"><div class="ov-disc"></div></div>')
    body.append('<div id="screenA" class="screen clip" data-start="26.0" data-duration="5.6" data-track-index="14"><div class="sa-1">不是王菲热门歌单</div><div class="sa-2">是林夕写给王菲的<span class="acc">精神地图</span></div></div>')
    for kk,st in IL["lines"]:
        body.append('<div id="sub_%s" class="sub clip" data-start="%s" data-duration="%s" data-track-index="12">%s</div>'%(kk,f(st),f(D[kk]+0.5),SUB[kk]))
    body.append('<div id="cover" class="cover clip" data-start="0" data-duration="5.0" data-track-index="40"><div class="cv-veil"></div><div class="cv-film"></div><div class="cv-flower"></div><div class="cv-col"><div class="cv-eyebrow">词 · 林夕　／　唱 · 王菲</div><div class="cv-pwrap"><div class="cv-vinyl"></div><div class="cv-portrait"></div><div class="cv-ptint"></div></div><h1 class="cv-title">林夕把王菲<br><span class="acc">写成了神</span></h1><div class="cv-sub">10 首封神词作盘点</div></div></div>')
    js=""
    js+=TS("#cover","opacity:1",0)
    js+=TS(".cv-col,.cv-portrait,.cv-title,.cv-sub,.cv-eyebrow,.cv-flower,.cv-vinyl","opacity:1",0)
    js+='tl.fromTo(".cv-portrait",{scale:1.0},{scale:1.03,duration:4.0,ease:"sine.inOut"},0.6);\n'
    js+=TO("#cover","opacity:0,duration:0.7,ease:power2.in",4.3); js+=TS("#cover","opacity:0",5.0)
    js+=TW("#city","opacity:0","opacity:1,duration:1.3,ease:power1.inOut",4.5)
    js+=TO("#city","opacity:0,duration:1.8,ease:power1.in",28.2); js+=TS("#city","opacity:0",30.0)
    js+='tl.fromTo("#city",{scale:1.06},{scale:1.0,duration:25.5,ease:"none"},4.5);\n'
    js+=TW("#opvinyl","opacity:0","opacity:1,duration:1.5,ease:power1.inOut",13.0)
    js+=TO("#opvinyl","opacity:0,duration:1.8,ease:power1.in",24.7); js+=TS("#opvinyl","opacity:0",26.5)
    js+='tl.fromTo(".ov-disc",{rotation:0},{rotation:150,duration:13.5,ease:"none"},13.0);\n'
    js+=TW("#fopen","opacity:0","opacity:1,duration:1.8,ease:power1.inOut",26.0)
    js+=TO("#fopen","opacity:0,duration:1.5,ease:power1.in",round(e-1.5,3)); js+=TS("#fopen","opacity:0",e)
    js+='tl.fromTo("#fopen",{scale:1.05},{scale:1.0,duration:%s,ease:"none"},26.0);\n'%f(e-26.0)
    js+=TW("#screenA","opacity:0,y:14","opacity:1,y:0,duration:0.6,ease:power2.out",26.0)
    js+=TO("#screenA","opacity:0,y:-10,duration:0.7,ease:power1.in",30.4); js+=TS("#screenA","opacity:0",31.6)
    js+=sub_js(IL["lines"])
    return comp("intro", e, "\n".join(body), js)

def outro_html():
    e=OL["end"]
    SUB={"ot1":"林夕给王菲写过很多歌。<br>有些写爱，有些写孤独，有些写放下。","ot2":"但他好像一直在替王菲，<br>搭一座桥：","ot3":"从人间，到暗涌；从执念，到空；<br>最后，走到彼岸。","ot4":"王菲最迷人的地方，<br>从来不只是声音。","ot5":"而是林夕给了她一套语言，<br>她又把它唱成了自己的命。","ot6":"你心里，林夕写给王菲<br>最封神的一首，是哪一首？"}
    body=[]
    body.append('<video id="obg" class="foot show g-dim clip" data-start="0" data-duration="%s" data-track-index="1" src="clips_seg/bianhua_show.mp4" muted playsinline preload="auto"></video>'%f(min(e,39.0)))
    body.append('<div class="otblk clip" id="otext" data-start="0" data-duration="%s" data-track-index="17"><div class="ot-bg"></div><div class="ot-rule"></div><div class="ot-1">林夕给了王菲语言</div><div class="ot-2">王菲把它<span class="acc">唱成命</span></div></div>'%f(e))
    for kk,st in OL["lines"]:
        body.append('<div id="sub_%s" class="sub clip" data-start="%s" data-duration="%s" data-track-index="12">%s</div>'%(kk,f(st),f(D[kk]+0.5),SUB[kk]))
    cta_at=round(OL["lines"][-1][1],3)
    body.append('<div id="cta" class="ot-cta clip" data-start="%s" data-duration="%s" data-track-index="19">《红豆》《暗涌》，还是《彼岸花》？</div>'%(f(cta_at),f(e-cta_at)))
    js=""
    js+=TW("#obg","opacity:0","opacity:0.6,duration:2.0,ease:power1.inOut",0)
    js+=TO("#obg","opacity:0,duration:2.0,ease:power1.in",round(min(e,39.0)-2.0,3)); js+=TS("#obg","opacity:0",round(min(e,39.0),3))
    js+='tl.fromTo("#obg",{scale:1.06},{scale:1.0,duration:%s,ease:"none"},0);\n'%f(min(e,39.0))
    # otext block holds; animate inner
    js+=TS("#otext","opacity:1",0)
    js+=TW(".ot-1","opacity:0,y:14","opacity:1,y:0,duration:1.0,ease:power2.out",round(e-9.0,3))
    js+=TW(".ot-2","opacity:0,y:18","opacity:1,y:0,duration:1.1,ease:power3.out",round(e-7.6,3))
    js+=TS(".ot-rule","opacity:1",0)
    js+=TW("#cta","opacity:0,y:10","opacity:0.95,y:0,duration:0.7,ease:power2.out",cta_at)
    js+=sub_js(OL["lines"])
    # hide ot text early (before narration ot4/5 about it) then show at end — simpler: keep hidden until e-9
    js=js.replace('tl.set("#otext",{opacity:1},0.0);','tl.set("#otext",{opacity:1},0.0);\ntl.set(".ot-1,.ot-2",{opacity:0},0);\n')
    return comp("outro", e, "\n".join(body), js)

# ============================================================
# 4) 写出各块 HTML + 项目文件 + blocks.json
# ============================================================
for fn in ["package.json","hyperframes.json"]:
    src=Path("hf")/fn
    if src.exists(): shutil.copy(str(src), str(HF/fn))
(HF/"intro.html").write_text(intro_html(), encoding="utf-8")
for s in SONGS:
    (HF/f'{s["key"]}.html').write_text(song_html(s), encoding="utf-8")
(HF/"outro.html").write_text(outro_html(), encoding="utf-8")
(HF/"index.html").write_text(intro_html(), encoding="utf-8")  # default
Path("hf_full/blocks.json").write_text(json.dumps({"blocks":BLOCKS,"durs":BDUR,"total":TOTAL}, ensure_ascii=False, indent=1), encoding="utf-8")
print("WROTE", len(BLOCKS), "block compositions ; TOTAL", TOTAL)
