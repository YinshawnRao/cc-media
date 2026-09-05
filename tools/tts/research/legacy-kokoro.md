# Kokoro 历史复现

仅用于用户明确要求的旧工程复现，不是新项目默认、环境修复或 Qwen 故障降级路径。新项目见 [Qwen README](../README.md)。旧命令复用前核验依赖和项目。

## Legacy Kokoro

以下调用保留历史语义：

```bash
python3 tools/tts/narrate.py "中文文本" --voice zm_yunxi -o out.wav
python3 tools/tts/narrate.py "中文文本" --voice zf_xiaoyi -o out.wav
python3 tools/tts/narrate.py "中文文本" --female -o out.wav
```

`--female` 仍等价于 Kokoro `zf_xiaoyi`，只为旧脚本兼容；**新盘点不得用它表达默认**。已有项目的旧 `KPipeline` 和“接下来”垫话不批量迁移；新 Qwen 项目禁止复制这些旁路。

Kokoro 环境重建：

```bash
/opt/homebrew/bin/python3.12 -m venv tools/tts/venv
tools/tts/venv/bin/pip install "kokoro>=0.9.4" "misaki[zh]" soundfile \
  "librosa==0.11.0" "openai-whisper==20250625"
```

中文不要使用 `npx hyperframes tts`；生成的 24kHz mono WAV 作为独立 `<audio>` 轨进入 composition，最终仍以 post-mux MP4 的音频 QA 为准。
