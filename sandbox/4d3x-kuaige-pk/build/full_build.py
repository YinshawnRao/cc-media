#!/usr/bin/env python3
"""四大三小快歌 PK — 7 首 ~6:40 竖屏 1080×1920 编排。
产物：master.wav + hf/index.html + hf/clips_seg/<key>.mp4。
"""
import subprocess, wave, contextlib, json, shutil
from pathlib import Path

ROOT = Path("/Users/yinshawnrao/explorer/cc-media")
PROJ = ROOT / "sandbox/4d3x-kuaige-pk"
A = PROJ / "audio"
C = PROJ / "clips"           # vfill 竖屏后的 mp4
HF = PROJ / "hf"
HF.mkdir(exist_ok=True)
(HF / "clips_seg").mkdir(exist_ok=True)
(HF / "cover_assets").mkdir(exist_ok=True)

def dur(p):
    with contextlib.closing(wave.open(str(p), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

# ============ 旁白时长 ============
NARR = {k: dur(A / f"{k}.wav") for k in [
    "intro","rules",
    "s1_voice","s1_mid","s2_voice","s2_mid","s3_voice","s3_mid",
    "s4_voice","s4_mid","s5_voice","s5_mid","s6_voice","s6_mid","s7_voice","s7_mid",
    "outro","vote"]}
print("NARR durs:", json.dumps(NARR, indent=2, ensure_ascii=False))

# ============ 节奏常量 ============
COVER_D   = 4.0          # 静态封面停留（含小动作）
HOOK_D    = NARR["intro"] + 1.5  # intro 旁白 + 7 歌名闪现段
RULES_D   = NARR["rules"] + 3.0  # 规则段（7 卡 + "出场顺序≠排名"）

LEAD       = 0.15        # 进入到 voice 起的预滚
PRE_VOICE  = 0.8         # voice 起前音乐床起伏
POST_VOICE = 1.2         # voice 收尾消化位
SWELL      = 1.5         # swell 时长
BED        = 0.18        # voice 期音乐床增益（旁白响时音乐 -15dB）
HIGH_BASE  = 23          # 副歌展示基础时长（前 6 首，配合 50s 源 cap）
HIGH_LAST  = 25          # 最后一首（杨丞琳，finale）

OUTRO_D   = NARR["outro"] + NARR["vote"] + 7.0  # 总结+投票+CTA 停留

# 每首段总长
def song_seg_len(key):
    high = HIGH_LAST if key == "s7" else HIGH_BASE
    return LEAD + PRE_VOICE + NARR[f"{key}_voice"] + POST_VOICE + SWELL + high + NARR[f"{key}_mid"] + 1.0

starts = {}
t = 0.0
starts["cover"] = (t, COVER_D); t += COVER_D
starts["hook"]  = (t, HOOK_D); t += HOOK_D
starts["rules"] = (t, RULES_D); t += RULES_D
for i in range(1, 8):
    k = f"s{i}"
    L = song_seg_len(k)
    starts[k] = (t, L); t += L
starts["outro"] = (t, OUTRO_D); t += OUTRO_D
TOTAL = round(t, 3)
print(f"\nTOTAL: {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# 章节内锚点（相对段起 0）
def anchors(key):
    voice_dur = NARR[f"{key}_voice"]
    mid_dur   = NARR[f"{key}_mid"]
    high_dur  = HIGH_LAST if key == "s7" else HIGH_BASE
    v0 = LEAD + PRE_VOICE
    v1 = v0 + voice_dur
    sw0 = v1 + POST_VOICE
    full0 = sw0 + SWELL
    full1 = full0 + high_dur
    mid0  = full1 - mid_dur
    return dict(v0=v0, v1=v1, sw0=sw0, full0=full0, full1=full1, mid0=mid0)

# 绝对锚点
abs_anchors = {}
for i in range(1, 8):
    k = f"s{i}"; base = starts[k][0]
    a = anchors(k)
    abs_anchors[k] = {kk: round(base + vv, 3) for kk, vv in a.items()}
    abs_anchors[k]["start"] = round(base, 3)
    abs_anchors[k]["end"]   = round(base + starts[k][1], 3)

# ============ 歌曲元数据 ============
SONGS = [
    dict(key="s1", no="01", singer="蔡依林", song="舞娘", year="2006",
         style="唱跳标杆", clip="s1_caiyilin_wuniang",
         kws=["唱跳控制", "舞台工业化", "快歌标杆"],
         gold="很多人的快歌是热闹，<br>蔡依林的快歌是控制。",
         vote="如果快歌看舞台完成度，这一票很难绕开。",
         bg="#150A1F", pri="#D4A848", acc="#E63C5C", muted="#8B5A8C",
         tint="linear-gradient(180deg, rgba(212,168,72,.22) 0%, rgba(21,10,31,.55) 40%, rgba(0,0,0,.80) 100%)"),
    dict(key="s2", no="02", singer="萧亚轩", song="爱的主打歌", year="2006",
         style="千禧律动", clip="s2_xiaoyaxuan_zhudage",
         kws=["千禧律动", "都市女王", "松弛快歌"],
         gold="她的快歌不是用力炸场，<br>是松弛地踩在节奏上。",
         vote="不费力但很会撩，这一票给松弛感。",
         bg="#0A0A12", pri="#C8C8D4", acc="#E84A8C", muted="#5A5A6E",
         tint="linear-gradient(180deg, rgba(232,74,140,.18) 0%, rgba(10,10,18,.60) 40%, rgba(0,0,0,.85) 100%)"),
    dict(key="s3", no="03", singer="孙燕姿", song="超快感", year="2001",
         style="生命力快歌", clip="s3_sunyanzi_chaokuaigan",
         kws=["少年感", "冲劲", "生命力快歌"],
         gold="她的快，不是舞步的快，<br>是整个人往前跑。",
         vote="快歌也可以是冲出去，这一首必须有名字。",
         bg="#1A1208", pri="#FFB347", acc="#7DC95E", muted="#9A7234",
         tint="linear-gradient(180deg, rgba(255,179,71,.22) 0%, rgba(26,18,8,.55) 42%, rgba(0,0,0,.82) 100%)"),
    dict(key="s4", no="04", singer="梁静茹", song="燕尾蝶", year="2004",
         style="情绪起飞", clip="s4_liangjingru_yanweidie",
         kws=["情绪起飞", "流行摇滚", "梁式快歌"],
         gold="她连快歌都不是为了炫技，<br>而是把心事唱到飞起来。",
         vote="快歌里也有情绪和故事，这一票有重量。",
         bg="#0A0F2A", pri="#8FA8FF", acc="#C8AEFF", muted="#4A5878",
         tint="linear-gradient(180deg, rgba(143,168,255,.18) 0%, rgba(10,15,42,.55) 42%, rgba(0,0,0,.82) 100%)"),
    dict(key="s5", no="05", singer="王心凌", song="Honey", year="2005",
         style="甜心舞曲", clip="s5_wangxinling_honey",
         kws=["甜心舞曲", "旋律记忆", "可爱暴击"],
         gold="甜心快歌不是幼稚，<br>是旋律记忆太强。",
         vote="甜到自动跟着摇，这一票很稳。",
         bg="#2A1020", pri="#FF8FB8", acc="#F7E8F0", muted="#8B5074",
         tint="linear-gradient(180deg, rgba(255,143,184,.22) 0%, rgba(42,16,32,.55) 42%, rgba(0,0,0,.80) 100%)"),
    dict(key="s6", no="06", singer="张韶涵", song="That Girl", year="2012",
         style="自我宣言", clip="s6_zhangshaohan_thatgirl",
         kws=["Girl Power", "电子快歌", "自我宣言"],
         gold="她不是小身体大能量，<br>而是不被定义的 That Girl。",
         vote="她也能唱快歌，且姿态全开。",
         bg="#080A18", pri="#5AC8FF", acc="#D0D8E0", muted="#3A5078",
         tint="linear-gradient(180deg, rgba(90,200,255,.18) 0%, rgba(8,10,24,.60) 42%, rgba(0,0,0,.85) 100%)"),
    dict(key="s7", no="07", singer="杨丞琳", song="新流感", year="2009",
         style="甜酷转型", clip="s7_yangchenglin_xinliugan",
         kws=["甜酷转型", "电子律动", "节奏态度"],
         gold="偶像剧女主不哭了，<br>开始把节奏穿在身上。",
         vote="甜酷上身节奏有攻击性，这一票给转型。",
         bg="#150818", pri="#A8FF5A", acc="#E63C5C", muted="#8B3D74",
         tint="linear-gradient(180deg, rgba(168,255,90,.18) 0%, rgba(21,8,24,.60) 42%, rgba(0,0,0,.85) 100%)"),
]

# ============ 构建每段音频 wav ============
SEG = PROJ / "build/segs"; SEG.mkdir(exist_ok=True)

# intro+rules+cover 段：用 s1 舞娘的器乐尾声/intro 做 ambient bed
PRE_TOTAL = COVER_D + HOOK_D + RULES_D
print(f"PRE_TOTAL (cover+hook+rules): {PRE_TOTAL:.2f}s")

# Build intro seg = cover (silent ambient) + intro voice + rules voice
# We'll mix sequential: voice at COVER_D, then rules at COVER_D+HOOK_D
intro_delay_ms = int((COVER_D + 0.3) * 1000)  # cover 后 0.3s 起 intro 旁白
rules_delay_ms = int((COVER_D + HOOK_D + 0.2) * 1000)

# Use s1 clip as ambient music base (低音量铺底)
def get_clip(key): return str(C / f"vert_{key.replace('s','s')}.mp4")  # vert_s1...s7

clip_for_bed = str(C / "vert_s1.mp4")  # 用 s1 蔡依林做开场 ambient
run(["ffmpeg","-v","error",
     "-i", clip_for_bed,
     "-i", str(A/"intro.wav"),
     "-i", str(A/"rules.wav"),
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={intro_delay_ms}|{intro_delay_ms},volume=2.0[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={rules_delay_ms}|{rules_delay_ms},volume=2.0[v2];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{PRE_TOTAL},asetpts=PTS-STARTPTS,volume=0.16,"
     f"afade=t=in:st=0:d=1.5,afade=t=out:st={PRE_TOTAL-2.0}:d=2.0[bed];"
     f"[v1][v2][bed]amix=inputs=3:normalize=0:duration=longest,atrim=0:{PRE_TOTAL},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",
     str(SEG/"seg_pre.wav"),"-y"])

# 每首歌段
def build_song_seg(s):
    k = s["key"]; seg_len = starts[k][1]
    clip = C / f"vert_{k}.mp4"
    a = anchors(k)
    voice_at = a["v0"]; sw0 = a["sw0"]; full0 = a["full0"]; full1 = a["full1"]
    mid_at = a["mid0"]
    fade_out_start = full1
    fade_out_end = seg_len

    # 音乐床/swell 包络
    # 0→LEAD: 0
    # LEAD→v0: ramp 0→BED
    # v0→sw0: BED
    # sw0→full0: BED→1.0 (swell)
    # full0→full1: 1.0
    # full1→end: afade out
    ve = (f"(lt(t,{LEAD}))*0"
          f"+(between(t,{LEAD},{voice_at}))*({BED}*(t-{LEAD})/{voice_at-LEAD})"
          f"+(between(t,{voice_at},{sw0}))*{BED}"
          f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
          f"+(gte(t,{full0}))*1.0")

    voice_delay_ms = int(voice_at * 1000)
    mid_delay_ms = int(mid_at * 1000)

    out = SEG / f"seg_{k}.wav"
    run(["ffmpeg","-v","error",
         "-i", str(clip),
         "-i", str(A/f"{k}_voice.wav"),
         "-i", str(A/f"{k}_mid.wav"),
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={voice_delay_ms}|{voice_delay_ms},volume=2.0[voice];"
         f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={mid_delay_ms}|{mid_delay_ms},volume=1.6[mid];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{seg_len},asetpts=PTS-STARTPTS,"
         f"volume='{ve}':eval=frame,afade=t=out:st={fade_out_start}:d={fade_out_end-fade_out_start}[music];"
         f"[voice][mid][music]amix=inputs=3:normalize=0:duration=longest,atrim=0:{seg_len},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000", str(out),"-y"])
    return out

for s in SONGS:
    print(f"building seg_{s['key']}...")
    build_song_seg(s)

# outro: 用 s7 杨丞琳 clip 尾声做 bed + outro voice + vote voice
outro_v_delay = int((1.0) * 1000)   # 起手 1s 后旁白进来
vote_v_delay = int((1.0 + NARR["outro"] + 1.8) * 1000)  # outro voice 完 1.8s 后 vote 进
clip_for_outro = str(C / "vert_s7.mp4")
run(["ffmpeg","-v","error",
     "-i", clip_for_outro,
     "-i", str(A/"outro.wav"),
     "-i", str(A/"vote.wav"),
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={outro_v_delay}|{outro_v_delay},volume=2.0[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={vote_v_delay}|{vote_v_delay},volume=2.0[v2];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
     f"atrim=0:{OUTRO_D},asetpts=PTS-STARTPTS,volume=0.20,"
     f"afade=t=in:st=0:d=1.2,afade=t=out:st={OUTRO_D-2.5}:d=2.5[bed];"
     f"[v1][v2][bed]amix=inputs=3:normalize=0:duration=longest,atrim=0:{OUTRO_D},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000",
     str(SEG/"seg_outro.wav"),"-y"])

# concat
seglist = SEG / "seglist.txt"
order = ["seg_pre"] + [f"seg_s{i}" for i in range(1,8)] + ["seg_outro"]
seglist.write_text("\n".join(f"file '{n}.wav'" for n in order) + "\n", encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i", str(seglist),
     "-ac","2","-ar","48000", str(PROJ/"master.wav"),"-y"])
print(f"\nmaster dur: {dur(PROJ/'master.wav')}s vs planned {TOTAL}s")

shutil.copy(PROJ/"master.wav", HF/"master.wav")

# 切出每首歌从 t=0 起 chapter_dur 长的 footage 段（密集关键帧给 HF seek 用）
for s in SONGS:
    k = s["key"]; a = abs_anchors[k]
    sect_dur = a["end"] - a["start"]
    src = str(C / f"vert_{k}.mp4")
    out = str(HF / f"clips_seg/{k}.mp4")
    run(["ffmpeg","-v","error","-i", src, "-t", str(sect_dur),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30",
         "-pix_fmt","yuv420p","-an", out, "-y"])
    print(f"clips_seg/{k}.mp4 ({sect_dur}s)")

print("\n== AUDIO + CLIPS DONE ==")
print(f"Now generate index.html via build/build_html.py")

# save anchors for HTML builder
(PROJ/"build/timing.json").write_text(json.dumps({
    "TOTAL": TOTAL,
    "COVER_D": COVER_D, "HOOK_D": HOOK_D, "RULES_D": RULES_D, "OUTRO_D": OUTRO_D,
    "starts": {k:[v[0],v[1]] for k,v in starts.items()},
    "abs_anchors": abs_anchors,
    "NARR": NARR,
    "SONGS": SONGS,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"timing.json written")
