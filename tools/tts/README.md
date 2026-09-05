# Qwen TTS 旁白与编号声音库

当前新旁白统一由 `tools/tts/narrate.py` 调用 **Qwen3-TTS Base**，使用此前通过 Qwen 开源 TTS 工作流制作并登记的参考声音。它不是 Kokoro 包装脚本，也不使用 HyperFrames 内置 TTS。Kokoro 仅用于显式历史复现，不能自动回退。

## 选择、检查与生成

只在需要新生成旁白时执行。唯一精确指定的已注册编号/名称/别名优先；其他情况由代理根据作品主题、情绪与叙事节奏选择。决策池与策略以 [config.json](config.json) 为准，声音名称和画像以 [registry.json](voices/registry.json) 为准。不按歌手性别机械选声；模糊偏好可作为模型选择依据，不做名称相似度猜测。只有无法可靠判断时用 low 触发一次随机兜底。

```bash
python3 tools/tts/narrate.py --list-voices
python3 tools/tts/resolve_voice.py --task-prompt-file sandbox/<slug>/brief.txt --model-choice <池内精确ID> --model-reason '<作品情绪与叙事匹配理由>' --model-confidence high -o sandbox/<slug>/voice-selection.json
python3 tools/tts/doctor.py --voice <resolved_id>
```

doctor 同时核对核心 runtime/model 和已选母带，无需先检查未使用的 CV002。无 selector 的 doctor 仍提供维护用 preflight。初始化、模型/runtime 变化或 receipt 失效时，对已选声线运行 `doctor.py --voice <resolved_id> --full-model-hash`；日常复用有效 receipt。未使用声线和纯中文不需要的 mixed-script 不阻断生产。

原始 brief、最终选择、候选池、理由和置信度落盘后整期复用。历史 WAV 按原配置复现，不因规范整理自动重配。

```bash
python3 tools/tts/narrate.py '本期实际口播。' --selection-file sandbox/<slug>/voice-selection.json -o sandbox/<slug>/audio/intro.wav
python3 tools/tts/narrate.py --batch sandbox/<slug>/narration-request.json --selection-file sandbox/<slug>/voice-selection.json
python3 tools/tts/verify_voice_usage.py --selection sandbox/<slug>/voice-selection.json --project-root sandbox/<slug>
```

batch 的 blocks 每项为 id/text/output。文本与结构来自当期 manifest；默认 CTA 来源是 tools/video/outro_cta.py，用户可改写或省略。不在项目另写 VOICE 常量、直接调用引擎或调用另一套 provider。

每个 24kHz mono WAV 有 `.wav.tts.json`，绑定原文、声线、模型/reference、生成参数、fingerprint 和输出 SHA；必须 VOICE GATE: PASS。侧车证明本地工作流一致性，不独立证明参考声音来源或抵抗同 UID 主动篡改。最终可听性仍检查 mux 后 MP4。

## 发音与缓存

Qwen 默认 language=Auto，支持中英日混合文本。先实测外文发音，不自动删除外文；不自然时使用通行译名或 pronunciation_overrides。明显全大写英文单词优先词读，首字母缩写按实际读法；画面仍保留官方写法。

```bash
python3 tools/tts/text_normalizer.py '今天重听BEYOND；BTS也在候选。' --json
python3 tools/tts/narrate.py 'BTOB的这首作品。' --selection-file voice-selection.json --pronunciation 'BTOB=B to B' -o audio/sample.wav
```

自动归一化只处理 ASCII 拉丁 token；未显式覆盖时纯中文、标点、数字、seed 和既有缓存指纹保持原样。sidecar 的 source_text 记录原稿，normalized_text 记录实际发音输入。speed 由中央入口处理，不靠异常加速规避转场时长。

## 环境与恢复

日常旁白用 Base；VoiceDesign 用于参考母带制作。固定模型、revision、MLX-Audio 版本和发现路径以 config.json、model-manifests/ 和 qwen_runtime.py 为准，不在多份说明重复哈希。

中央 dispatcher/worker 先通过 stdlib-only Metal preflight 再加载 MLX。当前上下文无 Metal 权限时快速失败，在已授权执行上下文恢复。模型/runtime/母带缺失时修复固定输入并重跑，不换引擎或重抽声线。不要为了 Qwen 修改服务 Whisper 的 tools/tts/venv。

## 声音库维护

新增或替换母带须绑定逐字匹配的 reference_text，运行 `python3 tools/tts/verify_standard_pool.py`，通过正式生成、sidecar/VOICE、解码、响度、静音、削波和固定 ASR。命中 max_tokens 或异常长音不可晋级；skip-asr 只用于诊断。

维护可用 `doctor.py --full-library --check-mixed-script`；试听见 [listen.html](voices/listen.html)。[历史 Kokoro](research/legacy-kokoro.md) 仅在明确复现旧工程时阅读；[角色实验](research/qwen-character-voice-lab/README.md)和[声音池复选](research/qwen-standard-refresh-20-lab/README.md)不作为每期前置步骤。
