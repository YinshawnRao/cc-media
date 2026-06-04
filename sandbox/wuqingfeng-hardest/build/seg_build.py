#!/usr/bin/env python3
"""分段渲染用：把整片按时间窗 [W0,W1] 生成一个独立 composition（时间轴整体平移到 0）。
原因：本机 Chrome 单条长 render 会在 ~1190 帧/worker 处累积内存崩溃（Target closed）；
分段每段 < 阈值，逐段渲染再 concat。音频用整片 master.wav 后期 mux，故本脚本不建音频、不放 <audio>。
窗对齐到 block 边界（label 不跨窗）。footage 用整片 footage.mp4 裁出对应窗段。
用法：WINDOW=W0,W1 SEG=seg1 python build/seg_build.py  → 写 hf_<SEG>/index.html + meta.json + footage 裁切。"""
import os, subprocess, wave, contextlib
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

A = "audio"; C = "clips"
LEAD = 0.3; DIG = 1.4; SHOW_REG = 14.0; SHOW_LAST = 18.0
d_intro = dur(f"{A}/intro.wav"); d_out = dur(f"{A}/outro.wav")
INTRO_END = round(LEAD + d_intro + 1.3, 3)

songs = [
    ("p5_wohaoxiang","05","《我好想你》","2013 · 苏打绿",["高位稳定","情绪拉满","声音不能粗"],"一到副歌就喊，<b>一秒就露馅</b>",SHOW_REG),
    ("p4_qifengle","04","《起风了》","2019 · 歌手",["长线条气息","高位咬字","清澈不薄"],"越想唱得像青峰，<b>破绽越藏不住</b>",SHOW_REG),
    ("p3_dixin","03","《地心》","2019 · 歌手",["轻声压迫感","真假声转换","高位爆发"],"越安静，<b>越藏不住瑕疵</b>",SHOW_REG),
    ("p2_tongkuai","02","《痛快的哀艳》","2016 · 金曲奖",["音域跨两个八度","交响张力","持续输出"],"唱好是史诗，<b>唱塌成体测</b>",SHOW_REG),
    ("p1_pinlv","01","《频率》","Live · 苏打绿",["全程换声区","头声极限","轻而不虚"],"不是唱不上去，<b>是连赛道都进不去</b>",SHOW_LAST),
]
blocks = []; t = INTRO_END
for key,no,name,meta,tags,tagline,show in songs:
    dk = dur(f"{A}/{key}.wav"); L = round(LEAD+dk+0.2+DIG+show,3)
    full = round(t+LEAD+dk+0.2+DIG,3); end = round(t+L,3)
    blocks.append(dict(key=key,start=t,L=L,end=end,full=full,no=no,name=name,meta=meta,tags=tags,tagline=tagline))
    t = end
F_start = t; F_voice = round(F_start+LEAD,3); F_voice_end = round(F_voice+d_out,3)
F_end = round(F_voice_end+2.8,3); TOTAL = round(F_end+0.4,3)
COVER_END=4.9; CHIP_IN,CHIP_OUT=5.1,12.6; BRG_IN,BRG_OUT=12.9,round(INTRO_END-0.5,3)

# ---- window ----
W0, W1 = (float(x) for x in os.environ["WINDOW"].split(","))
SEG = os.environ["SEG"]; WLEN = round(W1-W0,3)
def P(x): return round(x-W0,3)                       # GSAP 位移（可为负→过去状态）
def emit(s,d):                                       # 裁到窗内：返回(start,dur)或None
    e=s+d
    if e<=W0+1e-6 or s>=W1-1e-6: return None
    ns=max(s,W0); ne=min(e,W1)
    return (round(ns-W0,3), round(ne-ns,3))
HF = Path(f"hf_{SEG}"); HF.mkdir(exist_ok=True)

# footage 裁出窗段
subprocess.run(["ffmpeg","-v","error","-ss",str(W0),"-i",f"{C}/footage.mp4","-t",str(WLEN),
                "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
                "-pix_fmt","yuv420p","-movflags","+faststart",str(HF/"footage_win.mp4"),"-y"],check=True)

vids = f'<video id="bg" class="fv" data-start="0" data-duration="{WLEN}" data-track-index="0" src="footage_win.mp4" muted playsinline></video>'

# overlays（全程）→ 窗内 [0,WLEN]
overlays = "".join(f'<div id="{i}" class="clip" data-start="0" data-duration="{WLEN}" data-track-index="{tk}"></div>'
                   for i,tk in [("scrim",1),("tint",8),("aur",10),("vig",7)])

parts=[vids, overlays]; js=[]
# cover/chips/bridge（intro 段）
_r=emit(0,COVER_END)
if _r:
    parts.append(f'<div id="cover" class="clip" data-start="{_r[0]}" data-duration="{_r[1]}" data-track-index="5"><div class="cv-kick">唱功盘点 · 换声区试炼</div><div class="cv-name">吴青峰</div><div class="cv-title">最难的5首</div><div class="cv-en">Wu Tsing-Fong — The Hardest Five</div><div class="cv-sub">听起来像羽毛 · <b>其实最难复刻</b></div></div>')
    js += [f'tl.set("#cover",{{opacity:1}},{P(0)});',
           f'tl.set(["#cover .cv-kick","#cover .cv-name","#cover .cv-title","#cover .cv-en","#cover .cv-sub"],{{opacity:1}},{P(0)});',
           f'tl.to("#cover .cv-title",{{scale:1.03,duration:3.2,transformOrigin:"left center",ease:"sine.inOut",yoyo:true,repeat:1}},{P(0.6)});',
           f'tl.to("#cover",{{y:-30,opacity:0,duration:.5,ease:"power2.in"}},{P(COVER_END-0.55)});',
           f'tl.set("#cover",{{opacity:0}},{P(COVER_END)});']
_r=emit(CHIP_IN,CHIP_OUT-CHIP_IN)
if _r:
    parts.append(f'<div id="chips" class="clip" data-start="{_r[0]}" data-duration="{_r[1]}" data-track-index="2"><div class="k">大众印象</div><ul class="imp-list"><li class="ci"><span class="strike">清亮<i class="xln"></i></span></li><li class="ci"><span class="strike">空灵<i class="xln"></i></span></li><li class="ci"><span class="strike">像羽毛一样飘<i class="xln"></i></span></li></ul><div class="imp-note">听着 <b>像呼吸一样轻</b> · 其实全是控制力</div></div>')
    js += [f'tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{P(CHIP_IN+0.1)});',
           f'tl.from("#chips .ci",{{x:-46,opacity:0,duration:.55,ease:"power3.out",stagger:.42}},{P(CHIP_IN+0.3)});',
           f'tl.to("#chips .ci:nth-child(1) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{P(CHIP_IN+2.2)});',
           f'tl.to("#chips .ci:nth-child(2) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{P(CHIP_IN+2.7)});',
           f'tl.to("#chips .ci:nth-child(3) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{P(CHIP_IN+3.2)});',
           f'tl.from("#chips .imp-note",{{opacity:0,y:14,duration:.5}},{P(CHIP_IN+3.9)});',
           f'tl.to("#chips",{{opacity:0,duration:.4,ease:"power1.in"}},{P(CHIP_OUT-0.45)});',
           f'tl.set("#chips",{{opacity:0}},{P(CHIP_OUT)});']
_r=emit(BRG_IN,BRG_OUT-BRG_IN)
if _r:
    parts.append(f'<div id="bridge" class="clip" data-start="{_r[0]}" data-duration="{_r[1]}" data-track-index="5"><div class="big"><small>公认最难唱</small>TOP 5</div><div class="line">换声区 · 头声 · <b>长线高压</b></div></div>')
    js += [f'tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{P(BRG_IN+0.1)});',
           f'tl.from("#bridge .big",{{scale:.7,opacity:0,duration:.6,ease:"back.out(1.4)"}},{P(BRG_IN+0.2)});',
           f'tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{P(BRG_IN+0.8)});',
           f'tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{P(BRG_OUT-0.45)});',
           f'tl.set("#bridge",{{opacity:0}},{P(BRG_OUT)});']
# 排名卡
for b in blocks:
    no=b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start=round(b["start"]+0.2,3); lf_dur=round(b["full"]-lf_start,3)
    lm_start=b["full"]; lm_dur=round(b["end"]-b["full"]+(0.4 if b is blocks[-1] else 0),3)
    climax=' climax' if no=="01" else ''
    crown='<div class="crown">公认天花板</div>' if no=="01" else '<div class="lab">最难 TOP 5</div>'
    tagchips="".join(f"<span>{x}</span>" for x in b["tags"])
    _rf=emit(lf_start,lf_dur)
    if _rf:
        parts.append(f'<div id="{fid}" class="clip labelFull{climax}" data-start="{_rf[0]}" data-duration="{_rf[1]}" data-track-index="2"><div class="rank"><div class="no">{no}</div>{crown}</div><div class="meta">{b["meta"]}</div><div class="song">{b["name"]}</div><div class="tags">{tagchips}</div><div class="tag">{b["tagline"]}</div></div>')
        js += [f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.7,ease:"power3.out"}},{P(lf_start+0.1)});',
               f'tl.from("#{fid} .rank>div:last-child",{{x:-24,opacity:0,duration:.5,ease:"power2.out"}},{P(lf_start+0.38)});',
               f'tl.from("#{fid} .meta",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{P(lf_start+0.5)});',
               f'tl.from("#{fid} .song",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{P(lf_start+0.62)});',
               f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{P(lf_start+0.95)});',
               f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{P(lf_start+1.35)});',
               f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{P(b["full"]-0.4)});',
               f'tl.set("#{fid}",{{opacity:0}},{P(b["full"])});']
    _rm=emit(lm_start,lm_dur)
    if _rm:
        parts.append(f'<div id="{mid}" class="clip labelMin{climax}" data-start="{_rm[0]}" data-duration="{_rm[1]}" data-track-index="4"><span class="no">{no}</span><span class="song">{b["name"]}</span></div>')
        js += [f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{P(lm_start+0.1)});',
               f'tl.to("#{mid}",{{opacity:0,duration:.4,ease:"power1.in"}},{P(b["end"]-0.35)});',
               f'tl.set("#{mid}",{{opacity:0}},{P(b["end"])});']
# 片尾
o_start=round(F_voice+0.2,3); o_dur=round(F_end-F_voice-0.2+0.4,3)
_ro=emit(o_start,o_dur)
if _ro:
    parts.append(f'<div id="outro" class="clip" data-start="{_ro[0]}" data-duration="{_ro[1]}" data-track-index="4"><div class="o1">吴青峰的轻，从来不是真的轻松</div><div class="o2">那些像羽毛的高音，<br>是最难复刻的控制力</div><div class="q">你心里他最难的一首，<b>是哪一首？</b></div><div class="bar"></div></div>')
    js += [f'tl.from("#outro .o1",{{y:24,opacity:0,duration:.6,ease:"power2.out"}},{P(F_voice+0.3)});',
           f'tl.from("#outro .o2",{{y:50,opacity:0,scale:1.05,duration:.8,ease:"power4.out"}},{P(F_voice+0.95)});',
           f'tl.from("#outro .q",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{P(F_voice+1.85)});',
           f'tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{P(F_voice+2.3)});']

CSS = Path("index.html").read_text(encoding="utf-8").split("<style>",1)[1].split("</style>",1)[0]
html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@700;800&family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{WLEN}" data-width="1080" data-height="1920">
{chr(10).join(parts)}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{chr(10).join(js)}
window.__timelines["main"]=tl;
</script></body></html>'''
(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"seg"}', encoding="utf-8")
print(f"{SEG}: window [{W0},{W1}] WLEN={WLEN} elems={len(parts)} tweens={len(js)} -> hf_{SEG}/")
