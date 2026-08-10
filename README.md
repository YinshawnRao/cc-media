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
6. 用配音、项目结构、终片三道门禁，再结合抽帧、音量/静音分析与人工眼耳复核做 QA。

最终仓库应该能回答三个问题：

- 这个视频用了哪些来源，为什么选这些来源？
- 如果重新构建，脚本、时间码和工程文件是否足够复现？
- 成片是否通过了画面、声音、水印、路径泄漏等基本质量检查？

## 核心原则

- **双平台查源**：除非 brief 明确排除某个平台，每条素材都要同时查 YouTube 和 B站；先比较版本身份和官方属性，再在同一来源层级内比较画面干净度、立体声和清晰度。
- **版本正确、官方优先**：先确认目标歌手/翻唱版本，再优先可用官方 MV；官方 MV 画质稍差也不因此换成第三方高清修复或二剪。确需换源时在 `SOURCES.md` 留证。
- **TOP 倒数揭晓**：凡 TOP / 排名 / 榜单都按 N→1 播放；封面和 intro 不提前列完整歌单、排序或第一名，每一名到对应转场才揭晓。
- **结构完整、质量优先**：一般视频保留开头、歌曲转场和结尾配音；完全自由探索类才可例外。默认不设总时长上限，不为变短牺牲完整乐句或观赏体验。
- **配音默认稳定**：新盘点默认 `CV002「治愈少女」`。未指定、未知、模糊或冲突选择均回退 CV002；Qwen 缺模型或母带时硬失败，不静默换 Kokoro。外文只做窄范围 ASCII token 发音处理，纯中文文本、标点、seed、请求结构和既有缓存 fingerprint 保持不变。
- **封面排版也是 QA**：标题按语义自然换行，歌手名与同层级主要文字同字号或更大；首帧同时检查排版美感、安全区、主体避让和平台裁剪。
- **源码进仓库，素材留本地**：提交脚本、清单、配置、设计稿、时间码和 QA 记录，不提交下载视频、渲染结果、缓存、cookie 和大体积中间产物。
- **可复现优先**：`production/<项目名>/` 里保留能重建成片的输入，而不是只放一个最终 MP4。
- **QA = 机械门禁 + 人工复核**：不能只凭印象下结论，也不能把机械 PASS 当成工具已经理解画面或听感。渲染后要检查当前终片的音量/静音、抽帧、旁白语义、排版、水印和发布裁剪。
- **成片不泄漏制作痕迹**：不得出现平台水印、网址、提示词、文件路径、调试文本或无关字幕。
- **本地测试优先**：当前默认只做本地测试和研究。若要公开发布，需要单独评估 YouTube 与 B站素材授权和平台条款。

## 目录结构

```text
.
├── CONVENTIONS.md          # 全局规范，已验证做法的唯一沉淀入口
├── AGENTS.md               # Codex/自动化代理工作说明
├── CLAUDE.md               # Claude 薄入口；业务规则仍以 AGENTS.md 为准
├── tools/
│   ├── video/              # 视频任务 runbook 和复用脚本
│   └── tts/                # 编号化本地中文配音库；默认 CV002 治愈少女
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

- 下载原片、切片、转码中间文件、最终 MP4、普通 WAV/MP3、大图、缓存帧。唯一音频例外是 `tools/tts/voices/` 内编号角色的精选参考母带与试听样例。
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

新项目固定使用 `hyperframes@0.6.69`，例如 `npx --yes hyperframes@0.6.69 lint`；已有项目遵循自身 `package.json` 的精确 pin。禁止裸 `npx hyperframes` 和 `hyperframes@latest`。新项目字体默认使用项目内合法授权的 WOFF2；系统 `local()` 只用于明确锁定本机/OS、且不要求跨机复现的历史或本机专用工程，任何项目都不得依赖 Google Fonts 等渲染时网络请求。中文旁白统一使用 `tools/tts/narrate.py`，不要使用 HyperFrames 内置 TTS。

## 新视频任务流程

1. 阅读 `AGENTS.md`、`CONVENTIONS.md` 和 `tools/video/README.md`。
2. 按 brief 创建 `sandbox/<slug>/`，只放该期素材、渲染和可丢弃试验；跨项目研究与复用代码归 `tools/<domain>/research/` 或相应工具目录。
3. 运行 `python3 tools/tts/doctor.py`；首次初始化或模型/runtime 变化后运行一次 `--full-model-hash`。
4. 把原始任务提示词交给 `tools/tts/resolve_voice.py`，保存项目级 `voice-selection.json`。新盘点默认 `CV002「治愈少女」`；未知、模糊或冲突指定也回退 CV002。
5. Cookie 原始全量导出只允许临时放仓库外并设为 `0600`；用 `tools/video/filter_cookie_jar.py` 过滤 YouTube / Google / B站域并原子写入根目录 `all_cookies.txt`。旧 `www.*_cookies.txt` 仅作脚本回退，任何 Cookie 文件都不得提交或复制进 `sandbox/`。
6. YouTube 和 B站都查源，先确认歌手/表演版本，再优先官方 MV；把候选、取舍理由、URL 和时间码写进 `SOURCES.md`。
7. 用中央 TTS 入口生成旁白，运行 `python3 tools/tts/verify_voice_usage.py --selection sandbox/<slug>/voice-selection.json --project-root sandbox/<slug>`，必须得到 `VOICE GATE: PASS`。
8. 填写 `project-manifest.json`，正式 build 前运行 `python3 tools/video/verify_project.py --project sandbox/<slug>`，必须得到 `PROJECT CONTRACT: PASS`。
9. 用固定的 `hyperframes@0.6.69` 生成包装层并以 `--sdr` 渲染；历史项目使用自身 pin。
10. 用预混 `master.wav` 后期 mux 到最终视频。
11. 填写终片 QA manifest，运行 `python3 tools/video/verify_final_video.py --project sandbox/<slug> --manifest qa/final-video-qa.json`；只有 `FINAL VIDEO QA: PASS` 才算机械验收完成，之后仍要完成人工画面和听感复核。
12. 若项目要长期保留，再把可复现输入整理到 `production/<项目名>/`。

## 重要工具入口

- `tools/video/vfill.sh`：横屏素材转竖屏画布。
- `tools/video/countdown_build.py`：倒计时类视频的音轨和工程生成模板。
- `tools/video/narrate_segments.py`：按分段生成旁白。
- `tools/video/vocal_segments.py`：Whisper 词时间戳 + 声学 + stereo 的多证据主唱候选检测；旧能量法只作候选。
- `tools/video/showcase_align.py`：阻断式检查主唱入点和完整乐句出点；REVIEW 需逐曲留证，硬边界 FAIL 不可跳过。
- `tools/video/filter_cookie_jar.py`：把仓库外原始导出过滤为根目录目标域 Cookie jar，原子写入且固定 `0600`。
- `tools/video/check_yt_cookie.py`：静态检查 YouTube Cookie 字段、文件内 expiry、目标域 allowlist 与权限；不能证明服务端会话仍有效。
- `tools/video/bili_search.py`、`tools/video/bili_dl.py`：B站搜索和下载辅助。
- `tools/video/verify_project.py`：build 前项目结构与来源证据门禁；本地 receipt 只证明声明的 URL 到本地文件派生链一致，不证明上传者或“官方”身份。
- `tools/video/verify_final_video.py`：标准 HyperFrames post-mux 项目的终片机械门禁；AI 音色 MV 走 durable builder 的独立检查。
- `tools/tts/doctor.py`：默认 CV002、固定模型/runtime 与参考母带自检。
- `tools/tts/resolve_voice.py`：从原始任务提示词确定一次项目级配音；默认及兜底均为 CV002。
- `tools/tts/narrate.py`：统一中文旁白入口，读取 `voice-selection.json`，Qwen 缺失时硬失败而非换声。
- `tools/tts/verify_voice_usage.py`：项目配音 sidecar、模型声明与当前 WAV 一致性门禁；本地 receipt 不等于音色来源或抗篡改证明。
- `tools/tts/voices/listen.html`：CV001–CV008 编号声音、参考母带和实际样音。

更多细节以 `CONVENTIONS.md` 和 `tools/video/README.md` 为准。
