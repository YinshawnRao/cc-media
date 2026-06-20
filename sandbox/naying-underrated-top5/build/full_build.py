#!/usr/bin/env python3
"""Build master.wav + HyperFrames HTML for 那英最被低估的5首歌."""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"

LEAD = 0.35
DIG = 1.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.45
INTRO_GAP = 1.15
BETWEEN = 0.0
OUTRO_TAIL = 2.6
DIGEST_O = 1.0
INTRO_CLIP = "vert_chuan"
OUTRO_CLIP = "vert_yuandu"

# Per-song gain compensation after QA. Keep at 1.0 until volumedetect proves otherwise.
MGAIN = {}


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def q(value):
    return round(float(value), 3)


json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))

items = [
    {
        "key": "p5_chuan", "clip": "vert_chuan", "no": "05",
        "name": "《船》", "plain": "船", "show": 30.0,
        "tag": "不抢，却有漂远之后的空",
        "note": "《我不是天使》时期被低估的离岸感",
        "mask": True,
    },
    {
        "key": "p4_nideshiwoderen", "clip": "vert_nideshiwoderen", "no": "04",
        "name": "《你是我的人》", "plain": "你是我的人", "show": 32.0,
        "tag": "《征服》里少见的和缓柔软",
        "note": "被同名主打和几首大歌压住的一面",
        "mask": False,
        "album": True,
    },
    {
        "key": "p3_wanqianli", "clip": "vert_wanqianli", "no": "03",
        "name": "《一万一千公里》", "plain": "一万一千公里", "show": 32.0,
        "tag": "远、长、到不了的关系",
        "note": "林夕词，李偲菘曲，文艺感藏在拨弦里",
        "mask": False,
    },
    {
        "key": "p2_baisixian", "clip": "vert_baisixian", "no": "02",
        "name": "《白丝线》", "plain": "白丝线", "show": 30.0,
        "tag": "不靠热度，靠质感留下来",
        "note": "《干脆》里唱法和气质都很特别的遗珠",
        "mask": True,
    },
    {
        "key": "p1_yuandu", "clip": "vert_yuandu", "no": "01",
        "name": "《愿赌服输》", "plain": "愿赌服输", "show": 34.0,
        "tag": "硬气里的脆弱",
        "note": "输也输得明白，不撒娇，不求饶",
        "mask": False,
    },
]

d_intro = dur(A / "intro.wav")
d_outro = dur(A / "outro.wav")
d_cta = dur(A / "outro_cta.wav")
for item in items:
    item["voice_dur"] = dur(A / f"{item['key']}.wav")

intro_end = q(INTRO_VOICE_START + d_intro + INTRO_GAP)
t = intro_end
blocks = []
for item in items:
    narr_start = q(t + LEAD)
    narr_end = q(narr_start + item["voice_dur"])
    full_start = q(narr_end + 0.25 + DIG)
    end = q(full_start + item["show"])
    block = {
        **item,
        "start": q(t),
        "end": end,
        "narr_start": narr_start,
        "narr_end": narr_end,
        "full_start": full_start,
    }
    blocks.append(block)
    t = q(end + BETWEEN)

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
planned_total = q(cta_voice_end + OUTRO_TAIL)


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
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{INTRO_CLIP}.mp4",
        "-i", f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_dur},volume=0.12,afade=t=in:st=0:d=0.8,afade=t=out:st={intro_dur-0.9}:d=0.9[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ]
)
segments.append("seg_intro.wav")

for block in blocks:
    seg_dur = q(block["end"] - block["start"])
    narr_end_local = q(LEAD + block["voice_dur"])
    full_start_local = q(block["full_start"] - block["start"])
    env = song_envelope(narr_end_local, full_start_local)
    music_gain = MGAIN.get(block["key"], 1.0)
    out = f"seg_{block['key']}.wav"
    run(
        [
            "ffmpeg", "-v", "error",
            "-i", f"{C}/{block['clip']}.mp4",
            "-i", f"{A}/{block['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{env}':eval=frame,volume={music_gain}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(planned_total - outro_start)
cta_local = q(cta_voice - outro_start)
run(
    [
        "ffmpeg", "-v", "error",
        "-i", f"{C}/{OUTRO_CLIP}.mp4",
        "-i", f"{A}/outro.wav",
        "-i", f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.14,afade=t=in:st=0:d=0.8,afade=t=out:st={outro_dur-1.6}:d=1.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ]
)
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt", "-ac", "2", "-ar", "48000", "master.wav", "-y"])
total = dur(ROOT / "master.wav")
print("master dur:", total, "planned:", planned_total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="clips/{src}.mp4" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, INTRO_CLIP)]
for idx, block in enumerate(blocks, start=1):
    videos.append(video_tag(idx, block["start"], q(block["end"] - block["start"]), block["clip"]))
videos.append(video_tag(len(videos), outro_start, q(total - outro_start), OUTRO_CLIP))

labels = []
tweens = []
for idx, block in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(block["full_start"] - block["start"])
    mdur = q(block["end"] - block["full_start"])
    rank_class = " topRank" if block["no"] == "01" else ""
    album_class = " albumRank" if block.get("album") else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{rank_class}{album_class}" data-start="{block["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {block["no"]} 名</div><h2>{block["name"]}</h2><p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{rank_class}" data-start="{block["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{block["no"]}</span><strong>{block["plain"]}</strong></section>'
    )
    if block.get("mask"):
        labels.append(
            f'<div id="mask{idx}" class="clip lyricMask" data-start="{block["start"]}" data-duration="{q(block["end"] - block["start"])}" data-track-index="5"></div>'
        )
    tweens.append(f'tl.fromTo("#{fid} .rank",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power3.out"}},{q(block["start"]+.18)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:48,opacity:0,filter:"blur(6px)"}},{{y:0,opacity:1,filter:"blur(0px)",duration:.68,ease:"expo.out"}},{q(block["start"]+.35)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"sine.out"}},{q(block["start"]+.76)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{x:18,opacity:0}},{{x:0,opacity:1,duration:.48,ease:"power1.out"}},{q(block["start"]+1.02)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,filter:"blur(8px)",duration:.42,ease:"power1.in"}},{q(block["full_start"]-.5)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(block["full_start"])});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(block["full_start"]+.1)});')
    if block.get("album"):
        tweens.append(f'tl.fromTo("#v{idx}",{{scale:1.0}},{{scale:1.055,duration:{q(block["end"]-block["start"])},ease:"sine.inOut"}},{q(block["start"])});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "船"),
        ("04", "你是我的人"),
        ("03", "一万一千公里"),
        ("02", "白丝线"),
        ("01", "愿赌服输"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08070a;font-family:"PingFang SC","Hiragino Sans GB",sans-serif;color:#f8f3ec}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#08070a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0;will-change:transform}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(8,7,10,.78),rgba(8,7,10,.14) 30%,rgba(8,7,10,.16) 58%,rgba(8,7,10,.86))}
#grain{position:absolute;inset:-20px;z-index:2;opacity:.13;background:repeating-linear-gradient(0deg,rgba(248,243,236,.12) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
#cover{position:absolute;inset:0;z-index:6;padding:146px 76px 132px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(8,7,10,.70),rgba(8,7,10,.17) 34%,rgba(8,7,10,.22) 60%,rgba(8,7,10,.88))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#d6b16a;letter-spacing:.08em}
.eyebrow:before{content:"";width:56px;height:4px;background:#d6b16a;border-radius:99px}
#cover h1{margin-top:28px;font-family:"Songti SC","STSong",serif;font-size:116px;line-height:1.08;font-weight:900;max-width:940px;text-shadow:0 7px 42px rgba(0,0,0,.65)}
#cover .sub{margin-top:30px;font-size:39px;line-height:1.5;color:#ded4c5;font-weight:500;max-width:904px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:930px}
.chips span{border:1px solid rgba(214,177,106,.54);color:#f0dfbd;background:rgba(5,5,8,.54);font-size:28px;font-weight:800;padding:12px 19px;border-radius:8px}
.fullLabel{position:absolute;z-index:7;left:70px;right:70px;bottom:196px;padding:35px 36px 39px;background:linear-gradient(135deg,rgba(5,5,8,.88),rgba(5,5,8,.50));border-left:8px solid #d6b16a;border-radius:4px;backdrop-filter:blur(2px)}
.fullLabel .rank{font-size:31px;font-weight:900;color:#d6b16a;letter-spacing:.12em}
.fullLabel h2{font-family:"Songti SC","STSong",serif;margin-top:14px;font-size:88px;line-height:1.06;font-weight:900}
.fullLabel .tag{margin-top:19px;font-size:41px;line-height:1.28;font-weight:900;color:#f0dfbd}
.fullLabel .note{margin-top:12px;font-size:31px;line-height:1.42;font-weight:500;color:#bdb3a6}
.fullLabel.topRank{border-left-color:#c7333f;background:linear-gradient(135deg,rgba(12,6,8,.91),rgba(12,6,8,.52))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#f06f76}
.fullLabel.albumRank{border-left-color:#7fb7b2}
.fullLabel.albumRank .rank,.fullLabel.albumRank .tag{color:#a8d5d1}
.miniLabel{position:absolute;z-index:7;top:94px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(5,5,8,.68);border:1px solid rgba(214,177,106,.56);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:900;color:#d6b16a;font-variant-numeric:tabular-nums}
.miniLabel strong{font-family:"Songti SC","STSong",serif;font-size:39px;font-weight:900}
.miniLabel.topRank{border-color:rgba(199,51,63,.74)}
.miniLabel.topRank span{color:#f06f76}
.lyricMask{position:absolute;z-index:4;left:0;right:0;bottom:0;height:760px;background:linear-gradient(180deg,rgba(8,7,10,0),rgba(8,7,10,.82) 45%,rgba(8,7,10,.96))}
#outro{position:absolute;z-index:6;inset:0;padding:140px 76px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(8,7,10,.26),rgba(8,7,10,.80))}
#outro .small{font-size:32px;font-weight:900;color:#d6b16a;letter-spacing:.12em}
#outro h2{font-family:"Songti SC","STSong",serif;margin-top:20px;font-size:66px;line-height:1.2;font-weight:900;max-width:925px}
#outro ol{margin-top:42px;list-style:none;display:grid;gap:15px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:22px;padding:18px 24px;background:rgba(5,5,8,.60);border:1px solid rgba(248,243,236,.12);border-radius:9px}
#outro li span{font-size:35px;font-weight:900;color:#d6b16a;font-variant-numeric:tabular-nums}
#outro li:last-child{background:rgba(199,51,63,.14);border-color:rgba(199,51,63,.46)}
#outro li:last-child span{color:#f06f76}
#outro li strong{font-family:"Songti SC","STSong",serif;font-size:38px;font-weight:900;text-align:right}
#outro .close{margin-top:34px;font-size:31px;line-height:1.52;color:#ded4c5;font-weight:500}
#cta{position:absolute;z-index:8;left:76px;right:76px;bottom:102px;text-align:center;padding:22px 20px;background:rgba(5,5,8,.66);border:1px solid rgba(214,177,106,.40);border-radius:10px}
#cta .v{font-size:44px;font-weight:900;color:#d6b16a;line-height:1.22}
#cta .f{margin-top:16px;font-size:35px;font-weight:900;color:#7fb7b2;letter-spacing:.12em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.15)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 那英</div><h1>那英最被低估的5首歌</h1>'
    '<p class="sub">不聊最大热歌，只把那些被压在代表作旁边、却越听越有后劲的歌，一首首捡回来。</p></div>'
    '<div class="chips"><span>干脆</span><span>征服</span><span>我不是天使</span><span>硬气里的脆弱</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>这些遗珠把那英声音里的硬气、柔软、距离感和清醒，一层层摊开。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">热门作品证明她能赢；这些歌，反而说明她为什么经得起反复听。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.2)}" data-duration="{q(total-cta_voice+0.2)}" data-track-index="8">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.018,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.3);
tl.fromTo("#cover .eyebrow",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.55,ease:"power3.out"}},0.18);
tl.fromTo("#cover .chips span",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.42,ease:"sine.out",stagger:.08}},1.0);
tl.to("#cover",{{opacity:0,filter:"blur(10px)",duration:.48,ease:"power1.in"}},{q(intro_end-.62)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0,filter:"blur(6px)"}},{{y:0,opacity:1,filter:"blur(0px)",duration:.68,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.18)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(outro_start+2.18)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power1.out"}},{q(cta_voice+0.35)});
"""

html = f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=1080, height=1920" />
  <script src="vendor/gsap.min.js"></script>
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "naying-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"]) for b in blocks])
