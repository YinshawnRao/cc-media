# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project intent

Build a pipeline that turns long-form online videos into self-media ("自媒体") short-form content:

1. **Source** — download/clip segments from **YouTube 和 B站（哔哩哔哩）** 作为并行素材源，用 `yt-dlp`。
2. **Compose** — build the published video (titles, captions, overlays, transitions, intros/outros) with **HyperFrames**, which renders plain HTML/CSS/JS to MP4.

> **素材源硬约束（优先级高于单期任务 brief）**：每条素材**两边都要找**（YouTube + B站）。先锁定正确歌手/表演版本，再优先可用官方 MV；官方 MV 画质稍差也不因此降级。只有官方 MV 不存在或结构性不可用时才比较 Live / 综艺 / 二次来源，并在同一来源层级内按画面干净度、立体声和清晰度选择。除非 brief 显式排除某平台，否则**不允许只搜单边**。具体执行细则见 `CONVENTIONS.md` "素材源平台" 章节。

The repository is in an **exploration phase**. When scaffolding, follow `CONVENTIONS.md` (the single source of reusable standards) so future work stays consistent. The directory is not yet a git repo; run `git init` before the first commit.

## Layout

- `sandbox/` — 测试/实验区，内容视为可丢弃。所有试错先在这里跑。
- `production/<项目名>/` — 正式成片，每个项目一个子目录，保留可复现输入。
- `tools/` — 跨项目复用工具。`tools/tts/` = 编号化本地中文配音库（Qwen3-TTS 角色声音 + Kokoro legacy）。
- `CONVENTIONS.md` — 全局规范，验证可行的做法沉淀到这里。

## 视频任务启动协议

接到任何视频制作 brief（如"做一个音乐盘点/主题视频…"），动手前先：
1. 读 `CONVENTIONS.md`（全局规范 + brief 格式 + QA 方法论）和 `tools/video/README.md`（从 brief 到成片的 Runbook）。
2. **新启动的盘点视频先解析一次配音**：把用户原始任务提示词交给 `tools/tts/resolve_voice.py`，将结果保存为项目级 `voice-selection.json`。唯一精确匹配的编号/名称/注册别名优先；未指定、无法匹配、描述模糊或同时命中多个声音，一律回退 `CV002「治愈少女」`。
3. 复用脚本在 `tools/`（配音 `tools/tts/`、竖屏 `tools/video/vfill.sh`、音轨+合成模板 `tools/video/countdown_build.py`）——不要重造。新项目旁白必须把同一个 `voice-selection.json` 传给中央入口 `tools/tts/narrate.py`；不得直接 `KPipeline(...)`、不得在项目里硬编码 `VOICE`。
4. 涉及联网下载（yt-dlp）统一读取仓库根目录 `all_cookies.txt`；用 `tools/video/filter_cookie_jar.py` 从仓库外、权限 `0600` 的原始导出中过滤 YouTube / Google / B站域并原子写入。旧 `www.*_cookies.txt` 仅作脚本回退。原始全量导出不得进入仓库，Cookie 不得复制到 `sandbox/`；产物写 `sandbox/<slug>/`。
5. **关键铁律**：① 渲染后必须用预混 master.wav **后期 mux**（HyperFrames 会压平音频动态）；② 我看不到画面/听不到声音，**QA 靠抽帧 Read + ffmpeg volumedetect/silencedetect**，不凭感觉下结论；③ 成片里不得出现水印/网址/提示词/路径；④ **禁止自定义旁白字幕**（不要把 TTS 口播再叠成底部字幕条；用户未显式要求就一律不加，详见 `CONVENTIONS.md`「禁止自定义旁白字幕」）。

## 新盘点内容硬约束

- **翻唱版本必须匹配画面版本**：盘点对象若是某位歌手/组合的翻唱，YouTube 与 B站都优先找该翻唱者对应版本的 MV、现场或正式演出视频，不得直接拿原唱歌手画面冒充。只有两边都没有可用对应版本，才可退回原版视频，并在 `SOURCES.md` 记录搜索证据与替代理由。
- **官方 MV 优先于清晰度**：先保证歌手/版本身份正确；同一目标版本只要存在可用官方 MV，就优先选官方 MV，即使分辨率、码率或年代画质稍差。只有官方 MV 确实不存在、无法取得或目标段结构性不可用时，才退到官方 Live / 综艺 / 二次来源，并在 `SOURCES.md` 说明。低清本身不是放弃官方源的理由。
- **TOP 一律倒数揭晓并保留悬念**：凡标题、brief 或结构属于 TOP / 排名 / 榜单，播放顺序必须从最后一名到第一名（N→1）。封面和 intro 可说明主题与 TOP 数量，但不得提前列完整歌单、展示排序或泄露第一名；每一名只在对应歌曲转场时揭晓。非排名主题片不得伪装成 TOP。
- **开头口播禁用“接下来”**：intro 第一段不得出现“接下来”。默认 Qwen 支持多语种，不预先删除非中文；外文歌名/人名先实测发音，只有读得不自然或不可懂时，才改用通行中文译名、音译/谐音或从口播省略（画面文字仍可保留原文）。
- **英文单词优先按词发音，纯中文零改写**：口播里的连续全大写明显单词先归一为正常词形（`BEYOND → Beyond`）；只有明确的首字母缩写或非词字母串才逐字母读。自动规则只处理 ASCII 拉丁 token，纯中文文本、中文标点和原有措辞必须原样透传。
- **旁白结构默认完整**：一般视频默认在开头、每首歌曲转场、作品结尾与固定 CTA 都安排配音；没有明确要求不等于可以省略。只有完全自由探索类、以音乐/视觉实验本身为主体且不承担排名或解说结构的视频，才可在 brief/design 明确记录后按创意需要精简部分或全部旁白。
- **质量优先、总时长默认不设上限**：除非用户明确给出平台硬时长，不能为了压缩总时长牺牲内容、节奏或完整乐句。某首的完整副歌/演唱段需要更长就保留更长；若确有硬时长，应优先减少条目或精简旁白，不得掐断唱句、尾音或高光段。
- **封面排版与安全区同时过关**：标题必须按语义短语和视觉层级选择自然换行，禁止机械等字数拆行、留下孤字或让重点词断裂；歌手名字号应与同层级主要文字相同或更大，不能被缩成次要小字。标题、排名、主题等关键信息不得拆到画面最顶端和最底端，也不得整块死居中遮住人物/主体；应放在一个中上或侧向安全信息区，并通过首帧抽帧检查排版美感、主体避让和发布裁剪后的完整可读性。

## AI 克隆歌手音色 MV durable 模板协议

当 brief 明确是“AI 克隆/训练歌手音色制作 MV”“如果某歌手唱某歌”，且用户提供了可直接使用的训练音频 WAV 时，新建当期 `sandbox/<slug>/`，并复用 `tools/video/templates/ai-voice-mv/`；历史 `sandbox/angela-ai-mv-covers/` 已删除，不得恢复或继续依赖。先读 `tools/video/templates/README.md`，再按 `CONVENTIONS.md` 的“格式之三：AI 克隆歌手音色 MV（整首 MV 换训练音轨）”执行。

固定做法：
- 只把用户明确给出的训练 WAV 复制到当期项目 `audio/`，填写项目 `build/config.json`；用中央 durable builder 一首输出一个独立 MP4，不在 `sandbox/` 留唯一脚本副本。
- 仍然必须双平台查源（YouTube + B站），记录候选和取舍到 `SOURCES.md`。
- intro 必须复用当期 `voice-selection.json` 调用 `tools/tts/narrate.py`；未指定时 resolver 默认 CV002，唯一有效指定则按指定。歌曲音频在 intro 期间 duck，随后恢复。
- 全程叠加 `AI训练，仅供娱乐`，并通过抽帧确认无平台/UP 主水印、无网址、无路径、无提示词泄漏。
- 遇到 B站 4K 修复源带底部水印/烧词，优先尝试全宽横带 crop 保主体；crop 不成立再退回更干净源。不要交付带平台/UP 主水印的成片。
- `silencedetect` 报静音时，对照训练 WAV。若静音来自用户给的 e200/训练源，为保证整首 MV 对齐可保留，并在结果里说明。

## 配音

新启动的盘点视频统一用 `tools/tts/` 编号声音库，默认 `CV002「治愈少女」`。任务提示词若唯一精确指定 `CV001–CV008`、正式名称或注册别名，则使用指定角色；未知、模糊、冲突指定仍用 CV002，不做相似度猜测。同一期 intro、全部排名转场、作品 outro 与固定 CTA 必须共享同一 resolved voice ID，并通过 `verify_voice_usage.py` 校验。Qwen 运行环境、模型或参考母带缺失时必须停止，**不得静默降级 Kokoro**。Kokoro 只保留给显式 legacy ID 与历史工程复现。不要用 `npx hyperframes tts` 做中文。详见 `CONVENTIONS.md` 配音规范。

## Copyright stance

当前仅**本地测试**，不对外发布、不商用。若后期要发布，再单独评估 YouTube / B站 源素材的使用授权（两个平台条款不同，需分别评估）。

## How the two tools fit together

`yt-dlp` produces raw source material (full videos, clipped sections, audio, subtitles). HyperFrames does *not* re-encode arbitrary footage well — it is a browser-based renderer (headless Chrome screenshots stitched by FFmpeg), best at motion graphics, animated text/captions, overlays, and slide-style segments. So the natural split is:

- Use `yt-dlp` + FFmpeg for the actual video footage clips.
- Use HyperFrames for the "produced" layer: hooks, captions, lower-thirds, transitions, branded intro/outro, and composing footage clips onto an HTML timeline (footage referenced as `<video>`/image assets inside a composition).

Both ultimately shell out to **FFmpeg**, which is a hard dependency for the whole pipeline.

## Prerequisites

- **Node.js >= 22** (HyperFrames)
- **FFmpeg** (rendering for both tools) — `brew install ffmpeg`
- **yt-dlp** — `brew install yt-dlp` (or `pipx install yt-dlp`)
- Optional: **Git LFS** if cloning the HyperFrames repo with test baselines

## yt-dlp — common commands

```bash
# Download best mp4 video+audio
yt-dlp -f "bv*+ba/b" -o "%(title)s.%(ext)s" "<URL>"

# Clip a section without downloading the whole file (00:01:23 - 00:02:05)
yt-dlp --download-sections "*00:01:23-00:02:05" -f "bv*+ba/b" "<URL>"

# Pull subtitles / auto-captions (useful as a source for HyperFrames captions)
yt-dlp --write-auto-subs --sub-langs "en,zh-Hans" --skip-download "<URL>"

# Audio-only extraction
yt-dlp -x --audio-format mp3 "<URL>"
```

Note: 本地测试阶段不涉及发布；发布前的授权评估见上文 Copyright stance。

## HyperFrames — setup and dev loop

HyperFrames renders HTML compositions to video. Compositions are plain HTML files with `data-*` attributes (no React/DSL). Animations are driven by GSAP (or anime.js, Lottie, Three.js, WAAPI, CSS).

```bash
# Scaffold a project (non-interactive form preferred for agent use)
npx hyperframes init <name> --non-interactive --example blank

# Install agent skills — registers /hyperframes slash commands in Codex
npx skills add heygen-com/hyperframes

# Dev loop
npx hyperframes preview            # live-reload browser preview
npx hyperframes render --output output.mp4
npx hyperframes lint               # validate composition files before rendering
npx hyperframes inspect            # examine composition metadata
npx hyperframes doctor             # diagnose environment (FFmpeg, Node, etc.)
```

### Composition anatomy

A composition needs three things wired together:

1. Root element carrying metadata: `data-composition-id`, `data-start`, `data-width`, `data-height`.
2. Timed clips marked `class="clip"` with `data-start`, `data-duration`, `data-track-index`.
3. A paused GSAP timeline registered on `window.__timelines["<composition-id>"]` — HyperFrames drives this timeline frame-by-frame during render, which is what makes output **deterministic** (same input → identical MP4).

### Use the installed skills

Once `npx skills add heygen-com/hyperframes` is run, prefer these slash commands over hand-writing composition boilerplate — they encode the correct `class="clip"` / timeline-registration patterns:

- `/hyperframes` — composition authoring patterns
- `/hyperframes-cli` — dev-loop command guidance
- `/hyperframes-media` — asset preprocessing (TTS, transcription, background removal)
- `/gsap`, `/tailwind`, and adapter skills `/animejs` `/css-animations` `/lottie` `/three` `/waapi`

## References

- HyperFrames repo: https://github.com/heygen-com/hyperframes
- HyperFrames docs/quickstart: https://hyperframes.mintlify.app/quickstart
- yt-dlp: https://github.com/yt-dlp/yt-dlp
