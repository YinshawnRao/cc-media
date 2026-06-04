#!/usr/bin/env python3
"""《隐形的翅膀》5版本时间线 — 完整片构建。
产物：master.wav（逐段 footage 音乐床→swell→副歌展示 + 旁白 ducking）+ hf/index.html + hf/clips_seg/*。
预设：audio/<key>.wav 来自 build/narrate_segments.py；clips/vert_*.mp4 来自 vfill。
渲染后必须 ffmpeg mux master.wav（HyperFrames 会压平音频动态）。叙事序，非倒数。
"""
import subprocess, wave, contextlib, json
from pathlib import Path

A = "audio"; C = "clips"
def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)
def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

NARR = {k: dur(f"{A}/{k}.wav") for k in
        ["intro","s1_voice","s2_voice","s3_voice","s4_voice","s5_voice","outro"]}
MID = {k: v["text"] for k, v in json.loads(Path("narration.json").read_text(encoding="utf-8")).items()
       if k.endswith("_mid")}
print("NARR:", json.dumps(NARR, ensure_ascii=False))

# ---------- 节奏常量 ----------
LEAD=0.15; PRE_VOICE=0.8; POST_VOICE=1.2; SWELL=1.5; BED=0.18
HIGH_BASE=28.0; HIGH_LAST=36.0; TAIL=1.2
COVER_D=4.0; HOOK_LEAD=0.3
MGAIN={"s5":"volume=2dB,"}  # 2023 副歌偏软，补齐响度一致性

# 每首源切点 (clip, music_seek_start)
SOURCES = {"s1":("vert_06",0.0),"s2":("vert_07",0.0),"s3":("vert_13",0.0),
           "s4":("vert_20",0.0),"s5":("vert_23",20.0)}

def high_of(key): return HIGH_LAST if key=="s5" else HIGH_BASE
def sect_len(key): return LEAD+PRE_VOICE+NARR[f"{key}_voice"]+POST_VOICE+SWELL+high_of(key)+TAIL
def anchors(key):
    v0=LEAD+PRE_VOICE; v1=v0+NARR[f"{key}_voice"]; sw0=v1+POST_VOICE
    full0=sw0+SWELL; full1=full0+high_of(key); end=full1+TAIL
    mid0=full1-5.0  # 中段金句在副歌后半段叠
    return dict(v0=v0,v1=v1,sw0=sw0,full0=full0,full1=full1,mid0=mid0,end=end)

intro_seg = COVER_D + HOOK_LEAD + NARR["intro"] + 1.5
outro_seg = LEAD + NARR["outro"] + 5.0

starts={}; t=0.0
starts["intro"]=(t,intro_seg); t+=intro_seg
for k in ["s1","s2","s3","s4","s5"]:
    sl=sect_len(k); starts[k]=(t,sl); t+=sl
starts["outro"]=(t,outro_seg); t+=outro_seg
TOTAL=round(t,3)
print(f"TOTAL: {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ============ 音频段构建 ============
Path("build/segs").mkdir(parents=True, exist_ok=True)

# intro：2006 MV 作低音 ambient bed（origin），voice 上叠
intro_voice_at = COVER_D + HOOK_LEAD
run(["ffmpeg","-v","error","-i",f"{C}/vert_06.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(intro_voice_at*1000)}|{int(intro_voice_at*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=2:{2+intro_seg},asetpts=PTS-STARTPTS,volume=0.16,afade=t=in:st=0:d=1.4,afade=t=out:st={intro_seg-1.8}:d=1.8[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_intro.wav","-y"])

def build_song_seg(key):
    a=anchors(key); seg_len=starts[key][1]; clip,mseek=SOURCES[key]
    v0=a["v0"]; sw0=a["sw0"]; full0=a["full0"]; full1=a["full1"]
    ve=(f"(lt(t,{LEAD}))*0"
        f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
        f"+(between(t,{v0},{sw0}))*{BED}"
        f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
        f"+(gte(t,{full0}))*1.0")
    out=f"build/segs/seg_{key}.wav"
    run(["ffmpeg","-v","error","-i",f"{C}/{clip}.mp4","-i",f"{A}/{key}_voice.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,{MGAIN.get(key,'')}"
         f"atrim={mseek}:{mseek+seg_len},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,"
         f"afade=t=out:st={full1}:d={seg_len-full1}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])

for k in ["s1","s2","s3","s4","s5"]:
    print(f"building seg_{k}..."); build_song_seg(k)

# outro：2023 作低床
run(["ffmpeg","-v","error","-i",f"{C}/vert_23.mp4","-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=30:{30+outro_seg},asetpts=PTS-STARTPTS,volume=0.18,afade=t=in:st=0:d=1.2,afade=t=out:st={outro_seg-2.8}:d=2.8[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])

Path("build/segs/seglist.txt").write_text(
    "".join(f"file 'seg_{k}.wav'\n" for k in ["intro","s1","s2","s3","s4","s5","outro"]), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "planned:", TOTAL)

import shutil
shutil.copy("master.wav","hf/master.wav")

# clips_seg：每段从 mseek 输出端预切（HF 控不了 currentTime）
Path("hf/clips_seg").mkdir(exist_ok=True)
for k in ["s1","s2","s3","s4","s5"]:
    clip,mseek=SOURCES[k]; seg_len=starts[k][1]
    run(["ffmpeg","-v","error","-ss",str(mseek),"-i",f"{C}/{clip}.mp4","-t",str(seg_len),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
         f"hf/clips_seg/{k}.mp4","-y"])
    print(f"clips_seg/{k}.mp4 ({seg_len:.1f}s from {mseek}s of {clip})")
print("audio + clips build done")

# ============ HTML ============
SONGS=[
 dict(key="s1",no="01",year="2006",name="最初的翅膀",occasion="《爱杀十七》片尾曲 · 官方 MV",
      stage="起点",keyword="原始",tag="那时候的翅膀，真的还是隐形的",
      pri="#E6BDB4",acc="#EBCF96",clip="vert_06"),
 dict(key="s2",no="02",year="2007",name="飞上春晚",occasion="中央电视台 春节联欢晚会",
      stage="破圈",keyword="国民",tag="从偶像金曲，飞成一代人的国民记忆",
      pri="#EBCF96",acc="#F4EFE3",clip="vert_07"),
 dict(key="s3",no="03",year="2013",name="隐形，变成有形",occasion="《全能星战》隐形的翅膀 ＋ 有形的翅膀",
      stage="回望",keyword="长出",tag="隐形的翅膀，终于被时间看见",
      pri="#BB95DE",acc="#9DD6F9",clip="vert_13"),
 dict(key="s4",no="04",year="2020",name="唱给自己听",occasion="《未定义》线上演唱会",
      stage="情绪回流",keyword="接住",tag="这首歌，也接住过唱歌的人",
      pri="#A6BBDE",acc="#F4EFE3",clip="vert_20"),
 dict(key="s5",no="05",year="2023",name="还在往前飞",occasion="《声生不息·宝岛季》金曲盛典",
      stage="现在",keyword="往前",tag="十七年后，她还在往前飞",
      pri="#C6E4F4",acc="#EBCF96",clip="vert_23"),
]
for s in SONGS: s["mid"]=MID[f'{s["key"]}_mid']

abs_a={}
for s in SONGS:
    k=s["key"]; base=starts[k][0]; a=anchors(k)
    abs_a[k]={kk:round(base+vv,3) for kk,vv in a.items()}; abs_a[k]["start"]=round(base,3)
INTRO_T=0.0; INTRO_D=intro_seg
OUTRO_T=starts["outro"][0]; OUTRO_D=outro_seg

# footage（每段一段 video，交替 track 0/6）
foot_tracks=[0,6,0,6,0]; foot_html=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=abs_a[k]
    foot_html.append(f'<video id="fv_{k}" class="fv clip" data-start="{fmt(a["start"])}" data-duration="{fmt(starts[k][1])}" data-track-index="{foot_tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>')

tint_html=[]; chrome_html=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=abs_a[k]; d=starts[k][1]
    tint_html.append(f'<div id="tint_{k}" class="clip tint tint_{k}" data-start="{fmt(a["start"])}" data-duration="{fmt(d)}" data-track-index="{10+i}"></div>')
    rail="".join(f'<div class="rail-dot{" active" if j==i else ""}{" past" if j<i else ""}" style="top:{8+j*20}%"><span class="rail-tick">0{j+1}</span></div>' for j in range(5))
    chrome_html.append(f'''<div id="chrome_{k}" class="clip chrome chrome_{k}" data-start="{fmt(a["start"])}" data-duration="{fmt(d)}" data-track-index="{20+i}">
  <div class="rail"><div class="rail-bar"></div>{rail}</div>
  <div class="card">
    <div class="card-stage"><span class="dot"></span>{s["stage"]}</div>
    <div class="card-year">{s["year"]}</div>
    <div class="card-name">{s["name"]}</div>
    <div class="card-occ">{s["occasion"]}</div>
  </div>
  <div class="kw" id="kw_{k}">{s["keyword"]}</div>
  <div class="mid" id="mid_{k}">{s["mid"]}</div>
  <div class="ytag" id="ytag_{k}"><b>{s["year"]}</b>｜{s["tag"]}</div>
</div>''')

cover_html=f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D+0.6)}" data-track-index="30">
  <div class="cv-bg cv-bg-y"></div><div class="cv-bg cv-bg-m"></div>
  <div class="cv-veil"></div><div class="cv-grain"></div>
  <div class="cv-portraits">
    <div class="cv-pf"><div class="cv-img cv-img-y"></div><div class="cv-cap"><span class="cv-yy">2006</span><span class="cv-rl">最初</span></div></div>
    <div class="cv-link"><span class="cv-feather">↝</span></div>
    <div class="cv-pf"><div class="cv-img cv-img-m"></div><div class="cv-cap"><span class="cv-yy">2023</span><span class="cv-rl">此刻</span></div></div>
  </div>
  <div class="cv-main">
    <div class="cv-eyebrow">同一首歌 · 5 个版本 · 一条飞了 17 年的时间线</div>
    <h1 class="cv-title">《隐形的翅膀》<br>飞了 17 年</h1>
    <div class="cv-sub">从一首剧集片尾曲，<br>到一代人的国民记忆</div>
  </div>
  <div class="cv-rail">
    <div class="cv-yrs">2006 ── 2007 ── 2013 ── 2020 ── 2023</div>
  </div>
</div>'''

hook_d=INTRO_D-COVER_D
hook_tags=[(s["year"],s["stage"],s["name"]) for s in SONGS]
hook_lines="".join(f'<div class="hk-line" id="hk_{i+1}"><span class="hk-y">{y}</span><span class="hk-s">{st}</span><span class="hk-n">{nm}</span></div>' for i,(y,st,nm) in enumerate(hook_tags))
hook_html=f'''<div id="hook" class="clip hook" data-start="{fmt(COVER_D)}" data-duration="{fmt(hook_d)}" data-track-index="31">
  <div class="hk-grad"></div>
  <div class="hk-h">同一首歌，<br>飞了十七年</div>
  {hook_lines}
</div>'''

outro_rail="".join(f'<div class="ot-line"><span class="ot-y">{s["year"]}</span><span class="ot-n">{s["name"]}</span></div>' for s in SONGS)
outro_html=f'''<div id="outro" class="clip outroblk" data-start="{fmt(OUTRO_T)}" data-duration="{fmt(OUTRO_D)}" data-track-index="32">
  <div class="ot-bg"></div>
  <div class="ot-rail">{outro_rail}</div>
  <h2 class="ot-h">小时候听，是相信自己会飞；<br>长大后再听，<br>是发现自己真的飞过了很多风。</h2>
  <p class="ot-q">你第一次听《隐形的翅膀》，是哪一年？<br>哪个版本，最戳你？</p>
</div>'''

audio_html=f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

CSS='''
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#070A14;font-family:"Noto Serif SC","Songti SC",serif;color:#F4EFE3;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0}
.tint{position:absolute;inset:0;z-index:2;opacity:0}
.tint_s1{background:linear-gradient(180deg,rgba(230,189,180,.16) 0%,rgba(20,12,14,.34) 42%,rgba(5,7,14,.74) 100%)}
.tint_s2{background:linear-gradient(180deg,rgba(235,207,150,.16) 0%,rgba(28,20,8,.40) 44%,rgba(5,7,14,.76) 100%)}
.tint_s3{background:linear-gradient(180deg,rgba(150,110,200,.18) 0%,rgba(18,12,30,.46) 44%,rgba(5,7,14,.80) 100%)}
.tint_s4{background:linear-gradient(180deg,rgba(120,150,200,.14) 0%,rgba(10,16,30,.50) 44%,rgba(4,6,14,.82) 100%)}
.tint_s5{background:linear-gradient(180deg,rgba(150,200,235,.14) 0%,rgba(10,22,32,.44) 44%,rgba(5,8,16,.78) 100%)}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none}
.chrome_s1{--pri:#E6BDB4;--acc:#EBCF96}.chrome_s2{--pri:#EBCF96;--acc:#F4EFE3}
.chrome_s3{--pri:#BB95DE;--acc:#9DD6F9}.chrome_s4{--pri:#A6BBDE;--acc:#F4EFE3}.chrome_s5{--pri:#C6E4F4;--acc:#EBCF96}

/* 左侧时间线轨 */
.rail{position:absolute;top:150px;left:60px;bottom:240px;width:10px;opacity:0}
.rail-bar{position:absolute;top:0;bottom:0;left:4px;width:2px;background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.22),rgba(255,255,255,.05))}
.rail-dot{position:absolute;left:-20px;width:48px;height:48px;border-radius:50%;background:rgba(16,18,28,.9);border:2px solid rgba(255,255,255,.22);display:flex;align-items:center;justify-content:center}
.rail-dot.past{background:rgba(70,70,82,.7);border-color:rgba(255,255,255,.3)}
.rail-dot.active{background:var(--pri);border-color:var(--pri);box-shadow:0 0 32px var(--pri),0 0 70px rgba(255,255,255,.22);transform:scale(1.18)}
.rail-tick{font-family:"Noto Sans SC",sans-serif;font-size:22px;font-weight:800;color:rgba(255,255,255,.72)}
.rail-dot.active .rail-tick{color:rgba(16,18,28,.95)}

/* 右上玻璃歌名卡 */
.card{position:absolute;top:138px;right:52px;width:648px;padding:44px 46px 42px;border-radius:26px;background:linear-gradient(160deg,rgba(255,255,255,.10),rgba(255,255,255,.03));backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);border:1.5px solid rgba(255,255,255,.18);box-shadow:0 36px 96px rgba(0,0,0,.6);opacity:0}
.card-stage{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;letter-spacing:.12em;color:var(--acc);display:inline-flex;align-items:center;gap:14px;margin-bottom:18px}
.card-stage .dot{width:12px;height:12px;border-radius:50%;background:var(--pri);box-shadow:0 0 16px var(--pri)}
.card-year{font-family:"Noto Sans SC",sans-serif;font-size:26px;font-weight:800;letter-spacing:.30em;color:rgba(255,255,255,.6);padding:7px 18px;border:1.5px solid rgba(255,255,255,.24);border-radius:999px;display:inline-block;margin-bottom:20px}
.card-name{font-size:76px;font-weight:800;line-height:1.06;color:#F7F2E8;letter-spacing:-1px;margin-bottom:22px}
.card-occ{font-family:"Noto Sans SC",sans-serif;font-size:27px;line-height:1.5;color:rgba(255,255,255,.78);font-weight:500;letter-spacing:.02em}

/* 大关键词 */
.kw{position:absolute;left:0;right:0;bottom:430px;text-align:center;font-family:"Noto Serif SC",serif;font-size:300px;font-weight:800;line-height:.9;color:var(--pri);opacity:0;letter-spacing:-6px;mix-blend-mode:screen;filter:drop-shadow(0 8px 60px rgba(255,255,255,.16))}
/* 中段金句 */
.mid{position:absolute;left:80px;right:80px;bottom:300px;font-family:"Noto Serif SC",serif;font-size:52px;font-weight:500;line-height:1.42;text-align:center;color:rgba(244,239,227,.96);opacity:0;letter-spacing:.02em;text-shadow:0 4px 24px rgba(0,0,0,.6)}
/* 底部一行短评 */
.ytag{position:absolute;left:64px;right:64px;bottom:150px;font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:500;text-align:center;color:rgba(244,239,227,.92);opacity:0;letter-spacing:.02em;text-shadow:0 3px 18px rgba(0,0,0,.7)}
.ytag b{color:var(--acc);font-weight:800;margin-right:6px}

/* 封面 */
.cover{position:absolute;inset:0;z-index:50;background:#070A14;overflow:hidden}
.cv-bg{position:absolute;top:-8%;width:62%;height:64%;background-size:cover;background-position:center;filter:blur(46px) brightness(.42);opacity:.5;transform:scale(1.25)}
.cv-bg-y{left:-8%;background-image:url("cover_assets/young.jpg");filter:blur(46px) brightness(.45) saturate(.8)}
.cv-bg-m{right:-8%;background-image:url("cover_assets/mature.jpg");filter:blur(46px) brightness(.40) saturate(.95)}
.cv-veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(7,10,20,.42) 0%,rgba(7,10,20,.66) 40%,rgba(7,10,20,.93) 100%)}
.cv-grain{position:absolute;inset:0;background-image:radial-gradient(circle at 12% 30%,rgba(255,255,255,.04) 0 .5px,transparent .8px),radial-gradient(circle at 78% 68%,rgba(255,255,255,.04) 0 .5px,transparent .8px);background-size:200px 200px,240px 240px;opacity:.5}
.cv-portraits{position:absolute;top:150px;left:0;right:0;display:flex;align-items:center;justify-content:center;gap:40px}
.cv-pf{display:flex;flex-direction:column;align-items:center;gap:16px}
.cv-img{width:300px;height:300px;border-radius:50%;background-size:cover;background-position:center top;border:4px solid rgba(255,255,255,.92);box-shadow:0 24px 60px rgba(0,0,0,.55),inset 0 0 0 1px rgba(255,255,255,.15)}
.cv-img-y{background-image:url("cover_assets/young.jpg");background-position:center 28%}
.cv-img-m{background-image:url("cover_assets/mature.jpg");background-position:center 32%}
.cv-cap{display:flex;flex-direction:column;align-items:center;gap:4px}
.cv-yy{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:800;letter-spacing:.16em;color:#EBCF96}
.cv-rl{font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:500;letter-spacing:.30em;color:rgba(244,239,227,.7)}
.cv-link{display:flex;align-items:center;transform:translateY(-26px)}
.cv-feather{font-family:"Noto Serif SC",serif;font-size:84px;font-weight:300;color:rgba(235,207,150,.7);text-shadow:0 0 30px rgba(235,207,150,.5)}
.cv-main{position:absolute;top:760px;left:72px;right:72px}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:700;letter-spacing:.16em;color:#EBCF96;margin-bottom:28px}
.cv-title{font-family:"Noto Serif SC",serif;font-size:128px;font-weight:800;line-height:1.08;color:#F7F2E8;letter-spacing:-2px;margin-bottom:34px}
.cv-sub{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:500;color:rgba(244,239,227,.8);line-height:1.42}
.cv-rail{position:absolute;bottom:120px;left:72px;right:72px}
.cv-yrs{font-family:"Noto Sans SC",sans-serif;font-size:30px;letter-spacing:.16em;font-weight:800;color:rgba(235,207,150,.92);text-align:center}

/* Hook */
.hook{position:absolute;inset:0;z-index:49;background:linear-gradient(180deg,#0A0F1C 0%,#070A14 100%)}
.hk-grad{position:absolute;inset:0;background:radial-gradient(ellipse at 30% 18%,rgba(235,207,150,.08) 0,transparent 50%),radial-gradient(ellipse at 70% 82%,rgba(150,110,200,.08) 0,transparent 50%)}
.hk-h{position:absolute;top:300px;left:80px;right:80px;font-family:"Noto Serif SC",serif;font-size:96px;font-weight:800;line-height:1.1;color:#F7F2E8;letter-spacing:-1px;opacity:0}
.hk-line{position:absolute;left:90px;right:90px;display:flex;align-items:baseline;gap:24px;opacity:0}
#hk_1{top:760px}#hk_2{top:920px}#hk_3{top:1080px}#hk_4{top:1240px}#hk_5{top:1400px}
.hk-y{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:800;color:#EBCF96;letter-spacing:.12em;min-width:108px}
.hk-s{font-family:"Noto Sans SC",sans-serif;font-size:26px;font-weight:600;color:rgba(157,214,249,.85);letter-spacing:.10em;min-width:150px}
.hk-n{font-family:"Noto Serif SC",serif;font-size:50px;font-weight:700;color:#F4EFE3;margin-left:auto}

/* Outro */
.outroblk{position:absolute;inset:0;z-index:48;background:radial-gradient(ellipse at 50% 36%,#14182A 0%,#070A14 70%)}
.ot-bg{position:absolute;inset:0;background:radial-gradient(circle at 50% 46%,rgba(235,207,150,.10) 0,transparent 46%)}
.ot-rail{position:absolute;top:300px;left:120px;right:120px;display:flex;flex-direction:column;gap:6px}
.ot-line{display:flex;align-items:baseline;gap:26px;padding:8px 0;opacity:0}
.ot-y{font-family:"Noto Sans SC",sans-serif;font-size:26px;font-weight:800;color:#EBCF96;letter-spacing:.14em;min-width:108px}
.ot-n{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:700;color:#F4EFE3}
.ot-h{position:absolute;top:760px;left:96px;right:96px;font-family:"Noto Serif SC",serif;font-size:66px;font-weight:700;line-height:1.34;color:#F7F2E8;letter-spacing:-.5px;opacity:0}
.ot-q{position:absolute;top:1340px;left:96px;right:96px;font-family:"Noto Sans SC",sans-serif;font-size:38px;font-weight:600;line-height:1.5;color:#EBCF96;letter-spacing:.04em;opacity:0}
'''

def js_ch(s,i):
    k=s["key"]; a=abs_a[k]; base=a["start"]; sw0=a["sw0"]; full0=a["full0"]; full1=a["full1"]; mid0=a["mid0"]; end=a["end"]; fo=end-1.0
    return f'''
// ---- {s["year"]} {s["name"]} ----
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.08}},{{opacity:1,scale:1.0,duration:1.6,ease:"power2.out"}},{fmt(base)});
tl.to("#tint_{k}",{{opacity:1,duration:1.4,ease:"power1.out"}},{fmt(base)});
tl.fromTo(".chrome_{k} .rail",{{opacity:0}},{{opacity:1,duration:.8}},{fmt(base+0.3)});
tl.fromTo(".chrome_{k} .card",{{opacity:0,x:60,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{fmt(base+0.5)});
tl.fromTo(".chrome_{k} #ytag_{k}",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.7,ease:"power1.out"}},{fmt(base+1.0)});
tl.to(".chrome_{k} .card",{{opacity:0,y:-12,duration:.55,ease:"power2.in"}},{fmt(sw0-0.1)});
tl.to(".chrome_{k} #ytag_{k}",{{opacity:0,duration:.5,ease:"power1.in"}},{fmt(sw0-0.1)});
tl.fromTo(".chrome_{k} #kw_{k}",{{opacity:0,scale:.92}},{{opacity:.30,scale:1.0,duration:1.6,ease:"power3.out"}},{fmt(full0-0.4)});
tl.to(".chrome_{k} #kw_{k}",{{opacity:.46,duration:1.2,ease:"sine.inOut"}},{fmt(full0+1.4)});
tl.fromTo(".chrome_{k} #mid_{k}",{{opacity:0,y:28}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(mid0)});
tl.to(".chrome_{k} #mid_{k}",{{opacity:0,y:-12,duration:.55,ease:"power2.in"}},{fmt(end-1.3)});
tl.to(".chrome_{k} #kw_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(end-1.3)});
tl.to("#fv_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(fo)});
tl.set("#fv_{k}",{{opacity:0}},{fmt(end)});
tl.to("#tint_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(fo)});
tl.set("#tint_{k}",{{opacity:0}},{fmt(end)});
tl.to(".chrome_{k} .rail",{{opacity:0,duration:.6,ease:"power1.in"}},{fmt(end-0.4)});
tl.set(".chrome_{k} .rail",{{opacity:0}},{fmt(end)});
'''

hook_anim="".join(f'tl.fromTo("#hk_{i+1}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{fmt(COVER_D+0.9+i*1.5)});tl.to("#hk_{i+1}",{{opacity:.45,duration:.6}},{fmt(COVER_D+0.9+i*1.5+1.0)});\n' for i in range(5))
outro_anim="".join(f'tl.fromTo(".ot-rail .ot-line:nth-child({i+1})",{{opacity:0,x:-18}},{{opacity:.9,x:0,duration:.5,ease:"power2.out"}},{fmt(OUTRO_T+0.4+i*0.16)});\n' for i in range(5))

JS=f'''
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-img-y",{{opacity:1}},0);tl.set(".cv-img-m",{{opacity:1}},0);
tl.fromTo(".cv-link",{{opacity:.4}},{{opacity:1,duration:1.6,yoyo:true,repeat:1,ease:"sine.inOut"}},0.4);
tl.to(".cv-portraits",{{y:-8,duration:2.0,yoyo:true,repeat:1,ease:"sine.inOut"}},0.5);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D-0.6)});
tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});
tl.set("#hook",{{opacity:1}},{fmt(COVER_D)});
tl.fromTo(".hk-h",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{fmt(COVER_D+0.2)});
{hook_anim}
tl.to(".hk-h",{{opacity:.5,duration:.6}},{fmt(INTRO_D-2.0)});
tl.to("#hook",{{opacity:0,duration:.8,ease:"power2.in"}},{fmt(INTRO_D-0.8)});
tl.set("#hook",{{opacity:0}},{fmt(INTRO_D)});
{''.join(js_ch(s,i) for i,s in enumerate(SONGS))}
tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.8,ease:"power2.out"}},{fmt(OUTRO_T)});
{outro_anim}
tl.fromTo(".ot-h",{{opacity:0,y:32}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{fmt(OUTRO_T+1.8)});
tl.fromTo(".ot-q",{{opacity:0,y:14}},{{opacity:.96,y:0,duration:.7,ease:"power2.out"}},{fmt(OUTRO_T+4.2)});
tl.to("#outro",{{opacity:1,duration:.1}},{fmt(TOTAL-0.2)});
'''

html=f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
{chr(10).join(foot_html)}
{chr(10).join(tint_html)}
{chr(10).join(chrome_html)}
{cover_html}
{hook_html}
{outro_html}
{audio_html}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script>
</body></html>'''

Path("hf/index.html").write_text(html,encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"yxdcb-timeline"}',encoding="utf-8")
print("index.html written:",len(html),"bytes; TOTAL",TOTAL)
