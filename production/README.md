# production/ — 生产区

用于正式产出的视频项目。只有在 `sandbox/` 验证过、遵循 `CONVENTIONS.md` 规范的流程才进入这里。

约定（随项目成熟再细化）：
- 每个成片放在独立子目录：`production/<项目名>/`。
- 保留可复现的输入（源 URL、切片时间码、composition 文件），而非只保留最终 MP4。
- 渲染产物与大体积素材通过 `.gitignore` 排除。
