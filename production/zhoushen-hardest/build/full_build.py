#!/usr/bin/env python3
"""完整片：周深最难的5首歌 / 倒数 5→1。极光天籁配色(冰青→紫→金)，竖屏 1080x1920。
结构：开场钩子+intro旁白(独立暗调底) → 5首(每首一条连续素材，副歌特写落在展示段，自带音轨保口型) → 片尾。
master.wav 逐段(床→swell→展示 + 旁白 ducking + 逐首 loudnorm 统一响度)。
之后 lint → render → mux master.wav。"""
import subprocess, wave, contextlib
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
LEAD = 0.3; GAP_A = 1.35; DIG = 1.4; SHOW = 6.0
BED_I = 0.07; BED_N = 0.13
MGAIN = {}   # 逐首额外增益（loudnorm 后仍偏低时补偿）

d_intro = dur(f"{A}/intro.wav")
d_out = dur(f"{A}/outro.wav")
d = {k: dur(f"{A}/{k}.wav") for k in ["p5_muyang","p4_dala","p3_renshi","p2_guang","p1_shao"]}

# 倒数 5→1（揭晓顺序）
songs = [
    ("p5_muyang","vert_muyang","05","《孤独的牧羊人》",
     ["约德尔唱法","八度大跳","真假声闪切"], "难的不是大声，<b>是极速声区跳跃里不滑倒</b>"),
    ("p4_dala","vert_dala","04","《达拉崩吧》",
     ["一人五角","铁肺快嘴","音色切换"], "不是给真人写的，<b>结尾一口气念到缺氧</b>"),
    ("p3_renshi","vert_renshi","03","《人是_》",
     ["E5/F5连发","强混咬字","压迫感"], "不是飘着唱，<b>顶着推进还不能糊字</b>"),
    ("p2_guang","vert_guang","02","《光亮》",
     ["C6长音","戏腔共鸣","神仙耐力"], "C6不是点一下，<b>要稳成一道光</b>"),
    ("p1_shao","vert_shao","01","《少管我》",
     ["D6尖峰","高位头声","非人类轻盈"], "比《光亮》还高一截，<b>还得唱得又轻又稳</b>"),
]

# ---------- 时间轴 ----------
INTRO_END = 19.0
blocks = []
t = INTRO_END
for key, clip, no, name, tags, tagline in songs:
    L = round(LEAD + d[key] + 0.2 + DIG + SHOW, 3)
    ns = round(t + LEAD, 3); ne = round(ns + d[key], 3)
    full = round(ne + 0.2 + DIG, 3); end = round(t + L, 3)
    blocks.append(dict(key=key, clip=clip, start=t, L=L, end=end, ns=ns, ne=ne, full=full,
                       no=no, name=name, tags=tags, tagline=tagline))
    t = end
F_start = t; F_voice = round(F_start + LEAD, 3); F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 2.6, 3); TOTAL = F_end

# ---------- 音频分段 ----------
def envB(ns_loc, ne_loc, full_loc):
    sw = round(ne_loc + 0.2, 3)
    return (f"(lt(t,0.8))*({BED_N}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED_N}"
            f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_loc}))*1.0")

segs = []
# seg_intro: 暗调底(vert_intro 自带 少管我 intro 器乐)做低床 + intro 旁白；先声后乐(~4s 进床)
veI = (f"(lt(t,3.5))*0"
       f"+(between(t,3.5,4.5))*({BED_I}*(t-3.5)/1.0)"
       f"+(gte(t,4.5))*{BED_I}")
run(["ffmpeg","-v","error","-i",f"{C}/vert_intro.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{INTRO_END},volume='{veI}':eval=frame[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_intro.wav","-y"])
segs.append("seg_intro.wav")

# seg5..seg1
for b in blocks:
    seg_dur = b["L"]
    ns_loc = LEAD; ne_loc = round(LEAD + d[b["key"]], 3); full_loc = round(b["full"] - b["start"], 3)
    ve = envB(ns_loc, ne_loc, full_loc); mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['no']}.wav"
    # 部分源 webm 音轨被 download-sections 截断/或换了干净源，改用提前抽出的 wav（与视频同区间，口型仍对齐）
    _wav = {"p1_shao": "shao_music.wav", "p2_guang": "guang_music.wav"}
    msrc = f"{C}/{_wav[b['key']]}" if b["key"] in _wav else f"{C}/{b['clip']}.mp4"
    run(["ffmpeg","-v","error","-i",msrc,"-i",f"{A}/{b['key']}.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

# seg_outro: 光亮(时光音乐会)抽出的器乐低床 + 旁白 + 淡出（画面侧用 vert_intro 暗调底做开合呼应）
segF_dur = round(F_end - F_start, 3)
run(["ffmpeg","-v","error","-i",f"{C}/outro_music.wav","-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{segF_dur},volume=0.2,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-1.6}:d=1.6[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_outro.wav","-y"])
segs.append("seg_outro.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- HTML ----------
CHIP_IN, CHIP_OUT = 0.3, 4.0
TITLE_IN, TITLE_OUT = 4.3, 11.0
BRG_IN, BRG_OUT = 11.3, 18.5

# footage（交替轨道 0/6）
fc = [("vert_intro", 0.0, INTRO_END)]
for b in blocks:
    fc.append((b["clip"], b["start"], b["L"]))
fc.append(("vert_intro", F_start, round(F_end-F_start,3)))  # 片尾复用暗调 intro 底（开合呼应，且干净无烧字）
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{round(s,3)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i%2==0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i,(src,s,dv) in enumerate(fc))

# 标签
labels, tweens = [], []
for b in blocks:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = round(b["start"]+0.2,3); lf_dur = round(b["full"]-lf_start,3)
    lm_start = b["full"]; lm_dur = round(b["end"]-b["full"],3)
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
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0c14;font-family:"PingFang SC","Hiragino Sans GB",system-ui,sans-serif}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,8,16,.64) 0%,rgba(6,8,16,.12) 26%,rgba(6,8,16,.20) 56%,rgba(6,8,16,.84) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 80% at 50% 40%,rgba(0,0,0,0) 42%,rgba(0,0,0,.55) 100%)}
.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:800;color:#6fe8ec;letter-spacing:.32em}
.k::before{content:"";width:48px;height:4px;background:#6fe8ec;border-radius:2px;box-shadow:0 0 16px rgba(111,232,236,.75)}
#chips{position:absolute;top:300px;left:84px;right:84px;z-index:5;color:#fff}
.imp-list{list-style:none;margin:46px 0 0}
.imp-list li{font-size:80px;font-weight:900;line-height:1.32;color:rgba(236,244,248,.94);padding-left:38px;position:relative}
.imp-list li::before{content:"";position:absolute;left:0;top:.32em;width:7px;height:.74em;background:#6fe8ec;border-radius:3px;box-shadow:0 0 14px rgba(111,232,236,.6)}
.imp-note{margin-top:34px;font-size:34px;font-weight:600;color:#8893a0;letter-spacing:.14em}
#title{position:absolute;left:84px;right:84px;bottom:430px;z-index:5;color:#fff}
#title .badge{display:inline-flex;align-items:center;gap:12px;padding:11px 24px;border:2px solid rgba(155,111,255,.7);border-radius:999px;font-size:27px;font-weight:800;color:#b79bff;letter-spacing:.2em}
#title .badge::before{content:"";width:13px;height:13px;border-radius:50%;background:#9b6fff;box-shadow:0 0 16px #9b6fff}
#title .who{margin-top:30px;font-size:58px;font-weight:800;color:#bcc6e6;letter-spacing:.04em}
#title .hero{margin-top:2px;font-size:172px;font-weight:900;line-height:.94;letter-spacing:-3px;background:linear-gradient(102deg,#6fe8ec 6%,#9b6fff 52%,#ffd36f 98%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 10px 42px rgba(111,232,236,.34))}
#title .sub{margin-top:26px;font-size:40px;font-weight:700;color:#e2eaf0}
#title .sub b{color:#ffd36f}
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#fff;text-align:center}
#bridge .big{font-size:230px;font-weight:900;line-height:.9;color:#6fe8ec;filter:drop-shadow(0 0 52px rgba(111,232,236,.5))}
#bridge .big small{font-size:62px;font-weight:800;color:#cfeef0;letter-spacing:.2em;display:block;margin-bottom:6px}
#bridge .line{margin-top:30px;font-size:52px;font-weight:900;color:#fff}
#bridge .line b{color:#ffd36f}
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#fff}
.labelFull .rank{display:flex;align-items:flex-end;gap:22px}
.labelFull .rank .lab{font-size:34px;font-weight:800;color:#6fe8ec;letter-spacing:.26em;padding-bottom:30px}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#1a1206;background:linear-gradient(180deg,#ffe9a8,#ffc44d);border-radius:9px;padding:9px 20px;margin-bottom:34px;letter-spacing:.1em;box-shadow:0 0 32px rgba(255,200,77,.6)}
.labelFull .no{font-size:196px;font-weight:900;line-height:.82;color:#fff;text-shadow:0 0 42px rgba(111,232,236,.42)}
.labelFull.climax .no{background:linear-gradient(180deg,#ffe9a8,#ffc44d);-webkit-background-clip:text;background-clip:text;color:transparent;text-shadow:0 0 54px rgba(255,200,77,.5)}
.labelFull .song{font-size:82px;font-weight:900;margin-top:8px;color:#fff}
.labelFull.climax .song{font-size:78px}
.labelFull .tags{margin-top:22px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:700;color:#cfeef0;border:1.5px solid rgba(111,232,236,.5);border-radius:999px;padding:8px 20px}
.labelFull.climax .tags span{color:#ffe9b0;border-color:rgba(255,211,111,.6)}
.labelFull .tag{font-size:42px;font-weight:700;color:#d7e2ea;margin-top:24px;line-height:1.32}
.labelFull .tag b{color:#b79bff;font-weight:800}
.labelFull.climax .tag b{color:#ffd36f}
.labelMin{position:absolute;top:120px;left:74px;z-index:5;color:#fff;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:60px;font-weight:900;color:#6fe8ec}
.labelMin.climax .no{color:#ffd36f}
.labelMin .song{font-size:50px;font-weight:800}
#outro{position:absolute;left:84px;right:84px;bottom:430px;z-index:5;color:#fff}
#outro .o1{font-size:54px;font-weight:700;color:#cfe8ef;line-height:1.4}
#outro .o2{margin-top:18px;font-size:92px;font-weight:900;line-height:1.05;background:linear-gradient(102deg,#6fe8ec,#9b6fff 52%,#ffd36f);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:30px;font-size:42px;font-weight:700;color:#e2eaee}
#outro .bar{width:130px;height:8px;background:linear-gradient(90deg,#6fe8ec,#ffd36f);margin-top:26px;border-radius:4px}
"""

# labelMin climax 类
labels = [l.replace('class="clip labelMin" data-start="'+str(blocks[-1]["full"]),
                    'class="clip labelMin climax" data-start="'+str(blocks[-1]["full"])) for l in labels]

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci">空灵</li><li class="ci">天籁</li><li class="ci">治愈系高音</li></ul>
<div class="imp-note">《大鱼》·《光亮》· 干净到不真实</div></div>
<div id="title" class="clip" data-start="{TITLE_IN}" data-duration="{round(TITLE_OUT-TITLE_IN,2)}" data-track-index="4">
<div class="badge">高音盘点 · 封神现场</div>
<div class="who">你以为很轻松的周深</div>
<div class="hero">最难的5首</div>
<div class="sub">难到 <b>普通人找不到模仿路径</b></div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="5">
<div class="big"><small>公认最难唱</small>TOP 5</div>
<div class="line">高音 · 头声 · <b>D6</b></div></div>
{chr(10).join(labels)}
<div id="outro" class="clip" data-start="{round(F_voice+0.2,3)}" data-duration="{round(F_end-F_voice-0.2,3)}" data-track-index="4">
<div class="o1">周深从来不是只会唱温柔和治愈</div>
<div class="o2">他把高音，<br>唱成了非人类的技术</div>
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
Path("meta.json").write_text('{"id":"main","name":"zhoushen-hardest"}', encoding="utf-8")
print("TOTAL:", TOTAL, "s")
for b in blocks: print(f"  {b['no']} {b['name']:14s} start={b['start']:.2f} full={b['full']:.2f} end={b['end']:.2f}")
print(f"  outro start={F_start:.2f} end={F_end:.2f}")
