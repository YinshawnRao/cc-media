# 视频制作 Runbook

编辑目标见 [CONVENTIONS](../../CONVENTIONS.md)，代理边界见 [AGENTS](../../AGENTS.md)。按实际任务执行；修代码或文档不启动 TTS/渲染。

## 1. Brief 与准备

记录主题、画幅、歌单/版本、是否排名、用户硬时长和明确偏好。新项目放 sandbox/<slug>/；设计简述写 design.md。新项目使用 schema v2，历史 v1 仅供复现。

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

## 来源记录与例外

每个 item.sources 记录 target_version、两平台记录、selection、cover_fallback、official_choice；字段定义以 [project-manifest.schema.json](project-manifest.schema.json) 为准。

默认平台记录为 searched=true、非空 search_queries 和 candidates；无结果写 no_usable_reason。若用户指定链接、排除平台或确认独占，使用：

```json
{"searched":false,"search_queries":[],"candidates":[],"search_exception":{"kind":"user_excluded_platform","reason":"用户本期明确只使用 YouTube"}}
```

kind 可为 user_specified_url、user_excluded_platform、platform_exclusive。直接指定 URL 的平台可在 skipped 记录中保留该 URL 的真实候选；排除的平台不得含候选。searched=false 表示没有执行搜索，不能填虚构搜索词。指定 URL 仍需核验身份、可用性和真实下载 receipt。

selection.download_receipt 只包含 schema 允许的脱敏 URL、平台、raw SHA、时长和派生链字段，不能保存 info_json/Cookie/header。它证明当前本地文件与声明的一致性，不单独证明网络上的官方身份。SOURCES.md 保存可核对的搜索、选源和事实来源，避免重复抄写全部机器字段。

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

## 4. 渲染与 mux

新项目在项目目录运行（已有项目用自己的精确 pin）：

```bash
npx --yes hyperframes@0.6.69 lint
python3 ../../tools/video/resource_budget.py hyperframes -- npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr
python3 ../../tools/video/resource_budget.py ffmpeg -- ffmpeg -threads __CC_MEDIA_THREADS__ -i renders/full_raw.mp4 -i master.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -threads __CC_MEDIA_THREADS__ -b:a 192k renders/<slug>.mp4
```

先核对 video/master 时长，不盲用 -shortest 隐藏尾部缺失。render 前后检查首帧和代表时刻；将同轮问题合并修正。实际 worker 预算由 wrapper 注入，不手写 auto。

逐首回听 mux 后的展示入点、出点及转场，确认没有首字被旁白遮盖、半句切断或淡出吃掉尾音；若延长/换窗，更新源窗口、timeline、预混与画面，再重新生成当前 SHA 的 QA。时长够长或边界检测 PASS 都不能替代这项实际听感核对。

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

自由探索不强套 preparer，按当前 project/final contract 准备 QA。AI 音色 MV 使用 [durable builder](templates/README.md) 与 --check，不伪造标准 manifest。两类同样交付 renders/<slug>.mp4 和 publishing/xiaohongshu.md，报告各自适用检查。

只有用户明确要求发布级终验才运行 --require-human-review；无 input 时工具生成当前 SHA 模板并返回 REVIEW_REQUIRED，真人完成后用 --human-review-input 合并。agent 不代签 human，本地 pending 不阻断普通制作交付。

## 开发回归

对代码改动运行相关 tests；完整轻量回归用 `python3 -m unittest discover -s tools/video/tests`。真实模型/历史媒体回归显式 opt-in。机械门禁不是审美或发布效果保证，最终仍须实际查看抽帧并核对音频。
