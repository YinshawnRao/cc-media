# tools/tts — 本地中文配音 (Kokoro + misaki[zh])

cc-media 的配音能力。本地、免费、无需 API KEY。经横评（见 `wemedia/tts-local-benchmark`）后选定 Kokoro，中文走 **misaki[zh]** 前端（jieba + pypinyin），不是 espeak。

## 音色策略（约定）

- **默认男声 `zm_yunxi`**。
- **女声 `zf_xiaoyi` 仅在明确要求女性配音时使用**（`--female` 或 `--voice zf_xiaoyi`）。
- 其余 6 个中文音色可用 `--voice` 显式指定，但不作默认。全部 8 个：
  `zf_xiaobei zf_xiaoni zf_xiaoxiao zf_xiaoyi`（女）/ `zm_yunjian zm_yunxi zm_yunxia zm_yunyang`（男）。

## 环境

- Python **3.12**（`/opt/homebrew/bin/python3.12`），venv 在 `tools/tts/venv`（已 gitignore，需各机自建）。
- 重建：
  ```bash
  /opt/homebrew/bin/python3.12 -m venv tools/tts/venv
  tools/tts/venv/bin/pip install "kokoro>=0.9.4" "misaki[zh]" soundfile \
    "librosa==0.11.0" "openai-whisper==20250625"
  ```
- 首次合成会下载 Kokoro 模型（自动缓存）。约 1–2s/条（warmup 后）。输出 24kHz wav。
- 多证据主唱检测首次使用前，**显式**预取 Whisper small（正常 build 不联网）：
  ```bash
  tools/tts/venv/bin/python -c "import whisper; whisper.load_model('small', device='cpu')"
  test -f "$HOME/.cache/whisper/small.pt"
  ```
  `tools/video/vocal_segments.py --mode multi` 会从该本地 checkpoint 加载；缺失、损坏或推理失败均非零退出。

## 用法

```bash
# 默认男声
tools/tts/venv/bin/python tools/tts/narrate.py "要配音的中文文本" -o out.wav

# 女声（明确要求时）
tools/tts/venv/bin/python tools/tts/narrate.py script.txt --female -o out.wav

# 显式指定音色 / 语速
tools/tts/venv/bin/python tools/tts/narrate.py "文本" --voice zf_xiaoni --speed 1.1 -o out.wav
```

## 接入 HyperFrames

生成的 wav 作为独立 `<audio>` 轨引入 composition（见 `CONVENTIONS.md` 全链路一节）。
后续若要自动字幕，可用 `npx hyperframes transcribe out.wav` 得到逐字时间轴。
注意：HyperFrames 内置 `npx hyperframes tts` 对**中文不可用**（传 `zh` 给 espeak，espeak 只认 `cmn`），所以中文配音统一走本工具。
