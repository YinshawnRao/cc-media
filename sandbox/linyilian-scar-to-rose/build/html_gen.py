# -*- coding: utf-8 -*-
"""生成 hf/index.html（竖屏 1080x1920 叙事时间线）。被 build.py 调用。"""
from pathlib import Path

def fmt(x): return f"{round(float(x),3)}"

ROSE_SVG = '''<svg class="cv-rose" width="150" height="180" viewBox="0 0 150 180" fill="none">
  <g transform="translate(75,72)">
    <g opacity="0.96">
      <ellipse cx="0" cy="-24" rx="21" ry="31" fill="#6f1a26"/>
      <ellipse cx="0" cy="-24" rx="21" ry="31" fill="#6f1a26" transform="rotate(72)"/>
      <ellipse cx="0" cy="-24" rx="21" ry="31" fill="#6f1a26" transform="rotate(144)"/>
      <ellipse cx="0" cy="-24" rx="21" ry="31" fill="#6f1a26" transform="rotate(216)"/>
      <ellipse cx="0" cy="-24" rx="21" ry="31" fill="#6f1a26" transform="rotate(288)"/>
    </g>
    <g opacity="0.98">
      <ellipse cx="0" cy="-15" rx="14" ry="21" fill="#9b2733" transform="rotate(36)"/>
      <ellipse cx="0" cy="-15" rx="14" ry="21" fill="#9b2733" transform="rotate(108)"/>
      <ellipse cx="0" cy="-15" rx="14" ry="21" fill="#9b2733" transform="rotate(180)"/>
      <ellipse cx="0" cy="-15" rx="14" ry="21" fill="#9b2733" transform="rotate(252)"/>
      <ellipse cx="0" cy="-15" rx="14" ry="21" fill="#9b2733" transform="rotate(324)"/>
    </g>
    <ellipse cx="0" cy="-7" rx="9" ry="13" fill="#bb3344"/>
    <ellipse cx="0" cy="-7" rx="9" ry="13" fill="#bb3344" transform="rotate(120)"/>
    <ellipse cx="0" cy="-7" rx="9" ry="13" fill="#bb3344" transform="rotate(240)"/>
    <circle r="6" cy="-2" fill="#5d121c"/>
  </g>
  <path d="M75 138 q 8 26 0 40" stroke="#2f5a36" stroke-width="3" fill="none" opacity=".75"/>
  <path d="M70 152 q -20 -6 -26 -20 q 20 -2 27 16" fill="#2f5a36" opacity=".6"/>
</svg>'''

def write_html(starts, KEYS, SRC, BY_KEY, content, NARR, cfg, anchors):
    COVER_D = cfg["COVER_D"]; intro_seg = cfg["intro_seg"]; outro_seg = cfg["outro_seg"]
    TOTAL = cfg["TOTAL"]; SAMPLE = cfg["SAMPLE"]

    # ---- 绝对锚点 ----
    AB = {}
    for k in KEYS:
        base = starts[k][0]; a = anchors(k)
        AB[k] = {x: round(base + a[x], 3) for x in ("v0","v1","sw0","full0","full1","t0","t1","end")}
        AB[k]["start"] = round(base, 3); AB[k]["seg"] = a["seg"]
    intro_t = starts["intro"][0]
    cover_t = 0.0

    foot_tracks = {}
    for i, k in enumerate(KEYS):
        foot_tracks[k] = 0 if i % 2 == 0 else 6

    # 全 8 首叙事编号(rail 用)；展示顺序号 = no
    all_no = [s["no"] for s in content.SONGS]

    parts = []  # body html clips
    js = []     # gsap calls

    def seg_js(sel, in_at, out_at, in_d=0.7, out_d=0.6, y=0):
        js.append(f'S("{sel}",{fmt(in_at)},{fmt(out_at)},{in_d},{out_d},{y});')

    # ================= COVER (首帧封面) =================
    parts.append(f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="2">
  <div class="cv-photo"></div>
  <div class="cv-grade"></div>
  <div class="cv-bloom"></div>
  <div class="cv-frame"></div>
  <div class="cv-block">
    {ROSE_SVG}
    <div class="cv-kicker">李宗盛 × 林忆莲 · 词曲解读</div>
    <div class="cv-title">从伤痕到玫瑰</div>
    <div class="cv-sub">李宗盛写透了林忆莲</div>
    <div class="cv-rule"></div>
    <div class="cv-en">Sandy Lam · 8 songs, one woman</div>
  </div>
</div>''')

    # ================= INTRO =================
    parts.append(f'''<video id="introbg" class="clip fv" data-start="{fmt(intro_t)}" data-duration="{fmt(intro_seg)}" data-track-index="4" src="clips_seg/intro.mp4" muted playsinline></video>
<div id="introtint" class="clip introtint" data-start="{fmt(intro_t)}" data-duration="{fmt(intro_seg)}" data-track-index="5"></div>
<div id="introtxt" class="clip introtxt" data-start="{fmt(intro_t)}" data-duration="{fmt(intro_seg)}" data-track-index="7">
  <div class="in-line in-1">不是普通情歌盘点</div>
  <div class="in-line in-2">是从伤痕走到玫瑰的<br><span class="hl">女性叙事</span></div>
</div>''')
    js.append(f'TLscale("#introbg",{fmt(intro_t)},{fmt(intro_seg)});')
    seg_js("#introbg", intro_t, intro_t+intro_seg, 1.0, 1.0)
    seg_js("#introtint", intro_t, intro_t+intro_seg, 1.0, 1.0)
    # intro 文字：稍晚出现，整段在
    js.append(f'fadeChild(".in-1",{fmt(intro_t+1.4)});')
    js.append(f'fadeChild(".in-2",{fmt(intro_t+2.6)});')
    seg_js("#introtxt", intro_t+1.2, intro_t+intro_seg, 0.8, 1.0)

    # ================= 每首歌 =================
    for i, k in enumerate(KEYS):
        s = BY_KEY[k]; a = AB[k]; col = SRC[k]
        no2 = f"{s['no']:02d}"
        # footage
        parts.append(f'<video id="fv_{k}" class="clip fv" data-start="{fmt(a["start"])}" data-duration="{fmt(a["seg"])}" data-track-index="{foot_tracks[k]}" src="clips_seg/{k}.mp4" muted playsinline></video>')
        js.append(f'TLscale("#fv_{k}",{fmt(a["start"])},{fmt(a["seg"])});')
        # tint
        parts.append(f'<div id="tint_{k}" class="clip songtint" data-start="{fmt(a["start"])}" data-duration="{fmt(a["seg"])}" data-track-index="{11+i}" style="background:radial-gradient(120% 80% at 50% 38%, transparent 30%, {col["tintB"]} 64%, {col["tintA"]} 100%), linear-gradient(180deg, {col["tintA"]} 0%, transparent 26%, transparent 70%, {col["tintA"]} 100%);"></div>')
        # rail (左侧时间线)
        ticks = "".join(
            f'<div class="tk {"on" if n==s["no"] else ""}"><span class="tk-d"></span><span class="tk-n">{n:02d}</span></div>'
            for n in all_no)
        parts.append(f'''<div id="rail_{k}" class="clip rail" data-start="{fmt(a["start"])}" data-duration="{fmt(a["seg"])}" data-track-index="{31+i}" style="--acc:{col["acc"]};">
  <div class="rail-line"></div>{ticks}
</div>''')
        # 歌名玻璃卡 (顶部暗带)
        parts.append(f'''<div id="card_{k}" class="clip card" data-start="{fmt(a["start"])}" data-duration="{fmt(a["seg"])}" data-track-index="{51+i}" style="--acc:{col["acc"]};--pri:{col["pri"]};">
  <div class="cd-top"><span class="cd-no">{no2}</span><span class="cd-year">{s["year"]}</span></div>
  <div class="cd-name">{s["name"]}</div>
  <div class="cd-credit">{s["credit"]}</div>
  <div class="cd-tag">{s["tag"]}</div>
</div>''')
        # 大屏主题句 (底部暗带，副歌展示期)
        big_lines = "".join(f'<div class="bg-l">{ln}</div>' for ln in s["screen"])
        parts.append(f'''<div id="big_{k}" class="clip bigtxt" data-start="{fmt(a["full0"])}" data-duration="{fmt(a["end"]-a["full0"])}" data-track-index="{71+i}" style="--acc:{col["acc"]};">
  <div class="bg-song">{s["name"]}</div>{big_lines}
</div>''')
        # footage 进出
        in_overlap = 0.6
        seg_js(f"#fv_{k}", a["start"], a["end"], in_d=in_overlap+0.4, out_d=0.7)
        seg_js(f"#tint_{k}", a["start"], a["end"], 0.8, 0.7)
        seg_js(f"#rail_{k}", a["start"]+0.3, a["end"], 0.7, 0.6, y=18)
        seg_js(f"#card_{k}", a["start"]+0.4, a["full1"]-0.3 if (a["t1"]>a["full1"]) else a["end"], 0.8, 0.6, y=-22)
        # big 主题句：展示中段进，转场出现前淡出(否则与转场字幕底部撞)
        big_out = (a["t0"]-0.2) if a["t1"] > a["full1"] else a["end"]-0.3
        seg_js(f"#big_{k}", a["full0"]+0.6, big_out, 0.9, 0.6, y=24)
        # 转场字幕
        if a["t1"] > a["full1"]:
            parts.append(f'''<div id="trans_{k}" class="clip transcap" data-start="{fmt(a["t0"])}" data-duration="{fmt(a["end"]-a["t0"])}" data-track-index="{91+i}">
  <div class="tc-mark"></div><div class="tc-txt">{s["trans"]}</div>
</div>''')
            seg_js(f"#trans_{k}", a["t0"], a["t1"]+0.9, 0.6, 0.6, y=14)

    # ================= OUTRO + 固定 CTA =================
    if not SAMPLE:
        ot = starts["outro"][0]
        oscreen = "".join(f'<div class="ou-l">{ln}</div>' for ln in content.OUTRO_SCREEN)
        parts.append(f'''<video id="outrobg" class="clip fv" data-start="{fmt(ot)}" data-duration="{fmt(outro_seg)}" data-track-index="8" src="clips_seg/outro.mp4" muted playsinline></video>
<div id="outrotint" class="clip introtint" data-start="{fmt(ot)}" data-duration="{fmt(outro_seg)}" data-track-index="9" style="background:radial-gradient(120% 80% at 50% 40%, transparent 24%, rgba(70,16,20,.30) 70%, rgba(20,6,8,.66) 100%);"></div>
<div id="outrotxt" class="clip outrotxt" data-start="{fmt(ot)}" data-duration="{fmt(outro_seg)}" data-track-index="12">{oscreen}</div>
<div id="ctaui" class="clip ctaui" data-start="{fmt(ot)}" data-duration="{fmt(outro_seg)}" data-track-index="13">
  <div class="cta-row"><span class="cta-ic">♥</span><span class="cta-ic">★</span><span class="cta-ic">+</span></div>
  <div class="cta-tip">点赞 · 收藏 · 关注</div>
</div>''')
        js.append(f'TLscale("#outrobg",{fmt(ot)},{fmt(outro_seg)});')
        seg_js("#outrobg", ot, ot+outro_seg, 1.0, 2.0)
        seg_js("#outrotint", ot, ot+outro_seg, 1.0, 2.0)
        cta_at = ot + 0.15 + NARR["outro"] + 0.9
        for j, _ in enumerate(content.OUTRO_SCREEN):
            js.append(f'fadeChild(".ou-l:nth-child({j+1})",{fmt(ot+1.2+j*0.9)});')
        seg_js("#outrotxt", ot+1.0, cta_at-0.2, 0.9, 0.6)
        seg_js("#ctaui", cta_at-0.4, ot+outro_seg-1.0, 0.7, 1.2, y=18)

    body = "\n".join(parts)
    js_body = "\n      ".join(js)
    # 渲染用静音占位(真音频后期 mux);避免把 100MB+ 的 master.wav base64 内联进 HTML 卡死 Chrome
    audio = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="100" src="silent.m4a" data-volume="1"></audio>'

    html = TEMPLATE.replace("__BODY__", body).replace("__AUDIO__", audio)\
                   .replace("__JS__", js_body).replace("__COVER_D__", fmt(COVER_D))\
                   .replace("__TOTAL__", fmt(TOTAL))
    Path("hf/index.html").write_text(html, encoding="utf-8")
    Path("hf/meta.json").write_text('{"id":"main","name":"linyilian-scar-to-rose"}', encoding="utf-8")
    print("index.html written:", len(html), "bytes")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@300;400;500;700&family=Cormorant+Garamond:ital,wght@1,400;1,500&family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1920px; background:#06070C; overflow:hidden; }
#stage { position:relative; width:1080px; height:1920px; background:#06070C; font-family:"Noto Sans SC",sans-serif; }

/* footage letterbox 已在文件内做好 */
.fv { position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; z-index:1; opacity:0; will-change:transform,opacity; }

/* 永久层 */
.vig { position:absolute; inset:0; z-index:5; pointer-events:none;
  background:radial-gradient(120% 78% at 50% 42%, transparent 52%, rgba(0,0,0,.55) 100%); }
.grain { position:absolute; inset:0; z-index:60; pointer-events:none; opacity:.05;
  background:url("cover_assets/grain.png") repeat; background-size:300px 300px; }

.songtint,.introtint { position:absolute; inset:0; z-index:3; opacity:0; }

/* ---------- COVER ---------- */
.cover { position:absolute; inset:0; z-index:50; background:#0a0608; overflow:hidden; }
.cv-photo { position:absolute; inset:0; background:url("cover_assets/sandy.png") center 22% / cover no-repeat;
  filter:saturate(.92) contrast(1.04) brightness(.82); }
.cv-grade { position:absolute; inset:0;
  background:linear-gradient(180deg, rgba(8,5,8,.42) 0%, rgba(8,5,8,.05) 30%, rgba(10,5,8,.50) 64%, rgba(8,4,7,.96) 100%); }
.cv-bloom { position:absolute; left:50%; bottom:300px; transform:translateX(-50%); width:760px; height:520px;
  background:radial-gradient(circle, rgba(150,30,40,.42) 0%, rgba(110,20,30,.16) 45%, transparent 70%); filter:blur(8px); }
.cv-frame { position:absolute; inset:30px; border:1px solid rgba(210,168,106,.34); }
.cv-block { position:absolute; left:0; right:0; bottom:150px; text-align:center; z-index:2; }
.cv-rose { display:block; margin:0 auto 14px; filter:drop-shadow(0 8px 24px rgba(120,20,30,.5)); }
.cv-kicker { font-family:"JetBrains Mono",monospace; font-size:25px; letter-spacing:.34em; color:#D2A86A; opacity:.92; margin-bottom:22px; }
.cv-title { font-family:"Noto Serif SC",serif; font-weight:900; font-size:128px; line-height:1.04; color:#F3ECE0;
  letter-spacing:.04em; text-shadow:0 6px 34px rgba(0,0,0,.6); }
.cv-sub { font-family:"Noto Serif SC",serif; font-weight:600; font-size:52px; color:#E8C39A; margin-top:18px; letter-spacing:.10em; }
.cv-rule { width:120px; height:2px; background:linear-gradient(90deg,transparent,#D2A86A,transparent); margin:30px auto 18px; }
.cv-en { font-family:"Cormorant Garamond",serif; font-style:italic; font-size:32px; color:#A9A39A; letter-spacing:.08em; }

/* ---------- INTRO ---------- */
.introtint { background:radial-gradient(120% 80% at 50% 42%, transparent 22%, rgba(40,12,18,.34) 66%, rgba(10,5,8,.74) 100%); }
.introtxt { position:absolute; left:80px; right:80px; bottom:300px; z-index:23; text-align:center; opacity:0; }
.in-line { font-family:"Noto Serif SC",serif; font-weight:700; color:#ECE6DA; opacity:0;
  text-shadow:0 4px 22px rgba(0,0,0,.7); }
.in-1 { font-size:52px; color:#A9A39A; margin-bottom:24px; letter-spacing:.06em; }
.in-2 { font-size:70px; line-height:1.28; letter-spacing:.04em; }
.in-2 .hl { color:#E8B45A; }

/* ---------- 左侧时间线 rail ---------- */
.rail { position:absolute; left:46px; top:300px; z-index:20; opacity:0; }
.rail-line { position:absolute; left:13px; top:8px; bottom:8px; width:2px; background:linear-gradient(180deg,transparent,rgba(210,168,106,.35),transparent); }
.tk { position:relative; display:flex; align-items:center; height:78px; }
.tk-d { width:14px; height:14px; border-radius:50%; background:rgba(255,255,255,.22); margin-left:7px; }
.tk-n { font-family:"JetBrains Mono",monospace; font-size:22px; font-weight:600; color:rgba(255,255,255,.32); margin-left:18px; }
.tk.on .tk-d { width:24px; height:24px; margin-left:2px; background:var(--acc); box-shadow:0 0 22px var(--acc); }
.tk.on .tk-n { color:var(--acc); font-size:30px; font-weight:800; }

/* ---------- 歌名玻璃卡 (顶部暗带) ---------- */
.card { position:absolute; left:150px; right:60px; top:150px; z-index:22; opacity:0;
  padding:34px 40px; border-radius:18px; background:rgba(10,11,17,.66);
  border:1px solid rgba(255,255,255,.10); }
.cd-top { display:flex; align-items:baseline; gap:22px; }
.cd-no { font-family:"JetBrains Mono",monospace; font-weight:800; font-size:62px; color:var(--acc); line-height:1; }
.cd-year { font-family:"JetBrains Mono",monospace; font-size:26px; color:#A9A39A; letter-spacing:.08em; }
.cd-name { font-family:"Noto Serif SC",serif; font-weight:900; font-size:84px; color:#F1EBDF; margin-top:8px; letter-spacing:.03em; }
.cd-credit { font-family:"Noto Sans SC",sans-serif; font-weight:500; font-size:30px; color:#C7C0B5; margin-top:14px; }
.cd-tag { display:inline-block; margin-top:18px; font-family:"Noto Sans SC",sans-serif; font-weight:700; font-size:30px;
  color:var(--acc); padding:6px 22px; border:1.5px solid var(--acc); border-radius:999px; letter-spacing:.18em; }

/* ---------- 底部大屏主题句 ---------- */
.bigtxt { position:absolute; left:70px; right:70px; bottom:226px; z-index:23; text-align:center; opacity:0; }
.bg-song { font-family:"Cormorant Garamond",serif; font-style:italic; font-size:34px; color:var(--acc); opacity:.9; margin-bottom:18px; letter-spacing:.05em; }
.bg-l { font-family:"Noto Serif SC",serif; font-weight:700; font-size:64px; line-height:1.34; color:#F1EBDF;
  text-shadow:0 4px 24px rgba(0,0,0,.78); letter-spacing:.03em; }

/* ---------- 转场字幕 ---------- */
.transcap { position:absolute; left:96px; right:96px; bottom:250px; z-index:24; text-align:center; opacity:0; }
.tc-mark { width:46px; height:3px; background:#D2A86A; margin:0 auto 22px; opacity:.8; }
.tc-txt { font-family:"Noto Sans SC",sans-serif; font-weight:400; font-size:46px; line-height:1.5; color:#D9D3C8;
  text-shadow:0 3px 18px rgba(0,0,0,.8); letter-spacing:.02em; }

/* ---------- OUTRO + CTA ---------- */
.outrotxt { position:absolute; left:80px; right:80px; bottom:430px; z-index:23; text-align:center; opacity:0; }
.ou-l { font-family:"Noto Serif SC",serif; font-weight:700; color:#F1EBDF; opacity:0; margin:14px 0;
  text-shadow:0 4px 22px rgba(0,0,0,.78); }
.ou-l:nth-child(1){ font-size:78px; color:#E8B45A; letter-spacing:.05em; }
.ou-l:nth-child(2){ font-size:50px; color:#C7C0B5; }
.ou-l:nth-child(3){ font-size:50px; color:#F1EBDF; }
.ctaui { position:absolute; left:0; right:0; bottom:200px; z-index:24; text-align:center; opacity:0; }
.cta-row { display:flex; justify-content:center; gap:42px; margin-bottom:20px; }
.cta-ic { width:84px; height:84px; line-height:84px; border-radius:50%; font-size:40px; color:#F1EBDF;
  background:rgba(200,50,74,.30); border:1.5px solid rgba(232,180,90,.6); }
.cta-tip { font-family:"Noto Sans SC",sans-serif; font-weight:700; font-size:38px; color:#E8C39A; letter-spacing:.22em; }
</style>
</head>
<body>
<div id="stage" data-composition-id="main" data-start="0" data-width="1080" data-height="1920">
  <div class="vig"></div>
  <div class="grain"></div>
__BODY__
__AUDIO__
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused:true });

  function S(sel, inAt, outAt, inD, outD, y){
    y = y || 0;
    tl.set(sel, { opacity:0, y:y }, Math.max(inAt-0.001,0));
    tl.to(sel, { opacity:1, y:0, duration:inD, ease:"power2.out" }, inAt);
    if (outAt > inAt + inD){
      tl.to(sel, { opacity:0, duration:outD, ease:"power2.in" }, outAt-outD);
      tl.set(sel, { opacity:0 }, outAt);
    }
  }
  function fadeChild(sel, at){
    tl.set(sel, { opacity:0, y:16 }, Math.max(at-0.001,0));
    tl.to(sel, { opacity:1, y:0, duration:0.8, ease:"power2.out" }, at);
  }
  function TLscale(sel, at, d){
    tl.fromTo(sel, { scale:1.0 }, { scale:1.06, duration:d, ease:"none" }, at);
    tl.set(sel, { scale:1.0 }, at+d);
  }

  // cover：首帧即显示，不做 fade-in
  tl.set("#cover", { opacity:1 }, 0);
  tl.to("#cover", { opacity:0, duration:0.6, ease:"power2.in" }, __COVER_D__-0.6);
  tl.set("#cover", { opacity:0 }, __COVER_D__);

  __JS__

  tl.set({}, {}, __TOTAL__);
  window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
