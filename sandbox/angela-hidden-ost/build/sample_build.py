#!/usr/bin/env python3
"""样片构建：封面 + 开头悬念 + 第1首《不痛 / 你来自哪颗星》整段。
产物 master_sample.wav + hf/index.html。复古电视剧 OST 考古风。
- 音频：seg_open(cover+intro+trans1，不痛器乐低床+女声) + seg_s1(不痛连续铺底，voice 期 duck，副歌满量)。
  mseek 对齐使副歌(54.2s)正好落在 full0(展示满量起点)。
- 渲染后必须 mux master_sample.wav。
"""
import subprocess, wave, contextlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "audio"; C = ROOT / "clips"; HF = ROOT / "hf"
AUDIO_SONG = ROOT / "raw" / "s1_butong_audio.wav"   # 不痛 录音室全曲

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

NARR = {k: dur(A / f"{k}.wav") for k in ["intro", "trans1", "s1_voice"]}
print("NARR:", NARR)

# ---------------- 时间轴 ----------------
COVER_D    = 5.0
LEAD       = 0.3
PRE_VOICE  = 1.0
POST_VOICE = 1.2
SWELL      = 1.5
BED        = 0.20      # voice 期音乐床
HIGH       = 32.0      # 副歌展示
TAIL       = 2.2

intro_dur  = NARR["intro"]
trans1_dur = NARR["trans1"]
s1v        = NARR["s1_voice"]

# 场景绝对时间
cover_t0, cover_t1 = 0.0, COVER_D
intro_t0 = cover_t1
intro_seg = LEAD + intro_dur + POST_VOICE
intro_t1 = intro_t0 + intro_seg
trans1_t0 = intro_t1
trans1_seg = LEAD + trans1_dur + 0.8
trans1_t1 = trans1_t0 + trans1_seg
open_dur = trans1_t1                     # seg_open 总长 = cover+intro+trans1

s1_t0 = trans1_t1
# 段内锚点
v0 = LEAD + PRE_VOICE
v1 = v0 + s1v
sw0 = v1 + POST_VOICE
full0 = sw0 + SWELL
full1 = full0 + HIGH
s1_seg = full1 + TAIL
s1_t1 = s1_t0 + s1_seg

# mseek 让副歌(54.2)落在 full0
CHORUS = 54.2
mseek = round(CHORUS - full0, 2)
TOTAL = round(s1_t1, 3)
print(f"open_dur={open_dur:.2f} s1_seg={s1_seg:.2f} mseek={mseek} TOTAL={TOTAL:.2f} ({TOTAL//60:.0f}:{TOTAL%60:05.2f})")
print(f"  song-time @full0={mseek+full0:.1f} @full1={mseek+full1:.1f} (chorus block 54.2-94.3)")

# ---------------- 音频段 ----------------
SEG = ROOT / "build" / "segs"; SEG.mkdir(parents=True, exist_ok=True)

# seg_open: 不痛器乐低床[0:open_dur] + intro(延迟到 cover 后) + trans1
intro_at  = COVER_D + LEAD
trans1_at = intro_t1 + LEAD
run(["ffmpeg","-v","error",
     "-i", str(AUDIO_SONG), "-i", str(A/"intro.wav"), "-i", str(A/"trans1.wav"),
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(intro_at*1000)}|{int(intro_at*1000)},volume=2.0[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(trans1_at*1000)}|{int(trans1_at*1000)},volume=2.0[v2];"
     f"[v1][v2]amix=inputs=2:normalize=0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{open_dur},asetpts=PTS-STARTPTS,volume=0.17,afade=t=in:st=0:d=1.4,afade=t=out:st={open_dur-2.0}:d=2.0[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{open_dur},alimiter=level=disabled:limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000", str(SEG/"seg_open.wav"), "-y"])

# seg_s1: 不痛 从 mseek 连续铺底，床→swell→满量；voice 期 duck
ve = (f"(lt(t,{LEAD}))*0"
      f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
      f"+(between(t,{v0},{sw0}))*{BED}"
      f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
      f"+(gte(t,{full0}))*1.0")
run(["ffmpeg","-v","error",
     "-i", str(AUDIO_SONG), "-i", str(A/"s1_voice.wav"),
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim={mseek}:{mseek+s1_seg},asetpts=PTS-STARTPTS,"
     f"volume='{ve}':eval=frame,afade=t=out:st={full1}:d={s1_seg-full1}[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{s1_seg},alimiter=level=disabled:limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000", str(SEG/"seg_s1.wav"), "-y"])

# concat
(SEG/"list.txt").write_text("file 'seg_open.wav'\nfile 'seg_s1.wav'\n", encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(SEG/"list.txt"),
     "-ac","2","-ar","48000", str(ROOT/"master_sample.wav"), "-y"])
print("master dur:", dur(ROOT/"master_sample.wav"), "planned:", TOTAL)

# ---------------- 预切 footage ----------------
(HF/"clips_seg").mkdir(parents=True, exist_ok=True)
FOOT_SEEK = 2.0
run(["ffmpeg","-v","error","-ss",str(FOOT_SEEK),"-i",str(C/"vert_butong.mp4"),
     "-t",str(s1_seg+0.5),"-c:v","libx264","-preset","veryfast","-r","30","-g","30",
     "-keyint_min","30","-pix_fmt","yuv420p","-an", str(HF/"clips_seg"/"s1.mp4"), "-y"])
import shutil
shutil.copy(ROOT/"master_sample.wav", HF/"master.wav")
print("footage cut + master copied")

# ============================================================
# HTML
# ============================================================
GOLD="#D8A55A"; CREAM="#F2E6D2"; RED="#C2563B"; BG="#120D0A"

# 关键词标签（brief 画面字幕关键词）
S1_TAGS = ["明明很痛，却说不痛", "韩剧感拉满", "张韶涵早期 OST 隐藏大招"]
# 标签出现时间（绝对）：narration 中后段 + 展示段各一
tag_times = [s1_t0 + v0 + 3.0, s1_t0 + sw0 + 0.5, s1_t0 + full0 + 6.0]

cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="40">
  <div class="cv-frag cv-frag1"></div>
  <div class="cv-frag cv-frag2"></div>
  <div class="cv-frag cv-frag3"></div>
  <div class="cv-veil"></div>
  <div class="cv-scan"></div>
  <div class="cv-grain"></div>
  <div class="cv-tvtag">CH&nbsp;OST&nbsp;·&nbsp;典藏</div>
  <div class="cv-face-wrap"><div class="cv-face"></div><div class="cv-face-ring"></div></div>
  <div class="cv-title">
    <div class="cv-name">张韶涵</div>
    <div class="cv-sub">隐藏 OST 名场面</div>
  </div>
  <div class="cv-badge">这些歌你可能听过，<br>但未必知道出处</div>
  <div class="cv-vig"></div>
</div>'''

intro_html = f'''<div id="intro" class="clip scene" data-start="{fmt(intro_t0)}" data-duration="{fmt(intro_seg)}" data-track-index="41">
  <div class="sc-bg"></div>
  <div class="sc-scan"></div><div class="sc-grain"></div><div class="sc-vig"></div>
  <div class="in-kick">影视歌曲考古</div>
  <div class="in-line in-l1">片头 · 片尾 · 主题曲</div>
  <div class="in-line in-l2">有些歌，你听了很多年</div>
  <div class="in-line in-l3">却不知道，它来自哪部剧</div>
</div>'''

trans1_html = f'''<div id="trans1" class="clip scene" data-start="{fmt(trans1_t0)}" data-duration="{fmt(trans1_seg)}" data-track-index="42">
  <div class="sc-bg"></div>
  <div class="sc-scan"></div><div class="sc-grain"></div><div class="sc-vig"></div>
  <div class="tr-no">第 1 首</div>
  <div class="tr-line">听过副歌，<br>却未必知道它的出处</div>
  <div class="tr-rule"></div>
  <div class="tr-tvline"></div>
</div>'''

# song1 footage + tint + chrome
fv_html = (f'<video id="fv_s1" class="fv clip" data-start="{fmt(s1_t0)}" '
           f'data-duration="{fmt(s1_seg)}" data-track-index="0" src="clips_seg/s1.mp4" muted playsinline></video>')
tint_html = (f'<div id="tint_s1" class="clip tint" data-start="{fmt(s1_t0)}" '
             f'data-duration="{fmt(s1_seg)}" data-track-index="10"></div>')

chrome_html = f'''<div id="chrome_s1" class="clip chrome" data-start="{fmt(s1_t0)}" data-duration="{fmt(s1_seg)}" data-track-index="20">
  <!-- 标题卡 -->
  <div class="title-card" id="tcard">
    <div class="tc-no">OST · 01</div>
    <div class="tc-name">不痛</div>
    <div class="tc-drama">《你来自哪颗星》</div>
    <div class="tc-stamp">原来它也是 OST</div>
  </div>
  <!-- 常驻绑定标签（左下） -->
  <div class="bind" id="bind">
    <span class="bind-song">不痛</span>
    <span class="bind-sep">·</span>
    <span class="bind-drama">你来自哪颗星</span>
    <span class="bind-badge">片尾曲｜八大戲劇台</span>
  </div>
  <!-- 关键词标签 -->
  {''.join(f'<div class="kwtag" id="kw{i}">{t}</div>' for i,t in enumerate(S1_TAGS))}
</div>'''

# 全局复古叠层（footage 场景之上、文字层之上，低 opacity 不挡）
global_fx = '''<div class="gfx-scan"></div><div class="gfx-grain"></div><div class="gfx-vig"></div>'''

audio_html = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

CSS = f'''
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:{BG};
  font-family:"Noto Serif SC","Songti SC",serif;color:{CREAM};-webkit-font-smoothing:antialiased;}}
.clip{{position:absolute;inset:0;}}

/* ---- footage ---- */
.fv{{width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}}
.tint{{z-index:2;opacity:0;background:
  linear-gradient(180deg, rgba(40,22,10,.30) 0%, rgba(18,13,10,.30) 42%, rgba(8,5,3,.74) 100%);
  mix-blend-mode:multiply;}}
.chrome{{z-index:5;pointer-events:none;}}

/* ---- 全局复古 fx（z46，盖 footage+文字，低 opacity）---- */
.gfx-scan{{position:absolute;inset:0;z-index:46;pointer-events:none;opacity:.10;
  background:repeating-linear-gradient(0deg, rgba(0,0,0,.9) 0px, rgba(0,0,0,.9) 1px, transparent 1px, transparent 3px);}}
.gfx-grain{{position:absolute;inset:0;z-index:46;pointer-events:none;opacity:.06;mix-blend-mode:overlay;
  background-image:radial-gradient(circle at 12% 28%, #fff 0 .5px, transparent 1px),
    radial-gradient(circle at 67% 71%, #fff 0 .5px, transparent 1px),
    radial-gradient(circle at 39% 53%, #fff 0 .4px, transparent 1px),
    radial-gradient(circle at 85% 18%, #fff 0 .5px, transparent 1px);
  background-size:140px 140px,180px 180px,120px 120px,160px 160px;}}
.gfx-vig{{position:absolute;inset:0;z-index:45;pointer-events:none;
  background:radial-gradient(ellipse 75% 62% at 50% 46%, transparent 0%, transparent 55%, rgba(0,0,0,.55) 100%);}}

/* ---- 复古叠层局部用（cover/scene 自带）---- */
.sc-scan,.cv-scan{{position:absolute;inset:0;opacity:.10;pointer-events:none;
  background:repeating-linear-gradient(0deg, rgba(0,0,0,.9) 0 1px, transparent 1px 3px);}}
.sc-grain,.cv-grain{{position:absolute;inset:0;opacity:.07;mix-blend-mode:overlay;pointer-events:none;
  background-image:radial-gradient(circle at 20% 30%, #fff 0 .5px, transparent 1px),
    radial-gradient(circle at 75% 65%, #fff 0 .5px, transparent 1px);background-size:150px 150px,170px 170px;}}
.sc-vig,.cv-vig{{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 78% 64% at 50% 44%, transparent 0 56%, rgba(0,0,0,.6) 100%);}}

/* ================= 封面 ================= */
.cover{{z-index:50;background:radial-gradient(ellipse at 50% 38%, #25160d 0%, {BG} 72%);overflow:hidden;}}
.cv-frag{{position:absolute;background-size:cover;background-position:center;opacity:.34;filter:saturate(.55);}}
.cv-frag1{{left:-6%;top:4%;width:46%;height:30%;background-image:url("cover_assets/frag1.jpg");transform:rotate(-3deg);}}
.cv-frag2{{right:-7%;top:10%;width:48%;height:28%;background-image:url("cover_assets/frag2.jpg");transform:rotate(2.5deg);}}
.cv-frag3{{right:2%;bottom:8%;width:50%;height:26%;background-image:url("cover_assets/frag3.jpg");transform:rotate(-1.5deg);opacity:.26;}}
.cv-veil{{position:absolute;inset:0;background:linear-gradient(180deg, rgba(18,13,10,.55) 0%, rgba(18,13,10,.30) 34%, rgba(18,13,10,.55) 64%, rgba(10,6,3,.92) 100%);}}
.cv-tvtag{{position:absolute;top:96px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;
  font-size:30px;font-weight:700;letter-spacing:.42em;color:{GOLD};opacity:.85;}}
.cv-face-wrap{{position:absolute;top:330px;left:0;right:0;display:flex;justify-content:center;}}
.cv-face{{width:430px;height:430px;border-radius:50%;background-image:url("cover_assets/zsh_face.jpg");
  background-size:cover;background-position:center 22%;filter:saturate(.92) contrast(1.03) brightness(1.02);
  box-shadow:0 30px 90px rgba(0,0,0,.6), inset 0 0 0 1px rgba(255,255,255,.1);}}
.cv-face-ring{{position:absolute;top:-14px;left:50%;transform:translateX(-50%);width:458px;height:458px;border-radius:50%;
  border:3px solid rgba(216,165,90,.85);box-shadow:0 0 50px rgba(216,165,90,.3);}}
.cv-title{{position:absolute;top:830px;left:0;right:0;text-align:center;}}
.cv-name{{font-family:"Noto Serif SC",serif;font-size:158px;font-weight:800;letter-spacing:.06em;color:{CREAM};
  text-shadow:0 6px 30px rgba(0,0,0,.6);line-height:1.0;}}
.cv-sub{{font-family:"Noto Serif SC",serif;font-size:96px;font-weight:700;letter-spacing:.04em;margin-top:14px;
  color:{GOLD};text-shadow:0 4px 24px rgba(0,0,0,.5);}}
.cv-badge{{position:absolute;bottom:210px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;
  font-size:40px;font-weight:500;line-height:1.5;color:rgba(242,230,210,.82);letter-spacing:.04em;}}

/* ================= intro / trans 场景 ================= */
.scene{{z-index:41;background:{BG};overflow:hidden;}}
.sc-bg{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%, #251509 0%, {BG} 70%);}}
.in-kick{{position:absolute;top:560px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;
  font-size:34px;font-weight:700;letter-spacing:.5em;color:{GOLD};opacity:0;}}
.in-line{{position:absolute;left:80px;right:80px;text-align:center;font-family:"Noto Serif SC",serif;
  font-weight:700;color:{CREAM};opacity:0;}}
.in-l1{{top:760px;font-size:74px;color:{GOLD};letter-spacing:.06em;}}
.in-l2{{top:980px;font-size:58px;}}
.in-l3{{top:1110px;font-size:58px;}}
.tr-no{{position:absolute;top:720px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;
  font-size:46px;font-weight:700;letter-spacing:.4em;color:{RED};opacity:0;}}
.tr-line{{position:absolute;top:840px;left:90px;right:90px;text-align:center;font-family:"Noto Serif SC",serif;
  font-size:78px;font-weight:800;line-height:1.32;color:{CREAM};opacity:0;}}
.tr-rule{{position:absolute;top:1140px;left:50%;width:0;height:3px;background:{GOLD};transform:translateX(-50%);opacity:.9;}}
.tr-tvline{{position:absolute;left:0;right:0;top:50%;height:3px;background:rgba(242,230,210,.9);opacity:0;
  box-shadow:0 0 30px rgba(242,230,210,.8);}}

/* ================= 标题卡 / 绑定 / 关键词 ================= */
.title-card{{position:absolute;top:560px;left:80px;right:80px;text-align:center;opacity:0;}}
.tc-no{{font-family:"JetBrains Mono",monospace;font-size:36px;font-weight:700;letter-spacing:.46em;color:{GOLD};margin-bottom:26px;}}
.tc-name{{font-family:"Noto Serif SC",serif;font-size:172px;font-weight:800;line-height:1.0;color:{CREAM};
  text-shadow:0 8px 40px rgba(0,0,0,.7);}}
.tc-drama{{font-family:"Noto Serif SC",serif;font-size:64px;font-weight:600;color:rgba(242,230,210,.9);margin-top:18px;letter-spacing:.04em;}}
.tc-stamp{{display:inline-block;margin-top:34px;font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:700;
  color:{RED};border:3px solid {RED};border-radius:10px;padding:10px 28px;transform:rotate(-4deg);letter-spacing:.08em;
  box-shadow:0 6px 24px rgba(0,0,0,.4);}}
.bind{{position:absolute;left:64px;bottom:150px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;max-width:760px;opacity:0;}}
.bind-song{{font-family:"Noto Serif SC",serif;font-size:60px;font-weight:800;color:{CREAM};text-shadow:0 4px 18px rgba(0,0,0,.8);}}
.bind-sep{{font-size:46px;color:{GOLD};}}
.bind-drama{{font-family:"Noto Serif SC",serif;font-size:54px;font-weight:600;color:rgba(242,230,210,.92);text-shadow:0 4px 18px rgba(0,0,0,.8);}}
.bind-badge{{font-family:"Noto Sans SC",sans-serif;font-size:28px;font-weight:700;color:{GOLD};
  border:2px solid rgba(216,165,90,.7);border-radius:999px;padding:7px 20px;letter-spacing:.1em;
  background:rgba(18,13,10,.45);width:100%;text-align:left;max-width:max-content;}}
.kwtag{{position:absolute;left:64px;bottom:330px;font-family:"Noto Sans SC",sans-serif;font-size:50px;font-weight:800;
  color:{CREAM};padding:16px 30px;background:linear-gradient(90deg, rgba(194,86,59,.92), rgba(160,60,40,.6));
  border-left:6px solid {GOLD};border-radius:6px;letter-spacing:.03em;opacity:0;
  text-shadow:0 3px 14px rgba(0,0,0,.6);box-shadow:0 10px 36px rgba(0,0,0,.5);}}
'''

def js():
    L = []
    # 封面（首帧即在，不 fade-in）
    L.append(f'tl.set("#cover",{{opacity:1}},0);')
    L.append(f'tl.set(".cv-tvtag,.cv-face-wrap,.cv-title,.cv-badge",{{opacity:1}},0);')
    L.append(f'tl.to(".cv-face",{{scale:1.03,duration:3.4,ease:"sine.inOut",yoyo:true,repeat:1}},1.0);')
    L.append(f'tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D-0.55)});')
    L.append(f'tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});')
    # intro 文字逐行
    base = intro_t0 + LEAD
    L.append(f'tl.set("#intro",{{opacity:1}},{fmt(intro_t0)});')
    L.append(f'tl.fromTo(".in-kick",{{opacity:0,y:18}},{{opacity:.9,y:0,duration:.7,ease:"power2.out"}},{fmt(base+0.2)});')
    L.append(f'tl.fromTo(".in-l1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(base+2.0)});')
    L.append(f'tl.fromTo(".in-l2",{{opacity:0,y:24}},{{opacity:.96,y:0,duration:.7,ease:"power2.out"}},{fmt(base+9.0)});')
    L.append(f'tl.fromTo(".in-l3",{{opacity:0,y:24}},{{opacity:.96,y:0,duration:.7,ease:"power2.out"}},{fmt(base+13.5)});')
    L.append(f'tl.to("#intro",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(intro_t1-0.5)});')
    L.append(f'tl.set("#intro",{{opacity:0}},{fmt(intro_t1)});')
    # trans1
    tb = trans1_t0 + LEAD
    L.append(f'tl.set("#trans1",{{opacity:1}},{fmt(trans1_t0)});')
    L.append(f'tl.fromTo(".tr-no",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.5,ease:"power2.out"}},{fmt(tb)});')
    L.append(f'tl.fromTo(".tr-line",{{opacity:0,y:22}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{fmt(tb+0.6)});')
    L.append(f'tl.fromTo(".tr-rule",{{width:0}},{{width:280,duration:.9,ease:"power2.out"}},{fmt(tb+1.2)});')
    # 关机白线收束转场
    L.append(f'tl.fromTo(".tr-tvline",{{opacity:0,scaleY:1}},{{opacity:1,duration:.18}},{fmt(trans1_t1-0.55)});')
    L.append(f'tl.to("#trans1 .tr-no,#trans1 .tr-line,#trans1 .tr-rule",{{opacity:0,duration:.2}},{fmt(trans1_t1-0.5)});')
    L.append(f'tl.to(".tr-tvline",{{scaleY:60,opacity:0,duration:.33,ease:"power2.in",overwrite:"auto"}},{fmt(trans1_t1-0.33)});')
    L.append(f'tl.set(".tr-tvline",{{opacity:0}},{fmt(trans1_t1)});')
    L.append(f'tl.to("#trans1",{{opacity:0,duration:.2}},{fmt(trans1_t1-0.1)});')
    L.append(f'tl.set("#trans1",{{opacity:0}},{fmt(trans1_t1)});')
    # song1 footage
    L.append(f'tl.fromTo("#fv_s1",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:1.2,ease:"power2.out"}},{fmt(s1_t0)});')
    L.append(f'tl.to("#tint_s1",{{opacity:1,duration:1.0}},{fmt(s1_t0)});')
    # 标题卡：出现→narration 前淡出
    L.append(f'tl.fromTo("#tcard",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{fmt(s1_t0+0.5)});')
    L.append(f'tl.to("#tcard",{{opacity:0,y:-20,duration:.6,ease:"power2.in"}},{fmt(s1_t0+v0+0.2)});')
    # 绑定标签：narration 起常驻
    L.append(f'tl.fromTo("#bind",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.7,ease:"power2.out"}},{fmt(s1_t0+v0+0.6)});')
    # 关键词标签 轮换
    for i,tt in enumerate(tag_times):
        nxt = tag_times[i+1] if i+1 < len(tag_times) else s1_t1-1.0
        L.append(f'tl.fromTo("#kw{i}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{fmt(tt)});')
        L.append(f'tl.to("#kw{i}",{{opacity:0,x:14,duration:.45,ease:"power2.in"}},{fmt(min(nxt-0.2, s1_t1-0.8))});')
    # 收尾淡出（hard kill）
    fo = s1_t1 - 1.4
    for sel in ['#fv_s1','#tint_s1','#bind']:
        L.append(f'tl.to("{sel}",{{opacity:0,duration:1.2,ease:"power1.in"}},{fmt(fo)});')
        L.append(f'tl.set("{sel}",{{opacity:0}},{fmt(s1_t1)});')
    return "\n    ".join(L)

html = f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
    {fv_html}
    {tint_html}
    {chrome_html}
    {global_fx}
    {trans1_html}
    {intro_html}
    {cover_html}
    {audio_html}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{paused:true}});
    {js()}
    window.__timelines["main"] = tl;
  </script>
</body></html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"angela-hidden-ost-sample"}', encoding="utf-8")
print("index.html:", len(html), "bytes ·  TOTAL", TOTAL, "s")
