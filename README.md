# cc-media

将在线音乐/视频素材制作成自媒体视频：yt-dlp/FFmpeg 负责来源与媒体处理，Qwen3-TTS 提供编号参考声音的旁白，HyperFrames 渲染 HTML 视觉层，预混 master 后期 mux 为最终 MP4。

- 代理入口：[AGENTS.md](AGENTS.md)
- 编辑目标与默认：[CONVENTIONS.md](CONVENTIONS.md)
- 封面设计参考：[封面案例库](references/covers/README.md)（图片、提示词与设计简述；辅助本期表达，不照搬案例）
- 制作步骤、manifest 与 QA：[tools/video/README.md](tools/video/README.md)
- Qwen 旁白：[tools/tts/README.md](tools/tts/README.md)
- 环境/下载/资源恢复：[operations.md](tools/video/operations.md)
- 本地与全局技能选择：[skill-routing.md](tools/video/skill-routing.md)
- 可复用媒体骨架：[durable templates](tools/video/templates/README.md)

## 目录与提交

- `sandbox/<slug>/`：内部测试工程与产物，包括完整 MP4、封面和配套文案；不纳入发布版权审核，不因预设版权顾虑降级可用 MV。
- `production/<slug>/`：正式产物及需长期留存的可复现工程；在此处理授权范围与公开发布风险。
- `tools/`：跨项目源码、schema 和模板。
- `references/covers/`：精选封面案例与设计参考，独立留存必要图片、提示词和设计理由；不作为新作品的固定模板。

测试与生产的验收边界、测试片转正式发布的处理见 [测试产物与生产产物](CONVENTIONS.md#测试产物与生产产物)。目录划分不代表素材已经获得授权，两类项目均执行真实来源与技术 QA。

raw render 与最终 MP4 位于项目 renders/，最终文件名为 renders/<slug>.mp4；发布文案为并列 publishing/xiaohongshu.md。Git 保存源码、文档、配置和轻量证据，以及封面案例库明确收录的必要图片快照；不提交 Cookie、下载媒体、模型、普通 WAV/MP4 或缓存。已有项目不自动迁移版本、声线或视觉。

## 开始

依赖 Node >=22、FFmpeg 和 yt-dlp；新生成旁白还需要固定 Qwen/MLX 环境与已登记参考声音。按 Runbook 解析任务并执行适用步骤；代码/规范维护不需要启动模型或制作整片。
