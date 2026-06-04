#!/usr/bin/env python3
"""全片构建：没有周杰伦，方文山也写过这些歌（7首叙事序 + 转场 + 结尾）。
复用样片视觉系统（旧纸/水墨/黑金/深蓝/毛笔），每首切换 --acc 强调色 + 场景tint。
产物：hf/master.wav + hf/index.html + hf/clips_seg/<key>.mp4。
依赖：audio/<key>.wav (narrate_full.py)；clips/vert_<key>.mp4 (vfill，逐首裁烧字+letterbox)。
渲染后必须 ffmpeg mux master.wav。"""
import subprocess, wave, contextlib, json
from pathlib import Path

A = "audio"; C = "clips"
def dur(p):
    with contextlib.closing(wave.open(str(p),'r')) as w:
        return round(w.getnframes()/w.getframerate(),3)
def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

KEYS = ["s1","s2","s3","s4","s5","s6","s7"]
NARR = {k: dur(f"{A}/{k}.wav") for k in ["intro","outro"]+[f"{s}_voice" for s in KEYS]+[f"{s}_mid" for s in KEYS]}

# ============ 每首源切点（vert_<key> 内偏移，使副歌对齐展示窗）—— 逐首分析后填 ============
# mseek = vert 内的起播秒；副歌全量段 τ[full0..full1] 显示 vert[mseek+full0 .. mseek+full1]
SRC = {
    "s1": ("vert_asang", 6.25),  # vert_asang 源95s起；副歌对齐源116
    "s2": ("vert_s2", 0.0),      # 窗源197起；副歌对齐源~210
    "s3": ("vert_s3", 0.0),      # 窗源217起；谭维维finale对齐源~228
    "s4": ("vert_s4", 0.0),      # 窗源183起；群像副歌~197
    "s5": ("vert_s5", 0.0),      # 窗源136起；方大同副歌~150
    "s6": ("vert_s6", 0.0),      # 窗源213起；大副歌~224
    "s7": ("vert_s7", 0.0),      # 窗源52起；律动段~62
}

# ============ 每首展示/包装元数据 ============
SONGS = [
 dict(key="s1", no="01", cn="第一首", name="一直很安静", artist="阿桑",
      credit='词：<b>方文山</b>　曲：蔡如岳', tag="安静到卑微的爱", kw="静",
      acc="#93A7C4", tintA="rgba(120,150,200,.16)", tintB="rgba(10,14,26,.55)",
      src="官方 MV · 華研國際",
      trans="他写得了沉默的爱，<br>也写得了三国旧梦"),
 dict(key="s2", no="02", cn="第二首", name="醉赤壁", artist="林俊杰",
      credit='词：<b>方文山</b>　曲：林俊杰', tag="离开周杰伦的中国风", kw="醉",
      acc="#D06A4A", tintA="rgba(180,70,50,.18)", tintB="rgba(30,12,10,.55)",
      src="官方 MV · 太合音樂",
      trans="从一个人的赤壁，<br>到千军万马的城墙"),
 dict(key="s3", no="03", cn="第三首", name="缘分一道桥", artist="王力宏 · 谭维维",
      credit='词：<b>方文山</b>　曲：王力宏', tag="电影级的江湖与宿命", kw="侠",
      acc="#D69A52", tintA="rgba(200,140,60,.16)", tintB="rgba(28,16,8,.55)",
      src="官方 MV · 电影《长城》片尾曲",
      trans="从东方的战鼓，<br>到希腊的神话"),
 dict(key="s4", no="04", cn="第四首", name="月桂女神", artist="S.H.E",
      credit='词：<b>方文山</b>　曲：李天龙', tag="写进女团的希腊神话", kw="神",
      acc="#CBB46A", tintA="rgba(190,170,90,.16)", tintB="rgba(20,22,10,.52)",
      src="官方 MV · 華研國際",
      trans="从天上的女神，<br>到城市里的想念"),
 dict(key="s5", no="05", cn="第五首", name="千纸鹤", artist="方大同",
      credit='词：<b>方文山</b>　曲：方大同', tag="都市里很轻的想念", kw="念",
      acc="#D9A86A", tintA="rgba(210,150,90,.15)", tintB="rgba(24,16,10,.55)",
      src="官方 MV · Warner Music",
      trans="从一个人的想念，<br>到两个人的家"),
 dict(key="s6", no="06", cn="第六首", name="将故事写成我们", artist="林俊杰",
      credit='词：<b>方文山</b>　曲：林俊杰', tag="把人生写成一个家", kw="家",
      acc="#CE8090", tintA="rgba(190,90,110,.16)", tintB="rgba(26,10,14,.55)",
      src="官方 MV · JJ Lin",
      trans="从婚礼的温柔，<br>到街头的节奏"),
 dict(key="s7", no="07", cn="第七首", name="壁虎漫步", artist="潘玮柏",
      credit='词：<b>方文山</b>　曲：Eddy Teddy / Park Hong-Jun', tag="原来他也能写街头", kw="街",
      acc="#5FD2A6", tintA="rgba(80,210,170,.15)", tintB="rgba(8,24,20,.5)",
      src="官方 MV · 潘瑋柏",
      trans=None),
]

# ============ 节奏常量 ============
COVER_D=5.0; IVOICE=5.4
INTRO_END=round(IVOICE+NARR["intro"]+1.45,3)
LEAD,PRE,POST,SWELL,BED=0.15,0.8,1.2,1.5,0.18
CHORUS=30.0; POST_CHORUS,TAILPAD=1.0,0.8
OUTRO_LEAD=0.5

def anchors(key):
    v=NARR[f"{key}_voice"]; m=NARR[f"{key}_mid"]
    v0=LEAD+PRE; v1=v0+v; sw0=v1+POST; full0=sw0+SWELL; full1=full0+CHORUS
    mid_at=full1+POST_CHORUS; end=mid_at+m+TAILPAD
    return dict(v0=v0,v1=v1,sw0=sw0,full0=full0,full1=full1,mid_at=mid_at,end=end)
def seg_len(key): return round(anchors(key)["end"],3)

# 绝对时间轴
starts={}; t=0.0
starts["intro"]=(0.0,INTRO_END); t=INTRO_END
for k in KEYS:
    sl=seg_len(k); starts[k]=(t,sl); t=round(t+sl,3)
OUTRO=t; OUTRO_LEN=round(OUTRO_LEAD+NARR["outro"]+4.0,3); starts["outro"]=(OUTRO,OUTRO_LEN)
TOTAL=round(OUTRO+OUTRO_LEN,3)
print(f"INTRO_END={INTRO_END}  per-chapter={{ {', '.join(k+':'+str(seg_len(k)) for k in KEYS)} }}")
print(f"OUTRO={OUTRO} TOTAL={TOTAL} ({TOTAL//60:.0f}:{TOTAL%60:05.2f})")

# ============ 音频 ============
def build_audio():
    Path("build/segs").mkdir(parents=True,exist_ok=True)
    # intro: 低音 ambient 床(用 s1 源前奏) + intro 旁白
    run(["ffmpeg","-v","error","-i","raw/asang_full.mp4","-i",f"{A}/intro.wav","-filter_complex",
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{INTRO_END},asetpts=PTS-STARTPTS,volume=0.16,afade=t=in:st=0:d=1.3,afade=t=out:st={INTRO_END-1.6}:d=1.6[bed];"
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(IVOICE*1000)}|{int(IVOICE*1000)},volume=2.0[v];"
        f"[bed][v]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[o]",
        "-map","[o]","-ac","2","-ar","48000","build/segs/seg_intro.wav","-y"])
    # 每首
    for k in KEYS:
        a=anchors(k); sl=seg_len(k); clip,ms=SRC[k]; v0=a["v0"]; sw0=a["sw0"]; full0=a["full0"]; full1=a["full1"]; mid_at=a["mid_at"]
        ve=(f"(lt(t,{LEAD}))*0+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
            f"+(between(t,{v0},{sw0}))*{BED}+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
            f"+(gte(t,{full0}))*1.0")
        run(["ffmpeg","-v","error","-i",f"{C}/{clip}.mp4","-i",f"{A}/{k}_voice.wav","-i",f"{A}/{k}_mid.wav","-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[vo];"
            f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(mid_at*1000)}|{int(mid_at*1000)},volume=2.2[mo];"
            f"[vo][mo]amix=inputs=2:normalize=0:duration=longest,apad,atrim=0:{sl}[vx];[vx]asplit=2[sc][vm];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
            f"atrim={ms}:{ms+sl},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,afade=t=out:st={round(sl-5,3)}:d=5[mu];"
            f"[mu][sc]sidechaincompress=threshold=0.04:ratio=8:attack=180:release=320[dk];"
            f"[dk][vm]amix=inputs=2:normalize=0:duration=longest,atrim=0:{sl},alimiter=limit=0.95[o]",
            "-map","[o]","-ac","2","-ar","48000",f"build/segs/seg_{k}.wav","-y"])
    # outro: 用 s1 源前奏低床 + outro 旁白
    run(["ffmpeg","-v","error","-i","raw/asang_full.mp4","-i",f"{A}/outro.wav","-filter_complex",
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=20:{20+OUTRO_LEN},asetpts=PTS-STARTPTS,volume=0.17,afade=t=in:st=0:d=1.2,afade=t=out:st={OUTRO_LEN-2.6}:d=2.6[bed];"
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(OUTRO_LEAD*1000)}|{int(OUTRO_LEAD*1000)},volume=2.0[v];"
        f"[bed][v]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OUTRO_LEN},alimiter=limit=0.95[o]",
        "-map","[o]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])
    seglist=["seg_intro.wav"]+[f"seg_{k}.wav" for k in KEYS]+["seg_outro.wav"]
    Path("build/segs/seglist.txt").write_text("".join(f"file '{s}'\n" for s in seglist),encoding="utf-8")
    run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
    import shutil; shutil.copy("master.wav","hf/master.wav")
    print("master dur",dur("master.wav"),"planned",TOTAL)

def cut_clips():
    Path("hf/clips_seg").mkdir(parents=True,exist_ok=True)
    for k in KEYS:
        clip,ms=SRC[k]; sl=seg_len(k)
        run(["ffmpeg","-v","error","-ss",str(ms),"-i",f"{C}/{clip}.mp4","-t",str(sl),
             "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
             f"hf/clips_seg/{k}.mp4","-y"])
    print("clips_seg cut")

# ============ HTML ============
def emit_html():
    abs_a={}
    for s in SONGS:
        k=s["key"]; a=anchors(k); base=starts[k][0]
        abs_a[k]={kk:round(base+vv,3) for kk,vv in a.items()}; abs_a[k]["start"]=base; abs_a[k]["end"]=round(base+seg_len(k),3)

    # footage + scrim + chrome per song
    foot_tracks=[0,6,0,6,0,6,0]
    foot=[]; scrim=[]; chrome=[]
    for idx,s in enumerate(SONGS):
        k=s["key"]; a=abs_a[k]; sl=seg_len(k)
        foot.append(f'<video id="fv_{k}" class="fv clip" data-start="{fmt(a["start"])}" data-duration="{fmt(sl)}" data-track-index="{foot_tracks[idx]}" src="clips_seg/{k}.mp4" muted playsinline></video>')
        scrim.append(f'<div id="scrim_{k}" class="scrim clip" data-start="{fmt(a["start"])}" data-duration="{fmt(sl)}" data-track-index="{10+idx}"></div>')
        scrim.append(f'<div id="scrim2_{k}" class="scrim2 clip" data-start="{fmt(a["start"])}" data-duration="{fmt(sl)}" data-track-index="{20+idx}" style="background:linear-gradient(180deg,{s["tintA"]},{s["tintB"]});"></div>')
        nodes="".join(f'<div class="nd{" on" if i==idx else (" pa" if i<idx else "")}" style="top:{i*15.4:.1f}%"><span class="t">{SONGS[i]["no"]}</span></div>' for i in range(7))
        chrome.append(f'''<div id="chrome_{k}" class="chrome clip" data-start="{fmt(a["start"])}" data-duration="{fmt(sl)}" data-track-index="{30+idx}" style="--acc:{s["acc"]};">
  <div class="hd" id="hd_{k}"><span class="seq">{s["cn"]} · {s["no"]} ／ 07</span><span class="line"></span><span class="mark">詞</span></div>
  <div class="rail" id="rail_{k}"><div class="bar"></div>{nodes}</div>
  <div class="kw" id="kw_{k}">{s["kw"]}</div>
  <div class="card" id="card_{k}">
    <div class="cno">FANG WEN SHAN · {s["no"]}</div>
    <div class="cname">{s["name"]}</div>
    <div class="cart">{s["artist"]}</div>
    <div class="ccr">{s["credit"]}</div>
    <div class="ctag"><span class="d"></span>{s["tag"]}</div>
  </div>
  <div class="midq" id="mid_{k}">{MIDTEXT[k]}</div>
  <div class="src" id="src_{k}">{s["src"]}</div>
</div>''')

    # 转场卡（s1..s6 之后）
    trans=[]
    for idx,s in enumerate(SONGS[:-1]):
        k=s["key"]; a=abs_a[k]
        t0=round(a["end"]-1.0,3)
        trans.append(f'''<div id="tr_{idx}" class="trans clip" data-start="{fmt(t0)}" data-duration="2.8" data-track-index="{40+idx}">
  <div class="tr-rule"></div><div class="tr-txt">{s["trans"]}</div></div>''')

    cover=f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D+0.6)}" data-track-index="50">
  <div class="paper cvp"></div>
  <div class="cv-bokeh"><span class="b1"></span><span class="b2"></span><span class="b3"></span><span class="b4"></span></div>
  <div class="cv-veil"></div><div class="cv-vinyl" id="cvVinyl"></div><div class="grain"></div>
  <div class="cv-ink"></div><div class="cv-ms"></div>
  <div class="cv-fws">方文山</div><div class="cv-seal"><span>詞</span></div>
  <div class="cv-main">
    <div class="cv-eyebrow">华语词人 · <b>周杰伦之外</b></div>
    <h1 class="cv-title">没有<span class="zjl">周杰伦</span>，<br><span class="fws">方文山</span>也写过这些歌</h1>
    <div class="cv-sub">原来这些歌，也藏着他的名字</div>
  </div>
  <div class="cv-foot">手写的歌词<span class="dot">·</span>没署他的脸<span class="dot">·</span>却都听过</div>
</div>'''

    hook=f'''<div id="hook" class="clip hook" data-start="{fmt(COVER_D-0.6)}" data-duration="{fmt(INTRO_END-(COVER_D-0.6)+0.2)}" data-track-index="51">
  <div class="paper"></div><div class="hk-glow"></div><div class="grain"></div>
  <div class="hk-a" id="hkA"><div class="big">方文山</div><div class="neq">很多人以为，他只会和周杰伦一起出现</div></div>
  <div class="hk-b" id="hkB"><span class="hkw">青春</span><span class="hkw g">江湖</span><span class="hkw">爱情</span></div>
  <div class="hk-c" id="hkC">
    <div class="hc-eyebrow">这一期 · 只有一个范围</div>
    <div class="hc-row">作词，<span class="fws">方文山</span></div>
    <div class="hc-row">却没有，<span class="zjl">周杰伦</span></div>
    <div class="hc-tail">这些歌，你可能都听过</div>
  </div>
</div>'''

    recap="".join(f'<span class="rc"><b>{s["artist"].split(" ")[0]}</b>《{s["name"]}》</span>' for s in SONGS)
    o=starts["outro"][0]; od=starts["outro"][1]
    outro=f'''<div id="outro" class="clip outro" data-start="{fmt(o)}" data-duration="{fmt(od)}" data-track-index="52">
  <div class="paper"></div><div class="grain"></div><div class="ot-glow"></div>
  <div class="ot-fws">方文山</div><div class="ot-seal"><span>詞</span></div>
  <h2 class="ot-h">他不只是<br>周杰伦的影子</h2>
  <div class="ot-recap">{recap}</div>
  <div class="ot-cta1">你最意外的是哪一首？</div>
  <div class="ot-cta2">评论区，再补一首方文山写给别人的歌 →</div>
</div>'''

    audio=f'<audio id="master" class="clip" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

    # JS
    js=[f'''tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .cv-main, #cover .cv-fws, #cover .cv-seal, #cover .cv-foot",{{opacity:1}},0);
tl.to("#cvVinyl",{{rotation:14,duration:{COVER_D+0.6},ease:"none",transformOrigin:"50% 50%"}},0.2);
tl.fromTo(".cv-bokeh",{{scale:1.0}},{{scale:1.06,duration:4.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.3);
tl.fromTo(".cv-title",{{scale:1.0}},{{scale:1.018,duration:3.0,ease:"sine.inOut",yoyo:true,repeat:1}},2.0);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D)});
tl.set("#cover",{{opacity:0}},{fmt(COVER_D+0.6)});
tl.set("#hook",{{opacity:1}},{fmt(COVER_D-0.6)});
tl.fromTo("#hkA",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(IVOICE+0.1)});
tl.to("#hkA",{{opacity:0,y:-24,duration:.7,ease:"power2.in"}},{fmt(IVOICE+5.0)});
tl.set("#hkA",{{opacity:0}},{fmt(IVOICE+5.8)});
tl.fromTo("#hkB .hkw",{{opacity:0,y:26}},{{opacity:1,y:0,duration:.6,stagger:.5,ease:"power2.out"}},{fmt(IVOICE+5.6)});
tl.set("#hkB",{{opacity:1}},{fmt(IVOICE+5.6)});
tl.to("#hkB",{{opacity:0,duration:.7,ease:"power2.in"}},{fmt(IVOICE+10.0)});
tl.set("#hkB",{{opacity:0}},{fmt(IVOICE+10.8)});
tl.fromTo("#hkC",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(IVOICE+10.4)});
tl.fromTo("#hkC .hc-row",{{y:18}},{{y:0,duration:.6,stagger:.16,ease:"power2.out"}},{fmt(IVOICE+10.4)});
tl.to("#hook",{{opacity:0,duration:.8,ease:"power2.in"}},{fmt(INTRO_END-0.6)});
tl.set("#hook",{{opacity:0}},{fmt(INTRO_END+0.2)});''']

    for idx,s in enumerate(SONGS):
        k=s["key"]; a=abs_a[k]; st=a["start"]; end=a["end"]; fo=round(end-1.0,3)
        js.append(f'''
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:1.4,ease:"power2.out"}},{fmt(st)});
tl.to("#scrim_{k}",{{opacity:1,duration:1.2}},{fmt(st)});
tl.to("#scrim2_{k}",{{opacity:1,duration:1.2}},{fmt(st)});
tl.fromTo("#hd_{k}",{{opacity:0,y:-14}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(a["start"]+0.5)});
tl.fromTo("#rail_{k}",{{opacity:0}},{{opacity:1,duration:.8}},{fmt(a["start"]+0.7)});
tl.fromTo("#card_{k}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(a["start"]+1.0)});
tl.to("#card_{k}",{{opacity:.34,y:10,duration:.7,ease:"power2.inOut"}},{fmt(a["sw0"])});
tl.fromTo("#kw_{k}",{{opacity:0,scale:.9}},{{opacity:.5,scale:1,duration:1.8,ease:"power3.out"}},{fmt(a["full0"]-0.5)});
tl.to("#kw_{k}",{{opacity:.32,duration:2.0,ease:"sine.inOut"}},{fmt(a["full0"]+1.5)});
tl.to("#kw_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(a["mid_at"]-0.6)});
tl.set("#kw_{k}",{{opacity:0}},{fmt(a["mid_at"]+0.4)});
tl.to("#card_{k}",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{fmt(a["mid_at"]-0.4)});
tl.set("#card_{k}",{{opacity:0}},{fmt(a["mid_at"]+0.3)});
tl.fromTo("#mid_{k}",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{fmt(a["mid_at"])});
tl.fromTo("#src_{k}",{{opacity:0}},{{opacity:1,duration:.6}},{fmt(a["start"]+1.6)});
tl.to("#mid_{k}",{{opacity:0,duration:.8,ease:"power1.in"}},{fmt(end-0.9)});
tl.set("#mid_{k}",{{opacity:0}},{fmt(end)});
tl.to("#fv_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(fo)});
tl.set("#fv_{k}",{{opacity:0}},{fmt(end)});
tl.to("#scrim_{k}, #scrim2_{k}, #src_{k}, #hd_{k}, #rail_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(fo)});
tl.set("#scrim_{k}, #scrim2_{k}, #src_{k}, #hd_{k}, #rail_{k}",{{opacity:0}},{fmt(end)});''')

    for idx in range(len(SONGS)-1):
        k=SONGS[idx]["key"]; a=abs_a[k]; t0=round(a["end"]-1.0,3)
        js.append(f'''
tl.fromTo("#tr_{idx}",{{opacity:0}},{{opacity:1,duration:.4,ease:"power2.out"}},{fmt(t0)});
tl.fromTo("#tr_{idx} .tr-txt",{{y:18}},{{y:0,duration:.6,ease:"power2.out"}},{fmt(t0)});
tl.to("#tr_{idx}",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(t0+2.0)});
tl.set("#tr_{idx}",{{opacity:0}},{fmt(t0+2.8)});''')

    js.append(f'''
tl.set("#outro",{{opacity:1}},{fmt(OUTRO)});
tl.set("#outro .ot-fws, #outro .ot-seal",{{opacity:1}},{fmt(OUTRO)});
tl.fromTo("#outro .ot-h",{{opacity:0,y:30}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{fmt(OUTRO+0.6)});
tl.fromTo("#outro .ot-recap",{{opacity:0}},{{opacity:1,duration:1.0}},{fmt(OUTRO+2.0)});
tl.fromTo("#outro .ot-cta1",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(OUTRO+3.4)});
tl.fromTo("#outro .ot-cta2",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(OUTRO+4.4)});
tl.to("#outro",{{opacity:1,duration:.1}},{fmt(TOTAL-0.2)});''')

    html=f'''<!doctype html>
<html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=Ma+Shan+Zheng&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
{chr(10).join(foot)}
{chr(10).join(scrim)}
{chr(10).join(chrome)}
{chr(10).join(trans)}
{cover}
{hook}
{outro}
{audio}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body></html>'''
    Path("hf/index.html").write_text(html,encoding="utf-8")
    print("index.html",len(html),"bytes; TOTAL",TOTAL)

# 短评文案（屏幕 + 语音同源）
MIDTEXT={
 "s1":"没有华丽的辞藻，也没有大开大合，<br>他只是把站在爱情边缘的沉默，写得很痛。",
 "s2":"林俊杰给了它流行情歌的骨架，<br>方文山把它写成了前世、江湖和赤壁的梦。",
 "s3":"他写的不是小情小爱，<br>而是城墙、战鼓与风沙之间，一种宿命的英雄气。",
 "s4":"他把希腊神话写进女团的流行歌里——<br>不是单纯的甜，而是自由、神话与女性的选择。",
 "s5":"没有古风，没有战争，也没有浓烈的戏剧感，<br>他写的是都市里那种很轻、却很有后劲的想念。",
 "s6":"上一次写前世与江湖，这一次，<br>他把一个人的人生，慢慢写成两个人的家。",
 "s7":"原来他也能写怪、写俏皮、写街头——<br>方文山不是某一种风格，而是一整套文字系统。",
}

CSS = r'''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#080B12;color:#ECE3CE;
  font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased;}
:root{--ink:#080B12;--gold:#C9A24B;--goldhi:#E8C879;--paper:#ECE3CE;}
.paper{position:absolute;inset:0;background:
  radial-gradient(ellipse at 30% 18%, rgba(36,46,72,.55) 0, transparent 55%),
  radial-gradient(ellipse at 75% 82%, rgba(28,22,14,.6) 0, transparent 60%),
  linear-gradient(180deg,#0A0E18 0%,#080B12 55%,#06080E 100%);}
.grain{position:absolute;inset:0;opacity:.5;mix-blend-mode:overlay;background-image:
  radial-gradient(circle at 12% 28%, rgba(236,227,206,.05) 0 .6px, transparent 1px),
  radial-gradient(circle at 68% 62%, rgba(236,227,206,.05) 0 .6px, transparent 1px),
  radial-gradient(circle at 42% 88%, rgba(236,227,206,.04) 0 .5px, transparent .9px);
  background-size:160px 160px,210px 210px,140px 140px;}
/* 封面 */
.cover{position:absolute;inset:0;z-index:60;overflow:hidden;background:#06080E;}
.cv-bokeh{position:absolute;inset:0;filter:blur(2px);}
.cv-bokeh span{position:absolute;border-radius:50%;filter:blur(46px);mix-blend-mode:screen;opacity:.66;}
.b1{width:420px;height:420px;left:560px;top:60px;background:radial-gradient(circle,rgba(216,170,80,.9),transparent 70%);}
.b2{width:360px;height:360px;left:820px;top:300px;background:radial-gradient(circle,rgba(120,150,220,.8),transparent 70%);}
.b3{width:300px;height:300px;left:640px;top:430px;background:radial-gradient(circle,rgba(200,90,130,.7),transparent 70%);}
.b4{width:340px;height:340px;left:430px;top:240px;background:radial-gradient(circle,rgba(90,170,150,.55),transparent 70%);}
.cv-veil{position:absolute;inset:0;background:linear-gradient(115deg,rgba(6,8,14,.96) 0%,rgba(6,8,14,.72) 38%,rgba(6,8,14,.4) 62%,rgba(8,12,22,.86) 100%);}
.cv-vinyl{position:absolute;right:-190px;bottom:-210px;width:620px;height:620px;border-radius:50%;
  background:radial-gradient(circle,#1a1206 0 14%,transparent 14.5%),
  repeating-radial-gradient(circle, rgba(201,162,75,.10) 0 2px, transparent 2px 9px);
  border:2px solid rgba(201,162,75,.18);opacity:.5;}
.cv-vinyl::after{content:"";position:absolute;left:50%;top:50%;width:56px;height:56px;transform:translate(-50%,-50%);
  border-radius:50%;background:radial-gradient(circle,var(--gold),#7a5c1f);}
.cv-ink{position:absolute;left:-60px;top:120px;width:560px;height:760px;
  background:radial-gradient(ellipse at 40% 45%, rgba(10,14,26,.9) 0, transparent 70%);filter:blur(6px);}
.cv-ms{position:absolute;left:70px;top:250px;width:300px;height:560px;opacity:.16;
  background:repeating-linear-gradient(180deg,rgba(236,227,206,.55) 0 1.5px,transparent 1.5px 34px);
  border-left:2px solid rgba(236,227,206,.25);transform:rotate(-1.5deg);}
.cv-fws{position:absolute;left:96px;top:236px;font-family:"Ma Shan Zheng",cursive;
  font-size:208px;line-height:.96;color:var(--goldhi);writing-mode:vertical-rl;letter-spacing:6px;
  text-shadow:0 0 30px rgba(201,162,75,.45),0 6px 20px rgba(0,0,0,.6);}
.cv-seal{position:absolute;left:322px;top:700px;width:112px;height:112px;border-radius:10px;
  background:linear-gradient(145deg,#a8231f,#7c1714);display:flex;align-items:center;justify-content:center;
  box-shadow:0 8px 26px rgba(0,0,0,.5),inset 0 0 0 3px rgba(255,255,255,.14);transform:rotate(-4deg);}
.cv-seal span{font-family:"Ma Shan Zheng",cursive;font-size:74px;color:#f6ece0;}
.cv-main{position:absolute;left:84px;right:84px;top:1066px;}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;letter-spacing:.34em;color:var(--gold);margin-bottom:30px;}
.cv-eyebrow b{color:var(--paper);font-weight:800;}
.cv-title{font-family:"Noto Serif SC",serif;font-size:90px;font-weight:900;line-height:1.16;color:var(--paper);letter-spacing:-1px;text-shadow:0 4px 24px rgba(0,0,0,.6);}
.cv-title .zjl{color:rgba(236,227,206,.5);position:relative;}
.cv-title .zjl::after{content:"";position:absolute;left:-4px;right:-4px;top:54%;height:6px;background:var(--gold);transform:rotate(-3deg);border-radius:3px;opacity:.92;}
.cv-title .fws{color:var(--goldhi);}
.cv-sub{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:500;color:rgba(236,227,206,.82);margin-top:36px;letter-spacing:.02em;}
.cv-foot{position:absolute;left:84px;bottom:88px;font-family:"Noto Sans SC",sans-serif;font-size:26px;font-weight:600;letter-spacing:.3em;color:rgba(201,162,75,.78);}
.cv-foot .dot{color:rgba(236,227,206,.45);margin:0 14px;}
/* 钩子 */
.hook{position:absolute;inset:0;z-index:55;background:#06080E;overflow:hidden;}
.hk-glow{position:absolute;inset:0;background:
  radial-gradient(ellipse at 28% 30%, rgba(201,162,75,.10) 0, transparent 52%),
  radial-gradient(ellipse at 72% 74%, rgba(120,150,220,.10) 0, transparent 55%);}
.hk-a{position:absolute;left:0;right:0;top:560px;text-align:center;opacity:0;}
.hk-a .big{font-family:"Ma Shan Zheng",cursive;font-size:230px;color:var(--goldhi);line-height:1;text-shadow:0 0 40px rgba(201,162,75,.4);}
.hk-a .neq{font-family:"Noto Serif SC",serif;font-size:50px;color:rgba(236,227,206,.78);margin-top:30px;font-weight:600;}
.hk-b{position:absolute;left:0;right:0;top:600px;text-align:center;opacity:0;}
.hk-b .hkw{display:block;font-family:"Noto Serif SC",serif;font-size:150px;font-weight:800;color:var(--paper);line-height:1.14;letter-spacing:.14em;}
.hk-b .hkw.g{color:var(--goldhi);}
.hk-c{position:absolute;left:80px;right:80px;top:640px;text-align:center;opacity:0;}
.hk-c .hc-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:700;letter-spacing:.32em;color:var(--gold);margin-bottom:46px;}
.hk-c .hc-row{font-family:"Noto Serif SC",serif;font-size:96px;font-weight:800;line-height:1.34;color:var(--paper);}
.hk-c .hc-row .fws{color:var(--goldhi);}
.hk-c .hc-row .zjl{color:rgba(236,227,206,.42);text-decoration:line-through;text-decoration-color:rgba(201,162,75,.85);text-decoration-thickness:5px;}
.hk-c .hc-tail{font-family:"Noto Serif SC",serif;font-size:58px;font-weight:600;color:rgba(236,227,206,.8);margin-top:48px;}
/* chapter */
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.scrim{position:absolute;inset:0;z-index:2;opacity:0;background:linear-gradient(180deg,rgba(6,8,14,.82) 0%,rgba(6,8,14,.12) 26%,rgba(6,8,14,.05) 60%,rgba(6,8,14,.9) 100%);}
.scrim2{position:absolute;inset:0;z-index:2;opacity:0;mix-blend-mode:soft-light;}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none;}
.hd{position:absolute;top:74px;left:88px;right:88px;display:flex;align-items:center;gap:22px;opacity:0;}
.hd .seq{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:700;color:var(--gold);letter-spacing:.08em;white-space:nowrap;}
.hd .line{flex:1;height:1px;background:linear-gradient(90deg,rgba(201,162,75,.6),rgba(201,162,75,0));}
.hd .mark{font-family:"Ma Shan Zheng",cursive;font-size:40px;color:rgba(236,227,206,.8);}
.rail{position:absolute;left:60px;top:300px;bottom:560px;width:8px;opacity:0;}
.rail .bar{position:absolute;left:3px;top:0;bottom:0;width:2px;background:linear-gradient(180deg,rgba(236,227,206,.05),rgba(236,227,206,.22),rgba(236,227,206,.05));}
.rail .nd{position:absolute;left:-13px;width:34px;height:34px;border-radius:50%;background:rgba(20,25,40,.9);border:2px solid rgba(236,227,206,.22);display:flex;align-items:center;justify-content:center;}
.rail .nd.pa{background:rgba(70,70,82,.7);border-color:rgba(236,227,206,.3);}
.rail .nd.on{background:var(--acc);border-color:var(--acc);box-shadow:0 0 26px var(--acc);transform:scale(1.2);}
.rail .nd .t{font-family:"JetBrains Mono",monospace;font-size:16px;font-weight:700;color:rgba(236,227,206,.55);}
.rail .nd.on .t{color:#12161e;}
.kw{position:absolute;left:0;right:0;top:300px;text-align:center;font-family:"Noto Serif SC",serif;font-size:300px;font-weight:900;color:var(--acc);opacity:0;letter-spacing:6px;mix-blend-mode:screen;filter:drop-shadow(0 6px 50px rgba(255,255,255,.16));}
.card{position:absolute;left:70px;right:70px;bottom:300px;padding:44px 50px 46px;border-radius:24px;opacity:0;
  background:linear-gradient(155deg,rgba(20,26,42,.66),rgba(8,11,20,.5));backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);
  border:1.5px solid rgba(201,162,75,.32);box-shadow:0 30px 80px rgba(0,0,0,.6),inset 0 0 0 1px rgba(236,227,206,.06);}
.card .cno{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:700;letter-spacing:.3em;color:var(--gold);margin-bottom:16px;}
.card .cname{font-family:"Noto Serif SC",serif;font-size:88px;font-weight:800;line-height:1.04;color:var(--paper);}
.card .cart{font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:600;color:rgba(236,227,206,.78);margin-top:10px;letter-spacing:.04em;}
.card .ccr{font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:500;color:rgba(236,227,206,.62);margin-top:24px;letter-spacing:.02em;}
.card .ccr b{color:var(--goldhi);font-weight:700;}
.card .ctag{display:inline-flex;align-items:center;gap:14px;margin-top:26px;font-family:"Noto Serif SC",serif;font-size:38px;font-weight:700;color:var(--acc);}
.card .ctag .d{width:12px;height:12px;border-radius:50%;background:var(--acc);box-shadow:0 0 16px var(--acc);}
.midq{position:absolute;left:84px;right:84px;bottom:430px;text-align:center;font-family:"Noto Serif SC",serif;font-size:52px;font-weight:600;line-height:1.42;color:rgba(236,227,206,.96);opacity:0;letter-spacing:.01em;text-shadow:0 4px 24px rgba(0,0,0,.7);}
.src{position:absolute;left:0;right:0;bottom:96px;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:22px;font-weight:500;letter-spacing:.24em;color:rgba(236,227,206,.4);opacity:0;}
/* 转场 */
.trans{position:absolute;inset:0;z-index:9;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;
  background:radial-gradient(ellipse at center, rgba(6,8,14,.9) 0%, rgba(6,8,14,.66) 100%);}
.tr-rule{width:120px;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin-bottom:46px;}
.tr-txt{font-family:"Noto Serif SC",serif;font-size:70px;font-weight:700;line-height:1.5;text-align:center;color:var(--paper);text-shadow:0 4px 24px rgba(0,0,0,.7);}
/* 结尾 */
.outro{position:absolute;inset:0;z-index:58;overflow:hidden;background:#06080E;}
.ot-glow{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 36%, rgba(201,162,75,.12) 0, transparent 52%);}
.ot-fws{position:absolute;left:0;right:0;top:150px;text-align:center;font-family:"Ma Shan Zheng",cursive;font-size:150px;color:var(--goldhi);text-shadow:0 0 36px rgba(201,162,75,.4);}
.ot-seal{position:absolute;left:50%;top:150px;transform:translateX(180px) rotate(-4deg);width:92px;height:92px;border-radius:9px;background:linear-gradient(145deg,#a8231f,#7c1714);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(0,0,0,.5),inset 0 0 0 3px rgba(255,255,255,.14);}
.ot-seal span{font-family:"Ma Shan Zheng",cursive;font-size:58px;color:#f6ece0;}
.ot-h{position:absolute;left:80px;right:80px;top:430px;text-align:center;font-family:"Noto Serif SC",serif;font-size:104px;font-weight:900;line-height:1.14;color:var(--paper);opacity:0;}
.ot-recap{position:absolute;left:90px;right:90px;top:760px;text-align:center;line-height:2.0;opacity:0;}
.ot-recap .rc{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:500;color:rgba(236,227,206,.72);margin:0 14px;white-space:nowrap;}
.ot-recap .rc b{color:var(--goldhi);font-weight:700;}
.ot-cta1{position:absolute;left:80px;right:80px;top:1230px;text-align:center;font-family:"Noto Serif SC",serif;font-size:64px;font-weight:800;color:var(--goldhi);opacity:0;}
.ot-cta2{position:absolute;left:80px;right:80px;top:1360px;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:600;color:rgba(236,227,206,.7);letter-spacing:.04em;opacity:0;}
'''

if __name__ == "__main__":
    import sys
    if "--html-only" in sys.argv:
        emit_html()
    elif "--audio-only" in sys.argv:
        build_audio()
    else:
        build_audio(); cut_clips(); emit_html()
    print("BUILD DONE")
