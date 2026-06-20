#!/usr/bin/env python3
"""华晨宇最被低估的5首歌 — 单一来源构建脚本。
切片(crop+letterbox) → master.wav(逐段 床→swell→展示, 逐首 loudnorm 统一) → index.html。

揭晓序 5→1: Let You Go / 消失的昨天 / 造物者 / 微光 / 我离孤单几公里。
女声旁白(zf_xiaoyi)。展示段 vocal onset 对齐转场旁白收尾前 ~2s(CONVENTIONS 展示段硬规则 C)。
封面/片头取微光特写,片尾取我离孤单(不复用同一段,见 diversify-footage-sources)。

ENV:
  SAMPLE_KEYS=p2_weiguang,p1_wligj   只构建这几首(+intro/outro)出样片
  SKIP_CLIPS=1                        复用已切好的 clips/(只重建 master+html)
"""
import contextlib
import json
import os
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
R = ROOT / "raw"
C.mkdir(exist_ok=True)

# ---- 时间常量 ----
LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
CLIP_PAD = 0.8   # 切片比 seg_dur 多留的安全尾(避免末尾黑帧)

# 各首音乐增益微调(loudnorm I=-14 后若仍偏轻在此抬)。QA 后回填:
# 消失/造物者带戏剧停顿/间奏 → 窗均值偏低(-17.x),抬到与其余 ~-15 一致;微光-13.8略热不动。
MGAIN = {"p1_wligj": 1.12, "p4_xiaoshi": 1.32, "p3_zaowuzhe": 1.26}

SAMPLE_KEYS = [k for k in os.environ.get("SAMPLE_KEYS", "").split(",") if k]
SKIP_CLIPS = os.environ.get("SKIP_CLIPS") == "1"

# ---- 选源 / 窗口 / 裁切(揭晓序 5→1) ----
ITEMS = [
    {"key": "p5_letyougo", "raw": "letyougo_hntv.mkv", "no": "05",
     "name": "《Let You Go》", "plain": "Let You Go", "album": "卡西莫多的礼物 · 2014",
     "vocal_onset": 76.0, "show": 23.0, "crop": "1920:575:0:178",
     "tag": "把放手唱得漂浮又空", "note": "首专遗珠，存在感低却最耐听"},
    {"key": "p4_xiaoshi", "raw": "xsdzt_2021.mkv", "no": "04",
     "name": "《消失的昨天》", "plain": "消失的昨天", "album": "H · 2017",
     "vocal_onset": 163.0, "show": 24.0, "crop": "1920:1008:0:0",
     "tag": "站在原地，和昨天慢慢告别", "note": "H 的隐藏款，旋律情绪都很完整"},
    {"key": "p3_zaowuzhe", "raw": "zwz_haikou.mkv", "no": "03",
     "name": "《造物者》", "plain": "造物者", "album": "H · 2017",
     "vocal_onset": 101.0, "show": 25.0, "crop": "1920:898:0:58",
     "tag": "有点冷、有点俯瞰的世界观", "note": "真爱粉单拎出来的「很有东西」"},
    {"key": "p2_weiguang", "raw": "weiguang_9th.mp4", "no": "02",
     "name": "《微光》", "plain": "微光", "album": "卡西莫多的礼物 · 2014",
     "vocal_onset": 216.0, "show": 38.0, "crop": "1920:960:0:0",
     "tag": "细小的光，唱得一点都不廉价", "note": "早期最难得的温柔与明亮"},
    {"key": "p1_wligj", "raw": "wligj_2016sz.mp4", "no": "01",
     "name": "《我离孤单几公里》", "plain": "我离孤单几公里", "album": "H · 2017",
     "vocal_onset": 120.0, "show": 34.0, "crop": "1280:636:0:0",
     "tag": "越安静，越有后劲", "note": "藏在专辑最深处的一段独白"},
]
if SAMPLE_KEYS:
    ITEMS = [it for it in ITEMS if it["key"] in SAMPLE_KEYS]

# 封面/片头(微光特写) 与 片尾(我离孤单) 的取景
INTRO_SRC = {"raw": "weiguang_9th.mp4", "ss": 117.0, "crop": "1920:960:0:0"}
OUTRO_SRC = {"raw": "wligj_2016sz.mp4", "ss": 178.0, "crop": "1280:636:0:0"}

RANK_DISPLAY = [("01", "我离孤单几公里"), ("02", "微光"), ("03", "造物者"),
                ("04", "消失的昨天"), ("05", "Let You Go")]


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


def vfilter(crop, br=-0.32, sat=1.06):
    return (
        f"[0:v]crop={crop},split=2[bg][fg];"
        f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"gblur=sigma=30,eq=brightness={br}:saturation={sat}[bgb];"
        f"[fg]scale=1080:-2[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )


def cut_clip(raw, ss, dur_s, crop, out):
    """input-seek 到 ss-4(快, 落在前面的关键帧) + output-seek 4s(精确到 ss) → crop+letterbox。"""
    pre = 4.0 if ss >= 4.0 else 0.0
    run([
        "ffmpeg", "-v", "error",
        "-ss", str(q(ss - pre)), "-i", str(R / raw),
        "-ss", str(q(pre)), "-t", str(q(dur_s)),
        "-filter_complex", vfilter(crop),
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        str(out), "-y",
    ])


# ---- 时间轴 ----
d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")
for it in ITEMS:
    it["voice_dur"] = dur(A / f"{it['key']}.wav")
    it["full_start_local"] = q(LEAD + it["voice_dur"] + 0.25 + DIG)
    it["seg_dur"] = q(it["full_start_local"] + it["show"])
    it["clip_start_src"] = q(it["vocal_onset"] - (LEAD + it["voice_dur"] - 2.0))

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for it in ITEMS:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + it["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + it["show"])
    blocks.append({**it, "start": q(t), "end": end,
                   "narr_start": narr_start, "narr_end": narr_end, "full_start": full_start})
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total_planned = q(cta_voice_end + OUTRO_TAIL)

# ---- 切片 ----
if not SKIP_CLIPS:
    cut_clip(INTRO_SRC["raw"], INTRO_SRC["ss"], q(intro_end + CLIP_PAD), INTRO_SRC["crop"], C / "vert_intro.mp4")
    for b in blocks:
        cut_clip(b["raw"], b["clip_start_src"], q(b["seg_dur"] + CLIP_PAD), b["crop"], C / f"vert_{b['key']}.mp4")
    outro_dur_clip = q(total_planned - outro_start + CLIP_PAD)
    cut_clip(OUTRO_SRC["raw"], OUTRO_SRC["ss"], outro_dur_clip, OUTRO_SRC["crop"], C / "vert_outro.mp4")
    print("clips cut.")


# ---- 音频包络 ----
def song_envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + 0.25)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []
intro_dur = intro_end
run([
    "ffmpeg", "-v", "error", "-i", f"{C}/vert_intro.mp4", "-i", f"{A}/intro.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
])
segments.append("seg_intro.wav")

for b in blocks:
    seg_dur = q(b["end"] - b["start"])
    narr_end_local = q(LEAD + b["voice_dur"])
    full_start_local = q(b["full_start"] - b["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    run([
        "ffmpeg", "-v", "error", "-i", f"{C}/vert_{b['key']}.mp4", "-i", f"{A}/{b['key']}.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=level=disabled:limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
    ])
    segments.append(out)

outro_dur = q(total_planned - outro_start)
cta_local = q(cta_voice - outro_start)
run([
    "ffmpeg", "-v", "error", "-i", f"{C}/vert_outro.mp4", "-i", f"{A}/outro.wav", "-i", f"{A}/outro_cta.wav",
    "-filter_complex",
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
    f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
    f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
    f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=level=disabled:limit=0.95[out]",
    "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
])
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", total_planned)


# ---- HTML ----
def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (f'<video id="v{idx}" class="fv" data-start="{q(start)}" data-duration="{q(duration)}" '
            f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>')


videos = [video_tag(0, 0, intro_end, "vert_intro")]
for idx, b in enumerate(blocks, start=1):
    videos.append(video_tag(idx, b["start"], q(b["end"] - b["start"]), f"vert_{b['key']}"))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), "vert_outro"))

labels, tweens = [], []
for idx, b in enumerate(blocks):
    fid, mid = f"full{idx}", f"mini{idx}"
    fdur = q(b["full_start"] - b["start"])
    mdur = q(b["end"] - b["full_start"])
    rank_class = " topRank" if b["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}" data-start="{b["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {b["no"]} 名</div><h2>{b["name"]}</h2>'
        f'<p class="album">{b["album"]}</p>'
        f'<p class="tag">{b["tag"]}</p><p class="note">{b["note"]}</p></section>')
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{b["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{b["no"]}</span><strong>{b["plain"]}</strong></section>')
    tweens.append(f'tl.from("#{fid} .rank",{{y:28,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.18)});')
    tweens.append(f'tl.from("#{fid} h2",{{y:44,opacity:0,duration:.6,ease:"power3.out"}},{q(b["start"]+.35)});')
    tweens.append(f'tl.from("#{fid} .album",{{y:18,opacity:0,duration:.4,ease:"power2.out"}},{q(b["start"]+.62)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+.82)});')
    tweens.append(f'tl.from("#{fid} .note",{{y:18,opacity:0,duration:.45,ease:"power2.out"}},{q(b["start"]+1.02)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(b["full_start"]-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(b["full_start"])});')
    tweens.append(f'tl.from("#{mid}",{{x:-26,opacity:0,duration:.45,ease:"power2.out"}},{q(b["full_start"]+.1)});')

ranking_rows = "".join(f'<li><span>{n}</span><strong>{name}</strong></li>' for n, name in RANK_DISPLAY)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0810;font-family:"Noto Sans SC",sans-serif;color:#f4ede1}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0a0810}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(6,4,10,.74),rgba(6,4,10,.10) 30%,rgba(6,4,10,.16) 56%,rgba(6,4,10,.84))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.10;background:repeating-linear-gradient(0deg,rgba(255,255,255,.15) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:5;padding:168px 76px 150px;display:flex;flex-direction:column;justify-content:space-between}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:850;color:#e7a44c;letter-spacing:.04em}
.eyebrow:before{content:"";width:52px;height:4px;background:#e7a44c;border-radius:99px}
#cover h1{margin-top:30px;font-size:128px;line-height:1.04;font-weight:900;max-width:940px;text-wrap:balance;letter-spacing:.01em}
#cover h1 b{color:#ffd98a;font-weight:900}
#cover .sub{margin-top:30px;font-size:37px;line-height:1.5;color:#d8cdbd;font-weight:550;max-width:880px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:900px}
.chips span{border:1px solid rgba(231,164,76,.50);color:#f3d6ac;background:rgba(12,9,16,.50);font-size:28px;font-weight:700;padding:12px 18px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:188px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(7,5,11,.84),rgba(7,5,11,.48));border-left:8px solid #e7a44c;border-radius:4px}
.fullLabel .rank{font-size:30px;font-weight:900;color:#e7a44c;letter-spacing:.06em}
.fullLabel h2{margin-top:12px;font-size:80px;line-height:1.06;font-weight:900}
.fullLabel .album{margin-top:12px;font-size:27px;font-weight:600;color:#a99e8e;letter-spacing:.06em}
.fullLabel .tag{margin-top:18px;font-size:40px;line-height:1.3;font-weight:850;color:#f3c89a}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.4;font-weight:550;color:#ccc1b3}
.fullLabel.topRank{border-left-color:#ffd98a;box-shadow:0 0 60px rgba(255,217,138,.18)}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#ffd98a}
.miniLabel{position:absolute;z-index:5;top:96px;left:58px;display:flex;align-items:center;gap:16px;padding:12px 18px;background:rgba(7,5,11,.66);border:1px solid rgba(231,164,76,.55);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:900;color:#e7a44c}
.miniLabel strong{font-size:36px;font-weight:800}
.miniLabel.topRank{border-color:rgba(255,217,138,.72)}
.miniLabel.topRank span{color:#ffd98a}
#outro{position:absolute;z-index:5;inset:0;padding:150px 76px;display:flex;flex-direction:column;justify-content:center}
#outro .small{font-size:32px;font-weight:850;color:#e7a44c;letter-spacing:.05em}
#outro h2{margin-top:18px;font-size:66px;line-height:1.18;font-weight:900;max-width:910px}
#outro h2 b{color:#ffd98a}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;padding:17px 22px;background:rgba(7,5,11,.60);border:1px solid rgba(255,255,255,.10);border-radius:8px}
#outro li span{font-size:33px;font-weight:900;color:#e7a44c}
#outro li:first-child{border-color:rgba(255,217,138,.55)}
#outro li:first-child span{color:#ffd98a}
#outro li strong{font-size:34px;font-weight:800;text-align:right}
#outro .close{margin-top:32px;font-size:31px;line-height:1.48;color:#d8cdbd;font-weight:550}
#cta{position:absolute;z-index:6;left:76px;right:76px;bottom:104px;text-align:center}
#cta .v{font-size:46px;font-weight:900;color:#ffd98a;line-height:1.22}
#cta .f{margin-top:16px;font-size:35px;font-weight:850;color:#e7a44c;letter-spacing:.1em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.1)}" data-track-index="2">'
    '<div><div class="eyebrow">被低估的遗珠盘点</div>'
    '<h1>华晨宇<br>最被<b>低估</b>的5首歌</h1>'
    '<p class="sub">不是高音，也不是炸裂。这五首藏在专辑深处的遗珠，安静、耐听，越听越有味道——值得被重新听见。</p></div>'
    '<div class="chips"><span>专辑遗珠</span><span>被低估</span><span>越听越上头</span><span>温柔的光</span><span>单曲循环</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div>'
    '<h2>被低估，从来不等于<b>不够好</b>。最安静的歌，往往最经得起重听。</h2>'
    f'<ol>{ranking_rows}</ol>'
    '<p class="close">从 Let You Go、消失的昨天、造物者、微光，到我离孤单几公里——华晨宇藏得最深的五首遗珠。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
// 首屏封面硬约束: t=0 第一帧须为完整静态封面(标题可见)。
// → 封面元素 opacity 起即 1, 入场只用 transform(scale/位移) settle, 保留 0-1s 视觉动作但不 fade-from-blank。
tl.set("#cover .eyebrow,#cover h1,#cover .sub,#cover .chips span",{{opacity:1}},0);
tl.from("#cover .eyebrow",{{x:-20,duration:.7,ease:"power2.out"}},0);
tl.from("#cover h1",{{scale:1.035,transformOrigin:"left top",duration:1.1,ease:"power3.out"}},0);
tl.from("#cover .sub",{{y:18,duration:.7,ease:"power2.out"}},0.25);
tl.from("#cover .chips span",{{y:14,duration:.5,ease:"power2.out",stagger:.07}},0.45);
tl.to("#cover h1",{{scale:1.012,transformOrigin:"left top",duration:2.2,yoyo:true,repeat:1,ease:"sine.inOut"}},4.5);
tl.to("#cover",{{opacity:0,duration:.4,ease:"power1.in"}},{q(intro_end-.55)});
{chr(10).join(tweens)}
tl.from("#outro .small",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.from("#outro h2",{{y:40,opacity:0,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.from("#outro li",{{x:-34,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.15)});
tl.from("#outro .close",{{y:24,opacity:0,duration:.45,ease:"power2.out"}},{q(outro_start+2.0)});
tl.from("#cta .v",{{y:26,opacity:0,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.from("#cta .f",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},{q(cta_voice+0.35)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@500;700;800;900&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{body}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["main"] = tl;
  </script>
</body>
</html>
"""

(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "huachenyu-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], "clip_src", b["clip_start_src"], "start", b["start"], "full", b["full_start"], "end", b["end"]) for b in blocks])
