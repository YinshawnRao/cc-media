#!/usr/bin/env python3
"""孙燕姿毕业季叙事盘点（走出考场那一刻·请打开孙燕姿，5首叙事序）。
结构：封面(纯情绪) → 标题 → 5×(转场卡 + 章节letterbox) → 结尾/CTA。
情绪线：释然→回望→告别→怅惘→出发。色温弧：暖白柔光→sepia怀旧→暖橙黄昏→冷蓝夜→金亮逆光。
女声 zf_xiaoyi。无开头长钩子（封面+标题后~7.6s进第一首，节奏常量照搬五月天毕业季）。
渲染后必须 ffmpeg mux master.wav（HyperFrames 会压平动态）。
SAMPLE=1 只构建前两首（样片）。
"""
import subprocess, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT/"audio"; C = ROOT/"clips"; HF = ROOT/"hf"; SEG = ROOT/"build"/"segs"
SEG.mkdir(parents=True, exist_ok=True)
SAMPLE = bool(os.environ.get("SAMPLE"))
BED_SRC = A/"dongye_studio.wav"   # 当冬夜渐暖 录音室原声，做开场/结尾干净铺底

def adur(p):
    return round(float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)])),3)
def run(cmd): subprocess.run([str(c) for c in cmd], check=True)
def f(x): return f"{round(x,3)}"

# ---------------- 节奏常量（与五月天毕业季一致，硬约束）----------------
TRANS=3.8; LEADV=0.5; POST=1.3; SWELL=1.6; TAIL=1.5; BED=0.15; TBED=0.24
COVER_D=3.4; TITLE_T=3.2; TITLE_D=4.6

# ---------------- 每首歌定义 ----------------
SONGS = [
 dict(key="dongye", no="01", name="当冬夜渐暖", emo="释然", year="2011", album="是时候",
      clip="vert_dongye", show=32.0, ghost="暖", acc="#F0C674", mgain=1.12,
      subline="冬夜会过去，你也该歇一歇了",
      trans=["第一首，不是庆祝","是终于可以","松一口气"],
      src="官方签售会 Live · 《是时候》",
      tint="linear-gradient(180deg,rgba(255,250,235,.16) 0%,rgba(255,250,235,0) 26%,rgba(40,32,20,.06) 60%,rgba(22,16,8,.60) 100%)",
      ttop="linear-gradient(180deg,rgba(18,13,6,.42) 0%,rgba(18,13,6,0) 24%)",
      ghostcol="rgba(255,248,228,.17)"),
 dict(key="huainian", no="02", name="我怀念的", emo="回望", year="2007", album="逆光",
      clip="vert_huainian", show=32.0, ghost="念", acc="#E8964C", mgain=1.05,
      subline="我怀念的，是那个再也回不去的夏天",
      trans=["考完才发现","最怀念的","是那些回不去的普通日子"],
      src="官方 4K MV · Timeless Music",
      tint="linear-gradient(180deg,rgba(228,150,76,.22) 0%,rgba(150,95,45,.10) 32%,rgba(55,32,16,.34) 64%,rgba(26,15,7,.74) 100%)",
      ttop="linear-gradient(180deg,rgba(12,8,4,.50) 0%,rgba(12,8,4,0) 26%)",
      ghostcol="rgba(232,150,76,.20)"),
 dict(key="yujian", no="03", name="遇见", emo="告别", year="2003", album="The Moment",
      clip="vert_yujian", show=34.0, ghost="遇", acc="#F2B23E", mgain=1.05,
      subline="谢谢你，出现在我的青春里",
      trans=["有些遇见","不是为了永远","是为了陪你走过那一段"],
      src="官方 4K MV · Timeless Music",
      tint="linear-gradient(180deg,rgba(28,22,30,.42) 0%,rgba(242,178,62,.10) 42%,rgba(62,42,16,.40) 74%,rgba(14,10,6,.80) 100%)",
      ttop="linear-gradient(180deg,rgba(10,8,12,.55) 0%,rgba(10,8,12,0) 26%)",
      ghostcol="rgba(242,178,62,.20)"),
 dict(key="tianheihei", no="04", name="天黑黑", emo="怅惘", year="2000", album="孙燕姿",
      clip="vert_tianheihei", show=32.0, ghost="夜", acc="#7FB0D6", mgain=1.00,
      subline="天黑也没关系，迷路也算在长大",
      trans=["未来终于来了","可它好像","也没那么容易回答"],
      src="官方 4K MV · Timeless Music",
      tint="linear-gradient(180deg,rgba(45,78,118,.34) 0%,rgba(22,38,62,.30) 40%,rgba(10,18,34,.58) 74%,rgba(4,8,18,.82) 100%)",
      ttop="linear-gradient(180deg,rgba(6,10,20,.55) 0%,rgba(6,10,20,0) 26%)",
      ghostcol="rgba(150,185,220,.20)"),
 dict(key="niguang", no="05", name="逆光", emo="出发", year="2007", album="逆光",
      clip="vert_niguang", show=42.0, ghost="光", acc="#F5D27A", mgain=1.15,
      subline="前路很远，但你已经开始了",
      trans=["最后一首","不是说别怕","是带着怕，也继续往前"],
      src="官方 4K MV · Timeless Music",
      tint="linear-gradient(180deg,rgba(255,242,210,.22) 0%,rgba(255,228,175,.06) 32%,rgba(120,90,50,.12) 64%,rgba(40,28,14,.55) 100%)",
      ttop="linear-gradient(180deg,rgba(16,12,6,.40) 0%,rgba(16,12,6,0) 24%)",
      ghostcol="rgba(245,210,122,.20)"),
]
if SAMPLE:
    SONGS = SONGS[:2]
    print("*** SAMPLE MODE: songs 1-2 only ***")

# voice durations (s1..sN)
for i,s in enumerate(SONGS): s["voice"] = adur(A/f"s{i+1}_voice.wav")
OUTRO_V = adur(A/"outro.wav")

def chap_anchors(s):
    voice_at = TRANS + LEADV
    v1   = voice_at + s["voice"]
    sw0  = v1 + POST
    full0= sw0 + SWELL
    full1= full0 + s["show"]
    dur  = full1 + TAIL
    return dict(voice_at=voice_at, v1=v1, sw0=sw0, full0=full0, full1=full1, dur=round(dur,3))

# ---------------- 绝对时间轴 ----------------
CH1 = round(TITLE_T + TITLE_D - 0.2, 3)
starts = {}
t = CH1
for s in SONGS:
    a = chap_anchors(s); s["anchor"]=a
    starts[s["key"]] = t; s["start"]=t; s["end"]=round(t+a["dur"],3)
    t = s["end"]
OUTRO_T = round(t, 3)
OUTRO_D = round(0.4 + OUTRO_V + 5.0, 3)
TOTAL = round(OUTRO_T + OUTRO_D, 3)
print("chapter starts:", {s["key"]:(s["start"],s["end"]) for s in SONGS})
print(f"OUTRO {OUTRO_T}-{TOTAL}  TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# =====================================================================
#  AUDIO
# =====================================================================
def build_open():
    dur = CH1
    ve = (f"(lt(t,1.4))*({0.10}*t/1.4)+(between(t,1.4,{TITLE_T}))*0.10"
          f"+(between(t,{TITLE_T},{TITLE_T+2.0}))*(0.10+0.10*(t-{TITLE_T})/2.0)+(gte(t,{TITLE_T+2.0}))*0.20")
    run(["ffmpeg","-v","error","-i",BED_SRC,"-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
         f"atrim=0:{dur},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,"
         f"afade=t=in:st=0:d=1.0,afade=t=out:st={dur-0.7}:d=0.7[out]",
         "-map","[out]","-ac","2","-ar","48000",SEG/"seg_open.wav","-y"])

def build_chapter_seg(i, s):
    a=s["anchor"]; dur=a["dur"]; va=a["voice_at"]; sw0=a["sw0"]; full0=a["full0"]; full1=a["full1"]
    ve=(f"(lt(t,1.0))*({TBED}*t/1.0)"
        f"+(between(t,1.0,{TRANS}))*{TBED}"
        f"+(between(t,{TRANS},{va}))*({TBED}+({BED}-{TBED})*(t-{TRANS})/{va-TRANS})"
        f"+(between(t,{va},{sw0}))*{BED}"
        f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
        f"+(gte(t,{full0}))*1.0")
    out=SEG/f"seg_{s['key']}.wav"
    run(["ffmpeg","-v","error","-i",C/f"{s['clip']}.mp4","-i",A/f"s{i+1}_voice.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{dur},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,volume={s['mgain']},afade=t=out:st={full1}:d={TAIL}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{dur},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])

def build_outro():
    dur=OUTRO_D; va=0.4
    run(["ffmpeg","-v","error","-i",BED_SRC,"-i",A/"outro.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
         f"atrim=0:{dur},asetpts=PTS-STARTPTS,volume=0.2,afade=t=in:st=0:d=1.2,afade=t=out:st={dur-2.5}:d=2.5[bed];"
         f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{dur},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",SEG/"seg_outro.wav","-y"])

build_open()
for i,s in enumerate(SONGS): print("audio",s["key"]); build_chapter_seg(i,s)
build_outro()

listfile = SEG/"list.txt"
names = ["seg_open.wav"]+[f"seg_{s['key']}.wav" for s in SONGS]+["seg_outro.wav"]
listfile.write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",listfile,"-ac","2","-ar","48000",ROOT/"master.wav","-y"])
print("master:", adur(ROOT/"master.wav"), "planned:", TOTAL)

# HF assets
HF.mkdir(exist_ok=True); (HF/"clips_seg").mkdir(exist_ok=True)
shutil.copy(ROOT/"master.wav", HF/"master.wav")
for s in SONGS:
    a=s["anchor"]
    run(["ffmpeg","-v","error","-i",C/f"{s['clip']}.mp4","-t",str(a["dur"]+0.4),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
         HF/"clips_seg"/f"{s['key']}.mp4","-y"])
print("clips_seg done")

# =====================================================================
#  HTML / CSS / JS  (CSS、转场/章节/封面/标题/结尾结构与五月天毕业季一致)
# =====================================================================
CSS = r'''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07060a;
  font-family:"Noto Serif SC",serif;color:#241d14;-webkit-font-smoothing:antialiased;}
.layer{position:absolute;inset:0;width:1080px;height:1920px;}
.grain{position:absolute;inset:0;pointer-events:none;mix-blend-mode:overlay;opacity:.5;
  background-image:radial-gradient(circle at 12% 22%,rgba(255,255,255,.05) 0 .5px,transparent .9px),
   radial-gradient(circle at 76% 64%,rgba(0,0,0,.05) 0 .5px,transparent .9px),
   radial-gradient(circle at 44% 88%,rgba(255,255,255,.04) 0 .4px,transparent .8px);
  background-size:200px 200px,240px 240px,170px 170px;}

/* ===== COVER ===== */
#cover{z-index:60;background:linear-gradient(168deg,#FBF6EA 0%,#F4ECDA 46%,#E7DAC2 100%);overflow:hidden;}
.cv-sun{position:absolute;top:-160px;right:-120px;width:760px;height:760px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,247,224,.95) 0%,rgba(255,240,200,.55) 32%,rgba(255,236,190,0) 66%);filter:blur(6px);}
.cv-haze{position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,250,235,0) 40%,rgba(255,247,228,.35) 100%);}
.cv-floor{position:absolute;left:0;right:0;bottom:0;height:430px;
  background:linear-gradient(180deg,rgba(206,190,160,0) 0%,rgba(196,178,146,.35) 60%,rgba(150,132,100,.42) 100%);}
.crowd{position:absolute;left:0;right:0;bottom:150px;height:300px;}
.fig{position:absolute;bottom:0;background:#6b5c44;filter:blur(.4px);}
.solo{position:absolute;left:118px;bottom:150px;width:128px;height:360px;z-index:2;}
.solo .body{position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:104px;height:300px;border-radius:34px 34px 0 0;
  background:linear-gradient(180deg,#5b4d39,#473a2a);filter:blur(.5px);}
.solo .head{position:absolute;bottom:296px;left:50%;transform:translateX(-50%);width:78px;height:80px;border-radius:50% 50% 48% 48%;background:#4f4231;}
.solo .hair{position:absolute;bottom:300px;left:50%;transform:translateX(-44%) rotate(8deg);width:120px;height:60px;border-radius:0 60% 40% 50%;
  background:linear-gradient(90deg,rgba(60,50,36,0),#3f3527 55%);opacity:.9;}
.ticket{position:absolute;left:64px;bottom:300px;width:330px;height:226px;transform:rotate(-6deg);
  background:linear-gradient(160deg,#fffdf7,#f3ead7);border-radius:10px;
  box-shadow:0 26px 50px rgba(90,70,40,.30),0 2px 0 rgba(255,255,255,.6) inset;padding:18px 20px;}
.ticket::after{content:"";position:absolute;inset:0;border-radius:10px;
  background:linear-gradient(110deg,rgba(255,255,255,.35) 0%,rgba(255,255,255,0) 30%,rgba(0,0,0,.05) 64%,rgba(255,255,255,.25) 100%);}
.tk-hd{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:800;letter-spacing:.42em;
  color:#b23b2e;border-bottom:2px solid rgba(178,59,46,.5);padding-bottom:8px;}
.tk-row{display:flex;gap:14px;margin-top:16px;}
.tk-photo{width:70px;height:88px;background:repeating-linear-gradient(135deg,#d8cdb4,#d8cdb4 6px,#cfc3a6 6px,#cfc3a6 12px);border:1px solid rgba(120,100,70,.4);border-radius:3px;}
.tk-lines{flex:1;display:flex;flex-direction:column;gap:12px;padding-top:6px;}
.tk-line{height:9px;border-radius:5px;background:rgba(120,100,70,.30);}
.tk-line.s{width:62%;}
.cv-text{position:absolute;right:54px;top:560px;width:660px;text-align:right;z-index:3;}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:700;letter-spacing:.30em;color:#9a6b3a;margin-bottom:26px;}
.cv-rule{width:120px;height:3px;background:linear-gradient(90deg,transparent,#c08a3e);margin:0 0 30px auto;}
.cv-h1{font-size:102px;font-weight:900;line-height:1.08;color:#2a2118;letter-spacing:-1px;white-space:nowrap;text-shadow:0 2px 24px rgba(255,250,235,.6);}
.cv-h2{font-size:94px;font-weight:900;line-height:1.12;color:#b23b2e;letter-spacing:-1px;margin-top:6px;white-space:nowrap;}
.cv-sub{font-family:"Noto Sans SC",sans-serif;font-size:31px;font-weight:500;line-height:1.55;color:#6a5740;margin-top:34px;}

/* ===== TITLE ===== */
#title{z-index:54;background:linear-gradient(170deg,#F7EFDE 0%,#EADBBF 100%);opacity:0;overflow:hidden;}
.ti-vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,rgba(255,252,242,.6) 0%,rgba(210,190,156,0) 55%),linear-gradient(180deg,rgba(120,100,66,.10),rgba(120,100,66,.22));}
.ti-wrap{position:absolute;left:80px;right:80px;top:700px;text-align:center;}
.ti-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:700;letter-spacing:.42em;color:#9a6b3a;margin-bottom:34px;opacity:0;}
.ti-l1{font-size:86px;font-weight:900;line-height:1.18;color:#2a2118;letter-spacing:-1px;opacity:0;}
.ti-l2{font-size:96px;font-weight:900;line-height:1.2;color:#b23b2e;letter-spacing:-1px;margin-top:14px;opacity:0;}
.ti-rule{width:0;height:3px;background:#c08a3e;margin:40px auto 0;}

/* ===== CHAPTERS ===== */
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.tint{position:absolute;inset:0;z-index:2;opacity:0;}
.tinttop{position:absolute;inset:0;z-index:2;opacity:0;}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none;}
.card{position:absolute;top:150px;right:54px;width:580px;padding:40px 44px 38px;border-radius:24px;
  background:linear-gradient(160deg,rgba(255,250,238,.16),rgba(255,250,238,.05));
  backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);
  border:1.5px solid rgba(255,246,225,.30);box-shadow:0 30px 80px rgba(0,0,0,.45);opacity:0;}
.card-no{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:800;letter-spacing:.30em;}
.card-name-row{display:flex;align-items:baseline;gap:18px;margin-top:14px;flex-wrap:wrap;}
.card-name{font-size:72px;font-weight:900;color:#fff7e9;letter-spacing:1px;line-height:1;}
.card-emo{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:700;}
.card-credit{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:500;line-height:1.5;color:rgba(255,247,232,.74);margin-top:22px;letter-spacing:.02em;}
.kw{position:absolute;left:0;right:0;bottom:560px;text-align:center;font-size:300px;font-weight:900;line-height:.85;opacity:0;letter-spacing:-6px;}
.subline{position:absolute;left:70px;right:70px;bottom:300px;text-align:center;font-size:46px;font-weight:600;color:#fff7e9;opacity:0;letter-spacing:.02em;text-shadow:0 3px 24px rgba(0,0,0,.7);}
.src{position:absolute;bottom:52px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:19px;font-weight:400;color:rgba(255,247,232,.34);letter-spacing:.22em;opacity:0;}

/* ===== TRANSITION CARDS ===== */
.trans{position:absolute;inset:0;z-index:40;opacity:0;background:linear-gradient(180deg,#15110b 0%,#0a0805 100%);}
.tr-wrap{position:absolute;left:90px;right:90px;top:800px;text-align:center;}
.tr-l{font-size:56px;font-weight:600;line-height:1.42;color:#efe6d2;opacity:0;letter-spacing:.02em;}
.tr-l.accent{font-weight:700;}

/* ===== OUTRO ===== */
#outro{z-index:52;background:linear-gradient(176deg,#FBF4E2 0%,#F2E6CC 55%,#E4D2B0 100%);opacity:0;overflow:hidden;}
.ot-sun{position:absolute;top:-180px;left:50%;transform:translateX(-50%);width:1000px;height:620px;
  background:radial-gradient(ellipse at center,rgba(255,248,225,.95) 0%,rgba(255,240,205,0) 70%);}
.ot-floor{position:absolute;left:0;right:0;bottom:0;height:420px;background:linear-gradient(180deg,rgba(200,182,150,0),rgba(170,150,116,.40));}
.ot-wrap{position:absolute;left:80px;right:80px;top:430px;text-align:center;}
.ot-h1{font-size:78px;font-weight:900;color:#2a2118;line-height:1.2;opacity:0;letter-spacing:-1px;}
.ot-h2{font-size:78px;font-weight:900;color:#b23b2e;line-height:1.2;opacity:0;letter-spacing:-1px;margin-top:6px;}
.ot-sub{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:600;color:#6a5740;margin-top:30px;opacity:0;}
.ot-recap{margin-top:38px;display:flex;flex-direction:column;gap:13px;align-items:center;}
.ot-row{font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:600;color:#7a6444;opacity:0;letter-spacing:.04em;}
.ot-row b{color:#2a2118;font-weight:800;}
.ot-cta{position:absolute;left:80px;right:80px;bottom:150px;text-align:center;opacity:0;}
.ot-cta .q1{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:700;color:#2a2118;}
.ot-cta .q2{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:800;color:#b23b2e;margin-top:14px;}
'''

crowd_specs=[(4,52,150,40,.30),(13,46,128,34,.24),(22,58,168,46,.32),(33,42,120,32,.22),
             (44,60,176,48,.36),(56,50,150,40,.26),(66,46,132,36,.22),(76,58,166,46,.32),(87,48,140,38,.26)]
def crowd():
    h=""
    for lf,w,bh,hd,op in crowd_specs:
        h+=(f'<div class="fig" style="left:{lf}%;width:{w}px;height:{bh}px;opacity:{op};border-radius:{w//3}px {w//3}px 0 0;">'
            f'<i style="position:absolute;bottom:{bh-6}px;left:50%;transform:translateX(-50%);width:{hd}px;height:{hd}px;border-radius:50%;background:#6b5c44;"></i></div>')
    return h

# 前景迎光背影（剪影，无脸）—— 对应 brief「一个学生背影站在阳光里」
solo='<div class="solo"><div class="hair"></div><div class="head"></div><div class="body"></div></div>'

ticket=('<div class="ticket"><div class="tk-hd">准 考 证</div>'
        '<div class="tk-row"><div class="tk-photo"></div>'
        '<div class="tk-lines"><div class="tk-line"></div><div class="tk-line s"></div>'
        '<div class="tk-line"></div><div class="tk-line s"></div></div></div></div>')

cover_html=f'''<div id="cover" class="layer">
  <div class="cv-sun"></div><div class="cv-haze"></div><div class="cv-floor"></div>
  <div class="crowd">{crowd()}</div>{solo}{ticket}
  <div class="cv-text">
    <div class="cv-eyebrow">毕业季 · 孙燕姿单人歌单</div><div class="cv-rule"></div>
    <div class="cv-h1">走出考场<br>那一刻</div><div class="cv-h2">请打开孙燕姿</div>
    <div class="cv-sub">给高考后的你，<br>一条从释怀到逆光的歌单</div>
  </div><div class="grain"></div>
</div>'''

title_html=f'''<div id="title" class="layer">
  <div class="ti-vig"></div>
  <div class="ti-wrap">
    <div class="ti-eyebrow" id="tiE">写给刚放下笔的你</div>
    <div class="ti-l1" id="tiL1">走出高考考场那一刻</div>
    <div class="ti-l2" id="tiL2">请打开这 5 首孙燕姿</div>
    <div class="ti-rule" id="tiR"></div>
  </div><div class="grain"></div>
</div>'''

chap_html=[]
foot_tracks=[0,6,0,6,0]
for i,s in enumerate(SONGS):
    k=s["key"]
    chap_html.append(f'''<video id="fv_{k}" class="fv clip" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{foot_tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>
<div id="tint_{k}" class="clip tint" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{20+i}" style="background:{s['tint']}"></div>
<div id="ttop_{k}" class="clip tinttop" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{30+i}" style="background:{s['ttop']}"></div>
<div id="chrome_{k}" class="clip chrome" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{40+i}" style="--acc:{s['acc']}">
  <div class="card">
    <div class="card-no" style="color:{s['acc']}">{s['no']}</div>
    <div class="card-name-row"><span class="card-name">{s['name']}</span><span class="card-emo" style="color:{s['acc']}">｜{s['emo']}</span></div>
    <div class="card-credit">孙燕姿 · {s['year']}<br>《{s['album']}》</div>
  </div>
  <div class="kw" id="kw_{k}" style="color:{s['ghostcol']}">{s['ghost']}</div>
  <div class="subline" id="sub_{k}">{s['subline']}</div>
  <div class="src" id="src_{k}">{s['src']}</div>
</div>''')

trans_html=[]
for i,s in enumerate(SONGS):
    k=s["key"]; trl=s["trans"]
    trans_html.append(f'''<div id="trans_{k}" class="clip trans" data-start="{f(s['start'])}" data-duration="{f(TRANS+0.6)}" data-track-index="{50+i}">
  <div class="tr-wrap">
    <div class="tr-l" id="tr1_{k}">{trl[0]}</div>
    <div class="tr-l" id="tr2_{k}">{trl[1]}</div>
    <div class="tr-l accent" id="tr3_{k}" style="color:{s['acc']}">{trl[2]}</div>
  </div>
</div>''')

recap_rows="".join(f'<div class="ot-row" id="orow{i}"><b>{s["name"]}</b>　{s["emo"]}</div>' for i,s in enumerate(SONGS))
outro_html=f'''<div id="outro" class="layer">
  <div class="ot-sun"></div><div class="ot-floor"></div>
  <div class="crowd" style="bottom:120px;opacity:.9;">{crowd()}</div>
  <div class="ot-wrap">
    <div class="ot-h1" id="oth1">高考结束了</div>
    <div class="ot-h2" id="oth2">但你的人生，才刚刚开始</div>
    <div class="ot-sub" id="otsub">这 5 首孙燕姿，送给走出考场的你</div>
    <div class="ot-recap">{recap_rows}</div>
  </div>
  <div class="ot-cta" id="otcta">
    <div class="q1">如果只能选一首孙燕姿陪你毕业</div>
    <div class="q2">你会选哪一首？</div>
  </div>
  <div class="grain"></div>
</div>'''

audio_html=f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ---------------- JS ----------------
def js_chapter(i,s):
    k=s["key"]; a=s["anchor"]; b=s["start"]; end=s["end"]
    sw0=b+a["sw0"]; full0=b+a["full0"]; full1=b+a["full1"]; fade=end-1.3
    tend=b+TRANS+0.6
    return f'''
// ---- {s["name"]} ----
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:1.6,ease:"power2.out"}},{f(b)});
tl.to("#tint_{k}",{{opacity:1,duration:1.4}},{f(b)});
tl.to("#ttop_{k}",{{opacity:1,duration:1.4}},{f(b)});
tl.fromTo("#trans_{k}",{{opacity:0}},{{opacity:1,duration:.5,ease:"power2.out"}},{f(b)});
tl.fromTo("#tr1_{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.6}},{f(b+0.35)});
tl.fromTo("#tr2_{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.6}},{f(b+1.15)});
tl.fromTo("#tr3_{k}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{f(b+1.95)});
tl.to("#trans_{k}",{{opacity:0,duration:.7,ease:"power2.in"}},{f(tend-0.7)});
tl.set("#trans_{k}",{{opacity:0}},{f(tend)});
tl.fromTo("#chrome_{k} .card",{{opacity:0,x:50,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{f(b+TRANS+0.3)});
tl.fromTo("#src_{k}",{{opacity:0}},{{opacity:1,duration:.6}},{f(b+TRANS+1.0)});
tl.to("#chrome_{k} .card",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{f(sw0-0.1)});
tl.fromTo("#kw_{k}",{{opacity:0,scale:.94}},{{opacity:1,scale:1,duration:1.8,ease:"power3.out"}},{f(full0-0.5)});
tl.fromTo("#sub_{k}",{{opacity:0,y:22}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(full0+ (s["show"]*0.32))});
tl.to("#sub_{k}",{{opacity:0,y:-12,duration:.7,ease:"power2.in"}},{f(end-1.8)});
tl.to("#fv_{k}",{{opacity:0,duration:1.3,ease:"power1.in"}},{f(fade)});
tl.set("#fv_{k}",{{opacity:0}},{f(end)});
tl.to("#tint_{k}",{{opacity:0,duration:1.3}},{f(fade)});
tl.set("#tint_{k}",{{opacity:0}},{f(end)});
tl.to("#ttop_{k}",{{opacity:0,duration:1.3}},{f(fade)});
tl.set("#ttop_{k}",{{opacity:0}},{f(end)});
tl.to("#kw_{k}",{{opacity:0,duration:1.2}},{f(fade)});
tl.set("#kw_{k}",{{opacity:0}},{f(end)});
tl.to("#src_{k}",{{opacity:0,duration:.7}},{f(fade)});
tl.set("#src_{k}",{{opacity:0}},{f(end)});
'''

JS=f'''
// COVER
tl.set("#cover",{{opacity:1}},0);tl.set(".cv-text",{{opacity:1}},0);
tl.fromTo("#cover .ticket",{{rotate:-6,y:0}},{{rotate:-7.5,y:-6,duration:3.0,ease:"sine.inOut"}},0);
tl.fromTo("#cover .cv-sun",{{opacity:.85}},{{opacity:1,duration:2.6,yoyo:true,repeat:1,ease:"sine.inOut"}},0);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{f(COVER_D-0.3)});
tl.set("#cover",{{opacity:0}},{f(COVER_D+0.1)});
// TITLE
tl.fromTo("#title",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(TITLE_T-0.3)});
tl.fromTo("#tiE",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.6}},{f(TITLE_T+0.2)});
tl.fromTo("#tiL1",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(TITLE_T+0.5)});
tl.fromTo("#tiL2",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(TITLE_T+1.1)});
tl.fromTo("#tiR",{{width:0}},{{width:160,duration:.8,ease:"power2.out"}},{f(TITLE_T+1.8)});
tl.to("#title",{{opacity:0,duration:.7,ease:"power2.in"}},{f(CH1-0.4)});
tl.set("#title",{{opacity:0}},{f(CH1+0.2)});
{''.join(js_chapter(i,s) for i,s in enumerate(SONGS))}
// OUTRO
tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.8,ease:"power2.out"}},{f(OUTRO_T-0.3)});
tl.fromTo("#oth1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(OUTRO_T+0.5)});
tl.fromTo("#oth2",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(OUTRO_T+1.3)});
tl.fromTo("#otsub",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.7}},{f(OUTRO_T+2.4)});
{''.join(f'tl.fromTo("#orow{i}",{{opacity:0,x:-16}},{{opacity:1,x:0,duration:.45}},{f(OUTRO_T+3.3+i*0.32)});' for i in range(len(SONGS)))}
tl.fromTo("#otcta",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{f(OUTRO_T+OUTRO_V-1.5)});
tl.to("#outro",{{opacity:1,duration:.1}},{f(TOTAL-0.2)});
'''

html=f'''<!doctype html>
<html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
  {''.join(chap_html)}
  {''.join(trans_html)}
  {cover_html}
  {title_html}
  {outro_html}
  {audio_html}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script></body></html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"sunyanzi-graduation"}', encoding="utf-8")
print("index.html:", len(html), "bytes ; TOTAL", TOTAL)
print("BUILD DONE", "(SAMPLE)" if SAMPLE else "(FULL)")
