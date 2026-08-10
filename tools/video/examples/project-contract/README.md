# Project contract synthetic example

这是 `tools/video/verify_project.py` 的**字段模板**，不是可播放、可渲染、可发布或可直接 PASS 的视频工程。仓库不提交伪装成 WAV/MP4 的 ASCII 文件，也不提交模型输出；`clips/*.mp4`、`narration/*.wav(.tts.json)` 与 `sources/raw/*.mp4` 必须由真实项目生成后再填写当前 SHA。

直接从仓库根运行会按预期 FAIL，并列出尚未水合的媒体、sidecar 与 placeholder SHA：

```bash
python3 tools/video/verify_project.py \
  --project tools/video/examples/project-contract
```

真实可执行正例由 `tools/video/tests/test_verify_project.py` 在临时目录生成小型、可被 ffprobe 解码的 MP4 和 24kHz mono WAV，再写入当前 hash/receipt；不会污染仓库。测试 sidecar 也使用中央 TTS gate 的完整 registry/config/model/reference portable claim，并注入合成的可信模型声明，因此不会读取或冒充本机 2GB 模型。真实项目必须由 `tools/tts/narrate.py` 生成当前 `voice-selection.json`、WAV 与相对路径 sidecar；生产门禁会验证本机 full-hash receipt，不能复用测试声明、这里的 placeholder hash 或虚构 evidence。manifest 每条 `text/wav/sidecar` 都与中央 gate 已验证的 canonical input、24kHz mono WAV 和输出 hash 一一绑定，未列出的额外 sidecar 也会失败。

可用 `shasum -a 256 <项目内文件>` 填写每个 `sha256`。`selection.download_receipt` 只保留选中 URL、脱敏 raw asset、时长与 raw→clip derivation；严禁复制 yt-dlp 原始 `info_json`、Cookie、HTTP headers。它只证明本地路径/SHA/时长链一致，不能联网证明账号、平台页面或“官方”声明真实。Vocal evidence 会重算 `showcase_align` 并绑定 analysis 的 clip SHA/时长；instrumental evidence 会实测 clip 时长、连续窗口和人工起止证据。终片是否确已混入且视听合格仍由后续 QA 证明。
