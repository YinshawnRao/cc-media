#!/usr/bin/env python3
"""样片 HyperFrames 合成：封面 + 开头 + 第10首《人间》。
读取 timeline.json（与 master.wav 同源）→ 生成 hf/index.html。
风格：暗底+暗红单一强调色、Noto Serif SC、letterbox 主体、film grain/vignette/cinebar。
从项目根运行：python3 build/build_html.py
"""
import json
from pathlib import Path

TL = json.loads(Path("timeline.json").read_text(encoding="utf-8"))
S = TL["starts"]; D = TL["durs"]
COVER_D = TL["COVER_D"]; OPEN_END = TL["OPEN_END"]; ENTRY = TL["ENTRY_START"]
SWELL_START = TL["SWELL_START"]; SHOW_START = TL["SHOW_START"]; SHOW_END = TL["SHOW_END"]
TR_START = TL["TR_START"]; TR_END = TL["TR_END"]; TOTAL = TL["TOTAL"]
def f(x): return f"{round(x,3)}"

# ---------------- 字幕文案（与配音一致，长句两行）----------------
SUBS = {
    "op1": "王菲，当然有很多好歌。",
    "op2": "但有一种王菲，是林夕写出来的。",
    "op3": "他写给她的，不只是爱情；",
    "op4": "还有孤独，还有放下，还有无常。",
    "op5": "还有一个人走到世界尽头以后，<br>仍然不解释自己的样子。",
    "op6": "今天这十首，不只听旋律，<br>更听林夕怎么把王菲写成传奇。",
    "rj1": "林夕写给王菲的第一层，是人间。",
    "rj2": "这首歌没有太多锋利的隐喻，<br>反而像一句很轻的祝福。",
    "rj3": "王菲一开口，那种疏离感忽然就落地了。",
    "rj4": "她不是不食人间烟火，<br>她只是把人间唱得很远，也很温柔。",
    "tr1": "但林夕真正厉害的地方，<br>是他写爱，从来不只写甜。",
}

# ---------------- footage（本机渲染器 ≥7 video 会超时 → 仅 4 个 video，老唱片用 CSS 旋转环）----------------
FOOT = [
    dict(id="city",  src="clips_seg/city.mp4",         start=4.5,        dur=25.5, track=0, kind="full", grade="g-city", fin=1.3, fout=1.8),
    dict(id="fopen", src="clips_seg/faye_open.mp4",     start=26.0,       dur=20.0, track=1, kind="lb",   grade="g-cool", fin=1.8, fout=1.8),
    dict(id="rimg",  src="clips_seg/renjian_img.mp4",   start=44.3,       dur=18.0, track=2, kind="lb",   grade="g-warm", fin=1.6, fout=1.7),
    dict(id="rshow", src="clips_seg/renjian_show.mp4",  start=SHOW_START, dur=30.0, track=5, kind="lb",   grade="g-warm", fin=0.9, fout=1.8),
]
foot_html = []
for s in FOOT:
    cls = "foot " + ("full" if s["kind"] == "full" else "lb") + " " + s["grade"]
    foot_html.append(
        f'<video id="{s["id"]}" class="{cls} clip" data-start="{f(s["start"])}" '
        f'data-duration="{f(s["dur"])}" data-track-index="{s["track"]}" '
        f'src="{s["src"]}" muted playsinline preload="auto"></video>')

# ---------------- 字幕 ----------------
sub_html = []
for k, txt in SUBS.items():
    st = S[k]; du = D[k]
    sub_html.append(
        f'<div id="sub_{k}" class="sub clip" data-start="{f(st)}" data-duration="{f(du+0.5)}" '
        f'data-track-index="12">{txt}</div>')

html_blocks = "\n    ".join(foot_html) + "\n    " + "\n    ".join(sub_html)

# ---------------- 封面 ----------------
cover = f'''<div id="cover" class="cover clip" data-start="0" data-duration="{f(COVER_D)}" data-track-index="40">
  <div class="cv-veil"></div>
  <div class="cv-film cv-film-l"></div>
  <div class="cv-flower"></div>
  <div class="cv-col">
    <div class="cv-eyebrow">词 · 林夕　／　唱 · 王菲</div>
    <div class="cv-pwrap">
      <div class="cv-vinyl"></div>
      <div class="cv-portrait"></div>
      <div class="cv-ptint"></div>
    </div>
    <h1 class="cv-title">林夕把王菲<br><span class="acc">写成了神</span></h1>
    <div class="cv-sub">10 首封神词作盘点</div>
  </div>
</div>'''

# ---------------- 开头：老唱片转动（CSS 旋转环，代替 video 省一个 video 元素）----------------
op_vinyl = '''<div id="opvinyl" class="opvinyl clip" data-start="13.0" data-duration="13.5" data-track-index="8">
  <div class="ov-disc"></div>
</div>'''

# ---------------- 开头：精神地图 屏幕文字 ----------------
screenA = f'''<div id="screenA" class="screen clip" data-start="26.0" data-duration="5.6" data-track-index="14">
  <div class="sa-1">不是王菲热门歌单</div>
  <div class="sa-2">是林夕写给王菲的<span class="acc">精神地图</span></div>
</div>'''

# ---------------- 人间：番号+歌名+资料 ----------------
title_rj = f'''<div id="title_rj" class="songcard clip" data-start="{f(ENTRY+0.3)}" data-duration="8.6" data-track-index="15">
  <div class="sc-no">10</div>
  <div class="sc-name">人间</div>
  <div class="sc-credit">词 · 林夕　唱 · 王菲　曲 · 中岛美雪</div>
  <div class="sc-album">1997 ·《王菲》</div>
</div>'''

# 常驻角标（题卡淡出后才进，避免与大标题重复）
TAG_START = ENTRY + 8.0
tag_rj = f'''<div id="tag_rj" class="corner clip" data-start="{f(TAG_START)}" data-duration="{f(TR_START-TAG_START)}" data-track-index="16">
  <span class="cn-no">10</span><span class="cn-line"></span><span class="cn-tag">人间</span>
</div>'''

# 人间 主题屏幕文字（副歌期）
screenB = f'''<div id="screenB" class="screen2 clip" data-start="61.2" data-duration="8.5" data-track-index="17">
  <div class="sb-1">她不是不在人间</div>
  <div class="sb-2">她只是把人间<span class="acc">唱得很远</span></div>
</div>'''

# 转场卡（含暗红微光底，避免纯黑只剩文字）
trans = f'''<div id="trans" class="transcard clip" data-start="{f(TR_START)}" data-duration="{f(TOTAL-TR_START)}" data-track-index="18">
  <div class="tc-bg"></div>
  <div class="tc-rule"></div>
  <div class="tc-text">他写爱，<br>从来<span class="acc">不只写甜</span></div>
</div>'''

# 全局氛围层
chrome = '''<div id="cinetop" class="cinetop"></div>
    <div id="cinebot" class="cinebot"></div>
    <div id="vignette" class="vignette"></div>
    <div id="grain" class="grain"></div>'''

audio = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ---------------- CSS ----------------
GRAIN_URI = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E"
             "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E"
             "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.9'/%3E%3C/svg%3E")

CSS = '''
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1920px; overflow:hidden; background:#08080b;
  font-family:"Noto Serif SC",serif; color:#ece4d6; -webkit-font-smoothing:antialiased; }
.foot { position:absolute; opacity:0; will-change:opacity,transform; }
.full { inset:0; width:1080px; height:1920px; object-fit:cover; }
.lb   { left:0; width:1080px; height:auto; top:740px; }   /* 1080x372 letterbox 居中偏上 */
.g-city  { filter:grayscale(.45) saturate(.55) brightness(.5) contrast(1.12); }
.g-vinyl { filter:saturate(.6) brightness(.58) contrast(1.05) sepia(.12); }
.g-cool  { filter:grayscale(.55) saturate(.7) brightness(1.0) contrast(1.1); }
.g-warm  { filter:saturate(.92) brightness(1.06) contrast(1.04) sepia(.06); }
.g-dim   { filter:grayscale(.4) saturate(.7) brightness(.62) contrast(1.06); }

/* cinematic 框：上下暗渐变托字 + 暗角 + 颗粒 */
.cinetop { position:absolute; top:0; left:0; right:0; height:660px; z-index:6; pointer-events:none;
  background:linear-gradient(180deg, rgba(8,8,11,.94) 0%, rgba(8,8,11,.55) 52%, rgba(8,8,11,0) 100%); }
.cinebot { position:absolute; bottom:0; left:0; right:0; height:720px; z-index:6; pointer-events:none;
  background:linear-gradient(0deg, rgba(8,8,11,.96) 0%, rgba(8,8,11,.62) 48%, rgba(8,8,11,0) 100%); }
.vignette { position:absolute; inset:0; z-index:7; pointer-events:none;
  background:radial-gradient(ellipse 78% 62% at 50% 46%, rgba(0,0,0,0) 38%, rgba(0,0,0,.5) 100%); }
.grain { position:absolute; inset:0; z-index:9; pointer-events:none; opacity:.09; mix-blend-mode:overlay;
  background-image:url("''' + GRAIN_URI + '''"); background-size:220px 220px; }

/* 字幕 */
.sub { position:absolute; left:90px; right:90px; bottom:300px; z-index:13; text-align:center;
  font-family:"Noto Serif SC",serif; font-weight:500; font-size:46px; line-height:1.5;
  color:rgba(236,228,214,.97); letter-spacing:.02em; opacity:0;
  text-shadow:0 2px 24px rgba(0,0,0,.85), 0 1px 4px rgba(0,0,0,.9); }

/* 屏幕文字（开头精神地图） */
.screen { position:absolute; left:80px; right:80px; top:560px; z-index:14; text-align:center; opacity:0; }
.sa-1 { font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:40px; letter-spacing:.06em;
  color:rgba(236,228,214,.5); margin-bottom:26px; text-decoration:line-through; text-decoration-color:rgba(180,55,59,.7); text-decoration-thickness:2px; }
.sa-2 { font-family:"Noto Serif SC",serif; font-weight:700; font-size:64px; line-height:1.34; color:#ece4d6; letter-spacing:.01em; }
.acc { color:#c0413f; }

/* 人间 番号歌名卡（置于上方暗区，避免与画面条重叠） */
.songcard { position:absolute; left:0; right:0; top:286px; z-index:15; text-align:center; opacity:0; }
.sc-no { font-family:"Cormorant Garamond",serif; font-style:italic; font-weight:500; font-size:108px;
  line-height:.8; color:rgba(192,65,63,.92); letter-spacing:.02em; }
.sc-name { font-family:"Noto Serif SC",serif; font-weight:900; font-size:150px; line-height:1.0; color:#ece4d6;
  letter-spacing:.06em; margin:4px 0 24px; text-shadow:0 6px 50px rgba(0,0,0,.6); }
.sc-credit { font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:30px; letter-spacing:.16em;
  color:rgba(236,228,214,.72); margin-bottom:14px; }
.sc-album { font-family:"JetBrains Mono",monospace; font-weight:400; font-size:24px; letter-spacing:.2em;
  color:rgba(91,110,128,.95); }

/* 常驻角标 */
.corner { position:absolute; top:96px; left:64px; z-index:16; display:flex; align-items:center; gap:18px; opacity:0; }
.cn-no { font-family:"Cormorant Garamond",serif; font-style:italic; font-weight:600; font-size:46px; color:#c0413f; }
.cn-line { width:46px; height:2px; background:rgba(236,228,214,.4); }
.cn-tag { font-family:"Noto Serif SC",serif; font-weight:700; font-size:40px; color:rgba(236,228,214,.92); letter-spacing:.14em; }

/* 人间 主题屏幕文字（副歌） */
.screen2 { position:absolute; left:80px; right:80px; top:430px; z-index:17; text-align:center; opacity:0; }
.sb-1 { font-family:"Noto Serif SC",serif; font-weight:500; font-size:50px; color:rgba(236,228,214,.85); margin-bottom:18px; letter-spacing:.04em; }
.sb-2 { font-family:"Noto Serif SC",serif; font-weight:700; font-size:70px; line-height:1.28; color:#ece4d6; letter-spacing:.02em; }

/* 开头老唱片（CSS 旋转环） */
.opvinyl { position:absolute; left:0; right:0; top:0; bottom:0; z-index:5; pointer-events:none; opacity:0;
  display:flex; align-items:center; justify-content:center;
  background:radial-gradient(circle at 50% 50%, rgba(8,8,11,.62) 0%, rgba(8,8,11,.2) 32%, rgba(8,8,11,0) 52%); }
.ov-disc { width:520px; height:520px; border-radius:50%;
  background:
    radial-gradient(circle at 50% 50%, #2a2530 0 5.5%, #7d1f24 5.5% 6.2%, #1e1a24 6.6% 9%, rgba(0,0,0,0) 9%),
    radial-gradient(circle at 40% 36%, rgba(236,228,214,.12) 0%, rgba(236,228,214,0) 46%),
    repeating-radial-gradient(circle at 50% 50%, rgba(236,228,214,.06) 0 1.4px, rgba(0,0,0,.18) 1.4px 6px),
    radial-gradient(circle at 50% 50%, #181420 0 100%);
  box-shadow:0 0 0 2px rgba(236,228,214,.10), inset 0 0 70px rgba(0,0,0,.55), 0 30px 90px rgba(0,0,0,.75);
  opacity:.5; }

/* 转场卡 */
.transcard { position:absolute; left:0; right:0; top:0; bottom:0; z-index:18; opacity:0;
  display:flex; flex-direction:column; align-items:center; justify-content:center; }
.tc-bg { position:absolute; inset:0; z-index:-1;
  background:radial-gradient(ellipse 70% 50% at 50% 50%, rgba(140,30,36,.34) 0%, rgba(8,8,11,.0) 60%); }
.tc-rule { width:64px; height:2px; background:#c0413f; margin:0 0 40px; opacity:.9; }
.tc-text { font-family:"Noto Serif SC",serif; font-weight:600; font-size:80px; line-height:1.35; text-align:center; color:#ece4d6; letter-spacing:.02em; padding:0 70px; }

/* ============ 封面 ============ */
.cover { position:absolute; inset:0; z-index:50; background:#08080b; overflow:hidden; }
.cv-veil { position:absolute; inset:0; z-index:1;
  background:radial-gradient(ellipse 90% 70% at 50% 38%, rgba(40,20,22,.5) 0%, rgba(8,8,11,.9) 62%, #08080b 100%); }
.cv-film { position:absolute; top:0; bottom:0; width:46px; z-index:2; opacity:.5;
  background:repeating-linear-gradient(180deg, rgba(236,228,214,.0) 0 14px, rgba(236,228,214,.0) 14px 22px, transparent 22px 40px),
             repeating-linear-gradient(180deg, transparent 0 8px, rgba(236,228,214,.16) 8px 24px, transparent 24px 40px); }
.cv-film-l { left:30px; }
.cv-flower { position:absolute; right:-120px; bottom:-140px; width:560px; height:560px; z-index:2; opacity:.5;
  background:radial-gradient(circle at 50% 50%, rgba(176,40,46,.55) 0%, rgba(120,20,26,.32) 26%, rgba(60,10,14,.12) 46%, transparent 62%);
  filter:blur(2px); }
.cv-col { position:absolute; left:0; right:0; top:50%; transform:translateY(-50%); z-index:5;
  display:flex; flex-direction:column; align-items:center; }
.cv-eyebrow { font-family:"Noto Sans SC",sans-serif; font-weight:600; font-size:30px; letter-spacing:.42em;
  color:rgba(192,65,63,.9); margin-bottom:34px; padding-left:.42em; }
.cv-pwrap { position:relative; width:470px; height:560px; margin-bottom:46px; }
.cv-vinyl { position:absolute; right:-66px; top:120px; width:300px; height:300px; border-radius:50%; z-index:1;
  background:radial-gradient(circle at 50% 50%, #b0282e 0 8%, #1a1216 9% 12%, #0e0c10 13% 100%);
  box-shadow:0 0 0 1px rgba(236,228,214,.1), inset 0 0 0 26px rgba(236,228,214,.02), inset 0 0 0 52px rgba(236,228,214,.03);
  opacity:.85; filter:brightness(.9); }
.cv-portrait { position:absolute; inset:0; z-index:2; border-radius:8px;
  background-image:url("cover_assets/faye_wide.jpg"); background-size:cover; background-position:50% 38%;
  filter:grayscale(.85) contrast(1.16) brightness(1.05); border:1px solid rgba(236,228,214,.14);
  box-shadow:0 40px 90px rgba(0,0,0,.6); }
.cv-ptint { position:absolute; inset:0; z-index:3; border-radius:8px; mix-blend-mode:soft-light;
  background:linear-gradient(155deg, rgba(176,40,46,.42) 0%, rgba(8,8,11,0) 50%, rgba(70,90,110,.3) 100%); }
.cv-title { font-family:"Noto Serif SC",serif; font-weight:900; font-size:118px; line-height:1.06; text-align:center;
  color:#ece4d6; letter-spacing:.04em; text-shadow:0 8px 50px rgba(0,0,0,.55); }
.cv-title .acc { color:#c0413f; }
.cv-sub { font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:42px; letter-spacing:.28em;
  color:rgba(236,228,214,.82); margin-top:34px; padding-left:.28em;
  border-top:1px solid rgba(236,228,214,.16); padding-top:30px; }
'''

# ---------------- JS GSAP ----------------
def fade(el, fin, start, dur, fout, peak=1.0, ease="power1.inOut"):
    end = start + dur
    return (
        f'tl.fromTo("{el}",{{opacity:0}},{{opacity:{peak},duration:{f(fin)},ease:"{ease}"}},{f(start)});\n'
        f'tl.to("{el}",{{opacity:0,duration:{f(fout)},ease:"power1.in"}},{f(end-fout)});\n'
        f'tl.set("{el}",{{opacity:0}},{f(end)});\n')

js = []
# 封面：frame0 完整（不 fade-in），轻微呼吸，4.4s 起淡出
js.append('tl.set("#cover",{opacity:1},0);')
js.append('tl.set(".cv-col,.cv-portrait,.cv-title,.cv-sub,.cv-eyebrow,.cv-flower,.cv-vinyl",{opacity:1},0);')
js.append('tl.fromTo(".cv-portrait",{scale:1.0},{scale:1.03,duration:4.0,ease:"sine.inOut"},0.6);')
js.append('tl.fromTo(".cv-flower",{scale:1.0,opacity:.5},{scale:1.08,opacity:.62,duration:4.2,ease:"sine.inOut"},0.4);')
js.append(f'tl.to("#cover",{{opacity:0,duration:0.7,ease:"power2.in"}},{f(COVER_D-0.7)});')
js.append(f'tl.set("#cover",{{opacity:0}},{f(COVER_D)});')

# footage
for s in FOOT:
    peak = 0.5 if s["id"] == "ftran" else 1.0
    js.append(fade(f'#{s["id"]}', s["fin"], s["start"], s["dur"], s["fout"], peak=peak))
    # 轻微 ken-burns / 漂移
    if s["kind"] == "full":
        js.append(f'tl.fromTo("#{s["id"]}",{{scale:1.06}},{{scale:1.0,duration:{f(s["dur"])},ease:"none"}},{f(s["start"])});')
    else:
        js.append(f'tl.fromTo("#{s["id"]}",{{scale:1.04}},{{scale:1.0,duration:{f(s["dur"])},ease:"none"}},{f(s["start"])});')

# 字幕：入场上移淡入、结束淡出
for k in SUBS:
    st = S[k]; du = D[k]
    js.append(f'tl.fromTo("#sub_{k}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.45,ease:"power2.out"}},{f(st)});')
    js.append(f'tl.to("#sub_{k}",{{opacity:0,y:-8,duration:0.45,ease:"power1.in"}},{f(st+du+0.05)});')
    js.append(f'tl.set("#sub_{k}",{{opacity:0}},{f(st+du+0.5)});')

# 开头老唱片：淡入淡出 + 缓慢旋转
js.append('tl.fromTo("#opvinyl",{opacity:0},{opacity:1,duration:1.5,ease:"power1.inOut"},13.0);')
js.append('tl.to("#opvinyl",{opacity:0,duration:1.8,ease:"power1.in"},24.7);')
js.append('tl.set("#opvinyl",{opacity:0},26.5);')
js.append('tl.fromTo(".ov-disc",{rotation:0},{rotation:150,duration:13.5,ease:"none"},13.0);')

# 屏幕文字 A（精神地图）整体淡入（防抽帧半截）
js.append('tl.fromTo("#screenA",{opacity:0,y:14},{opacity:1,y:0,duration:0.6,ease:"power2.out"},26.0);')
js.append('tl.to("#screenA",{opacity:0,y:-10,duration:0.7,ease:"power1.in"},30.4);')
js.append('tl.set("#screenA",{opacity:0},31.6);')

# 人间 番号歌名卡
js.append(fade('#title_rj', 0.7, ENTRY+0.3, 8.6, 1.0, ease="power2.out"))
js.append(f'tl.fromTo("#title_rj .sc-name",{{letterSpacing:"0.22em",opacity:0}},{{letterSpacing:"0.06em",opacity:1,duration:1.0,ease:"power3.out"}},{f(ENTRY+0.5)});')
# 角标
js.append(f'tl.fromTo("#tag_rj",{{opacity:0,x:-14}},{{opacity:1,x:0,duration:0.7,ease:"power2.out"}},{f(TAG_START)});')
js.append(f'tl.to("#tag_rj",{{opacity:0,duration:0.8,ease:"power1.in"}},{f(TR_START-0.4)});')
js.append(f'tl.set("#tag_rj",{{opacity:0}},{f(TR_START)});')
# 屏幕文字 B（副歌主题）整体淡入
js.append('tl.fromTo("#screenB",{opacity:0,y:16},{opacity:1,y:0,duration:0.8,ease:"power2.out"},61.2);')
js.append('tl.to("#screenB",{opacity:0,y:-10,duration:0.9,ease:"power1.in"},68.8);')
js.append('tl.set("#screenB",{opacity:0},69.7);')
# 转场卡
js.append(f'tl.fromTo("#trans",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},{f(TR_START+0.2)});')
js.append(f'tl.to("#trans",{{opacity:1,duration:0.1}},{f(TOTAL-0.3)});')
# grain 轻微闪烁/位移（保持有机感）
js.append('tl.fromTo("#grain",{opacity:.07},{opacity:.12,duration:2.2,yoyo:true,repeat:44,ease:"sine.inOut"},0);')

JS = "\n".join(js)

html = f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@400;500;600;700&family=Cormorant+Garamond:ital,wght@1,400;1,500;1,600&family=JetBrains+Mono:wght@400;500&family=Ma+Shan+Zheng&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
    {html_blocks}
    {chrome}
    {op_vinyl}
    {screenA}
    {title_rj}
    {tag_rj}
    {screenB}
    {trans}
    {cover}
    {audio}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused:true }});
    {JS}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>'''

Path("hf/index.html").write_text(html, encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"linxi-faye-fengshen-sample"}', encoding="utf-8")
print("index.html:", len(html), "bytes ; TOTAL", TOTAL)
