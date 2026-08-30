# AGENTS.md

This file is the single top-level source of agent instructions for this repository. Other agent entry files may point here, but must not copy and independently maintain these business rules.

## Project intent

Build a pipeline that turns long-form online videos into self-media ("自媒体") short-form content:

1. **Source** — download/clip segments from **YouTube 和 B站（哔哩哔哩）** 作为并行素材源，用 `yt-dlp`。
2. **Compose** — build the published video (titles, captions, overlays, transitions, intros/outros) with **HyperFrames**, which renders plain HTML/CSS/JS to MP4.

> **素材源硬约束（优先级高于单期任务 brief）**：每条素材**两边都要找**（YouTube + B站）。先锁定正确歌手/表演版本，再优先可用官方 MV；官方 MV 画质稍差也不因此降级。只有官方 MV 不存在或结构性不可用时才比较 Live / 综艺 / 二次来源，并在同一来源层级内按画面干净度、立体声和清晰度选择。除非 brief 显式排除某平台，否则**不允许只搜单边**。具体执行细则见 `CONVENTIONS.md` "素材源平台" 章节。

The repository is in an **exploration phase** and is already an initialized Git repository. Before work, inspect the current branch, HEAD and dirty worktree; do not repeat `git init`, overwrite unrelated changes or stage outside the agreed scope. When scaffolding, follow `CONVENTIONS.md` (the single source of reusable production standards) so future work stays consistent.

## Layout

- `sandbox/` — 单期视频的下载素材、渲染产物和可丢弃试验区；内容不承诺长期保留。新项目的 raw render 与 mux 后最终 MP4 全部放在 `sandbox/<slug>/renders/`，发布文案放在并列的 `sandbox/<slug>/publishing/`。
- `production/<项目名>/` — 正式成片，每个项目一个子目录，保留可复现输入。
- `tools/` — 跨项目复用工具。可复用的工具调研放 `tools/<domain>/research/`，不能因为仍在试验就塞进视频成品目录；`tools/tts/` = 编号化本地中文配音库（Qwen3-TTS 角色声音 + Kokoro legacy），实际母带与样音放 `tools/tts/voices/`。
- `CONVENTIONS.md` — 全局规范，验证可行的做法沉淀到这里。

## 视频任务启动协议

接到任何视频制作 brief（如"做一个音乐盘点/主题视频…"），动手前先：
1. 读 `CONVENTIONS.md`（全局规范 + brief 格式 + QA 方法论）和 `tools/video/README.md`（从 brief 到成片的 Runbook）。
2. 先运行 `python3 tools/tts/doctor.py`；初始化机器或模型/runtime 变化后运行一次 `--full-model-hash`。必须得到 `TTS DOCTOR: PASS preflight=CV002`；这里的 CV002 仅是稳定的环境预检声线，不是新项目默认成片声线。缺模型、参考母带、receipt 或固定运行环境时只停止当前 TTS 步骤：先按 doctor 输出修复/安装固定依赖、恢复模型与母带并重建 receipt，再重跑 doctor、旁白及所有受影响下游门禁；不得静默降级 Kokoro，也不得把可修复的环境问题变成普通 goal 的用户确认点。
3. **新启动的自媒体视频先解析一次配音**：把用户原始任务提示词交给 `tools/tts/resolve_voice.py`，将结果保存为项目级 `voice-selection.json`。用户唯一精确指定的已注册编号/名称/别名优先；未指定、未知、模糊或冲突时，代理必须根据作品主题、整体情绪、叙事角度与节奏，从 `CV012 / CV013 / CV014 / CV015 / CV016 / CV002 / CV003 / CV008 / CV009 / CV017` 十声线标准池（5 男 5 女）选择最匹配的一款，并把选择、简短理由与 `high`/`medium` 置信度传给 resolver。不得按歌手或人物性别机械决定配音性别；只有作品信息不足、模型不可用或判断置信度为 `low` 时，resolver 才从同一十声线池随机一次。选择结果、完整候选池、理由和置信度必须写入 selection，后续不得逐段重选。若解析结果不是预检声线 CV002，再运行 `python3 tools/tts/doctor.py --voice <resolved_id>` 精确检查本期母带；日常 doctor 不因未使用角色或纯中文不需要的 mixed-script 策略阻断。
4. 复用脚本在 `tools/`（配音 `tools/tts/`、竖屏 `tools/video/vfill.sh`、音轨+合成模板 `tools/video/countdown_build.py`）——不要重造。新项目旁白必须把同一个 `voice-selection.json` 传给中央入口 `tools/tts/narrate.py`；不得直接 `KPipeline(...)`、不得在项目里硬编码 `VOICE`。旁白生成完运行 `python3 tools/tts/verify_voice_usage.py --selection sandbox/<slug>/voice-selection.json --project-root sandbox/<slug>`，必须得到 `VOICE GATE: PASS`。
5. **根目录 `all_cookies.txt` 是仅用户维护的 canonical 输入**：canonical 不要求不可变锁，代理禁止覆盖完全由本文件与 `CONVENTIONS.md` 的提示词约束。代理仅可通过 `check_yt_cookie.py`、`yt_dlp_readonly.py`、`bili_search.py` 或 `bili_dl.py` 的既定只读路径消费它，禁止对文件或其路径直接执行写入、`chmod`、`touch`、`mv`、`cp` 或过滤替换，也不得借自动修复、测试或普通 goal 覆盖它。`yt-dlp --cookies FILE` 在退出时会回写 FILE，因此凡需 Cookie 的 yt-dlp 搜索、校验或下载，一律运行 `python3 tools/video/yt_dlp_readonly.py -- <yt-dlp 参数>`；不得裸传 `--cookies all_cookies.txt`，wrapper 只在仓库外私有临时目录创建工作副本。`filter_cookie_jar.py` 只生成仓库外 candidate，用户自行安装为 canonical；代理不得安装。Cookie 缺失、静态检查异常或服务端失效时先继续公开下载和双平台备选，不得因此暂停普通 goal。旧 `www.*_cookies.txt` 不再作为新任务入口；Cookie 不得复制到 `sandbox/`，不得输出 Cookie 值、header 或原始 info JSON。
6. 盘点、叙事和自由探索项目在正式 build 前填写项目级 `project-manifest.json`；新项目固定使用 schema v2，schema v1 只保留给历史工程复现。运行 `python3 tools/video/verify_project.py --project sandbox/<slug>`，必须得到 `PROJECT CONTRACT: PASS`；不能先出产物再补来源、旁白或展示证据。
7. **关键铁律**：① HyperFrames raw render 与用预混 `master.wav` 后期 mux 的最终 MP4 都必须写入项目 `renders/`；最终交付文件固定为 `renders/<slug>.mp4`，不得写入 `final/`、`output/`、项目根或其他目录；② 对具有标准 `project-manifest.json` 的盘点、叙事与自由探索项目，build、render 和 post-mux 完成后，按本期真实主题、歌手与选题角度写 `publishing/xiaohongshu.md`，运行 `python3 tools/video/verify_publishing.py --project sandbox/<slug>`，必须得到 `PUBLISHING COPY: PASS` 后才进入 FINAL；发布文案不属于 build 前 `project-manifest.json` 门禁；③ 对有 intro / song / outro / CTA timeline 与完整旁白的**标准结构化盘点/叙事项目**，mux 后必须运行中央 `tools/video/prepare_final_qa.py`：它从当前 timeline、authoring manifest、final、render 与 master 生成 `qa/final-video-qa.json`、实时 ASR、抽帧及诊断证据，并在同一进程内完成本地机械 FINAL；不得跳过 preparer 手写一份看似可过的 manifest，只有该命令输出 `FINAL VIDEO QA: PASS` 才算机械验收完成。`tools/video/verify_final_video.py` 保留给独立复核或故障诊断，默认流程不得在 preparer PASS 后立刻再跑一遍重复 ASR/解码；④ `project_kind: free_exploration` 不得冒充 preparer 已支持的 structured timeline，按其当期 project/final schema 准备 QA；AI 音色 MV 继续走 durable builder 与独立 `--check`，不得为套用标准 PUBLISHING/FINAL schema 伪造 `project-manifest.json`；⑤ 解码、媒体结构、当前 hash、音轨一致性、固定 ASR 工具链、响度/true peak 与 `>1.5s` 静音等机械红线在本地和发布模式都不能放松；⑥ 代理仍要抽帧实际查看并做 FFmpeg 音量/静音分析，但不得把代理判断、自动生成记录或 pending 模板伪装成 `reviewer_kind: human`；⑦ 只有用户明确要求“公开发布 / 发布验收 / 可发布交付”时，才由真人完成 preparer 生成的当前 SHA 模板，使用 `prepare_final_qa.py --human-review-input <项目相对路径> --require-human-review` 合并批准并完成严格终验；普通 sandbox 制作中的 pending 状态只保存在 QA 文件，不作为默认交付话术；⑧ 成片里不得出现水印/网址/提示词/路径；⑨ **禁止自定义旁白字幕**（不要把 TTS 口播再叠成底部字幕条；用户未显式要求就一律不加，详见 `CONVENTIONS.md`「禁止自定义旁白字幕」）。
8. **goal / 视频制作默认一次交付整片**：用户用 goal 或直接 brief 要求“制作 / 完成一期视频”时，默认终止条件是拿到 `renders/<slug>.mp4` 与 `publishing/xiaohongshu.md`；具有标准 manifest 的项目还必须通过 VOICE / PROJECT / PUBLISHING / 本地机械 FINAL 四道门禁并完成当期 QA，AI durable 等专用流程则完成其明确列出的独立检查；不得因为是新风格就只做开场或首个揭晓段后暂停等待确认，也不得因为真人终验尚未进行就暂停或把 goal 标记为 `blocked`。只有用户明确要求“小样 / 预览 / 先看风格”时才可把样片设为阶段性交付；只有显式发布任务才把 `--require-human-review` 的真人批准作为终止条件。内部进度更新不得中断继续制作。

## Goal 自恢复协议（硬约束）

内部步骤首次失败只停止当前步骤，不停止整个 goal。核心循环是“**诊断 → 修复 → 重跑**”：保存错误、当前输入与 hash，分类根因；在不改变 brief、不伪造 evidence、不绕过 gate 的前提下修复上游输入/配置/产物，或使用本仓库已经记录的安全替代路径；随后从最近失败步骤继续，并重跑所有受影响下游门禁。不得因可自行修复的内部失败暂停、等待用户确认或标记 `blocked`；机械红线不得降级或放松。

- 普通公开下载失败、单个候选不可用、Cookie 静态检查异常但仍有公开/备选源、模型可安装、TTS/ASR/sidecar 异常、render/mux 失败、发布文案结构或歌曲名剧透、manifest/evidence 过期，以及 VOICE / PROJECT / PUBLISHING / FINAL 或展示门禁 FAIL/REVIEW，全部属于内部恢复：依次尝试修环境、换客户端、换双平台同版本备选源、换安全窗口、修正文案、重建产物/证据并复跑。展示 `REVIEW` 必须严格按 **multi → 换窗 → 换源** 恢复；只有该顺序确已穷尽且硬 `FAIL=0` 时，普通本地 goal 才可显式写入绑定当前 clip/window/analysis hash 的 `status=observed, reviewer_kind=agent` 工具辅助观察，计为 `OBSERVED` 且仅本地有效，不得称为真人 `APPROVED`。发布模式 `--require-human-review` 只接受 `status=approved, reviewer_kind=human`；代理不得代签 human。硬 `FAIL` 只能修，不能被任何观察/批准覆盖。
- 只有以下窄边界允许暂停并请求用户：用户明确要求小样或阶段确认；缺少用户独占的必需输入（如用户指定但未提供的 AI WAV）；已穷尽安全替代、公开双平台来源、备用 client 与安全重试后，仍确实需要模型无法取得的新凭据、权限或外部能力；继续必须实质改变歌单、排名、歌手版本、平台排除、硬时长等核心 brief；或显式发布任务缺少真人终验。即便如此，也要先保留可恢复现场并汇报已经尝试的路径，不能把一次命令失败包装成用户 blocker；首次出现真实外部边界时只请求所需输入/权限，不得立即把 goal 标为 `blocked`，只有同一外部阻断连续三次 goal turn 均存在且无法继续时才可标记。

## 多 Goal 并发资源协议（硬约束）

多个 goal 必须持续并发推进；禁止为了“保护机器”新增跨 goal 的 `flock`、全局 semaphore、任务队列、sleep 轮询或“等另一个任务完成再开始”的调度。标准重任务统一走 `tools/video/resource_budget.py` 的**启动时自适应预算**：进程先发布不含项目内容的 PID/启动身份标记并立即计数，当前第 1 个重任务使用 4 线程/worker，第 2 个使用 3，达到 3 个及以上时新任务使用 2（`4 → 3 → 2`）；已经运行的任务不暂停、不动态改速。Whisper/Torch/BLAS、重 FFmpeg 和 HyperFrames render 都必须继承该预算；显式 `CC_MEDIA_ASR_THREADS=1..4`、`CC_MEDIA_FFMPEG_THREADS=1..4`、`CC_MEDIA_HYPERFRAMES_WORKERS=1..4` 或 HyperFrames 唯一的 `--workers 1..4` 优先，但任务仍登记为 active 供其他 goal 计数。禁止 `auto` 和 1–4 外的值。

活跃标记只用于计数，不是调度锁：不得在注册表上等待或轮询。正常/异常退出、PID 复用或崩溃残留由后续任务按操作系统 PID + 进程启动时间清理；注册表不可用时当前任务立即回退 2 线程继续，不能因此阻断 goal。FFmpeg 走中央 wrapper，HyperFrames 从项目目录使用 `python3 ../../tools/video/resource_budget.py hyperframes -- <固定版本 render 命令>`，不得绕开 wrapper 手写 `auto`。

视频任务禁止直接运行裸 `whisper` / `whisper-cli`；统一走 `tools/video/vocal_segments.py`、`tools/video/offline_asr.py` 或调用它们的中央 QA，从而继承同一资源预算。Qwen/MLX 必须先经过 stdlib-only Metal preflight；受限执行上下文只让当前 TTS 命令快速、干净失败并由 goal 自恢复到具备 Metal 权限的执行上下文，不能先 import MLX 触发原生崩溃，也不能用等待锁串行化多个配音任务。

## 新盘点内容硬约束

- **翻唱版本必须匹配画面版本**：盘点对象若是某位歌手/组合的翻唱，YouTube 与 B站都优先找该翻唱者对应版本的 MV、现场或正式演出视频，不得直接拿原唱歌手画面冒充。只有两边都没有可用对应版本，才可退回原版视频，并在 `SOURCES.md` 记录搜索证据与替代理由。
- **官方 MV 优先于清晰度**：先保证歌手/版本身份正确；同一目标版本只要存在可用官方 MV，就优先选官方 MV，即使分辨率、码率或年代画质稍差。只有官方 MV 确实不存在、无法取得或目标段结构性不可用时，才退到官方 Live / 综艺 / 二次来源，并在 `SOURCES.md` 说明。低清本身不是放弃官方源的理由。
- **TOP 一律倒数揭晓并保留悬念**：凡标题、brief 或结构属于 TOP / 排名 / 榜单，播放顺序必须从最后一名到第一名（N→1）。这个顺序只属于内部编排规则，成片和封面不得出现 `05→01`、`05->01`、`N→1`、`倒数开始`、`从第5名开始` 等解释视频机制的 meta 文案；逐首揭晓时的单个名次数字、`第X名` 口播和当前 `RANK 05` 等名次标识仍可使用。封面和 intro 可说明主题与数量，但不得提前列完整歌单、展示排序或泄露第一名；**只在封面**，若主标题已经用“最难 / 最燃 / 最被低估”等“最……”中文极值描述表达榜单语义，就省略独立的 `TOP` / `TOP N` 标签，不再用“榜单 / 排名”等同义角标补回；需要数量时可自然写成“5首”等中文标题组成部分。intro、逐首转场、口播、项目标题、timeline、发布文案与其他位置不受这条封面去重规则新增限制。每一名只在对应歌曲转场时揭晓。非排名主题片不得伪装成 TOP。
- **开头口播禁用“接下来”**：intro 第一段不得出现“接下来”。默认 Qwen 支持多语种，不预先删除非中文；外文歌名/人名先实测发音，只有读得不自然或不可懂时，才改用通行中文译名、音译/谐音或从口播省略（画面文字仍可保留原文）。
- **英文单词优先按词发音，纯中文零改写**：口播里的连续全大写明显单词先归一为正常词形（`BEYOND → Beyond`）；只有明确的首字母缩写或非词字母串才逐字母读。自动规则只处理 ASCII 拉丁 token，纯中文文本、中文标点和原有措辞必须原样透传。
- **旁白结构完整、篇幅两头重**：一般视频默认在开头、每首歌曲转场、作品结尾与固定 CTA 都安排配音；没有明确要求不等于可以省略，但结构完整不等于逐段平均展开。`intro` 集中建立主题、评判标准与钩子且不泄榜，作品 `outro` 集中做整体结论；逐首转场只承担首次揭晓与一个不可替代的判断，不得堆叠履历、多个数据点、社区评价和重复形容。新项目的 `project-manifest.json` 使用 schema v2：TOP 转场实际 WAV 目标 4–6 秒、硬上限 8 秒；非排名叙事转场目标 6–8 秒、硬上限 10 秒。超限必须先删减文案，不能靠延长歌曲展示免责；full-music 展示开始后不得继续配音。只有完全自由探索类、以音乐/视觉实验本身为主体且不承担排名或解说结构的视频，才可在 brief/design 明确记录后按创意需要精简部分或全部旁白。
- **质量优先、总时长默认不设上限**：除非用户明确给出平台硬时长，不能为了压缩总时长牺牲内容、节奏或完整乐句。某首的完整副歌/演唱段需要更长就保留更长；若确有硬时长，应优先减少条目或精简旁白，不得掐断唱句、尾音或高光段。
- **封面排版与安全区同时过关**：标题必须按语义短语和视觉层级选择自然换行，禁止机械等字数拆行、留下孤字或让重点词断裂。单歌手 / 单组合主题封面中，歌手 / 组合名必须是第一视觉主体和全封面唯一最大字号，严格大于主题口号、歌名、`TOP N`、类型标签与副标；名字与主题同大也不合格。标题、排名、主题等关键信息不得拆到画面最顶端和最底端，也不得整块死居中遮住人物/主体；应放在一个中上或侧向安全信息区，并通过首帧抽帧检查排版美感、主体避让和发布裁剪后的完整可读性。完整例外与 QA 口径见 `CONVENTIONS.md`「首屏封面」。
- **小红书发布文案默认随片交付**：固定写入 `publishing/xiaohongshu.md`。标题候选允许 1–5 个、默认给 3 个，第一条是首选；正文必须可直接发布，最后一行必须是 hashtags。标题、正文、互动句和 hashtags 的全部对外文字都不得出现本期任何歌曲名称，以免剧透；内容必须强关联真实主题、歌手与选题角度，不得泛化套模板或杜撰作品事实。

## AI 克隆歌手音色 MV durable 模板协议

当 brief 明确是“AI 克隆/训练歌手音色制作 MV”“如果某歌手唱某歌”，且用户提供了可直接使用的训练音频 WAV 时，新建当期 `sandbox/<slug>/`，并复用 `tools/video/templates/ai-voice-mv/`；历史 `sandbox/angela-ai-mv-covers/` 已删除，不得恢复或继续依赖。先读 `tools/video/templates/README.md`，再按 `CONVENTIONS.md` 的“格式之三：AI 克隆歌手音色 MV（整首 MV 换训练音轨）”执行。

固定做法：
- 只把用户明确给出的训练 WAV 复制到当期项目 `audio/`，填写项目 `build/config.json`；用中央 durable builder 一首输出一个位于 `renders/` 内的独立 MP4，不在 `sandbox/` 留唯一脚本副本。
- 仍然必须双平台查源（YouTube + B站），记录候选和取舍到 `SOURCES.md`。
- intro 必须复用当期 `voice-selection.json` 调用 `tools/tts/narrate.py`；唯一有效指定按指定，否则按十声线标准池的作品情绪决策规则选择，只有模型无法可靠判断时才随机兜底。歌曲音频在 intro 期间 duck，随后恢复。
- 全程叠加 `AI训练，仅供娱乐`，并通过抽帧确认无平台/UP 主水印、无网址、无路径、无提示词泄漏。
- 遇到 B站 4K 修复源带底部水印/烧词，优先尝试全宽横带 crop 保主体；crop 不成立再退回更干净源。不要交付带平台/UP 主水印的成片。
- `silencedetect` 报静音时，对照训练 WAV。若静音来自用户给的 e200/训练源，为保证整首 MV 对齐可保留，并在结果里说明。
- AI 音色 MV 不使用标准 HyperFrames post-mux 的 `verify_project.py` / `verify_final_video.py` schema；继续走 durable builder 与其独立 `--check`。两条流程的 PASS 不得互相冒充。

## 配音

新启动的自媒体视频统一用 `tools/tts/` 编号声音库。任务提示词若唯一精确指定已注册的编号、正式名称或别名，则使用指定角色；未指定、未知、模糊或冲突时，代理根据作品主题、整体情绪、叙事角度与节奏，从 `CV012 / CV013 / CV014 / CV015 / CV016 / CV002 / CV003 / CV008 / CV009 / CV017` 十声线标准池做一次模型决策，记录简短理由及 `high`/`medium` 置信度。只有模型无法可靠决策时才从同一池随机一次，不做名称相似度猜测，也不按内容主体性别机械匹配配音性别。选择落盘后，同一期 intro、全部排名或叙事转场、作品 outro 与固定 CTA 必须共享同一 resolved voice ID，并通过 `verify_voice_usage.py` 校验。Qwen 运行环境、模型或参考母带缺失时必须 fail closed 当前生成步骤，然后自动修复固定环境并重跑，**不得静默降级 Kokoro，也不得因此停止整个 goal**。Kokoro 只保留给显式 legacy ID 与历史工程复现。Qwen 的外文策略只处理 ASCII 拉丁 token；未提供显式覆盖时，纯中文文本、中文标点、数字、seed、请求结构和既有缓存 fingerprint 必须保持原样。不要用 HyperFrames 内置 TTS 做中文。receipt、sidecar 和哈希只证明当前本地工作流的一致性，不证明音色来源，也不抵抗同一用户权限下的主动篡改。正式池新增或更换母带时，必须确保该声音绑定的 `reference_text` 与母带逐字匹配，并让当前十声线分别通过生产 `narrate.py` 生成、sidecar/VOICE gate、可解码/响度/静音/削波检查；任何生成达到 `max_tokens`、出现异常长音或疑似杂音都必须 fail closed，不能进入标准池。详见 `CONVENTIONS.md` 配音规范和 `tools/tts/README.md`。

## Sandbox 成片交付收尾（硬约束）

所有新 Sandbox 项目的 raw render 与 mux 后最终 MP4 都直接写入 `sandbox/<slug>/renders/`，最终成片固定为 `renders/<slug>.mp4`；不得另建 `final/`、`output/`，也不得把终片放在项目根或其他目录。与 `renders/` 并列创建 `publishing/`，默认交付 `publishing/xiaohongshu.md`。最终回复同时报告这两个文件、最终 MP4 当前 SHA、VOICE / PROJECT / PUBLISHING / FINAL 结果、实际修复和确实影响成片的问题；发布文案是必需内容产物，不属于被禁止的“未来发布建议”。仍不得自动附加用途定位、权利或条款免责声明、额外真人复核建议等套话；QA 报告、`SOURCES.md`、README、checklist、manifest 生成器和 CLI 默认输出同样不得生成这类套话。只有用户在当期任务中主动询问相应主题时才回答，且不得把它写成固定结尾或成片完成条件。

## How the two tools fit together

`yt-dlp` produces raw source material (full videos, clipped sections, audio, subtitles). HyperFrames does *not* re-encode arbitrary footage well — it is a browser-based renderer (headless Chrome screenshots stitched by FFmpeg), best at motion graphics, animated text/captions, overlays, and slide-style segments. So the natural split is:

- Use `yt-dlp` + FFmpeg for the actual video footage clips.
- Use HyperFrames for the "produced" layer: hooks, captions, lower-thirds, transitions, branded intro/outro, and composing footage clips onto an HTML timeline (footage referenced as `<video>`/image assets inside a composition).

Both ultimately shell out to **FFmpeg**, which is a hard dependency for the whole pipeline.

## Prerequisites

- **Node.js >= 22** (HyperFrames)
- **FFmpeg** (rendering for both tools) — `brew install ffmpeg`
- **yt-dlp** — `brew install yt-dlp` (or `pipx install yt-dlp`)
- Optional: **Git LFS** if cloning the HyperFrames repo with test baselines

## yt-dlp — common commands

```bash
# Download best mp4 video+audio
python3 tools/video/yt_dlp_readonly.py -- \
  -f "bv*+ba/b" -o "%(title)s.%(ext)s" "<URL>"

# Clip a section without downloading the whole file (00:01:23 - 00:02:05)
python3 tools/video/yt_dlp_readonly.py -- \
  --download-sections "*00:01:23-00:02:05" -f "bv*+ba/b" "<URL>"

# Pull subtitles / auto-captions (useful as a source for HyperFrames captions)
python3 tools/video/yt_dlp_readonly.py -- \
  --write-auto-subs --sub-langs "en,zh-Hans" --skip-download "<URL>"

# Audio-only extraction
python3 tools/video/yt_dlp_readonly.py -- -x --audio-format mp3 "<URL>"
```

## HyperFrames — setup and dev loop

HyperFrames renders HTML compositions to video. Compositions are plain HTML files with `data-*` attributes (no React/DSL). Animations are driven by GSAP (or anime.js, Lottie, Three.js, WAAPI, CSS).

新项目固定使用 **`hyperframes@0.6.69`**；已有项目遵循自身 `package.json` 中的精确 pin，不为套用新默认而升级。禁止裸 `npx hyperframes`、`hyperframes@latest` 或未评估的自动升级；升级必须作为独立兼容性任务重新走 lint、render、mux 与终片 QA。渲染所需字体必须离线可用：新项目默认使用项目内合法授权的 WOFF2；系统 `local()` 只允许明确锁定本机/OS、且不要求跨机复现的历史或本机专用工程。不得依赖 Google Fonts 等渲染时网络请求。

```bash
# Scaffold a project (non-interactive form preferred for agent use)
npx --yes hyperframes@0.6.69 init <name> --non-interactive --example blank

# Install agent skills — registers /hyperframes slash commands in Codex
npx skills add heygen-com/hyperframes

# Dev loop
npx --yes hyperframes@0.6.69 preview
python3 ../../tools/video/resource_budget.py hyperframes -- \
  npx --yes hyperframes@0.6.69 render --output renders/output.mp4 --sdr
npx --yes hyperframes@0.6.69 lint
npx --yes hyperframes@0.6.69 inspect
npx --yes hyperframes@0.6.69 doctor
```

### Composition anatomy

A composition needs three things wired together:

1. Root element carrying metadata: `data-composition-id`, `data-start`, `data-width`, `data-height`.
2. Timed clips marked `class="clip"` with `data-start`, `data-duration`, `data-track-index`.
3. A paused GSAP timeline registered on `window.__timelines["<composition-id>"]` — HyperFrames drives this timeline frame-by-frame during render. The goal is frame-level reproducibility under the same pinned toolchain, browser, fonts and inputs; do not claim byte-identical MP4 output across environments.

### Use the installed skills

Once `npx skills add heygen-com/hyperframes` is run, prefer these slash commands over hand-writing composition boilerplate — they encode the correct `class="clip"` / timeline-registration patterns:

- `/hyperframes` — composition authoring patterns
- `/hyperframes-cli` — dev-loop command guidance
- `/hyperframes-media` — asset preprocessing (TTS, transcription, background removal)
- `/gsap`, `/tailwind`, and adapter skills `/animejs` `/css-animations` `/lottie` `/three` `/waapi`

## References

- HyperFrames repo: https://github.com/heygen-com/hyperframes
- HyperFrames docs/quickstart: https://hyperframes.mintlify.app/quickstart
- yt-dlp: https://github.com/yt-dlp/yt-dlp
