#!/usr/bin/env python3
"""样片构建：封面反差 + 开头钩子(冷顾里↔甜郭采洁) + No.1《Little Sunshine》救场展示段。
产物：hf/master_sample.wav（Little Sunshine 床→swell→副歌 + 女声旁白 ducking）+ hf/index.html + 预切 clips_seg。
渲染后必须 mux master（HF 会压平音频动态）。"""
import subprocess, json, wave, contextlib
from pathlib import Path

ROOT = Path("/Users/yinshawnrao/explorer/cc-media/sandbox/guocaijie-sweet")
A = ROOT/"audio"; C = ROOT/"clips"; HF = ROOT/"hf"
def run(cmd): subprocess.run(cmd, check=True)
def fmt(x): return f"{round(x,3)}"

NARR = json.loads((A/"sample_narration.json").read_text())
D = {k: v["dur"] for k, v in NARR.items()}
print("NARR:", {k: round(v,2) for k,v in D.items()})

# ===== 时间轴 =====
S0 = 1.0          # 歌曲起点(song-time 0 在 t=1.0)
COVER_D = 5.0
LEAD = 0.6
intro_at = COVER_D + LEAD                              # 5.6
bridge_at = intro_at + D["intro"] + 0.7
s1_voice_at = bridge_at + D["bridge"] + 1.0
POST, SWELL, SHOW = 1.2, 1.5, 30.0
swell0 = s1_voice_at + D["s1_voice"] + POST
show0 = swell0 + SWELL
show1 = show0 + SHOW
mid_at = show1 - D["s1_mid"] - 1.8
END = round(show1 + 2.4, 2)
TOTAL = END
print(f"intro@{intro_at} bridge@{bridge_at:.2f} s1@{s1_voice_at:.2f} swell0@{swell0:.2f} show0@{show0:.2f} show1@{show1:.2f} mid@{mid_at:.2f} TOTAL={TOTAL}")

# ===== 音频 master =====
bed_c, bed_n, duckmid = 0.13, 0.20, 0.55
m0, m1 = mid_at, mid_at + D["s1_mid"] + 0.3
env = (
 f"(lt(t,{S0}))*0"
 f"+(between(t,{S0},{COVER_D}))*{bed_c}"
 f"+(between(t,{COVER_D},{swell0}))*{bed_n}"
 f"+(between(t,{swell0},{show0}))*({bed_n}+{1.0-bed_n}*(t-{swell0})/{SWELL})"
 f"+(between(t,{show0},{m0}))*1.0"
 f"+(between(t,{m0},{m1}))*{duckmid}"
 f"+(gte(t,{m1}))*1.0"
)
def voice(idx, at): return (f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
                            f"adelay={int(at*1000)}|{int(at*1000)},volume=2.0[v{idx}]")
fc = (
 f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
 f"atrim=0:{TOTAL-S0+1},asetpts=PTS-STARTPTS,adelay={int(S0*1000)}|{int(S0*1000)},"
 f"volume='{env}':eval=frame,afade=t=out:st={show1}:d={END-show1}[mus];"
 + voice(1, intro_at) + ";" + voice(2, bridge_at) + ";" + voice(3, s1_voice_at) + ";" + voice(4, mid_at) + ";"
 + f"[mus][v1][v2][v3][v4]amix=inputs=5:normalize=0:duration=longest,apad,atrim=0:{TOTAL},asetpts=PTS-STARTPTS,alimiter=limit=0.96[out]"
)
run(["ffmpeg","-v","error","-i",str(ROOT/"raw/littlesunshine_audio.wav"),
     "-i",str(A/"intro.wav"),"-i",str(A/"bridge.wav"),"-i",str(A/"s1_voice.wav"),"-i",str(A/"s1_mid.wav"),
     "-filter_complex",fc,"-map","[out]","-ac","2","-ar","48000",str(HF/"master_sample.wav"),"-y"])
with contextlib.closing(wave.open(str(HF/"master_sample.wav"))) as w:
    print("master dur:", round(w.getnframes()/w.getframerate(),2), "planned:", TOTAL)

# ===== footage 时间轴 (kind, asset, t0, dur, tint, [kb]) =====
# stills 用 background-image(ken-burns); videos 预切到 clips_seg
FOOT = [
  dict(id="f1",  kind="still", asset="guli1", t0=4.6,  dur=6.9, tint="cold", kb=(1.06,1.17,"58% 33%")),
  dict(id="f2",  kind="video", asset="w_yx_a",      t0=10.7, dur=7.9, tint="warm"),
  dict(id="f3",  kind="still", asset="guli2", t0=17.9, dur=6.4, tint="cold", kb=(1.05,1.15,"60% 40%")),
  dict(id="f4",  kind="video", asset="w_yx_garden",  t0=23.5, dur=8.2, tint="warm"),
  dict(id="f5",  kind="video", asset="w_geita_a",    t0=30.9, dur=5.6, tint="warm"),
  dict(id="f6",  kind="video", asset="w_yx_b",       t0=35.0, dur=7.8, tint="warm"),
  dict(id="f7",  kind="video", asset="w_yx_c",       t0=42.2, dur=9.5, tint="warm"),
  dict(id="f8",  kind="video", asset="w_geita_b",    t0=51.0, dur=4.8, tint="warm"),
  dict(id="f9",  kind="video", asset="w_yx_garden",  t0=55.0, dur=9.4, tint="warm"),
  dict(id="f10", kind="video", asset="w_yx_a",       t0=63.8, dur=9.4, tint="warm"),
  dict(id="f11", kind="video", asset="w_yx_c",       t0=72.6, dur=9.4, tint="warm"),
  dict(id="f12", kind="video", asset="w_yx_b",       t0=81.4, dur=5.6, tint="warm"),
]

# 预切 video slots
(HF/"clips_seg").mkdir(parents=True, exist_ok=True)
for f in FOOT:
    if f["kind"] != "video": continue
    src = C/f"{f['asset']}.mp4"; out = HF/"clips_seg"/f"{f['id']}.mp4"
    run(["ffmpeg","-v","error","-i",str(src),"-t",str(f["dur"]),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
         "-pix_fmt","yuv420p","-an",str(out),"-y"])
print("clips_seg cut")

# ===== HTML =====
foot_dom = []
for i, f in enumerate(FOOT):
    z = 1
    if f["kind"] == "video":
        foot_dom.append(f'<video id="{f["id"]}" class="fv clip" data-start="{fmt(f["t0"])}" '
                        f'data-duration="{fmt(f["dur"])}" data-track-index="{i}" '
                        f'src="clips_seg/{f["id"]}.mp4" muted playsinline></video>')
    else:
        foot_dom.append(f'<div id="{f["id"]}" class="kb clip" data-start="{fmt(f["t0"])}" '
                        f'data-duration="{fmt(f["dur"])}" data-track-index="{i}" '
                        f'style="background-image:url(stills/{f["asset"]}.jpg);background-position:{f["kb"][2]}"></div>')

CSS = '''
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1920px; overflow:hidden; background:#1A130E;
  font-family:"Noto Serif SC",serif; color:#FFF6EC; -webkit-font-smoothing:antialiased; }
.fv,.kb { position:absolute; inset:0; width:1080px; height:1920px; z-index:1; opacity:0; }
.fv { object-fit:cover; }
.kb { background-size:cover; background-repeat:no-repeat; transform-origin:center; }

/* 全局胶片层：暗角 + 颗粒 + 顶/底压暗利于读字 */
#grain { position:absolute; inset:0; z-index:3; pointer-events:none; opacity:.0;
  background:
    radial-gradient(ellipse at 50% 42%, transparent 52%, rgba(20,12,8,.55) 100%),
    linear-gradient(180deg, rgba(20,12,8,.42) 0%, transparent 16%, transparent 72%, rgba(20,12,8,.66) 100%); }
#grain::after { content:""; position:absolute; inset:0; mix-blend-mode:overlay; opacity:.5;
  background-image:radial-gradient(circle at 12% 22%, rgba(255,255,255,.05) 0 .6px, transparent 1px),
    radial-gradient(circle at 72% 64%, rgba(255,255,255,.045) 0 .6px, transparent 1px),
    radial-gradient(circle at 42% 84%, rgba(255,255,255,.04) 0 .5px, transparent 1px);
  background-size:180px 180px,220px 220px,160px 160px; }

/* #1 暖底 scrim（卡片/关键词可读） */
#scrim1 { position:absolute; inset:0; z-index:2; opacity:0; pointer-events:none;
  background:linear-gradient(180deg, rgba(255,201,60,.10) 0%, transparent 30%, transparent 56%, rgba(26,16,8,.72) 100%); }

/* ===== Cover：左冷顾里 / 右暖甜妹 双肖像卡 + 斜缝 ===== */
#cover { position:absolute; inset:0; z-index:50; overflow:hidden;
  background:linear-gradient(108deg, #181B23 0%, #2A2E38 33%, #2E2620 49%, #4A3328 64%, #6E4631 100%); }
.cv-glow-l { position:absolute; left:-8%; top:6%; width:58%; height:56%; z-index:0;
  background:radial-gradient(ellipse at 42% 42%, rgba(120,140,175,.22), transparent 70%); }
.cv-glow-r { position:absolute; right:-8%; top:5%; width:60%; height:58%; z-index:0;
  background:radial-gradient(ellipse at 58% 42%, rgba(255,193,120,.26), transparent 70%); }
.cv-seam { position:absolute; top:-60px; bottom:-60px; left:50%; width:4px; z-index:2;
  background:linear-gradient(180deg, rgba(255,231,182,0), rgba(255,231,182,.8) 35%, rgba(255,231,182,.8) 65%, rgba(255,231,182,0));
  transform:translateX(-50%) rotate(7deg); box-shadow:0 0 30px rgba(255,220,150,.55); }
.cv-grain { position:absolute; inset:0; z-index:2; opacity:.45; mix-blend-mode:overlay;
  background-image:radial-gradient(circle at 20% 30%, rgba(255,255,255,.05) 0 .6px, transparent 1px),
    radial-gradient(circle at 75% 60%, rgba(255,255,255,.045) 0 .6px, transparent 1px);
  background-size:200px 200px,240px 240px; }
.cv-card { position:absolute; top:236px; width:468px; height:614px; border-radius:26px; z-index:3;
  background-size:cover; transform-origin:center; box-shadow:0 30px 72px rgba(0,0,0,.55); }
.cv-card-l { left:54px; background-image:url("cover_assets/cover_guli.jpg"); background-position:50% 22%;
  border:3px solid rgba(214,67,90,.55); }
.cv-card-r { right:54px; background-image:url("cover_assets/cover_sweet.jpg"); background-position:50% 18%;
  border:3px solid rgba(255,201,60,.72); }
.cv-card::after { content:""; position:absolute; inset:0; border-radius:23px; }
.cv-card-l::after { background:linear-gradient(180deg, rgba(28,32,42,.12), rgba(18,20,28,.50)); }
.cv-card-r::after { background:linear-gradient(180deg, rgba(255,205,130,.08), rgba(42,26,14,.40)); }
.cv-clabel { position:absolute; top:872px; width:468px; text-align:center; z-index:4;
  font-family:"Noto Sans SC",sans-serif; font-size:31px; font-weight:800; letter-spacing:.14em; }
.cv-clabel-l { left:54px; color:#EDB9C3; text-shadow:0 2px 12px rgba(0,0,0,.6); }
.cv-clabel-r { right:54px; color:#FFE2A4; text-shadow:0 2px 12px rgba(0,0,0,.6); }
.cv-eyebrow { position:absolute; top:104px; left:0; right:0; text-align:center; z-index:6;
  font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:800; letter-spacing:.42em;
  color:#FFE6A6; text-shadow:0 2px 14px rgba(0,0,0,.6); }
.cv-hook { position:absolute; top:948px; left:60px; right:60px; z-index:6; text-align:center; }
.cv-hook .hk-pill { display:inline-block; padding:18px 44px; border-radius:999px;
  background:rgba(20,14,10,.46); border:2px solid rgba(255,225,170,.6); backdrop-filter:blur(6px);
  font-family:"Ma Shan Zheng",cursive; font-size:64px; color:#FFF1D6; letter-spacing:.04em;
  text-shadow:0 3px 20px rgba(0,0,0,.7); }
.cv-title { position:absolute; bottom:148px; left:64px; right:64px; z-index:6; text-align:center; }
.cv-title h1 { font-family:"Noto Serif SC",serif; font-size:120px; font-weight:900; line-height:1.1;
  color:#FFF6EC; letter-spacing:-1px; text-shadow:0 4px 30px rgba(0,0,0,.78); }
.cv-title .ti-acc { color:#FFC93C; }
.cv-title .ti-sub { margin-top:26px; font-family:"Noto Sans SC",sans-serif; font-size:34px; font-weight:700;
  letter-spacing:.10em; color:rgba(255,246,236,.88); text-shadow:0 2px 16px rgba(0,0,0,.7); }

/* ===== 开头 eyebrow（冷↔甜 标签） ===== */
.ollab { position:absolute; left:64px; top:120px; z-index:5; opacity:0; }
.ollab .ol-tag { display:inline-block; padding:12px 26px; border-radius:999px;
  font-family:"Noto Sans SC",sans-serif; font-size:32px; font-weight:800; letter-spacing:.14em; }
.ol-cold { background:rgba(28,32,42,.62); border:2px solid rgba(214,67,90,.7); color:#FAD7DE; }
.ol-warm { background:rgba(255,201,60,.18); border:2px solid rgba(255,201,60,.8); color:#FFEFC2; }

/* ===== No.1 chrome ===== */
#no1 { position:absolute; left:60px; top:150px; z-index:5; opacity:0; }
#no1 .n1-k { font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:800; letter-spacing:.4em; color:#FFC93C; }
#no1 .n1-big { font-family:"Noto Serif SC",serif; font-size:150px; font-weight:900; line-height:.9; color:#FFF1D6;
  text-shadow:0 6px 40px rgba(255,180,40,.4); }
#card1 { position:absolute; left:56px; right:56px; bottom:430px; z-index:5; opacity:0;
  padding:34px 40px; border-radius:26px; background:linear-gradient(160deg, rgba(255,247,232,.16), rgba(255,247,232,.05));
  backdrop-filter:blur(26px); border:1.5px solid rgba(255,225,170,.34); box-shadow:0 30px 80px rgba(0,0,0,.5); }
#card1 .c-name { font-family:"Noto Serif SC",serif; font-size:78px; font-weight:800; color:#FFF6EC; letter-spacing:.5px; }
#card1 .c-en { font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:700; letter-spacing:.18em; color:#FFC93C; margin-top:6px; }
#card1 .c-meta { font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:500; color:rgba(255,246,236,.8); margin-top:16px; letter-spacing:.02em; }
#card1 .c-tag { display:inline-flex; align-items:center; gap:12px; margin-top:18px;
  font-family:"Noto Sans SC",sans-serif; font-size:31px; font-weight:700; color:#FFE6A6; }
#card1 .c-tag .dot { width:12px; height:12px; border-radius:50%; background:#FFC93C; box-shadow:0 0 16px #FFC93C; }
#kw1 { position:absolute; left:0; right:0; bottom:300px; z-index:4; text-align:center; opacity:0;
  font-family:"Noto Serif SC",serif; font-size:300px; font-weight:900; line-height:.82; color:#FFC93C;
  letter-spacing:-6px; mix-blend-mode:screen; filter:drop-shadow(0 10px 70px rgba(255,200,90,.28)); }
#mid1 { position:absolute; left:76px; right:76px; bottom:210px; z-index:5; text-align:center; opacity:0;
  font-family:"Noto Serif SC",serif; font-size:50px; font-weight:600; line-height:1.42; color:#FFF6EC;
  text-shadow:0 3px 22px rgba(0,0,0,.7); }
#endcream { position:absolute; inset:0; z-index:55; background:#FBF3E7; opacity:0; }
'''

cover = f'''<div id="cover" class="clip" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="40">
  <div class="cv-glow-l"></div><div class="cv-glow-r"></div>
  <div class="cv-card cv-card-l"></div>
  <div class="cv-card cv-card-r"></div>
  <div class="cv-seam"></div>
  <div class="cv-grain"></div>
  <div class="cv-clabel cv-clabel-l">顾里 · 高冷</div>
  <div class="cv-clabel cv-clabel-r">早期 · 甜妹</div>
  <div class="cv-eyebrow">华 语 甜 妹 考 古 · 郭 采 洁</div>
  <div class="cv-hook"><span class="hk-pill">这真的是同一个郭采洁？</span></div>
  <div class="cv-title">
    <h1>顾里之前，<br>她明明是<span class="ti-acc">甜妹</span>啊。</h1>
    <div class="ti-sub">短发红唇之前，她是一颗小太阳</div>
  </div>
</div>'''

OPENLABS = [
  ("lab_a","ol-cold","顾里 · 高冷", 4.9, 5.2),
  ("lab_b","ol-warm","早期 · 甜妹", 10.7, 5.6),
  ("lab_c","ol-cold","顾里 · 毒舌", 17.9, 5.2),
]
openlab_dom = "".join(
  f'<div id="{lid}" class="clip ollab" data-start="{fmt(t0)}" data-duration="{fmt(dur)}" data-track-index="{15+i}">'
  f'<span class="ol-tag {cls}">{txt}</span></div>'
  for i,(lid,cls,txt,t0,dur) in enumerate(OPENLABS))

no1 = '''<div id="no1"><div class="n1-k">NO.</div><div class="n1-big">1</div></div>'''
card1 = '''<div id="card1">
  <div class="c-name">Little Sunshine</div>
  <div class="c-en">郭采洁 · 小太阳</div>
  <div class="c-meta">2010 · 收录于专辑《烟火》</div>
  <div class="c-tag"><span class="dot"></span>小太阳 · 清爽甜 · 顾里之前的郭采洁</div>
</div>'''
kw1 = '<div id="kw1">小太阳</div>'
mid1 = f'<div id="mid1">{NARR["s1_mid"]["text"]}</div>'

audio = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="60" src="master_sample.wav" data-volume="1"></audio>'

# ===== GSAP =====
def kb_js(f):
    s,e,_ = f["kb"]
    return (f'tl.set("#{f["id"]}",{{scale:{s}}},{fmt(f["t0"])});'
            f'tl.fromTo("#{f["id"]}",{{opacity:0}},{{opacity:1,duration:1.0,ease:"power1.out"}},{fmt(f["t0"])});'
            f'tl.to("#{f["id"]}",{{scale:{e},duration:{f["dur"]},ease:"none"}},{fmt(f["t0"])});'
            f'tl.to("#{f["id"]}",{{opacity:0,duration:0.9,ease:"power1.in"}},{fmt(f["t0"]+f["dur"]-0.9)});'
            f'tl.set("#{f["id"]}",{{opacity:0}},{fmt(f["t0"]+f["dur"])});')
def vid_js(f):
    return (f'tl.fromTo("#{f["id"]}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:0.9,ease:"power1.out"}},{fmt(f["t0"])});'
            f'tl.to("#{f["id"]}",{{opacity:0,duration:0.9,ease:"power1.in"}},{fmt(f["t0"]+f["dur"]-0.9)});'
            f'tl.set("#{f["id"]}",{{opacity:0}},{fmt(f["t0"]+f["dur"])});')
foot_js = "".join(kb_js(f) if f["kind"]=="still" else vid_js(f) for f in FOOT)

# openlab 冷/甜 三标签（开头反差），各自独立元素 + hard kill
openlab_js = "".join(
  f'tl.fromTo("#{lid}",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{fmt(t0)});'
  f'tl.to("#{lid}",{{opacity:0,duration:.45,ease:"power1.in"}},{fmt(t0+dur-0.5)});'
  f'tl.set("#{lid}",{{opacity:0}},{fmt(t0+dur)});'
  for (lid,cls,txt,t0,dur) in OPENLABS)

JS = f'''
// 全局胶片层
tl.to("#grain",{{opacity:1,duration:1.2}},{fmt(COVER_D-0.3)});

// 封面：首帧即缩略图（不淡入）。轻 ken-burns + hook 呼吸
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-card,.cv-clabel,.cv-title,.cv-hook,.cv-eyebrow,.cv-seam",{{opacity:1}},0);
tl.fromTo(".cv-card-l",{{scale:1.0}},{{scale:1.04,duration:{fmt(COVER_D)},ease:"none"}},0);
tl.fromTo(".cv-card-r",{{scale:1.0}},{{scale:1.04,duration:{fmt(COVER_D)},ease:"none"}},0);
tl.fromTo(".cv-hook .hk-pill",{{scale:.97}},{{scale:1.03,duration:1.4,yoyo:true,repeat:2,ease:"sine.inOut"}},0.4);
tl.to("#cover",{{opacity:0,duration:0.7,ease:"power2.in"}},{fmt(COVER_D-0.7)});
tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});

// footage
{foot_js}

// 开头 冷/甜 标签
{openlab_js}

// ===== No.1 chrome =====
tl.to("#scrim1",{{opacity:1,duration:1.2}},{fmt(s1_voice_at-0.6)});
tl.fromTo("#no1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{fmt(s1_voice_at+0.2)});
tl.fromTo("#card1",{{opacity:0,y:40}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{fmt(s1_voice_at+0.6)});
// 旁白收尾→副歌：卡片淡出，大字关键词
tl.to("#card1",{{opacity:0,y:-16,duration:.6,ease:"power2.in"}},{fmt(swell0-0.2)});
tl.fromTo("#kw1",{{opacity:0,scale:.92}},{{opacity:.5,scale:1.0,duration:1.6,ease:"power3.out"}},{fmt(show0-0.4)});
tl.to("#kw1",{{opacity:.62,duration:1.4,ease:"sine.inOut"}},{fmt(show0+1.2)});
// 中段金句
tl.fromTo("#mid1",{{opacity:0,y:28}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},{fmt(mid_at)});
tl.to("#mid1",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{fmt(show1-1.0)});
// 收尾
tl.to("#no1",{{opacity:0,duration:.8}},{fmt(show1-0.6)});
tl.to("#kw1",{{opacity:0,duration:1.0}},{fmt(show1-0.6)});
tl.to("#endcream",{{opacity:1,duration:1.4,ease:"power2.in"}},{fmt(END-1.6)});
tl.set("#endcream",{{opacity:1}},{fmt(END-0.05)});
'''

html = f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;600;700;800;900&family=Noto+Sans+SC:wght@500;700;800;900&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
  {chr(10).join(foot_dom)}
  <div id="scrim1" class="clip" data-start="{fmt(s1_voice_at-1)}" data-duration="{fmt(TOTAL-(s1_voice_at-1))}" data-track-index="13"></div>
  <div id="grain" class="clip" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="14"></div>
  {cover}
  {openlab_dom}
  {no1.replace('id="no1"','id="no1" class="clip" data-start="'+fmt(s1_voice_at)+'" data-duration="'+fmt(show1-s1_voice_at)+'" data-track-index="22"')}
  {card1.replace('id="card1"','id="card1" class="clip" data-start="'+fmt(s1_voice_at)+'" data-duration="'+fmt(swell0-s1_voice_at+0.5)+'" data-track-index="23"')}
  {kw1.replace('id="kw1"','id="kw1" class="clip" data-start="'+fmt(show0-1)+'" data-duration="'+fmt(show1-(show0-1))+'" data-track-index="24"')}
  {mid1.replace('id="mid1"','id="mid1" class="clip" data-start="'+fmt(mid_at-0.5)+'" data-duration="'+fmt(show1-mid_at)+'" data-track-index="25"')}
  <div id="endcream" class="clip" data-start="{fmt(END-1.7)}" data-duration="1.7" data-track-index="27"></div>
  {audio}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused:true }});
{JS}
window.__timelines["main"] = tl;
</script>
</body></html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"guocaijie-sweet-sample"}', encoding="utf-8")
print("index.html:", len(html), "bytes;  TOTAL", TOTAL)
print("BUILD DONE")
