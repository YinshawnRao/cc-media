#!/usr/bin/env python3
"""样片 HyperFrames 合成：封面 + 开头 + 第8首《没有人》。
读取 timeline.json（与 master.wav 同源）→ 生成 hf/index.html。
风格：Y2K 都市冷感——近黑蓝底、银色金属(chrome)、蓝紫/青霓虹、暗红点缀、扫描线、胶片颗粒、CD 转动、复古字幕条。
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

# ---------------- 字幕文案（与配音一致；屏幕可保留 Elva / R&B 英文）----------------
SUBS = {
    "op1": "很多人记得萧亚轩，<br>是因为她会跳、会唱、会时髦。",
    "op2": '但只用"唱跳女歌手"概括她，<br>其实太浅了。',
    "op3": "真正把 Elva 做出来的人之一，<br>是陈伟。",
    "op4": "他写旋律、做节奏、抓声线，<br>也抓住了那年代最摩登的都市感。",
    "op5": "所以这期，不聊普通热门歌单。",
    "op6": "我们聊 8 首歌，<br>看陈伟怎么把萧亚轩做成都市女声。",
    "rj1": "第 8 首 ·《没有人》",
    "rj2": "不是讨好市场的甜歌，<br>而是直接推出她的中低音和 R&B 底色。",
    "rj3": "陈伟做的不只是写一首歌，<br>是帮她确认了一个方向。",
    "rj4": "她不是邻家女孩，<br>是带着距离感的都市女声。",
    "tr1": "想念不再是哭哭啼啼，<br>是城市夜里的突然失神。",
}

# ---------------- 开头 Elva 静帧蒙太奇（letterbox 带，交叉淡入）----------------
STILLS = [
    dict(id="m1", img="cover_assets/still_126.jpg", start=COVER_D+0.2,  dur=15.5, track=0, fin=1.4, fout=2.0),
    dict(id="m2", img="cover_assets/still_224.jpg", start=COVER_D+13.5, dur=15.0, track=1, fin=2.0, fout=2.0),
    dict(id="m3", img="cover_assets/still_200.jpg", start=COVER_D+26.0, dur=13.5, track=2, fin=2.0, fout=1.6),
]
# 进入段（番号卡期）Elva 静帧底
ENTRY_STILL = dict(id="estill", img="cover_assets/still_132.jpg", start=ENTRY-0.5, dur=(SHOW_START-ENTRY+1.2), track=4, fin=1.4, fout=1.4)

still_html = []
for s in STILLS + [ENTRY_STILL]:
    still_html.append(
        f'<div id="{s["id"]}" class="band still clip" data-start="{f(s["start"])}" '
        f'data-duration="{f(s["dur"])}" data-track-index="{s["track"]}" '
        f'style="background-image:url(\'{s["img"]}\')"></div>')

# ---------------- 展示段 footage（唯一 video）----------------
show_html = (
    f'<video id="rshow" class="band lb clip" data-start="{f(SHOW_START)}" '
    f'data-duration="{f(SHOW_END-SHOW_START)}" data-track-index="5" '
    f'src="clips_seg/meiyouren_show.mp4" muted playsinline preload="auto"></video>')

# ---------------- 字幕（复古字幕条）----------------
sub_html = []
for k, txt in SUBS.items():
    st = S[k]; du = D[k]
    sub_html.append(
        f'<div id="sub_{k}" class="sub clip" data-start="{f(st)}" data-duration="{f(du+0.5)}" '
        f'data-track-index="12"><span class="sub-in">{txt}</span></div>')

html_blocks = "\n    ".join(still_html) + "\n    " + show_html + "\n    " + "\n    ".join(sub_html)

# ---------------- 封面 ----------------
cover = f'''<div id="cover" class="cover clip" data-start="0" data-duration="{f(COVER_D)}" data-track-index="40">
  <div class="cv-bg" style="background-image:url('cover_assets/still_132.jpg')"></div>
  <div class="cv-grade"></div>
  <div class="cv-scan"></div>
  <div class="cv-cd"><span class="cd-hole"></span></div>
  <div class="cv-col">
    <div class="cv-eyebrow"><span class="ey-dot"></span>制作人 · 陈伟　×　萧亚轩</div>
    <div class="cv-frame">
      <div class="cv-portrait" style="background-image:url('cover_assets/still_132.jpg')"></div>
      <div class="cv-ptint"></div>
      <div class="cv-corner tl"></div><div class="cv-corner tr"></div>
      <div class="cv-corner bl"></div><div class="cv-corner br"></div>
    </div>
    <h1 class="cv-title">陈伟把萧亚轩<br>做成了 <span class="chrome">ELVA</span></h1>
    <div class="cv-eq"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
    <div class="cv-sub">8 首歌 · 听懂千禧年都市女声</div>
  </div>
</div>'''

# ---------------- 开头 CD（转动，chrome）----------------
op_cd = '''<div id="opcd" class="opcd clip" data-start="6.0" data-duration="34.0" data-track-index="8">
  <div class="ov-cd"><span class="ov-hole"></span></div>
</div>'''

# ---------------- 开头 屏幕文字（声音系统）----------------
screenA = f'''<div id="screenA" class="screen clip" data-start="{f(OPEN_END-9.0)}" data-duration="6.4" data-track-index="14">
  <div class="sa-1">不是普通萧亚轩歌单</div>
  <div class="sa-2">是陈伟做出来的<br><span class="neon">Elva 声音系统</span></div>
</div>'''

# ---------------- 没有人：番号+歌名+资料卡 ----------------
title_rj = f'''<div id="title_rj" class="songcard clip" data-start="{f(ENTRY+0.3)}" data-duration="9.0" data-track-index="15">
  <div class="sc-no"><span class="chrome">08</span></div>
  <div class="sc-name">没有人</div>
  <div class="sc-credit">曲 · 陈伟　词 · 姚谦　制作 · 陈伟</div>
  <div class="sc-album">1999 ·《萧亚轩》同名首张专辑</div>
</div>'''

# 常驻角标（题卡淡出后才进）
TAG_START = ENTRY + 8.4
tag_rj = f'''<div id="tag_rj" class="corner clip" data-start="{f(TAG_START)}" data-duration="{f(TR_START-TAG_START)}" data-track-index="16">
  <span class="cn-no">08</span><span class="cn-line"></span><span class="cn-tag">出道冷感</span>
</div>'''

# 没有人 主题屏幕文字（副歌期）
SB_START = SHOW_START + 3.0
screenB = f'''<div id="screenB" class="screen2 clip" data-start="{f(SB_START)}" data-duration="8.5" data-track-index="17">
  <div class="sb-1">Elva 的起点</div>
  <div class="sb-2">不是甜，<span class="warm">是冷</span></div>
</div>'''

# 转场卡
trans = f'''<div id="trans" class="transcard clip" data-start="{f(TR_START)}" data-duration="{f(TOTAL-TR_START)}" data-track-index="18">
  <div class="tc-bg"></div>
  <div class="tc-rule"></div>
  <div class="tc-text">城市夜里的<br><span class="neon">突然失神</span></div>
</div>'''

# 全局氛围层
chrome = '''<div id="cinetop" class="cinetop"></div>
    <div id="cinebot" class="cinebot"></div>
    <div id="neonglow" class="neonglow"></div>
    <div id="scan" class="scan"></div>
    <div id="vignette" class="vignette"></div>
    <div id="grain" class="grain"></div>'''

audio = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ---------------- CSS ----------------
GRAIN_URI = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E"
             "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E"
             "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.9'/%3E%3C/svg%3E")

CSS = '''
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1920px; overflow:hidden; background:#06070d;
  font-family:"Noto Sans SC",sans-serif; color:#e8edf5; -webkit-font-smoothing:antialiased; }

/* ===== footage / 静帧 letterbox 带 ===== */
.band { position:absolute; left:0; width:1080px; opacity:0; will-change:opacity,transform; }
.still { height:500px; top:712px; background-size:cover; background-position:50% 42%;
  filter:saturate(.82) brightness(.92) contrast(1.12); }
.lb { top:0; height:1920px; }   /* vfill 已是 1080x1920 全幅(带内 letterbox+模糊填充) → 全屏铺底 */
#rshow { position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; filter:saturate(.9) brightness(1.04) contrast(1.08); }
/* footage 带上叠冷蓝薄层，统一 Y2K 都市冷调 */
.band::after { content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(180deg, rgba(40,70,120,.10), rgba(20,30,60,.18)); mix-blend-mode:soft-light; }

/* ===== cinematic 框 + 暗角 + 颗粒 + 扫描线 + 霓虹 ===== */
.cinetop { position:absolute; top:0; left:0; right:0; height:640px; z-index:6; pointer-events:none;
  background:linear-gradient(180deg, rgba(6,7,13,.94) 0%, rgba(6,7,13,.5) 54%, rgba(6,7,13,0) 100%); }
.cinebot { position:absolute; bottom:0; left:0; right:0; height:760px; z-index:6; pointer-events:none;
  background:linear-gradient(0deg, rgba(6,7,13,.97) 0%, rgba(6,7,13,.6) 46%, rgba(6,7,13,0) 100%); }
.neonglow { position:absolute; inset:0; z-index:5; pointer-events:none;
  background:
    radial-gradient(ellipse 50% 36% at 84% 16%, rgba(123,92,255,.20) 0%, rgba(123,92,255,0) 60%),
    radial-gradient(ellipse 56% 40% at 12% 88%, rgba(47,214,232,.16) 0%, rgba(47,214,232,0) 62%); }
.scan { position:absolute; inset:0; z-index:8; pointer-events:none; opacity:.5;
  background-image:repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0 1px, rgba(0,0,0,0) 1px 4px); mix-blend-mode:overlay; }
.vignette { position:absolute; inset:0; z-index:7; pointer-events:none;
  background:radial-gradient(ellipse 80% 64% at 50% 46%, rgba(0,0,0,0) 40%, rgba(0,0,0,.55) 100%); }
.grain { position:absolute; inset:0; z-index:9; pointer-events:none; opacity:.10; mix-blend-mode:overlay;
  background-image:url("''' + GRAIN_URI + '''"); background-size:220px 220px; }

/* ===== 复古字幕条 ===== */
.sub { position:absolute; left:70px; right:70px; bottom:286px; z-index:13; text-align:center; opacity:0; }
.sub-in { display:inline-block; padding:20px 34px; border-radius:4px;
  font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:44px; line-height:1.46; letter-spacing:.01em;
  color:#eef2f8; background:linear-gradient(180deg, rgba(12,16,28,.66), rgba(8,11,20,.82));
  border:1px solid rgba(150,170,210,.28); box-shadow:0 0 0 1px rgba(0,0,0,.5), 0 14px 40px rgba(0,0,0,.55), inset 0 1px 0 rgba(180,200,240,.16);
  text-shadow:0 2px 14px rgba(0,0,0,.85); }

/* ===== 开头屏幕文字 ===== */
.screen { position:absolute; left:80px; right:80px; top:556px; z-index:14; text-align:center; opacity:0; }
.sa-1 { font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:40px; letter-spacing:.05em;
  color:rgba(180,192,214,.55); margin-bottom:26px; text-decoration:line-through; text-decoration-color:rgba(47,214,232,.55); text-decoration-thickness:2px; }
.sa-2 { font-family:"Noto Sans SC",sans-serif; font-weight:900; font-size:66px; line-height:1.3; color:#eef2f8; letter-spacing:.005em; }
.neon { color:#5fe4f5; text-shadow:0 0 18px rgba(47,214,232,.55), 0 0 40px rgba(47,214,232,.3); }
.warm { color:#e06b6b; text-shadow:0 0 18px rgba(192,65,63,.5); }

/* ===== 番号歌名卡 ===== */
.songcard { position:absolute; left:0; right:0; top:268px; z-index:15; text-align:center; opacity:0; }
.sc-no { font-family:"Chakra Petch",monospace; font-weight:700; font-size:128px; line-height:.82; letter-spacing:.02em; }
.sc-name { font-family:"Noto Sans SC",sans-serif; font-weight:900; font-size:140px; line-height:1.0; color:#eef2f8;
  letter-spacing:.08em; margin:6px 0 26px; text-shadow:0 6px 50px rgba(0,0,0,.6); }
.sc-credit { font-family:"Chakra Petch",monospace; font-weight:500; font-size:32px; letter-spacing:.12em;
  color:rgba(95,228,245,.92); margin-bottom:14px; }
.sc-album { font-family:"Chakra Petch",monospace; font-weight:400; font-size:25px; letter-spacing:.18em;
  color:rgba(150,164,190,.92); }

/* chrome 金属字（银色渐变） */
.chrome { background:linear-gradient(180deg,#f4f8ff 0%,#cdd6e6 28%,#8c97ad 52%,#e6ecf7 60%,#9aa6bd 76%,#c3cdde 100%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:transparent;
  filter:drop-shadow(0 2px 1px rgba(0,0,0,.45)); }

/* ===== 常驻角标 ===== */
.corner { position:absolute; top:92px; left:60px; z-index:16; display:flex; align-items:center; gap:18px; opacity:0; }
.cn-no { font-family:"Chakra Petch",monospace; font-weight:700; font-size:48px; color:#5fe4f5; text-shadow:0 0 14px rgba(47,214,232,.5); }
.cn-line { width:42px; height:2px; background:rgba(150,170,210,.5); }
.cn-tag { font-family:"Noto Sans SC",sans-serif; font-weight:700; font-size:38px; color:rgba(232,237,245,.92); letter-spacing:.14em; }

/* ===== 副歌主题文字 ===== */
.screen2 { position:absolute; left:80px; right:80px; top:404px; z-index:17; text-align:center; opacity:0; }
.sb-1 { font-family:"Chakra Petch",monospace; font-weight:600; font-size:46px; color:rgba(180,192,214,.85); margin-bottom:18px; letter-spacing:.1em; }
.sb-2 { font-family:"Noto Sans SC",sans-serif; font-weight:900; font-size:84px; line-height:1.2; color:#eef2f8; letter-spacing:.04em; }

/* ===== 开头 CD（chrome 转动）===== */
.opcd { position:absolute; left:0; right:0; top:300px; z-index:4; pointer-events:none; opacity:0;
  display:flex; align-items:center; justify-content:center; }
.ov-cd { position:relative; width:540px; height:540px; border-radius:50%;
  background:
    conic-gradient(from 0deg, #c9d2e2,#8ea0c4,#e9eef8,#9fb4d8,#c0a6d8,#e6c8e0,#9fc8d8,#c9d2e2),
    radial-gradient(circle at 50% 50%, #0a0c14 0 16%, rgba(0,0,0,0) 17%);
  box-shadow:0 0 0 2px rgba(180,200,240,.18), inset 0 0 60px rgba(0,0,0,.5), 0 30px 90px rgba(0,0,0,.6);
  opacity:.34; filter:brightness(.9) saturate(.8); }
.ov-cd::before { content:""; position:absolute; inset:0; border-radius:50%;
  background:repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,.05) 0 1.2px, rgba(0,0,0,.10) 1.2px 5px); }
.ov-hole { position:absolute; left:50%; top:50%; width:96px; height:96px; transform:translate(-50%,-50%); border-radius:50%;
  background:#06070d; box-shadow:0 0 0 18px rgba(180,200,240,.10), inset 0 0 0 2px rgba(180,200,240,.25); }

/* ===== 转场卡 ===== */
.transcard { position:absolute; left:0; right:0; top:0; bottom:0; z-index:18; opacity:0;
  display:flex; flex-direction:column; align-items:center; justify-content:center; }
.tc-bg { position:absolute; inset:0; z-index:-1;
  background:radial-gradient(ellipse 70% 50% at 50% 50%, rgba(47,214,232,.16) 0%, rgba(6,7,13,0) 60%); }
.tc-rule { width:60px; height:2px; background:#5fe4f5; margin:0 0 40px; box-shadow:0 0 16px rgba(47,214,232,.6); }
.tc-text { font-family:"Noto Sans SC",sans-serif; font-weight:800; font-size:80px; line-height:1.34; text-align:center; color:#eef2f8; letter-spacing:.03em; padding:0 70px; }

/* ============ 封面 ============ */
.cover { position:absolute; inset:0; z-index:50; background:#06070d; overflow:hidden; }
.cv-bg { position:absolute; inset:-40px; z-index:1; background-size:cover; background-position:50% 40%;
  filter:blur(14px) brightness(.42) saturate(.7) contrast(1.1); transform:scale(1.15); }
.cv-grade { position:absolute; inset:0; z-index:2;
  background:
    radial-gradient(ellipse 70% 44% at 80% 14%, rgba(123,92,255,.30) 0%, rgba(123,92,255,0) 60%),
    radial-gradient(ellipse 70% 44% at 16% 92%, rgba(47,214,232,.22) 0%, rgba(47,214,232,0) 60%),
    linear-gradient(180deg, rgba(6,7,13,.55) 0%, rgba(6,7,13,.2) 38%, rgba(6,7,13,.72) 78%, #06070d 100%); }
.cv-scan { position:absolute; inset:0; z-index:7; pointer-events:none; opacity:.5;
  background-image:repeating-linear-gradient(0deg, rgba(255,255,255,.04) 0 1px, rgba(0,0,0,0) 1px 4px); mix-blend-mode:overlay; }
.cv-cd { position:absolute; right:-150px; top:120px; width:430px; height:430px; z-index:3; border-radius:50%;
  background:conic-gradient(from 20deg, #c9d2e2,#8ea0c4,#e9eef8,#9fb4d8,#c0a6d8,#e6c8e0,#9fc8d8,#c9d2e2);
  box-shadow:inset 0 0 50px rgba(0,0,0,.5), 0 20px 70px rgba(0,0,0,.5); opacity:.30; filter:brightness(.92) saturate(.8); }
.cd-hole { position:absolute; left:50%; top:50%; width:78px; height:78px; transform:translate(-50%,-50%); border-radius:50%; background:#06070d; box-shadow:0 0 0 16px rgba(180,200,240,.1); }
.cv-col { position:absolute; left:0; right:0; top:50%; transform:translateY(-50%); z-index:5;
  display:flex; flex-direction:column; align-items:center; padding:0 64px; }
.cv-eyebrow { display:flex; align-items:center; gap:16px; font-family:"Chakra Petch",monospace; font-weight:600; font-size:30px; letter-spacing:.3em;
  color:rgba(95,228,245,.92); margin-bottom:34px; text-shadow:0 0 16px rgba(47,214,232,.4); }
.ey-dot { width:12px; height:12px; border-radius:50%; background:#5fe4f5; box-shadow:0 0 14px rgba(47,214,232,.8); }
.cv-frame { position:relative; width:454px; height:556px; margin-bottom:44px; }
.cv-portrait { position:absolute; inset:0; z-index:2; background-size:cover; background-position:50% 26%;
  filter:saturate(.74) contrast(1.16) brightness(1.0); border:1px solid rgba(150,170,210,.3); box-shadow:0 40px 90px rgba(0,0,0,.6); }
.cv-ptint { position:absolute; inset:0; z-index:3; mix-blend-mode:soft-light;
  background:linear-gradient(150deg, rgba(123,92,255,.42) 0%, rgba(6,7,13,0) 48%, rgba(47,214,232,.34) 100%); }
.cv-corner { position:absolute; width:34px; height:34px; z-index:4; border:2px solid rgba(150,170,210,.85); }
.cv-corner.tl { left:-8px; top:-8px; border-right:0; border-bottom:0; }
.cv-corner.tr { right:-8px; top:-8px; border-left:0; border-bottom:0; }
.cv-corner.bl { left:-8px; bottom:-8px; border-right:0; border-top:0; }
.cv-corner.br { right:-8px; bottom:-8px; border-left:0; border-top:0; }
.cv-title { font-family:"Noto Sans SC",sans-serif; font-weight:900; font-size:108px; line-height:1.1; text-align:center;
  color:#eef2f8; letter-spacing:.02em; text-shadow:0 8px 50px rgba(0,0,0,.55); }
.cv-title .chrome { font-family:"Chakra Petch",monospace; font-weight:700; letter-spacing:.06em; }
.cv-eq { display:flex; align-items:flex-end; gap:8px; height:42px; margin:30px 0 26px; }
.cv-eq i { width:9px; border-radius:2px; background:linear-gradient(180deg,#5fe4f5,#7b5cff); box-shadow:0 0 10px rgba(47,214,232,.5); }
.cv-eq i:nth-child(1){height:18px}.cv-eq i:nth-child(2){height:34px}.cv-eq i:nth-child(3){height:24px}
.cv-eq i:nth-child(4){height:40px}.cv-eq i:nth-child(5){height:14px}.cv-eq i:nth-child(6){height:30px}
.cv-eq i:nth-child(7){height:22px}.cv-eq i:nth-child(8){height:38px}.cv-eq i:nth-child(9){height:16px}
.cv-sub { font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:40px; letter-spacing:.16em;
  color:rgba(220,228,240,.9); padding-top:26px; border-top:1px solid rgba(150,170,210,.26); }
'''

# ---------------- JS GSAP ----------------
def fade(el, fin, start, dur, fout, peak=1.0, ease="power1.inOut"):
    end = start + dur
    return (
        f'tl.fromTo("{el}",{{opacity:0}},{{opacity:{peak},duration:{f(fin)},ease:"{ease}"}},{f(start)});\n'
        f'tl.to("{el}",{{opacity:0,duration:{f(fout)},ease:"power1.in"}},{f(end-fout)});\n'
        f'tl.set("{el}",{{opacity:0}},{f(end)});\n')

js = []
# 封面：frame0 完整（不 fade-in），轻微呼吸，4.3s 起淡出
js.append('tl.set("#cover",{opacity:1},0);')
js.append('tl.set(".cv-col,.cv-portrait,.cv-title,.cv-sub,.cv-eyebrow,.cv-cd,.cv-bg,.cv-eq",{opacity:1},0);')
js.append('tl.fromTo(".cv-portrait",{scale:1.0},{scale:1.03,duration:4.2,ease:"sine.inOut"},0.4);')
js.append('tl.fromTo(".cv-cd",{rotation:0},{rotation:40,duration:5,ease:"none"},0);')
js.append('tl.fromTo(".cv-eq i",{scaleY:.7},{scaleY:1.15,duration:.5,yoyo:true,repeat:9,ease:"sine.inOut",stagger:{each:.08,from:"center"}},0);')
js.append(f'tl.to("#cover",{{opacity:0,duration:0.7,ease:"power2.in"}},{f(COVER_D-0.7)});')
js.append(f'tl.set("#cover",{{opacity:0}},{f(COVER_D)});')

# 静帧蒙太奇 + 进入静帧 + 展示 video
for s in STILLS + [ENTRY_STILL]:
    js.append(fade(f'#{s["id"]}', s["fin"], s["start"], s["dur"], s["fout"]))
    js.append(f'tl.fromTo("#{s["id"]}",{{scale:1.06}},{{scale:1.0,duration:{f(s["dur"])},ease:"none"}},{f(s["start"])});')
js.append(fade('#rshow', 0.9, SHOW_START, SHOW_END-SHOW_START, 1.6))
js.append(f'tl.fromTo("#rshow",{{scale:1.05}},{{scale:1.0,duration:{f(SHOW_END-SHOW_START)},ease:"none"}},{f(SHOW_START)});')

# 字幕
for k in SUBS:
    st = S[k]; du = D[k]
    js.append(f'tl.fromTo("#sub_{k}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.42,ease:"power2.out"}},{f(st)});')
    js.append(f'tl.to("#sub_{k}",{{opacity:0,y:-8,duration:0.42,ease:"power1.in"}},{f(st+du+0.08)});')
    js.append(f'tl.set("#sub_{k}",{{opacity:0}},{f(st+du+0.5)});')

# 开头 CD：淡入淡出 + 转动
js.append('tl.fromTo("#opcd",{opacity:0},{opacity:1,duration:1.6,ease:"power1.inOut"},6.0);')
js.append(f'tl.to("#opcd",{{opacity:0,duration:1.8,ease:"power1.in"}},{f(OPEN_END-2.0)});')
js.append(f'tl.set("#opcd",{{opacity:0}},{f(OPEN_END)});')
js.append('tl.fromTo(".ov-cd",{rotation:0},{rotation:300,duration:34.0,ease:"none"},6.0);')

# 屏幕文字 A（声音系统）整体淡入
sA = OPEN_END-9.0
js.append(f'tl.fromTo("#screenA",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.6,ease:"power2.out"}},{f(sA)});')
js.append(f'tl.to("#screenA",{{opacity:0,y:-10,duration:0.7,ease:"power1.in"}},{f(sA+5.0)});')
js.append(f'tl.set("#screenA",{{opacity:0}},{f(sA+6.4)});')

# 番号歌名卡
js.append(fade('#title_rj', 0.7, ENTRY+0.3, 9.0, 1.0, ease="power2.out"))
js.append(f'tl.fromTo("#title_rj .sc-name",{{letterSpacing:"0.26em",opacity:0}},{{letterSpacing:"0.08em",opacity:1,duration:1.0,ease:"power3.out"}},{f(ENTRY+0.5)});')
js.append(f'tl.fromTo("#title_rj .sc-no",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},{f(ENTRY+0.35)});')
# 角标
js.append(f'tl.fromTo("#tag_rj",{{opacity:0,x:-14}},{{opacity:1,x:0,duration:0.7,ease:"power2.out"}},{f(TAG_START)});')
js.append(f'tl.to("#tag_rj",{{opacity:0,duration:0.8,ease:"power1.in"}},{f(TR_START-0.4)});')
js.append(f'tl.set("#tag_rj",{{opacity:0}},{f(TR_START)});')
# 屏幕文字 B 整体淡入
js.append(f'tl.fromTo("#screenB",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.8,ease:"power2.out"}},{f(SB_START)});')
js.append(f'tl.to("#screenB",{{opacity:0,y:-10,duration:0.9,ease:"power1.in"}},{f(SB_START+7.0)});')
js.append(f'tl.set("#screenB",{{opacity:0}},{f(SB_START+8.5)});')
# 转场卡（整体淡入防半截）
js.append(f'tl.fromTo("#trans",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},{f(TR_START+0.2)});')
js.append(f'tl.to("#trans",{{opacity:1,duration:0.1}},{f(TOTAL-0.3)});')
# grain 轻微闪烁
js.append('tl.fromTo("#grain",{opacity:.08},{opacity:.13,duration:2.2,yoyo:true,repeat:48,ease:"sine.inOut"},0);')

JS = "\n".join(js)

html = f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Chakra+Petch:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
    {html_blocks}
    {chrome}
    {op_cd}
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
Path("hf/meta.json").write_text('{"id":"main","name":"chenwei-elva-sample"}', encoding="utf-8")
print("index.html:", len(html), "bytes ; TOTAL", TOTAL)
