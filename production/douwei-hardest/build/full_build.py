#!/usr/bin/env python3
"""完整片：窦唯最难的5首歌 / 倒数 5→1。冷蓝钢灰+血红，竖屏 1080x1920。
master.wav（逐段 床→swell→展示 + 旁白 + 逐首响度归一）+ index.html。
之后 lint → render → mux master.wav。"""
import subprocess, wave, contextlib
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
LEAD = 0.3; DIG = 1.4; SHOW = 17.0; GAP_A = 1.35
BED_I = 0.08; BED_N = 0.14
MGAIN = {}   # 逐首额外增益（loudnorm 后仍偏低时补偿）

d_intro = dur(f"{A}/intro.wav")
d = {k: dur(f"{A}/{k}.wav") for k in
     ["p5_beishang","p4_kaojin","p3_wudi","p2_dontbreak","p1_bielai","outro"]}

# 倒数 5→1
songs = [
    ("p5_beishang","vert_beishang","05","《悲伤的梦》",
     ["后朋克阴影","冷声压迫","克制爆发"], "不在飙多高，难在<b>把压抑收进一条窄缝</b>"),
    ("p4_kaojin","vert_kj","04","《靠近我》",
     ["清亮穿透","海豚音节点","少年锋利"], "前面要松要亮，关键一下<b>突然拉出极高尖峰</b>"),
    ("p3_wudi","vert_wd","03","《无地自容》",
     ["高位耐力","密集咬字","一口气到底"], "整首压在中高音，<b>像声带在跑马拉松</b>"),
    ("p2_dontbreak","vert_db","02","《Don't Break My Heart》",
     ["甜嗓硬核","强弱转换","少年感杀手"], "明亮干净里完成高音咬字，<b>太硬会油，太轻会虚</b>"),
    ("p1_bielai","vert_bl","01","《别来纠缠我》",
     ["极限爆裂","A5尖峰","金属嘶吼"], "近90个A4、最高冲到A5，<b>谁唱谁翻车</b>"),
]

# ---------- 时间轴 ----------
intro_voice_end = LEAD + d_intro
p5_start = intro_voice_end + GAP_A
p5_end = p5_start + d["p5_beishang"]
A_swell = p5_end + 0.2; A_full = A_swell + DIG; A_end = round(A_full + SHOW, 3)

blocks = []
blocks.append(dict(key="p5_beishang", clip="vert_beishang", start=0.0, end=A_end,
                   narr_start=p5_start, narr_end=p5_end, full=A_full,
                   no="05", name="《悲伤的梦》",
                   tags=songs[0][4], tagline=songs[0][5], is_A=True))
t = A_end
for key, clip, no, name, tags, tagline in songs[1:]:
    ns = t + LEAD; ne = ns + d[key]; full = ne + 0.2 + DIG; end = round(full + SHOW, 3)
    blocks.append(dict(key=key, clip=clip, start=t, end=end, narr_start=ns, narr_end=ne,
                       full=full, no=no, name=name, tags=tags, tagline=tagline, is_A=False))
    t = end
F_start = t; F_voice = F_start + LEAD; F_voice_end = F_voice + d["outro"]
F_end = round(F_voice_end + 2.6, 3); TOTAL = F_end

# ---------- 音频分段 ----------
def envB(ns_loc, ne_loc, full_loc):
    sw = ne_loc + 0.2
    return (f"(lt(t,0.8))*({BED_N}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED_N}"
            f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_loc}))*1.0")

segs = []
# seg A: intro + p5
veA = (f"(lt(t,0.8))*({BED_I}*t/0.8)"
       f"+(between(t,0.8,{p5_start}))*{BED_I}"
       f"+(between(t,{p5_start},{A_swell}))*{BED_N}"
       f"+(between(t,{A_swell},{A_full}))*({BED_N}+{1.0-BED_N}*(t-{A_swell})/{DIG})"
       f"+(gte(t,{A_full}))*1.0")
run(["ffmpeg","-v","error","-i",f"{C}/vert_beishang.mp4",
     "-i",f"{A}/intro.wav","-i",f"{A}/p5_beishang.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(p5_start*1000)}|{int(p5_start*1000)}[v2];"
     f"[v1][v2]amix=inputs=2:normalize=0,volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{A_end},volume='{veA}':eval=frame[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{A_end},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_A.wav","-y"])
segs.append("seg_A.wav")

# seg B-E
for i, b in enumerate(blocks[1:], start=1):
    seg_dur = round(b["end"] - b["start"], 3)
    ns_loc = LEAD; ne_loc = LEAD + d[b["key"]]; full_loc = round(b["full"] - b["start"], 3)
    ve = envB(ns_loc, ne_loc, full_loc); mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['no']}.wav"
    run(["ffmpeg","-v","error","-i",f"{C}/{b['clip']}.mp4","-i",f"{A}/{b['key']}.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

# seg F: outro（beishang 低床 + 旁白 + 淡出）
segF_dur = round(F_end - F_start, 3)
run(["ffmpeg","-v","error","-i",f"{C}/vert_beishang.mp4","-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{segF_dur},volume=0.2,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-1.6}:d=1.6[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_F.wav","-y"])
segs.append("seg_F.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- HTML ----------
# 钩子 beats
CHIP_IN, CHIP_OUT = 0.3, 4.0
TITLE_IN, TITLE_OUT = 4.3, 11.0
BRG_IN, BRG_OUT = 11.3, 18.5

# footage（交替轨道 0/6）
fclips = [(b["clip"], b["start"], round(b["end"]-b["start"],3)) for b in blocks]
fclips.append(("vert_beishang", F_start, round(F_end-F_start,3)))
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{round(s,3)}" data-duration="{dv}" '
    f'data-track-index="{0 if i%2==0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i,(src,s,dv) in enumerate(fclips))

# 标签
labels, tweens = [], []
for b in blocks:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = 18.9 if b["is_A"] else round(b["start"]+0.2,3)
    lf_dur = round(b["full"] - lf_start, 3)
    lm_start = b["full"]; lm_dur = round(b["end"] - b["full"], 3)
    climax = ' climax' if no=="01" else ''
    crown = '<div class="crown">公认天花板</div>' if no=="01" else '<div class="lab">最难 TOP 5</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{lf_start}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{crown}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>')
    labels.append(
        f'<div id="{mid}" class="clip labelMin" data-start="{lm_start}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>')
    tweens.append(f'tl.from("#{fid} .no",{{y:54,opacity:0,duration:.7,ease:"power3.out"}},{round(lf_start+0.1,3)});')
    tweens.append(f'tl.from("#{fid} .rank>div:last-child",{{x:-20,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+0.35,3)});')
    tweens.append(f'tl.from("#{fid} .song",{{y:40,opacity:0,duration:.6,ease:"power3.out"}},{round(lf_start+0.4,3)});')
    tweens.append(f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{round(lf_start+0.7,3)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+1.05,3)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["full"]-0.4,3)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{b["full"]});')
    tweens.append(f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{round(lm_start+0.1,3)});')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0b0e;font-family:"PingFang SC","Hiragino Sans GB",system-ui,sans-serif}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(4,6,10,.62) 0%,rgba(4,6,10,.12) 26%,rgba(4,6,10,.18) 56%,rgba(4,6,10,.82) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 42%,rgba(0,0,0,0) 42%,rgba(0,0,0,.55) 100%)}
.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:800;color:#6fd3e8;letter-spacing:.32em}
.k::before{content:"";width:48px;height:4px;background:#6fd3e8;border-radius:2px;box-shadow:0 0 14px rgba(111,211,232,.7)}
#chips{position:absolute;top:300px;left:84px;right:84px;z-index:5;color:#fff}
.imp-list{list-style:none;margin:46px 0 0}
.imp-list li{font-size:78px;font-weight:900;line-height:1.34;color:rgba(236,244,248,.92);padding-left:36px;position:relative}
.imp-list li::before{content:"";position:absolute;left:0;top:.32em;width:7px;height:.76em;background:#6fd3e8;border-radius:3px}
.imp-note{margin-top:34px;font-size:34px;font-weight:600;color:#8893a0;letter-spacing:.14em}
#title{position:absolute;left:84px;right:84px;bottom:420px;z-index:5;color:#fff}
#title .badge{display:inline-flex;align-items:center;gap:12px;padding:11px 24px;border:2px solid rgba(255,46,46,.7);border-radius:999px;font-size:27px;font-weight:800;color:#ff5a5a;letter-spacing:.2em}
#title .badge::before{content:"";width:13px;height:13px;border-radius:50%;background:#ff2e2e;box-shadow:0 0 16px #ff2e2e}
#title .who{margin-top:30px;font-size:60px;font-weight:800;color:#cfe8ef;letter-spacing:.06em}
#title .hero{margin-top:2px;font-size:158px;font-weight:900;line-height:.96;letter-spacing:-3px;background:linear-gradient(102deg,#6fd3e8 8%,#cfeef6 46%,#ff5a5a 98%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 10px 40px rgba(111,211,232,.32))}
#title .sub{margin-top:26px;font-size:40px;font-weight:700;color:#e2eaee}
#title .sub b{color:#ff5a5a}
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#fff;text-align:center}
#bridge .big{font-size:230px;font-weight:900;line-height:.9;color:#6fd3e8;filter:drop-shadow(0 0 50px rgba(111,211,232,.45))}
#bridge .big small{font-size:64px;font-weight:800;color:#cfe8ef;letter-spacing:.2em;display:block;margin-bottom:6px}
#bridge .line{margin-top:30px;font-size:52px;font-weight:900;color:#fff}
#bridge .line b{color:#ff5a5a}
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#fff}
.labelFull .rank{display:flex;align-items:flex-end;gap:20px}
.labelFull .rank .lab{font-size:34px;font-weight:800;color:#6fd3e8;letter-spacing:.28em;padding-bottom:30px}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#0a0b0e;background:#ff2e2e;border-radius:8px;padding:8px 18px;margin-bottom:34px;letter-spacing:.12em;box-shadow:0 0 30px rgba(255,46,46,.6)}
.labelFull .no{font-size:188px;font-weight:900;line-height:.82;color:#fff;text-shadow:0 0 40px rgba(111,211,232,.4)}
.labelFull.climax .no{background:linear-gradient(180deg,#ff7a7a,#ff2e2e);-webkit-background-clip:text;background-clip:text;color:transparent;text-shadow:0 0 50px rgba(255,46,46,.5)}
.labelFull .song{font-size:84px;font-weight:900;margin-top:8px;color:#fff}
.labelFull.climax .song{font-size:78px}
.labelFull .tags{margin-top:20px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:700;color:#cfe8ef;border:1.5px solid rgba(111,211,232,.5);border-radius:999px;padding:8px 20px}
.labelFull.climax .tags span{color:#ffd0d0;border-color:rgba(255,90,90,.6)}
.labelFull .tag{font-size:42px;font-weight:700;color:#d7e2e8;margin-top:24px;line-height:1.32}
.labelFull .tag b{color:#ff7a7a;font-weight:800}
.labelMin{position:absolute;top:120px;left:74px;z-index:5;color:#fff;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:60px;font-weight:900;color:#6fd3e8}
.labelMin .song{font-size:50px;font-weight:800}
#outro{position:absolute;left:84px;right:84px;bottom:430px;z-index:5;color:#fff}
#outro .o1{font-size:54px;font-weight:700;color:#cfe8ef;line-height:1.4}
#outro .o2{margin-top:18px;font-size:96px;font-weight:900;line-height:1.04;background:linear-gradient(102deg,#6fd3e8,#cfeef6 50%,#ff5a5a);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:30px;font-size:42px;font-weight:700;color:#e2eaee}
#outro .bar{width:130px;height:8px;background:#ff2e2e;margin-top:26px;border-radius:4px}
"""

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci">神隐</li><li class="ci">飘渺</li><li class="ci">不食人间烟火</li></ul>
<div class="imp-note">近年的窦唯 · 音乐隐士</div></div>
<div id="title" class="clip" data-start="{TITLE_IN}" data-duration="{round(TITLE_OUT-TITLE_IN,2)}" data-track-index="4">
<div class="badge">硬核盘点 · 高音地狱</div>
<div class="who">但早年的窦唯</div>
<div class="hero">最难的5首</div>
<div class="sub">嗓子炸到 <b>谁唱谁翻车</b></div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="5">
<div class="big"><small>公认最难唱</small>TOP 5</div>
<div class="line">高音 · 嘶吼 · <b>海豚音</b></div></div>
{chr(10).join(labels)}
<div id="outro" class="clip" data-start="{round(F_voice+0.2,3)}" data-duration="{round(F_end-F_voice-0.2,3)}" data-track-index="4">
<div class="o1">他从来不是只有飘渺和神隐</div>
<div class="o2">能炸、能冷、<br>能撕裂，也能收</div>
<div class="q">你心里的天花板，是哪一首？</div>
<div class="bar"></div></div>
<audio id="master" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

js = f'''
tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{CHIP_IN+0.1});
tl.from("#chips .ci",{{x:-44,opacity:0,duration:.55,ease:"power3.out",stagger:.16}},{CHIP_IN+0.3});
tl.from("#chips .imp-note",{{opacity:0,duration:.5}},{CHIP_IN+1.6});
tl.to("#chips",{{opacity:0,duration:.35,ease:"power1.in"}},{round(CHIP_OUT-0.4,2)});
tl.from("#title .badge",{{y:20,opacity:0,scale:.9,duration:.5,ease:"back.out(1.6)"}},{TITLE_IN+0.1});
tl.from("#title .who",{{y:24,opacity:0,duration:.5,ease:"power2.out"}},{TITLE_IN+0.35});
tl.from("#title .hero",{{y:70,opacity:0,scale:1.08,duration:.75,ease:"power4.out"}},{TITLE_IN+0.7});
tl.from("#title .sub",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{TITLE_IN+1.25});
tl.to("#title",{{opacity:0,duration:.4,ease:"power2.in"}},{round(TITLE_OUT-0.45,2)});
tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{BRG_IN+0.1});
tl.from("#bridge .big",{{scale:.7,opacity:0,duration:.6,ease:"back.out(1.5)"}},{BRG_IN+0.2});
tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{BRG_IN+0.7});
tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{round(BRG_OUT-0.45,2)});
{chr(10).join(tweens)}
tl.from("#outro .o1",{{y:24,opacity:0,duration:.6,ease:"power2.out"}},{round(F_voice+0.3,3)});
tl.from("#outro .o2",{{y:50,opacity:0,scale:1.05,duration:.8,ease:"power4.out"}},{round(F_voice+0.9,3)});
tl.from("#outro .q",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{round(F_voice+1.7,3)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{round(F_voice+2.1,3)});
'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
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
Path("meta.json").write_text('{"id":"main","name":"douwei-hardest"}', encoding="utf-8")
print("TOTAL:", TOTAL, "s")
for b in blocks: print(f"  {b['no']} {b['name']:22s} start={b['start']:.2f} full={b['full']:.2f} end={b['end']:.2f}")
print(f"  outro start={F_start:.2f} end={F_end:.2f}")
