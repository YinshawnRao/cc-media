#!/usr/bin/env python3
"""样片：封面(设计) + 开场蒙太奇钩子 + Part1 动力火车《彩虹》。
验证：彩虹设计语言 / 节奏 / 男声配音 / 悬念(不泄漏歌单)。
渲染后 ffmpeg mux master_sample.wav。"""
import subprocess, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import os
os.chdir(ROOT)
A = "audio"; C = "clips"
def run(c): subprocess.run(c, check=True)
NARR = json.loads(Path("narration.json").read_text())
Vi = NARR["intro"]["dur"]; Vs1 = NARR["s1"]["dur"]

# ---------- 时间轴 ----------
COVER_D = 5.0
HOOK_VOICE_AT = COVER_D + 0.8
OPEN_END = round(HOOK_VOICE_AT + Vi + 1.6, 3)          # 钩子结束(消化位)
LEAD, PRE, POST, SWELL, TAIL = 0.2, 0.8, 1.2, 1.5, 1.2
BED = 0.20
SHOW = 30.0
v0 = LEAD + PRE
v1 = v0 + Vs1
sw0 = v1 + POST
full0 = sw0 + SWELL
full1 = full0 + SHOW
S1_LEN = round(full1 + TAIL, 3)
S1_START = OPEN_END
TOTAL = round(S1_START + S1_LEN + 0.8, 3)
print(f"OPEN_END={OPEN_END} S1_START={S1_START} S1_LEN={S1_LEN} TOTAL={TOTAL} ({TOTAL//60:.0f}:{TOTAL%60:05.2f})")

MSEEK = 0.0   # vert_p1 local 起点 (abs 0:50)；full-show 落在 abs ~1:06-1:36 副歌区

# ============ 音频 ============
Path("build/segs").mkdir(parents=True, exist_ok=True)

# seg_open: 低通器乐床(p1, 神秘化) + intro 旁白
run(["ffmpeg","-v","error","-i",f"{C}/vert_p1.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(HOOK_VOICE_AT*1000)}|{int(HOOK_VOICE_AT*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{OPEN_END},asetpts=PTS-STARTPTS,"
     f"lowpass=f=620,volume=0.17,afade=t=in:st=0:d=1.2,afade=t=out:st={OPEN_END-1.4}:d=1.4[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OPEN_END},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000","build/segs/seg_open.wav","-y"])

# seg_s1: 床→swell→展示 副歌
ve = (f"(lt(t,{LEAD}))*0"
      f"+(between(t,{LEAD},{v0}))*({BED}*(t-{LEAD})/{v0-LEAD})"
      f"+(between(t,{v0},{sw0}))*{BED}"
      f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
      f"+(gte(t,{full0}))*1.0")
run(["ffmpeg","-v","error","-i",f"{C}/vert_p1.mp4","-i",f"{A}/s1.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(v0*1000)}|{int(v0*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={MSEEK}:{MSEEK+S1_LEN},asetpts=PTS-STARTPTS,"
     f"volume='{ve}':eval=frame,afade=t=out:st={full1}:d={S1_LEN-full1}[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{S1_LEN},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000","build/segs/seg_s1.wav","-y"])

# concat + 末尾静默补到 TOTAL
Path("build/segs/list.txt").write_text("file 'seg_open.wav'\nfile 'seg_s1.wav'\n",encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/list.txt","-ac","2","-ar","48000","build/segs/_cat.wav","-y"])
run(["ffmpeg","-v","error","-i","build/segs/_cat.wav","-af",f"apad=whole_dur={TOTAL}","-ac","2","-ar","48000","hf/master_sample.wav","-y"])
def adur(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).strip())
print("master_sample dur:", round(adur("hf/master_sample.wav"),2), "planned", TOTAL)

# 预切 Part1 footage (HF 控不了 currentTime)
Path("hf/clips_seg").mkdir(parents=True, exist_ok=True)
run(["ffmpeg","-v","error","-ss",str(MSEEK),"-i",f"{C}/vert_p1.mp4","-t",str(S1_LEN),
     "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an","hf/clips_seg/p1.mp4","-y"])
print("clips_seg/p1.mp4 cut")

# ============ HTML ============
def f(x): return f"{round(x,3)}"
# Part1 绝对锚点
b = S1_START
a = dict(start=b, v0=b+v0, v1=b+v1, sw0=b+sw0, full0=b+full0, full1=b+full1, end=b+S1_LEN)
mid0 = a["full1"] - 6.0  # 中段金句在展示后半段

CSS = r'''
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06080F;color:#F4EFE7;
 font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased}
.clip{position:absolute}
:root{--rb:linear-gradient(90deg,#d9665f 0%,#dd9a52 17%,#d8c85a 33%,#69bd84 52%,#5ea6c9 69%,#7d7ec9 85%,#c77bb1 100%);}

/* ===== 通用底纹 ===== */
.vign{position:absolute;inset:0;background:radial-gradient(ellipse 70% 55% at 50% 46%,rgba(40,44,60,.40)0,rgba(6,8,15,.0)55%),
 radial-gradient(ellipse 120% 90% at 50% 120%,rgba(0,0,0,.85)0,transparent 60%);z-index:2}
.grain{position:absolute;inset:0;z-index:3;opacity:.5;mix-blend-mode:overlay;
 background-image:radial-gradient(circle at 12% 28%,rgba(255,255,255,.05)0 .5px,transparent .9px),
 radial-gradient(circle at 78% 66%,rgba(255,255,255,.05)0 .5px,transparent .9px),
 radial-gradient(circle at 46% 84%,rgba(255,255,255,.04)0 .4px,transparent .8px);background-size:200px 200px,260px 260px,180px 180px}

/* ===== COVER ===== */
#cover{inset:0;z-index:60;background:#06080F;overflow:hidden}
.cv-disc{position:absolute;left:50%;top:610px;width:780px;height:780px;transform:translate(-50%,-50%);border-radius:50%;
 background:
  repeating-radial-gradient(circle at 50% 50%,rgba(255,255,255,.022)0 2px,transparent 2px 6px),
  radial-gradient(circle at 50% 50%,#15131c 0 27%,#0c0a12 27% 30%,#141019 30% 100%);
 box-shadow:0 40px 120px rgba(0,0,0,.7),inset 0 0 60px rgba(0,0,0,.8);z-index:5}
.cv-disc::after{content:"";position:absolute;left:50%;top:50%;width:150px;height:150px;transform:translate(-50%,-50%);border-radius:50%;
 background:radial-gradient(circle at 42% 40%,#3a3550,#16121f 70%);box-shadow:inset 0 0 0 2px rgba(255,255,255,.06)}
.cv-sheen{position:absolute;left:50%;top:610px;width:880px;height:300px;transform:translate(-50%,-50%) rotate(-16deg);
 background:var(--rb);filter:blur(46px);opacity:.55;mix-blend-mode:screen;border-radius:50%;z-index:6}
.cv-hero{position:absolute;left:0;right:0;top:430px;text-align:center;z-index:8;
 font-weight:900;font-size:316px;letter-spacing:.04em;line-height:1;
 background:var(--rb);-webkit-background-clip:text;background-clip:text;color:transparent;
 filter:drop-shadow(0 6px 40px rgba(120,140,200,.35)) drop-shadow(0 0 4px rgba(255,255,255,.25))}
.cv-eyebrow{position:absolute;top:188px;left:0;right:0;text-align:center;z-index:8;
 font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;letter-spacing:.46em;color:#C9A86A}
.cv-eyebrow .bar{display:inline-block;width:54px;height:1px;background:#C9A86A;vertical-align:middle;margin:0 18px;opacity:.7}
.cv-paper{position:absolute;left:62px;top:1108px;width:520px;height:300px;transform:rotate(-4deg);z-index:7;opacity:.9;
 background:linear-gradient(180deg,rgba(244,239,231,.10),rgba(244,239,231,.04));border:1px solid rgba(244,239,231,.10);border-radius:10px;
 box-shadow:0 24px 60px rgba(0,0,0,.5);
 background-image:repeating-linear-gradient(180deg,transparent 0 38px,rgba(244,239,231,.07)38px 39px)}
.cv-title{position:absolute;left:70px;right:70px;top:1180px;z-index:9}
.cv-t1{font-size:104px;font-weight:900;line-height:1.08;color:#F4EFE7;letter-spacing:-1px}
.cv-t1 .n{font-family:"JetBrains Mono",monospace;font-weight:800;
 background:var(--rb);-webkit-background-clip:text;background-clip:text;color:transparent;padding-right:6px}
.cv-t2{font-size:92px;font-weight:800;line-height:1.12;color:#F4EFE7;margin-top:6px}
.cv-sub{position:absolute;left:72px;right:72px;top:1560px;z-index:9;
 font-size:46px;font-weight:500;color:rgba(244,239,231,.62);letter-spacing:.02em}
.cv-rule{position:absolute;left:72px;right:72px;top:1700px;height:4px;border-radius:4px;z-index:9;
 background:var(--rb);opacity:.85;filter:saturate(.85)}
.cv-foot{position:absolute;left:0;right:0;top:1748px;text-align:center;z-index:9;
 font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:600;letter-spacing:.3em;color:rgba(244,239,231,.4)}

/* ===== HOOK 蒙太奇 ===== */
#hook{inset:0;z-index:55;background:radial-gradient(ellipse at 50% 30%,#0c1020 0,#06080F 70%);overflow:hidden}
.hk-glow{position:absolute;border-radius:50%;filter:blur(60px);mix-blend-mode:screen;opacity:0}
.hk-g1{left:-160px;top:300px;width:620px;height:620px;background:radial-gradient(circle,rgba(217,150,82,.5),transparent 70%)}
.hk-g2{right:-180px;top:780px;width:680px;height:680px;background:radial-gradient(circle,rgba(94,166,201,.5),transparent 70%)}
.hk-g3{left:240px;top:1180px;width:560px;height:560px;background:radial-gradient(circle,rgba(125,126,201,.45),transparent 70%)}
.hk-band{position:absolute;left:-12%;width:124%;height:130px;background:var(--rb);filter:blur(30px);mix-blend-mode:screen;opacity:0}
.hk-b1{top:520px;transform:rotate(-9deg)}
.hk-b2{top:980px;transform:rotate(7deg)}
.hk-rain{position:absolute;inset:-10% 0;z-index:4;opacity:0;mix-blend-mode:screen;
 background-image:repeating-linear-gradient(74deg,transparent 0 26px,rgba(180,200,230,.16)26px 27px,transparent 27px 60px);background-size:auto 100%}
.hk-disc{position:absolute;left:50%;top:760px;width:300px;height:300px;transform:translate(-50%,-50%);border-radius:50%;z-index:6;opacity:0;
 background:repeating-radial-gradient(circle at 50% 50%,rgba(255,255,255,.05)0 1.5px,transparent 1.5px 5px),radial-gradient(circle,#15131c 0 30%,#0e0b14 100%);
 box-shadow:0 20px 60px rgba(0,0,0,.6)}
.hk-frag{position:absolute;font-family:"Noto Serif SC",serif;color:rgba(244,239,231,.16);z-index:7;opacity:0;white-space:nowrap}
.hk-f1{left:80px;top:430px;font-size:40px;transform:rotate(-3deg)}
.hk-f2{right:70px;top:680px;font-size:34px}
.hk-f3{left:120px;top:1320px;font-size:36px;transform:rotate(2deg)}
.hk-text{position:absolute;left:80px;right:80px;z-index:9;text-align:center;opacity:0}
#hkt1{top:820px;font-size:78px;font-weight:900;color:#F4EFE7;letter-spacing:.02em}
#hkt1 b{background:var(--rb);-webkit-background-clip:text;background-clip:text;color:transparent}
#hkt2{top:1010px;font-size:46px;font-weight:500;line-height:1.45;color:rgba(244,239,231,.82)}

/* ===== PART 1 footage 章节 ===== */
.fv{inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0}
.tint{inset:0;z-index:2;opacity:0;background:
 linear-gradient(180deg,rgba(217,120,60,.16)0%,rgba(20,10,6,.0)26%,rgba(6,5,8,.34)64%,rgba(0,0,0,.82)100%)}
.p1{--pri:#E8954E;--acc:#F0C98A}
.rail{position:absolute;top:300px;left:60px;height:560px;width:10px;z-index:5;opacity:0}
.rail-bar{position:absolute;top:0;bottom:0;left:4px;width:2px;background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.20),rgba(255,255,255,.04))}
.rail-dot{position:absolute;left:-20px;width:46px;height:46px;border-radius:50%;background:rgba(18,16,24,.9);border:2px solid rgba(255,255,255,.20);display:flex;align-items:center;justify-content:center}
.rail-dot .t{font-family:"JetBrains Mono",monospace;font-size:22px;font-weight:800;color:rgba(255,255,255,.6)}
.rail-dot.on{background:var(--pri);border-color:var(--pri);box-shadow:0 0 28px var(--pri);transform:scale(1.18)}
.rail-dot.on .t{color:#140e08}
.card{position:absolute;top:250px;right:54px;width:600px;padding:42px 44px;border-radius:24px;z-index:6;opacity:0;
 background:linear-gradient(160deg,rgba(255,255,255,.11),rgba(255,255,255,.03));backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);
 border:1.5px solid rgba(255,255,255,.18);box-shadow:0 32px 90px rgba(0,0,0,.6)}
.card-no{font-family:"JetBrains Mono",monospace;font-size:34px;font-weight:800;letter-spacing:.3em;color:var(--pri);margin-bottom:18px}
.card-art{font-size:76px;font-weight:900;line-height:1.04;color:#F4EFE7;letter-spacing:-1px}
.card-song{font-size:44px;font-weight:700;color:rgba(244,239,231,.9);margin-top:8px}
.card-song i{font-style:normal;color:var(--acc)}
.card-tag{margin-top:26px;font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;color:var(--acc);display:flex;align-items:center;gap:14px}
.card-tag .d{width:12px;height:12px;border-radius:50%;background:var(--pri);box-shadow:0 0 16px var(--pri)}
.lead{position:absolute;left:70px;right:70px;top:1430px;z-index:6;opacity:0;
 font-size:54px;font-weight:800;line-height:1.28;color:#F4EFE7;text-shadow:0 4px 30px rgba(0,0,0,.7)}
.lead .hl{background:var(--rb);-webkit-background-clip:text;background-clip:text;color:transparent}
.kw{position:absolute;left:0;right:0;top:560px;text-align:center;z-index:4;opacity:0;
 font-size:300px;font-weight:900;line-height:.9;color:var(--pri);mix-blend-mode:screen;letter-spacing:-6px;
 filter:drop-shadow(0 8px 60px rgba(232,149,78,.3))}
.mid{position:absolute;left:80px;right:80px;top:1480px;z-index:6;opacity:0;text-align:center;
 font-size:52px;font-weight:600;line-height:1.4;color:#F8F2EA;text-shadow:0 4px 24px rgba(0,0,0,.8)}
.src{position:absolute;bottom:52px;left:0;right:0;text-align:center;z-index:6;opacity:0;
 font-family:"Noto Sans SC",sans-serif;font-size:22px;font-weight:500;letter-spacing:.28em;color:rgba(244,239,231,.4)}
'''

cover = f'''<div id="cover" class="clip" data-start="0" data-duration="{f(COVER_D)}" data-track-index="40">
  <div class="cv-sheen"></div><div class="cv-disc"></div>
  <div class="vign"></div><div class="grain"></div>
  <div class="cv-eyebrow"><span class="bar"></span>华语乐坛 · 同名歌曲盘点<span class="bar"></span></div>
  <div class="cv-hero">彩虹</div>
  <div class="cv-paper"></div>
  <div class="cv-title"><div class="cv-t1"><span class="n">5</span>首《彩虹》，</div><div class="cv-t2">你先想到谁？</div></div>
  <div class="cv-sub">同名歌曲，差别太大了。</div>
  <div class="cv-rule"></div>
  <div class="cv-foot">同一个歌名 · 不同的人生</div>
</div>'''

hook = f'''<div id="hook" class="clip" data-start="{f(COVER_D)}" data-duration="{f(OPEN_END-COVER_D)}" data-track-index="41">
  <div class="hk-glow hk-g1"></div><div class="hk-glow hk-g2"></div><div class="hk-glow hk-g3"></div>
  <div class="hk-band hk-b1"></div><div class="hk-band hk-b2"></div>
  <div class="hk-rain"></div><div class="hk-disc"></div>
  <div class="hk-frag hk-f1">雨後的天空</div><div class="hk-frag hk-f2">藍綠黃紅</div><div class="hk-frag hk-f3">哪裡有彩虹</div>
  <div class="vign"></div><div class="grain"></div>
  <div class="hk-text" id="hkt1">同样叫<b>《彩虹》</b></div>
  <div class="hk-text" id="hkt2">唱出来的，<br>却完全不是同一种人生。</div>
</div>'''

part1 = f'''<video id="fv1" class="fv clip p1" data-start="{f(a["start"])}" data-duration="{f(S1_LEN)}" data-track-index="0" src="clips_seg/p1.mp4" muted playsinline></video>
<div id="tint1" class="tint clip p1" data-start="{f(a["start"])}" data-duration="{f(S1_LEN)}" data-track-index="10"></div>
<div id="chrome1" class="clip p1" data-start="{f(a["start"])}" data-duration="{f(S1_LEN)}" data-track-index="20" style="position:absolute;inset:0;z-index:5;pointer-events:none">
  <div class="rail">
    <div class="rail-bar"></div>
    {''.join(f'<div class="rail-dot{(" on" if i==0 else "")}" style="top:{i*120}px"><span class="t">{i+1}</span></div>' for i in range(5))}
  </div>
  <div class="card">
    <div class="card-no">PART 01</div>
    <div class="card-art">动力火车</div>
    <div class="card-song">《<i>彩虹</i>》</div>
    <div class="card-tag"><span class="d"></span>热血 · 不认输</div>
  </div>
  <div class="lead">这一道彩虹，<br>是<span class="hl">热血</span>和不认输。</div>
  <div class="kw" id="kw1">热血</div>
  <div class="mid" id="mid1">人在泥里，<br>也要把自己唱起来。</div>
  <div class="src" id="src1">动力火车《彩虹》 · 官方 MV</div>
</div>'''

audio_el = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master_sample.wav" data-volume="1"></audio>'

JS = f'''
// ===== COVER (首帧=封面, opacity 1 起) =====
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-disc, .cv-sheen, .cv-hero, .cv-eyebrow, .cv-paper, .cv-title, .cv-sub, .cv-rule, .cv-foot",{{opacity:1}},0);
tl.to(".cv-sheen",{{rotation:-12, duration:4, ease:"sine.inOut"}},0.4);
tl.to(".cv-hero",{{scale:1.02, duration:3.4, yoyo:true, repeat:1, ease:"sine.inOut", transformOrigin:"50% 50%"}},0.6);
tl.to("#cover",{{opacity:0,duration:.7,ease:"power2.in"}},{f(COVER_D-0.7)});
tl.set("#cover",{{opacity:0}},{f(COVER_D)});

// ===== HOOK =====
tl.set("#hook",{{opacity:1}},{f(COVER_D)});
tl.to(".hk-glow",{{opacity:.85,duration:1.4,stagger:.35,ease:"sine.out"}},{f(COVER_D+0.1)});
tl.to(".hk-g1",{{x:120,y:-40,duration:9,ease:"sine.inOut"}},{f(COVER_D)});
tl.to(".hk-g2",{{x:-100,y:40,duration:9,ease:"sine.inOut"}},{f(COVER_D)});
tl.to(".hk-band",{{opacity:.55,duration:1.6,stagger:.3,ease:"sine.out"}},{f(COVER_D+0.4)});
tl.to(".hk-b1",{{x:80,duration:8,ease:"none"}},{f(COVER_D)});
tl.to(".hk-b2",{{x:-80,duration:8,ease:"none"}},{f(COVER_D)});
tl.to(".hk-rain",{{opacity:1,duration:1.2}},{f(COVER_D+0.6)});
tl.fromTo(".hk-rain",{{backgroundPositionY:"0px"}},{{backgroundPositionY:"600px",duration:{f(OPEN_END-COVER_D)},ease:"none"}},{f(COVER_D)});
tl.fromTo(".hk-disc",{{opacity:0,rotation:0}},{{opacity:.6,rotation:120,duration:{f(OPEN_END-COVER_D)},ease:"none"}},{f(COVER_D+0.4)});
tl.to(".hk-frag",{{opacity:1,duration:1.6,stagger:.5,ease:"sine.out"}},{f(COVER_D+0.8)});
// 两行屏幕文字
tl.fromTo("#hkt1",{{opacity:0,y:24,scale:.96}},{{opacity:1,y:0,scale:1,duration:.9,ease:"power3.out"}},{f(COVER_D+1.2)});
tl.fromTo("#hkt2",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(COVER_D+4.6)});
tl.to("#hook",{{opacity:0,duration:.8,ease:"power2.in"}},{f(OPEN_END-0.8)});
tl.set("#hook",{{opacity:0}},{f(OPEN_END)});

// ===== PART 1 =====
tl.fromTo("#fv1",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:1.6,ease:"power2.out"}},{f(a["start"])});
tl.to("#tint1",{{opacity:1,duration:1.4}},{f(a["start"])});
tl.fromTo(".p1 .rail",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:.8,ease:"power2.out"}},{f(a["start"]+0.4)});
tl.fromTo(".p1 .card",{{opacity:0,x:60,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{f(a["start"]+0.6)});
tl.fromTo(".p1 .lead",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(a["v0"]+0.4)});
tl.fromTo("#src1",{{opacity:0}},{{opacity:1,duration:.6}},{f(a["start"]+1.4)});
// 旁白收尾 → 卡片/铺垫淡出，进入展示
tl.to(".p1 .card",{{opacity:0,y:-12,duration:.5,ease:"power2.in"}},{f(a["sw0"]-0.1)});
tl.to(".p1 .lead",{{opacity:0,y:-12,duration:.5,ease:"power2.in"}},{f(a["sw0"]-0.1)});
tl.fromTo("#kw1",{{opacity:0,scale:.9}},{{opacity:.3,scale:1,duration:1.6,ease:"power3.out"}},{f(a["full0"]-0.4)});
tl.fromTo("#mid1",{{opacity:0,y:26}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(mid0)});
tl.to("#mid1",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{f(a["end"]-1.4)});
tl.to("#kw1",{{opacity:0,duration:1.0,ease:"power1.in"}},{f(a["end"]-1.4)});
// 章节收尾 hard kill
tl.to("#fv1",{{opacity:0,duration:1.0,ease:"power1.in"}},{f(a["end"]-1.0)});
tl.set("#fv1",{{opacity:0}},{f(a["end"])});
tl.to("#tint1",{{opacity:0,duration:1.0}},{f(a["end"]-1.0)});
tl.set("#tint1",{{opacity:0}},{f(a["end"])});
tl.to(".p1 .rail, #src1",{{opacity:0,duration:.6}},{f(a["end"]-0.6)});
tl.set(".p1 .rail, #src1",{{opacity:0}},{f(a["end"])});
'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@600;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
{part1}
{cover}
{hook}
{audio_el}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script></body></html>'''

Path("hf/index.html").write_text(html, encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"caihong-tongming-sample"}', encoding="utf-8")
# hf 项目文件
Path("hf/package.json").write_text(json.dumps({"name":"hf","private":True,"type":"module","scripts":{
  "dev":"npx --yes hyperframes@0.6.47 preview","check":"npx --yes hyperframes@0.6.47 lint",
  "render":"npx --yes hyperframes@0.6.47 render"}},indent=2),encoding="utf-8")
print("index.html written", len(html), "bytes")
print("DONE sample build")
