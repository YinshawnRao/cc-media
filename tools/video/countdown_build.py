#!/usr/bin/env python3
"""完整片构建模板（竖屏 1080x1920）：master.wav（逐段 床→swell→展示 + 旁白 + 逐首响度归一）+ index.html。

模板，非通用程序。按每条 brief 复制到项目目录后改：songs（每首 旁白key/vert片段/序号/歌名/标签）、
时长常量（SHOW/DIG/GAP_A）、MGAIN（暗调安静歌补偿）、开场 chips/title 与 outro 文案。
前置：audio/<key>.wav（narrate_segments.py）、clips/vert_<song>.mp4（vfill.sh）、
      **probe/vocal_analysis.json**（先跑 `vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json`，
      供下方展示段对齐闸门校验"副歌入点 vs 旁白收尾 / 结尾不切半句"，见 CONVENTIONS「展示段硬规则 (C)」）。
之后：npx hyperframes lint → render → ffmpeg mux master.wav（见 tools/video/README.md 第 8 步）。
"""
import subprocess, wave, contextlib
from pathlib import Path

def dur(wav):
    with contextlib.closing(wave.open(str(wav), 'r')) as w:
        return round(w.getnframes() / w.getframerate(), 3)

def run(cmd):
    subprocess.run(cmd, check=True)

A = "audio"; C = "clips"
SHOW = 19.0      # 每首副歌展示时长
DIG = 1.4        # swell 时长
BED = 0.14       # 旁白时音乐床增益
MGAIN = {"p4_quanmian": 2.2}  # 逐首额外增益（暗调安静歌补偿，统一响度）
LEAD = 0.3       # 每段旁白前导
GAP_A = 1.35     # intro 旁白后到 p1 的消化位
DIGEST_O = 1.0   # outro 升华 → 固定 CTA 的消化位（见 CONVENTIONS「固定结尾配音」）
OUTRO_TAIL = 2.6 # 固定 CTA 念完到片尾的余量（床末 1.6s fade）

# 旁白时长（outro = 作品升华；outro_cta = 固定引流 CTA，全片最后一句，禁改）
d_intro = dur(f"{A}/intro.wav")
d = {k: dur(f"{A}/{k}.wav") for k in ["p1_pandora","p2_nahan","p3_pojian","p4_quanmian","p5_adiao","outro","outro_cta"]}

songs = [
    ("p1_pandora", "vert_pandora", "01", "《潘朵拉》",  "天使嗓音，也能打开<b>暗黑魔盒</b>"),
    ("p2_nahan",   "vert_nahan",   "02", "《呐喊》",    "不是安慰，是把<b>情绪撕开</b>"),
    ("p3_pojian",  "vert_pojian",  "03", "《破茧》",    "不是飞翔，是从<b>深渊里破开</b>"),
    ("p4_quanmian","vert_quanmian","04", "《全面沦陷》","明知道危险，<b>还是往里走</b>"),
    ("p5_adiao",   "vert_adiao",   "05", "《阿刁》",    "她唱的不是励志，<b>是活下来</b>"),
]

# ---------- 计算时间轴 ----------
CUT = 3.5
intro_voice_end = LEAD + d_intro            # 7.85
p1_start = intro_voice_end + GAP_A          # 9.2
p1_end = p1_start + d["p1_pandora"]         # 23.73
A_swell = p1_end + 0.2
A_full = A_swell + DIG
A_end = round(A_full + SHOW, 3)

blocks = []  # (key, clip, start, end, narr_start, narr_end, full_start, no, name, tag)
# Block A: intro + 潘朵拉
blocks.append(dict(key="A", clip="vert_pandora", start=0.0, end=A_end,
                   narr_start=p1_start, narr_end=p1_end, full_start=A_full,
                   no="01", name="《潘朵拉》", tag="天使嗓音，也能打开<b>暗黑魔盒</b>",
                   vid_start=CUT, mseek=-CUT))  # 潘朵拉画面从 3.5 起；mseek=-CUT：音乐在段内延后 CUT 对齐 clip-0
# Blocks B-E: 其余 4 首
t = A_end
for key, clip, no, name, tag in songs[1:]:
    ns = t + LEAD
    ne = ns + d[key]
    fs = ne + 0.2 + DIG
    end = round(fs + SHOW, 3)
    blocks.append(dict(key=key, clip=clip, start=t, end=end,
                       narr_start=ns, narr_end=ne, full_start=fs,
                       no=no, name=name, tag=tag, vid_start=t, mseek=0.0))
    t = end
# Block F: outro（回到隐形的翅膀=光）：升华 → 消化位 → 固定 CTA → 片尾余量
F_start = t
F_voice = F_start + LEAD
F_voice_end = F_voice + d["outro"]
F_cta = round(F_voice_end + DIGEST_O, 3)      # 固定 CTA 起点
F_cta_end = round(F_cta + d["outro_cta"], 3)
F_end = round(F_cta_end + OUTRO_TAIL, 3)
TOTAL = F_end

# ---------- 展示段对齐闸门（硬规则，违规不出 master）----------
# 机械校验每首：① 副歌人声在转场旁白收尾时正好进来、贯穿展示段（问题1：旁白别盖副歌）；
#               ② 展示段结尾落在唱完一句之后 / 器乐 gap，不切半句（问题2：别暴力裁切）。
# 依据各 clip 的人声段（probe/vocal_analysis.json）。误报时设 SHOWCASE_OVERRIDE=1 跳过。
import sys as _sys
_repo = Path(__file__).resolve()
while _repo != _repo.parent and not (_repo / "tools" / "video" / "showcase_align.py").exists():
    _repo = _repo.parent
_sys.path.insert(0, str(_repo))
from tools.video import showcase_align  # noqa: E402
showcase_align.gate(blocks, "probe/vocal_analysis.json",
                    consts=dict(POST=0.2, DIG=DIG), plan_path="probe/showcase_plan.json")

# ---------- 构建音频分段 ----------
def vol_envelope(narr_local_start, narr_local_end, full_start, seg_dur):
    sw = narr_local_end + 0.2
    return (f"(lt(t,0.8))*({BED}*t/0.8)"
            f"+(between(t,0.8,{sw}))*{BED}"
            f"+(between(t,{sw},{full_start}))*({BED}+{1.0-BED}*(t-{sw})/{DIG})"
            f"+(gte(t,{full_start}))*1.0")

segs = []
# seg A
segA_dur = A_end
veA = (f"(lt(t,{intro_voice_end+0.1}))*0"
       f"+(between(t,{intro_voice_end+0.1},{p1_start}))*({BED}*(t-{intro_voice_end+0.1})/{p1_start-intro_voice_end-0.1})"
       f"+(between(t,{p1_start},{A_swell}))*{BED}"
       f"+(between(t,{A_swell},{A_full}))*({BED}+{1.0-BED}*(t-{A_swell})/{DIG})"
       f"+(gte(t,{A_full}))*1.0")
run(["ffmpeg","-v","error","-i",f"{C}/vert_pandora.mp4","-i",f"{A}/intro.wav","-i",f"{A}/p1_pandora.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[v1];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(p1_start*1000)}|{int(p1_start*1000)}[v2];"
     f"[v1][v2]amix=inputs=2:normalize=0,volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{segA_dur-CUT},adelay={int(CUT*1000)}|{int(CUT*1000)},volume='{veA}':eval=frame[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segA_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_A.wav","-y"])
segs.append("seg_A.wav")

# seg B-E
for b in blocks[1:]:
    seg_dur = b["end"] - b["start"]
    ns_loc = LEAD; ne_loc = LEAD + d[b["key"]]; fs_loc = b["full_start"] - b["start"]
    ve = vol_envelope(ns_loc, ne_loc, fs_loc, seg_dur)
    mg = MGAIN.get(b["key"], 1.0)
    out = f"seg_{b['key']}.wav"
    run(["ffmpeg","-v","error","-i",f"{C}/{b['clip']}.mp4","-i",f"{A}/{b['key']}.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{seg_dur},volume='{ve}':eval=frame,volume={mg}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg_dur},alimiter=limit=0.95[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])
    segs.append(out)

# seg F (outro): 隐形的翅膀 低床 + 升华旁白 → 消化位 → 固定 CTA（床末 1.6s fade）
segF_dur = F_end - F_start
cta_local = round(F_cta - F_start, 3)   # CTA 在本段内的起点
run(["ffmpeg","-v","error","-i",f"{C}/vert_wings.mp4","-i",f"{A}/outro.wav","-i",f"{A}/outro_cta.wav",
     "-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)}[vo];"
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta_local*1000)}|{int(cta_local*1000)}[vc];"
     f"[vo][vc]amix=inputs=2:normalize=0,volume=2.0[voice];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{segF_dur},volume=0.22,afade=t=in:st=0:d=1,afade=t=out:st={segF_dur-1.6}:d=1.6[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{segF_dur},alimiter=limit=0.95[out]",
     "-map","[out]","-ac","2","-ar","48000","seg_F.wav","-y"])
segs.append("seg_F.wav")

# 拼接
Path("seglist.txt").write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","seglist.txt","-ac","2","-ar","48000","master.wav","-y"])
print("master dur:", dur("master.wav"), "/ planned TOTAL:", TOTAL)

# ---------- 生成 HTML ----------
def clip(idv, cls, start, durv, track, extra=""):
    return f'<div id="{idv}" class="clip {cls}" data-start="{round(start,3)}" data-duration="{round(durv,3)}" data-track-index="{track}"{extra}></div>'

# footage 顺序：交替轨道(0/6)避免相邻贴边被判重叠；视觉层级靠 z-index
fclips = [(0.0, CUT, "vert_wings"), (CUT, A_end-CUT, "vert_pandora")]
for b in blocks[1:]:
    fclips.append((b["start"], b["end"]-b["start"], b["clip"]))
fclips.append((F_start, F_end-F_start, "vert_wings"))
vids = [f'<video id="v{i}" class="fv" data-start="{round(s,3)}" data-duration="{round(dv,3)}" '
        f'data-track-index="{0 if i%2==0 else 6}" src="{C}/{src}.mp4" muted playsinline></video>'
        for i,(s,dv,src) in enumerate(fclips)]

# 歌曲标签 + 动画
labels_html, tweens = [], []
for i, b in enumerate(blocks):
    fid, mid = f"lf{i}", f"lm{i}"
    lf_start = 9.0 if b["key"]=="A" else b["start"]+0.2
    lf_dur = b["full_start"] - lf_start
    lm_start = b["full_start"]; lm_dur = b["end"] - b["full_start"]
    labels_html.append(
        f'<div id="{fid}" class="clip labelFull" data-start="{round(lf_start,3)}" data-duration="{round(lf_dur,3)}" data-track-index="2">'
        f'<div class="no">{b["no"]}</div><div class="song">{b["name"]}</div><div class="tag">{b["tag"]}</div></div>')
    labels_html.append(
        f'<div id="{mid}" class="clip labelMin" data-start="{round(lm_start,3)}" data-duration="{round(lm_dur,3)}" data-track-index="4">'
        f'<span class="no">{b["no"]}</span><span class="song">{b["name"]}</span></div>')
    tweens.append(f'tl.from("#{fid} .no",{{y:50,opacity:0,duration:.7,ease:"power3.out"}},{round(lf_start+0.1,3)});')
    tweens.append(f'tl.from("#{fid} .song",{{y:40,opacity:0,duration:.6,ease:"power3.out"}},{round(lf_start+0.3,3)});')
    tweens.append(f'tl.from("#{fid} .tag",{{y:24,opacity:0,duration:.5,ease:"power2.out"}},{round(lf_start+0.5,3)});')
    tweens.append(f'tl.to("#{fid}",{{opacity:0,duration:.4,ease:"power1.in"}},{round(lf_start+lf_dur-0.4,3)});')
    tweens.append(f'tl.set("#{fid}",{{opacity:0}},{round(lf_start+lf_dur,3)});')
    tweens.append(f'tl.from("#{mid}",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},{round(lm_start+0.1,3)});')

TITLE_IN, TITLE_OUT = CUT+0.3, CUT+4.3
CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0a0a0d;font-family:"PingFang SC","Hiragino Sans GB",system-ui,sans-serif}
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:0}
#scrim{position:absolute;inset:0;z-index:1;background:linear-gradient(to bottom,rgba(0,0,0,.5) 0%,rgba(0,0,0,.05) 22%,rgba(0,0,0,.12) 54%,rgba(0,0,0,.8) 100%)}
#chips{position:absolute;top:250px;left:78px;right:78px;z-index:5;color:#fff}
.imp-k{display:flex;align-items:center;gap:18px;font-size:30px;font-weight:700;color:#ff2e88;letter-spacing:.34em}
.imp-k::before{content:"";width:46px;height:4px;background:#ff2e88;border-radius:2px}
.imp-list{list-style:none;margin:40px 0 0}
.imp-list li{font-size:64px;font-weight:800;line-height:1.42;color:rgba(255,255,255,.9);padding-left:34px;position:relative}
.imp-list li::before{content:"";position:absolute;left:0;top:.34em;width:6px;height:.74em;background:rgba(255,46,136,.85);border-radius:3px}
.imp-note{margin-top:30px;font-size:33px;font-weight:600;color:#9a9aa6;letter-spacing:.16em}
#title{position:absolute;left:78px;right:78px;bottom:300px;z-index:5;color:#fff}
#title .kick{display:inline-flex;align-items:center;gap:14px;padding:10px 22px;border:2px solid rgba(255,46,136,.65);border-radius:999px;font-size:27px;font-weight:700;color:#ff2e88;letter-spacing:.22em}
#title .kick::before{content:"";width:14px;height:14px;border-radius:50%;background:#ff2e88;box-shadow:0 0 16px #ff2e88}
#title .setup{margin-top:30px;font-size:46px;font-weight:700;color:#e9e9f0;line-height:1.34}
#title .strike{position:relative;color:#fff;white-space:nowrap}
#title .strike .sl{position:absolute;left:-4px;right:-4px;top:52%;height:6px;background:#ff2e88;border-radius:3px;transform:scaleX(0);transform-origin:left center;box-shadow:0 0 14px rgba(255,46,136,.7)}
#title .hero{margin-top:8px;font-size:220px;font-weight:900;line-height:.92;letter-spacing:-4px;background:linear-gradient(104deg,#ff2e88,#b15cff 52%,#fff);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 10px 44px rgba(255,46,136,.4))}
#title .sub{margin-top:22px;font-size:36px;font-weight:600;color:#c2c2cc;line-height:1.4}
.labelFull{position:absolute;left:78px;right:78px;bottom:230px;z-index:5;color:#fff}
.labelFull .no{font-size:150px;font-weight:900;line-height:.9;color:#ff2e88;filter:drop-shadow(0 8px 30px rgba(255,46,136,.4))}
.labelFull .song{font-size:84px;font-weight:900;margin-top:4px}
.labelFull .tag{font-size:42px;font-weight:600;color:#d7d7e0;margin-top:16px;line-height:1.35}
.labelFull .tag b{color:#ff7ab3;font-weight:700}
.labelMin{position:absolute;top:118px;left:70px;z-index:5;color:#fff;display:flex;align-items:center;gap:18px}
.labelMin .no{font-size:56px;font-weight:900;color:#ff2e88}
.labelMin .song{font-size:50px;font-weight:800}
#outro{position:absolute;left:78px;right:78px;bottom:380px;z-index:5;color:#fff;text-align:left}
#outro .o1{font-size:56px;font-weight:700;color:#e9e9f0;line-height:1.4}
#outro .o2{margin-top:18px;font-size:88px;font-weight:900;line-height:1.05;background:linear-gradient(104deg,#ff2e88,#b15cff 55%,#fff);-webkit-background-clip:text;background-clip:text;color:transparent}
#outro .bar{width:120px;height:8px;background:#ff2e88;margin-top:28px;border-radius:4px}
#cta{position:absolute;left:78px;right:78px;bottom:180px;z-index:6;color:#fff;text-align:left}
#cta .v{font-size:50px;font-weight:900;color:#ff2e88;line-height:1.18}
#cta .f{margin-top:18px;font-size:38px;font-weight:800;color:#e9e9f0;letter-spacing:.1em}
"""

body = "\n".join(vids) + "\n" + clip("scrim","",0,TOTAL,1) + "\n"
body += f'''<div id="chips" class="clip" data-start="0.3" data-duration="{round(CUT-0.3,2)}" data-track-index="2">
<div class="imp-k">大众印象</div>
<ul class="imp-list"><li class="ci">《隐形的翅膀》</li><li class="ci">《欧若拉》</li><li class="ci">《寓言》</li><li class="ci">《梦里花》</li></ul>
<div class="imp-note">温暖 · 治愈 · 天使嗓音</div></div>
<div id="title" class="clip" data-start="{TITLE_IN}" data-duration="{round(TITLE_OUT-TITLE_IN,2)}" data-track-index="4">
<div class="kick">暗黑面 · 深度盘点</div>
<div class="setup">张韶涵 被<span class="strike">《隐形的翅膀》<i class="sl"></i></span> 耽误的</div>
<div class="hero">暗黑面</div>
<div class="sub">她不是只会唱希望，也很会唱破茧和反击</div></div>
'''
body += "\n".join(labels_html) + "\n"
body += f'''<div id="outro" class="clip" data-start="{round(F_voice+0.2,3)}" data-duration="{round(F_cta-F_voice,3)}" data-track-index="4">
<div class="o1">张韶涵不是只有《隐形的翅膀》</div>
<div class="o2">她只是把黑暗，<br>唱成了光</div>
<div class="bar"></div></div>
<div id="cta" class="clip" data-start="{round(F_cta-0.2,3)}" data-duration="{round(F_end-F_cta+0.2,3)}" data-track-index="5">
<div class="v">为你的第一名，评论区投票</div>
<div class="f">点赞 · 收藏 · 关注</div></div>
'''
body += f'<audio id="master" data-start="0" data-duration="{TOTAL}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

js = f'''
tl.from("#chips .imp-k",{{x:-30,opacity:0,duration:.5,ease:"power2.out"}},0.4);
tl.from("#chips .ci",{{x:-40,opacity:0,duration:.5,ease:"power3.out",stagger:.13}},0.6);
tl.from("#chips .imp-note",{{opacity:0,duration:.5}},1.25);
tl.to("#chips",{{opacity:0,duration:.3,ease:"power1.in"}},{round(CUT-0.35,2)});
tl.from("#title .kick",{{y:20,opacity:0,scale:.9,duration:.5,ease:"back.out(1.6)"}},{TITLE_IN+0.1});
tl.from("#title .setup",{{y:26,opacity:0,duration:.5,ease:"power2.out"}},{TITLE_IN+0.35});
tl.fromTo("#title .strike .sl",{{scaleX:0}},{{scaleX:1,duration:.45,ease:"power2.inOut"}},{TITLE_IN+0.8});
tl.from("#title .hero",{{y:70,opacity:0,scale:1.08,duration:.7,ease:"power4.out"}},{TITLE_IN+0.95});
tl.from("#title .sub",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{TITLE_IN+1.35});
tl.to("#title",{{opacity:0,duration:.45,ease:"power2.in"}},{round(TITLE_OUT-0.45,2)});
{chr(10).join(tweens)}
tl.from("#outro .o1",{{y:24,opacity:0,duration:.6,ease:"power2.out"}},{round(F_voice+0.3,3)});
tl.from("#outro .o2",{{y:50,opacity:0,scale:1.05,duration:.8,ease:"power4.out"}},{round(F_voice+0.9,3)});
tl.from("#outro .bar",{{scaleX:0,transformOrigin:"left",duration:.5}},{round(F_voice+1.6,3)});
tl.to("#outro",{{opacity:0,duration:.4,ease:"power1.in"}},{round(F_cta-0.4,3)});
tl.from("#cta .v",{{y:28,opacity:0,duration:.55,ease:"power2.out"}},{round(F_cta,3)});
tl.from("#cta .f",{{y:20,opacity:0,duration:.5,ease:"power2.out"}},{round(F_cta+0.35,3)});
'''

html = f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
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
</script></body></html>'''

Path("index.html").write_text(html, encoding="utf-8")
Path("meta.json").write_text('{"id":"main","name":"zsh-dark-side"}', encoding="utf-8")
print("TOTAL:", TOTAL, "s  blocks:", [(b['key'], b['start'], b['end']) for b in blocks], "F:", F_start, F_end)
