# Qwen 声线扩展试听实验区

这是一个与 `cc-media` 正式 TTS 工作流完全隔离的本地试听实验区。它只读复用固定的 Qwen3-TTS VoiceDesign 1.7B 与 Base 0.6B 模型，不读取或修改：

- `tools/tts/config.json`
- `tools/tts/voices/registry.json`
- `tools/tts/voices/listen.html`
- 任一项目的 `voice-selection.json`
- 任一正式项目旁白或 sidecar

所有生成物都写入本目录的 `outputs/`。仓库现有 `.gitignore` 已忽略 `tools/tts/research/**/outputs/`，因此候选母带、样音、QA 和试听页不会进入正式声音库。

## 第一批候选

`manifest.json` 当前包含 69 种原创成年声线：

- 16 种短视频电影 / 纪录片经典解说型
- 27 种扩展女声
- 18 种扩展男声
- 8 种中性声

“经典解说型”复现的是常见的声学与节奏特征，例如快节奏影视直述、阳光解说、磁性大叔、悬疑低沉、冷峻科幻、浑厚纪录片、自然纪录片、人文纪录片和历史纪录片；不克隆、不命名、不冒充任何平台预置音色或可识别真人。

## 生成

从仓库根目录执行。必须先得到 `QWEN METAL PREFLIGHT: PASS`；失败时不要 import MLX，应换到有 Metal 权限的本地终端重跑。

```bash
python3 tools/tts/metal_preflight.py

../local-anime-avatar-workflow/work/venvs/poc-a-mlx-audio/bin/python \
  tools/tts/research/qwen-voice-expansion-lab/src/generate_samples.py

python3 tools/tts/research/qwen-voice-expansion-lab/src/build_listen_page.py
```

生成过程可中断后重跑；脚本按 manifest、模型 revision、文本、参考母带和参数指纹复用已经完成且哈希一致的文件。

只生成指定候选时，使用 persona ID：

```bash
../local-anime-avatar-workflow/work/venvs/poc-a-mlx-audio/bin/python \
  tools/tts/research/qwen-voice-expansion-lab/src/generate_samples.py \
  --only film_fast_direct documentary_weathered
```

## 试听与证据

生成完成后直接打开：

```text
tools/tts/research/qwen-voice-expansion-lab/outputs/listen.html
```

页面提供类型筛选、性别筛选、关键词搜索、统一文案试听和母带试听。公平试听 WAV 统一到 24kHz 单声道、约 `-18 LUFS / -1.5 dBTP`。机械检查写入：

```text
outputs/qa/audio-report.json
outputs/qa/generation-report.json
```

自动 QA 只证明文件可解码、格式、响度、峰值与静音情况；声音是否自然、耐听、适合长期旁白仍需人工试听。

## 正式声音库边界

本实验区的候选永远不会自动成为 `CV009+`。只有人工选中后，才另开正式提升步骤：分配永久 CV 编号、复制选定母带与样音、登记 SHA、处理旧 selection 兼容、更新测试并重建正式试听页。
