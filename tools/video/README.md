# tools/video — 自媒体视频制作 Runbook（冷启动可执行）

新窗口接到一段视频 brief，按本文件从头跑。配套脚本：
- `vfill.sh` — 片段 → 竖屏 1080×1920（模糊填充 + 裁台标）。
- `narrate_segments.py` — 批量生成各段旁白 wav（改 BLOCKS 文案 + VOICE）。
- `countdown_build.py` — **TOP 盘点模板**（60-90s 倒数揭晓，每段单 footage ~19s）。按 brief 改顶部 `songs` / 时间常量 / 文案，再运行。
- `vocal_segments.py` — 人声段检测（谐波分离 + 频带 RMS）。同一首歌多版本接力类项目（"AI 跨时空同台"）用它定位每个版本的 verse 1 / verse 2 / final chorus 入口时间码。详见 `CONVENTIONS.md "格式之二：AI 跨时空同台"`。**盘点类也要先跑它产出 `probe/vocal_analysis.json`，供下面 `showcase_align` 闸门校验展示段对齐。**
- `showcase_align.py` — **展示段对齐闸门（机械化强制）**。用 `vocal_analysis.json` 校验每首：① 副歌人声在转场旁白收尾时正好进来、贯穿展示段（问题1：旁白别盖副歌）；② 结尾落在句末/器乐 gap、不切半句（问题2：别暴力裁切）。违规 `raise SystemExit`，build 不出 master。`countdown_build.py` 已内置；复用 `full_build.py` 照抄一行 `gate()`。详见 `CONVENTIONS.md「展示段硬规则 (C) → 展示段对齐闸门」`。
- **长篇叙事盘点 / 音乐时间线**（6-8 分钟，5+ 首歌每首 60-90s 含七阶段）：参考 `sandbox/lirh-yangcl-timeline/build/full_build.py`。与 countdown 模板差异：每首独立 audio segment、多 footage 需 ffmpeg 输出端预切到 `clips_seg/`、cover 需真人头像（首选用户提供合照）、字号基线放大、render 必加 `--sdr`。详见 CONVENTIONS「长篇叙事盘点」与「HyperFrames render 默认参数」。

> 配音引擎、音色策略见 `../tts/`；全局规范见仓库根 `CONVENTIONS.md`。

## 0. 启动自检
- 确认在 `cc-media/` 仓库内；读根 `CLAUDE.md` 和 `CONVENTIONS.md`。
- 依赖：`ffmpeg`、`yt-dlp`、`node>=22`、`tools/tts/venv`（缺则按 tts/README 建）。
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
- **竖屏化后立即跑人声段检测**（供第 6 步对齐闸门）：
  `tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json`。

## 5. 旁白
改 `narrate_segments.py` 的 `VOICE` 与 `BLOCKS`（intro/各首/outro），用 `tools/tts/venv/bin/python` 跑，得到各段 wav。

## 6. 音频 + 7. 合成
改 `countdown_build.py` 顶部 `songs`（key/clip/序号/歌名/标签）、各时长常量、`MGAIN`（暗调安静歌补偿），运行：建 master.wav（逐段 床→swell→展示，逐首 `loudnorm=I=-14` 统一响度）+ 生成 `index.html`。
- **展示段时长（硬规则 (B)）**：每首给**一段连续副歌**含前后余量，**不碎镜快闪、不因旁白长就把歌切短**。解说盘点类单首 **≥~25s**（不设上限，以观赏为准）；footage 窗 == 音乐窗（同源同窗）→ 口型同步。clip 切到 `SHOW+余量`，`data-duration=SHOW`。
- **🔒 展示段对齐闸门（硬规则 (C)，build 内置，违规不出 master）**：build 算完时间轴会自动跑 `showcase_align.gate()`，机械校验 ① 副歌人声在旁白收尾时入声并贯穿展示段（问题1）② 结尾落句末/器乐 gap 不切半句（问题2）。**FAIL → 修 `ch_off`/`show`**（拿不准跑 `showcase_align.py plan` 反推），WARN（人声检测不可靠）→ 导 26s mp3 人工耳验，误报才 `SHOWCASE_OVERRIDE=1` 跳过。
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
- **展示段对齐**：`showcase_align.py check --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json` 必须 0 FAIL（副歌入点对齐旁白收尾、结尾不切半句）；WARN 项导 26s mp3 人工耳验。
- **节奏**：开场先配音再进音乐；每段旁白收尾有 0.8–1.2s 消化位，不死静、不硬切。
- 通过后给用户 `<slug>.mp4` 的绝对路径，并说明仍需人工耳/眼定夺的点（高光段是否最佳、源清晰度）。
