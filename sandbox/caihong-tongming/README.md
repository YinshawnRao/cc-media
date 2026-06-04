# caihong-tongming — 华语同名歌曲盘点《彩虹》

竖屏 1080×1920 音乐盘点，叙事序 1→5，成片 ~4:57。5 首同名《彩虹》气质各异：热血 / 失恋(双版本) / 陪伴 / 青春 / 雨季。

## 成片
`renders/caihong-tongming.mp4`（HF 渲染 + 预混 master.wav 后期 mux 而成）

## 结构
封面(设计款·彩虹渐变字+黑胶+歌词纸，不泄漏歌单) → 蒙太奇钩子(CSS 光带/雨/碎词，不泄漏歌单) →
Part1 动力火车(热血) → Part2 梁静茹/五月天(同曲双版本，冷蓝→暖光转场卡) → Part3 张惠妹(陪伴) →
Part4 羽泉·2001春晚(千禧青春) → Part5 周杰伦(雨季) → 回放6闪 + 揭晓歌单 + 评论引导。

## 选源（全部 YouTube 官方频道 MV，详见 design.md / 记忆 caihong-tongming-sourcing）
动力火车 fYrBo8XEssE(480p) · 梁静茹 HnnXkxlyuM8(1080p) · 五月天 7WQFI_wiEIk(1080p) ·
张惠妹 OvlWgjiQYpo(1080p) · 羽泉 LCvHysJGDSw(2001春晚) · 周杰伦 WxZvXPTBC0A(480p)
> 千禧台版 MV 普遍带烧死歌词(约 80% 高度) → vfill 全宽 letterbox + crop 掉烧词带。

## 复现
```bash
# 1. 配音（默认男声 zm_yunxi）
tools/tts/venv/bin/python build/narrate_segments.py        # -> audio/*.wav + narration.json
# 2. 素材已在 downloads/（yt-dlp 切片）；竖屏化见各 vert_*.mp4 的 crop（README/记忆）
#    bash tools/video/vfill.sh downloads/<x>.mkv clips/vert_<x>.mp4 <W:H:0:0>
# 3. 构建音轨 master.wav + index.html + clips_seg/
python3 build/build.py
# 4. 渲染（必加 --sdr，本机 GPU 截帧偶发崩 → -w1 + 重试）
cd hf && npx hyperframes@0.6.47 lint && npx hyperframes@0.6.47 render -o renders/full_raw.mp4 --sdr -w 1
# 5. mux 预混音轨（HF 会压平动态，必须后期覆盖）
ffmpeg -i hf/renders/full_raw.mp4 -i hf/master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/caihong-tongming.mp4
```

## QA（成片已通过）
无 >1s 整片静音；6 段副歌响度 -13.9~-16.2dB(≈-15dB 一致)，旁白段明显更低(ducking)；
抽帧确认各段对应素材、无烧词/水印/网址/路径/meta 文案；封面首帧可作缩略图。
