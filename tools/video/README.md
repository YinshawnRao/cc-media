# tools/video — 自媒体视频制作 Runbook（冷启动可执行）

新窗口接到一段视频 brief，按本文件从头跑。配套脚本：
- `vfill.sh` — 片段 → 竖屏 1080×1920（模糊填充 + 裁台标）。
- `narrate_segments.py` — 中央 TTS batch 调用模板（只改 BLOCKS 文案；配音读取项目级 `voice-selection.json`，禁止手改 `VOICE` 或直接调用 Kokoro）。
- `countdown_build.py` — **TOP 盘点模板**。解说盘点默认从每首 25s 起步，并用 `SHOWS` 逐曲落到完整乐句；固定时长不是硬切上限。
- `vocal_segments.py` — **多证据主唱候选检测**。旧 HPSS + 频带能量只保留为候选；默认再用本机 Whisper small 的有效歌词密度/word timestamps、字幕幻觉过滤和 stereo mid/side 区分“中心主唱”与“观众/合唱/宽混音待复核”。输出兼容旧 `vocal_segments`，并新增 `lead_segments`、`safe_cut_intervals`、`segment_scores`、`evidence_level`。**盘点类和多版本接力都必须先产出 `probe/vocal_analysis.json`。**
- `showcase_align.py` — **展示段对齐闸门（机械化强制）**。校验：① 主唱身份证据与副歌入点；② 展示覆盖；③ 结尾不落在 word/唱声中；④ 候选出点后 3s 内若有下一咬字就继续向后吞完整句。状态为 `OK / APPROVED / REVIEW / FAIL / MISS`；只有 `OK/APPROVED` 可继续 build。旧能量结果、观众/合唱风险和缺模型都变成阻断式 `REVIEW`，不再假绿。
- `verify_project.py` — **项目结构与素材证据门禁**。读取项目 `project-manifest.json`，机械检查 TOP N→1/不剧透、完整旁白顺序与固定 CTA、同一期配音 sidecar、逐曲 vocal/instrumental 实证、YouTube+B站搜索和翻唱/官方源取舍。Schema 见 `project-manifest.schema.json`；`examples/project-contract/` 是不含媒体/模型输出的字段模板，不冒充可执行 PASS 工程。
- **长篇叙事盘点 / 音乐时间线**：复用 `templates/longform-timeline/` 的无媒体构建骨架，将已验证的章节画面输出端预切后拼成单一 `footage_track.mp4`，将当期预混章节音频拼成 `master.wav`；封面和 HTML 仍按当期 design 创建，render 必加 `--sdr`。历史 `sandbox/lirh-yangcl-timeline/` 已删除，不得依赖。详见 `templates/README.md` 与 CONVENTIONS「长篇叙事盘点」。
- **整首 AI 音色 MV**：复用 `templates/ai-voice-mv/`；历史 `sandbox/angela-ai-mv-covers/` 已删除。模板只读项目内已复制素材，不含媒体、Cookie、歌单或人物绑定配置。

> 配音引擎、音色策略见 `../tts/`；全局规范见仓库根 `CONVENTIONS.md`。

## 0. 启动自检
- 确认在 `cc-media/` 仓库内；读根 `CLAUDE.md` 和 `CONVENTIONS.md`。
- 依赖：`ffmpeg`、`yt-dlp`、`node>=22`。旁白默认还要求 `tools/tts/` 能找到 Qwen/MLX interpreter、固定 Base 模型与 CV002 参考母带；缺失必须硬失败，不能静默换 Kokoro。多证据检测与终片 ASR 要求 `tools/tts/venv` 内的 `openai-whisper==20250625`，以及已显式预取且完整 SHA-256 为 `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794` 的 `~/.cache/whisper/small.pt`；只同名或只存在不算通过。
- 开工前运行 `python3 tools/tts/doctor.py`，必须 `TTS DOCTOR: PASS default=CV002`；初始化机器或模型变化后运行一次 `--full-model-hash`。
- 新项目 Cookie 唯一入口是仓库根目录 `all_cookies.txt`：原始全量导出必须留在仓库外并为 `0600`；运行 `python3 tools/video/filter_cookie_jar.py /仓库外/原始导出.txt`，脚本只保留 YouTube / Google / B站域并以 `0600` 原子写入。旧 `www.*_cookies.txt` 仅作回退；不得在 `sandbox/` 复制 Cookie。`check_yt_cookie.py` 只做字段、文件内 expiry、目标域 allowlist 和权限的静态预检，不能证明服务端会话仍有效。
- 所有产物写 `sandbox/<项目slug>/`（可丢弃）；正式留存才进 `production/`。

### 0.1 项目 manifest 门禁

盘点、非排名叙事和完全自由探索项目在正式 build 前填写项目根 `project-manifest.json`，再运行：

```bash
python3 tools/video/verify_project.py --project sandbox/<slug>

# 仓库自带的是无媒体字段模板，直接运行应 FAIL，不是正式正例
python3 tools/video/verify_project.py \
  --project tools/video/examples/project-contract

# 可执行正例由测试在临时目录水合，不写入仓库
python3 -m unittest tools.video.tests.test_verify_project -v
```

`project_kind` 只接受 `top_ranking`、`narrative`、`free_exploration`。自由探索必须写非空 `rationale` 且 item 不得带 `rank`；这只是明确例外，不是绕过素材证据的开关。Vocal 项会从 hash 绑定的 analysis/window 实时调用 `showcase_align` 重算，REVIEW 仅在当前 clip/window/analysis 绑定的逐曲批准（reviewer、带时区日期、hash evidence）有效时才成为 APPROVED；纯音乐项必须提供 hash 绑定的连续性、真实 clip 时长和起止边界人工复核证据。clip 与 raw source 都必须是 ffprobe 可解码的真实音视频，窗口不得超过实测时长。

每个选中来源必须有 `selection.download_receipt`，且 receipt 只允许脱敏的 `schema_version/kind/platform/url/downloaded_at/raw_asset/raw_duration_sec/derivation`：其中 raw asset、raw→clip 输入输出、时窗和时长都与当前 SHA 闭环。严禁把 yt-dlp 原始 `info_json`、Cookie、HTTP headers 放进项目。这个 receipt 只证明**当前本地文件与所声明 URL/派生链一致**；门禁不联网，不能证明平台页面仍存在、账号状态、上传者身份或“官方”声明真实，候选身份与取舍仍须人工审阅。

配音由项目 `voice-selection.json` 和中央 `tools/tts/verify_voice_usage.py` 统一校验：manifest 每条旁白原文必须精确匹配 sidecar canonical input（有 `source_text` 时优先，否则为 `text`），sidecar 输出必须正好指向该条 manifest WAV，且 WAV 为可读的 24kHz mono、当前 SHA。默认 Qwen sidecar 还必须带可迁移的 registry/config/model/reference portable claim，并与本机 `python3 tools/tts/doctor.py --full-model-hash` 生成的当前 receipt 一致；缺 receipt 或旧 Qwen 绝对路径 sidecar 会 fail closed，不提供项目级绕过。用户精确指定的 Kokoro legacy voice 仍由中央 selection 规则显式识别。正式 PASS 必须使用真实 `narrate.py` 输出，不能复用测试注入的合成声明。

共享 `countdown_build.py` 会在读取旁白、运行展示 gate、写 `master.wav/index.html` 之前自动执行本门禁；其他 build 入口也必须先得到 `PROJECT CONTRACT: PASS`，不能先生成产物再补 evidence。

该门禁当前只覆盖上述三类盘点/叙事/自由探索项目，且检查的是**构建前结构和 provenance**，不能证明终片实际可听、可见或已正确 mux，后续第 9 节 QA 仍必须完整执行。AI 克隆歌手音色 MV 不冒充本 schema，继续走 `templates/ai-voice-mv/` durable builder 与对应 `--check`。

## 1. 解析 brief
提取：标题、画幅（默认竖屏 1080×1920）、是否为 TOP/排名、每首真实名次映射、歌手/歌名/URL或搜索倾向/切点、旁白、配音音色、平台硬时长。**配音只解析一次**：把用户原始任务提示词交给 `tools/tts/resolve_voice.py` 并保存项目根 `voice-selection.json`；唯一精确匹配按指定，未写/未知/模糊/冲突一律 `CV002「治愈少女」`。凡 TOP / 排名 / 榜单，保留用户给定名次映射并按最后一名到第一名 **N→1** 播放；非排名叙事片才按脚本顺序，且不得挂 TOP 名义。默认不设总时长上限，质量优先。

```bash
python3 tools/tts/resolve_voice.py --task-prompt-file <原始brief文件> \
  -o sandbox/<slug>/voice-selection.json
```

## 2. 样片先行（首个新风格时）
先做 **开场钩子 + 首个揭晓段** 一条样片（TOP 即最后一名，如第 05 名），渲染给用户审风格/节奏/配音，确认后再批量。重复同风格的 brief 可跳过直接全片。

## 3. 素材（yt-dlp）
- **顺序执行**，不并行。先 `--skip-download --print` 验证 cookie + 可用性 + 时长 + 清晰度。
- **翻唱版本身份先于画质**：若盘点的是某歌手/组合的翻唱，YouTube 与 B站都先找该翻唱者对应 MV/现场/正式演出，禁止直接拿原唱歌手画面。两边都没有可用对应版本时才退回原版视频，并在 `SOURCES.md` 记录搜索证据和替代理由。
- **身份正确后官方 MV 优先**：目标歌手/版本有可用官方 MV 时，即使年代久、4:3 或清晰度稍差也优先使用；第三方 4K 修复、综艺 Live 或二剪不能仅凭分辨率胜出。只有官方 MV 不存在、无法取得或目标段结构性不可用时才换源，并在 `SOURCES.md` 写明证据。
- 切片：`--download-sections "*HH:MM:SS-HH:MM:SS"`，`-f "bv*[height<=1080]+ba/b"`（**不要强制 avc**，否则老 MV 只给 480p；HD 才拿得到真 1080p）。
- **每段抽帧自检**（`ffmpeg -ss N -i raw -frames:v 1 f.png` 后用 Read 看）：确认是真动态 MV 画面、记下水印/烧死字幕/画幅，据此定 `vfill.sh` 的 crop。老歌多为标清 4:3、带水印，属源限制。

## 4. 竖屏化（⚠️ 硬规则见 CONVENTIONS「展示段硬规则 (A)」）
`bash tools/video/vfill.sh <raw> clips/vert_<song>.mp4 <crop>`。
- **默认 letterbox 保原比例、不放大画面**：crop 传**全宽横带**（`源宽 : 裁掉烧词后的高 : 0 : Y`），全宽呈现、上下模糊填充。**双人/合唱/多人/宽机位一律 letterbox**，否则主体被裁半。
- **只有单主体全程居中**才可传窄竖条做"裁切放大贴宽"。拿不准就 letterbox。
- 抽帧确认：人物完整不被裁、无烧词/水印残留。
- **竖屏化后立即跑多证据主唱检测**（供第 6 步对齐闸门）：
  `tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json --mode multi --language zh`。
  - `--mode multi` 缺模型即退出；不得在正式 build 静默退回旧能量法。
  - 日/英歌曲按实际语言改 `--language`，不确定可省略让 Whisper 自动识别。
  - Live / 演唱会 / 观众明显的素材必须加 `--source-kind live`；在 crowd/choir 事件模型尚未接入前，即使识别出完整歌词也只会 REVIEW，不会把观众合唱自动当目标主唱。
  - `classification=no_lexical_singing_detected` 表示器乐/观众窗没有有效歌词证据；`singing_or_group_review` 表示可能是观众、合唱、对唱或宽混音，必须人工复核。

## 5. 旁白
只改 `narrate_segments.py` 的 `BLOCKS`，不得新增 `VOICE` 常量、不得 `from kokoro import KPipeline`。一般视频必须具备完整骨架：`intro` 负责主题钩子但不泄榜；每首歌曲都有独立转场旁白，并在此首次公布该名次与歌名；`outro` 只做主题收束；固定 CTA 是最后一句。只有 brief/design 从启动阶段就明确标注的**完全自由探索类**音乐/视觉实验，才可按已记录的创意方案精简部分或全部旁白，不能由执行者临时猜测。通过中央入口一次加载模型并复用项目级选择：

```bash
python3 tools/tts/narrate.py --batch narration-request.json \
  --selection-file voice-selection.json
```

每条 WAV 都必须有 `.wav.tts.json` sidecar；本期所有旁白必须是同一个 resolved voice ID。新盘点不要使用 legacy `--female`。**intro 第一段禁止出现“接下来”**。Qwen 支持多语种；明显英文单词优先按词发音，连续全大写词先转正常词形（`BEYOND → Beyond`），明确的首字母缩写或非词字母串才逐字母读。自动归一化只作用于送入 TTS 的 ASCII 拉丁 token，画面可继续使用官方写法 `BEYOND`，纯中文文本和中文标点必须原样透传。读音不确定时先生成短样音或写项目级 `pronunciation_overrides`，不要先改成生硬中文谐音。Qwen 不需要 Kokoro 垫话，禁止把旧模板垫话机械复制过来。

## 6. 音频 + 7. 合成
改 `countdown_build.py` 顶部 `songs`（key/clip/序号/歌名/标签）、各时长常量、`MGAIN`（暗调安静歌补偿），运行：建 master.wav（逐段 床→swell→展示，逐首 `loudnorm=I=-14` 统一响度）+ 生成 `index.html`。
- **展示段时长（硬规则 (B)）**：每首给**一段连续副歌**含前后余量，**不碎镜快闪、不因旁白长或总片时长就把歌切短**。解说盘点类单首 **≥~25s**，不设上限；某首完整演唱高光需要 35s、45s 或更长就保留，不得强切唱句/尾音。footage 窗 == 音乐窗（同源同窗）→ 口型同步。clip 切到 `SHOW+余量`，`data-duration=SHOW`。
- **整片时长（硬规则）**：没有用户明确的平台硬时长，就不设置总时长上限；整体质量、叙事完整和音乐观赏性优先。确有硬时长时优先减少条目、删除重复信息或精简旁白，不能用压缩歌曲高光补预算。
- **🔒 展示段对齐闸门（硬规则 (C)，build 内置，违规不出 master）**：build 算完时间轴会自动跑 `showcase_align.gate()`。`FAIL` 必须修 `ch_off/show`，不能批准跳过；`REVIEW` 必须重跑多证据分析，或逐曲试听后留下绑定 clip、分析摘要和三个时间码的批准记录。全局 `SHOWCASE_OVERRIDE` 已废弃。
  ```bash
  # 只向后找完整乐句出点；推荐值还会再走同一 verify 自检
  tools/tts/venv/bin/python tools/video/showcase_align.py plan \
    --vocals probe/vocal_analysis.json --clip vert_p4_wait --voice-dur 14 --near 105

  # 生成全部 pending 的逐曲批准骨架；人工填 reason/evidence 并改 approved
  tools/tts/venv/bin/python tools/video/showcase_align.py approval-template \
    --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json
  ```
- **🔒 盘点类封面（默认）**：用**第一首出场歌**（TOP = 最先揭晓的最后一名，如 #5）的**动态画面**做封面底，并让 intro footage 与该首 footage 取**同一条素材的连续窗**。TOP 封面只写主题与 `TOP N`，禁止列完整歌单、歌曲排序或泄露第 1 名。标题按语义短语自然换行，不机械等字数拆分、不留孤字；歌手名与同层级主要文字同字号或更大，不能偏小。关键信息集中在约 `x=72–1008 / y=220–1420` 的一个安全信息区，不拆到最顶和最底，也不死居中挡主体；首帧必须做排版与发布裁剪预览。详见 `CONVENTIONS.md「首屏封面」`。
- `npx hyperframes lint` 必须 **0 error**（媒体元素要有 id；相邻 footage 用交替轨道 0/6；同轨不可贴边）。

## 8. 渲染 + MUX（关键）
```bash
npx hyperframes render --output renders/full.mp4 --sdr   # ← --sdr 必加
# HyperFrames 会对音频做响度归一化、压平动态 → 必须用预混 master 覆盖音轨：
ffmpeg -i renders/full.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/<slug>.mp4
```
成片以 mux 后的 `<slug>.mp4` 为准。render、master 和 final 三者都必须保留到终片 gate 完成；不能只凭文件名或“已经跑过 mux”口头判断。

> **`--sdr` 必加原因**：HF 会从任意源 auto-detect HDR。Bili 杜比视界流（如 LIKE A STAR 巡演）会触发整片输出升级为 HLG 10-bit H.265，短视频平台不收。强制 SDR H.264。

## 9. 终片 QA gate（只认 mux 后 MP4）

每期在项目内创建 `qa/final-video-qa.json`，再运行：

```bash
python3 tools/video/verify_final_video.py \
  --project sandbox/<slug> --manifest qa/final-video-qa.json
```

只有 `FINAL VIDEO QA: PASS` 才算终片机械验收完成。工具只调用本地 `ffmpeg` / `ffprobe` 和已安装的 `tools/tts/venv`，用固定 Whisper small checkpoint 实时重跑 ASR；模型加载前会完整读取并校验上述 checkpoint SHA，同时核对 `openai-whisper` distribution 版本。它不联网、不读取 Cookie、不调用 TTS。模型或固定运行环境缺失、被替换或版本漂移时硬失败，不会下载模型。manifest、媒体、ASR 和人工证据都只能使用项目相对路径，并拒绝 `..`、绝对路径，以及项目内部被引用路径组件中的 symlink（仓库/工作区祖先目录不在这条声明范围内）。

manifest `schema_version: 1` 必须完整包含以下内容，不能用空字段或旧报告占位：

- `assets.final / render / master`：各自的项目相对 `path` 与当前文件 `sha256`。final 必须是 mux 后 MP4，render 必须是原始 render MP4，master 必须是 PCM WAV，三条路径互不相同；任一文件变化后旧 manifest 自动失效。
- `authoring_manifest`：当前项目 `project-manifest.json` 的 path+SHA。终片 gate 会在开始与结束分别实时运行 `verify_project.py`；`narration_expectations` 必须逐条绑定其中的 narration ID、原文、角色和当前 WAV SHA，不能在 QA JSON 里另写一套旁白或 CTA。
- `checks.expected_video_codec`：新项目写 `h264`。只有当期明确接受 HEVC 时才写 `hevc`，工具按 manifest 精确校验，不把“任意 H.264/HEVC 都算过”。`duration_tolerance_sec` 默认 0.5 秒且不得超过 1 秒。
- `checks.loudness`：不写时仍强制整片 integrated loudness 位于 **-20 至 -10 LUFS**，true peak 不高于 **-0.1 dBTP**；manifest 只能收窄范围，不能放宽。decoded master 与 final AAC 还会计算波形相似度 SDR，默认最低 **12 dB**（`min_master_aac_sdr_db`，也只能提高）；SDR 是防错 master / 错音轨门禁，不代表听感已经完全一致。
- `chapters`：按时间顺序覆盖整片，每章写 `id / role / start_sec / end_sec / requires_narration`，供静音归属、抽帧覆盖和旁白断言使用。章节覆盖使用固定 0.05 秒帧级容差，不能借较宽的 container tolerance 留出未归属空档。
- `narration_expectations`：每条写 `id / role / chapter_id / expected_text / expected_text_sha256 / authoring_narration_id / authoring_wav_sha256`；可列明带 SHA 的 `acceptable_variants`。`structured` 必须绑定 authoring manifest 的全部 intro、转场、work outro 和 canonical CTA；`free_exploration` 也必须逐条绑定其实际 narration，authoring 中确实没有旁白时才可为空。任何 expected/variant/live observed 文本归一化后为空都失败。
- `asr_evidence.final_aac_asr / isolated_narration_asr`：两类都提供当前 JSON artifact SHA、实际 source path+SHA，并使用固定参数 `openai-whisper / small / zh`（final 另固定 `audio_stream: 0:a:0`）。gate 每次从当前 final AAC 和 authoring narration WAV 实时转录；`live_receipt` 会写入并强校验 checkpoint SHA 与 `openai-whisper` distribution 版本，artifact 必须逐字段等于本次结果。assertion 只引用按时间排序的 live `segment_ids`，每段最多消费一次，observed 文本与时间窗由 gate 推导，不能手填。final 段必须落在对应 chapter；isolated 段必须来自该 expectation 绑定的 WAV。disposition 只能是 `exact`、注册的 `accepted_variant`，或附当前 final SHA 人工记录的 `human_review`。只有旧 transcript/手写“识别结果”不能放行。
- `reviews.visual_frames / leakage / release_safety`：只能是 `reviewer_kind: human` 的人工批准，包含 reviewer、带时区且不在未来的 reviewed_at、当前 final SHA、notes 与有 SHA 的项目内 evidence。visual evidence 的路径和 PTS 必须各自唯一，并且**每个 PTS 一张无损 PNG**；至少包含 `sample_time_sec: 0` 的封面首帧，并覆盖每个 chapter。frame 0 只归首章，其他时间必须严格落在章节内部，内部边界不能同时给两章充数。gate 会从当前 final 抽帧、核对实际返回 PTS，再把当前帧与证据图统一解码为 RGB24 比较像素 SHA。旧 contact sheet、无效图片或一张图自报多个时间都不能放行。gate 仍只验证证据像素与批准没有过期，**不会声称机器已经看懂画面、水印、提示词泄漏、发布裁剪或排版美感**。
- `reviews.silence / black`：机器检测到的 review 区间必须有一一对应、绑定当前 final SHA 的人工 context；旧区间或多余批准都会失败。

`reviewer_kind: human` 是项目内无签名记录：gate 能验证字段、时间、当前 final SHA 与 evidence 新鲜度，不能认证 reviewer 的真实身份。实际流程仍必须由人完成画面/听感复核；本地 JSON 不能冒充外部签名或机器视觉结论。

Whisper checkpoint/版本校验同样属于本机同一 UID 的一致性门禁：它能可靠发现常见的模型替换、缓存损坏和依赖漂移，但不声称抵抗拥有同一用户权限、还能同时篡改校验代码与常量的主动攻击者。

机械 gate 会实际执行：final 全片音视频 decode；final 严格单视频+单 AAC、render 严格单视频、master 严格单 PCM 音轨；final AAC 至少 160 kbps，采样率与声道数必须和 master 相同；MP4、视频 codec、container 时长与各主 stream 覆盖校验（MP4 主流必须显式报告 start，普通 PCM WAV 因 ffprobe 不提供 start 字段而按该格式的无偏移语义取 0；stream 起止固定 0.1 秒容差，不能用较宽的 container 容差掩盖尾部缺帧/缺声）；final 与 render 的 decoded PTS、逐帧 duration 和 RGB frame hash receipt 一致性；master PCM 与 final AAC 统一补齐/修剪到终片长度后的 decoded SDR；`silencedetect`、`blackdetect`；整片 LUFS 与 true peak。结束前会再次校验 QA manifest、authoring contract、媒体、ASR source/artifact、视觉/人工证据等全部已读输入，运行中换文件也失败。视觉证据列出的抽帧时间必须严格落在唯一 chapter 内，章节边界时间不能同时给两章充数。静音规则固定如下：

- 任意 **>1.5 秒**静音都是硬失败，不能靠人为增加 chapter boundary 降级；普通 human review 不能覆盖。
- **1–1.5 秒**静音，或跨 chapter boundary 的检测结果，只进入 REVIEW；有当前 final SHA、精确区间和人工 context 才能放行。
- `blackdetect` 只报告黑场，不判断它是自然淡入淡出还是故障；每个命中都需要当前 final SHA 的人工 context。

此 gate 的 schema 只覆盖标准 HyperFrames post-mux 项目（`structured` / `free_exploration`），不接受 `ai_voice_mv`、`content_kind` 或训练源静音例外。AI 克隆整首 MV 继续走 `tools/video/templates/ai-voice-mv/` durable builder 的独立 QA；不能拿该 builder 的自报 source 身份伪装成本 gate 的机械证明。

gate 通过后仍执行以下内容判断；这些判断不能被机械 PASS 替代：

- **画面**：抽多帧拼 contact sheet，用 Read 逐帧看——各段对应素材、标签/标题清晰、**画面里无水印/网址/提示词/路径/项目内部词**。
- **封面排版与安全区**：单独检查 frame 0 的完整帧与顶部/底部裁剪预览；检查标题语义换行、行长平衡、孤字、歌手名字号层级、留白和主体避让。关键信息不得分裂在上下边缘，裁剪后必须完整；TOP 封面/intro 不得提前列歌单、排序或第 1 名。
- **音频语义**：人工核对 final AAC 与 isolated narration ASR 的 expected/assertion，确认可接受变体确实合理，旁白没有被音乐遮蔽；另抽测各首副歌响度趋于一致、旁白段音乐明显低于展示段。
- **展示段对齐**：`showcase_align.py check --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json` 必须 `FAIL=0 REVIEW=0 MISS=0`；同目录 `showcase_approvals.json` 会自动读取，但批准只允许解决 REVIEW，不能覆盖硬边界 FAIL。
- **节奏**：开场先配音再进音乐；每段旁白收尾有 0.8–1.2s 消化位，不死静、不硬切。
- **结构与时长**：普通盘点必须确认 intro、每首转场、作品 outro、固定 CTA 齐全；完全自由探索例外必须在 brief/design 有明确记录。确认没有人为总时长上限压缩歌曲，每首高光都落在完整乐句和自然出点。
- **配音一致性**：运行 `python3 tools/tts/verify_voice_usage.py --selection voice-selection.json --project-root .`，必须 `VOICE GATE: PASS`；intro、各排名转场、作品 outro 与固定 CTA 的 sidecar resolved ID 必须完全一致，且新项目脚本不得直连 Kokoro/硬编码 VOICE。
- 通过后给用户 `<slug>.mp4` 的绝对路径，并说明仍需人工耳/眼定夺的点（高光段是否最佳、源清晰度）。

## 人声检测回归

```bash
# 快速 schema/边界/批准门禁（媒体缺失也可跑）
tools/tts/venv/bin/python -m unittest discover -s tools/video/tests -p 'test_*.py' -v

# 使用本机 sandbox 历史音频，完整原音频分析；需显式 opt-in
CC_MEDIA_AUDIO_REGRESSION=1 tools/tts/venv/bin/python -m unittest \
  tools.video.tests.test_real_audio_regression.RealAudioRegressionTests -v
```

`audio_regression_manifest.json` 只是历史本地素材的可选索引，不随 git 分发音频。未设置 opt-in 时整组推理测试跳过；即使显式设置，若所有 manifest fixture 都缺失，也必须在加载 Whisper 前明确 `SKIP`，不能把缺素材报成检测器失败，更不能伪造同名 WAV。只有实际存在的 fixture 才执行，存在但 SHA 不符仍应失败。

首轮依赖仅增加已写入 `tools/tts/README.md` 重建命令的 `librosa==0.11.0`、`openai-whisper==20250625` 与显式缓存的 small 模型；不引入 Demucs/PANNs。后续若仍有无语义吟唱/超宽现场混音难例，再在独立 `tools/audio-analysis/venv` 引入 Demucs（只分离展示候选窗）和 PANNs crowd/choir 事件分数；不要把这两套老依赖装进 `tools/tts/venv`，模型缺失也不得按 0 分处理。
