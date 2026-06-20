#!/usr/bin/env python3
"""SAMPLE build — 走出考场那一刻 · 请打开五月天（毕业情绪叙事盘点）。
样片范围：封面(纯情绪) → 开头钩子(女声) → 标题 → 转场 → 第1首《知足》完整章节 → 收束淡出。
设计目标：不剧透歌单、女声温柔克制、夏日白光基调、官方MV letterbox + 设计化氛围。
渲染后必须 ffmpeg mux master.wav（HyperFrames 会压平音频动态）。
"""
import subprocess, wave, contextlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "audio"; C = ROOT / "clips"; HF = ROOT / "hf"

def wdur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def adur(p):
    out = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)])
    return round(float(out), 3)

def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)

HOOK_V = adur(A/"hook.wav")
S1_V   = adur(A/"s1_voice.wav")
print(f"hook={HOOK_V}s  s1={S1_V}s")

# ============ 节奏常量 ============
COVER_D = 3.4
HOOK_VOICE_AT = 4.0          # abs
HOOK_END   = HOOK_VOICE_AT + HOOK_V + 0.7
TITLE_T    = round(HOOK_END - 0.1, 3)
TITLE_D    = 4.4
TRANS_T    = round(TITLE_T + TITLE_D - 0.2, 3)
TRANS_D    = 3.9
S1_T       = round(TRANS_T + TRANS_D - 0.1, 3)

# 章节内部锚点（相对 S1_T）
LEAD=0.2; PRE=0.8; POST=1.3; SWELL=1.6; SHOW=34.0; TAIL=1.5
s1_voice_at = LEAD+PRE                          # 1.0
s1_v1   = s1_voice_at + S1_V
s1_sw0  = s1_v1 + POST
s1_full = s1_sw0 + SWELL                         # showcase start (chorus)
s1_fend = s1_full + SHOW
S1_DUR  = round(s1_fend + TAIL, 3)
S1_END  = round(S1_T + S1_DUR, 3)
TOTAL   = S1_END

OPEN_DUR = S1_T                                  # open audio segment length
print(f"sections: cover0-{COVER_D} hook{HOOK_VOICE_AT} title{TITLE_T} trans{TRANS_T} s1{S1_T} end{S1_END}")
print(f"s1 showcase abs {S1_T+s1_full:.2f}-{S1_T+s1_fend:.2f}  footage vert@show={S1_T+s1_full-S1_T:.2f}s (song {46+(s1_full):.0f}s)")
print(f"TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

BED=0.16
SEG = ROOT/"build"/"segs"; SEG.mkdir(parents=True, exist_ok=True)

# ---- seg_open: 钢琴床(知足intro) + hook 女声 ----
# 床音量包络：0->0.13 ramp(0-1.2), 0.13 hold, title 段轻微抬到 0.20
title_rise = TITLE_T
ve_open = (f"(lt(t,1.2))*({0.13}*t/1.2)"
           f"+(between(t,1.2,{title_rise}))*{0.13}"
           f"+(between(t,{title_rise},{title_rise+2.0}))*({0.13}+{0.20-0.13}*(t-{title_rise})/2.0)"
           f"+(gte(t,{title_rise+2.0}))*{0.20}")
run(["ffmpeg","-v","error","-i",A/"zhizu_intro.wav","-i",A/"hook.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(HOOK_VOICE_AT*1000)}|{int(HOOK_VOICE_AT*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
     f"atrim=0:{OPEN_DUR},asetpts=PTS-STARTPTS,volume='{ve_open}':eval=frame,"
     f"afade=t=in:st=0:d=1.0,afade=t=out:st={OPEN_DUR-0.6}:d=0.6[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OPEN_DUR},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",SEG/"seg_open.wav","-y"])

# ---- seg_s1: 知足 章节（footage 音乐床→swell→副歌全量 + s1 女声）----
ve_s1 = (f"(lt(t,{LEAD}))*0"
         f"+(between(t,{LEAD},{s1_voice_at}))*({BED}*(t-{LEAD})/{s1_voice_at-LEAD})"
         f"+(between(t,{s1_voice_at},{s1_sw0}))*{BED}"
         f"+(between(t,{s1_sw0},{s1_full}))*({BED}+{1.0-BED}*(t-{s1_sw0})/{SWELL})"
         f"+(gte(t,{s1_full}))*1.0")
run(["ffmpeg","-v","error","-i",C/"vert_zhizu.mp4","-i",A/"s1_voice.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(s1_voice_at*1000)}|{int(s1_voice_at*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{S1_DUR},asetpts=PTS-STARTPTS,volume='{ve_s1}':eval=frame,"
     f"afade=t=out:st={s1_fend}:d={TAIL}[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{S1_DUR},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",SEG/"seg_s1.wav","-y"])

# ---- concat master ----
(SEG/"list.txt").write_text("file 'seg_open.wav'\nfile 'seg_s1.wav'\n", encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",SEG/"list.txt","-ac","2","-ar","48000",ROOT/"master.wav","-y"])
print("master:", adur(ROOT/"master.wav"), "planned:", TOTAL)

# ---- HF assets: master + footage (video-only, dense kf) ----
HF.mkdir(exist_ok=True)
(HF/"clips_seg").mkdir(exist_ok=True)
import shutil
shutil.copy(ROOT/"master.wav", HF/"master.wav")
run(["ffmpeg","-v","error","-i",C/"vert_zhizu.mp4","-t",str(S1_DUR+0.5),
     "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
     HF/"clips_seg"/"s1.mp4","-y"])

def f(x): return f"{round(x,3)}"

# =====================================================================
#  HTML / CSS / JS
# =====================================================================
CSS = r'''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0c0b0a;
  font-family:"Noto Serif SC",serif;color:#241d14;-webkit-font-smoothing:antialiased;}
.layer{position:absolute;inset:0;width:1080px;height:1920px;}

/* ---------- 共用纹理 ---------- */
.grain{position:absolute;inset:0;pointer-events:none;mix-blend-mode:overlay;opacity:.5;
  background-image:radial-gradient(circle at 12% 22%,rgba(255,255,255,.05) 0 .5px,transparent .9px),
   radial-gradient(circle at 76% 64%,rgba(0,0,0,.05) 0 .5px,transparent .9px),
   radial-gradient(circle at 44% 88%,rgba(255,255,255,.04) 0 .4px,transparent .8px);
  background-size:200px 200px,240px 240px,170px 170px;}

/* ================= COVER ================= */
#cover{z-index:60;background:linear-gradient(168deg,#FBF6EA 0%,#F4ECDA 46%,#E7DAC2 100%);overflow:hidden;}
.cv-sun{position:absolute;top:-160px;right:-120px;width:760px;height:760px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,247,224,.95) 0%,rgba(255,240,200,.55) 32%,rgba(255,236,190,0) 66%);
  filter:blur(6px);}
.cv-haze{position:absolute;inset:0;background:linear-gradient(180deg,rgba(255,250,235,.0) 40%,rgba(255,247,228,.35) 100%);}
.cv-floor{position:absolute;left:0;right:0;bottom:0;height:430px;
  background:linear-gradient(180deg,rgba(206,190,160,0) 0%,rgba(196,178,146,.35) 60%,rgba(150,132,100,.42) 100%);}
/* 散场人群背影（剪影，纯CSS） */
.crowd{position:absolute;left:0;right:0;bottom:150px;height:300px;}
.fig{position:absolute;bottom:0;background:#6b5c44;opacity:.30;filter:blur(.4px);}
.fig::before{content:"";position:absolute;left:50%;transform:translateX(-50%);border-radius:50%;background:#6b5c44;}
/* admission ticket 准考证 */
.ticket{position:absolute;left:64px;bottom:300px;width:330px;height:226px;transform:rotate(-6deg);
  background:linear-gradient(160deg,#fffdf7,#f3ead7);border-radius:10px;
  box-shadow:0 26px 50px rgba(90,70,40,.30),0 2px 0 rgba(255,255,255,.6) inset;
  padding:18px 20px;}
.ticket::after{content:"";position:absolute;inset:0;border-radius:10px;
  background:linear-gradient(110deg,rgba(255,255,255,.35) 0%,rgba(255,255,255,0) 30%,rgba(0,0,0,.05) 64%,rgba(255,255,255,.25) 100%);}
.tk-hd{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:800;letter-spacing:.42em;
  color:#b23b2e;border-bottom:2px solid rgba(178,59,46,.5);padding-bottom:8px;}
.tk-row{display:flex;gap:14px;margin-top:16px;}
.tk-photo{width:70px;height:88px;background:repeating-linear-gradient(135deg,#d8cdb4,#d8cdb4 6px,#cfc3a6 6px,#cfc3a6 12px);border:1px solid rgba(120,100,70,.4);border-radius:3px;}
.tk-lines{flex:1;display:flex;flex-direction:column;gap:12px;padding-top:6px;}
.tk-line{height:9px;border-radius:5px;background:rgba(120,100,70,.30);}
.tk-line.s{width:62%;}

.cv-text{position:absolute;right:54px;top:560px;width:660px;text-align:right;z-index:3;}
.cv-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:700;letter-spacing:.30em;
  color:#9a6b3a;margin-bottom:26px;}
.cv-rule{width:120px;height:3px;background:linear-gradient(90deg,transparent,#c08a3e);margin:0 0 30px auto;}
.cv-h1{font-size:102px;font-weight:900;line-height:1.08;color:#2a2118;letter-spacing:-1px;white-space:nowrap;
  text-shadow:0 2px 24px rgba(255,250,235,.6);}
.cv-h2{font-size:94px;font-weight:900;line-height:1.12;color:#b23b2e;letter-spacing:-1px;margin-top:6px;white-space:nowrap;}
.cv-sub{font-family:"Noto Sans SC",sans-serif;font-size:31px;font-weight:500;line-height:1.55;
  color:#6a5740;margin-top:34px;}

/* ================= HOOK ================= */
#hook{z-index:55;background:linear-gradient(176deg,#FAF4E6 0%,#F1E7D2 60%,#E2D3B6 100%);opacity:0;overflow:hidden;}
.hk-sun{position:absolute;top:-200px;left:50%;transform:translateX(-50%);width:900px;height:560px;
  background:radial-gradient(ellipse at center,rgba(255,248,228,.9) 0%,rgba(255,243,210,0) 70%);}
.hk-paper{position:absolute;width:150px;height:200px;background:linear-gradient(160deg,#fffef9,#efe6d2);
  border-radius:4px;box-shadow:0 18px 36px rgba(120,95,55,.22);opacity:0;}
.hk-lines{position:absolute;left:90px;right:90px;top:760px;text-align:center;}
.hk-l{font-size:62px;font-weight:700;line-height:1.3;color:#332817;opacity:0;letter-spacing:.01em;}
.hk-l.dim{font-size:54px;font-weight:500;color:#6a5a40;}
.hk-l.accent{color:#9a3526;font-weight:800;}

/* ================= TITLE ================= */
#title{z-index:54;background:linear-gradient(170deg,#F7EFDE 0%,#EADBBF 100%);opacity:0;overflow:hidden;}
.ti-vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,rgba(255,252,242,.6) 0%,rgba(210,190,156,.0) 55%),
  linear-gradient(180deg,rgba(120,100,66,.10),rgba(120,100,66,.22));}
.ti-wrap{position:absolute;left:80px;right:80px;top:680px;text-align:center;}
.ti-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:700;letter-spacing:.42em;
  color:#9a6b3a;margin-bottom:34px;opacity:0;}
.ti-l1{font-size:86px;font-weight:900;line-height:1.18;color:#2a2118;letter-spacing:-1px;opacity:0;}
.ti-l2{font-size:96px;font-weight:900;line-height:1.2;color:#b23b2e;letter-spacing:-1px;margin-top:14px;opacity:0;}
.ti-rule{width:0;height:3px;background:#c08a3e;margin:40px auto 0;}

/* ================= TRANSITION ================= */
#trans{z-index:53;opacity:0;background:linear-gradient(180deg,#1a1610 0%,#0e0b07 100%);overflow:hidden;}
.tr-wrap{position:absolute;left:90px;right:90px;top:820px;text-align:center;}
.tr-l{font-size:58px;font-weight:600;line-height:1.42;color:#efe6d2;opacity:0;letter-spacing:.02em;}
.tr-l.accent{color:#f3c46a;font-weight:700;}

/* ================= CHAPTER s1 ================= */
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.tint{position:absolute;inset:0;z-index:2;opacity:0;
  background:linear-gradient(180deg,rgba(255,250,235,.16) 0%,rgba(255,250,235,0) 26%,
    rgba(40,32,20,.06) 60%,rgba(22,16,8,.60) 100%);}
.tint-top{position:absolute;inset:0;z-index:2;opacity:0;
  background:linear-gradient(180deg,rgba(18,13,6,.40) 0%,rgba(18,13,6,0) 24%);}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none;}

/* 歌名章节卡（右上玻璃卡） */
.card{position:absolute;top:150px;right:54px;width:560px;padding:40px 44px 38px;border-radius:24px;
  background:linear-gradient(160deg,rgba(255,250,238,.16),rgba(255,250,238,.05));
  backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);
  border:1.5px solid rgba(255,246,225,.30);box-shadow:0 30px 80px rgba(0,0,0,.45);opacity:0;}
.card-no{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:800;letter-spacing:.30em;color:#f3c46a;}
.card-name-row{display:flex;align-items:baseline;gap:20px;margin-top:14px;}
.card-name{font-size:80px;font-weight:900;color:#fff7e9;letter-spacing:1px;line-height:1;}
.card-emo{font-family:"Noto Sans SC",sans-serif;font-size:36px;font-weight:700;color:#f3c46a;}
.card-credit{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:500;line-height:1.5;
  color:rgba(255,247,232,.74);margin-top:22px;letter-spacing:.02em;}

/* 大情绪关键词（副歌段） */
.kw{position:absolute;left:0;right:0;bottom:560px;text-align:center;font-size:300px;font-weight:900;
  line-height:.85;color:rgba(255,248,228,.16);opacity:0;letter-spacing:-6px;}
/* 副歌底部小标签行 */
.subline{position:absolute;left:80px;right:80px;bottom:300px;text-align:center;
  font-size:48px;font-weight:600;color:#fff7e9;opacity:0;letter-spacing:.02em;
  text-shadow:0 3px 24px rgba(0,0,0,.6);}
.src{position:absolute;bottom:54px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;
  font-size:19px;font-weight:400;color:rgba(255,247,232,.34);letter-spacing:.22em;opacity:0;}
'''

# ---------- crowd silhouettes (背影) ----------
# 形状: 矩形身体 + ::before 头. 用内联样式排一排，远近大小不一
crowd_specs = [
    # left%, w, bodyH, headD, op
    (4,52,150,40,.34),(13,46,128,34,.28),(22,58,168,46,.36),(33,42,120,32,.24),
    (44,60,176,48,.40),(56,50,150,40,.30),(66,46,132,36,.26),(76,58,166,46,.36),
    (87,48,140,38,.30),
]
crowd_html = ""
for i,(lf,w,bh,hd,op) in enumerate(crowd_specs):
    crowd_html += (f'<div class="fig" style="left:{lf}%;width:{w}px;height:{bh}px;opacity:{op};'
                   f'border-radius:{w//3}px {w//3}px 0 0;">'
                   f'<i style="position:absolute;bottom:{bh-6}px;left:50%;transform:translateX(-50%);'
                   f'width:{hd}px;height:{hd}px;border-radius:50%;background:#6b5c44;"></i></div>')

ticket_html = '''<div class="ticket">
  <div class="tk-hd">准 考 证</div>
  <div class="tk-row"><div class="tk-photo"></div>
    <div class="tk-lines"><div class="tk-line"></div><div class="tk-line s"></div>
      <div class="tk-line"></div><div class="tk-line s"></div></div></div>
</div>'''

cover_html = f'''<div id="cover" class="layer">
  <div class="cv-sun"></div>
  <div class="cv-haze"></div>
  <div class="cv-floor"></div>
  <div class="crowd">{crowd_html}</div>
  {ticket_html}
  <div class="cv-text">
    <div class="cv-eyebrow">毕业季 · 五月天单团歌单</div>
    <div class="cv-rule"></div>
    <div class="cv-h1">走出考场<br>那一刻</div>
    <div class="cv-h2">请打开五月天</div>
    <div class="cv-sub">给高考后的你，<br>一条从告别到出发的歌单</div>
  </div>
  <div class="grain"></div>
</div>'''

hook_html = f'''<div id="hook" class="layer">
  <div class="hk-sun"></div>
  <div class="crowd" style="bottom:120px;opacity:.85;">{crowd_html}</div>
  <div class="hk-paper" id="hkpaper" style="left:140px;top:430px;transform:rotate(-12deg);"></div>
  <div class="hk-paper" id="hkpaper2" style="right:150px;top:360px;transform:rotate(9deg);"></div>
  <div class="hk-lines">
    <div class="hk-l" id="hk1">最后一科交卷后</div>
    <div class="hk-l dim" id="hk2">你以为会很激动</div>
    <div class="hk-l accent" id="hk3">但走出考场那一刻，<br>反而有点空</div>
  </div>
  <div class="grain"></div>
</div>'''

title_html = f'''<div id="title" class="layer">
  <div class="ti-vig"></div>
  <div class="ti-wrap">
    <div class="ti-eyebrow" id="tiE">写给刚放下笔的你</div>
    <div class="ti-l1" id="tiL1">走出高考考场那一刻</div>
    <div class="ti-l2" id="tiL2">请打开这 5 首五月天</div>
    <div class="ti-rule" id="tiR"></div>
  </div>
  <div class="grain"></div>
</div>'''

trans_html = f'''<div id="trans" class="layer">
  <div class="tr-wrap">
    <div class="tr-l" id="tr1">第一首，不是庆祝</div>
    <div class="tr-l" id="tr2">是你终于放下笔之后</div>
    <div class="tr-l accent" id="tr3">才听见自己的心跳</div>
  </div>
</div>'''

s1_html = f'''<video id="fv_s1" class="fv clip" data-start="{f(S1_T)}" data-duration="{f(S1_DUR)}" data-track-index="0" src="clips_seg/s1.mp4" muted playsinline></video>
<div id="tint_s1" class="clip tint" data-start="{f(S1_T)}" data-duration="{f(S1_DUR)}" data-track-index="10"></div>
<div id="tinttop_s1" class="clip tint-top" data-start="{f(S1_T)}" data-duration="{f(S1_DUR)}" data-track-index="11"></div>
<div id="chrome_s1" class="clip chrome" data-start="{f(S1_T)}" data-duration="{f(S1_DUR)}" data-track-index="12">
  <div class="card">
    <div class="card-no">01</div>
    <div class="card-name-row"><span class="card-name">知足</span><span class="card-emo">｜释然</span></div>
    <div class="card-credit">五月天 · 2005<br>《神的孩子都在跳舞》</div>
  </div>
  <div class="kw" id="kw_s1">空</div>
  <div class="subline" id="sub_s1">终于可以，不用再倒数了</div>
  <div class="src" id="src_s1">官方 MV · 滚石唱片</div>
</div>'''

audio_html = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ---------- JS timeline ----------
JS = f'''
// ===== COVER (0~{COVER_D}) 首帧静态 + 轻微动作 =====
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-text",{{opacity:1}},0);
tl.fromTo("#cover .ticket",{{rotate:-6,y:0}},{{rotate:-7.5,y:-6,duration:3.0,ease:"sine.inOut"}},0);
tl.fromTo("#cover .cv-sun",{{opacity:.85}},{{opacity:1,duration:2.6,yoyo:true,repeat:1,ease:"sine.inOut"}},0);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{f(COVER_D-0.3)});
tl.set("#cover",{{opacity:0}},{f(COVER_D+0.1)});

// ===== HOOK =====
tl.fromTo("#hook",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(COVER_D-0.4)});
tl.fromTo("#hkpaper",{{opacity:0,y:-40,rotate:-12}},{{opacity:.9,y:40,rotate:-4,duration:6,ease:"sine.inOut"}},{f(COVER_D)});
tl.fromTo("#hkpaper2",{{opacity:0,y:-30,rotate:9}},{{opacity:.85,y:50,rotate:2,duration:6.5,ease:"sine.inOut"}},{f(COVER_D+0.6)});
tl.fromTo("#hk1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{f(HOOK_VOICE_AT+0.3)});
tl.fromTo("#hk2",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{f(HOOK_VOICE_AT+4.0)});
tl.fromTo("#hk3",{{opacity:0,y:30}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{f(HOOK_VOICE_AT+7.6)});
tl.to("#hook",{{opacity:0,duration:.7,ease:"power2.in"}},{f(TITLE_T-0.2)});
tl.set("#hook",{{opacity:0}},{f(TITLE_T+0.3)});

// ===== TITLE =====
tl.fromTo("#title",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(TITLE_T-0.3)});
tl.fromTo("#tiE",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.6}},{f(TITLE_T+0.2)});
tl.fromTo("#tiL1",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(TITLE_T+0.5)});
tl.fromTo("#tiL2",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(TITLE_T+1.1)});
tl.fromTo("#tiR",{{width:0}},{{width:160,duration:.8,ease:"power2.out"}},{f(TITLE_T+1.8)});
tl.to("#title",{{opacity:0,duration:.7,ease:"power2.in"}},{f(TRANS_T-0.2)});
tl.set("#title",{{opacity:0}},{f(TRANS_T+0.3)});

// ===== TRANSITION =====
tl.fromTo("#trans",{{opacity:0}},{{opacity:1,duration:.6,ease:"power2.out"}},{f(TRANS_T-0.2)});
tl.fromTo("#tr1",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.7}},{f(TRANS_T+0.3)});
tl.fromTo("#tr2",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.7}},{f(TRANS_T+1.2)});
tl.fromTo("#tr3",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(TRANS_T+2.1)});
tl.to("#trans",{{opacity:0,duration:.8,ease:"power2.in"}},{f(S1_T+0.2)});
tl.set("#trans",{{opacity:0}},{f(S1_T+1.1)});

// ===== CHAPTER 知足 =====
const b={f(S1_T)};
tl.fromTo("#fv_s1",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:1.6,ease:"power2.out"}},b);
tl.to("#tint_s1",{{opacity:1,duration:1.4}},b);
tl.to("#tinttop_s1",{{opacity:1,duration:1.4}},b);
tl.fromTo(".card",{{opacity:0,x:50,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{f(S1_T+0.5)});
tl.fromTo("#src_s1",{{opacity:0}},{{opacity:1,duration:.6}},{f(S1_T+1.2)});
// 旁白结束→swell：卡片淡出，大字关键词浮起
tl.to(".card",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{f(S1_T+s1_sw0-0.1)});
tl.fromTo("#kw_s1",{{opacity:0,scale:.94}},{{opacity:.16,scale:1,duration:1.8,ease:"power3.out"}},{f(S1_T+s1_full-0.5)});
// 副歌中后段小标签
tl.fromTo("#sub_s1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(S1_T+s1_full+9)});
tl.to("#sub_s1",{{opacity:0,y:-12,duration:.7,ease:"power2.in"}},{f(S1_END-2.0)});
// 章节收尾淡出（hard kill）
tl.to("#fv_s1",{{opacity:0,duration:1.3,ease:"power1.in"}},{f(S1_END-1.4)});
tl.set("#fv_s1",{{opacity:0}},{f(S1_END)});
tl.to("#tint_s1",{{opacity:0,duration:1.3}},{f(S1_END-1.4)});
tl.set("#tint_s1",{{opacity:0}},{f(S1_END)});
tl.to("#tinttop_s1",{{opacity:0,duration:1.3}},{f(S1_END-1.4)});
tl.set("#tinttop_s1",{{opacity:0}},{f(S1_END)});
tl.to("#kw_s1",{{opacity:0,duration:1.2}},{f(S1_END-1.4)});
tl.set("#kw_s1",{{opacity:0}},{f(S1_END)});
tl.to("#src_s1",{{opacity:0,duration:.8}},{f(S1_END-1.4)});
tl.set("#src_s1",{{opacity:0}},{f(S1_END)});
'''

html = f'''<!doctype html>
<html lang="zh">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
  {s1_html}
  {cover_html}
  {hook_html}
  {title_html}
  {trans_html}
  {audio_html}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"] = tl;
</script>
</body>
</html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"wuyuetian-graduation-sample"}', encoding="utf-8")
print("index.html:", len(html), "bytes ; TOTAL", TOTAL)
print("SAMPLE BUILD DONE")
