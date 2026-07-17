# cc-media

`cc-media` 是一个本地短视频生产流水线仓库，用来把长视频、音乐现场、访谈、盘点素材加工成可发布的自媒体短视频。它的核心价值不是保存下载下来的大体积素材，而是沉淀一套可复现的制作方法：素材来源、时间点、脚本、合成工程、旁白、QA 证据和项目规范。

项目仍处在探索阶段。已经验证过的通用做法会沉淀到 [CONVENTIONS.md](CONVENTIONS.md)，具体视频任务先在 `sandbox/` 试错，确认可交付后再整理到 `production/`。

## 项目本质

这不是一个视频素材仓库，也不是单纯的 HyperFrames 示例项目。它是一个面向短视频成片的工作台：

1. 从 YouTube 和 B站并行查找素材源。
2. 用 `yt-dlp` 和 FFmpeg 下载、裁剪、转码实际视频片段。
3. 用本地中文 TTS 生成旁白。
4. 用 HyperFrames 生成标题、字幕、倒计时、转场、包装层和竖屏构图。
5. 用预混音频 `master.wav` 做后期 mux，避免浏览器渲染压平音频动态。
6. 用抽帧、音量检测、静音检测和项目专用检查脚本做 QA。

最终仓库应该能回答三个问题：

- 这个视频用了哪些来源，为什么选这些来源？
- 如果重新构建，脚本、时间码和工程文件是否足够复现？
- 成片是否通过了画面、声音、水印、路径泄漏等基本质量检查？

## 核心原则

- **双平台查源**：除非 brief 明确排除某个平台，每条素材都要同时查 YouTube 和 B站，再按清晰度、画面干净度、立体声、现场质量和版本匹配度选源。
- **源码进仓库，素材留本地**：提交脚本、清单、配置、设计稿、时间码和 QA 记录，不提交下载视频、渲染结果、缓存、cookie 和大体积中间产物。
- **可复现优先**：`production/<项目名>/` 里保留能重建成片的输入，而不是只放一个最终 MP4。
- **QA 靠工具**：不能只凭肉眼印象或听感下结论。渲染后要用 FFmpeg 检查音量/静音，用抽帧或 contact sheet 检查画面。
- **成片不泄漏制作痕迹**：不得出现平台水印、网址、提示词、文件路径、调试文本或无关字幕。
- **本地测试优先**：当前默认只做本地测试和研究。若要公开发布，需要单独评估 YouTube 与 B站素材授权和平台条款。

## 目录结构

```text
.
├── CONVENTIONS.md          # 全局规范，已验证做法的唯一沉淀入口
├── AGENTS.md               # Codex/自动化代理工作说明
├── CLAUDE.md               # Claude/自动化代理工作说明
├── tools/
│   ├── video/              # 视频任务 runbook 和复用脚本
│   └── tts/                # 本地中文旁白工具，基于 Kokoro + misaki[zh]
├── sandbox/                # 实验区，可丢弃，不承诺长期保留
└── production/             # 正式项目区，保留可复现输入和工程文件
```

`tools/video/README.md` 是从 brief 到成片的具体执行手册。接到新视频任务时，先读 `CONVENTIONS.md` 和 `tools/video/README.md`，再开工。

## 什么应该提交

适合进入 git 的内容：

- `README.md`、`CONVENTIONS.md`、`AGENTS.md`、`CLAUDE.md` 等项目说明。
- `SOURCES.md`、`design.md`、`index.html`、`meta.json`、旁白文本、时间码、构建脚本。
- 轻量 QA 证据，例如 `ffprobe`、`volumedetect`、`silencedetect`、抽帧索引、项目分析 JSON/TXT。
- `tools/` 下可复用脚本和说明。
- `production/<项目名>/` 下的可复现工程文件。

不适合进入 git 的内容：

- 下载原片、切片、转码中间文件、最终 MP4、WAV/MP3、大图、缓存帧。
- `node_modules/`、Python venv、`__pycache__/`、`.hf-local/`、HyperFrames 本地缓存。
- 任何 cookie、登录态、token、`.env` 和私密配置。
- `sandbox/` 下的一次性下载产物和临时渲染结果。

根目录 `.gitignore` 会尽量把这些大文件和敏感文件挡在外面。提交前仍然要用 `git status --short` 和 `git diff --stat` 检查 staged 内容。

## 依赖

本地需要：

- Node.js >= 22，用于 HyperFrames。
- FFmpeg，用于裁剪、转码、合成和 QA。
- `yt-dlp`，用于 YouTube / B站素材下载。
- Python 3，用于 `tools/video/` 辅助脚本和 `tools/tts/` 本地中文 TTS。

常用安装方式：

```bash
brew install ffmpeg yt-dlp
```

HyperFrames 通常通过 `npx hyperframes ...` 使用。中文旁白不要使用 `npx hyperframes tts`，因为它不适合中文；统一使用 `tools/tts/narrate.py`。

## 新视频任务流程

1. 阅读 `CONVENTIONS.md` 和 `tools/video/README.md`。
2. 按 brief 创建 `sandbox/<slug>/`，所有试错先放这里。
3. 确认 cookie 只在仓库根目录。优先使用 `all_cookies.txt`；旧脚本可能读取 `www.youtube.com_cookies.txt` 或 `www.bilibili.com_cookies.txt`。这些文件都不应提交。
4. YouTube 和 B站都查源，把候选、取舍理由、URL 和时间码写进 `SOURCES.md`。
5. 用 `yt-dlp` / FFmpeg 获取素材，用 `tools/video/` 脚本做竖屏填充、旁白分段、倒计时或 showcase 对齐。
6. 用 HyperFrames 生成包装层，渲染画面。
7. 用预混 `master.wav` 后期 mux 到最终视频。
8. 运行音频和画面 QA，记录结果。
9. 若项目要长期保留，再把可复现输入整理到 `production/<项目名>/`。

## 重要工具入口

- `tools/video/vfill.sh`：横屏素材转竖屏画布。
- `tools/video/countdown_build.py`：倒计时类视频的音轨和工程生成模板。
- `tools/video/narrate_segments.py`：按分段生成旁白。
- `tools/video/vocal_segments.py`：Whisper 词时间戳 + 声学 + stereo 的多证据主唱候选检测；旧能量法只作候选。
- `tools/video/showcase_align.py`：阻断式检查主唱入点和完整乐句出点；REVIEW 需逐曲留证，硬边界 FAIL 不可跳过。
- `tools/video/check_yt_cookie.py`：检查 YouTube cookie 登录态。
- `tools/video/bili_search.py`、`tools/video/bili_dl.py`：B站搜索和下载辅助。
- `tools/tts/narrate.py`：本地中文旁白生成。

更多细节以 `CONVENTIONS.md` 和 `tools/video/README.md` 为准。
