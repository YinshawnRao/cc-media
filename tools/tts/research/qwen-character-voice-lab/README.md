# 角色化本地 TTS 实验室

状态：`RESEARCH ARCHIVE — 首轮自动 QA 已通过`。本目录保存完整调研、原始产物与复现脚本；正式编号声音、精选样音和当前默认配置已经提升到 `../../voices/` 与 `../../config.json`。完整首轮结果见 `QA.md`。

## 目标

验证一条比当前 Kokoro 预置音色更有角色感、仍然免费且可离线运行的中文配音流程：

```text
角色描述
  -> Qwen3-TTS VoiceDesign 生成原创声音母带
  -> Qwen3-TTS Base 固化/克隆母带
  -> 同一角色批量生成盘点解说与中英日混读
  -> 保留 raw WAV，另写去首尾静音的 ready WAV
  -> ffprobe / volumedetect / silencedetect 技术 QA
```

当前公平对照还会用仓库现有 `tools/tts/narrate.py` 生成全部 8 个 Kokoro 中文预置音色。所有方案使用同一段盘点文案。

## 为什么首轮选 Qwen3-TTS + MLX-Audio

- VoiceDesign 可以用自然语言直接描述“元气萌妹、傲娇吐槽、清冷学姐、热血少年”等原创声线。
- 官方推荐的“VoiceDesign 先做短母带，再交给 Base 克隆”能避免逐句重新设计造成音色漂移。
- Qwen3-TTS 支持中文、英文、日文、韩文等 10 种语言；首轮另有混合文字样音。
- 当前 Apple Silicon 机器已有参考项目固定的 MLX 8-bit 权重和隔离环境，本实验只读复用，不重复占用约 5GB 模型空间。
- 生成过程强制使用本地模型路径和 Hugging Face/Transformers 离线开关，不会静默回退云服务。

## 目录

```text
manifest.json                 # 文案、角色描述、模型版本与采样参数
RESEARCH.md                   # 候选方案对比与阶段结论
src/
  generate_qwen_samples.py    # VoiceDesign 母带 + Base 批量克隆
  generate_kokoro_baselines.py# 调用仓库现有 Kokoro 管线
  audio_qa.py                 # 最终 WAV 技术检查
  prepare_listen_audio.py     # 统一 -18 LUFS 的公平试听副本
  asr_qa.py                   # 复用本地 Whisper small 做内容证据
  build_listen_page.py        # 生成本地试听页
outputs/                         # 本地生成、整目录忽略；正式精选试听见 ../../voices/listen.html
  qwen3-tts/<voice>/raw|ready/
  kokoro/raw/
  listen.html
qa/
  qwen-generation-report.json
  kokoro-generation-report.json
  audio-report.json
  audio-summary.csv
  asr-report.json
  human-listening-template.csv
```

## 本机首轮命令

以下命令从仓库根目录执行。模型和 venv 默认从同级参考项目 `../local-anime-avatar-workflow` 只读复用，也可用环境变量覆盖。

```bash
# 1. Qwen VoiceDesign + Base（需要本机 Metal；沙箱环境要在获批的本地进程中运行）
../local-anime-avatar-workflow/work/venvs/poc-a-mlx-audio/bin/python \
  tools/tts/research/qwen-character-voice-lab/src/generate_qwen_samples.py

# 2. 当前项目 Kokoro 的 8 音色公平基线
python3 tools/tts/research/qwen-character-voice-lab/src/generate_kokoro_baselines.py

# 3. 统一试听响度 + 技术 QA + 本地试听页
python3 tools/tts/research/qwen-character-voice-lab/src/prepare_listen_audio.py
python3 tools/tts/research/qwen-character-voice-lab/src/audio_qa.py
python3 tools/tts/research/qwen-character-voice-lab/src/build_listen_page.py

# 4. 可选但本轮实际执行：本地 Whisper small 内容检查
tools/tts/venv/bin/python tools/tts/research/qwen-character-voice-lab/src/asr_qa.py
```

可覆盖路径：

```bash
QWEN_VOICE_DESIGN_MODEL=/path/to/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit \
QWEN_BASE_MODEL=/path/to/Qwen3-TTS-12Hz-0.6B-Base-8bit \
python /path/to/generate_qwen_samples.py
```

## 人工试听门禁

自动 QA 只能确认文件可解码、时长、响度、长静音和削波风险，不能替代听感。试听时建议每条按 1–5 分记录：

- 角色辨识度
- 中文自然度
- 情绪/节奏是否适合盘点视频
- 长期听是否疲劳
- 中英日作品名是否可懂
- 同一母带在不同句子里的音色一致性

用户已选中 `CV002「治愈少女」` 并将其提升为新盘点默认；其余 7 个角色仍是可选候选。后续横评可继续在 `qa/human-listening-template.csv` 记录评分。
