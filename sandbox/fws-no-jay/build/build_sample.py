#!/usr/bin/env python3
"""样片构建：封面(设计悬念) + 开场钩子 + 第1首《一直很安静》。
锁定「方文山·非周杰伦创作链」视觉系统（旧纸/水墨/黑金/深蓝/毛笔）。
产物：hf/master.wav + hf/index.html + hf/clips_seg/s1.mp4。
渲染后必须 ffmpeg mux master.wav。"""
import subprocess, wave, contextlib, json
from pathlib import Path

A = "audio"; C = "clips"
def dur(p):
    with contextlib.closing(wave.open(str(p),'r')) as w:
        return round(w.getnframes()/w.getframerate(), 3)
def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

NARR = {k: dur(f"{A}/{k}.wav") for k in ["intro","s1_voice","s1_mid"]}
print("NARR", NARR)

# ============ 节奏常量 ============
COVER_D   = 5.0
IVOICE    = 5.4                      # intro 旁白起点（封面淡出后）
INTRO_END = round(IVOICE + NARR["intro"] + 1.45, 3)   # intro 段结束
LEAD, PRE, POST, SWELL, BED = 0.15, 0.8, 1.2, 1.5, 0.18
CHORUS = 30.0                        # 副歌展示（连续，≥25s）
POST_CHORUS, TAILPAD = 1.0, 0.8

# 第1首 chapter 局部锚点（τ）
v0  = LEAD + PRE                     # 0.95 旁白起
v1  = v0 + NARR["s1_voice"]          # 旁白止
sw0 = v1 + POST                      # swell 起
full0 = sw0 + SWELL                  # 副歌全量起
full1 = full0 + CHORUS               # 副歌全量止
mid_at = full1 + POST_CHORUS         # 短评(余韵)起
S1_LEN = round(mid_at + NARR["s1_mid"] + TAILPAD, 3)

S1 = INTRO_END                       # 第1首绝对起点
TOTAL = round(S1 + S1_LEN, 3)

MSEEK = 6.25                         # vert_asang 内偏移：副歌对齐源 116s
print(f"INTRO_END={INTRO_END} S1={S1} S1_LEN={S1_LEN} TOTAL={TOTAL} ({TOTAL//60:.0f}:{TOTAL%60:05.2f})")
print(f"  chorus τ {full0}..{full1}  (vert {MSEEK+full0}..{MSEEK+full1})")

# ============ 音频段 ============
Path("build/segs").mkdir(parents=True, exist_ok=True)
ASANG = f"{C}/vert_asang.mp4"

# intro 段：低音 ambient 床(用源 MV 前奏) + intro 旁白
run(["ffmpeg","-v","error","-i","raw/asang_full.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{INTRO_END},asetpts=PTS-STARTPTS,volume=0.16,afade=t=in:st=0:d=1.3,afade=t=out:st={INTRO_END-1.6}:d=1.6[bed];"
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(IVOICE*1000)}|{int(IVOICE*1000)},volume=2.0[voice];"
     f"[bed][voice]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_intro.wav","-y"])

# 第1首段：床→swell→副歌全量→淡出；旁白@v0；短评@mid_at（sidechain ducking）
ve = (f"(lt(t,{LEAD}))*0"
      f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
      f"+(between(t,{v0},{sw0}))*{BED}"
      f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
      f"+(gte(t,{full0}))*1.0")
run(["ffmpeg","-v","error","-i",ASANG,"-i",f"{A}/s1_voice.wav","-i",f"{A}/s1_mid.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[vo];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(mid_at*1000)}|{int(mid_at*1000)},volume=2.2[mo];"
     f"[vo][mo]amix=inputs=2:normalize=0:duration=longest[vox];[vox]asplit=2[sc][vmix];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim={MSEEK}:{MSEEK+S1_LEN},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,"
     f"afade=t=out:st={full1}:d={S1_LEN-full1}[music];"
     f"[music][sc]sidechaincompress=threshold=0.04:ratio=8:attack=180:release=320[duck];"
     f"[duck][vmix]amix=inputs=2:normalize=0:duration=longest,atrim=0:{S1_LEN},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_s1.wav","-y"])

# 拼接 master
Path("build/segs/seglist.txt").write_text("file 'seg_intro.wav'\nfile 'seg_s1.wav'\n",encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
import shutil; shutil.copy("master.wav","hf/master.wav")
print("master dur", dur("master.wav"), "planned", TOTAL)

# 切 footage 段（HF 控不了 currentTime → 预切）
run(["ffmpeg","-v","error","-ss",str(MSEEK),"-i",ASANG,"-t",str(S1_LEN),
     "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
     "hf/clips_seg/s1.mp4","-y"])
print("clips_seg/s1.mp4 done")

# ============================================================
# HTML
# ============================================================
CSS = r'''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#080B12;color:#ECE3CE;
  font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased;}
:root{--ink:#080B12;--ink2:#11192B;--gold:#C9A24B;--goldhi:#E8C879;--paper:#ECE3CE;--acc1:#93A7C4;}

/* ---------- 公共纹理 ---------- */
.paper{position:absolute;inset:0;background:
  radial-gradient(ellipse at 30% 18%, rgba(36,46,72,.55) 0, transparent 55%),
  radial-gradient(ellipse at 75% 82%, rgba(28,22,14,.6) 0, transparent 60%),
  linear-gradient(180deg,#0A0E18 0%,#080B12 55%,#06080E 100%);}
.grain{position:absolute;inset:0;opacity:.5;mix-blend-mode:overlay;background-image:
  radial-gradient(circle at 12% 28%, rgba(236,227,206,.05) 0 .6px, transparent 1px),
  radial-gradient(circle at 68% 62%, rgba(236,227,206,.05) 0 .6px, transparent 1px),
  radial-gradient(circle at 42% 88%, rgba(236,227,206,.04) 0 .5px, transparent .9px);
  background-size:160px 160px,210px 210px,140px 140px;}
.fibers{position:absolute;inset:0;opacity:.10;background-image:repeating-linear-gradient(90deg,
  rgba(236,227,206,.5) 0 1px, transparent 1px 7px);mix-blend-mode:soft-light;}

/* ---------- 封面 ---------- */
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
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;letter-spacing:.34em;
  color:var(--gold);margin-bottom:30px;}
.cv-eyebrow b{color:var(--paper);font-weight:800;}
.cv-title{font-family:"Noto Serif SC",serif;font-size:90px;font-weight:900;line-height:1.16;
  color:var(--paper);letter-spacing:-1px;text-shadow:0 4px 24px rgba(0,0,0,.6);}
.cv-title .zjl{color:rgba(236,227,206,.5);position:relative;}
.cv-title .zjl::after{content:"";position:absolute;left:-4px;right:-4px;top:54%;height:6px;background:var(--gold);
  transform:rotate(-3deg);border-radius:3px;opacity:.92;}
.cv-title .fws{color:var(--goldhi);}
.cv-sub{font-family:"Noto Serif SC",serif;font-size:46px;font-weight:500;color:rgba(236,227,206,.82);
  margin-top:36px;letter-spacing:.02em;}
.cv-foot{position:absolute;left:84px;bottom:88px;font-family:"Noto Sans SC",sans-serif;font-size:26px;
  font-weight:600;letter-spacing:.3em;color:rgba(201,162,75,.78);}
.cv-foot .dot{color:rgba(236,227,206,.45);margin:0 14px;}

/* ---------- 开场钩子 ---------- */
.hook{position:absolute;inset:0;z-index:55;background:#06080E;overflow:hidden;}
.hk-glow{position:absolute;inset:0;background:
  radial-gradient(ellipse at 28% 30%, rgba(201,162,75,.10) 0, transparent 52%),
  radial-gradient(ellipse at 72% 74%, rgba(120,150,220,.10) 0, transparent 55%);}
.hk-a{position:absolute;left:0;right:0;top:560px;text-align:center;opacity:0;}
.hk-a .big{font-family:"Ma Shan Zheng",cursive;font-size:230px;color:var(--goldhi);line-height:1;
  text-shadow:0 0 40px rgba(201,162,75,.4);}
.hk-a .neq{font-family:"Noto Serif SC",serif;font-size:50px;color:rgba(236,227,206,.78);margin-top:30px;font-weight:600;}
.hk-b{position:absolute;left:0;right:0;top:600px;text-align:center;opacity:0;}
.hk-b .hkw{display:block;font-family:"Noto Serif SC",serif;font-size:150px;font-weight:800;
  color:var(--paper);line-height:1.14;letter-spacing:.14em;}
.hk-b .hkw.g{color:var(--goldhi);}
.hk-c{position:absolute;left:80px;right:80px;top:740px;text-align:center;opacity:0;}
.hk-c .l1{font-family:"Noto Sans SC",sans-serif;font-size:48px;font-weight:800;letter-spacing:.12em;
  color:var(--gold);margin-bottom:34px;}
.hk-c .l1 i{color:rgba(236,227,206,.5);font-style:normal;text-decoration:line-through;text-decoration-color:var(--gold);}
.hk-c .l2{font-family:"Noto Serif SC",serif;font-size:64px;font-weight:700;color:var(--paper);}

/* ---------- 第1首 chapter ---------- */
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.scrim{position:absolute;inset:0;z-index:2;opacity:0;background:
  linear-gradient(180deg,rgba(6,8,14,.82) 0%,rgba(6,8,14,.12) 26%,rgba(6,8,14,.05) 60%,rgba(6,8,14,.9) 100%);}
.scrim2{position:absolute;inset:0;z-index:2;opacity:0;mix-blend-mode:soft-light;
  background:linear-gradient(180deg,rgba(120,150,200,.18),rgba(10,14,26,.5));}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none;}

/* 顶栏 */
.hd{position:absolute;top:74px;left:88px;right:88px;display:flex;align-items:center;gap:22px;opacity:0;}
.hd .seq{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:700;color:var(--gold);letter-spacing:.12em;}
.hd .line{flex:1;height:1px;background:linear-gradient(90deg,rgba(201,162,75,.6),rgba(201,162,75,0));}
.hd .mark{font-family:"Ma Shan Zheng",cursive;font-size:40px;color:rgba(236,227,206,.8);}

/* 左侧节点轨（匿名，仅进度，不剧透歌单） */
.rail{position:absolute;left:60px;top:300px;bottom:560px;width:8px;opacity:0;}
.rail .bar{position:absolute;left:3px;top:0;bottom:0;width:2px;
  background:linear-gradient(180deg,rgba(236,227,206,.05),rgba(236,227,206,.22),rgba(236,227,206,.05));}
.rail .nd{position:absolute;left:-13px;width:34px;height:34px;border-radius:50%;
  background:rgba(20,25,40,.9);border:2px solid rgba(236,227,206,.22);display:flex;align-items:center;justify-content:center;}
.rail .nd.on{background:var(--gold);border-color:var(--goldhi);box-shadow:0 0 26px rgba(201,162,75,.7);transform:scale(1.2);}
.rail .nd .t{font-family:"JetBrains Mono",monospace;font-size:16px;font-weight:700;color:rgba(236,227,206,.55);}
.rail .nd.on .t{color:#1a1206;}

/* 大关键词（顶部留白带，screen 混合，不挡脸） */
.kw{position:absolute;left:0;right:0;top:300px;text-align:center;font-family:"Noto Serif SC",serif;
  font-size:300px;font-weight:900;color:var(--acc1);opacity:0;letter-spacing:6px;
  mix-blend-mode:screen;filter:drop-shadow(0 6px 50px rgba(147,167,196,.3));}

/* 歌名玻璃卡（底部留白带，不挡 MV 主体脸） */
.card{position:absolute;left:70px;right:70px;bottom:300px;padding:44px 50px 46px;border-radius:24px;opacity:0;
  background:linear-gradient(155deg,rgba(20,26,42,.66),rgba(8,11,20,.5));backdrop-filter:blur(26px);
  -webkit-backdrop-filter:blur(26px);border:1.5px solid rgba(201,162,75,.32);
  box-shadow:0 30px 80px rgba(0,0,0,.6),inset 0 0 0 1px rgba(236,227,206,.06);}
.card .cno{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:700;letter-spacing:.3em;
  color:var(--gold);margin-bottom:16px;}
.card .cname{font-family:"Noto Serif SC",serif;font-size:92px;font-weight:800;line-height:1.02;color:var(--paper);}
.card .cart{font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:600;color:rgba(236,227,206,.78);
  margin-top:10px;letter-spacing:.04em;}
.card .ccr{font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:500;color:rgba(236,227,206,.62);
  margin-top:24px;letter-spacing:.02em;}
.card .ccr b{color:var(--goldhi);font-weight:700;}
.card .ctag{display:inline-flex;align-items:center;gap:14px;margin-top:26px;font-family:"Noto Serif SC",serif;
  font-size:38px;font-weight:700;color:var(--acc1);}
.card .ctag .d{width:12px;height:12px;border-radius:50%;background:var(--acc1);box-shadow:0 0 16px var(--acc1);}

/* 短评（余韵段，居中衬线） */
.midq{position:absolute;left:84px;right:84px;bottom:430px;text-align:center;font-family:"Noto Serif SC",serif;
  font-size:54px;font-weight:600;line-height:1.42;color:rgba(236,227,206,.96);opacity:0;letter-spacing:.01em;
  text-shadow:0 4px 24px rgba(0,0,0,.7);}

/* 来源 */
.src{position:absolute;left:0;right:0;bottom:96px;text-align:center;font-family:"Noto Sans SC",sans-serif;
  font-size:22px;font-weight:500;letter-spacing:.26em;color:rgba(236,227,206,.4);opacity:0;}
'''

cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D+0.6)}" data-track-index="5">
  <div class="paper"></div>
  <div class="cv-bokeh"><span class="b1"></span><span class="b2"></span><span class="b3"></span><span class="b4"></span></div>
  <div class="cv-veil"></div>
  <div class="cv-vinyl" id="cvVinyl"></div>
  <div class="grain"></div>
  <div class="cv-ink"></div>
  <div class="cv-ms"></div>
  <div class="cv-fws">方文山</div>
  <div class="cv-seal"><span>詞</span></div>
  <div class="cv-main">
    <div class="cv-eyebrow">华语词人 · <b>非周杰伦创作链</b></div>
    <h1 class="cv-title">没有<span class="zjl">周杰伦</span>，<br><span class="fws">方文山</span>也写过这些歌</h1>
    <div class="cv-sub">原来这些歌，也藏着他的名字</div>
  </div>
  <div class="cv-foot">手写的歌词<span class="dot">·</span>没署他的脸<span class="dot">·</span>却都听过</div>
</div>'''

hook_html = f'''<div id="hook" class="clip hook" data-start="{fmt(COVER_D-0.6)}" data-duration="{fmt(INTRO_END-(COVER_D-0.6)+0.2)}" data-track-index="6">
  <div class="paper"></div><div class="hk-glow"></div><div class="grain"></div>
  <div class="hk-a" id="hkA"><div class="big">方文山</div><div class="neq">很多人以为，他只会和周杰伦一起出现</div></div>
  <div class="hk-b" id="hkB"><span class="hkw">青春</span><span class="hkw g">江湖</span><span class="hkw">爱情</span></div>
  <div class="hk-c" id="hkC"><div class="l1">方文山 作词 · <i>周杰伦</i> 创作链</div><div class="l2">这些歌，你可能都听过</div></div>
</div>'''

# 第1首 chapter
def anchor_abs(t): return round(S1 + t, 3)
rail_nodes = "".join(
    f'<div class="nd{" on" if i==0 else ""}" style="top:{i*15.4:.1f}%"><span class="t">{i+1}</span></div>'
    for i in range(7))
chapter_html = f'''<video id="fv_s1" class="fv clip" data-start="{fmt(S1)}" data-duration="{fmt(S1_LEN)}" data-track-index="0" src="clips_seg/s1.mp4" muted playsinline></video>
<div id="scrim_s1" class="scrim clip" data-start="{fmt(S1)}" data-duration="{fmt(S1_LEN)}" data-track-index="1"></div>
<div id="scrim2_s1" class="scrim2 clip" data-start="{fmt(S1)}" data-duration="{fmt(S1_LEN)}" data-track-index="7"></div>
<div id="chrome_s1" class="chrome clip" data-start="{fmt(S1)}" data-duration="{fmt(S1_LEN)}" data-track-index="2">
  <div class="hd" id="hd_s1"><span class="seq">第一首 · 01 ／ 07</span><span class="line"></span><span class="mark">詞</span></div>
  <div class="rail" id="rail_s1"><div class="bar"></div>{rail_nodes}</div>
  <div class="kw" id="kw_s1">静</div>
  <div class="card" id="card_s1">
    <div class="cno">FANG WEN SHAN · 01</div>
    <div class="cname">一直很安静</div>
    <div class="cart">阿桑</div>
    <div class="ccr">词：<b>方文山</b>　曲：蔡如岳</div>
    <div class="ctag"><span class="d"></span>安静到卑微的爱</div>
  </div>
  <div class="midq" id="mid_s1">没有华丽的辞藻，也没有大开大合，<br>他只是把站在爱情边缘的沉默，写得很痛。</div>
  <div class="src" id="src_s1">官方 MV · 華研國際</div>
</div>'''

audio_html = f'<audio id="master" class="clip" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ============ JS timeline ============
A0 = anchor_abs
JS = f'''
// ---------- 封面 0~{COVER_D}s（首帧即完整，无淡入） ----------
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .cv-main, #cover .cv-fws, #cover .cv-seal, #cover .cv-foot",{{opacity:1}},0);
tl.to("#cvVinyl",{{rotation:14,duration:{COVER_D+0.6},ease:"none",transformOrigin:"50% 50%"}},0.2);
tl.fromTo(".cv-bokeh",{{scale:1.0}},{{scale:1.06,duration:4.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.3);
tl.fromTo(".cv-title",{{scale:1.0}},{{scale:1.018,duration:3.0,ease:"sine.inOut",yoyo:true,repeat:1}},2.0);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D)});
tl.set("#cover",{{opacity:0}},{fmt(COVER_D+0.6)});

// ---------- 钩子 ----------
tl.set("#hook",{{opacity:1}},{fmt(COVER_D-0.6)});
tl.fromTo("#hkA",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(IVOICE+0.1)});
tl.to("#hkA",{{opacity:0,y:-24,duration:.7,ease:"power2.in"}},{fmt(IVOICE+5.0)});
tl.set("#hkA",{{opacity:0}},{fmt(IVOICE+5.8)});
tl.fromTo("#hkB .hkw",{{opacity:0,y:26}},{{opacity:1,y:0,duration:.6,stagger:.5,ease:"power2.out"}},{fmt(IVOICE+5.6)});
tl.set("#hkB",{{opacity:1}},{fmt(IVOICE+5.6)});
tl.to("#hkB",{{opacity:0,duration:.7,ease:"power2.in"}},{fmt(IVOICE+10.0)});
tl.set("#hkB",{{opacity:0}},{fmt(IVOICE+10.8)});
tl.fromTo("#hkC",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(IVOICE+10.4)});
tl.to("#hook",{{opacity:0,duration:.8,ease:"power2.in"}},{fmt(INTRO_END-0.6)});
tl.set("#hook",{{opacity:0}},{fmt(INTRO_END+0.2)});

// ---------- 第1首《一直很安静》 ----------
tl.fromTo("#fv_s1",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:1.4,ease:"power2.out"}},{fmt(S1)});
tl.to("#scrim_s1",{{opacity:1,duration:1.2}},{fmt(S1)});
tl.to("#scrim2_s1",{{opacity:1,duration:1.2}},{fmt(S1)});
tl.fromTo("#hd_s1",{{opacity:0,y:-14}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(A0(0.5))});
tl.fromTo("#rail_s1",{{opacity:0}},{{opacity:1,duration:.8}},{fmt(A0(0.7))});
tl.fromTo("#card_s1",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(A0(1.0))});
// 旁白收住 → swell → 副歌：卡片下沉减弱、关键词浮现
tl.to("#card_s1",{{opacity:.34,y:10,duration:.7,ease:"power2.inOut"}},{fmt(A0(sw0))});
tl.fromTo("#kw_s1",{{opacity:0,scale:.9}},{{opacity:.5,scale:1,duration:1.8,ease:"power3.out"}},{fmt(A0(full0-0.5))});
tl.to("#kw_s1",{{opacity:.32,duration:2.0,ease:"sine.inOut"}},{fmt(A0(full0+1.5))});
// 短评（余韵）：关键词淡、卡片淡、短评浮现
tl.to("#kw_s1",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(A0(mid_at-0.6))});
tl.set("#kw_s1",{{opacity:0}},{fmt(A0(mid_at+0.4))});
tl.to("#card_s1",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{fmt(A0(mid_at-0.4))});
tl.set("#card_s1",{{opacity:0}},{fmt(A0(mid_at+0.3))});
tl.fromTo("#mid_s1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{fmt(A0(mid_at))});
tl.fromTo("#src_s1",{{opacity:0}},{{opacity:1,duration:.6}},{fmt(A0(1.6))});
// 章节收尾（hard kill 防 seek 残留）
tl.to("#mid_s1",{{opacity:0,duration:.8,ease:"power1.in"}},{fmt(S1+S1_LEN-1.0)});
tl.set("#mid_s1",{{opacity:0}},{fmt(TOTAL)});
tl.to("#fv_s1",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(S1+S1_LEN-1.0)});
tl.set("#fv_s1",{{opacity:0}},{fmt(TOTAL)});
tl.to("#scrim_s1, #scrim2_s1, #src_s1, #hd_s1, #rail_s1",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(S1+S1_LEN-1.0)});
tl.set("#scrim_s1, #scrim2_s1, #src_s1, #hd_s1, #rail_s1",{{opacity:0}},{fmt(TOTAL)});
'''

html = f'''<!doctype html>
<html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=Ma+Shan+Zheng&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
{chapter_html}
{cover_html}
{hook_html}
{audio_html}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"] = tl;
</script>
</body></html>'''

Path("hf/index.html").write_text(html, encoding="utf-8")
print("index.html", len(html), "bytes; TOTAL", TOTAL)
