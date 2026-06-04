#!/usr/bin/env python3
"""生成竖屏 1080x1920 HyperFrames composition (index.html) - V3 美术升级版。
跑：python3 scripts/build.py  → 写出 ../index.html"""
import json
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
NARR = json.loads((PROJ / 'narration.json').read_text())

# ===== 全片时间线（V4：封面压到 5.5s，开头从 t=5 起进入主内容）=====
SECTIONS = {
    'cover':  (0,     5.5),
    'open3':  (5.5,   15.5),
    'title':  (15.5,  29.5),
    'ch1':    (29.5,  76.5),
    'trans1': (76.5,  89.5),
    'ch2':    (89.5,  143.5),
    'trans2': (143.5, 156.5),
    'ch3':    (156.5, 203.5),
    'three':  (203.5, 246.5),
    'outro':  (246.5, 276.5),
    'cta':    (276.5, 289.5),
}
TOTAL = SECTIONS['cta'][1]  # 289.5s = 4:49.5

TTS_AT = {
    's01_open':     ('cover',  1.0),    # V4：cover 起 1s 即起口播，避免开头静默
    's02_three':    ('open3',  0.5),
    's03_title':    ('title',  1.0),
    's04_douwei':   ('ch1',    1.8),
    's05_trans1':   ('trans1', 1.2),
    's06_faye':     ('ch2',    1.8),
    's07_trans2':   ('trans2', 1.2),
    's08_jingtong': ('ch3',    1.8),
    's09_three_p':  ('three',  1.0),
    's10_outro':    ('outro',  1.5),
    's11_cta':      ('cta',    0.8),
}
def abs_t(sec_key, offset):
    s, e = SECTIONS[sec_key]
    return s + offset

# ===== 字幕（含主文案+副文案）=====
CAPTIONS = [
    (abs_t('open3', 0.5),  9.0,  '同一首歌，',  '三种人生。'),
    (abs_t('ch1',   1.6),  6.0,  '01 窦唯',     '原点 ｜ 年轻时的热烈'),
    (abs_t('ch2',   1.6),  6.5,  '02 王菲',     '回声 ｜ 把摇滚唱得很轻'),
    (abs_t('ch3',   1.6),  6.5,  '03 窦靖童',   '接住 ｜ 她没有复制谁'),
    (abs_t('three', 1.0),  41.0, '同一首歌，', '三种气质，三种人生。'),
    # V4: outro caption 缩短至 TTS 结束附近，避免与 outro hero 重叠
    (abs_t('outro', 1.5),  11.0, '有些歌不是被翻唱，', '是被时间，慢慢唱完。'),
    (abs_t('cta',   1.0),  12.0, '你最喜欢哪一个版本？', '评论区聊聊。'),
]

# ===== Footage（章节主素材 + outro 延长版）=====
FOOTAGE = [
    (abs_t('open3', 0.0),  3.0,  'clips/clip_dw_open.mp4',  0, 'open-dw'),
    (abs_t('open3', 3.0),  3.0,  'clips/clip_fw_open.mp4',  6, 'open-fw'),
    (abs_t('open3', 6.0),  3.0,  'clips/clip_jt_open.mp4',  0, 'open-jt'),
    # ch1 / ch2 / ch3 主 footage
    (abs_t('ch1', 0.0),    47.0, 'clips/clip_dw_main.mp4',  6, 'ch1-dw'),
    (abs_t('ch2', 0.0),    54.0, 'clips/clip_fw_main.mp4',  0, 'ch2-fw'),
    (abs_t('ch3', 0.0),    47.0, 'clips/clip_jt_main.mp4',  6, 'ch3-jt'),
    # outro montage：延长每段到 13s 让画面 fill 到 285（避免黑屏）
    (abs_t('outro', 0.5),  13.0, 'clips/clip_dw_main.mp4',  0, 'out-dw'),
    (abs_t('outro', 11.5), 13.0, 'clips/clip_fw_main.mp4',  6, 'out-fw'),
    (abs_t('outro', 22.0), 8.0,  'clips/clip_jt_main.mp4',  0, 'out-jt'),  # 277-285 → 与 CTA 衔接
]

THREE_BANDS = [
    (abs_t('three', 0.0), 43.0, 'clips/clip_dw_three.mp4', 1, 'three-dw', 'top'),
    (abs_t('three', 0.0), 43.0, 'clips/clip_fw_three.mp4', 2, 'three-fw', 'mid'),
    (abs_t('three', 0.0), 43.0, 'clips/clip_jt_three.mp4', 3, 'three-jt', 'bot'),
]

TTS_ELEMENTS = []
for key, (sec, off) in TTS_AT.items():
    TTS_ELEMENTS.append((abs_t(sec, off), NARR[key]['dur'], f'voice/{key}.wav', key))

def fmt(x):
    return f'{x:.3f}'.rstrip('0').rstrip('.')

# ---- footage video tags
footage_html = []
for start, dur, src, tk, eid in FOOTAGE:
    footage_html.append(
        f'<video id="{eid}" class="clip footage" '
        f'data-start="{fmt(start)}" data-duration="{fmt(dur)}" data-track-index="{tk}" '
        f'src="{src}" muted playsinline preload="auto"></video>'
    )

three_html = []
for start, dur, src, tk, eid, band in THREE_BANDS:
    three_html.append(
        f'<video id="{eid}" class="clip three-band three-{band}" '
        f'data-start="{fmt(start)}" data-duration="{fmt(dur)}" data-track-index="{tk}" '
        f'src="{src}" muted playsinline preload="auto"></video>'
    )

# ---- chapter labels 升级：番号 / 名 / role / 装饰线 三段 stagger
CHAPTERS = [
    (abs_t('ch1', 0.8), 6.0, '01', '窦唯',   '原点',   'ch1-label', 'dw'),
    (abs_t('ch2', 0.8), 6.0, '02', '王菲',   '回声',   'ch2-label', 'fw'),
    (abs_t('ch3', 0.8), 6.0, '03', '窦靖童', '接住',   'ch3-label', 'jt'),
]
label_html = []
for start, dur, num, name, role, eid, theme in CHAPTERS:
    label_html.append(
        f'<div id="{eid}" class="clip chapter-label theme-{theme}" '
        f'data-start="{fmt(start)}" data-duration="{fmt(dur)}" data-track-index="7">'
        f'<div class="ch-rail"></div>'
        f'<div class="ch-num">{num}</div>'
        f'<div class="ch-meta">'
        f'  <div class="ch-name">{name}</div>'
        f'  <div class="ch-role">{role}</div>'
        f'</div>'
        f'</div>'
    )

# ---- captions
cap_html = []
for i, (start, dur, l1, l2) in enumerate(CAPTIONS):
    track = 8 if i % 2 == 0 else 9
    cap_html.append(
        f'<div id="cap-{i}" class="clip caption" '
        f'data-start="{fmt(start)}" data-duration="{fmt(dur)}" data-track-index="{track}">'
        f'<div class="cap-l1">{l1}</div>'
        f'<div class="cap-l2">{l2}</div>'
        f'</div>'
    )

# ---- TTS audio
audio_html = []
for start, dur, src, key in TTS_ELEMENTS:
    audio_html.append(
        f'<audio id="aud-{key}" class="clip tts" '
        f'data-start="{fmt(start)}" data-duration="{fmt(dur)}" data-track-index="20" '
        f'src="{src}" preload="auto"></audio>'
    )

# ---- 标题卡 (24-38s)：年份带在上 + hero 在下，垂直分离不重叠
title_card = (
    f'<div id="title-card" class="clip title-card" '
    f'data-start="{fmt(abs_t("title", 0.0))}" data-duration="14.0" data-track-index="6">'
    f'<div class="tc-top">'
    f'  <div class="tc-years">'
    f'    <span class="yr yr1"><span class="yrnum">1991</span><span class="yrsep">/</span><span class="yrnum">92</span></span>'
    f'    <span class="yrdot">·</span>'
    f'    <span class="yr yr2"><span class="yrnum">1999</span></span>'
    f'    <span class="yrdot">·</span>'
    f'    <span class="yr yr3"><span class="yrnum">2026</span></span>'
    f'  </div>'
    f'  <svg class="tc-sine" viewBox="0 0 900 40" preserveAspectRatio="none">'
    f'    <path d="M0,20 Q112,4 225,20 T450,20 T675,20 T900,20" stroke="url(#sineGrad)" stroke-width="1.5" fill="none"/>'
    f'    <defs><linearGradient id="sineGrad" x1="0" x2="1"><stop offset="0" stop-color="#d4a574"/><stop offset=".5" stop-color="#c8d4e2"/><stop offset="1" stop-color="#a896d4"/></linearGradient></defs>'
    f'  </svg>'
    f'</div>'
    f'<div class="tc-hero">'
    f'  <div class="th-l">一首歌</div>'
    f'  <div class="th-l">三个人</div>'
    f'  <div class="th-l ital">三段回声</div>'
    f'</div>'
    f'<div class="tc-foot">echoes of a song</div>'
    f'</div>'
)

# ---- 转场卡 1 / 2 ：诗意大字 + 年份小字
def transition_card(eid, start, dur, big_l1, big_l2, year_from, year_to):
    return (
        f'<div id="{eid}" class="clip trans-card" '
        f'data-start="{fmt(start)}" data-duration="{fmt(dur)}" data-track-index="6">'
        f'<div class="tr-years">'
        f'  <span class="tr-yr-from">{year_from}</span>'
        f'  <span class="tr-arrow"></span>'
        f'  <span class="tr-yr-to">{year_to}</span>'
        f'</div>'
        f'<div class="tr-hero">'
        f'  <div class="trh-l">{big_l1}</div>'
        f'  <div class="trh-l ital">{big_l2}</div>'
        f'</div>'
        f'<div class="tr-deco">'
        f'  <svg viewBox="0 0 600 6"><line x1="0" y1="3" x2="600" y2="3" stroke="url(#trGrad)" stroke-width="1"/>'
        f'    <defs><linearGradient id="trGrad" x1="0" x2="1"><stop offset="0" stop-color="transparent"/><stop offset=".5" stop-color="#e8e2d4"/><stop offset="1" stop-color="transparent"/></linearGradient></defs>'
        f'  </svg>'
        f'</div>'
        f'</div>'
    )
trans1_card = transition_card('trans1-card', abs_t('trans1', 0.0), 13.0,
    '几年后，', '它换了一个声音继续往前。',
    '1991 / 92', '1999')
trans2_card = transition_card('trans2-card', abs_t('trans2', 0.0), 13.0,
    '再后来，', '女儿也唱起了这首歌。',
    '1999', '2026')

# ---- Outro hero（270-285）+ 后景持续 footage 不留黑
outro_hero = (
    f'<div id="outro-hero" class="clip outro-hero" '
    f'data-start="{fmt(abs_t("outro", 15.0))}" data-duration="14.5" data-track-index="11">'
    f'<div class="oh-quote">'
    f'  <div class="oh-l">同一首歌，</div>'
    f'  <div class="oh-l">三种气质。</div>'
    f'</div>'
    f'<div class="oh-tags"><span class="tag-amber">热烈</span><span class="oh-sep">/</span>'
    f'<span class="tag-silver">回声</span><span class="oh-sep">/</span><span class="tag-violet">松弛</span></div>'
    f'</div>'
)

# ---- CTA（删 fair 行；加优雅卡片风）
cta_panel = (
    f'<div id="cta-panel" class="clip cta-panel" '
    f'data-start="{fmt(abs_t("cta", 0.0))}" data-duration="13.0" data-track-index="12">'
    f'<div class="cta-inner">'
    f'  <div class="cta-mark">— ENDING —</div>'
    f'  <div class="cta-q">你最喜欢，</div>'
    f'  <div class="cta-q-em ital">哪一个版本？</div>'
    f'  <div class="cta-rule"></div>'
    f'  <div class="cta-credit">'
    f'    <div class="cta-credit-label">素材出处</div>'
    f'    <div class="cta-credit-line">黑豹 ·《Don\'t Break My Heart》Official MV</div>'
    f'    <div class="cta-credit-line">王菲 · 1999 唱游大世界 日本武道馆</div>'
    f'    <div class="cta-credit-line">窦靖童 ·《歌手 2026》</div>'
    f'  </div>'
    f'</div>'
    f'</div>'
)

# ---- 三人同屏 overlay
three_overlay = (
    f'<div id="three-overlay" class="clip three-overlay" '
    f'data-start="{fmt(abs_t("three", 0.0))}" data-duration="43.0" data-track-index="13">'
    f'<div class="three-tag tag-dw"><div class="tt-name">窦唯</div><div class="tt-role">热烈</div></div>'
    f'<div class="three-tag tag-fw"><div class="tt-name">王菲</div><div class="tt-role">空灵</div></div>'
    f'<div class="three-tag tag-jt"><div class="tt-name">窦靖童</div><div class="tt-role">松弛</div></div>'
    f'<svg class="three-divider" viewBox="0 0 1080 1920" preserveAspectRatio="none">'
    f'  <line x1="0" y1="640" x2="1080" y2="640" stroke="rgba(232,226,212,.18)" stroke-width="0.8" stroke-dasharray="4,8"/>'
    f'  <line x1="0" y1="1280" x2="1080" y2="1280" stroke="rgba(232,226,212,.18)" stroke-width="0.8" stroke-dasharray="4,8"/>'
    f'</svg>'
    f'</div>'
)

# ---- Cold open 三人冻结（V4：cold open 末 1.9s）
FT_START = abs_t('open3', 8.1)  # 5.5 + 8.1 = 13.6
freeze_trio = (
    f'<div id="freeze-trio" class="clip freeze-trio" '
    f'data-start="{fmt(FT_START)}" data-duration="1.9" data-track-index="11">'
    f'<div class="ft-row">'
    f'  <div class="ft-card ft-dw" style="background-image:url(\'cover/final_douwei_clean.jpg\')"></div>'
    f'  <div class="ft-card ft-fw" style="background-image:url(\'cover/final_faye_clean.jpg\')"></div>'
    f'  <div class="ft-card ft-jt" style="background-image:url(\'cover/final_jingtong_clean.jpg\')"></div>'
    f'</div>'
    f'<div class="ft-cap"><span>同一首歌</span><span class="ft-sep">｜</span><span>三种人生</span></div>'
    f'</div>'
)

# ---- 全片暗角 scrim
scrim_html = (
    f'<div id="global-scrim" class="clip global-scrim" '
    f'data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="5"></div>'
)

# ---- Progress bar（开头 cover 不显示，从 cold open 起）
PB_START = SECTIONS['open3'][0]
progress_html = (
    f'<div id="progress" class="clip progress-bar" '
    f'data-start="{fmt(PB_START)}" data-duration="{fmt(TOTAL-PB_START)}" data-track-index="14">'
    f'<div class="pb-fill"></div></div>'
)

# ---- Cover layer (V4: 0-5.5s 快节奏入场)
cover_html = f"""
<div id="cover" class="clip cover-root" data-start="0" data-duration="{fmt(SECTIONS['cover'][1])}" data-track-index="2">
  <div class="cover-bg"></div>
  <svg class="cover-noise" preserveAspectRatio="none" viewBox="0 0 1080 1920">
    <filter id="nz"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="3"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .055 0"/></filter>
    <rect width="1080" height="1920" filter="url(#nz)"/>
  </svg>
  <svg class="cover-wave" viewBox="0 0 1080 1920" preserveAspectRatio="none">
    <path d="M0,1620 Q270,1570 540,1620 T1080,1620" stroke="#3b4a78" stroke-width="1.5" fill="none" opacity=".5"/>
    <path d="M0,1660 Q270,1610 540,1660 T1080,1660" stroke="#4d5e8c" stroke-width="1"   fill="none" opacity=".4"/>
    <path d="M0,1700 Q270,1650 540,1700 T1080,1700" stroke="#2a3a60" stroke-width="1"   fill="none" opacity=".35"/>
  </svg>

  <svg class="cover-connect" viewBox="0 0 1080 1920" preserveAspectRatio="none">
    <defs>
      <linearGradient id="cgrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0"   stop-color="#d4a574"/>
        <stop offset=".55" stop-color="#a8b8c8"/>
        <stop offset="1"   stop-color="#9b86d4"/>
      </linearGradient>
      <filter id="glow"><feGaussianBlur stdDeviation="4"/></filter>
    </defs>
    <path class="cover-path" d="M 230 180 Q 540 340 540 540 T 760 990"
          stroke="url(#cgrad)" stroke-width="2.5" fill="none" filter="url(#glow)" opacity="0"
          stroke-dasharray="900" stroke-dashoffset="900"/>
    <circle class="cover-dot dot-dw" cx="230" cy="180" r="6" fill="#d4a574" opacity="0"/>
    <circle class="cover-dot dot-fw" cx="540" cy="540" r="7" fill="#a8b8c8" opacity="0"/>
    <circle class="cover-dot dot-jt" cx="760" cy="990" r="6" fill="#9b86d4" opacity="0"/>
  </svg>

  <div class="cv-card cv-dw" id="cv-dw"
       style="background-image:url('cover/final_douwei_clean.jpg')">
    <div class="cv-tint"></div>
    <div class="cv-label"><span class="cv-name">窦唯</span><span class="cv-bar">／</span><span class="cv-role">原点</span></div>
    <div class="cv-year">1991 / 92</div>
  </div>
  <div class="cv-card cv-fw" id="cv-fw"
       style="background-image:url('cover/final_faye_clean.jpg')">
    <div class="cv-tint"></div>
    <div class="cv-label"><span class="cv-name">王菲</span><span class="cv-bar">／</span><span class="cv-role">回声</span></div>
    <div class="cv-year">1999</div>
  </div>
  <div class="cv-card cv-jt" id="cv-jt"
       style="background-image:url('cover/final_jingtong_clean.jpg')">
    <div class="cv-tint"></div>
    <div class="cv-label"><span class="cv-name">窦靖童</span><span class="cv-bar">／</span><span class="cv-role">接住</span></div>
    <div class="cv-year">2026</div>
  </div>

  <div class="cover-title">
    <div class="ct-tag">FAMILY · ONE SONG</div>
    <div class="ct-line ct1"><span class="word">一家</span><span class="word">三口</span></div>
    <div class="ct-line ct2"><span class="word">同唱</span><span class="word">一首歌</span></div>
    <div class="ct-song">DON&rsquo;T BREAK MY HEART</div>
    <div class="ct-sub"><span class="cs-name">窦唯</span><span class="cs-slash">／</span><span class="cs-name">王菲</span><span class="cs-slash">／</span><span class="cs-name">窦靖童</span></div>
  </div>
</div>
"""

# ================== 组装完整 HTML ==================
HTML = f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<!-- 字体（Google Fonts；hyperframes 渲染时会自动 inline+cache） -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@300;400;500;600;700&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js" integrity="sha384-sG0Hv1tP1lZCk9KQmrIbY/XNwi+OY84GQqhMscbnsoBFqAz8KNCil1kvfL3Hbbk2" crossorigin="anonymous"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#05060c;
  font-family:'Noto Sans SC','Inter',-apple-system,'Helvetica Neue',sans-serif;
  color:#e8e6dc;-webkit-font-smoothing:antialiased;}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#05060c}}

/* design tokens */
:root{{
  --gold:#d4a574;
  --silver:#c8d4e2;
  --violet:#a896d4;
  --paper:#f3ebd6;
  --paper-dim:#cfcab8;
  --ink:#e8e6dc;
  --ink-dim:#9aa1b5;
  --serif:'Noto Serif SC','Cormorant Garamond','Times New Roman',serif;
  --sans:'Noto Sans SC','Inter',-apple-system,sans-serif;
  --mono:'JetBrains Mono','SF Mono',monospace;
  --italic-serif:'Cormorant Garamond','Noto Serif SC',serif;
}}
.ital{{font-family:var(--italic-serif);font-style:italic;font-weight:300}}

/* ---------- 全片底层 ---------- */
.footage{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:5}}
.global-scrim{{position:absolute;inset:0;width:1080px;height:1920px;
  background:radial-gradient(120% 90% at 50% 60%, transparent 35%, rgba(0,0,0,.42) 75%, rgba(0,0,0,.7) 100%);
  z-index:10;pointer-events:none}}

/* ---------- Cover ---------- */
.cover-root{{position:absolute;inset:0;width:1080px;height:1920px;z-index:80}}
.cover-bg{{position:absolute;inset:0;background:
  radial-gradient(58% 48% at 50% 18%, #14264a 0%, #0a1228 40%, #050912 75%, #02030a 100%),
  linear-gradient(180deg,#060a18 0%, #03050d 100%);}}
.cover-noise{{position:absolute;inset:0;mix-blend-mode:overlay;opacity:.55;pointer-events:none}}
.cover-wave{{position:absolute;inset:0;opacity:.55;pointer-events:none}}
.cover-connect{{position:absolute;inset:0;pointer-events:none;z-index:2}}

.cv-card{{position:absolute;background-size:cover;background-position:center;border-radius:14px;overflow:hidden;
  box-shadow:0 30px 60px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.06);}}
.cv-card .cv-tint{{position:absolute;inset:0}}
.cv-card .cv-label{{position:absolute;left:20px;bottom:18px;display:flex;align-items:baseline;gap:8px;
  font-family:var(--serif);font-size:30px;font-weight:500;letter-spacing:4px;
  text-shadow:0 2px 10px rgba(0,0,0,.88)}}
.cv-card .cv-name{{font-weight:600}}
.cv-card .cv-bar{{opacity:.55;font-size:22px}}
.cv-card .cv-role{{font-weight:400;opacity:.92;font-size:26px}}
.cv-card .cv-year{{position:absolute;right:18px;top:14px;font-family:var(--mono);font-size:16px;letter-spacing:3px;
  opacity:.62;text-shadow:0 1px 4px #000}}

.cv-dw{{left:60px;top:20px;width:380px;height:540px;}}
.cv-dw .cv-tint{{background:linear-gradient(140deg, rgba(139,0,0,.42), rgba(60,18,0,.5) 65%, rgba(20,8,4,.6))}}
.cv-dw .cv-label{{color:#f3c987}}

.cv-fw{{left:340px;top:300px;width:560px;height:780px;
  filter:saturate(.5) contrast(1.08) brightness(.94);
  box-shadow:0 40px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(168,184,200,.18), 0 0 60px rgba(168,184,200,.12)}}
.cv-fw .cv-tint{{background:
  linear-gradient(155deg, rgba(168,184,200,.28) 0%, rgba(110,135,165,.32) 55%, rgba(18,28,46,.55) 100%),
  linear-gradient(0deg, rgba(40,55,80,.42), rgba(40,55,80,.42));
  mix-blend-mode:multiply}}
.cv-fw .cv-label{{color:#e8edf3}}

.cv-jt{{left:540px;top:810px;width:430px;height:600px;}}
.cv-jt .cv-tint{{background:
  linear-gradient(165deg, rgba(91,76,138,.35), rgba(60,55,110,.45) 60%, rgba(15,18,36,.6));
  mix-blend-mode:multiply}}
.cv-jt::after{{content:'';position:absolute;inset:0;
  background:
    linear-gradient(225deg, rgba(0,0,0,.98) 0%, rgba(0,0,0,.85) 18%, rgba(0,0,0,.55) 30%, transparent 50%),
    radial-gradient(70% 50% at 100% 0%, rgba(0,0,0,.92) 0%, rgba(0,0,0,.4) 35%, transparent 60%)}}
.cv-jt .cv-label{{color:#d5cae8}}

.cover-title{{position:absolute;left:0;right:0;bottom:62px;text-align:center;z-index:5}}
.ct-tag{{font-family:var(--mono);font-size:14px;letter-spacing:10px;color:var(--gold);opacity:.78;margin-bottom:24px}}
.ct-line{{font-family:var(--serif);font-weight:700;letter-spacing:18px;line-height:1.05;color:var(--paper);
  text-shadow:0 4px 18px rgba(0,0,0,.5);display:flex;justify-content:center;gap:18px}}
.ct1{{font-size:96px}}
.ct2{{font-size:96px;margin-top:6px}}
.ct-line .word{{display:inline-block}}
.ct-song{{margin-top:30px;font-family:'Cormorant Garamond',serif;font-style:italic;font-weight:300;
  font-size:42px;letter-spacing:6px;
  background:linear-gradient(90deg,var(--gold) 0%,#e8edf3 50%,var(--violet) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  filter:drop-shadow(0 2px 18px rgba(212,165,116,.25))}}
.ct-sub{{margin-top:20px;font-family:var(--serif);font-size:22px;letter-spacing:10px;color:var(--paper-dim);
  display:flex;justify-content:center;gap:14px;align-items:baseline}}
.cs-slash{{color:#5f6680;opacity:.7;font-size:18px}}
.cs-name{{font-weight:400}}

/* ---------- Chapter labels (左上铁路侧栏 + 番号 + 名/role) ---------- */
.chapter-label{{position:absolute;left:50px;top:120px;display:grid;grid-template-columns:auto auto;align-items:end;gap:24px;
  z-index:60;text-shadow:0 2px 14px rgba(0,0,0,.75)}}
.chapter-label .ch-rail{{position:absolute;left:-26px;top:32px;width:2px;height:84px;
  background:linear-gradient(180deg,transparent 0%,currentColor 30%,currentColor 70%,transparent 100%);
  opacity:.55}}
.chapter-label .ch-num{{font-family:var(--mono);font-weight:300;font-size:120px;line-height:.9;letter-spacing:-4px;
  color:currentColor;opacity:.92}}
.chapter-label .ch-meta{{padding-bottom:12px;display:flex;flex-direction:column;gap:6px}}
.chapter-label .ch-name{{font-family:var(--serif);font-size:54px;font-weight:600;letter-spacing:10px;line-height:1;
  color:currentColor}}
.chapter-label .ch-role{{font-family:var(--mono);font-size:18px;letter-spacing:8px;color:currentColor;opacity:.78;
  text-transform:uppercase}}
.chapter-label .ch-role::before{{content:'— ';opacity:.55}}
.theme-dw{{color:#f3c987}}
.theme-fw{{color:#e3ecf6}}
.theme-jt{{color:#dccef0}}

/* ---------- Captions: 左下偏移、字体衬线、上下排错 ---------- */
.caption{{position:absolute;left:60px;right:60px;bottom:280px;z-index:55;text-align:left}}
.cap-l1{{font-family:var(--serif);font-size:62px;font-weight:600;letter-spacing:6px;line-height:1.22;
  color:var(--paper);text-shadow:0 4px 16px rgba(0,0,0,.78)}}
.cap-l2{{font-family:var(--serif);font-size:38px;font-weight:400;letter-spacing:5px;line-height:1.3;margin-top:14px;
  color:var(--paper-dim);text-shadow:0 4px 16px rgba(0,0,0,.78);opacity:.92}}

/* ---------- Title card (24-38s)：年份在上 + hero 在下 ---------- */
.title-card{{position:absolute;inset:0;z-index:65;
  background:radial-gradient(55% 60% at 50% 45%, #0b1428 0%, #050912 70%, #02030a 100%);
  display:flex;flex-direction:column;justify-content:space-between;padding:340px 80px 280px}}
.tc-top{{display:flex;flex-direction:column;align-items:center;gap:34px}}
.tc-years{{display:flex;align-items:baseline;gap:30px;font-family:var(--mono);font-weight:300}}
.tc-years .yr{{font-size:46px;letter-spacing:4px;color:var(--ink);display:inline-flex;align-items:baseline}}
.tc-years .yrnum{{}}
.tc-years .yrsep{{opacity:.45;margin:0 2px}}
.tc-years .yrdot{{font-size:30px;opacity:.4}}
.tc-years .yr1{{color:#f3c987}}
.tc-years .yr2{{color:#e3ecf6}}
.tc-years .yr3{{color:#dccef0}}
.tc-sine{{width:520px;height:34px;opacity:.6}}
.tc-hero{{display:flex;flex-direction:column;align-items:center;gap:0px}}
.tc-hero .th-l{{font-family:var(--serif);font-size:120px;font-weight:700;letter-spacing:24px;line-height:1.05;
  color:var(--paper);text-shadow:0 4px 22px rgba(0,0,0,.55)}}
.tc-hero .th-l.ital{{font-size:96px;letter-spacing:14px;font-weight:400;color:var(--gold);margin-top:10px}}
.tc-foot{{position:absolute;left:0;right:0;bottom:160px;text-align:center;
  font-family:'Cormorant Garamond',serif;font-style:italic;font-size:24px;letter-spacing:8px;color:var(--ink-dim);opacity:.55}}

/* ---------- Transition card ---------- */
.trans-card{{position:absolute;inset:0;z-index:65;
  background:radial-gradient(55% 55% at 50% 48%, #0a1226 0%, #050913 70%, #02040c 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 80px;gap:40px}}
.tr-years{{font-family:var(--mono);font-weight:300;font-size:30px;letter-spacing:6px;color:var(--ink-dim);
  display:flex;align-items:center;gap:24px;opacity:.75}}
.tr-yr-from{{}}
.tr-arrow{{width:140px;height:1px;background:linear-gradient(90deg,transparent,var(--paper),transparent);position:relative}}
.tr-arrow::after{{content:'';position:absolute;right:0;top:50%;width:8px;height:8px;border-right:1px solid var(--paper);
  border-top:1px solid var(--paper);transform:translateY(-50%) rotate(45deg)}}
.tr-yr-to{{color:var(--paper)}}
.tr-hero{{display:flex;flex-direction:column;align-items:center;gap:14px;text-align:center}}
.trh-l{{font-family:var(--serif);font-size:78px;font-weight:600;letter-spacing:14px;color:var(--paper);
  text-shadow:0 4px 18px rgba(0,0,0,.6);line-height:1.18}}
.trh-l.ital{{font-size:62px;letter-spacing:8px;font-weight:400;color:var(--paper-dim)}}
.tr-deco{{width:480px;opacity:.5}}

/* ---------- Three-up ---------- */
.three-band{{position:absolute;left:0;width:1080px;object-fit:cover;z-index:6;
  box-shadow:0 0 0 1px rgba(255,255,255,.04) inset}}
.three-top{{top:0;height:640px;}}
.three-mid{{top:640px;height:640px;}}
.three-bot{{top:1280px;height:640px;}}
.three-overlay{{position:absolute;inset:0;z-index:50;pointer-events:none}}
.three-divider{{position:absolute;inset:0;opacity:.85}}
.three-tag{{position:absolute;display:flex;align-items:baseline;gap:14px;
  padding:14px 22px;border-radius:0;background:rgba(6,8,16,.55);backdrop-filter:blur(10px);
  border-left:3px solid currentColor;border-top:1px solid rgba(255,255,255,.05)}}
.three-tag .tt-name{{font-family:var(--serif);font-size:34px;font-weight:600;letter-spacing:8px;color:currentColor}}
.three-tag .tt-role{{font-family:var(--mono);font-size:18px;letter-spacing:6px;opacity:.82;color:currentColor;text-transform:uppercase}}
.tag-dw{{left:40px;top:34px;color:#f3c987}}
.tag-fw{{left:40px;top:674px;color:#dde6f0}}
.tag-jt{{left:40px;top:1314px;color:#dccef0}}

/* ---------- Outro hero ---------- */
.outro-hero{{position:absolute;left:0;right:0;bottom:240px;z-index:70;pointer-events:none;
  text-align:center;padding:0 80px}}
.oh-quote{{display:flex;flex-direction:column;align-items:center;gap:8px}}
.oh-l{{font-family:var(--serif);font-size:96px;font-weight:700;letter-spacing:18px;color:var(--paper);
  text-shadow:0 4px 22px rgba(0,0,0,.7);line-height:1.08}}
.oh-l:nth-child(2){{font-style:italic;font-family:'Cormorant Garamond',var(--serif);font-weight:500;letter-spacing:12px;color:var(--gold)}}
.oh-tags{{margin-top:50px;font-family:var(--serif);font-size:32px;letter-spacing:10px;color:var(--paper-dim);
  display:flex;justify-content:center;align-items:center;gap:14px}}
.oh-tags .tag-amber{{color:var(--gold)}}
.oh-tags .tag-silver{{color:#dde6f0}}
.oh-tags .tag-violet{{color:var(--violet)}}
.oh-tags .oh-sep{{opacity:.4;font-size:24px}}

/* ---------- CTA ---------- */
.cta-panel{{position:absolute;inset:0;display:flex;justify-content:center;align-items:center;
  z-index:80;background:linear-gradient(180deg,#02040a 0%,#070b16 50%,#02040a 100%);padding:120px 80px}}
.cta-inner{{display:flex;flex-direction:column;align-items:center;text-align:center;width:100%}}
.cta-mark{{font-family:var(--mono);font-size:16px;letter-spacing:14px;color:var(--gold);opacity:.7;margin-bottom:64px}}
.cta-q{{font-family:var(--serif);font-size:76px;font-weight:600;letter-spacing:12px;color:var(--paper);line-height:1.18}}
.cta-q-em{{font-family:'Cormorant Garamond',var(--serif);font-style:italic;font-size:96px;letter-spacing:6px;color:var(--gold);margin-top:12px;font-weight:400}}
.cta-rule{{width:120px;height:1px;background:linear-gradient(90deg,transparent,var(--paper-dim),transparent);
  margin:80px 0 60px}}
.cta-credit{{font-family:var(--serif);font-size:22px;letter-spacing:4px;color:var(--ink-dim);line-height:2}}
.cta-credit-label{{font-family:var(--mono);font-size:14px;letter-spacing:10px;color:var(--gold);opacity:.7;margin-bottom:18px}}
.cta-credit-line{{}}

/* ---------- Freeze trio (22.1-24) ---------- */
.freeze-trio{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
  align-items:center;z-index:75;background:radial-gradient(50% 60% at 50% 50%, #0a1126, #03050d 80%)}}
.freeze-trio .ft-row{{display:flex;gap:20px;align-items:center}}
.freeze-trio .ft-card{{width:300px;height:480px;background-size:cover;background-position:center;border-radius:14px;
  box-shadow:0 28px 50px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.05)}}
.freeze-trio .ft-dw{{filter:saturate(1.15) brightness(.95)}}
.freeze-trio .ft-fw{{filter:saturate(.55) brightness(.96);transform:translateY(-14px) scale(1.04)}}
.freeze-trio .ft-jt{{filter:saturate(.85) brightness(.95)}}
.freeze-trio .ft-cap{{margin-top:56px;font-family:var(--serif);font-size:44px;font-weight:600;letter-spacing:14px;color:var(--paper);
  text-shadow:0 4px 18px rgba(0,0,0,.7);display:flex;align-items:baseline;gap:16px}}
.freeze-trio .ft-sep{{color:var(--gold);font-size:30px;opacity:.7}}

/* ---------- Progress bar ---------- */
.progress-bar{{position:absolute;left:0;right:0;bottom:0;height:2px;z-index:90;background:rgba(255,255,255,.06)}}
.progress-bar .pb-fill{{height:100%;width:0;
  background:linear-gradient(90deg,#d4a574 0%,#a8b8c8 50%,#9b86d4 100%);
  box-shadow:0 0 8px rgba(168,184,200,.5)}}

audio{{display:none}}

</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">

  {scrim_html}

  <!-- footage -->
  {chr(10).join(footage_html)}

  <!-- three-up -->
  {chr(10).join(three_html)}
  {three_overlay}

  <!-- chapter labels -->
  {chr(10).join(label_html)}

  <!-- captions -->
  {chr(10).join(cap_html)}

  <!-- title card -->
  {title_card}

  <!-- transitions -->
  {trans1_card}
  {trans2_card}

  <!-- cold open freeze trio -->
  {freeze_trio}

  <!-- outro / cta -->
  {outro_hero}
  {cta_panel}

  <!-- progress bar -->
  {progress_html}

  <!-- TTS audio -->
  {chr(10).join(audio_html)}

  <!-- cover layer (last so it sits above on z-stack tie) -->
  {cover_html}

</div>

<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});

const TOTAL = {fmt(TOTAL)};
const S = {{
  cover:  {fmt(SECTIONS['cover'][0])},
  open3:  {fmt(SECTIONS['open3'][0])},
  title:  {fmt(SECTIONS['title'][0])},
  ch1:    {fmt(SECTIONS['ch1'][0])},
  trans1: {fmt(SECTIONS['trans1'][0])},
  ch2:    {fmt(SECTIONS['ch2'][0])},
  trans2: {fmt(SECTIONS['trans2'][0])},
  ch3:    {fmt(SECTIONS['ch3'][0])},
  three:  {fmt(SECTIONS['three'][0])},
  outro:  {fmt(SECTIONS['outro'][0])},
  cta:    {fmt(SECTIONS['cta'][0])},
}};
const E = {{
  cover:  {fmt(SECTIONS['cover'][1])},
  open3:  {fmt(SECTIONS['open3'][1])},
  title:  {fmt(SECTIONS['title'][1])},
  ch1:    {fmt(SECTIONS['ch1'][1])},
  trans1: {fmt(SECTIONS['trans1'][1])},
  ch2:    {fmt(SECTIONS['ch2'][1])},
  trans2: {fmt(SECTIONS['trans2'][1])},
  ch3:    {fmt(SECTIONS['ch3'][1])},
  three:  {fmt(SECTIONS['three'][1])},
  outro:  {fmt(SECTIONS['outro'][1])},
  cta:    {fmt(SECTIONS['cta'][1])},
}};

/* ===== COVER (0-5.5s) - V4 快节奏入场 =====
 * 0.0-0.5  真静止（第 1 帧即封面）
 * 0.5-2.0  时间线 SVG path 绘制 + 3 个发光点
 * 1.0-5.45 TTS s01_open（"有一首歌，被窦唯/王菲/窦靖童…"）
 * 2.0-3.5  标题字 stagger + 歌名
 * 3.5-5.0  微呼吸 / 强调
 * 5.0-5.5  退场
 */
// 初始：path/dots/cover-wave 隐藏，其他全显（封面 thumbnail-ready）
tl.set('.cover-path', {{ opacity: 0 }}, 0);
tl.set('.cover-dot', {{ opacity: 0, scale: 0 }}, 0);
tl.set('.cover-wave', {{ opacity: 0 }}, 0);

// 0.4s 起 wave fade-in
tl.to('.cover-wave', {{ opacity: .55, duration: 0.6, ease: 'sine.out' }}, 0.4);

// 0.5s 时间线 path draw（1.0s 内完成）
tl.to('.cover-path', {{ opacity: .75, duration: 0.3 }}, 0.5);
tl.to('.cover-path', {{ strokeDashoffset: 0, duration: 1.2, ease: 'power2.inOut' }}, 0.5);
tl.to('.dot-dw', {{ opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(2)' }}, 0.7);
tl.to('.dot-fw', {{ opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(2)' }}, 1.0);
tl.to('.dot-jt', {{ opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(2)' }}, 1.3);

// 卡片轻微缩放呼吸（不 reveal，全程可见）
tl.to('.cv-dw', {{ scale: 1.025, duration: 2.5, ease: 'sine.inOut' }}, 2.0);
tl.to('.cv-fw', {{ scale: 1.018, duration: 2.5, ease: 'sine.inOut' }}, 2.2);
tl.to('.cv-jt', {{ scale: 1.03,  duration: 2.5, ease: 'sine.inOut' }}, 2.4);

// 歌名 emphasize @ 2.5s（同步 TTS 念到歌手们）
tl.to('.ct-song', {{ filter: 'drop-shadow(0 2px 28px rgba(212,165,116,.55))', duration: 1.5, yoyo: true, repeat: 1 }}, 2.5);

// 5.0-5.5 退场
tl.to('#cover', {{ opacity: 0, scale: 1.04, duration: 0.5, ease: 'power2.in' }}, 5.0);
tl.set('#cover', {{ opacity: 0 }}, E.cover);

/* ===== Cold open 三连切 (5.5-15.5s) — 硬切 ===== */
['#open-dw','#open-fw','#open-jt'].forEach((sel, i) => {{
  const t = S.open3 + i*2.7;
  tl.set(sel, {{ opacity: 1, scale: 1 }}, t);
  tl.to(sel, {{ opacity: 0, duration: 0.35, ease: 'power2.in' }}, t + 2.4);
  tl.set(sel, {{ opacity: 0 }}, t + 2.75);
}});
// 三人冻结
const FT = S.open3 + 8.1;
tl.fromTo('#freeze-trio', {{ opacity: 0, scale: 1.03 }},
  {{ opacity: 1, scale: 1, duration: 0.55, ease: 'power2.out' }}, FT);
tl.fromTo('.ft-card', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.55, stagger: 0.1 }}, FT + 0.15);
tl.fromTo('.ft-cap span', {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.5, stagger: 0.08 }}, FT + 0.55);
tl.to('#freeze-trio', {{ opacity: 0, duration: 0.4 }}, FT + 1.5);
tl.set('#freeze-trio', {{ opacity: 0 }}, E.open3);

/* ===== Title card - 上 years + 下 hero ===== */
tl.fromTo('#title-card', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7 }}, S.title);
tl.fromTo('.tc-years .yr, .tc-years .yrdot', {{ opacity: 0, y: 18 }},
  {{ opacity: 1, y: 0, duration: 0.7, stagger: 0.14, ease: 'power2.out' }}, S.title + 0.4);
tl.fromTo('.tc-sine', {{ opacity: 0, scaleX: .6 }},
  {{ opacity: .6, scaleX: 1, duration: 1.0, ease: 'power2.out' }}, S.title + 1.4);
tl.fromTo('.tc-hero .th-l', {{ opacity: 0, y: 28 }},
  {{ opacity: 1, y: 0, duration: 0.9, stagger: 0.25, ease: 'power3.out' }}, S.title + 2.2);
tl.fromTo('.tc-foot', {{ opacity: 0 }}, {{ opacity: .55, duration: 1.0 }}, S.title + 4.5);
tl.to('#title-card', {{ opacity: 0, duration: 0.7 }}, E.title - 1.0);
tl.set('#title-card', {{ opacity: 0 }}, E.title);

/* ===== 章节 footage fade ===== */
function fadeClip(sel, atIn, atOut) {{
  tl.fromTo(sel, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7, ease: 'power2.out' }}, atIn);
  tl.to(sel,    {{ opacity: 0, duration: 0.7, ease: 'power2.in' }},  atOut - 0.7);
  tl.set(sel,   {{ opacity: 0 }}, atOut);
}}
fadeClip('#ch1-dw', S.ch1,  E.ch1);
fadeClip('#ch2-fw', S.ch2,  E.ch2);
fadeClip('#ch3-jt', S.ch3,  E.ch3);

/* ===== Chapter labels - stagger ===== */
[['ch1-label', S.ch1 + 0.8],
 ['ch2-label', S.ch2 + 0.8],
 ['ch3-label', S.ch3 + 0.8]].forEach(([id, at]) => {{
  const sel = '#' + id;
  tl.set(sel, {{ opacity: 0 }}, at);
  tl.fromTo(sel + ' .ch-rail', {{ scaleY: 0, transformOrigin: 'top' }},
    {{ scaleY: 1, duration: 0.7, ease: 'power2.out' }}, at);
  tl.fromTo(sel + ' .ch-num', {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.7 }}, at + 0.15);
  tl.fromTo(sel + ' .ch-name', {{ opacity: 0, x: 20 }}, {{ opacity: 1, x: 0, duration: 0.7 }}, at + 0.35);
  tl.fromTo(sel + ' .ch-role', {{ opacity: 0, x: 20 }}, {{ opacity: .78, x: 0, duration: 0.6 }}, at + 0.55);
  tl.set(sel, {{ opacity: 1 }}, at);
  tl.to(sel, {{ opacity: 0, duration: 0.7 }}, at + 5.0);
}});

/* ===== 转场 ===== */
function transitionShow(sel, at, dur) {{
  tl.fromTo(sel, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7 }}, at);
  tl.fromTo(sel + ' .tr-years', {{ opacity: 0, y: 10 }}, {{ opacity: .75, y: 0, duration: 0.7 }}, at + 0.3);
  tl.fromTo(sel + ' .tr-deco svg', {{ opacity: 0, scaleX: .5 }},
    {{ opacity: .5, scaleX: 1, duration: 0.9, ease: 'power2.out' }}, at + 0.7);
  tl.fromTo(sel + ' .trh-l:not(.ital)', {{ opacity: 0, y: 20 }},
    {{ opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }}, at + 1.0);
  tl.fromTo(sel + ' .trh-l.ital', {{ opacity: 0, y: 16 }},
    {{ opacity: 1, y: 0, duration: 0.9 }}, at + 1.5);
  tl.to(sel, {{ opacity: 0, duration: 0.7 }}, at + dur - 0.7);
  tl.set(sel, {{ opacity: 0 }}, at + dur);
}}
transitionShow('#trans1-card', S.trans1, E.trans1 - S.trans1);
transitionShow('#trans2-card', S.trans2, E.trans2 - S.trans2);

/* ===== 字幕通用 ===== */
document.querySelectorAll('.caption').forEach(el => {{
  const start = parseFloat(el.dataset.start);
  const dur   = parseFloat(el.dataset.duration);
  tl.fromTo(el, {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }}, start);
  tl.fromTo(el.querySelector('.cap-l1'), {{ opacity: 0, x: -14 }}, {{ opacity: 1, x: 0, duration: 0.65 }}, start + 0.05);
  tl.fromTo(el.querySelector('.cap-l2'), {{ opacity: 0, x: -10 }}, {{ opacity: .92, x: 0, duration: 0.65 }}, start + 0.35);
  tl.to(el, {{ opacity: 0, duration: 0.55, ease: 'power2.in' }}, start + dur - 0.55);
}});

/* ===== Three-up ===== */
['#three-dw','#three-fw','#three-jt'].forEach((sel, i) => {{
  tl.fromTo(sel, {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: 'power2.out' }}, S.three + i*0.22);
}});
tl.fromTo('#three-overlay', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.9 }}, S.three + 0.6);
['.tag-dw','.tag-fw','.tag-jt'].forEach((sel, i) => {{
  tl.fromTo(sel, {{ opacity: 0, x: -22 }}, {{ opacity: 1, x: 0, duration: 0.7, ease: 'power3.out' }}, S.three + 1.0 + i*0.3);
}});
['#three-dw','#three-fw','#three-jt','#three-overlay'].forEach(sel => {{
  tl.to(sel, {{ opacity: 0, duration: 0.8 }}, E.three - 1.5);
  tl.set(sel, {{ opacity: 0 }}, E.three);
}});

/* ===== Outro footage montage（filling 整个 outro 区段）===== */
const OUT_OFFSETS = [0.5, 11.5, 22.0];  // dw, fw, jt 启动相对 outro 起点
[['#out-dw',S.outro + OUT_OFFSETS[0]],['#out-fw',S.outro + OUT_OFFSETS[1]],['#out-jt',S.outro + OUT_OFFSETS[2]]].forEach(([sel,t]) => {{
  tl.fromTo(sel, {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.8 }}, t);
}});
tl.to('#out-dw', {{ opacity: 0, duration: 0.8 }}, S.outro + 12.0);
tl.to('#out-fw', {{ opacity: 0, duration: 0.8 }}, S.outro + 22.5);
tl.to('#out-jt', {{ opacity: 0, duration: 0.8 }}, E.outro - 1.5);

// outro hero — 起始时刻避开 caption（caption end ≈ outro+12.5；hero start = outro+15.0）
tl.fromTo('#outro-hero', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8 }}, S.outro + 15.0);
tl.fromTo('.oh-l', {{ opacity: 0, y: 22 }},
  {{ opacity: 1, y: 0, duration: 0.9, stagger: 0.28, ease: 'power3.out' }}, S.outro + 15.2);
tl.fromTo('.oh-tags', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.8 }}, S.outro + 17.0);
tl.to('#outro-hero', {{ opacity: 0, duration: 0.7 }}, E.outro - 1.5);
tl.set('#outro-hero', {{ opacity: 0 }}, E.outro);

/* ===== CTA ===== */
tl.fromTo('#cta-panel', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8 }}, S.cta);
tl.fromTo('.cta-mark', {{ opacity: 0 }}, {{ opacity: .7, duration: 0.7 }}, S.cta + 0.4);
tl.fromTo('.cta-q', {{ opacity: 0, y: 18 }}, {{ opacity: 1, y: 0, duration: 0.7 }}, S.cta + 0.7);
tl.fromTo('.cta-q-em', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.8 }}, S.cta + 1.1);
tl.fromTo('.cta-rule', {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.9, ease: 'power2.out' }}, S.cta + 2.0);
tl.fromTo('.cta-credit-label', {{ opacity: 0 }}, {{ opacity: .7, duration: 0.6 }}, S.cta + 2.7);
tl.fromTo('.cta-credit-line', {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.6, stagger: 0.18 }}, S.cta + 3.0);

/* ===== Progress bar fill ===== */
tl.fromTo('.pb-fill', {{ width: '0%' }}, {{ width: '100%', duration: TOTAL - S.open3, ease: 'none' }}, S.open3);

window.__timelines["main"] = tl;
</script>
</body>
</html>
"""

(PROJ / 'index.html').write_text(HTML, encoding='utf-8')
print(f"wrote {PROJ}/index.html ({len(HTML):,} bytes, TOTAL={TOTAL}s)")
print("\nTTS placements:")
for k, (sec, off) in TTS_AT.items():
    print(f"  {k:14s} @ {sec:6s}+{off:5.1f}s = {abs_t(sec, off):6.2f}s  dur={NARR[k]['dur']:.2f}s")
