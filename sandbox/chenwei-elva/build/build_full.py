#!/usr/bin/env python3
"""全片构建（陈伟×Elva 8→1，Y2K 都市冷感）：开头 + 8首 + 结尾。
按 BLOCK 生成独立 HF 合成（每块仅 1 video=showcase，entry 用静帧 bg-image）+ 各块 seg 音频 → master_full.wav。
渲染各块→concat→mux master。从项目根运行：python3 build/build_full.py
依赖：audio_full/<line>.wav + durs.json、hf_full/clips_seg/<key>_show.mp4、hf_full/cover_assets/<key>_entry.jpg + aida_face.png + cover_bg.png、raw/<key>_full.wav
"""
import subprocess, json, shutil, re as _re
from pathlib import Path

HF = Path("hf_full"); CS = HF/"clips_seg"; AUD = HF/"audio"; CA = HF/"cover_assets"
for d in (HF, CS, AUD, CA): d.mkdir(parents=True, exist_ok=True)
def run(c): subprocess.run(c, check=True)
def f(x): return f"{round(float(x),3)}"
def dur_wav(p):
    import wave, contextlib
    with contextlib.closing(wave.open(str(p),'r')) as w: return round(w.getnframes()/w.getframerate(),3)

D = json.loads(Path("audio_full/durs.json").read_text())

# ---------- phase constants ----------
LEAD=0.4; GAP=0.55; POST=1.2; SWELL=1.5
B=0.30; Fmus=1.0; TRLOW=0.30; RAMP=0.8

# ---------- per-song config (8→1) ----------
SONGS = [
 dict(key="meiyouren",no="08",name="没有人",year="1999",album="《萧亚轩》同名专辑",credit="曲 · 陈伟　词 · 姚谦　制作 · 陈伟",
   tag="出道冷感",scr1="Elva 的起点",scr2a="不是甜，",scr2b="是冷",s0=200,showd=30,grade="g-cool",
   narr=["s8a","s8b","s8c","s8d"],tr="t8"),
 dict(key="turan",no="07",name="突然想起你",year="1999",album="《萧亚轩》同名专辑",credit="曲 · 陈伟　词 · 林夕　制作 · 陈伟",
   tag="都市想念",scr1="不是崩溃式想念",scr2a="是城市夜里的",scr2b="突然失神",s0=144,showd=32,grade="g-cool",
   narr=["s7a","s7b","s7c"],tr="t7"),
 dict(key="yuji",no="06",name="雨季中",year="2000",album="《红蔷薇》",credit="曲 · 陈伟　词 · 姚谦　编 · 陈伟／于光彦",
   tag="潮湿 R&B",scr1="她的声音从不甜腻",scr2a="而是潮湿、低沉、",scr2b="有距离",s0=207,showd=30,grade="g-cool",
   narr=["s6a","s6b","s6c"],tr="t6"),
 dict(key="mingtian",no="05",name="明天",year="2001",album="《明天》",credit="曲 · 陈伟　词 · 姚谦　制作 · 陈伟",
   tag="未来感",scr1="从都市新人",scr2a="到",scr2b="未来感女声",s0=204,showd=30,grade="g-steel",
   narr=["s5a","s5b","s5c"],tr="t5"),
 dict(key="woaini",no="04",name="我爱你那么多",year="2001",album="《明天》",credit="曲 · 陈伟　词 · 姚谦　制作 · 陈伟",
   tag="低音深情",scr1="她的深情",scr2a="不是软，",scr2b="是有重量",s0=149,showd=30,grade="g-cool",
   narr=["s4a","s4b","s4c","s4d"],tr="t4"),
 dict(key="woxihuan",no="03",name="我喜欢你快乐",year="2002",album="《4U》",credit="曲 · 陈伟　词 · 姚谦　编 · 陈伟／吕绍淳",
   tag="体面成熟",scr1="爱不是占有",scr2a="是",scr2b="我喜欢你快乐",s0=66,showd=30,grade="g-warm",
   narr=["s3a","s3b","s3c"],tr="t3"),
 dict(key="aida",no="02",name="爱的主打歌",year="2002",album="《爱的主打歌》",credit="曲 · 陈伟　词 · 周耀辉　制作 · 含陈伟",
   tag="舞曲人格",scr1="这不是普通快歌",scr2a="这是 Elva 的",scr2b="人格名片",s0=136,showd=30,grade="g-warm",
   narr=["s2a","s2b","s2c"],tr="t2"),
 dict(key="woyao",no="01",name="我要的世界",year="2006",album="《1087》",credit="曲 · 陈伟　词 · 萧亚轩　制作 · 陈伟",
   tag="自我宣言",scr1="从被听见",scr2a="到说出",scr2b="我要的世界",s0=194,showd=30,grade="g-live",
   narr=["s1a","s1b","s1c","s1d"],tr=None),
]

SUBMAP={
 "op1":"很多人记得萧亚轩，<br>是因为她会跳、会唱、会时髦。","op2":'但只用"唱跳女歌手"概括她，<br>其实太浅了。',
 "op3":"真正把 Elva 做出来的人之一，<br>是陈伟。","op4":"他写旋律、做节奏、抓声线，<br>也抓住了那年代最摩登的都市感。",
 "op5":"所以这期，不聊普通热门歌单。","op6":"我们聊 8 首歌，<br>看陈伟怎么把萧亚轩做成都市女声。",
 "s8a":"第 8 首 ·《没有人》","s8b":"不是讨好市场的甜歌，<br>而是直接推出她的中低音和 R&B 底色。","s8c":"陈伟做的不只是写一首歌，<br>是帮她确认了一个方向。","s8d":"她不是邻家女孩，<br>是带着距离感的都市女声。","t8":"想念不再是哭哭啼啼，<br>是城市夜里的突然失神。",
 "s7a":"第 7 首 ·《突然想起你》","s7b":"她唱想念，不柔弱也不崩溃，<br>像城市里灯光一闪，记忆突然打来。","s7c":"陈伟给了她很都市的情绪：<br>冷，但有感觉；淡，但后劲很长。","t7":"夜里的想念之后，<br>是潮湿空气里的质感。",
 "s6a":"第 6 首 ·《雨季中》","s6b":"陈伟和她的默契，<br>从这首开始稳定成形。","s6c":"微哑的中低音、潮湿的 R&B 气息，<br>像从城市雨季里走出来的人。","t6":"但他没把她困在慢歌里，<br>很快加入更强的未来感。",
 "s5a":"第 5 首 ·《明天》","s5b":"一次关键升级——<br>她开始拥有更强的舞台人格。","s5c":"不是普通抒情歌，<br>而是更利落、更有速度的女战士感。","t5":"她可以很冷，也可以很深情。<br>陈伟也不只会做舞曲。",
 "s4a":"第 4 首 ·《我爱你那么多》","s4b":"它证明陈伟不只会做酷和快，<br>也懂怎么放出她声音里的重量。","s4c":"她的深情不是柔弱，<br>而是低低压着，越不爆发越有分量。","s4d":"她唱爱，不像求你留下，<br>更像我已经爱过，且知道自己是谁。","t4":"再往后，爱不再是占有，<br>而是体面。",
 "s3a":"第 3 首 ·《我喜欢你快乐》","s3b":"一边是重低音 Disco 律动，<br>一边是很成熟的情感态度。","s3c":"她可以跳舞、可以时髦，<br>也能把体面唱得很有节奏。","t3":"但真正把她推成时代符号的，<br>是下一首。",
 "s2a":"第 2 首 ·《爱的主打歌》","s2b":"不是普通快歌，<br>而是一套被看见、被记住、被模仿的舞曲人格。","s2c":"从节奏到舞蹈，它都在说：<br>她可以站到舞台中央。","t2":"最后一首，不只用最红收尾，<br>而要落在一句自我宣言上。",
 "s1a":"第 1 首 ·《我要的世界》","s1b":"从冷感的起点到舞台的人格，<br>她一路被陈伟的制作推向更完整的自己。","s1c":"到这一首，她不只是被打造的人，<br>她开始说出自己要的方向。","s1d":"陈伟帮她做出声音系统，<br>她把这个系统，唱成了自己的世界。",
 "o1":"陈伟和萧亚轩，<br>不只是几首经典歌。","o2":"他写旋律、做节奏，抓住她的中低音，<br>也抓住那个时代最摩登的城市感。","o3":"没有这套制作系统，她还是会红，<br>但未必成为我们记忆里的那个样子。","o4":"她不是甜妹，也不是唱跳歌手，<br>是千禧年里很少见的都市女声。",
}

# ---------- layouts ----------
def song_layout(s):
    a={}; cur=RAMP+0.1; lines=[]
    for k in s["narr"]:
        lines.append((k,round(cur,3))); cur+=D[k]+GAP
    a["lines"]=lines; last_end=cur-GAP
    a["sw0"]=round(last_end+POST,3); a["show_start"]=round(a["sw0"]+SWELL,3); a["show_end"]=round(a["show_start"]+s["showd"],3)
    if s["tr"]:
        a["tr_voice"]=round(a["show_end"]+0.4,3); a["tr_end"]=round(a["tr_voice"]+D[s["tr"]],3); a["block_end"]=round(a["tr_end"]+1.0,3)
    else:
        a["block_end"]=round(a["show_end"]+2.0,3)
    a["mo"]=round(s["s0"]-a["show_start"],3)
    assert a["mo"]>=0, f'{s["key"]} mo<0'
    return a

IN=["op1","op2","op3","op4","op5","op6"]
def intro_layout():
    a={}; cur=5.8; gaps=[0.7,0.7,0.6,0.7,1.0,1.5]; L=[]
    for k,g in zip(IN,gaps): L.append((k,round(cur,3))); cur+=D[k]+g
    a["lines"]=L; a["cover"]=5.0; a["end"]=round(cur+0.4,3); return a
OT=["o1","o2","o3","o4"]
def outro_layout():
    a={}; cur=1.2; gaps=[0.7,0.7,0.8,1.4]; L=[]
    for k,g in zip(OT,gaps): L.append((k,round(cur,3))); cur+=D[k]+g
    a["lines"]=L; a["end"]=round(cur+2.2,3); return a

IL=intro_layout(); OL=outro_layout(); LAY={s["key"]:song_layout(s) for s in SONGS}
BLOCKS=["intro"]+[s["key"] for s in SONGS]+["outro"]
BDUR={"intro":IL["end"],"outro":OL["end"]}
for s in SONGS: BDUR[s["key"]]=LAY[s["key"]]["block_end"]
TOTAL=round(sum(BDUR[b] for b in BLOCKS),3)
print("block durs:",{b:BDUR[b] for b in BLOCKS}); print(f"TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# ============ audio ============
AF="audio_full"; SEGD=Path("build/segs_full"); SEGD.mkdir(parents=True,exist_ok=True)
def build_seg(out, music, mo, length, ve, lines):
    voice=str(SEGD/"_v.wav"); mus=str(SEGD/"_m.wav")
    vin=sum([["-i",f"{AF}/{k}.wav"] for k,_ in lines],[]); vfc=[]; labs=[]
    for i,(k,st) in enumerate(lines):
        ms=int(round(st*1000))
        vfc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,adelay={ms}|{ms}[a{i}]"); labs.append(f"[a{i}]")
    vfc.append(f"{''.join(labs)}amix=inputs={len(lines)}:normalize=0:duration=longest[v]")
    run(["ffmpeg","-v","error",*vin,"-filter_complex",";".join(vfc),"-map","[v]","-ac","2","-ar","48000",voice,"-y"])
    run(["ffmpeg","-v","error","-i",music,"-filter_complex",
         f"[0:a]atrim={mo}:{round(mo+length,3)},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,volume='{ve}':eval=frame[m]",
         "-map","[m]","-ac","2","-ar","48000",mus,"-y"])
    run(["ffmpeg","-v","error","-i",voice,"-i",mus,"-filter_complex",
         f"[0:a][1:a]amix=inputs=2:normalize=0:duration=longest,atrim=0:{length},alimiter=limit=0.95[o]","-map","[o]","-ac","2","-ar","48000",out,"-y"])

# intro bed = meiyouren chorus (low), fade ends
e=IL["end"]; iv=(f"(lt(t,1.5))*({B}*t/1.5)+(between(t,1.5,{round(e-2.2,3)}))*{B}+(gte(t,{round(e-2.2,3)}))*max(0,{B}-{B}*(t-{round(e-2.2,3)})/2.2)")
build_seg(str(SEGD/"seg_intro.wav"),"raw/meiyouren_full.wav",118.0,e,iv,IL["lines"]); print("seg_intro",dur_wav(SEGD/"seg_intro.wav"))
for s in SONGS:
    a=LAY[s["key"]]; be=a["block_end"]; sw0=a["sw0"]; ss=a["show_start"]; se=a["show_end"]
    if s["tr"]:
        f1=round(se+1.2,3)
        ve=(f"(lt(t,{RAMP}))*({B}*t/{RAMP})+(between(t,{RAMP},{sw0}))*{B}+(between(t,{sw0},{ss}))*({B}+({Fmus}-{B})*(t-{sw0})/{SWELL})"
            f"+(between(t,{ss},{se}))*{Fmus}+(between(t,{se},{f1}))*({Fmus}+({TRLOW}-{Fmus})*(t-{se})/1.2)"
            f"+(between(t,{f1},{round(be-0.6,3)}))*{TRLOW}+(gte(t,{round(be-0.6,3)}))*max(0,{TRLOW}-{TRLOW}*(t-{round(be-0.6,3)})/0.6)")
        lines=list(a["lines"])+[(s["tr"],a["tr_voice"])]
    else:
        ve=(f"(lt(t,{RAMP}))*({B}*t/{RAMP})+(between(t,{RAMP},{sw0}))*{B}+(between(t,{sw0},{ss}))*({B}+({Fmus}-{B})*(t-{sw0})/{SWELL})"
            f"+(between(t,{ss},{se}))*{Fmus}+(gte(t,{se}))*max(0,{Fmus}-{Fmus}*(t-{se})/{round(be-se,3)})")
        lines=list(a["lines"])
    build_seg(str(SEGD/f"seg_{s['key']}.wav"),f"raw/{s['key']}_full.wav",a["mo"],be,ve,lines); print("seg",s["key"],dur_wav(SEGD/f"seg_{s['key']}.wav"))
eo=OL["end"]; B2=0.34
ov=(f"(lt(t,1.2))*({B2}*t/1.2)+(between(t,1.2,{round(eo-2.8,3)}))*{B2}+(gte(t,{round(eo-2.8,3)}))*max(0,{B2}-{B2}*(t-{round(eo-2.8,3)})/2.8)")
build_seg(str(SEGD/"seg_outro.wav"),"raw/aida_full.wav",150.0,eo,ov,OL["lines"]); print("seg_outro",dur_wav(SEGD/"seg_outro.wav"))
seglist=SEGD/"list.txt"; seglist.write_text("".join(f"file 'seg_{b}.wav'\n" for b in BLOCKS),encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(seglist),"-ac","2","-ar","48000","master_full.wav","-y"])
print("master_full.wav",dur_wav("master_full.wav"),"planned",TOTAL)
shutil.copy("master_full.wav",str(HF/"master.wav"))
for b in BLOCKS: shutil.copy(str(SEGD/f"seg_{b}.wav"),str(AUD/f"{b}.wav"))

# ============ CSS (Y2K) ============
GRAIN=("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E"
 "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E"
 "%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.9'/%3E%3C/svg%3E")
CSS='''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06070d;font-family:"Noto Sans SC",sans-serif;color:#e8edf5;-webkit-font-smoothing:antialiased;}
.foot{position:absolute;opacity:0;will-change:opacity,transform;}
#show,.showv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;}
.estill{position:absolute;inset:0;width:1080px;height:1920px;background-size:cover;background-position:50% 42%;opacity:0;}
.g-cool{filter:saturate(.86) brightness(.98) contrast(1.1);}
.g-steel{filter:saturate(.78) brightness(1.0) contrast(1.12) hue-rotate(-6deg);}
.g-warm{filter:saturate(.96) brightness(1.06) contrast(1.06);}
.g-live{filter:saturate(.9) brightness(1.02) contrast(1.08);}
.g-dim{filter:saturate(.7) brightness(.5) contrast(1.1);}
.ebg{filter:saturate(.6) brightness(.42) contrast(1.12) blur(2px);}
.tintl{position:absolute;inset:0;z-index:3;pointer-events:none;opacity:0;mix-blend-mode:soft-light;}
.cinetop{position:absolute;top:0;left:0;right:0;height:640px;z-index:6;pointer-events:none;background:linear-gradient(180deg,rgba(6,7,13,.94) 0%,rgba(6,7,13,.5) 54%,rgba(6,7,13,0) 100%);}
.cinebot{position:absolute;bottom:0;left:0;right:0;height:760px;z-index:6;pointer-events:none;background:linear-gradient(0deg,rgba(6,7,13,.97) 0%,rgba(6,7,13,.6) 46%,rgba(6,7,13,0) 100%);}
.neonglow{position:absolute;inset:0;z-index:5;pointer-events:none;background:radial-gradient(ellipse 50% 36% at 84% 16%,rgba(123,92,255,.18) 0%,rgba(123,92,255,0) 60%),radial-gradient(ellipse 56% 40% at 12% 88%,rgba(47,214,232,.14) 0%,rgba(47,214,232,0) 62%);}
.scan{position:absolute;inset:0;z-index:8;pointer-events:none;opacity:.5;background-image:repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 1px,rgba(0,0,0,0) 1px 4px);mix-blend-mode:overlay;}
.vignette{position:absolute;inset:0;z-index:7;pointer-events:none;background:radial-gradient(ellipse 80% 64% at 50% 46%,rgba(0,0,0,0) 40%,rgba(0,0,0,.55) 100%);}
.grain{position:absolute;inset:0;z-index:9;pointer-events:none;opacity:.10;mix-blend-mode:overlay;background-image:url("'''+GRAIN+'''");background-size:220px 220px;}
.sub{position:absolute;left:70px;right:70px;bottom:286px;z-index:13;text-align:center;opacity:0;}
.sub-in{display:inline-block;padding:20px 34px;border-radius:4px;font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:44px;line-height:1.46;color:#eef2f8;background:linear-gradient(180deg,rgba(12,16,28,.66),rgba(8,11,20,.82));border:1px solid rgba(150,170,210,.28);box-shadow:0 0 0 1px rgba(0,0,0,.5),0 14px 40px rgba(0,0,0,.55),inset 0 1px 0 rgba(180,200,240,.16);text-shadow:0 2px 14px rgba(0,0,0,.85);}
.neon{color:#5fe4f5;text-shadow:0 0 18px rgba(47,214,232,.55),0 0 40px rgba(47,214,232,.3);}
.warm{color:#e06b6b;text-shadow:0 0 18px rgba(192,65,63,.5);}
.chrome{background:linear-gradient(180deg,#f4f8ff 0%,#cdd6e6 28%,#8c97ad 52%,#e6ecf7 60%,#9aa6bd 76%,#c3cdde 100%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:transparent;filter:drop-shadow(0 2px 1px rgba(0,0,0,.45));}
.songcard{position:absolute;left:0;right:0;top:268px;z-index:15;text-align:center;opacity:0;padding:0 50px;}
.sc-no{font-family:"Chakra Petch",monospace;font-weight:700;font-size:122px;line-height:.82;letter-spacing:.02em;}
.sc-name{font-family:"Noto Sans SC",sans-serif;font-weight:900;font-size:138px;line-height:1.02;color:#eef2f8;letter-spacing:.06em;margin:6px 0 26px;text-shadow:0 6px 50px rgba(0,0,0,.6);}
.sc-name.sm{font-size:96px;letter-spacing:.04em;}
.sc-credit{font-family:"Chakra Petch",monospace;font-weight:500;font-size:31px;letter-spacing:.1em;color:rgba(95,228,245,.92);margin-bottom:14px;}
.sc-album{font-family:"Chakra Petch",monospace;font-weight:400;font-size:25px;letter-spacing:.16em;color:rgba(150,164,190,.92);}
.corner{position:absolute;top:90px;left:60px;z-index:16;display:flex;align-items:center;gap:18px;opacity:0;}
.cn-no{font-family:"Chakra Petch",monospace;font-weight:700;font-size:46px;color:#5fe4f5;text-shadow:0 0 14px rgba(47,214,232,.5);}
.cn-line{width:40px;height:2px;background:rgba(150,170,210,.5);}
.cn-tag{font-family:"Noto Sans SC",sans-serif;font-weight:700;font-size:37px;color:rgba(232,237,245,.92);letter-spacing:.12em;}
.screen2{position:absolute;left:80px;right:80px;top:402px;z-index:17;text-align:center;opacity:0;}
.sb-1{font-family:"Chakra Petch",monospace;font-weight:600;font-size:46px;color:rgba(180,192,214,.85);margin-bottom:18px;letter-spacing:.08em;}
.sb-2{font-family:"Noto Sans SC",sans-serif;font-weight:900;font-size:82px;line-height:1.2;color:#eef2f8;letter-spacing:.03em;}
.transcard{position:absolute;inset:0;z-index:18;opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.tc-bg{position:absolute;inset:0;z-index:-1;background:radial-gradient(ellipse 70% 50% at 50% 50%,rgba(47,214,232,.15) 0%,rgba(6,7,13,0) 60%);}
.tc-rule{width:58px;height:2px;background:#5fe4f5;margin:0 0 38px;box-shadow:0 0 16px rgba(47,214,232,.6);}
.tc-text{font-family:"Noto Sans SC",sans-serif;font-weight:800;font-size:74px;line-height:1.36;text-align:center;color:#eef2f8;letter-spacing:.02em;padding:0 80px;}
/* 封面 */
.cover{position:absolute;inset:0;z-index:50;background:#06070d;overflow:hidden;}
.cv-bg{position:absolute;inset:-40px;z-index:1;background-size:cover;background-position:50% 30%;filter:blur(14px) brightness(.4) saturate(.7) contrast(1.1);transform:scale(1.15);}
.cv-grade{position:absolute;inset:0;z-index:2;background:radial-gradient(ellipse 70% 44% at 80% 14%,rgba(123,92,255,.30) 0%,rgba(123,92,255,0) 60%),radial-gradient(ellipse 70% 44% at 16% 92%,rgba(47,214,232,.22) 0%,rgba(47,214,232,0) 60%),linear-gradient(180deg,rgba(6,7,13,.5) 0%,rgba(6,7,13,.16) 36%,rgba(6,7,13,.72) 76%,#06070d 100%);}
.cv-scan{position:absolute;inset:0;z-index:7;pointer-events:none;opacity:.5;background-image:repeating-linear-gradient(0deg,rgba(255,255,255,.04) 0 1px,rgba(0,0,0,0) 1px 4px);mix-blend-mode:overlay;}
.cv-cd{position:absolute;right:-150px;top:120px;width:430px;height:430px;z-index:3;border-radius:50%;background:conic-gradient(from 20deg,#c9d2e2,#8ea0c4,#e9eef8,#9fb4d8,#c0a6d8,#e6c8e0,#9fc8d8,#c9d2e2);box-shadow:inset 0 0 50px rgba(0,0,0,.5),0 20px 70px rgba(0,0,0,.5);opacity:.28;filter:brightness(.92) saturate(.8);}
.cd-hole{position:absolute;left:50%;top:50%;width:78px;height:78px;transform:translate(-50%,-50%);border-radius:50%;background:#06070d;box-shadow:0 0 0 16px rgba(180,200,240,.1);}
.cv-col{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);z-index:5;display:flex;flex-direction:column;align-items:center;padding:0 64px;}
.cv-eyebrow{display:flex;align-items:center;gap:16px;font-family:"Chakra Petch",monospace;font-weight:600;font-size:30px;letter-spacing:.28em;color:rgba(95,228,245,.92);margin-bottom:34px;text-shadow:0 0 16px rgba(47,214,232,.4);}
.ey-dot{width:12px;height:12px;border-radius:50%;background:#5fe4f5;box-shadow:0 0 14px rgba(47,214,232,.8);}
.cv-av{position:relative;width:420px;height:420px;margin-bottom:46px;}
.cv-ring{position:absolute;inset:-14px;border-radius:50%;background:conic-gradient(from 140deg,#5fe4f5,#7b5cff,#e06b6b,#5fe4f5);opacity:.9;filter:blur(.5px);}
.cv-ring2{position:absolute;inset:-4px;border-radius:50%;border:2px solid rgba(232,237,245,.5);}
.cv-face{position:absolute;inset:0;border-radius:50%;background-image:url("cover_assets/aida_face.png");background-size:cover;background-position:50% 42%;filter:saturate(.92) contrast(1.1) brightness(1.02);box-shadow:inset 0 0 0 4px rgba(6,7,13,.9),0 30px 80px rgba(0,0,0,.6);}
.cv-title{font-family:"Noto Sans SC",sans-serif;font-weight:900;font-size:104px;line-height:1.12;text-align:center;color:#eef2f8;letter-spacing:.02em;text-shadow:0 8px 50px rgba(0,0,0,.55);}
.cv-title .chrome{font-family:"Chakra Petch",monospace;font-weight:700;letter-spacing:.06em;}
.cv-eq{display:flex;align-items:flex-end;gap:8px;height:40px;margin:28px 0 24px;}
.cv-eq i{width:9px;border-radius:2px;background:linear-gradient(180deg,#5fe4f5,#7b5cff);box-shadow:0 0 10px rgba(47,214,232,.5);}
.cv-eq i:nth-child(1){height:18px}.cv-eq i:nth-child(2){height:34px}.cv-eq i:nth-child(3){height:24px}.cv-eq i:nth-child(4){height:40px}.cv-eq i:nth-child(5){height:14px}.cv-eq i:nth-child(6){height:30px}.cv-eq i:nth-child(7){height:22px}.cv-eq i:nth-child(8){height:38px}.cv-eq i:nth-child(9){height:16px}
.cv-sub{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:40px;letter-spacing:.16em;color:rgba(220,228,240,.9);padding-top:26px;border-top:1px solid rgba(150,170,210,.26);}
/* 开头 CD + 屏幕字 */
.opcd{position:absolute;left:0;right:0;top:300px;z-index:4;pointer-events:none;opacity:0;display:flex;align-items:center;justify-content:center;}
.ov-cd{position:relative;width:520px;height:520px;border-radius:50%;background:conic-gradient(from 0deg,#c9d2e2,#8ea0c4,#e9eef8,#9fb4d8,#c0a6d8,#e6c8e0,#9fc8d8,#c9d2e2),radial-gradient(circle at 50% 50%,#0a0c14 0 16%,rgba(0,0,0,0) 17%);box-shadow:0 0 0 2px rgba(180,200,240,.18),inset 0 0 60px rgba(0,0,0,.5);opacity:.32;filter:brightness(.9) saturate(.8);}
.ov-hole{position:absolute;left:50%;top:50%;width:92px;height:92px;transform:translate(-50%,-50%);border-radius:50%;background:#06070d;box-shadow:0 0 0 18px rgba(180,200,240,.1);}
.screen{position:absolute;left:80px;right:80px;top:556px;z-index:14;text-align:center;opacity:0;}
.sa-1{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:40px;letter-spacing:.05em;color:rgba(180,192,214,.55);margin-bottom:26px;text-decoration:line-through;text-decoration-color:rgba(47,214,232,.55);text-decoration-thickness:2px;}
.sa-2{font-family:"Noto Sans SC",sans-serif;font-weight:900;font-size:64px;line-height:1.3;color:#eef2f8;}
/* outro */
.otblk{position:absolute;inset:0;z-index:18;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;}
.ot-bg{position:absolute;inset:0;z-index:-1;background:radial-gradient(ellipse 80% 55% at 50% 50%,rgba(47,214,232,.16) 0%,rgba(6,7,13,0) 62%);}
.ot-rule{width:58px;height:2px;background:#5fe4f5;margin:0 0 34px;box-shadow:0 0 16px rgba(47,214,232,.6);}
.ot-1{font-family:"Noto Sans SC",sans-serif;font-weight:500;font-size:50px;color:rgba(220,228,240,.88);margin-bottom:18px;letter-spacing:.04em;text-align:center;}
.ot-2{font-family:"Noto Sans SC",sans-serif;font-weight:900;font-size:74px;line-height:1.3;color:#eef2f8;text-align:center;letter-spacing:.02em;}
.ot-cta{position:absolute;left:90px;right:90px;bottom:200px;z-index:19;text-align:center;font-family:"Noto Sans SC",sans-serif;font-weight:600;font-size:38px;line-height:1.5;color:rgba(220,228,240,.92);letter-spacing:.03em;opacity:0;text-shadow:0 2px 20px rgba(0,0,0,.8);}
'''
HEAD='''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Chakra+Petch:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script><style>__CSS__</style></head><body>'''
def comp(cid,d,body,js):
    return (HEAD.replace("__CSS__",CSS)+
      f'<div id="root" data-composition-id="{cid}" data-start="0" data-duration="{f(d)}" data-width="1080" data-height="1920">\n{body}\n'
      f'<div class="neonglow"></div><div class="cinetop"></div><div class="cinebot"></div><div class="scan"></div><div class="vignette"></div><div class="grain"></div>\n'
      f'<audio id="aud" data-start="0" data-duration="{f(d)}" data-track-index="3" src="audio/{cid}.wav" data-volume="1"></audio>\n'
      f'</div>\n<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});\n{js}\n'
      f'tl.fromTo("#root>.grain",{{opacity:.08}},{{opacity:.13,duration:2.2,yoyo:true,repeat:{max(0,int(d/2.2)-1)},ease:"sine.inOut"}},0);\n'
      f'window.__timelines["{cid}"]=tl;</script></body></html>')

def _qe(s): return _re.sub(r'ease:([A-Za-z][A-Za-z0-9.]*)', r'ease:"\1"', s)
def TW(el,a,b,at): return 'tl.fromTo("%s",{%s},{%s},%s);\n'%(el,_qe(a),_qe(b),f(at))
def TO(el,b,at): return 'tl.to("%s",{%s},%s);\n'%(el,_qe(b),f(at))
def TS(el,b,at): return 'tl.set("%s",{%s},%s);\n'%(el,_qe(b),f(at))
def sub_js(lines):
    js=""
    for k,st in lines:
        d=D[k]
        js+=(f'tl.fromTo("#sub_{k}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.42,ease:"power2.out"}},{f(st)});'
             f'tl.to("#sub_{k}",{{opacity:0,y:-8,duration:0.42,ease:"power1.in"}},{f(st+d+0.08)});'
             f'tl.set("#sub_{k}",{{opacity:0}},{f(st+d+0.5)});\n')
    return js

def song_html(s):
    a=LAY[s["key"]]; ss=a["show_start"]; se=a["show_end"]; be=a["block_end"]; k=s["key"]
    showvid=min(s["showd"]+3.5,39.0); estill_d=round(ss+1.0,3)
    nm="sc-name sm" if len(s["name"])>=5 else "sc-name"
    body=[]
    body.append(f'<div id="es_{k}" class="estill ebg clip" data-start="0" data-duration="{f(estill_d)}" data-track-index="0" style="background-image:url(\'cover_assets/{k}_entry.jpg\')"></div>')
    body.append(f'<video id="show_{k}" class="foot showv {s["grade"]} clip" data-start="{f(ss)}" data-duration="{f(showvid)}" data-track-index="1" src="clips_seg/{k}_show.mp4" muted playsinline preload="auto"></video>')
    body.append(f'<div id="card_{k}" class="songcard clip" data-start="0.4" data-duration="9.2" data-track-index="15"><div class="sc-no"><span class="chrome">{s["no"]}</span></div><div class="{nm}">{s["name"]}</div><div class="sc-credit">{s["credit"]}</div><div class="sc-album">{s["year"]} ·{s["album"]}</div></div>')
    tag_start=9.6; tag_dur=round(be-0.5-tag_start,3)
    body.append(f'<div id="tag_{k}" class="corner clip" data-start="{f(tag_start)}" data-duration="{f(tag_dur)}" data-track-index="16"><span class="cn-no">{s["no"]}</span><span class="cn-line"></span><span class="cn-tag">{s["tag"]}</span></div>')
    sb=round(ss+2.0,3)
    body.append(f'<div id="scr_{k}" class="screen2 clip" data-start="{f(sb)}" data-duration="8.6" data-track-index="17"><div class="sb-1">{s["scr1"]}</div><div class="sb-2">{s["scr2a"]}<span class="warm">{s["scr2b"]}</span></div></div>')
    sublines=list(a["lines"])+([(s["tr"],a["tr_voice"])] if s["tr"] else [])
    for kk,st in sublines:
        body.append(f'<div id="sub_{kk}" class="sub clip" data-start="{f(st)}" data-duration="{f(D[kk]+0.5)}" data-track-index="12"><span class="sub-in">{SUBMAP[kk]}</span></div>')
    if s["tr"]:
        tcs=round(se+0.1,3)
        body.append(f'<div id="trans_{k}" class="transcard clip" data-start="{f(tcs)}" data-duration="{f(be-tcs)}" data-track-index="18"><div class="tc-bg"></div><div class="tc-rule"></div><div class="tc-text">{SUBMAP[s["tr"]]}</div></div>')
    js=""
    js+=TW(f"#es_{k}","opacity:0","opacity:1,duration:1.0,ease:power1.inOut",0)
    js+=TO(f"#es_{k}","opacity:0,duration:1.2,ease:power1.in",round(estill_d-1.2,3)); js+=TS(f"#es_{k}","opacity:0",estill_d)
    js+='tl.fromTo("#es_%s",{scale:1.06},{scale:1.0,duration:%s,ease:"none"},0);\n'%(k,f(estill_d))
    js+=TW(f"#show_{k}","opacity:0","opacity:1,duration:0.9,ease:power1.inOut",ss)
    js+=TO(f"#show_{k}","opacity:0,duration:1.5,ease:power1.in",round(ss+showvid-1.5,3)); js+=TS(f"#show_{k}","opacity:0",round(ss+showvid,3))
    js+='tl.fromTo("#show_%s",{scale:1.05},{scale:1.0,duration:%s,ease:"none"},%s);\n'%(k,f(showvid),f(ss))
    js+=TW(f"#card_{k}","opacity:0,y:18","opacity:1,y:0,duration:0.8,ease:power2.out",0.5)
    js+='tl.fromTo("#card_%s .sc-name",{letterSpacing:"0.24em",opacity:0},{letterSpacing:"0.06em",opacity:1,duration:1.0,ease:"power3.out"},0.7);\n'%k
    js+=TO(f"#card_{k}","opacity:0,y:-12,duration:0.7,ease:power2.in",8.8); js+=TS(f"#card_{k}","opacity:0",9.6)
    js+=TW(f"#tag_{k}","opacity:0,x:-14","opacity:1,x:0,duration:0.7,ease:power2.out",tag_start)
    js+=TO(f"#tag_{k}","opacity:0,duration:0.7",round(be-0.6,3)); js+=TS(f"#tag_{k}","opacity:0",round(be-0.3,3))
    js+=TW(f"#scr_{k}","opacity:0,y:16","opacity:1,y:0,duration:0.8,ease:power2.out",sb)
    js+=TO(f"#scr_{k}","opacity:0,y:-10,duration:0.9,ease:power1.in",round(sb+7.0,3)); js+=TS(f"#scr_{k}","opacity:0",round(sb+8.6,3))
    js+=sub_js(sublines)
    if s["tr"]:
        tcs=round(se+0.1,3); js+=TW(f"#trans_{k}","opacity:0,y:18","opacity:1,y:0,duration:0.7,ease:power2.out",round(tcs+0.1,3)); js+=TO(f"#trans_{k}","opacity:1,duration:0.1",round(be-0.25,3))
    return comp(k,be,"\n".join(body),js)

def intro_html():
    e=IL["end"]
    body=[]
    # 静帧蒙太奇（Elva 早期MV快切）
    monta=[("m1","meiyouren_entry.jpg",5.2,14.0,0),("m2","aida_entry.jpg",16.5,13.5,1),("m3","woxihuan_entry.jpg",27.5,round(e-27.5+0.4,3),2)]
    for mid,img,st,du,tr in monta:
        body.append(f'<div id="{mid}" class="estill clip" data-start="{f(st)}" data-duration="{f(du)}" data-track-index="{tr}" style="background-image:url(\'cover_assets/{img}\')"></div>')
    body.append('<div id="opcd" class="opcd clip" data-start="6.0" data-duration="%s" data-track-index="8"><div class="ov-cd"><span class="ov-hole"></span></div></div>'%f(e-9.0))
    sA=round(e-9.0,3)
    body.append(f'<div id="screenA" class="screen clip" data-start="{f(sA)}" data-duration="6.4" data-track-index="14"><div class="sa-1">不是普通萧亚轩歌单</div><div class="sa-2">是陈伟做出来的<br><span class="neon">Elva 声音系统</span></div></div>')
    for kk,st in IL["lines"]:
        body.append(f'<div id="sub_{kk}" class="sub clip" data-start="{f(st)}" data-duration="{f(D[kk]+0.5)}" data-track-index="12"><span class="sub-in">{SUBMAP[kk]}</span></div>')
    body.append('<div id="cover" class="cover clip" data-start="0" data-duration="5.0" data-track-index="40">'
      '<div class="cv-bg" style="background-image:url(\'cover_assets/cover_bg.png\')"></div><div class="cv-grade"></div><div class="cv-scan"></div>'
      '<div class="cv-cd"><span class="cd-hole"></span></div>'
      '<div class="cv-col"><div class="cv-eyebrow"><span class="ey-dot"></span>制作人 · 陈伟　×　萧亚轩</div>'
      '<div class="cv-av"><div class="cv-ring"></div><div class="cv-ring2"></div><div class="cv-face"></div></div>'
      '<h1 class="cv-title">陈伟把萧亚轩<br>做成了 <span class="chrome">ELVA</span></h1>'
      '<div class="cv-eq"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>'
      '<div class="cv-sub">8 首歌 · 听懂千禧年都市女声</div></div></div>')
    js=""
    js+=TS("#cover","opacity:1",0)+TS(".cv-col,.cv-face,.cv-title,.cv-sub,.cv-eyebrow,.cv-cd,.cv-bg,.cv-eq,.cv-ring,.cv-ring2","opacity:1",0)
    js+='tl.fromTo(".cv-face",{scale:1.0},{scale:1.03,duration:4.2,ease:"sine.inOut"},0.4);\n'
    js+='tl.fromTo(".cv-ring",{rotation:0},{rotation:120,duration:5,ease:"none"},0);\n'
    js+='tl.fromTo(".cv-eq i",{scaleY:.7},{scaleY:1.15,duration:.5,yoyo:true,repeat:9,ease:"sine.inOut",stagger:{each:.08,from:"center"}},0);\n'
    js+=TO("#cover","opacity:0,duration:0.7,ease:power2.in",4.3)+TS("#cover","opacity:0",5.0)
    for mid,img,st,du,tr in monta:
        js+=TW("#"+mid,"opacity:0","opacity:1,duration:1.5,ease:power1.inOut",st)
        js+=TO("#"+mid,"opacity:0,duration:1.8,ease:power1.in",round(st+du-1.8,3))+TS("#"+mid,"opacity:0",round(st+du,3))
        js+='tl.fromTo("#%s",{scale:1.07},{scale:1.0,duration:%s,ease:"none"},%s);\n'%(mid,f(du),f(st))
    js+=TW("#opcd","opacity:0","opacity:1,duration:1.6,ease:power1.inOut",6.0)+TO("#opcd","opacity:0,duration:1.8,ease:power1.in",round(sA-2.0,3))+TS("#opcd","opacity:0",sA)
    js+='tl.fromTo(".ov-cd",{rotation:0},{rotation:300,duration:%s,ease:"none"},6.0);\n'%f(e-9.0)
    js+=TW("#screenA","opacity:0,y:14","opacity:1,y:0,duration:0.6,ease:power2.out",sA)+TO("#screenA","opacity:0,y:-10,duration:0.7,ease:power1.in",round(sA+5.0,3))+TS("#screenA","opacity:0",round(sA+6.4,3))
    js+=sub_js(IL["lines"])
    return comp("intro",e,"\n".join(body),js)

def outro_html():
    e=OL["end"]
    body=[]
    body.append('<video id="obg" class="foot showv g-dim clip" data-start="0" data-duration="%s" data-track-index="1" src="clips_seg/woyao_show.mp4" muted playsinline preload="auto"></video>'%f(min(e,33.0)))
    body.append('<div class="otblk clip" id="otext" data-start="0" data-duration="%s" data-track-index="17"><div class="ot-bg"></div><div class="ot-rule"></div><div class="ot-1">陈伟做出了 Elva 的声音系统</div><div class="ot-2">萧亚轩把它<span class="neon">唱成了自己的时代</span></div></div>'%f(e))
    for kk,st in OL["lines"]:
        body.append('<div id="sub_%s" class="sub clip" data-start="%s" data-duration="%s" data-track-index="12"><span class="sub-in">%s</span></div>'%(kk,f(st),f(D[kk]+0.5),SUBMAP[kk]))
    cta=round(OL["lines"][-1][1]+D[OL["lines"][-1][0]]+0.6,3)
    body.append('<div id="cta" class="ot-cta clip" data-start="%s" data-duration="%s" data-track-index="19">你心里，陈伟 × 萧亚轩最好的一首是哪首？<br>《突然想起你》《爱的主打歌》还是《我要的世界》？</div>'%(f(cta),f(e-cta)))
    js=""
    js+=TW("#obg","opacity:0","opacity:0.55,duration:2.0,ease:power1.inOut",0)+TO("#obg","opacity:0,duration:2.0,ease:power1.in",round(min(e,33.0)-2.0,3))+TS("#obg","opacity:0",round(min(e,33.0),3))
    js+='tl.fromTo("#obg",{scale:1.06},{scale:1.0,duration:%s,ease:"none"},0);\n'%f(min(e,33.0))
    js+=TS("#otext","opacity:1",0)+TS(".ot-1,.ot-2",("opacity:0"),0)
    js+=TW(".ot-1","opacity:0,y:14","opacity:1,y:0,duration:1.0,ease:power2.out",round(e-9.5,3))
    js+=TW(".ot-2","opacity:0,y:18","opacity:1,y:0,duration:1.1,ease:power3.out",round(e-8.0,3))
    js+=TW("#cta","opacity:0,y:10","opacity:0.95,y:0,duration:0.7,ease:power2.out",cta)
    js+=sub_js(OL["lines"])
    return comp("outro",e,"\n".join(body),js)

# ============ write ============
for fn in ["package.json","hyperframes.json"]:
    src=Path("hf")/fn
    if src.exists(): shutil.copy(str(src),str(HF/fn))
(HF/"intro.html").write_text(intro_html(),encoding="utf-8")
for s in SONGS: (HF/f'{s["key"]}.html').write_text(song_html(s),encoding="utf-8")
(HF/"outro.html").write_text(outro_html(),encoding="utf-8")
(HF/"index.html").write_text(intro_html(),encoding="utf-8")
Path("hf_full/blocks.json").write_text(json.dumps({"blocks":BLOCKS,"durs":BDUR,"total":TOTAL},ensure_ascii=False,indent=1),encoding="utf-8")
print("WROTE",len(BLOCKS),"blocks ; TOTAL",TOTAL)
