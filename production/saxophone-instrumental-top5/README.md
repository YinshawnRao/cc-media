# 最顶级的5首萨克斯纯音乐

竖屏 1080×1920、30fps 的 05→01 音乐盘点。视觉概念为“午夜黄铜母带档案”：封面和解说段使用档案卡，完整音乐段仅保留小型曲目信息，让现场/MV 画面和长音乐窗口成为主体。

## 排名

1. Songbird — Kenny G
2. Going Home — Kenny G
3. Lily Was Here — David A. Stewart & Candy Dulfer
4. Forever in Love — Kenny G
5. Mister Magic — Grover Washington Jr.

成片按 05 → 01 展示。英文曲名只上屏，不进入中文 TTS；开场及全部旁白不含“接下来”，也没有自定义旁白字幕。

## 可复现构建

```bash
# 旁白（本地 Kokoro）
../../tools/tts/venv/bin/python build/narrate_segments.py

# 音乐分析、画面单轨、预混 master.wav、HTML 时间线
../../tools/tts/venv/bin/python build/analyze_instrumental.py
python3 build/full_build.py

# HyperFrames 门禁和 SDR 渲染
npx --yes hyperframes@0.6.69 lint --json
npx --yes hyperframes@0.6.69 validate --json
npx --yes hyperframes@0.6.69 inspect --json
npx --yes hyperframes@0.6.69 render --sdr --output renders/full_raw.mp4

# 后期 mux 和成片 QA
bash build/mux_and_qa.sh
```

`master.wav` 必须在 HyperFrames 渲染后 mux。权威交付文件为 `renders/saxophone-instrumental-top5.mp4`，不是 `renders/full_raw.mp4`。

## 关键证据

- 来源：`SOURCES.md`
- 设计：`design.md`、`.hyperframes/expanded-prompt.md`
- 时间表：`meta.json`
- 纯音乐窗口门禁：`probe/instrumental_plan.json`
- 最终 QA：`qa/FINAL_QA.md`、`qa/COMPLETION_AUDIT.md`
