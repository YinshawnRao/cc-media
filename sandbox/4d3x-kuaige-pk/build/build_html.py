#!/usr/bin/env python3
"""从 timing.json 生成 hf/index.html — 四大三小快歌 PK 1080×1920 竖屏。"""
import json
from pathlib import Path

PROJ = Path("/Users/yinshawnrao/explorer/cc-media/sandbox/4d3x-kuaige-pk")
HF = PROJ / "hf"
TIMING = json.loads((PROJ/"build/timing.json").read_text(encoding="utf-8"))

TOTAL = TIMING["TOTAL"]
COVER_D = TIMING["COVER_D"]
HOOK_D = TIMING["HOOK_D"]
RULES_D = TIMING["RULES_D"]
OUTRO_D = TIMING["OUTRO_D"]
starts = TIMING["starts"]
abs_anchors = TIMING["abs_anchors"]
SONGS = TIMING["SONGS"]
NARR = TIMING["NARR"]

def fmt(x): return f"{round(x,3)}"

COVER_T = starts["cover"][0]
HOOK_T = starts["hook"][0]
RULES_T = starts["rules"][0]
OUTRO_T = starts["outro"][0]

# ============ Footage 元素：每首歌一段 video（密集关键帧已预切到 clips_seg/sX.mp4）============
foot_tracks = [0, 6, 0, 6, 0, 6, 0]  # 交替轨道避免 HF 同轨冲突
foot_html = []
for idx, s in enumerate(SONGS):
    k = s["key"]; a = abs_anchors[k]
    sect_dur = a["end"] - a["start"]
    foot_html.append(
        f'<video id="fv_{k}" class="fv clip" data-start="{fmt(a["start"])}" '
        f'data-duration="{fmt(sect_dur)}" data-track-index="{foot_tracks[idx]}" '
        f'src="clips_seg/{k}.mp4" muted playsinline></video>')

# ============ Tint overlay（每段歌曲全段覆盖一层渐变）============
tint_html = []
for idx, s in enumerate(SONGS):
    k = s["key"]; a = abs_anchors[k]
    sect_dur = a["end"] - a["start"]
    tint_html.append(
        f'<div id="tint_{k}" class="clip tint tint_{k}" data-start="{fmt(a["start"])}" '
        f'data-duration="{fmt(sect_dur)}" data-track-index="{10+idx}"></div>')

# ============ Chrome (per-song UI 容器) ============
def kw_pills(kws, k):
    return "".join(f'<span class="kw-pill kw-pill-{k}">{w}</span>' for w in kws)

chrome_html = []
for idx, s in enumerate(SONGS):
    k = s["key"]; a = abs_anchors[k]
    sect_dur = a["end"] - a["start"]
    chrome_html.append(f'''<div id="chrome_{k}" class="clip chrome chrome_{k}" data-start="{fmt(a["start"])}" data-duration="{fmt(sect_dur)}" data-track-index="{20+idx}">
  <div class="cand">
    <span class="cand-lbl">候选</span><span class="cand-no">{s["no"]}</span>
    <span class="cand-tag">/ 7</span>
  </div>
  <div class="card">
    <div class="card-singer">{s["singer"]}</div>
    <div class="card-song">{s["song"]}</div>
    <div class="card-meta"><span>{s["year"]}</span><span class="dot-sep">·</span><span>{s["style"]}</span></div>
    <div class="card-pills">{kw_pills(s["kws"], k)}</div>
  </div>
  <div class="gold" id="gold_{k}">{s["gold"]}</div>
  <div class="cta-vote" id="cta_{k}">{s["vote"]}</div>
  <div class="particles"></div>
</div>''')

# ============ Cover (PK 擂台开场) ============
# 改版：去 7 卡列表+按钮；改用 7 段 MV 拼贴背景 + 暗色叠层 + 大字居中
cover_html = f'''<div id="cover" class="clip cover" data-start="{fmt(COVER_T)}" data-duration="{fmt(COVER_D)}" data-track-index="30">
  <div class="cv-mosaic"></div>
  <div class="cv-veil"></div>
  <div class="cv-grad"></div>
  <div class="cv-electric"></div>
  <div class="cv-stripe cv-stripe-top"></div>
  <div class="cv-stripe cv-stripe-bot"></div>

  <div class="cv-top">
    <div class="cv-eyebrow"><span>EP. 01</span><span class="cv-dot">·</span><span>四大三小</span><span class="cv-dot">·</span><span>快歌 PK</span></div>
  </div>

  <div class="cv-title-wrap">
    <h1 class="cv-title">
      <span class="cv-l1">四大三小</span>
      <span class="cv-vs">快歌</span>
      <span class="cv-l2">PK</span>
    </h1>
  </div>

  <div class="cv-foot">
    <div class="cv-sub">每人一首 · 投票决定排名</div>
    <div class="cv-corner"><span class="cv-warn">⚠</span>出场顺序 ≠ 排名</div>
  </div>
</div>'''

# ============ Hook (intro 旁白期 — 7 行歌名快闪) ============
hook_lines = ""
for i, s in enumerate(SONGS):
    hook_lines += f'<div class="hk-line" id="hk_{i+1}"><span class="hk-no">{s["no"]}</span><span class="hk-singer">{s["singer"]}</span><span class="hk-song">{s["song"]}</span></div>\n'

hook_html = f'''<div id="hook" class="clip hook" data-start="{fmt(HOOK_T)}" data-duration="{fmt(HOOK_D)}" data-track-index="31">
  <div class="hk-grad"></div>
  <div class="hk-flash"></div>
  <div class="hk-title">这一次，<br>我们只看快歌。</div>
  <div class="hk-list">{hook_lines}</div>
</div>'''

# ============ Rules (规则段 — 居中布局，无 7 卡列表，避免与上屏重复) ============
rules_html = f'''<div id="rules" class="clip rules" data-start="{fmt(RULES_T)}" data-duration="{fmt(RULES_D)}" data-track-index="32">
  <div class="rl-grad"></div>
  <div class="rl-eyebrow">本期规则</div>
  <div class="rl-h">每人 1 首快歌代表作<br>排名由<span class="rl-acc">粉丝投票</span>决定</div>
  <div class="rl-divider"></div>
  <div class="rl-tags">
    <span class="rl-tag">唱跳</span>
    <span class="rl-tag">律动</span>
    <span class="rl-tag">传唱度</span>
    <span class="rl-tag">舞台记忆点</span>
  </div>
  <div class="rl-foot">
    <span class="rl-warn">⚠</span>
    <span>出场顺序 不代表 排名</span>
  </div>
</div>'''

# ============ Outro (总结 + 投票 CTA — 无按钮版) ============
def outro_card(s):
    return f'''<div class="ot-card ot-card-{s["key"]}">
      <span class="ot-no">{s["no"]}</span>
      <span class="ot-singer">{s["singer"]}</span>
      <span class="ot-song">{s["song"]}</span>
      <span class="ot-style">{s["style"]}</span>
    </div>'''

outro_html = f'''<div id="outro" class="clip outroblk" data-start="{fmt(OUTRO_T)}" data-duration="{fmt(OUTRO_D)}" data-track-index="33">
  <div class="ot-bg"></div>
  <div class="ot-eyebrow">7 首 · 7 种快歌能量</div>
  <div class="ot-grid">
    {chr(10).join(outro_card(s) for s in SONGS)}
  </div>
  <h2 class="ot-h">你投谁第一？</h2>
  <div class="ot-foot">投票区见 · 评论区告诉我，没入选的你最不服哪一首？</div>
</div>'''

# ============ Audio Master ============
audio_html = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ============ CSS ============
CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden;
  background: #06080F; color: #F7F0E8;
  font-family: "Noto Sans SC","PingFang SC",system-ui,sans-serif;
  -webkit-font-smoothing: antialiased; }

/* ===== Footage ===== */
.fv { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 1; opacity: 0; }

/* ===== Tints (per-song color glaze) ===== */
.tint { position: absolute; inset: 0; z-index: 2; mix-blend-mode: multiply; opacity: 0; }
'''
# Add per-song tint backgrounds
for s in SONGS:
    CSS += f'.tint_{s["key"]} {{ background: {s["tint"]}; }}\n'

CSS += '''

/* ===== Chrome (per-song UI) ===== */
.chrome { position: absolute; inset: 0; z-index: 4; pointer-events: none; }
'''
for s in SONGS:
    CSS += f'.chrome_{s["key"]} {{ --pri:{s["pri"]}; --acc:{s["acc"]}; --bg:{s["bg"]}; --muted:{s["muted"]}; }}\n'

CSS += '''

/* 候选编号（左上） */
.cand { position: absolute; top: 70px; left: 64px; display: flex; align-items: baseline; gap: 10px; opacity: 0; }
.cand-lbl { font-family: "Noto Sans SC"; font-size: 26px; font-weight: 700; letter-spacing: .35em; color: var(--pri); padding: 6px 14px 6px 16px; border: 2px solid var(--pri); border-radius: 999px; background: rgba(0,0,0,.32); }
.cand-no { font-family: "Bebas Neue","Noto Sans SC"; font-size: 110px; font-weight: 900; line-height: .9; color: var(--pri); margin-left: 8px; text-shadow: 0 6px 32px rgba(0,0,0,.5), 0 0 24px color-mix(in srgb, var(--pri) 70%, transparent); }
.cand-tag { font-family: "Noto Sans SC"; font-size: 28px; font-weight: 700; color: rgba(255,255,255,.55); letter-spacing: .15em; }

/* 歌名卡（右上） */
.card { position: absolute; top: 90px; right: 56px; width: 600px; padding: 38px 42px 36px;
  border-radius: 28px;
  background: linear-gradient(155deg, rgba(255,255,255,.10), rgba(255,255,255,.025));
  backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
  border: 1.5px solid rgba(255,255,255,.18);
  box-shadow: 0 30px 80px rgba(0,0,0,.55);
  opacity: 0; }
.card-singer { font-family: "Noto Sans SC"; font-size: 36px; font-weight: 800; letter-spacing: .08em; color: rgba(255,255,255,.78); margin-bottom: 8px; }
.card-song { font-family: "Noto Serif SC","Songti SC",serif; font-size: 90px; font-weight: 800; line-height: 1.0; color: #F7F0E8; letter-spacing: -2px; margin-bottom: 22px; text-shadow: 0 2px 14px color-mix(in srgb, var(--pri) 30%, transparent); }
.card-meta { font-family: "Noto Sans SC"; font-size: 26px; font-weight: 600; color: rgba(255,255,255,.62); letter-spacing: .04em; margin-bottom: 26px; display: flex; align-items: center; gap: 14px; }
.card-meta .dot-sep { color: var(--pri); font-size: 20px; }
.card-pills { display: flex; flex-wrap: wrap; gap: 12px; }
.kw-pill { font-family: "Noto Sans SC"; font-size: 26px; font-weight: 700; padding: 9px 18px; border-radius: 999px; background: rgba(255,255,255,.08); border: 1.5px solid var(--pri); color: var(--pri); letter-spacing: .04em; }

/* 金句（副歌段大字浮于画面） */
.gold { position: absolute; left: 60px; right: 60px; bottom: 480px; font-family: "Noto Serif SC",serif; font-size: 64px; font-weight: 600; line-height: 1.35; text-align: center; color: #F7F0E8; opacity: 0; letter-spacing: .02em; text-shadow: 0 6px 28px rgba(0,0,0,.85), 0 0 18px color-mix(in srgb, var(--pri) 35%, transparent); }

/* 投票刺激句（mid 段时弹出，模拟弹幕） */
.cta-vote { position: absolute; left: 60px; right: 60px; bottom: 250px; font-family: "Noto Sans SC"; font-size: 38px; font-weight: 700; text-align: center; color: var(--acc); opacity: 0; letter-spacing: .03em; padding: 22px 30px; border-radius: 22px; background: rgba(0,0,0,.45); border: 2px solid var(--pri); box-shadow: 0 10px 34px rgba(0,0,0,.55), inset 0 0 40px color-mix(in srgb, var(--pri) 18%, transparent); }

/* 粒子层 */
.particles { position: absolute; inset: 0; pointer-events: none; mix-blend-mode: screen; opacity: 0;
  background:
    radial-gradient(circle at 18% 22%, color-mix(in srgb, var(--pri) 18%, transparent) 0, transparent 2%),
    radial-gradient(circle at 70% 35%, color-mix(in srgb, var(--pri) 12%, transparent) 0, transparent 1.5%),
    radial-gradient(circle at 35% 70%, color-mix(in srgb, var(--acc) 14%, transparent) 0, transparent 1.8%),
    radial-gradient(circle at 82% 78%, color-mix(in srgb, var(--pri) 12%, transparent) 0, transparent 1.5%); }

/* ===== Cover ===== */
.cover { position: absolute; inset: 0; z-index: 50; background: #06080F; overflow: hidden; }
/* 7 段 MV 拼贴背景：用 cover_bg.jpg（已 vstack 7 个 vert clip 中段） */
.cv-mosaic { position: absolute; inset: 0; background-image: url("cover_assets/cover_bg.jpg"); background-size: cover; background-position: center; filter: saturate(.92); }
/* 暗色叠层 — 保证标题清晰可读 */
.cv-veil { position: absolute; inset: 0; background:
  radial-gradient(ellipse at 50% 50%, rgba(6,8,15,.88) 0%, rgba(6,8,15,.55) 22%, rgba(6,8,15,.22) 40%, rgba(6,8,15,.22) 60%, rgba(6,8,15,.55) 78%, rgba(6,8,15,.88) 100%); }
.cv-grad { position: absolute; inset: 0; background:
  radial-gradient(ellipse at 50% 42%, rgba(230,60,92,.22) 0, transparent 40%),
  radial-gradient(ellipse at 50% 92%, rgba(212,168,72,.20) 0, transparent 45%); mix-blend-mode: screen; }
.cv-electric { position: absolute; inset: 0; background-image:
  linear-gradient(90deg, transparent 0, transparent 49.5%, rgba(255,255,255,.025) 49.7%, rgba(255,255,255,.025) 50.3%, transparent 50.5%, transparent 100%);
  background-size: 4px 100%; opacity: .25; mix-blend-mode: screen; }
.cv-stripe { position: absolute; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, transparent, #E63C5C, #D4A848, #5AC8FF, transparent); opacity: .82; box-shadow: 0 0 24px #E63C5C; }
.cv-stripe-top { top: 56px; }
.cv-stripe-bot { bottom: 56px; }

.cv-top { position: absolute; top: 140px; left: 0; right: 0; text-align: center; }
.cv-eyebrow { display: inline-flex; align-items: center; gap: 14px; font-family: "Noto Sans SC"; font-size: 28px; font-weight: 800; letter-spacing: .38em; color: #D4A848; padding: 10px 26px; border: 1.5px solid rgba(212,168,72,.55); border-radius: 999px; background: rgba(0,0,0,.45); }
.cv-dot { color: rgba(255,255,255,.35); font-weight: 400; }

/* 居中放置标题区，落在 9 宫格中心格内 (y=640-1280)，紧凑 ~580px */
.cv-title-wrap { position: absolute; top: 685px; left: 0; right: 0; text-align: center; }
.cv-title { font-family: "Noto Serif SC",serif; letter-spacing: -3px; }
.cv-title .cv-l1 { display: block; font-size: 132px; font-weight: 900; line-height: 1.0; color: #F7F0E8; text-shadow: 0 0 48px rgba(212,168,72,.5), 0 6px 24px rgba(0,0,0,.85); margin-bottom: 32px; }
.cv-title .cv-vs { display: block; font-size: 92px; font-weight: 700; line-height: 1.0; color: #D4A848; letter-spacing: .18em; margin-bottom: 32px; text-shadow: 0 0 36px rgba(212,168,72,.5); }
.cv-title .cv-l2 { display: block; font-size: 220px; font-weight: 900; line-height: 1.0; color: #E63C5C; font-family: "Bebas Neue","Noto Serif SC",serif; letter-spacing: .06em; text-shadow: 0 0 60px rgba(230,60,92,.7), 0 8px 28px rgba(0,0,0,.85); }

.cv-foot { position: absolute; bottom: 70px; left: 0; right: 0; text-align: center; }
.cv-sub { font-family: "Noto Sans SC"; font-size: 38px; font-weight: 800; color: #F7F0E8; letter-spacing: .22em; margin-bottom: 18px; text-shadow: 0 2px 12px rgba(0,0,0,.95); padding: 10px 0; background: linear-gradient(90deg, transparent, rgba(0,0,0,.55) 20%, rgba(0,0,0,.55) 80%, transparent); }
.cv-corner { font-family: "Noto Sans SC"; font-size: 22px; font-weight: 700; letter-spacing: .26em; color: rgba(247,240,232,.78); display: inline-flex; align-items: center; gap: 10px; padding: 8px 22px; border: 1.5px solid rgba(255,255,255,.32); border-radius: 999px; background: rgba(0,0,0,.65); }
.cv-warn { color: #E63C5C; font-size: 24px; }

/* ===== Hook ===== */
.hook { position: absolute; inset: 0; z-index: 49; background: linear-gradient(180deg, #0A0512 0%, #06080F 100%); }
.hk-grad { position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 30%, rgba(230,60,92,.15) 0, transparent 50%); }
.hk-flash { position: absolute; inset: 0; background: linear-gradient(180deg, transparent, rgba(255,255,255,.04) 50%, transparent); opacity: .5; mix-blend-mode: screen; }
.hk-title { position: absolute; top: 180px; left: 0; right: 0; text-align: center; font-family: "Noto Serif SC",serif; font-size: 96px; font-weight: 800; color: #F7F0E8; line-height: 1.1; letter-spacing: -2px; text-shadow: 0 0 32px rgba(212,168,72,.4); }
.hk-list { position: absolute; top: 520px; left: 80px; right: 80px; }
.hk-line { display: flex; align-items: baseline; gap: 22px; padding: 14px 0; opacity: 0; border-bottom: 1px solid rgba(255,255,255,.08); }
.hk-line:last-child { border-bottom: none; }
.hk-no { font-family: "Bebas Neue","Noto Sans SC"; font-size: 40px; font-weight: 900; color: #D4A848; min-width: 80px; letter-spacing: .04em; }
.hk-singer { font-family: "Noto Sans SC"; font-size: 40px; font-weight: 800; color: #F7F0E8; }
.hk-song { font-family: "Noto Serif SC",serif; font-size: 38px; font-weight: 600; color: rgba(247,240,232,.70); margin-left: auto; }

/* ===== Rules — 居中布局，无 7 卡列表，避免重复 ===== */
.rules { position: absolute; inset: 0; z-index: 48; background: linear-gradient(180deg, #0A0512 0%, #06080F 100%); }
.rl-grad { position: absolute; inset: 0; background:
  radial-gradient(ellipse at 50% 35%, rgba(230,60,92,.16) 0, transparent 45%),
  radial-gradient(ellipse at 50% 85%, rgba(90,200,255,.14) 0, transparent 45%); }
.rl-eyebrow { position: absolute; top: 580px; left: 0; right: 0; text-align: center; font-family: "Noto Sans SC"; font-size: 32px; font-weight: 800; letter-spacing: .48em; color: #D4A848; opacity: 0; }
.rl-h { position: absolute; top: 700px; left: 0; right: 0; text-align: center; font-family: "Noto Serif SC",serif; font-size: 92px; font-weight: 800; color: #F7F0E8; line-height: 1.22; letter-spacing: -1px; opacity: 0; }
.rl-h .rl-acc { color: #E63C5C; text-shadow: 0 0 28px rgba(230,60,92,.55); }
.rl-divider { position: absolute; top: 1080px; left: 50%; transform: translateX(-50%); width: 120px; height: 3px; background: linear-gradient(90deg, transparent, #D4A848, transparent); opacity: 0; }
.rl-tags { position: absolute; top: 1140px; left: 0; right: 0; text-align: center; display: flex; justify-content: center; flex-wrap: wrap; gap: 18px; padding: 0 60px; }
.rl-tag { font-family: "Noto Sans SC"; font-size: 36px; font-weight: 700; padding: 14px 32px; border-radius: 999px; background: rgba(255,255,255,.06); border: 2px solid rgba(255,255,255,.22); color: rgba(247,240,232,.88); letter-spacing: .12em; opacity: 0; }
.rl-foot { position: absolute; bottom: 240px; left: 0; right: 0; text-align: center; opacity: 0; }
.rl-foot .rl-warn { color: #E63C5C; font-size: 40px; margin-right: 20px; }
.rl-foot span:last-child { font-family: "Noto Sans SC"; font-size: 40px; font-weight: 800; color: #F7F0E8; letter-spacing: .3em; }

/* ===== Outro ===== */
.outroblk { position: absolute; inset: 0; z-index: 47; background: radial-gradient(ellipse at 50% 40%, #2A0B1F 0%, #06080F 70%); }
.ot-bg { position: absolute; inset: 0; background:
  radial-gradient(ellipse at 18% 18%, rgba(230,60,92,.18) 0, transparent 35%),
  radial-gradient(ellipse at 82% 22%, rgba(90,200,255,.14) 0, transparent 32%),
  radial-gradient(ellipse at 50% 92%, rgba(212,168,72,.18) 0, transparent 40%); }
.ot-eyebrow { position: absolute; top: 110px; left: 0; right: 0; text-align: center; font-family: "Noto Sans SC"; font-size: 28px; font-weight: 800; letter-spacing: .4em; color: #D4A848; opacity: 0; }
.ot-grid { position: absolute; top: 220px; left: 64px; right: 64px; display: grid; grid-template-columns: 1fr; gap: 10px; }
.ot-card { padding: 16px 24px; border-radius: 18px; background: linear-gradient(155deg, rgba(255,255,255,.10), rgba(255,255,255,.02)); border: 1.5px solid rgba(255,255,255,.22); display: flex; align-items: baseline; gap: 14px; opacity: 0; }
.ot-no { font-family: "Bebas Neue"; font-size: 32px; font-weight: 900; color: #D4A848; min-width: 38px; }
.ot-singer { font-family: "Noto Sans SC"; font-size: 28px; font-weight: 800; color: #F7F0E8; min-width: 130px; }
.ot-song { font-family: "Noto Serif SC",serif; font-size: 28px; font-weight: 600; color: rgba(247,240,232,.80); }
.ot-style { font-family: "Noto Sans SC"; font-size: 22px; font-weight: 700; color: #E63C5C; margin-left: auto; padding: 4px 14px; border: 1.5px solid rgba(230,60,92,.6); border-radius: 999px; }
.ot-h { position: absolute; bottom: 340px; left: 0; right: 0; text-align: center; font-family: "Noto Serif SC",serif; font-size: 108px; font-weight: 900; color: #F7F0E8; letter-spacing: .14em; opacity: 0; text-shadow: 0 0 48px rgba(230,60,92,.55); white-space: nowrap; }
.ot-foot { position: absolute; bottom: 200px; left: 60px; right: 60px; text-align: center; font-family: "Noto Sans SC"; font-size: 32px; font-weight: 700; color: rgba(247,240,232,.82); opacity: 0; letter-spacing: .04em; line-height: 1.5; }
'''

# ============ GSAP JS ============
def js_chapter(s, idx):
    k = s["key"]; a = abs_anchors[k]
    base = a["start"]
    v0 = a["v0"]; v1 = a["v1"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]; mid0 = a["mid0"]
    end = a["end"]
    fade_out = end - 1.0
    cta_show = mid0 + 0.2  # 投票刺激句和 mid 旁白同步
    cta_hide = end - 1.6
    return f'''
// ---- {s["singer"]} 《{s["song"]}》 ----
tl.fromTo("#fv_{k}", {{opacity:0, scale:1.06}}, {{opacity:1, scale:1.0, duration:1.4, ease:"power2.out"}}, {fmt(base)});
tl.to("#tint_{k}", {{opacity:1, duration:1.2, ease:"power1.out"}}, {fmt(base)});
tl.fromTo(".chrome_{k} .cand", {{opacity:0, y:-12}}, {{opacity:1, y:0, duration:.6, ease:"power2.out"}}, {fmt(base+0.2)});
tl.fromTo(".chrome_{k} .card", {{opacity:0, x:40, y:-10}}, {{opacity:1, x:0, y:0, duration:.85, ease:"power3.out"}}, {fmt(base+0.5)});
tl.fromTo(".chrome_{k} .particles", {{opacity:0}}, {{opacity:1, duration:1.8, ease:"sine.inOut"}}, {fmt(base+0.4)});
// 旁白结束→ swell：卡片淡出，金句大字浮现
tl.to(".chrome_{k} .card", {{opacity:0, y:-10, duration:.5, ease:"power2.in"}}, {fmt(sw0-0.1)});
tl.to(".chrome_{k} .cand", {{opacity:0, duration:.5, ease:"power2.in"}}, {fmt(sw0-0.1)});
tl.fromTo(".chrome_{k} #gold_{k}", {{opacity:0, y:30, scale:.94}}, {{opacity:1, y:0, scale:1.0, duration:1.2, ease:"power3.out"}}, {fmt(full0-0.3)});
// 投票刺激句弹出（mid 旁白时机）
tl.fromTo(".chrome_{k} #cta_{k}", {{opacity:0, y:24, scale:.92}}, {{opacity:1, y:0, scale:1.0, duration:.7, ease:"back.out(1.4)"}}, {fmt(cta_show)});
tl.to(".chrome_{k} #cta_{k}", {{opacity:0, y:-12, duration:.55, ease:"power2.in"}}, {fmt(cta_hide)});
// 章节收尾淡出（hard kill）
tl.to(".chrome_{k} #gold_{k}", {{opacity:0, y:-10, duration:.6, ease:"power2.in"}}, {fmt(end-1.4)});
tl.set(".chrome_{k} #gold_{k}", {{opacity:0}}, {fmt(end)});
tl.to("#fv_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(fade_out)});
tl.set("#fv_{k}", {{opacity:0}}, {fmt(end)});
tl.to("#tint_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(fade_out)});
tl.set("#tint_{k}", {{opacity:0}}, {fmt(end)});
tl.to(".chrome_{k} .particles", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(fade_out)});
tl.set(".chrome_{k} .particles", {{opacity:0}}, {fmt(end)});
'''

# Cover JS: t=0 即可见（封面首帧硬约束）
cover_js = f'''
tl.set("#cover", {{opacity:1}}, 0);
tl.set(".cv-mosaic", {{opacity:1}}, 0);
tl.set(".cv-eyebrow", {{opacity:1}}, 0);
tl.set(".cv-title", {{opacity:1}}, 0);
tl.set(".cv-sub", {{opacity:1}}, 0);
tl.set(".cv-corner", {{opacity:1}}, 0);
tl.to(".cv-mosaic", {{scale:1.04, duration:{fmt(COVER_D)}, ease:"power1.out"}}, 0);
tl.to(".cv-title .cv-l2", {{scale:1.03, duration:.9, yoyo:true, repeat:3, ease:"sine.inOut"}}, 0.5);
tl.to("#cover", {{opacity:0, duration:.6, ease:"power2.in"}}, {fmt(COVER_D-0.5)});
tl.set("#cover", {{opacity:0}}, {fmt(COVER_D)});
'''

# Hook JS: 7 行歌名依次扫过
hook_anchor = HOOK_T
intro_voice_at = HOOK_T + 0.3
line_total = HOOK_D - 2.0
line_interval = max(0.8, line_total / 7.5)
hook_js = f'''
tl.set("#hook", {{opacity:1}}, {fmt(HOOK_T)});
tl.fromTo(".hk-title", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.7, ease:"power3.out"}}, {fmt(HOOK_T+0.1)});
'''
for i in range(7):
    t0 = HOOK_T + 0.8 + i * line_interval
    t1 = t0 + 1.0
    hook_js += f'tl.fromTo("#hk_{i+1}", {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:.45, ease:"power2.out"}}, {fmt(t0)});\n'
    hook_js += f'tl.to("#hk_{i+1}", {{opacity:.45, duration:.4, ease:"power1.out"}}, {fmt(t1)});\n'
hook_js += f'tl.to("#hook", {{opacity:0, duration:.6, ease:"power2.in"}}, {fmt(HOOK_T+HOOK_D-0.6)});\n'
hook_js += f'tl.set("#hook", {{opacity:0}}, {fmt(HOOK_T+HOOK_D)});\n'

# Rules JS
rules_anchor = RULES_T
rules_js = f'''
tl.set("#rules", {{opacity:1}}, {fmt(RULES_T)});
tl.fromTo(".rl-eyebrow", {{opacity:0, y:-12}}, {{opacity:1, y:0, duration:.5, ease:"power2.out"}}, {fmt(RULES_T+0.2)});
tl.fromTo(".rl-h", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.9, ease:"power3.out"}}, {fmt(RULES_T+0.6)});
'''
rules_js += f'tl.fromTo(".rl-divider", {{opacity:0, scaleX:0}}, {{opacity:1, scaleX:1, duration:.6, ease:"power2.out"}}, {fmt(RULES_T+2.0)});\n'
for i in range(4):
    t = RULES_T + 2.4 + i * 0.18
    rules_js += f'tl.fromTo(".rl-tags .rl-tag:nth-child({i+1})", {{opacity:0, y:14, scale:.94}}, {{opacity:1, y:0, scale:1.0, duration:.5, ease:"back.out(1.4)"}}, {fmt(t)});\n'
rules_js += f'tl.fromTo(".rl-foot", {{opacity:0, scale:.92}}, {{opacity:1, scale:1.0, duration:.7, ease:"back.out(1.5)"}}, {fmt(RULES_T+4.2)});\n'
rules_js += f'tl.to("#rules", {{opacity:0, duration:.6, ease:"power2.in"}}, {fmt(RULES_T+RULES_D-0.6)});\n'
rules_js += f'tl.set("#rules", {{opacity:0}}, {fmt(RULES_T+RULES_D)});\n'

# Outro JS
outro_anchor = OUTRO_T
outro_js = f'''
tl.fromTo("#outro", {{opacity:0}}, {{opacity:1, duration:.7, ease:"power2.out"}}, {fmt(OUTRO_T)});
tl.fromTo(".ot-eyebrow", {{opacity:0, y:-10}}, {{opacity:1, y:0, duration:.5, ease:"power2.out"}}, {fmt(OUTRO_T+0.3)});
'''
for i in range(7):
    t = OUTRO_T + 0.8 + i * 0.22
    outro_js += f'tl.fromTo(".ot-grid .ot-card:nth-child({i+1})", {{opacity:0, x:-16}}, {{opacity:1, x:0, duration:.5, ease:"power2.out"}}, {fmt(t)});\n'
outro_js += f'tl.fromTo(".ot-h", {{opacity:0, y:30, scale:.94}}, {{opacity:1, y:0, scale:1.0, duration:.9, ease:"power3.out"}}, {fmt(OUTRO_T + NARR["outro"] + 0.5)});\n'
outro_js += f'tl.fromTo(".ot-foot", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:.7, ease:"power2.out"}}, {fmt(OUTRO_T + NARR["outro"] + 2.0)});\n'
outro_js += f'tl.to(".ot-h", {{scale:1.03, duration:1.0, yoyo:true, repeat:3, ease:"sine.inOut"}}, {fmt(OUTRO_T + NARR["outro"] + NARR["vote"] + 0.5)});\n'

JS = cover_js + hook_js + rules_js + "\n".join(js_chapter(s, i) for i, s in enumerate(SONGS)) + outro_js

# ============ Final HTML ============
html = f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=Bebas+Neue&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
    {chr(10).join(foot_html)}
    {chr(10).join(tint_html)}
    {chr(10).join(chrome_html)}
    {cover_html}
    {hook_html}
    {rules_html}
    {outro_html}
    {audio_html}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    {JS}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"4d3x-kuaige-pk"}', encoding="utf-8")
print(f"index.html written: {len(html)} bytes")
