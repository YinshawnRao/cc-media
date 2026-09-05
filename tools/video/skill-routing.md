# cc-media 技能适配

仓库的生产入口是 [AGENTS](../../AGENTS.md) 和 [Runbook](README.md)。只按任务需要加载下面的仓库技能，不再先遍历通用视频工作流。

| 任务 | 仓库技能/工具 |
| --- | --- |
| HTML、时间线、素材布局 | [.agents/skills/hyperframes/SKILL.md](../../.agents/skills/hyperframes/SKILL.md) |
| lint、预览、render | [hyperframes-cli](../../.agents/skills/hyperframes-cli/SKILL.md) |
| 配音、ASR、其他媒体处理 | [hyperframes-media](../../.agents/skills/hyperframes-media/SKILL.md)，旁白固定 tools/tts/narrate.py 的 Qwen 能力 |
| 特定动画 runtime | .agents/skills/ 下对应 gsap/animejs/waapi 等，只读取实际使用的一种 |
| 用户明确要网站捕获或迁移 | 对应 website-to-hyperframes/remotion-to-hyperframes 技能 |

仓库技能来自已安装 HyperFrames 技能集，当前有本地适配；生产兼容基线是新项目 hyperframes@0.6.69，已有项目以自身 pin 为准。技能描述中的功能不是当前 pin 的能力证明，未用过的 API/CLI 必须先用该版本确认。不要在普通任务中运行浮动 skills update/install 覆盖这些适配。

本机全局 .agents/.codex/.claude 下可能存在同名技能与软链接；它们不是本仓库当前工作流的默认入口。无需删除全局文件来消除歧义，也不修改其他仓库的技能配置。需要升级或同步时先比较真实路径、内容和版本，作为单独兼容工作验证。

通用技能的 TTS provider 选择、自动 Kokoro 降级、默认 16:9、必须先用户审批、只交预览、元素/easing 配额等在本仓库不生效。制作授权、画幅和编辑偏好来自用户及当前仓库配置；动画技术细节按需借鉴。
