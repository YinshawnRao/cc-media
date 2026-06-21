# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project intent

Build a pipeline that turns long-form online videos into self-media ("自媒体") short-form content:

1. **Source** — download/clip segments from **YouTube 和 B站（哔哩哔哩）** 作为并行素材源，用 `yt-dlp`。
2. **Compose** — build the published video (titles, captions, overlays, transitions, intros/outros) with **HyperFrames**, which renders plain HTML/CSS/JS to MP4.

> **素材源硬约束（优先级高于单期任务 brief）**：每条素材**两边都要找**（YouTube + B站），按清晰度 / 画面干净度（无烧死字幕台标）/ 立体声 / 现场质量综合选**质量高的一边**。除非 brief 显式排除某平台，否则**不允许只搜单边**。具体执行细则见 `CONVENTIONS.md` "素材源平台" 章节。

The repository is in an **exploration phase**. When scaffolding, follow `CONVENTIONS.md` (the single source of reusable standards) so future work stays consistent. The directory is not yet a git repo; run `git init` before the first commit.

## Layout

- `sandbox/` — 测试/实验区，内容视为可丢弃。所有试错先在这里跑。
- `production/<项目名>/` — 正式成片，每个项目一个子目录，保留可复现输入。
- `tools/` — 跨项目复用工具。`tools/tts/` = 本地中文配音 (Kokoro + misaki[zh])。
- `CONVENTIONS.md` — 全局规范，验证可行的做法沉淀到这里。

## 视频任务启动协议

接到任何视频制作 brief（如"做一个音乐盘点/主题视频…"），动手前先：
1. 读 `CONVENTIONS.md`（全局规范 + brief 格式 + QA 方法论）和 `tools/video/README.md`（从 brief 到成片的 Runbook）。
2. 复用脚本在 `tools/`（配音 `tools/tts/`、竖屏 `tools/video/vfill.sh`、音轨+合成模板 `tools/video/countdown_build.py`）——不要重造。
3. 涉及联网下载（yt-dlp）先确认对应平台 cookie 可用（仓库根目录 `www.youtube.com_cookies.txt` / `www.bilibili.com_cookies.txt`）；产物写 `sandbox/<slug>/`。**Cookie 只允许放根目录，不得在 `sandbox/` 下复制或覆盖第二份。**
4. **关键铁律**：① 渲染后必须用预混 master.wav **后期 mux**（HyperFrames 会压平音频动态）；② 我看不到画面/听不到声音，**QA 靠抽帧 Read + ffmpeg volumedetect/silencedetect**，不凭感觉下结论；③ 成片里不得出现水印/网址/提示词/路径。

## AI 克隆歌手音色 MV 复用协议

当 brief 明确是“AI 克隆/训练歌手音色制作 MV”“如果某歌手唱某歌”，且用户提供了可直接使用的训练音频 WAV 时，默认复用 `sandbox/angela-ai-mv-covers/`，不要新开实验目录。先读该目录的 `README.md` 和 `SOURCES.md`，再按 `CONVENTIONS.md` 的“格式之三：AI 克隆歌手音色 MV（整首 MV 换训练音轨）”执行。

固定做法：
- 把训练 WAV 复制到 `sandbox/angela-ai-mv-covers/audio/`，在 `build/build.py` 追加 `Song` 配置，一首输出一个独立 MP4。
- 仍然必须双平台查源（YouTube + B站），记录候选和取舍到 `SOURCES.md`。
- intro 用本地 `tools/tts/narrate.py --female` 生成“如果张韶涵唱《歌名》”类女声提示；歌曲音频在 intro 期间 duck，随后恢复。
- 全程叠加 `AI训练，仅供娱乐`，并通过抽帧确认无平台/UP 主水印、无网址、无路径、无提示词泄漏。
- 遇到 B站 4K 修复源带底部水印/烧词，优先尝试全宽横带 crop 保主体；crop 不成立再退回更干净源。不要交付带平台/UP 主水印的成片。
- `silencedetect` 报静音时，对照训练 WAV。若静音来自用户给的 e200/训练源，为保证整首 MV 对齐可保留，并在结果里说明。

## 配音

中文旁白用 `tools/tts/`（Kokoro + misaki[zh]），默认男声 `zm_yunxi`，女声 `zf_xiaoyi` 仅在明确要求时用。**不要用 `npx hyperframes tts` 做中文**（espeak 不支持 `zh`）。详见 `CONVENTIONS.md` 配音规范。

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
