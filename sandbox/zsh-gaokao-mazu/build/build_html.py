#!/usr/bin/env python3
"""高考妈祖娘 — HyperFrames composition 生成。读 build/timeline.json。
蓝白+金主题；封面(首帧)+开场(倒计时快切)+4part(场景→副歌无缝切+揭晓卡+短评+稀疏弹幕)+outro(回收)。
渲染：npx hyperframes render --output renders/full.mp4 --sdr ；再 mux master.wav。"""
import json
from pathlib import Path

tl = json.loads(Path("build/timeline.json").read_text(encoding="utf-8"))
S = tl["start"]; SEG = tl["seg"]; P = tl["parts"]; TOTAL = tl["total"]
COVER_D = tl["cover_d"]
def f(x): return f"{round(x,3)}"

# ---- 每 part 元数据 ----
PARTS = [
 dict(k="p1", song="破茧", tag="考前冲刺 · 先开大", comment="压力越大，越要破壳",
      danmu=["这首像开大招", "张韶涵：我来陪考了"], trans=None,
      pri="#F5C451", tint="linear-gradient(180deg, rgba(20,46,110,.30) 0%, rgba(10,20,48,.34) 42%, rgba(4,8,22,.74) 100%)"),
 dict(k="p2", song="篇章", tag="赶考路上 · 把这页翻过去", comment="狼狈，也能成篇章",
      danmu=["新闻感拉满", "赶上了就是新开头"], trans="冲出去之后，<br>下一步是翻过去。",
      pri="#FFB860", tint="linear-gradient(180deg, rgba(70,80,96,.28) 0%, rgba(40,40,52,.34) 42%, rgba(8,8,14,.76) 100%)"),
 dict(k="p3", song="淋雨一直走", tag="低谷坚持 · 没伞也向前", comment="走着走着，天就亮了",
      danmu=["考前低谷适用", "边崩溃边前进"], trans="有些路，<br>不是晴天才走。",
      pri="#8FC0F0", tint="linear-gradient(180deg, rgba(40,64,100,.34) 0%, rgba(20,34,60,.36) 45%, rgba(6,12,26,.78) 100%)"),
 dict(k="p4", song="隐形的翅膀", tag="高考DNA · 祖师爷来了", comment="作文题DNA动了",
      danmu=["高考BGM祖师爷", "很多人的青春存档"], trans="真正让张韶涵和高考绑定的，<br>是这一首。",
      pri="#FFD873", tint="linear-gradient(180deg, rgba(62,111,176,.30) 0%, rgba(28,52,96,.30) 40%, rgba(8,14,30,.72) 100%)"),
]
META = {p["k"]: p for p in PARTS}

# ---- 锚点 ----
def anchors(k):
    ps = S[k]; sd = P[k]["scene_dur"]; show = P[k]["show"]
    song = round(ps+sd,3); send = round(song+show,3); pe = round(S[k]+SEG[k],3)
    return dict(ps=ps, sd=sd, song=song, show=show, send=send, pe=pe)
AN = {k: anchors(k) for k in ["p1","p2","p3","p4"]}
INTRO_S = S["intro"]; INTRO_D = SEG["intro"]
OUTRO_S = S["outro"]; OUTRO_D = SEG["outro"]

# ============ footage（交替 track 0/6，z-index 1）============
foot = []
trk = [0]
def nt():
    trk[0] = 6 if trk[0]==0 else 0; return trk[0]
# scene_intro（加长 backdrop 覆盖到倒计时）
foot.append(f'<video id="fv_intro" class="fv clip" data-start="{f(INTRO_S)}" data-duration="{f(INTRO_D+1.5)}" data-track-index="0" src="clips_seg/scene_intro.mp4" muted playsinline></video>')
for k in ["p1","p2","p3","p4"]:
    a = AN[k]
    # 场景提前 0.8s 起(与上段尾重叠交叉淡化)，覆盖到副歌起
    foot.append(f'<video id="fv_sc_{k}" class="fv clip" data-start="{f(a["ps"]-0.8)}" data-duration="{f(a["sd"]+1.0)}" data-track-index="{nt()}" src="clips_seg/scene_{k}.mp4" muted playsinline></video>')
    sn = k.replace("p","s")
    # 副歌 footage 覆盖整段(含 TAIL)到 part 末，避免尾部黑档
    foot.append(f'<video id="fv_song_{k}" class="fv clip" data-start="{f(a["song"]-0.3)}" data-duration="{f(a["show"]+1.5)}" data-track-index="{nt()}" src="clips_seg/song_{sn}.mp4" muted playsinline></video>')
# outro bg（zsh_stage 加长铺满 outro）
foot.append(f'<video id="fv_outro" class="fv clip" data-start="{f(OUTRO_S-0.7)}" data-duration="{f(OUTRO_D+0.7)}" data-track-index="{nt()}" src="clips_seg/zsh_stage.mp4" muted playsinline></video>')

# ============ tint（z-index 2）============
tints = []
for k in ["p1","p2","p3","p4"]:
    a = AN[k]; m = META[k]
    tints.append(f'<div id="tint_{k}" class="clip tintbox" data-start="{f(a["ps"])}" data-duration="{f(a["pe"]-a["ps"])}" data-track-index="11" style="background:{m["tint"]}"></div>')
tints.append(f'<div id="tint_intro" class="clip tintbox" data-start="{f(INTRO_S)}" data-duration="{f(INTRO_D)}" data-track-index="12" style="background:linear-gradient(180deg, rgba(10,20,48,.40) 0%, rgba(6,12,30,.78) 100%)"></div>')
tints.append(f'<div id="tint_outro" class="clip tintbox" data-start="{f(OUTRO_S)}" data-duration="{f(OUTRO_D)}" data-track-index="13" style="background:linear-gradient(180deg, rgba(20,40,90,.42) 0%, rgba(6,12,30,.86) 100%)"></div>')

# ============ 章节 chrome（z-index 4）============
chrome = []
for i,k in enumerate(["p1","p2","p3","p4"]):
    a = AN[k]; m = META[k]
    transhtml = ""
    if m["trans"]:
        transhtml = f'<div class="transcard" id="trans_{k}"><span class="trans-dot"></span><div class="trans-t">{m["trans"]}</div></div>'
    danmu_html = "".join(f'<div class="danmu" id="dm_{k}_{j}">{d}</div>' for j,d in enumerate(m["danmu"]))
    extra = ""
    if k == "p4":
        extra = (f'<div class="examq" id="examq"><div class="examq-yr">2009 · 北京高考作文题</div>'
                 f'<div class="examq-t">《我有一双隐形的翅膀》</div></div>')
    chrome.append(f'''<div id="ch_{k}" class="clip chrome" data-start="{f(a["ps"])}" data-duration="{f(a["pe"]-a["ps"])}" data-track-index="{20+i}" style="--pri:{m["pri"]}">
  {transhtml}
  {extra}
  <div class="reveal" id="rev_{k}">
    <div class="rev-no">第 {i+1} 首</div>
    <div class="rev-name">《{m["song"]}》</div>
    <div class="rev-tag">{m["tag"]}</div>
  </div>
  <div class="cornercard" id="corner_{k}"><span class="corner-name">《{m["song"]}》</span><span class="corner-tag">{m["tag"]}</span></div>
  <div class="comment" id="cmt_{k}">{m["comment"]}</div>
  {danmu_html}
</div>''')

# ============ 封面（z-index 50，首帧；居中布局防小红书裁切）============
cover = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{f(COVER_D)}" data-track-index="30">
  <div class="cv-bg"></div>
  <div class="cv-glow"></div>
  <div class="cv-grid"></div>
  <div class="cv-col">
    <div class="cv-corner">高考季 · BGM 盘点</div>
    <div class="cv-photo"><div class="cv-photo-img"></div><div class="cv-photo-ring"></div></div>
    <div class="cv-title"><span class="cv-t1">高考</span><span class="cv-t2">妈祖娘</span></div>
    <div class="cv-sub">张韶涵 · 六月上岗</div>
    <div class="cv-badges"><span class="cv-b cv-b-gold">六月不调休</span><span class="cv-b cv-b-white">BGM自动上岗</span><span class="cv-b cv-b-line">距高考 06·07</span></div>
  </div>
</div>'''

# ============ 开场 overlay（z-index 49）============
intro = f'''<div id="introv" class="clip introv" data-start="{f(INTRO_S)}" data-duration="{f(INTRO_D)}" data-track-index="31">
  <div class="iv-top"><span class="iv-cd">距高考 06·07</span></div>
  <div class="iv-lines">
    <div class="iv-line" id="iv1">高考妈祖娘？</div>
    <div class="iv-line" id="iv2">张韶涵 六月上岗</div>
    <div class="iv-line" id="iv3">BGM 自动续费</div>
  </div>
  <div class="iv-count" id="ivcount"><span id="ivnum">3</span></div>
  <div class="iv-flash" id="ivflash"></div>
</div>'''

# ============ outro（z-index 48）============
recap = [("破茧","冲出去"),("篇章","翻过去"),("淋雨一直走","撑下去"),("隐形的翅膀","飞得起")]
outro = f'''<div id="outro" class="clip outro" data-start="{f(OUTRO_S)}" data-duration="{f(OUTRO_D)}" data-track-index="32">
  <div class="ot-recap">
    {''.join(f'<div class="ot-line" id="ot{i}"><span class="ot-n">《{n}》</span><span class="ot-v">是{v}</span></div>' for i,(n,v) in enumerate(recap))}
  </div>
  <div class="ot-title" id="ot-title">高考妈祖娘<br><span class="ot-title-n">张韶涵</span></div>
  <div class="ot-sub" id="ot-sub">六月上岗 · 全年有效</div>
  <div class="ot-cta" id="ot-cta">只能选一首高考BGM，<br>你选哪一首？</div>
</div>'''

audio = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ============ CSS ============
CSS = r'''
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0A1430;color:#EAF2FF;font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
:root{--night:#0A1430;--gold:#F5C451;--gold2:#FFD873;--white:#EAF2FF;--blue:#9DB8E8}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0}
.tintbox{position:absolute;inset:0;z-index:2;opacity:0}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none}

/* 揭晓卡 */
.reveal{position:absolute;left:0;right:0;top:560px;text-align:center;opacity:0}
.rev-no{font-size:34px;font-weight:800;letter-spacing:.5em;color:var(--pri);text-shadow:0 2px 24px rgba(0,0,0,.6);margin-bottom:18px;padding-left:.5em}
.rev-name{font-size:150px;font-weight:900;line-height:1;color:#fff;letter-spacing:2px;text-shadow:0 6px 40px rgba(0,0,0,.7),0 0 60px var(--pri)}
.rev-tag{margin-top:26px;display:inline-block;font-size:40px;font-weight:800;color:var(--night);background:var(--pri);padding:12px 30px;border-radius:999px;letter-spacing:.04em;box-shadow:0 12px 40px rgba(0,0,0,.5)}

/* 角标(副歌期常驻) */
.cornercard{position:absolute;left:60px;top:130px;opacity:0;display:flex;flex-direction:column;gap:8px;border-left:5px solid var(--pri);padding:6px 0 6px 22px}
.corner-name{font-size:58px;font-weight:900;color:#fff;line-height:1;text-shadow:0 3px 18px rgba(0,0,0,.7)}
.corner-tag{font-size:27px;font-weight:700;color:var(--pri);letter-spacing:.02em}

/* 短评 */
.comment{position:absolute;left:70px;right:70px;bottom:300px;text-align:center;font-family:"Noto Serif SC",serif;font-size:62px;font-weight:700;color:#fff;line-height:1.3;opacity:0;text-shadow:0 4px 30px rgba(0,0,0,.8)}
.comment::before{content:"「";color:var(--pri)}
.comment::after{content:"」";color:var(--pri)}

/* 转场卡 */
.transcard{position:absolute;left:90px;right:90px;top:780px;text-align:center;opacity:0}
.trans-dot{display:block;width:14px;height:14px;border-radius:50%;background:var(--pri);margin:0 auto 28px;box-shadow:0 0 24px var(--pri)}
.trans-t{font-family:"Noto Serif SC",serif;font-size:66px;font-weight:700;color:#fff;line-height:1.4;text-shadow:0 4px 30px rgba(0,0,0,.85)}

/* 作文题卡 */
.examq{position:absolute;left:90px;right:90px;top:1180px;text-align:center;opacity:0;background:rgba(8,16,38,.62);border:1.5px solid rgba(245,196,81,.5);border-radius:24px;padding:30px 28px;backdrop-filter:blur(8px)}
.examq-yr{font-size:28px;font-weight:800;letter-spacing:.18em;color:var(--gold2)}
.examq-t{margin-top:14px;font-family:"Noto Serif SC",serif;font-size:52px;font-weight:700;color:#fff}

/* 弹幕 */
.danmu{position:absolute;font-size:33px;font-weight:700;color:rgba(255,255,255,.92);white-space:nowrap;opacity:0;text-shadow:0 2px 14px rgba(0,0,0,.85);padding:8px 20px;background:rgba(10,20,48,.30);border-radius:999px;border:1px solid rgba(255,255,255,.14)}
#dm_p1_0,#dm_p2_0,#dm_p3_0,#dm_p4_0{top:430px}
#dm_p1_1,#dm_p2_1,#dm_p3_1,#dm_p4_1{top:1480px}

/* ===== 封面（居中，防小红书裁切：关键元素全居中且在 y240-1680 安全区）===== */
.cover{position:absolute;inset:0;z-index:50;background:#08122C;overflow:hidden}
.cv-bg{position:absolute;inset:0;background-image:url("cover_assets/zsh_yinxing.jpg");background-size:cover;background-position:center 28%;filter:blur(54px) saturate(.7) brightness(.4);transform:scale(1.3);opacity:.42}
.cv-glow{position:absolute;inset:0;background:radial-gradient(ellipse 82% 46% at 50% 7%, rgba(255,216,115,.32) 0%, transparent 56%),radial-gradient(ellipse 100% 52% at 50% 100%, rgba(10,22,64,.85) 0%, transparent 72%),linear-gradient(180deg, rgba(8,16,40,.60) 0%, rgba(8,14,34,.26) 42%, rgba(6,10,26,.84) 100%)}
.cv-grid{position:absolute;inset:0;opacity:.08;background-image:linear-gradient(rgba(157,184,232,.6) 1px,transparent 1px),linear-gradient(90deg,rgba(157,184,232,.6) 1px,transparent 1px);background-size:96px 96px}
.cv-col{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.cv-corner{font-size:28px;font-weight:800;letter-spacing:.26em;color:var(--gold2);border:1.6px solid rgba(255,216,115,.55);border-radius:999px;padding:13px 30px 13px 38px;margin-bottom:44px}
.cv-photo{position:relative;width:500px;height:600px;margin-bottom:50px}
.cv-photo-img{position:absolute;inset:0;background-image:url("cover_assets/zsh_yinxing.jpg");background-size:cover;background-position:center 26%;border-radius:30px;box-shadow:0 34px 90px rgba(0,0,0,.6)}
.cv-photo-ring{position:absolute;inset:-7px;border-radius:37px;border:3.5px solid rgba(255,216,115,.9);box-shadow:0 0 56px rgba(245,196,81,.45)}
.cv-title{display:flex;flex-direction:column;align-items:center;line-height:.9;margin-bottom:28px}
.cv-t1{font-size:96px;font-weight:900;color:#fff;letter-spacing:10px;text-shadow:0 4px 30px rgba(0,0,0,.5);padding-left:10px}
.cv-t2{font-size:192px;font-weight:900;letter-spacing:6px;padding-left:6px;background:linear-gradient(160deg,#FFE9A8 0%,#F5C451 46%,#E0A52E 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 8px 32px rgba(245,196,81,.45))}
.cv-sub{font-size:50px;font-weight:800;color:var(--white);letter-spacing:.1em;margin-bottom:42px}
.cv-badges{display:flex;gap:18px;align-items:center}
.cv-b{font-size:30px;font-weight:800;padding:14px 24px;border-radius:14px;white-space:nowrap}
.cv-b-gold{background:var(--gold);color:#1A1408;transform:rotate(-3deg);box-shadow:0 8px 22px rgba(0,0,0,.35)}
.cv-b-white{background:rgba(234,242,255,.96);color:#0A1430;transform:rotate(2deg)}
.cv-b-line{background:rgba(10,22,58,.66);color:var(--gold2);border:1.5px solid rgba(255,216,115,.5);font-family:"Oswald",sans-serif;letter-spacing:.06em}

/* ===== 开场 ===== */
.introv{position:absolute;inset:0;z-index:49}
.iv-top{position:absolute;top:90px;left:0;right:0;text-align:center}
.iv-cd{font-family:"Oswald",sans-serif;font-size:40px;font-weight:600;letter-spacing:.2em;color:var(--gold2);border:1.5px solid rgba(255,216,115,.5);border-radius:999px;padding:12px 34px}
.iv-lines{position:absolute;left:80px;right:80px;top:780px;display:flex;flex-direction:column;gap:40px;align-items:center}
.iv-line{font-size:84px;font-weight:900;color:#fff;opacity:0;text-shadow:0 4px 30px rgba(0,0,0,.8)}
#iv2{color:var(--gold2)}
.iv-count{position:absolute;left:0;right:0;top:760px;text-align:center;opacity:0}
#ivnum{font-family:"Oswald",sans-serif;font-size:420px;font-weight:700;color:#fff;line-height:1;text-shadow:0 0 80px var(--gold)}
.iv-flash{position:absolute;inset:0;background:#fff;opacity:0}

/* ===== outro ===== */
.outro{position:absolute;inset:0;z-index:48}
.ot-recap{position:absolute;left:90px;right:90px;top:300px}
.ot-line{display:flex;align-items:baseline;gap:24px;padding:14px 0;opacity:0}
.ot-n{font-size:62px;font-weight:900;color:#fff;min-width:430px}
.ot-v{font-size:46px;font-weight:700;color:var(--gold2)}
.ot-title{position:absolute;left:90px;right:90px;top:880px;font-size:118px;font-weight:900;line-height:1.04;color:#fff;opacity:0;letter-spacing:2px}
.ot-title-n{background:linear-gradient(160deg,#FFE9A8,#F5C451 60%,#E0A52E);-webkit-background-clip:text;background-clip:text;color:transparent}
.ot-sub{position:absolute;left:92px;top:1200px;font-size:46px;font-weight:800;color:var(--gold2);opacity:0;letter-spacing:.04em}
.ot-cta{position:absolute;left:90px;right:90px;top:1370px;font-family:"Noto Serif SC",serif;font-size:64px;font-weight:700;color:#fff;line-height:1.4;opacity:0}
'''

# ============ JS timeline ============
def part_js(i, k):
    a = AN[k]; m = META[k]
    ps=a["ps"]; sd=a["sd"]; song=a["song"]; send=a["send"]; pe=a["pe"]
    js = []
    # 场景 footage 入/出（提前 0.8s 起与上段交叉淡化）
    js.append(f'tl.fromTo("#fv_sc_{k}",{{opacity:0}},{{opacity:1,duration:.9,ease:"power2.out"}},{f(ps-0.8)});')
    js.append(f'tl.to("#fv_sc_{k}",{{opacity:0,duration:.6,ease:"power1.in"}},{f(song-0.3)});')
    js.append(f'tl.set("#fv_sc_{k}",{{opacity:0}},{f(song+0.5)});')
    js.append(f'tl.to("#tint_{k}",{{opacity:1,duration:.8}},{f(ps)});')
    # 转场卡(p2-4) 或 p1 无
    if m["trans"]:
        tdur = {"p2":3.6,"p3":2.9,"p4":4.6}[k]
        js.append(f'tl.fromTo("#trans_{k}",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.5,ease:"power2.out"}},{f(ps+0.4)});')
        js.append(f'tl.to("#trans_{k}",{{opacity:0,y:-16,duration:.5,ease:"power2.in"}},{f(ps+0.4+tdur)});')
        js.append(f'tl.set("#trans_{k}",{{opacity:0}},{f(ps+0.4+tdur+0.4)});')
    # 作文题卡(p4)
    if k=="p4":
        js.append(f'tl.fromTo("#examq",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.6,ease:"power2.out"}},{f(ps+6.4)});')
        js.append(f'tl.to("#examq",{{opacity:0,duration:.5,ease:"power1.in"}},{f(song-0.4)});')
        js.append(f'tl.set("#examq",{{opacity:0}},{f(song)});')
    # 场景期弹幕0(上)
    js.append(f'tl.fromTo("#dm_{k}_0",{{opacity:0,x:120}},{{opacity:.96,x:0,duration:.6,ease:"power2.out"}},{f(ps+sd*0.42)});')
    js.append(f'tl.to("#dm_{k}_0",{{opacity:0,x:-120,duration:.8,ease:"power1.in"}},{f(ps+sd*0.42+3.0)});')
    js.append(f'tl.set("#dm_{k}_0",{{opacity:0}},{f(ps+sd*0.42+3.9)});')
    # 副歌 footage 入/出（覆盖到 part 末 pe-0.5，与下段场景交叉淡化）
    js.append(f'tl.fromTo("#fv_song_{k}",{{opacity:0}},{{opacity:1,duration:.6,ease:"power2.out"}},{f(song-0.3)});')
    js.append(f'tl.to("#fv_song_{k}",{{opacity:0,duration:.6,ease:"power1.in"}},{f(pe-0.5)});')
    js.append(f'tl.set("#fv_song_{k}",{{opacity:0}},{f(pe+0.2)});')
    # 揭晓卡(song起)
    js.append(f'tl.fromTo("#rev_{k}",{{opacity:0,scale:.86}},{{opacity:1,scale:1,duration:.7,ease:"back.out(1.5)"}},{f(song-0.1)});')
    js.append(f'tl.to("#rev_{k}",{{opacity:0,scale:1.05,duration:.5,ease:"power2.in"}},{f(song+3.0)});')
    js.append(f'tl.set("#rev_{k}",{{opacity:0}},{f(song+3.6)});')
    # 角标常驻
    js.append(f'tl.fromTo("#corner_{k}",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{f(song+3.2)});')
    js.append(f'tl.to("#corner_{k}",{{opacity:0,duration:.6,ease:"power1.in"}},{f(send-0.4)});')
    js.append(f'tl.set("#corner_{k}",{{opacity:0}},{f(pe)});')
    # 短评(副歌中段)
    cmt_at = round(song + a["show"]*0.46,3)
    js.append(f'tl.fromTo("#cmt_{k}",{{opacity:0,y:22}},{{opacity:1,y:0,duration:.6,ease:"power2.out"}},{f(cmt_at)});')
    js.append(f'tl.to("#cmt_{k}",{{opacity:0,y:-14,duration:.6,ease:"power2.in"}},{f(cmt_at+3.4)});')
    js.append(f'tl.set("#cmt_{k}",{{opacity:0}},{f(cmt_at+4.0)});')
    # 副歌弹幕1(下)
    dm_at = round(song + a["show"]*0.72,3)
    js.append(f'tl.fromTo("#dm_{k}_1",{{opacity:0,x:120}},{{opacity:.96,x:0,duration:.6,ease:"power2.out"}},{f(dm_at)});')
    js.append(f'tl.to("#dm_{k}_1",{{opacity:0,x:-120,duration:.8,ease:"power1.in"}},{f(dm_at+3.0)});')
    js.append(f'tl.set("#dm_{k}_1",{{opacity:0}},{f(dm_at+3.9)});')
    # tint 出
    js.append(f'tl.to("#tint_{k}",{{opacity:0,duration:.8,ease:"power1.in"}},{f(pe-0.8)});')
    js.append(f'tl.set("#tint_{k}",{{opacity:0}},{f(pe)});')
    return "\n".join(js)

JS = f'''
// 封面 (首帧 opacity:1, 6s后呼吸)
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-col",{{opacity:1}},0);
tl.to(".cv-t2",{{scale:1.03,duration:1.6,yoyo:true,repeat:1,ease:"sine.inOut"}},1.0);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{f(COVER_D-0.6)});
tl.set("#cover",{{opacity:0}},{f(COVER_D)});

// 开场 footage + overlay
tl.fromTo("#fv_intro",{{opacity:0}},{{opacity:1,duration:.6}},{f(INTRO_S)});
tl.to("#fv_intro",{{opacity:0,duration:.8,ease:"power1.in"}},{f(INTRO_S+INTRO_D-0.5)});
tl.set("#fv_intro",{{opacity:0}},{f(INTRO_S+INTRO_D+0.8)});
tl.fromTo("#tint_intro",{{opacity:0}},{{opacity:1,duration:.6}},{f(INTRO_S)});
tl.to("#tint_intro",{{opacity:0,duration:.5}},{f(INTRO_S+INTRO_D-0.4)});
tl.set("#tint_intro",{{opacity:0}},{f(INTRO_S+INTRO_D)});
tl.fromTo("#introv .iv-top",{{opacity:0,y:-20}},{{opacity:1,y:0,duration:.6}},{f(INTRO_S+0.2)});
{''.join(f'tl.fromTo("#iv{j+1}",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.5,ease:"power2.out"}},{f(INTRO_S+0.6+j*1.9)});'+chr(10)+f'tl.to("#iv{j+1}",{{opacity:.25,duration:.5}},{f(INTRO_S+0.6+j*1.9+1.5)});'+chr(10) for j in range(3))}
tl.to("#introv .iv-top",{{opacity:0,duration:.4}},{f(INTRO_S+INTRO_D-2.6)});
{''.join(f'tl.to("#iv{j+1}",{{opacity:0,duration:.3}},{f(INTRO_S+INTRO_D-2.6)});'+chr(10) for j in range(3))}
// 倒计时 3-2-1 + 闪白 → part1
tl.set("#ivcount",{{opacity:1}},{f(INTRO_S+INTRO_D-2.4)});
tl.fromTo("#ivnum",{{scale:.6,opacity:0}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2)"}},{f(INTRO_S+INTRO_D-2.4)});
tl.set("#ivnum",{{innerText:"2"}},{f(INTRO_S+INTRO_D-1.7)});tl.fromTo("#ivnum",{{scale:.6,opacity:.2}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2)"}},{f(INTRO_S+INTRO_D-1.7)});
tl.set("#ivnum",{{innerText:"1"}},{f(INTRO_S+INTRO_D-1.0)});tl.fromTo("#ivnum",{{scale:.6,opacity:.2}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2)"}},{f(INTRO_S+INTRO_D-1.0)});
tl.to("#ivcount",{{opacity:0,duration:.2}},{f(INTRO_S+INTRO_D-0.45)});
tl.set("#ivcount",{{opacity:0}},{f(INTRO_S+INTRO_D)});
tl.fromTo("#ivflash",{{opacity:0}},{{opacity:.9,duration:.18}},{f(INTRO_S+INTRO_D-0.4)});
tl.to("#ivflash",{{opacity:0,duration:.5}},{f(INTRO_S+INTRO_D-0.22)});
tl.set("#ivflash",{{opacity:0}},{f(INTRO_S+INTRO_D+0.2)});

{''.join(part_js(i,k) for i,k in enumerate(["p1","p2","p3","p4"]))}

// outro
tl.fromTo("#fv_outro",{{opacity:0}},{{opacity:1,duration:.9}},{f(OUTRO_S-0.7)});
tl.to("#fv_outro",{{opacity:.5,duration:1.0}},{f(OUTRO_S+1.2)});
tl.fromTo("#tint_outro",{{opacity:0}},{{opacity:1,duration:.8}},{f(OUTRO_S)});
{''.join(f'tl.fromTo("#ot{i}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.5,ease:"power2.out"}},{f(OUTRO_S+0.4+i*0.6)});'+chr(10) for i in range(4))}
tl.fromTo("#ot-title",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(OUTRO_S+3.4)});
tl.fromTo("#ot-sub",{{opacity:0}},{{opacity:1,duration:.6}},{f(OUTRO_S+4.6)});
tl.fromTo("#ot-cta",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{f(OUTRO_S+5.6)});
tl.to("#outro",{{opacity:1,duration:.1}},{f(TOTAL-0.2)});
'''

html = f'''<!doctype html>
<html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800;900&family=Noto+Serif+SC:wght@600;700;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
{chr(10).join(foot)}
{chr(10).join(tints)}
{chr(10).join(chrome)}
{cover}
{intro}
{outro}
{audio}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script>
</body></html>'''

Path("hf/index.html").write_text(html, encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"zsh-gaokao-mazu"}', encoding="utf-8")
print("index.html:", len(html), "bytes; TOTAL", TOTAL)

# ---- 封面专项测试 composition（仅 cover，1.2s，快渲验缩略图）----
cover_test = f'''<!doctype html><html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;800;900&family=Noto+Serif+SC:wght@600;700;900&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="1.2" data-width="1080" data-height="1920">
<div id="cover" class="clip cover" data-start="0" data-duration="1.2" data-track-index="0">{cover[cover.index('>')+1:cover.rindex('</div>')]}</div>
</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
tl.set("#cover",{{opacity:1}},0);window.__timelines["main"]=tl;</script>
</body></html>'''
Path("hf/cover_test.html").write_text(cover_test, encoding="utf-8")
print("cover_test.html written")

# ---- 预览 composition（cover+intro+part1，前 ~55s）----
PREVIEW_D = round(S["p1"] + SEG["p1"] + 1.5, 3)
preview = html.replace(f'data-duration="{f(TOTAL)}"', f'data-duration="{f(PREVIEW_D)}"')
Path("hf/preview.html").write_text(preview, encoding="utf-8")
print("preview.html written, dur", PREVIEW_D)
