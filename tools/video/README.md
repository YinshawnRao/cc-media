# tools/video — 自媒体视频制作 Runbook（冷启动可执行）

新窗口接到一段视频 brief，按本文件从头跑。配套脚本：
- `vfill.sh` — 片段 → 竖屏 1080×1920（模糊填充 + 裁台标）。
- `narrate_segments.py` — 批量生成各段旁白 wav（改 BLOCKS 文案 + VOICE）。
- `countdown_build.py` — **TOP 盘点模板**。解说盘点默认从每首 25s 起步，并用 `SHOWS` 逐曲落到完整乐句；固定时长不是硬切上限。
- `vocal_segments.py` — **多证据主唱候选检测**。旧 HPSS + 频带能量只保留为候选；默认再用本机 Whisper small 的有效歌词密度/word timestamps、字幕幻觉过滤和 stereo mid/side 区分“中心主唱”与“观众/合唱/宽混音待复核”。输出兼容旧 `vocal_segments`，并新增 `lead_segments`、`safe_cut_intervals`、`segment_scores`、`evidence_level`。**盘点类和多版本接力都必须先产出 `probe/vocal_analysis.json`。**
- `showcase_align.py` — **展示段对齐闸门（机械化强制）**。校验：① 主唱身份证据与副歌入点；② 展示覆盖；③ 结尾不落在 word/唱声中；④ 候选出点后 3s 内若有下一咬字就继续向后吞完整句。状态为 `OK / APPROVED / REVIEW / FAIL / MISS`；只有 `OK/APPROVED` 可继续 build。旧能量结果、观众/合唱风险和缺模型都变成阻断式 `REVIEW`，不再假绿。
- **长篇叙事盘点 / 音乐时间线**（6-8 分钟，5+ 首歌每首 60-90s 含七阶段）：参考 `sandbox/lirh-yangcl-timeline/build/full_build.py`。与 countdown 模板差异：每首独立 audio segment、多 footage 需 ffmpeg 输出端预切到 `clips_seg/`、cover 需真人头像（首选用户提供合照）、字号基线放大、render 必加 `--sdr`。详见 CONVENTIONS「长篇叙事盘点」与「HyperFrames render 默认参数」。

> 配音引擎、音色策略见 `../tts/`；全局规范见仓库根 `CONVENTIONS.md`。

## 0. 启动自检
- 确认在 `cc-media/` 仓库内；读根 `CLAUDE.md` 和 `CONVENTIONS.md`。
- 依赖：`ffmpeg`、`yt-dlp`、`node>=22`、`tools/tts/venv`（缺则按 tts/README 建）。多证据检测还要求该 venv 内已有 `openai-whisper`，且 `~/.cache/whisper/small.pt` 已显式预取；正常 build **不会自动联网下载模型**。
- Cookie 文件唯一来源：仓库根目录 `www.youtube.com_cookies.txt` / `www.bilibili.com_cookies.txt`（Netscape 格式，含 HttpOnly 认证 cookie）。不要在 `sandbox/` 下复制第二份；失效会报 "Sign in to confirm you're not a bot"，让用户重新导出并覆盖根目录文件。
- 所有产物写 `sandbox/<项目slug>/`（可丢弃）；正式留存才进 `production/`。

## 1. 解析 brief
提取：标题、画幅（默认竖屏 1080×1920）、每首 歌手/歌名/URL或搜索倾向/切点、旁白（逐字稿就照念，要点就扩写，节奏需要可适当精简）、配音音色（默认男声 `zm_yunxi`，女声 `zf_xiaoyi` 仅在要求时）、揭晓顺序（难度排名→倒数 N→1；主题/代表作盘点→按脚本叙事序，**不硬套倒序**）。

## 2. 样片先行（首个新风格时）
先做 **开场钩子 + 第1首** 一条样片，渲染给用户审风格/节奏/配音，确认后再批量。重复同风格的 brief 可跳过直接全片。

## 3. 素材（yt-dlp）
- **顺序执行**，不并行。先 `--skip-download --print` 验证 cookie + 可用性 + 时长 + 清晰度。
- 切片：`--download-sections "*HH:MM:SS-HH:MM:SS"`，`-f "bv*[height<=1080]+ba/b"`（**不要强制 avc**，否则老 MV 只给 480p；HD 才拿得到真 1080p）。
- **每段抽帧自检**（`ffmpeg -ss N -i raw -frames:v 1 f.png` 后用 Read 看）：确认是真动态 MV 画面、记下水印/烧死字幕/画幅，据此定 `vfill.sh` 的 crop。老歌多为标清 4:3、带水印，属源限制。

## 4. 竖屏化（⚠️ 硬规则见 CONVENTIONS「展示段硬规则 (A)」）
`bash tools/video/vfill.sh <raw> clips/vert_<song>.mp4 <crop>`。
- **默认 letterbox 保原比例、不放大画面**：crop 传**全宽横带**（`源宽 : 裁掉烧词后的高 : 0 : Y`），全宽呈现、上下模糊填充。**双人/合唱/多人/宽机位一律 letterbox**，否则主体被裁半。
- **只有单主体全程居中**才可传窄竖条做"裁切放大贴宽"。拿不准就 letterbox。
- 抽帧确认：人物完整不被裁、无烧词/水印残留。
- **竖屏化后立即跑多证据主唱检测**（供第 6 步对齐闸门）：
  `tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json --mode multi --language zh`。
  - `--mode multi` 缺模型即退出；不得在正式 build 静默退回旧能量法。
  - 日/英歌曲按实际语言改 `--language`，不确定可省略让 Whisper 自动识别。
  - Live / 演唱会 / 观众明显的素材必须加 `--source-kind live`；在 crowd/choir 事件模型尚未接入前，即使识别出完整歌词也只会 REVIEW，不会把观众合唱自动当目标主唱。
  - `classification=no_lexical_singing_detected` 表示器乐/观众窗没有有效歌词证据；`singing_or_group_review` 表示可能是观众、合唱、对唱或宽混音，必须人工复核。

## 5. 旁白
改 `narrate_segments.py` 的 `VOICE` 与 `BLOCKS`（intro/各首/outro），用 `tools/tts/venv/bin/python` 跑，得到各段 wav。

## 6. 音频 + 7. 合成
改 `countdown_build.py` 顶部 `songs`（key/clip/序号/歌名/标签）、各时长常量、`MGAIN`（暗调安静歌补偿），运行：建 master.wav（逐段 床→swell→展示，逐首 `loudnorm=I=-14` 统一响度）+ 生成 `index.html`。
- **展示段时长（硬规则 (B)）**：每首给**一段连续副歌**含前后余量，**不碎镜快闪、不因旁白长就把歌切短**。解说盘点类单首 **≥~25s**（不设上限，以观赏为准）；footage 窗 == 音乐窗（同源同窗）→ 口型同步。clip 切到 `SHOW+余量`，`data-duration=SHOW`。
- **🔒 展示段对齐闸门（硬规则 (C)，build 内置，违规不出 master）**：build 算完时间轴会自动跑 `showcase_align.gate()`。`FAIL` 必须修 `ch_off/show`，不能批准跳过；`REVIEW` 必须重跑多证据分析，或逐曲试听后留下绑定 clip、分析摘要和三个时间码的批准记录。全局 `SHOWCASE_OVERRIDE` 已废弃。
  ```bash
  # 只向后找完整乐句出点；推荐值还会再走同一 verify 自检
  tools/tts/venv/bin/python tools/video/showcase_align.py plan \
    --vocals probe/vocal_analysis.json --clip vert_p4_wait --voice-dur 14 --near 105

  # 生成全部 pending 的逐曲批准骨架；人工填 reason/evidence 并改 approved
  tools/tts/venv/bin/python tools/video/showcase_align.py approval-template \
    --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json
  ```
- **🔒 盘点类封面（默认）**：用**第一首出场歌**（倒数盘点=最先揭晓的最后一名，如 #5）的**动态画面**做封面底，并让 intro footage 与该首 footage 取**同一条素材的连续窗**（帧首尾相接）→ 封面切第一首**画面不剪、丝滑**（只标题淡出+歌名卡淡入）。删静态 `cover_hero.png` 图层。详见 `CONVENTIONS.md「首屏封面 → 盘点类封面=第一首出场歌动态画面」`。
- `npx hyperframes lint` 必须 **0 error**（媒体元素要有 id；相邻 footage 用交替轨道 0/6；同轨不可贴边）。

## 8. 渲染 + MUX（关键）
```bash
npx hyperframes render --output renders/full.mp4 --sdr   # ← --sdr 必加
# HyperFrames 会对音频做响度归一化、压平动态 → 必须用预混 master 覆盖音轨：
ffmpeg -i renders/full.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/<slug>.mp4
```
成片以 mux 后的 `<slug>.mp4` 为准。

> **`--sdr` 必加原因**：HF 会从任意源 auto-detect HDR。Bili 杜比视界流（如 LIKE A STAR 巡演）会触发整片输出升级为 HLG 10-bit H.265，短视频平台不收。强制 SDR H.264。

## 9. QA（我看不到画面、听不到声音，必须用工具验证）
- **画面**：抽多帧拼 contact sheet，用 Read 逐帧看——各段对应素材、标签/标题清晰、**画面里无水印/网址/提示词/路径/项目内部词**。
- **音频**：`silencedetect=n=-35dB:d=1` 无 >1s 整片静音；`volumedetect` 抽测各首副歌均值趋于一致（~-15dB），旁白段音乐明显低于展示段。
- **展示段对齐**：`showcase_align.py check --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json` 必须 `FAIL=0 REVIEW=0 MISS=0`；同目录 `showcase_approvals.json` 会自动读取，但批准只允许解决 REVIEW，不能覆盖硬边界 FAIL。
- **节奏**：开场先配音再进音乐；每段旁白收尾有 0.8–1.2s 消化位，不死静、不硬切。
- 通过后给用户 `<slug>.mp4` 的绝对路径，并说明仍需人工耳/眼定夺的点（高光段是否最佳、源清晰度）。

## 人声检测回归

```bash
# 快速 schema/边界/批准门禁（媒体缺失也可跑）
tools/tts/venv/bin/python -m unittest discover -s tools/video/tests -p 'test_*.py' -v

# 使用本机 sandbox 历史音频，完整原音频分析；需显式 opt-in
CC_MEDIA_AUDIO_REGRESSION=1 tools/tts/venv/bin/python -m unittest \
  tools.video.tests.test_real_audio_regression.RealAudioRegressionTests -v
```

首轮依赖仅增加已写入 `tools/tts/README.md` 重建命令的 `librosa==0.11.0`、`openai-whisper==20250625` 与显式缓存的 small 模型；不引入 Demucs/PANNs。后续若仍有无语义吟唱/超宽现场混音难例，再在独立 `tools/audio-analysis/venv` 引入 Demucs（只分离展示候选窗）和 PANNs crowd/choir 事件分数；不要把这两套老依赖装进 `tools/tts/venv`，模型缺失也不得按 0 分处理。
