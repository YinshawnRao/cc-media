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
6. 用配音、项目结构、发布文案、本地机械终片四道门禁，再结合抽帧、音量/静音分析做默认 QA；只有明确要求发布级交付时才把真人眼耳复核升级为硬门禁。

最终仓库应该能回答三个问题：

- 这个视频用了哪些来源，为什么选这些来源？
- 如果重新构建，脚本、时间码和工程文件是否足够复现？
- 成片是否通过了画面、声音、水印、路径泄漏等基本质量检查？

## 核心原则

- **双平台查源**：除非 brief 明确排除某个平台，每条素材都要同时查 YouTube 和 B站；先比较版本身份和官方属性，再在同一来源层级内比较画面干净度、立体声和清晰度。
- **版本正确、官方优先**：先确认目标歌手/翻唱版本，再优先可用官方 MV；官方 MV 画质稍差也不因此换成第三方高清修复或二剪。确需换源时在 `SOURCES.md` 留证。
- **TOP 倒数揭晓**：凡 TOP / 排名 / 榜单都按 N→1 播放；封面和 intro 不提前列完整歌单、排序或第一名，每一名到对应转场才揭晓。
- **结构完整、质量优先**：一般视频保留开头、歌曲转场和结尾配音；完全自由探索类才可例外。默认不设总时长上限，不为变短牺牲完整乐句或观赏体验。
- **配音项目内稳定**：新盘点若未唯一指定音色，则从 `CV001 / CV002 / CV003 / CV004 / CV005 / CV008` 女声池随机一次，并把结果落盘供整期复用；Qwen 缺模型或母带时只让当前 TTS 步骤硬失败，代理修复固定环境后重跑，不静默换 Kokoro、不重抽声线，也不停止整个 goal。外文只做窄范围 ASCII token 发音处理，纯中文文本、标点、seed、请求结构和既有缓存 fingerprint 保持不变。
- **封面排版也是 QA**：标题按语义自然换行，歌手名与同层级主要文字同字号或更大；首帧同时检查排版美感、安全区、主体避让和平台裁剪。
- **源码进仓库，素材留本地**：提交脚本、清单、配置、设计稿、时间码和 QA 记录，不提交下载视频、渲染结果、缓存、cookie 和大体积中间产物。根 `all_cookies.txt` 是仅用户可手工覆盖的 canonical 输入，代理不得改变其内容、元数据或路径绑定。
- **可复现优先**：`production/<项目名>/` 里保留能重建成片的输入，而不是只放一个最终 MP4。
- **QA 默认先完成本地机械闭环**：不能只凭印象下结论，也不能把机械 PASS 当成工具已经理解画面或听感。渲染后仍要对当前终片做解码、hash、音轨、ASR、音量/静音和抽帧诊断；pending 状态保存在 QA 文件中，不阻断普通 goal，也不作为默认交付话术。只有用户明确要求公开发布、发布验收或可发布交付时，才用 `--require-human-review` 强制绑定当前 final SHA 的真人画面、听感、泄漏与发布安全复核；代理不得伪造人审。
- **Goal 内部失败自动恢复**：内部步骤首次失败只停止当前步骤，不停止整个 goal。执行“**诊断 → 修复 → 重跑**”，从最近失败步骤继续并重跑受影响下游门禁；不得因可自行修复的内部失败暂停、等待用户确认或标记 `blocked`，机械红线不得降级或放松。普通公开下载、备选源、模型可安装、TTS/ASR/sidecar、render/mux、manifest/evidence 以及门禁 FAIL/REVIEW 都应由代理自行换路、修复并复跑。只有用户明确要求小样、缺用户独占的必需输入（如 AI WAV）、穷尽安全替代后仍需新凭据/权限/外部能力、继续必须改变歌单/排名/歌手版本/平台排除/硬时长等核心 brief，或显式发布缺真人终验时才可暂停；真实外部边界首次出现也只请求必需输入/权限，同一阻断连续三次 goal turn 仍存在且无法继续时才可标记 `blocked`。
- **多 Goal 公平并发**：多个 goal（包括视频 goal）必须同时继续，不建立全局锁、队列、semaphore、sleep 轮询或跨 goal 等待。Whisper/Torch/BLAS、重 FFmpeg 与 HyperFrames 统一经 `tools/video/resource_budget.py` 在启动时按活跃重任务数选择 `4 → 3 → 2`：只有一个用 4、第二个新任务用 3、三个及以上的新任务用 2；已运行任务不暂停或动态改速。手动 1–4 覆盖优先，注册表异常直接回退 2。Qwen 先做不 import MLX 的 Metal preflight，避免在受限上下文触发 Python native crash；失败只进入本 goal 的自动修复重跑，不会占着共享锁等待。
- **成片不泄漏制作痕迹**：不得出现平台水印、网址、提示词、文件路径、调试文本或无关字幕。
- **Sandbox 产物目录固定**：新项目的 HyperFrames raw render 和 mux 后最终 MP4 全部放在 `sandbox/<slug>/renders/`，最终交付固定为 `renders/<slug>.mp4`。不得使用 `final/`、`output/`、项目根终片或其他目录。
- **小红书文案随片交付**：与 `renders/` 并列创建 `publishing/`，固定交付 `publishing/xiaohongshu.md`。提供 1–5 个爆款标题候选、默认 3 个且第一条为首选；正文可直接发布，最后一行是 hashtags。全文不得出现任何本期歌曲名称，且必须围绕真实主题、歌手和选题角度，不得泛化或杜撰。
- **Sandbox 成片直接交付**：最终回复同时报告 `renders/<slug>.mp4` 与 `publishing/xiaohongshu.md`、最终 MP4 当前 SHA、VOICE / PROJECT / PUBLISHING / FINAL 四道门禁结果、实际修复和确实影响成片的问题。发布文案是必需内容产物，不属于被禁止的未来发布建议。不得自动附加用途定位、权利或条款免责声明、额外真人复核建议；QA、SOURCES、README、checklist 和 CLI 默认输出也不得生成这类固定收尾。只有用户当期主动询问相应主题时才回答。

## 目录结构

```text
.
├── CONVENTIONS.md          # 全局规范，已验证做法的唯一沉淀入口
├── AGENTS.md               # Codex/自动化代理工作说明
├── CLAUDE.md               # Claude 薄入口；业务规则仍以 AGENTS.md 为准
├── tools/
│   ├── video/              # 视频任务 runbook 和复用脚本
│   └── tts/                # 编号化本地中文配音库；新项目从女声池随机一次
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
2. 按 brief 创建 `sandbox/<slug>/`，其中 raw render 和 mux 后最终 MP4 统一放 `renders/`，发布文案放并列的 `publishing/`；跨项目研究与复用代码归 `tools/<domain>/research/` 或相应工具目录。goal / 视频制作任务默认持续到 `renders/<slug>.mp4`、`publishing/xiaohongshu.md`；标准 manifest 项目还要完成 VOICE / PROJECT / PUBLISHING / 本地机械 FINAL 四道门禁和当期 QA，专用 durable 项目完成自身独立检查，一次完成整片；除非用户明确要求小样或预览，不在开场或首个揭晓段暂停等待确认，也不得因 pending human review 暂停或标记 `blocked`。
3. 运行 `python3 tools/tts/doctor.py`；首次初始化或模型/runtime 变化后运行一次 `--full-model-hash`。
4. 把原始任务提示词交给 `tools/tts/resolve_voice.py`，保存项目级 `voice-selection.json`。唯一精确指定优先；未指定、未知、模糊或冲突时从 `CV001 / CV002 / CV003 / CV004 / CV005 / CV008` 女声池随机一次。若解析结果不是预检声线 CV002，再以 `python3 tools/tts/doctor.py --voice <resolved_id>` 精确检查本期音色；全声音库与 mixed-script 能力只在维护时显式完整审计，不阻塞无关的纯中文任务。
5. 根 `all_cookies.txt` 只由用户手工维护；canonical 不要求不可变锁，代理禁止覆盖由 `AGENTS.md` 与 `CONVENTIONS.md` 的提示词约束。代理禁止对它直接写入，或执行 `chmod`、`touch`、`mv`、`cp` 和过滤替换。所有需要 Cookie 的 yt-dlp 命令走 `python3 tools/video/yt_dlp_readonly.py -- <yt-dlp 参数>`，不得裸传 `--cookies all_cookies.txt`；wrapper 只操作仓库外私有临时副本。用户需要更新时，可自行运行 `python3 tools/video/filter_cookie_jar.py SOURCE --output /absolute/outside/candidate.txt` 生成仓库外 candidate，检查后亲自安装并设为 `0600`。代理和普通 goal 不运行过滤或安装流程；Cookie 不可用时继续公开下载和双平台备选，不因此停止 goal。
6. YouTube 和 B站都查源，先确认歌手/表演版本，再优先官方 MV；把候选、取舍理由、URL 和时间码写进 `SOURCES.md`。
7. 用中央 TTS 入口生成旁白，运行 `python3 tools/tts/verify_voice_usage.py --selection sandbox/<slug>/voice-selection.json --project-root sandbox/<slug>`，必须得到 `VOICE GATE: PASS`。
8. 填写 `project-manifest.json`，正式 build 前运行 `python3 tools/video/verify_project.py --project sandbox/<slug>`，必须得到 `PROJECT CONTRACT: PASS`。
9. 用固定的 `hyperframes@0.6.69` 生成包装层；在项目目录通过 `python3 ../../tools/video/resource_budget.py hyperframes -- npx --yes hyperframes@0.6.69 render --output renders/full.mp4 --sdr` 自适应渲染。历史项目使用自身 pin，但同样通过 wrapper 将 workers 限制在 1–4，不能用 auto。
10. 用预混 `master.wav` 后期 mux 到 `renders/<slug>.mp4`。raw render 与最终 MP4 都不得离开 `renders/`。
11. 基于已经完成的真实视频写 `publishing/xiaohongshu.md`，运行 `python3 tools/video/verify_publishing.py --project sandbox/<slug>`，必须得到 `PUBLISHING COPY: PASS`。这一门禁在 build/post-mux 后、FINAL 前执行，不属于 build 前 `project-manifest.json`。
12. 对有 intro / song / outro / CTA timeline 与完整旁白的**标准结构化盘点/叙事项目**，mux 后运行中央 `tools/video/prepare_final_qa.py --project sandbox/<slug> --final renders/<slug>.mp4 --render renders/full.mp4`，由当前 timeline、authoring manifest、final、render 与 master 生成 `qa/final-video-qa.json`、实时 ASR、抽帧和诊断证据，并在同一进程完成中央机械 FINAL。该命令输出 `FINAL VIDEO QA: PASS` 就算本地机械验收完成；默认不要紧跟 standalone `verify_final_video.py` 重复 ASR/解码，它只保留给显式独立复核或诊断。未请求发布时，需要人判断的语义项只保存在 QA 文件中；默认交付只报告 advisory 数量，不追加后续模式提示。只有用户明确要求发布级终验时，才让真人填写 preparer 生成的当前 SHA 模板，以 `--human-review-input qa/human-review-input.json --require-human-review` 重新 prepare；缺少真人批准会返回 `REVIEW_REQUIRED`，但不得用自动记录冒充真人。`project_kind: free_exploration` 仍按当期 project/final schema 准备 QA，不强套 structured preparer；AI 音色 MV 继续走 durable builder 的独立检查。
13. 若项目要长期保留，再把可复现输入整理到 `production/<项目名>/`。

## 重要工具入口

- `tools/video/vfill.sh`：横屏素材转竖屏画布。
- `tools/video/countdown_build.py`：倒计时类视频的音轨和工程生成模板。
- `tools/video/narrate_segments.py`：按分段生成旁白。
- `tools/video/vocal_segments.py`：Whisper 词时间戳 + 声学 + stereo 的多证据主唱候选检测；旧能量法只作候选。
- `tools/video/showcase_align.py`：阻断式检查主唱入点和完整乐句出点；REVIEW 先按 **multi → 换窗 → 换源** 恢复，穷尽且硬 `FAIL=0` 后本地才可用 `reviewer_kind=agent` 得到仅本地的 `OBSERVED`；`--require-human-review` 只认 `reviewer_kind=human` 的真人 `APPROVED`，硬边界 FAIL 不可跳过。
- `tools/video/yt_dlp_readonly.py`：唯一允许使用 canonical Cookie 的 yt-dlp 入口；在仓库外创建私有临时工作副本，避免 yt-dlp 退出时回写根文件。
- `tools/video/filter_cookie_jar.py`：仅供用户维护时把原始导出过滤成仓库外 candidate；不安装、不覆盖根 `all_cookies.txt`，代理和普通 goal 禁止调用。
- `tools/video/check_yt_cookie.py`：只读检查 YouTube Cookie 字段、文件内 expiry 与权限；canonical 不要求不可变锁。额外域只作不泄露域名的 advisory，不会让有效用户快照 FAIL，也不能证明服务端会话仍有效。
- `tools/video/bili_search.py`、`tools/video/bili_dl.py`：B站搜索和下载辅助。
- `tools/video/verify_project.py`：build 前项目结构与来源证据门禁；本地 receipt 只证明声明的 URL 到本地文件派生链一致，不证明上传者或“官方”身份。
- `tools/video/verify_publishing.py`：具有标准 `project-manifest.json` 的盘点、叙事与自由探索项目，在 build/post-mux 后、FINAL 前使用的小红书发布文案门禁；默认读取固定路径 `publishing/xiaohongshu.md`，检查标题候选、可发布正文、末行 hashtags、歌曲名剧透，以及正文是否命中项目真实歌手或封面主题。AI durable 工程继续走自身独立契约，不得伪造标准 manifest。
- `tools/video/prepare_final_qa.py`：标准结构化盘点/叙事项目的 mux 后中央 QA manifest/evidence 生成器；默认生成带诚实 pending review 的 `qa/final-video-qa.json`，发布模式只合并显式 `--human-review-input`，绝不自动批准。`project_kind: free_exploration` 与 AI 音色 MV 不强套此工具。
- `tools/video/verify_final_video.py`：标准 HyperFrames post-mux 项目的终片机械门禁；AI 音色 MV 走 durable builder 的独立检查。
- `tools/tts/doctor.py`：用 CV002 作为稳定预检声线，检查固定模型/runtime 与参考母带；不决定项目成片声线。
- `tools/tts/resolve_voice.py`：从原始任务提示词确定一次项目级配音；无唯一精确选择时从配置女声池随机一次。
- `tools/tts/narrate.py`：统一中文旁白入口，读取 `voice-selection.json`；Qwen 缺失时当前步骤 fail closed，修复固定环境后自动重跑，不换声、不暂停整个 goal。
- `tools/tts/verify_voice_usage.py`：项目配音 sidecar、模型声明与当前 WAV 一致性门禁；本地 receipt 不等于音色来源或抗篡改证明。
- `tools/tts/voices/listen.html`：CV001–CV008 编号声音、参考母带和实际样音。

更多细节以 `CONVENTIONS.md` 和 `tools/video/README.md` 为准。
