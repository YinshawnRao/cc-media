# Grok × Qwen 一百声线实验室

这是给 Grok 用的隔离试听实验：用仓内 Qwen3-TTS **VoiceDesign 1.7B** 生成原创母带，再用 **Base 0.6B** 克隆统一文案。目标是一次给出 **50 女 + 50 男**，方便人工挑出能替换当前正式 5 男 5 女池的声线。

## 隔离边界

- 只读仓内模型：`tools/tts/models/qwen3-tts/`。
- Python 只用 `tools/tts/qwen.venv/bin/python`。
- 所有母带、样音、QA 和试听页只写本目录 `outputs/`（仓库已忽略）。
- 不读取项目 `voice-selection.json`，不调用正式 `narrate.py`，不分配 CV 编号，不自动提升候选。
- 不修改 `tools/tts/config.json`、`tools/tts/voices/registry.json` 或 `tools/tts/voices/` 内任何正式 WAV。
- 生成前后跑 `src/isolation_guard.py`，正式声音库哈希必须不变。

编号是 `GX-F01`–`GX-F50` 和 `GX-M01`–`GX-M50`。选定后告诉 Grok 这些编号，再另开正式提升步骤。

## 运行

从仓库根目录：

```bash
python3 tools/tts/research/grok-qwen-voice-lab/src/catalog.py
python3 tools/tts/research/grok-qwen-voice-lab/src/isolation_guard.py capture

python3 tools/tts/metal_preflight.py
tools/tts/qwen.venv/bin/python \
  tools/tts/research/grok-qwen-voice-lab/src/generate_samples.py --sample all

python3 tools/tts/research/grok-qwen-voice-lab/src/build_listen_page.py
python3 tools/tts/research/grok-qwen-voice-lab/src/isolation_guard.py verify
```

完成后打开：

```text
tools/tts/research/grok-qwen-voice-lab/outputs/listen.html
```

页面有「全部 / 女声 / 男声」三个 tab，可按分类筛选、搜索编号，并把喜欢的编号标记后复制。
