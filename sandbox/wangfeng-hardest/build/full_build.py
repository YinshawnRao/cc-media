#!/usr/bin/env python3
"""完整片：汪峰最难的5首歌 / 倒数 5→1。摇滚暗黑+猩红/琥珀配色，竖屏 1080x1920。
结构：封面(不剧透排名)+intro女声旁白 → 5首(连续副歌≥25s，footage窗==音乐窗保口型) → 片尾(口播+完整难度榜)。
本机渲染坑：总长>240s 或 ≥7个<video> 必崩 → 切两段渲染。
  PART="" 全片(建 clips_seg + master.wav + index.html，供 lint 参考)
  PART=A  intro+#5+#4 (3 video, ~114s) → partA.html
  PART=B  #3+#2+#1+outro (4 video, ~152s) → partB.html
分段 render --sdr -w1 → ffmpeg concat → mux 全片 master.wav。女声 zf_xiaoyi。"""
import subprocess, wave, contextlib, os
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)
def run(cmd): subprocess.run(cmd, check=True)

A = "audio"; C = "clips"; CS = "clips_seg"
Path(CS).mkdir(exist_ok=True)
LEAD = 0.3; POST = 0.2; DIG = 1.5; SHOW = 25.0
CH_OFF = 24.0
BED_N = 0.14
MGAIN = {"p4_yonggan": 1.5, "p2_dengdai": 1.15}
INTRO_END = 26.0; COVER_END = 6.5; INTRO_VOICE = 3.0

d_out = dur(f"{A}/outro.wav"); d_intro = dur(f"{A}/intro.wav")
d = {k: dur(f"{A}/{k}.wav") for k in
     ["p5_yaobai","p4_yonggan","p3_cunzai","p2_dengdai","p1_guangming"]}

songs = [
    ("p5_yaobai","vert_yiqiyaobai","05","《一起摇摆》",
     ["110+个 G4","近90个 A4","持续轰炸"], "不是气氛歌，<b>是血氧测试</b>"),
    ("p4_yonggan","vert_yonggan","04","《勇敢的心》",
     ["著名 B4 折磨曲","长时高位","体能极限"], "越往后，越像<b>一场体能测试</b>"),
    ("p3_cunzai","vert_cunzai","03","《存在》",
     ["B4 / C#5","男声高压区","字头不能糊"], "想的不是如何存在，<b>是如何换歌</b>"),
    ("p2_dengdai","vert_dengdai","02","《等待》",
     ["撕裂唱法","B4 连咬","C5 撕裂音"], "在嘶吼和失控之间，<b>走钢丝</b>"),
    ("p1_guangming","vert_guangming","01","《光明》",
     ["60+个 A4","C5 - D5 高音","副歌持续高压"], "光明还没寻到，<b>声音先没了</b>"),
]

blocks = []
t = INTRO_END
for key, clip, no, name, tags, tagline in songs:
    L = round(LEAD + d[key] + POST + DIG + SHOW, 3)
    ns = round(t + LEAD, 3); ne = round(ns + d[key], 3)
    full = round(ne + POST + DIG, 3); end = round(t + L, 3)
    mseek = round(CH_OFF - (LEAD + d[key] + POST + DIG), 3)
    blocks.append(dict(key=key, clip=clip, start=t, L=L, end=end, ns=ns, ne=ne, full=full,
                       mseek=mseek, no=no, name=name, tags=tags, tagline=tagline))
    t = end
F_start = t; F_voice = round(F_start + LEAD, 3); F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 3.2, 3); TOTAL = F_end

# ---------- PART 划分 ----------
PART = os.environ.get("WF_PART", "")
SPLIT = 2   # A: blocks[:2]=#5,#4 ; B: blocks[2:]=#3,#2,#1
if PART == "A":
    OFF = 0.0; INC_INTRO = True; INC_OUTRO = False; BLK = blocks[:SPLIT]
    PART_DUR = blocks[SPLIT-1]["end"]; OUTFILE = "partA.html"
elif PART == "B":
    OFF = blocks[SPLIT]["start"]; INC_INTRO = False; INC_OUTRO = True; BLK = blocks[SPLIT:]
    PART_DUR = round(TOTAL - OFF, 3); OUTFILE = "partB.html"
else:
    OFF = 0.0; INC_INTRO = True; INC_OUTRO = True; BLK = blocks
    PART_DUR = TOTAL; OUTFILE = "index.html"
def E(x): return round(x - OFF, 3)
BUILD_AUDIO = (PART == "")

# ---------- clips_seg 精切 + 音频(仅全片模式建) ----------
if BUILD_AUDIO:
    for b in blocks:
        run(["ffmpeg","-v","error","-ss",str(b["mseek"]),"-i",f"{C}/{b['clip']}.mp4","-t",str(b["L"]),
             "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
             "-c:a","aac","-b:a","192k",f"{CS}/{b['key']}.mp4","-y"])
    def envB(ne_loc, full_loc):
        sw = round(ne_loc + POST, 3)
        return (f"(lt(t,{sw}))*{BED_N}"
                f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
                f"+(gte(t,{full_loc}))*1.0")
    segs = []
    v0 = INTRO_VOICE
    veI = (f"(lt(t,0.8))*(0.18*t/0.8)"
           f"+(between(t,0.8,2.8))*0.18"
           f"+(between(t,2.8,3.2))*(0.18-0.12*(t-2.8)/0.4)"
           f"+(between(t,3.2,{v0+d_intro+0.8}))*0.06"
           f"+(between(t,{v0+d_intro+0.8},{INTRO_END}))*(0.06+0.22*(t-{v0+d_intro+0.8})/{max(0.5,INTRO_END-(v0+d_intro+0.8))})"
           f"+(gte(t,{INTRO_END}))*0.28")
    run(["ffmpeg","-v","error","-i",f"{C}/vert_introbed.mp4","-i",f"{A}/intro.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{INTRO_END},volume='{veI}':eval=frame[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000","seg_intro.wav","-y"])
    segs.append("seg_intro.wav")
    for b in blocks:
        seg_dur = b["L"]
        ne_loc = round(LEAD + d[b["key"]], 3); full_loc = round(b["full"] - b["start"], 3)
        ve = envB(ne_loc, full_loc); mg = MGAIN.get(b["key"], 1.0)
        out = f"seg_{b['no']}.wav"
        run(["ffmpeg","-v","error","-i",f"{CS}/{b['key']}.mp4","-i",f"{A}/{b['key']}.wav","-filter_complex",
             f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
             f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
             f"atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
             f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
             "-map","[out]","-ac","2","-ar","48000",out,"-y"])
        segs.append(out)
    segF_dur = round(F_end - F_start, 3)
    run(["ffmpeg","-v","error","-i",f"{C}/vert_introbed.mp4","-i",f"{A}/outro.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{segF_dur},volume=0.2,afade=t=in:st=0:d=1,afade=t=out:st={round(segF_dur-1.8,3)}:d=1.8[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000","seg_outro.wav","-y"])
    segs.append("seg_outro.wav")
    Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
    print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- footage（交替轨道 0/6）----------
fc = []
if INC_INTRO: fc.append(("clips/vert_introbed", 0.0, INTRO_END))
for b in BLK: fc.append((f"clips_seg/{b['key']}", b["start"], b["L"]))
if INC_OUTRO: fc.append(("clips/vert_introbed", F_start, round(F_end-F_start,3)))
vids = "\n".join(
    f'<video id="v{i}" class="fv" data-start="{E(s)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i%2==0 else 6}" src="{src}.mp4" muted playsinline></video>'
    for i,(src,s,dv) in enumerate(fc))

# ---------- 标签 ----------
labels, tweens = [], []
for b in BLK:
    no = b["no"]; fid=f"lf{no}"; mid=f"lm{no}"
    lf_start = round(b["start"]+0.25,3); lf_dur = round(b["full"]-lf_start,3)
    lm_start = b["full"]; lm_dur = round(b["end"]-b["full"],3)
    climax = ' climax' if no=="01" else ''
    badge = '<div class="crown">公认天花板</div>' if no=="01" else '<div class="lab">最难 TOP 5</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{E(lf_start)}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{badge}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>')
    labels.append(
        f'<div id="{mid}" class="clip labelMin{climax}" data-start="{E(lm_start)}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>')
    tweens.append(f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.6,ease:"power3.out"}},{E(lf_start+0.05)});')
    tweens.append(f'tl.from("#{fid} .rank>div:last-child",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{E(lf_start+0.3)});')
    tweens.append(f'tl.from("#{fid} .song",{{y:42,opacity:0,duration:.55,ease:"power3.out"}},{E(lf_start+0.35)});')
    tweens.append(f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.4,ease:"power2.out",stagger:.09}},{E(lf_start+0.65)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:20,opacity:0,duration:.45,ease:"power2.out"}},{E(lf_start+0.95)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{E(b["full"]-0.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{E(b["full"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{E(lm_start+0.1)});')

# ---------- 片尾完整榜单 ----------
outro_html = ""; rank_tweens = []
if INC_OUTRO:
    rank_rows = [("01","《光明》"),("02","《等待》"),("03","《存在》"),("04","《勇敢的心》"),("05","《一起摇摆》")]
    rank_html = "".join(
        f'<div class="rrow{" rgold" if n=="01" else ""}" id="rr{n}"><span class="rn">{n}</span>'
        f'<span class="rs">{nm}</span>{"<span class=rc>公认天花板</span>" if n=="01" else ""}</div>'
        for n,nm in rank_rows)
    outro_html = (
        f'<div id="outro" class="clip" data-start="{E(F_voice-0.4)}" data-duration="{round(F_end-(F_voice-0.4),3)}" data-track-index="9">'
        f'<div class="o1">汪峰，从来不只是热搜上的那个汪峰</div>'
        f'<div class="o2">最难5首 · 完整难度榜</div>'
        f'<div id="rankbox">{rank_html}</div>'
        f'<div class="q">你心里的天花板，是<b>哪一首</b>？</div></div>')
    for i,n in enumerate(["05","04","03","02","01"]):
        rt = E(F_voice + 6.0 + i*1.05)
        rank_tweens.append(f'tl.from("#rr{n}",{{x:-34,opacity:0,duration:.5,ease:"power3.out"}},{rt});')
        if n=="01":
            rank_tweens.append(f'tl.fromTo("#rr01",{{scale:.92}},{{scale:1,duration:.5,ease:"back.out(1.8)"}},{rt});')
    rank_tweens.append(f'tl.from("#outro .o1",{{y:22,opacity:0,duration:.6,ease:"power2.out"}},{E(F_voice+0.1)});')
    rank_tweens.append(f'tl.from("#outro .o2",{{y:40,opacity:0,scale:1.04,duration:.7,ease:"power4.out"}},{E(F_voice+0.7)});')
    rank_tweens.append(f'tl.from("#outro .q",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{E(F_voice+12.0)});')

# ---------- 封面 + intro hook/bridge ----------
intro_html = ""; intro_tweens = []
if INC_INTRO:
    intro_html = (
        f'<div id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="8">'
        f'<div class="cimg"></div><div class="cgrad"></div>'
        f'<div class="ctop"><div class="cbadge">高音封神 · 难度盘点</div></div>'
        f'<div class="ctitle"><div class="who">你以为只会上热搜的<b>汪峰</b></div>'
        f'<div class="hero">最难的5首歌</div>'
        f'<div class="desc">副歌持续高压 · 嘶吼 · <b>高位轰炸</b></div>'
        f'<div class="bar"></div></div></div>'
        f'<div id="hook" class="clip" data-start="7.4" data-duration="6.6" data-track-index="4">'
        f'<div class="hk">先把话放这</div><div class="hl">这五首，每一首副歌<br>都唱到<b>缺氧</b></div></div>'
        f'<div id="bridge" class="clip" data-start="18.4" data-duration="6.6" data-track-index="5">'
        f'<div class="big"><small>公认最难唱</small>TOP 5</div>'
        f'<div class="line">高音 · 嘶吼 · <b>体能极限</b></div></div>')
    intro_tweens = [
        'tl.set("#cover",{opacity:1},0);',
        'tl.set(["#cover .ctitle",".cbadge"],{opacity:1},0);',
        'tl.fromTo("#cover .cimg",{scale:1.0},{scale:1.05,duration:6,ease:"none"},0);',
        'tl.from(".ctitle .hero",{y:30,duration:.7,ease:"power3.out"},0.1);',
        'tl.from(".cbadge",{y:-14,duration:.6,ease:"power2.out"},0.15);',
        f'tl.to("#cover",{{opacity:0,duration:1.0,ease:"power1.inOut"}},{COVER_END-1.0});',
        f'tl.set("#cover",{{opacity:0}},{COVER_END});',
        'tl.from("#hook .hk",{x:-26,opacity:0,duration:.5,ease:"power2.out"},7.5);',
        'tl.from("#hook .hl",{y:26,opacity:0,duration:.6,ease:"power3.out"},7.85);',
        'tl.to("#hook",{opacity:0,duration:.4,ease:"power1.in"},13.6);',
        'tl.set("#hook",{opacity:0},14.0);',
        'tl.from("#bridge .big small",{opacity:0,y:14,duration:.4},18.5);',
        'tl.from("#bridge .big",{scale:.72,opacity:0,duration:.6,ease:"back.out(1.5)"},18.6);',
        'tl.from("#bridge .line",{y:22,opacity:0,duration:.5,ease:"power3.out"},19.15);',
        'tl.to("#bridge",{opacity:0,duration:.45,ease:"power1.in"},24.4);',
        'tl.set("#bridge",{opacity:0},25.0);',
    ]

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08080a;font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,6,9,.62) 0%,rgba(6,6,9,.06) 24%,rgba(6,6,9,.18) 54%,rgba(6,6,9,.88) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(125% 80% at 50% 42%,rgba(0,0,0,0) 40%,rgba(0,0,0,.6) 100%)}
#cover{position:absolute;inset:0;z-index:8;background:#000}
#cover .cimg{position:absolute;inset:0;background:url("assets/cover.png") center/cover no-repeat;transform-origin:50% 42%}
#cover .cgrad{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(8,6,8,.5) 0%,rgba(8,6,8,0) 30%,rgba(8,6,8,.12) 52%,rgba(10,6,8,.82) 82%,rgba(8,5,7,.96) 100%)}
#cover .ctop{position:absolute;top:96px;left:84px;right:84px;display:flex;justify-content:center}
.cbadge{display:inline-flex;align-items:center;gap:14px;padding:13px 30px;border:2px solid rgba(255,60,46,.85);border-radius:999px;font-size:30px;font-weight:800;letter-spacing:.2em;color:#ff6a52;background:rgba(20,6,6,.45)}
.cbadge::before{content:"";width:14px;height:14px;border-radius:50%;background:#ff3324;box-shadow:0 0 18px #ff3324}
#cover .ctitle{position:absolute;left:84px;right:84px;bottom:150px;color:#fff;text-align:left}
.ctitle .who{font-size:46px;font-weight:700;color:#dfe3ea;letter-spacing:.04em}
.ctitle .who b{color:#ff5a45;font-weight:900;font-size:84px;letter-spacing:.02em;margin-left:6px;vertical-align:-6px}
.ctitle .hero{margin-top:8px;font-size:158px;font-weight:900;line-height:.92;letter-spacing:-2px;background:linear-gradient(100deg,#ff5236 4%,#ff8a3c 48%,#ffc24d 98%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 8px 36px rgba(255,80,40,.4))}
.ctitle .desc{margin-top:30px;font-size:38px;font-weight:700;color:#e7eaf0;letter-spacing:.04em}
.ctitle .desc b{color:#ffc24d}
.ctitle .bar{margin-top:24px;width:140px;height:9px;border-radius:5px;background:linear-gradient(90deg,#ff3a24,#ffc24d)}
#hook{position:absolute;left:84px;right:120px;top:300px;z-index:5;color:#fff}
.hk{display:inline-flex;align-items:center;gap:16px;font-size:31px;font-weight:800;color:#ff6a52;letter-spacing:.26em}
.hk::before{content:"";width:50px;height:5px;background:#ff3324;border-radius:3px;box-shadow:0 0 16px rgba(255,60,40,.8)}
#hook .hl{margin-top:34px;font-size:76px;font-weight:900;line-height:1.28;color:#f3f5f8}
#hook .hl b{color:#ffc24d}
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#fff;text-align:center}
#bridge .big{font-size:250px;font-weight:900;line-height:.86;letter-spacing:-4px;background:linear-gradient(100deg,#ff5236,#ff8a3c 50%,#ffc24d);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 50px rgba(255,80,40,.5))}
#bridge .big small{display:block;font-size:58px;font-weight:800;letter-spacing:.22em;color:#ff6a52;margin-bottom:10px;-webkit-text-fill-color:#ff6a52}
#bridge .line{margin-top:26px;font-size:50px;font-weight:900;color:#fff;letter-spacing:.04em}
#bridge .line b{color:#ffc24d}
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#fff}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:33px;font-weight:800;color:#ff6a52;letter-spacing:.24em;padding-bottom:32px}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#2a0b06;background:linear-gradient(180deg,#ffd98a,#ffb02e);border-radius:10px;padding:10px 22px;margin-bottom:36px;letter-spacing:.08em;box-shadow:0 0 34px rgba(255,160,40,.65)}
.labelFull .no{font-size:210px;font-weight:900;line-height:.8;color:#fff;font-family:"Oswald","Noto Sans SC",sans-serif;text-shadow:0 0 44px rgba(255,70,40,.5)}
.labelFull.climax .no{background:linear-gradient(180deg,#ffe0a0,#ffb02e);-webkit-background-clip:text;background-clip:text;color:transparent}
.labelFull .song{font-size:88px;font-weight:900;margin-top:6px;color:#fff;letter-spacing:.01em}
.labelFull.climax .song{font-size:84px}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:31px;font-weight:700;color:#ffd9c2;border:1.5px solid rgba(255,90,60,.55);border-radius:999px;padding:9px 22px}
.labelFull.climax .tags span{color:#ffe2ad;border-color:rgba(255,176,46,.7)}
.labelFull .tag{font-size:43px;font-weight:700;color:#e3e7ee;margin-top:26px;line-height:1.3}
.labelFull .tag b{color:#ff6a52;font-weight:900}
.labelFull.climax .tag b{color:#ffc24d}
.labelMin{position:absolute;top:120px;left:74px;z-index:5;color:#fff;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:64px;font-weight:900;color:#ff5a45;font-family:"Oswald","Noto Sans SC",sans-serif}
.labelMin.climax .no{color:#ffc24d}
.labelMin .song{font-size:50px;font-weight:800}
#outro{position:absolute;left:84px;right:84px;top:182px;z-index:5;color:#fff}
#outro .o1{font-size:42px;font-weight:700;color:#dfe4ec;line-height:1.4}
#outro .o2{margin-top:14px;font-size:74px;font-weight:900;line-height:1.06;background:linear-gradient(100deg,#ff5236,#ff8a3c 50%,#ffc24d);-webkit-background-clip:text;background-clip:text;color:transparent}
#rankbox{margin-top:46px;display:flex;flex-direction:column;gap:20px}
.rrow{display:flex;align-items:center;gap:26px;padding:18px 26px;border-radius:16px;background:rgba(22,16,18,.5);border:1.5px solid rgba(255,90,60,.28)}
.rrow .rn{font-size:62px;font-weight:900;color:#ff5a45;font-family:"Oswald","Noto Sans SC",sans-serif;min-width:96px}
.rrow .rs{font-size:58px;font-weight:900;color:#fff}
.rrow.rgold{background:linear-gradient(90deg,rgba(60,34,8,.7),rgba(30,18,10,.4));border-color:rgba(255,176,46,.75)}
.rrow.rgold .rn{color:#ffc24d}
.rrow .rc{margin-left:auto;font-size:28px;font-weight:900;color:#2a0b06;background:linear-gradient(180deg,#ffd98a,#ffb02e);border-radius:8px;padding:8px 16px;letter-spacing:.06em}
#outro .q{margin-top:42px;font-size:46px;font-weight:800;color:#f0f3f8;text-align:center}
#outro .q b{color:#ffc24d}
"""

body = f'''{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{PART_DUR}" data-track-index="1"></div>
<div id="vig" class="clip" data-start="0" data-duration="{PART_DUR}" data-track-index="7"></div>
{intro_html}
{chr(10).join(labels)}
{outro_html}
<audio id="master" data-start="0" data-duration="{PART_DUR}" data-track-index="3" src="master.wav" data-volume="1"></audio>'''

js = "\n".join(intro_tweens) + "\n" + chr(10).join(tweens) + "\n" + chr(10).join(rank_tweens)

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&family=Oswald:wght@600;700&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{PART_DUR}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>'''

Path(OUTFILE).write_text(html, encoding="utf-8")
Path("meta.json").write_text('{"id":"main","name":"wangfeng-hardest"}', encoding="utf-8")
print(f"PART {PART or 'FULL'} -> {OUTFILE} | PART_DUR={PART_DUR} OFF={OFF} videos={len(fc)} blocks={len(BLK)} intro={INC_INTRO} outro={INC_OUTRO}")
if not PART:
    for b in blocks: print(f"  {b['no']} {b['name']:12s} start={b['start']:.2f} mseek={b['mseek']:.2f} full={b['full']:.2f} end={b['end']:.2f}")
    print(f"  outro start={F_start:.2f} end={F_end:.2f}  TOTAL={TOTAL} ({round(TOTAL/60,2)}min)")
