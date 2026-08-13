# sandbox/ — 单期视频工作区

每期视频使用独立的 `sandbox/<slug>/`。下载素材、切片、中间音视频和 QA 证据可以按项目需要组织；可复用工具与长期规范仍应沉淀到 `tools/` 和根目录 `CONVENTIONS.md`。

完成型项目固定保留下面两个并列目录：

```text
sandbox/<slug>/
├── renders/
│   ├── full.mp4           # HyperFrames raw render，可按项目改名
│   └── <slug>.mp4         # post-mux 后的唯一最终成片
└── publishing/
    └── xiaohongshu.md     # 标题候选、正文与末行 hashtags
```

- raw render 与 mux 后最终 MP4 都只能放在 `renders/`；最终交付固定为 `renders/<slug>.mp4`，不得另用 `final/`、`output/` 或项目根终片。
- 小红书文案固定写入 `publishing/xiaohongshu.md`，并通过 `tools/video/verify_publishing.py`；全部对外文字不得直接出现本期歌曲名称。
- 内容可按需清理；大体积素材与渲染产物不进入版本控制（见 `.gitignore`）。
