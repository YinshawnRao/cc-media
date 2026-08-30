# 2026-08-30 生成结果

本报告绑定当前隔离实验输出。用户试听后，RF02、RM04、RM07 已通过显式人工选择分别迁入正式编号 CV017、CV015、CV016；迁入动作复制冻结资产和元数据，生产流程不依赖本实验目录。

## 完成情况

- 候选：20 个，女声 10、男声 10。
- 每个候选：1 条 VoiceDesign 原创母带、1 条统一盘点文案、1 条中英日混读。
- 试听文件：60 个，24kHz mono，统一响度副本。
- HTML：20 张候选卡、60 个播放器，可按女声/男声筛选并跳转当前正式十声线页面。

## 机械检查

- 音频 QA：`60/60 PASS`，`0 FAIL`。
- 40 条正式比较样音：`0 warning`。
- 3 条原创母带检测到 `>0.8s` 的风格性停顿：RF03、RF08、RM08；对应统一盘点与混合语言样音均无长静音警告。
- 生成记录：60 条；最大 token count `143`，没有达到 `max_tokens=2048`，未发现 token 上限截断。
- 时长范围：约 `5.70–11.02s`。
- 声学分布观察：女声统一文案中位基频约 `173.61–285.30Hz`；男声约 `79.60–199.42Hz`。20 条统一文案 SHA 均唯一。该观察只说明可测声学特征存在跨度，不判断自然度、角色辨识度或长期耐听度。
- 隔离终验：`ISOLATION GATE: PASS`，正式 TTS 的 60 个受保护文件生成前后 `changed=0`。

## 当前输出哈希

| 文件 | SHA-256 |
| --- | --- |
| `outputs/listen.html` | `1505aa13ae1a514c05a9717ed0b6b13e7df20ab99861971004fc9561c6f1ed47` |
| `outputs/qa/generation-report.json` | `641b5c988ad380670cd2f282376494b139d3440dbeb7e54b1b44d81c2668e394` |
| `outputs/qa/audio-report.json` | `785237d9e19eb4273d9b84bb90459d3c554afb7cda60ce9a37cac54d907c33d1` |
| `outputs/qa/acoustic-diversity-report.json` | `e0057d101b2b6830fef6b62d1561b769ad06817a974ad05f67719ddf4f806ef9` |
| `outputs/qa/isolation-report.json` | `ff5749f9c15d33690baadd57613cfaee966e08df93d720f7dffe309b9d4ab435` |

若任一音频、manifest、生成参数或页面模板变化，必须重建对应输出并更新本报告哈希。
