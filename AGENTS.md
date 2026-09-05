# AGENTS.md

本文件是 cc-media 的代理入口。仓库将 YouTube/B站素材、Qwen TTS 旁白和 HyperFrames 视觉合成为视频。

## 指令与范围

- 当期用户明确要求优先于仓库制作默认值。审美、文案、CTA、画幅与结构可以按 brief 调整；将影响构建的例外记入项目 manifest/design，不必为单期偏好修改全局规范。
- 不伪造来源、检测结果或真人批准，不以偏好覆盖绕过媒体真实性、安全或技术验收。
- 开始先看 branch、HEAD、dirty worktree。保留无关改动；不重复 git init，暂存时只包含明确范围。
- 代码/文档任务按相关文件工作；视频制作读 [CONVENTIONS.md](CONVENTIONS.md) 和 [Runbook](tools/video/README.md)。已有项目遵循自身精确 pin 与已解析声线，不因新默认自动迁移。

## 生产入口

- 定位为竖屏短视频，成片固定 **1080×1920（9:16）**；只有用户明确要求其他画幅才可变更，须在 manifest 的 output_format 记录尺寸和用户原话。横屏素材、全景保留或模型审美判断都不是改横屏的授权。
- “短视频”不等于总时长上限。没有用户硬时长时，先按每首完整连续副歌/代表段及自然收尾选窗，再累加整片时长；不按曲数均分分钟数，不为凑 3–4 分钟压缩歌曲。取材前后留足安全余量，唱字、尾音和未完成乐句不可截断；细则见 CONVENTIONS。
- 有旁白的盘点、解说与主题叙事成片，结尾必须保留一句简短的点赞、收藏、关注引流配音，作为最后一句旁白；默认使用中央固定短句。只有用户明确要求才可替换或省略，并记录用户原话；“非排名”“去模板化”或主题问句不能作为自行取消的理由。文字浮层不替代真实配音，须纳入最终音轨 QA，详见 [结尾引流配音](CONVENTIONS.md#结尾引流配音)。
- 素材默认双平台查找，先匹配歌手/表演版本，再优先可用官方 MV。用户指定 URL、排除平台或确认独占时使用 [来源例外](tools/video/README.md#来源记录与例外)，如实记录，禁止伪造“已搜索”。
- 当前旁白使用 **Qwen3-TTS**：中央 `tools/tts/narrate.py` 调用固定 Qwen runtime、模型和预先制作的参考声音。需要新生成旁白时才解析一次 `voice-selection.json`、对已选声音运行 doctor；同一期共用选择。详见 [TTS](tools/tts/README.md)。不默认使用或自动降级到 Kokoro，不走 HyperFrames 内置 TTS。
- 视频技能选择仓库内 [.agents/skills/hyperframes/SKILL.md](.agents/skills/hyperframes/SKILL.md)；CLI 与媒体能力也选其同目录版本。全局同名技能仅作可选技术参考，不引入另一套 TTS、画幅、审批或交付流程。技能路由见 [技能适配](tools/video/skill-routing.md)。
- 新项目固定 `hyperframes@0.6.69`，已有项目使用自身 package scripts/lockfile 的精确版本。升级是独立兼容性工作。渲染字体离线可用。
- 重 FFmpeg、ASR、HyperFrames 使用中央资源入口；多个 goal 持续推进，不添加跨项目等待锁。实现与故障处理见 [运行与恢复](tools/video/operations.md)。

## 文件与凭据边界

- 单期放 `sandbox/<slug>/`；需长期保留的可复现工程放 `production/<slug>/`；复用源码、schema、模板放 `tools/`。
- raw render 和最终 MP4 均放项目 `renders/`，最终文件为 `renders/<slug>.mp4`；配套文案为 `publishing/xiaohongshu.md`。
- `all_cookies.txt` 只由用户维护。代理只通过 `check_yt_cookie.py`、`yt_dlp_readonly.py`、`bili_search.py`、`bili_dl.py` 既定只读路径消费；禁止直接写入、chmod、touch、mv、cp、删除、过滤替换或安装。`filter_cookie_jar.py` 仅生成仓库外 candidate，由用户自行安装为 canonical。需要 Cookie 的 yt-dlp 一律经只读 wrapper，临时副本只由 wrapper 在仓库外管理。
- 不输出 Cookie、header、原始 info JSON；不把凭据复制进项目或 Git。Cookie 不可用先尝试公开下载与备选源。

## 完成与验收

- 制作 brief 默认授权完成整片及发布文案。设计、试渲和 prompt expansion 是内部步骤；只有用户要求小样/阶段确认才停在预览。
- 标准项目：构建前 PROJECT（有旁白时含 VOICE），mux 后 PUBLISHING 与中央 `prepare_final_qa.py` 的本地 FINAL。编辑例外也必须通过实际媒体、哈希、旁白绑定和展示边界检查。
- 自由探索和 AI 音色 MV 使用各自受支持的 QA 路径；不伪造项目类型来套门禁。无旁白时 VOICE 标为不适用。
- 抽帧实际查看，检查最终音频。检测覆盖范围与 agent/human 身份如实标注；只有用户明确要求公开发布/发布验收/可发布交付才启用 `--require-human-review`。
- 失败先诊断、修复、重跑受影响步骤。仅在缺用户独占输入、必要权限/凭据或继续须改变核心 brief 时询问。REVIEW 按原因处理，已知检测能力限制不做无效换窗/换源循环。
- 交付报告 MP4、文案、当前 SHA、适用门禁结果和实际影响成片的问题；不附加未经询问的发布建议或套话。
