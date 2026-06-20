#!/usr/bin/env python3
"""完整片：张韶涵隐藏OST名场面（封面+开头悬念+5首+5剧闪回+作品outro+固定CTA）。
复古电视剧 OST 考古风。产物 master.wav + hf/index.html + hf/clips_seg/*.mp4。
- 每首：转场卡 → 标题卡(歌名/《剧名》/原来它也是OST) → 剧画面(静音,复古) → 女声解说(音乐duck) → 完整副歌(满量,解说停) → 转场。
- 音频：各曲录音室音频连续铺底，voice期duck到BED，副歌满量；mseek对齐使副歌落在full0。
- 渲染后必须 mux master.wav（HF压平动态）。--sdr 渲染。
"""
import subprocess, wave, contextlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT/"audio"; C = ROOT/"clips"; HF = ROOT/"hf"; RAW = ROOT/"raw"
def dur(p):
    with contextlib.closing(wave.open(str(p),'r')) as w: return round(w.getnframes()/w.getframerate(),3)
def run(c): subprocess.run(c, check=True)
def fmt(x): return f"{round(x,3)}"

GOLD="#D8A55A"; CREAM="#F2E6D2"; RED="#C2563B"; BG="#120D0A"

# ---------------- 歌曲数据 ----------------
SONGS = [
 dict(key="butong", no="01", name="不痛", drama="你来自哪颗星", badge="片尾曲｜八大戲劇台",
      clip="vert_butong", audio="s1_butong_audio.wav", chorus=54.2, foot_seek=2.0, high=30,
      tags=["明明很痛，却说不痛","韩剧感拉满","张韶涵早期 OST 隐藏大招"]),
 dict(key="baibaide", no="02", name="白白的", drama="贝多芬病毒", badge="片尾曲｜韩剧",
      clip="vert_baibaide", audio="s2_baibaide_audio.wav", chorus=142.0, foot_seek=18.0, high=30,
      tags=["被忽略的韩剧片尾","白白的，不是空白","情绪被抽走后的安静"]),
 dict(key="zhende", no="03", name="真的", drama="风尘三侠之红拂女", badge="片尾曲｜古装剧",
      clip="vert_zhende", audio="s3_zhende_audio.wav", chorus=40.0, foot_seek=33.0, high=28,
      tags=["冷门神曲","古装剧片尾曲氛围拉满","故事结束，遗憾开始"]),
 dict(key="qishi", no="04", name="其实很爱你", drama="屋顶上的绿宝石", badge="片头曲｜偶像剧",
      clip="vert_qishi", audio="s4_qishi_audio.wav", chorus=94.0, foot_seek=4.0, high=30,
      tags=["早年偶像剧遗珠","嘴上放下，心里全是你","原来它是片头曲"]),
 dict(key="yinxing", no="05", name="隐形的翅膀", drama="爱杀17", badge="片尾曲｜偶像剧",
      clip="vert_yinxing", audio="s5_yinxing_audio.wav", chorus=60.0, foot_seek=2.0, high=38,
      tags=["不是只有励志","也是《爱杀17》的青春伤口","越长大，越听懂那双翅膀"]),
]
TRANS = {"butong":"trans1","baibaide":"trans2","zhende":"trans3","qishi":"trans4","yinxing":"trans5"}

# ---------------- 节奏常量 ----------------
COVER_D=5.0; LEAD=0.3; PRE_BED=0.8; GAP=0.6; PRE_VOICE=1.0; POST_VOICE=1.2; SWELL=1.5; BED=0.20; TAIL=2.4
intro_dur=dur(A/"intro.wav"); outro_dur=dur(A/"outro.wav"); cta_dur=dur(A/"outro_cta.wav")

# 段内锚点（含转场前缀）
def anchors(s):
    td=dur(A/f"{TRANS[s['key']]}.wav"); vd=dur(A/f"s{[x['key'] for x in SONGS].index(s['key'])+1}_voice.wav")
    a={}
    a['tr0']=LEAD; a['tr1']=LEAD+td
    a['v0']=a['tr1']+GAP+PRE_VOICE; a['v1']=a['v0']+vd
    a['sw0']=a['v1']+POST_VOICE; a['full0']=a['sw0']+SWELL; a['full1']=a['full0']+s['high']
    a['seg']=a['full1']+TAIL; a['td']=td; a['vd']=vd
    return a

# voice wav 名按序号
def voicewav(i): return f"s{i+1}_voice.wav"

# ---------------- 绝对时间轴 ----------------
open_seg = COVER_D + LEAD + intro_dur + POST_VOICE
outro_seg = LEAD + outro_dur + 1.0 + cta_dur + 2.0
ANC=[anchors(s) for s in SONGS]
t=0.0; START={}
START['open']=t; t+=open_seg
for i,s in enumerate(SONGS): START[s['key']]=t; t+=ANC[i]['seg']
START['outro']=t; t+=outro_seg
TOTAL=round(t,3)
print(f"TOTAL={TOTAL:.1f}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")
for i,s in enumerate(SONGS):
    mseek=round(s['chorus']-ANC[i]['full0'],2)
    print(f"  {s['key']:9s} seg={ANC[i]['seg']:.1f} mseek={mseek} chorus@full0={mseek+ANC[i]['full0']:.1f}")

# ---------------- 音频段 ----------------
SEG=ROOT/"build"/"segs"; SEG.mkdir(parents=True, exist_ok=True)
def af(p): return f"aresample=48000,aformat=channel_layouts=stereo"

# seg_open: 不痛器乐低床 + intro 女声
intro_at=COVER_D+LEAD
run(["ffmpeg","-v","error","-i",str(RAW/"s1_butong_audio.wav"),"-i",str(A/"intro.wav"),
 "-filter_complex",
 f"[1:a]{af(0)},adelay={int(intro_at*1000)}|{int(intro_at*1000)},volume=2.0[voice];"
 f"[0:a]{af(0)},loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{open_seg},asetpts=PTS-STARTPTS,"
 f"volume=0.17,afade=t=in:st=0:d=1.4,afade=t=out:st={open_seg-2.0}:d=2.0[bed];"
 f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{open_seg},alimiter=level=disabled:limit=0.95[o]",
 "-map","[o]","-ac","2","-ar","48000",str(SEG/"seg_open.wav"),"-y"])

# 每首
for i,s in enumerate(SONGS):
    a=ANC[i]; seg=a['seg']; mseek=round(s['chorus']-a['full0'],2)
    bed_ramp=LEAD+PRE_BED
    ve=(f"(lt(t,{LEAD}))*0"
        f"+(between(t,{LEAD},{bed_ramp}))*({BED}*(t-{LEAD})/{PRE_BED})"
        f"+(between(t,{bed_ramp},{a['sw0']}))*{BED}"
        f"+(between(t,{a['sw0']},{a['full0']}))*({BED}+{1.0-BED}*(t-{a['sw0']})/{SWELL})"
        f"+(gte(t,{a['full0']}))*1.0")
    run(["ffmpeg","-v","error","-i",str(RAW/s['audio']),
         "-i",str(A/f"{TRANS[s['key']]}.wav"),"-i",str(A/voicewav(i)),
     "-filter_complex",
     f"[1:a]{af(0)},adelay={int(a['tr0']*1000)}|{int(a['tr0']*1000)},volume=2.0[tr];"
     f"[2:a]{af(0)},adelay={int(a['v0']*1000)}|{int(a['v0']*1000)},volume=2.0[vo];"
     f"[tr][vo]amix=inputs=2:normalize=0[voice];"
     f"[0:a]{af(0)},loudnorm=I=-14:TP=-1.0:LRA=11,atrim={mseek}:{mseek+seg},asetpts=PTS-STARTPTS,"
     f"volume='{ve}':eval=frame,afade=t=out:st={a['full1']}:d={seg-a['full1']}[music];"
     f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg},alimiter=level=disabled:limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000",str(SEG/f"seg_{s['key']}.wav"),"-y"])

# seg_outro: 隐形的翅膀副歌做暖床 + 作品outro + 固定CTA
o_v0=LEAD; o_cta=LEAD+outro_dur+1.0
run(["ffmpeg","-v","error","-i",str(RAW/"s5_yinxing_audio.wav"),
     "-i",str(A/"outro.wav"),"-i",str(A/"outro_cta.wav"),
 "-filter_complex",
 f"[1:a]{af(0)},adelay={int(o_v0*1000)}|{int(o_v0*1000)},volume=2.0[v1];"
 f"[2:a]{af(0)},adelay={int(o_cta*1000)}|{int(o_cta*1000)},volume=2.0[v2];"
 f"[v1][v2]amix=inputs=2:normalize=0[voice];"
 f"[0:a]{af(0)},loudnorm=I=-14:TP=-1.0:LRA=11,atrim=60:{60+outro_seg},asetpts=PTS-STARTPTS,"
 f"volume=0.30,afade=t=in:st=0:d=1.2,afade=t=out:st={outro_seg-1.8}:d=1.8[bed];"
 f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{outro_seg},alimiter=level=disabled:limit=0.95[o]",
 "-map","[o]","-ac","2","-ar","48000",str(SEG/"seg_outro.wav"),"-y"])

# concat
names=["seg_open.wav"]+[f"seg_{s['key']}.wav" for s in SONGS]+["seg_outro.wav"]
(SEG/"list.txt").write_text("".join(f"file '{n}'\n" for n in names),encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(SEG/"list.txt"),"-ac","2","-ar","48000",str(ROOT/"master.wav"),"-y"])
print("master:",dur(ROOT/"master.wav"),"planned:",TOTAL)
shutil.copy(ROOT/"master.wav",HF/"master.wav")

# ---------------- 预切 footage ----------------
(HF/"clips_seg").mkdir(parents=True,exist_ok=True)
FOOT_LEAD=0.5
for i,s in enumerate(SONGS):
    a=ANC[i]; foot_start=a['tr1']-FOOT_LEAD; foot_dur=a['seg']-foot_start+0.3
    run(["ffmpeg","-v","error","-ss",str(s['foot_seek']),"-i",str(C/f"{s['clip']}.mp4"),
         "-t",str(foot_dur),"-c:v","libx264","-preset","veryfast","-r","30","-g","30",
         "-keyint_min","30","-pix_fmt","yuv420p","-an",str(HF/"clips_seg"/f"{s['key']}.mp4"),"-y"])
print("footage cut")

# ============================================================
# HTML / CSS / JS
# ============================================================
def song_abs(i,key): return START[SONGS[i]['key']]

# footage + tint + chrome + trans cards
fv=[]; tint=[]; chrome=[]; trans=[]
foot_tracks=[0,6,0,6,0]
for i,s in enumerate(SONGS):
    a=ANC[i]; base=START[s['key']]; foot_start=base+a['tr1']-FOOT_LEAD; foot_dur=a['seg']-(a['tr1']-FOOT_LEAD)+0.3
    fv.append(f'<video id="fv_{s["key"]}" class="fv clip" data-start="{fmt(foot_start)}" data-duration="{fmt(foot_dur)}" data-track-index="{foot_tracks[i]}" src="clips_seg/{s["key"]}.mp4" muted playsinline></video>')
    tint.append(f'<div id="tint_{s["key"]}" class="clip tint" data-start="{fmt(foot_start)}" data-duration="{fmt(foot_dur)}" data-track-index="{11+i}"></div>')
    tagdivs="".join(f'<div class="kwtag" id="kw_{s["key"]}_{j}">{tg}</div>' for j,tg in enumerate(s['tags']))
    chrome.append(f'''<div id="chrome_{s['key']}" class="clip chrome" data-start="{fmt(foot_start)}" data-duration="{fmt(foot_dur)}" data-track-index="{20+i}">
  <div class="title-card" id="tc_{s['key']}">
    <div class="tc-no">OST · {s['no']}</div>
    <div class="tc-name">{s['name']}</div>
    <div class="tc-drama">《{s['drama']}》</div>
    <div class="tc-stamp">原来它也是 OST</div>
  </div>
  <div class="bind" id="bind_{s['key']}">
    <span class="bind-song">{s['name']}</span><span class="bind-sep">·</span><span class="bind-drama">{s['drama']}</span>
    <span class="bind-badge">{s['badge']}</span>
  </div>
  {tagdivs}
</div>''')
    # 转场卡
    tb=base+a['tr0']; tkey=s['key']
    trans.append(f'''<div id="trans_{tkey}" class="clip scene trcard" data-start="{fmt(base)}" data-duration="{fmt(a['tr1']+GAP)}" data-track-index="{30+i}">
  <div class="sc-bg"></div><div class="sc-scan"></div><div class="sc-grain"></div><div class="sc-vig"></div>
  <div class="tr-no" id="trno_{tkey}">第 {int(s['no'])} 首</div>
  <div class="tr-line" id="trln_{tkey}">{["听过副歌，<br>却未必知道它的出处","名字很轻，<br>情绪却一点都不轻","老粉心里的<br>冷门神曲","早年偶像剧里，<br>被忘掉的那首","你只记得励志，<br>却忘了它的来路"][i]}</div>
  <div class="tr-rule" id="trru_{tkey}"></div>
  <div class="tr-tvline" id="trtv_{tkey}"></div>
</div>''')

# 封面（梦里花脸；文字往中间收，适配小红书3:4裁切：核心元素落在 y[240,1680]）
cover=f'''<div id="cover" class="clip cover" data-start="0" data-duration="{fmt(COVER_D)}" data-track-index="48">
  <div class="cv-frag cv-frag1"></div><div class="cv-frag cv-frag2"></div><div class="cv-frag cv-frag3"></div>
  <div class="cv-veil"></div><div class="cv-scan"></div><div class="cv-grain"></div>
  <div class="cv-tvtag">CH&nbsp;OST&nbsp;·&nbsp;典藏</div>
  <div class="cv-face-wrap"><div class="cv-face"></div><div class="cv-face-ring"></div></div>
  <div class="cv-title"><div class="cv-name">张韶涵</div><div class="cv-sub">隐藏 OST 名场面</div></div>
  <div class="cv-badge">这些歌你可能听过，<br>但未必知道出处</div>
  <div class="cv-vig"></div>
</div>'''

intro=f'''<div id="intro" class="clip scene" data-start="{fmt(COVER_D)}" data-duration="{fmt(open_seg-COVER_D)}" data-track-index="46">
  <div class="sc-bg"></div><div class="sc-scan"></div><div class="sc-grain"></div><div class="sc-vig"></div>
  <div class="in-kick">影视歌曲考古</div>
  <div class="in-line in-l1">片头 · 片尾 · 主题曲</div>
  <div class="in-line in-l2">有些歌，你听了很多年</div>
  <div class="in-line in-l3">却不知道，它来自哪部剧</div>
</div>'''

# 作品 outro + 5剧闪回 + 固定CTA
ot0=START['outro']
outro=f'''<div id="outro" class="clip scene outroblk" data-start="{fmt(ot0)}" data-duration="{fmt(outro_seg)}" data-track-index="47">
  <div class="sc-bg"></div>
  {''.join(f'<div class="fb fb{j+1}" id="fb_{j+1}"></div>' for j in range(5))}
  <div class="ot-veil" id="ot_veil"></div>
  <div class="sc-scan"></div><div class="sc-grain"></div><div class="sc-vig"></div>
  <div class="ot-flabel" id="ot_flabel">5 部剧 · 5 首被忘记的 OST</div>
  <h2 class="ot-h" id="ot_h">原来她的声音，<br>陪过这么多<br>电视剧的结尾</h2>
  <div class="ot-cta" id="ot_cta">
    <div class="cta-row"><span class="cta-ic">♡</span>投票<span class="cta-dot">·</span><span class="cta-ic">☆</span>收藏<span class="cta-dot">·</span><span class="cta-ic">+</span>关注</div>
    <div class="cta-sub">你最想为哪一首投票？</div>
  </div>
</div>'''

global_fx='<div class="gfx-scan"></div><div class="gfx-grain"></div><div class="gfx-vig"></div>'
audio_html=f'<audio id="master" data-start="0" data-duration="{fmt(TOTAL)}" data-track-index="60" src="master.wav" data-volume="1"></audio>'

CSS=f'''
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:{BG};font-family:"Noto Serif SC","Songti SC",serif;color:{CREAM};-webkit-font-smoothing:antialiased;}}
.clip{{position:absolute;inset:0;}}
.fv{{width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}}
.tint{{z-index:2;opacity:0;background:linear-gradient(180deg, rgba(40,22,10,.30) 0%, rgba(18,13,10,.30) 42%, rgba(8,5,3,.74) 100%);mix-blend-mode:multiply;}}
.chrome{{z-index:5;pointer-events:none;}}
.gfx-scan{{position:absolute;inset:0;z-index:44;pointer-events:none;opacity:.10;background:repeating-linear-gradient(0deg, rgba(0,0,0,.9) 0 1px, transparent 1px 3px);}}
.gfx-grain{{position:absolute;inset:0;z-index:44;pointer-events:none;opacity:.06;mix-blend-mode:overlay;background-image:radial-gradient(circle at 12% 28%, #fff 0 .5px, transparent 1px),radial-gradient(circle at 67% 71%, #fff 0 .5px, transparent 1px),radial-gradient(circle at 39% 53%, #fff 0 .4px, transparent 1px),radial-gradient(circle at 85% 18%, #fff 0 .5px, transparent 1px);background-size:140px 140px,180px 180px,120px 120px,160px 160px;}}
.gfx-vig{{position:absolute;inset:0;z-index:43;pointer-events:none;background:radial-gradient(ellipse 75% 62% at 50% 46%, transparent 0%, transparent 55%, rgba(0,0,0,.55) 100%);}}
.sc-scan{{position:absolute;inset:0;opacity:.10;pointer-events:none;background:repeating-linear-gradient(0deg, rgba(0,0,0,.9) 0 1px, transparent 1px 3px);}}
.sc-grain{{position:absolute;inset:0;opacity:.07;mix-blend-mode:overlay;pointer-events:none;background-image:radial-gradient(circle at 20% 30%, #fff 0 .5px, transparent 1px),radial-gradient(circle at 75% 65%, #fff 0 .5px, transparent 1px);background-size:150px 150px,170px 170px;}}
.sc-vig{{position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 78% 64% at 50% 44%, transparent 0 56%, rgba(0,0,0,.6) 100%);}}

/* 封面 */
.cover{{z-index:50;background:radial-gradient(ellipse at 50% 42%, #28180d 0%, {BG} 74%);overflow:hidden;}}
.cv-frag{{position:absolute;background-size:cover;background-position:center;opacity:.30;filter:saturate(.5);}}
.cv-frag1{{left:-7%;top:6%;width:46%;height:26%;background-image:url("cover_assets/frag1.jpg");transform:rotate(-3deg);}}
.cv-frag2{{right:-8%;top:12%;width:48%;height:25%;background-image:url("cover_assets/frag2.jpg");transform:rotate(2.5deg);}}
.cv-frag3{{right:0%;bottom:5%;width:50%;height:22%;background-image:url("cover_assets/frag3.jpg");transform:rotate(-1.5deg);opacity:.22;}}
.cv-veil{{position:absolute;inset:0;background:linear-gradient(180deg, rgba(18,13,10,.55) 0%, rgba(18,13,10,.28) 36%, rgba(18,13,10,.55) 66%, rgba(10,6,3,.9) 100%);}}
.cv-tvtag{{position:absolute;top:400px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:700;letter-spacing:.42em;color:{GOLD};opacity:.85;}}
.cv-face-wrap{{position:absolute;top:490px;left:0;right:0;display:flex;justify-content:center;}}
.cv-face{{width:380px;height:380px;border-radius:50%;background-image:url("cover_assets/zsh_face.jpg");background-size:cover;background-position:center 38%;filter:saturate(.92) contrast(1.04) brightness(1.0);box-shadow:0 30px 90px rgba(0,0,0,.6), inset 0 0 0 1px rgba(255,255,255,.1);}}
.cv-face-ring{{position:absolute;top:-13px;left:50%;transform:translateX(-50%);width:406px;height:406px;border-radius:50%;border:3px solid rgba(216,165,90,.85);box-shadow:0 0 50px rgba(216,165,90,.3);}}
.cv-title{{position:absolute;top:930px;left:0;right:0;text-align:center;}}
.cv-name{{font-size:150px;font-weight:800;letter-spacing:.06em;color:{CREAM};text-shadow:0 6px 30px rgba(0,0,0,.65);line-height:1.0;}}
.cv-sub{{font-size:92px;font-weight:700;letter-spacing:.04em;margin-top:16px;color:{GOLD};text-shadow:0 4px 24px rgba(0,0,0,.55);}}
.cv-badge{{position:absolute;top:1330px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:39px;font-weight:500;line-height:1.5;color:rgba(242,230,210,.82);letter-spacing:.04em;}}

/* intro / trans 场景 */
.scene{{z-index:41;background:{BG};overflow:hidden;}}
.sc-bg{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%, #251509 0%, {BG} 72%);}}
.in-kick{{position:absolute;top:600px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;font-size:34px;font-weight:700;letter-spacing:.5em;color:{GOLD};opacity:0;}}
.in-line{{position:absolute;left:80px;right:80px;text-align:center;font-weight:700;color:{CREAM};opacity:0;}}
.in-l1{{top:800px;font-size:74px;color:{GOLD};letter-spacing:.06em;}}
.in-l2{{top:1010px;font-size:56px;}} .in-l3{{top:1140px;font-size:56px;}}
.trcard{{z-index:38;}}
.tr-no{{position:absolute;top:760px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;font-size:46px;font-weight:700;letter-spacing:.4em;color:{RED};opacity:0;}}
.tr-line{{position:absolute;top:880px;left:90px;right:90px;text-align:center;font-size:76px;font-weight:800;line-height:1.34;color:{CREAM};opacity:0;}}
.tr-rule{{position:absolute;top:1190px;left:50%;width:0;height:3px;background:{GOLD};transform:translateX(-50%);opacity:.9;}}
.tr-tvline{{position:absolute;left:0;right:0;top:50%;height:3px;background:rgba(242,230,210,.9);opacity:0;box-shadow:0 0 30px rgba(242,230,210,.8);}}

/* 标题卡 / 绑定 / 关键词 */
.title-card{{position:absolute;top:560px;left:80px;right:80px;text-align:center;opacity:0;}}
.tc-no{{font-family:"JetBrains Mono",monospace;font-size:36px;font-weight:700;letter-spacing:.46em;color:{GOLD};margin-bottom:24px;}}
.tc-name{{font-size:164px;font-weight:800;line-height:1.0;color:{CREAM};text-shadow:0 8px 40px rgba(0,0,0,.7);}}
.tc-drama{{font-size:60px;font-weight:600;color:rgba(242,230,210,.9);margin-top:18px;letter-spacing:.04em;}}
.tc-stamp{{display:inline-block;margin-top:32px;font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:700;color:{RED};border:3px solid {RED};border-radius:10px;padding:10px 28px;transform:rotate(-4deg);letter-spacing:.08em;box-shadow:0 6px 24px rgba(0,0,0,.4);}}
.bind{{position:absolute;left:60px;bottom:148px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;max-width:840px;opacity:0;}}
.bind-song{{font-size:58px;font-weight:800;color:{CREAM};text-shadow:0 4px 18px rgba(0,0,0,.85);}}
.bind-sep{{font-size:44px;color:{GOLD};}}
.bind-drama{{font-size:52px;font-weight:600;color:rgba(242,230,210,.92);text-shadow:0 4px 18px rgba(0,0,0,.85);}}
.bind-badge{{font-family:"Noto Sans SC",sans-serif;font-size:28px;font-weight:700;color:{GOLD};border:2px solid rgba(216,165,90,.7);border-radius:999px;padding:7px 20px;letter-spacing:.08em;background:rgba(18,13,10,.5);width:100%;max-width:max-content;}}
.kwtag{{position:absolute;left:60px;bottom:330px;font-family:"Noto Sans SC",sans-serif;font-size:50px;font-weight:800;color:{CREAM};padding:16px 30px;background:linear-gradient(90deg, rgba(194,86,59,.92), rgba(160,60,40,.55));border-left:6px solid {GOLD};border-radius:6px;letter-spacing:.03em;opacity:0;text-shadow:0 3px 14px rgba(0,0,0,.6);box-shadow:0 10px 36px rgba(0,0,0,.5);}}

/* outro */
.outroblk{{z-index:47;}}
.fb{{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;}}
.fb1{{background-image:url("cover_assets/fb1.jpg");}}.fb2{{background-image:url("cover_assets/fb2.jpg");}}
.fb3{{background-image:url("cover_assets/fb3.jpg");}}.fb4{{background-image:url("cover_assets/fb4.jpg");}}
.fb5{{background-image:url("cover_assets/fb5.jpg");}}
.ot-veil{{position:absolute;inset:0;background:linear-gradient(180deg, rgba(10,6,3,.6) 0%, rgba(10,6,3,.4) 40%, rgba(10,6,3,.92) 100%);opacity:0;}}
.ot-flabel{{position:absolute;top:560px;left:0;right:0;text-align:center;font-family:"JetBrains Mono",monospace;font-size:32px;font-weight:700;letter-spacing:.34em;color:{GOLD};opacity:0;}}
.ot-h{{position:absolute;top:680px;left:80px;right:80px;text-align:center;font-size:84px;font-weight:800;line-height:1.28;color:{CREAM};opacity:0;text-shadow:0 6px 30px rgba(0,0,0,.7);}}
.ot-cta{{position:absolute;top:1230px;left:0;right:0;text-align:center;opacity:0;}}
.cta-row{{font-family:"Noto Sans SC",sans-serif;font-size:52px;font-weight:800;color:{CREAM};letter-spacing:.06em;display:flex;justify-content:center;align-items:center;gap:18px;}}
.cta-ic{{color:{GOLD};font-size:46px;}} .cta-dot{{color:rgba(242,230,210,.4);}}
.cta-sub{{margin-top:26px;font-size:42px;font-weight:600;color:{GOLD};letter-spacing:.04em;}}
'''

def JS():
    L=[]
    # 封面（首帧即在）
    L+=['tl.set("#cover",{opacity:1},0);','tl.set(".cv-tvtag,.cv-face-wrap,.cv-title,.cv-badge",{opacity:1},0);',
        f'tl.to(".cv-face",{{scale:1.03,duration:3.4,ease:"sine.inOut",yoyo:true,repeat:1}},1.0);',
        f'tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(COVER_D-0.55)});',
        f'tl.set("#cover",{{opacity:0}},{fmt(COVER_D)});']
    # intro
    ib=COVER_D+LEAD
    L+=[f'tl.set("#intro",{{opacity:1}},{fmt(COVER_D)});',
        f'tl.fromTo(".in-kick",{{opacity:0,y:18}},{{opacity:.9,y:0,duration:.7}},{fmt(ib+0.2)});',
        f'tl.fromTo(".in-l1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.7}},{fmt(ib+2.2)});',
        f'tl.fromTo(".in-l2",{{opacity:0,y:24}},{{opacity:.96,y:0,duration:.7}},{fmt(ib+9.5)});',
        f'tl.fromTo(".in-l3",{{opacity:0,y:24}},{{opacity:.96,y:0,duration:.7}},{fmt(ib+14.0)});',
        f'tl.to("#intro",{{opacity:0,duration:.6,ease:"power2.in"}},{fmt(START[SONGS[0]["key"]]-0.5)});',
        f'tl.set("#intro",{{opacity:0}},{fmt(START[SONGS[0]["key"]])});']
    # 每首
    for i,s in enumerate(SONGS):
        k=s['key']; a=ANC[i]; base=START[k]; tb=base+a['tr0']; tend=base+a['tr1']+GAP
        foot_start=base+a['tr1']-FOOT_LEAD; vstart=base+a['v0']; sw0=base+a['sw0']; full0=base+a['full0']; end=base+a['seg']
        # 转场卡
        L+=[f'tl.set("#trans_{k}",{{opacity:1}},{fmt(base)});',
            f'tl.fromTo("#trno_{k}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.5}},{fmt(tb+0.1)});',
            f'tl.fromTo("#trln_{k}",{{opacity:0,y:22}},{{opacity:1,y:0,duration:.7}},{fmt(tb+0.5)});',
            f'tl.fromTo("#trru_{k}",{{width:0}},{{width:280,duration:.9,ease:"power2.out"}},{fmt(tb+1.1)});',
            f'tl.fromTo("#trtv_{k}",{{opacity:0,scaleY:1}},{{opacity:1,duration:.16}},{fmt(tend-0.5)});',
            f'tl.to("#trno_{k},#trln_{k},#trru_{k}",{{opacity:0,duration:.2}},{fmt(tend-0.45)});',
            f'tl.to("#trtv_{k}",{{scaleY:60,opacity:0,duration:.32,ease:"power2.in",overwrite:"auto"}},{fmt(tend-0.33)});',
            f'tl.set("#trtv_{k}",{{opacity:0}},{fmt(tend)});',
            f'tl.to("#trans_{k}",{{opacity:0,duration:.2}},{fmt(tend-0.05)});',
            f'tl.set("#trans_{k}",{{opacity:0}},{fmt(tend)});']
        # footage + tint
        L+=[f'tl.fromTo("#fv_{k}",{{opacity:0,scale:1.05}},{{opacity:1,scale:1.0,duration:1.0,ease:"power2.out"}},{fmt(foot_start)});',
            f'tl.to("#tint_{k}",{{opacity:1,duration:1.0}},{fmt(foot_start)});']
        # 标题卡
        L+=[f'tl.fromTo("#tc_{k}",{{opacity:0,y:28}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{fmt(foot_start+0.5)});',
            f'tl.to("#tc_{k}",{{opacity:0,y:-18,duration:.6,ease:"power2.in"}},{fmt(vstart+0.1)});']
        # bind
        L+=[f'tl.fromTo("#bind_{k}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.7}},{fmt(vstart+0.5)});']
        # 关键词标签轮换
        tag_times=[vstart+3.5, sw0+0.3, full0+8.0]
        for j in range(3):
            nxt=tag_times[j+1] if j+1<3 else end-1.0
            L+=[f'tl.fromTo("#kw_{k}_{j}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:.5}},{fmt(tag_times[j])});',
                f'tl.to("#kw_{k}_{j}",{{opacity:0,x:14,duration:.45}},{fmt(min(nxt-0.2,end-0.8))});']
        # 收尾淡出 (hard kill)
        fo=end-1.4
        for sel in [f'#fv_{k}',f'#tint_{k}',f'#bind_{k}']:
            L+=[f'tl.to("{sel}",{{opacity:0,duration:1.2,ease:"power1.in"}},{fmt(fo)});',
                f'tl.set("{sel}",{{opacity:0}},{fmt(end)});']
    # outro: 5剧闪回(换台) → 文字 → CTA
    ob=START['outro']
    L+=[f'tl.set("#outro",{{opacity:1}},{fmt(ob)});']
    for j in range(5):
        ft=ob+0.2+j*1.15
        L+=[f'tl.fromTo("#fb_{j+1}",{{opacity:0}},{{opacity:.9,duration:.12}},{fmt(ft)});',
            f'tl.to("#fb_{j+1}",{{opacity:0,duration:.12}},{fmt(ft+1.0)});',
            f'tl.set("#fb_{j+1}",{{opacity:0}},{fmt(ft+1.05)});']
    settle=ob+0.2+5*1.15+0.1
    L+=[f'tl.fromTo("#ot_veil",{{opacity:0}},{{opacity:1,duration:.8}},{fmt(settle)});',
        f'tl.fromTo("#ot_flabel",{{opacity:0,y:14}},{{opacity:.9,y:0,duration:.7}},{fmt(settle+0.4)});',
        f'tl.fromTo("#ot_h",{{opacity:0,y:34}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{fmt(settle+1.0)});',
        f'tl.fromTo("#ot_cta",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.7}},{fmt(ob+LEAD+outro_dur+1.0)});',
        f'tl.to("#outro",{{opacity:1,duration:.1}},{fmt(TOTAL-0.2)});']
    return "\n    ".join(L)

html=f'''<!doctype html>
<html lang="zh"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{fmt(TOTAL)}" data-width="1080" data-height="1920">
    {chr(10).join(fv)}
    {chr(10).join(tint)}
    {chr(10).join(chrome)}
    {global_fx}
    {chr(10).join(trans)}
    {intro}
    {outro}
    {cover}
    {audio_html}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{paused:true}});
    {JS()}
    window.__timelines["main"] = tl;
  </script>
</body></html>'''
(HF/"index.html").write_text(html,encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"angela-hidden-ost"}',encoding="utf-8")
print("index.html:",len(html),"bytes · TOTAL",TOTAL,"s")
