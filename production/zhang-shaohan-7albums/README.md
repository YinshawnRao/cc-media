# zhang-shaohan-7albums — 张韶涵前7张专辑·冷门遗珠盘点

成片：[`zhang-shaohan-7albums.mp4`](zhang-shaohan-7albums.mp4)（4:59.7 / 1080×1920 / 30 fps / H.264 + AAC stereo / ~208 MB）

**主题**：按发行顺序逐张打捞张韶涵前 7 张正式专辑的"冷门遗珠"——每张选 1 首有 MV、被同期大热歌盖住的代表作，串成一条隐藏成长线（出发 → 漂浮 → 防备 → 寻找 → 直球 → 回头 → 回到自己）。
**风格**：复古华语流行 + 2000 年代青春 MV 感 + 音乐杂志排版；女声电台旁白（zf_xiaoyi）。
**格式参考**：CONVENTIONS.md「长篇叙事盘点 / 音乐时间线」（无排名，按叙事序）。
**素材源约束**：YouTube + B站双边并行搜索，按清晰度 / 干净度 / 立体声 / 现场质量综合挑选；详见 `SOURCES.md`。

## 目录

```
production/zhang-shaohan-7albums/
├── README.md                    — 本文件
├── SOURCES.md                   — 7 首歌每首的源 URL / 切点 / vfill crop 参数
├── design.md                    — 主色板 + 字体 + 时间线 + QA 清单
├── zhang-shaohan-7albums.mp4    — 成片（mux 后）
├── index.html                   — HyperFrames composition（最终版）
├── meta.json / hyperframes.json / package.json  — HF 项目元数据
├── master.wav                   — 预混后的 48kHz stereo 总音轨（mux 用）
├── narration.json               — 16 段 TTS 文本 + 时长记录
├── intro_voice_only.m4a         — 开头旁白单段试听（2.5s-12s）
├── scripts/
│   ├── narration.txt            — 16 段女声文案（intro / 7×voice / 7×mid / outro）
│   ├── narrate_segments.py      — Kokoro zf_xiaoyi TTS 生成
│   ├── build.py                 — 生成 master.wav + index.html + clips_seg/
│   └── finalize.sh              — mux + silencedetect + volumedetect QA
├── audio/                       — 16 段 Kokoro TTS wav（24 kHz）
├── cover_assets/                — 7 张张韶涵 face thumbnail（cover 拼贴用）
├── clips/                       — vfill 后竖屏 1080×1920 mp4（7 首副歌段，~50s 每首）
├── clips_seg/                   — HF 渲染用的逐段切片（与 index.html 对应）
└── raw/                         — yt-dlp 切片的原始 16:9 MV 段（vfill 前）
```

## 复现步骤（从零）

> 假设在 `cc-media/` 仓库根目录，已装好 ffmpeg / yt-dlp / Node 22+ / Kokoro venv（见根 `CLAUDE.md`）。

```bash
# 1. 准备 sandbox 工作区
mkdir -p sandbox/zhang-shaohan-7albums-rebuild/{raw,clips,audio,hf,build}
cd sandbox/zhang-shaohan-7albums-rebuild

# 2. 下载 7 条源（cookie 见 sandbox/www.{youtube,bilibili}.com_cookies.txt）
#    URL / 时间码 / 格式编号 见 ../../production/zhang-shaohan-7albums/SOURCES.md
# yt-dlp --cookies sandbox/www.bilibili.com_cookies.txt --download-sections "*HH:MM:SS-HH:MM:SS" \
#   -f "30112+30280/30080+30280" "https://www.bilibili.com/video/<BVID>" -o "raw/song_NN.%(ext)s"
# 重复 7 次（s4 注意 vfill crop 参数）

# 3. vfill 到竖屏（默认 736:920:592:0；s4 用 736:780:592:0 去更深的底部歌词）
for n in 01 02 03 05 06 07; do
  bash ../../tools/video/vfill.sh raw/song_${n}.mp4 clips/vert_${n}.mp4 "736:920:592:0"
done
bash ../../tools/video/vfill.sh raw/song_04.mp4 clips/vert_04.mp4 "736:780:592:0"

# 4. TTS（女声 zf_xiaoyi）— 拷 scripts/narration.txt 到 build/，跑：
cp ../../production/zhang-shaohan-7albums/scripts/narration.txt build/
cp ../../production/zhang-shaohan-7albums/scripts/narrate_segments.py build/
cp ../../production/zhang-shaohan-7albums/scripts/build.py build/
../../tools/tts/venv/bin/python build/narrate_segments.py

# 5. 构建（master.wav + hf/index.html + hf/clips_seg/）
../../tools/tts/venv/bin/python build/build.py

# 6. 提取 cover 拼贴脸 thumbnail（7 张）— picks 见下方
declare -a PICKS=("01:6" "02:12" "03:18" "04:27" "05:6" "06:18" "07:15")
for entry in "${PICKS[@]}"; do
  n="${entry%%:*}"; t="${entry##*:}"
  ffmpeg -y -v error -i "raw/song_${n}.mp4" -ss "$t" -frames:v 1 \
    -vf "crop=720:760:600:60,scale=300:316,setsar=1" \
    "hf/cover_assets/face_${n}.jpg"
done

# 7. 渲染 + mux
cd hf
npx hyperframes lint           # 0 error 期望
npx hyperframes render --output renders/full_raw.mp4 --sdr
cd ..
cp ../../production/zhang-shaohan-7albums/scripts/finalize.sh build/
bash build/finalize.sh         # mux + silencedetect + volumedetect
```

## 关键决策摘录

- **画幅**：1080×1920 30fps（短视频主流）
- **配音音色**：女声 `zf_xiaoyi`（brief 强制；CONVENTIONS 默认男声 `zm_yunxi` 被本期覆盖）
- **素材源**：6/7 用 B站 1080P 修复版（YouTube 福茂唱片官频上传仅 480p），#07《是我》用 YouTube 本人官频原生 1920×1080
- **烧死歌词**：6/7 首 MV master 自带底部歌词条，统一 bottom-160 crop；#04《寻宝》歌词位置更高（y≈820+），单独用 bottom-300 crop
- **音频**：每段 `loudnorm I=-14`，旁白段音乐床 BED_GAIN=0.28（约 -12dB），副歌全量；s6/s7 因暗调安静曲补 +3.5dB；后期 mux master.wav 覆盖（HF 渲染会压平动态）
- **首屏封面**：title + sub + 7 张 face thumb 拼贴（4+3 布局），无 fade-in；列表在 intro 旁白起时（t=2.7s）动画淡入
- **章节卡**：与 footage 同时入场（不再先卡片后画面），低透明度，文字格式「歌名（大）/ 专辑名·年份 / 描述」，全片无《》符号
- **结尾**：简化为单题 + CTA，删去歌单列表（开头已渲染）
- **过场**：cover→s1 cross-fade（cover data-duration 延伸进 s1 起始 0.6s，与 s1 fade-in 重叠）；song→song 用 1.0s footage fade-out + fade-in
- **总时长**：299.7s = 4:59.7（target 4:30-5:30 内）

## QA 结果（v7 最终）

- 画面：抽帧 16 个时间点 + contact sheet（见各 `qa/v6/` `qa/v7/` 目录验收）。无文字重叠、无烧死歌词残留、无水印 / 路径 / 项目内部词泄漏
- `silencedetect=n=-35dB:d=1.5`：✅ 无 >1.5s 整片静音（章节交界已做 ramp-in/out 衔接）
- `volumedetect`：mean = -16.0 dB，max = 0.0 dB（alimiter 内）；副歌段彼此差异 8 dB（CONVENTIONS 目标 <1.5 dB，留为后续 v8 优化点）
- 首屏可截屏作封面：✅ t=0 已包含完整 cover layout（无 fade-in 元素）

## 未解决的小遗憾（不影响发布）

- #03 cover 缩略图：cap 占比偏大，face 露出有限（《潘朵拉》MV 该时段风格本身如此）
- #04 cover 缩略图：Angela 在画面右侧、左侧有灯具背景（可改 ffmpeg crop 重抽）
- 副歌段响度跨歌 ~8 dB 差异：单首内 ducking 准确，跨歌响度归一化未做（CONVENTIONS 推荐 <1.5 dB），下版加 ReplayGain 风格的二次 loudnorm 可解
- 整体画面偏紫调（vfill 默认 brightness=-0.32 用于压住模糊背景）：MV 源色温本身偏暖，建议下版改为 brightness=-0.18

## 引用

- 项目 brief（用户原版）：`sandbox/zhang_shaohan_7albums_video_agent_prompt.md`（已并入仓库，sandbox 已清理）
- 规范：`CONVENTIONS.md` § 「自媒体视频」 / 「长篇叙事盘点」 / 「HyperFrames render 默认参数」
- 工具：`tools/video/README.md` / `tools/tts/README.md`
