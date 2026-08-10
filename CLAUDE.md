# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
3. 复用脚本在 `tools/`（配音 `tools/tts/`、竖屏 `tools/video/vfill.sh`、音轨+合成模板 `tools/video/countdown_build.py`）——不要重造。新项目旁白必须把同一个 `voice-selection.json` 传给 `tools/tts/narrate.py`；不得直接 `KPipeline(...)`、不得硬编码 `VOICE`。
4. 涉及联网下载（yt-dlp）统一读取仓库根目录 `all_cookies.txt`；用 `tools/video/filter_cookie_jar.py` 从仓库外、权限 `0600` 的原始导出中过滤 YouTube / Google / B站域并原子写入，旧 `www.*_cookies.txt` 仅作脚本回退。原始全量导出不得进入仓库，Cookie 不得复制到 `sandbox/`。产物写 `sandbox/<slug>/`；bot 拦先 `brew upgrade yt-dlp` 再判 cookie 过期（详见 `CONVENTIONS.md`）。
5. **关键铁律**：① 渲染后必须用预混 master.wav **后期 mux**（HyperFrames 会压平音频动态）；② 我看不到画面/听不到声音，**QA 靠抽帧 Read + ffmpeg volumedetect/silencedetect**，不凭感觉下结论；③ 成片里不得出现水印/网址/提示词/路径；④ footage 竖屏化默认 **letterbox 保原比例、不放大画面**（双人/合唱/多人/宽机位**禁止竖裁放大**，会把主体裁半）；⑤ 每首展示段给**一段连续副歌**（含前后余量，解说盘点类 ≥~25s），**不碎镜快闪、不因旁白长就把歌切短**；⑥ 除启动阶段已明确归类的完全自由探索类无旁白实验外，成片**最后一句旁白固定为引流 CTA**（"你最想为哪一首投票？…盘到你单曲循环过的那一首。"），逐字照念、永远排在作品 outro 之后，**优先级高于 brief / 提示词**；⑦ **禁止自定义旁白字幕 / 解说字幕条**（不要把 TTS 口播再叠成底部字幕；用户未显式要求就一律不加）。④⑤ 详见 `CONVENTIONS.md`「展示段硬规则」，⑥ 详见「固定结尾配音」，⑦ 详见「禁止自定义旁白字幕」。

## 新盘点内容硬约束

- 翻唱歌曲优先且必须尽力使用对应翻唱者版本的 MV/现场/正式演出；只有 YouTube+B站均无可用对应版本时才退回原唱视频，并在 `SOURCES.md` 留证。
- 版本身份正确后，官方 MV 优先于清晰度；只要有可用官方 MV，即使画质稍差也优先使用。仅在官方 MV 不存在、无法取得或目标段结构性不可用时换源，并在 `SOURCES.md` 说明。
- 凡 TOP / 排名 / 榜单，必须按最后一名到第一名 N→1 揭晓；封面和 intro 不得提前列歌单、展示排序或泄露第一名，每首只在对应转场揭晓。非排名片不要挂 TOP 名义。
- intro 第一段禁用“接下来”。Qwen 多语种能力默认允许保留外文；若实测读音不自然，再用通行中文译名、音译/谐音或从口播省略，屏幕原文可保留。
- 明显英文单词优先按词发音：连续全大写单词先归一为正常词形（`BEYOND → Beyond`）；只有明确的首字母缩写或非词字母串才逐字母读。自动规则只处理 ASCII 拉丁 token，纯中文文本、中文标点和原有措辞必须原样透传。
- 一般视频默认在开头、每首歌曲转场、作品结尾和固定 CTA 都有配音；只有完全自由探索类、以音乐/视觉实验为主体且不承担排名或解说结构的视频，才可在 brief/design 明确记录后精简部分或全部旁白。
- 整体质量优先，总时长默认不设上限；除非用户明确给出平台硬时长，否则不得为了变短牺牲内容、节奏或完整乐句。确有硬时长时优先减条目或精简旁白，不能掐断高光段。
- 封面标题按语义和视觉层级自然换行，不机械拆行、不留孤字；歌手名必须与同层级主要文字同字号或更大，不能偏小。关键信息仍集中在一个不遮主体的安全信息区，首帧检查排版、主体避让和平台裁剪安全。

## 配音

新启动的盘点视频统一用 `tools/tts/` 编号声音库，默认 `CV002「治愈少女」`。任务提示词若唯一精确指定注册声音则按指定；未知、模糊或冲突指定回退 CV002。同一期所有旁白必须共享同一 resolved voice ID；Qwen 环境、模型或母带缺失时硬失败，不得静默换 Kokoro。Kokoro 仅用于显式 legacy ID 与历史复现。不要用 `npx hyperframes tts` 做中文。详见 `CONVENTIONS.md`。

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
