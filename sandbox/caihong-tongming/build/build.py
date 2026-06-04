#!/usr/bin/env python3
"""全片：华语同名《彩虹》盘点（竖屏 1080×1920，叙事序 1→5）。
封面(设计款) + 蒙太奇钩子 + Part1 动力火车 + Part2 梁静茹/五月天(双版本) + Part3 张惠妹
+ Part4 羽泉(春晚) + Part5 周杰伦 + 回放/评论引导 outro。
产物：hf/master.wav（逐段 床→swell→展示，loudnorm I=-14） + hf/index.html + hf/clips_seg/*。
渲染后必须 ffmpeg mux master.wav。"""
import subprocess, json
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parent.parent; os.chdir(ROOT)
C = "clips"; A = "audio"
def run(c): subprocess.run(c, check=True)
def adur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).strip())
NARR = json.loads(Path("narration.json").read_text())
def f(x): return f"{round(x,3)}"

# ===== 节奏常量 =====
COVER_D=5.0; HOOK_VOICE_AT=COVER_D+0.8
OPEN_END=round(HOOK_VOICE_AT+NARR["intro"]["dur"]+1.6,3)
LEAD,PRE,POST,SWELL,TAIL=0.2,0.8,1.2,1.5,1.2
BED=0.20

# ===== 每首配置 =====
# 标准段 anchors
def anchors(base, voice, show):
    v0=LEAD+PRE; v1=v0+voice; sw0=v1+POST; full0=sw0+SWELL; full1=full0+show; seg=full1+TAIL
    return dict(start=base, v0=base+v0, v1=base+v1, sw0=base+sw0, full0=base+full0,
                full1=base+full1, end=base+seg, seg=seg, lv0=v0,lsw0=sw0,lfull0=full0,lfull1=full1)

PARTS=[
 dict(key="p1",no="01",artist="动力火车",tag="热血 · 不认输",kw="热血",
      lead='这一道彩虹，<br>是<span class="hl">热血</span>和不认输。',
      mid="人在泥里，<br>也要把自己唱起来。",
      clip="vert_p1",mseek=0.0,show=30.0,voice=NARR["s1"]["dur"],
      pri="#E8954E",acc="#F4C98A",
      tint="linear-gradient(180deg,rgba(217,120,60,.16)0%,rgba(20,10,6,0)26%,rgba(6,5,8,.34)64%,rgba(0,0,0,.82)100%)",
      src="动力火车《彩虹》 · 官方 MV",track=0),
 dict(key="p3",no="03",artist="张惠妹",tag="陪伴 · 被看见",kw="陪伴",
      lead='这一道彩虹，<br>是<span class="hl">陪伴</span>和被看见。',
      mid="不是所有光，<br>都来自爱情。",
      clip="vert_p3",mseek=6.6,show=30.0,voice=NARR["s3"]["dur"],
      pri="#C79BD8",acc="#E8C98A",
      tint="linear-gradient(180deg,rgba(150,110,200,.16)0%,rgba(14,10,22,0)28%,rgba(6,5,10,.36)64%,rgba(0,0,0,.84)100%)",
      src="张惠妹《彩虹》 · 官方 MV",track=6),
 dict(key="p4",no="04",artist="羽泉",tag="千禧 · 青春滤镜",kw="青春",
      lead='这一道彩虹，<br>是千禧年的<span class="hl">青春</span>滤镜。',
      mid="有人一听前奏，<br>就回到学生时代。",
      clip="vert_p4",mseek=33.45,show=28.0,voice=NARR["s4"]["dur"],
      pri="#D8B85B",acc="#E8D69A",
      tint="linear-gradient(180deg,rgba(216,184,91,.15)0%,rgba(20,16,8,0)28%,rgba(8,6,4,.36)64%,rgba(0,0,0,.84)100%)",
      src="羽泉《彩虹》 · 2001 央视春晚",track=0),
 dict(key="p5",no="05",artist="周杰伦",tag="青春失恋 · 标准答案？",kw="雨季",
      lead='青春失恋的，<br><span class="hl">标准答案</span>？',
      mid="哪里有彩虹，<br>告诉我。",
      clip="vert_p5",mseek=23.2,show=28.0,voice=NARR["s5"]["dur"],
      pri="#8FB6C9",acc="#BBD7E4",
      tint="linear-gradient(180deg,rgba(120,160,190,.15)0%,rgba(8,12,16,0)28%,rgba(5,7,10,.38)64%,rgba(0,0,0,.85)100%)",
      src="周杰伦《彩虹》 · 官方 MV",track=6),
]
# Part 2 (dual) 常量
P2=dict(voice=NARR["s2"]["dur"], LJR_SHOW=17.0, TRANS=3.0, MYT_SHOW=24.0,
        ljr_clip="vert_p2a", ljr_mseek=3.0, myt_clip="vert_p2b", myt_mseek=30.0,
        pri_l="#6FA8C7", pri_m="#D98A5B")
p2_v0=LEAD+PRE; p2_v1=p2_v0+P2["voice"]; p2_sw0=p2_v1+POST; p2_ljr_full0=p2_sw0+SWELL
p2_ljr_full1=p2_ljr_full0+P2["LJR_SHOW"]; p2_trans0=p2_ljr_full1; p2_trans1=p2_trans0+P2["TRANS"]
p2_myt_full0=p2_trans1; p2_myt_full1=p2_myt_full0+P2["MYT_SHOW"]; p2_seg=p2_myt_full1+TAIL

# ===== 时间轴：blocks 顺序 cover/hook(open) → p1 → p2 → p3 → p4 → p5 → outro =====
Vo=NARR["outro"]["dur"]
RECAP_N=6; RECAP_EACH=1.15; RECAP=RECAP_N*RECAP_EACH
OUTRO_SEG=round(LEAD+RECAP+Vo+5.5,3)
t=OPEN_END
# p1
A1=anchors(t,PARTS[0]["voice"],PARTS[0]["show"]); PARTS[0]["A"]=A1; t=A1["end"]
# p2
P2_START=t; t=P2_START+p2_seg
# p3,p4,p5
for p in PARTS[1:]:
    ap=anchors(t,p["voice"],p["show"]); p["A"]=ap; t=ap["end"]
OUTRO_T=t; t=OUTRO_T+OUTRO_SEG
TOTAL=round(t,3)
print(f"opening={OPEN_END} p2@{P2_START} outro@{OUTRO_T} TOTAL={TOTAL} ({int(TOTAL//60)}:{TOTAL%60:05.2f})")

# ============ 音频 ============
Path("build/segs").mkdir(parents=True, exist_ok=True)
def env_std(voice, full0_local, sw0_local, v0_local):
    return (f"(lt(t,{LEAD}))*0+(between(t,{LEAD},{v0_local}))*({BED}*(t-{LEAD})/{v0_local-LEAD})"
            f"+(between(t,{v0_local},{sw0_local}))*{BED}"
            f"+(between(t,{sw0_local},{full0_local}))*({BED}+{1.0-BED}*(t-{sw0_local})/{SWELL})"
            f"+(gte(t,{full0_local}))*1.0")

# --- open (cover+hook): p1 低通器乐床 + intro 旁白 ---
run(["ffmpeg","-v","error","-i",f"{C}/vert_p1.mp4","-i",f"{A}/intro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(HOOK_VOICE_AT*1000)}|{int(HOOK_VOICE_AT*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=0:{OPEN_END},asetpts=PTS-STARTPTS,"
     f"lowpass=f=620,volume=0.17,afade=t=in:st=0:d=1.2,afade=t=out:st={OPEN_END-1.4}:d=1.4[b];"
     f"[v][b]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OPEN_END},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000","build/segs/seg_open.wav","-y"])

# --- 标准段 ---
def build_std(p):
    Aa=p["A"]; seg=Aa["seg"]; ve=env_std(p["voice"],Aa["lfull0"],Aa["lsw0"],Aa["lv0"])
    full1=Aa["lfull1"]
    run(["ffmpeg","-v","error","-i",f"{C}/{p['clip']}.mp4","-i",f"{A}/{ {'p1':'s1','p3':'s3','p4':'s4','p5':'s5'}[p['key']] }.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(Aa['lv0']*1000)}|{int(Aa['lv0']*1000)},volume=2.0[v];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={p['mseek']}:{p['mseek']+seg},asetpts=PTS-STARTPTS,"
         f"volume='{ve}':eval=frame,afade=t=out:st={full1}:d={seg-full1}[m];"
         f"[v][m]amix=inputs=2:normalize=0:duration=longest,atrim=0:{seg},alimiter=limit=0.95[o]",
         "-map","[o]","-ac","2","-ar","48000",f"build/segs/seg_{p['key']}.wav","-y"])
for p in PARTS: build_std(p)

# --- Part 2 dual ---
ljr_env=(f"(lt(t,{LEAD}))*0+(between(t,{LEAD},{p2_v0}))*({BED}*(t-{LEAD})/{p2_v0-LEAD})"
         f"+(between(t,{p2_v0},{p2_sw0}))*{BED}"
         f"+(between(t,{p2_sw0},{p2_ljr_full0}))*({BED}+{1.0-BED}*(t-{p2_sw0})/{SWELL})"
         f"+(between(t,{p2_ljr_full0},{p2_ljr_full1}))*1.0"
         f"+(between(t,{p2_ljr_full1},{p2_trans1}))*(1.0-(t-{p2_ljr_full1})/{P2['TRANS']})")
myt_env=(f"(between(t,{p2_trans0},{p2_myt_full0}))*((t-{p2_trans0})/{P2['TRANS']})"
         f"+(between(t,{p2_myt_full0},{p2_myt_full1}))*1.0"
         f"+(gte(t,{p2_myt_full1}))*max(0,1.0-(t-{p2_myt_full1})/{TAIL})")
run(["ffmpeg","-v","error","-i",f"{C}/{P2['ljr_clip']}.mp4","-i",f"{C}/{P2['myt_clip']}.mp4","-i",f"{A}/s2.wav","-filter_complex",
     f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(p2_v0*1000)}|{int(p2_v0*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={P2['ljr_mseek']}:{P2['ljr_mseek']+p2_trans1},asetpts=PTS-STARTPTS,volume='{ljr_env}':eval=frame[l];"
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim={P2['myt_mseek']}:{P2['myt_mseek']+(p2_seg-p2_trans0)},asetpts=PTS-STARTPTS,adelay={int(p2_trans0*1000)}|{int(p2_trans0*1000)},volume='{myt_env}':eval=frame[m];"
     f"[v][l][m]amix=inputs=3:normalize=0:duration=longest,atrim=0:{p2_seg},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000","build/segs/seg_p2.wav","-y"])

# --- outro: 张惠妹 暖副歌作床 + outro 旁白 ---
ov_at=LEAD+RECAP*0.18
run(["ffmpeg","-v","error","-i",f"{C}/vert_p3.mp4","-i",f"{A}/outro.wav","-filter_complex",
     f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(ov_at*1000)}|{int(ov_at*1000)},volume=2.0[v];"
     f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,atrim=20:{20+OUTRO_SEG},asetpts=PTS-STARTPTS,"
     f"volume=0.42,afade=t=in:st=0:d=1.0,afade=t=out:st={OUTRO_SEG-2.4}:d=2.4[b];"
     f"[v][b]amix=inputs=2:normalize=0:duration=longest,atrim=0:{OUTRO_SEG},alimiter=limit=0.95[o]",
     "-map","[o]","-ac","2","-ar","48000","build/segs/seg_outro.wav","-y"])

# concat
order=["seg_open","seg_p1","seg_p2","seg_p3","seg_p4","seg_p5","seg_outro"]
Path("build/segs/list.txt").write_text("".join(f"file '{n}.wav'\n" for n in order),encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/segs/list.txt","-ac","2","-ar","48000","hf/master.wav","-y"])
print("master:",round(adur("hf/master.wav"),2),"planned",TOTAL)

# ============ 预切 footage ============
Path("hf/clips_seg").mkdir(parents=True, exist_ok=True)
def cut(clip,mseek,dur,out):
    run(["ffmpeg","-v","error","-ss",str(mseek),"-i",f"{C}/{clip}.mp4","-t",str(dur),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",f"hf/clips_seg/{out}.mp4","-y"])
for p in PARTS: cut(p["clip"],p["mseek"],p["A"]["seg"],p["key"])
cut(P2["ljr_clip"],P2["ljr_mseek"],p2_trans1,"p2a")           # 梁 footage: block 0→trans1
cut(P2["myt_clip"],P2["myt_mseek"],p2_seg-p2_trans0,"p2b")    # 五月天 footage: trans0→end
# recap flashes
RECAP_SRC=[("vert_p1",8),("vert_p2a",21),("vert_p2b",40),("vert_p3",23),("vert_p4",50),("vert_p5",50)]
for i,(clip,ms) in enumerate(RECAP_SRC): cut(clip,ms,RECAP_EACH+0.3,f"r{i+1}")
print("clips_seg done")

# ============ HTML ============
RB="linear-gradient(90deg,#d9665f 0%,#dd9a52 17%,#d8c85a 33%,#69bd84 52%,#5ea6c9 69%,#7d7ec9 85%,#c77bb1 100%)"
RBH="linear-gradient(94deg,#ff8a82 0%,#ffb45c 18%,#ffe27a 34%,#79da99 52%,#6bbcec 70%,#a695f2 86%,#f094d0 100%)"

CSS = '''
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06080F;color:#F4EFE7;font-family:"Noto Serif SC","Songti SC",serif;-webkit-font-smoothing:antialiased}
.clip{position:absolute}
.vign{position:absolute;inset:0;z-index:2;background:radial-gradient(ellipse 70% 55% at 50% 46%,rgba(40,44,60,.34)0,rgba(6,8,15,0)55%),radial-gradient(ellipse 120% 90% at 50% 120%,rgba(0,0,0,.85)0,transparent 60%)}
.grain{position:absolute;inset:0;z-index:3;opacity:.5;mix-blend-mode:overlay;background-image:radial-gradient(circle at 12% 28%,rgba(255,255,255,.05)0 .5px,transparent .9px),radial-gradient(circle at 78% 66%,rgba(255,255,255,.05)0 .5px,transparent .9px);background-size:200px 200px,260px 260px}
/* COVER */
#cover{inset:0;z-index:60;background:#06080F;overflow:hidden}
.cv-disc{position:absolute;left:50%;top:610px;width:780px;height:780px;transform:translate(-50%,-50%);border-radius:50%;background:repeating-radial-gradient(circle at 50% 50%,rgba(255,255,255,.022)0 2px,transparent 2px 6px),radial-gradient(circle at 50% 50%,#15131c 0 27%,#0c0a12 27% 30%,#141019 30% 100%);box-shadow:0 40px 120px rgba(0,0,0,.7),inset 0 0 60px rgba(0,0,0,.8);z-index:5}
.cv-disc::after{content:"";position:absolute;left:50%;top:50%;width:150px;height:150px;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient(circle at 42% 40%,#3a3550,#16121f 70%);box-shadow:inset 0 0 0 2px rgba(255,255,255,.06)}
.cv-sheen{position:absolute;left:50%;top:742px;width:860px;height:230px;transform:translate(-50%,-50%) rotate(-15deg);background:__RB__;filter:blur(42px);opacity:.34;mix-blend-mode:screen;border-radius:50%;z-index:6}
.cv-halo{position:absolute;left:50%;top:600px;width:940px;height:540px;transform:translate(-50%,-50%);z-index:7;background:radial-gradient(ellipse 50% 46% at 50% 50%,rgba(5,7,13,.94)0%,rgba(5,7,13,.66)42%,rgba(5,7,13,0)72%)}
.cv-hero{position:absolute;left:0;right:0;top:430px;text-align:center;z-index:8;font-weight:900;font-size:316px;letter-spacing:.04em;line-height:1;background:__RBH__;-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 8px 26px rgba(0,0,0,.7)) drop-shadow(0 0 46px rgba(0,0,0,.55)) drop-shadow(0 0 3px rgba(255,255,255,.28))}
.cv-eyebrow{position:absolute;top:188px;left:0;right:0;text-align:center;z-index:8;font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;letter-spacing:.46em;color:#C9A86A}
.cv-eyebrow .bar{display:inline-block;width:54px;height:1px;background:#C9A86A;vertical-align:middle;margin:0 18px;opacity:.7}
.cv-paper{position:absolute;left:62px;top:1108px;width:520px;height:300px;transform:rotate(-4deg);z-index:7;opacity:.85;background:linear-gradient(180deg,rgba(244,239,231,.10),rgba(244,239,231,.04));border:1px solid rgba(244,239,231,.10);border-radius:10px;box-shadow:0 24px 60px rgba(0,0,0,.5);background-image:repeating-linear-gradient(180deg,transparent 0 38px,rgba(244,239,231,.07)38px 39px)}
.cv-title{position:absolute;left:70px;right:70px;top:1180px;z-index:9}
.cv-t1{font-size:104px;font-weight:900;line-height:1.08;color:#F4EFE7;letter-spacing:-1px}
.cv-t1 .n{font-family:"JetBrains Mono",monospace;font-weight:800;background:__RBH__;-webkit-background-clip:text;background-clip:text;color:transparent;padding-right:6px}
.cv-t2{font-size:92px;font-weight:800;line-height:1.12;color:#F4EFE7;margin-top:6px}
.cv-sub{position:absolute;left:72px;right:72px;top:1560px;z-index:9;font-size:46px;font-weight:500;color:rgba(244,239,231,.62)}
.cv-rule{position:absolute;left:72px;right:72px;top:1700px;height:4px;border-radius:4px;z-index:9;background:__RB__;opacity:.85}
.cv-foot{position:absolute;left:0;right:0;top:1748px;text-align:center;z-index:9;font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:600;letter-spacing:.3em;color:rgba(244,239,231,.4)}
/* HOOK */
#hook{inset:0;z-index:55;background:radial-gradient(ellipse at 50% 30%,#0c1020 0,#06080F 70%);overflow:hidden}
.hk-glow{position:absolute;border-radius:50%;filter:blur(60px);mix-blend-mode:screen;opacity:0}
.hk-g1{left:-160px;top:300px;width:620px;height:620px;background:radial-gradient(circle,rgba(217,150,82,.5),transparent 70%)}
.hk-g2{right:-180px;top:780px;width:680px;height:680px;background:radial-gradient(circle,rgba(94,166,201,.5),transparent 70%)}
.hk-g3{left:240px;top:1180px;width:560px;height:560px;background:radial-gradient(circle,rgba(125,126,201,.45),transparent 70%)}
.hk-band{position:absolute;left:-12%;width:124%;height:130px;background:__RB__;filter:blur(30px);mix-blend-mode:screen;opacity:0}
.hk-b1{top:520px;transform:rotate(-9deg)}.hk-b2{top:980px;transform:rotate(7deg)}
.hk-rain{position:absolute;inset:-10% 0;z-index:4;opacity:0;mix-blend-mode:screen;background-image:repeating-linear-gradient(74deg,transparent 0 26px,rgba(180,200,230,.16)26px 27px,transparent 27px 60px);background-size:auto 100%}
.hk-disc{position:absolute;left:50%;top:760px;width:300px;height:300px;transform:translate(-50%,-50%);border-radius:50%;z-index:6;opacity:0;background:repeating-radial-gradient(circle at 50% 50%,rgba(255,255,255,.05)0 1.5px,transparent 1.5px 5px),radial-gradient(circle,#15131c 0 30%,#0e0b14 100%);box-shadow:0 20px 60px rgba(0,0,0,.6)}
.hk-frag{position:absolute;font-family:"Noto Serif SC",serif;color:rgba(244,239,231,.16);z-index:7;opacity:0;white-space:nowrap}
.hk-f1{left:80px;top:430px;font-size:40px;transform:rotate(-3deg)}.hk-f2{right:70px;top:680px;font-size:34px}.hk-f3{left:120px;top:1320px;font-size:36px;transform:rotate(2deg)}
.hk-text{position:absolute;left:80px;right:80px;z-index:9;text-align:center;opacity:0}
#hkt1{top:820px;font-size:78px;font-weight:900;color:#F4EFE7;letter-spacing:.02em}
#hkt1 b{background:__RBH__;-webkit-background-clip:text;background-clip:text;color:transparent}
#hkt2{top:1010px;font-size:46px;font-weight:500;line-height:1.45;color:rgba(244,239,231,.82)}
/* footage 章节 */
.fv{inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0}
.tint{inset:0;opacity:0}
.chrome{position:absolute;inset:0;pointer-events:none}
.rail{position:absolute;top:300px;left:60px;height:560px;width:10px;opacity:0}
.rail-bar{position:absolute;top:0;bottom:0;left:4px;width:2px;background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.20),rgba(255,255,255,.04))}
.rail-dot{position:absolute;left:-20px;width:46px;height:46px;border-radius:50%;background:rgba(18,16,24,.9);border:2px solid rgba(255,255,255,.20);display:flex;align-items:center;justify-content:center}
.rail-dot .t{font-family:"JetBrains Mono",monospace;font-size:22px;font-weight:800;color:rgba(255,255,255,.6)}
.rail-dot.on{box-shadow:0 0 28px currentColor;transform:scale(1.18)}
.card{position:absolute;top:250px;right:54px;width:600px;padding:42px 44px;border-radius:24px;opacity:0;background:linear-gradient(160deg,rgba(255,255,255,.11),rgba(255,255,255,.03));backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);border:1.5px solid rgba(255,255,255,.18);box-shadow:0 32px 90px rgba(0,0,0,.6)}
.card-no{font-family:"JetBrains Mono",monospace;font-size:34px;font-weight:800;letter-spacing:.3em;margin-bottom:18px}
.card-art{font-size:76px;font-weight:900;line-height:1.04;color:#F4EFE7;letter-spacing:-1px}
.card-song{font-size:44px;font-weight:700;color:rgba(244,239,231,.9);margin-top:8px}
.card-song i{font-style:normal}
.card-tag{margin-top:26px;font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;display:flex;align-items:center;gap:14px}
.card-tag .d{width:12px;height:12px;border-radius:50%}
.lead{position:absolute;left:70px;right:70px;top:1430px;opacity:0;font-size:54px;font-weight:800;line-height:1.28;color:#F4EFE7;text-shadow:0 4px 30px rgba(0,0,0,.7)}
.lead .hl{background:__RBH__;-webkit-background-clip:text;background-clip:text;color:transparent}
.kw{position:absolute;left:0;right:0;top:560px;text-align:center;opacity:0;font-size:300px;font-weight:900;line-height:.9;mix-blend-mode:screen;letter-spacing:-6px}
.mid{position:absolute;left:80px;right:80px;top:1470px;opacity:0;text-align:center;font-size:52px;font-weight:600;line-height:1.4;color:#F8F2EA;text-shadow:0 4px 24px rgba(0,0,0,.8)}
.src{position:absolute;bottom:52px;left:0;right:0;text-align:center;opacity:0;font-family:"Noto Sans SC",sans-serif;font-size:22px;font-weight:500;letter-spacing:.26em;color:rgba(244,239,231,.4)}
/* Part2 transition card */
#p2trans{position:absolute;inset:0;z-index:30;pointer-events:none;opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(ellipse at 50% 50%,rgba(8,10,18,.55),rgba(5,7,12,.86))}
#p2trans .tl{font-size:60px;font-weight:900;color:#F4EFE7;letter-spacing:.02em}
#p2trans .vs{margin:30px 0;display:flex;align-items:center;gap:30px;font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:800}
#p2trans .vs .a{color:#6FA8C7}#p2trans .vs .b{color:#D98A5B}#p2trans .vs .x{color:rgba(244,239,231,.4);font-size:34px}
#p2trans .sb{font-size:38px;font-weight:500;color:rgba(244,239,231,.72);text-align:center;line-height:1.4}
/* OUTRO */
#outro{inset:0;z-index:48;background:radial-gradient(ellipse at 50% 36%,#16131f 0,#06080F 72%);overflow:hidden}
.ot-rule{position:absolute;top:300px;left:90px;right:90px;height:4px;border-radius:4px;background:__RB__;opacity:0}
.ot-list{position:absolute;top:360px;left:90px;right:90px}
.ot-li{display:flex;align-items:baseline;gap:26px;padding:13px 0;border-bottom:1px solid rgba(255,255,255,.08);opacity:0}
.ot-n{font-family:"JetBrains Mono",monospace;font-size:30px;font-weight:800;color:#C9A86A;min-width:54px}
.ot-a{font-size:42px;font-weight:700;color:#F4EFE7}
.ot-s{font-size:30px;font-weight:500;color:rgba(244,239,231,.5);margin-left:auto}
.ot-q{position:absolute;top:1180px;left:80px;right:80px;text-align:center;font-size:74px;font-weight:900;color:#F4EFE7;opacity:0}
.ot-q b{background:__RBH__;-webkit-background-clip:text;background-clip:text;color:transparent}
.ot-deb{position:absolute;top:1380px;left:90px;right:90px;opacity:0}
.ot-deb .d{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:500;color:rgba(244,239,231,.7);text-align:center;line-height:1.55;margin:6px 0}
.ot-cta{position:absolute;top:1660px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:36px;font-weight:800;letter-spacing:.1em;color:#C9A86A;opacity:0}
'''.replace("__RBH__",RBH).replace("__RB__",RB)

# ----- cover/hook html -----
cover=f'''<div id="cover" class="clip" data-start="0" data-duration="{f(COVER_D)}" data-track-index="40">
 <div class="cv-sheen"></div><div class="cv-disc"></div><div class="cv-halo"></div><div class="vign"></div><div class="grain"></div>
 <div class="cv-eyebrow"><span class="bar"></span>华语乐坛 · 同名歌曲盘点<span class="bar"></span></div>
 <div class="cv-hero">彩虹</div><div class="cv-paper"></div>
 <div class="cv-title"><div class="cv-t1"><span class="n">5</span>首《彩虹》，</div><div class="cv-t2">你先想到谁？</div></div>
 <div class="cv-sub">同名歌曲，差别太大了。</div><div class="cv-rule"></div><div class="cv-foot">同一个歌名 · 不同的人生</div></div>'''
hook=f'''<div id="hook" class="clip" data-start="{f(COVER_D)}" data-duration="{f(OPEN_END-COVER_D)}" data-track-index="41">
 <div class="hk-glow hk-g1"></div><div class="hk-glow hk-g2"></div><div class="hk-glow hk-g3"></div>
 <div class="hk-band hk-b1"></div><div class="hk-band hk-b2"></div><div class="hk-rain"></div><div class="hk-disc"></div>
 <div class="hk-frag hk-f1">雨後的天空</div><div class="hk-frag hk-f2">藍綠黃紅</div><div class="hk-frag hk-f3">哪裡有彩虹</div>
 <div class="vign"></div><div class="grain"></div>
 <div class="hk-text" id="hkt1">同样叫<b>《彩虹》</b></div>
 <div class="hk-text" id="hkt2">唱出来的，<br>却完全不是同一种人生。</div></div>'''

# ----- 标准段 html (rail dots: 5 节点, p1=1 p3=3 p4=4 p5=5 active) -----
RAIL_IDX={"p1":0,"p3":2,"p4":3,"p5":4}
def std_html(p):
    Aa=p["A"];idx=RAIL_IDX[p["key"]]
    dots="".join(f'<div class="rail-dot{(" on" if i==idx else "")}" style="top:{i*120}px;{("color:"+p["pri"]+";background:"+p["pri"]+";border-color:"+p["pri"]) if i==idx else ""}"><span class="t" style="{("color:#140e08" if i==idx else "")}">{i+1}</span></div>' for i in range(5))
    return f'''<video id="fv_{p['key']}" class="fv clip" data-start="{f(Aa['start'])}" data-duration="{f(Aa['seg'])}" data-track-index="{p['track']}" src="clips_seg/{p['key']}.mp4" muted playsinline></video>
<div id="tint_{p['key']}" class="tint clip" data-start="{f(Aa['start'])}" data-duration="{f(Aa['seg'])}" data-track-index="{10+idx}" style="z-index:2;background:{p['tint']}"></div>
<div id="ch_{p['key']}" class="chrome clip" data-start="{f(Aa['start'])}" data-duration="{f(Aa['seg'])}" data-track-index="{20+idx}" style="z-index:5">
  <div class="rail"><div class="rail-bar"></div>{dots}</div>
  <div class="card"><div class="card-no" style="color:{p['pri']}">PART {p['no']}</div><div class="card-art">{p['artist']}</div>
   <div class="card-song">《<i style="color:{p['acc']}">彩虹</i>》</div>
   <div class="card-tag" style="color:{p['acc']}"><span class="d" style="background:{p['pri']};box-shadow:0 0 16px {p['pri']}"></span>{p['tag']}</div></div>
  <div class="lead">{p['lead']}</div>
  <div class="kw" id="kw_{p['key']}" style="color:{p['pri']};filter:drop-shadow(0 8px 60px {p['pri']})">{p['kw']}</div>
  <div class="mid" id="mid_{p['key']}">{p['mid']}</div>
  <div class="src">{p['src']}</div></div>'''

# ----- Part2 html -----
b=P2_START
def P(x): return f(b+x)
dots2="".join(f'<div class="rail-dot{(" on" if i==1 else "")}" style="top:{i*120}px;{("color:#9E94C9;background:#9E94C9;border-color:#9E94C9") if i==1 else ""}"><span class="t" style="{("color:#140e08" if i==1 else "")}">{i+1}</span></div>' for i in range(5))
part2=f'''<video id="fv_p2a" class="fv clip" data-start="{P(0)}" data-duration="{f(p2_trans1)}" data-track-index="6" src="clips_seg/p2a.mp4" muted playsinline></video>
<video id="fv_p2b" class="fv clip" data-start="{P(p2_trans0)}" data-duration="{f(p2_seg-p2_trans0)}" data-track-index="0" src="clips_seg/p2b.mp4" muted playsinline></video>
<div id="tint_p2a" class="tint clip" data-start="{P(0)}" data-duration="{f(p2_trans1)}" data-track-index="11" style="z-index:2;background:linear-gradient(180deg,rgba(110,168,199,.16)0%,rgba(8,14,20,0)28%,rgba(5,8,12,.4)64%,rgba(0,0,0,.85)100%)"></div>
<div id="tint_p2b" class="tint clip" data-start="{P(p2_trans0)}" data-duration="{f(p2_seg-p2_trans0)}" data-track-index="12" style="z-index:2;background:linear-gradient(180deg,rgba(217,138,91,.16)0%,rgba(20,12,6,0)28%,rgba(8,6,4,.4)64%,rgba(0,0,0,.85)100%)"></div>
<div id="ch_p2" class="chrome clip" data-start="{P(0)}" data-duration="{f(p2_seg)}" data-track-index="22" style="z-index:5">
  <div class="rail"><div class="rail-bar"></div>{dots2}</div>
  <div class="card"><div class="card-no" style="color:#9E94C9">PART 02</div><div class="card-art" id="p2art">梁静茹</div>
   <div class="card-song">《<i id="p2acc" style="color:#9ECBE0">彩虹</i>》</div>
   <div class="card-tag" id="p2tag" style="color:#9ECBE0"><span class="d" style="background:#6FA8C7;box-shadow:0 0 16px #6FA8C7"></span>同一首歌 · 两种失恋</div></div>
  <div class="lead" id="p2lead">同一首歌，<br>两种<span class="hl">失恋</span>质感。</div>
  <div class="kw" id="kw_p2a" style="color:#6FA8C7;filter:drop-shadow(0 8px 60px #6FA8C7)">想通</div>
  <div class="kw" id="kw_p2b" style="color:#D98A5B;filter:drop-shadow(0 8px 60px #D98A5B)">告别</div>
  <div class="mid" id="mid_p2a">一个，<br>湿漉漉的青春。</div>
  <div class="mid" id="mid_p2b">一个，<br>乐团式的告别。</div>
  <div class="src" id="src_p2">梁静茹《彩虹》 · 官方 MV</div></div>
<div id="p2trans" class="clip" data-start="{P(p2_trans0-0.4)}" data-duration="{f(P2['TRANS']+0.8)}" data-track-index="30">
  <div class="tl">同一首歌</div><div class="vs"><span class="a">梁静茹</span><span class="x">×</span><span class="b">五月天</span></div>
  <div class="sb">一个湿漉漉的青春，<br>一个乐团式的告别。</div></div>'''

# ----- outro html -----
RECAP_TRACKS=[0,6,0,6,0,6]
recap_html="".join(
 f'<video id="rc{i+1}" class="fv clip" data-start="{f(OUTRO_T+LEAD+i*RECAP_EACH)}" data-duration="{f(RECAP_EACH+0.05)}" data-track-index="{RECAP_TRACKS[i]}" src="clips_seg/r{i+1}.mp4" muted playsinline></video>'
 for i in range(RECAP_N))
OUT_LIST=[("01","动力火车","热血"),("02","梁静茹 · 五月天","失恋"),("03","张惠妹","陪伴"),("04","羽泉","青春"),("05","周杰伦","雨季")]
ot_lis="".join(f'<div class="ot-li"><span class="ot-n">{n}</span><span class="ot-a">{a}《彩虹》</span><span class="ot-s">{s}</span></div>' for n,a,s in OUT_LIST)
outro=f'''{recap_html}
<div id="outro" class="clip" data-start="{f(OUTRO_T)}" data-duration="{f(OUTRO_SEG)}" data-track-index="42">
  <div class="vign"></div>
  <div class="ot-rule"></div>
  <div class="ot-list">{ot_lis}</div>
  <div class="ot-q">你先想到哪一首<b>《彩虹》</b>？</div>
  <div class="ot-deb">
   <div class="d">周杰伦，是不是断层第一反应？</div>
   <div class="d">羽泉，是不是大陆听众的青春 DNA？</div>
   <div class="d">梁静茹和五月天，你更喜欢哪个版本？</div></div>
  <div class="ot-cta">评论区 · 交给你们</div></div>'''

audio_el=f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ============ JS ============
def js_std(p):
    Aa=p["A"];a=Aa;end=a["end"];fo=end-1.0;mid0=a["full1"]-6.0;k=p["key"]
    return f'''
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:1.6,ease:"power2.out"}},{f(a["start"])});
tl.to("#tint_{k}",{{opacity:1,duration:1.4}},{f(a["start"])});
tl.fromTo("#ch_{k} .rail",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:.8,ease:"power2.out"}},{f(a["start"]+0.4)});
tl.fromTo("#ch_{k} .card",{{opacity:0,x:60,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{f(a["start"]+0.6)});
tl.fromTo("#ch_{k} .lead",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(a["v0"]+0.3)});
tl.fromTo("#ch_{k} .src",{{opacity:0}},{{opacity:1,duration:.6}},{f(a["start"]+1.4)});
tl.to("#ch_{k} .card",{{opacity:0,y:-12,duration:.5,ease:"power2.in"}},{f(a["sw0"]-0.1)});
tl.to("#ch_{k} .lead",{{opacity:0,y:-12,duration:.5,ease:"power2.in"}},{f(a["sw0"]-0.1)});
tl.fromTo("#kw_{k}",{{opacity:0,scale:.9}},{{opacity:.3,scale:1,duration:1.6,ease:"power3.out"}},{f(a["full0"]-0.4)});
tl.fromTo("#mid_{k}",{{opacity:0,y:26}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(mid0)});
tl.to("#mid_{k}",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{f(end-1.4)});
tl.to("#kw_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{f(end-1.4)});
tl.to("#fv_{k}",{{opacity:0,duration:1.0,ease:"power1.in"}},{f(fo)});tl.set("#fv_{k}",{{opacity:0}},{f(end)});
tl.to("#tint_{k}",{{opacity:0,duration:1.0}},{f(fo)});tl.set("#tint_{k}",{{opacity:0}},{f(end)});
tl.to("#ch_{k} .rail, #ch_{k} .src",{{opacity:0,duration:.6}},{f(end-0.6)});tl.set("#ch_{k} .rail, #ch_{k} .src",{{opacity:0}},{f(end)});'''

# part2 JS
def J(x): return f(b+x)
js_p2=f'''
tl.fromTo("#fv_p2a",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:1.6,ease:"power2.out"}},{J(0)});
tl.to("#tint_p2a",{{opacity:1,duration:1.4}},{J(0)});
tl.fromTo("#ch_p2 .rail",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:.8}},{J(0.4)});
tl.fromTo("#ch_p2 .card",{{opacity:0,x:60,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{J(0.6)});
tl.fromTo("#ch_p2 .lead",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{J(p2_v0+0.3)});
tl.fromTo("#src_p2",{{opacity:0}},{{opacity:1,duration:.6}},{J(1.4)});
tl.to("#ch_p2 .card",{{opacity:0,y:-12,duration:.5}},{J(p2_sw0-0.1)});
tl.to("#ch_p2 .lead",{{opacity:0,y:-12,duration:.5}},{J(p2_sw0-0.1)});
/* 梁静茹 展示: kw 想通 + mid 湿漉漉 */
tl.fromTo("#kw_p2a",{{opacity:0,scale:.9}},{{opacity:.3,scale:1,duration:1.4,ease:"power3.out"}},{J(p2_ljr_full0-0.3)});
tl.fromTo("#mid_p2a",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8}},{J(p2_ljr_full0+3)});
tl.to("#mid_p2a",{{opacity:0,duration:.5}},{J(p2_ljr_full1-0.4)});
tl.to("#kw_p2a",{{opacity:0,duration:.6}},{J(p2_ljr_full1-0.2)});
/* 转场卡 + 切五月天 */
tl.fromTo("#p2trans",{{opacity:0}},{{opacity:1,duration:.5,ease:"power2.out"}},{J(p2_trans0-0.2)});
tl.fromTo("#p2trans .vs",{{y:14,opacity:.4}},{{y:0,opacity:1,duration:.6,ease:"power2.out"}},{J(p2_trans0+0.1)});
tl.to("#p2trans",{{opacity:0,duration:.6,ease:"power2.in"}},{J(p2_trans1-0.3)});tl.set("#p2trans",{{opacity:0}},{J(p2_trans1+0.1)});
tl.to("#fv_p2a",{{opacity:0,duration:1.0}},{J(p2_trans0+0.2)});tl.set("#fv_p2a",{{opacity:0}},{J(p2_trans1)});
tl.to("#tint_p2a",{{opacity:0,duration:1.0}},{J(p2_trans0+0.2)});tl.set("#tint_p2a",{{opacity:0}},{J(p2_trans1)});
tl.fromTo("#fv_p2b",{{opacity:0,scale:1.06}},{{opacity:1,scale:1,duration:1.2,ease:"power2.out"}},{J(p2_trans0+0.4)});
tl.to("#tint_p2b",{{opacity:1,duration:1.2}},{J(p2_trans0+0.6)});
/* 卡片切到五月天 */
tl.add(()=>{{var e=document.getElementById('p2art');if(e)e.textContent='五月天';
 var t=document.getElementById('p2tag');if(t)t.innerHTML='<span class="d" style="background:#D98A5B;box-shadow:0 0 16px #D98A5B"></span>乐团式的告别';t&&(t.style.color='#E0B58A');
 var ac=document.getElementById('p2acc');if(ac)ac.style.color='#E0B58A';
 var s=document.getElementById('src_p2');if(s)s.textContent='五月天《彩虹》 · 官方 MV';}},{J(p2_myt_full0-0.6)});
tl.fromTo("#ch_p2 .card",{{opacity:0,x:60}},{{opacity:1,x:0,duration:.7,ease:"power3.out"}},{J(p2_myt_full0-0.5)});
tl.to("#ch_p2 .card",{{opacity:0,duration:.5}},{J(p2_myt_full0+3.5)});
tl.fromTo("#kw_p2b",{{opacity:0,scale:.9}},{{opacity:.3,scale:1,duration:1.4}},{J(p2_myt_full0+0.4)});
tl.fromTo("#mid_p2b",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8}},{J(p2_myt_full1-7)});
tl.to("#mid_p2b",{{opacity:0,y:-12,duration:.6}},{J(p2_seg-1.4)});
tl.to("#kw_p2b",{{opacity:0,duration:1.0}},{J(p2_seg-1.4)});
tl.to("#fv_p2b",{{opacity:0,duration:1.0}},{J(p2_seg-1.0)});tl.set("#fv_p2b",{{opacity:0}},{J(p2_seg)});
tl.to("#tint_p2b",{{opacity:0,duration:1.0}},{J(p2_seg-1.0)});tl.set("#tint_p2b",{{opacity:0}},{J(p2_seg)});
tl.to("#ch_p2 .rail, #src_p2",{{opacity:0,duration:.6}},{J(p2_seg-0.6)});tl.set("#ch_p2 .rail, #src_p2",{{opacity:0}},{J(p2_seg)});'''

# recap + outro JS
recap_js="".join(f'tl.fromTo("#rc{i+1}",{{opacity:0}},{{opacity:1,duration:.25}},{f(OUTRO_T+LEAD+i*RECAP_EACH)});tl.to("#rc{i+1}",{{opacity:0,duration:.2}},{f(OUTRO_T+LEAD+(i+1)*RECAP_EACH-0.1)});tl.set("#rc{i+1}",{{opacity:0}},{f(OUTRO_T+LEAD+(i+1)*RECAP_EACH)});' for i in range(RECAP_N))
ot0=OUTRO_T+LEAD+RECAP
js_outro=f'''
tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.6,ease:"power2.out"}},{f(OUTRO_T+RECAP*0.55)});
tl.fromTo(".ot-rule",{{opacity:0,scaleX:0}},{{opacity:.85,scaleX:1,duration:.7,ease:"power2.out",transformOrigin:"0% 50%"}},{f(ot0)});
{''.join(f'tl.fromTo(".ot-list .ot-li:nth-child({i+1})",{{opacity:0,x:-18}},{{opacity:1,x:0,duration:.45,ease:"power2.out"}},{f(ot0+0.3+i*0.16)});' for i in range(5))}
tl.fromTo(".ot-q",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(ot0+1.6)});
tl.fromTo(".ot-deb",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.7}},{f(ot0+2.8)});
tl.fromTo(".ot-cta",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.6}},{f(ot0+4.0)});
tl.to("#outro",{{opacity:1,duration:.1}},{f(TOTAL-0.2)});'''

JS=f'''
tl.set("#cover",{{opacity:1}},0);
tl.set(".cv-disc,.cv-sheen,.cv-halo,.cv-hero,.cv-eyebrow,.cv-paper,.cv-title,.cv-sub,.cv-rule,.cv-foot",{{opacity:1}},0);
tl.to(".cv-sheen",{{rotation:-12,duration:4,ease:"sine.inOut"}},0.4);
tl.to(".cv-hero",{{scale:1.02,duration:3.4,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"50% 50%"}},0.6);
tl.to("#cover",{{opacity:0,duration:.7,ease:"power2.in"}},{f(COVER_D-0.7)});tl.set("#cover",{{opacity:0}},{f(COVER_D)});
tl.set("#hook",{{opacity:1}},{f(COVER_D)});
tl.to(".hk-glow",{{opacity:.85,duration:1.4,stagger:.35}},{f(COVER_D+0.1)});
tl.to(".hk-g1",{{x:120,y:-40,duration:9,ease:"sine.inOut"}},{f(COVER_D)});tl.to(".hk-g2",{{x:-100,y:40,duration:9,ease:"sine.inOut"}},{f(COVER_D)});
tl.to(".hk-band",{{opacity:.55,duration:1.6,stagger:.3}},{f(COVER_D+0.4)});
tl.to(".hk-b1",{{x:80,duration:8,ease:"none"}},{f(COVER_D)});tl.to(".hk-b2",{{x:-80,duration:8,ease:"none"}},{f(COVER_D)});
tl.to(".hk-rain",{{opacity:1,duration:1.2}},{f(COVER_D+0.6)});
tl.fromTo(".hk-rain",{{backgroundPositionY:"0px"}},{{backgroundPositionY:"600px",duration:{f(OPEN_END-COVER_D)},ease:"none"}},{f(COVER_D)});
tl.fromTo(".hk-disc",{{opacity:0,rotation:0}},{{opacity:.6,rotation:120,duration:{f(OPEN_END-COVER_D)},ease:"none"}},{f(COVER_D+0.4)});
tl.to(".hk-frag",{{opacity:1,duration:1.6,stagger:.5}},{f(COVER_D+0.8)});
tl.fromTo("#hkt1",{{opacity:0,y:24,scale:.96}},{{opacity:1,y:0,scale:1,duration:.9,ease:"power3.out"}},{f(COVER_D+1.2)});
tl.fromTo("#hkt2",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(COVER_D+4.6)});
tl.to("#hook",{{opacity:0,duration:.8,ease:"power2.in"}},{f(OPEN_END-0.8)});tl.set("#hook",{{opacity:0}},{f(OPEN_END)});
{js_std(PARTS[0])}
{js_p2}
{js_std(PARTS[1])}
{js_std(PARTS[2])}
{js_std(PARTS[3])}
{recap_js}
{js_outro}
'''

html=f'''<!doctype html><html lang="zh"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@600;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
{std_html(PARTS[0])}
{part2}
{std_html(PARTS[1])}
{std_html(PARTS[2])}
{std_html(PARTS[3])}
{cover}
{hook}
{outro}
{audio_el}
</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;</script></body></html>'''
Path("hf/index.html").write_text(html,encoding="utf-8")
Path("hf/meta.json").write_text('{"id":"main","name":"caihong-tongming"}',encoding="utf-8")
print("index.html",len(html),"bytes  DONE")
