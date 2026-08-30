# 标准声线候选刷新实验（20 声线）

这是一次与正式 TTS 工作流完全隔离的候选生成实验，目标是生成 **10 个女声 + 10 个男声**，与当前正式十声线池一起人工试听，再另行决定是否提升为新标准。

## 隔离边界

- 只读复用固定的 Qwen3-TTS VoiceDesign 1.7B 与 Base 0.6B 本地模型。
- 所有母带、克隆样音、运行缓存、QA 和试听页只写入本目录 `outputs/`。
- 不读取项目 `voice-selection.json`，不调用正式 `narrate.py`，不分配 CV 编号，不自动提升候选。
- 不修改 `tools/tts/config.json`、`tools/tts/voices/registry.json`、`tools/tts/voices/` 内任何正式 WAV 或正式试听页。
- `outputs/` 已由仓库规则统一忽略，不进入正式声音库。
- 生成前后运行 `src/isolation_guard.py`，对正式配置、入口、注册表与完整 `tools/tts/voices/` 树做 SHA-256 对比；只有 `ISOLATION GATE: PASS` 才算实验完成。

## 风格矩阵

| ID | 性别 | 候选名 | 主要对比轴 |
| --- | --- | --- | --- |
| RF01 | 女 | 粗粝摇滚女声 | 微沙、直接、高能 |
| RF02 | 女 | 童话绘本女声 | 想象力、韵律、温暖 |
| RF03 | 女 | 黑胶暗夜女中音 | 低沉、烟熏、黑色电影感 |
| RF04 | 女 | 爆发赛事女声 | 快速、明亮、强推动 |
| RF05 | 女 | 冷面干幽默女声 | 平直、克制、冷幽默 |
| RF06 | 女 | 戏剧舞台女声 | 共鸣、张力、戏剧层次 |
| RF07 | 女 | 质朴生活女声 | 松弛、真实、生活质地 |
| RF08 | 女 | 极简未来女声 | 低情绪、精准、疏离 |
| RF09 | 女 | 复古歌舞厅女声 | 明艳、复古、俏雅 |
| RF10 | 女 | 紧迫调查女声 | 克制紧迫、果断、调查感 |
| RM01 | 男 | 粗声摇滚男声 | 粗粝、爆发、直接 |
| RM02 | 男 | 长者寓言男声 | 年长、温厚、寓言感 |
| RM03 | 男 | 高速电竞男声 | 高速、明亮、兴奋 |
| RM04 | 男 | 冷幽默男声 | 松弛、干笑点、反差 |
| RM05 | 男 | 史诗低男声 | 极低音、宏阔、神话感 |
| RM06 | 男 | 匠人质朴男声 | 可靠、朴实、手作质感 |
| RM07 | 男 | 锐利未来男高音 | 偏高、锋利、精确 |
| RM08 | 男 | 深夜丝绒男声 | 贴近、柔滑、成熟 |
| RM09 | 男 | 戏剧反派男声 | 狡黠、戏剧、受控张力 |
| RM10 | 男 | 现场纪实男声 | 临场、呼吸感、事件推进 |

所有描述都要求原创成年声线，不模仿、不命名、不冒充任何真人、平台预置音色或已注册 CV 声线。

## 运行

从仓库根目录执行：

```bash
python3 tools/tts/research/qwen-standard-refresh-20-lab/src/isolation_guard.py capture

../local-anime-avatar-workflow/work/venvs/poc-a-mlx-audio/bin/python \
  tools/tts/research/qwen-standard-refresh-20-lab/src/generate_samples.py --sample all

python3 tools/tts/research/qwen-standard-refresh-20-lab/src/build_listen_page.py
tools/tts/venv/bin/python \
  tools/tts/research/qwen-standard-refresh-20-lab/src/acoustic_diversity.py
python3 tools/tts/research/qwen-standard-refresh-20-lab/src/isolation_guard.py verify
```

完成后打开 `outputs/listen.html`。页面中“统一解说文案”与当前正式声线的盘点试听文本一致；混合语言文本也一致，便于后续汇总选择。

机械证据位于 `outputs/qa/`：

- `generation-report.json`：模型、revision、seed、输入指纹、母带与样音 SHA。
- `audio-report.json`：格式、时长、响度、峰值与长静音检查。
- `acoustic-diversity-report.json`：同文案样音的声学分布观察，只用于筛查跨度，不代替人工听感。
- `isolation-report.json`：正式 TTS 受保护文件的生成前后哈希对比。
