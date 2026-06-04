#!/usr/bin/env python3
"""样片构建：封面 + 开场钩子 + 第8首《最爱的人伤我最深》+ 样片尾卡。
验证：男声配音 / 节奏 ducking / letterbox / 封面 / 章节设计 / 屏幕文字 / 字体 / 金黑红配色。
渲染后必须 ffmpeg mux master_pilot.wav（HyperFrames 会压平音频动态）。
音乐统一用 s8_yt.webm（最爱的人 录音室对唱）。s8 footage 与音乐解耦（蒙太奇）。
"""
import subprocess, wave, contextlib, json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
A = BASE / "audio"
C = BASE / "clips"
HF = BASE / "hf"
RAW = BASE / "raw"
SEG = BASE / "build" / "segs"
SEG.mkdir(parents=True, exist_ok=True)
MUSIC = str(RAW / "s8_yt.webm")   # 最爱的人 录音室对唱（音乐源）

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

# ---- narration durations ----
NARR = {k: dur(A / f"{k}.wav") for k in ["intro", "s8_voice", "s8_trans"]}
print("NARR:", NARR)

# ============ 节奏常量 ============
LEAD = 0.15; PRE = 0.8; POST = 1.2; SWELL = 1.5
BED = 0.20; DUCK = 0.34            # voice 期 / trans 期 音乐床
HIGH_S8 = 26.5                     # 副歌展示（= s8 蒙太奇时长 ~26.67）
COVER_D = 4.5
HOOK_TAIL = 3.0
END_D = 5.0

# ============ 段时长 ============
hook_seg = LEAD + NARR["intro"] + HOOK_TAIL
s8_v = NARR["s8_voice"]; s8_t = NARR["s8_trans"]
s8_seg = LEAD + PRE + s8_v + POST + SWELL + HIGH_S8 + s8_t + 1.0

# 绝对起点
t = 0.0
S = {}
S["cover"] = (t, COVER_D); t += COVER_D
S["hook"]  = (t, hook_seg); t += hook_seg
S["s8"]    = (t, s8_seg); t += s8_seg
S["end"]   = (t, END_D); t += END_D
TOTAL = round(t, 3)
print(f"TOTAL pilot = {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# s8 内部锚点（相对 s8 段起点）
s8_v0 = LEAD + PRE
s8_v1 = s8_v0 + s8_v
s8_sw0 = s8_v1 + POST
s8_full0 = s8_sw0 + SWELL
s8_full1 = s8_full0 + HIGH_S8
s8_tr0 = s8_full1
s8_tr1 = s8_tr0 + s8_t
s8_end = s8_seg
MSEEK = 90.0 - s8_full0   # 让副歌展示对齐到 90s 的合唱副歌

# ============ 音频段构建 ============
def mk_bed(out, mseek, length, vol, fin, fout, fout_d):
    """单纯音乐床（无旁白）。"""
    run(["ffmpeg","-v","error","-i",MUSIC,"-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim={mseek}:{mseek+length},asetpts=PTS-STARTPTS,volume={vol},"
         f"afade=t=in:st=0:d={fin},afade=t=out:st={length-fout_d}:d={fout_d},"
         f"atrim=0:{length},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",str(out),"-y"])

# cover：低音乐床淡入
mk_bed(SEG/"seg_cover.wav", 28.0, COVER_D, 0.16, 1.0, 0.6, 0.6)

# hook：intro 旁白 + 低音乐床
voice_at = LEAD + 0.3
run(["ffmpeg","-v","error","-i",MUSIC,"-i",str(A/"intro.wav"),"-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=32.5:{32.5+hook_seg},asetpts=PTS-STARTPTS,volume=0.18,"
     f"afade=t=in:st=0:d=1.0,afade=t=out:st={hook_seg-1.5}:d=1.5[m];"
     f"[v][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{hook_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",str(SEG/"seg_hook.wav"),"-y"])

# s8：voice 床 → swell → 副歌全量 → trans duck → fade
ve = (f"(lt(t,{LEAD}))*0"
      f"+(between(t,{LEAD},{s8_v0}))*({BED}*(t-{LEAD})/{s8_v0-LEAD})"
      f"+(between(t,{s8_v0},{s8_sw0}))*{BED}"
      f"+(between(t,{s8_sw0},{s8_full0}))*({BED}+{1.0-BED}*(t-{s8_sw0})/{SWELL})"
      f"+(between(t,{s8_full0},{s8_full1}))*1.0"
      f"+(between(t,{s8_full1},{s8_full1+0.5}))*(1.0-{1.0-DUCK}*(t-{s8_full1})/0.5)"
      f"+(between(t,{s8_full1+0.5},{s8_tr1}))*{DUCK}"
      f"+(gte(t,{s8_tr1}))*{DUCK}")
run(["ffmpeg","-v","error","-i",MUSIC,"-i",str(A/"s8_voice.wav"),"-i",str(A/"s8_trans.wav"),
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(s8_v0*1000)}|{int(s8_v0*1000)},volume=2.0[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(s8_tr0*1000)}|{int(s8_tr0*1000)},volume=2.0[v2];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim={MSEEK}:{MSEEK+s8_seg},asetpts=PTS-STARTPTS,"
     f"volume='{ve}':eval=frame,afade=t=out:st={s8_end-1.0}:d=1.0[m];"
     f"[v1][v2][m]amix=inputs=3:normalize=0:duration=longest,atrim=0:{s8_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",str(SEG/"seg_s8.wav"),"-y"])

# endcard：音乐尾淡出
mk_bed(SEG/"seg_end.wav", 116.0, END_D, 0.20, 0.8, 2.5, 2.5)

# 拼接 master_pilot.wav
(SEG/"plist.txt").write_text(
    "file 'seg_cover.wav'\nfile 'seg_hook.wav'\nfile 'seg_s8.wav'\nfile 'seg_end.wav'\n", encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(SEG/"plist.txt"),
     "-ac","2","-ar","48000",str(BASE/"master_pilot.wav"),"-y"])
import shutil
shutil.copy(BASE/"master_pilot.wav", HF/"master_pilot.wav")
print("master_pilot dur:", dur(BASE/"master_pilot.wav"), "planned:", TOTAL)

# ============================================================
# HTML composition
# ============================================================
COVER_T, HOOK_T, S8_T, END_T = S["cover"][0], S["hook"][0], S["s8"][0], S["end"][0]
s8a = {k: round(S8_T+v,3) for k,v in dict(v0=s8_v0,v1=s8_v1,sw0=s8_sw0,full0=s8_full0,
       full1=s8_full1,tr0=s8_tr0,tr1=s8_tr1,end=s8_end).items()}

# 8 节点倒数轨（#8 active）
RANKS = ["08","07","06","05","04","03","02","01"]
rail_nodes = "".join(
    f'<div class="rk-dot{" active" if i==0 else ""}" style="top:{8+i*11.6:.1f}%">'
    f'<span class="rk-t">{r}</span></div>' for i,r in enumerate(RANKS))

CSS = '''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#080503;
 font-family:"Noto Serif SC","Songti SC",serif;color:#F3EBDD;-webkit-font-smoothing:antialiased;}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.scrim{position:absolute;inset:0;z-index:2;opacity:0;
 background:linear-gradient(180deg,rgba(8,5,3,.55) 0%,rgba(8,5,3,.30) 32%,rgba(8,5,3,.62) 72%,rgba(8,5,3,.92) 100%);}
.grain{position:absolute;inset:0;z-index:3;pointer-events:none;mix-blend-mode:overlay;opacity:.5;
 background-image:radial-gradient(circle at 12% 22%,rgba(255,255,255,.05) 0 .5px,transparent 1px),
 radial-gradient(circle at 76% 64%,rgba(255,255,255,.05) 0 .5px,transparent 1px),
 radial-gradient(circle at 46% 88%,rgba(255,255,255,.04) 0 .4px,transparent .9px);background-size:180px 180px,220px 220px,160px 160px;}

/* ---------- 封面 ---------- */
.cover{position:absolute;inset:0;z-index:60;background:#080503;overflow:hidden;}
.cv-bg{position:absolute;inset:-6%;background:url("cover_assets/studio.jpg") center/cover;
 filter:blur(26px) brightness(.4) contrast(1.05);transform:scale(1.15);}
.cv-veil{position:absolute;inset:0;background:
 radial-gradient(ellipse at 50% 32%,rgba(178,58,46,.18) 0,transparent 55%),
 linear-gradient(180deg,rgba(8,5,3,.55) 0%,rgba(8,5,3,.40) 40%,rgba(8,5,3,.93) 100%);}
.cv-zys{position:absolute;right:96px;top:300px;width:300px;height:420px;
 background:url("cover_assets/zys.jpg") center top/cover;border-radius:8px;
 filter:grayscale(1) brightness(.62) contrast(1.18);
 -webkit-mask-image:linear-gradient(180deg,#000 60%,transparent);mask-image:linear-gradient(180deg,#000 60%,transparent);
 opacity:.5;box-shadow:0 30px 80px rgba(0,0,0,.6);}
.cv-zys-cap{position:absolute;right:104px;top:712px;font-family:"Noto Sans SC",sans-serif;
 font-size:24px;letter-spacing:.3em;color:rgba(201,162,75,.85);font-weight:700;}
.cv-amei{position:absolute;left:84px;top:236px;width:520px;height:600px;border-radius:14px;
 background:url("cover_assets/amei.jpg") center 18%/cover;
 box-shadow:0 36px 90px rgba(0,0,0,.65),inset 0 0 0 2px rgba(201,162,75,.5);
 filter:saturate(1.06) contrast(1.04);}
.cv-amei-cap{position:absolute;left:96px;top:856px;font-family:"Noto Sans SC",sans-serif;
 font-size:26px;letter-spacing:.18em;color:#E3C16A;font-weight:700;}
.cv-amei-cap small{display:block;font-size:19px;letter-spacing:.32em;color:rgba(243,235,221,.6);font-weight:500;margin-top:6px;}
.cv-main{position:absolute;left:84px;right:84px;bottom:300px;}
.cv-kicker{display:inline-block;font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:800;
 letter-spacing:.36em;color:#080503;background:#C9A24B;padding:9px 20px;border-radius:4px;margin-bottom:28px;}
.cv-title{font-size:104px;font-weight:900;line-height:1.1;letter-spacing:-2px;color:#F3EBDD;
 text-shadow:0 6px 40px rgba(0,0,0,.7);}
.cv-title b{color:#E3C16A;}
.cv-sub{margin-top:30px;font-size:42px;font-weight:600;color:rgba(243,235,221,.82);letter-spacing:.04em;}
.cv-sub::before{content:"";display:inline-block;width:46px;height:3px;background:#B23A2E;
 vertical-align:middle;margin-right:18px;transform:translateY(-8px);}
.cv-foot{position:absolute;left:84px;bottom:128px;font-family:"Noto Sans SC",sans-serif;
 font-size:25px;letter-spacing:.06em;color:rgba(243,235,221,.5);}

/* ---------- 钩子 ---------- */
.hook{position:absolute;inset:0;z-index:40;}
.hk-txt{position:absolute;left:80px;right:80px;bottom:300px;opacity:0;}
.hk-l1{font-size:70px;font-weight:800;color:#F3EBDD;line-height:1.18;letter-spacing:-1px;}
.hk-l2{font-size:70px;font-weight:900;color:#E3C16A;line-height:1.18;letter-spacing:-1px;margin-top:10px;}
.hk-l2 .rd{color:#C8463A;}

/* ---------- s8 章节 chrome ---------- */
.chrome{position:absolute;inset:0;z-index:5;pointer-events:none;}
.rk{position:absolute;top:150px;left:54px;bottom:230px;width:48px;opacity:0;}
.rk-bar{position:absolute;top:0;bottom:0;left:22px;width:2px;background:linear-gradient(180deg,transparent,rgba(201,162,75,.4),transparent);}
.rk-dot{position:absolute;left:0;width:46px;height:46px;border-radius:50%;background:rgba(20,12,8,.85);
 border:2px solid rgba(243,235,221,.22);display:flex;align-items:center;justify-content:center;}
.rk-dot.active{background:#C8463A;border-color:#E3C16A;box-shadow:0 0 28px rgba(200,70,58,.8),0 0 60px rgba(201,162,75,.3);transform:scale(1.18);}
.rk-t{font-family:"Noto Sans SC",sans-serif;font-size:21px;font-weight:800;color:rgba(243,235,221,.7);}
.rk-dot.active .rk-t{color:#fff;}

.card{position:absolute;top:150px;right:54px;width:600px;padding:42px 44px 40px;border-radius:22px;
 background:linear-gradient(160deg,rgba(40,26,16,.55),rgba(20,12,8,.40));backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);
 border:1.5px solid rgba(201,162,75,.30);box-shadow:0 30px 80px rgba(0,0,0,.6);opacity:0;}
.card-no{font-family:"Noto Sans SC",sans-serif;font-size:34px;letter-spacing:.3em;font-weight:800;color:#E3C16A;margin-bottom:8px;}
.card-no small{font-size:22px;color:rgba(243,235,221,.5);letter-spacing:.2em;}
.card-name{font-size:74px;font-weight:800;line-height:1.04;letter-spacing:-1px;color:#F3EBDD;margin:6px 0 22px;}
.card-credit{font-family:"Noto Sans SC",sans-serif;font-size:27px;line-height:1.5;color:rgba(243,235,221,.78);font-weight:500;}
.card-credit b{color:#E3C16A;font-weight:700;}
.card-tag{margin-top:24px;display:inline-flex;align-items:center;gap:13px;font-family:"Noto Sans SC",sans-serif;
 font-size:29px;font-weight:700;color:#C8463A;}
.card-tag .d{width:11px;height:11px;border-radius:50%;background:#C8463A;box-shadow:0 0 14px #C8463A;}

/* 副歌屏幕文字 */
.show{position:absolute;left:80px;right:80px;bottom:330px;text-align:left;opacity:0;}
.show-l1{font-size:78px;font-weight:800;color:#F3EBDD;line-height:1.12;letter-spacing:-1px;text-shadow:0 4px 30px rgba(0,0,0,.7);}
.show-l2{font-size:78px;font-weight:900;color:#E3C16A;line-height:1.12;letter-spacing:-1px;}

/* 来源小字 */
.src{position:absolute;bottom:64px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;
 font-size:18px;letter-spacing:.22em;color:rgba(243,235,221,.34);opacity:0;}

/* ---------- 样片尾卡 ---------- */
.endcard{position:absolute;inset:0;z-index:70;background:radial-gradient(ellipse at 50% 42%,#1a0f08 0,#080503 72%);opacity:0;
 display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;}
.ec-k{font-family:"Noto Sans SC",sans-serif;font-size:30px;letter-spacing:.5em;color:#C9A24B;font-weight:800;}
.ec-h{font-size:60px;font-weight:800;color:#F3EBDD;text-align:center;line-height:1.3;}
.ec-h b{color:#E3C16A;}
.ec-s{font-family:"Noto Sans SC",sans-serif;font-size:27px;color:rgba(243,235,221,.6);letter-spacing:.05em;}
'''

# footage：hook 段（jm → s8bw 交替）、s8 段（蒙太奇）
foot = f'''
<video id="fv_hook" class="fv" data-start="{fmt(HOOK_T)}" data-duration="{fmt(hook_seg+0.3)}" data-track-index="0" src="clips_seg/s8.mp4" muted playsinline></video>
<video id="fv_s8" class="fv" data-start="{fmt(S8_T)}" data-duration="{fmt(s8_seg)}" data-track-index="6" src="clips_seg/s8.mp4" muted playsinline></video>
'''

scrim = f'''
<div id="sc_hook" class="scrim clip" data-start="{fmt(HOOK_T)}" data-duration="{fmt(hook_seg)}" data-track-index="11"></div>
<div id="sc_s8" class="scrim clip" data-start="{fmt(S8_T)}" data-duration="{fmt(s8_seg)}" data-track-index="12"></div>
<div class="grain"></div>
'''

cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="30">
 <div class="cv-bg"></div><div class="cv-veil"></div>
 <div class="cv-zys"></div><div class="cv-zys-cap">伯乐 · 张雨生</div>
 <div class="cv-amei"></div>
 <div class="cv-amei-cap">张惠妹<small>最初的声音</small></div>
 <div class="cv-main">
   <div class="cv-kicker">华语唱片 · 黄金年代</div>
   <h1 class="cv-title">没有张雨生<br>就没有<b>最初的阿妹</b></h1>
   <div class="cv-sub">8 首歌，听懂天后起点</div>
 </div>
 <div class="cv-foot">他看见了她的声音 · 把她推向时代中央</div>
 <div class="grain"></div>
</div>'''

hook_html = f'''<div id="hook" class="clip hook" data-start="{fmt(HOOK_T)}" data-duration="{fmt(hook_seg)}" data-track-index="31">
 <div class="hk-txt" id="hk_txt">
   <div class="hk-l1">不是普通阿妹歌单</div>
   <div class="hk-l2">是<span class="rd">张雨生</span>推开的天后之路</div>
 </div>
</div>'''

chrome_html = f'''<div id="chrome_s8" class="clip chrome" data-start="{fmt(S8_T)}" data-duration="{fmt(s8_seg)}" data-track-index="20">
 <div class="rk" id="rk"><div class="rk-bar"></div>{rail_nodes}</div>
 <div class="card" id="card">
   <div class="card-no">08 <small>/ 08</small></div>
   <div class="card-name">最爱的人<br>伤我最深</div>
   <div class="card-credit"><b>张雨生 × 张惠妹 合唱</b><br>1996《两伊战争—红色热情》</div>
   <div class="card-tag"><span class="d"></span>第一次被听见</div>
 </div>
 <div class="show" id="show">
   <div class="show-l1">这是合唱</div>
   <div class="show-l2">也是一次被听见</div>
 </div>
 <div class="src" id="src">官方MV · 录音室影像 ｜ 音源：官方对唱录音</div>
</div>'''

end_html = f'''<div id="endcard" class="clip endcard" data-start="{fmt(END_T)}" data-duration="{fmt(END_D)}" data-track-index="32">
 <div class="ec-k">样 片 · PILOT</div>
 <div class="ec-h">第 8 首已成型<br>后续 <b>7 首 + 彩蛋</b> 同一风格批量</div>
 <div class="ec-s">确认风格 / 配音 / 节奏 / 封面 后继续</div>
</div>'''

audio_html = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master_pilot.wav" data-volume="1"></audio>'

JS = f'''
// 封面（首帧即缩略图，无 fade-in）
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-amei",{{opacity:1}},0);tl.set(".cv-zys",{{opacity:.5}},0);
tl.to(".cv-amei",{{scale:1.02,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.6);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D-0.6)});
tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});

// 钩子
tl.fromTo("#fv_hook",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:1.2,ease:"power2.out"}},{fmt(HOOK_T)});
tl.to("#sc_hook",{{opacity:1,duration:1.0}},{fmt(HOOK_T)});
tl.fromTo("#hk_txt",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(HOOK_T+2.0)});
tl.to("#hk_txt",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(HOOK_T+hook_seg-0.9)});
tl.set("#hk_txt",{{opacity:0}},{fmt(HOOK_T+hook_seg)});
tl.to("#fv_hook",{{opacity:0,duration:.8}},{fmt(HOOK_T+hook_seg-0.5)});
tl.set("#fv_hook",{{opacity:0}},{fmt(HOOK_T+hook_seg)});

// s8 章节
tl.fromTo("#fv_s8",{{opacity:0,scale:1.06}},{{opacity:1,scale:1,duration:1.4,ease:"power2.out"}},{fmt(S8_T)});
tl.to("#sc_s8",{{opacity:1,duration:1.2}},{fmt(S8_T)});
tl.fromTo("#rk",{{opacity:0}},{{opacity:1,duration:.8}},{fmt(S8_T+0.3)});
tl.fromTo("#card",{{opacity:0,x:50,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{fmt(S8_T+0.5)});
tl.fromTo("#src",{{opacity:0}},{{opacity:1,duration:.6}},{fmt(S8_T+1.4)});
// 旁白结束→消化位→swell：卡片淡出，副歌屏幕文字进
tl.to("#card",{{opacity:0,y:-12,duration:.55,ease:"power2.in"}},{fmt(s8a["sw0"]-0.1)});
tl.fromTo("#show",{{opacity:0,y:28}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(s8a["full0"]+0.4)});
tl.to("#show",{{opacity:0,y:-12,duration:.55,ease:"power2.in"}},{fmt(s8a["tr0"]-0.2)});
tl.set("#show",{{opacity:0}},{fmt(s8a["tr1"]) });
// 章节收尾淡出
tl.to("#fv_s8",{{opacity:0,duration:1.0,ease:"power1.in"}},{fmt(s8a["end"]+S8_T-1.0)});
tl.set("#fv_s8",{{opacity:0}},{fmt(s8a["end"]+S8_T)});
tl.to("#sc_s8",{{opacity:0,duration:1.0}},{fmt(s8a["end"]+S8_T-1.0)});
tl.set("#sc_s8",{{opacity:0}},{fmt(s8a["end"]+S8_T)});
tl.to("#rk",{{opacity:0,duration:.6}},{fmt(s8a["end"]+S8_T-0.6)});
tl.set("#rk",{{opacity:0}},{fmt(s8a["end"]+S8_T)});
tl.to("#src",{{opacity:0,duration:.5}},{fmt(s8a["end"]+S8_T-0.8)});
tl.set("#src",{{opacity:0}},{fmt(s8a["end"]+S8_T)});

// 样片尾卡
tl.fromTo("#endcard",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{fmt(END_T)});
tl.to("#endcard",{{opacity:1,duration:.1}},{fmt(TOTAL-0.2)});
'''

html = f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
{foot}
{scrim}
{chrome_html}
{cover_html}
{hook_html}
{end_html}
{audio_html}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"] = tl;
</script>
</body></html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"zys-amei-pilot"}', encoding="utf-8")
print("index.html:", len(html), "bytes")
print("BUILD DONE")
