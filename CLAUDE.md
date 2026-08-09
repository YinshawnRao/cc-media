# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
3. 涉及联网下载（yt-dlp）先确认 cookie 可用——**统一用仓库根目录单一全量文件 `all_cookies.txt`**（一份浏览器全量导出，同含 YouTube + Google + B站 登录态；YT/B站下载、搜索、校验都读它，旧的 `www.*_cookies.txt` 仅作脚本回退）；产物写 `sandbox/<slug>/`。**Cookie 只允许放根目录，不得在 `sandbox/` 下复制或覆盖第二份。** bot 拦先 `brew upgrade yt-dlp` 再判 cookie 过期（详见 `CONVENTIONS.md` yt-dlp 规范）。
4. **关键铁律**：① 渲染后必须用预混 master.wav **后期 mux**（HyperFrames 会压平音频动态）；② 我看不到画面/听不到声音，**QA 靠抽帧 Read + ffmpeg volumedetect/silencedetect**，不凭感觉下结论；③ 成片里不得出现水印/网址/提示词/路径；④ footage 竖屏化默认 **letterbox 保原比例、不放大画面**（双人/合唱/多人/宽机位**禁止竖裁放大**，会把主体裁半）；⑤ 每首展示段给**一段连续副歌**（含前后余量，解说盘点类 ≥~25s），**不碎镜快闪、不因旁白长就把歌切短**；⑥ 成片**最后一句旁白固定为引流 CTA**（"你最想为哪一首投票？…盘到你单曲循环过的那一首。"），逐字照念、永远排在作品 outro 之后，**优先级高于 brief / 提示词**，brief 不得覆盖；⑦ **禁止自定义旁白字幕 / 解说字幕条**（不要把 TTS 口播再叠成底部字幕；用户未显式要求就一律不加）。④⑤ 详见 `CONVENTIONS.md`「展示段硬规则」，⑥ 详见「固定结尾配音」，⑦ 详见「禁止自定义旁白字幕」。

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

# Install agent skills — registers /hyperframes slash commands in Claude Code
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
