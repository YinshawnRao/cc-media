#!/usr/bin/env python3
"""完整片：张信哲最难的5首歌 / 倒数 5→1。情歌王子风：墨蓝底 + 香槟金 + 衬线歌名，竖屏 1080x1920。
结构：封面(真人正脸+作品描述，不剧透排名)+intro女声旁白 → 5首(连续副歌≥25s，footage窗==音乐窗保口型) → 片尾(口播+完整难度榜)。
本机渲染坑：总长>240s 或 ≥7个<video> 必崩 → 切两段渲染。
  PART=""  全片(建 clips_seg + master.wav + index.html，供 lint 参考)
  PART=A   intro+#5+#4 → partA.html
  PART=B   #3+#2+#1+outro → partB.html
分段 render --sdr -w1 → ffmpeg concat → mux 全片 master.wav。女声 zf_xiaoyi。"""
import subprocess, wave, contextlib, os
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)
def run(cmd): subprocess.run(cmd, check=True)

A = "audio"; C = "clips"; CS = "clips_seg"
Path(CS).mkdir(exist_ok=True)
LEAD = 0.3; POST = 0.2; DIG = 1.6
BED_N = 0.13
MGAIN = {"p4_airuchaoshui": 0.85}   # QA: 爱如潮水副歌偏热(-14.3) → ×0.85 拉齐到 ~-15.7
INTRO_END = 26.0; COVER_END = 6.5; INTRO_VOICE = 3.0

d_out = dur(f"{A}/outro.wav"); d_intro = dur(f"{A}/intro.wav")
d = {k: dur(f"{A}/{k}.wav") for k in
     ["p5_guohuo","p4_airuchaoshui","p3_taixiangaini","p2_kuanrong","p1_xinyang"]}

# key, clip, no, name, ch_off(副歌在 vert 片内偏移), show, tags, tagline
songs = [
    ("p5_guohuo","vert_guohuo","05","《过火》", 38.0, 30.0,
     ["克制 · 不能过火","高位置 轻薄音色","咬字要精准"], "一用力，<b>味道就全没了</b>"),
    ("p4_airuchaoshui","vert_airuchaoshui","04","《爱如潮水》", 28.0, 31.0,
     ["换声技术","音色要统一","柔韧不能变粗"], "潮水来了，<b>嗓子不能被淹</b>"),
    ("p3_taixiangaini","vert_taixiangaini","03","《太想爱你》", 25.0, 36.0,
     ["长线条 高位情绪","气息续航","明亮不能喊破"], "唱轻没情绪，<b>唱重失清透</b>"),
    ("p2_kuanrong","vert_kuanrong","02","《宽容》", 43.0, 28.0,
     ["换声区折磨","极吃闭合 · 气息","越用力越僵"], "深情，最怕唱成<b>硬扛</b>"),
    ("p1_xinyang","vert_xinyang","01","《信仰》", 32.0, 33.0,
     ["副歌长时高位","明亮 不能发粗","有力 不能硬喊"], "上得去，<b>更要稳得住</b>"),
]

blocks = []
t = INTRO_END
for key, clip, no, name, ch_off, show, tags, tagline in songs:
    L = round(LEAD + d[key] + POST + DIG + show, 3)
    ns = round(t + LEAD, 3); ne = round(ns + d[key], 3)
    full = round(ne + POST + DIG, 3); end = round(t + L, 3)
    mseek = round(ch_off - (LEAD + d[key] + POST + DIG), 3)
    blocks.append(dict(key=key, clip=clip, start=t, L=L, end=end, ns=ns, ne=ne, full=full,
                       mseek=mseek, no=no, name=name, tags=tags, tagline=tagline, show=show, ch_off=ch_off))
    t = end
F_start = t; F_voice = round(F_start + LEAD, 3); F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 3.4, 3); TOTAL = F_end

# ---------- PART 划分 ----------
PART = os.environ.get("ZX_PART", "")
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
    veI = (f"(lt(t,0.8))*(0.16*t/0.8)"
           f"+(between(t,0.8,2.6))*0.16"
           f"+(between(t,2.6,3.0))*(0.16-0.10*(t-2.6)/0.4)"
           f"+(between(t,3.0,{v0+d_intro+0.8}))*0.06"
           f"+(between(t,{v0+d_intro+0.8},{INTRO_END}))*(0.06+0.24*(t-{v0+d_intro+0.8})/{max(0.5,INTRO_END-(v0+d_intro+0.8))})"
           f"+(gte(t,{INTRO_END}))*0.30")
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
         f"atrim=0:{segF_dur},volume=0.22,afade=t=in:st=0:d=1,afade=t=out:st={round(segF_dur-2.0,3)}:d=2.0[music];"
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
    tweens.append(f'tl.from("#{fid} .song",{{y:42,opacity:0,duration:.6,ease:"power3.out"}},{E(lf_start+0.35)});')
    tweens.append(f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.4,ease:"power2.out",stagger:.09}},{E(lf_start+0.7)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:20,opacity:0,duration:.45,ease:"power2.out"}},{E(lf_start+1.0)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{E(b["full"]-0.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{E(b["full"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{E(lm_start+0.1)});')

# ---------- 片尾完整榜单 ----------
outro_html = ""; rank_tweens = []
if INC_OUTRO:
    rank_rows = [("01","《信仰》"),("02","《宽容》"),("03","《太想爱你》"),("04","《爱如潮水》"),("05","《过火》")]
    rank_html = "".join(
        f'<div class="rrow{" rgold" if n=="01" else ""}" id="rr{n}"><span class="rn">{n}</span>'
        f'<span class="rs">{nm}</span>{"<span class=rc>公认天花板</span>" if n=="01" else ""}</div>'
        for n,nm in rank_rows)
    outro_html = (
        f'<div id="outro" class="clip" data-start="{E(F_voice-0.4)}" data-duration="{round(F_end-(F_voice-0.4),3)}" data-track-index="9">'
        f'<div class="o1">那份听起来毫不费力的干净</div>'
        f'<div class="o2">最难5首 · 完整难度榜</div>'
        f'<div id="rankbox">{rank_html}</div>'
        f'<div class="q">你心里的天花板，是<b>哪一首</b>？</div></div>')
    for i,n in enumerate(["05","04","03","02","01"]):
        rt = E(F_voice + 6.2 + i*1.05)
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
        f'<div class="ctop"><div class="cbadge">华语情歌天花板 · 难度盘点</div></div>'
        f'<div class="ctitle"><div class="who">情歌王子 <b>张信哲</b></div>'
        f'<div class="hero">最难的<em>5</em>首歌</div>'
        f'<div class="desc">清亮 · 高位 · 那份干净，<b>最难复刻</b></div>'
        f'<div class="bar"></div></div></div>'
        f'<div id="hook" class="clip" data-start="7.4" data-duration="6.8" data-track-index="4">'
        f'<div class="hk">先说在前面</div><div class="hl">他唱得越像<b>不费力</b><br>底下越是<b>真功夫</b></div></div>'
        f'<div id="bridge" class="clip" data-start="18.6" data-duration="6.6" data-track-index="5">'
        f'<div class="big"><small>公认最难唱</small>TOP 5</div>'
        f'<div class="line">换声 · 高位 · <b>气息控制</b></div></div>')
    intro_tweens = [
        'tl.set("#cover",{opacity:1},0);',
        'tl.set(["#cover .ctitle",".cbadge"],{opacity:1},0);',
        'tl.fromTo("#cover .cimg",{scale:1.0},{scale:1.05,duration:6.5,ease:"none"},0);',
        'tl.from(".ctitle .hero",{y:30,duration:.7,ease:"power3.out"},0.1);',
        'tl.from(".cbadge",{y:-14,duration:.6,ease:"power2.out"},0.15);',
        f'tl.to("#cover",{{opacity:0,duration:1.0,ease:"power1.inOut"}},{COVER_END-1.0});',
        f'tl.set("#cover",{{opacity:0}},{COVER_END});',
        'tl.from("#hook .hk",{x:-26,opacity:0,duration:.5,ease:"power2.out"},7.5);',
        'tl.from("#hook .hl",{y:26,opacity:0,duration:.6,ease:"power3.out"},7.85);',
        'tl.to("#hook",{opacity:0,duration:.4,ease:"power1.in"},13.8);',
        'tl.set("#hook",{opacity:0},14.2);',
        'tl.from("#bridge .big small",{opacity:0,y:14,duration:.4},18.7);',
        'tl.from("#bridge .big",{scale:.72,opacity:0,duration:.6,ease:"back.out(1.5)"},18.8);',
        'tl.from("#bridge .line",{y:22,opacity:0,duration:.5,ease:"power3.out"},19.35);',
        'tl.to("#bridge",{opacity:0,duration:.45,ease:"power1.in"},24.6);',
        'tl.set("#bridge",{opacity:0},25.1);',
    ]

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#070b14;font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,9,18,.66) 0%,rgba(6,9,18,.05) 26%,rgba(6,9,18,.16) 52%,rgba(5,7,14,.9) 100%)}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(128% 82% at 50% 40%,rgba(0,0,0,0) 42%,rgba(2,4,9,.62) 100%)}
#cover{position:absolute;inset:0;z-index:8;background:#04060c}
#cover .cimg{position:absolute;inset:0;background:url("assets/cover.png") center/cover no-repeat;transform-origin:50% 38%}
#cover .cgrad{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(5,8,16,.42) 0%,rgba(5,8,16,0) 26%,rgba(5,8,16,.10) 48%,rgba(5,8,18,.8) 78%,rgba(4,6,13,.97) 100%)}
#cover .ctop{position:absolute;top:104px;left:84px;right:84px;display:flex;justify-content:center}
.cbadge{display:inline-flex;align-items:center;gap:14px;padding:13px 32px;border:1.5px solid rgba(233,201,135,.7);border-radius:999px;font-size:29px;font-weight:700;letter-spacing:.18em;color:#f0d28a;background:rgba(10,14,28,.4);backdrop-filter:blur(2px)}
.cbadge::before{content:"";width:12px;height:12px;border-radius:50%;background:#e9c987;box-shadow:0 0 18px #e9c987}
#cover .ctitle{position:absolute;left:84px;right:84px;bottom:158px;color:#fff;text-align:left}
.ctitle .who{font-size:44px;font-weight:500;color:#cdd6e6;letter-spacing:.06em}
.ctitle .who b{color:#f0d28a;font-weight:800;font-size:62px;letter-spacing:.02em;margin-left:8px;font-family:"Noto Serif SC",serif;vertical-align:-4px}
.ctitle .hero{margin-top:14px;font-family:"Noto Serif SC",serif;font-size:152px;font-weight:900;line-height:.94;letter-spacing:1px;color:#f4f6fb;text-shadow:0 6px 40px rgba(0,0,0,.5)}
.ctitle .hero em{font-style:normal;background:linear-gradient(150deg,#f6e3ab 6%,#e9c987 50%,#c79a4e 98%);-webkit-background-clip:text;background-clip:text;color:transparent;padding:0 4px}
.ctitle .desc{margin-top:30px;font-size:37px;font-weight:500;color:#d7dce8;letter-spacing:.05em}
.ctitle .desc b{color:#f0d28a;font-weight:800}
.ctitle .bar{margin-top:26px;width:132px;height:6px;border-radius:4px;background:linear-gradient(90deg,#e9c987,rgba(233,201,135,0))}
#hook{position:absolute;left:84px;right:110px;top:300px;z-index:5;color:#fff}
.hk{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:700;color:#f0d28a;letter-spacing:.22em}
.hk::before{content:"";width:48px;height:3px;background:#e9c987;border-radius:3px;box-shadow:0 0 14px rgba(233,201,135,.7)}
#hook .hl{margin-top:34px;font-family:"Noto Serif SC",serif;font-size:74px;font-weight:700;line-height:1.34;color:#f1f4fa}
#hook .hl b{color:#f0d28a}
#bridge{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-50%);z-index:5;color:#fff;text-align:center}
#bridge .big{font-family:"Noto Serif SC",serif;font-size:236px;font-weight:900;line-height:.9;letter-spacing:1px;background:linear-gradient(150deg,#f6e3ab,#e9c987 52%,#c79a4e);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 6px 36px rgba(180,140,60,.35))}
#bridge .big small{display:block;font-family:"Noto Sans SC",sans-serif;font-size:52px;font-weight:700;letter-spacing:.24em;color:#aebfd6;margin-bottom:14px;-webkit-text-fill-color:#aebfd6}
#bridge .line{margin-top:30px;font-size:46px;font-weight:700;color:#eef1f7;letter-spacing:.05em}
#bridge .line b{color:#f0d28a}
.labelFull{position:absolute;left:84px;right:84px;bottom:300px;z-index:5;color:#fff}
.labelFull .rank{display:flex;align-items:flex-end;gap:26px}
.labelFull .rank .lab{font-size:31px;font-weight:700;color:#aebfd6;letter-spacing:.22em;padding-bottom:34px}
.labelFull .rank .crown{font-size:33px;font-weight:800;color:#3a2607;background:linear-gradient(180deg,#f6e3ab,#e0b766);border-radius:9px;padding:10px 22px;margin-bottom:38px;letter-spacing:.06em;box-shadow:0 0 30px rgba(224,183,102,.5)}
.labelFull .no{font-size:200px;font-weight:800;line-height:.78;color:#f4f6fb;font-family:"Oswald","Noto Sans SC",sans-serif;text-shadow:0 0 40px rgba(20,40,80,.6)}
.labelFull.climax .no{background:linear-gradient(180deg,#f6e3ab,#e0b766);-webkit-background-clip:text;background-clip:text;color:transparent}
.labelFull .song{font-family:"Noto Serif SC",serif;font-size:86px;font-weight:900;margin-top:10px;color:#fff;letter-spacing:.01em}
.labelFull.climax .song{font-size:82px}
.labelFull .tags{margin-top:26px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:500;color:#cdd9ea;border:1.5px solid rgba(150,180,215,.42);border-radius:999px;padding:9px 22px;background:rgba(12,18,34,.36)}
.labelFull.climax .tags span{color:#f1e2b8;border-color:rgba(224,183,102,.6)}
.labelFull .tag{font-size:42px;font-weight:600;color:#e3e8f2;margin-top:28px;line-height:1.3}
.labelFull .tag b{color:#f0d28a;font-weight:800}
.labelMin{position:absolute;top:120px;left:74px;z-index:5;color:#fff;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:60px;font-weight:800;color:#f0d28a;font-family:"Oswald","Noto Sans SC",sans-serif}
.labelMin.climax .no{color:#f6e3ab}
.labelMin .song{font-family:"Noto Serif SC",serif;font-size:48px;font-weight:700}
#outro{position:absolute;left:84px;right:84px;top:196px;z-index:5;color:#fff}
#outro .o1{font-size:40px;font-weight:500;color:#cdd6e6;line-height:1.4}
#outro .o2{margin-top:14px;font-family:"Noto Serif SC",serif;font-size:72px;font-weight:900;line-height:1.08;background:linear-gradient(150deg,#f6e3ab,#e9c987 52%,#c79a4e);-webkit-background-clip:text;background-clip:text;color:transparent}
#rankbox{margin-top:48px;display:flex;flex-direction:column;gap:20px}
.rrow{display:flex;align-items:center;gap:28px;padding:18px 28px;border-radius:15px;background:rgba(14,20,38,.5);border:1.5px solid rgba(150,180,215,.24)}
.rrow .rn{font-size:60px;font-weight:800;color:#aebfd6;font-family:"Oswald","Noto Sans SC",sans-serif;min-width:92px}
.rrow .rs{font-family:"Noto Serif SC",serif;font-size:54px;font-weight:900;color:#fff}
.rrow.rgold{background:linear-gradient(90deg,rgba(58,42,12,.66),rgba(20,18,12,.4));border-color:rgba(224,183,102,.7)}
.rrow.rgold .rn{color:#f6e3ab}
.rrow .rc{margin-left:auto;font-size:27px;font-weight:800;color:#3a2607;background:linear-gradient(180deg,#f6e3ab,#e0b766);border-radius:8px;padding:8px 16px;letter-spacing:.05em}
#outro .q{margin-top:44px;font-size:44px;font-weight:700;color:#eef1f7;text-align:center}
#outro .q b{color:#f0d28a}
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
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Noto+Serif+SC:wght@700;900&family=Oswald:wght@600;700&display=swap" rel="stylesheet"/>
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
Path("meta.json").write_text('{"id":"main","name":"zhangxinzhe-hardest"}', encoding="utf-8")
print(f"PART {PART or 'FULL'} -> {OUTFILE} | PART_DUR={PART_DUR} OFF={OFF} videos={len(fc)} blocks={len(BLK)} intro={INC_INTRO} outro={INC_OUTRO}")
if not PART:
    for b in blocks: print(f"  {b['no']} {b['name']:12s} start={b['start']:.2f} mseek={b['mseek']:.2f} full={b['full']:.2f} end={b['end']:.2f} show={b['show']}")
    print(f"  outro start={F_start:.2f} end={F_end:.2f}  TOTAL={TOTAL} ({round(TOTAL/60,2)}min)")
