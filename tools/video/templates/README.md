# Durable video templates

这里保存从历史 `sandbox/` 工程中提炼出的、可跨项目复用的**源码骨架**。模板不包含下载媒体、训练音频、TTS 输出、Cookie、人物素材、成片或历史歌单；`sandbox/` 仍是每期实际项目和可丢弃产物的位置。

所有项目仍先执行仓库根 `CONVENTIONS.md` 与 `tools/video/README.md`。模板只解决稳定的构建机械步骤，不覆盖当期的选源、封面设计、旁白、showcase / instrumental gate 和终片 QA。

## 1. `ai-voice-mv/`：整首 MV 换训练音轨

适用于用户明确提供可直接使用的训练 WAV，并要求“如果某歌手唱某歌”或“AI 音色 MV”的任务。历史 `sandbox/angela-ai-mv-covers/` 已按实验目录生命周期删除；不要恢复其中媒体，也不要继续依赖该路径。

项目布局建议：

```text
sandbox/<slug>/
├── build/config.json          # 从 project.example.json 复制后填写
├── voice-selection.json       # resolve_voice.py 的项目级结果
├── raw/                       # 本地 MV 视频，不进 git
├── audio/                     # 用户明确提供并复制进本项目的训练 WAV，不进 git
├── voice/                     # narrate.py 生成的 intro WAV + sidecar，不进 git
└── final/YYYY-MM-DD/          # 一首一个 MP4，不进 git
```

先生成项目级声线选择和 intro；没有显式指定时 resolver 会得到默认 CV002，显式有效指定则沿用指定角色：

```bash
python3 tools/tts/resolve_voice.py --task-prompt-file sandbox/<slug>/brief.txt \
  -o sandbox/<slug>/voice-selection.json

python3 tools/tts/narrate.py '如果某位歌手唱《示例歌名》。' \
  --selection-file sandbox/<slug>/voice-selection.json \
  -o sandbox/<slug>/voice/song-key-intro.wav --speed 1.12

mkdir -p sandbox/<slug>/assets sandbox/<slug>/build
xcrun swiftc tools/video/templates/ai-voice-mv/watermark.swift \
  -o sandbox/<slug>/build/watermark
sandbox/<slug>/build/watermark \
  sandbox/<slug>/assets/ai-training-watermark.png 'AI训练，仅供娱乐' 30
```

复制示例配置并填写项目相对路径，然后先检查、再构建：

```bash
cp tools/video/templates/ai-voice-mv/project.example.json sandbox/<slug>/build/config.json
python3 tools/video/templates/ai-voice-mv/build.py \
  --project sandbox/<slug> --config build/config.json --check
python3 tools/video/templates/ai-voice-mv/build.py \
  --project sandbox/<slug> --config build/config.json song-key
```

模板会：精确裁切可选的全宽污染带、补足略短视频尾帧、修剪 intro 首尾静音、intro 期间 duck 训练音轨、叠加 `AI训练，仅供娱乐`，最后输出 H.264/AAC MP4。配置必须提供项目内透明角标 PNG；随模板保留的 `watermark.swift` 只负责离线生成这张当期输入图，不含媒体或人物信息。模板不会下载素材、读取仓库外目录或生成 TTS。

硬前置：`video` 必须已经与训练音频从同一歌曲起点对齐；视频允许比训练 WAV 短不超过 0.5 秒，模板仅用尾帧补足这种编码级差异，不能修复剧情片头或错误歌曲偏移。intro 修剪后还必须比训练音频至少短 1 秒，给正歌留下有效展示。`--check` 会验证这些时长关系，并确认每条 intro sidecar 内嵌的 selection 与项目 `voice-selection.json` 完全一致、记录的输出 SHA-256 与当前 WAV 一致。

## 2. `longform-timeline/`：长篇叙事时间线媒体骨架

适用于多章节、长解说、每首保留长连续高光的叙事视频。历史 `sandbox/lirh-yangcl-timeline/` 曾验证此结构，但其人物、文案、旧 Kokoro 脚本、静态双头像封面和强制 ambient 底床都不是通用模板，已刻意剔除。

模板只冻结稳定、可验证的媒体主轴：

- 从已竖屏化的项目片段精确预切每章画面；
- 将所有章节拼成一个 `footage_track.mp4`，避免 HyperFrames 同时打开多个长视频；
- 将项目已经按当期 ducking/响度方案预混好的章节 WAV 统一到 48kHz stereo，并串成 `master.wav`；
- 生成含逐段旁白路径、声线 ID 与音频 SHA-256 的 `timeline.json`，供当期 HyperFrames composition 读取时间锚点和 provenance。

它**不生成通用封面或视觉 HTML**。封面必须按当期 brief/design 与现行安全区规范设计；TOP 仍须 N→1 且不能提前泄榜，非 TOP 时间线才能按叙事顺序。

```bash
cp tools/video/templates/longform-timeline/project.example.json \
  sandbox/<slug>/build/timeline-config.json

python3 tools/video/templates/longform-timeline/build.py \
  --project sandbox/<slug> --config build/timeline-config.json --check
python3 tools/video/templates/longform-timeline/build.py \
  --project sandbox/<slug> --config build/timeline-config.json
```

每个 segment 都必须显式声明自己的 `narration_wavs`。intro、song、outro、cta 等结构角色至少绑定一个由 `tools/tts/narrate.py` 生成并带 `.wav.tts.json` sidecar 的 WAV；只有 `role: "free"` 可明确写空数组 `[]`。模板逐条核对 sidecar 内嵌 selection、非空 resolved voice ID 和当前 WAV 的输出 SHA-256，因而不会再由无绑定的顶层清单冒充实际章节旁白。

`audio_segment` 是该章旁白与音乐最终预混 WAV。完成预混后运行下面的命令，把输出第一列写入同一 segment 的 `audio_segment_sha256`；示例配置中的 64 个 `0` 只是必须替换的占位值，任何重混或编辑后都要重新计算：

```bash
shasum -a 256 sandbox/<slug>/audio/segments/intro.wav
shasum -a 256 sandbox/<slug>/audio/segments/song-01.wav
```

`--check` 会核对声明 SHA 与当前文件，并要求每个 `audio_segment` 覆盖 `duration_sec`；只容忍最多约 0.05 秒的容器/编码误差，1 秒音频不能再被静默补成数分钟。普通叙事项目应显式包含 intro、各章节转场、作品 outro 和固定 CTA；完全自由探索类例外必须先写进 brief/design。每个歌曲章节还必须把 `acceptance` 写成 `showcase_align` 或 `instrumental_plan`，但该字段只是可审计声明，不能代替实际 gate 证据。

这些 selection、mapping 与 SHA 校验建立的是 **provenance 绑定**：证明旁白被声明绑定到该段、指定的预混文件被用于构建；不能证明旁白波形确实已经混入预混文件，也不能证明成片里一定可听、咬字正确或没有被音乐遮蔽。实际可听性仍必须以 mux 后终片的 isolated narration ASR、final AAC ASR、响度/静音检测和抽检 QA 为准。

构建后再编写/更新 HyperFrames composition，执行 `--sdr` render，并以预混 `master.wav` 后期 mux。最终交付和 QA 对象始终是 mux 后 MP4，不是 `footage_track.mp4`、raw render 或 `master.wav`。

## 安全与仓库边界

- 配置内只接受项目目录中的相对路径，拒绝绝对路径和 `..`。
- 模板不接收 Cookie 参数，也不会输出 Cookie 或环境变量。
- 示例配置只有占位名称，不含真实 URL、账号、人物路径或真实媒体哈希；64 个 `0` 是刻意不可通过素材校验的 SHA-256 占位值。
- `*.wav`、`*.mp4`、`raw/`、`audio/`、`final/` 等仍由根 `.gitignore` 排除。
