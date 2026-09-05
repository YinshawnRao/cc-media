# 运行环境与故障恢复

只在运行相关工具或排障时读取；编辑偏好见 [CONVENTIONS](../../CONVENTIONS.md)。

## 资源与工具入口

重任务使用 resource_budget.py，线程/worker 范围、活跃进程身份、回收和回退行为以脚本为真源。当前预算是启动时按活跃任务数分配 4→3→2，已运行任务不暂停或动态调速；允许范围内的显式设置由 wrapper 校验。不添加跨 goal flock、semaphore、全局队列或等待锁。

- HyperFrames：在项目目录运行 `python3 ../../tools/video/resource_budget.py hyperframes -- <项目固定版本render命令>`。
- FFmpeg：`python3 tools/video/resource_budget.py ffmpeg -- ffmpeg -threads __CC_MEDIA_THREADS__ <ffmpeg参数>`；Python 工具复用同模块入口。
- ASR：vocal_segments.py、offline_asr.py 或中央 QA。不得裸跑 whisper/whisper-cli；固定模型、版本和哈希由中央代码验证。
- Qwen：先通过中央 stdlib-only Metal preflight；受限上下文无法访问 Metal 时只让当前 TTS 失败，再通过已授权执行权限恢复，避免先 import MLX 导致原生崩溃。无需等其他配音任务完成。
- Node/FFmpeg/yt-dlp 与字体依赖以当前固定项目配置核验；不为排障自动升级全局环境。

## 下载与 Cookie

all_cookies.txt 的用户所有权见 [AGENTS](../../AGENTS.md)。代理只用既定只读工具，绝不修权限或安装 candidate。check_yt_cookie.py 检查静态内容不证明服务端会话新鲜。

下载失败区分登录态、播放器/签名兼容、码流不可用和网络错误。先复现最小公开请求，尝试同版本可用候选/客户端。需要 Cookie 时经 yt_dlp_readonly.py，临时工作副本由其在仓库外创建和清理，日志不输出凭据或原始 info JSON。

确认兼容问题时优先使用明确版本的隔离环境恢复。仍需要新凭据或额外权限时请求具体输入，保留已尝试路径与可恢复现场。

## 展示检测与恢复

先得到 multi 分析并识别 REVIEW 的原因。窗口不佳就换窗，素材不佳就换同版本源，模型/runtime 缺失就修复环境。Live/单声道/宽混音等检测能力限制可直接用真实辅助证据形成 hash-bound agent observation，不要求尝试必定重复 REVIEW 的候选。不得把分类能力不足伪装成机器 OK；不得覆盖 active-word 等硬 FAIL。

showcase_align.py 的观察/批准文件必须显式传入，工具不自动读取同目录记录。逐曲记录绑定 clip、analysis SHA、narr_end/show_start/show_end 和 evidence_files。只有人工实际复核才记录 status=approved/reviewer_kind=human。输入改变后重建证据。

## Render、mux 与 QA

新项目固定 hyperframes@0.6.69；历史项目跟自己的 pin。只使用当前版本已验证的命令/属性；新增能力先最小验证，再更新 pin 及兼容说明，不把最新上游技能当作旧版 API 保证。

长片同时解码多个视频可能增加 setup 成本，优先使用 concat 单 footage_track；具体问题先 doctor/最小试渲。字体冻结到项目，避免在线 fetch。输出保持 SDR 并检查真实编码/色彩信息。

动态混音使用 master.wav post-mux。先比对时长再编码，保持完整尾音与尾帧。机械检查包括解码、媒体结构、当前 hash、音轨一致性、固定 ASR、响度、true peak 和 >1.5 秒静音红线。模型不能用自报结论替代这些检查。

内部错误按根因修复后从失败步骤重跑，并刷新受影响下游 SHA/evidence；没有新输入或不同方案时不重复同一失败路径。需要改变核心 brief、用户独占输入、权限或凭据时请求必要信息。goal 状态遵循执行环境提供的生命周期规则，不另维护一份三次计数协议。

历史案例与旧命令在 [legacy-production-notes.md](research/legacy-production-notes.md)，仅为排障线索，需重新核验。
