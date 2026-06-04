#!/usr/bin/env python3
"""吴青峰为别人写的歌 TOP5 — 完整片构建（竖屏 1080×1920，叙事序 1→5）。
产物：clips_seg/<key>.mp4(竖屏副歌段) + master.wav(逐段 床→swell→完整副歌 + 旁白ducking + 逐首loudnorm) + hf/index.html。
渲染后必须 ffmpeg mux master.wav（HyperFrames 会压平音频动态）。
规则：每首展示完整副歌；副歌期无旁白；收束用屏幕金句字幕；无 meta 文案；成片无水印/烧词。
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
LEAD = 0.15        # 段首预滚（接续不死静）
PRE_VOICE = 0.8    # voice 起前音乐床抬起
POST_VOICE = 1.2   # voice 收尾消化位
SWELL = 1.6        # 床→满 升起
TAIL = 1.2         # 段末淡出
BED = 0.17         # voice 期音乐床增益（ducking 后的原曲）
ENTER_OVERLAP = 0.6

COVER_D = 3.6      # 封面（首帧可作封面）
INTRO_VOICE_AT = 2.6
INTRO_TAIL = 2.2

# ---------------- 每首歌定义 ----------------
# chorus_start = 源中完整副歌起点(s)；HIGH = 副歌展示时长(s)
SONGS = [
    dict(key="s1", no="01", name="有形的翅膀", singer="张韶涵", year="2007",
         credit="作词 · 作曲　吴青峰", tag="传唱度最高 · 温暖励志",
         kw="飞", quote="不是一个人撑住，<br>是有人，陪你一起飞。",
         src="s1_youxing_yt", chorus=53.5, high=16.0, crop="864:820:528:0", br=-0.30, sat=1.05,
         pri="#F0C079", acc="#FBEAC4", muted="#9A7B45",
         tint="linear-gradient(180deg, rgba(240,192,121,.16) 0%, rgba(40,26,10,.50) 44%, rgba(0,0,0,.84) 100%)",
         src_label="官方 MV · YouTube"),
    dict(key="s2", no="02", name="带我走", singer="杨丞琳", year="2007",
         credit="作词 · 作曲　吴青峰", tag="偶像剧记忆 · 青春离别",
         kw="走", quote="悲伤，但不狗血——<br>越听，越有被留下的后劲。",
         src="s2_daiwozou_bi", chorus=85.0, high=20.0, crop="864:820:528:0", br=-0.30, sat=1.02,
         pri="#8FB8DC", acc="#D6E6F2", muted="#4E6076",
         tint="linear-gradient(180deg, rgba(120,160,205,.16) 0%, rgba(10,18,30,.55) 45%, rgba(0,0,0,.86) 100%)",
         src_label="4K 修复 MV · 哔哩哔哩"),
    dict(key="s3", no="03", name="掉了", singer="张惠妹", year="2009",
         credit="作词 · 作曲　吴青峰", tag="失去感 · 情绪重量",
         kw="掉", quote="青峰写得碎，<br>阿妹，唱得重。",
         src="s3_diaole_bi", chorus=151.0, high=26.0, crop="864:1080:528:0", br=-0.36, sat=1.02,
         pri="#C76470", acc="#E7B6BC", muted="#6E3138",
         tint="linear-gradient(180deg, rgba(150,55,65,.22) 0%, rgba(24,8,10,.60) 45%, rgba(0,0,0,.90) 100%)",
         src_label="华纳官方修复 4K · 哔哩哔哩"),
    dict(key="s4", no="04", name="年轮说", singer="杨丞琳", year="2015",
         credit="作词　吴青峰　·　作曲　郑宇界", tag="高级作词 · 时间剖面",
         kw="轮", quote="把爱情，<br>写成时间的剖面。",
         src="s4_nianlun_yt", chorus=187.0, high=26.0, crop="864:820:528:0", br=-0.26, sat=1.04,
         pri="#BCD2E0", acc="#E8F1F7", muted="#5E7282",
         tint="linear-gradient(180deg, rgba(180,205,225,.14) 0%, rgba(18,28,38,.52) 46%, rgba(0,0,0,.84) 100%)",
         src_label="官方 HD MV · YouTube"),
    dict(key="s5", no="05", name="怪美的", singer="蔡依林", year="2018",
         credit="作词　吴青峰　·　作曲　Rhys Fletcher 等", tag="态度表达 · 自我重建",
         kw="美", quote="不再只是清冷诗意，<br>而是反击，与重建。",
         src="s5_guaimei_yt", chorus=62.0, high=22.0, crop="864:1080:528:0", br=-0.30, sat=1.10,
         pri="#F0586E", acc="#FFC2CF", muted="#8A2738",
         tint="linear-gradient(180deg, rgba(225,40,70,.20) 0%, rgba(26,4,8,.58) 44%, rgba(0,0,0,.90) 100%)",
         src_label="官方 MV · YouTube"),
]
SM = {s["key"]: s for s in SONGS}

# ---------------- 段时长与锚点 ----------------
def full0_of(key):
    return LEAD + PRE_VOICE + NARR[key] + POST_VOICE + SWELL

def seg_len_of(key):
    return full0_of(key) + SM[key]["high"] + TAIL

intro_seg = max(COVER_D, INTRO_VOICE_AT) + NARR["intro"] + INTRO_TAIL
outro_seg = LEAD + NARR["outro"] + 3.2

starts = {}
t = 0.0
starts["intro"] = (round(t, 3), round(intro_seg, 3)); t += intro_seg
for s in SONGS:
    L = seg_len_of(s["key"]); starts[s["key"]] = (round(t, 3), round(L, 3)); t += L
starts["outro"] = (round(t, 3), round(outro_seg, 3)); t += outro_seg
TOTAL = round(t, 3)
print(f"TOTAL: {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")
for k, (st, ln) in starts.items():
    print(f"  {k:6s} start={st:7.2f} len={ln:6.2f}")

def anchors(key):
    v0 = LEAD + PRE_VOICE
    v1 = v0 + NARR[key]
    sw0 = v1 + POST_VOICE
    full0 = sw0 + SWELL
    full1 = full0 + SM[key]["high"]
    return dict(v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1)

# mseek：源中起点，使副歌(chorus)恰好落在 full0
def mseek_of(key):
    return round(SM[key]["chorus"] - full0_of(key), 3)

# =========================================================
# 1) footage：每首切 [mseek, mseek+seg_len] → 竖屏(裁烧词/水印) → clips_seg
# =========================================================
def vert_filter(crop, br, sat):
    return (f"[0:v]crop={crop},split=2[bg][fg];"
            f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"gblur=sigma=30,eq=brightness={br}:saturation={sat}[bgb];"
            f"[fg]scale=1080:-2[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")

def build_footage(s):
    key = s["key"]; ms = mseek_of(key); L = starts[key][1]
    src = RAWH / f"{s['src']}.mp4"
    out = CSEG / f"{key}.mp4"
    run(["ffmpeg", "-v", "error", "-ss", ms, "-i", src, "-t", L,
         "-filter_complex", vert_filter(s["crop"], s["br"], s["sat"]),
         "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-r", "30", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p", out, "-y"])
    print(f"  footage {key}.mp4  mseek={ms}  len={L}")

print("== footage ==")
for s in SONGS:
    build_footage(s)

# =========================================================
# 2) 音频 master：逐段建 wav 再 concat
# =========================================================
def build_song_audio(s):
    key = s["key"]; a = anchors(key); L = starts[key][1]
    ms = mseek_of(key)
    voice_at = a["v0"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]
    # 音乐床/swell 包络（volume eval=frame）：
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
    print(f"  seg_{key}.wav  ({L}s)")

# intro / outro 用 s4《年轮说》前段器乐(0-79s 无人声)作低 ambient 床
def build_pad_seg(name, voice_key, seg_len, voice_at, bed_src_seek, bed_vol, fade_in, fade_out):
    run(["ffmpeg", "-v", "error", "-i", RAWW / f"{SM[voice_key]['src']}.wav" if voice_key in SM else RAWW / "s4_nianlun_yt.wav",
         "-i", A / f"{name}.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim={bed_src_seek}:{bed_src_seek+seg_len},asetpts=PTS-STARTPTS,"
         f"loudnorm=I=-15:TP=-1.0:LRA=11,volume={bed_vol},afade=t=in:st=0:d={fade_in},afade=t=out:st={seg_len-fade_out}:d={fade_out}[bed];"
         f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.96[out]",
         "-map", "[out]", "-ac", "2", "-ar", "48000", SEGS / f"seg_{name}.wav", "-y"])
    print(f"  seg_{name}.wav ({seg_len}s)")

print("== audio segs ==")
# intro：年轮说 5-? 器乐床；voice 在 INTRO_VOICE_AT
build_pad_seg("intro", None, round(intro_seg, 3), INTRO_VOICE_AT, 6.0, 0.22, 0.6, 1.6)
for s in SONGS:
    build_song_audio(s)
# outro：年轮说 另一段器乐床
build_pad_seg("outro", None, round(outro_seg, 3), LEAD + 0.3, 40.0, 0.22, 1.0, 2.4)

# concat
order = ["intro"] + [s["key"] for s in SONGS] + ["outro"]
(SEGS / "seglist.txt").write_text("".join(f"file 'seg_{k}.wav'\n" for k in order), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", SEGS / "seglist.txt",
     "-ac", "2", "-ar", "48000", ROOT / "master.wav", "-y"])
print("master dur:", dur(ROOT / "master.wav"), "planned:", TOTAL)

# 复制资源到 hf/
shutil.copy(ROOT / "master.wav", HF / "master.wav")
for s in SONGS:
    shutil.copy(CSEG / f"{s['key']}.mp4", HF / "clips_seg" / f"{s['key']}.mp4")

# 封面肖像（吴青峰本人）裁圆形头像源 + 模糊底图源
run(["ffmpeg", "-v", "error", "-i", RAWW / "wqf_face1.png",
     "-vf", "crop=620:740:250:24,scale=560:668", HF / "cover_assets" / "wqf.jpg", "-y"])
run(["ffmpeg", "-v", "error", "-i", RAWW / "wqf_face1.png",
     "-vf", "crop=1040:1080:440:0,scale=720:-1", HF / "cover_assets" / "wqf_bg.jpg", "-y"])
print("assets copied")

# =========================================================
# 3) HTML 合成
# =========================================================
def f(x): return f"{round(x,3)}"

abs_a = {}
for s in SONGS:
    k = s["key"]; base = starts[k][0]; a = anchors(k)
    abs_a[k] = {kk: round(base + vv, 3) for kk, vv in a.items()}
    abs_a[k]["start"] = base
    abs_a[k]["end"] = round(base + starts[k][1], 3)

INTRO_T, INTRO_D = starts["intro"]
OUTRO_T, OUTRO_D = starts["outro"]

# footage 元素（交替 track 0/6）
foot_tracks = [0, 6, 0, 6, 0]
foot_html = []
for i, s in enumerate(SONGS):
    k = s["key"]; a = abs_a[k]; sect = a["end"] - a["start"]
    foot_html.append(
        f'<video id="fv_{k}" class="fv clip" data-start="{f(a["start"])}" data-duration="{f(sect)}" '
        f'data-track-index="{foot_tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>')

# tint overlay 每首
tint_html = []
for i, s in enumerate(SONGS):
    k = s["key"]; a = abs_a[k]; sect = a["end"] - a["start"]
    tint_html.append(
        f'<div id="tint_{k}" class="clip tint tint_{k}" data-start="{f(a["start"])}" '
        f'data-duration="{f(sect)}" data-track-index="{10+i}"></div>')

# chrome（排名卡 + 左轨 + 大字 + 金句 + 来源标）
chrome_html = []
for i, s in enumerate(SONGS):
    k = s["key"]; a = abs_a[k]; sect = a["end"] - a["start"]
    rail = "".join(
        f'<div class="rd{(" act" if j==i else "")}{(" pst" if j<i else "")}" style="top:{8+j*20.5}%">'
        f'<span class="rt">{SONGS[j]["no"]}</span></div>' for j in range(5))
    chrome_html.append(f'''<div id="ch_{k}" class="clip chrome ch_{k}" data-start="{f(a["start"])}" data-duration="{f(sect)}" data-track-index="{20+i}">
  <div class="rail"><div class="rail-bar"></div>{rail}</div>
  <div class="card">
    <div class="card-top"><span class="card-no">{s["no"]}</span><span class="card-yr">{s["year"]}</span></div>
    <div class="card-name">{s["name"]}</div>
    <div class="card-singer">{s["singer"]}</div>
    <div class="card-credit">{s["credit"]}</div>
    <div class="card-tag"><span class="dot"></span>{s["tag"]}</div>
  </div>
  <div class="kw" id="kw_{k}">{s["kw"]}</div>
  <div class="quote" id="qt_{k}">{s["quote"]}</div>
  <div class="src" id="src_{k}">{s["src_label"]}</div>
</div>''')

# 封面（首帧可作封面）：吴青峰肖像 + 杂志大标题 + 5 首小字
cover_nodes = "".join(
    f'<div class="cv-node"><span class="cv-no">{s["no"]}</span>'
    f'<span class="cv-nm">《{s["name"]}》</span><span class="cv-sg">{s["singer"]}</span></div>'
    for s in SONGS)
cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{f(COVER_D)}" data-track-index="30">
  <div class="cv-bg"></div><div class="cv-veil"></div>
  <div class="cv-vinyl"></div><div class="cv-staff"></div><div class="cv-grain"></div>
  <div class="cv-head">
    <div class="cv-eyebrow">华语创作者盘点</div>
    <div class="cv-byline">作词 · 作曲　吴青峰</div>
  </div>
  <div class="cv-portrait"><div class="cv-pimg"></div><div class="cv-pring"></div></div>
  <div class="cv-titlewrap">
    <div class="cv-kicker">写给别人的歌</div>
    <h1 class="cv-title">吴青峰<br>写给别人<span class="cv-top5">TOP5</span></h1>
    <div class="cv-sub">原来，这些歌都是他写的</div>
  </div>
  <div class="cv-list">{cover_nodes}</div>
</div>'''

# hook：5 首歌名 + 歌手 扫过（COVER_D ~ INTRO_D）
hook_lines = "".join(
    f'<div class="hk-line" id="hk_{i+1}"><span class="hk-no">{s["no"]}</span>'
    f'<span class="hk-nm">{s["name"]}</span><span class="hk-sg">{s["singer"]}</span></div>'
    for i, s in enumerate(SONGS))
hook_html = f'''<div id="hook" class="clip hook" data-start="{f(COVER_D)}" data-duration="{f(INTRO_D-COVER_D)}" data-track-index="31">
  <div class="hk-grad"></div>
  <div class="hk-title">吴青峰<br>为别人写的歌 <span class="hk-t5">TOP5</span></div>
  <div class="hk-sub">不只是会唱，他写给别人也首首有戏</div>
  {hook_lines}
</div>'''

# outro：回顾 5 首 + 结尾字幕
outro_lines = "".join(
    f'<div class="ot-line"><span class="ot-no">{s["no"]}</span><span class="ot-nm">{s["name"]}</span>'
    f'<span class="ot-sg">{s["singer"]}</span></div>' for s in SONGS)
outro_html = f'''<div id="outro" class="clip outroblk" data-start="{f(OUTRO_T)}" data-duration="{f(OUTRO_D)}" data-track-index="32">
  <div class="ot-bg"></div>
  <div class="ot-rail">{outro_lines}</div>
  <h2 class="ot-h">他写给别人的歌，<br>也是一部隐藏的<br>吴青峰作品集。</h2>
</div>'''

audio_html = f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ----- 每首歌色卡的 CSS 变量 -----
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

/* 顶/底 杂志暗角，统一各首 */
#vign {{ position:absolute; inset:0; z-index:3; pointer-events:none;
  background:linear-gradient(180deg, rgba(0,0,0,.42) 0%, rgba(0,0,0,0) 16%, rgba(0,0,0,0) 78%, rgba(0,0,0,.55) 100%); }}

.chrome {{ position:absolute; inset:0; z-index:4; pointer-events:none; }}
{chrome_vars}

/* 左侧排名时间线轨 */
.rail {{ position:absolute; top:150px; left:60px; bottom:300px; width:10px; opacity:0; }}
.rail-bar {{ position:absolute; top:0; bottom:0; left:4px; width:2px;
  background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.22), rgba(255,255,255,.06)); }}
.rd {{ position:absolute; left:-21px; width:50px; height:50px; border-radius:50%;
  background:rgba(16,16,22,.9); border:2px solid rgba(255,255,255,.22);
  display:flex; align-items:center; justify-content:center; }}
.rd.pst {{ background:rgba(70,68,74,.7); border-color:rgba(255,255,255,.30); }}
.rd.act {{ background:var(--pri); border-color:var(--pri);
  box-shadow:0 0 30px var(--pri), 0 0 64px rgba(255,255,255,.18); transform:scale(1.22); }}
.rt {{ font-family:"JetBrains Mono",monospace; font-size:22px; font-weight:800; color:rgba(255,255,255,.78); }}
.rd.act .rt {{ color:rgba(14,14,18,.95); }}

/* 排名卡（右上玻璃卡） */
.card {{ position:absolute; top:140px; right:54px; width:660px; padding:44px 46px 40px;
  border-radius:24px; background:linear-gradient(160deg, rgba(255,255,255,.11), rgba(255,255,255,.03));
  backdrop-filter:blur(30px); -webkit-backdrop-filter:blur(30px);
  border:1.5px solid rgba(255,255,255,.18); box-shadow:0 34px 90px rgba(0,0,0,.6); opacity:0; }}
.card-top {{ display:flex; align-items:baseline; gap:20px; margin-bottom:14px; }}
.card-no {{ font-family:"JetBrains Mono",monospace; font-size:88px; font-weight:800; line-height:.9;
  color:var(--pri); letter-spacing:-2px; text-shadow:0 0 30px rgba(0,0,0,.4); }}
.card-yr {{ font-family:"JetBrains Mono",monospace; font-size:26px; font-weight:600;
  letter-spacing:.12em; color:rgba(255,255,255,.6); padding:6px 14px;
  border:1.5px solid rgba(255,255,255,.24); border-radius:999px; }}
.card-name {{ font-size:84px; font-weight:800; line-height:1.02; color:#FBF6EC;
  letter-spacing:-1px; margin-bottom:8px; }}
.card-singer {{ font-family:"Noto Sans SC",sans-serif; font-size:40px; font-weight:700;
  color:var(--acc); letter-spacing:.06em; margin-bottom:22px; }}
.card-credit {{ font-family:"Noto Sans SC",sans-serif; font-size:27px; line-height:1.5;
  color:rgba(255,255,255,.72); font-weight:500; letter-spacing:.02em; margin-bottom:24px; }}
.card-tag {{ font-family:"Noto Sans SC",sans-serif; font-size:29px; font-weight:700; color:var(--acc);
  display:inline-flex; align-items:center; gap:13px; }}
.card-tag .dot {{ width:12px; height:12px; border-radius:50%; background:var(--pri); box-shadow:0 0 16px var(--pri); }}

/* 副歌大字（单字水印感） */
.kw {{ position:absolute; right:40px; bottom:330px; font-family:"Noto Serif SC",serif;
  font-size:520px; font-weight:900; line-height:.8; color:var(--pri); opacity:0;
  mix-blend-mode:soft-light; filter:drop-shadow(0 10px 60px rgba(0,0,0,.3)); }}

/* 副歌金句（观点字幕） */
.quote {{ position:absolute; left:70px; right:70px; bottom:250px; font-family:"Noto Serif SC",serif;
  font-size:54px; font-weight:600; line-height:1.42; text-align:center;
  color:#FBF6EC; opacity:0; letter-spacing:.01em; text-shadow:0 4px 30px rgba(0,0,0,.7); }}

/* 来源标（小，低调） */
.src {{ position:absolute; bottom:62px; left:0; right:0; text-align:center;
  font-family:"Noto Sans SC",sans-serif; font-size:19px; font-weight:400;
  color:rgba(255,255,255,.34); letter-spacing:.24em; opacity:0; }}

/* ============ 封面 ============ */
.cover {{ position:absolute; inset:0; z-index:50; background:#06070C; overflow:hidden; }}
.cv-bg {{ position:absolute; inset:-8%; background:url("cover_assets/wqf_bg.jpg") center 18%/cover no-repeat;
  filter:blur(34px) saturate(.75) brightness(.5); transform:scale(1.18); opacity:.6; }}
.cv-veil {{ position:absolute; inset:0;
  background:radial-gradient(ellipse at 50% 32%, rgba(212,175,106,.12) 0%, transparent 46%),
  linear-gradient(180deg, rgba(6,7,12,.55) 0%, rgba(6,7,12,.30) 30%, rgba(6,7,12,.80) 72%, rgba(6,7,12,.97) 100%); }}
.cv-vinyl {{ position:absolute; right:-150px; top:-150px; width:520px; height:520px; border-radius:50%;
  background:repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,.05) 0 2px, transparent 2px 7px);
  border:2px solid rgba(212,175,106,.18); opacity:.5; }}
.cv-staff {{ position:absolute; left:0; right:0; top:0; height:100%; opacity:.10;
  background:repeating-linear-gradient(180deg, transparent 0 26px, rgba(255,255,255,.5) 26px 27px); transform:rotate(-7deg) scale(1.4); }}
.cv-grain {{ position:absolute; inset:0; opacity:.5;
  background-image:radial-gradient(circle at 12% 30%, rgba(255,255,255,.04) 0 .5px, transparent .8px),
  radial-gradient(circle at 78% 66%, rgba(255,255,255,.04) 0 .5px, transparent .8px); background-size:190px 190px, 230px 230px; }}

.cv-head {{ position:absolute; top:70px; left:70px; right:70px; display:flex;
  justify-content:space-between; align-items:center; }}
.cv-eyebrow {{ font-family:"Noto Sans SC",sans-serif; font-size:26px; font-weight:700;
  letter-spacing:.4em; color:#D4AF6A; }}
.cv-byline {{ font-family:"Noto Sans SC",sans-serif; font-size:23px; font-weight:600;
  letter-spacing:.14em; color:rgba(255,255,255,.62); }}

.cv-portrait {{ position:absolute; top:150px; left:0; right:0; display:flex; justify-content:center; }}
.cv-pimg {{ width:340px; height:404px; border-radius:14px; background:url("cover_assets/wqf.jpg") center top/cover no-repeat;
  box-shadow:0 30px 70px rgba(0,0,0,.6); border:1px solid rgba(255,255,255,.12); }}
.cv-pring {{ position:absolute; top:-14px; left:50%; transform:translateX(-50%); width:368px; height:432px;
  border:1.5px solid rgba(212,175,106,.55); border-radius:18px; }}

.cv-titlewrap {{ position:absolute; top:610px; left:70px; right:70px; text-align:center; }}
.cv-kicker {{ font-family:"Noto Sans SC",sans-serif; font-size:30px; font-weight:700;
  letter-spacing:.5em; color:#D4AF6A; margin-bottom:18px; }}
.cv-title {{ font-family:"Noto Serif SC",serif; font-size:140px; font-weight:900; line-height:1.0;
  color:#FBF6EC; letter-spacing:-2px; text-shadow:0 6px 40px rgba(0,0,0,.6); }}
.cv-top5 {{ font-family:"JetBrains Mono",monospace; font-size:124px; font-weight:800; color:#D4AF6A; margin-left:18px; letter-spacing:0; }}
.cv-sub {{ font-family:"Noto Serif SC",serif; font-size:44px; font-weight:500;
  color:rgba(244,239,230,.82); margin-top:24px; letter-spacing:.04em; }}

.cv-list {{ position:absolute; bottom:232px; left:90px; right:90px; }}
.cv-node {{ display:flex; align-items:baseline; gap:26px; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.1); }}
.cv-node:last-child {{ border-bottom:none; }}
.cv-no {{ font-family:"JetBrains Mono",monospace; font-size:28px; font-weight:800; color:#D4AF6A; min-width:46px; }}
.cv-nm {{ font-family:"Noto Serif SC",serif; font-size:42px; font-weight:600; color:#FBF6EC; flex:1; }}
.cv-sg {{ font-family:"Noto Sans SC",sans-serif; font-size:28px; font-weight:500; color:rgba(244,239,230,.6); letter-spacing:.04em; }}

/* ============ Hook ============ */
.hook {{ position:absolute; inset:0; z-index:49; background:linear-gradient(180deg,#0A0C16 0%,#06070C 100%); }}
.hk-grad {{ position:absolute; inset:0;
  background:radial-gradient(ellipse at 28% 18%, rgba(212,175,106,.10) 0, transparent 50%),
  radial-gradient(ellipse at 74% 82%, rgba(140,60,80,.10) 0, transparent 50%); }}
.hk-title {{ position:absolute; top:232px; left:90px; right:90px; font-family:"Noto Serif SC",serif;
  font-size:86px; font-weight:900; line-height:1.1; color:#FBF6EC; opacity:0; letter-spacing:-1px; }}
.hk-t5 {{ font-family:"JetBrains Mono",monospace; font-weight:800; color:#D4AF6A; }}
.hk-sub {{ position:absolute; top:516px; left:90px; right:90px; font-family:"Noto Sans SC",sans-serif;
  font-size:38px; font-weight:600; line-height:1.4; color:rgba(212,175,106,.92); opacity:0; letter-spacing:.03em; }}
.hk-line {{ position:absolute; left:90px; right:90px; display:flex; align-items:baseline; gap:28px; opacity:0; }}
#hk_1 {{ top:760px; }} #hk_2 {{ top:912px; }} #hk_3 {{ top:1064px; }} #hk_4 {{ top:1216px; }} #hk_5 {{ top:1368px; }}
.hk-no {{ font-family:"JetBrains Mono",monospace; font-size:34px; font-weight:800; color:#D4AF6A; min-width:62px; }}
.hk-nm {{ font-family:"Noto Serif SC",serif; font-size:62px; font-weight:700; color:#FBF6EC; }}
.hk-sg {{ font-family:"Noto Sans SC",sans-serif; font-size:34px; font-weight:500; color:rgba(244,239,230,.55); margin-left:auto; }}

/* ============ Outro ============ */
.outroblk {{ position:absolute; inset:0; z-index:48; background:radial-gradient(ellipse at 50% 38%, #16131F 0%, #06070C 72%); }}
.ot-bg {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 46%, rgba(212,175,106,.10) 0, transparent 46%); }}
.ot-rail {{ position:absolute; top:300px; left:110px; right:110px; }}
.ot-line {{ display:flex; align-items:baseline; gap:26px; padding:11px 0; opacity:0; border-bottom:1px solid rgba(255,255,255,.08); }}
.ot-no {{ font-family:"JetBrains Mono",monospace; font-size:26px; font-weight:800; color:#D4AF6A; min-width:48px; }}
.ot-nm {{ font-family:"Noto Serif SC",serif; font-size:48px; font-weight:700; color:#FBF6EC; flex:1; }}
.ot-sg {{ font-family:"Noto Sans SC",sans-serif; font-size:28px; font-weight:500; color:rgba(244,239,230,.55); }}
.ot-h {{ position:absolute; top:1020px; left:110px; right:110px; font-family:"Noto Serif SC",serif;
  font-size:74px; font-weight:800; line-height:1.18; color:#FBF6EC; letter-spacing:-1px; opacity:0; }}
'''

# ----- JS timeline -----
def js_chapter(s, i):
    k = s["key"]; a = abs_a[k]
    base = a["start"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]; end = a["end"]
    fade = end - 1.0
    qt0 = full0 + (full1 - full0) * 0.42   # 金句在副歌中段出
    qt1 = full1 - 0.4
    return f'''
// ---- {s["name"]} ----
tl.fromTo("#fv_{k}", {{opacity:0, scale:1.07}}, {{opacity:1, scale:1.0, duration:1.5, ease:"power2.out"}}, {f(base)});
tl.to("#tint_{k}", {{opacity:1, duration:1.3, ease:"power1.out"}}, {f(base)});
tl.fromTo(".ch_{k} .rail", {{opacity:0}}, {{opacity:1, duration:.8}}, {f(base+0.3)});
tl.fromTo(".ch_{k} .card", {{opacity:0, x:54, y:-16}}, {{opacity:1, x:0, y:0, duration:.9, ease:"power3.out"}}, {f(base+0.55)});
tl.fromTo(".ch_{k} .src", {{opacity:0}}, {{opacity:1, duration:.6}}, {f(base+1.3)});
// 副歌前：卡片淡出，让位给画面与大字
tl.to(".ch_{k} .card", {{opacity:0, y:-12, duration:.6, ease:"power2.in"}}, {f(sw0-0.1)});
tl.fromTo(".ch_{k} #kw_{k}", {{opacity:0, scale:.94, x:30}}, {{opacity:.5, scale:1.0, x:0, duration:1.8, ease:"power3.out"}}, {f(full0-0.5)});
tl.to(".ch_{k} #kw_{k}", {{opacity:.62, duration:1.2, ease:"sine.inOut"}}, {f(full0+1.5)});
// 副歌中段：金句观点字幕
tl.fromTo(".ch_{k} #qt_{k}", {{opacity:0, y:26}}, {{opacity:1, y:0, duration:.85, ease:"power2.out"}}, {f(qt0)});
tl.to(".ch_{k} #qt_{k}", {{opacity:0, y:-12, duration:.6, ease:"power2.in"}}, {f(qt1)});
// 收尾淡出（带 hard kill）
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

hook_reveal = "".join(
    f'tl.fromTo("#hk_{i+1}", {{opacity:0, x:-28}}, {{opacity:1, x:0, duration:.5, ease:"power2.out"}}, {f(COVER_D+1.4+i*0.62)});\n'
    f'tl.to("#hk_{i+1}", {{opacity:.42, duration:.5}}, {f(COVER_D+1.4+i*0.62+2.4)});\n'
    for i in range(5))

outro_reveal = "".join(
    f'tl.fromTo(".ot-rail .ot-line:nth-child({i+1})", {{opacity:0, x:-18}}, {{opacity:.92, x:0, duration:.45, ease:"power2.out"}}, {f(OUTRO_T+0.5+i*0.22)});\n'
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
tl.fromTo(".hk-title", {{opacity:0, y:24}}, {{opacity:1, y:0, duration:.7, ease:"power2.out"}}, {f(COVER_D+0.3)});
tl.fromTo(".hk-sub", {{opacity:0, y:16}}, {{opacity:1, y:0, duration:.6, ease:"power2.out"}}, {f(COVER_D+0.9)});
{hook_reveal}
tl.to("#hook", {{opacity:0, duration:.7, ease:"power2.in"}}, {f(INTRO_T+INTRO_D-0.7)});
tl.set("#hook", {{opacity:0}}, {f(INTRO_T+INTRO_D)});

{"".join(js_chapter(s,i) for i,s in enumerate(SONGS))}

// Outro
tl.fromTo("#outro", {{opacity:0}}, {{opacity:1, duration:.8, ease:"power2.out"}}, {f(OUTRO_T)});
{outro_reveal}
tl.fromTo(".ot-h", {{opacity:0, y:34}}, {{opacity:1, y:0, duration:1.0, ease:"power3.out"}}, {f(OUTRO_T+2.4)});
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
(HF / "meta.json").write_text('{"id":"main","name":"wuqingfeng-others-top5"}', encoding="utf-8")
print("index.html:", len(html), "bytes")
print("ALL BUILD DONE")
