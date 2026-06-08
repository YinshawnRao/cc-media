#!/usr/bin/env python3
"""完整片：杜德伟最难的5首歌 / 倒数 05→01。
风格：夜色 R&B，黑金 + 品红 + 青绿；竖屏 1080x1920；女声旁白。
片头只做封面和作品描述，不列榜单；片尾完整回顾用户给定排名。
运行位置：sandbox/dudewei-hardest/
"""
import subprocess
import wave
import contextlib
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
SHOW_REG = 28.0
SHOW_LAST = 34.0
BED_I = 0.07
BED_N = 0.20
MASTER_GAIN = 1.35
MGAIN = {
    "p5_zhongai": 0.82,
    "p4_chonghuai": 0.79,
    "p3_qingren": 0.83,
    "p2_wuxin": 0.75,
    "p1_nozou": 0.98,
}

d_intro = dur(f"{A}/intro.wav")
d_out = dur(f"{A}/outro.wav")
INTRO_END = round(LEAD + d_intro + 1.4, 3)

songs = [
    (
        "p5_zhongai",
        "vert_zhongai",
        "05",
        "《钟爱一生》",
        "传统情歌 · 大线条",
        ["长句气息", "高位支撑", "情绪完整度"],
        "宽旋律要铺开，<b>声音不能虚也不能硬</b>",
        SHOW_REG,
    ),
    (
        "p4_chonghuai",
        "vert_chonghuai",
        "04",
        "《把你宠坏》",
        "快歌 · R&B律动",
        ["歌词密度", "节奏弹性", "轻松感"],
        "听起来潇洒，<b>身体一直高速运转</b>",
        SHOW_REG,
    ),
    (
        "p3_qingren",
        "vert_qingren_clean",
        "03",
        "《情人》",
        "音色 · 呼吸感",
        ["贴声", "暖声线", "高级感"],
        "深情不能油，<b>稳里还要有呼吸</b>",
        SHOW_REG,
    ),
    (
        "p2_wuxin",
        "vert_wuxin",
        "02",
        "《无心伤害》",
        "R&B语感 · 情绪拉扯",
        ["滑音转音", "真假声边缘", "节奏弹性"],
        "苦情不够，<b>还要松弛、性感和克制</b>",
        SHOW_REG,
    ),
    (
        "p1_nozou",
        "vert_nozou",
        "01",
        "《不走》",
        "压轴 · 高位长线",
        ["持续高位", "厚度", "尾音控制"],
        "不能只靠喊，<b>越到后面越要稳住</b>",
        SHOW_LAST,
    ),
]

recap = [
    ("05", "《钟爱一生》"),
    ("04", "《把你宠坏》"),
    ("03", "《情人》"),
    ("02", "《无心伤害》"),
    ("01", "《不走》"),
]

# ---------- 时间轴 ----------
blocks = []
t = INTRO_END
for key, clip, no, name, meta, tags, tagline, show in songs:
    dk = dur(f"{A}/{key}.wav")
    L = round(LEAD + dk + 0.2 + DIG + show, 3)
    ns = round(t + LEAD, 3)
    ne = round(ns + dk, 3)
    full = round(ne + 0.2 + DIG, 3)
    end = round(t + L, 3)
    blocks.append(
        dict(
            key=key,
            clip=clip,
            no=no,
            name=name,
            meta=meta,
            tags=tags,
            tagline=tagline,
            show=show,
            start=t,
            L=L,
            ns=ns,
            ne=ne,
            full=full,
            end=end,
        )
    )
    t = end

F_start = t
F_voice = round(F_start + LEAD, 3)
F_voice_end = round(F_voice + d_out, 3)
F_end = round(F_voice_end + 3.2, 3)
TOTAL = round(F_end + 0.4, 3)

# ---------- 音频预混 ----------
def env_song(ne_loc, full_loc):
    sw = round(ne_loc, 3)
    return (
        f"(lt(t,0.8))*({BED_N}*t/0.8)"
        f"+(between(t,0.8,{sw}))*{BED_N}"
        f"+(between(t,{sw},{full_loc}))*({BED_N}+{1.0-BED_N}*(t-{sw})/{DIG})"
        f"+(gte(t,{full_loc}))*1.0"
    )


segs = []
ve_intro = f"(lt(t,3.2))*0+(between(t,3.2,4.2))*({BED_I}*(t-3.2)/1.0)+(gte(t,4.2))*{BED_I}"
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_nozou.mp4",
        "-i",
        f"{A}/intro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{INTRO_END},volume='{ve_intro}':eval=frame[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{INTRO_END},alimiter=limit=0.95[out]",
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
    dk = dur(f"{A}/{b['key']}.wav")
    ne_loc = round(LEAD + dk, 3)
    full_loc = round(b["full"] - b["start"], 3)
    ve = env_song(ne_loc, full_loc)
    mg = MGAIN.get(b["key"], 1.0)
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
            f"atrim=0:{b['L']},volume='{ve}':eval=frame,volume={mg}[music];"
            f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{b['L']},alimiter=limit=0.95[out]",
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

segF_dur = round(F_end - F_start, 3)
run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        f"{C}/vert_nozou.mp4",
        "-i",
        f"{A}/outro.wav",
        "-filter_complex",
        f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
        f"atrim=0:{segF_dur},volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-2.6}:d=2.6[music];"
        f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
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
print("master dur:", dur("master.wav"), "/ TOTAL:", TOTAL)

# ---------- HTML ----------
COVER_END = 4.6
HOOK_IN = 4.8
HOOK_OUT = round(INTRO_END - 4.8, 2)
BRIDGE_IN = round(INTRO_END - 4.4, 2)
BRIDGE_OUT = round(INTRO_END - 0.35, 2)

fc = [("vert_nozou", 0.0, INTRO_END)]
for b in blocks:
    fc.append((b["clip"], b["start"], b["L"]))
fc.append(("vert_nozou", F_start, round(F_end - F_start, 3)))
vids = "\n".join(
    f'<video id="v{i}" class="clip fv" data-start="{round(s,3)}" data-duration="{round(dv,3)}" '
    f'data-track-index="{0 if i % 2 == 0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
    for i, (src, s, dv) in enumerate(fc)
)

labels = []
tweens = []
for b in blocks:
    no = b["no"]
    fid = f"lf{no}"
    mid = f"lm{no}"
    lf_start = round(b["start"] + 0.2, 3)
    lf_dur = round(b["full"] - lf_start, 3)
    lm_start = b["full"]
    lm_dur = round(b["end"] - b["full"], 3)
    climax = " climax" if no == "01" else ""
    crown = '<div class="crown">压轴最难</div>' if no == "01" else '<div class="lab">最难 TOP 5</div>'
    tagchips = "".join(f"<span>{x}</span>" for x in b["tags"])
    labels.append(
        f'<div id="{fid}" class="clip labelFull{climax}" data-start="{lf_start}" data-duration="{lf_dur}" data-track-index="2">'
        f'<div class="rank"><div class="no">{no}</div>{crown}</div>'
        f'<div class="meta">{b["meta"]}</div>'
        f'<div class="song">{b["name"]}</div>'
        f'<div class="tags">{tagchips}</div>'
        f'<div class="tag">{b["tagline"]}</div></div>'
    )
    labels.append(
        f'<div id="{mid}" class="clip labelMin{climax}" data-start="{lm_start}" data-duration="{lm_dur}" data-track-index="4">'
        f'<span class="no">{no}</span><span class="song">{b["name"]}</span></div>'
    )
    tweens.extend(
        [
            f'tl.from("#{fid} .no",{{y:60,opacity:0,duration:.7,ease:"power3.out"}},{round(lf_start+0.1,3)});',
            f'tl.from("#{fid} .rank>div:last-child",{{x:-24,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+0.36,3)});',
            f'tl.from("#{fid} .meta",{{x:-18,opacity:0,duration:.45,ease:"power2.out"}},{round(lf_start+0.5,3)});',
            f'tl.from("#{fid} .song",{{y:44,opacity:0,duration:.62,ease:"power3.out"}},{round(lf_start+0.64,3)});',
            f'tl.from("#{fid} .tags span",{{y:18,opacity:0,duration:.45,ease:"power2.out",stagger:.1}},{round(lf_start+0.96,3)});',
            f'tl.from("#{fid} .tag",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+1.34,3)});',
            f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["full"]-0.4,3)});',
            f'tl.set("#{fid}",{{opacity:0}},{b["full"]});',
            f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{round(lm_start+0.1,3)});',
            f'tl.to("#{mid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(b["end"]-0.35,3)});',
            f'tl.set("#{mid}",{{opacity:0}},{round(b["end"],3)});',
        ]
    )

recap_rows = "".join(
    f'<li class="{"top" if no == "01" else ""}"><span class="rn">{no}</span><span class="rs">{nm}</span></li>'
    for no, nm in recap
)

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#08080d;font-family:"Noto Sans SC",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(5,5,10,.78),rgba(5,5,10,.16) 32%,rgba(8,7,12,.28) 58%,rgba(5,5,9,.9))}
#vig{position:absolute;inset:0;z-index:1;background:radial-gradient(120% 78% at 50% 38%,rgba(0,0,0,0) 40%,rgba(0,0,0,.62) 100%)}
#tint{position:absolute;inset:0;z-index:1;background:linear-gradient(135deg,rgba(255,52,120,.12),rgba(25,212,198,.08) 48%,rgba(226,181,93,.10));mix-blend-mode:screen}
#grain{position:absolute;inset:0;z-index:8;opacity:.055;mix-blend-mode:soft-light;pointer-events:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='280' height='280'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch' seed='19'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");background-size:280px 280px}
#cover{position:absolute;left:78px;right:78px;bottom:230px;z-index:6;color:#f7efe4}
#cover .kick{display:inline-flex;align-items:center;gap:14px;padding:12px 26px;border:2px solid rgba(226,181,93,.58);border-radius:999px;font-size:28px;font-weight:800;color:#e2b55d;background:rgba(8,8,13,.34)}
#cover .kick::before{content:"";width:13px;height:13px;border-radius:50%;background:#19d4c6;box-shadow:0 0 18px #19d4c6}
#cover .name{margin-top:26px;font-size:72px;font-weight:900;color:#fff}
#cover .title{margin-top:4px;font-size:164px;font-weight:900;line-height:.96;font-family:"Noto Serif SC",serif;background:linear-gradient(105deg,#fff2cb,#e2b55d 42%,#ff3478 88%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 10px 42px rgba(255,52,120,.28))}
#cover .sub{margin-top:24px;font-size:40px;font-weight:700;line-height:1.35;color:#efe5d8}
#cover .sub b{color:#19d4c6}
.k{display:inline-flex;align-items:center;gap:16px;font-size:30px;font-weight:800;color:#e2b55d}
.k::before{content:"";width:52px;height:4px;background:linear-gradient(90deg,#e2b55d,#ff3478,#19d4c6);border-radius:2px}
#hooks{position:absolute;top:310px;left:78px;right:78px;z-index:5;color:#f7efe4}
#hooks ul{list-style:none;margin-top:42px}
#hooks li{font-size:75px;font-weight:900;line-height:1.32;padding-left:38px;position:relative;color:rgba(255,255,255,.95)}
#hooks li::before{content:"";position:absolute;left:0;top:.31em;width:8px;height:.72em;background:#ff3478;border-radius:3px;box-shadow:0 0 14px rgba(255,52,120,.65)}
#hooks .note{margin-top:32px;font-size:34px;font-weight:700;color:#b7b0aa}
#hooks .note b{color:#e2b55d}
#bridge{position:absolute;left:78px;right:78px;top:50%;transform:translateY(-50%);z-index:5;color:#f7efe4;text-align:center}
#bridge .big{font-size:214px;font-weight:900;line-height:.92;font-family:"JetBrains Mono",monospace;background:linear-gradient(180deg,#fff2cb,#e2b55d 48%,#19d4c6);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 0 44px rgba(226,181,93,.35))}
#bridge .big small{display:block;margin-bottom:10px;font-size:52px;font-weight:800;color:#e2b55d;font-family:"Noto Sans SC",sans-serif;-webkit-text-fill-color:#e2b55d}
#bridge .line{margin-top:28px;font-size:46px;font-weight:900;color:#fff}
#bridge .line b{color:#19d4c6}
.labelFull{position:absolute;left:78px;right:78px;bottom:300px;z-index:5;color:#f7efe4}
.labelFull .rank{display:flex;align-items:flex-end;gap:24px}
.labelFull .rank .lab{font-size:33px;font-weight:800;color:#e2b55d;padding-bottom:30px}
.labelFull .rank .crown{font-size:34px;font-weight:900;color:#13070b;background:linear-gradient(180deg,#ff7aa6,#ff3478);border-radius:9px;padding:9px 22px;margin-bottom:34px;box-shadow:0 0 34px rgba(255,52,120,.56)}
.labelFull .no{font-size:194px;font-weight:800;line-height:.78;font-family:"JetBrains Mono",monospace;background:linear-gradient(180deg,#fff2cb,#e2b55d);-webkit-background-clip:text;background-clip:text;color:transparent}
.labelFull.climax .no{background:linear-gradient(180deg,#fff2cb,#ff3478 56%,#19d4c6);-webkit-background-clip:text;background-clip:text;color:transparent}
.labelFull .meta{margin-top:14px;font-size:30px;font-weight:700;color:#b7b0aa;font-family:"JetBrains Mono",monospace}
.labelFull .song{font-size:88px;font-weight:900;margin-top:6px;color:#fff;font-family:"Noto Serif SC",serif}
.labelFull .tags{margin-top:24px;display:flex;flex-wrap:wrap;gap:14px}
.labelFull .tags span{font-size:30px;font-weight:700;color:#98eee7;border:1.5px solid rgba(25,212,198,.5);border-radius:999px;padding:9px 22px;background:rgba(25,212,198,.07)}
.labelFull .tag{font-size:43px;font-weight:700;color:#efe5d8;margin-top:26px;line-height:1.3}
.labelFull .tag b{color:#e2b55d;font-weight:900}
.labelFull.climax .tag b{color:#ff7aa6}
.labelMin{position:absolute;top:118px;left:74px;z-index:5;color:#f7efe4;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:62px;font-weight:800;color:#e2b55d;font-family:"JetBrains Mono",monospace}
.labelMin.climax .no{color:#ff3478}
.labelMin .song{font-size:50px;font-weight:800;font-family:"Noto Serif SC",serif}
#outro{position:absolute;left:70px;right:70px;top:252px;z-index:5;color:#f7efe4;padding:46px 48px;border-radius:26px;border:1px solid rgba(226,181,93,.18);background:linear-gradient(180deg,rgba(8,8,13,.54),rgba(8,8,13,.86));box-shadow:0 24px 80px rgba(0,0,0,.5)}
#outro .o2{font-size:70px;font-weight:900;line-height:1.1;font-family:"Noto Serif SC",serif;background:linear-gradient(104deg,#fff2cb,#e2b55d 46%,#ff3478);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .recap-t{margin-top:38px;font-size:30px;font-weight:800;color:#b7b0aa}
#outro .recap{list-style:none;margin-top:20px}
#outro .recap li{display:flex;align-items:baseline;gap:24px;padding:12px 0;border-bottom:1px solid rgba(226,181,93,.15)}
#outro .recap li .rn{font-size:46px;font-weight:800;font-family:"JetBrains Mono",monospace;color:#e2b55d;min-width:76px}
#outro .recap li .rs{font-size:49px;font-weight:800;font-family:"Noto Serif SC",serif;color:#f7efe4}
#outro .recap li.top{border-bottom:none}
#outro .recap li.top .rn{color:#ff3478}
#outro .recap li.top .rs{background:linear-gradient(100deg,#fff2cb,#ff3478 60%,#19d4c6);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .q{margin-top:32px;font-size:40px;font-weight:700;color:#efe5d8;line-height:1.35}
#outro .q b{color:#19d4c6}
#outro .bar{width:140px;height:8px;background:linear-gradient(90deg,#e2b55d,#ff3478,#19d4c6);margin-top:22px;border-radius:4px}
"""

body = f"""{vids}
<div id="scrim" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1"></div>
<div id="tint" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8"></div>
<div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="7"></div>
<div id="grain" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9"></div>
<div id="cover" class="clip" data-start="0" data-duration="{COVER_END}" data-track-index="5">
  <div class="kick">唱功盘点 · R&B情歌</div>
  <div class="name">杜德伟</div>
  <div class="title">最难的5首歌</div>
  <div class="sub">不是只会有型，<b>更难的是松弛里的控制</b></div>
</div>
<div id="hooks" class="clip" data-start="{HOOK_IN}" data-duration="{round(HOOK_OUT-HOOK_IN,2)}" data-track-index="2">
  <div class="k">难点不只高音</div>
  <ul><li>气息要厚</li><li>律动要准</li><li>情绪要克制</li></ul>
  <div class="note">R&B语感、情歌线条和舞台张力，<b>缺一块都不像他</b></div>
</div>
<div id="bridge" class="clip" data-start="{BRIDGE_IN}" data-duration="{round(BRIDGE_OUT-BRIDGE_IN,2)}" data-track-index="5">
  <div class="big"><small>从第五名开始</small>TOP 5</div>
  <div class="line">厚度 · 律动 · <b>高级感</b></div>
</div>
{chr(10).join(labels)}
<div id="outro" class="clip" data-start="{round(F_voice+0.2,3)}" data-duration="{round(F_end-F_voice-0.2+0.4,3)}" data-track-index="4">
  <div class="o2">杜德伟最难的地方，<br>是把控制唱得像本能</div>
  <div class="recap-t">完整榜单回顾</div>
  <ul class="recap">{recap_rows}</ul>
  <div class="q">这五首里，你觉得最难复刻的是<b>哪一首？</b></div>
  <div class="bar"></div>
</div>
<audio id="master" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>"""

js = f"""
tl.set("#cover",{{opacity:1}},0);
tl.from("#cover .kick",{{y:18,opacity:0,duration:.5,ease:"power2.out"}},.2);
tl.from("#cover .name",{{y:30,opacity:0,duration:.55,ease:"power2.out"}},.55);
tl.from("#cover .title",{{y:64,opacity:0,scale:1.04,duration:.75,ease:"power4.out"}},.85);
tl.from("#cover .sub",{{y:22,opacity:0,duration:.5,ease:"power2.out"}},1.35);
tl.to("#cover",{{y:-28,opacity:0,duration:.5,ease:"power2.in"}},{round(COVER_END-.55,2)});
tl.set("#cover",{{opacity:0}},{COVER_END});
tl.from("#hooks .k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{HOOK_IN+.1});
tl.from("#hooks li",{{x:-44,opacity:0,duration:.55,ease:"power3.out",stagger:.32}},{HOOK_IN+.35});
tl.from("#hooks .note",{{opacity:0,y:18,duration:.5}},{HOOK_IN+2.0});
tl.to("#hooks",{{opacity:0,duration:.4,ease:"power1.in"}},{round(HOOK_OUT-.45,2)});
tl.set("#hooks",{{opacity:0}},{HOOK_OUT});
tl.from("#bridge .big small",{{opacity:0,y:14,duration:.4}},{BRIDGE_IN+.1});
tl.from("#bridge .big",{{scale:.72,opacity:0,duration:.62,ease:"back.out(1.4)"}},{BRIDGE_IN+.2});
tl.from("#bridge .line",{{y:24,opacity:0,duration:.5,ease:"power3.out"}},{BRIDGE_IN+.82});
tl.to("#bridge",{{opacity:0,duration:.4,ease:"power1.in"}},{round(BRIDGE_OUT-.45,2)});
tl.set("#bridge",{{opacity:0}},{BRIDGE_OUT});
{chr(10).join(tweens)}
tl.from("#outro",{{y:40,opacity:0,duration:.7,ease:"power3.out"}},{round(F_voice+.25,3)});
tl.from("#outro .o2",{{y:28,opacity:0,duration:.65,ease:"power2.out"}},{round(F_voice+.45,3)});
tl.from("#outro .recap-t",{{opacity:0,y:14,duration:.45}},{round(F_voice+1.15,3)});
tl.from("#outro .recap li",{{x:-24,opacity:0,duration:.42,ease:"power2.out",stagger:.16}},{round(F_voice+1.45,3)});
tl.from("#outro .q",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{round(F_voice+2.55,3)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{round(F_voice+2.9,3)});
"""

html = f"""<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700;900&family=Noto+Sans+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{body}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{js}
window.__timelines["main"]=tl;
</script></body></html>"""

Path("index.html").write_text(html, encoding="utf-8")
Path("meta.json").write_text('{"id":"main","name":"dudewei-hardest"}', encoding="utf-8")
print("TOTAL:", TOTAL, "blocks:", [(b["no"], b["name"], b["start"], b["end"]) for b in blocks])
