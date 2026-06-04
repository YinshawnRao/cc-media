#!/usr/bin/env python3
"""样片：梁博最难的5首歌 — 开场钩子 + 第五名《男孩》。
风格定调用：暗火/灼烧配色(暖黑→琥珀→猩红)，竖屏 1080x1920，女声旁白(zf_xiaoyi)。
结构：intro(大众印象反差钩子 → 最难5首标题 → TOP5 bridge) → 第五《男孩》(rank卡+介绍旁白+消化位+副歌展示)。
master.wav 逐段(床→swell→展示 + 旁白 ducking + 逐首 loudnorm)。之后 lint → render --sdr → mux。
全片 full_build.py 复用本文件的 CSS / JS 模式。"""
import subprocess, wave, contextlib
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
LEAD = 0.3; DIG = 1.4; SHOW = 6.0
BED_I = 0.06; BED_N = 0.13

d_intro = dur(f"{A}/intro.wav")
d_p5 = dur(f"{A}/p5_nanhai.wav")
INTRO_END = round(LEAD + d_intro + 1.3, 3)   # 消化位 1.3s

songs = [
    ("p5_nanhai", "vert_nanhai", "05", "《男孩》", "2017 · 歌手",
     ["换声区控制", "情绪强度", "大众熟悉度反噬"],
     "越是大家都熟的歌，<b>越藏不住功力</b>"),
]

# ---------- 时间轴 ----------
blocks = []
t = INTRO_END
for key, clip, no, name, meta, tags, tagline in songs:
    L = round(LEAD + dur(f"{A}/{key}.wav") + 0.2 + DIG + SHOW, 3)
    ns = round(t + LEAD, 3); ne = round(ns + dur(f"{A}/{key}.wav"), 3)
    full = round(ne + 0.2 + DIG, 3); end = round(t + L, 3)
    blocks.append(dict(key=key, clip=clip, start=t, L=L, end=end, ns=ns, ne=ne, full=full,
                       no=no, name=name, meta=meta, tags=tags, tagline=tagline))
    t = end
TOTAL = round(t + 0.6, 3)   # 末尾 0.6s 让最后展示帧不被硬切

# ---------- 音频分段 ----------
def envB(ne_loc, full_loc):
    sw = round(ne_loc + 0.2, 3)
    return (f"(lt(t,0.8))*({BED_N}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED_N}"
            f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_loc}))*1.0")

segs = []
# seg_intro: 灵魂歌手 底(自带音轨)做低床 + intro 旁白；先声后乐(~3.5s 进床)
veI = (f"(lt(t,3.5))*0+(between(t,3.5,4.5))*({BED_I}*(t-3.5)/1.0)+(gte(t,4.5))*{BED_I}")
run(["ffmpeg","-v","error","-i",f"{C}/vert_intro.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{INTRO_END},volume='{veI}':eval=frame[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_intro.wav","-y"])
segs.append("seg_intro.wav")

for b in blocks:
    seg_dur = b["L"]; dk = dur(f"{A}/{b['key']}.wav")
    ne_loc = round(LEAD + dk, 3); full_loc = round(b["full"] - b["start"], 3)
    ve = envB(ne_loc, full_loc)
    out = f"seg_{b['no']}.wav"
    run(["ffmpeg","-v","error","-i",f"{C}/{b['clip']}.mp4","-i",f"{A}/{b['key']}.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_dur},volume='{ve}':eval=frame[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- 时间点 (intro overlays 跟随旁白节拍) ----------
CHIP_IN, CHIP_OUT = 0.4, 6.6
TITLE_IN, TITLE_OUT = 6.9, 14.6
BRG_IN, BRG_OUT = 14.9, round(INTRO_END-0.6,3)

# footage（交替轨道 0/6）
fc = [("vert_intro", 0.0, INTRO_END)]
for b in blocks:
    fc.append((b["clip"], b["start"], b["L"]))
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{round(s,3)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i%2==0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i,(src,s,dv) in enumerate(fc))

# 标签
labels, tweens = [], []
for b in blocks:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = round(b["start"]+0.2,3); lf_dur = round(b["full"]-lf_start,3)
    lm_start = b["full"]; lm_dur = round(b["end"]-b["full"]+0.6,3)
    climax = ' climax' if no=="01" else ''
    crown = '<div class="crown">公认天花板</div>' if no=="01" else '<div class="lab">最难 TOP 5</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{lf_start}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{crown}</div>'
        f'<div class="meta">{b["meta"]}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>')
    labels.append(
        f'<div id="{mid}" class="clip labelMin{climax}" data-start="{lm_start}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>')
    tweens.append(f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.7,ease:"power3.out"}},{round(lf_start+0.1,3)});')
    tweens.append(f'tl.from("#{fid} .rank>div:last-child",{{x:-24,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+0.38,3)});')
    tweens.append(f'tl.from("#{fid} .meta",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{round(lf_start+0.5,3)});')
    tweens.append(f'tl.from("#{fid} .song",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{round(lf_start+0.62,3)});')
    tweens.append(f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{round(lf_start+0.95,3)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+1.35,3)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["full"]-0.4,3)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{b["full"]});')
    tweens.append(f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{round(lm_start+0.1,3)});')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0b0908;
  font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,6,5,.72) 0%,rgba(10,7,5,.16) 28%,rgba(10,7,5,.24) 56%,rgba(8,5,4,.88) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(118% 78% at 50% 38%,rgba(0,0,0,0) 40%,rgba(0,0,0,.6) 100%)}
#tint{position:absolute;inset:0;z-index:1;background:radial-gradient(90% 60% at 50% 30%,rgba(255,120,40,.10) 0%,rgba(0,0,0,0) 60%);mix-blend-mode:screen}
#grain{position:absolute;inset:0;z-index:8;opacity:.06;mix-blend-mode:soft-light;pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='280'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch' seed='7'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");background-size:280px 280px}

/* ---- intro: 大众印象 钩子 ---- */
.k{display:inline-flex;align-items:center;gap:16px;font-size:31px;font-weight:800;color:#ff9d3c;letter-spacing:.34em}
.k::before{content:"";width:50px;height:4px;background:linear-gradient(90deg,#ffb454,#e23a2e);border-radius:2px;box-shadow:0 0 18px rgba(255,140,60,.7)}
#chips{position:absolute;top:286px;left:84px;right:84px;z-index:5;color:#f3ece6}
.imp-list{list-style:none;margin:44px 0 0}
.imp-list li{font-size:84px;font-weight:900;line-height:1.28;color:rgba(243,236,230,.96);padding-left:40px;position:relative}
.imp-list li .strike{position:relative;display:inline-block}
.imp-list li .xln{position:absolute;left:-8px;right:-8px;top:52%;height:8px;background:linear-gradient(90deg,#ff6a2b,#e23a2e);border-radius:4px;box-shadow:0 0 18px rgba(226,58,46,.75);transform:scaleX(0);transform-origin:left}
.imp-list li::before{content:"";position:absolute;left:0;top:.30em;width:8px;height:.72em;background:linear-gradient(180deg,#ffb454,#ff6a2b);border-radius:3px;box-shadow:0 0 14px rgba(255,140,60,.6)}
.imp-note{margin-top:34px;font-size:35px;font-weight:600;color:#9a8c82;letter-spacing:.08em}
.imp-note b{color:#ffb47a;font-weight:700}

/* ---- intro: 标题 hook ---- */
#title{position:absolute;left:84px;right:84px;bottom:430px;z-index:5;color:#f3ece6}
#title .badge{display:inline-flex;align-items:center;gap:13px;padding:11px 26px;border:2px solid rgba(255,140,60,.6);border-radius:999px;font-size:28px;font-weight:800;color:#ffb454;letter-spacing:.2em}
#title .badge::before{content:"";width:13px;height:13px;border-radius:50%;background:#ff6a2b;box-shadow:0 0 16px #ff6a2b}
#title .who{margin-top:28px;font-size:58px;font-weight:700;color:#cdbcae;letter-spacing:.02em}
#title .hero{margin-top:0;font-size:170px;font-weight:900;line-height:.92;letter-spacing:-2px;font-family:"Noto Serif SC",serif;
  background:linear-gradient(100deg,#ffe0b0 4%,#ff8a3c 46%,#e23a2e 98%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 10px 40px rgba(255,90,40,.34))}
#title .en{margin-top:14px;font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:46px;color:#c79a6e;letter-spacing:.04em}
#title .sub{margin-top:22px;font-size:42px;font-weight:700;color:#e7ddd4}
#title .sub b{color:#ff9d3c}

/* ---- intro: TOP5 bridge ---- */
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#f3ece6;text-align:center}
#bridge .big{font-size:240px;font-weight:900;line-height:.9;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#ffd9a8,#ff6a2b);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 50px rgba(255,110,50,.5))}
#bridge .big small{font-size:60px;font-weight:800;color:#ffc59a;letter-spacing:.24em;display:block;margin-bottom:8px;font-family:"Noto Sans SC",sans-serif;-webkit-text-fill-color:#ffc59a}
#bridge .line{margin-top:28px;font-size:52px;font-weight:900;color:#f3ece6}
#bridge .line b{color:#e23a2e}

/* ---- 排名大卡 ---- */
.labelFull{position:absolute;left:84px;right:84px;bottom:296px;z-index:5;color:#f3ece6}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:34px;font-weight:800;color:#ff9d3c;letter-spacing:.26em;padding-bottom:32px;font-family:"Noto Sans SC",sans-serif}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#1a0b06;background:linear-gradient(180deg,#ff8f5e,#e23a2e);border-radius:9px;padding:9px 22px;margin-bottom:36px;letter-spacing:.1em;box-shadow:0 0 34px rgba(226,58,46,.6)}
.labelFull .no{font-size:200px;font-weight:800;line-height:.78;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#ffe0b0,#ff6a2b);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 40px rgba(255,110,50,.4))}
.labelFull.climax .no{background:linear-gradient(180deg,#ff9a6e,#e23a2e);-webkit-background-clip:text;background-clip:text;color:transparent}
.labelFull .meta{margin-top:14px;font-size:30px;font-weight:700;color:#b9a89a;letter-spacing:.18em;font-family:"JetBrains Mono",monospace}
.labelFull .song{font-size:88px;font-weight:900;margin-top:4px;color:#fff;font-family:"Noto Serif SC",serif}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:31px;font-weight:700;color:#ffc59a;border:1.5px solid rgba(255,140,60,.5);border-radius:999px;padding:9px 22px;background:rgba(255,120,40,.06)}
.labelFull.climax .tags span{color:#ff9a8a;border-color:rgba(226,58,46,.6)}
.labelFull .tag{font-size:44px;font-weight:700;color:#e7ddd4;margin-top:26px;line-height:1.3}
.labelFull .tag b{color:#ff9d3c;font-weight:800}
.labelFull.climax .tag b{color:#e23a2e}

/* ---- 展示期角标 ---- */
.labelMin{position:absolute;top:118px;left:74px;z-index:5;color:#f3ece6;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:62px;font-weight:800;color:#ff9d3c;font-family:"JetBrains Mono",monospace}
.labelMin.climax .no{color:#e23a2e}
.labelMin .song{font-size:50px;font-weight:800;font-family:"Noto Serif SC",serif}
"""

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="tint" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="grain" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9"></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci"><span class="strike">太稳<i class="xln"></i></span></li><li class="ci"><span class="strike">太松弛<i class="xln"></i></span></li><li class="ci"><span class="strike">好像没在用力<i class="xln"></i></span></li></ul>
<div class="imp-note">《男孩》《出现又离开》· <b>听起来像呼吸一样轻</b></div></div>
<div id="title" class="clip" data-start="{TITLE_IN}" data-duration="{round(TITLE_OUT-TITLE_IN,2)}" data-track-index="4">
<div class="badge">唱功盘点 · 强混现场</div>
<div class="who">你以为很松弛的梁博</div>
<div class="hero">最难的5首</div>
<div class="en">Liang Bo — The Hardest Five</div>
<div class="sub">难到 <b>听起来毫不费力</b></div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="5">
<div class="big"><small>公认最难唱</small>TOP 5</div>
<div class="line">强混 · 撕裂 · <b>长线高压</b></div></div>
{chr(10).join(labels)}
<audio id="master" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

js = f'''
tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{CHIP_IN+0.1});
tl.from("#chips .ci",{{x:-46,opacity:0,duration:.55,ease:"power3.out",stagger:.42}},{CHIP_IN+0.3});
tl.to("#chips .ci:nth-child(1) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+2.2});
tl.to("#chips .ci:nth-child(2) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+2.7});
tl.to("#chips .ci:nth-child(3) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+3.2});
tl.from("#chips .imp-note",{{opacity:0,y:14,duration:.5}},{CHIP_IN+3.8});
tl.to("#chips",{{opacity:0,duration:.4,ease:"power1.in"}},{round(CHIP_OUT-0.45,2)});
tl.set("#chips",{{opacity:0}},{CHIP_OUT});
tl.from("#title .badge",{{y:20,opacity:0,scale:.9,duration:.5,ease:"back.out(1.6)"}},{TITLE_IN+0.1});
tl.from("#title .who",{{y:24,opacity:0,duration:.5,ease:"power2.out"}},{TITLE_IN+0.35});
tl.from("#title .hero",{{y:72,opacity:0,scale:1.08,duration:.78,ease:"power4.out"}},{TITLE_IN+0.7});
tl.from("#title .en",{{opacity:0,y:16,duration:.5,ease:"power2.out"}},{TITLE_IN+1.3});
tl.from("#title .sub",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{TITLE_IN+1.6});
tl.to("#title",{{opacity:0,duration:.4,ease:"power2.in"}},{round(TITLE_OUT-0.45,2)});
tl.set("#title",{{opacity:0}},{TITLE_OUT});
tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{BRG_IN+0.1});
tl.from("#bridge .big",{{scale:.7,opacity:0,duration:.6,ease:"back.out(1.4)"}},{BRG_IN+0.2});
tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{BRG_IN+0.8});
tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{round(BRG_OUT-0.45,2)});
tl.set("#bridge",{{opacity:0}},{BRG_OUT});
{chr(10).join(tweens)}
'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@700;800&family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>'''

Path("index.html").write_text(html, encoding="utf-8")
Path("meta.json").write_text('{"id":"main","name":"liangbo-hardest-sample"}', encoding="utf-8")
print("TOTAL:", TOTAL, "s  | INTRO_END:", INTRO_END)
for b in blocks: print(f"  {b['no']} {b['name']:10s} start={b['start']:.2f} full={b['full']:.2f} end={b['end']:.2f}")
