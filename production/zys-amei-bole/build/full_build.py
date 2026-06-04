#!/usr/bin/env python3
"""全片构建：《没有张雨生，就没有最初的阿妹》8首倒数 + 彩蛋 + 片头片尾。
复用样片验证过的：音频包络(床→swell→副歌全量→trans duck)、章节chrome、letterbox、ducking、金黑红主题。
屏幕文案已重写为自然口径(用户反馈"推开的天后之路"不通顺)。Credit 用事实修正版。
渲染后必须 ffmpeg mux master.wav。
用法: python build/full_build.py            # 全量(音频+html+footage)
      FRAMES_ONLY=1 python build/full_build.py  # 只出 footage + 每首副歌QA帧，不建音频
"""
import subprocess, wave, contextlib, json, os, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
A = BASE/"audio"; C = BASE/"clips"; HF = BASE/"hf"; RAW = BASE/"raw"
SEG = BASE/"build"/"segs"; SEG.mkdir(parents=True, exist_ok=True)
(HF/"clips_seg").mkdir(parents=True, exist_ok=True)
QA = BASE/"qa"/"full"; QA.mkdir(parents=True, exist_ok=True)
VFILL = str(BASE.parent.parent/"tools"/"video"/"vfill.sh")
FRAMES_ONLY = os.environ.get("FRAMES_ONLY") == "1"
HTML_ONLY = os.environ.get("HTML_ONLY") == "1"   # 仅重生 html（复用已有 footage/master）

def dur(p):
    with contextlib.closing(wave.open(str(p),'r')) as w: return round(w.getnframes()/w.getframerate(),3)
def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

# ============ 节奏常量（同样片）============
LEAD=0.15; PRE=0.8; POST=1.2; SWELL=1.5; BED=0.20; DUCK=0.34
COVER_D=4.8; HOOK_TAIL=3.0; OUTRO_TAIL=4.0

# ============ 歌曲表（倒数 8→1 + 彩蛋）============
# chorus_raw=源里副歌起点(秒)；crop=vfill letterbox 裁切(去烧词/台标)；high=副歌展示时长
SONGS = [
 dict(key="s8", no="08", name="最爱的人<br>伤我最深", flat="最爱的人伤我最深",
      credit="<b>张雨生 × 张惠妹 合唱</b><br>1996《两伊战争—红色热情》", tag="第一次被听见",
      pri="#C8463A", acc="#E3C16A", src=None, chorus_raw=90.0, crop=None, high=26.5, mode="montage",
      music_src="s8_yt.webm", music_chorus=90.0,
      show=["这是一次合唱","也是一次被听见"]),
 dict(key="s7", no="07", name="水蓝色眼泪", flat="水蓝色眼泪",
      credit="<b>张雨生 词 · 曲 · 制作</b><br>1996《姊妹》", tag="抒情里的重量",
      pri="#6E8CA8", acc="#AECBE0", src="s7_yt.webm", chorus_raw=236.0, crop="1920:1036:0:22", high=28, mode="window",
      show=["她的悲伤","是有重量的"]),
 dict(key="s6", no="06", name="姊妹", flat="姊妹",
      credit="<b>张雨生 词 · 曲 · 制作</b><br>1996《姊妹》", tag="身份亮相",
      pri="#C9A24B", acc="#E8D08A", src="s6_yt.webm", chorus_raw=140.0, crop="1600:930:0:20", high=28, mode="window",
      show=["她不是被包装出来的","她带着来处，站上舞台"]),
 dict(key="s5", no="05", name="一想到你呀", flat="一想到你呀",
      credit="<b>张雨生 词 · 曲 · 制作</b><br>1997《Bad Boy》", tag="生命力",
      pri="#E0A23A", acc="#F4CC72", src="s5_yt.webm", chorus_raw=170.0, crop="712:392:0:14", high=28, mode="window",
      show=["她的快乐不是甜","是生命力"]),
 dict(key="s4", no="04", name="孤单Tequila", flat="孤单Tequila",
      credit="<b>张雨生 词 · 曲 · 制作</b><br>1997《Bad Boy》", tag="野性",
      pri="#B5342E", acc="#E08A3A", src="s4_yt_live2010.webm", chorus_raw=150.0, crop="1280:740:80:150", high=28, mode="window",
      show=["张雨生给她的","不只是安全牌，还有野性"]),
 dict(key="s3", no="03", name="Bad Boy", flat="Bad Boy",
      credit="<b>张雨生 词 · 曲 · 制作</b><br>1997《Bad Boy》", tag="天后确立",
      pri="#C8463A", acc="#E3C16A", src="s3_yt.webm", chorus_raw=125.0, crop="712:410:0:12", high=30, mode="window",
      show=["这不是一首普通主打","是天后位置的确认键"]),
 dict(key="s2", no="02", name="当我开始<br>偷偷地想你", flat="当我开始偷偷地想你",
      credit="<b>张雨生 词 · 曲（遗作）</b><br>1999《我可以抱你吗？爱人》", tag="遗作回声",
      pri="#5E7596", acc="#A6B8D0", src="s2_yt.webm", chorus_raw=150.0, crop="712:368:0:8", high=28, mode="window",
      show=["人不在了","歌还在，替他陪着她"]),
 dict(key="s1", no="01", name="不顾一切", flat="不顾一切",
      credit="<b>张雨生 词 · 曲 · 制作（遗作）</b><br>2000《不顾一切》", tag="未完成的守护",
      pri="#C9A24B", acc="#E8D08A", src="s1_yt.webm", chorus_raw=216.0, crop="696:316:8:66", high=34, mode="window",
      show=["他点亮了最初的路","她把这条路，唱成了时代"]),
 dict(key="egg", no="·", name="听你 · 听我", flat="听你听我",
      credit="<b>阿妹献给雨生</b><br>词 光禹 · 曲 陈志远 · 1997《给雨生的歌》", tag="她的回答",
      pri="#B89A5A", acc="#E3D2A0", src="egg_yt.webm", chorus_raw=158.0, crop="712:372:0:8", high=26, mode="montage",
      music_src="egg_yt.webm", music_chorus=150.0,
      show=["前面八首，是他把她推上舞台","这一首，是她唱给他的回答"]),
]

NARR = {k: dur(A/f"{k}.wav") for k in
        ["intro","outro","egg_voice"] + [f"{s['key']}_voice" for s in SONGS if s['key']!='egg']
        + [f"{s['key']}_trans" for s in SONGS if s['key'] not in ('egg',)]}

def full0(voice): return LEAD+PRE+voice+POST+SWELL
def seg_anchors(key, high, has_trans=True):
    vk = "egg_voice" if key=="egg" else f"{key}_voice"
    voice = NARR[vk]; tr = NARR.get(f"{key}_trans", 0.0) if has_trans else 0.0
    v0=LEAD+PRE; v1=v0+voice; sw0=v1+POST; f0=sw0+SWELL; f1=f0+high
    tr0=f1; tr1=tr0+tr; end=tr1+1.0
    return dict(voice=voice,tr=tr,v0=v0,v1=v1,sw0=sw0,f0=f0,f1=f1,tr0=tr0,tr1=tr1,end=end,seg=end)

# ============ 时间轴 ============
hook_seg = LEAD + NARR["intro"] + HOOK_TAIL
outro_seg = LEAD + NARR["outro"] + OUTRO_TAIL
plan=[("cover",COVER_D),("hook",hook_seg)]
for s in SONGS:
    a = seg_anchors(s["key"], s["high"], has_trans=(s["key"]!="egg"))
    s["_a"]=a; plan.append((s["key"], a["seg"]))
plan.append(("outro",outro_seg))
T={}; t=0.0
for k,d in plan: T[k]=(round(t,3),d); t+=d
TOTAL=round(t,3)
print(f"TOTAL = {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ============ FOOTAGE：每首切窗 + letterbox ============
def prep_footage(s):
    key=s["key"]; a=s["_a"]; seg=a["seg"]
    out=HF/"clips_seg"/f"{key}.mp4"
    if s["mode"]=="montage":   # 蒙太奇片(s8 师徒 / egg 纪念)，预建于 clips/vert_<key>.mp4
        vsrc = C/f"vert_{key}.mp4"
        if vsrc.exists(): shutil.copy(vsrc, out)
        else: print(f"WARN: {vsrc.name} missing"); return
    else:
        mseek = max(s["chorus_raw"] - a["f0"], 0.0)   # 让副歌落在 showcase
        cut = C/f"cut_{key}.mp4"; vert=C/f"vert_{key}.mp4"
        run(["ffmpeg","-v","error","-i",str(RAW/s["src"]),"-ss",str(mseek),"-t",str(seg+1.5),
             "-c:v","libx264","-preset","veryfast","-r","30","-c:a","aac",str(cut),"-y"])
        run(["bash",VFILL,str(cut),str(vert),s["crop"],"-0.34","1.05"])
        run(["ffmpeg","-v","error","-i",str(vert),"-an","-c:v","libx264","-preset","veryfast",
             "-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p",str(out),"-y"])
    # QA 帧：showcase 中点
    mid = a["f0"] + (a["f1"]-a["f0"])/2
    run(["ffmpeg","-v","error","-i",str(out),"-ss",str(round(mid,2)),"-frames:v","1",str(QA/f"{key}_show.png"),"-y"])
    print(f"footage {key}: {out.name} (showcase@{round(mid,1)}s)")

if not HTML_ONLY:
    for s in SONGS: prep_footage(s)
# hook 用 s8 蒙太奇做背景
if not (HF/"clips_seg"/"s8.mp4").exists(): print("WARN no s8 montage")

if FRAMES_ONLY:
    print("FRAMES_ONLY done — QA", QA); raise SystemExit(0)

# ============ AUDIO ============
def mk_bed(out,src,mseek,length,vol,fin,fout_d):
    run(["ffmpeg","-v","error","-i",str(src),"-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim={mseek}:{mseek+length},asetpts=PTS-STARTPTS,volume={vol},"
         f"afade=t=in:st=0:d={fin},afade=t=out:st={max(length-fout_d,0)}:d={fout_d},"
         f"atrim=0:{length},alimiter=limit=0.95[o]","-map","[o]","-ac","2","-ar","48000",str(out),"-y"])

DUET=str(RAW/"s8_yt.webm")
# cover bed
mk_bed(SEG/"seg_cover.wav",DUET,28.0,COVER_D,0.16,1.0,0.6)
# hook
voice_at=LEAD+0.3
run(["ffmpeg","-v","error","-i",DUET,"-i",str(A/"intro.wav"),"-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=32.5:{32.5+hook_seg},asetpts=PTS-STARTPTS,volume=0.18,"
     f"afade=t=in:st=0:d=1.0,afade=t=out:st={hook_seg-1.5}:d=1.5[m];"
     f"[v][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{hook_seg},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000",str(SEG/"seg_hook.wav"),"-y"])

def build_song_seg(s):
    key=s["key"]; a=s["_a"]; seg=a["seg"]
    if s["mode"]=="montage":
        src = str(RAW/s["music_src"]); mchorus = s["music_chorus"]
    else:
        src = str(RAW/s["src"]); mchorus = s["chorus_raw"]
    mseek = max(mchorus - a["f0"], 0.0)
    v0=a["v0"]; sw0=a["sw0"]; f0=a["f0"]; f1=a["f1"]; tr0=a["tr0"]; tr1=a["tr1"]
    has_tr = a["tr"]>0
    ve=(f"(lt(t,{LEAD}))*0"
        f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
        f"+(between(t,{v0},{sw0}))*{BED}"
        f"+(between(t,{sw0},{f0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
        f"+(between(t,{f0},{f1}))*1.0")
    if has_tr:
        ve+=(f"+(between(t,{f1},{f1+0.5}))*(1.0-{1.0-DUCK}*(t-{f1})/0.5)"
             f"+(gte(t,{f1+0.5}))*{DUCK}")
    else:
        ve+=f"+(gte(t,{f1}))*1.0"
    inputs=["-i",src,"-i",str(A/('egg_voice.wav' if key=='egg' else key+'_voice.wav'))]
    fc=(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[v1];")
    mixn=2
    if has_tr:
        inputs+=["-i",str(A/f"{key}_trans.wav")]
        fc+=f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(tr0*1000)}|{int(tr0*1000)},volume=2.0[v2];"
        mixn=3
    fc+=(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim={mseek}:{mseek+seg},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,"
         f"afade=t=out:st={a['end']-1.0}:d=1.0[m];")
    mixlbl="[v1][m]" if not has_tr else "[v1][v2][m]"
    fc+=f"{mixlbl}amix=inputs={mixn}:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95[o]"
    run(["ffmpeg","-v","error",*inputs,"-filter_complex",fc,"-map","[o]","-ac","2","-ar","48000",str(SEG/f"seg_{key}.wav"),"-y"])

for s in SONGS:
    print("audio",s["key"]); build_song_seg(s)

# outro bed + voice
ov_at=LEAD
run(["ffmpeg","-v","error","-i",str(RAW/"s1_yt.webm"),"-i",str(A/"outro.wav"),"-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(ov_at*1000)}|{int(ov_at*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=120:{120+outro_seg},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=1.0,afade=t=out:st={outro_seg-2.5}:d=2.5[m];"
     f"[v][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_seg},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000",str(SEG/"seg_outro.wav"),"-y"])

order=["cover","hook"]+[s["key"] for s in SONGS]+["outro"]
(SEG/"list.txt").write_text("".join(f"file 'seg_{k}.wav'\n" for k in order),encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(SEG/"list.txt"),"-ac","2","-ar","48000",str(BASE/"master.wav"),"-y"])
shutil.copy(BASE/"master.wav", HF/"master.wav")
print("master:", dur(BASE/"master.wav"), "planned:", TOTAL)

# ============ HTML ============
def ct(k): return T[k][0]
RANKS=[s["no"] for s in SONGS if s["key"]!="egg"]
def rail(idx_active):
    nodes=""
    for i,r in enumerate(RANKS):
        cls=" active" if i==idx_active else (" past" if i<idx_active else "")
        nodes+=f'<div class="rk-dot{cls}" style="top:{8+i*11.6:.1f}%"><span class="rk-t">{r}</span></div>'
    return nodes

# footage 元素：每章一段；相邻交替 track 0/6
foot=[f'<video id="fv_hook" class="fv" data-start="{fmt(ct("hook"))}" data-duration="{fmt(hook_seg+0.3)}" data-track-index="0" src="clips_seg/s8.mp4" muted playsinline></video>']
tracks=[6,0,6,0,6,0,6,0,6]
for i,s in enumerate(SONGS):
    k=s["key"]; foot.append(
      f'<video id="fv_{k}" class="fv" data-start="{fmt(ct(k))}" data-duration="{fmt(s["_a"]["seg"])}" '
      f'data-track-index="{tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>')
foot.append(f'<video id="fv_outro" class="fv" data-start="{fmt(ct("outro"))}" data-duration="{fmt(outro_seg)}" data-track-index="0" src="clips_seg/s1.mp4" muted playsinline></video>')

scrim=[f'<div id="sc_{k}" class="scrim clip" data-start="{fmt(ct(k))}" data-duration="{fmt(T[k][1])}" data-track-index="{40+i}"></div>'
       for i,k in enumerate(["hook"]+[s["key"] for s in SONGS]+["outro"])]

# 章节 chrome
chrome=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=s["_a"]; base=ct(k)
    is_egg = k=="egg"
    railhtml = "" if is_egg else f'<div class="rk" id="rk_{k}"><div class="rk-bar"></div>{rail(i)}</div>'
    no_html = '<span class="card-egg">片尾彩蛋</span>' if is_egg else f'{s["no"]} <small>/ 08</small>'
    chrome.append(f'''<div id="chr_{k}" class="clip chrome" data-start="{fmt(base)}" data-duration="{fmt(a["seg"])}" data-track-index="{20+i}" style="--pri:{s['pri']};--acc:{s['acc']}">
 {railhtml}
 <div class="card" id="card_{k}">
   <div class="card-no">{no_html}</div>
   <div class="card-name">{s["name"]}</div>
   <div class="card-credit">{s["credit"]}</div>
   <div class="card-tag"><span class="d"></span>{s["tag"]}</div>
 </div>
 <div class="show" id="show_{k}">{''.join(f'<div class="show-l{j+1}">{ln}</div>' for j,ln in enumerate(s["show"]))}</div>
</div>''')

cover_html=f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="30">
 <div class="cv-bg"></div><div class="cv-veil"></div>
 <div class="cv-zys"></div><div class="cv-zys-cap">伯乐 · 张雨生</div>
 <div class="cv-amei"></div><div class="cv-amei-cap">张惠妹<small>最初的声音</small></div>
 <div class="cv-main">
   <div class="cv-kicker">华语唱片 · 黄金年代</div>
   <h1 class="cv-title">没有张雨生<br>就没有<b>最初的阿妹</b></h1>
   <div class="cv-sub">8 首歌，听懂天后的起点</div>
 </div>
 <div class="cv-foot">他先听见了她的声音 · 再把她推向时代中央</div>
 <div class="grain"></div>
</div>'''

hook_html=f'''<div id="hook" class="clip hook" data-start="{fmt(ct("hook"))}" data-duration="{fmt(hook_seg)}" data-track-index="31">
 <div class="hk-txt" id="hk_txt">
   <div class="hk-l1">这不是一份阿妹金曲盘点</div>
   <div class="hk-l2">是<span class="rd">张雨生</span>，把她推上舞台的8首歌</div>
 </div>
</div>'''

outro_html=f'''<div id="outro" class="clip outroblk" data-start="{fmt(ct("outro"))}" data-duration="{fmt(outro_seg)}" data-track-index="32">
 <div class="ot-veil"></div>
 <div class="ot-main">
   <h2 class="ot-h">他看见了阿妹<br>也把她<b>交给了时代</b></h2>
   <p class="ot-q">张雨生写给阿妹的歌里，你最爱哪一首？</p>
   <p class="ot-q2">《姊妹》《Bad Boy》还是《不顾一切》</p>
 </div>
</div>'''

audio_html=f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

CSS='''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#080503;font-family:"Noto Serif SC","Songti SC",serif;color:#F3EBDD;-webkit-font-smoothing:antialiased;}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.scrim{position:absolute;inset:0;z-index:2;opacity:0;background:linear-gradient(180deg,rgba(8,5,3,.55) 0%,rgba(8,5,3,.28) 32%,rgba(8,5,3,.60) 72%,rgba(8,5,3,.92) 100%);}
.grain{position:absolute;inset:0;z-index:3;pointer-events:none;mix-blend-mode:overlay;opacity:.45;background-image:radial-gradient(circle at 12% 22%,rgba(255,255,255,.05) 0 .5px,transparent 1px),radial-gradient(circle at 76% 64%,rgba(255,255,255,.05) 0 .5px,transparent 1px);background-size:180px 180px,220px 220px;}
.chrome{position:absolute;inset:0;z-index:5;pointer-events:none;}
.rk{position:absolute;top:150px;left:54px;bottom:230px;width:48px;opacity:0;}
.rk-bar{position:absolute;top:0;bottom:0;left:22px;width:2px;background:linear-gradient(180deg,transparent,rgba(201,162,75,.4),transparent);}
.rk-dot{position:absolute;left:0;width:44px;height:44px;border-radius:50%;background:rgba(20,12,8,.82);border:2px solid rgba(243,235,221,.20);display:flex;align-items:center;justify-content:center;}
.rk-dot.past{background:rgba(70,55,40,.6);border-color:rgba(243,235,221,.28);}
.rk-dot.active{background:var(--pri);border-color:var(--acc);box-shadow:0 0 26px var(--pri),0 0 56px rgba(201,162,75,.3);transform:scale(1.16);}
.rk-t{font-family:"Noto Sans SC",sans-serif;font-size:20px;font-weight:800;color:rgba(243,235,221,.7);}
.rk-dot.active .rk-t{color:#fff;}
.card{position:absolute;top:150px;right:54px;width:600px;padding:40px 44px 38px;border-radius:22px;background:linear-gradient(160deg,rgba(40,26,16,.55),rgba(18,11,7,.40));backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);border:1.5px solid rgba(201,162,75,.28);box-shadow:0 30px 80px rgba(0,0,0,.6);opacity:0;}
.card-no{font-family:"Noto Sans SC",sans-serif;font-size:32px;letter-spacing:.3em;font-weight:800;color:var(--acc);margin-bottom:8px;}
.card-no small{font-size:20px;color:rgba(243,235,221,.45);}
.card-egg{font-size:24px;letter-spacing:.3em;color:var(--acc);font-weight:800;}
.card-name{font-size:70px;font-weight:800;line-height:1.05;letter-spacing:-1px;color:#F3EBDD;margin:4px 0 20px;}
.card-credit{font-family:"Noto Sans SC",sans-serif;font-size:25px;line-height:1.5;color:rgba(243,235,221,.74);font-weight:500;}
.card-credit b{color:var(--acc);font-weight:700;}
.card-tag{margin-top:22px;display:inline-flex;align-items:center;gap:12px;font-family:"Noto Sans SC",sans-serif;font-size:28px;font-weight:700;color:var(--pri);}
.card-tag .d{width:11px;height:11px;border-radius:50%;background:var(--pri);box-shadow:0 0 14px var(--pri);}
.show{position:absolute;left:78px;right:78px;bottom:300px;opacity:0;}
.show div{font-weight:800;line-height:1.16;letter-spacing:-1px;text-shadow:0 4px 30px rgba(0,0,0,.75);}
.show-l1{font-size:74px;color:#F3EBDD;}
.show-l2{font-size:74px;color:var(--acc);font-weight:900;margin-top:6px;}
.show-l3{font-size:74px;color:var(--acc);font-weight:900;margin-top:6px;}
/* cover */
.cover{position:absolute;inset:0;z-index:60;background:#080503;overflow:hidden;}
.cv-bg{position:absolute;inset:-6%;background:url("cover_assets/studio.jpg") center/cover;filter:blur(26px) brightness(.4) contrast(1.05);transform:scale(1.15);}
.cv-veil{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 32%,rgba(178,58,46,.18) 0,transparent 55%),linear-gradient(180deg,rgba(8,5,3,.5) 0%,rgba(8,5,3,.4) 40%,rgba(8,5,3,.93) 100%);}
.cv-zys{position:absolute;right:96px;top:300px;width:300px;height:420px;background:url("cover_assets/zys.jpg") center top/cover;border-radius:8px;filter:grayscale(1) brightness(.62) contrast(1.18);-webkit-mask-image:linear-gradient(180deg,#000 60%,transparent);opacity:.5;box-shadow:0 30px 80px rgba(0,0,0,.6);}
.cv-zys-cap{position:absolute;right:104px;top:712px;font-family:"Noto Sans SC",sans-serif;font-size:24px;letter-spacing:.3em;color:rgba(201,162,75,.85);font-weight:700;}
.cv-amei{position:absolute;left:84px;top:236px;width:520px;height:600px;border-radius:14px;background:url("cover_assets/amei.jpg") center 20%/cover;box-shadow:0 36px 90px rgba(0,0,0,.65),inset 0 0 0 2px rgba(201,162,75,.5);filter:saturate(1.06) contrast(1.04);}
.cv-amei-cap{position:absolute;left:96px;top:856px;font-family:"Noto Sans SC",sans-serif;font-size:26px;letter-spacing:.18em;color:#E3C16A;font-weight:700;}
.cv-amei-cap small{display:block;font-size:19px;letter-spacing:.32em;color:rgba(243,235,221,.6);font-weight:500;margin-top:6px;}
.cv-main{position:absolute;left:84px;right:84px;bottom:300px;}
.cv-kicker{display:inline-block;font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:800;letter-spacing:.36em;color:#080503;background:#C9A24B;padding:9px 20px;border-radius:4px;margin-bottom:28px;}
.cv-title{font-size:104px;font-weight:900;line-height:1.1;letter-spacing:-2px;color:#F3EBDD;text-shadow:0 6px 40px rgba(0,0,0,.7);}
.cv-title b{color:#E3C16A;}
.cv-sub{margin-top:30px;font-size:42px;font-weight:600;color:rgba(243,235,221,.82);}
.cv-sub::before{content:"";display:inline-block;width:46px;height:3px;background:#B23A2E;vertical-align:middle;margin-right:18px;transform:translateY(-8px);}
.cv-foot{position:absolute;left:84px;bottom:128px;font-family:"Noto Sans SC",sans-serif;font-size:25px;color:rgba(243,235,221,.5);}
/* hook */
.hook{position:absolute;inset:0;z-index:32;}
.hk-txt{position:absolute;left:80px;right:80px;bottom:300px;opacity:0;}
.hk-l1{font-size:66px;font-weight:800;color:#F3EBDD;line-height:1.18;letter-spacing:-1px;}
.hk-l2{font-size:66px;font-weight:900;color:#E3C16A;line-height:1.18;letter-spacing:-1px;margin-top:10px;}
.hk-l2 .rd{color:#C8463A;}
/* outro */
.outroblk{position:absolute;inset:0;z-index:33;opacity:0;}
.ot-veil{position:absolute;inset:0;background:linear-gradient(180deg,rgba(8,5,3,.6),rgba(8,5,3,.86));}
.ot-main{position:absolute;left:84px;right:84px;bottom:360px;}
.ot-h{font-size:88px;font-weight:900;line-height:1.12;letter-spacing:-2px;color:#F3EBDD;}
.ot-h b{color:#E3C16A;}
.ot-q{margin-top:40px;font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:700;color:#F3EBDD;}
.ot-q2{margin-top:12px;font-family:"Noto Sans SC",sans-serif;font-size:30px;color:var(--acc,#E3C16A);color:#E3C16A;letter-spacing:.06em;}
.src{display:none;}
'''

def js_chapter(s,i):
    k=s["key"]; a=s["_a"]; base=ct(k)
    v=lambda x: fmt(base+x)
    is_egg=k=="egg"
    railjs = "" if is_egg else f'tl.fromTo("#rk_{k}",{{opacity:0}},{{opacity:1,duration:.8}},{v(0.3)});tl.to("#rk_{k}",{{opacity:0,duration:.6}},{v(a["end"]-0.6)});tl.set("#rk_{k}",{{opacity:0}},{v(a["end"])});'
    return f'''
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1,duration:1.4,ease:"power2.out"}},{v(0)});
tl.to("#sc_{k}",{{opacity:1,duration:1.2}},{v(0)});
{railjs}
tl.fromTo("#card_{k}",{{opacity:0,x:50,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{v(0.5)});
tl.to("#card_{k}",{{opacity:0,y:-12,duration:.55,ease:"power2.in"}},{v(a["sw0"]-0.1)});
tl.fromTo("#show_{k}",{{opacity:0,y:28}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{v(a["f0"]+0.4)});
tl.to("#show_{k}",{{opacity:0,y:-12,duration:.55,ease:"power2.in"}},{v(a["tr0"]-0.2 if a["tr"]>0 else a["f1"]-0.4)});
tl.set("#show_{k}",{{opacity:0}},{v(a["end"])});
tl.to("#fv_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{v(a["end"]-1.0)});
tl.set("#fv_{k}",{{opacity:0}},{v(a["end"])});
tl.to("#sc_{k}",{{opacity:0,duration:1.0}},{v(a["end"]-1.0)});
tl.set("#sc_{k}",{{opacity:0}},{v(a["end"])});'''

JS=f'''
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-amei",{{opacity:1}},0);tl.set(".cv-zys",{{opacity:.5}},0);
tl.to(".cv-amei",{{scale:1.02,duration:3.4,ease:"sine.inOut",yoyo:true,repeat:1}},0.6);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D-0.6)});
tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});
tl.fromTo("#fv_hook",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:1.2,ease:"power2.out"}},{fmt(ct("hook"))});
tl.to("#sc_hook",{{opacity:1,duration:1.0}},{fmt(ct("hook"))});
tl.fromTo("#hk_txt",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(ct("hook")+2.0)});
tl.to("#hk_txt",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(ct("hook")+hook_seg-0.9)});
tl.set("#hk_txt",{{opacity:0}},{fmt(ct("hook")+hook_seg)});
tl.to("#fv_hook",{{opacity:0,duration:.8}},{fmt(ct("hook")+hook_seg-0.5)});
tl.set("#fv_hook",{{opacity:0}},{fmt(ct("hook")+hook_seg)});
{''.join(js_chapter(s,i) for i,s in enumerate(SONGS))}
tl.fromTo("#fv_outro",{{opacity:0,scale:1.05}},{{opacity:1,scale:1,duration:1.2}},{fmt(ct("outro"))});
tl.to("#sc_outro",{{opacity:1,duration:1.0}},{fmt(ct("outro"))});
tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.8,ease:"power2.out"}},{fmt(ct("outro")+0.4)});
tl.fromTo(".ot-h",{{opacity:0,y:30}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{fmt(ct("outro")+1.6)});
tl.fromTo(".ot-q",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.7}},{fmt(ct("outro")+3.2)});
tl.fromTo(".ot-q2",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.6}},{fmt(ct("outro")+4.0)});
tl.to("#outro",{{opacity:1,duration:.1}},{fmt(TOTAL-0.2)});
'''

html=f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
{chr(10).join(foot)}
{chr(10).join(scrim)}
<div class="grain"></div>
{chr(10).join(chrome)}
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
</script></body></html>'''
(HF/"index.html").write_text(html,encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"zys-amei-bole"}',encoding="utf-8")
print("index.html:",len(html),"bytes; TOTAL",TOTAL,"s")
print("FULL BUILD DONE")
