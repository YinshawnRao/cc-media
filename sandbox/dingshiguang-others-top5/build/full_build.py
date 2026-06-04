#!/usr/bin/env python3
"""丁世光为别人写的歌 TOP5 — 完整片构建（竖屏 1080×1920，倒数 #5→#1）。
- 揭晓顺序：倒数（先 #5，最后 #1 压轴）；封面/开场不剧透排名；结尾画面揭晓 TOP1→TOP5。
- 每首：排名卡 → 女声引入旁白(音乐床+ducking) → swell → 完整副歌展示(纯音乐+大字+金句) → 收束。
- #3《爱来过》解耦：音频用 S.H.E 录音室原声(raw/s3_ailaiguo.wav)，画面用 S.H.E 演唱会干净特写(raw_h264/s3_ailaiguo.mp4，montage救场)。
- 产物：clips_seg/<key>.mp4 + master.wav(逐段 床→swell→副歌 + ducking + 逐首loudnorm) + hf/index.html。
渲染后必须 ffmpeg mux master.wav。无 meta 文案、无水印/烧词残留。
"""
import subprocess, wave, contextlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "audio"
RAWH = ROOT / "raw_h264"
RAWW = ROOT / "raw"
CSEG = ROOT / "clips_seg"
HF = ROOT / "hf"
SEGS = ROOT / "build" / "segs"
for d in (CSEG, HF, SEGS, HF / "clips_seg", HF / "cover_assets"):
    d.mkdir(parents=True, exist_ok=True)

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)

# ---------------- 旁白时长 ----------------
NARR = {k: dur(A / f"{k}.wav") for k in ["intro", "s1", "s2", "s3", "s4", "s5", "outro"]}
print("NARR:", json.dumps(NARR, ensure_ascii=False))

# ---------------- 节奏常量 ----------------
LEAD = 0.15
PRE_VOICE = 0.8
POST_VOICE = 1.2
SWELL = 1.6
TAIL = 1.3
BED = 0.17
COVER_D = 4.0
INTRO_VOICE_AT = 2.8
INTRO_TAIL = 2.2

# ---------------- 每首歌定义（rank 1→5；倒数呈现 s5→s1） ----------------
# chorus=源音频中完整副歌起点(s)；high=副歌展示时长；vseek=画面源起点(None=与音频同步)
SONGS = [
    dict(key="s1", no="01", name="心酸", singer="林宥嘉",
         credit="作曲 · 编曲　丁世光", tag="综合传唱度最高 · 绕不开的第一",
         kw="酸", quote="越听，后劲越上来——<br>那种心酸，是慢慢漫上来的。",
         src="s1_xinsuan_redbull", chorus=188.0, high=15.5, vseek=None,
         crop="864:1080:528:0", br=-0.04, sat=1.06,
         pri="#F0C572", acc="#FCEBC2", muted="#8C6A33",
         tint="linear-gradient(180deg, rgba(240,197,114,.12) 0%, rgba(10,16,30,.50) 44%, rgba(0,0,0,.86) 100%)",
         src_label="红牛不插电 Live · 哔哩哔哩", crown=True),
    dict(key="s2", no="02", name="Catherine", singer="陶喆",
         credit="作曲　丁世光", tag="幕后天才被看见 · 履历分量",
         kw="光", quote="正是这一首，<br>让世界第一次记住「丁世光」。",
         src="s2_catherine", chorus=131.0, high=17.0, vseek=None,
         crop="864:952:528:0", br=0.05, sat=1.05,
         pri="#D06A74", acc="#EBB9BE", muted="#6E3138",
         tint="linear-gradient(180deg, rgba(150,55,65,.20) 0%, rgba(18,8,10,.56) 45%, rgba(0,0,0,.90) 100%)",
         src_label="官方MV 4K修复 · 哔哩哔哩"),
    dict(key="s3", no="03", name="爱来过", singer="S.H.E",
         credit="作曲　丁世光　·　作词　施人诚", tag="国民度 · 偶像剧OST滤镜",
         kw="爱", quote="够抓耳，够青春——<br>偶像剧滤镜下的国民情歌。",
         src="s3_ailaiguo", chorus=64.0, high=16.0, vseek=28.0,
         crop="864:1080:528:0", br=-0.02, sat=1.05,
         pri="#E98AA4", acc="#FBD0DC", muted="#7E3A4C",
         tint="linear-gradient(180deg, rgba(225,110,150,.14) 0%, rgba(24,10,16,.54) 45%, rgba(0,0,0,.88) 100%)",
         src_label="演唱会 Live 现场 · YouTube"),
    dict(key="s4", no="04", name="肋骨", singer="周笔畅",
         credit="作曲　丁世光　·　作词　小寒", tag="骨感R&B · 歌迷心头好",
         kw="骨", quote="克制里带着力气，<br>骨子里是丁世光的 R&B。",
         src="s4_lvgu", chorus=158.0, high=18.0, vseek=None,
         crop="660:820:632:0", br=0.06, sat=1.08,
         pri="#7FB4D0", acc="#D2E8F4", muted="#3F5E72",
         tint="linear-gradient(180deg, rgba(120,170,205,.14) 0%, rgba(8,16,26,.55) 45%, rgba(0,0,0,.88) 100%)",
         src_label="LUNAR 巡演 Live · YouTube"),
    dict(key="s5", no="05", name="讽刺的情书", singer="田馥甄",
         credit="作词 · 作曲 · 编曲　丁世光", tag="词曲编曲全包 · 风格最完整",
         kw="信", quote="词、曲、编曲一个人包办——<br>所以它，最像他自己。",
         src="s5_fengci", chorus=199.0, high=16.0, vseek=None,
         crop="864:992:528:0", br=0.08, sat=1.06,
         pri="#E2B574", acc="#F6E0B6", muted="#7E5E2C",
         tint="linear-gradient(180deg, rgba(226,181,116,.13) 0%, rgba(24,18,8,.54) 45%, rgba(0,0,0,.88) 100%)",
         src_label="官方MV · YouTube"),
]
SM = {s["key"]: s for s in SONGS}
COUNTDOWN = ["s5", "s4", "s3", "s2", "s1"]   # 倒数呈现顺序
RANK_ORDER = ["s1", "s2", "s3", "s4", "s5"]  # outro 揭晓顺序 TOP1->TOP5

# ---------------- 段时长与锚点 ----------------
def full0_of(key):
    return LEAD + PRE_VOICE + NARR[key] + POST_VOICE + SWELL

def seg_len_of(key):
    return full0_of(key) + SM[key]["high"] + TAIL

intro_seg = max(COVER_D, INTRO_VOICE_AT) + NARR["intro"] + INTRO_TAIL
outro_seg = LEAD + NARR["outro"] + 3.6

starts = {}
t = 0.0
starts["intro"] = (round(t, 3), round(intro_seg, 3)); t += intro_seg
for k in COUNTDOWN:
    L = seg_len_of(k); starts[k] = (round(t, 3), round(L, 3)); t += L
starts["outro"] = (round(t, 3), round(outro_seg, 3)); t += outro_seg
TOTAL = round(t, 3)
print(f"TOTAL: {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")
for k in ["intro"] + COUNTDOWN + ["outro"]:
    st, ln = starts[k]; print(f"  {k:6s} start={st:7.2f} len={ln:6.2f}")

def anchors(key):
    v0 = LEAD + PRE_VOICE
    v1 = v0 + NARR[key]
    sw0 = v1 + POST_VOICE
    full0 = sw0 + SWELL
    full1 = full0 + SM[key]["high"]
    return dict(v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1)

def mseek_of(key):   # 音频副歌对齐 full0
    return round(SM[key]["chorus"] - full0_of(key), 3)

def vseek_of(key):   # 画面起点（默认与音频同步）
    s = SM[key]
    return round(s["vseek"], 3) if s.get("vseek") is not None else mseek_of(key)

# =========================================================
# 1) footage：竖屏(裁烧词/水印) → clips_seg
# =========================================================
def vert_filter(crop, br, sat):
    return (f"[0:v]crop={crop},split=2[bg][fg];"
            f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"gblur=sigma=30,eq=brightness={br}:saturation={sat}[bgb];"
            f"[fg]scale=1080:-2[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")

def build_footage(s):
    key = s["key"]; vs = vseek_of(key); L = starts[key][1]
    src = RAWH / f"{s['src']}.mp4"
    out = CSEG / f"{key}.mp4"
    run(["ffmpeg", "-v", "error", "-ss", vs, "-i", src, "-t", L,
         "-filter_complex", vert_filter(s["crop"], s["br"], s["sat"]),
         "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", out, "-y"])
    print(f"  footage {key}.mp4  vseek={vs}  len={L}")

print("== footage ==")
for s in SONGS:
    build_footage(s)

# =========================================================
# 2) 音频 master
# =========================================================
def build_song_audio(s):
    key = s["key"]; a = anchors(key); L = starts[key][1]
    ms = mseek_of(key)
    voice_at = a["v0"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{voice_at}))*({BED}*(t-{LEAD})/{voice_at-LEAD})"
          f"+(between(t,{voice_at},{sw0}))*{BED}"
          f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
          f"+(gte(t,{full0}))*1.0")
    out = SEGS / f"seg_{key}.wav"
    run(["ffmpeg", "-v", "error", "-i", RAWW / f"{s['src']}.wav", "-i", A / f"{key}.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,"
         f"atrim={ms}:{ms+L},asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"volume='{ve}':eval=frame,afade=t=out:st={full1}:d={L-full1}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{L},alimiter=limit=0.96[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y"])
    print(f"  seg_{key}.wav  ({L}s)  ms={ms}")

# intro/outro 低 ambient 床（用《讽刺的情书》器乐前段，温暖、与开场调性贴）
BED_SRC = "s5_fengci"
def build_pad_seg(name, seg_len, voice_at, bed_src_seek, bed_vol, fade_in, fade_out):
    run(["ffmpeg", "-v", "error", "-i", RAWW / f"{BED_SRC}.wav", "-i", A / f"{name}.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim={bed_src_seek}:{bed_src_seek+seg_len},asetpts=PTS-STARTPTS,"
         f"loudnorm=I=-15:TP=-1.0:LRA=11,volume={bed_vol},afade=t=in:st=0:d={fade_in},afade=t=out:st={seg_len-fade_out}:d={fade_out}[bed];"
         f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.96[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", SEGS / f"seg_{name}.wav", "-y"])
    print(f"  seg_{name}.wav ({seg_len}s)")

print("== audio segs ==")
build_pad_seg("intro", round(intro_seg, 3), INTRO_VOICE_AT, 30.0, 0.22, 0.7, 1.7)
for s in SONGS:
    build_song_audio(s)
build_pad_seg("outro", round(outro_seg, 3), LEAD + 0.3, 60.0, 0.22, 1.0, 2.6)

order = ["intro"] + COUNTDOWN + ["outro"]
(SEGS / "seglist.txt").write_text("".join(f"file 'seg_{k}.wav'\n" for k in order), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", SEGS / "seglist.txt",
     "-ac", "2", "-ar", "48000", ROOT / "master.wav", "-y"])
print("master dur:", dur(ROOT / "master.wav"), "planned:", TOTAL)

# 复制资源到 hf/
shutil.copy(ROOT / "master.wav", HF / "master.wav")
for s in SONGS:
    shutil.copy(CSEG / f"{s['key']}.mp4", HF / "clips_seg" / f"{s['key']}.mp4")

# 封面肖像（丁世光本人，用户提供 160x160）：圆头像 + 模糊底图
run(["ffmpeg", "-v", "error", "-i", RAWW / "ding_profile.jpg",
     "-vf", "scale=600:600:flags=lanczos,unsharp=5:5:0.8", HF / "cover_assets" / "ding.jpg", "-y"])
run(["ffmpeg", "-v", "error", "-i", RAWW / "ding_profile.jpg",
     "-vf", "scale=900:900:flags=lanczos", HF / "cover_assets" / "ding_bg.jpg", "-y"])
print("assets copied")

# =========================================================
# 3) HTML 合成
# =========================================================
def f(x): return f"{round(x,3)}"

abs_a = {}
for k in COUNTDOWN:
    base = starts[k][0]; a = anchors(k)
    abs_a[k] = {kk: round(base + vv, 3) for kk, vv in a.items()}
    abs_a[k]["start"] = base
    abs_a[k]["end"] = round(base + starts[k][1], 3)

INTRO_T, INTRO_D = starts["intro"]
OUTRO_T, OUTRO_D = starts["outro"]

# footage（交替 track 0/6）
foot_tracks = {k: (0 if i % 2 == 0 else 6) for i, k in enumerate(COUNTDOWN)}
foot_html = []
for k in COUNTDOWN:
    a = abs_a[k]; sect = a["end"] - a["start"]
    foot_html.append(
        f'<video id="fv_{k}" class="fv clip" data-start="{f(a["start"])}" data-duration="{f(sect)}" '
        f'data-track-index="{foot_tracks[k]}" src="clips_seg/{k}.mp4" muted playsinline></video>')

tint_html = []
for i, k in enumerate(COUNTDOWN):
    a = abs_a[k]; sect = a["end"] - a["start"]
    tint_html.append(
        f'<div id="tint_{k}" class="clip tint tint_{k}" data-start="{f(a["start"])}" '
        f'data-duration="{f(sect)}" data-track-index="{10+i}"></div>')

# chrome（排名卡 + 左轨 + 大字 + 金句 + 来源标）
# 左轨：自上而下 05..01；当前高亮，已揭晓(更靠后名次,序号更大)的标记为 done
def rail_html_for(cur_key):
    cur_rank = int(SM[cur_key]["no"])  # 1..5
    items = []
    for rk in [5, 4, 3, 2, 1]:
        cls = "rd"
        if rk == cur_rank: cls += " act"
        elif rk > cur_rank: cls += " done"   # 已经数过的（更后名次）
        top = 6 + (5 - rk) * 20.5
        items.append(f'<div class="{cls}" style="top:{top}%"><span class="rt">{rk:02d}</span></div>')
    return "".join(items)

chrome_html = []
for i, k in enumerate(COUNTDOWN):
    s = SM[k]; a = abs_a[k]; sect = a["end"] - a["start"]
    crown = '<div class="crown">榜 · 首</div>' if s.get("crown") else ''
    chrome_html.append(f'''<div id="ch_{k}" class="clip chrome ch_{k}" data-start="{f(a["start"])}" data-duration="{f(sect)}" data-track-index="{20+i}">
  <div class="rail"><div class="rail-bar"></div>{rail_html_for(k)}</div>
  <div class="card">
    <div class="card-rankrow"><span class="card-rk">NO.</span><span class="card-no">{s["no"]}</span>{crown}</div>
    <div class="card-name">{s["name"]}</div>
    <div class="card-singer">{s["singer"]}</div>
    <div class="card-credit">{s["credit"]}</div>
    <div class="card-tag"><span class="dot"></span>{s["tag"]}</div>
  </div>
  <div class="kw" id="kw_{k}">{s["kw"]}</div>
  <div class="quote" id="qt_{k}">{s["quote"]}</div>
  <div class="src" id="src_{k}">{s["src_label"]}</div>
</div>''')

# 封面（首帧即封面）：丁世光肖像 + 杂志大标题 + 作品描述(不剧透排名,按年代列, 无序号)
COVER_CHIPS = [("Catherine", "陶喆"), ("爱来过", "S.H.E"), ("肋骨", "周笔畅"),
               ("心酸", "林宥嘉"), ("讽刺的情书", "田馥甄")]
cover_chips = "".join(
    f'<div class="cv-chip"><span class="cv-cn">《{nm}》</span><span class="cv-cs">{sg}</span></div>'
    for nm, sg in COVER_CHIPS)
cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{f(COVER_D)}" data-track-index="30">
  <div class="cv-bg"></div><div class="cv-veil"></div>
  <div class="cv-vinyl"></div><div class="cv-staff"></div><div class="cv-grain"></div>
  <div class="cv-head"><div class="cv-eyebrow">华语幕后创作者</div><div class="cv-byline">词 · 曲 · 编曲</div></div>
  <div class="cv-portrait"><div class="cv-pimg"></div><div class="cv-pring"></div></div>
  <div class="cv-titlewrap">
    <div class="cv-kicker">原来这些歌，都是他写的</div>
    <h1 class="cv-title">丁世光<br>写给别人的歌<span class="cv-top5">TOP5</span></h1>
    <div class="cv-sub">他自己也唱，但更动人的旋律，留给了别人</div>
  </div>
  <div class="cv-list">{cover_chips}</div>
</div>'''

# hook：标题 + 主题句（不列排名）
hook_html = f'''<div id="hook" class="clip hook" data-start="{f(COVER_D)}" data-duration="{f(INTRO_D-COVER_D)}" data-track-index="31">
  <div class="hk-grad"></div>
  <div class="hk-kick">华语幕后创作者</div>
  <div class="hk-title">丁世光<br>为别人写的歌 <span class="hk-t5">TOP5</span></div>
  <div class="hk-sub">那几首你单曲循环过的歌，<br>背后都是同一支笔</div>
  <div class="hk-hint">这支笔，藏在太多首歌里</div>
</div>'''

# outro：揭晓 TOP1→TOP5 + 结尾字幕
outro_lines = "".join(
    f'<div class="ot-line"><span class="ot-no">{SM[k]["no"]}</span>'
    f'<span class="ot-nm">{SM[k]["name"]}</span>'
    f'<span class="ot-sg">{SM[k]["singer"]}</span></div>' for k in RANK_ORDER)
outro_html = f'''<div id="outro" class="clip outroblk" data-start="{f(OUTRO_T)}" data-duration="{f(OUTRO_D)}" data-track-index="32">
  <div class="ot-bg"></div>
  <div class="ot-eyebrow">完整榜单</div>
  <div class="ot-rail">{outro_lines}</div>
  <h2 class="ot-h">他写给别人的歌，<br>也是一部隐藏的<br>丁世光作品集。</h2>
</div>'''

audio_html = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

chrome_vars = "\n".join(
    f'.ch_{s["key"]} {{ --pri:{s["pri"]}; --acc:{s["acc"]}; --muted:{s["muted"]}; }}' for s in SONGS)
tint_css = "\n".join(f'.tint_{s["key"]} {{ background:{s["tint"]}; }}' for s in SONGS)

CSS = f'''
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:1080px; height:1920px; overflow:hidden; background:#06070C;
  font-family:"Noto Serif SC",serif; color:#F4EFE6; -webkit-font-smoothing:antialiased; }}
.fv {{ position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; z-index:1; opacity:0; }}
.tint {{ position:absolute; inset:0; z-index:2; opacity:0; }}
{tint_css}
#vign {{ position:absolute; inset:0; z-index:3; pointer-events:none;
  background:linear-gradient(180deg, rgba(0,0,0,.44) 0%, rgba(0,0,0,0) 16%, rgba(0,0,0,0) 76%, rgba(0,0,0,.58) 100%); }}
.chrome {{ position:absolute; inset:0; z-index:4; pointer-events:none; }}
{chrome_vars}

/* 左侧倒数轨 */
.rail {{ position:absolute; top:150px; left:60px; bottom:300px; width:10px; opacity:0; }}
.rail-bar {{ position:absolute; top:0; bottom:0; left:4px; width:2px;
  background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.22), rgba(255,255,255,.06)); }}
.rd {{ position:absolute; left:-23px; width:54px; height:54px; border-radius:50%;
  background:rgba(16,16,22,.9); border:2px solid rgba(255,255,255,.20);
  display:flex; align-items:center; justify-content:center; }}
.rd.done {{ background:rgba(70,68,74,.55); border-color:rgba(255,255,255,.26); }}
.rd.act {{ background:var(--pri); border-color:var(--pri);
  box-shadow:0 0 30px var(--pri), 0 0 64px rgba(255,255,255,.18); transform:scale(1.22); }}
.rt {{ font-family:"JetBrains Mono",monospace; font-size:23px; font-weight:800; color:rgba(255,255,255,.7); }}
.rd.act .rt {{ color:rgba(14,14,18,.95); }}
.rd.done .rt {{ color:rgba(255,255,255,.45); }}

/* 排名卡 */
.card {{ position:absolute; top:140px; right:54px; width:672px; padding:42px 46px 40px;
  border-radius:24px; background:linear-gradient(160deg, rgba(255,255,255,.11), rgba(255,255,255,.03));
  backdrop-filter:blur(30px); -webkit-backdrop-filter:blur(30px);
  border:1.5px solid rgba(255,255,255,.18); box-shadow:0 34px 90px rgba(0,0,0,.6); opacity:0; }}
.card-rankrow {{ display:flex; align-items:baseline; gap:14px; margin-bottom:8px; }}
.card-rk {{ font-family:"JetBrains Mono",monospace; font-size:30px; font-weight:700;
  letter-spacing:.1em; color:rgba(255,255,255,.5); }}
.card-no {{ font-family:"JetBrains Mono",monospace; font-size:104px; font-weight:800; line-height:.86;
  color:var(--pri); letter-spacing:-3px; text-shadow:0 0 34px rgba(0,0,0,.4); }}
.crown {{ margin-left:auto; align-self:center; font-family:"Noto Sans SC",sans-serif; font-size:24px;
  font-weight:800; letter-spacing:.3em; color:#1a1206; background:var(--pri); padding:8px 16px 8px 20px;
  border-radius:999px; box-shadow:0 0 24px var(--pri); }}
.card-name {{ font-size:80px; font-weight:800; line-height:1.02; color:#FBF6EC;
  letter-spacing:-1px; margin-bottom:8px; }}
.card-singer {{ font-family:"Noto Sans SC",sans-serif; font-size:40px; font-weight:700;
  color:var(--acc); letter-spacing:.06em; margin-bottom:22px; }}
.card-credit {{ font-family:"Noto Sans SC",sans-serif; font-size:28px; line-height:1.5;
  color:rgba(255,255,255,.74); font-weight:500; letter-spacing:.02em; margin-bottom:22px; }}
.card-tag {{ font-family:"Noto Sans SC",sans-serif; font-size:29px; font-weight:700; color:var(--acc);
  display:inline-flex; align-items:center; gap:13px; }}
.card-tag .dot {{ width:12px; height:12px; border-radius:50%; background:var(--pri); box-shadow:0 0 16px var(--pri); }}

/* 副歌大字 */
.kw {{ position:absolute; right:46px; bottom:330px; font-family:"Noto Serif SC",serif;
  font-size:480px; font-weight:900; line-height:.8; color:var(--pri); opacity:0;
  mix-blend-mode:soft-light; filter:drop-shadow(0 10px 60px rgba(0,0,0,.3)); }}
/* 副歌金句 */
.quote {{ position:absolute; left:70px; right:70px; bottom:248px; font-family:"Noto Serif SC",serif;
  font-size:54px; font-weight:600; line-height:1.42; text-align:center;
  color:#FBF6EC; opacity:0; letter-spacing:.01em; text-shadow:0 4px 30px rgba(0,0,0,.7); }}
/* 来源标 */
.src {{ position:absolute; bottom:60px; left:0; right:0; text-align:center;
  font-family:"Noto Sans SC",sans-serif; font-size:20px; font-weight:400;
  color:rgba(255,255,255,.34); letter-spacing:.22em; opacity:0; }}

/* ============ 封面 ============ */
.cover {{ position:absolute; inset:0; z-index:50; background:#06070C; overflow:hidden; }}
.cv-bg {{ position:absolute; inset:-8%; background:url("cover_assets/ding_bg.jpg") center 26%/cover no-repeat;
  filter:blur(40px) saturate(.78) brightness(.46); transform:scale(1.25); opacity:.62; }}
.cv-veil {{ position:absolute; inset:0;
  background:radial-gradient(ellipse at 50% 30%, rgba(224,180,120,.12) 0%, transparent 46%),
  linear-gradient(180deg, rgba(6,7,12,.52) 0%, rgba(6,7,12,.28) 28%, rgba(6,7,12,.82) 72%, rgba(6,7,12,.98) 100%); }}
.cv-vinyl {{ position:absolute; right:-150px; top:-150px; width:520px; height:520px; border-radius:50%;
  background:repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,.05) 0 2px, transparent 2px 7px);
  border:2px solid rgba(224,180,120,.18); opacity:.45; }}
.cv-staff {{ position:absolute; left:0; right:0; top:0; height:100%; opacity:.09;
  background:repeating-linear-gradient(180deg, transparent 0 26px, rgba(255,255,255,.5) 26px 27px); transform:rotate(-7deg) scale(1.4); }}
.cv-grain {{ position:absolute; inset:0; opacity:.5;
  background-image:radial-gradient(circle at 12% 30%, rgba(255,255,255,.04) 0 .5px, transparent .8px),
  radial-gradient(circle at 78% 66%, rgba(255,255,255,.04) 0 .5px, transparent .8px); background-size:190px 190px, 230px 230px; }}
.cv-head {{ position:absolute; top:66px; left:70px; right:70px; display:flex; justify-content:space-between; align-items:center; }}
.cv-eyebrow {{ font-family:"Noto Sans SC",sans-serif; font-size:27px; font-weight:700; letter-spacing:.4em; color:#E0B478; }}
.cv-byline {{ font-family:"Noto Sans SC",sans-serif; font-size:24px; font-weight:600; letter-spacing:.16em; color:rgba(255,255,255,.6); }}
.cv-portrait {{ position:absolute; top:168px; left:0; right:0; display:flex; justify-content:center; }}
.cv-pimg {{ width:300px; height:300px; border-radius:50%; background:url("cover_assets/ding.jpg") center 42%/cover no-repeat;
  box-shadow:0 28px 64px rgba(0,0,0,.62); border:2px solid rgba(255,255,255,.14); }}
.cv-pring {{ position:absolute; top:-12px; left:50%; transform:translateX(-50%); width:324px; height:324px;
  border:1.5px solid rgba(224,180,120,.55); border-radius:50%; }}
.cv-titlewrap {{ position:absolute; top:520px; left:70px; right:70px; text-align:center; }}
.cv-kicker {{ font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:700; letter-spacing:.34em; color:#E0B478; margin-bottom:18px; }}
.cv-title {{ font-family:"Noto Serif SC",serif; font-size:118px; font-weight:900; line-height:1.04;
  color:#FBF6EC; letter-spacing:-2px; text-shadow:0 6px 40px rgba(0,0,0,.6); }}
.cv-top5 {{ font-family:"JetBrains Mono",monospace; font-size:104px; font-weight:800; color:#E0B478; margin-left:18px; letter-spacing:0; }}
.cv-sub {{ font-family:"Noto Serif SC",serif; font-size:40px; font-weight:500; color:rgba(244,239,230,.82); margin-top:22px; letter-spacing:.02em; }}
.cv-list {{ position:absolute; bottom:150px; left:80px; right:80px; display:flex; flex-wrap:wrap; gap:16px 18px; justify-content:center; }}
.cv-chip {{ display:flex; align-items:baseline; gap:12px; padding:14px 24px; border-radius:999px;
  background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.14); }}
.cv-cn {{ font-family:"Noto Serif SC",serif; font-size:34px; font-weight:700; color:#FBF6EC; }}
.cv-cs {{ font-family:"Noto Sans SC",sans-serif; font-size:26px; font-weight:500; color:rgba(244,239,230,.6); }}

/* ============ Hook ============ */
.hook {{ position:absolute; inset:0; z-index:49; background:linear-gradient(180deg,#0A0C16 0%,#06070C 100%); }}
.hk-grad {{ position:absolute; inset:0;
  background:radial-gradient(ellipse at 28% 18%, rgba(224,180,120,.10) 0, transparent 50%),
  radial-gradient(ellipse at 74% 82%, rgba(140,60,80,.10) 0, transparent 50%); }}
.hk-kick {{ position:absolute; top:430px; left:90px; right:90px; font-family:"Noto Sans SC",sans-serif;
  font-size:30px; font-weight:700; letter-spacing:.4em; color:#E0B478; opacity:0; }}
.hk-title {{ position:absolute; top:498px; left:90px; right:90px; font-family:"Noto Serif SC",serif;
  font-size:96px; font-weight:900; line-height:1.1; color:#FBF6EC; opacity:0; letter-spacing:-1px; }}
.hk-t5 {{ font-family:"JetBrains Mono",monospace; font-weight:800; color:#E0B478; }}
.hk-sub {{ position:absolute; top:792px; left:90px; right:90px; font-family:"Noto Sans SC",sans-serif;
  font-size:42px; font-weight:600; line-height:1.46; color:rgba(244,239,230,.82); opacity:0; letter-spacing:.02em; }}
.hk-hint {{ position:absolute; top:1010px; left:90px; right:90px; font-family:"Noto Sans SC",sans-serif;
  font-size:32px; font-weight:600; letter-spacing:.2em; color:#E0B478; opacity:0; }}

/* ============ Outro ============ */
.outroblk {{ position:absolute; inset:0; z-index:48; background:radial-gradient(ellipse at 50% 36%, #16131F 0%, #06070C 72%); }}
.ot-bg {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 42%, rgba(224,180,120,.10) 0, transparent 46%); }}
.ot-eyebrow {{ position:absolute; top:212px; left:0; right:0; text-align:center; font-family:"Noto Sans SC",sans-serif;
  font-size:30px; font-weight:700; letter-spacing:.5em; color:#E0B478; opacity:0; }}
.ot-rail {{ position:absolute; top:300px; left:110px; right:110px; }}
.ot-line {{ display:flex; align-items:baseline; gap:26px; padding:13px 0; opacity:0; border-bottom:1px solid rgba(255,255,255,.08); }}
.ot-no {{ font-family:"JetBrains Mono",monospace; font-size:30px; font-weight:800; color:#E0B478; min-width:54px; }}
.ot-nm {{ font-family:"Noto Serif SC",serif; font-size:50px; font-weight:700; color:#FBF6EC; flex:1; }}
.ot-sg {{ font-family:"Noto Sans SC",sans-serif; font-size:29px; font-weight:500; color:rgba(244,239,230,.55); }}
.ot-line:first-child .ot-no {{ color:#FBF6EC; }}
.ot-line:first-child {{ background:linear-gradient(90deg, rgba(224,180,120,.16), transparent); }}
.ot-h {{ position:absolute; top:1040px; left:110px; right:110px; font-family:"Noto Serif SC",serif;
  font-size:72px; font-weight:800; line-height:1.2; color:#FBF6EC; letter-spacing:-1px; opacity:0; }}
'''

# ----- JS timeline -----
def js_chapter(k):
    s = SM[k]; a = abs_a[k]
    base = a["start"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]; end = a["end"]
    fade = end - 1.0
    qt0 = full0 + (full1 - full0) * 0.40
    qt1 = full1 - 0.4
    rk_pop = ', scale:1.18' if s.get("crown") else ''
    return f'''
// ---- {s["name"]} (NO.{s["no"]}) ----
tl.fromTo("#fv_{k}", {{opacity:0, scale:1.07}}, {{opacity:1, scale:1.0, duration:1.5, ease:"power2.out"}}, {f(base)});
tl.to("#tint_{k}", {{opacity:1, duration:1.3, ease:"power1.out"}}, {f(base)});
tl.fromTo(".ch_{k} .rail", {{opacity:0}}, {{opacity:1, duration:.8}}, {f(base+0.3)});
tl.fromTo(".ch_{k} .card", {{opacity:0, x:54, y:-16}}, {{opacity:1, x:0, y:0, duration:.9, ease:"power3.out"}}, {f(base+0.5)});
tl.fromTo(".ch_{k} .card-no", {{opacity:0, scale:.6{rk_pop}}}, {{opacity:1, scale:1.0, duration:.7, ease:"back.out(2.2)"}}, {f(base+0.72)});
tl.fromTo(".ch_{k} .src", {{opacity:0}}, {{opacity:1, duration:.6}}, {f(base+1.3)});
tl.to(".ch_{k} .card", {{opacity:0, y:-12, duration:.6, ease:"power2.in"}}, {f(sw0-0.1)});
tl.fromTo(".ch_{k} #kw_{k}", {{opacity:0, scale:.94, x:30}}, {{opacity:.5, scale:1.0, x:0, duration:1.8, ease:"power3.out"}}, {f(full0-0.5)});
tl.to(".ch_{k} #kw_{k}", {{opacity:.6, duration:1.2, ease:"sine.inOut"}}, {f(full0+1.5)});
tl.fromTo(".ch_{k} #qt_{k}", {{opacity:0, y:26}}, {{opacity:1, y:0, duration:.85, ease:"power2.out"}}, {f(qt0)});
tl.to(".ch_{k} #qt_{k}", {{opacity:0, y:-12, duration:.6, ease:"power2.in"}}, {f(qt1)});
tl.to("#fv_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {f(fade)});
tl.set("#fv_{k}", {{opacity:0}}, {f(end)});
tl.to("#tint_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {f(fade)});
tl.set("#tint_{k}", {{opacity:0}}, {f(end)});
tl.to(".ch_{k} #kw_{k}", {{opacity:0, duration:.9, ease:"power1.in"}}, {f(fade)});
tl.set(".ch_{k} #kw_{k}", {{opacity:0}}, {f(end)});
tl.to(".ch_{k} .src", {{opacity:0, duration:.6}}, {f(fade)});
tl.set(".ch_{k} .src", {{opacity:0}}, {f(end)});
tl.to(".ch_{k} .rail", {{opacity:0, duration:.5}}, {f(end-0.4)});
tl.set(".ch_{k} .rail", {{opacity:0}}, {f(end)});
'''

outro_reveal = "".join(
    f'tl.fromTo(".ot-rail .ot-line:nth-child({i+1})", {{opacity:0, x:-18}}, {{opacity:{0.96 if i==0 else 0.9}, x:0, duration:.5, ease:"power2.out"}}, {f(OUTRO_T+1.0+i*0.45)});\n'
    for i in range(5))

JS = f'''
// 封面（首帧即封面：opacity 起就 1，仅做呼吸，不淡入）
tl.set("#cover", {{opacity:1}}, 0);
tl.set(".cv-portrait, .cv-titlewrap, .cv-list, .cv-head", {{opacity:1}}, 0);
tl.fromTo(".cv-pimg", {{scale:1.0}}, {{scale:1.03, duration:2.6, yoyo:true, repeat:1, ease:"sine.inOut"}}, 0.4);
tl.to(".cv-vinyl", {{rotation:24, duration:{f(COVER_D)}, ease:"none", transformOrigin:"50% 50%"}}, 0);
tl.to("#cover", {{opacity:0, duration:.6, ease:"power2.in"}}, {f(COVER_D-0.6)});
tl.set("#cover", {{opacity:0}}, {f(COVER_D)});

// Hook
tl.set("#hook", {{opacity:1}}, {f(COVER_D)});
tl.fromTo(".hk-kick", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:.5, ease:"power2.out"}}, {f(COVER_D+0.2)});
tl.fromTo(".hk-title", {{opacity:0, y:24}}, {{opacity:1, y:0, duration:.7, ease:"power2.out"}}, {f(COVER_D+0.45)});
tl.fromTo(".hk-sub", {{opacity:0, y:16}}, {{opacity:1, y:0, duration:.6, ease:"power2.out"}}, {f(COVER_D+1.1)});
tl.fromTo(".hk-hint", {{opacity:0}}, {{opacity:1, duration:.6}}, {f(COVER_D+2.0)});
tl.to(".hk-hint", {{opacity:.55, duration:.8, yoyo:true, repeat:3, ease:"sine.inOut"}}, {f(COVER_D+2.8)});
tl.to("#hook", {{opacity:0, duration:.7, ease:"power2.in"}}, {f(INTRO_T+INTRO_D-0.7)});
tl.set("#hook", {{opacity:0}}, {f(INTRO_T+INTRO_D)});

{"".join(js_chapter(k) for k in COUNTDOWN)}

// Outro
tl.fromTo("#outro", {{opacity:0}}, {{opacity:1, duration:.8, ease:"power2.out"}}, {f(OUTRO_T)});
tl.fromTo(".ot-eyebrow", {{opacity:0, y:10}}, {{opacity:1, y:0, duration:.6}}, {f(OUTRO_T+0.5)});
{outro_reveal}
tl.fromTo(".ot-h", {{opacity:0, y:34}}, {{opacity:1, y:0, duration:1.0, ease:"power3.out"}}, {f(OUTRO_T+3.6)});
tl.to("#outro", {{opacity:1, duration:.1}}, {f(TOTAL-0.2)});
'''

html = f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
  {chr(10).join(foot_html)}
  {chr(10).join(tint_html)}
  <div id="vign"></div>
  {chr(10).join(chrome_html)}
  {cover_html}
  {hook_html}
  {outro_html}
  {audio_html}
</div>
<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused:true }});
  {JS}
  window.__timelines["main"] = tl;
</script>
</body></html>'''

(HF / "index.html").write_text(html, encoding="utf-8")
(HF / "meta.json").write_text('{"id":"main","name":"dingshiguang-others-top5"}', encoding="utf-8")
(HF / "package.json").write_text(json.dumps({
    "name": "hf", "private": True, "type": "module",
    "scripts": {
        "dev": "npx --yes hyperframes@0.6.47 preview",
        "check": "npx --yes hyperframes@0.6.47 lint",
        "render": "npx --yes hyperframes@0.6.47 render"
    }}, indent=2), encoding="utf-8")
print("index.html:", len(html), "bytes")
print("ALL BUILD DONE")
