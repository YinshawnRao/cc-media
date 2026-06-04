#!/usr/bin/env python3
"""完整片构建：李荣浩写进杨丞琳歌里的时间线（5首叙事序）。
产物：master.wav（逐段：footage 音乐床 + voice + swell + 高光 + 中段文案 + 转场）+ index.html。
预设：audio/<key>.wav 来自 build/narrate_segments.py；clips/vert_*.mp4 来自 vfill。
渲染后必须 ffmpeg mux master.wav（HyperFrames 会压平音频动态）。
"""
import subprocess, wave, contextlib, json, math
from pathlib import Path

A = "audio"; C = "clips"

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

# ============ 旁白时长 ============
NARR = {k: dur(f"{A}/{k}.wav") for k in [
    "intro","s1_voice","s1_mid","s2_voice","s2_mid","s3_voice","s3_mid",
    "s4_voice","s4_mid","s5_voice","s5_mid","outro"]}
print("NARR:", json.dumps(NARR, indent=2))

# ============ 节奏常量 ============
LEAD       = 0.15  # 进入到 voice 起的预滚（保持下场段不死静）
PRE_VOICE  = 0.8   # voice 起前的音乐床起伏
POST_VOICE = 1.2   # voice 收尾消化位
SWELL      = 1.5   # swell 时长
BED        = 0.18  # voice 期音乐床增益
MID_OVER   = 5.0   # 中段文案在副歌余韵段时长
HIGH_BASE  = 42    # 副歌展示基础时长
HIGH_LAST  = 56    # 最后一首副歌延长（finale）
ENTER_OVERLAP = 0.6  # 章节起始与素材进入的画面动画前置

# 各歌段落时长（音频时间轴）
SECT = {}
def make_sect(key, voice_dur, mid_dur, high_dur):
    seg = LEAD + PRE_VOICE + voice_dur + POST_VOICE + SWELL + high_dur + mid_dur + 1.0
    return seg

intro_seg = LEAD + NARR["intro"] + 2.2  # intro 旁白 + 5节点闪现 + 引入
s1 = make_sect("s1", NARR["s1_voice"], NARR["s1_mid"], HIGH_BASE)
s2 = make_sect("s2", NARR["s2_voice"], NARR["s2_mid"], HIGH_BASE)
s3 = make_sect("s3", NARR["s3_voice"], NARR["s3_mid"], HIGH_BASE)
s4 = make_sect("s4", NARR["s4_voice"], NARR["s4_mid"], HIGH_BASE)
s5 = make_sect("s5", NARR["s5_voice"], NARR["s5_mid"], HIGH_LAST)
outro_seg = LEAD + NARR["outro"] + 4.0  # 旁白 + 总结画面停留

starts = {}
t = 0.0
starts["intro"] = (t, intro_seg); t += intro_seg
starts["s1"]    = (t, s1); t += s1
starts["s2"]    = (t, s2); t += s2
starts["s3"]    = (t, s3); t += s3
starts["s4"]    = (t, s4); t += s4
starts["s5"]    = (t, s5); t += s5
starts["outro"] = (t, outro_seg); t += outro_seg
TOTAL = round(t, 3)
print(f"TOTAL: {TOTAL}s = {TOTAL//60:.0f}:{TOTAL%60:05.2f}")

# ============ 每首歌的源切点（footage 取段） ============
# (clip_id, music_seek_start, allow_full_dur)
SOURCES = {
    "s1": ("vert_xfgz",     12.0),   # 幸福菓子 live 副歌位
    "s2": ("vert_guanzhong", 60.0),  # 观众 MV 副歌
    "s3": ("vert_manman",    20.0),  # 慢慢喜欢你 live 副歌位
    "s4": ("vert_xianchou",  55.0),  # 献丑 MV 副歌
    "s5": ("vert_xingxing", 130.0),  # 像是一颗星星 MV 副歌（写给20年作品）
}

# 章节内部本地时间锚点
def anchors(key):
    voice_dur = NARR[f"{key}_voice"]
    mid_dur   = NARR[f"{key}_mid"]
    high_dur  = HIGH_LAST if key == "s5" else HIGH_BASE
    v0 = LEAD + PRE_VOICE
    v1 = v0 + voice_dur
    sw0 = v1 + POST_VOICE
    full0 = sw0 + SWELL
    full1 = full0 + high_dur
    mid0  = full1 - mid_dur  # 中段文案在 high 后半段叠
    return dict(v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1, mid0=mid0)

# ============ 构建每段音频 wav ============
Path("build/segs").mkdir(parents=True, exist_ok=True)

# ---- intro: 用 s5《像是一颗星星》尾声器乐作低音 ambient bed，全段铺底；voice 上叠 ----
intro_voice_at = LEAD + 0.4  # voice 稍延后给 ambient swell up
run(["ffmpeg","-v","error","-i", f"{C}/vert_xingxing.mp4","-i", f"{A}/intro.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(intro_voice_at*1000)}|{int(intro_voice_at*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=235:{235+intro_seg},asetpts=PTS-STARTPTS,volume=0.18,afade=t=in:st=0:d=1.2,afade=t=out:st={intro_seg-1.5}:d=1.5[bed];"
     f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_intro.wav","-y"])

# ---- 每首歌 segment ----
def build_song_seg(key):
    a = anchors(key)
    seg_len = starts[key][1]
    clip, mseek = SOURCES[key]
    voice_at = a["v0"]
    sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]
    # 音乐床/swell 包络：
    #  0→LEAD: 0
    #  LEAD→v0: ramp 0→BED
    #  v0→sw0: BED
    #  sw0→full0: BED→1.0 ramp (swell)
    #  full0→full1: 1.0
    #  full1→end: 1.0→0.0 fadeout
    fade_out_start = full1
    fade_out_end = seg_len
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{voice_at}))*({BED}*(t-{LEAD})/{voice_at-LEAD})"
          f"+(between(t,{voice_at},{sw0}))*{BED}"
          f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
          f"+(between(t,{full0},{full1}))*1.0"
          f"+(gte(t,{full1}))*(1.0-((t-{full1})/{max(fade_out_end-fade_out_start,0.01)}))*step({fade_out_end},t)*-1+gte(t,{full1})*(1.0-((t-{full1})/{max(fade_out_end-fade_out_start,0.01)})))")
    # 简化 fadeout 用 afade 单独跑
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{voice_at}))*({BED}*(t-{LEAD})/{voice_at-LEAD})"
          f"+(between(t,{voice_at},{sw0}))*{BED}"
          f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
          f"+(gte(t,{full0}))*1.0")
    out = f"build/segs/seg_{key}.wav"
    run(["ffmpeg","-v","error","-i", f"{C}/{clip}.mp4", "-i", f"{A}/{key}_voice.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(voice_at*1000)}|{int(voice_at*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,"
         f"loudnorm=I=-14:TP=-1.0:LRA=11,atrim={mseek}:{mseek+seg_len},asetpts=PTS-STARTPTS,"
         f"volume='{ve}':eval=frame,afade=t=out:st={fade_out_start}:d={fade_out_end-fade_out_start}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    return out

for k in ["s1","s2","s3","s4","s5"]:
    print(f"building seg_{k}...")
    build_song_seg(k)

# ---- outro: 用 s5 像是一颗星星的器乐尾段作低床 ----
outro_voice_at = LEAD
clip_o, mseek_o = ("vert_xingxing", 240.0)  # 取星星尾声
run(["ffmpeg","-v","error","-i", f"{C}/{clip_o}.mp4", "-i", f"{A}/outro.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(outro_voice_at*1000)}|{int(outro_voice_at*1000)},volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={mseek_o}:{mseek_o+outro_seg},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=1.0,afade=t=out:st={outro_seg-2.5}:d=2.5[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_seg},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])

# ---- 拼接 master.wav ----
seglist = "build/segs/seglist.txt"
Path(seglist).write_text("".join(f"file '{Path(p).name}'\n" for p in [
    "build/segs/seg_intro.wav",
    "build/segs/seg_s1.wav",
    "build/segs/seg_s2.wav",
    "build/segs/seg_s3.wav",
    "build/segs/seg_s4.wav",
    "build/segs/seg_s5.wav",
    "build/segs/seg_outro.wav",
]), encoding="utf-8")
# concat 需要相对路径
Path("build/segs/seglist.txt").write_text(
    "file 'seg_intro.wav'\nfile 'seg_s1.wav'\nfile 'seg_s2.wav'\nfile 'seg_s3.wav'\nfile 'seg_s4.wav'\nfile 'seg_s5.wav'\nfile 'seg_outro.wav'\n",
    encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "planned:", TOTAL)

# 复制到 hf/ 项目内（HyperFrames 媒体必须与 index.html 同目录或子目录）
import shutil
shutil.copy("master.wav", "hf/master.wav")
Path("hf/clips").mkdir(exist_ok=True)
for k, (clip, _) in SOURCES.items():
    shutil.copy(f"{C}/{clip}.mp4", f"hf/clips/{clip}.mp4")

print("audio build done")

# ============================================================
# HTML composition
# ============================================================
SONGS_META = [
    dict(key="s1", no="01", name="幸福菓子", year="2007", credit="作曲：李荣浩 · 演唱：杨丞琳",
         theme="樱花粉 · 早春初遇", keyword="种子", mid_text="那时候，故事还没有开始。<br>歌已经先到了一步。",
         pri="#E8B7C8", bg="#1F1018", acc="#F7F0E8", muted_acc="#9B5A75",
         clip="vert_xfgz", source_label="官方 Karaoke Live · YouTube"),
    dict(key="s2", no="02", name="观众", year="2016", credit="词 / 曲：李荣浩 · 演唱：杨丞琳",
         theme="冷光自白 · 成年人的清醒", keyword="自白", mid_text="有些爱，不是输了。<br>只是终于看清了自己的座位。",
         pri="#DDE7F0", bg="#0B1118", acc="#88A1B8", muted_acc="#4D5B70",
         clip="vert_guanzhong", source_label="官方 HD MV · YouTube"),
    dict(key="s3", no="03", name="慢慢喜欢你", year="2018", credit="词 / 曲：李荣浩 · 原唱：莫文蔚 · 现场：杨丞琳",
         theme="暖夜柔光 · 慢慢的喜欢", keyword="长情", mid_text="慢，不是迟钝。<br>是终于愿意把时间交给一个人。",
         pri="#D8A85B", bg="#1A0F08", acc="#E8B7C8", muted_acc="#8C6A38",
         clip="vert_manman", source_label="LIKE A STAR 巡演现场 · 哔哩哔哩"),
    dict(key="s4", no="04", name="献丑", year="2019", credit="作词：陈信延 / 李荣浩 · 演唱：杨丞琳",
         theme="暗红倒影 · 亲密里的坦白", keyword="献丑", mid_text="真正亲近的人，<br>会看见你的光，也接住你的狼狈。",
         pri="#C97A86", bg="#1A0808", acc="#E0BFB2", muted_acc="#6D3D3D",
         clip="vert_xianchou", source_label="官方 HD MV · YouTube"),
    dict(key="s5", no="05", name="像是一颗星星", year="2020", credit="作词 / 制作：李荣浩 · 演唱：杨丞琳",
         theme="深夜星轨 · 她自己发光", keyword="星星", mid_text="最好的情歌，不是把她写成谁的爱人。<br>而是看见她本来就是星星。",
         pri="#DDE7F0", bg="#080F1C", acc="#D8A85B", muted_acc="#4A5878",
         clip="vert_xingxing", source_label="官方 HD MV · YouTube"),
]

# 计算每首段在主轴上的绝对锚点
sect_start = {}
for k in ["intro","s1","s2","s3","s4","s5","outro"]:
    sect_start[k] = starts[k][0]

abs_anchors = {}
for s in SONGS_META:
    k = s["key"]
    a = anchors(k)
    base = sect_start[k]
    abs_anchors[k] = {kk: round(base + vv, 3) for kk, vv in a.items()}
    abs_anchors[k]["start"] = round(base, 3)
    abs_anchors[k]["end"]   = round(base + starts[k][1], 3)

# 章节配色（intro/outro 用 s5 调）
INTRO_T = sect_start["intro"]
INTRO_D = starts["intro"][1]
OUTRO_T = sect_start["outro"]
OUTRO_D = starts["outro"][1]

# ============ HTML 生成 ============
def fmt(x): return f"{round(x,3)}"

# footage 元素：每首歌一段 video，从对应 SOURCES 的 mseek 起；交替 track 0/6
foot_html = []
foot_tracks = [0, 6, 0, 6, 0]
for idx, s in enumerate(SONGS_META):
    k = s["key"]; a = abs_anchors[k]
    seek = SOURCES[k][1]
    sect_dur = a["end"] - a["start"]
    # video 元素 data-start = 章节起始；data-duration = 章节时长；用 currentTime offset 不行，用 trim？
    # HyperFrames 视频从 t=0 播。我们要让视频从 mseek 开始，需要做 ffmpeg 预切。简化：直接给 footage 设个内部 css transform 来 mask 已经裁好的 vert mp4 是足够好的；视频从开头播即 trimmed segment 不需要。
    # 实际：vert_*.mp4 是完整长视频，我们要从 mseek 开始 displays 该段。HyperFrames 没法控 videoElement.currentTime 在渲染时（会被覆盖）。需要预切。
    foot_html.append(
        f'<video id="fv_{k}" class="fv clip" data-start="{fmt(a["start"])}" '
        f'data-duration="{fmt(sect_dur)}" data-track-index="{foot_tracks[idx]}" '
        f'src="clips_seg/{k}.mp4" muted playsinline></video>')

# 章节 tint overlay（每首段全段）
tint_html = []
for idx, s in enumerate(SONGS_META):
    k = s["key"]; a = abs_anchors[k]
    sect_dur = a["end"] - a["start"]
    tint_html.append(
        f'<div id="tint_{k}" class="clip tint tint_{k}" data-start="{fmt(a["start"])}" '
        f'data-duration="{fmt(sect_dur)}" data-track-index="{10+idx}"></div>')

# 章节滤镜 (per-song color theme 容器，全段覆盖)
chrome_html = []
for idx, s in enumerate(SONGS_META):
    k = s["key"]; a = abs_anchors[k]
    chrome_html.append(f'''<div id="chrome_{k}" class="clip chrome chrome_{k}" data-start="{fmt(a["start"])}" data-duration="{fmt(a["end"]-a["start"])}" data-track-index="{20+idx}">
  <div class="rail">
    <div class="rail-bar"></div>
    {''.join(f'<div class="rail-dot{(" active" if i==idx else "")}{(" past" if i<idx else "")}" style="top:{12+i*20}%"><span class="rail-tick">{SONGS_META[i]["no"]}</span></div>' for i in range(5))}
  </div>
  <div class="card">
    <div class="card-no">{s["no"]}</div>
    <div class="card-year">{s["year"]}</div>
    <div class="card-name">{s["name"]}</div>
    <div class="card-credit">{s["credit"]}</div>
    <div class="card-tag"><span class="dot"></span>{s["theme"]}</div>
  </div>
  <div class="kw" id="kw_{k}">{s["keyword"]}</div>
  <div class="mid" id="mid_{k}">{s["mid_text"]}</div>
  <div class="src" id="src_{k}">{s["source_label"]}</div>
  <div class="particles"></div>
</div>''')

# 封面（0~3.0s）：两人头像 + 大标题 + 5节点时间线（间距加大）
COVER_D = 3.0
cover_html = f'''<div id="cover" class="clip cover" data-start="0" data-duration="{COVER_D}" data-track-index="30">
  <div class="cv-bg-rh"></div>
  <div class="cv-bg-yc"></div>
  <div class="cv-veil"></div>
  <div class="cv-grain"></div>

  <div class="cv-portraits">
    <div class="cv-pf">
      <div class="cv-img cv-img-lirh"></div>
      <div class="cv-label"><span class="cv-role">作曲 / 作词</span><span class="cv-name">李荣浩</span></div>
    </div>
    <div class="cv-amp">×</div>
    <div class="cv-pf">
      <div class="cv-img cv-img-rainie"></div>
      <div class="cv-label"><span class="cv-role">演唱 / 时间</span><span class="cv-name">杨丞琳</span></div>
    </div>
  </div>

  <div class="cv-main">
    <div class="cv-eyebrow">5 首歌 · 一条很温柔的时间线</div>
    <h1 class="cv-title">写进她歌里的<br>时间线</h1>
    <div class="cv-sub">从一颗幸福菓子，<br>到她自己成为星星</div>
  </div>

  <div class="cv-rail">
    <div class="cv-yr">2007 ─── 2020</div>
    {''.join(f'<div class="cv-node"><span class="cv-n">{s["no"]}</span><span class="cv-nm">《{s["name"]}》</span><span class="cv-yy">{s["year"]}</span></div>' for s in SONGS_META)}
  </div>
</div>'''

# 开场片头钩子：5 个年份节点扫过（COVER_D ~ INTRO_D）
hook_d = INTRO_D - COVER_D
hook_html = f'''<div id="hook" class="clip hook" data-start="{fmt(COVER_D)}" data-duration="{fmt(hook_d)}" data-track-index="31">
  <div class="hk-grad"></div>
  {''.join(f'<div class="hk-line" id="hk_{i+1}"><span class="hk-y">{s["year"]}</span><span class="hk-n">{s["name"]}</span><span class="hk-tag">{["一颗幸福菓子","她成了自己的观众","慢慢喜欢你","敢把不完美摊开","她像是一颗星星"][i]}</span></div>' for i,s in enumerate(SONGS_META))}
</div>'''

# Outro 总结
outro_html = f'''<div id="outro" class="clip outroblk" data-start="{fmt(OUTRO_T)}" data-duration="{fmt(OUTRO_D)}" data-track-index="32">
  <div class="ot-bg"></div>
  <div class="ot-rail">
    {''.join(f'<div class="ot-line"><span class="ot-y">{s["year"]}</span><span class="ot-n">{s["name"]}</span></div>' for s in SONGS_META)}
  </div>
  <h2 class="ot-h">从幸福菓子，<br>到一颗星星</h2>
  <p class="ot-p">有些歌，后来真的会长成故事。</p>
  <p class="ot-q">你最喜欢哪一首？</p>
</div>'''

# 音频 master
audio_html = f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# CSS — 多 ~600 行的样式
CSS = '''
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #06080F; font-family: "Noto Serif SC","Songti SC","Source Han Serif SC",serif; color: #F7F0E8; -webkit-font-smoothing: antialiased; }
.fv { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 1; opacity: 0; }
.tint { position: absolute; inset: 0; z-index: 2; mix-blend-mode: multiply; opacity: 0; }
.tint_s1 { background: linear-gradient(180deg, rgba(255,200,220,.25) 0%, rgba(31,16,24,.40) 40%, rgba(0,0,0,.78) 100%); }
.tint_s2 { background: linear-gradient(180deg, rgba(150,180,210,.18) 0%, rgba(11,17,24,.55) 45%, rgba(0,0,0,.82) 100%); }
.tint_s3 { background: linear-gradient(180deg, rgba(216,168,91,.18) 0%, rgba(40,24,12,.55) 45%, rgba(0,0,0,.82) 100%); }
.tint_s4 { background: linear-gradient(180deg, rgba(120,40,55,.30) 0%, rgba(26,8,8,.60) 45%, rgba(0,0,0,.88) 100%); }
.tint_s5 { background: linear-gradient(180deg, rgba(160,180,220,.15) 0%, rgba(8,15,28,.55) 45%, rgba(0,0,0,.85) 100%); }

.chrome { position: absolute; inset: 0; z-index: 4; pointer-events: none; }
.chrome_s1 { --pri:#E8B7C8; --acc:#F7F0E8; --muted:#9B5A75; }
.chrome_s2 { --pri:#DDE7F0; --acc:#88A1B8; --muted:#4D5B70; }
.chrome_s3 { --pri:#D8A85B; --acc:#E8B7C8; --muted:#8C6A38; }
.chrome_s4 { --pri:#C97A86; --acc:#E0BFB2; --muted:#6D3D3D; }
.chrome_s5 { --pri:#DDE7F0; --acc:#D8A85B; --muted:#4A5878; }

/* 左侧时间线轨 — 节点放大、序号字体放大 */
.rail { position: absolute; top: 150px; left: 64px; bottom: 200px; width: 10px; opacity: 0; }
.rail-bar { position: absolute; top: 0; bottom: 0; left: 4px; width: 2px; background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.22), rgba(255,255,255,.05)); }
.rail-dot { position: absolute; left: -20px; width: 48px; height: 48px; border-radius: 50%; background: rgba(20,18,28,.88); border: 2px solid rgba(255,255,255,.22); transition: none; display: flex; align-items: center; justify-content: center; }
.rail-dot.past { background: rgba(70,70,82,.7); border-color: rgba(255,255,255,.30); }
.rail-dot.active { background: var(--pri); border-color: var(--pri); box-shadow: 0 0 32px var(--pri), 0 0 70px rgba(255,255,255,.22); transform: scale(1.20); }
.rail-tick { font-family: "Noto Sans SC", system-ui, sans-serif; font-size: 22px; font-weight: 800; color: rgba(255,255,255,.75); letter-spacing: 0; }
.rail-dot.active .rail-tick { color: rgba(20,18,28,.95); }

/* 玻璃歌名卡（右上） — 所有辅助字号放大 */
.card { position: absolute; top: 140px; right: 56px; width: 640px; padding: 46px 48px 44px; border-radius: 26px; background: linear-gradient(160deg, rgba(255,255,255,.10), rgba(255,255,255,.03)); backdrop-filter: blur(32px); -webkit-backdrop-filter: blur(32px); border: 1.5px solid rgba(255,255,255,.18); box-shadow: 0 36px 96px rgba(0,0,0,.6); opacity: 0; }
.card-no { font-family: "Noto Sans SC", sans-serif; font-size: 36px; letter-spacing: .38em; font-weight: 800; color: var(--pri); margin-bottom: 14px; }
.card-year { display: inline-block; font-family: "Noto Sans SC", sans-serif; font-size: 24px; font-weight: 700; letter-spacing: .25em; color: rgba(255,255,255,.65); padding: 8px 16px; border: 1.5px solid rgba(255,255,255,.25); border-radius: 999px; margin-bottom: 20px; }
.card-name { font-size: 78px; font-weight: 800; line-height: 1.04; color: #F7F0E8; letter-spacing: -1px; margin-bottom: 22px; font-family: "Noto Serif SC","Songti SC",serif; }
.card-credit { font-family: "Noto Sans SC", sans-serif; font-size: 28px; line-height: 1.55; color: rgba(255,255,255,.75); font-weight: 500; letter-spacing: .03em; margin-bottom: 28px; }
.card-tag { font-family: "Noto Sans SC", sans-serif; font-size: 30px; font-weight: 700; color: var(--acc); display: inline-flex; align-items: center; gap: 14px; }
.card-tag .dot { width: 12px; height: 12px; border-radius: 50%; background: var(--pri); box-shadow: 0 0 16px var(--pri); }

/* 大关键词（副歌段画面右侧/下方） */
.kw { position: absolute; left: 0; right: 0; bottom: 380px; text-align: center; font-family: "Noto Serif SC", serif; font-size: 280px; font-weight: 800; line-height: .9; color: var(--pri); opacity: 0; letter-spacing: -8px; mix-blend-mode: screen; filter: drop-shadow(0 8px 60px rgba(255,255,255,.16)); }

/* 中段两行金句 */
.mid { position: absolute; left: 80px; right: 80px; bottom: 240px; font-family: "Noto Serif SC", serif; font-size: 50px; font-weight: 500; line-height: 1.4; text-align: center; color: rgba(247,240,232,.95); opacity: 0; letter-spacing: .02em; }

/* 来源水印（小） */
.src { position: absolute; bottom: 60px; left: 0; right: 0; text-align: center; font-family: "Noto Sans SC", sans-serif; font-size: 18px; font-weight: 400; color: rgba(255,255,255,.32); letter-spacing: .25em; opacity: 0; }

/* 粒子层（per-song themed） */
.particles { position: absolute; inset: 0; pointer-events: none; mix-blend-mode: screen; opacity: 0; }
.chrome_s1 .particles { background: radial-gradient(circle at 20% 30%, rgba(232,183,200,.15) 0, transparent 6%), radial-gradient(circle at 78% 50%, rgba(232,183,200,.10) 0, transparent 5%), radial-gradient(circle at 50% 80%, rgba(247,240,232,.10) 0, transparent 4%), radial-gradient(circle at 30% 65%, rgba(232,183,200,.08) 0, transparent 3%); }
.chrome_s2 .particles { background: radial-gradient(circle at 25% 20%, rgba(221,231,240,.10) 0, transparent 5%), radial-gradient(circle at 70% 60%, rgba(150,170,200,.12) 0, transparent 4%), radial-gradient(circle at 50% 88%, rgba(255,255,255,.06) 0, transparent 3%); }
.chrome_s3 .particles { background: radial-gradient(circle at 25% 30%, rgba(216,168,91,.18) 0, transparent 6%), radial-gradient(circle at 75% 55%, rgba(247,210,160,.12) 0, transparent 5%), radial-gradient(circle at 40% 85%, rgba(232,183,200,.08) 0, transparent 4%); }
.chrome_s4 .particles { background: radial-gradient(circle at 30% 40%, rgba(201,122,134,.18) 0, transparent 5%), radial-gradient(circle at 70% 65%, rgba(140,60,75,.16) 0, transparent 5%); }
.chrome_s5 .particles { background: radial-gradient(circle at 18% 22%, rgba(255,255,255,.22) 0, transparent 1.5%), radial-gradient(circle at 38% 35%, rgba(255,255,255,.18) 0, transparent 1.2%), radial-gradient(circle at 72% 18%, rgba(255,255,255,.20) 0, transparent 1.8%), radial-gradient(circle at 60% 42%, rgba(216,168,91,.18) 0, transparent 2%), radial-gradient(circle at 85% 55%, rgba(255,255,255,.16) 0, transparent 1.5%), radial-gradient(circle at 22% 65%, rgba(216,168,91,.14) 0, transparent 1.8%), radial-gradient(circle at 55% 82%, rgba(255,255,255,.14) 0, transparent 1.2%); }

/* 封面 (cover) — 两人头像 + 大标题 + 时间线节点（间距加大） */
.cover { position: absolute; inset: 0; z-index: 50; background: #06080F; overflow: hidden; }
.cv-bg-rh { position: absolute; left: -10%; top: -10%; width: 65%; height: 70%; background-image: url("cover_assets/lirh.jpg"); background-size: cover; background-position: center; filter: blur(40px) saturate(.7) brightness(.45); opacity: .55; transform: scale(1.2); }
.cv-bg-yc { position: absolute; right: -10%; top: -10%; width: 65%; height: 70%; background-image: url("cover_assets/rainie.jpg"); background-size: cover; background-position: center; filter: blur(40px) saturate(.85) brightness(.50); opacity: .55; transform: scale(1.2); }
.cv-veil { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(6,8,15,.45) 0%, rgba(6,8,15,.70) 38%, rgba(6,8,15,.92) 100%); }
.cv-grain { position: absolute; inset: 0; background-image: radial-gradient(circle at 10% 30%, rgba(255,255,255,.04) 0 .5px, transparent .8px), radial-gradient(circle at 80% 70%, rgba(255,255,255,.04) 0 .5px, transparent .8px), radial-gradient(circle at 50% 50%, rgba(255,255,255,.03) 0 .4px, transparent .7px); background-size: 200px 200px, 240px 240px, 180px 180px; opacity: .55; }

.cv-portraits { position: absolute; top: 140px; left: 0; right: 0; display: flex; align-items: center; justify-content: center; gap: 36px; }
.cv-pf { display: flex; flex-direction: column; align-items: center; gap: 18px; }
.cv-img { width: 280px; height: 280px; border-radius: 50%; background-size: cover; background-position: center top; border: 4px solid rgba(255,255,255,.92); box-shadow: 0 24px 60px rgba(0,0,0,.55), inset 0 0 0 1px rgba(255,255,255,.15); }
.cv-img-lirh { background-image: url("cover_assets/lirh.jpg"); background-position: center center; }
.cv-img-rainie { background-image: url("cover_assets/rainie.jpg"); background-position: center center; }
.cv-label { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.cv-role { font-family: "Noto Sans SC", sans-serif; font-size: 22px; font-weight: 600; letter-spacing: .32em; color: rgba(216,168,91,.85); }
.cv-name { font-family: "Noto Serif SC", serif; font-size: 56px; font-weight: 800; color: #F7F0E8; letter-spacing: .04em; }
.cv-amp { font-family: "Noto Serif SC", serif; font-size: 96px; font-weight: 300; color: rgba(216,168,91,.55); padding: 0 8px; transform: translateY(-32px); }

.cv-main { position: absolute; top: 760px; left: 70px; right: 70px; }
.cv-eyebrow { font-family: "Noto Sans SC", sans-serif; font-size: 28px; font-weight: 700; letter-spacing: .38em; color: #D8A85B; margin-bottom: 30px; }
.cv-title { font-family: "Noto Serif SC", serif; font-size: 130px; font-weight: 800; line-height: 1.06; color: #F7F0E8; letter-spacing: -3px; margin-bottom: 32px; }
.cv-sub { font-family: "Noto Serif SC", serif; font-size: 46px; font-weight: 500; color: rgba(247,240,232,.78); line-height: 1.4; }

.cv-rail { position: absolute; bottom: 90px; left: 70px; right: 70px; }
.cv-yr { font-family: "Noto Sans SC", sans-serif; font-size: 22px; letter-spacing: .48em; font-weight: 800; color: rgba(216,168,91,.9); margin-bottom: 24px; }
.cv-node { display: flex; align-items: baseline; gap: 32px; padding: 18px 0; border-bottom: 1px solid rgba(255,255,255,.10); }
.cv-node:last-child { border-bottom: none; }
.cv-n { font-family: "Noto Sans SC", sans-serif; font-size: 32px; font-weight: 800; color: #D8A85B; letter-spacing: .12em; min-width: 70px; }
.cv-nm { font-family: "Noto Serif SC", serif; font-size: 44px; font-weight: 600; color: #F7F0E8; flex: 1; }
.cv-yy { font-family: "Noto Sans SC", sans-serif; font-size: 22px; font-weight: 600; color: rgba(247,240,232,.55); letter-spacing: .18em; }

/* Hook (intro 5节点扫过) */
.hook { position: absolute; inset: 0; z-index: 49; background: linear-gradient(180deg, #0A0F1C 0%, #06080F 100%); }
.hk-grad { position: absolute; inset: 0; background: radial-gradient(ellipse at 30% 20%, rgba(232,183,200,.07) 0, transparent 50%), radial-gradient(ellipse at 70% 80%, rgba(216,168,91,.07) 0, transparent 50%); }
.hk-line { position: absolute; left: 80px; right: 80px; display: flex; align-items: baseline; gap: 30px; opacity: 0; }
#hk_1 { top: 540px; }
#hk_2 { top: 720px; }
#hk_3 { top: 900px; }
#hk_4 { top: 1080px; }
#hk_5 { top: 1260px; }
.hk-y { font-family: "Noto Sans SC", sans-serif; font-size: 28px; font-weight: 800; color: #D8A85B; letter-spacing: .25em; min-width: 130px; }
.hk-n { font-family: "Noto Serif SC", serif; font-size: 56px; font-weight: 700; color: #F7F0E8; }
.hk-tag { font-family: "Noto Serif SC", serif; font-size: 30px; font-weight: 400; color: rgba(247,240,232,.55); margin-left: auto; }

/* Outro */
.outroblk { position: absolute; inset: 0; z-index: 48; background: radial-gradient(ellipse at 50% 40%, #1A1828 0%, #06080F 70%); }
.ot-bg { position: absolute; inset: 0; background: radial-gradient(circle at 50% 50%, rgba(216,168,91,.10) 0, transparent 45%); }
.ot-rail { position: absolute; top: 420px; left: 100px; right: 100px; }
.ot-line { display: flex; align-items: baseline; gap: 28px; padding: 10px 0; opacity: 0; }
.ot-y { font-family: "Noto Sans SC", sans-serif; font-size: 22px; font-weight: 800; color: #D8A85B; letter-spacing: .25em; min-width: 110px; }
.ot-n { font-family: "Noto Serif SC", serif; font-size: 44px; font-weight: 700; color: #F7F0E8; }
.ot-h { position: absolute; top: 880px; left: 100px; right: 100px; font-family: "Noto Serif SC", serif; font-size: 100px; font-weight: 800; line-height: 1.08; color: #F7F0E8; letter-spacing: -2px; opacity: 0; }
.ot-p { position: absolute; top: 1190px; left: 100px; right: 100px; font-family: "Noto Serif SC", serif; font-size: 36px; color: rgba(247,240,232,.65); opacity: 0; }
.ot-q { position: absolute; top: 1290px; left: 100px; right: 100px; font-family: "Noto Sans SC", sans-serif; font-size: 28px; font-weight: 600; color: var(--acc, #D8A85B); letter-spacing: .15em; opacity: 0; }
'''

# JS: GSAP timeline
def js_chapter(s, idx):
    k = s["key"]; a = abs_anchors[k]
    base = a["start"]
    v0 = a["v0"]; v1 = a["v1"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]; mid0 = a["mid0"]
    end = a["end"]
    fade_out = end - 1.0
    return f'''
// ---- {s["name"]} ----
tl.fromTo("#fv_{k}", {{opacity:0, scale:1.08}}, {{opacity:1, scale:1.0, duration:1.6, ease:"power2.out"}}, {fmt(base)});
tl.to("#tint_{k}", {{opacity:1, duration:1.4, ease:"power1.out"}}, {fmt(base)});
tl.fromTo(".chrome_{k} .rail", {{opacity:0}}, {{opacity:1, duration:.8}}, {fmt(base+0.3)});
tl.fromTo(".chrome_{k} .card", {{opacity:0, x:60, y:-20}}, {{opacity:1, x:0, y:0, duration:.9, ease:"power3.out"}}, {fmt(base+0.6)});
tl.fromTo(".chrome_{k} .particles", {{opacity:0}}, {{opacity:1, duration:2.0, ease:"sine.inOut"}}, {fmt(base+0.4)});
tl.fromTo(".chrome_{k} .src", {{opacity:0, y:8}}, {{opacity:1, y:0, duration:.6, ease:"power1.out"}}, {fmt(base+1.2)});
// 旁白结束→消化位→swell：卡片淡出，关键词大字
tl.to(".chrome_{k} .card", {{opacity:0, y:-12, duration:.55, ease:"power2.in"}}, {fmt(sw0-0.1)});
tl.fromTo(".chrome_{k} #kw_{k}", {{opacity:0, scale:.92}}, {{opacity:.32, scale:1.0, duration:1.6, ease:"power3.out"}}, {fmt(full0-0.4)});
tl.to(".chrome_{k} #kw_{k}", {{opacity:.5, duration:1.0, ease:"sine.inOut"}}, {fmt(full0+0.6)});
// 中段金句：在高光后半段叠
tl.fromTo(".chrome_{k} #mid_{k}", {{opacity:0, y:30}}, {{opacity:1, y:0, duration:.8, ease:"power2.out"}}, {fmt(mid0)});
tl.to(".chrome_{k} #mid_{k}", {{opacity:0, y:-12, duration:.55, ease:"power2.in"}}, {fmt(end-1.4)});
tl.to(".chrome_{k} #kw_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(end-1.4)});
// 章节收尾淡出 footage + 章节 chrome（带 hard kill 防 seek 残留）
tl.to("#fv_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(fade_out)});
tl.set("#fv_{k}", {{opacity:0}}, {fmt(end)});
tl.to("#tint_{k}", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(fade_out)});
tl.set("#tint_{k}", {{opacity:0}}, {fmt(end)});
tl.to(".chrome_{k} .particles", {{opacity:0, duration:1.0, ease:"power1.in"}}, {fmt(fade_out)});
tl.set(".chrome_{k} .particles", {{opacity:0}}, {fmt(end)});
tl.to(".chrome_{k} .src", {{opacity:0, duration:.6, ease:"power1.in"}}, {fmt(fade_out)});
tl.set(".chrome_{k} .src", {{opacity:0}}, {fmt(end)});
tl.to(".chrome_{k} .rail", {{opacity:0, duration:.6, ease:"power1.in"}}, {fmt(end-0.4)});
tl.set(".chrome_{k} .rail", {{opacity:0}}, {fmt(end)});
'''

JS = f'''
// 封面 0~{COVER_D}s 静态
tl.set("#cover", {{opacity:1}}, 0);
tl.to("#cover", {{opacity:0, duration:.6, ease:"power2.in"}}, {fmt(COVER_D-0.6)});

// Hook 5 行扫过
tl.set("#hook", {{opacity:1}}, {fmt(COVER_D)});
{''.join(f'tl.fromTo("#hk_{i+1}", {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:.55, ease:"power2.out"}}, {fmt(COVER_D + 0.5 + i*1.6)});' + chr(10) for i in range(5))}
{''.join(f'tl.to("#hk_{i+1}", {{opacity:.35, duration:.6, ease:"power1.out"}}, {fmt(COVER_D + 0.5 + i*1.6 + 1.2)});' + chr(10) for i in range(5))}
tl.to("#hook", {{opacity:0, duration:.8, ease:"power2.in"}}, {fmt(INTRO_T + INTRO_D - 0.8)});

{''.join(js_chapter(s, i) for i, s in enumerate(SONGS_META))}

// Outro
tl.fromTo("#outro", {{opacity:0}}, {{opacity:1, duration:.8, ease:"power2.out"}}, {fmt(OUTRO_T)});
{''.join(f'tl.fromTo(".ot-rail .ot-line:nth-child({i+1})", {{opacity:0, x:-20}}, {{opacity:.9, x:0, duration:.5, ease:"power2.out"}}, {fmt(OUTRO_T + 0.4 + i*0.18)});' + chr(10) for i in range(5))}
tl.fromTo(".ot-h", {{opacity:0, y:40}}, {{opacity:1, y:0, duration:1.0, ease:"power3.out"}}, {fmt(OUTRO_T + 2.0)});
tl.fromTo(".ot-p", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:.7, ease:"power2.out"}}, {fmt(OUTRO_T + 3.2)});
tl.fromTo(".ot-q", {{opacity:0, y:10}}, {{opacity:.95, y:0, duration:.6, ease:"power2.out"}}, {fmt(OUTRO_T + 4.5)});
tl.to("#outro", {{opacity:1, duration:.1}}, {fmt(TOTAL-0.2)});
'''

html = f'''<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
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

Path("hf/index.html").write_text(html, encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"lirh-yangcl-timeline"}', encoding="utf-8")
print("index.html written:", len(html), "bytes")

# 切出每首歌从 mseek 起始的 footage 段（HyperFrames 控不了 currentTime，必须预切）
Path("hf/clips_seg").mkdir(exist_ok=True)
for idx, s in enumerate(SONGS_META):
    k = s["key"]; a = abs_anchors[k]
    sect_dur = a["end"] - a["start"]
    seek = SOURCES[k][1]
    src = f"{C}/{SOURCES[k][0]}.mp4"
    out = f"hf/clips_seg/{k}.mp4"
    # 输出端 seek 抽 video（音频不要 — 用 master.wav）；密集关键帧给 HF seek 用
    run(["ffmpeg","-v","error","-ss",str(seek),"-i",src,"-t",str(sect_dur),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
         "-pix_fmt","yuv420p","-an", out, "-y"])
    print(f"clips_seg/{k}.mp4 ({sect_dur}s from {seek}s)")

print("ALL BUILD DONE")

