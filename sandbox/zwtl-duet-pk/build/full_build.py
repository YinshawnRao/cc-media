#!/usr/bin/env python3
"""周王陶林男女合唱神曲PK（倒数 #4->#1，女声）。
结构：cover(2x2真人肖像,无歌单) -> intro(钩子,4歌手+PK+空榜) -> rules(5项加权评分条)
      -> 4章节[揭晓VO(低床)->评分条+综合分->swell->纯音乐副歌展示] -> outro(总榜回顾+CTA)。
悬念硬约束：cover/intro/rules 不出现任何歌名/合唱对象/排名/评分；总榜只在 #1 揭晓后(outro)出现。
音频：前段(cover/intro/rules)用 #4 器乐低床(lowpass,低音量,不剧透)；各章节 床->swell->副歌(loudnorm I=-14);
      最后必须 ffmpeg mux master.wav。"""
import subprocess, wave, contextlib, json, shutil
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
def f(x): return f"{round(x,3)}"

# ---------- 节奏常量 ----------
LEAD=0.15; PRE_VOICE=0.8; POST_VOICE=1.0; SWELL=1.5; BED=0.18; TAIL=1.1
VOICE_GAIN=2.2
SHOW_TARGET={"heaven":28.0,"dimples":27.0,"coral":28.0,"today":32.0}  # 连续副歌展示, 前后留余量

# ---------- 歌曲（揭晓顺序 #4->#1） ----------
# 5项评分条权重(全曲统一)：传唱度30 影响力25 奖项20 口碑15 合唱适配10
DIMS=[("传唱度","30%"),("影响力","25%"),("奖项","20%"),("口碑","15%"),("合唱适配","10%")]
SONGS = [
  dict(key="heaven", rank="04", score="8.7", name="另一个天堂", male="王力宏", female="张靓颖",
       year="2008", album="心跳", tag="双强对唱 · 高配置对撞",
       W=98.0, bars=[8.5,8.5,8.5,9.0,10.0],
       bg="#0A1020", pri="#7FB0E6", acc="#E9C77A", tint="90,130,200"),
  dict(key="dimples", rank="03", score="8.8", name="小酒窝", male="林俊杰", female="蔡卓妍",
       year="2008", album="JJ陆", tag="甜歌天花板 · 记忆点拉满",
       W=24.0, bars=[9.5,8.5,7.5,9.0,9.5],
       bg="#1B1206", pri="#F2A84E", acc="#F7CEDA", tint="220,150,90"),
  dict(key="coral", rank="02", score="9.2", name="珊瑚海", male="周杰伦", female="梁心颐",
       year="2005", album="十一月的萧邦", tag="遗憾感 · 质感最稳",
       W=25.0, bars=[9.0,9.5,8.8,9.8,9.0],
       bg="#08131C", pri="#6FC6D8", acc="#CFE9F1", tint="90,170,195"),
  dict(key="today", rank="01", score="9.6", name="今天你要嫁给我", male="陶喆", female="蔡依林",
       year="2005", album="太美丽", tag="婚礼神曲 · 全民场景统治",
       W=26.0, bars=[10.0,9.8,9.5,9.0,9.5],
       bg="#1C0A0A", pri="#E8B24C", acc="#F0786A", tint="220,150,70"),
]
KEYS=[s["key"] for s in SONGS]
RAWF={"heaven":"lh_zlj_live","dimples":"jj_asa_mv","coral":"jay_lara","today":"tao_jolin_mv"}
FRONT_BED="lh_zlj_live"   # #4 器乐低床(首个揭晓,低音量+lowpass,剧透极小)
OUTRO_BED="tao_jolin_mv"  # #1 已揭晓,庆典感做总榜+CTA床

# 封面肖像顺序 周王陶林
COVER=[("p_jay","周杰伦"),("p_wlh","王力宏"),("p_tao","陶喆"),("p_jj","林俊杰")]

# ---------- 时长 ----------
NV={s["key"]: wdur(f"{A}/{s['key']}.wav") for s in SONGS}
for k in ("intro","rules","outro"): NV[k]=wdur(f"{A}/{k}.wav")
SHOW={s["key"]: round(min(vdur(f"{CS}/{s['key']}.mp4"), SHOW_TARGET[s["key"]]),3) for s in SONGS}
print("VO:",json.dumps(NV,ensure_ascii=False)); print("SHOW:",SHOW)

def anchors(key):
    vo=NV[key]; sd=SHOW[key]
    v0=LEAD+PRE_VOICE; v1=v0+vo; sw0=v1+POST_VOICE; show0=sw0+SWELL; show1=show0+sd; end=show1+TAIL
    return dict(v0=v0,v1=v1,sw0=sw0,show0=show0,show1=show1,end=end,seg=end)

COVER_D=2.0   # 缩短开场静止(用户：开头静止太长)
INTRO_SEG=round(LEAD+0.5+NV["intro"]+1.6,3)
RULES_SEG=round(LEAD+0.5+NV["rules"]+1.6,3)
OUTRO_SEG=round(LEAD+NV["outro"]+2.4,3)

starts={}; t=COVER_D
starts["intro"]=(t,INTRO_SEG); t+=INTRO_SEG
starts["rules"]=(t,RULES_SEG); t+=RULES_SEG
for s in SONGS:
    a=anchors(s["key"]); starts[s["key"]]=(round(t,3),a["seg"]); t+=a["seg"]
starts["outro"]=(round(t,3),OUTRO_SEG); t+=OUTRO_SEG
TOTAL=round(t,3)
print(f"TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ============ 音频段 ============
Path("build/segs").mkdir(parents=True, exist_ok=True)
FB=f"{RAW}/{FRONT_BED}.mkv" if Path(f"{RAW}/{FRONT_BED}.mkv").exists() else f"{RAW}/{FRONT_BED}.mp4"
OB=f"{RAW}/{OUTRO_BED}.mkv" if Path(f"{RAW}/{OUTRO_BED}.mkv").exists() else f"{RAW}/{OUTRO_BED}.mp4"

# 前段连续低床(cover+intro+rules)从 #4 器乐区 orig0:40起(=raw t0)，lowpass 模糊旋律
FRONT_TOTAL=round(COVER_D+INTRO_SEG+RULES_SEG,3)
# cover 段（短开场, 音乐床要明显可听, 别再让人觉得"没声音"）
run(["ffmpeg","-v","error","-i",FB,"-filter_complex",
  f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
  f"atrim=0:{COVER_D},asetpts=PTS-STARTPTS,lowpass=f=1400,volume=0.42,afade=t=in:st=0:d=0.5[o]",
  "-map","[o]","-ac","2","-ar","48000","build/segs/seg_cover.wav","-y"])
# intro 段(VO + 床续)
def front_voice_seg(name, segdur, bed_off, vo_delay):
    run(["ffmpeg","-v","error","-i",FB,"-i",f"{A}/{name}.wav","-filter_complex",
      f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(vo_delay*1000)}|{int(vo_delay*1000)},volume={VOICE_GAIN}[v];"
      f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
      f"atrim={bed_off}:{round(bed_off+segdur,3)},asetpts=PTS-STARTPTS,lowpass=f=620,volume=0.15,"
      f"afade=t=out:st={segdur-1.4}:d=1.4[bed];"
      f"[v][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segdur},alimiter=limit=0.95[o]",
      "-map","[o]","-ac","2","-ar","48000",f"build/segs/seg_{name}.wav","-y"])
front_voice_seg("intro", INTRO_SEG, COVER_D, LEAD+0.5)
front_voice_seg("rules", RULES_SEG, COVER_D+INTRO_SEG, LEAD+0.5)

# 章节：床->swell->副歌展示(各曲自身 raw 的 W 处)
def build_song(s):
    k=s["key"]; a=anchors(k); seg=a["seg"]
    v0=a["v0"]; sw0=a["sw0"]; show0=a["show0"]; show1=a["show1"]
    src=f"{RAW}/{RAWF[k]}.mkv" if Path(f"{RAW}/{RAWF[k]}.mkv").exists() else f"{RAW}/{RAWF[k]}.mp4"
    mstart=round(s["W"]-show0,3)
    ve=(f"(lt(t,{LEAD}))*0"
        f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
        f"+(between(t,{v0},{sw0}))*{BED}"
        f"+(between(t,{sw0},{show0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
        f"+(gte(t,{show0}))*1.0")
    run(["ffmpeg","-v","error","-i",src,"-i",f"{A}/{k}.wav","-filter_complex",
      f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume={VOICE_GAIN}[v];"
      f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
      f"atrim={mstart}:{round(mstart+seg,3)},asetpts=PTS-STARTPTS,"
      f"volume='{ve}':eval=frame,afade=t=out:st={show1}:d={round(seg-show1,3)}[m];"
      f"[v][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95[o]",
      "-map","[o]","-ac","2","-ar","48000",f"build/segs/seg_{k}.wav","-y"])
for s in SONGS: build_song(s); print("seg",s["key"],"ok")

# outro：#1 副歌低床做总榜+CTA(避免淡出尾太轻)
o_mstart=32.0
run(["ffmpeg","-v","error","-i",OB,"-i",f"{A}/outro.wav","-filter_complex",
  f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[v];"
  f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
  f"atrim={o_mstart}:{round(o_mstart+OUTRO_SEG,3)},asetpts=PTS-STARTPTS,volume=0.30,"
  f"afade=t=in:st=0:d=1.0,afade=t=out:st={OUTRO_SEG-1.8}:d=1.8[bed];"
  f"[v][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OUTRO_SEG},alimiter=limit=0.95[o]",
  "-map","[o]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])

order=["cover","intro","rules"]+KEYS+["outro"]
Path("build/segs/list.txt").write_text("".join(f"file 'seg_{k}.wav'\n" for k in order),encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/list.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master:",wdur("master.wav"),"planned:",TOTAL)

# ============ 资源 ============
Path("hf/clips_seg").mkdir(parents=True, exist_ok=True)
for k in KEYS: shutil.copy(f"{CS}/{k}.mp4", f"hf/clips_seg/{k}.mp4")
shutil.copy("master.wav","hf/master.wav")
print("assets copied")

# ============ 绝对锚点 ============
ABS={}
for s in SONGS:
    k=s["key"]; a=anchors(k); base=starts[k][0]
    ABS[k]={kk:round(base+vv,3) for kk,vv in a.items() if kk!='seg'}
    ABS[k]["base"]=base; ABS[k]["end"]=round(base+a["seg"],3)
INTRO_T=starts["intro"][0]; RULES_T=starts["rules"][0]; OUTRO_T=starts["outro"][0]

# ============ HTML 片段 ============
foot=[]; tracks=[0,6,0,6]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    foot.append(f'<video id="fv_{k}" class="fv clip" data-start="{f(a["show0"])}" data-duration="{f(SHOW[k])}" data-track-index="{tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>')

bglayer=[]; tints=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    bglayer.append(f'<div id="bg_{k}" class="clip chbg chbg_{k}" data-start="{f(a["base"])}" data-duration="{f(a["end"]-a["base"])}" data-track-index="{40+i}"><div class="chbg-glow"></div></div>')
    tints.append(f'<div id="tint_{k}" class="clip ftint ftint_{k}" data-start="{f(a["show0"])}" data-duration="{f(SHOW[k])}" data-track-index="{50+i}"></div>')

# 章节 chrome：大名次 + 揭晓卡(歌手×对象/歌名/年代/tag) + 5评分条 + 综合分 + 进度轨 + 展示期角标
chrome=[]
for i,s in enumerate(SONGS):
    k=s["key"]; a=ABS[k]
    dots="".join(
        f'<div class="rdot{(" on" if j==i else "")}{(" done" if j<i else "")}"><span>{SONGS[j]["rank"]}</span></div>'
        for j in range(4))
    bars="".join(
        f'<div class="sbar"><span class="sb-l">{DIMS[d][0]}</span>'
        f'<span class="sb-w">{DIMS[d][1]}</span>'
        f'<span class="sb-track"><i class="sb-fill" id="sf_{k}_{d}"></i></span>'
        f'<span class="sb-v" id="sv_{k}_{d}">{s["bars"][d]:.1f}</span></div>'
        for d in range(5))
    chrome.append(f'''<div id="ch_{k}" class="clip chrome chrome_{k}" data-start="{f(a["base"])}" data-duration="{f(a["end"]-a["base"])}" data-track-index="{20+i}">
  <div class="rail">{dots}</div>
  <div class="bignum" id="big_{k}"><span class="bn-hash">NO.</span>{s["rank"]}</div>
  <div class="reveal" id="rev_{k}">
    <div class="rv-credit">{s["male"]}<span class="rv-x">×</span>{s["female"]}</div>
    <div class="rv-name">《{s["name"]}》</div>
    <div class="rv-meta">{s["album"]} · {s["year"]}</div>
    <div class="rv-tag">{s["tag"]}</div>
    <div class="rv-bars">{bars}</div>
    <div class="rv-score"><span class="rs-l">综合评分</span><span class="rs-v" id="rsv_{k}">{s["score"]}</span></div>
  </div>
  <div class="badge" id="badge_{k}"><span class="bg-no">NO.{s["rank"]}</span><span class="bg-nm">{s["male"]}×{s["female"]}《{s["name"]}》</span><span class="bg-sc">{s["score"]}</span></div>
</div>''')

cover=f'''<div id="cover" class="clip cover" data-start="0" data-duration="{f(COVER_D)}" data-track-index="60">
  <div class="cv-grid">
    {''.join(f'<div class="cv-cell"><div class="cv-img" style="background-image:url(cover_assets/{img}.png)"></div><div class="cv-shade"></div><div class="cv-nm">{nm}</div></div>' for img,nm in COVER)}
  </div>
  <div class="cv-title">
    <div class="cv-eyebrow">四位创作天王 · 各一首男女合唱</div>
    <h1 class="cv-h">周王陶林</h1>
    <div class="cv-h2">合唱神曲<span class="cv-pk">PK</span></div>
    <div class="cv-sub">谁才是男女对唱，<b>最强王者</b>？</div>
    <div class="cv-cta">综合评分排名 · 评论区先猜</div>
  </div>
</div>'''

intro=f'''<div id="introblk" class="clip introblk" data-start="{f(INTRO_T)}" data-duration="{f(INTRO_SEG)}" data-track-index="61">
  <div class="ib-grad"></div>
  <div class="ib-names">
    {''.join(f'<span class="ib-n" id="ibn_{i}">{nm}</span>' for i,(img,nm) in enumerate(COVER))}
  </div>
  <h2 class="ib-h" id="ib_h">每人只能派出<br><span>一首</span>男女合唱代表作</h2>
  <div class="ib-slots">
    {''.join(f'<div class="ib-slot" id="ibs_{j}"><span class="ib-sno">NO.{4-j}</span><span class="ib-sq">？</span></div>' for j in range(4))}
  </div>
  <div class="ib-q" id="ib_q">谁，才是最强王者？</div>
</div>'''

rules=f'''<div id="rulesblk" class="clip rulesblk" data-start="{f(RULES_T)}" data-duration="{f(RULES_SEG)}" data-track-index="63">
  <div class="rb-grad"></div>
  <div class="rb-eyebrow">评分规则 · 十分制</div>
  <h2 class="rb-h">五个维度，综合打分</h2>
  <div class="rb-list">
    {''.join(f'<div class="rb-row" id="rbr_{d}"><span class="rb-l">{DIMS[d][0]}</span><span class="rb-track"><i class="rb-fill" id="rbf_{d}"></i></span><span class="rb-w">{DIMS[d][1]}</span></div>' for d in range(5))}
  </div>
  <div class="rb-foot" id="rb_foot">一首一首，倒序揭晓</div>
</div>'''

# 总榜回顾(只在 #1 揭晓后 outro 出现) + CTA
recap_rows="".join(
    f'<div class="ot-line" id="otl_{i}"><span class="ot-no">NO.{s["rank"]}</span>'
    f'<span class="ot-nm">{s["male"]}×{s["female"]}《{s["name"]}》</span>'
    f'<span class="ot-sc">{s["score"]}</span></div>'
    for i,s in enumerate(reversed(SONGS)))   # #1->#4
outro=f'''<div id="outroblk" class="clip outroblk" data-start="{f(OUTRO_T)}" data-duration="{f(OUTRO_SEG)}" data-track-index="62">
  <div class="ot-bg"></div>
  <div class="ot-head">本期总榜</div>
  <div class="ot-list">{recap_rows}</div>
  <h2 class="ot-q" id="ot_q">这个排名，你认吗？</h2>
  <p class="ot-cta" id="ot_cta">评论区，说出你心里的第一名</p>
</div>'''

audio=f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

def theme_vars():
    out=[]
    for s in SONGS:
        out.append(f'.chrome_{s["key"]}{{--pri:{s["pri"]};--acc:{s["acc"]};}}')
        out.append(f'.chbg_{s["key"]}{{background:radial-gradient(ellipse 130% 90% at 50% 16%, {s["bg"]} 0%, #05060A 76%);}}')
        out.append(f'.chbg_{s["key"]} .chbg-glow{{background:radial-gradient(circle at 72% 26%, {s["pri"]}26 0%, transparent 46%),radial-gradient(circle at 24% 76%, {s["pri"]}1c 0%, transparent 42%);}}')
        out.append(f'.ftint_{s["key"]}{{background:linear-gradient(180deg, rgba({s["tint"]},.10) 0%, rgba(5,6,10,.18) 38%, rgba(5,6,10,.82) 100%);}}')
    return "\n".join(out)

CSS=r'''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#05060A;color:#F5EFE6;font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased;}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.ftint{position:absolute;inset:0;z-index:2;opacity:0;}
.chbg{position:absolute;inset:0;z-index:0;opacity:0;}
.chbg-glow{position:absolute;inset:0;mix-blend-mode:screen;opacity:.9;}
.chrome{position:absolute;inset:0;z-index:6;pointer-events:none;}

/* 进度轨(顶部4点) */
.rail{position:absolute;top:70px;left:0;right:0;display:flex;justify-content:center;gap:26px;opacity:0;}
.rdot{width:62px;height:62px;border-radius:50%;background:rgba(18,18,26,.85);border:2px solid rgba(255,255,255,.20);display:flex;align-items:center;justify-content:center;font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:800;color:rgba(255,255,255,.72);}
.rdot.done{background:rgba(60,60,72,.55);border-color:rgba(255,255,255,.24);color:rgba(255,255,255,.5);}
.rdot.on{background:var(--pri);border-color:var(--pri);color:#0b0c12;box-shadow:0 0 30px var(--pri);transform:scale(1.12);}

/* 大名次 */
.bignum{position:absolute;top:150px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:440px;font-weight:900;line-height:.82;color:transparent;-webkit-text-stroke:3px var(--pri);opacity:0;letter-spacing:-10px;filter:drop-shadow(0 10px 50px rgba(0,0,0,.5));}
.bn-hash{display:block;-webkit-text-stroke:0;color:var(--pri);font-size:56px;font-weight:800;letter-spacing:.42em;text-indent:.42em;margin-bottom:4px;}

/* 揭晓卡 */
.reveal{position:absolute;top:560px;left:60px;right:60px;opacity:0;}
.rv-credit{font-family:"Noto Sans SC",sans-serif;font-size:46px;font-weight:800;letter-spacing:.04em;color:#F5EFE6;text-align:center;}
.rv-x{color:var(--pri);margin:0 18px;font-weight:700;}
.rv-name{font-family:"Noto Serif SC",serif;font-size:104px;font-weight:900;line-height:1.04;color:#fff;text-align:center;letter-spacing:-1px;margin:10px 0 14px;text-shadow:0 6px 36px rgba(0,0,0,.5);}
.rv-meta{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:500;letter-spacing:.06em;color:rgba(245,239,230,.6);text-align:center;margin-bottom:20px;}
.rv-tag{display:block;width:fit-content;margin:0 auto 30px;font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:800;color:#0b0c12;background:var(--pri);padding:12px 30px;border-radius:999px;box-shadow:0 8px 30px rgba(0,0,0,.4);}
.rv-bars{margin:0 14px;}
.sbar{display:flex;align-items:center;gap:18px;margin:16px 0;}
.sb-l{font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:700;color:#F5EFE6;width:172px;letter-spacing:.02em;}
.sb-w{font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:600;color:rgba(245,239,230,.5);width:70px;}
.sb-track{flex:1;height:18px;border-radius:999px;background:rgba(255,255,255,.10);overflow:hidden;}
.sb-fill{display:block;height:100%;width:0%;border-radius:999px;background:linear-gradient(90deg,var(--pri),var(--acc));}
.sb-v{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:900;color:var(--acc);width:78px;text-align:right;}
.rv-score{display:flex;align-items:center;justify-content:center;gap:24px;margin-top:34px;}
.rs-l{font-family:"Noto Sans SC",sans-serif;font-size:38px;font-weight:700;letter-spacing:.14em;color:rgba(245,239,230,.8);}
.rs-v{font-family:"Noto Sans SC",sans-serif;font-size:128px;font-weight:900;line-height:1;color:var(--pri);text-shadow:0 0 40px var(--pri);}

/* 展示期角标 */
.badge{position:absolute;top:104px;left:56px;right:56px;display:flex;align-items:center;gap:18px;opacity:0;}
.bg-no{font-family:"Noto Sans SC",sans-serif;font-size:52px;font-weight:900;color:var(--pri);text-shadow:0 3px 18px rgba(0,0,0,.7);}
.bg-nm{flex:1;font-family:"Noto Serif SC",serif;font-size:40px;font-weight:800;color:#fff;text-shadow:0 3px 18px rgba(0,0,0,.8);}
.bg-sc{font-family:"Noto Sans SC",sans-serif;font-size:58px;font-weight:900;color:var(--acc);text-shadow:0 3px 18px rgba(0,0,0,.7);}

/* ===== 封面 ===== */
.cover{position:absolute;inset:0;z-index:80;background:#05060A;overflow:hidden;}
.cv-grid{position:absolute;top:78px;left:40px;right:40px;height:1050px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:14px;}
.cv-cell{position:relative;overflow:hidden;border-radius:14px;border:1px solid rgba(233,199,122,.25);}
.cv-img{position:absolute;inset:0;background-size:cover;background-position:center 22%;filter:contrast(1.05) saturate(1.02) brightness(1.04);}
.cv-shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,6,10,.04) 54%,rgba(5,6,10,.82) 100%);}
.cv-q{position:absolute;top:14px;right:20px;font-family:"Noto Sans SC",sans-serif;font-size:64px;font-weight:900;color:rgba(233,199,122,.92);text-shadow:0 4px 16px rgba(0,0,0,.6);}
.cv-nm{position:absolute;bottom:18px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:46px;font-weight:900;letter-spacing:.06em;color:#fff;text-shadow:0 3px 16px rgba(0,0,0,.8);}
.cv-no{position:absolute;top:96px;right:64px;z-index:3;font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:800;letter-spacing:.1em;color:#0b0c12;background:linear-gradient(135deg,#E9C77A,#C99B3F);padding:8px 22px;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.5);}
.cv-no span{font-size:44px;}
.cv-title{position:absolute;bottom:62px;left:50px;right:50px;text-align:center;}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;letter-spacing:.22em;color:#E9C77A;margin-bottom:18px;}
.cv-h{font-family:"Noto Serif SC",serif;font-size:140px;font-weight:900;line-height:1.0;color:#fff;letter-spacing:8px;white-space:nowrap;}
.cv-h2{font-family:"Noto Serif SC",serif;font-size:84px;font-weight:900;color:#E9C77A;letter-spacing:6px;margin-top:8px;white-space:nowrap;}
.cv-pk{font-family:"Noto Sans SC",sans-serif;font-size:84px;font-weight:900;color:#E0584C;margin-left:20px;-webkit-text-stroke:2px rgba(255,255,255,.12);}
.cv-sub{font-family:"Noto Serif SC",serif;font-size:54px;font-weight:600;color:rgba(245,239,230,.92);margin-top:20px;}
.cv-sub b{color:#E9C77A;font-weight:900;}
.cv-cta{font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:600;letter-spacing:.06em;color:rgba(245,239,230,.62);margin-top:22px;}

/* ===== 开场钩子 ===== */
.introblk{position:absolute;inset:0;z-index:70;background:radial-gradient(ellipse at 50% 26%,#11131F 0%,#05060A 74%);}
.ib-grad{position:absolute;inset:0;background:radial-gradient(circle at 74% 22%,rgba(224,88,76,.10) 0,transparent 46%),radial-gradient(circle at 24% 78%,rgba(233,199,122,.08) 0,transparent 44%);}
.ib-names{position:absolute;top:230px;left:60px;right:60px;display:flex;flex-wrap:wrap;justify-content:center;gap:18px 34px;}
.ib-n{font-family:"Noto Sans SC",sans-serif;font-size:60px;font-weight:900;color:#F5EFE6;opacity:0;text-shadow:0 4px 24px rgba(0,0,0,.5);}
.ib-h{position:absolute;top:440px;left:80px;right:80px;text-align:center;font-family:"Noto Serif SC",serif;font-size:80px;font-weight:800;line-height:1.18;color:#F5EFE6;opacity:0;}
.ib-h span{color:#E9C77A;font-size:104px;}
.ib-slots{position:absolute;top:760px;left:70px;right:70px;display:grid;grid-template-columns:1fr 1fr;gap:26px;}
.ib-slot{height:200px;border:2px dashed rgba(255,255,255,.22);border-radius:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;opacity:0;background:rgba(255,255,255,.02);}
.ib-sno{font-family:"Noto Sans SC",sans-serif;font-size:42px;font-weight:900;color:#E9C77A;letter-spacing:.06em;}
.ib-sq{font-family:"Noto Sans SC",sans-serif;font-size:86px;font-weight:900;color:rgba(255,255,255,.3);line-height:.7;}
.ib-q{position:absolute;bottom:150px;left:80px;right:80px;text-align:center;font-family:"Noto Serif SC",serif;font-size:78px;font-weight:900;color:#fff;opacity:0;}

/* ===== 评分规则 ===== */
.rulesblk{position:absolute;inset:0;z-index:69;background:radial-gradient(ellipse at 50% 30%,#101524 0%,#05060A 74%);}
.rb-grad{position:absolute;inset:0;background:radial-gradient(circle at 70% 24%,rgba(127,176,230,.10) 0,transparent 46%);}
.rb-eyebrow{position:absolute;top:300px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:700;letter-spacing:.24em;color:#7FB0E6;}
.rb-h{position:absolute;top:360px;left:0;right:0;text-align:center;font-family:"Noto Serif SC",serif;font-size:88px;font-weight:900;color:#fff;}
.rb-list{position:absolute;top:560px;left:90px;right:90px;}
.rb-row{display:flex;align-items:center;gap:24px;margin:30px 0;opacity:0;}
.rb-l{font-family:"Noto Sans SC",sans-serif;font-size:42px;font-weight:800;color:#F5EFE6;width:230px;}
.rb-track{flex:1;height:24px;border-radius:999px;background:rgba(255,255,255,.10);overflow:hidden;}
.rb-fill{display:block;height:100%;width:0%;border-radius:999px;background:linear-gradient(90deg,#7FB0E6,#E9C77A);}
.rb-w{font-family:"Noto Sans SC",sans-serif;font-size:48px;font-weight:900;color:#E9C77A;width:120px;text-align:right;}
.rb-foot{position:absolute;bottom:200px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:38px;font-weight:700;letter-spacing:.12em;color:rgba(245,239,230,.7);opacity:0;}

/* ===== 总榜 + CTA ===== */
.outroblk{position:absolute;inset:0;z-index:71;background:radial-gradient(ellipse at 50% 40%,#1A1410 0%,#05060A 74%);}
.ot-bg{position:absolute;inset:0;background:radial-gradient(circle at 50% 42%,rgba(232,178,76,.12) 0,transparent 48%);}
.ot-head{position:absolute;top:250px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:800;letter-spacing:.2em;color:#E9C77A;}
.ot-list{position:absolute;top:360px;left:90px;right:90px;}
.ot-line{display:flex;align-items:center;gap:22px;padding:18px 0;border-bottom:1px solid rgba(255,255,255,.10);opacity:0;}
.ot-no{font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:900;color:#E9C77A;width:130px;}
.ot-nm{flex:1;font-family:"Noto Serif SC",serif;font-size:44px;font-weight:700;color:#fff;}
.ot-sc{font-family:"Noto Sans SC",sans-serif;font-size:52px;font-weight:900;color:#F0786A;}
.ot-q{position:absolute;top:1180px;left:80px;right:80px;text-align:center;font-family:"Noto Serif SC",serif;font-size:84px;font-weight:900;color:#fff;opacity:0;}
.ot-cta{position:absolute;top:1360px;left:80px;right:80px;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:700;letter-spacing:.06em;color:#E9C77A;opacity:0;}
'''+theme_vars()

# ============ JS ============
def js_song(s,i):
    k=s["key"]; a=ABS[k]
    base=a["base"]; v0=a["v0"]; sw0=a["sw0"]; show0=a["show0"]; show1=a["show1"]; end=a["end"]
    bars_js="".join(
        f'tl.to("#sf_{k}_{d}",{{width:"{s["bars"][d]*10:.0f}%",duration:.7,ease:"power2.out"}},{f(base+1.7+d*0.12)});'
        for d in range(5))
    return f'''
// ---- {s["name"]} (#{s["rank"]}) ----
tl.set("#bg_{k}",{{opacity:1}},{f(base)});
tl.fromTo(".chrome_{k} .rail",{{opacity:0}},{{opacity:1,duration:.6}},{f(base+0.15)});
tl.fromTo("#big_{k}",{{opacity:0,scale:1.16,y:8}},{{opacity:1,scale:1,y:0,duration:.8,ease:"power3.out"}},{f(base+0.2)});
tl.to("#big_{k}",{{opacity:0,y:-30,duration:.6,ease:"power2.in"}},{f(base+1.5)});
tl.set("#big_{k}",{{opacity:0}},{f(base+2.2)});
tl.fromTo("#rev_{k}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{f(base+1.4)});
{bars_js}
tl.fromTo("#rsv_{k}",{{scale:.6,opacity:0}},{{scale:1,opacity:1,duration:.6,ease:"back.out(2)"}},{f(base+2.5)});
tl.to("#rev_{k}",{{opacity:0,y:-26,duration:.55,ease:"power2.in"}},{f(sw0+0.1)});
tl.set("#rev_{k}",{{opacity:0}},{f(show0)});
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.07}},{{opacity:1,scale:1,duration:1.0,ease:"power2.out"}},{f(show0-0.4)});
tl.fromTo("#tint_{k}",{{opacity:0}},{{opacity:1,duration:1.0}},{f(show0-0.4)});
tl.fromTo("#badge_{k}",{{opacity:0,x:-22}},{{opacity:1,x:0,duration:.6,ease:"power2.out"}},{f(show0+0.15)});
tl.to("#fv_{k}",{{opacity:0,duration:.9,ease:"power1.in"}},{f(show1-0.5)});
tl.set("#fv_{k}",{{opacity:0}},{f(end)});
tl.to("#tint_{k}",{{opacity:0,duration:.9}},{f(show1-0.5)});
tl.set("#tint_{k}",{{opacity:0}},{f(end)});
tl.to("#badge_{k}",{{opacity:0,duration:.5}},{f(show1-0.4)});
tl.set("#badge_{k}",{{opacity:0}},{f(end)});
tl.to(".chrome_{k} .rail",{{opacity:0,duration:.4}},{f(end-0.4)});
tl.set(".chrome_{k} .rail",{{opacity:0}},{f(end)});
tl.to("#bg_{k}",{{opacity:0,duration:.7}},{f(end-0.5)});
tl.set("#bg_{k}",{{opacity:0}},{f(end)});
'''

JS=f'''
// 封面：首帧即满(无fade-in)；2s 短开场, 轻微推进运动
tl.set("#cover",{{opacity:1}},0);
tl.fromTo(".cv-grid",{{scale:1.0}},{{scale:1.022,duration:{f(COVER_D)},ease:"sine.out"}},0);
tl.to("#cover",{{opacity:0,duration:.5,ease:"power2.in"}},{f(COVER_D-0.5)});
tl.set("#cover",{{opacity:0}},{f(COVER_D)});

// 开场钩子
tl.set("#introblk",{{opacity:1}},{f(INTRO_T)});
{''.join(f'tl.fromTo("#ibn_{i}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.4,ease:"power2.out"}},{f(INTRO_T+0.3+i*0.28)});'+chr(10) for i in range(4))}
tl.fromTo("#ib_h",{{opacity:0,y:28}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{f(INTRO_T+1.8)});
{''.join(f'tl.fromTo("#ibs_{j}",{{opacity:0,scale:.9}},{{opacity:1,scale:1,duration:.4,ease:"back.out(1.6)"}},{f(INTRO_T+3.2+j*0.22)});'+chr(10) for j in range(4))}
tl.fromTo("#ib_q",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.6,ease:"power2.out"}},{f(INTRO_T+5.0)});
tl.to("#introblk",{{opacity:0,duration:.6,ease:"power2.in"}},{f(INTRO_T+INTRO_SEG-0.6)});
tl.set("#introblk",{{opacity:0}},{f(INTRO_T+INTRO_SEG)});

// 评分规则
tl.set("#rulesblk",{{opacity:1}},{f(RULES_T)});
tl.fromTo(".rb-eyebrow",{{opacity:0}},{{opacity:1,duration:.5}},{f(RULES_T+0.2)});
tl.fromTo(".rb-h",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.6,ease:"power3.out"}},{f(RULES_T+0.4)});
{''.join(f'tl.fromTo("#rbr_{d}",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:.45,ease:"power2.out"}},{f(RULES_T+1.2+d*0.5)});tl.to("#rbf_{d}",{{width:"{[30,25,20,15,10][d]*2.6:.0f}%",duration:.7,ease:"power2.out"}},{f(RULES_T+1.45+d*0.5)});'+chr(10) for d in range(5))}
tl.fromTo("#rb_foot",{{opacity:0}},{{opacity:1,duration:.6}},{f(RULES_T+4.6)});
tl.to("#rulesblk",{{opacity:0,duration:.6,ease:"power2.in"}},{f(RULES_T+RULES_SEG-0.6)});
tl.set("#rulesblk",{{opacity:0}},{f(RULES_T+RULES_SEG)});

{''.join(js_song(s,i) for i,s in enumerate(SONGS))}

// 总榜 + CTA（#1 揭晓后才出现）
tl.set("#outroblk",{{opacity:0}},{f(OUTRO_T-0.01)});
tl.fromTo("#outroblk",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(OUTRO_T)});
tl.fromTo(".ot-head",{{opacity:0}},{{opacity:1,duration:.5}},{f(OUTRO_T+0.4)});
{''.join(f'tl.fromTo("#otl_{i}",{{opacity:0,x:-18}},{{opacity:1,x:0,duration:.45,ease:"power2.out"}},{f(OUTRO_T+0.8+i*0.22)});'+chr(10) for i in range(4))}
tl.fromTo("#ot_q",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{f(OUTRO_T+2.4)});
tl.fromTo("#ot_cta",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6,ease:"power2.out"}},{f(OUTRO_T+3.4)});
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
{rules}
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
Path("hf/meta.json").write_text('{"id":"main","name":"zwtl-duet-pk"}', encoding="utf-8")
print("index.html:",len(html),"bytes; TOTAL",TOTAL,"s")
print("ALL BUILD DONE")
