#!/usr/bin/env python3
"""全片：《顾里之前，她明明是甜妹啊。》倒数5→1，约5.2分钟。
封面3s + 开头12s(精简) + 5段(床→swell→连续副歌≥30s + ducking + 反差转场) + 结尾互动。
持久 No.X+歌名 徽标(卡片消失后仍在) + 左倒数轨。
s5-s2=官方MV连续段(footage窗==音乐窗,口型同步)；s1=Little Sunshine救场(同期甜镜montage + 干净音轨)。
渲染后必须 mux master.wav。
FOOT 的 chorus_start 来自 footage-prep workflow；clips/vert_*.mp4 已 letterbox。"""
import subprocess, json, wave, contextlib
from pathlib import Path

ROOT = Path("/Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet")
A = ROOT/"audio"; C = ROOT/"clips"; HF = ROOT/"hf"; RAW = ROOT/"raw"
def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"
def wdur(p):
    with contextlib.closing(wave.open(str(p))) as w: return round(w.getnframes()/w.getframerate(),3)
def _clip_dur(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 99.0

_NJ = json.loads((A/"full_narration.json").read_text())
NARR = {k:v["dur"] for k,v in _NJ.items()}
NARR_TXT = {k:v["text"] for k,v in _NJ.items()}

# ============ 节奏常量 ============
COVER_D=3.0; INTRO_LEAD=0.3; INTRO_TAIL=1.1
LEAD=0.15; PRE=0.8; POST=1.2; SWELL=1.5; BED=0.20; TAIL=1.0
SHOW=30.0; SHOW_LAST=34.0; MID_OVER=5.0
DUCK=0.55   # 金句期音乐回落

# ============ 选源(prep workflow 填) + 每首元数据 ============
# kind=mv: 连续官方MV段(clips/vert_<key>.mp4, raw/<sec> 音轨)；chorus_start=副歌在section内秒
# s1 kind=montage: 干净音轨 littlesunshine + 同期甜镜 clips
SONGS = [
 dict(key="s5", no="5", name="又圆了的月亮", en="", album="2009《爱异想》", tag="苦甜 · 月光味的倔强",
      kw="苦甜", kind="mv", sec="s5_yueliang", chorus_start=70.0, show=27.0,
      pri="#9FB3C8", acc="#E8E2D6", tintc="rgba(120,150,190,.20)",
      trans=None),
 dict(key="s4", no="4", name="快一点", en="", album="2007《隐形超人》", tag="元气 · 校园 · 初代甜妹",
      kw="元气", kind="mv", sec="s4_kuaiyidian", chorus_start=52.0, show=26.0,
      pri="#F7A23B", acc="#FCD96B", tintc="rgba(247,162,59,.18)",
      trans="还没到顾里的冷脸时期，<br>她已经，有点小倔强了。"),
 dict(key="s3", no="3", name="卡通人生", en="", album="2010《烟火》· 广告主题曲", tag="鬼马 · 童话 · 可爱暴击",
      kw="鬼马", kind="mv", sec="s3_katong", chorus_start=50.0, show=30.0,
      pri="#F4A9C0", acc="#FFE3F0", tintc="rgba(244,169,192,.20)",
      trans="甜妹，也不是只会撒娇——<br>她还可以，很鬼马。"),
 dict(key="s2", no="2", name="爱异想", en="", album="2009《爱异想》同名主打", tag="甜酷 · 嘴硬心软 · 反差萌",
      kw="甜酷", kind="mv", sec="s2_aiyixiang", chorus_start=42.0, show=30.0,
      pri="#E8597B", acc="#C9CED6", tintc="rgba(232,89,123,.18)",
      trans="你以为她后来才有气场？<br>早期的甜里，就藏着锋利。"),
 dict(key="s1", no="1", name="Little Sunshine", en="Little Sunshine", album="2010《烟火》", tag="小太阳 · 清爽甜 · 顾里之前的郭采洁",
      kw="小太阳", kind="montage", sec="littlesunshine_audio", chorus_start=49.0, show=34.0,
      pri="#FFC93C", acc="#FFF1D6", tintc="rgba(255,201,60,.16)",
      trans="而最后这一首，<br>才是本期真正的——小太阳。",
      mont=["w_yx_b","w_yx_c","w_geita_b","w_yx_garden","w_yx_a","w_geita_a","w_yx_b","w_yx_c"]),
]
SK = {s["key"]:s for s in SONGS}

# ============ 时间轴 ============
def seg_len(s):
    voice=NARR[f"{s['key']}_voice"]; tr=NARR[s['transkey']] if s.get('transkey') else 0.0
    show=s["show"]
    return LEAD + tr + PRE + voice + POST + SWELL + show + TAIL
# 转场 voice key
for s in SONGS:
    s["transkey"] = {"s4":"t5_4","s3":"t4_3","s2":"t3_2","s1":"t2_1"}.get(s["key"])

intro_seg = COVER_D + INTRO_LEAD + NARR["intro"] + INTRO_TAIL
outro_seg = LEAD + NARR["outro"] + 3.0

starts={}; t=0.0
starts["intro"]=(t,intro_seg); t+=intro_seg
for s in SONGS:
    L=seg_len(s); starts[s["key"]]=(t,L); t+=L
starts["outro"]=(t,outro_seg); t+=outro_seg
TOTAL=round(t,3)
print(f"TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

def anchors(s):
    voice=NARR[f"{s['key']}_voice"]; tr=NARR[s['transkey']] if s.get('transkey') else 0.0
    show=s["show"]
    tr0=LEAD
    v0=LEAD+tr+PRE
    v1=v0+voice
    sw0=v1+POST
    full0=sw0+SWELL
    full1=full0+show
    mid0=full1-MID_OVER
    return dict(tr0=tr0, v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1, mid0=mid0, seg=seg_len(s), trdur=tr)

# ============ 音频 master(逐段) ============
Path(HF).mkdir(exist_ok=True); (ROOT/"build/segs").mkdir(parents=True, exist_ok=True)
def music_seek(s):
    a=anchors(s); return round(s["chorus_start"]-a["full0"],3)  # 让 section 的 chorus 落在 full0

def build_seg(s):
    a=anchors(s); seg=a["seg"]; full0=a["full0"]; full1=a["full1"]
    show=s["show"]
    if s["kind"]=="mv":
        src=str(next(RAW.glob(f"{s['sec']}.*")))
    else:
        src=str(RAW/"littlesunshine_audio.wav")
    mseek=music_seek(s)
    # 音乐包络：0..LEAD=0；LEAD..v0 ramp→BED；v0..sw0=BED；sw0..full0 swell→1；full0..full1=1(金句段回落)；
    v0=a["v0"]; sw0=a["sw0"]; mid0=a["mid0"]; rmp=LEAD+0.8
    env=(f"(lt(t,{LEAD}))*0"
         f"+(between(t,{LEAD},{rmp}))*({BED}*(t-{LEAD})/0.8)"
         f"+(between(t,{rmp},{sw0}))*{BED}"
         f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
         f"+(between(t,{full0},{mid0}))*1.0"
         f"+(between(t,{mid0},{full1}))*{DUCK}"
         f"+(gte(t,{full1}))*1.0")
    # voice 输入：转场voice(若有)在 tr0 起；song voice 在 v0 起
    vin=[]; fc=[]
    idx=1
    inputs=["-i",src]
    if a["trdur"]>0:
        inputs+=["-i",str(A/f"{s['transkey']}.wav")]
        fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[tv]")
        vin.append("[tv]"); idx+=1
    inputs+=["-i",str(A/f"{s['key']}_voice.wav")]
    fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[sv]")
    vin.append("[sv]"); idx+=1
    inputs+=["-i",str(A/f"{s['key']}_mid.wav")]
    fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(mid0*1000)}|{int(mid0*1000)},volume=2.0[mv]")
    vin.append("[mv]")
    # 音乐
    fc.insert(0, f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
                 f"atrim={max(mseek,0)}:{max(mseek,0)+seg},asetpts=PTS-STARTPTS,"
                 f"volume='{env}':eval=frame,afade=t=out:st={full1}:d={seg-full1}[mus]")
    allm="[mus]"+"".join(vin)
    fc.append(f"{allm}amix=inputs={1+len(vin)}:normalize=0:duration=longest,apad,atrim=0:{seg},asetpts=PTS-STARTPTS,alimiter=limit=0.96[out]")
    out=str(ROOT/f"build/segs/seg_{s['key']}.wav")
    run(["ffmpeg","-v","error"]+inputs+["-filter_complex",";".join(fc),"-map","[out]","-ac","2","-ar","48000",out,"-y"])
    return out

# intro 段：用 s5 section 的早段做低 ambient bed + intro voice
def build_intro():
    src=str(next(RAW.glob("s5_yueliang.*")))
    vat=COVER_D+INTRO_LEAD
    run(["ffmpeg","-v","error","-i",src,"-i",str(A/"intro.wav"),"-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(vat*1000)}|{int(vat*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=8:{8+intro_seg},asetpts=PTS-STARTPTS,"
     f"volume=0.17,afade=t=in:st=0:d=1.0,afade=t=out:st={intro_seg-1.4}:d=1.4[bed];"
     f"[v][bed]amix=inputs=2:normalize=0:duration=longest,apad,atrim=0:{intro_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",str(ROOT/"build/segs/seg_intro.wav"),"-y"])

def build_outro():
    src=str(RAW/"littlesunshine_audio.wav")
    run(["ffmpeg","-v","error","-i",src,"-i",str(A/"outro.wav"),"-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=60:{60+outro_seg},asetpts=PTS-STARTPTS,"
     f"volume=0.20,afade=t=in:st=0:d=1.0,afade=t=out:st={outro_seg-2.3}:d=2.3[bed];"
     f"[v][bed]amix=inputs=2:normalize=0:duration=longest,apad,atrim=0:{outro_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",str(ROOT/"build/segs/seg_outro.wav"),"-y"])

print("building audio segs...")
build_intro()
for s in SONGS: build_seg(s); print("  seg",s["key"],"done")
build_outro()
seglist=ROOT/"build/segs/seglist.txt"
order=["intro","s5","s4","s3","s2","s1","outro"]
seglist.write_text("".join(f"file 'seg_{k}.wav'\n" for k in order),encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(seglist),"-ac","2","-ar","48000",str(HF/"master.wav"),"-y"])
print("master dur:", wdur(HF/"master.wav"), "planned:", TOTAL)

# ============ 预切 footage 窗 → clips_seg ============
(HF/"clips_seg").mkdir(exist_ok=True)
seg_abs={}
for k in order: seg_abs[k]=starts[k][0]
PRE_ROLL=1.0
for s in SONGS:
    a=anchors(s)
    if s["kind"]=="mv":
        mseek=max(music_seek(s)-PRE_ROLL,0); seg=a["seg"]+PRE_ROLL
        src=str(C/f"vert_{s['key']}.mp4")
        run(["ffmpeg","-v","error","-ss",str(mseek),"-i",src,"-t",str(seg),
             "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
             str(HF/"clips_seg"/f"{s['key']}.mp4"),"-y"])
    else:
        seg=a["seg"]; n=len(s["mont"]); step=seg/n
        for i,clip in enumerate(s["mont"]):
            d=min(step+1.5, _clip_dur(C/f"{clip}.mp4"))
            run(["ffmpeg","-v","error","-i",str(C/f"{clip}.mp4"),"-t",str(round(d,2)),
                 "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
                 str(HF/"clips_seg"/f"s1_m{i}.mp4"),"-y"])
print("clips_seg cut")

# Copy 开头复用甜镜 clips into hf/clips_seg2 (stills/cover_assets 已在 hf/ 来自样片)
import shutil
(HF/"clips_seg2").mkdir(exist_ok=True)
for nm in ["w_yx_a","w_yx_garden"]:
    shutil.copy(str(C/f"{nm}.mp4"), str(HF/"clips_seg2"/f"{nm}.mp4"))

# ============================================================
# HTML composition
# ============================================================
seg_anchor={}
for s in SONGS:
    a=anchors(s); base=seg_abs[s["key"]]
    seg_anchor[s["key"]]={k:round(base+v,3) for k,v in a.items() if k!="seg"}
    seg_anchor[s["key"]]["start"]=round(base,3); seg_anchor[s["key"]]["end"]=round(base+a["seg"],3)
INTRO_T=seg_abs["intro"]; INTRO_D=intro_seg
OUTRO_T=seg_abs["outro"]; OUTRO_D=outro_seg
NS=len(SONGS)

foot_dom=[]; foot_js=[]; trk=0
def nt():
    global trk; trk+=1; return trk

# ---- 封面（双肖像卡，复用样片）----
cover=f'''<div id="cover" class="clip" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="200">
  <div class="cv-glow-l"></div><div class="cv-glow-r"></div>
  <div class="cv-card cv-card-l"></div><div class="cv-card cv-card-r"></div>
  <div class="cv-seam"></div><div class="cv-grain"></div>
  <div class="cv-clabel cv-clabel-l">顾里 · 高冷</div><div class="cv-clabel cv-clabel-r">早期 · 甜妹</div>
  <div class="cv-eyebrow">华 语 甜 妹 考 古 · 郭 采 洁</div>
  <div class="cv-hook"><span class="hk-pill">这真的是同一个郭采洁？</span></div>
  <div class="cv-title"><h1>顾里之前，<br>她明明是<span class="ti-acc">甜妹</span>啊。</h1>
    <div class="ti-sub">短发红唇之前，她是一颗小太阳</div></div>
</div>'''

# ---- 开头反差 montage（cover后~13s）----
IF=[
  dict(id="if1",kind="still",asset="guli1",t0=COVER_D-0.4,dur=5.2,kb=(1.06,1.16,"58% 33%")),
  dict(id="if2",kind="video",asset="w_yx_a",t0=COVER_D+4.4,dur=5.4),
  dict(id="if3",kind="still",asset="guli2",t0=COVER_D+9.2,dur=4.0,kb=(1.05,1.15,"60% 40%")),
  dict(id="if4",kind="video",asset="w_yx_garden",t0=COVER_D+12.4,dur=INTRO_T+INTRO_D-(COVER_D+12.4)+1.0),
]
for f in IF:
    tk=nt()
    if f["kind"]=="still":
        foot_dom.append(f'<div id="{f["id"]}" class="kb clip" data-start="{fmt(f["t0"])}" data-duration="{fmt(f["dur"])}" data-track-index="{tk}" style="background-image:url(stills/{f["asset"]}.jpg);background-position:{f["kb"][2]}"></div>')
        s0,e0,_=f["kb"]
        foot_js.append(f'tl.set("#{f["id"]}",{{scale:{s0}}},{fmt(f["t0"])});tl.fromTo("#{f["id"]}",{{opacity:0}},{{opacity:1,duration:.9}},{fmt(f["t0"])});tl.to("#{f["id"]}",{{scale:{e0},duration:{f["dur"]},ease:"none"}},{fmt(f["t0"])});tl.to("#{f["id"]}",{{opacity:0,duration:.8}},{fmt(f["t0"]+f["dur"]-0.8)});tl.set("#{f["id"]}",{{opacity:0}},{fmt(f["t0"]+f["dur"])});')
    else:
        foot_dom.append(f'<video id="{f["id"]}" class="fv clip" data-start="{fmt(f["t0"])}" data-duration="{fmt(f["dur"])}" data-track-index="{tk}" src="clips_seg2/{f["asset"]}.mp4" muted playsinline></video>')
        foot_js.append(f'tl.fromTo("#{f["id"]}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:.9}},{fmt(f["t0"])});tl.to("#{f["id"]}",{{opacity:0,duration:.8}},{fmt(f["t0"]+f["dur"]-0.8)});tl.set("#{f["id"]}",{{opacity:0}},{fmt(f["t0"]+f["dur"])});')

# 开头冷/甜标签
OLABS=[("ol1","ol-cold","顾里 · 高冷",COVER_D-0.2,4.8),("ol2","ol-warm","早期 · 甜妹",COVER_D+4.8,INTRO_T+INTRO_D-(COVER_D+4.8)-0.3)]
openlab_dom="".join(f'<div id="{i}" class="clip ollab" data-start="{fmt(t0)}" data-duration="{fmt(d)}" data-track-index="{nt()}"><span class="ol-tag {c}">{x}</span></div>' for (i,c,x,t0,d) in OLABS)
openlab_js="".join(f'tl.fromTo("#{i}",{{opacity:0,x:-22}},{{opacity:1,x:0,duration:.5}},{fmt(t0)});tl.to("#{i}",{{opacity:0,duration:.45}},{fmt(t0+d-0.5)});tl.set("#{i}",{{opacity:0}},{fmt(t0+d)});' for (i,c,x,t0,d) in OLABS)

# ---- 每首歌 footage + chrome ----
chrome_dom=[]; chrome_js=[]
for si,s in enumerate(SONGS):
    k=s["key"]; A_=seg_anchor[k]; st=A_["start"]; en=A_["end"]; bt=100+si*10
    v0=A_["v0"]; sw0=A_["sw0"]; full0=A_["full0"]; full1=A_["full1"]; mid0=A_["mid0"]; tr0=A_["tr0"]
    fade=en-1.0
    # footage
    if s["kind"]=="mv":
        fst=st-PRE_ROLL; fdur=A_["end"]-st+PRE_ROLL
        tk=nt()
        foot_dom.append(f'<video id="fv_{k}" class="fv clip" data-start="{fmt(fst)}" data-duration="{fmt(fdur)}" data-track-index="{tk}" src="clips_seg/{k}.mp4" muted playsinline></video>')
        foot_js.append(f'tl.fromTo("#fv_{k}",{{opacity:0,scale:1.05}},{{opacity:1,scale:1.0,duration:1.0}},{fmt(fst)});tl.to("#fv_{k}",{{opacity:0,duration:1.0}},{fmt(fade)});tl.set("#fv_{k}",{{opacity:0}},{fmt(en)});')
    else:
        n=len(s["mont"]); seg=A_["end"]-st; step=seg/n
        for i in range(n):
            ct=st-PRE_ROLL+i*step; cd=step+1.4
            tk=nt()
            foot_dom.append(f'<video id="fv_{k}_{i}" class="fv clip" data-start="{fmt(ct)}" data-duration="{fmt(cd)}" data-track-index="{tk}" src="clips_seg/s1_m{i}.mp4" muted playsinline></video>')
            fo=ct+cd-1.0
            foot_js.append(f'tl.fromTo("#fv_{k}_{i}",{{opacity:0,scale:1.05}},{{opacity:1,scale:1.0,duration:1.0}},{fmt(ct)});tl.to("#fv_{k}_{i}",{{opacity:0,duration:1.0}},{fmt(fo)});tl.set("#fv_{k}_{i}",{{opacity:0}},{fmt(ct+cd)});')
    # tint
    chrome_dom.append(f'<div id="tint_{k}" class="clip tint" data-start="{fmt(st-PRE_ROLL)}" data-duration="{fmt(en-st+PRE_ROLL)}" data-track-index="{bt}" style="background:linear-gradient(180deg,{s["tintc"]} 0%, rgba(20,14,8,.30) 42%, rgba(16,10,6,.82) 100%)"></div>')
    chrome_js.append(f'tl.fromTo("#tint_{k}",{{opacity:0}},{{opacity:1,duration:1.2}},{fmt(st-PRE_ROLL)});tl.to("#tint_{k}",{{opacity:0,duration:1.0}},{fmt(fade)});tl.set("#tint_{k}",{{opacity:0}},{fmt(en)});')
    # 倒数轨
    dots="".join(f'<div class="rd{" act" if j==si else (" past" if j<si else "")}"><span>{SONGS[j]["no"]}</span></div>' for j in range(NS))
    chrome_dom.append(f'<div id="rail_{k}" class="clip rail" data-start="{fmt(st)}" data-duration="{fmt(en-st)}" data-track-index="{bt+1}" style="--pri:{s["pri"]}">{dots}</div>')
    chrome_js.append(f'tl.fromTo("#rail_{k}",{{opacity:0}},{{opacity:1,duration:.7}},{fmt(st+0.2)});tl.to("#rail_{k}",{{opacity:0,duration:.6}},{fmt(en-0.5)});tl.set("#rail_{k}",{{opacity:0}},{fmt(en)});')
    # 持久 No+歌名 徽标（卡片消失后仍在，到段末）
    namedisp = s["en"] if s["en"] else f'《{s["name"]}》'
    chrome_dom.append(f'<div id="badge_{k}" class="clip badge" data-start="{fmt(v0)}" data-duration="{fmt(en-v0)}" data-track-index="{bt+2}" style="--pri:{s["pri"]}"><span class="b-no">No.<b>{s["no"]}</b></span><span class="b-nm">{namedisp}</span></div>')
    chrome_js.append(f'tl.fromTo("#badge_{k}",{{opacity:0,x:-16}},{{opacity:1,x:0,duration:.7,ease:"power2.out"}},{fmt(v0)});tl.to("#badge_{k}",{{opacity:0,duration:.7}},{fmt(en-0.6)});tl.set("#badge_{k}",{{opacity:0}},{fmt(en)});')
    # 信息卡（旁白期，swell 淡出）
    chrome_dom.append(f'''<div id="card_{k}" class="clip card" data-start="{fmt(v0)}" data-duration="{fmt(sw0-v0+0.6)}" data-track-index="{bt+3}" style="--pri:{s["pri"]};--acc:{s["acc"]}">
      <div class="c-nm">{("《"+s["name"]+"》") if not s["en"] else s["en"]}</div>
      <div class="c-al">{s["album"]}</div>
      <div class="c-tag"><span class="dot"></span>{s["tag"]}</div></div>''')
    chrome_js.append(f'tl.fromTo("#card_{k}",{{opacity:0,y:36}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{fmt(v0+0.3)});tl.to("#card_{k}",{{opacity:0,y:-14,duration:.55,ease:"power2.in"}},{fmt(sw0)});tl.set("#card_{k}",{{opacity:0}},{fmt(sw0+0.6)});')
    # 大关键词（副歌）
    chrome_dom.append(f'<div id="kw_{k}" class="clip kw" data-start="{fmt(full0-1)}" data-duration="{fmt(en-(full0-1))}" data-track-index="{bt+4}" style="color:{s["pri"]}">{s["kw"]}</div>')
    chrome_js.append(f'tl.fromTo("#kw_{k}",{{opacity:0,scale:.92}},{{opacity:.5,scale:1.0,duration:1.6,ease:"power3.out"}},{fmt(full0-0.4)});tl.to("#kw_{k}",{{opacity:0,duration:1.0}},{fmt(en-1.3)});tl.set("#kw_{k}",{{opacity:0}},{fmt(en)});')
    # 金句
    chrome_dom.append(f'<div id="mid_{k}" class="clip midq" data-start="{fmt(mid0-0.5)}" data-duration="{fmt(en-(mid0-0.5))}" data-track-index="{bt+5}">{NARR_TXT[k+"_mid"]}</div>')
    chrome_js.append(f'tl.fromTo("#mid_{k}",{{opacity:0,y:26}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(mid0)});tl.to("#mid_{k}",{{opacity:0,y:-12,duration:.55}},{fmt(full1-0.8)});tl.set("#mid_{k}",{{opacity:0}},{fmt(en)});')
    # 反差转场卡
    if s.get("transkey"):
        chrome_dom.append(f'<div id="tr_{k}" class="clip transcard" data-start="{fmt(st)}" data-duration="{fmt(v0-st+0.3)}" data-track-index="{bt+6}"><div class="tc-line">{s["trans"]}</div></div>')
        chrome_js.append(f'tl.fromTo("#tr_{k}",{{opacity:0}},{{opacity:1,duration:.45}},{fmt(st+0.15)});tl.fromTo("#tr_{k} .tc-line",{{y:14}},{{y:0,duration:.6,ease:"power2.out"}},{fmt(st+0.15)});tl.to("#tr_{k}",{{opacity:0,duration:.5}},{fmt(v0-0.35)});tl.set("#tr_{k}",{{opacity:0}},{fmt(v0+0.1)});')

# ---- 结尾 ----
outro_dom=f'''<div id="outro" class="clip outroblk" data-start="{fmt(OUTRO_T)}" data-duration="{fmt(OUTRO_D)}" data-track-index="310">
  <div class="ot-rail">{"".join(f'<div class="ot-li"><span class="ot-n">No.{s["no"]}</span><span class="ot-m">{(s["en"] or "《"+s["name"]+"》")}</span></div>' for s in SONGS)}</div>
  <h2 class="ot-h">顾里之前，<br>她明明是个甜妹啊。</h2>
  <p class="ot-q">你是从哪一首歌认识她的？</p>
</div>'''
outro_js=(f'tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.9}},{fmt(OUTRO_T+0.3)});'
  + "".join(f'tl.fromTo(".ot-rail .ot-li:nth-child({i+1})",{{opacity:0,x:-18}},{{opacity:.92,x:0,duration:.5}},{fmt(OUTRO_T+1.0+i*0.22)});' for i in range(NS))
  + f'tl.fromTo(".ot-h",{{opacity:0,y:30}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{fmt(OUTRO_T+2.6)});'
  + f'tl.fromTo(".ot-q",{{opacity:0,y:10}},{{opacity:.95,y:0,duration:.7}},{fmt(OUTRO_T+OUTRO_D-NARR["outro"]+NARR["outro"]-3.2)});')

audio=f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="190" src="master.wav" data-volume="1"></audio>'
print("HTML elements built")


CSS = '''
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1920px; overflow:hidden; background:#160E08;
  font-family:"Noto Serif SC",serif; color:#FFF6EC; -webkit-font-smoothing:antialiased; }
.fv,.kb { position:absolute; inset:0; width:1080px; height:1920px; z-index:1; opacity:0; }
.fv { object-fit:cover; } .kb { background-size:cover; background-repeat:no-repeat; transform-origin:center; }
.tint { position:absolute; inset:0; z-index:2; opacity:0; }
#grain { position:absolute; inset:0; z-index:3; pointer-events:none; opacity:0;
  background:radial-gradient(ellipse at 50% 42%, transparent 54%, rgba(18,10,6,.5) 100%); }
#grain::after { content:""; position:absolute; inset:0; mix-blend-mode:overlay; opacity:.42;
  background-image:radial-gradient(circle at 12% 22%, rgba(255,255,255,.05) 0 .6px, transparent 1px),
    radial-gradient(circle at 72% 64%, rgba(255,255,255,.045) 0 .6px, transparent 1px);
  background-size:190px 190px,230px 230px; }

/* Cover */
#cover { position:absolute; inset:0; z-index:200; overflow:hidden;
  background:linear-gradient(108deg, #181B23 0%, #2A2E38 33%, #2E2620 49%, #4A3328 64%, #6E4631 100%); }
.cv-glow-l { position:absolute; left:-8%; top:6%; width:58%; height:56%; background:radial-gradient(ellipse at 42% 42%, rgba(120,140,175,.22), transparent 70%); }
.cv-glow-r { position:absolute; right:-8%; top:5%; width:60%; height:58%; background:radial-gradient(ellipse at 58% 42%, rgba(255,193,120,.26), transparent 70%); }
.cv-seam { position:absolute; top:-60px; bottom:-60px; left:50%; width:4px; z-index:2;
  background:linear-gradient(180deg, rgba(255,231,182,0), rgba(255,231,182,.8) 35%, rgba(255,231,182,.8) 65%, rgba(255,231,182,0));
  transform:translateX(-50%) rotate(7deg); box-shadow:0 0 30px rgba(255,220,150,.55); }
.cv-grain { position:absolute; inset:0; z-index:2; opacity:.4; mix-blend-mode:overlay;
  background-image:radial-gradient(circle at 20% 30%, rgba(255,255,255,.05) 0 .6px, transparent 1px); background-size:200px 200px; }
.cv-card { position:absolute; top:236px; width:468px; height:614px; border-radius:26px; z-index:3; background-size:cover; transform-origin:center; box-shadow:0 30px 72px rgba(0,0,0,.55); }
.cv-card-l { left:54px; background-image:url("cover_assets/cover_guli.jpg"); background-position:50% 22%; border:3px solid rgba(214,67,90,.55); }
.cv-card-r { right:54px; background-image:url("cover_assets/cover_sweet.jpg"); background-position:50% 18%; border:3px solid rgba(255,201,60,.72); }
.cv-card::after { content:""; position:absolute; inset:0; border-radius:23px; }
.cv-card-l::after { background:linear-gradient(180deg, rgba(28,32,42,.12), rgba(18,20,28,.5)); }
.cv-card-r::after { background:linear-gradient(180deg, rgba(255,205,130,.08), rgba(42,26,14,.4)); }
.cv-clabel { position:absolute; top:872px; width:468px; text-align:center; z-index:4; font-family:"Noto Sans SC",sans-serif; font-size:31px; font-weight:800; letter-spacing:.14em; }
.cv-clabel-l { left:54px; color:#EDB9C3; text-shadow:0 2px 12px rgba(0,0,0,.6); }
.cv-clabel-r { right:54px; color:#FFE2A4; text-shadow:0 2px 12px rgba(0,0,0,.6); }
.cv-eyebrow { position:absolute; top:104px; left:0; right:0; text-align:center; z-index:6; font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:800; letter-spacing:.42em; color:#FFE6A6; text-shadow:0 2px 14px rgba(0,0,0,.6); }
.cv-hook { position:absolute; top:948px; left:60px; right:60px; z-index:6; text-align:center; }
.cv-hook .hk-pill { display:inline-block; padding:18px 44px; border-radius:999px; background:rgba(20,14,10,.46); border:2px solid rgba(255,225,170,.6); backdrop-filter:blur(6px); font-family:"Ma Shan Zheng",cursive; font-size:64px; color:#FFF1D6; letter-spacing:.04em; text-shadow:0 3px 20px rgba(0,0,0,.7); }
.cv-title { position:absolute; bottom:148px; left:64px; right:64px; z-index:6; text-align:center; }
.cv-title h1 { font-family:"Noto Serif SC",serif; font-size:120px; font-weight:900; line-height:1.1; color:#FFF6EC; letter-spacing:-1px; text-shadow:0 4px 30px rgba(0,0,0,.78); }
.cv-title .ti-acc { color:#FFC93C; }
.cv-title .ti-sub { margin-top:26px; font-family:"Noto Sans SC",sans-serif; font-size:34px; font-weight:700; letter-spacing:.1em; color:rgba(255,246,236,.88); text-shadow:0 2px 16px rgba(0,0,0,.7); }

/* 开头标签 */
.ollab { position:absolute; left:64px; top:120px; z-index:5; opacity:0; }
.ollab .ol-tag { display:inline-block; padding:12px 26px; border-radius:999px; font-family:"Noto Sans SC",sans-serif; font-size:32px; font-weight:800; letter-spacing:.14em; }
.ol-cold { background:rgba(28,32,42,.62); border:2px solid rgba(214,67,90,.7); color:#FAD7DE; }
.ol-warm { background:rgba(255,201,60,.18); border:2px solid rgba(255,201,60,.8); color:#FFEFC2; }

/* 倒数轨 */
.rail { position:absolute; left:44px; top:556px; width:64px; z-index:5; opacity:0; }
.rail .rd { position:relative; width:60px; height:60px; margin:13px 0; border-radius:50%; background:rgba(20,16,12,.66); border:2px solid rgba(255,255,255,.22); display:flex; align-items:center; justify-content:center; }
.rail .rd span { font-family:"Noto Sans SC",sans-serif; font-size:26px; font-weight:800; color:rgba(255,255,255,.7); }
.rail .rd.past { background:rgba(86,80,72,.55); }
.rail .rd.act { background:var(--pri); border-color:var(--pri); box-shadow:0 0 30px var(--pri); transform:scale(1.16); }
.rail .rd.act span { color:#1A130E; }

/* 持久 No+歌名 徽标 */
.badge { position:absolute; left:60px; top:150px; z-index:5; opacity:0; display:flex; align-items:baseline; gap:18px; }
.badge .b-no { font-family:"Noto Serif SC",serif; font-weight:900; font-size:74px; color:var(--pri); line-height:.9; letter-spacing:.02em; text-shadow:0 4px 22px rgba(0,0,0,.55); }
.badge .b-no b { font-size:104px; }
.badge .b-nm { font-family:"Noto Serif SC",serif; font-weight:700; font-size:42px; color:#FFF6EC; text-shadow:0 2px 16px rgba(0,0,0,.75); }

/* 信息卡 */
.card { position:absolute; left:56px; right:56px; bottom:432px; z-index:5; opacity:0; padding:32px 40px; border-radius:24px;
  background:linear-gradient(160deg, rgba(255,247,232,.15), rgba(255,247,232,.04)); backdrop-filter:blur(24px); border:1.5px solid rgba(255,225,170,.3); box-shadow:0 28px 70px rgba(0,0,0,.5); }
.card .c-nm { font-family:"Noto Serif SC",serif; font-size:74px; font-weight:800; color:#FFF6EC; letter-spacing:.5px; }
.card .c-al { font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:500; color:rgba(255,246,236,.82); margin-top:14px; letter-spacing:.02em; }
.card .c-tag { display:inline-flex; align-items:center; gap:12px; margin-top:18px; font-family:"Noto Sans SC",sans-serif; font-size:31px; font-weight:700; color:var(--acc); }
.card .c-tag .dot { width:12px; height:12px; border-radius:50%; background:var(--pri); box-shadow:0 0 14px var(--pri); }

/* 大关键词 / 金句 */
.kw { position:absolute; left:0; right:0; bottom:300px; z-index:4; text-align:center; opacity:0; font-family:"Noto Serif SC",serif; font-size:300px; font-weight:900; line-height:.82; letter-spacing:-6px; mix-blend-mode:screen; filter:drop-shadow(0 10px 70px rgba(255,200,90,.22)); }
.midq { position:absolute; left:76px; right:76px; bottom:206px; z-index:5; text-align:center; opacity:0; font-family:"Noto Serif SC",serif; font-size:50px; font-weight:600; line-height:1.42; color:#FFF6EC; text-shadow:0 3px 22px rgba(0,0,0,.72); }

/* 反差转场卡 */
.transcard { position:absolute; inset:0; z-index:6; opacity:0; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg, rgba(16,10,6,.5), rgba(16,10,6,.74)); }
.transcard .tc-line { font-family:"Noto Serif SC",serif; font-size:64px; font-weight:700; line-height:1.46; text-align:center; color:#FFF1D6; padding:0 84px; text-shadow:0 4px 24px rgba(0,0,0,.75); }

/* 结尾 */
.outroblk { position:absolute; inset:0; z-index:8; opacity:0; background:radial-gradient(ellipse at 50% 38%, #2A1E14 0%, #160E08 72%); }
.ot-rail { position:absolute; top:430px; left:104px; right:104px; }
.ot-li { display:flex; align-items:baseline; gap:24px; padding:9px 0; opacity:0; border-bottom:1px solid rgba(255,255,255,.08); }
.ot-n { font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:800; color:#FFC93C; min-width:92px; }
.ot-m { font-family:"Noto Serif SC",serif; font-size:44px; font-weight:700; color:#FFF6EC; }
.ot-h { position:absolute; top:1000px; left:100px; right:100px; font-family:"Noto Serif SC",serif; font-size:96px; font-weight:900; line-height:1.1; color:#FFF6EC; letter-spacing:-1px; opacity:0; }
.ot-q { position:absolute; top:1320px; left:100px; right:100px; font-family:"Noto Sans SC",sans-serif; font-size:34px; font-weight:700; letter-spacing:.06em; color:#FFC93C; opacity:0; }
'''

cover_js=(f'tl.set("#cover",{{opacity:1}},0);'
  f'tl.set(".cv-card,.cv-clabel,.cv-title,.cv-hook,.cv-eyebrow,.cv-seam",{{opacity:1}},0);'
  f'tl.fromTo(".cv-card-l",{{scale:1.0}},{{scale:1.04,duration:{fmt(COVER_D)},ease:"none"}},0);'
  f'tl.fromTo(".cv-card-r",{{scale:1.0}},{{scale:1.04,duration:{fmt(COVER_D)},ease:"none"}},0);'
  f'tl.fromTo(".cv-hook .hk-pill",{{scale:.97}},{{scale:1.03,duration:1.4,yoyo:true,repeat:1,ease:"sine.inOut"}},0.4);'
  f'tl.to("#cover",{{opacity:0,duration:.7,ease:"power2.in"}},{fmt(COVER_D-0.7)});'
  f'tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});'
  f'tl.to("#grain",{{opacity:1,duration:1.0}},{fmt(COVER_D-0.2)});')

JS = cover_js + "".join(foot_js) + openlab_js + "".join(chrome_js) + outro_js

html=f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;600;700;800;900&family=Noto+Sans+SC:wght@500;700;800;900&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
  {chr(10).join(foot_dom)}
  {chr(10).join(chrome_dom)}
  <div id="grain" class="clip" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="300"></div>
  {cover}
  {openlab_dom}
  {outro_dom}
  {audio}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused:true }});
{JS}
window.__timelines["main"] = tl;
</script>
</body></html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"guocaijie-sweet-full"}', encoding="utf-8")
print("index.html written:", len(html), "bytes  TOTAL", TOTAL)
print("ALL BUILD DONE")
