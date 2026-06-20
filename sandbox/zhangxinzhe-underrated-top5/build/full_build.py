#!/usr/bin/env python3
"""Build master.wav and HyperFrames HTML for 张信哲最被低估的5首歌.

The timeline is calculated from generated narration durations. Final audio must
be muxed from master.wav after HyperFrames render.
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "audio"
C = ROOT / "clips"
CS = ROOT / "clips_seg"
CS.mkdir(exist_ok=True)

LEAD = 0.35
POST = 0.25
DIG = 1.45
BED = 0.16
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.15
OUTRO_TAIL = 2.8
DIGEST_O = 1.05
MASTER_GAIN = 1.04


def dur(path):
    with contextlib.closing(wave.open(str(path), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def q(value):
    return round(float(value), 3)


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


items = [
    {
        "key": "p5_kong",
        "clip": "vert_p5_kong",
        "no": "05",
        "name": "《空出来的时间刚好拿来寂寞》",
        "plain": "空出来的时间刚好拿来寂寞",
        "meta": "空出来的时间 · 2012",
        "show": 30.0,
        "ch_off": 49.0,
        "tag": "城市孤独，不靠大哭取胜",
        "note": "中后期阿哲的都市自白，被歌名耽误的质感单曲",
    },
    {
        "key": "p4_fei",
        "clip": "vert_p4_fei",
        "no": "04",
        "name": "《你应该飞的》",
        "plain": "你应该飞的",
        "meta": "做你的男人 · 2006",
        "show": 30.0,
        "ch_off": 90.0,
        "tag": "舍不得你，也要放你去远方",
        "note": "陈小霞、姚若龙写出的体面告别",
    },
    {
        "key": "p3_shuohuang",
        "clip": "vert_p3_shuohuang",
        "no": "03",
        "name": "《说谎》",
        "plain": "说谎",
        "meta": "做你的男人 · 2006",
        "show": 28.0,
        "ch_off": 72.0,
        "tag": "明知道，却还是替关系找台阶",
        "note": "不是爆哭，是清醒之后仍不愿拆穿",
    },
    {
        "key": "p2_xiayong",
        "clip": "vert_p2_xiayong",
        "no": "02",
        "name": "《下一个永远》",
        "plain": "下一个永远",
        "meta": "下一个永远 · 2004",
        "show": 33.0,
        "ch_off": 142.0,
        "tag": "被《白月光》压住的同名曲",
        "note": "低吟开场到副歌转折，都是电影感",
    },
    {
        "key": "p1_xinqing",
        "clip": "vert_p1_xinqing",
        "no": "01",
        "name": "《心情卡片》",
        "plain": "心情卡片",
        "meta": "直觉 · 1997",
        "show": 32.0,
        "ch_off": 177.5,
        "tag": "粉丝懂，但大众歌单少见",
        "note": "清新、都市、流畅高音，转入新力后的遗珠代表",
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
    full_start = q(narr_end + POST + DIG)
    end = q(full_start + item["show"])
    full_start_local = q(full_start - t)
    mseek = q(max(0, item["ch_off"] - full_start_local))
    block = {
        **item,
        "start": q(t),
        "end": end,
        "narr_start": narr_start,
        "narr_end": narr_end,
        "full_start": full_start,
        "full_start_local": full_start_local,
        "mseek": mseek,
        "seg_dur": q(end - t),
    }
    blocks.append(block)
    t = end

outro_start = q(t)
outro_voice = q(outro_start + LEAD)
outro_voice_end = q(outro_voice + d_outro)
cta_voice = q(outro_voice_end + DIGEST_O)
cta_voice_end = q(cta_voice + d_cta)
total = q(cta_voice_end + OUTRO_TAIL)


def envelope(narr_end_local, full_start_local):
    swell = q(narr_end_local + POST)
    return (
        f"(lt(t,0.8))*({BED}*t/0.8)"
        f"+(between(t,0.8,{swell}))*{BED}"
        f"+(between(t,{swell},{full_start_local}))*({BED}+{1.0-BED}*(t-{swell})/{DIG})"
        f"+(gte(t,{full_start_local}))*1.0"
    )


segments = []

# Intro bed and video.
intro_src = C / "vert_p2_xiayong.mp4"
run(
    [
        "ffmpeg", "-v", "error", "-i", str(intro_src), "-t", str(intro_end),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", str(CS / "intro.mp4"), "-y",
    ]
)
run(
    [
        "ffmpeg", "-v", "error",
        "-i", str(intro_src),
        "-i", str(A / "intro.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(INTRO_VOICE_START*1000)}|{int(INTRO_VOICE_START*1000)},volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{intro_end},volume=0.12,afade=t=in:st=0:d=0.7,afade=t=out:st={q(intro_end-0.8)}:d=0.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{intro_end},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_intro.wav", "-y",
    ]
)
segments.append("seg_intro.wav")

for block in blocks:
    src = C / f"{block['clip']}.mp4"
    seg = CS / f"{block['key']}.mp4"
    run(
        [
            "ffmpeg", "-v", "error", "-ss", str(block["mseek"]), "-i", str(src), "-t", str(block["seg_dur"]),
            "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
            "-c:a", "aac", "-b:a", "192k", str(seg), "-y",
        ]
    )
    narr_end_local = q(LEAD + block["voice_dur"])
    full_start_local = block["full_start_local"]
    env = envelope(narr_end_local, full_start_local)
    out = f"seg_{block['key']}.wav"
    run(
        [
            "ffmpeg", "-v", "error",
            "-i", str(seg),
            "-i", str(A / f"{block['key']}.wav"),
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume={VOICE_GAIN}[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{block['seg_dur']},volume='{env}':eval=frame[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{block['seg_dur']},alimiter=limit=0.95[out]",
            "-map", "[out]", "-ac", "2", "-ar", "48000", out, "-y",
        ]
    )
    segments.append(out)

outro_dur = q(total - outro_start)
cta_local = q(cta_voice - outro_start)
outro_src = C / "vert_p1_xinqing.mp4"
run(
    [
        "ffmpeg", "-v", "error", "-ss", "177.5", "-i", str(outro_src), "-t", str(outro_dur),
        "-c:v", "libx264", "-preset", "veryfast", "-r", "30", "-g", "30", "-keyint_min", "30",
        "-an", str(CS / "outro.mp4"), "-y",
    ]
)
run(
    [
        "ffmpeg", "-v", "error",
        "-ss", "177.5", "-i", str(outro_src),
        "-i", str(A / "outro.wav"),
        "-i", str(A / "outro_cta.wav"),
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
        f"[vo][vc]amix=inputs=2:normalize=0,volume={VOICE_GAIN}[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.0:LRA=11,atrim=0:{outro_dur},volume=0.16,afade=t=in:st=0:d=0.8,afade=t=out:st={q(outro_dur-1.8)}:d=1.8[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_dur},alimiter=limit=0.95[out]",
        "-map", "[out]", "-ac", "2", "-ar", "48000", "seg_outro.wav", "-y",
    ]
)
segments.append("seg_outro.wav")

(ROOT / "seglist.txt").write_text("".join(f"file '{name}'\n" for name in segments), encoding="utf-8")
run(
    [
        "ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", "seglist.txt",
        "-af", f"volume={MASTER_GAIN},alimiter=limit=0.97",
        "-ac", "2", "-ar", "48000", "master.wav", "-y",
    ]
)
print("master dur:", dur(ROOT / "master.wav"), "planned:", total)


def video_tag(idx, start, duration, src):
    track = 0 if idx % 2 == 0 else 6
    return (
        f'<video id="v{idx}" class="clip fv" data-start="{q(start)}" data-duration="{q(duration)}" '
        f'data-track-index="{track}" src="{src}" muted playsinline></video>'
    )


videos = [video_tag(0, 0, intro_end, "clips_seg/intro.mp4")]
for idx, block in enumerate(blocks, start=1):
    videos.append(video_tag(idx, block["start"], block["seg_dur"], f"clips_seg/{block['key']}.mp4"))
videos.append(video_tag(len(videos), outro_start, outro_dur, "clips_seg/outro.mp4"))

labels = []
tweens = []
for idx, block in enumerate(blocks):
    fid = f"full{idx}"
    mid = f"mini{idx}"
    fdur = q(block["full_start"] - block["start"])
    mdur = q(block["end"] - block["full_start"])
    top = " topRank" if block["no"] == "01" else ""
    labels.append(
        f'<section id="{fid}" class="clip fullLabel{top}" data-start="{block["start"]}" data-duration="{fdur}" data-track-index="2">'
        f'<div class="rank">第 {block["no"]} 名</div><div class="meta">{block["meta"]}</div><h2>{block["name"]}</h2>'
        f'<p class="tag">{block["tag"]}</p><p class="note">{block["note"]}</p></section>'
    )
    labels.append(
        f'<section id="{mid}" class="clip miniLabel{top}" data-start="{block["full_start"]}" data-duration="{mdur}" data-track-index="4">'
        f'<span>{block["no"]}</span><strong>{block["plain"]}</strong></section>'
    )
    s = block["start"]
    fs = block["full_start"]
    e = block["end"]
    tweens.append(f'tl.fromTo("#{fid} .rank",{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"power2.out"}},{q(s+.18)});')
    tweens.append(f'tl.fromTo("#{fid} .meta",{{x:-22,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"sine.out"}},{q(s+.34)});')
    tweens.append(f'tl.fromTo("#{fid} h2",{{y:46,opacity:0}},{{y:0,opacity:1,duration:.64,ease:"power3.out"}},{q(s+.5)});')
    tweens.append(f'tl.fromTo("#{fid} .tag",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:"power1.out"}},{q(s+.86)});')
    tweens.append(f'tl.fromTo("#{fid} .note",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.44,ease:"power2.out"}},{q(s+1.12)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(fs-.4)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{q(fs)});')
    tweens.append(f'tl.fromTo("#{mid}",{{x:-28,opacity:0}},{{x:0,opacity:1,duration:.46,ease:"power2.out"}},{q(fs+.1)});')
    tweens.append(f'tl.to("#{mid}",{{opacity:0,duration:.35,ease:"power1.in"}},{q(e-.35)});')
    tweens.append(f'tl.set("#{mid}",{{opacity:0}},{q(e)});')

transition_divs = []
transition_tweens = []
for i, block in enumerate(blocks):
    tid = f"tr{i}"
    ts = q(max(0, block["start"] - 0.15))
    transition_divs.append(
        f'<div id="{tid}" class="clip trans" data-start="{ts}" data-duration="0.9" data-track-index="8"></div>'
    )
    transition_tweens.append(f'tl.fromTo("#{tid}",{{opacity:.58,scaleY:.05}},{{opacity:0,scaleY:1,duration:.75,ease:"power2.out"}},{ts});')

ranking_rows = "".join(
    f'<li><span>{n}</span><strong>{name}</strong></li>'
    for n, name in [
        ("05", "空出来的时间刚好拿来寂寞"),
        ("04", "你应该飞的"),
        ("03", "说谎"),
        ("02", "下一个永远"),
        ("01", "心情卡片"),
    ]
)

css = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#07101a;
  font-family:"Noto Sans SC","PingFang SC",system-ui,sans-serif;color:#f5f1e8;-webkit-font-smoothing:antialiased}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#07101a}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(5,12,22,.84),rgba(5,12,22,.12) 31%,rgba(5,12,22,.20) 58%,rgba(5,9,16,.88))}
#aurora{position:absolute;inset:-260px;z-index:1;opacity:.38;background:radial-gradient(48% 30% at 22% 20%,rgba(145,201,195,.42),rgba(145,201,195,0) 64%),radial-gradient(54% 32% at 80% 78%,rgba(232,199,126,.26),rgba(232,199,126,0) 66%)}
#grain{position:absolute;inset:-20px;z-index:9;opacity:.08;mix-blend-mode:soft-light;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(245,241,232,.13) 0 1px,transparent 1px 4px)}
.trans{position:absolute;left:0;right:0;top:0;bottom:0;z-index:8;background:linear-gradient(90deg,rgba(232,199,126,0),rgba(232,199,126,.72),rgba(145,201,195,0));transform-origin:center}
#cover{position:absolute;inset:0;z-index:5;padding:132px 78px 132px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(180deg,rgba(5,12,22,.78),rgba(5,12,22,.18) 34%,rgba(5,12,22,.18) 60%,rgba(5,10,18,.88))}
.eyebrow{display:inline-flex;align-items:center;gap:18px;font-size:30px;font-weight:900;color:#91c9c3;letter-spacing:.12em}
.eyebrow:before{content:"";width:58px;height:4px;background:#91c9c3;border-radius:99px;box-shadow:0 0 18px rgba(145,201,195,.65)}
#cover h1{margin-top:30px;font-family:"Noto Serif SC",serif;font-size:112px;line-height:1.1;font-weight:900;max-width:940px;text-shadow:0 6px 42px rgba(0,0,0,.62)}
#cover h1 b{color:#e8c77e;font-weight:900}
#cover .sub{margin-top:30px;font-size:37px;line-height:1.52;color:#d7dce5;font-weight:600;max-width:900px}
.chips{display:flex;flex-wrap:wrap;gap:14px;max-width:930px}
.chips span{border:1.5px solid rgba(145,201,195,.52);color:#dbeeed;background:rgba(5,12,22,.54);font-size:28px;font-weight:800;padding:12px 20px;border-radius:8px}
.fullLabel{position:absolute;z-index:5;left:70px;right:70px;bottom:190px;padding:34px 36px 38px;background:linear-gradient(135deg,rgba(5,12,22,.88),rgba(5,12,22,.50));border-left:8px solid #91c9c3;border-radius:5px;backdrop-filter:blur(2px);box-shadow:0 22px 70px rgba(0,0,0,.24)}
.fullLabel .rank{font-size:31px;font-weight:900;color:#91c9c3;letter-spacing:.14em}
.fullLabel .meta{margin-top:14px;font-size:28px;font-weight:700;color:#bac9d7;letter-spacing:.08em}
.fullLabel h2{font-family:"Noto Serif SC",serif;margin-top:12px;font-size:76px;line-height:1.12;font-weight:900;color:#fff}
#full0 h2{font-size:58px}
.fullLabel .tag{margin-top:19px;font-size:40px;line-height:1.28;font-weight:900;color:#e8c77e}
.fullLabel .note{margin-top:12px;font-size:30px;line-height:1.42;font-weight:600;color:#d1d8e3}
.fullLabel.topRank{border-left-color:#e8c77e;background:linear-gradient(135deg,rgba(12,10,18,.90),rgba(8,12,22,.52))}
.fullLabel.topRank .rank,.fullLabel.topRank .tag{color:#e8c77e}
.miniLabel{position:absolute;z-index:5;top:92px;left:58px;display:flex;align-items:center;gap:16px;padding:13px 21px;background:rgba(5,12,22,.68);border:1.5px solid rgba(145,201,195,.56);border-radius:8px}
.miniLabel span{font-size:44px;font-weight:900;color:#91c9c3}
.miniLabel strong{font-family:"Noto Serif SC",serif;font-size:36px;font-weight:900;max-width:800px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.miniLabel.topRank{border-color:rgba(232,199,126,.76)}
.miniLabel.topRank span{color:#e8c77e}
#outro{position:absolute;z-index:5;inset:0;padding:118px 72px 160px;display:flex;flex-direction:column;justify-content:center;background:linear-gradient(180deg,rgba(5,12,22,.32),rgba(5,12,22,.82))}
#outro .small{font-size:31px;font-weight:900;color:#91c9c3;letter-spacing:.14em}
#outro h2{font-family:"Noto Serif SC",serif;margin-top:20px;font-size:62px;line-height:1.22;font-weight:900;max-width:925px}
#outro ol{margin-top:40px;list-style:none;display:grid;gap:13px;width:100%}
#outro li{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 22px;background:rgba(5,12,22,.62);border:1px solid rgba(245,241,232,.13);border-radius:8px}
#outro li span{font-size:32px;font-weight:900;color:#91c9c3}
#outro li:last-child{background:rgba(232,199,126,.13);border-color:rgba(232,199,126,.42)}
#outro li:last-child span{color:#e8c77e}
#outro li strong{font-family:"Noto Serif SC",serif;font-size:34px;font-weight:900;text-align:right}
#outro .close{margin-top:32px;font-size:30px;line-height:1.52;color:#d7dce5;font-weight:600}
#cta{position:absolute;z-index:6;left:72px;right:72px;bottom:92px;text-align:center;padding:20px 20px;background:rgba(5,12,22,.68);border:1.5px solid rgba(232,199,126,.40);border-radius:9px}
#cta .v{font-size:42px;font-weight:900;color:#e8c77e;line-height:1.22}
#cta .f{margin-top:14px;font-size:33px;font-weight:900;color:#91c9c3;letter-spacing:.14em}
"""

body = "\n".join(videos)
body += f'\n<div id="scrim" class="clip" data-start="0" data-duration="{total}" data-track-index="1"></div>'
body += f'\n<div id="aurora" class="clip" data-start="0" data-duration="{total}" data-track-index="7"></div>'
body += f'\n<div id="grain" class="clip" data-start="0" data-duration="{total}" data-track-index="10"></div>'
body += "\n" + "\n".join(transition_divs)
body += (
    f'\n<section id="cover" class="clip" data-start="0" data-duration="{q(intro_end-.12)}" data-track-index="2">'
    '<div><div class="eyebrow">华语遗珠 · 都市情歌</div><h1>张信哲<br><b>最被低估</b>的5首歌</h1>'
    '<p class="sub">不是那些被反复点名的全民金曲，而是藏在专辑角落里，越听越能听见阿哲另一面的歌。</p></div>'
    '<div class="chips"><span>Sony 都市感</span><span>专辑遗珠</span><span>真爱粉向</span><span>清新高音</span><span>体面告别</span></div></section>'
)
body += "\n" + "\n".join(labels)
body += (
    f'\n<section id="outro" class="clip" data-start="{outro_start}" data-duration="{q(total-outro_start)}" data-track-index="2">'
    '<div class="small">最终榜单</div><h2>张信哲最动人的，不只是高音和金曲，而是这些被大歌挡住的角落里，也有完整的城市、告别和温柔。</h2>'
    f'<ol>{ranking_rows}</ol><p class="close">从第五到第一：空出来的时间刚好拿来寂寞、你应该飞的、说谎、下一个永远、心情卡片。</p></section>'
)
body += (
    f'\n<section id="cta" class="clip" data-start="{q(cta_voice-0.15)}" data-duration="{q(total-cta_voice+0.15)}" data-track-index="5">'
    '<div class="v">为你的第一名，评论区投票</div><div class="f">点赞 · 收藏 · 关注</div></section>'
)
body += f'\n<audio id="master" class="clip" data-start="0" data-duration="{total}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.set("#cover .eyebrow, #cover h1, #cover .sub, #cover .chips span",{{opacity:1,x:0,y:0}},0);
tl.fromTo("#cover h1",{{scale:1.0}},{{scale:1.018,duration:3.2,ease:"sine.inOut",yoyo:true,repeat:1}},0.25);
tl.fromTo("#aurora",{{x:-18,y:0}},{{x:20,y:-14,duration:{total},ease:"none"}},0);
tl.to("#cover",{{opacity:0,duration:.42,ease:"power1.in"}},{q(intro_end-.5)});
tl.set("#cover",{{opacity:0}},{q(intro_end)});
{chr(10).join(transition_tweens)}
{chr(10).join(tweens)}
tl.fromTo("#outro .small",{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power2.out"}},{q(outro_start+.2)});
tl.fromTo("#outro h2",{{y:40,opacity:0}},{{y:0,opacity:1,duration:.65,ease:"power3.out"}},{q(outro_start+.55)});
tl.fromTo("#outro li",{{x:-34,opacity:0}},{{x:0,opacity:1,duration:.45,ease:"power2.out",stagger:.1}},{q(outro_start+1.18)});
tl.fromTo("#outro .close",{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:"sine.out"}},{q(outro_start+2.18)});
tl.fromTo("#cta .v",{{y:26,opacity:0}},{{y:0,opacity:1,duration:.55,ease:"power2.out"}},{q(cta_voice)});
tl.fromTo("#cta .f",{{y:18,opacity:0}},{{y:0,opacity:1,duration:.5,ease:"power1.out"}},{q(cta_voice+.35)});
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
(ROOT / "meta.json").write_text(json.dumps({"id": "main", "name": "zhangxinzhe-underrated-top5"}, ensure_ascii=False), encoding="utf-8")
print("TOTAL:", total, "intro_end:", intro_end, "outro_start:", outro_start)
print("blocks:", [(b["no"], b["plain"], b["start"], b["full_start"], b["end"], b["mseek"]) for b in blocks])
