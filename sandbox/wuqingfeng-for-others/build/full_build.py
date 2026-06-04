#!/usr/bin/env python3
"""吴青峰为别人写的歌 TOP5（倒数 #5->#1，女声）。
结构：cover -> intro(VO) -> 5 首[转场VO(低床)->swell->纯音乐展示(footage)] -> outro(VO)。
音乐：每首从 raw[W - show0] 连续取，chapter-local show0 对齐 raw W；展示段=raw[W..W+SHOW]。
 - 实拍同步曲(掉了/带我走Live): clips_seg 切自 start==W => footage 与音乐口型同步。
 - 蒙太奇曲(怪美/年轮/有形feat): footage 解耦(歌手镜头剪辑)，音乐仍取该曲副歌 W。
渲染后必须 ffmpeg mux master.wav。
"""
import subprocess, wave, contextlib, json
from pathlib import Path

A = "audio"; CS = "clips_seg"; RAW = "raw"

def wdur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def vdur(p):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","csv=p=0",str(p)], capture_output=True, text=True).stdout.strip()
    return round(float(out), 3)

def run(cmd): subprocess.run(cmd, check=True)

# ---------- 节奏常量 ----------
LEAD=0.15; PRE_VOICE=0.8; POST_VOICE=0.9; SWELL=1.4; BED=0.17; TAIL=0.9
VOICE_GAIN=2.2
SHOW_TARGET={"guaimei":13.5,"nianlun":14.0,"diaole":14.0,"daiwozou":14.0,"youxing":12.5}

# ---------- 歌曲（揭晓顺序 #5->#1） ----------
# key|rank|name|singer|album|year|credit|tag|W(raw展示音乐起点)|颜色
SONGS = [
  dict(key="guaimei", rank="05", name="怪美的", singer="蔡依林", album="Ugly Beauty", year="2018",
       credit="作词：吴青峰", tag="尖锐 · 自嘲 · 自我重建", W=58.0,
       bg="#170812", pri="#E0507A", acc="#F6C8DA", tint="200,80,120"),
  dict(key="nianlun", rank="04", name="年轮说", singer="杨丞琳", album="年轮说", year="2015",
       credit="作词：吴青峰 · 作曲：郑宇界", tag="把爱情写成时间的剖面", W=210.0,
       bg="#140F08", pri="#E2A95A", acc="#F5DEAE", tint="180,130,60"),
  dict(key="diaole", rank="03", name="掉了", singer="张惠妹", album="阿密特", year="2009",
       credit="词曲：吴青峰", tag="把失去，写到最碎", W=163.0,
       bg="#0A1016", pri="#8FB6C8", acc="#D8E9F1", tint="110,150,175"),
  dict(key="daiwozou", rank="02", name="带我走", singer="杨丞琳", album="半熟宣言", year="2008",
       credit="词曲：吴青峰", tag="偶像剧时代的青春记忆", W=160.0,
       bg="#16080A", pri="#D8545F", acc="#F0BCBC", tint="200,80,85"),
  dict(key="youxing", rank="01", name="有形的翅膀", singer="张韶涵", album="有形的翅膀", year="2012",
       credit="词曲：吴青峰", tag="传唱度最高的那一首", W=208.0,
       bg="#14100A", pri="#E7C97A", acc="#F6E9C6", tint="210,175,120"),
]
KEYS = [s["key"] for s in SONGS]
RAWF = {"guaimei":"guaimei_yt","nianlun":"nianlun_yt","diaole":"diaole_bili",
        "daiwozou":"daiwozou_live","youxing":"youxing_feat"}
INTRO_BED = "guaimei_yt"   # 引入 #5
OUTRO_BED = "youxing_yt"   # 收束(用 有形 studio MV 干净尾)

# ---------- 时长 ----------
NV = {s["key"]: wdur(f"{A}/{s['key']}.wav") for s in SONGS}
NV["intro"] = wdur(f"{A}/intro.wav"); NV["outro"] = wdur(f"{A}/outro.wav")
SHOW = {s["key"]: round(min(vdur(f"{CS}/{s['key']}.mp4"), SHOW_TARGET[s["key"]]), 3) for s in SONGS}
print("VO:", json.dumps(NV, ensure_ascii=False)); print("SHOW:", SHOW)

def anchors(key):
    vo = NV[key]; sd = SHOW[key]
    v0 = LEAD + PRE_VOICE
    v1 = v0 + vo
    sw0 = v1 + POST_VOICE
    show0 = sw0 + SWELL
    show1 = show0 + sd
    end = show1 + TAIL
    return dict(v0=v0,v1=v1,sw0=sw0,show0=show0,show1=show1,end=end,seg=end)

COVER_D = 5.0
INTRO_SEG = round(LEAD + 0.5 + NV["intro"] + 1.8, 3)
OUTRO_SEG = round(LEAD + NV["outro"] + 2.6, 3)

starts = {}
t = COVER_D
starts["intro"] = (t, INTRO_SEG); t += INTRO_SEG
for s in SONGS:
    a = anchors(s["key"]); starts[s["key"]] = (round(t,3), a["seg"]); t += a["seg"]
starts["outro"] = (round(t,3), OUTRO_SEG); t += OUTRO_SEG
TOTAL = round(t, 3)
print(f"TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ============ 音频段构建 ============
Path("build/segs").mkdir(parents=True, exist_ok=True)

run(["ffmpeg","-v","error","-i",f"{RAW}/{INTRO_BED}.mp4","-i",f"{A}/intro.wav",
  "-filter_complex",
  f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int((LEAD+0.5)*1000)}|{int((LEAD+0.5)*1000)},volume={VOICE_GAIN}[v];"
  f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={COVER_D}:{round(COVER_D+INTRO_SEG,3)},asetpts=PTS-STARTPTS,"
  f"volume=0.16,afade=t=in:st=0:d=0.5,afade=t=out:st={INTRO_SEG-1.8}:d=1.8[bed];"
  f"[v][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_SEG},alimiter=limit=0.95[o]",
  "-map","[o]","-ac","2","-ar","48000","build/segs/seg_intro.wav","-y"])

def build_song(s):
    k = s["key"]; a = anchors(k); seg = a["seg"]
    v0=a["v0"]; sw0=a["sw0"]; show0=a["show0"]; show1=a["show1"]
    mstart = round(s["W"] - show0, 3)
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
          f"+(between(t,{v0},{sw0}))*{BED}"
          f"+(between(t,{sw0},{show0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
          f"+(gte(t,{show0}))*1.0")
    run(["ffmpeg","-v","error","-i",f"{RAW}/{RAWF[k]}.mp4","-i",f"{A}/{k}.wav",
      "-filter_complex",
      f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume={VOICE_GAIN}[v];"
      f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
      f"atrim={mstart}:{round(mstart+seg,3)},asetpts=PTS-STARTPTS,"
      f"volume='{ve}':eval=frame,afade=t=out:st={show1}:d={round(seg-show1,3)}[m];"
      f"[v][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95[o]",
      "-map","[o]","-ac","2","-ar","48000",f"build/segs/seg_{k}.wav","-y"])

for s in SONGS: build_song(s); print("seg", s["key"], "ok")

o_mstart = 146.0  # 有形 studio 副歌段做 outro 床(避免用歌曲淡出尾,否则太轻→片尾dead-air)
run(["ffmpeg","-v","error","-i",f"{RAW}/{OUTRO_BED}.mp4","-i",f"{A}/outro.wav",
  "-filter_complex",
  f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[v];"
  f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={o_mstart}:{round(o_mstart+OUTRO_SEG,3)},asetpts=PTS-STARTPTS,"
  f"volume=0.22,afade=t=in:st=0:d=1.2,afade=t=out:st={OUTRO_SEG-1.6}:d=1.6[bed];"
  f"[v][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OUTRO_SEG},alimiter=limit=0.95[o]",
  "-map","[o]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])

order = ["intro"]+KEYS+["outro"]
# 封面低音乐床(guaimei 0:COVER_D),消除开头 dead-air;与 intro 床(guaimei COVER_D:)续上
run(["ffmpeg","-v","error","-i",f"{RAW}/{INTRO_BED}.mp4",
     "-filter_complex",
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{COVER_D},asetpts=PTS-STARTPTS,"
     f"volume=0.20,afade=t=in:st=0:d=1.8[o]",
     "-map","[o]","-ac","2","-ar","48000","build/segs/seg_cover.wav","-y"])
Path("build/segs/list.txt").write_text("file 'seg_cover.wav'\n"+"".join(f"file 'seg_{k}.wav'\n" for k in order), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/list.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master:", wdur("master.wav"), "planned:", TOTAL)

# ============ 资源拷贝 ============
import shutil
Path("hf/clips_seg").mkdir(parents=True, exist_ok=True)
for k in KEYS: shutil.copy(f"{CS}/{k}.mp4", f"hf/clips_seg/{k}.mp4")
shutil.copy("master.wav", "hf/master.wav")
Path("hf/cover_assets").mkdir(exist_ok=True)
run(["ffmpeg","-v","error","-i",f"{RAW}/cover_face.png","-vf","crop=600:600:140:20,scale=560:560","-frames:v","1","-update","1","hf/cover_assets/face.png","-y"])
run(["ffmpeg","-v","error","-i",f"{RAW}/cover_face.png","-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920","-frames:v","1","-update","1","hf/cover_assets/cover_bg.png","-y"])
print("assets copied")

# ============ 绝对锚点 ============
ABS = {}
for s in SONGS:
    k=s["key"]; a=anchors(k); base=starts[k][0]
    ABS[k] = {kk: round(base+vv,3) for kk,vv in a.items() if kk!='seg'}
    ABS[k]["base"]=base; ABS[k]["end"]=round(base+a["seg"],3)
INTRO_T=starts["intro"][0]; OUTRO_T=starts["outro"][0]
def f(x): return f"{round(x,3)}"

# ============ HTML 片段 ============
foot=[]; tracks=[0,6,0,6,0]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    foot.append(f'<video id="fv_{k}" class="fv clip" data-start="{f(a["show0"])}" data-duration="{f(SHOW[k])}" data-track-index="{tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>')

bglayer=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    bglayer.append(f'<div id="bg_{k}" class="clip chbg chbg_{k}" data-start="{f(a["base"])}" data-duration="{f(a["end"]-a["base"])}" data-track-index="{40+i}"><div class="chbg-glow"></div><div class="chbg-grain"></div></div>')

tints=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    tints.append(f'<div id="tint_{k}" class="clip ftint ftint_{k}" data-start="{f(a["show0"])}" data-duration="{f(SHOW[k])}" data-track-index="{50+i}"></div>')

chrome=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    dots="".join(
        f'<div class="rail-dot{(" active" if j==i else "")}{(" past" if j<i else "")}" style="top:{8+j*20}%"><span class="rail-tick">{SONGS[j]["rank"]}</span></div>'
        for j in range(5))
    chrome.append(f'''<div id="ch_{k}" class="clip chrome chrome_{k}" data-start="{f(a["base"])}" data-duration="{f(a["end"]-a["base"])}" data-track-index="{20+i}">
  <div class="rail"><div class="rail-bar"></div>{dots}</div>
  <div class="bignum" id="big_{k}"><span class="bn-hash">NO.</span>{s["rank"]}</div>
  <div class="card" id="card_{k}">
    <div class="card-singer">{s["singer"]}<span class="card-meta"> ｜《{s["album"]}》{s["year"]}</span></div>
    <div class="card-name">{s["name"]}</div>
    <div class="card-credit">{s["credit"]}</div>
    <div class="card-tag"><span class="dot"></span>{s["tag"]}</div>
  </div>
  <div class="badge" id="badge_{k}"><span class="bg-no">{s["rank"]}</span><span class="bg-nm">{s["singer"]}《{s["name"]}》</span></div>
</div>''')

cover=f'''<div id="cover" class="clip cover" data-start="0" data-duration="{f(COVER_D)}" data-track-index="60">
  <div class="cv-bg"></div><div class="cv-veil"></div><div class="cv-grain"></div>
  <div class="cv-portrait"><div class="cv-face"></div><div class="cv-ring"></div></div>
  <div class="cv-head">
    <div class="cv-eyebrow">幕后金笔 · 华语词曲</div>
    <h1 class="cv-title">吴青峰<br><span class="cv-title2">为别人写的歌</span></h1>
    <div class="cv-sub">五首传遍华语乐坛的金曲，<br>原来都出自他的笔下。</div>
  </div>
  <div class="cv-list">
    {''.join(f'<div class="cv-node"><span class="cv-n">{s["rank"]}</span><span class="cv-nm">《{s["name"]}》</span><span class="cv-yy">{s["singer"]}</span></div>' for s in reversed(SONGS))}
  </div>
  <div class="cv-top">TOP<span>5</span></div>
</div>'''

intro=f'''<div id="introblk" class="clip introblk" data-start="{f(INTRO_T)}" data-duration="{f(INTRO_SEG)}" data-track-index="61">
  <div class="ib-grad"></div>
  <h2 class="ib-h">同一支笔，<br><span>五个名字</span></h2>
  <div class="ib-rows">
  {''.join(f'<div class="ib-row" id="ib_{i}"><span class="ib-no">{s["rank"]}</span><span class="ib-nm">{s["singer"]}《{s["name"]}》</span></div>' for i,s in enumerate(reversed(SONGS)))}
  </div>
</div>'''

outro=f'''<div id="outroblk" class="clip outroblk" data-start="{f(OUTRO_T)}" data-duration="{f(OUTRO_SEG)}" data-track-index="62">
  <div class="ot-bg"></div>
  <div class="ot-list">
    {''.join(f'<div class="ot-line"><span class="ot-no">{s["rank"]}</span><span class="ot-nm">{s["singer"]}《{s["name"]}》</span></div>' for s in reversed(SONGS))}
  </div>
  <h2 class="ot-h">最好的句子，<br>都写给了别人。</h2>
  <p class="ot-q">你心里的第一名，是哪一首？</p>
</div>'''

audio=f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

def theme_vars():
    out=[]
    for s in SONGS:
        out.append(f'.chrome_{s["key"]}{{--pri:{s["pri"]};--acc:{s["acc"]};}}')
        out.append(f'.chbg_{s["key"]}{{background:radial-gradient(ellipse 120% 80% at 50% 18%, {s["bg"]} 0%, #06070B 78%);}}')
        out.append(f'.chbg_{s["key"]} .chbg-glow{{background:radial-gradient(circle at 70% 30%, {s["pri"]}22 0%, transparent 45%),radial-gradient(circle at 25% 72%, {s["pri"]}18 0%, transparent 40%);}}')
        out.append(f'.ftint_{s["key"]}{{background:linear-gradient(180deg, rgba({s["tint"]},.10) 0%, rgba(6,7,11,.30) 42%, rgba(6,7,11,.86) 100%);}}')
    return "\n".join(out)

CSS = '''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06070B;color:#F7F0E8;font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased;}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.ftint{position:absolute;inset:0;z-index:2;opacity:0;}
.chbg{position:absolute;inset:0;z-index:0;opacity:0;}
.chbg-glow{position:absolute;inset:0;mix-blend-mode:screen;opacity:.9;}
.chbg-grain{position:absolute;inset:0;background-image:radial-gradient(circle at 12% 28%,rgba(255,255,255,.03) 0 .5px,transparent .9px),radial-gradient(circle at 78% 66%,rgba(255,255,255,.03) 0 .5px,transparent .9px);background-size:220px 220px,260px 260px;opacity:.6;}
.chrome{position:absolute;inset:0;z-index:6;pointer-events:none;}

.rail{position:absolute;top:150px;left:60px;bottom:210px;width:10px;opacity:0;}
.rail-bar{position:absolute;top:0;bottom:0;left:4px;width:2px;background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.22),rgba(255,255,255,.05));}
.rail-dot{position:absolute;left:-20px;width:48px;height:48px;border-radius:50%;background:rgba(16,16,22,.9);border:2px solid rgba(255,255,255,.22);display:flex;align-items:center;justify-content:center;}
.rail-dot.past{background:rgba(60,60,72,.6);border-color:rgba(255,255,255,.26);}
.rail-dot.active{background:var(--pri);border-color:var(--pri);box-shadow:0 0 34px var(--pri),0 0 70px rgba(255,255,255,.2);transform:scale(1.18);}
.rail-tick{font-family:"Noto Sans SC",sans-serif;font-size:23px;font-weight:800;color:rgba(255,255,255,.78);}
.rail-dot.active .rail-tick{color:rgba(16,16,22,.96);}

.bignum{position:absolute;top:560px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:520px;font-weight:900;line-height:.8;color:transparent;-webkit-text-stroke:3px var(--pri);opacity:0;letter-spacing:-10px;filter:drop-shadow(0 10px 60px rgba(0,0,0,.5));}
.bn-hash{display:block;-webkit-text-stroke:0;color:var(--pri);font-size:60px;font-weight:800;letter-spacing:.4em;margin-bottom:6px;text-indent:.4em;}

.card{position:absolute;left:70px;right:70px;bottom:300px;text-align:center;opacity:0;}
.card-singer{font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:700;letter-spacing:.06em;color:#F7F0E8;margin-bottom:16px;}
.card-meta{font-weight:500;font-size:28px;color:rgba(255,255,255,.62);letter-spacing:.04em;}
.card-name{font-family:"Noto Serif SC",serif;font-size:118px;font-weight:800;line-height:1.0;color:#F7F0E8;letter-spacing:-1px;margin-bottom:22px;text-shadow:0 6px 40px rgba(0,0,0,.5);}
.card-credit{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:600;letter-spacing:.04em;color:var(--acc);margin-bottom:26px;}
.card-tag{display:inline-flex;align-items:center;gap:14px;font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:700;color:var(--acc);}
.card-tag .dot{width:12px;height:12px;border-radius:50%;background:var(--pri);box-shadow:0 0 16px var(--pri);}

.badge{position:absolute;top:140px;left:60px;display:flex;align-items:center;gap:20px;opacity:0;max-width:920px;}
.bg-no{font-family:"Noto Sans SC",sans-serif;font-size:72px;font-weight:900;color:var(--pri);line-height:1;-webkit-text-stroke:0;text-shadow:0 4px 24px rgba(0,0,0,.6);}
.bg-nm{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:800;color:#F7F0E8;text-shadow:0 4px 24px rgba(0,0,0,.7);}

.cover{position:absolute;inset:0;z-index:80;background:#06070B;overflow:hidden;}
.cv-bg{position:absolute;inset:-6%;background-image:url("cover_assets/cover_bg.png");background-size:cover;background-position:center 16%;filter:blur(34px) saturate(.85) brightness(.5);transform:scale(1.18);}
.cv-veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,7,11,.55) 0%,rgba(6,7,11,.74) 46%,rgba(6,7,11,.95) 100%);}
.cv-grain{position:absolute;inset:0;background-image:radial-gradient(circle at 10% 30%,rgba(255,255,255,.04) 0 .5px,transparent .8px),radial-gradient(circle at 80% 70%,rgba(255,255,255,.04) 0 .5px,transparent .8px);background-size:200px 200px,240px 240px;opacity:.5;}
.cv-portrait{position:absolute;top:120px;left:50%;transform:translateX(-50%);width:360px;height:360px;}
.cv-face{position:absolute;inset:0;border-radius:50%;background-image:url("cover_assets/face.png");background-size:cover;background-position:center 38%;border:4px solid rgba(247,240,232,.92);box-shadow:0 24px 70px rgba(0,0,0,.6);}
.cv-ring{position:absolute;inset:-16px;border-radius:50%;border:1.5px solid rgba(231,201,122,.5);}
.cv-top{position:absolute;top:150px;right:70px;font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:800;letter-spacing:.2em;color:rgba(231,201,122,.9);}
.cv-top span{display:block;font-size:120px;font-weight:900;color:#E7C97A;line-height:.9;text-align:right;}
.cv-head{position:absolute;top:520px;left:70px;right:70px;text-align:center;}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:28px;font-weight:700;letter-spacing:.34em;color:#E7C97A;margin-bottom:22px;}
.cv-title{font-family:"Noto Serif SC",serif;font-size:118px;font-weight:900;line-height:1.04;color:#F7F0E8;letter-spacing:-1px;}
.cv-title2{color:#E7C97A;}
.cv-sub{font-family:"Noto Serif SC",serif;font-size:40px;font-weight:500;color:rgba(247,240,232,.8);line-height:1.45;margin-top:24px;}
.cv-list{position:absolute;bottom:90px;left:80px;right:80px;}
.cv-node{display:flex;align-items:baseline;gap:28px;padding:16px 0;border-bottom:1px solid rgba(255,255,255,.1);}
.cv-node:last-child{border-bottom:none;}
.cv-n{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:900;color:#E7C97A;min-width:60px;letter-spacing:.04em;}
.cv-nm{font-family:"Noto Serif SC",serif;font-size:44px;font-weight:700;color:#F7F0E8;flex:1;}
.cv-yy{font-family:"Noto Sans SC",sans-serif;font-size:28px;font-weight:600;color:rgba(247,240,232,.62);letter-spacing:.02em;}

.introblk{position:absolute;inset:0;z-index:70;background:radial-gradient(ellipse at 50% 30%,#12131F 0%,#06070B 72%);}
.ib-grad{position:absolute;inset:0;background:radial-gradient(circle at 72% 24%,rgba(231,201,122,.10) 0,transparent 46%),radial-gradient(circle at 26% 76%,rgba(216,84,95,.08) 0,transparent 44%);}
.ib-h{position:absolute;top:300px;left:80px;right:80px;font-family:"Noto Serif SC",serif;font-size:128px;font-weight:900;line-height:1.08;color:#F7F0E8;letter-spacing:-1px;opacity:0;}
.ib-h span{color:#E7C97A;}
.ib-rows{position:absolute;top:780px;left:90px;right:90px;}
.ib-row{display:flex;align-items:baseline;gap:26px;padding:14px 0;opacity:0;}
.ib-no{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:900;color:#E7C97A;min-width:64px;}
.ib-nm{font-family:"Noto Serif SC",serif;font-size:52px;font-weight:700;color:rgba(247,240,232,.92);}

.outroblk{position:absolute;inset:0;z-index:71;background:radial-gradient(ellipse at 50% 40%,#16131C 0%,#06070B 72%);}
.ot-bg{position:absolute;inset:0;background:radial-gradient(circle at 50% 46%,rgba(231,201,122,.1) 0,transparent 46%);}
.ot-list{position:absolute;top:330px;left:110px;right:110px;}
.ot-line{display:flex;align-items:baseline;gap:24px;padding:10px 0;opacity:0;}
.ot-no{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:900;color:#E7C97A;min-width:56px;}
.ot-nm{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:700;color:#F7F0E8;}
.ot-h{position:absolute;top:920px;left:110px;right:110px;font-family:"Noto Serif SC",serif;font-size:100px;font-weight:900;line-height:1.1;color:#F7F0E8;letter-spacing:-1px;opacity:0;}
.ot-q{position:absolute;top:1280px;left:110px;right:110px;font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:600;letter-spacing:.04em;color:#E7C97A;opacity:0;}
''' + theme_vars()

def js_song(s,i):
    k=s["key"]; a=ABS[k]
    base=a["base"]; v0=a["v0"]; sw0=a["sw0"]; show0=a["show0"]; show1=a["show1"]; end=a["end"]
    return f'''
// ---- {s["name"]} (#{s["rank"]}) ----
tl.set("#bg_{k}",{{opacity:1}},{f(base)});
tl.fromTo(".chrome_{k} .rail",{{opacity:0}},{{opacity:1,duration:.7}},{f(base+0.2)});
tl.fromTo("#big_{k}",{{opacity:0,scale:1.18,y:10}},{{opacity:1,scale:1,y:0,duration:.9,ease:"power3.out"}},{f(base+0.25)});
tl.fromTo("#card_{k}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(base+0.6)});
tl.to("#big_{k}",{{opacity:0,scale:.86,duration:.7,ease:"power2.in"}},{f(sw0-0.1)});
tl.set("#big_{k}",{{opacity:0}},{f(show0)});
tl.to("#card_{k}",{{opacity:0,y:-26,duration:.6,ease:"power2.in"}},{f(sw0+0.1)});
tl.set("#card_{k}",{{opacity:0}},{f(show0)});
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.07}},{{opacity:1,scale:1,duration:1.0,ease:"power2.out"}},{f(show0-0.4)});
tl.fromTo("#tint_{k}",{{opacity:0}},{{opacity:1,duration:1.0}},{f(show0-0.4)});
tl.fromTo("#badge_{k}",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.7,ease:"power2.out"}},{f(show0+0.15)});
tl.to("#fv_{k}",{{opacity:0,duration:.9,ease:"power1.in"}},{f(show1-0.5)});
tl.set("#fv_{k}",{{opacity:0}},{f(end)});
tl.to("#tint_{k}",{{opacity:0,duration:.9,ease:"power1.in"}},{f(show1-0.5)});
tl.set("#tint_{k}",{{opacity:0}},{f(end)});
tl.to("#badge_{k}",{{opacity:0,duration:.6,ease:"power1.in"}},{f(show1-0.4)});
tl.set("#badge_{k}",{{opacity:0}},{f(end)});
tl.to(".chrome_{k} .rail",{{opacity:0,duration:.5}},{f(end-0.4)});
tl.set(".chrome_{k} .rail",{{opacity:0}},{f(end)});
tl.to("#bg_{k}",{{opacity:0,duration:.7,ease:"power1.in"}},{f(end-0.5)});
tl.set("#bg_{k}",{{opacity:0}},{f(end)});
'''

JS=f'''
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-face",{{opacity:1}},0);tl.set(".cv-head",{{opacity:1}},0);tl.set(".cv-list",{{opacity:1}},0);tl.set(".cv-top",{{opacity:1}},0);
tl.to(".cv-portrait",{{scale:1.03,duration:3.2,yoyo:true,repeat:1,ease:"sine.inOut"}},1.2);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{f(COVER_D-0.6)});
tl.set("#cover",{{opacity:0}},{f(COVER_D)});

tl.set("#introblk",{{opacity:1}},{f(INTRO_T)});
tl.fromTo(".ib-h",{{opacity:0,y:40}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{f(INTRO_T+0.3)});
{''.join(f'tl.fromTo("#ib_{i}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{f(INTRO_T+1.6+i*0.5)});'+chr(10) for i in range(5))}
tl.to("#introblk",{{opacity:0,duration:.7,ease:"power2.in"}},{f(INTRO_T+INTRO_SEG-0.7)});
tl.set("#introblk",{{opacity:0}},{f(INTRO_T+INTRO_SEG)});

{''.join(js_song(s,i) for i,s in enumerate(SONGS))}

tl.fromTo("#outroblk",{{opacity:0}},{{opacity:1,duration:.8,ease:"power2.out"}},{f(OUTRO_T)});
{''.join(f'tl.fromTo(".ot-list .ot-line:nth-child({i+1})",{{opacity:0,x:-18}},{{opacity:.92,x:0,duration:.45,ease:"power2.out"}},{f(OUTRO_T+0.4+i*0.16)});'+chr(10) for i in range(5))}
tl.fromTo(".ot-h",{{opacity:0,y:40}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{f(OUTRO_T+2.0)});
tl.fromTo(".ot-q",{{opacity:0,y:12}},{{opacity:.95,y:0,duration:.7,ease:"power2.out"}},{f(OUTRO_T+3.4)});
tl.to("#outroblk",{{opacity:1,duration:.1}},{f(TOTAL-0.2)});
'''

html=f'''<!doctype html><html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
{chr(10).join(bglayer)}
{chr(10).join(foot)}
{chr(10).join(tints)}
{chr(10).join(chrome)}
{cover}
{intro}
{outro}
{audio}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script></body></html>'''

Path("hf/index.html").write_text(html, encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"wuqingfeng-for-others"}', encoding="utf-8")
print("index.html:", len(html), "bytes; TOTAL", TOTAL, "s")
print("ALL BUILD DONE")
