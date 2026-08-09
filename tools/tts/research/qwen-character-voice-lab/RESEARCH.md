# 本地多角色 TTS 调研

更新时间：2026-08-09。

本文件会在首轮实测完成后补齐最终数据。当前先记录选择边界：必须本地、免费、无需 API Key，以中文视频旁白为主，并优先考察角色差异、混合文字、Apple Silicon 实际可运行性和许可证。

## 阶段结论

首轮落地选择：**Qwen3-TTS VoiceDesign 1.7B + Base 0.6B，通过 MLX-Audio 8-bit 在 Apple Silicon 本地运行**。

它不是直接替换 Kokoro 默认值，而是新增“角色声线实验层”：

1. 用文字描述生成一次原创角色母带。
2. 人工挑选母带。
3. 用 Base 模型固定克隆母带，批量生成每期解说。
4. 保留 Kokoro 作为速度快、依赖轻、可预测的降级路径。

## 与当前 Kokoro 的核心差异

| 维度 | 当前 Kokoro + misaki[zh] | Qwen3-TTS VoiceDesign + Base |
| --- | --- | --- |
| 音色来源 | 8 个固定中文预置音色 | 自然语言设计原创声线，再固化克隆 |
| 角色差异 | 主要是男女、音高和基础音色 | 可控制年龄感、性格、气质、节奏、情绪 |
| 中文速度 | 很快，适合高频生产 | 母带设计较重；固化后 Base 批量较快 |
| 混合文字 | 中英混读已知不自然 | 官方覆盖中英日韩等 10 种语言，仍需逐句实测 |
| 稳定性 | 固定 voice id，稳定 | 每次 VoiceDesign 会漂；必须“母带一次生成 + Base 固化” |
| 资源 | 82M，轻量 | 1.7B VoiceDesign + 0.6B Base，8-bit 本地约 5GB 权重 |
| 适合用途 | 普通男/女旁白、故障降级 | 萌妹、傲娇、清冷、热血等角色化账号声音 |

## 候选方案初筛

| 方案 | 角色化能力 | 中文/混合语言 | Apple Silicon | 首轮定位 |
| --- | --- | --- | --- | --- |
| Qwen3-TTS | VoiceDesign、风格控制、3 秒克隆 | 官方 10 语言 | MLX-Audio 社区实现已在本机跑通 | **本轮实测主线** |
| CosyVoice 3 | 零样本克隆、跨语言、方言、细粒度控制 | 中文强，9 语言 + 18+ 方言 | 官方快速路径更偏 Linux/CUDA | 第二阶段质量对照 |
| GPT-SoVITS | 5 秒零样本、少量训练可长期固化 | 中英日韩粤，混合文本能力成熟 | 官方列出 Apple Silicon/CPU | 有授权参考音频时的长期角色方案 |
| MeloTTS | 多语言、中文可混英文、CPU 快 | 覆盖中英日韩 | Mac/CPU 相对轻 | 轻量基线，但角色设计弱 |
| ChatTTS | 对话韵律、笑声等口语控制 | 中英为主 | 可本地，但声线权利/稳定性需单独核验 | 只作探索，不进首轮 |
| Chatterbox Multilingual | 情绪和克隆，语言多 | 多语言，但句内 code-switching 风险需实测 | 有 MPS/MLX 社区路径 | 单语言情绪对照候选 |
| Fish Speech | 表达力、克隆、社区活跃 | 多语言 | Mac 路径和权重许可需谨慎 | 不作为默认生产主线 |

### 第一梯队的当前判断

- [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) + [MLX-Audio](https://github.com/Blaizzy/mlx-audio)：本轮首选。Qwen 官方提供 VoiceDesign、CustomVoice、Base 克隆和 10 种语言；MLX-Audio 是社区 Apple Silicon 后端，不是 Qwen 官方 MPS 实现。本机已有 1.7B VoiceDesign 8-bit 与 0.6B Base 8-bit，实测完整走通。
- [VoxCPM2](https://github.com/OpenBMB/VoxCPM)：官方 PyTorch 路线明确支持 MPS/CPU，同时有自然语言 Voice Design、克隆、多语言和方言。适合作为 Qwen 之后的第二套质量对照，但本轮不再额外下载约 5GB 模型和新环境。
- [CosyVoice 3](https://github.com/QwenAudio/CosyVoice)：零样本、多语言、18+ 中文方言和发音修补能力强；官方工程路径更偏 Linux/CUDA，当前 Mac 首轮落地成本高于 Qwen MLX。
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)：官方列出 Apple Silicon/CPU，5 秒零样本、约 1 分钟少样本训练，适合用户选中某个角色后用自有/授权参考音长期固化；不适合当前“无参考直接捏 8 个声音”的第一步。
- [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox)：CPU/MPS/CUDA、克隆和情绪控制都较友好，但以参考音为主，且带不可感知水印；可做后续单语言情绪对照。
- [IndexTTS2](https://github.com/index-tts/index-tts)：音色与情绪解耦有吸引力，但官方部署偏 CUDA，许可证也不是简单的 Apache/MIT，暂不作为 Mac 生产主线。

### 暂不进入首轮

- Fish Speech / S2 Pro：表达力强，但模型更重、macOS 支持和研究型权重许可都不利于当前生产目标。
- ChatTTS：随机 speaker 和口语控制有趣，但权重非商业、稳定性和高频噪声风险不适合作为正式旁白默认。
- MeloTTS：MIT、CPU 快、中文稳定，但角色设计/克隆能力弱，解决不了“有个性的多样声线”。
- EmotiVoice：Apache-2.0 且有大量预置声线，适合以后做“音色动物园”对照；技术栈相对旧。
- MOSS-TTS VoiceGenerator：2026 年的新角色声线方向，能无参考设计中英文声音，但官方依赖 CUDA 12.8，Mac 成熟度不如 Qwen MLX。
- Style-Bert-VITS2：日语动漫生态强，中文不是主优势；未来单做日语角色再测。

## 本轮实测结果

- 8 个 VoiceDesign 角色母带全部成功。
- 16 个 Base 克隆样音全部成功；8–10 秒音频平均生成约 2.90 秒。
- 8 个 Qwen 普通中文样音经本地 Whisper small 检查，核心文案均完整；规范化相似度 0.975–1.000。
- 88 个 raw/ready/试听 WAV 全部可解码、技术 QA 无失败。
- 同一 manifest 复跑时，8 条母带和 16 条克隆样音全部命中绑定模型、文案、角色描述、seed、参数及输出 SHA-256 的缓存。
- 混合语言的自动转录不足以确认日语发音；保留为人工试听项，不宣称已经通过。

完整数据见 `QA.md`、`qa/qwen-generation-report.json`、`qa/audio-report.json` 与 `qa/asr-report.json`。

## 风险与边界

- “代码 Apache/MIT”不自动等于所有社区量化权重、训练数据和生成声音可直接商用；本轮仅本地非商业技术测试。
- 不使用明星、声优、主播或其他可识别自然人的声音参考。
- VoiceDesign 的提示词只能描述抽象声学/角色特征，不写真实人物姓名。
- 自动 ASR 和响度检查不能判断“萌不萌、是否耐听”；最终一定需要人工听选。
- 用户已确认 `CV002「治愈少女」` 作为新盘点默认；正式策略、编号声音库和 fail-closed 生成入口已提升到 `tools/tts/`。其余角色未获选择前不进入默认策略。
