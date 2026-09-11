# AGENTS.md

本文件是 cc-media 的代理入口。仓库将 YouTube/B站素材、Qwen TTS 旁白和 HyperFrames 视觉合成为视频。

## 指令与范围

- 当期用户明确要求优先于仓库制作默认值。审美、文案、CTA、画幅与结构可以按 brief 调整；将影响构建的例外记入项目 manifest/design，不必为单期偏好修改全局规范。
- 视频任务在用户已指定内容的基础上，自主完成其余选材、文案、叙事与视觉设计，执行 [长期创作偏好](CONVENTIONS.md#长期创作偏好)：可信考证、创意适度、文字通俗纯净、按本期内容独立创作。用户无需在每期启动提示词中重申。
- 每期视觉按作品表达独立选择，复用工程时重新判断封面、配色与字体；设计依据见 [字幕与视觉](CONVENTIONS.md#字幕与视觉)。
- 新建、重做或优化封面必须使用 AIGC 图像模型生成或编辑：优先 imagegen；该入口不可用时可调用当前 agent 的其他 AIGC 生图工具，不限定工具名称。严禁以 SVG、HTML/CSS、Canvas、Python 等代码绘图替代封面生图。只有确认当前环境所有可用 AIGC 生图入口均不可调用时才可记录环境例外，见 [封面图像生成流程](CONVENTIONS.md#封面图像生成流程)。
- 封面默认采用无字 AIGC 视觉素材，标题、歌手名、年份等信息文字用 HTML/CSS 与项目离线字体独立排版，不建议交给图像模型生成。生图或编辑提示词明确要求不生成文字、为后期排版留出空间；具体流程与例外见 [封面图像生成流程](CONVENTIONS.md#封面图像生成流程)。
- 不伪造来源、检测结果或真人批准，不以偏好覆盖绕过媒体真实性、安全或技术验收。
- 开始先看 branch、HEAD、dirty worktree。保留无关改动；不重复 git init，暂存时只包含明确范围。
- 代码/文档任务按相关文件工作；视频制作读 [CONVENTIONS.md](CONVENTIONS.md) 和 [Runbook](tools/video/README.md)。已有项目遵循自身精确 pin 与已解析声线，不因新默认自动迁移。

## 测试与生产边界

- `sandbox/` 下全部是内部测试产物，完整 MP4 和配套 `publishing/` 文案也属于测试交付，不代表公开发布。不纳入发布版权审核，不因预设版权风险阻断制作、索要发布授权或将可用 MV 降级为音源封面、静图。
- `production/` 是正式产物与可复现工程的留存位置，进入版权、授权范围和公开发布风险核对流程。测试片需要公开发布时，先转入 production 发布流程；不能仅凭 sandbox 路径沿用测试免审规则。
- 上述区分规定项目用途与验收范围，不声明素材已获授权。两类项目都保留真实来源、版本、凭据边界与技术 QA；具体执行见 [测试产物与生产产物](CONVENTIONS.md#测试产物与生产产物)。

## 生产入口

- 定位为竖屏短视频，成片固定 **1080×1920（9:16）**；只有用户明确要求其他画幅才可变更，须在 manifest 的 output_format 记录尺寸和用户原话。横屏素材、全景保留或模型审美判断都不是改横屏的授权。
- “短视频”不等于总时长上限。没有用户硬时长时，先按每首完整连续副歌/代表段及自然收尾选窗，再累加整片时长；不按曲数均分分钟数，不为凑 3–4 分钟压缩歌曲。取材前后留足安全余量，唱字、尾音和未完成乐句不可截断；细则见 CONVENTIONS。
- 有旁白的盘点、解说与主题叙事成片，结尾必须保留一句简短的点赞、收藏、关注引流配音，作为最后一句旁白；默认使用中央固定短句。只有用户明确要求才可替换或省略，并记录用户原话；“非排名”“去模板化”或主题问句不能作为自行取消的理由。文字浮层不替代真实配音，须纳入最终音轨 QA，详见 [结尾引流配音](CONVENTIONS.md#结尾引流配音)。
- 素材默认双平台查找，先匹配歌手/表演版本，再优先可用官方 MV；两平台整体质量接近时优先 YouTube，按 [素材与画幅](CONVENTIONS.md#素材与画幅) 灵活比较实际音画与内容质量。用户指定 URL、排除平台或确认独占时使用 [来源例外](tools/video/README.md#来源记录与例外)，如实记录，禁止伪造“已搜索”。
- 需要在线取材时，制作开始前必须执行 [来源启动检测](tools/video/README.md#来源启动检测)，默认检查 YouTube 和 B站的实际登录态与搜索访问。任一平台 Cookie 失效、明确风控/拦截或排除执行权限问题后仍不通，暂停本期制作并等待用户确认；不能自行降级成单平台继续。代理授权、沙箱或本机权限不足先恢复执行环境，不据此判定平台不通；制作中出现同类故障也执行此规则。
- 当前旁白使用 **Qwen3-TTS**：中央 `tools/tts/narrate.py` 调用固定 Qwen runtime、模型和预先制作的参考声音。需要新生成旁白时才解析一次 `voice-selection.json`、对已选声音运行 doctor；同一期共用选择。详见 [TTS](tools/tts/README.md)。不默认使用或自动降级到 Kokoro，不走 HyperFrames 内置 TTS。
- 视频技能选择仓库内 [.agents/skills/hyperframes/SKILL.md](.agents/skills/hyperframes/SKILL.md)；CLI 与媒体能力也选其同目录版本。全局同名技能仅作可选技术参考，不引入另一套 TTS、画幅、审批或交付流程。技能路由见 [技能适配](tools/video/skill-routing.md)。
- 新项目固定 `hyperframes@0.6.69`，已有项目使用自身 package scripts/lockfile 的精确版本。升级是独立兼容性工作。渲染字体离线可用。
- 重 FFmpeg、ASR、HyperFrames 使用中央资源入口；多个 goal 持续推进，不添加跨项目等待锁。实现与故障处理见 [运行与恢复](tools/video/operations.md)。

## 文件与凭据边界

- 测试单期放 `sandbox/<slug>/`；正式产物及其可复现工程放 `production/<slug>/`，按上述用途区分；复用源码、schema、模板放 `tools/`。
- raw render 和最终 MP4 均放项目 `renders/`，最终文件为 `renders/<slug>.mp4`；配套文案为 `publishing/xiaohongshu.md`。
- `all_cookies.txt` 只由用户维护。代理只通过 `check_yt_cookie.py`、`yt_dlp_readonly.py`、`bili_search.py`、`bili_dl.py` 既定只读路径消费；禁止直接写入、chmod、touch、mv、cp、删除、过滤替换或安装。`filter_cookie_jar.py` 仅生成仓库外 candidate，由用户自行安装为 canonical。需要 Cookie 的 yt-dlp 一律经只读 wrapper，临时副本只由 wrapper 在仓库外管理。
- 不输出 Cookie、header、原始 info JSON；不把凭据复制进项目或 Git。`check_source_access.py` 通过上述既定读者和 wrapper 编排只读检测。Cookie 不可用时先按来源启动检测暂停确认，用户明确同意后才用公开下载或备选平台继续制作。

## 完成与验收

- 制作 brief 默认授权完成整片及发布文案。设计、试渲和 prompt expansion 是内部步骤；只有用户要求小样/阶段确认才停在预览。
- 标准项目：构建前 PROJECT（有旁白时含 VOICE），mux 后 PUBLISHING 与中央 `prepare_final_qa.py` 的本地 FINAL。编辑例外也必须通过实际媒体、哈希、旁白绑定和展示边界检查。
- 封面另走独立 [封面审美评估](tools/video/cover-aesthetic-review.md)：实际查看图文合成、手机预览与最终首帧，按本期 brief 评估并单独记录；明显不符合预期时仅退回封面重做，保持其他内容，刷新受影响的技术 QA。审美结论与机械门禁分开报告，不以技术 PASS 代替审美通过。
- 自由探索和 AI 音色 MV 使用各自受支持的 QA 路径；不伪造项目类型来套门禁。无旁白时 VOICE 标为不适用。
- 抽帧实际查看，检查最终音频。检测覆盖范围与 agent/human 身份如实标注；只有用户明确要求公开发布/发布验收/可发布交付才启用 `--require-human-review`。
- 失败先诊断、修复、重跑受影响步骤。来源启动检测要求暂停确认时，以及缺用户独占输入、必要权限/凭据或继续须改变核心 brief 时询问。REVIEW 按原因处理，已知检测能力限制不做无效换窗/换源循环。
- 交付报告 MP4、文案、当前 SHA、适用门禁结果、独立封面审美结论及审阅者身份，以及实际影响成片的问题；不附加未经询问的发布建议或套话。
