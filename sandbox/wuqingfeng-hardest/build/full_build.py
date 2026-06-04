#!/usr/bin/env python3
"""完整片：吴青峰最难的5首歌 / 倒数 5→1（#1《频率》压轴）。
夜空/极光配色（深墨蓝 #070b12 → 冰青 #5fe3d4 → 蓝 #7fb0ff → 紫 #b78bff；压轴用紫→品红热点）。
竖屏 1080x1920，女声旁白(zf_xiaoyi)。
结构：封面(首帧可作缩略图) + intro钩子(清亮反差→TOP5桥) → 5首(每首 介绍旁白+消化位+加长副歌展示) → 片尾。
用户偏好：副歌/精彩人声展示段加长(SHOW_REG/SHOW_LAST)，不要刚听就切走；锁青峰特写收尾。
master.wav 逐段(床→swell→展示 + 旁白 ducking + 逐首 loudnorm)，整体抬 ~+3dB。之后 lint → render --sdr → mux。"""
import subprocess, wave, contextlib
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
LEAD = 0.3; DIG = 1.4; SHOW_REG = 14.0; SHOW_LAST = 18.0
BED_I = 0.06; BED_N = 0.20
MGAIN = {}            # 逐首额外增益（loudnorm 后仍偏低时补偿）
MASTER_GAIN = 1.4     # 整体抬 ~+3dB

d_intro = dur(f"{A}/intro.wav"); d_out = dur(f"{A}/outro.wav")
INTRO_END = round(LEAD + d_intro + 1.3, 3)

# 倒数 5→1（揭晓顺序）。show = 该首展示段时长
songs = [
    ("p5_wohaoxiang", "vert_wohaoxiang", "05", "《我好想你》", "2013 · 苏打绿",
     ["高位稳定", "情绪拉满", "声音不能粗"],
     "一到副歌就喊，<b>一秒就露馅</b>", SHOW_REG),
    ("p4_qifengle", "vert_qifengle", "04", "《起风了》", "2019 · 歌手",
     ["长线条气息", "高位咬字", "清澈不薄"],
     "越想唱得像青峰，<b>破绽越藏不住</b>", SHOW_REG),
    ("p3_dixin", "vert_dixin", "03", "《地心》", "2019 · 歌手",
     ["轻声压迫感", "真假声转换", "高位爆发"],
     "越安静，<b>越藏不住瑕疵</b>", SHOW_REG),
    ("p2_tongkuai", "vert_tongkuai", "02", "《痛快的哀艳》", "2016 · 金曲奖",
     ["音域跨两个八度", "交响张力", "持续输出"],
     "唱好是史诗，<b>唱塌成体测</b>", SHOW_REG),
    ("p1_pinlv", "vert_pinlv", "01", "《频率》", "Live · 苏打绿",
     ["全程换声区", "头声极限", "轻而不虚"],
     "不是唱不上去，<b>是连赛道都进不去</b>", SHOW_LAST),
]

# ---------- 时间轴 ----------
blocks = []
t = INTRO_END
for key, clip, no, name, meta, tags, tagline, show in songs:
    dk = dur(f"{A}/{key}.wav")
    L = round(LEAD + dk + 0.2 + DIG + show, 3)
    ns = round(t + LEAD, 3); ne = round(ns + dk, 3)
    full = round(ne + 0.2 + DIG, 3); end = round(t + L, 3)
    blocks.append(dict(key=key, clip=clip, start=t, L=L, end=end, ns=ns, ne=ne, full=full,
                       no=no, name=name, meta=meta, tags=tags, tagline=tagline, show=show))
    t = end
F_start = t; F_voice = round(F_start + LEAD, 3); F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 2.8, 3); TOTAL = round(F_end + 0.4, 3)

# ---------- 音频分段 ----------
def envB(ne_loc, full_loc):
    sw = round(ne_loc, 3)
    return (f"(lt(t,0.8))*({BED_N}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED_N}"
            f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_loc}))*1.0")

segs = []
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
    ve = envB(ne_loc, full_loc); mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['no']}.wav"
    run(["ffmpeg","-v","error","-i",f"{C}/{b['clip']}.mp4","-i",f"{A}/{b['key']}.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

segF_dur = round(F_end - F_start, 3)
run(["ffmpeg","-v","error","-i",f"{C}/vert_intro.mp4","-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{segF_dur},volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-2.2}:d=2.2[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_outro.wav","-y"])
segs.append("seg_outro.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt",
     "-af",f"volume={MASTER_GAIN},alimiter=limit=0.97","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- 时间点 ----------
COVER_END = 4.9
CHIP_IN, CHIP_OUT = 5.1, 12.6
BRG_IN, BRG_OUT = 12.9, round(INTRO_END-0.5,3)

# footage：单条连续 footage.mp4（intro底 + 5首 + 片尾复用 intro底，已按各段时长 ffmpeg 预拼）。
# 用单个 <video> 而非 7 个——本机 Chrome 渲染同时加载多 video 会在首帧 capture 崩溃/超时（已实测：1 video OK，7 video 卡死）。
vids = (f'<video id="bg" class="fv" data-start="0" data-duration="{TOTAL}" '
        f'data-track-index="0" src="{C}/footage.mp4" muted playsinline></video>')

# 标签
labels, tweens = [], []
for b in blocks:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = round(b["start"]+0.2,3); lf_dur = round(b["full"]-lf_start,3)
    lm_start = b["full"]; lm_dur = round(b["end"]-b["full"]+(0.4 if b is blocks[-1] else 0),3)
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
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["end"]-0.35,3)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{round(b["end"],3)});')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#070b12;
  font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,9,16,.74) 0%,rgba(7,11,18,.16) 28%,rgba(7,11,18,.24) 56%,rgba(5,7,13,.90) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(118% 78% at 50% 38%,rgba(0,0,0,0) 40%,rgba(2,4,10,.62) 100%)}
#tint{position:absolute;inset:0;z-index:1;background:radial-gradient(96% 64% at 50% 26%,rgba(95,227,212,.10) 0%,rgba(120,150,255,.05) 38%,rgba(0,0,0,0) 66%)}
#aur{position:absolute;inset:0;z-index:1;background:radial-gradient(60% 40% at 82% 88%,rgba(183,139,255,.13) 0%,rgba(0,0,0,0) 70%)}

/* ---- 封面（首帧缩略图，不做 fade-in） ---- */
#cover{position:absolute;left:84px;right:84px;bottom:352px;z-index:6;color:#eaf2ff}
#cover .cv-kick{display:inline-flex;align-items:center;gap:13px;padding:11px 26px;border:2px solid rgba(95,227,212,.55);border-radius:999px;font-size:27px;font-weight:800;color:#7ff0e2;letter-spacing:.18em}
#cover .cv-kick::before{content:"";width:13px;height:13px;border-radius:50%;background:#5fe3d4;box-shadow:0 0 16px #5fe3d4}
#cover .cv-name{margin-top:30px;font-size:70px;font-weight:900;color:#e7eefb;letter-spacing:.08em;font-family:"Noto Sans SC",sans-serif}
#cover .cv-title{margin-top:-6px;font-size:184px;font-weight:900;line-height:.92;letter-spacing:-3px;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#b8f4ea 2%,#74b6ff 46%,#b78bff 98%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 10px 46px rgba(110,160,255,.40))}
#cover .cv-en{margin-top:14px;font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:47px;color:#8fb6c9;letter-spacing:.04em}
#cover .cv-sub{margin-top:22px;font-size:39px;font-weight:700;color:#dbe6f5}
#cover .cv-sub b{color:#5fe3d4}

/* ---- intro: 大众印象 钩子 ---- */
.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:800;color:#7ff0e2;letter-spacing:.32em}
.k::before{content:"";width:50px;height:4px;background:linear-gradient(90deg,#5fe3d4,#7fb0ff);border-radius:2px;box-shadow:0 0 18px rgba(95,227,212,.7)}
#chips{position:absolute;top:300px;left:84px;right:84px;z-index:5;color:#eaf2ff}
.imp-list{list-style:none;margin:44px 0 0}
.imp-list li{font-size:84px;font-weight:900;line-height:1.28;color:rgba(234,242,255,.96);padding-left:40px;position:relative}
.imp-list li .strike{position:relative;display:inline-block}
.imp-list li .xln{position:absolute;left:-8px;right:-8px;top:52%;height:8px;background:linear-gradient(90deg,#5fe3d4,#7fb0ff);border-radius:4px;box-shadow:0 0 18px rgba(95,227,212,.7);transform:scaleX(0);transform-origin:left}
.imp-list li::before{content:"";position:absolute;left:0;top:.30em;width:8px;height:.72em;background:linear-gradient(180deg,#5fe3d4,#7fb0ff);border-radius:3px;box-shadow:0 0 14px rgba(95,227,212,.6)}
.imp-note{margin-top:34px;font-size:35px;font-weight:600;color:#8593a8;letter-spacing:.06em}
.imp-note b{color:#9fe9de;font-weight:700}

/* ---- intro: TOP5 bridge ---- */
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#eaf2ff;text-align:center}
#bridge .big{font-size:240px;font-weight:900;line-height:.9;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#cdeef0,#74b6ff);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 50px rgba(110,160,255,.5))}
#bridge .big small{font-size:60px;font-weight:800;color:#9fd6ec;letter-spacing:.22em;display:block;margin-bottom:8px;font-family:"Noto Sans SC",sans-serif;-webkit-text-fill-color:#9fd6ec}
#bridge .line{margin-top:28px;font-size:52px;font-weight:900;color:#eaf2ff}
#bridge .line b{color:#b78bff}

/* ---- 排名大卡 ---- */
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#eaf2ff}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:33px;font-weight:800;color:#7ff0e2;letter-spacing:.24em;padding-bottom:32px;font-family:"Noto Sans SC",sans-serif}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#160a1f;background:linear-gradient(180deg,#d6a8ff,#ff6ec7);border-radius:9px;padding:9px 22px;margin-bottom:36px;letter-spacing:.1em;box-shadow:0 0 34px rgba(255,110,199,.55)}
.labelFull .no{font-size:200px;font-weight:800;line-height:.78;font-family:"JetBrains Mono",monospace;
  background:linear-gradient(180deg,#cdeef0,#74b6ff);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 40px rgba(110,160,255,.4))}
.labelFull.climax .no{background:linear-gradient(180deg,#d6a8ff,#ff6ec7);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 44px rgba(255,110,199,.45))}
.labelFull .meta{margin-top:14px;font-size:30px;font-weight:700;color:#9aa9bf;letter-spacing:.16em;font-family:"JetBrains Mono",monospace}
.labelFull .song{font-size:88px;font-weight:900;margin-top:4px;color:#fff;font-family:"Noto Serif SC",serif}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:700;color:#9fe9de;border:1.5px solid rgba(95,227,212,.45);border-radius:999px;padding:9px 22px;background:rgba(95,227,212,.06)}
.labelFull.climax .tags span{color:#e3b8ff;border-color:rgba(183,139,255,.55);background:rgba(183,139,255,.07)}
.labelFull .tag{font-size:44px;font-weight:700;color:#dbe6f5;margin-top:26px;line-height:1.3}
.labelFull .tag b{color:#5fe3d4;font-weight:800}
.labelFull.climax .tag b{color:#ff6ec7}

/* ---- 展示期角标 ---- */
.labelMin{position:absolute;top:118px;left:74px;z-index:5;color:#eaf2ff;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:62px;font-weight:800;color:#7ff0e2;font-family:"JetBrains Mono",monospace}
.labelMin.climax .no{color:#ff6ec7}
.labelMin .song{font-size:50px;font-weight:800;font-family:"Noto Serif SC",serif}

/* ---- 片尾 ---- */
#outro{position:absolute;left:84px;right:84px;bottom:420px;z-index:5;color:#eaf2ff}
#outro .o1{font-size:50px;font-weight:700;color:#dbe6f5;line-height:1.4}
#outro .o2{margin-top:16px;font-size:84px;font-weight:900;line-height:1.08;font-family:"Noto Serif SC",serif;
  background:linear-gradient(104deg,#b8f4ea,#74b6ff 52%,#b78bff);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:28px;font-size:42px;font-weight:700;color:#e7eefb}
#outro .q b{color:#5fe3d4}
#outro .bar{width:140px;height:8px;background:linear-gradient(90deg,#5fe3d4,#b78bff);margin-top:26px;border-radius:4px}
"""

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="tint" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8"></div>
<div id="aur" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="10"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="5">
<div class="cv-kick">唱功盘点 · 换声区试炼</div>
<div class="cv-name">吴青峰</div>
<div class="cv-title">最难的5首</div>
<div class="cv-en">Wu Tsing-Fong — The Hardest Five</div>
<div class="cv-sub">听起来像羽毛 · <b>其实最难复刻</b></div></div>
<div id="chips" class="clip" data-start="{CHIP_IN}" data-duration="{round(CHIP_OUT-CHIP_IN,2)}" data-track-index="2">
<div class="k">大众印象</div>
<ul class="imp-list"><li class="ci"><span class="strike">清亮<i class="xln"></i></span></li><li class="ci"><span class="strike">空灵<i class="xln"></i></span></li><li class="ci"><span class="strike">像羽毛一样飘<i class="xln"></i></span></li></ul>
<div class="imp-note">听着 <b>像呼吸一样轻</b> · 其实全是控制力</div></div>
<div id="bridge" class="clip" data-start="{BRG_IN}" data-duration="{round(BRG_OUT-BRG_IN,2)}" data-track-index="5">
<div class="big"><small>公认最难唱</small>TOP 5</div>
<div class="line">换声区 · 头声 · <b>长线高压</b></div></div>
{chr(10).join(labels)}
<div id="outro" class="clip" data-start="{round(F_voice+0.2,3)}" data-duration="{round(F_end-F_voice-0.2+0.4,3)}" data-track-index="4">
<div class="o1">吴青峰的轻，从来不是真的轻松</div>
<div class="o2">那些像羽毛的高音，<br>是最难复刻的控制力</div>
<div class="q">你心里他最难的一首，<b>是哪一首？</b></div>
<div class="bar"></div></div>
<audio id="master" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

js = f'''
tl.set("#cover",{{opacity:1}},0);
tl.set(["#cover .cv-kick","#cover .cv-name","#cover .cv-title","#cover .cv-en","#cover .cv-sub"],{{opacity:1}},0);
tl.to("#cover .cv-title",{{scale:1.03,duration:3.2,transformOrigin:"left center",ease:"sine.inOut",yoyo:true,repeat:1}},0.6);
tl.to("#cover",{{y:-30,opacity:0,duration:.5,ease:"power2.in"}},{round(COVER_END-0.55,2)});
tl.set("#cover",{{opacity:0}},{COVER_END});
tl.from("#chips .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{CHIP_IN+0.1});
tl.from("#chips .ci",{{x:-46,opacity:0,duration:.55,ease:"power3.out",stagger:.42}},{CHIP_IN+0.3});
tl.to("#chips .ci:nth-child(1) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+2.2});
tl.to("#chips .ci:nth-child(2) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+2.7});
tl.to("#chips .ci:nth-child(3) .xln",{{scaleX:1,duration:.4,ease:"power2.in"}},{CHIP_IN+3.2});
tl.from("#chips .imp-note",{{opacity:0,y:14,duration:.5}},{CHIP_IN+3.9});
tl.to("#chips",{{opacity:0,duration:.4,ease:"power1.in"}},{round(CHIP_OUT-0.45,2)});
tl.set("#chips",{{opacity:0}},{CHIP_OUT});
tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{BRG_IN+0.1});
tl.from("#bridge .big",{{scale:.7,opacity:0,duration:.6,ease:"back.out(1.4)"}},{BRG_IN+0.2});
tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{BRG_IN+0.8});
tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{round(BRG_OUT-0.45,2)});
tl.set("#bridge",{{opacity:0}},{BRG_OUT});
{chr(10).join(tweens)}
tl.from("#outro .o1",{{y:24,opacity:0,duration:.6,ease:"power2.out"}},{round(F_voice+0.3,3)});
tl.from("#outro .o2",{{y:50,opacity:0,scale:1.05,duration:.8,ease:"power4.out"}},{round(F_voice+0.95,3)});
tl.from("#outro .q",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{round(F_voice+1.85,3)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{round(F_voice+2.3,3)});
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
Path("meta.json").write_text('{"id":"main","name":"wuqingfeng-hardest"}', encoding="utf-8")
print("TOTAL:", TOTAL, "s  | INTRO_END:", INTRO_END)
for b in blocks: print(f"  {b['no']} {b['name']:14s} start={b['start']:.2f} ns={b['ns']:.2f} full={b['full']:.2f} end={b['end']:.2f} show={b['show']}  Lclip>={b['L']:.1f}s")
print(f"  outro start={F_start:.2f} end={F_end:.2f}")
