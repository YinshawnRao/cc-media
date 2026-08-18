# tools/tts — cc-media 编号化本地配音

这里是工作区唯一正式的中文旁白入口和声音库。新启动的盘点视频若未唯一指定音色，会从 **`CV001 / CV002 / CV003 / CV004 / CV005 / CV008`** 女声池随机一次；Kokoro 只保留为显式 legacy 兼容。

实际声音、参考母带和同文案样例都在 [`voices/`](voices/)；直接打开 [`voices/listen.html`](voices/listen.html) 可试听 CV001–CV008 与 Kokoro 基线。完整首轮调研与 QA 证据在 [`research/qwen-character-voice-lab/`](research/qwen-character-voice-lab/)。

## 默认与解析硬规则

`config.json` 是随机池与选择策略唯一真源，`voices/registry.json` 是角色编号、正式名称、分组和别名唯一真源。

1. 任务提示词的结构化 `配音：` / `音色：` / `voice=` 字段中，唯一精确匹配的编号、名称或别名优先。
2. 没有结构化字段时，只识别带配音语境的唯一、肯定式精确匹配。
3. 没指定、指定不存在、描述模糊、同时命中多个角色：从配置女声池随机一次。
4. 不做相似度猜测。“男声”“女声”“可爱一点”“二次元声音”等无法唯一定位的描述仍进入同一随机池。
5. 否定式不是选择：`不要/不使用/不想用/拒绝使用/不考虑/请勿使用/不能用/不可用/不是/避免/除了` 等前置否定，以及 `CV004 除外/不用/不考虑/不要了/不能用/不行` 等后置否定，都按未指定处理并进入随机池；裸 `CVxxx` 也不能绕过同一句否定。若后面另有唯一肯定式替换（如“我不想用 CV004，请改用 CV003”），则只采用肯定指定。
6. 每个项目只解析一次；随机结果和候选池写入 `voice-selection.json`，intro、排名转场、作品 outro、固定 CTA 共用该文件，禁止逐段重抽。
7. Qwen runtime、固定模型或参考母带缺失时只让当前 TTS 步骤硬失败；代理修复固定环境、模型、母带或 receipt 后重跑当前步骤及受影响下游门禁，禁止静默换 Kokoro，也不得因此暂停整个 goal。
8. Qwen dispatcher 与 direct worker 在 import MLX 前都必须先运行 stdlib-only Metal preflight。当前执行上下文拿不到 Metal 时固定快速返回，不启动 native worker、不产生 Python crash 弹窗；goal 应自动切换到具备 Metal 权限的执行上下文重跑。多个 goal 可同时合成，禁止用共享锁、队列、sleep 或等待另一个配音完成来串行化。

## 新盘点标准流程

首次初始化、模型/runtime 版本变化或 receipt 失效时，先做一次完整模型哈希（约 2 GB 顺序读取）；它只会在固定且被忽略的 `tools/tts/runtime/model-verifications/` 闭包中原子写入 `0600` receipt。manifest 只允许来自 `tools/tts/model-manifests/`。两者及其项目内父目录均拒绝 symlink；关键文件必须属于当前 UID，且不能 group/world writable。日常自检核对 receipt、manifest、实际 MLX-Audio 版本、模型 realpath、完整文件集合及含 `ctime_ns` 的每文件 stat 签名，不会重复读取 2 GB。默认 doctor 只校验核心 runtime/model 和预检声线 CV002 母带；CV002 在这里不决定项目随机结果。worker 仍会在真正生成前重新校验本期已选母带，并在加载模型后复验模型：

```bash
python3 tools/tts/doctor.py --full-model-hash
python3 tools/tts/doctor.py
```

resolver 完成后，若项目选中的不是预检声线 CV002，用解析出的准确 ID 检查本期实际音色；doctor 的 `--voice` 只接受唯一精确的编号、名称或注册别名，不做随机回退：

```bash
python3 tools/tts/doctor.py --voice CV004
```

声音库维护、角色母带变更或混合文本能力回归时，再显式运行完整审计。`--full-model-hash` 只表示重建模型树 receipt，不隐含全声音库或 mixed-script 检查；需要时可组合：

```bash
python3 tools/tts/doctor.py --full-library --check-mixed-script
python3 tools/tts/doctor.py --full-model-hash --full-library --check-mixed-script
```

纯中文生成本来就不读取 `pronunciation.json`，因此日常 doctor 跳过 mixed-script policy 与实际生成语义一致；含 ASCII 大写 token 或显式发音覆盖的任务仍会在 `narrate.py` 中按需加载该策略并 fail closed，也可提前用 `--check-mixed-script` 单独验明。

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
    {"id": "outro_cta", "text": "你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。", "output": "narration/outro-cta.wav"}
  ]
}
```

```bash
python3 tools/tts/narrate.py --batch sandbox/<slug>/narration-request.json \
  --selection-file sandbox/<slug>/voice-selection.json
```

每个 WAV 会生成一个 `.wav.tts.json` sidecar，记录 resolved voice ID、模型 revision、完整模型验证 receipt 摘要、参考母带 SHA、文本 SHA、输出 SHA 和生成参数。`output` 使用相对 sidecar 的可迁移路径。新 Qwen sidecar 必须先通过当前机器的本地 receipt 校验，再与当前模型比较可迁移 claim（包含 model/revision、manifest/tree、MLX-Audio、文件数/字节数和 `qwen_config_sha256`）。原始 receipt SHA 只保留为生成机器审计值，跨机器移动时不要求相等。完成后运行：

```bash
python3 tools/tts/verify_voice_usage.py \
  --selection sandbox/<slug>/voice-selection.json \
  --project-root sandbox/<slug>
```

必须输出 `VOICE GATE: PASS`。

中央门禁会拒绝项目外或经 symlink 读取的 selection、sidecar、output，并对当前 Qwen sidecar 重算完整 canonical contract：严格检查 `1.0.0` 纯中文 / `1.1.0` 归一化字段集合与类型，绑定项目 selection、模型与参考母带、language/speed、生成参数、fingerprint inputs/fingerprint、派生 seed、文本 SHA，以及实际 WAV 的 SHA 和格式元数据；缺字段、自相矛盾或冒充出来的额外派生字段都会失败。门禁同时暴露每个 sidecar 的 canonical 原始口播（有 `source_text` 时取它，否则取 `text`）及 provenance mode。只有复现历史工程时，才可显式加 `--allow-legacy-qwen-sidecars` 接受旧式 absolute-output、无 receipt 的 Qwen sidecar；结果会标记 `legacy_explicit` 并警告，默认不兼容性放行。

### Receipt 的诚实信任边界

receipt、canonical sidecar contract 与 WAV 哈希都是本地、同一 UID 的诚实工作流一致性证据，用来发现版本漂移、字段手改、错模型和“不完整 sidecar + 任意 WAV”式冒充；它们**不是音色来源证明，也不是抵抗同 UID 主动伪造的密码学证明**。拥有同一用户权限的人仍可替换 WAV，并同时重算或改写仓库配置、manifest、模型、receipt 与项目 JSON。若要把这一边界升级为对抗性证明，需要受信生成器签名、不可变或外部验签存储，并处理模型读取和产物落盘竞态；当前离线制作流程不声称提供该能力。

## 显式选择

```bash
# 查看全部编号与名称
python3 tools/tts/narrate.py --list-voices

# 直接指定编号、正式名称或注册别名
python3 tools/tts/narrate.py script.txt --voice CV004 -o out.wav
python3 tools/tts/narrate.py script.txt --voice 清冷学姐 -o out.wav

# 无效指定会警告并从女声池随机一次
python3 tools/tts/narrate.py script.txt --voice CV999 -o out.wav
```

`--speed 0.5–2.0` 仍受支持。Qwen/MLX 当前不直接支持 speed，中央入口会用 FFmpeg `atempo` 做真实后处理，不会静默忽略。

## 混合文本发音与纯中文稳定性

Qwen 默认使用 `language=Auto`，允许中英日等混合文本；不要再套用 Kokoro 的“外文一律跳过”。明显英文单词优先按词发音：连续全大写明显单词会先转为正常词形，例如 `BEYOND → Beyond`、`GO UP → Go Up`；明确的首字母缩写或不可自然词读的字母串才展开为逐字母读，例如 `BTS → B T S`、`S.H.E. → S H E`、`ABCD → A B C D`。画面标题仍可保留官方大写写法。

这个预处理是窄范围的：未提供显式覆盖时，纯中文文本、中文标点、数字和原有措辞逐字原样透传，并跳过发音策略加载；生成 seed、请求结构和旧缓存 fingerprint 均不改变。它不会为了修英文而给中文分词、加空格或转拼音。

先预览实际送入 TTS 的文本与判断依据：

```bash
python3 tools/tts/text_normalizer.py "今天重听BEYOND；BTS也在候选。" --json
```

判断不确定时先生成短样音；仍需指定时，用精确的项目级覆盖，不要先写生硬中文谐音：

```bash
python3 tools/tts/narrate.py "BTOB的这首作品。" \
  --selection-file voice-selection.json \
  --pronunciation "BTOB=B to B" \
  -o narration/pronunciation-check.wav
```

批量请求可在顶层或单个 block 写 `pronunciation_overrides`，block 级覆盖优先：

```json
{
  "pronunciation_overrides": {"BTOB": "B to B"},
  "blocks": [
    {"id": "intro", "text": "BTOB的五首作品。", "output": "narration/intro.wav"}
  ]
}
```

发生归一化时，`.wav.tts.json` 会额外保存 `source_text`、`normalized_text`、策略 hash 和逐项决策；纯中文 sidecar 不增加这些字段，以继续命中既有缓存。`--pronunciation` 只支持 Qwen 路径，Legacy Kokoro 明确拒绝。外文专名只有在短样音仍不自然时才考虑通行中文译名、音译或从口播省略。新盘点 intro 第一段始终禁止“接下来”。

## 运行环境

正常旁白只加载 Qwen3-TTS 0.6B Base；1.7B VoiceDesign 只在新增角色母带时使用。默认离线查找顺序：

1. 环境变量 `CC_MEDIA_QWEN_PYTHON` 与 `CC_MEDIA_QWEN_BASE_MODEL`。
2. `tools/tts/qwen.venv/` 与 `tools/tts/models/` 下固定版本。
3. 当前同级参考项目 `../local-anime-avatar-workflow` 已验证的 MLX-Audio 0.4.5 venv 和 Base 8-bit 固定权重。

模型不会在生成过程中静默联网下载，也不会复制进每个视频项目。当前固定 Base revision 为 `50f45ef0047cde7e84c2ef04326acb8ada2436a7`，模型树 SHA-256 为 `e536317ea04672c76a6baa12d2cf72efe88358db6b7f8f1588a6a8b203153903`，实际 MLX-Audio 必须为 `0.4.5`。worker 只有在完整哈希 receipt 与当前模型文件 stat、manifest、runtime 版本全部一致，且模型加载后复验仍完全相同时才允许生成；缺 receipt 或任一文件变化都会 fail closed，并提示重新运行 `doctor.py --full-model-hash`。receipt 只在 ignored runtime 目录复用，不写进项目，也不改变纯中文的 text、seed、请求形状或既有 cache fingerprint；但安全升级前生成、尚无 portable model validation 的旧 sidecar 不再算 cache hit，下一次请求会基于真实当前模型一次性重新生成，绝不向旧音频补写伪 provenance。

Metal preflight 只检查**当前进程上下文**能否取得默认设备，不 import `mlx` / `mlx_audio`，也不输出底层 IOKit、用户路径或 native 异常。它不是跨 goal 调度器：每条命令独立检查后立即继续，两个或更多具备权限的 goal 仍会并行运行。

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
