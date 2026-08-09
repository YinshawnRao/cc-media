# tools/tts — cc-media 编号化本地配音

这里是工作区唯一正式的中文旁白入口和声音库。新启动的盘点视频默认使用 **`CV002「治愈少女」`**；Kokoro 保留为显式 legacy 兼容，不再是新盘点默认。

实际声音、参考母带和同文案样例都在 [`voices/`](voices/)；直接打开 [`voices/listen.html`](voices/listen.html) 可试听 CV001–CV008 与 Kokoro 基线。完整首轮调研与 QA 证据在 [`research/qwen-character-voice-lab/`](research/qwen-character-voice-lab/)。

## 默认与解析硬规则

`config.json` 是默认配置唯一真源，`voices/registry.json` 是角色编号、正式名称和别名唯一真源。

1. 任务提示词的结构化 `配音：` / `音色：` / `voice=` 字段中，唯一精确匹配的编号、名称或别名优先。
2. 没有结构化字段时，只识别带配音语境的唯一、肯定式精确匹配。
3. 没指定、指定不存在、描述模糊、同时命中多个角色：全部回退 `CV002「治愈少女」`。
4. 不做相似度猜测。“男声”“女声”“可爱一点”“二次元声音”等无法唯一定位的描述仍按 CV002。
5. 每个项目只解析一次；intro、排名转场、作品 outro、固定 CTA 共用同一份 `voice-selection.json`。
6. Qwen runtime、固定模型或参考母带缺失时硬失败，禁止静默换 Kokoro。

## 新盘点标准流程

先做默认链路自检；正式机器初始化或模型变更后再加 `--full-model-hash`：

```bash
python3 tools/tts/doctor.py
python3 tools/tts/doctor.py --full-model-hash
```

先把用户原始任务提示词保存为 UTF-8 文件或直接传给 resolver：

```bash
python3 tools/tts/resolve_voice.py --task-prompt-file brief.txt \
  -o sandbox/<slug>/voice-selection.json
```

单条生成：

```bash
python3 tools/tts/narrate.py "第五名，真正让人记住的，是情绪突然拉满的瞬间。" \
  --selection-file sandbox/<slug>/voice-selection.json \
  -o sandbox/<slug>/narration/p5.wav
```

批量生成只加载一次 Base 模型，推荐盘点项目使用：

```json
{
  "blocks": [
    {"id": "intro", "text": "今天盘点五首经典作品。", "output": "narration/intro.wav"},
    {"id": "p5", "text": "第五名，先从这一首开始。", "output": "narration/p5.wav"},
    {"id": "outro_cta", "text": "你最想为哪一首投票？评论区告诉我。", "output": "narration/outro-cta.wav"}
  ]
}
```

```bash
python3 tools/tts/narrate.py --batch sandbox/<slug>/narration-request.json \
  --selection-file sandbox/<slug>/voice-selection.json
```

每个 WAV 会生成一个 `.wav.tts.json` sidecar，记录 resolved voice ID、模型 revision、参考母带 SHA、文本 SHA、输出 SHA 和生成参数。完成后运行：

```bash
python3 tools/tts/verify_voice_usage.py \
  --selection sandbox/<slug>/voice-selection.json \
  --project-root sandbox/<slug>
```

必须输出 `VOICE GATE: PASS`。

## 显式选择

```bash
# 查看全部编号与名称
python3 tools/tts/narrate.py --list-voices

# 直接指定编号、正式名称或注册别名
python3 tools/tts/narrate.py script.txt --voice CV004 -o out.wav
python3 tools/tts/narrate.py script.txt --voice 清冷学姐 -o out.wav

# 无效指定会警告并回退 CV002
python3 tools/tts/narrate.py script.txt --voice CV999 -o out.wav
```

`--speed 0.5–2.0` 仍受支持。Qwen/MLX 当前不直接支持 speed，中央入口会用 FFmpeg `atempo` 做真实后处理，不会静默忽略。

Qwen 默认使用 `language=Auto`，允许中英日等混合文本；不要再套用 Kokoro 的“外文一律跳过”。外文专名先生成并听检，只有读音确实不自然时才换通行中文译名、音译/谐音，或从口播省略并保留画面原文。新盘点 intro 第一段始终禁止“接下来”。

## 运行环境

正常旁白只加载 Qwen3-TTS 0.6B Base；1.7B VoiceDesign 只在新增角色母带时使用。默认离线查找顺序：

1. 环境变量 `CC_MEDIA_QWEN_PYTHON` 与 `CC_MEDIA_QWEN_BASE_MODEL`。
2. `tools/tts/qwen.venv/` 与 `tools/tts/models/` 下固定版本。
3. 当前同级参考项目 `../local-anime-avatar-workflow` 已验证的 MLX-Audio 0.4.5 venv 和 Base 8-bit 固定权重。

模型不会在生成过程中静默联网下载，也不会复制进每个视频项目。当前固定 Base revision 为 `50f45ef0047cde7e84c2ef04326acb8ada2436a7`，模型树 SHA-256 为 `e536317ea04672c76a6baa12d2cf72efe88358db6b7f8f1588a6a8b203153903`。

不要把 MLX/Qwen 依赖塞进现有 `tools/tts/venv`；该 venv 继续服务 Kokoro legacy、Whisper 与人声检测。

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
