#!/usr/bin/env python3
"""完整片：裘德最难的5首歌 / 倒数 05 -> 01。

结构：封面 + intro 钩子 -> 5 首转场口播 + 连续展示段 -> outro + 固定 CTA。
音频：逐段 loudnorm + 旁白 ducking + 预混 master.wav，render 后必须 mux 覆盖。
"""
import contextlib
import json
import subprocess
import wave
from pathlib import Path


def dur(wav):
    with contextlib.closing(wave.open(str(wav), "r")) as w:
        return round(w.getnframes() / w.getframerate(), 3)


def run(cmd):
    subprocess.run(cmd, check=True)


A = "audio"
C = "clips"

LEAD = 0.3
DIG = 1.4
VOICE_TO_FULL_GAP = 0.2
BED_N = 0.18
MASTER_GAIN = 1.05

d_intro = dur(f"{A}/intro.wav")
d_outro = dur(f"{A}/outro.wav")
d_cta = dur(f"{A}/outro_cta.wav")

INTRO_END = round(LEAD + d_intro + 1.6, 3)

songs = [
    (
        "p5_b_shark",
        "vert_b_shark",
        "05",
        "《B级鲨鱼》",
        "Funk / Disco / 律动",
        ["律动稳", "怪味", "幽默感"],
        "难在 <b>松而不散</b>",
        34.0,
        "#d7a84f",
    ),
    (
        "p4_semang",
        "vert_semang",
        "04",
        "《色盲》",
        "feat. 徐佳莹 / 和声",
        ["色彩感", "和声", "错位情绪"],
        "每一句都要 <b>轻巧精准</b>",
        32.0,
        "#51b9b0",
    ),
    (
        "p3_mobius",
        "vert_mobius",
        "03",
        "《莫比乌斯号的船医》",
        "Stage Video / 奇幻叙事",
        ["角色", "空间", "爵士律动"],
        "不是唱旋律，是唱 <b>一场海上电影</b>",
        35.0,
        "#5d8bd8",
    ),
    (
        "p2_aquarium",
        "vert_aquarium",
        "02",
        "《最后的水族馆》",
        "Official MV / 概念大歌",
        ["故事推进", "压迫感", "戏剧张力"],
        "别唱成参观说明，要唱成 <b>末日水族馆</b>",
        36.0,
        "#51b9b0",
    ),
    (
        "p1_lian_sheng",
        "vert_lian_sheng",
        "01",
        "《练声曲》",
        "feat. 窦靖童 / 双声部",
        ["气息控制", "音色变化", "声部配合"],
        "把复杂唱得像 <b>自然呼吸</b>",
        42.0,
        "#c94f4f",
    ),
]

blocks = []
t = INTRO_END
for key, clip, no, name, meta, tags, tagline, show, accent in songs:
    voice_d = dur(f"{A}/{key}.wav")
    length = round(LEAD + voice_d + VOICE_TO_FULL_GAP + DIG + show, 3)
    ns = round(t + LEAD, 3)
    ne = round(ns + voice_d, 3)
    full = round(ne + VOICE_TO_FULL_GAP + DIG, 3)
    end = round(t + length, 3)
    blocks.append(
        {
            "key": key,
            "clip": clip,
            "no": no,
            "name": name,
            "meta": meta,
            "tags": tags,
            "tagline": tagline,
            "accent": accent,
            "show": show,
            "start": t,
            "length": length,
            "ns": ns,
            "ne": ne,
            "full": full,
            "end": end,
        }
    )
    t = end

OUTRO_START = t
OUTRO_VOICE = round(OUTRO_START + LEAD, 3)
OUTRO_VOICE_END = round(OUTRO_VOICE + d_outro, 3)
CTA_START = round(OUTRO_VOICE_END + 0.9, 3)
CTA_END = round(CTA_START + d_cta, 3)
END = round(CTA_END + 1.5, 3)
TOTAL = round(END + 0.3, 3)


def env_for_segment(ne_loc, full_loc):
    return (
        f"(lt(t,0.8))*({BED_N}*t/0.8)"
        f"+(between(t,0.8,{ne_loc}))*{BED_N}"
        f"+(between(t,{ne_loc},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{ne_loc})/{DIG})"
        f"+(gte(t,{full_loc}))*1.0"
    )


segs = []
intro_env = (
    f"(lt(t,0.9))*(0.12*t/0.9)"
    f"+(between(t,0.9,{INTRO_END-1.5}))*0.12"
    f"+(gte(t,{INTRO_END-1.5}))*0.18"
)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_intro.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{INTRO_END},volume='{intro_env}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.96[out]",
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        "seg_intro.wav",
        "-y",
    ]
)
segs.append("seg_intro.wav")

for b in blocks:
    voice_d = dur(f"{A}/{b['key']}.wav")
    ne_loc = round(LEAD + voice_d, 3)
    full_loc = round(b["full"] - b["start"], 3)
    out = f"seg_{b['no']}.wav"
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            f"{C}/{b['clip']}.mp4",
            "-i",
            f"{A}/{b['key']}.wav",
            "-filter_complex",
            f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
            f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
            f"atrim=0:{b['length']},volume='{env_for_segment(ne_loc, full_loc)}':eval=frame[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['length']},alimiter=limit=0.96[out]",
            "-map",
            "[out]",
            "-ac",
            "2",
            "-ar",
            "48000",
            out,
            "-y",
        ]
    )
    segs.append(out)

outro_len = round(END - OUTRO_START, 3)
cta_delay = round((CTA_START - OUTRO_START) * 1000)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_lian_sheng.mp4",
        "-i",
        f"{A}/outro.wav",
        "-i",
        f"{A}/outro_cta.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[outro];"
        f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={cta_delay}|{cta_delay},volume=2.0[cta];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{outro_len},volume=0.16,afade=t=in:st=0:d=1.0,afade=t=out:st={outro_len-1.8}:d=1.8[music];"
        f"[outro][cta][music]amix=inputs=3:normalize=0:duration=longest,atrim=0:{outro_len},alimiter=limit=0.96[out]",
        "-map",
        "[out]",
        "-ac",
        "2",
        "-ar",
        "48000",
        "seg_outro.wav",
        "-y",
    ]
)
segs.append("seg_outro.wav")

Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "seglist.txt",
        "-af",
        f"volume={MASTER_GAIN},alimiter=limit=0.97",
        "-ac",
        "2",
        "-ar",
        "48000",
        "master.wav",
        "-y",
    ]
)
RENDER_TOTAL = dur("master.wav")
print("master dur:", RENDER_TOTAL, "/ planned TOTAL:", TOTAL)

Path("meta.json").write_text(
    json.dumps(
        {
            "total": RENDER_TOTAL,
            "planned_total": TOTAL,
            "intro_end": INTRO_END,
            "outro_start": OUTRO_START,
            "outro_voice": OUTRO_VOICE,
            "cta_start": CTA_START,
            "blocks": blocks,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

video_items = [("vert_intro", 0, INTRO_END)]
for b in blocks:
    video_items.append((b["clip"], b["start"], b["length"]))
video_items.append(("vert_lian_sheng", OUTRO_START, round(RENDER_TOTAL - OUTRO_START, 3)))

videos = "\n".join(
    f'<video id="v{i}" class="clip footage" data-start="{round(s,3)}" data-duration="{round(d,3)}" '
    f'data-track-index="{0 if i % 2 == 0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i, (src, s, d) in enumerate(video_items)
)

labels = []
tweens = []
for b in blocks:
    fid = f"label_{b['no']}"
    mid = f"mini_{b['no']}"
    accent_style = f' style="--accent:{b["accent"]}"'
    lf_start = round(b["start"] + 0.15, 3)
    lf_dur = round(b["full"] - lf_start, 3)
    mini_start = b["full"]
    mini_dur = round(b["end"] - b["full"] + (0.3 if b["no"] == "01" else 0), 3)
    chips = "".join(f"<span>{tag}</span>" for tag in b["tags"])
    climax = " climax" if b["no"] == "01" else ""
    labels.append(
        f'<div id="{fid}" class="clip rankCard{climax}"{accent_style} data-start="{lf_start}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rankNo">{b["no"]}</div>'
        f'<div class="rankBody"><div class="rankMeta">{b["meta"]}</div><div class="songName">{b["name"]}</div>'
        f'<div class="chipRow">{chips}</div><div class="tagline">{b["tagline"]}</div></div>'
        f"</div>"
    )
    labels.append(
        f'<div id="{mid}" class="clip miniLabel{climax}"{accent_style} data-start="{mini_start}" data-duration="{mini_dur}" data-track-index="4">'
        f'<span class="miniNo">{b["no"]}</span><span>{b["name"]}</span><i></i></div>'
    )
    tweens.extend(
        [
            f'tl.fromTo("#{fid} .rankNo",{{opacity:0,y:54,scale:.94}},{{opacity:1,y:0,scale:1,duration:.72,ease:"expo.out"}},{round(lf_start+0.12,3)});',
            f'tl.fromTo("#{fid} .rankMeta",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.48,ease:"power3.out"}},{round(lf_start+0.34,3)});',
            f'tl.fromTo("#{fid} .songName",{{opacity:0,y:36}},{{opacity:1,y:0,duration:.62,ease:"power2.out"}},{round(lf_start+0.48,3)});',
            f'tl.fromTo("#{fid} .chipRow span",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.42,ease:"back.out(1.4)",stagger:.08}},{round(lf_start+0.86,3)});',
            f'tl.fromTo("#{fid} .tagline",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.55,ease:"sine.out"}},{round(lf_start+1.18,3)});',
            f'tl.to("#{fid}",{{opacity:0,filter:"blur(14px)",duration:.44,ease:"power2.in"}},{round(b["full"]-0.46,3)});',
            f'tl.set("#{fid}",{{opacity:0}},{round(b["full"],3)});',
            f'tl.fromTo("#{mid}",{{opacity:0,x:-28}},{{opacity:1,x:0,duration:.48,ease:"power3.out"}},{round(mini_start+0.12,3)});',
            f'tl.fromTo("#{mid} i",{{scaleX:0}},{{scaleX:1,duration:{max(b["show"]-1, 1):.2f},ease:"none"}},{round(mini_start+0.4,3)});',
            f'tl.to("#{mid}",{{opacity:0,duration:.36,ease:"power1.in"}},{round(b["end"]-0.36,3)});',
            f'tl.set("#{mid}",{{opacity:0}},{round(b["end"],3)});',
        ]
    )

css = f"""
*{{box-sizing:border-box}}
@font-face{{font-family:"Noto Sans SC";src:local("Noto Sans CJK SC"),local("Noto Sans SC"),local("PingFang SC")}}
@font-face{{font-family:"Noto Serif SC";src:local("Noto Serif CJK SC"),local("Noto Serif SC"),local("Songti SC")}}
html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#080a0d;color:#f1ece4;
  font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
.footage{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}}
#scrim{{position:absolute;inset:0;z-index:1;background:
  linear-gradient(180deg,rgba(8,10,13,.72) 0%,rgba(8,10,13,.20) 28%,rgba(8,10,13,.16) 55%,rgba(8,10,13,.86) 100%)}}
#glass{{position:absolute;inset:0;z-index:1;background:
  radial-gradient(88% 54% at 50% 38%,rgba(81,185,176,.18),rgba(8,10,13,0) 62%),
  radial-gradient(72% 38% at 82% 84%,rgba(215,168,79,.14),rgba(8,10,13,0) 66%);mix-blend-mode:screen}}
#grain{{position:absolute;inset:0;z-index:9;opacity:.055;pointer-events:none;mix-blend-mode:soft-light;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch' seed='18'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}}
#cover{{position:absolute;z-index:5;left:72px;right:72px;bottom:330px;color:#f1ece4}}
.eyebrow{{display:inline-flex;align-items:center;gap:13px;font-size:28px;font-weight:800;letter-spacing:.26em;color:#d7a84f;
  border:2px solid rgba(215,168,79,.52);border-radius:999px;padding:11px 24px;background:rgba(8,10,13,.46)}}
.eyebrow::before{{content:"";width:13px;height:13px;border-radius:50%;background:#51b9b0;box-shadow:0 0 18px #51b9b0}}
.coverName{{margin-top:34px;font-size:74px;font-weight:900;letter-spacing:.16em;color:#f1ece4}}
.coverTitle{{margin-top:4px;font-family:"Noto Serif SC",serif;font-size:154px;font-weight:900;line-height:.96;letter-spacing:0;
  color:#f1ece4;text-shadow:0 20px 70px rgba(81,185,176,.28)}}
.coverTitle b{{color:#d7a84f}}
.coverSub{{margin-top:24px;font-size:40px;font-weight:700;line-height:1.34;color:#d5d0c8}}
.coverSub b{{color:#51b9b0}}
.ghost{{position:absolute;z-index:2;font-family:"JetBrains Mono",monospace;font-size:186px;font-weight:800;letter-spacing:.08em;
  color:rgba(241,236,228,.055);left:38px;top:192px;white-space:nowrap}}
#introText{{position:absolute;z-index:5;left:72px;right:72px;top:250px}}
#introText .kicker{{font-size:30px;font-weight:800;color:#51b9b0;letter-spacing:.34em}}
#introText .thesis{{margin-top:34px;font-size:58px;line-height:1.22;font-family:"Noto Serif SC",serif;font-weight:900;color:#f1ece4}}
#introText .thesis b{{color:#d7a84f}}
#introText .axis{{margin-top:38px;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
#introText .axis span{{font-family:"JetBrains Mono",monospace;font-size:27px;font-weight:800;color:#080a0d;background:#d7a84f;border-radius:6px;padding:14px 0;text-align:center}}
.rankCard{{position:absolute;z-index:5;left:70px;right:70px;bottom:248px;display:flex;gap:28px;align-items:flex-end;color:#f1ece4;--accent:#d7a84f}}
.rankNo{{font-family:"JetBrains Mono",monospace;font-size:178px;font-weight:800;line-height:.78;color:var(--accent);text-shadow:0 0 42px color-mix(in srgb,var(--accent) 45%,transparent)}}
.rankBody{{padding-bottom:8px;max-width:690px}}
.rankMeta{{font-size:26px;font-weight:800;color:#9fb0ad;letter-spacing:.18em}}
.songName{{margin-top:6px;font-family:"Noto Serif SC",serif;font-size:76px;font-weight:900;line-height:1.05;color:#fff}}
.chipRow{{margin-top:22px;display:flex;flex-wrap:wrap;gap:12px}}
.chipRow span{{font-size:28px;font-weight:800;color:#f1ece4;border:1.5px solid color-mix(in srgb,var(--accent) 70%,transparent);
  background:rgba(8,10,13,.58);border-radius:999px;padding:9px 18px}}
.tagline{{margin-top:22px;font-size:39px;font-weight:800;line-height:1.32;color:#d5d0c8}}
.tagline b{{color:var(--accent)}}
.rankCard.climax .rankNo{{color:#c94f4f;text-shadow:0 0 58px rgba(201,79,79,.62)}}
.miniLabel{{position:absolute;z-index:5;left:58px;right:58px;top:92px;height:96px;display:flex;align-items:center;gap:20px;color:#f1ece4;
  font-family:"Noto Serif SC",serif;font-size:42px;font-weight:900;--accent:#d7a84f;background:linear-gradient(90deg,rgba(8,10,13,.88),rgba(8,10,13,.18));padding:0 26px;border-left:7px solid var(--accent)}}
.miniNo{{font-family:"JetBrains Mono",monospace;color:var(--accent);font-size:54px;font-weight:800}}
.miniLabel i{{position:absolute;left:0;bottom:0;height:5px;width:100%;background:var(--accent);transform-origin:left center}}
#outro{{position:absolute;z-index:5;left:72px;right:72px;bottom:360px;color:#f1ece4}}
#outro .summary{{font-family:"Noto Serif SC",serif;font-size:68px;font-weight:900;line-height:1.18}}
#outro .summary b{{color:#d7a84f}}
#outro .small{{margin-top:24px;font-size:35px;font-weight:700;line-height:1.45;color:#d5d0c8}}
#outro .cta{{margin-top:34px;font-size:38px;font-weight:900;color:#51b9b0}}
#outro .bar{{margin-top:28px;width:168px;height:8px;border-radius:8px;background:linear-gradient(90deg,#51b9b0,#d7a84f,#c94f4f)}}
"""

body = f"""
{videos}
<div id="scrim" class="clip" data-start="0" data-duration="{RENDER_TOTAL}" data-track-index="1"></div>
<div id="glass" class="clip" data-start="0" data-duration="{RENDER_TOTAL}" data-track-index="8"></div>
<div id="grain" class="clip" data-start="0" data-duration="{RENDER_TOTAL}" data-track-index="9"></div>
<div id="ghost" class="ghost clip" data-start="0" data-duration="{RENDER_TOTAL}" data-track-index="5">JUDE</div>
<section id="cover" class="clip" data-start="0" data-duration="5.2" data-track-index="3">
  <div class="eyebrow">VOCAL DIFFICULTY</div>
  <div class="coverName">裘德</div>
  <div class="coverTitle">最难的<b>5</b>首歌</div>
  <div class="coverSub">不是只比高音，而是比 <b>角色、空间、气息和怪味</b></div>
</section>
<section id="introText" class="clip" data-start="5.1" data-duration="{round(INTRO_END-5.1,3)}" data-track-index="10">
  <div class="kicker">难点拆解</div>
  <div class="thesis">唱旋律，唱角色，唱空间。<br>还要保留那一点 <b>松弛和怪味</b>。</div>
  <div class="axis"><span>05</span><span>04</span><span>03</span><span>02</span><span>01</span></div>
</section>
{chr(10).join(labels)}
<section id="outro" class="clip" data-start="{round(OUTRO_VOICE+0.2,3)}" data-duration="{round(RENDER_TOTAL-OUTRO_VOICE,3)}" data-track-index="4">
  <div class="summary">裘德的难，<br>是把奇妙世界唱得像<b>自然发生</b>。</div>
  <div class="small">爵士、戏剧、叙事和怪诞幽默，都被压进一条很细的声线里。</div>
  <div class="cta">评论区投票 · 点赞收藏关注</div>
  <div class="bar"></div>
</section>
<audio id="master" class="clip" data-start="0" data-duration="{RENDER_TOTAL}" data-track-index="11" src="master.wav" data-volume="1"></audio>
"""

js = f"""
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.set("#cover", {{ opacity: 1 }}, 0);
tl.set("#cover > *", {{ opacity: 1 }}, 0);
tl.fromTo("#ghost", {{ x: 0, opacity: .35 }}, {{ x: -16, opacity: .7, duration: {RENDER_TOTAL}, ease: "none" }}, 0);
tl.fromTo("#cover .eyebrow", {{ scaleX: .94 }}, {{ scaleX: 1.02, duration: 2.8, yoyo: true, repeat: 1, ease: "sine.inOut" }}, .35);
tl.fromTo("#cover .coverTitle", {{ scale: 1 }}, {{ scale: 1.025, duration: 4.2, transformOrigin: "left center", ease: "sine.inOut" }}, .45);
tl.to("#cover", {{ opacity: 0, filter: "blur(14px)", duration: .58, ease: "power2.in" }}, 4.75);
tl.set("#cover", {{ opacity: 0 }}, 5.35);
tl.fromTo("#introText .kicker", {{ opacity: 0, x: -34 }}, {{ opacity: 1, x: 0, duration: .55, ease: "power3.out" }}, 5.35);
tl.fromTo("#introText .thesis", {{ opacity: 0, y: 34 }}, {{ opacity: 1, y: 0, duration: .72, ease: "expo.out" }}, 5.62);
tl.fromTo("#introText .axis span", {{ opacity: 0, y: 18 }}, {{ opacity: 1, y: 0, duration: .42, ease: "back.out(1.3)", stagger: .09 }}, 6.3);
tl.to("#introText", {{ opacity: 0, filter: "blur(12px)", duration: .46, ease: "power2.in" }}, {round(INTRO_END-0.5,3)});
tl.set("#introText", {{ opacity: 0 }}, {INTRO_END});
{chr(10).join(tweens)}
tl.fromTo("#outro .summary", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: .75, ease: "power3.out" }}, {round(OUTRO_VOICE+0.35,3)});
tl.fromTo("#outro .small", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: .58, ease: "sine.out" }}, {round(OUTRO_VOICE+0.85,3)});
tl.fromTo("#outro .cta", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: .52, ease: "power2.out" }}, {round(CTA_START+0.1,3)});
tl.fromTo("#outro .bar", {{ scaleX: 0, transformOrigin: "left center" }}, {{ scaleX: 1, duration: .8, ease: "power3.out" }}, {round(CTA_START+0.35,3)});
tl.to("#outro", {{ opacity: 0, duration: .9, ease: "sine.in" }}, {round(RENDER_TOTAL-1.05,3)});
tl.set("#outro", {{ opacity: 0 }}, {round(RENDER_TOTAL-0.05,3)});
window.__timelines["main"] = tl;
"""

html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>{css}</style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{RENDER_TOTAL}" data-width="1080" data-height="1920">
    {body}
  </div>
  <script>{js}</script>
</body>
</html>
"""

Path("index.html").write_text(html, encoding="utf-8")
print("wrote index.html TOTAL", RENDER_TOTAL)
