# 视频制作 Runbook

编辑目标见 [CONVENTIONS](../../CONVENTIONS.md)，代理边界见 [AGENTS](../../AGENTS.md)。按实际任务执行；修代码或文档不启动 TTS/渲染。

## 1. Brief 与准备

记录主题、画幅、歌单/版本、是否排名、用户硬时长和明确偏好。新测试项目放 sandbox/<slug>/，正式产物放 production/<slug>/；设计简述写 design.md。新项目使用 schema v2，历史 v1 仅供复现。

需要在线取材时，先通过下文 [来源启动检测](#来源启动检测)，再开展批量搜源、下载、旁白、封面生成和构建。纯代码/文档维护，以及完全复用本地已验证素材的编辑，不触发在线来源检测。

先按 [测试产物与生产产物](../../CONVENTIONS.md#测试产物与生产产物)确定用途。sandbox 全部按内部测试执行，不要求发布版权授权，不把配套文案或完整 MP4 当成公开发布请求；production 记录授权范围与目标发布用途。用户要求将测试片公开发布或按可发布成品交付时，先转入 production 发布流程。沿用既有 SOURCES.md/design.md 记录即可，不为目录区分添加未受支持的 manifest 字段。

新建、重做或优化封面必须执行 [封面图像生成流程](../../CONVENTIONS.md#封面图像生成流程)：

1. 检查当前 agent 实际提供的 AIGC 图像生成/编辑能力，优先 imagegen；该入口不可用时可使用其他名称的工具，须确认其实际调用图像模型。只有检查所有相关入口后均确认环境不可用，才按规范记录例外；写明已检查入口、实际错误及本轮未执行 AIGC 生图，可用现有真实图像和必要文字排版继续完成封面，严禁代码绘图补位。
2. 查看参考原图，按本期表达选择生成或编辑用途，实际调用选定的 AIGC 图像模型。默认生成无字视觉素材，提示词明确要求无文字、字母、数字、Logo 和水印，并按本期构图预留文字空间；不要求模型绘制标题、歌手名等最终文案。意外生成字形或伪文字时，先编辑清除或重新生成。不得以 SVG、HTML/CSS、Canvas、Python 绘图、网页截图或矢量转 PNG 替代模型生图；裁剪、缩放、合成及文字排版按规范允许的范围执行。输入错误或生成效果不佳应修正、迭代，不作为工具不可用的依据。
3. 将最终选用的生成图和采用版本的提示词保存在项目 `assets/`（如 `assets/cover-generation-prompt.txt`）；有参考图时保留原图。在 `design.md` 或已有素材记录中简记用途、实际工具、可取得的模型标识、参考图来源及输入/输出文件的对应关系，不虚构工具或模型名称。工具生成到项目外的图片须复制到项目内再引用，避免依赖宿主应用的缓存路径。
4. 在 HyperFrames HTML 中叠加独立文字层，用项目离线字体排版标题、歌手名、年份等信息，调整字号、字距、换行与层级。封面图与视频首帧使用同一套图文合成，首帧文字完整可见；不把无字生成图直接作为最终封面。用户明确要求生成艺术字等特殊表达时，按规范记录例外。
5. 检查实际封面、首帧和目标平台裁剪下的主体、文字与色彩融合，逐字核对文案，检查重复文字、伪文字残留、缺字和裁剪；随后执行独立 [封面审美评估](cover-aesthetic-review.md)。若替换已入片的首帧，重渲受影响内容并刷新最终成片 QA；仅导出新封面图不能代替更新已入片的封面。

没有明确画幅要求时固定 1080×1920（9:16），manifest 可省略 output_format 或写 `{"output_format":{"width":1080,"height":1920}}`。只有用户明确要求其他尺寸时才填写对应 width/height 和非空 user_request（用户原话）；设计理由不能代替用户要求。PROJECT 检查声明，FINAL 以同一 authoring manifest 核对 raw render 与最终 MP4 的真实宽高、方形像素和旋转信息；遗漏字段不会自动接受横屏。HTML 画布、构建配置与素材填充也须使用相同尺寸。

无用户硬时长则总长不限：先逐首确定完整核心段及安全起止，再累加音乐、实际旁白与衔接。不要从“短视频”推导分钟数或按歌数均分。选段表记录核心/展示源起止和音乐理由，前后各保留 3–5 秒可回调素材；成片缓冲按 [音乐规范](../../CONVENTIONS.md#结构旁白与音乐)与实际听感确定。

有新旁白才按 [TTS README](../tts/README.md) 选择声音、运行已选声线 doctor、通过中央 Qwen 入口生成 WAV。复用已有 WAV 不重新选声；无旁白不需要 TTS 环境或 voice_selection。

## 2. 素材、旁白与展示证据

来源记录见下文。需要 Cookie 的命令只使用：

```bash
python3 tools/video/yt_dlp_readonly.py -- -f 'bv*+ba/b' -o 'sandbox/<slug>/raw/%(id)s.%(ext)s' '<URL>'
bash tools/video/vfill.sh '<raw>' 'sandbox/<slug>/clips/vert_item.mp4' '<全宽横带crop>'
```

不得将 canonical Cookie 路径传给裸 yt-dlp。公开/备选下载与环境恢复见 [operations.md](operations.md)。

人声素材按实际语言分析，Live 必须声明 source-kind：

```bash
tools/tts/venv/bin/python tools/video/vocal_segments.py sandbox/<slug>/clips/vert_item.mp4 --mode multi --language zh --source-kind live -o sandbox/<slug>/probe/vocal_analysis.json
tools/tts/venv/bin/python tools/video/showcase_align.py plan --vocals sandbox/<slug>/probe/vocal_analysis.json --clip vert_item --near 105
```

plan 只建议源内展示窗，不读取 WAV；它保留的 --voice-dur/--lead 是历史兼容参数，不参与计算。初筛默认从约 60 秒展示空间开始向后找出点，--min-show 可按真实完整段落调整，不是成片硬下限；已知核心段结束时用 --through 指定必须完整保留到的源时间，出点再向后找。没有自动延长秒数上限，不能因候选长就倒退到半段。仍须核对整段内容，不能把自动候选当作副歌完整性的证明。构建时根据实际 WAV 计算预滚和 duck：TOP 转场 ≤8 秒，叙事转场 ≤10 秒；旁白在目标核心入点之前收尾，满音量从首字前的音乐铺垫开始，出点保留完整尾音和余韵。工具分析结果只描述检测证据，不能证明身份。

无旁白但有主唱的歌曲仍走 vocal/showcase 检查。此时 legacy 字段 narr_end_src 表示展示入点锚点，填为与 show_start_src 相同的真实源时间；不伪造 WAV 或改称器乐。例如窗口确定后记录 `{"songs":[{"key":"song-01","clip":"vert_item","narr_end_src":105,"show_start_src":105,"show_end_src":135}]}`（数字只是结构示例），再执行：

```bash
tools/tts/venv/bin/python tools/video/showcase_align.py check --plan sandbox/<slug>/build/showcase_plan.json --vocals sandbox/<slug>/probe/vocal_analysis.json
```

REVIEW 根据根因恢复。Live 能力限制可直接进入有证据的 agent observation；真实窗口问题再换窗，素材问题再换源，不以“穷尽所有源”作为观察的前置条件。记录要求不变：status=observed/reviewer_kind=agent、非空 reviewer、带时区 reviewed_at、clip/window/analysis 当前哈希及 evidence_files。APPROVED 只代表真人；FAIL 不可观察覆盖。

纯音乐项目提供 instrumental_plan 的真实时长、连续性和自然起止证据，不套唱声门禁。

## 来源启动检测

每期开工、故障恢复或重新开始在线取材时，执行一次中央只读检测；同次制作不在每个工具调用前重复运行：

```bash
python3 tools/video/check_source_access.py --query '本期歌手 代表歌曲'
```

默认检查两平台：YouTube Cookie 元数据、服务端登录态及 yt-dlp 搜索/视频元数据请求；B站 Cookie 元数据、nav 登录态及 WBI 搜索。静态 Cookie 检查通过、公开视频可访问或另一平台成功都不能替代失败平台的检测。PASS 只证明本次检测覆盖的访问，不能保证所有视频或媒体分片可下载；后续搜索/下载暴露同类故障，立即回到本节。

| 结果 / 退出码 | 处理 |
| --- | --- |
| `PASS` / 0 | 本次检查的平台均通过，继续制作；搜索确实返回空列表不是平台故障，继续换关键词或候选。 |
| `CONFIRM_REQUIRED` / 10 | Cookie 缺失/过期、服务端未登录、明确平台拒绝或风控等。任一平台出现即暂停本期制作，向用户说明平台、失败阶段、脱敏证据及另一平台状态，等待用户决定。不得自动切另一平台、匿名下载或生成后续制作产物。 |
| `ENVIRONMENT_BLOCKED` / 11 | 代理授权/沙箱/本机文件或进程权限不足、工具缺失。先在已有授权范围内恢复环境并复测；需要新增权限则按宿主权限流程处理。这不是平台不可用或 Cookie 失效的证据，不触发“接受单平台”的确认。 |
| `RETRY_REQUIRED` / 12 | DNS、超时、连接失败、无法解析的响应、提取器/单个候选问题，原因未定，尚未通过。先核对实际执行权限，再做一次有针对性的最小复测；单视频下架、地区/格式限制或无结果可换同版本候选。排除代理执行限制后平台仍无法访问，暂停并请用户确认，原因写实际网络/接口异常，不能猜成 Cookie 过期。 |

宿主拒绝执行、自动审批拒绝、`Operation not permitted` 等内部失败可能发生在脚本启动之前；必须先查看实际工具结果，不能因脚本没输出 PASS 就声称平台拦截。仅凭受限上下文里的 DNS/超时也不能排除沙箱原因。未经足够执行权限的复测，不得将 `ENVIRONMENT_BLOCKED` 或未知错误升级为平台故障。单个播放器/码流的 403 先核实是否候选或客户端兼容问题；确认平台风控后不得以反复换客户端、换源来绕过暂停。

暂停后只保留诊断与现场，不继续本期制作。可向用户请求“修复 Cookie/网络后重试，还是本期明确只用可用平台”；没有答复、一般性的“自主完成”或既有 sandbox 制作授权都不算接受来源降级。用户修复后重新检测通过，或用户明确同意本期降级/指定来源后，才恢复。将检测时间、各平台状态、脱敏错误、复测结果及真实用户答复写入 `SOURCES.md`；不改 Cookie，不保存原始响应、header 或 info JSON，不伪造自动批准。

用户此前已明确指定 URL、排除平台或确认独占时，按下节真实来源例外确定所需平台；可以用 `--platform youtube` 或 `--platform bilibili` 只检查所需平台。失败本身不能成为代理自行添加此参数的理由；所需平台仍须通过检测或取得针对该故障的明确用户决定。CLI 不代替用户交互，也没有自动批准开关；本节由执行制作的代理负责落实暂停与恢复。

## 来源记录与例外

每个 item.sources 记录 target_version、两平台记录、selection、cover_fallback、official_choice；字段定义以 [project-manifest.schema.json](project-manifest.schema.json) 为准。

默认平台记录为 searched=true、非空 search_queries 和 candidates；无结果写 no_usable_reason。若用户指定链接、排除平台或确认独占，使用：

```json
{"searched":false,"search_queries":[],"candidates":[],"search_exception":{"kind":"user_excluded_platform","reason":"用户本期明确只使用 YouTube"}}
```

kind 可为 user_specified_url、user_excluded_platform、platform_exclusive。直接指定 URL 的平台可在 skipped 记录中保留该 URL 的真实候选；排除的平台不得含候选。searched=false 表示没有执行搜索，不能填虚构搜索词。指定 URL 仍需核验身份、可用性和真实下载 receipt。

selection.download_receipt 只包含 schema 允许的脱敏 URL、平台、raw SHA、时长和派生链字段，不能保存 info_json/Cookie/header。它证明当前本地文件与声明的一致性，不单独证明网络上的官方身份。SOURCES.md 保存可核对的搜索、选源和事实来源，避免重复抄写全部机器字段。

sandbox 的 MV 候选按身份、版本、实际画面和可下载性评估，不因推测发布版权风险而改用音源封面。没有合适 MV、选择了其他版本、素材仅含封面、网络失败与平台明确版权限制是不同原因，必须分别记录；只有实际平台返回了版权限制证据，才可报告“被版权拦截”。`release_safety` 是发布复核字段，不是自动版权识别或过滤器。

## 编辑例外与旁白绑定

manifest 的可选 editorial 字段默认 narration=standard、cta=fixed、cta_text_version=short-v1。新项目自动追加固定简短引流配音；普通设计理由不能授权删除。只有用户明确要求例外时才记录，例如用户确实说了“这期不要结尾引流配音”：

```json
{"editorial":{"narration":"standard","cta":"omit","reason":"按用户要求省略本期引流配音","cta_user_request":"这期不要结尾引流配音"}}
```

- cta=custom：用本期最后一条 outro_cta.text 指定用户要求的文字；cta=omit：不得存在 outro_cta 行。两者都必须填写非空 cta_user_request（真实用户原话）和 reason；包括用户明确要求全片无旁白的情况。门禁只能核验字段，代理必须对照真实会话，不能把自己的设计理由伪装成用户要求。
- narration=custom：按设计声明实际 narration_sequence，可减少、合并或重排旁白；有 CTA 时仍最后出现一次。非默认选择必须填写 reason。转场不能靠改成 free 来绕过 8/10 秒检查。
- 默认文字通过 `python3 tools/video/outro_cta.py` 取得。默认短句只念一次，作为最后一句旁白；只有主题提问不满足引流要求。用户明确指定单期文字时使用 custom，不修改全局常量。
- 历史工程已使用原长版固定句时，重验前可显式记录 `{"editorial":{"cta":"fixed","cta_text_version":"legacy-v1","reason":"原工程已使用长版固定句，保留历史旁白复现"}}`；它只匹配中央保存的原文，不接受任意改写，不要求重新生成历史 WAV。新项目使用 short-v1；未声明版本按当前短版校验，不按文件日期猜测。
- 每条实际旁白绑定自己的 text/wav/sidecar；序列须覆盖所有中央 sidecar。转场 item_id 指向真实 item；重复角色或特殊结构用 chapter_id 显式绑定 timeline 章节。
- timeline 的 role 支持 intro/song/outro/cta/free；没有旁白的章节显式 requires_narration=false，实际 narration_wavs=[]。普通旁白不可漏登记，自定义结构也不能漏检。
- 最终音轨必须包含实际 CTA，纳入 FINAL 的 authoring 文本/WAV 绑定、音轨一致性和最终 AAC ASR 覆盖；交付前核对片尾。仅有 outro_cta 字段、浮层或 publishing 文案不算完成。

## 3. 构建门禁与媒体合成

在正式生成 master/HTML 前执行：

```bash
python3 tools/video/verify_project.py --project sandbox/<slug>
```

必须 PROJECT CONTRACT: PASS；有旁白时包含中央 VOICE 核验。字段示例在 [examples/project-contract](examples/project-contract/README.md)，其中媒体占位符不能冒充通过。

优先复用 [longform-timeline](templates/README.md) 拼接 footage_track/master/timeline。countdown_build.py 是既有固定榜单模板，包含示例曲目和固定 CTA；只用于匹配的结构。自定义结构使用 longform 骨架和当期 HTML，不能只改 manifest 却仍渲染旧模板。narrate_segments.py 是 Qwen batch 调用示例，实际文案由项目决定。

多片段长片优先拼成单一 footage_track，减少浏览器同时解码负担；短片/特殊构图可用经验证的多 video。所有时间锚点来自 timeline，使用可 seek 的动画，离线字体。音频预混 master.wav 后期覆盖 raw render 音轨。

## 封面审美评估

整片渲染前按 [独立封面审美评估](cover-aesthetic-review.md) 实际查看图文合成后的完整封面、手机预览和目标裁剪，在项目 `qa/cover-aesthetic-review.md` 记录本期期望、逐项观察、图像路径/哈希、审阅者身份与结论。此环节由 agent 视觉审阅完成，独立于机械门禁，不增加默认用户审批。

`PASS` 后继续渲染；`REWORK` 写清可见问题并仅退回封面图像、文字及封面区间，复用原音轨、时间轴和正文内容，修复后复评；`REVIEW_REQUIRED` 先补齐证据再审阅。具体范围保护、复评与记录格式见上述流程。初评通过不代替交付前的实际版本确认。

## 4. 渲染与 mux

新项目在项目目录运行（已有项目用自己的精确 pin）：

```bash
npx --yes hyperframes@0.6.69 lint
python3 ../../tools/video/resource_budget.py hyperframes -- npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr
python3 ../../tools/video/resource_budget.py ffmpeg -- ffmpeg -threads __CC_MEDIA_THREADS__ -i renders/full_raw.mp4 -i master.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -threads __CC_MEDIA_THREADS__ -b:a 192k renders/<slug>.mp4
```

先核对 video/master 时长，不盲用 -shortest 隐藏尾部缺失。render 前后检查首帧和代表时刻；将同轮问题合并修正。实际 worker 预算由 wrapper 注入，不手写 auto。

逐首回听 mux 后的展示入点、出点及转场，确认没有首字被旁白遮盖、半句切断或淡出吃掉尾音；同时检查开头、主题切换和结尾连续配音处，确认音乐没有无意的硬切或前奏重启。若延长/换窗，更新源窗口、timeline、预混与画面，再重新生成当前 SHA 的 QA。时长够长或边界检测 PASS 都不能替代这项实际听感核对。

## 5. 发布文案与 FINAL

完成 build/render/post-mux 后编写 publishing/xiaohongshu.md，按 [编辑规范](../../CONVENTIONS.md#发布文案)写作。文件结构：

```markdown
# 小红书发布文案

## 标题候选（第一条为首选）

- 首选标题

## 正文

与本期主题、人物和选题角度相关的可发布正文。

#相关人物 #本期主题
```

1–5 个标题，默认 3 个；字数和标签数是建议。明确歌名引用会失败；普通词语歧义会提示 EDITORIAL，由代理核对语境，不能把提示当成已经确认剧透。

```bash
python3 tools/video/verify_publishing.py --project sandbox/<slug>
python3 tools/video/prepare_final_qa.py --project sandbox/<slug> --final renders/<slug>.mp4 --render renders/full_raw.mp4
```

PUBLISHING 不属于 build 前 manifest 门禁，必须在 FINAL 前完成。preparer 支持 top_ranking/narrative 的标准或显式自定义结构，将 authoring 与 timeline 绑定，生成当前 SHA 的实时 ASR、逐章 PNG、诊断并在同一进程执行 FINAL。每条实际旁白都必须映射并检查，无旁白不会生成虚构 WAV。

只有输出 FINAL VIDEO QA: PASS 才算本地机械终验；不手写 QA manifest 冒充 preparer，也不在 PASS 后默认再次运行全量 standalone verifier。独立复核/诊断才使用 `verify_final_video.py`。

交付前完成封面审美的最终版本确认：查看最终封面、真实第 0 帧及手机裁剪，将当前 MP4 SHA 和实际图像证据补入 `qa/cover-aesthetic-review.md`。现有 preparer 不自动评判审美，交付分别报告 `COVER AESTHETIC REVIEW: PASS（agent/human 按实际填写）` 与适用技术门禁；未审或需重做时不能只凭 FINAL PASS 宣称全部完成。封面返工改变 MP4 后，刷新适用的技术 QA 并复核非封面部分的保护范围。

自由探索不强套 preparer，按当前 project/final contract 准备 QA。AI 音色 MV 使用 [durable builder](templates/README.md) 与 --check，不伪造标准 manifest。两类同样交付 renders/<slug>.mp4 和 publishing/xiaohongshu.md，报告各自适用检查。

内部 sandbox 测试使用以上本地命令，不运行 --require-human-review；已有 release_safety/pending_human_review 字段不表示发现版权问题，也不阻断测试交付。production 的版权与授权核对按已记录的用途执行；只有用户明确要求公开发布、发布级终验或可发布交付时才运行 --require-human-review。该开关需要显式传入，CLI 不按目录名自动切换。无 input 时工具生成当前 SHA 模板并返回 REVIEW_REQUIRED，真人完成后用 --human-review-input 合并；agent 不代签 human。

## 开发回归

对代码改动运行相关 tests；完整轻量回归用 `python3 -m unittest discover -s tools/video/tests`。真实模型/历史媒体回归显式 opt-in。机械门禁不是审美或发布效果保证，最终仍须实际查看抽帧并核对音频。
