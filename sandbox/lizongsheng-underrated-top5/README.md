# 李宗盛最被低估的5首歌（竖屏盘点，倒数 5→1）

女声盘点短片，~4:41，1080×1920。复用 `guangliang-underrated-top5` 同款长篇叙事盘点流水线。

## 排名（倒数揭晓 5→1）
| 名次 | 歌曲 | 现场源 |
|---|---|---|
| 05 | 一个人 | 既然青春留不住 2016（吉他特写） |
| 04 | 希望 | 既然青春留不住 2016（极特写） |
| 03 | 远行 | 理性与感性 2006（对麦正脸，封面源） |
| 02 | 你像个孩子 | 有歌之年 2026（粉衫，顶裁水印） |
| 01 | 和自己赛跑的人 | 有歌之年（蓝衫特写） |

详见 `design.md`（设计/文案）、`SOURCES.md`（双平台选源记录 + YT 失效说明）。

## 复现
```bash
# 1) 女声旁白（开头/转场/结尾全女声 zf_xiaoyi）
../../tools/tts/venv/bin/python build/narrate_segments.py
# 2) 切 footage（letterbox 1080x1920）+ 每首 music/<key>.wav（同源同窗）
python3 build/clips.py
# 3) master.wav + index.html（逐首 loudnorm=I=-14，一个人 +MGAIN 1.3）
python3 build/full_build.py
# 4) 渲染（-w1 + 重试，本机 GPU 截帧随机崩）+ mux 预混音轨
bash build/render_full.sh
bash build/finalize.sh   # ffmpeg mux master.wav → renders/lizongsheng-underrated-top5.mp4
```

## 关键约束（已落实）
- 五首全是李宗盛**本人现场特写**，同源同窗口型同步；无棚版 MV（1986/1993 深曲）。
- letterbox 保原比例，只裁烧词/水印横带；多机位全景/乐队/侧背均避开 show 窗。
- 片头不剧透排名；片尾揭晓 5→1；**全片最后一句为固定引流 CTA**（女声），作品 outro 不带投票问句（防双 CTA）。
- 成片画面无水印/网址/路径/提示词；音频后期 mux（HyperFrames 会压平动态）。
- ⚠️ YouTube cookie 本期失效（缺 SAPISID/HSID/SSID）→ 仅 B站 选源，已在 SOURCES.md 显式标注，待重导后回看。

## 产物
- 成片：`renders/lizongsheng-underrated-top5.mp4`（mux 后为准）
- `renders/`、`raw/`、`clips/`、`*.wav` 已被仓库 .gitignore 排除。
