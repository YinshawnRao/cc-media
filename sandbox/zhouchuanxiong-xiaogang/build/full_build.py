#!/usr/bin/env python3
"""周传雄最“小刚”的5首 — 倒数盘点 5→1（全新主题, 非最难/非低估）。
结构：封面(真人小刚+主题,不暴露排名) → 精简钩子(4行屏幕字+1句旁白) → 标题 → 5×(转场卡 + 倒数章节letterbox)
       → 作品outro(列排名+升华,无投票问句) → 消化位 → 固定引流CTA(全片最后一句,逐字硬约束)。
倒数 5→1：#5舍不得你走 #4风干我的悲伤 #3陪着我尽头 #2吉普赛情人 #1哈萨雅琪(冠军金调)。
色温弧：暖sepia(挽留)→冷灰(失落)→蓝暮(纯情)→金色异域(心动)→明亮少年(名片finale)。
女声 zf_xiaoyi。渲染后必须 ffmpeg mux master.wav。SAMPLE=1 只构建钩子+前两首(样片)。
"""
import subprocess, os, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from outro_cta import FIXED_OUTRO_CTA   # 固定引流 CTA 单一来源（硬约束）

ROOT = Path(__file__).resolve().parent.parent
A = ROOT/"audio"; C = ROOT/"clips"; HF = ROOT/"hf"; SEG = ROOT/"build"/"segs"
SEG.mkdir(parents=True, exist_ok=True)
SAMPLE = bool(os.environ.get("SAMPLE"))
INTRO_BED = A/"intro_bed.wav"   # 舍不得你走 柔声铺底（封面/钩子/标题干净铺底）
OUTRO_BED = A/"outro_bed.wav"   # 哈萨雅琪 副歌铺底（outro+CTA 床, 收在#1）
ARTIST = "周传雄"
# 复用脚本最易漏改写死的上一期专有名词，渲染前自动查禁词。
FORBIDDEN = ["周杰伦","zhoujielun","毕业季","晴天","蒲公英","轨迹","稻香","最长的电影","高考","考场",
             "杰威尔","蔡依林","孙燕姿","五月天","graduation","qingtian","daoxiang"]

def adur(p):
    return round(float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)])),3)
def run(cmd): subprocess.run([str(c) for c in cmd], check=True)
def f(x): return f"{round(x,3)}"

# ---------------- 节奏常量 ----------------
TRANS=3.8; LEADV=0.5; POST=1.3; SWELL=1.6; TAIL=1.5; BED=0.15; TBED=0.24
COVER_D=3.6
HOOK_LEAD=0.6; HOOK_TAIL=1.3
TITLE_HOLD=4.4
OUTRO_LEAD=0.4; DIGEST_O=1.0; OUTRO_TAIL=2.6

# ---------------- 每首歌定义（倒数 5→1）----------------
SONGS = [
 dict(key="shebude", rank="第 5 名", name="舍不得你走", emo="挽留", year="1991", album="早期小刚",
      clip="vert_shebude", show=44.0, ghost="舍", acc="#E0A861", mgain=1.06,
      nm_sz=72, subline="刚要失去时，那种说不出口的不舍",
      trans=["故事，从这一首说起","它没有后来的撕心裂肺","只是年轻时，最青涩的告别"],
      src="官方 MV · DVD",
      tint="linear-gradient(180deg,rgba(224,168,97,.18) 0%,rgba(150,108,52,.08) 34%,rgba(60,40,18,.34) 68%,rgba(20,13,6,.74) 100%)",
      ttop="linear-gradient(180deg,rgba(16,10,4,.42) 0%,rgba(16,10,4,0) 26%)",
      ghostcol="rgba(231,178,110,.18)"),
 dict(key="fenggan", rank="第 4 名", name="风干我的悲伤", emo="失落", year="1993", album="早期小刚",
      clip="vert_fenggan", show=44.0, ghost="风", acc="#9CB8CE", mgain=1.12,
      nm_sz=62, subline="悲伤不是爆炸，是被时间吹干",
      trans=["再往前一首","它的悲伤很清瘦、很干净","刚学会失去的少年，藏不住难过"],
      src="早期 MV · 絲路版",
      tint="linear-gradient(180deg,rgba(156,184,206,.16) 0%,rgba(90,110,128,.10) 36%,rgba(34,44,56,.42) 70%,rgba(12,16,22,.78) 100%)",
      ttop="linear-gradient(180deg,rgba(8,11,16,.46) 0%,rgba(8,11,16,0) 26%)",
      ghostcol="rgba(170,196,216,.18)"),
 dict(key="peizhe", rank="第 3 名", name="陪着我一直到世界的尽头", emo="纯情", year="早期", album="早期小刚",
      clip="vert_peizhe", show=44.0, ghost="陪", acc="#8AAEDC", mgain=1.14,
      nm_sz=46, subline="把“永远”说得很认真、很用力",
      trans=["继续往上走","光是这个歌名，就很九十年代","少年相信，真能陪一个人到尽头"],
      src="高清 MV",
      tint="linear-gradient(180deg,rgba(138,174,220,.18) 0%,rgba(70,100,150,.12) 38%,rgba(22,40,70,.48) 72%,rgba(6,12,24,.82) 100%)",
      ttop="linear-gradient(180deg,rgba(6,10,20,.50) 0%,rgba(6,10,20,0) 26%)",
      ghostcol="rgba(150,186,224,.18)"),
 dict(key="jipu", rank="第 2 名", name="吉普赛情人", emo="心动", year="早期", album="早期小刚",
      clip="vert_jipu", show=44.0, ghost="吉", acc="#EAB94E", mgain=1.10,
      nm_sz=66, subline="第一次看见爱情，眼睛是亮的",
      trans=["越靠前，越经典","标签感拉满的一首","九十年代才有的，异域浪漫"],
      src="早期 MV",
      tint="linear-gradient(180deg,rgba(234,185,78,.20) 0%,rgba(170,120,40,.12) 34%,rgba(70,46,16,.40) 68%,rgba(24,16,6,.78) 100%)",
      ttop="linear-gradient(180deg,rgba(18,12,5,.46) 0%,rgba(18,12,5,0) 26%)",
      ghostcol="rgba(238,196,100,.20)"),
 dict(key="hasa", rank="第 1 名", name="哈萨雅琪", emo="名片", year="1992", album="早期小刚",
      clip="vert_hasa", show=48.0, ghost="哈", acc="#FFC94D", mgain=1.00, champ=True,
      nm_sz=78, subline="一首歌，让路人懂什么叫小刚",
      trans=["而压轴的这一首","小刚时期的一张声音名片","声音明亮、带着少年冲劲的他"],
      src="台版 LD · 1992",
      tint="linear-gradient(180deg,rgba(255,222,150,.20) 0%,rgba(240,196,110,.08) 32%,rgba(120,90,40,.20) 64%,rgba(40,28,12,.60) 100%)",
      ttop="linear-gradient(180deg,rgba(16,11,5,.38) 0%,rgba(16,11,5,0) 24%)",
      ghostcol="rgba(255,210,110,.22)"),
]
if SAMPLE:
    SONGS = SONGS[:2]
    print("*** SAMPLE MODE: hook + songs #5,#4 only ***")

for i,s in enumerate(SONGS): s["voice"] = adur(A/f"s{i+1}_voice.wav")
HOOK_V  = adur(A/"hook_voice.wav")
OUTRO_V = adur(A/"outro_voice.wav")
CTA_V   = adur(A/"cta_voice.wav")

HOOK_D  = round(HOOK_LEAD + HOOK_V + HOOK_TAIL, 3)
OUTRO_D = round(OUTRO_LEAD + OUTRO_V + DIGEST_O + CTA_V + OUTRO_TAIL, 3)
CTA_LOCAL = round(OUTRO_LEAD + OUTRO_V + DIGEST_O, 3)

def chap_anchors(s):
    voice_at = TRANS + LEADV
    v1   = voice_at + s["voice"]
    sw0  = v1 + POST
    full0= sw0 + SWELL
    full1= full0 + s["show"]
    dur  = full1 + TAIL
    return dict(voice_at=voice_at, v1=v1, sw0=sw0, full0=full0, full1=full1, dur=round(dur,3))

# ---------------- 绝对时间轴 ----------------
COVER_T=0.0
HOOK_T = COVER_D
TITLE_T= round(COVER_D + HOOK_D, 3)
CH1    = round(TITLE_T + TITLE_HOLD, 3)
t = CH1
for s in SONGS:
    a = chap_anchors(s); s["anchor"]=a
    s["start"]=t; s["end"]=round(t+a["dur"],3)
    t = s["end"]
OUTRO_T = round(t, 3)
TOTAL = round(OUTRO_T + OUTRO_D, 3)
print(f"COVER 0-{COVER_D} HOOK {HOOK_T}-{TITLE_T} TITLE {TITLE_T}-{CH1}")
print("chapter starts:", {s["key"]:(s["start"],s["end"]) for s in SONGS})
print(f"OUTRO {OUTRO_T}-{TOTAL} (CTA@local {CTA_LOCAL})  TOTAL {TOTAL}s = {int(TOTAL//60)}:{TOTAL%60:05.2f}")

# =====================================================================
#  AUDIO
# =====================================================================
def build_open():
    dur = COVER_D
    run(["ffmpeg","-v","error","-i",INTRO_BED,"-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
         f"atrim=0:{dur},asetpts=PTS-STARTPTS,volume=0.16,afade=t=in:st=0:d=1.0[out]",
         "-map","[out]","-ac","2","-ar","48000",SEG/"seg_open.wav","-y"])

def build_hook():
    dur = HOOK_D; va = HOOK_LEAD
    run(["ffmpeg","-v","error","-i",INTRO_BED,"-i",A/"hook_voice.wav","-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
         f"atrim={COVER_D}:{COVER_D+dur},asetpts=PTS-STARTPTS,volume=0.17[bed];"
         f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{dur},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",SEG/"seg_hook.wav","-y"])

def build_title():
    dur = TITLE_HOLD; st = COVER_D + HOOK_D
    run(["ffmpeg","-v","error","-i",INTRO_BED,"-filter_complex",
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
         f"atrim={st}:{st+dur},asetpts=PTS-STARTPTS,volume=0.20,afade=t=out:st={dur-0.6}:d=0.6[out]",
         "-map","[out]","-ac","2","-ar","48000",SEG/"seg_title.wav","-y"])

def build_chapter_seg(i, s):
    a=s["anchor"]; dur=a["dur"]; va=a["voice_at"]; sw0=a["sw0"]; full0=a["full0"]; full1=a["full1"]
    ve=(f"(lt(t,1.0))*({TBED}*t/1.0)"
        f"+(between(t,1.0,{TRANS}))*{TBED}"
        f"+(between(t,{TRANS},{va}))*({TBED}+({BED}-{TBED})*(t-{TRANS})/{va-TRANS})"
        f"+(between(t,{va},{sw0}))*{BED}"
        f"+(between(t,{sw0},{full0}))*({BED}+{1.0-BED}*(t-{sw0})/{SWELL})"
        f"+(gte(t,{full0}))*1.0")
    out=SEG/f"seg_{s['key']}.wav"
    run(["ffmpeg","-v","error","-i",C/f"{s['clip']}.mp4","-i",A/f"s{i+1}_voice.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume=2.0[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.0:LRA=11,"
         f"atrim=0:{dur},asetpts=PTS-STARTPTS,volume='{ve}':eval=frame,volume={s['mgain']},afade=t=out:st={full1}:d={TAIL}[music];"
         f"[voice][music]amix=inputs=2:normalize=0:duration=longest,atrim=0:{dur},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",out,"-y"])

def build_outro():
    dur=OUTRO_D; va=OUTRO_LEAD; cta=CTA_LOCAL
    run(["ffmpeg","-v","error","-i",OUTRO_BED,"-i",A/"outro_voice.wav","-i",A/"cta_voice.wav",
         "-filter_complex",
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(va*1000)}|{int(va*1000)},volume=2.0[v1];"
         f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(cta*1000)}|{int(cta*1000)},volume=2.0[v2];"
         f"[v1][v2]amix=inputs=2:normalize=0:duration=longest[voice];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-15:TP=-1.5:LRA=11,"
         f"atrim=0:{dur},asetpts=PTS-STARTPTS,volume=0.22,afade=t=in:st=0:d=1.2,afade=t=out:st={dur-1.6}:d=1.6[bed];"
         f"[voice][bed]amix=inputs=2:normalize=0:duration=longest,atrim=0:{dur},alimiter=limit=0.95:level=disabled[out]",
         "-map","[out]","-ac","2","-ar","48000",SEG/"seg_outro.wav","-y"])

build_open(); build_hook(); build_title()
for i,s in enumerate(SONGS): print("audio",s["key"]); build_chapter_seg(i,s)
build_outro()

listfile = SEG/"list.txt"
names = ["seg_open.wav","seg_hook.wav","seg_title.wav"]+[f"seg_{s['key']}.wav" for s in SONGS]+["seg_outro.wav"]
listfile.write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")
run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",listfile,"-ac","2","-ar","48000",ROOT/"master.wav","-y"])
print("master:", adur(ROOT/"master.wav"), "planned:", TOTAL)

# HF assets
HF.mkdir(exist_ok=True); (HF/"clips_seg").mkdir(exist_ok=True)
shutil.copy(ROOT/"master.wav", HF/"master.wav")
if (ROOT/"hf"/"cover_assets").exists(): shutil.rmtree(ROOT/"hf"/"cover_assets")
shutil.copytree(ROOT/"assets", HF/"cover_assets")
for s in SONGS:
    a=s["anchor"]
    run(["ffmpeg","-v","error","-i",C/f"{s['clip']}.mp4","-t",str(a["dur"]+0.4),
         "-c:v","libx264","-preset","veryfast","-r","30","-g","30","-keyint_min","30","-pix_fmt","yuv420p","-an",
         HF/"clips_seg"/f"{s['key']}.mp4","-y"])
print("clips_seg done")

# =====================================================================
#  HTML / CSS / JS
# =====================================================================
CSS = r'''
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1920px;overflow:hidden;background:#06070c;
  font-family:"Noto Serif SC",serif;color:#20242c;-webkit-font-smoothing:antialiased;}
.layer{position:absolute;inset:0;width:1080px;height:1920px;}
.grain{position:absolute;inset:0;pointer-events:none;mix-blend-mode:overlay;opacity:.5;
  background-image:radial-gradient(circle at 12% 22%,rgba(255,255,255,.05) 0 .5px,transparent .9px),
   radial-gradient(circle at 76% 64%,rgba(0,0,0,.05) 0 .5px,transparent .9px),
   radial-gradient(circle at 44% 88%,rgba(255,255,255,.04) 0 .4px,transparent .8px);
  background-size:200px 200px,240px 240px,170px 170px;}

/* ===== COVER (小刚时期 · 缤纷怀旧, 居中) ===== */
#cover{z-index:60;overflow:hidden;
  background:
   radial-gradient(circle at 50% 33%, rgba(255,224,150,.55) 0%, rgba(255,184,96,0) 40%),
   radial-gradient(circle at 50% 33%, rgba(255,110,150,.32) 0%, rgba(255,110,150,0) 56%),
   radial-gradient(circle at 16% 84%, rgba(64,200,210,.26) 0%, rgba(64,200,210,0) 42%),
   radial-gradient(circle at 86% 88%, rgba(150,90,220,.30) 0%, rgba(150,90,220,0) 46%),
   linear-gradient(168deg,#1c1140 0%,#4a1d5e 22%,#922e64 44%,#cf5560 62%,#ec7d3e 82%,#f6b34c 100%);}
.cv-vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,rgba(0,0,0,0) 46%,rgba(15,6,30,.5) 100%);}
.cv-rays{position:absolute;left:50%;top:560px;transform:translate(-50%,-50%);width:1180px;height:1180px;border-radius:50%;opacity:.5;
  background:repeating-conic-gradient(from 0deg at 50% 50%, rgba(255,238,200,.16) 0deg 4deg, rgba(255,238,200,0) 4deg 13deg);
  -webkit-mask:radial-gradient(circle,#000 24%,transparent 62%);mask:radial-gradient(circle,#000 24%,transparent 62%);}
.cv-halo{position:absolute;left:50%;top:560px;transform:translate(-50%,-50%);width:640px;height:640px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,236,196,.85) 0%,rgba(255,196,120,.35) 40%,rgba(255,170,90,0) 70%);filter:blur(6px);}
.cv-ringD{position:absolute;left:50%;top:560px;transform:translate(-50%,-50%);width:566px;height:566px;border-radius:50%;
  border:2px dashed rgba(255,232,190,.65);}
.cv-portrait{position:absolute;left:50%;top:560px;transform:translate(-50%,-50%);width:474px;height:474px;border-radius:50%;
  overflow:hidden;box-shadow:0 24px 70px rgba(40,8,40,.6),0 0 0 7px rgba(255,255,255,.14),0 0 0 11px rgba(255,205,120,.85),0 0 0 13px rgba(255,170,90,.4);}
.cv-portrait img{width:100%;height:100%;object-fit:cover;object-position:50% 22%;filter:saturate(1.08) contrast(1.05) brightness(1.03);}
.cv-portrait::after{content:"";position:absolute;inset:0;border-radius:50%;background:linear-gradient(180deg,rgba(255,180,90,.12) 0%,rgba(60,10,50,.28) 100%);mix-blend-mode:soft-light;}
.spk{position:absolute;border-radius:50%;background:radial-gradient(circle,#fff 0%,rgba(255,240,200,.7) 30%,transparent 70%);
  box-shadow:0 0 12px rgba(255,235,190,.9);}
.cv-eyebrow{position:absolute;left:0;right:0;top:150px;text-align:center;z-index:3;font-family:"Noto Sans SC",sans-serif;
  font-size:25px;font-weight:800;letter-spacing:.42em;color:#ffe7b8;text-shadow:0 2px 14px rgba(60,10,40,.7);}
.cv-eyebrow .dot{color:#ffd86a;}
.cv-text{position:absolute;left:50px;right:50px;top:864px;text-align:center;z-index:3;}
.cv-h1{font-size:90px;font-weight:900;line-height:1.08;letter-spacing:-1px;
  background:linear-gradient(180deg,#fffefb 0%,#ffe9c0 55%,#ffcf86 100%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 4px 20px rgba(40,6,30,.55));}
.cv-h1 .q{background:linear-gradient(180deg,#fff2c2 0%,#ffc24d 60%,#ff9d3a 100%);-webkit-background-clip:text;background-clip:text;color:transparent;}
.cv-rule{width:160px;height:0;margin:30px auto 26px;position:relative;}
.cv-rule::before{content:"";position:absolute;left:0;top:0;width:100%;height:3px;border-radius:2px;
  background:linear-gradient(90deg,transparent,#ffd277 30%,#ff8fb0 50%,#ffd277 70%,transparent);}
.cv-rule::after{content:"✦";position:absolute;left:50%;top:-19px;transform:translateX(-50%);color:#ffe39a;font-size:26px;text-shadow:0 0 12px rgba(255,210,120,.9);}
.cv-sub{font-family:"Noto Sans SC",sans-serif;font-size:31px;font-weight:500;line-height:1.55;color:#ffe6d2;text-shadow:0 2px 12px rgba(50,8,30,.6);}
.cv-tag{display:inline-block;margin-top:30px;font-family:"Noto Sans SC",sans-serif;font-size:24px;font-weight:800;letter-spacing:.28em;
  color:#2a0e2a;background:linear-gradient(90deg,#ffe39a,#ffc05a);border-radius:30px;padding:11px 30px;box-shadow:0 10px 26px rgba(60,10,40,.4),0 0 0 1px rgba(255,255,255,.25) inset;}

/* ===== HOOK ===== */
#hook{z-index:58;background:linear-gradient(178deg,#161009 0%,#221708 48%,#0c0805 100%);opacity:0;overflow:hidden;}
.hk-glow{position:absolute;top:-120px;left:50%;transform:translateX(-50%);width:900px;height:520px;
  background:radial-gradient(ellipse at center,rgba(255,200,130,.20) 0%,rgba(255,190,110,0) 70%);}
.hk-wrap{position:absolute;left:84px;right:84px;top:700px;text-align:center;}
.hk-l{font-size:64px;font-weight:600;line-height:1.5;color:#efe3cf;opacity:0;letter-spacing:.02em;text-shadow:0 3px 22px rgba(0,0,0,.6);}
.hk-l.accent{font-weight:800;color:#FFCB5C;font-size:72px;}

/* ===== TITLE ===== */
#title{z-index:54;background:linear-gradient(170deg,#2a1c10 0%,#160f08 100%);opacity:0;overflow:hidden;}
.ti-vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,rgba(255,210,140,.18) 0%,rgba(40,28,14,0) 58%);}
.ti-wrap{position:absolute;left:80px;right:80px;top:720px;text-align:center;}
.ti-eyebrow{font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:700;letter-spacing:.42em;color:#e8c982;margin-bottom:34px;opacity:0;}
.ti-l1{font-size:80px;font-weight:900;line-height:1.18;color:#fbf2e2;letter-spacing:-1px;opacity:0;}
.ti-l2{font-size:92px;font-weight:900;line-height:1.2;color:#FFCB5C;letter-spacing:-1px;margin-top:14px;opacity:0;}
.ti-l2 .q{color:#fbf2e2;}
.ti-rule{width:0;height:3px;background:#e6b25e;margin:40px auto 0;}

/* ===== CHAPTERS ===== */
.fv{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;z-index:1;opacity:0;}
.tint{position:absolute;inset:0;z-index:2;opacity:0;}
.tinttop{position:absolute;inset:0;z-index:2;opacity:0;}
.chrome{position:absolute;inset:0;z-index:4;pointer-events:none;}
.card{position:absolute;top:150px;right:54px;width:600px;padding:38px 44px 36px;border-radius:24px;
  background:linear-gradient(160deg,rgba(245,250,255,.15),rgba(245,250,255,.05));
  backdrop-filter:blur(26px);-webkit-backdrop-filter:blur(26px);
  border:1.5px solid rgba(246,250,255,.28);box-shadow:0 30px 80px rgba(0,0,0,.45);opacity:0;}
.card.champ{border:1.6px solid rgba(255,201,77,.6);box-shadow:0 30px 90px rgba(0,0,0,.5),0 0 0 1px rgba(255,201,77,.3),0 0 60px rgba(255,201,77,.18);}
.rank-row{display:flex;align-items:center;gap:14px;}
.card-rank{font-family:"Noto Sans SC",sans-serif;font-size:38px;font-weight:900;letter-spacing:.06em;}
.champ-tag{font-family:"Noto Sans SC",sans-serif;font-size:22px;font-weight:800;letter-spacing:.16em;color:#1a1206;
  background:linear-gradient(90deg,#FFD874,#E8A93C);border-radius:20px;padding:5px 16px;}
.card-name{font-weight:900;color:#fbf7ef;letter-spacing:.5px;line-height:1.08;margin-top:14px;}
.card-emo{font-family:"Noto Sans SC",sans-serif;font-size:32px;font-weight:700;margin-top:12px;}
.card-credit{font-family:"Noto Sans SC",sans-serif;font-size:25px;font-weight:500;line-height:1.5;color:rgba(248,247,240,.72);margin-top:18px;letter-spacing:.02em;}
.kw{position:absolute;left:0;right:0;bottom:560px;text-align:center;font-size:300px;font-weight:900;line-height:.85;opacity:0;letter-spacing:-6px;}
.subline{position:absolute;left:70px;right:70px;bottom:300px;text-align:center;font-size:44px;font-weight:600;color:#fbf7ef;opacity:0;letter-spacing:.02em;text-shadow:0 3px 24px rgba(0,0,0,.7);}
.src{position:absolute;bottom:52px;left:0;right:0;text-align:center;font-family:"Noto Sans SC",sans-serif;font-size:19px;font-weight:400;color:rgba(248,247,240,.32);letter-spacing:.22em;opacity:0;}

/* ===== TRANSITION CARDS ===== */
.trans{position:absolute;inset:0;z-index:40;opacity:0;background:linear-gradient(180deg,#161009 0%,#08060b 100%);}
.tr-wrap{position:absolute;left:90px;right:90px;top:800px;text-align:center;}
.tr-num{font-family:"Noto Sans SC",sans-serif;font-size:34px;font-weight:900;letter-spacing:.2em;margin-bottom:30px;opacity:0;}
.tr-l{font-size:54px;font-weight:600;line-height:1.44;color:#efe3cf;opacity:0;letter-spacing:.02em;}
.tr-l.accent{font-weight:700;}

/* ===== OUTRO (缤纷收尾, 居中) ===== */
#outro{z-index:52;opacity:0;overflow:hidden;
  background:
   radial-gradient(circle at 50% 24%, rgba(255,220,150,.42) 0%, rgba(255,184,96,0) 40%),
   radial-gradient(circle at 50% 24%, rgba(255,120,150,.24) 0%, rgba(255,120,150,0) 52%),
   radial-gradient(circle at 86% 88%, rgba(150,90,220,.30) 0%, rgba(150,90,220,0) 46%),
   radial-gradient(circle at 14% 90%, rgba(64,200,210,.22) 0%, rgba(64,200,210,0) 44%),
   linear-gradient(170deg,#160c34 0%,#3a1850 24%,#7c2858 46%,#b94e52 68%,#e0743b 100%);}
.ot-vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 40%,rgba(0,0,0,0) 44%,rgba(12,4,26,.5) 100%);}
.ot-rays{position:absolute;left:50%;top:340px;transform:translate(-50%,-50%);width:1100px;height:1100px;border-radius:50%;opacity:.38;
  background:repeating-conic-gradient(from 0deg at 50% 50%, rgba(255,236,200,.14) 0deg 4deg, rgba(255,236,200,0) 4deg 13deg);
  -webkit-mask:radial-gradient(circle,#000 12%,transparent 56%);mask:radial-gradient(circle,#000 12%,transparent 56%);}
.ot-wrap{position:absolute;left:54px;right:54px;top:236px;text-align:center;}
.ot-h1{font-size:72px;font-weight:900;line-height:1.16;letter-spacing:-1px;opacity:0;
  background:linear-gradient(180deg,#fffefb,#ffe6bb 60%,#ffcd86);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 4px 18px rgba(30,4,24,.5));}
.ot-h2{font-size:50px;font-weight:900;line-height:1.22;letter-spacing:-1px;margin-top:12px;opacity:0;
  background:linear-gradient(180deg,#ffe7a0,#ffbf52);-webkit-background-clip:text;background-clip:text;color:transparent;}
.ot-recap{margin-top:42px;display:flex;flex-direction:column;gap:14px;align-items:center;}
.ot-row{display:flex;align-items:center;gap:18px;opacity:0;padding:11px 30px;border-radius:40px;min-width:560px;justify-content:center;
  background:linear-gradient(120deg,rgba(255,255,255,.12),rgba(255,255,255,.04));border:1.5px solid rgba(255,236,200,.22);}
.orank{font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:900;color:#ffd277;letter-spacing:.04em;min-width:96px;text-align:right;}
.oname{font-family:"Noto Sans SC",sans-serif;font-size:30px;font-weight:700;color:#fff4e6;}
.ot-row.r1{padding:15px 34px;min-width:600px;background:linear-gradient(120deg,rgba(255,206,90,.30),rgba(255,150,80,.14));
  border:1.6px solid rgba(255,210,110,.7);box-shadow:0 12px 36px rgba(60,10,40,.4),0 0 34px rgba(255,200,90,.22);}
.ot-row.r1 .orank{font-size:31px;color:#fff0c2;}
.ot-row.r1 .oname{font-size:37px;font-weight:900;color:#fff;}
.ot-row.r1 .crown{font-size:30px;filter:drop-shadow(0 0 10px rgba(255,210,120,.9));}
.ot-sub{font-family:"Noto Sans SC",sans-serif;font-size:29px;font-weight:600;color:#ffe6d2;margin-top:36px;opacity:0;text-shadow:0 2px 12px rgba(40,8,30,.5);}
.ot-cta{position:absolute;left:60px;right:60px;bottom:138px;text-align:center;opacity:0;}
.ot-cta .q1{font-family:"Noto Sans SC",sans-serif;font-size:40px;font-weight:900;
  background:linear-gradient(180deg,#fffefb,#ffe2ad);-webkit-background-clip:text;background-clip:text;color:transparent;}
.ot-cta .q2{display:inline-block;margin-top:20px;font-family:"Noto Sans SC",sans-serif;font-size:27px;font-weight:800;letter-spacing:.2em;
  color:#2a0e2a;background:linear-gradient(90deg,#ffe39a,#ffc05a);border-radius:30px;padding:11px 30px;box-shadow:0 10px 24px rgba(60,10,40,.4);}
'''

def sparkles(specs):
    return "".join(f'<div class="spk" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;opacity:{o}"></div>' for x,y,s,o in specs)
COVER_SPK=[(150,300,16,.95),(930,330,20,.9),(110,560,11,.8),(975,600,14,.85),(180,820,18,.9),
           (905,840,12,.8),(250,210,10,.7),(835,205,13,.8),(60,430,9,.65),(1015,470,10,.7)]
cover_html=f'''<div id="cover" class="layer">
  <div class="cv-vig"></div>
  <div class="cv-rays" id="cvRays"></div>
  <div class="cv-halo"></div>
  <div class="cv-ringD" id="cvRing"></div>
  <div class="cv-portrait"><img src="cover_assets/portrait.png" alt=""></div>
  {sparkles(COVER_SPK)}
  <div class="cv-eyebrow">怀旧金曲盘点 <span class="dot">·</span> {ARTIST}</div>
  <div class="cv-text">
    <div class="cv-h1">{ARTIST}最<span class="q">“小刚”</span>的<br>5 首歌</div>
    <div class="cv-rule"></div>
    <div class="cv-sub">在他变苦、变成熟之前，<br>那个声音最亮的少年</div>
    <div class="cv-tag">TOP 5 · 倒数揭晓</div>
  </div><div class="grain"></div>
</div>'''

HOOK_LINES=["在他唱黄昏之前","在他唱尽苦情之前","他还有一个名字","叫 小刚"]
hook_html=f'''<div id="hook" class="layer">
  <div class="hk-glow"></div>
  <div class="hk-wrap">
    <div class="hk-l" id="hk0">{HOOK_LINES[0]}</div>
    <div class="hk-l" id="hk1">{HOOK_LINES[1]}</div>
    <div class="hk-l" id="hk2">{HOOK_LINES[2]}</div>
    <div class="hk-l accent" id="hk3">{HOOK_LINES[3]}</div>
  </div><div class="grain"></div>
</div>'''

title_html=f'''<div id="title" class="layer">
  <div class="ti-vig"></div>
  <div class="ti-wrap">
    <div class="ti-eyebrow" id="tiE">回到小刚时期</div>
    <div class="ti-l1" id="tiL1">最能代表他的</div>
    <div class="ti-l2" id="tiL2">这 5 首，最<span class="q">“小刚”</span></div>
    <div class="ti-rule" id="tiR"></div>
  </div><div class="grain"></div>
</div>'''

chap_html=[]
foot_tracks=[0,6,0,6,0]
for i,s in enumerate(SONGS):
    k=s["key"]; champ = s.get("champ", False)
    taghtml = '<span class="champ-tag">压轴 · 最小刚</span>' if champ else ''
    chap_html.append(f'''<video id="fv_{k}" class="fv clip" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{foot_tracks[i]}" src="clips_seg/{k}.mp4" muted playsinline></video>
<div id="tint_{k}" class="clip tint" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{20+i}" style="background:{s['tint']}"></div>
<div id="ttop_{k}" class="clip tinttop" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{30+i}" style="background:{s['ttop']}"></div>
<div id="chrome_{k}" class="clip chrome" data-start="{f(s['start'])}" data-duration="{f(s['anchor']['dur'])}" data-track-index="{40+i}" style="--acc:{s['acc']}">
  <div class="card{' champ' if champ else ''}">
    <div class="rank-row"><span class="card-rank" style="color:{s['acc']}">{s['rank']}</span>{taghtml}</div>
    <div class="card-name" style="font-size:{s['nm_sz']}px">{s['name']}</div>
    <div class="card-emo" style="color:{s['acc']}">｜{s['emo']}</div>
    <div class="card-credit">{ARTIST} · {s['year']}</div>
  </div>
  <div class="kw" id="kw_{k}" style="color:{s['ghostcol']}">{s['ghost']}</div>
  <div class="subline" id="sub_{k}">{s['subline']}</div>
  <div class="src" id="src_{k}">{s['src']}</div>
</div>''')

trans_html=[]
for i,s in enumerate(SONGS):
    k=s["key"]; trl=s["trans"]
    trans_html.append(f'''<div id="trans_{k}" class="clip trans" data-start="{f(s['start'])}" data-duration="{f(TRANS+0.6)}" data-track-index="{50+i}">
  <div class="tr-wrap">
    <div class="tr-num" id="trn_{k}" style="color:{s['acc']}">{s['rank']}</div>
    <div class="tr-l" id="tr1_{k}">{trl[0]}</div>
    <div class="tr-l" id="tr2_{k}">{trl[1]}</div>
    <div class="tr-l accent" id="tr3_{k}" style="color:{s['acc']}">{trl[2]}</div>
  </div>
</div>''')

# outro recap：列排名（第1→第5，冠军在上）
recap = sorted(SONGS, key=lambda s: s["rank"])  # "第 1 名" < "第 5 名" 字符序即排名序
recap_rows="".join(
  f'<div class="ot-row{" r1" if s.get("champ") else ""}" id="orow{i}">'
  f'{"<span class=crown>✦</span>" if s.get("champ") else ""}'
  f'<span class="orank">{s["rank"].replace(" ","")}</span>'
  f'<span class="oname">{s["name"]}</span></div>' for i,s in enumerate(recap))
outro_html=f'''<div id="outro" class="layer">
  <div class="ot-vig"></div><div class="ot-rays" id="otRays"></div>
  <div class="ot-wrap">
    <div class="ot-h1" id="oth1">这就是小刚时期</div>
    <div class="ot-h2" id="oth2">声音最亮的那个少年</div>
    <div class="ot-recap">{recap_rows}</div>
    <div class="ot-sub" id="otsub">把爱情想得简单又用力的，{ARTIST}</div>
  </div>
  <div class="ot-cta" id="otcta">
    <div class="q1">你最想为哪一首投票？</div>
    <div class="q2">点赞 · 收藏 · 关注</div>
  </div>
  <div class="grain"></div>
</div>'''

audio_html=f'<audio id="master" data-start="0" data-duration="{f(TOTAL)}" data-track-index="3" src="master.wav" data-volume="1"></audio>'

# ---------------- JS ----------------
def js_chapter(i,s):
    k=s["key"]; a=s["anchor"]; b=s["start"]; end=s["end"]
    sw0=b+a["sw0"]; full0=b+a["full0"]; full1=b+a["full1"]; fade=end-1.3
    tend=b+TRANS+0.6
    return f'''
// ---- {s["rank"]} {s["name"]} ----
tl.fromTo("#fv_{k}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1.0,duration:1.6,ease:"power2.out"}},{f(b)});
tl.to("#tint_{k}",{{opacity:1,duration:1.4}},{f(b)});
tl.to("#ttop_{k}",{{opacity:1,duration:1.4}},{f(b)});
tl.fromTo("#trans_{k}",{{opacity:0}},{{opacity:1,duration:.5,ease:"power2.out"}},{f(b)});
tl.fromTo("#trn_{k}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.6}},{f(b+0.25)});
tl.fromTo("#tr1_{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.6}},{f(b+0.6)});
tl.fromTo("#tr2_{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.6}},{f(b+1.35)});
tl.fromTo("#tr3_{k}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.7,ease:"power3.out"}},{f(b+2.1)});
tl.to("#trans_{k}",{{opacity:0,duration:.7,ease:"power2.in"}},{f(tend-0.7)});
tl.set("#trans_{k}",{{opacity:0}},{f(tend)});
tl.fromTo("#chrome_{k} .card",{{opacity:0,x:50,y:-16}},{{opacity:1,x:0,y:0,duration:.9,ease:"power3.out"}},{f(b+TRANS+0.3)});
tl.fromTo("#src_{k}",{{opacity:0}},{{opacity:1,duration:.6}},{f(b+TRANS+1.0)});
tl.to("#chrome_{k} .card",{{opacity:0,y:-12,duration:.6,ease:"power2.in"}},{f(sw0-0.1)});
tl.fromTo("#kw_{k}",{{opacity:0,scale:.94}},{{opacity:1,scale:1,duration:1.8,ease:"power3.out"}},{f(full0-0.5)});
tl.fromTo("#sub_{k}",{{opacity:0,y:22}},{{opacity:1,y:0,duration:.9,ease:"power2.out"}},{f(full0+ (s["show"]*0.32))});
tl.to("#sub_{k}",{{opacity:0,y:-12,duration:.7,ease:"power2.in"}},{f(end-1.8)});
tl.to("#fv_{k}",{{opacity:0,duration:1.3,ease:"power1.in"}},{f(fade)});
tl.set("#fv_{k}",{{opacity:0}},{f(end)});
tl.to("#tint_{k}",{{opacity:0,duration:1.3}},{f(fade)});
tl.set("#tint_{k}",{{opacity:0}},{f(end)});
tl.to("#ttop_{k}",{{opacity:0,duration:1.3}},{f(fade)});
tl.set("#ttop_{k}",{{opacity:0}},{f(end)});
tl.to("#kw_{k}",{{opacity:0,duration:1.2}},{f(fade)});
tl.set("#kw_{k}",{{opacity:0}},{f(end)});
tl.to("#src_{k}",{{opacity:0,duration:.7}},{f(fade)});
tl.set("#src_{k}",{{opacity:0}},{f(end)});
'''

HK0=HOOK_T+HOOK_LEAD
JS=f'''
// COVER (首帧即封面: 元素 opacity 起即为1, 只做轻微运动)
tl.set("#cover",{{opacity:1}},0);tl.set(".cv-portrait",{{opacity:1}},0);tl.set(".cv-text",{{opacity:1}},0);
tl.set(".cv-eyebrow",{{opacity:1}},0);tl.set(".cv-halo",{{opacity:1}},0);tl.set(".cv-ringD",{{opacity:1}},0);tl.set(".spk",{{opacity:1}},0);
tl.fromTo("#cvRays",{{rotation:0}},{{rotation:18,duration:{f(COVER_D)},ease:"none",transformOrigin:"50% 50%"}},0);
tl.fromTo("#cvRing",{{rotation:0}},{{rotation:-12,duration:{f(COVER_D)},ease:"none",transformOrigin:"50% 50%"}},0);
tl.fromTo(".cv-halo",{{scale:.97}},{{scale:1.045,duration:1.8,yoyo:true,repeat:1,ease:"sine.inOut",transformOrigin:"50% 50%"}},0);
tl.fromTo(".cv-portrait",{{scale:1.0}},{{scale:1.022,duration:3.4,ease:"sine.inOut",transformOrigin:"50% 50%"}},0);
tl.fromTo(".spk",{{scale:.55,opacity:.5}},{{scale:1.1,opacity:1,duration:1.0,yoyo:true,repeat:2,stagger:.1,ease:"sine.inOut",transformOrigin:"50% 50%"}},0);
tl.to("#cover",{{opacity:0,duration:.6,ease:"power2.in"}},{f(COVER_D-0.3)});
tl.set("#cover",{{opacity:0}},{f(COVER_D+0.1)});
// HOOK
tl.fromTo("#hook",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(HOOK_T-0.25)});
tl.fromTo("#hk0",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7}},{f(HK0+0.1)});
tl.fromTo("#hk1",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7}},{f(HK0+1.9)});
tl.fromTo("#hk2",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7}},{f(HK0+3.7)});
tl.fromTo("#hk3",{{opacity:0,y:20,scale:.92}},{{opacity:1,y:0,scale:1,duration:.9,ease:"power3.out"}},{f(HK0+5.4)});
tl.to("#hook",{{opacity:0,duration:.6,ease:"power2.in"}},{f(TITLE_T-0.3)});
tl.set("#hook",{{opacity:0}},{f(TITLE_T+0.1)});
// TITLE
tl.fromTo("#title",{{opacity:0}},{{opacity:1,duration:.7,ease:"power2.out"}},{f(TITLE_T-0.1)});
tl.fromTo("#tiE",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.6}},{f(TITLE_T+0.4)});
tl.fromTo("#tiL1",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(TITLE_T+0.7)});
tl.fromTo("#tiL2",{{opacity:0,y:34}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(TITLE_T+1.3)});
tl.fromTo("#tiR",{{width:0}},{{width:160,duration:.8,ease:"power2.out"}},{f(TITLE_T+2.0)});
tl.to("#title",{{opacity:0,duration:.7,ease:"power2.in"}},{f(CH1-0.4)});
tl.set("#title",{{opacity:0}},{f(CH1+0.2)});
{''.join(js_chapter(i,s) for i,s in enumerate(SONGS))}
// OUTRO (列排名+升华) → 消化位 → 固定 CTA
tl.fromTo("#outro",{{opacity:0}},{{opacity:1,duration:.8,ease:"power2.out"}},{f(OUTRO_T-0.3)});
tl.fromTo("#oth1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.8,ease:"power3.out"}},{f(OUTRO_T+0.5)});
tl.fromTo("#oth2",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.9,ease:"power3.out"}},{f(OUTRO_T+1.3)});
{''.join(f'tl.fromTo("#orow{i}",{{opacity:0,x:-16}},{{opacity:1,x:0,duration:.45}},{f(OUTRO_T+2.5+i*0.34)});' for i in range(len(SONGS)))}
tl.fromTo("#otsub",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.7}},{f(OUTRO_T+2.5+len(SONGS)*0.34+0.4)});
tl.to(".ot-wrap",{{opacity:0,y:-16,duration:.6,ease:"power2.in"}},{f(OUTRO_T+CTA_LOCAL-0.7)});
tl.fromTo("#otcta",{{opacity:0,y:18}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},{f(OUTRO_T+CTA_LOCAL-0.2)});
tl.to("#outro",{{opacity:1,duration:.1}},{f(TOTAL-0.2)});
'''

html=f'''<!doctype html>
<html lang="zh"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f(TOTAL)}" data-width="1080" data-height="1920">
  {''.join(chap_html)}
  {''.join(trans_html)}
  {cover_html}
  {hook_html}
  {title_html}
  {outro_html}
  {audio_html}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{JS}
window.__timelines["main"]=tl;
</script></body></html>'''

(HF/"index.html").write_text(html, encoding="utf-8")
(HF/"meta.json").write_text('{"id":"main","name":"zhouchuanxiong-xiaogang"}', encoding="utf-8")
print("index.html:", len(html), "bytes ; TOTAL", TOTAL)
print("FIXED CTA:", FIXED_OUTRO_CTA)
_hits = sorted({w for w in FORBIDDEN if w in html})
if _hits:
    raise SystemExit(f"!!! LEAK GUARD 失败：index.html 含禁词 {_hits}（疑似复用上一期脚本漏改）。修正后再渲染。")
print(f"leak-guard: CLEAN（无 FORBIDDEN 禁词，ARTIST={ARTIST}）")
print("BUILD DONE", "(SAMPLE)" if SAMPLE else "(FULL)")
