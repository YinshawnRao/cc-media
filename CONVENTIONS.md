# CONVENTIONS.md — 全局规范

本文件用于**积累和定义可复用的规范**。每当在 `sandbox/` 验证出一个值得固化的做法，就写到这里；`AGENTS.md` 承载顶层代理硬约束，`CLAUDE.md` 只做入口，各工具 README 记录可执行细节，三者都不得另立与本文件相冲突的生产规则。

> 状态：仓库已经初始化并持续用 Git 管理；“探索阶段”只表示允许在 `sandbox/` 试错，不表示重新执行 `git init`，也不降低下列门禁和提交边界。

## 目录约定

- `sandbox/<项目名>/` — 每期实际项目、测试和生成物；内容可丢弃，且不得成为复用脚本、schema 或规范的唯一副本。新项目的 raw render 与 mux 后最终 MP4 统一在 `renders/`，最终交付固定为 `renders/<slug>.mp4`；发布文案统一在并列的 `publishing/`。
- `production/<项目名>/` — 需要长期保留的正式工程；每个项目独立，保存可复现输入与轻量证据，不把最终 MP4 当作唯一交付依据。
- `tools/` — 跨项目复用的源码、schema 与 durable 模板（如 `tools/tts/`、`tools/video/templates/`）；验证稳定后从 `sandbox/` 迁到这里。
- **Git 边界**：提交源码、文档、配置、schema 和轻量 QA 证据；下载媒体、普通 WAV/MP4、渲染缓存、模型/runtime、Cookie、token 与其他敏感信息必须由 `.gitignore` 隔离，并在提交前检查 staged 清单。根目录被忽略的 `all_cookies.txt` 是下载运行时输入，不是可提交资产。

## 配音 (TTS) 规范

- **适用范围**：以下默认只约束规则生效后**新启动的盘点视频**。已有 WAV 的历史项目原样复用；已有 voice/model/reference 记录的工程按原配置复现，不因新默认自动换声。本次随机池迁移前的已知 config/registry 哈希对由中央配置显式兼容，不能泛化接受任意 stale selection。只有用户明确要求“按当前默认重新配音/迁移”时才切换。
- **默认选择策略（硬约定）**：未唯一指定音色时，从 `CV001 / CV002 / CV003 / CV004 / CV005 / CV008` 女声池随机一次；均由 Qwen3-TTS Base + 已选定原创参考母带在 Apple Silicon 本地生成。`tools/tts/config.json` 是随机池与选择策略唯一真源，`tools/tts/voices/registry.json` 是编号、名称、分组和别名唯一真源。
- **任务提示词解析优先级**：
  1. `配音：` / `音色：` / `voice=` 结构化字段中唯一精确匹配的角色编号、正式名称或注册别名。
  2. 若无结构化字段，任务提示词中带配音语境的唯一、肯定式精确匹配。
  3. **未指定、未知、模糊描述、多个冲突候选、无法唯一匹配：从配置中的女声池随机一次。**禁止相似度猜测；“男声/女声/可爱一点/二次元声音”等不能唯一定位的描述也进入同一随机池。
- **启动解析闸门（每个项目只解析一次）**：把用户原始任务提示词交给 resolver，落盘项目级 `voice-selection.json`；随机结果与完整候选池必须同时记录。intro、全部排名转场、作品 outro、固定 CTA 都复用这一个文件，不得逐段重新判断或重新抽取。
  ```bash
  python3 tools/tts/resolve_voice.py --task-prompt-file brief.txt \
    -o sandbox/<slug>/voice-selection.json
  # 仅当 resolved_id 不是预检声线 CV002 时，精确检查本期实际母带
  python3 tools/tts/doctor.py --voice <resolved_id>
  python3 tools/tts/narrate.py script.txt \
    --selection-file sandbox/<slug>/voice-selection.json -o out.wav
  ```
  默认 doctor 只验核心模型/runtime 与预检声线 CV002；CV002 在此不代表新项目默认成片声线。`--full-library --check-mixed-script` 只用于声音库维护和混合文本能力回归。未使用角色或纯中文不依赖的策略不得阻断本期任务。
- **唯一正式生成入口**：新项目只能调用 `tools/tts/narrate.py`（单条或 batch）；禁止直接 `from kokoro import KPipeline`、禁止在项目脚本里硬编码 `VOICE = ...`。每个 WAV 必须生成 `.wav.tts.json` sidecar，记录 resolved ID、模型 revision、参考母带 SHA、文本与输出 SHA。
- **当前步骤硬失败，而不是换声或停止整个 goal**：本期已解析 Qwen 声线的运行环境、固定模型或参考母带缺失/校验失败时，只让当前 TTS 步骤 fail closed；代理必须按 doctor 输出修复固定环境、模型、母带或 receipt，再重跑旁白及受影响下游门禁。**不得静默降级 Kokoro，也不得重抽另一声线绕过失败**，也不得把可修复问题转成用户确认点，否则无法保证项目级音色一致性。
- **构建门禁**：新项目旁白完成后运行 `tools/tts/verify_voice_usage.py`；所有旁白 sidecar 必须与项目级 selection 同一 ID，项目脚本不得绕过中央入口。
- **显式声音**：`CV001–CV008` 的编号、名称、别名与实际样音见 `tools/tts/voices/listen.html`。无效显式选择进入女声随机池，并在 selection 中记录 fallback 原因、候选池与最终结果。
- **口播文本**：新盘点 intro 第一段**禁止出现“接下来”**。默认 Qwen `Auto` 允许中英日等混合文本，不再沿用 Kokoro 的“非中文一律跳过”经验；外文专名必须先听样音/做内容 QA。只有实际发音不自然、歧义大或不可懂时，才改用通行中文译名、音译/发音友好的谐音字，或从口播省略并只在画面保留原文。
- **混合文本发音（Qwen 硬约束）**：明显英文单词优先按词发音；视觉上为连续全大写时，送入 TTS 前先归一为正常词形，例如 `BEYOND → Beyond`。只有明确的首字母缩写或不可自然词读的字母串才逐字母读，例如 `BTS → B T S`、`S.H.E. → S H E`。判断不确定时先生成短样音，或通过项目级 `pronunciation_overrides` 明确读法，不得直接改成生硬中文谐音。归一化只影响 TTS 口播输入，画面仍保留艺人/作品的官方写法。
- **纯中文稳定性（硬约束）**：自动发音归一化只检查 ASCII 拉丁 token；未显式提供发音覆盖时，纯中文文本、中文标点、数字和原有中文措辞必须逐字原样透传，不做分词、加空格、拼音化或其他改写。纯中文请求不得依赖外文发音策略文件，其生成 seed、请求结构和既有缓存指纹必须保持不变。
- **Legacy Kokoro**：8 个旧 ID 仅用于历史复现或用户精确指定（如 `--voice zm_yunxi`）。`--female` 保留旧兼容语义 `zf_xiaoyi`，但**新盘点禁止用 `--female` 表达默认**。
- **不要用 HyperFrames 内置 `npx --yes hyperframes@0.6.69 tts` 做中文**：它把语言代码 `zh` 传给 espeak，而 espeak 只认 `cmn`，中文直接报错；且 espeak 普通话质量弱。英文旁白才考虑内置 tts。
- 输出 24kHz wav，作为独立 `<audio>` 轨接入 composition（见下「全链路」）。用户明确要求字幕时，自动字幕可对 wav 跑 `npx --yes hyperframes@0.6.69 transcribe`；历史项目则使用其 lockfile/package scripts 已固定的版本。
- **Legacy Kokoro 专属：⚠ 长句（~15s+）独立 `pipeline()` 调用会吞掉开头第一小句（2026-07 实战，`xietingfeng-underrated-top5` 排查）**。本条及下面的“垫话”修法**只用于明确复现 Kokoro 的旧项目，不得复制到当前编号 Qwen 声线流程**；Qwen 会把“接下来”等垫话正常念出来。TOP 盘点每首的整段旧旁白（"第X名，《歌名》。它收录在……" 一大段，单次 `pipeline(text, voice=..., speed=1.0)` 调用生成，时长 15-19s）有概率把开头第一句吞掉或吞掉一部分。
  - **根因**：与文本内容无关（把无意义的垫话放在最前面，垫话会被吞、真正内容才是"被吞对象"），是 Kokoro 对**长独立发声**开头的一个通病；短句（<10s）或"同一大段里第一句"都不受影响，只在"这段话本身是一次孤立的长 `pipeline()` 调用"时出现。**同一系列此前项目（如 `xuruyun-underrated-top5`）用 Whisper 抽查也复现同一问题**——过去这个 bug 一直存在但没被发现，因为没人用 ASR 逐句核对过旁白。
  - **旧项目修法（仅 Kokoro）**：给每段旁白文本前面拼接一句垫话（如"接下来，"），再送进旧 `pipeline()`。只在严格复现 legacy Kokoro 时保留；当前编号 Qwen 声线文案不得自动添加垫话。
  - **验证方法**：改完必须通过 `tools/video/offline_asr.py` 或调用它的中央 FINAL preparer 转录旁白，抽查开头“第X名”完整出现；不能只看 RMS/时长判断——那看不出“内容被吞”。不得裸跑 `whisper-cli` 绕过固定工具链与自适应预算。

## 命名约定

- 项目/成片名：`kebab-case`（如 `ai-news-weekly-01`）。
- 源素材文件名使用 `kebab-case`，至少包含项目内 item key、平台或 source ID、切片起止时间；完整 URL、时间窗、文件 SHA 与派生链以项目 `project-manifest.json`、download receipt 和 `SOURCES.md` 为准，文件名不承担完整 provenance。

## 素材源平台（硬约束，优先级高于 brief）

**两边都要找：YouTube + B站（哔哩哔哩）并行**。每条素材都先在两个平台各搜一遍候选，并严格按下面的优先级锁源；不要用“综合质量”把高清二剪排到可用官方 MV 前面：

1. **版本身份匹配（最高优先）**：盘点对象若是某翻唱者的翻唱版本，必须优先找该翻唱者对应的 MV、现场或正式演出视频，不能用原唱歌手画面冒充该版本。只有 YouTube 与 B站均找不到可用对应翻唱视频时，才考虑原版视频，并在 `SOURCES.md` 写清两边搜索证据、缺口与替代理由。
2. **官方 MV 来源（高于清晰度）**：在目标歌手/版本身份正确的前提下，只要存在可取得、目标段可正常使用的官方 MV，就优先官方 MV，即使年代久、分辨率或码率稍低。低清、4:3、轻微噪点本身都不是弃用官方源的理由。只有官方 MV 确实不存在、无法取得，或目标段有无法规避的结构性问题（例如全程静帧、目标人物完全不出镜、不可裁净的遮挡）时，才退到官方直拍 / Live、综艺 Live 或二次来源，并在 `SOURCES.md` 写明证据和理由。
3. **画面干净度**：无烧死歌词字幕 / 台标 / 平台水印 / UP主水印 / 双语条；MV 中部的歌词条比底部更难裁，优先无歌词版。
4. **音频质量**：立体声优先 > 单声道；高码率优先；注意 **B站给 4K 流配的音轨常是单声道**，遇到这种"4K 单声道 vs 1080P 立体声"，在两个候选同为官方 MV 时**优先立体声**（MV 听感为主）。
5. **清晰度**：只有在版本身份和官方属性相同后，才比较分辨率 + 码率（同 1080P 也可能码率差一倍）。
6. **备选来源层级**：官方 MV > 官方直拍 / Live > 综艺 Live > 二次剪辑；多机位综艺常切镜密集（每 2-4s），难锁长特写。
7. **可用切片**：源里要有连续可用段（如至少一个完整副歌不被打断）。

**优先级**：本条约束**高于单期任务 brief 里的临时指定**。除非用户在 brief 里 **显式** 说 "只用 YouTube" / "只用 B站" / "用这个 URL"，否则**不允许只搜单边**就开工。即使 brief 里给了一个 YouTube URL 但没说"必须用它"，仍要在 B站对照一下有没有更优版本，再决定。

**例外**（不需要强制对照）：
- brief 明确给定具体 URL，且语气是"就用这个"（如 "用这个链接的 0:20-0:30 段"）。
- 节目类型上一个平台明显独占（如纯 B站独家 UP 主二创、YouTube 独家直播档案）——但仍需在汇报里说明"另一边没有可比版本"。

**汇报模板**（给候选时）：
```
《歌名》候选：
 - YT: <URL> | 1080P AVC 立体声 | 烧死英文字幕(底) | 官方 MV
 - B站: <bvid> | 4K AV1 单声道 | 干净 | 官方 MV
 → 选 YT（立体声 > 4K 分辨率优势；底部字幕可 crop 掉）
```

## 固定结尾配音（结构化视频硬约束，优先级高于 brief / 任务提示词）

**每条非自由探索类成片的最后一句旁白固定为这句引流 CTA，逐字照念，不由单期 brief 决定；机器唯一真源是 `tools/video/outro_cta.py::FIXED_OUTRO_CTA`：**

> **你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。**

**优先级（核心）**：本句是**所有排名、解说、主题叙事视频的统一固定收尾**，优先级**高于单期任务 brief / 提示词**。brief 不写它、不改它，也不能用"这期结尾说点别的 / 换个 CTA / 不要 CTA"来覆盖它。唯一常规例外是项目从启动阶段就明确归类为**完全自由探索类**：以音乐/视觉实验本身为主体、没有排名或解说结构，并在 brief / design 中明确采用无旁白或非结构化声音方案；不能在普通盘点做完后临时借此名义删 CTA。固定句不存在项目级变量或替换；只有一次明确的**全局规范变更**同时修改 `FIXED_OUTRO_CTA`、本节与相应测试，才算改变 canonical CTA。即便某期 brief 给了自己的结尾文案，那份文案也只能落在「作品自身 outro」，固定句仍在其后照念。

**位置（铁律）**：永远是**全片最后一句**旁白——排在每期作品自身 outro 之后。结构：

```
[作品 outro] 总结排名 / 主题升华（收在歌手特质上，每期独有，brief 可写）
   ↓ 0.8–1.2s 消化位（床 swell，不死静）
[固定 CTA]  你最想为哪一首投票？……盘到你单曲循环过的那一首。  ← 全片最后一句，固定
   ↓ 末 1.6s fade
```

**音色一致性（铁律）**：固定 CTA 不得另开一条旧 Kokoro 配音。它必须与本期项目级 `voice-selection.json` 的 resolved voice ID 完全一致，并纳入 `verify_voice_usage.py` 门禁。

**防双 CTA（必守）**：既然固定句兜底互动，**每期作品自身 outro 不得再自带投票 / "你会怎么排" / "你心里第一名是谁"之类问句**——否则连问两次投票、像两个结尾。作品 outro 只负责把内容讲完、收在主题升华，互动 ask 一律交给固定句。

**音频 / 时长**：当前 Qwen 声线下固定句通常约 9–11s；`OUTRO_D` 必须由本期作品 outro、固定 CTA 的实际 WAV 时长与消化位动态计算，不得继续硬编码历史 `~22–24s`。音乐床取**副歌段**铺到底再 `afade` 末 1.6s 淡出（**别用歌曲淡出尾**，太轻会 dead-air，见下「片尾 dead-air」），旁白段照常 duck 到 ~20–26%；固定句念完留尾再 fade，不硬切、不死静。

**画面**：可配轻量"投票 / 点赞关注"CTA 浮层并与投票 UI 同步亮起；但**不得出现任何平台水印、账号 ID、网址**（老铁律，成片不露 meta / 平台信息）。

## yt-dlp 规范

- **Cookie 文件（统一约定）**：仓库根目录 `all_cookies.txt` 是用户维护的 canonical Netscape jar；它不是代理可再生的缓存，也不是普通 goal 的输出。canonical 不要求不可变锁，代理禁止覆盖完全由 `AGENTS.md` 与本节的提示词约束。只有用户本人可以手工覆盖或安装它。代理仅可静态读取，禁止对 canonical 文件或其路径直接写入，禁止执行 `chmod`、`touch`、`mv`、`cp`、过滤替换、删除或重建；不得以自动修复、测试、Cookie 更新或任务恢复为理由改变其内容、inode、mtime 或权限。
  - **为什么仍需 Google 域**：YT 过 bot 检查依赖登录态 cookie，其中 `LOGIN_INFO/SID/HSID/SSID/SAPISID` 等常落在 **`.google.com`** 域上；用户若选择生成目标域 candidate，过滤时必须保留 YouTube 域及所需 Google 域，B站则保留 Bilibili 域。canonical 使用完整导出还是过滤 candidate 由用户本人决定；代理不得因发现额外域而删除、重写或重新过滤 canonical。
  - **yt-dlp 必须经只读 wrapper**：`yt-dlp --cookies FILE` 会在退出时重新序列化并回写 FILE，所以搜索、`--skip-download`、格式检查和下载都不能把 canonical 路径传给裸 yt-dlp。统一使用 `python3 tools/video/yt_dlp_readonly.py -- <yt-dlp 参数>`，并且参数中不得再写 `--cookies`、`--cookies-from-browser` 或 canonical 路径。只有 wrapper 可以在仓库外权限隔离的私有临时目录创建工作副本；yt-dlp 仅回写该副本，结束即清理。代理不得用 shell `cp` 自制副本，也不得把 Cookie 放入 `sandbox/`、项目目录或仓库内临时目录。
  - **用户更新边界**：浏览器原始导出与 candidate 都必须在仓库外并为 `0600`。`filter_cookie_jar.py` 只接受显式 `--output`，且只生成仓库外 candidate，例如 `python3 tools/video/filter_cookie_jar.py SOURCE --output /absolute/outside/candidate.txt`；它不再安装或覆盖 canonical。该命令仅供用户维护流程调用，代理和普通 goal 禁止运行。candidate 由用户本人检查后手工安装为 `all_cookies.txt`，并亲自恢复 `0600`；代理不得代做安装或权限变更。`document.cookie` 拿不到 HttpOnly 凭据，不可用。
  - **静态检查与兼容边界**：`check_yt_cookie.py` 只读 canonical，检查字段、文件内 expiry 与 `0600`；不检查或要求不可变锁。额外域只报告数量作为 advisory，不输出域名、不让有效的用户快照 FAIL，也不修复文件。`bili_search.py` / `bili_dl.py` 只允许只读使用 canonical。旧 `www.*_cookies.txt` 不再作为新任务入口；登录态虽已 gitignore，仍必须在提交前检查 staged 内容。
  - **不中断普通任务**：Cookie 缺失、不可用、静态检查异常或服务端失效时，代理先继续公开下载和 YouTube / B站双平台备选，不得因此暂停或阻断普通 goal；确实需要新登录态时只报告用户输入边界，仍不得碰 canonical。
- **YouTube 登录态**（反爬：不带或缺登录态会报 "Sign in to confirm you're not a bot"）：
  - `all_cookies.txt` 须含 HttpOnly 认证 cookie（`LOGIN_INFO` + `SID/HSID/SSID/SAPISID/APISID` + `__Secure-3PSID`），其中多个在 `.google.com` 域。`python3 tools/video/check_yt_cookie.py` 会正确解析 Netscape `#HttpOnly_` 行，并静态检查字段、文件内 expiry 与 `0600` 权限。
  - **过期与更新**：标称过期约 1 年，但**实际寿命短得多**——YouTube 服务端频繁轮换 `*SIDCC`/`*SIDTS`，实践中常几天～几周失效。`check_yt_cookie.py` 只是**静态预检**，不能验证服务端新鲜度：字段都在却仍 bot 拦，仍可能是服务端已轮换、快照过期。
    - **bot 拦排查顺序（2026-06 经验，禁止自动升级环境）**：① 记录当前 `yt-dlp --version`，运行只读 `check_yt_cookie.py`，再通过 `yt_dlp_readonly.py` 包装的 `--skip-download --print` 复现并区分 bot 登录态提示与签名/播放器错误；② 静态字段正常但仍明确 bot 拦时，代理继续公开下载、双平台同版本候选和安全 client 备选，不修改 Cookie，也不暂停普通 goal；③ 确实需要新登录态时，只报告用户输入边界，由用户自行在仓库外生成 candidate 并手工安装；④ 只有证据指向 yt-dlp 兼容性且用户允许变更环境时，才安装/切换到明确版本并记录前后版本。不得把 `brew upgrade yt-dlp` 当作自动第一步，也不得用一次升级成功反推 Cookie 当时有效。换 `--extractor-args player_client` 对登录态失效无效。
    - 用户若希望快照更耐用，可在无痕窗口登录后把原始导出与 candidate 全程留在仓库外，亲自安装 canonical 后直接关闭窗口而不登出；代理不参与过滤、安装或权限变更。
  - **另一种 403（非 bot 拦，2026-07 实战，`sandbox/xietingfeng-underrated-top5` 验证）**：cookie 有效、`check_yt_cookie.py` 通过，但下载 adaptive(dash) 流（itag 137/140/251 等）持续 `HTTP 403 Forbidden`，日志显示走的是 `tv downgraded player API` + `[jsc:deno] Solving JS challenges` 链路——这是该 client 的签名解密偶发失效，与登录态无关（区别于上面 line 99 的 bot 拦场景）。单独 `--extractor-args "youtube:player_client=web"` 能避开 403，但格式表被裁到只剩 itag 18（360p）。**修法**：四个 client 一起传 `--extractor-args "youtube:player_client=web,web_embedded,web_music,mweb"` → 格式表恢复完整（含 1080p），下载不再 403。遇到"cookie 明明有效却仍 403（不是 bot 拦提示语）"时先试这个，而不是急着重新导出 cookie。
- **B站登录态**（无登录态只能拿到 ≤720P；大会员/番剧/4K 必须）：
  - canonical 若用于 Bilibili 登录态，须含 `SESSDATA`、`bili_jct`、`DedeUserID` 等字段；是否还包含其他域不影响本条有效性。
  - 过期更新比 YT 更频繁（几周）；触发信号是清晰度被压回 720P 或 4K 选项消失。代理先继续公开和双平台备选；只有用户本人可按“仓库外导出 → 仓库外 candidate → 手工安装 canonical”更新。
  - **B站搜索 yt-dlp 不能解析**，要用 API：`https://api.bilibili.com/x/web-interface/wbi/search/type?search_type=video&keyword=<关键词>`，response 里 `data.result[].bvid` 即视频 ID，URL 拼为 `https://www.bilibili.com/video/<bvid>`。
    - **必须 WBI 签名**（2026 验证）：普通 search 端点 + `yt-dlp bilisearchN:` 现在都返回 **HTTP 412 风控**。要先 GET `https://api.bilibili.com/x/web-interface/nav` 取 `wbi_img.img_url/sub_url` 的文件名 → mixin_key（固定 64 位重排表取前 32 位）→ 参数加 `wts` 排序 urlencode 后 `md5(query+mixin_key)` 得 `w_rid`，带 cookie + 桌面 UA 才通。**复用脚本 `tools/video/bili_search.py`**（用法 `python tools/video/bili_search.py "关键词" [n]`）：模块导入不读 Cookie，只有实际搜索时才延迟加载根目录 `all_cookies.txt`，输出 `bvid | 时长 | up主 | 标题`。
  - **B站下载 yt-dlp 报 HTTP 412 风控的救场（2026-06 验证）**：`yt-dlp` 的 BiliBili extractor 走的 webpage/playurl 端点会被 412 风控（即使 cookie 有效、search 与 `--skip-download --print` 偶尔能过），重试也基本恒 412。但**普通浏览器式 `curl --compressed` + 桌面 UA + `referer:https://www.bilibili.com/` + Netscape jar 仍能取到视频页**，页里内嵌 `window.__playinfo__`（DASH `baseUrl` m4s 直链）。**复用脚本 `tools/video/bili_dl.py`**（用法 `python tools/video/bili_dl.py <bvid> <out.mp4> [--max-h 1080]`）：curl 直接读取 jar 路径，cookie value 不进入 argv；随后解析 playinfo → 取 ≤max-h 优先 AVC 的 video + 最佳 audio 直链 → curl 下载 → ffmpeg mux 成 mp4。这是 B站下载被 412 挡住时的首选下载法。
- **切片**用 `--download-sections "*HH:MM:SS-HH:MM:SS"`，避免下整片（已验证：635s 视频只取 10s）。
- 已验证可用的切片命令（wrapper 自动使用 canonical 的仓库外临时副本）：
  ```bash
  python3 tools/video/yt_dlp_readonly.py -- "<URL>" \
    --download-sections "*00:00:30-00:00:40" --no-playlist \
    -f "bv*[height<=1080]+ba/b[height<=1080]" \
    -o "downloads/%(id)s_%(section_start)s-%(section_end)s.%(ext)s"
  ```
- **格式选择**：
  - YouTube：默认最佳 ≤1080p 往往是 **AV1**。若下游要 FFmpeg 重剪/拼接，AV1 解码慢，改用 H.264：`-f "bv*[height<=1080][vcodec^=avc]+ba"`。
  - B站：4K 流是 AV1 + 单声道音频；想要立体声选 1080P：`-f "bv*[height<=1080]+ba"`（实测张韶涵《大小孩》4K 流为 mono）。
  - **B站「修复版」常是 Live 演唱会版本，不等于棚版 MV**：搜结果里 "修复版" 头条往往清晰度更高（甚至 4K60 杜比视界），但内容与官方棚版 MV 调性差很多。**选源先匹配 brief 意图，再看分辨率**——brief 要"原版 MV 棚拍"，就别被 1080P Live 修复版替换走。
  - **「李荣浩 直拍」「XX 直拍」类搜索常返回别人**：B站标题党严重，多个 "李荣浩直拍" 实测是红发青年乐手，不是本人。当事人特写要找具体节目源（《我是歌手》《天赐的声音》《歌手》等综艺纯享版，或本人确认的官方 Live），由代理先核官方元数据、逐帧抽图和 ASR/节目上下文；无法证实就换源，不把普通身份核验变成用户确认点。
- **源信息记录**：每条入选素材在 `project-manifest.json` 绑定双平台候选、selection 与脱敏 download receipt；`SOURCES.md` 记录人工搜索过程和取舍理由。receipt 记录 URL、下载时间、raw→clip 时间窗/时长与 SHA 派生链，但不复制 Cookie、HTTP headers 或 yt-dlp 原始 `info_json`。

## Bash / 后台任务

- **后台 bash（`run_in_background`）不继承前台 cwd**：foreground 用 `cd` 切到子目录后跑 bg 命令，bg 命令仍在调用时的 cwd（项目根）。**bg 命令一律用绝对路径**，相对路径会 silently fail。
- **zsh nomatch 失败终止脚本**：`rm renders/work-*` 在没匹配时 zsh 默认报错并退出（bg 任务以 exit 1 结束）。改写 `rm -rf renders/work-* 2>/dev/null` 或 `setopt -u nomatch`。
- **bg 任务空文件 ≠ 完成**：`until [ -f X ]` 在 ffmpeg 创建空头文件时立即满足条件→提前退出。判完成用文件大小 `[ "$(wc -c < X)" -gt N ]` 或 ffprobe 能解析。

## 多 Goal 并发与单进程资源预算（硬约束）

- **多个 goal / 所有 goal 同时推进**：禁止用跨 goal `flock`、全局 semaphore、任务队列、sleep 轮询或“前一个完成后再启动”的方式控资源。不得让一个 goal 因另一个 goal 正在 render / ASR / TTS 而进入应用层挂起；只允许限制各自进程的并行宽度，并消除同一 goal 内的重复计算。
- **启动时自适应预算**：Whisper/Torch/BLAS、重 FFmpeg 与 HyperFrames 都通过 `tools/video/resource_budget.py` 发布当前 PID + 启动身份后立即计数；当前只有 1 个重任务时用 4，出现第 2 个时新任务用 3，达到 3 个及以上时新任务用 2（`4 → 3 → 2`）。已经运行的进程保持启动时预算，不暂停、不动态改速。PyTorch inter-op 默认仍为 1。
- **显式覆盖优先但仍可见**：手动覆盖范围统一为 1–4，只允许 `CC_MEDIA_ASR_THREADS=1..4` / `CC_MEDIA_ASR_INTEROP_THREADS=1..4`、`CC_MEDIA_FFMPEG_THREADS=1..4`、`CC_MEDIA_HYPERFRAMES_WORKERS=1..4`，或 HyperFrames 命令中唯一一个 `--workers 1..4`；显式覆盖的任务仍登记 active，供其他 goal 自动收敛。`0`、`auto`、重复 `--workers` 和大于 4 全部拒绝。
- **标记不是锁**：私有临时标记不写 slug、路径、prompt 或媒体信息；注册表没有 flock/semaphore/queue/wait/sleep。后续进程用操作系统 PID + 启动时间清理 SIGKILL 残留和 PID reuse；注册表不可读写时直接回退 2 线程继续，不能把预算探测失败变成 goal blocker。
- **入口不可绕过**：视频任务不得直接调用裸 `whisper` / `whisper-cli`；使用 `tools/video/vocal_segments.py`、`tools/video/offline_asr.py` 或中央 FINAL preparer。Qwen worker 启动前必须用不 import MLX 的 Metal preflight；当前执行上下文无 Metal 时快速退出当前 TTS 步骤并按 goal 自恢复协议切换到具备权限的执行上下文，不得先触发 native abort，也不得用全局锁把多个 Qwen goal 串行化。
- **FINAL 只做一轮重活**：标准 structured 流程由 `prepare_final_qa.py` 在同一进程生成 ASR/抽帧后立即运行中央机械 gate，并复用本轮只存在于内存、且绑定当前 path/SHA/参数的 evidence；standalone `verify_final_video.py` 仅用于显式独立复核或诊断。默认 preparer 已 PASS 后禁止立刻再跑 standalone verifier，避免重复 Whisper、逐帧 decode、SDR、black/silence 和 loudness。


## HyperFrames composition 规范

- **版本固定**：新项目统一 pin `hyperframes@0.6.69`，并把精确版本写入项目 `package.json` 与 lockfile/scripts；命令使用项目自己的 `npm run ...`，或显式 `npx --yes hyperframes@0.6.69 ...`。禁止省略包版本，也禁止使用浮动的 latest tag。历史项目继续使用其自身已提交的精确 pin/lockfile，不为追新自动改版本；只有显式迁移并重跑 lint/render/终片 QA 才升级。
- 渲染链路已验证：`init --example blank` → 编辑 `index.html` → `npm run check` → `npm run render`，产物 1920x1080 h264 30fps MP4。
- 每个计时元素必须 `class="clip"` + `data-start`/`data-duration`/`data-track-index`；timeline 须 `paused` 并注册到 `window.__timelines["<composition-id>"]`。
- 只允许确定性逻辑：禁用 `Date.now()`、`Math.random()`、网络 fetch（否则渲染不可复现）。
- **写/改 composition 前先读仓库 `AGENTS.md`、本文件和 `tools/video/README.md`，并使用当前任务适用的 HyperFrames skills**；不要依赖历史项目内另存的一份 `CLAUDE.md` 规则副本。
- **画布尺寸 / 帧率**：新启动的自媒体视频默认竖屏 `1080×1920 / 30fps`；只有 brief 明确要求横屏或其他交付规格时才改变，并把规格写入项目 manifest/design。blank 示例的 1920×1080 不是成片默认。
- **composition-id**：使用项目 slug 的 `kebab-case` 稳定 ID；重渲同一 composition 不随日期、进程或输出文件名变化。
- 动画库默认选型（GSAP / anime.js / …）：blank 默认 GSAP。
- **字幕 / 包装**：不设跨选题强制视觉模板；每期由 `design.md` 固定样式。旁白字幕默认禁止，只有用户明确要求才创建；片尾口播必须使用本文件「固定结尾配音」定义的 canonical CTA。

## 全链路（footage 进 composition）— 已验证

`sandbox/clip-demo/` 跑通：yt-dlp 切片 → HyperFrames `<video>` footage + 标题/字幕叠加 → MP4（h264 + aac，含原片音轨）。要点：

- **素材与 `index.html` 同目录**（`clip.mp4` 放项目根），`src="clip.mp4"` 相对引用。
- **视频**：`<video muted playsinline>`，计时属性(`data-start`/`data-duration`/`data-track-index`)**直接放在 video 元素上**，不要套进计时 div。全屏用 CSS `position:absolute; inset:0; object-fit:cover`。
- **音频独立**：原片声音用单独 `<audio src="同一个mp4">`，否则成片没声音。
- **层级靠 CSS `z-index`**，`data-track-index` 不决定视觉层级（footage z-index:0，叠加层更高）。
- **动画只碰视觉属性**，不要 `video.play()`；timeline `paused` 注册到 `window.__timelines["main"]`。
- **字体**：正式成片首选把有明确授权的 `.woff2` 放进项目 `fonts/`，用相对 URL 的 `@font-face` 锁定字形；禁止依赖渲染时网络请求或远程字体自动下载。`local()` 只允许在明确锁定本机/OS、记录字体名称且不要求跨机复现的历史或本机专用项目中使用。
- 渲染日志里 `[non-blocking] ... 404` 无害，可忽略。
- 10s/1080p 含 footage 渲染约 31s（blank 纯图形那条仅 6s，footage 更慢）。

## 多段旁白时间轴（用户明确要求字幕时才同步）— 历史验证

`sandbox/pipeline-demo/` 曾跑通“分句旁白 + 同步字幕”，但当前默认禁止自定义旁白字幕。下面只复用音频排轨；字幕相关步骤仅在用户明确要求旁白字幕时启用。

- **分句配音**：任务启动时只解析一次 `voice-selection.json`；各句用 `tools/tts/narrate.py --selection-file ...` 批量生成并复用同一角色，拿到各自时长后再排时间轴。
- **顺序排轨**：多个 `<audio>` 放同一 `data-track-index`，按累计时长设 `data-start`（句间留 ~1s 间隔更自然），互不重叠即可。
- **字幕（仅用户明确要求时）**：每句一个 `class="clip"`，`data-start`/`data-duration` 与对应音频一致；否则一律不创建旁白字幕层。
- **轨道分配**（`data-track-index` 不管层级，层级用 z-index）：footage=0、压暗 scrim=1、字幕=2、音频=3、片头/片尾=4。同轨元素时间不能重叠（scrim 跨全程要独占一轨，否则和片头片尾撞）。
- 用脚本程序化生成 `index.html`（读 `narration.json` 算时间轴）比手写多段更稳。
- **footage 关键帧坑**：yt-dlp 下来的片段关键帧可能稀疏（GOP 数秒），HyperFrames 逐帧 seek 时告警、可能卡顿。实测短片未见冻结，但正式成片建议先重编码加密关键帧：
  ```bash
  ffmpeg -i in.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 -movflags +faststart -c:a copy out.mp4
  ```
- CJK 系统字体曾在当前机器验证可用，但 `PingFang SC` 等 `local()` 字体不构成跨机可复现资产；新项目仍按上条优先提交有授权的项目内 WOFF2。

## 自媒体视频（通用能力与默认）

> ⚠️ 不要思维定势：成片**不止 TOP 盘点**，也有不区分排名的形式（人物/歌曲解读、主题串烧、科普合集等）。下面是**跨格式通用**的能力和默认；具体"格式"只是呈现方式，按当期任务定。

**通用默认**：只有某一条自身明确写出可覆盖条件时，单期 brief 才能覆盖该条默认；标为“硬约束”或由门禁执行的规则不能被一句临时提示词降级。
- **画幅**：竖屏 **1080×1920**（短视频主流）。
- **素材来源**：默认**我来搜并选**——用户给歌手+歌名/主题+倾向，我**同时在 YouTube 和 B站搜**（见"素材源平台"硬约束）。先保证目标歌手/版本身份正确，再优先官方 MV；官方 MV 画质稍差也不因此降级。拿不准的版本先给候选并标明各平台候选规格。
- **解说文案**：默认**混合模式**——用户写重点句/必须准确的点，其余我扩写成口播稿，出片前可审。
- **配音**：新盘点若无唯一精确指定，则从 `CV001 / CV002 / CV003 / CV004 / CV005 / CV008` 女声池随机一次；编号、正式名称或注册别名的唯一精确指定仍优先（见配音规范）。
- **旁白结构与重心**：一般视频默认包含**开头旁白 + 每首歌曲转场旁白 + 作品 outro + 固定 CTA**，四类旁白共用项目级音色。完整只指结构不缺项，不表示每段都要展开：`intro` 集中建立主题、评判标准与钩子且不泄榜，作品 `outro` 集中给整体结论；逐首转场只保留首次揭晓与一个不可替代的判断。新项目使用 authoring manifest schema v2，TOP 转场实际 WAV 目标 4–6 秒、硬上限 8 秒，非排名叙事转场目标 6–8 秒、硬上限 10 秒；超限必须先删减，不得靠拉长歌曲展示免责。只有完全自由探索类、以音乐/视觉实验本身为主体且没有排名或解说结构的视频，才可在 brief/design 明确记录后按创意精简部分或全部旁白；brief 没写旁白不构成省略理由。
- **整体节奏 / 时长**：默认**不设总时长上限，整体质量优先**。除非用户明确给出平台硬时长，不得为了变短牺牲叙事、观赏体验或完整乐句；确有硬时长时优先减少条目、收紧重复信息或精简旁白，不得把歌曲高光从句中掐断。
- **审美**：开期先定一份 `design.md`（配色/字体/动效基调）并全期统一，参考 `/hyperframes` 的 design 流程。默认"干净高级、暗底 + 单一强调色"，除非指定综艺花字等其他风格。
- **结构通用件**：footage（`<video muted>`）打底 + 大字标题/信息卡（rank 卡 / cover / outro）+ 片头片尾；原声可作 BGM 并按下面 ducking 处理。
- **信息层级去重**：同一个语义只保留一个主标识源，尤其是排名 / 序号 / 歌名。若画面已有"第X首 + 歌名"标题，就不要再叠右上角流水号、左上角浮层 bug、二级角标等同类元素；进入 full-music 展示段后，除非用户明确要常驻信息条，否则排名/歌名浮层应淡出，避免压住 MV 也避免重复标记。QA contact sheet 必须专门看一遍是否有同义元素堆砌。

### 禁止自定义旁白字幕（硬约束）— ⚠️ 用户多次反馈，**默认必须遵守**

- **禁止**在成片里加任何**自定义旁白字幕 / 解说文案字幕条**（把 TTS 口播内容再叠成底部字幕卡）。
- **包括但不限于**：开场旁白字幕、每首转场旁白字幕、outro / CTA 旁白字幕、`CAPTIONS` 字典驱动的 `class="clip caption"` 条、把旁白逐句做成 on-screen text。
- **原因**：多余、挡画面、与 rank 卡信息重复；一旦某期加了，后续模板会错误复用。
- **允许的画面字**：设计层信息卡（封面标题、排名卡歌名/点评、mini 标签、片尾目录/CTA 浮层），**不是**旁白同步字幕。
- **唯一例外**：用户在 brief 里**显式**要求"加字幕 / 加旁白字幕 / 加字幕条"。未写 = 不加。
- QA：抽帧确认无底部口播字幕条；`index.html` 不得出现旁白字幕用的 `class="clip caption"`（或等价实现）。

### 展示段硬规则（竖屏画面比例 + 副歌时长）— ⚠️ 用户多次反馈，**默认必须遵守，不要再犯**

**(A) 竖屏化默认 = letterbox 保原比例，禁止激进裁切放大。**
- **默认**：footage **全宽呈现、保留 MV/Live 原始横纵比**（信箱式：fg 缩到 1080 宽居中、上下用模糊背景填充），**不放大画面**。只裁掉烧死歌词/台标/水印的**横向窄带**（全宽保留）。
- **禁止**：把画面裁成竖条再放大贴宽——会把主体裁出画 / 只剩半边。**男女合唱 / 双人 / 多人 / 宽机位**素材尤其禁止（两个主体分布在画面左右，任何竖裁都会切掉一个人）。
- **历史兼容例外，不是新项目默认选项**：既有工程若已批准“单主体全程稳定居中”的竖向裁切，可按其自身 design/pin 复现；新项目只有用户明确要求该构图、并对完整候选窗逐帧确认不切主体后才能采用，且须在 design/QA 留证。拿不准或只是为了“更满”一律 letterbox。
- 实现：复用 `tools/video/vfill.sh`——把 crop 传**全宽横带**（`W=源宽 : H=裁掉烧词后的高度 : 0 : Y`）即得 letterbox；传**窄竖条**才是放大裁切（默认别这么做）。
- "清晰度 / 画幅没源那么满"可接受（用户已确认）；"人物被裁半 / 看不全"**不可接受**。

**(B) 展示段 = 一段连续副歌（含前后余量），不要碎镜快闪、不要把歌切短。**
- 每首给**一段连续**的副歌 / 代表段，**前后都留余量**（前奏带入 + 副歌 + 收尾），让观众"听得爽"。
- **先压旁白，再定展示时长**：不得旁白讲很久、歌却随便放一小段就跳过，也不得为了让比例看起来合理而把超限旁白对应的歌曲机械拉长。逐首转场先按下文的实际 WAV 上限删到只剩一次揭晓和一个判断，再独立按完整乐句确定展示时长。解说盘点类单首展示 **≥ ~25s**（甚至更长，**不设上限，以观赏体验为准**）。历史 60–90s 短榜单及其 12–18s 切片只是旧项目局部方案，不是新项目默认；若用户明确给出平台硬时长，应优先减少条目和重复信息，任何保留段仍只能落在完整乐句边界。
- **优先「连续整段 + letterbox」**：让 footage 窗 == 音乐窗（同源同窗）→ 口型天然同步，且 MV 自身的内部剪辑照常出现没问题。**不要**默认把多个碎镜头拼成蒙太奇。
- **「歌手镜头蒙太奇」仅作救场**：当连续段实在不可用（全程拍不到主体 / 大量空镜 / 烧字裁不净）时才拼，且救场段也要够长、并逐镜抽帧验证。
- QA：抽帧确认长 clip **播放到末尾无黑屏 / 冻结**（`<video> data-duration ≤ clip 实际时长`，clip 切到 SHOW+余量）；各首副歌响度一致（~-15dB）。

**(C) 展示段两条入/出对齐硬规则 — ⚠️ 用户实测反馈，反复犯，已机械化闸门强制（见文末「展示段对齐闸门」）。**

> **入点（问题1）**：副歌人声要在**转场配音快收尾时正好进来**并贯穿展示段，别让副歌被旁白盖走、推满音量的展示段落到纯器乐。
> **出点（问题2）**：展示段结尾要落在**唱完一句之后或纯器乐 gap**，**绝不因时长限制把一句唱到半路硬切**（人声戛然而止，观感最差）。

切片时**必须把转场配音的时间差算进去**。每首结构是：`短转场旁白（音乐 duck 成床）→ 消化位/swell → full-music 展示段`。旁白占用片段开头 `LEAD + voice_dur` 秒；历史约 15–19 秒的长转场只用于复现旧工程，不是新项目默认。新项目必须先让实际 WAV 通过 TOP ≤8 秒 / 非排名叙事 ≤10 秒的 authoring gate，再按真实 `voice_dur` 计算切点。**问题1 的坑：把唱的副歌放在了片段开头，结果整段副歌都被旁白盖住，旁白一结束、音量推满的展示段反而落在了间奏/前奏/outro 纯器乐段——观众真正想听的"炸点"全程没人声，只剩背景乐。**（华晨宇期 斗牛九周年：副歌"野性坦露"在旁白下，展示段是管弦 outro；烟火：展示段落在 30s 间奏。用户一耳听出。）

- **对齐原则（理想）**：让一段连续唱的副歌 **在转场旁白结束前约 2 秒入声**（vocal onset），唱声先在旁白尾巴下起来，再随 swell 推满进展示段——既丝滑、展示段又全程有唱。
- **切片公式**：`clip_start_src = vocal_onset_src − (LEAD + voice_dur − 2)`。即把"副歌入声"对到 segment-local 时间 `narr_end_local − 2`。（`full_start_local = LEAD + voice_dur + 0.25 + DIG`；展示段 = `clip_start + full_start_local` 起的 `SHOW` 秒，必须整段落在唱的区间。）
- **时长只定下限，不定硬切上限**：视频总时长不是切歌上限。某首完整副歌/演唱高光需要 35s、45s 或更长，就按自然乐句保留，不得为了压总时长缩短该首或强行掐断。从目标时长起只向后寻找完整乐句出点；候选 gap 后 3s 内还有下一咬字，就把下一小句一起吞完。若源本身只有一段 22–26s 的完整副歌，可把 SHOW 收到该句的已确认安全边界；不得为了凑固定时长切字，也不得为凑长拖进纯器乐。
- **变量命名防误用**：如果 build 脚本使用 `show_start` / `W` / `highlight_start` 这类字段，它必须表示**成片 full-music 展示段开始时对应的源时间码**，不是"这首歌从哪开始切"，也不是"副歌大概从哪开始"。实际预切起点应由脚本倒推：`media_seek = show_start - full_start_local`。改完必须抽成片 `full_start` 后 20-30s 的 contact sheet，确认画面歌词/口型已经进入人声段。
- **怎么判“目标歌手在唱”（关键，单一方法都不可靠）**：
  - 旧 HPSS + 200–3000Hz 能量只能叫 `candidate_segments`：萨克斯、吉他、合成器、观众合唱都会命中，**任何曲风都不能仅凭它自动 OK**。
  - `vocal_segments.py --mode multi` 组合：Whisper 有效歌词密度和 word timestamps、固定字幕/credit 幻觉过滤、声学候选重叠、stereo mid/side 中心性。强一致才写 `lead_segments + evidence_level=multi_evidence`；单声道、宽混音对唱、观众/合唱风险或证据冲突写 `REVIEW`。
  - Live / 演唱会 / 观众明显的源必须传 `--source-kind live`。在 crowd/choir 事件模型尚未接入前，Live 即使歌词和中心性都强也保持 REVIEW，防止整齐观众合唱假绿。
  - `no_speech_prob` 只记录；`avg_logprob` 只能与极低 word probability 组合成“低置信冲突→REVIEW”。两者都不能单独判唱声：历史真唱的 no-speech 可高于假群声。
  - 烧死卡拉 OK 歌词“逐句推进”只能作辅助证据，静态 lingering 歌词不是唱声。普通 goal 拿不准时严格按 **multi → 换窗 → 换源** 恢复，不得首次 REVIEW 就要求用户耳验。该路径确已穷尽且硬 `FAIL=0` 后，本地才可以绑定当前 hash/窗口的 `reviewer_kind=agent` 工具辅助观察闭环为 `OBSERVED`；它不是真人批准。只有用户已经明确进行了逐曲听音，才可写入 `reviewer_kind=human` 的人工批准记录，代理不得代签 human。
- **出点对齐（问题2，硬规则）**：`show_end_src` 落在 active word/唱声中，只容忍 0.12s 分帧误差，直接 `FAIL`。落在 gap 也不能立刻算安全：尾音后至少留 0.30s，且向前看 3.0s；若下一 onset 很快出现，视为句内气口并继续向后吞句。Whisper 自动生成的 `safe_cut_intervals` 仍必须通过 3s 前向保护；只有显式 `manual/verified` 乐句证据可覆盖这条启发式，而且任何证据都不能覆盖“仍落在 active 唱声中”的硬失败。
- QA 收尾：成片对每首展示段（旁白结束后那 30s）抽查确实有人声，不是只有伴奏；并核展示段最后 2s 是收在句末/器乐，不是切在唱字中间。

**🔒 展示段对齐闸门（机械化强制，build 不过就不出 master）— 反复犯 → 不再靠人肉算。**

`tools/video/showcase_align.py`：使用多证据 `vocal_analysis.json` 校验上面两条，状态为 `OK / OBSERVED / APPROVED / REVIEW / FAIL / MISS`。本地模式的 `OBSERVED` 只来自显式 `status=observed, reviewer_kind=agent` 记录；`APPROVED` 只来自真人记录。发布模式追加 `--require-human-review` 后不接受 `OBSERVED`。旧能量数据不会再假绿，硬 `FAIL` 不能被任何记录覆盖。它把“凭感觉填 `ch_off/show`”变成可验证、可审计的闸门。

- **接入（build 算完 blocks、建 master 之前，一行）**——`countdown_build.py` 模板已内置，复用 `full_build.py` 时照抄：
  ```python
  import sys; sys.path.insert(0, str(ROOT.parents[2]))   # 让 tools 可 import（ROOT=项目目录）
  from tools.video import showcase_align
  showcase_align.gate(blocks, ROOT/"probe"/"vocal_analysis.json",
                      consts=dict(POST=POST, DIG=DIG), plan_path=ROOT/"probe"/"showcase_plan.json")
  ```
  `blocks` 每首需含 `clip/start/narr_end/full_start/end`（可选 `mseek`=预切 `-ss`）。闸门自动换算源时间码：
  `narr_end_src=mseek+(narr_end-start)`、`show_start_src=mseek+(full_start-start)`、`show_end_src=mseek+(end-start)`。
- **前置**：build 前跑 `tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json --mode multi --language zh`（按歌曲实际语言调整；时间基准 = 各 vert clip 源时间）。正式 build 用 `--mode multi`；模型缺失只让当前分析步骤退出，代理修复固定模型/runtime 后重跑，不得静默退回能量候选，也不得因此停止整个 goal。
- **反推切点（别手填）**：拿不准 `ch_off`/`show` 就让工具算：
  ```bash
  tools/tts/venv/bin/python tools/video/showcase_align.py plan \
      --vocals probe/vocal_analysis.json --clip vert_p4_wait --voice-dur 14.0 --near 105
  ```
  它按“人声入点 = 旁白收尾前 2s”给 `ch_off`，从 ≥25s 目标开始只向后找完整乐句；推荐值还会走同一个 `verify_song()` 自检，自己判 FAIL 的值不会提示写入 build。
- **单独复核**（QA 阶段）：`showcase_align.py check --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json`，要求 `FAIL=0 REVIEW=0 MISS=0`。工具不自动读取同目录记录；需闭环 REVIEW 时必须显式追加 `--approvals probe/showcase_approvals.json`。本地 agent observation 必须是 `status=observed, reviewer_kind=agent`；真人记录必须是 `status=approved, reviewer_kind=human`。两者都要非空 reviewer、带时区 `reviewed_at` 并绑定当前窗口与 analysis hash；发布模式必须追加 `--require-human-review` 且只接受 human。
- **REVIEW 恢复顺序**：普通 goal 严格按 **multi → 换窗 → 换源** 恢复，优先得到机器 `OK`；不得把 pending 骨架当成等待用户的默认分支。只有该顺序确已穷尽且硬 `FAIL=0` 时，才可留下 hash/窗口绑定的 agent observation，并且结果必须叫 `OBSERVED` / local-only，不得叫 human / `APPROVED`。`showcase_align.py approval-template` 仍只供用户人工复核；代理不得把该 pending 模板改为 human approved。任一输入变化都使记录失效。
- **禁止全局逃生**：`SHOWCASE_OVERRIDE` 已废弃。逐曲批准只能解决证据不足的 REVIEW，不能覆盖 active word、短气口等硬边界 FAIL。

> 验证项目：`sandbox/zwtl-duet-pk/`（周王陶林男女合唱PK，4:25）。早期用竖裁放大→双人被裁半、副歌 14s 太短被吐槽；改 letterbox 全宽 + 连续 27–32s 副歌后达标。
> 验证项目：`sandbox/huachenyu-hardest-top5/`（华晨宇最难5首）。初版 4/5 首展示段落在器乐段（唱声全被转场旁白盖住），按 (C) 重对齐 vocal onset 到旁白收尾前 2s 后修复。

### 冷启动执行：从 brief 到成片

新窗口接到视频 brief，照 **`tools/video/README.md` 的 Runbook** 跑；不要复制旧章节编号，因为 Runbook 会随门禁扩展。复用源码都在 `tools/`，当期输入和生成物才放可丢弃的 `sandbox/<slug>/`：
- `tools/tts/narrate.py`、`tools/video/narrate_segments.py` — 配音
- `tools/video/vfill.sh` — 竖屏填充
- `tools/video/countdown_build.py` — 音轨 + 合成构建模板（按 brief 改 songs/时长/文案）

**四门禁顺序（标准盘点 / 叙事 / 自由探索项目不可调换）：**

1. **VOICE GATE**：解析一次 `voice-selection.json`、用中央入口生成全部旁白后，运行 `tools/tts/verify_voice_usage.py`。它证明 selection、sidecar、模型/reference 声明和当前 WAV/path/hash 在本地诚实工作流中一致；不证明旁白已混入终片、实际可听或音色来源具有对抗性证明。
2. **PROJECT CONTRACT**：任何 build 写 `master.wav`、HTML 或其他产物前，运行 `tools/video/verify_project.py --project sandbox/<slug>`。它证明结构、TOP 顺序、旁白绑定、逐曲 evidence、双平台来源声明及本地下载派生链满足门禁；不联网认证上传者/“官方”身份，也不证明最终画面或听感。
3. **PUBLISHING COPY**：只在 build、HyperFrames render 与 post-mux 已完成后生成 `publishing/xiaohongshu.md`，再运行 `tools/video/verify_publishing.py`；它在 FINAL 前执行，不得提前塞进 build 前的 `project-manifest.json` 门禁。只有 `PUBLISHING COPY: PASS` 才能继续交付。
4. **FINAL VIDEO QA（默认本地机械终验）**：HyperFrames 画面 render 后，用预混 `master.wav` 完成 post-mux。raw render 与 mux 后 final 都必须位于 `renders/`。对有 intro / song / outro / CTA timeline 与完整旁白的**标准结构化盘点/叙事项目**，调用中央 `tools/video/prepare_final_qa.py`，由它从当前 timeline、authoring manifest、final、render 与 master 生成 `qa/final-video-qa.json`、实时 ASR artifacts、逐章无损抽帧和机械诊断，并在同一进程内调用中央 FINAL gate；不得跳过 preparer 手写或复制旧 QA manifest。该命令输出 `FINAL VIDEO QA: PASS` 即完成默认机械终验，不再紧跟第二次 standalone verifier。`verify_final_video.py` 仍保留为显式独立复核/故障诊断入口，独立运行时继续 live 重算而不信任项目内自报 diagnostics。默认不要求真人代签，机械通过即可完成普通视频 goal。pending human review、需要人判断的自然黑淡变或语义项保存在 QA 文件中，不把普通 goal 标记为 `blocked`，默认交付只报告 advisory 数量。只有用户明确要求公开发布、发布验收或可发布交付时，才由真人完成 preparer 生成并绑定当前 final SHA 的 `qa/human-review-input.template.json`，再以 `--human-review-input` + `--require-human-review` 重新 prepare 并完成严格终验。`project_kind: free_exploration` 不得强套这个 structured preparer，仍按其当期 project/final schema 准备 QA；AI 音色 MV 继续走 durable builder 与独立 `--check`。所有模式都不能冒充工具理解了画面美感、水印语义或最佳高光，也不能伪造 `reviewer_kind: human`。

```bash
python3 tools/tts/verify_voice_usage.py \
  --selection sandbox/<slug>/voice-selection.json --project-root sandbox/<slug>
python3 tools/video/verify_project.py --project sandbox/<slug>
# build → 在项目目录用 resource_budget.py hyperframes wrapper + --sdr 自适应 render 到 renders/full.mp4 → 用 master.wav post-mux
python3 tools/video/verify_publishing.py --project sandbox/<slug>
python3 tools/video/prepare_final_qa.py \
  --project sandbox/<slug> \
  --final renders/<slug>.mp4 --render renders/full.mp4
# 上一命令已在同一进程运行中央 FINAL gate；不要默认重复执行 standalone verifier。
# 只有显式独立复核/诊断时才运行：
# python3 tools/video/verify_final_video.py \
#   --project sandbox/<slug> --manifest qa/final-video-qa.json
# 仅当用户明确要求发布级终验，且真人已完成当前 SHA 模板时：
python3 tools/video/prepare_final_qa.py \
  --project sandbox/<slug> \
  --final renders/<slug>.mp4 --render renders/full.mp4 \
  --human-review-input qa/human-review-input.json \
  --require-human-review
# strict gate 已由上一条 preparer 在同一进程执行。
```

VOICE、PROJECT、PUBLISHING 或 FINAL 的机械红线失败都回到其输入修正，禁止先产出再补写 evidence，或把下游 PASS 当成上游豁免。默认本地终验中的 human-review advisory 不是机械失败，也不是 goal blocker；显式 `--require-human-review` 返回 `REVIEW_REQUIRED` 才表示发布终验仍待真人。AI 克隆整首 MV 不冒充这套标准 project/final schema，按 `tools/video/templates/ai-voice-mv/` durable builder 的 `--check` 与独立 QA 边界执行；其输出仍按并列目录生成发布文案，但当前 AI config 缺少标准 performer/theme 上下文，不能伪造 `project-manifest.json` 冒充通过标准 PUBLISHING CLI。

**小红书发布文案（硬约束）**：每个完成型新 Sandbox 项目必须创建与 `renders/` 并列的 `publishing/`，固定文件为 `publishing/xiaohongshu.md`。文案不是终片简介或制作日志，而是一篇无需再改写即可发布、能让对应兴趣圈层愿意读完和回答的完整笔记。

- **先定受众兴趣，再写文案**：写作前核对本期真实主题、歌手、选题角度、旁白和最终内容，并结合当期公开社区讨论或可靠资料，提炼 1 个中心判断和 2–3 个受众真正关心的入口。单歌手项目优先写声音、人格或职业转向；现场项目写台上台下的共同经历；动漫、影视和游戏项目写可验证的时间坐标、作品机制与圈层记忆；怀旧项目不能只说“青春回忆”，必须说明今天为什么仍值得重听。调研只决定切入角度，不能把未经项目证据支持的热搜说法、粉圈传闻或流量判断写成作品事实。
- **标题要有判断，不做标题党**：提供 1–5 个候选，默认 3 个，第一条就是首选。优先使用本期真实矛盾、反差或新判断建立吸引力，禁止靠与正文无关的热词、情绪勒令、无法证明的绝对化词语或“封神/全网第一/不看后悔”等空洞夸张吸睛。三个默认候选应覆盖不同切口，不能只是替换同义词。
- **正文必须形成完整推进**：hashtags 前的正文固定为 **420–900 个非空白字符**，建议 6–10 个短段落。结构至少包含“具体入口或大众印象 → 本期中心判断 → 2–3 层有项目依据的展开 → 为什么值得今天重看/重听 → 一个具体互动问题”，不得把 timeline、人物名单或制作说明改写成流水账。互动问题必须能让对应受众回答具体记忆、选择或判断，禁止只写泛化的“你怎么看”。
- **全部对外文字禁用 emoji**：标题、正文、互动句和 hashtags 都不使用 emoji；不要用耳机、眼睛、火焰、爱心等符号代替语气、段落逻辑或真实表达。
- **hashtags 固定 8–10 个且各司其职**：文件最后一行必须是 hashtags，只放 8–10 个互不重复的标签。优先组合“核心人物/IP 1–2 个 + 垂类/题材 2–3 个 + 本期独特角度 2–3 个 + 有真实关联的圈层/年代 1–2 个”；不得只堆 `#音乐 #音乐分享 #音乐推荐` 一类可替换到任意作品的泛词，也不得为凑数加入正文没有涉及的人物、作品、年代或热点。
- **不剧透且不杜撰**：标题候选、正文、互动句和 hashtags 的全部对外文字都不得出现本期任何歌曲名称。全文必须与本期作品强相关，不得使用可替换到任意项目的泛化模板，不得杜撰作品事实。

具有标准 `project-manifest.json` 的盘点、叙事与自由探索项目，完成后运行 `python3 tools/video/verify_publishing.py --project sandbox/<slug>`，必须得到 `PUBLISHING COPY: PASS`。门禁会机械检查结构、正文长度、具体互动问题、emoji、8–10 个唯一 hashtags、歌曲名剧透和项目关联性；它不替代事实核对与编辑审美。这一门禁发生在 build/post-mux 之后、FINAL 之前，不改变 `project-manifest.json` 的 build 前职责；专用 durable 流程不得为调用该 CLI 伪造标准 manifest。

**Sandbox 成片交付收尾（硬约束）**：新项目的 raw render 和 mux 后最终 MP4 只能写在 `renders/`；最终交付固定为 `renders/<slug>.mp4`，禁止使用 `final/`、`output/`、项目根终片或其他目录。普通成片的最终回复同时报告 `renders/<slug>.mp4` 与 `publishing/xiaohongshu.md`、最终 MP4 当前 SHA、VOICE / PROJECT / PUBLISHING / FINAL 四道门禁结果、实际修复和确实影响成片的问题。发布文案是必需内容产物，不属于被禁止的“未来发布建议”；内部 pending、review template 和严格模式入口留在 QA 文件与 Runbook 中。仍不得自动附加用途定位、权利或条款免责声明、额外真人复核建议。只有用户在当期任务中主动询问相应主题时才回答，且不能把这类提示写进 `QA.md`、`SOURCES.md`、README、checklist 或 CLI 默认输出。

### Goal 自动恢复与真正阻断边界

内部步骤首次失败只停止当前步骤，不停止整个 goal。统一执行“**诊断 → 修复 → 重跑**”：保留错误、当前输入与 hash，先判断是素材、环境、配置还是产物问题；在不改变 brief、不伪造 evidence、不降低 gate 的前提下修复，或使用本文件已经验证的替代路径；然后从最近失败步骤继续，并重跑所有受影响下游门禁。不得因可自行修复的内部失败暂停、等待用户确认或标记 `blocked`；机械红线不得降级或放松。

- **必须自行恢复**：普通公开下载或单个候选失败就切换客户端、关键词、平台和同版本备选源；模型可安装或 receipt/runtime 漂移就修复固定环境；TTS/ASR/sidecar、render/mux、manifest/evidence 以及门禁 FAIL/REVIEW 都回到相应上游修正并复跑。下载、TTS、渲染或 QA 第一次非零退出不是用户 blocker。
- **展示 REVIEW 不等于等用户**：先重跑 `--mode multi`，调整切点与完整乐句窗，再换同版本官方 MV / 官方 Live / 另一平台干净来源，优先拿到机器 `OK`。不得由代理填写“人工 approved”，硬 FAIL 也不能批准覆盖；只有穷尽正确版本和安全窗口后，继续又必须改变核心 brief 时才进入下面的用户决策边界。
- **允许暂停的唯一窄边界**：用户明确要求小样或阶段确认；缺少用户独占的必需输入（如用户指定但未提供的 AI WAV）；已穷尽安全替代、公开双平台来源、备用 client 和安全重试后，仍需要模型无法取得的新凭据、权限或外部能力；继续必须改变歌单、排名、歌手版本、平台排除、硬时长等核心 brief；显式发布任务缺少真人终验。进入这些边界前必须记录已尝试方案并保留可恢复产物，不能把内部工具报错转嫁成用户确认；首次出现真实外部边界只请求必需输入/权限，不立即标记 `blocked`，只有同一外部阻断连续三次 goal turn 仍存在且无法继续时才可标记。

**用户 brief 的标准格式**（缺省项按本规范默认值处理）：
```
盘点主题/标题：
项目slug：
画幅：默认竖屏1080x1920 | 总时长：默认不设上限、质量优先；仅显式平台硬时长才限制
揭晓顺序：凡 TOP / 排名 / 榜单必须倒数 N→1；非排名叙事片才按脚本顺序，且标题不得写 TOP
悬念：TOP 封面/intro 不列完整歌单、不展示排序、不泄露第一名；每名在对应转场才揭晓
配音：默认从 CV001 / CV002 / CV003 / CV004 / CV005 / CV008 女声池随机一次；可写 CV 编号 / 正式名称 / 注册别名（唯一精确指定优先）
旁白结构：默认开头 + 每首歌曲短转场 + 作品 outro + 固定 CTA；信息重心放在开头/结尾，完全自由探索类可显式标注例外
每首：序号 / 歌手 /《歌名》
  素材：URL+切点 | 或 搜索倾向(官方MV/Live/原唱 + 想要的段落)
  旁白：逐字稿(照念) | 或 要点(我压缩为“首次揭晓 + 一个判断”)；TOP 实际 WAV ≤8s，非排名叙事 ≤10s
  字幕短标签：(可选)
开头文案与画面意图：(可选)
结尾文案：(可选，仅作品 outro 的内容总结/升华) —— 固定引流 CTA 自动追加为最后一句，brief 不写、不覆盖（见「固定结尾配音」硬约束）
```

### QA 方法论（我看不到画面、听不到声音 → 必须用工具验证，不能凭感觉说“好了”）

- **画面**：`ffmpeg -ss N -i v.mp4 -frames:v 1 f.png` 抽帧，用 **Read 工具实际查看**；多帧可 `hstack` 成 contact sheet。下载的每段素材也要先抽帧确认是真动态 MV、记录水印/字幕/画幅。
- **静音唯一口径（标准 post-mux 终片）**：以 `verify_final_video.py` 对 mux 后 MP4 的实时检测为机器真源。连续静音 `>1.5s` 在默认本地终验和发布终验中都一律 hard fail，不能由人工批准覆盖；`1.0–1.5s` 与跨 chapter boundary 的检测结果在默认本地终验中如实记录为非阻断 advisory，显式 `--require-human-review` 时才必须有绑定当前 final SHA 的真人 context。`blackdetect` 命中同理：默认记录区间供用户查看，发布终验才要求真人确认它是自然淡入淡出还是故障。小于 1.0s 不触发该机器门槛，仍应由代理通过波形和上下文检查是否突兀。禁止为绕过 gate 铺白噪音、brown noise、无关 ambient 或仅为抬过阈值的假音乐床；若停顿不合叙事，应从剪辑、旁白时机或与内容相关的真实音乐衔接修复。
- **响度**：用 `volumedetect` / loudness 检查各首副歌趋于一致、旁白段音乐明显更低；最终仍以 mux 后 AAC 为准。**绝不靠“应该没问题”下结论**。
- **泄漏**：确认成片画面内无水印/网址/提示词/路径/项目内部词（裁切 + 干净叠层）。
- **⚠ `ffmpeg -ss T -i x.wav ... volumedetect` 精确到零点几秒的窗口抽查可能不可信（2026-07 许美静最被低估5首验证）**：曾用它抽查 ducking 效果，测出"旁白段音乐几乎没被压低"的假警报（bed vs show 几乎同响度），一度怀疑 envelope/loudnorm 链路有 bug；改用 Python `wave`/`numpy` 按精确 sample offset 直接读取同一份 WAV，同一窗口测出的真实结果是 bed ~-46~-51dB vs show ~-11~-18dB（差 30+dB，ducking 完全正常）。根因是 `-ss`（无论放 `-i` 前后）在纯 PCM WAV 上的定位在某些环境下有明显偏差，对短窗口（<1s）尤其失真，但对秒级以上的粗粒度检查（如比较整段旁白 vs 整段展示段）误差不明显、不易察觉。**结论**：QA 阶段要做"零点几秒级"精确窗口的音量分析（如验证 ducking envelope 前几百 ms 是否真的压低），别用 `ffmpeg -ss` 抽查，改用 `wave`/`numpy` 按 sample offset 直接读取（或渲染后的 MP4 同样验证一遍，确认问题不是 mux 引入的）；`-ss` 抽帧做画面 QA、抽整段做粗粒度音量对比不受此问题影响，仍可正常使用。

### 旁白与音乐的节奏（硬规则，来自 wemedia/AGENTS.md 实战经验）

- **篇幅两头重，不把中段写成五篇短评**：开头负责主题、标准与钩子，作品 outro 负责整体结论；TOP 每首转场限一句，只保留“名次 + 歌名 + 一个判断”，目标 4–6 秒、实际 WAV 硬上限 8 秒；非排名叙事转场只保留“时间/作品节点 + 一个意义”，目标 6–8 秒、硬上限 10 秒。单首履历、多个数据点、社区评价与重复形容不能并列堆入同一转场；确有多个候选信息时只留最能解释入选理由的一项，其余删减，而不是整体搬到开头或结尾。
- **门禁看真实声音，不看字符数**：authoring manifest schema v2 由 `verify_project.py` 读取中央 VOICE gate 已验证的实际 WAV 时长并执行上述上限；schema v1 只为历史工程复现保留，不得用于新项目绕过节奏门禁。中段配音占单首章节约 20% 可作为编辑自检，但比例不能替代绝对上限，也不能靠延长歌曲刷过。
- **先配音，后进音乐**：章节/开场的介绍旁白先讲，期间音乐**最多是低音量床**（或无），不要一上来 voice+music 同时全量"轰炸"。**真正全量的音乐留给无旁白的副歌/展示段**。
- **旁白收尾留消化位**：每段介绍旁白讲完保留 **0.8–1.2s** 缓冲再切歌/进下一段；不得最后一个字刚落就硬切。需要声音支撑时只用与内容相关的音乐淡入或素材预入声，不以噪声/无关底床填门禁。
- **章节交界**避免出现"配音停 + 音乐未起 + 画面静止"的无意空等；有叙事意图的停顿仍按上面的统一静音阈值进入默认本地 advisory、发布 REVIEW 或 hard fail，不因位于交界而绕过实时检测。
- 典型每首结构：介绍旁白（音乐床）→ 消化位（床淡入/swell 起）→ 副歌展示（音乐全量、无旁白）。
- **QA**：成片运行终片 gate；单独排障可用 `ffmpeg -af silencedetect=n=-35dB:d=1` 观察区间，但不得用手工命令结果替代 gate manifest、当前 hash 与实时检测。默认本地终验把需要真人判断的区间保留为 advisory；显式发布终验的人工 context 必须绑定当前 final SHA。另抽测旁白段 vs 展示段音乐音量确认有明显高低差。

### 多段成片的实战经验（张韶涵暗黑面全片验证）

- **全片响度统一**：不同歌曲源响度差异大（实测副歌 -11～-28dB）。每首音乐先 `loudnorm=I=-14:TP=-1.0:LRA=11` 归一化；暗调/安静的歌（如《全面沦陷》）loudnorm 后仍偏低，再加一档静态增益（+7dB 左右）补偿。目标各首副歌均落在 ~-15dB。
- **逐段建音轨再 concat**：每首一个自包含音频段（旁白+该曲 床→swell→展示），用 `ffmpeg -f concat` 拼成总 master，比一条巨型 filtergraph 可控。
- **历史竖裁例外（不得当成新默认）**：该期曾对单主体全程居中素材使用约 4:5 竖向裁切放大；新项目默认仍是 **letterbox 保原比例、不放大**。只有用户明确要求且完整候选窗逐帧证明主体安全时，才按「展示段硬规则 (A)」的历史兼容例外留证采用；双人/合唱/多人/宽机位禁止复用。
- **相邻 footage 交替轨道**（track 0/6 轮换）：HyperFrames 里同轨片段**首尾相接也算重叠**会报错；交替轨道规避（视觉层级仍靠 z-index）。
- **媒体元素必须有 `id`**：`<video>`/`<audio>` 没 id 渲染会被冻结/静音（lint 会报 media_missing_id）。
- **非 TOP 的主题叙事片可以按脚本顺序**：历史项目可用 1→5 的立论曲→高潮收尾结构，但标题、brief 与画面必须明确它不是 TOP / 排名 / 榜单。一旦属于 TOP 类，统一执行 N→1，不能再用“主题盘点”作为正序例外。

### 老素材 / 难度盘点的实战补充（窦唯最难5首验证）

- **TOP / 排名必须倒数 5→1**：把最难/最炸的留作压轴（窦唯片压轴《别来纠缠我》），第1名给红色"公认天花板"角标强化。封面和 intro 只讲主题与钩子，不列完整歌单、不展示排序、不泄露第 1 名；直到对应转场才公布该名次与歌曲。
- **成片内禁出现描述视频自身机制的 meta 文案**（如 `05→01`、`05->01`、`N→1`、"倒数开始"、"从第5名开始"）——这些只属于脚本、timeline 和制作提示词里的内部编排规则，禁止进入封面、intro 或其他观众可见文案。口播里的"第五…第四…"排名播报、逐首单个数字角标和当前 `RANK 05` 等名次标识 OK；把完整揭晓顺序直接写给观众不 OK。
- **密集摇滚定不了副歌位**：满编曲老摇滚整首 RMS 几乎持平（`volumedetect` 各 5s 切片差 <1dB），靠响度找高潮无效。改用**歌曲结构常识 + 抽帧看画面**定展示段，并把"高光是否最具代表性"明确交回用户耳朵定夺。
- **老素材普遍标清且带烧死字幕/台标**：4:3 标清用顶部对齐 crop（如 `384:400:128:0`）裁掉底部歌词字幕；做旧/发暗的源（如《靠近我》）vfill 前先 `eq=brightness=0.10:saturation=1.12:contrast=1.06` 提亮（vfill 的 BR 只作用于模糊背景，不提亮前景）。
- **水印垂直范围常超目测**（李×杨时间线《幸福菓子》验证）：SONY BMG 等老唱片公司水印实际占 y:0-75（看起来只在 y:0-45），底部烧字常占 y:340-480（不止最后两行）。**crop 前先二分抽断面**：`ffmpeg -ss N -i src -vf "crop=W:60:0:y" -frames:v 1 probe.png`，y 取 50/100/150/200/300/350，看哪一行水印/字幕消失，定 crop 安全区。**bg 也会显示残留水印**：vfill 的 bg 用 fg 同样的 crop 区域 scale up 后模糊，fg crop 内有水印 → bg 模糊层也露出（模糊后的文字仍可识别）。所以 crop 必须把水印**完全**裁掉。
- **极冷门曲只有超低清源**：窦唯《别来纠缠我》全网最佳仅 320×246 黑白——黑白颗粒反而贴合"金属嘶吼"压轴，但务必先把"能接受的最高源清晰度"回报用户。排除 Topic 静态图 / 歌词视频（静态+第三方水印）/ 双字幕无法裁净 / 非原唱者的后期重组现场。
- **跨歌响度统一**：逐首 `loudnorm=I=-14` 后五首副歌落 -18~-19dB、彼此差 <1dB 即达标（一致性 > 绝对值；偏轻可整体抬 2–3dB 再 mux）。

### 老素材 / 难度盘点的实战补充（周深最难5首验证）

- **yt-dlp webm 音轨被 download-sections 截断的坑**：opus-in-webm 切片，从 `-ss 0` 再 `-t` 重剪时，**音频流会比视频短几秒**（实测 video 26.4s / audio 21.5s），ffprobe 还读不出 opus 流时长（N/A）。后果：成片展示段音乐戛然而止。**修法**：先把整段 webm 整体重编码成 mp4（`-c:v libx264 -c:a aac`，音频补全），再从 mp4 切；或干脆用 **输出端 seek**（`-i in -ss S -t L -vn -c:a pcm_s16le out.wav`）抽干净音轨，build 里用这条 wav 当音乐源（与视频同区间→口型仍对齐）。中段 `-ss` 切的片不受影响，只有从头切才坑。
- **多机位综艺极难锁长特写（旧 6s 方案已废止）**：周深历史项目曾为锁特写把展示压到约 6s，这与当前“完整核心段、质量优先、默认不设上限”冲突，**新项目不得复用**。多机位素材可以保留节目自身的正常切镜；若完整核心窗结构性不可用，应换官方 MV / 官方 Live，或使用逐镜验证的救场蒙太奇，不能靠缩短音乐解决。
- **烧死歌词位置随源/随歌变，未必在底部**：时光音乐会这类把歌词烧在**画面中部**（实测《人是_》y≈840–920、《光亮》y≈680），顶对齐裁会毁构图。**官方 MV 通常更干净**：歌词在最底（y≈900，能裁），但留意 MV 可能有**持久标题水印**（《人是_》流浪地球MV 底部有大字标题，不可用）。逐源抽帧定 crop，搞不定就换源。周深这期最终：声入人心(孤独牧羊人)/歌手2020(达拉崩吧)/微博盛典(少管我) 干净可裁；《人是_》用时光音乐会(裁 864:820 去歌词)；《光亮》换官方紫禁城MV(裁 864:860 去底部歌词)。
- **片头片尾可复用同一条暗调底**做开合呼应（本片片尾复用 intro 的暗调舞台底），省一条素材且更整。

### 音乐 + 配音 ducking（通用，凡音乐与旁白共存即适用）

- 配音响起时音乐降到 **~25%（-12dB）**，**300ms** 平滑过渡；配音结束恢复 100%。
- 实现：ffmpeg 预混成**单条音轨**再接进 HyperFrames `<audio>`（确定性）。优先 `sidechaincompress`（音乐被旁白侧链自动闪避，最自然）：
  ```bash
  # music.wav = 该片段原声；voice.wav = 该条旁白（已按时间轴对齐/留白）
  ffmpeg -i music.wav -i voice.wav -filter_complex \
    "[1:a]asplit=2[sc][vo];[0:a][sc]sidechaincompress=threshold=0.05:ratio=8:attack=200:release=300[duck];[duck][vo]amix=inputs=2:normalize=0" \
    mixed.wav
  ```
  比例/阈值可按试听微调；用户只在想改默认时才提。
- 备选（确定性更强，推荐用于"床→swell"这种结构化动态）：用 `volume='<分段表达式>':eval=frame` 脚本化音量包络（按时间窗给不同增益 + 边界做斜坡）。
- **关键坑：HyperFrames 渲染会对音频做响度归一化，压平你精心做的动态**（实测旁白段 vs 展示段从 7.6dB 差被压到 2.6dB）。render 没有关闭开关。所以**精确混音必须后期 mux**：让 HyperFrames 只渲画面，再用预混 `master.wav` 覆盖成片音轨——
  ```bash
  ffmpeg -i renders/full.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/<slug>.mp4
  ```
  成片以 `renders/<slug>.mp4`（mux 后）为准，而非 HyperFrames raw render；两类 MP4 都不得离开 `renders/`。

### HyperFrames render 默认参数（短视频自媒体）

- **`--sdr` 必加**：HF 渲染会从 **任意一个** 源做 HDR auto-detect。Bili「杜比视界」流（如 LIKE A STAR 巡演 BV15m411k7Yi）一旦进 footage，整片输出会被升级成 **HLG (BT.2020) 10-bit H.265**——抖音/小红书/视频号普遍不收，播放器色彩翻车。Render 命令一律：
  ```bash
  python3 ../../tools/video/resource_budget.py hyperframes -- \
    npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr
  ```
  已有历史项目优先运行其 package scripts/lockfile 固定的版本，不用上面命令强行跨版本。
- **`<video>` 不能控 `currentTime`**：HF 渲染期间会把 video 元素的 currentTime 锁到合成时间。要让 footage 从源的某个时间码起播，**必须 ffmpeg 输出端预切**（`-ss S -i in -t L -c:v libx264 -g 30 -keyint_min 30 -an out.mp4`），切完的视频从 0 开始播。
- **同轨 footage 不能贴边**：相邻 footage 片段交替放在 track 0/6（详见上文）。
- **⚠ 多段 footage 长片：拼成单条 footage_track，HTML 只挂 1 个 `<video>`（硬规则，2026-06 柯南TOP10 验证）**：一条竖屏长片若挂 **多个 `<video>` 元素**（如 12 段 footage 各一个），HF 渲染会在页面初始化时**同时为每个 video 建 frame-player**，Chrome 直接挂死——报 `Runtime.callFunctionOn timed out / protocolTimeout`，**帧 0 就超时**，多 worker（-w4）会 thrash 更快崩、**单 worker（-w1）也卡在 setup 不出帧**。**解法**：把所有 footage 段按时间线顺序 ffmpeg concat 成**一条连续 `footage_track.mp4`**（与各段时长对齐），HTML 只挂**一个** `<video data-start=0 data-duration=total src="footage_track.mp4">`。单 video = 已验证的 clip-demo 轻量模式，一次过（16110 帧 -w2 约 11min）。叠加层（scrim/卡片/字幕）照常多 track。**`HYPERFRAMES_EXTRACT_CACHE_DIR` 环境变量**可缓存抽帧、重试不重抽。
- **GSAP exit hard kill**：每个 `tl.to(..., {opacity:0})` 后要加 `tl.set("...", {opacity:0}, end_time)`；否则非线性 seek 时 footage / overlay 可能残留可见——lint 会以 `gsap_exit_missing_hard_kill` 告警。
- **字体（0.6.69 验证）**：不得依赖 Noto/Google Fonts auto-fetch、远程 `<link>`、CSS `@import` 或渲染时网络请求。首选把有明确授权的 WOFF2 冻结到项目 `fonts/` 并用相对 URL `@font-face`；这样 lint/render 不受网络和系统字体漂移影响。`local()` 仅供明确锁定本机/OS 的历史或本机专用工程，须在 design/README 记录字体族与系统边界，不能宣称跨机可复现。
- **`composition_file_too_large` warning 可忽略**：单线性长片（330+ 行）不适合拆 sub-composition；这条 warning 是文档建议不是 error。

### 长篇叙事盘点 / 音乐时间线的实战补充（李荣浩×杨丞琳时间线验证）

> 历史验证：`sandbox/lirh-yangcl-timeline/` 曾完成 5 首歌 6:33 竖屏纪录片式时间线，后按 sandbox 生命周期删除。可复用的无媒体骨架已迁到 `tools/video/templates/longform-timeline/`，新项目不得依赖旧路径。

**历史项目对比（非新项目时长默认）**：该期 brief 是 6–8 分钟长篇，曾与当时的 60–90s 短榜单做对比；这些总时长和单曲分钟数仅描述该期，不构成新项目模板。可复用的是“进入 → 旁白铺垫 → 消化位 → swell → 副歌展示 → 中段金句 → 转场”的七阶段结构。

- **时长基线**（5 首歌 ~7 分钟总时长）：
  - `LEAD ≈ 0.15s`（该期用于避免章节交界拖沓，只是历史节奏参数，不定义静音 gate 阈值）
  - `PRE_VOICE ≈ 0.8s` 音乐床起 ramp
  - `POST_VOICE ≈ 1.2s` 消化位
  - `SWELL ≈ 1.5s` 音乐升起
  - `HIGH_BASE ≈ 40-45s` 副歌展示（前 4 首），`HIGH_LAST ≈ 55s`（finale）
  - `MID_OVER ≈ 5s` 中段金句叠副歌后半段
  - 整片 ≈ `intro 17s + 5 首 × (~70s) + outro 16s ≈ 393s = 6:33`，落在 brief 6:30-8:30 的目标区。
- **章节交界防无意空等**（QA 必查）：该历史工程每首开头的静音 `LEAD` 与上一段尾部叠加后曾形成突兀停顿。新项目按本文件「QA 方法论」的唯一静音口径判定：`1.0–1.5s` 在默认本地终验中为非阻断 advisory，显式发布终验才进入真人 REVIEW；`>1.5s` 两种模式都 hard fail，跨章不自动放行。hard fail 由代理调整旁白/镜头、使用相关真实音乐衔接、重混并重跑，不等于 goal blocked；禁止复制该期“全程 ambient bed”做法或铺噪声绕 gate。
- **多 footage 段必须预切**（见上 HyperFrames render 章节）：每首歌段 `<video src="clips_seg/<key>.mp4">`，其中 `clips_seg/<key>.mp4` 是从 `vert_<song>.mp4` 输出端切出的对应段（按 mseek 起始）。HF 不能在 render 时控 currentTime。
- **跨章节响度统一**（同张韶涵章节规则）：副歌段 5 首 -14.8 ~ -16dB，差 <1.2dB 即达标；旁白段 -21 ~ -24dB（与副歌差 7-10dB 体现 ducking）。

### 长篇片的封面（cover frame）

封面要求**第 1 帧可直接作社交平台缩略图**。该长篇人物项目要求**真人头像**；新项目的人物与封面通用规则见本文件「首屏封面」，不要依赖不存在的外部偏好引用。

- **头像优先级**：① **用户直接提供合照**（如 `raw/li-yang.jpg` 婚纱照） > ② 当事人确认的官方 4K Live 直拍 > ③ 综艺纯享版正脸帧。**绝不**用：MV 演员替身（如李荣浩《年少有为》《模特》MV 主角是演员不是他本人）、Topic 静态图、第三方搜出来的 "XX 直拍"（标题党严重）。
- **当 brief 涉及双人**（如"A 写给 B 的歌"），先自行从已验证官方 MV / Live / 节目源寻找合照或同框帧并核验身份；只有用户明确要求使用其私有合照而尚未提供，才把它视为用户独占的必需输入。采用用户提供图时放 `raw/li-yang.jpg` 这类位置，build 时 ffmpeg crop 两个 280×280 头像到 `hf/cover_assets/`。
- **圆形头像必须脸部居中**：双人合照里裁单人，crop 框右/左边缘不得带入另一人的肩膀/衣物。靠近时 crop 收紧到 220×220 而非 280×280；脸对正横向中心；多个人物的头像 crop 框宽度要一致以视觉对称。
- **背景模糊层用同一张合照**两次（一左一右），blur 40px + brightness 0.45 + scale 1.2 + 上叠 `linear-gradient(180deg, rgba(6,8,15,.45) 0%, rgba(6,8,15,.92) 100%)` 暗夜叠层，避免纯黑封面。

### 长篇片的字号 / 间距基线

短视频上观众离屏幕远（手机），辅助信息字号要比 desktop 设计直觉**至少大一倍**。基线（1080×1920 画布）：

- **左侧时间线轨**：节点 `48px` 圆点（不要 26px），序号 `22px 800-weight`（不要 12px）。
- **歌名玻璃卡**（右上）：宽 `640px`，padding `46/48px`：
  - `card-no` **36px** 800-weight letter-spacing .38em（不要 16px）
  - `card-year` 24px badge（不要 14px）
  - `card-name` 78px serif（标题歌名 OK 可稍大）
  - `card-credit` 28px 500-weight（不要 18px — 词曲信息常被忽视）
  - `card-tag` 30px 700-weight 用 acc 色
- **封面 5 节点列表（仅非 TOP 长篇时间线）**：节点 padding `18px 0`、序号 32px、歌名 44px、年份 22px 右对齐。**不要**用默认 padding 14px + 22px 序号——行间太挤、扫不到。TOP / 排名封面禁止列完整曲目或排序，本条不得复制过去。

### 渲染迭代成本

- 历史基准中一次 1080×1920 6:30 全片渲染用 5 workers 约 **8-10 分钟**；这是旧单任务测速，不是当前默认。现在统一经 wrapper 启动时自适应为 `4 → 3 → 2` 并去重 FINAL 重活；不要为了追单条速度恢复 5 workers / auto。
- **goal / 视频制作默认一次完成**：用户要求制作或完成一期视频时，直接从 brief 持续执行到 `renders/<slug>.mp4`、`publishing/xiaohongshu.md`、VOICE / PROJECT / PUBLISHING / 本地机械 FINAL 四道门禁与当期 QA，不以“新风格”为由先交 90s 样片或开场 + 首段后暂停等待确认，也不得因 pending human review 暂停或把 goal 标记为 `blocked`。内部可做 lint、抽帧、短区间试渲等低成本自检，但它们不是阶段性交付，也不能中断最终产物目标；只有用户明确要求发布级终验时，`--require-human-review` 才成为完成条件。
- **只有用户明确要求才交小样**：用户明确写出“小样 / 预览 / 先看风格”时，才可把局部渲染作为阶段性交付并等待反馈。若首轮全片 QA 发现问题需要重渲，应先在内部合并所有已发现问题再统一修复，减少多轮渲染；不要把每次内部迭代变成用户确认点。

### 展示段选源：概念/多机位 MV 的「歌手镜头蒙太奇」（吴青峰为别人写的歌 TOP5 验证）

> ⚠️ **默认优先「连续整段 + letterbox」**（见「展示段硬规则」），蒙太奇仅在连续段实在不可用时救场。本节是救场技法，不是首选。

> 验证项目：`sandbox/wuqingfeng-for-others/`（5 首竖屏盘点 3:32，一次渲染成功）。

并非所有 MV 都能提供完整核心窗（解说盘点通常 ≥25s）的连续歌手特写。**快切概念 MV（蔡依林《怪美的》护士/法庭/舞群每 1-2s 切，含空镜）、艺术柔焦 MV（杨丞琳《年轮说》大量抽象纸环空镜）、剧情 MV（张韶涵《有形的翅膀》全程高频穿插男主角/小孩；杨丞琳《带我走》男主角情侣戏）** 都可能给不到连续主体特写。处理分两类：

- **实拍同步（首选）**：单主体 MV（张惠妹《掉了》）或干净 Live（杨丞琳《带我走》2026 红裙纯净收音）能连续锁主体时，`clips.sh` 切片 `start` == `full_build` 的 `W`（音乐窗起点），footage 与音乐口型同步。
- **歌手镜头蒙太奇（救场）**：概念 MV 拼 3-4 个该歌手的独立镜头（`build/montage.sh`：每镜 `输出端seek 切→各自 crop 居中→vfill→concat`），**音乐另取该曲副歌**（与画面解耦）。慢歌/快切歌口型微差不可察。每个子镜头要**逐一抽帧验证**：剔除他人（男主角/伴舞/观众）、空镜、烧死字幕（各镜头 crop 的 H 单独压低排除底部歌词）。
- **找连续窗的工具链**：① 6 帧总览联系表定场景；② 候选窗每 2s 密集抽帧确认主体是否全程在场；③ RMS 扫描（`ffmpeg volumedetect` 逐 5s 窗）定副歌能量峰做音乐 `W`，比凭感觉准。
- **「主题同框」只作有证据的官方 MV 不可用例外**：历史项目《有形的翅膀》因官方 MV 目标段主要穿插剧情男主、无法完成“词作者与演唱者同框”的明确叙事任务，才改用 **张韶涵 feat. 吴青峰同台合唱 Live**。新项目不能仅因 Live 更高清或更热闹就放弃官方 MV；只有官方 MV 对目标主题/人物存在结构性缺口，或用户明确要求特定同框叙事时，才可换官方 Live，并在 `SOURCES.md` 记录证据和旁白调整。
- **多歌手盘点封面**：主题围绕"幕后创作者"时，封面主角放**词曲作者本人正脸**（非各演唱者拼贴），更聚焦、更切题（满足真人封面硬约束）。
- **片头/片尾 dead-air**：封面 5s 若纯静音会触发 `>1.5s` hard fail。先从口播/画面/剪辑节奏解决；确需声音衔接时只能使用与内容相关的真实歌曲段，并按听感设计，而不是为过阈值铺白噪音、ambient 或无关底床。outro 的内容音乐可取合适副歌并自然 fade，仍须重跑终片 gate。

### 格式之一：音乐 TOP 盘点

在通用能力之上加排名呈现：**所有 TOP / 排名 / 榜单一律倒数揭晓 N→1**，每条在自己的转场才出现大号排名 + 歌手 + 歌名。`N→1` 只描述内部播放顺序，不是成片文案；封面和 intro 可以写主题与“TOP N”，但禁止出现 `05→01` / `N→1` 等完整顺序标签，禁止提前列完整歌单、展示排序或泄露第一名。悬念必须保留到逐条揭晓。非排名类视频不套排名件，也不要用 TOP 命名。

TOP 默认保留**开头旁白 + 每首短转场旁白 + 作品 outro + 固定 CTA**，并且整期不设时长上限、质量优先。历史 60–90s 榜单及每首 12–18s 是旧项目局部方案，不再作为默认；用户确有平台硬时长时优先减少条目/重复信息，保留片段仍必须停在完整乐句边界。历史每首 15s+ 的长解说只能按旧 schema v1 复现；新项目必须先把 TOP 转场压到实际 WAV ≤8s，再按「展示段硬规则 (B)」独立保留连续 ≥~25s 的副歌。

### 格式之二：AI 跨时空同台（历史自由探索实验）

> 验证项目：`sandbox/dbmh-ai-stage/`（窦唯/王菲/窦靖童《Don't Break My Heart》三人接力实验，2:54）。

> **历史自由探索例外，不是“带 AI 即可省略结构”的新默认**：只有新项目从启动时就以 `project_kind: free_exploration` 写明非空 rationale、brief/design 明确音乐实验方案，并通过 project gate，才可按创意减少旁白或不使用 canonical CTA；否则仍执行开头、逐项转场、作品 outro、固定 CTA 的完整结构。

把同一首歌的多个不同年代/不同版本拼成"AI 同台接力"，让观众感觉三人/多人像在同一场演出里依次接唱。本质上是**音乐实验**，不是盘点解说。

**与盘点格式的关键差异：**
- 不分排名、不分章节解说，**主体是音乐而非旁白**。
- 旁白只用在**开头 + 结尾**（声明 + 收尾），中段全程让音乐和画面说话。
- 必须显式声明 **"AI 剪辑实验｜非真实同台演出"**（开头小字 + 全程右下角小角标 + 结尾文案），避免误导观众以为是真实演出。
- 不能出现描述视频自身机制的 meta 文案；这是本仓库的成片泄漏规则，不依赖不存在的外部偏好引用。

**接力时间码定位（核心）：**

错误做法：用 RMS 能量峰找"高潮段"做接入点 — 能量峰常在副歌中段，错过了 verse/chorus 入口；同一首歌不同版本的 verse / chorus 入口时间码完全不同，必须**逐版本精确定位**。

正确做法：用**多证据主唱候选检测**找每个版本的 verse 1 / verse 2 / final chorus **入口时间码**，再让接力对齐到歌曲结构而非时间偏移。旧频带算法仍保留为低成本候选，但不能独立证明是主唱：

```python
# tools/video/vocal_segments.py 内部的 acoustic candidate（不是最终主唱结论）
y_harm, _ = librosa.effects.hpss(y, margin=3.0)         # 谐波分离
S = np.abs(librosa.stft(y_harm))
voice_mask = (freqs >= 200) & (freqs <= 3000)            # 人声频带 200-3000Hz
voice_rms = np.sqrt(np.mean(S[voice_mask] ** 2, axis=0))
# 平滑 + 60th percentile 阈值 → 连续 >2s 视为有效 vocal 段；>1.5s gap 视为段间
```

正式运行用 `--mode multi`，优先读取 `lead_segments`；`vocal_segments` 仅为兼容字段。若 `evidence_level!=multi_evidence`，不得仅按区间密度自动认定 verse/chorus：普通 goal 严格按 **multi → 换窗 → 换源** 恢复；穷尽且硬 `FAIL=0` 后，本地可消费 hash-bound agent observation 并且只能得到 `OBSERVED`，发布 `--require-human-review` 仍只接受 human。不能把首次分析不足变成等待用户的默认分支：
- **verse 1** = 早期第一个长 vocal 段（通常源开始后 30-90s 之间的一段连唱）。
- **verse 2** = 中段第二个长 vocal 段（通常 130-180s 之间）。
- **final chorus** = 接近尾段的高密度 vocal 段（通常 200-250s 之间，多句连唱）。

**接力策略：让 A 唱第一段 → B 接第二段 → C 接最后段**（dbmh-ai-stage 验证）。三段都对应歌曲结构的同等位置（verse 1, verse 2, final chorus），听众感受是音乐结构连续而非时间堆砌。**不要用 intro 期（纯 instrumental，没人声）做接力起点** — 听众会觉得"第一个人还没唱"。

**音频拼接：**
- 每段单独 `loudnorm I=-16` 后整体 `loudnorm I=-14`，副歌段响度 mean ≈ -14~-17dB。final chorus 比 verse 自然响 2-3dB，不必强压。
- 段间 **acrossfade 1-2s**（不是 4s 以上）— 太长 crossfade 会有"两人同时唱"的混叠感。
- 三段 BPM 接近（实测 99/108/103 BPM 差 ≤ 10）可保留各自节奏不做 time-stretch；BPM 差 >15 才考虑微调（人声 stretch >5% 会变形）。
- TTS 旁白起 200ms 前 ducking 音乐到 -10~-12dB，结束后 300ms 内平滑恢复。

**画面布局：**
- 不全程三等分。用 **"主舞台 + 记忆卡片 + 同屏爆点"**：
  - 主舞台段（每人 30-60s）：1080×1920 全屏单人 footage + 章节标签 "X｜角色"（左上滑入式）。
  - 同屏爆点段（10-15s）：**三层等高条带**（每层 1080×640），上中下顺序对应章节顺序，中央 SVG 声波线连接三人入点（圆点）。
- 章节配色用 CSS filter + 半透明色彩 overlay 区分（不是滤镜重渲）：
  - A 暗红/胶片：`filter: contrast(1.06) saturate(.85) sepia(.20) hue-rotate(-12deg)` + 红色 radial gradient overlay。
  - B 冷蓝：`filter: hue-rotate(180deg) saturate(.78)` + 蓝灰 radial。
  - C 蓝紫：`filter: hue-rotate(8deg) saturate(1.05)` + 紫罗兰 radial。

### 格式之三：AI 克隆歌手音色 MV（整首 MV 换训练音轨）

> 历史验证：`sandbox/angela-ai-mv-covers/` 曾持续追加多批独立 AI 音色 MV，后按 sandbox 生命周期删除。无媒体、无人物绑定的构建骨架已迁到 `tools/video/templates/ai-voice-mv/`；不要恢复旧目录或其中生成物。

当 brief 明确是“AI 克隆/训练歌手音色制作 MV”“如果某歌手唱某歌”，且用户给了可直接使用的训练音频 WAV 时，新建当期 `sandbox/<slug>/`，复用中央 durable 模板；每期素材、来源记录、声线选择和输出彼此隔离。

**固定流程：**
- 源音频：把用户给的训练 WAV 复制到当期项目 `audio/`，不要重新推理、不要改训练音色文件本身。若音频来自 `cc-voice`，只允许复制用户明确给出的 WAV 路径或目录内 WAV 到本项目；不得对 `cc-voice` 做目录扫描、状态检查、哈希/时长探测、进程检查或任何写操作。时长/静音/哈希等校验一律在复制到 `cc-media` 后对本地副本执行。批量目录导入时，文件名含 `废弃` 的 WAV 直接跳过。
- 源视频：每首仍按“素材源平台”硬约束同时查 YouTube + B站。版本身份正确后优先官方 MV，官方 MV 画质稍差也继续优先；第三方 4K 升级源不能仅凭分辨率胜出。仍需抽帧确认目标段可用，只有官方 MV 存在结构性缺口时才按总则换源并在 `SOURCES.md` 留证。
- 构建：按 `tools/video/templates/README.md` 填写项目 `build/config.json`，运行 `tools/video/templates/ai-voice-mv/build.py`；一首输出一个 `renders/YYYY-MM-DD/<配置输出名>.mp4`。视频必须先与训练 WAV 对齐；仅允许用 `tpad` 补视频短于音频不超过约 0.5s 的编码级差异，不能靠它掩盖剧情片头或错误偏移。
- intro：先从用户原始 prompt 解析一次项目 `voice-selection.json`，再用 `tools/tts/narrate.py <文案> --selection-file ... -o ... --speed 1.12` 生成“如果某歌手唱《歌名》。”类提示；未指定时从女声池随机一次，显式有效指定则按指定。构建脚本会校验 sidecar 与项目选择一致，并修剪 TTS 首尾静音。
- 混音：intro 期间训练音频 duck 到约 25%，intro 结束后 350ms 恢复；最终音频直接由 FFmpeg 预混/编码，不走 HyperFrames 音频归一化。单首训练音频若明显低于本目录响度基线，可在 `Song` 配置轻微 `audio_gain`，但最终 max volume 必须低于 0dB。
- 角标：全程叠加 `AI训练，仅供娱乐`。用 durable 模板内保留的 `watermark.swift` 离线生成当期项目透明 PNG，再由构建脚本 `overlay`；源码可复用，生成的工具和 PNG 仍留在 `sandbox/<slug>/`。
- 来源记录：每首都补 `SOURCES.md`，写清 YouTube/B站候选、最终选择、限制和是否做 crop。

**源选择与 crop 经验：**
- “官方 Karaoke 版”常自带大歌词，这是源内容限制；如果没有更干净且无平台/UP 主水印的同画质候选，可以保留，但必须记录。
- B站 4K 修复源常画质高，但可能有平台水印、UP 主水印、修复者 logo、烧死歌词。先抽 `1s`、`40s`、副歌附近帧，不干净就先试全宽横带 crop。
- 去水印/烧词优先用**全宽 crop**，只裁底部或顶部污染带，保持主体完整；不要用竖向激进裁切。《心墙》验证：`crop=3840:1920:0:0` 可去掉底部 `bilibili/zyl2012` 和歌词，同时保留 2:1 全宽画面。
- 若全宽 crop 会裁掉关键人物/标题，宁可退回低清官方源；不要交付含平台/UP 主水印的成片。
- 高分辨率候选不是充分条件。B站 4K/1080P 修复版只要带平台角标、UP 主水印、修复者 logo，且无法用全宽 crop 干净移除，就优先退回官方/版权方低清源；`回家`、`一个人想着一个人` 已验证这个取舍比保留高分辨率水印更稳。
- 画面污染区可能同时出现在顶部和底部，先用最终输出比例做 crop probe，再抽最终帧确认主体完整；`孤单心事` 用 `crop=1920:820:0:120`，`飞鸟和蝉` 用 `crop=1920:760:0:280`。
- B站 4K 修复版如果比训练音频短 2-4 秒，且标题/画面提示为歌词重制或非官方修复，不要为了分辨率牺牲整首 MV 对齐；优先选时长精确匹配的官方源，哪怕官方源只有标清。《搁浅》验证：YouTube 官方源 640x480 但与训练 WAV 268.65s 精确对齐，B站 4K 候选均短于训练音频。
- 官方 MV 若是长剧情版，时长可能明显长于训练 WAV，不能直接从 0 秒替换音轨。先用原 MV 音轨与训练 WAV 做粗粒度 RMS/能量包络相关性估算，确定歌曲对齐偏移，再预切出同长视频片段进 `Song` 配置。《慢冷》验证：官方 MV 457.71s，训练 WAV 289.30s，最佳偏移约 `97.5s`，预切为 `raw/manleng_aligned.mp4` 后合成。
- 官方/准官方 MV 若带 20s+ 片头剧情、唱片片头或对话，也按同一对齐流程处理；`我知道` 验证最佳偏移约 `22.3s`，预切后再替换训练音轨。

**QA：**
- `ffprobe` 确认最终 MP4 时长与训练 WAV 对齐，视频为 H.264、音频为 AAC。
- 抽 `1s` 和中段帧用 Read 看：角标存在、非黑屏、无平台/UP 主水印、无路径/提示词泄漏。
- **AI 整首 MV 的独立静音边界**：该格式不使用标准 `verify_final_video.py` schema，按 durable builder `--check` 与本节 QA 处理。`silencedetect` 命中必须与当前训练 WAV 的相同时间窗、当前 hash 对照；只有能证明是用户训练源自带、且剪除会破坏整首对齐的静音才可保留并在交付中说明。这个例外不能移植到标准盘点/叙事终片，也不能靠添加噪声或无关底床掩盖。
- `volumedetect` 目标与上一批保持接近，实测本目录多首 mean volume 约 `-17.4 dB`，max volume 保持低于 0dB。

### 首屏封面（首帧可作封面，硬约束）

**第 0 秒第一帧必须可作为静态封面图。** 不要给封面元素加 `fade-in` 入场动画（否则 t=0 时 opacity 仍是 0，整张封面黑屏）。

**🔒 盘点类封面 = 第一首出场歌的「动态」画面，连续流入该首（默认硬约束，2026-06 范晓萱期验证，用户点名要求）**

盘点类（音乐 TOP / 遗珠 / 主题盘点）开场封面**默认用「第一首出场歌」的真实素材动态画面做底**——不是静态图、不是单独抠出来的人像静帧——并让这段画面**连续不断地流进第一首歌**：切到第一首时**画面不剪、不跳**，只是封面标题淡出、该首的序号/歌名卡淡入。封面→第一首是**同源连续帧**，转场最丝滑（用户实测反馈"非常丝滑"）。

> **"第一首出场歌" = 播放顺序上第一个播的那首**：TOP / 排名片 = 排在最后一名、最先揭晓的那首（如 #5）；非排名叙事片 = 脚本里第一首。**不是"排名第一"那首**，别搞反。

实现（范晓萱期 `sandbox/fanxiaoxuan-underrated-top5` 验证，照抄）：
- intro footage 与第一首 footage **取自同一条素材的一段连续窗**，帧上首尾相接：
  `intro = src[T0 .. T0+intro_end]`、`song1 = src[T0+intro_end .. T0+intro_end+seg_dur1]`（两段**同 crop**，分别 vfill 成 `vert_intro.mp4` / `vert_<song1>.mp4`；footage_track 顺序拼接即连续无缝）。
- **T0 选点**：让 `src[T0]`（= 封面第 0 帧 = 缩略图）是**正脸 / 睁眼 / 可辨识**的好镜头（满足下面"封面单帧选择避坑" + 真人封面硬约束），同时 `src[T0+full_start_local .. T0+seg_dur1]`（第一首展示段）画面也够好。footage 解耦时 T0 可自由滑动找最佳开场帧。
- **删掉静态 `cover_hero.png` 图层**，让动态 footage 直接做封面底；`#cover` 的暗渐变（顶 ~.84 / 底 ~.86）保证标题/副文可读；封面标题用 `tl.to(opacity:0)` 在 `intro_end` 淡出，footage 继续播不剪（别给 footage 加 cut）。
- **为什么零成本**：盘点 footage 本就**解耦**（封面期音频 = 开场旁白 + 床，不是歌），footage 是静音 b-roll，所以"封面用第一首画面"天然同源、不增加任何素材。
- **例外（才退回旧做法）**：第一首确实没有可做封面的好开场帧（全程空镜 / 烧字裁不净 / 真人不清晰），才退回"单独预切人像静帧 `cover_hero.png` 封面"，并在交付说明为何退回。

**封面单帧（无论动态底还是静帧）的通用要求**：
- **默认优先歌手本人出镜**：封面别默认用空镜、抽象景、剧情演员或纯舞台灯；优先歌手本人正脸/半身/演唱动作清楚的段落。
- **TOP 封面必须保留悬念**：只允许展示选题主题和 `TOP N` 数量标签；不得列完整歌单、歌曲顺序、具体名次结果或第 1 名。`N→1` 是脚本、timeline、build 配置与 QA 的内部排序约定，**禁止在封面与 intro 画面绘制 `05→01`、`05->01`、`5→1`、`N→1`、“倒数开始”“倒序揭晓”“从第5名开始”或 `05 / 04 / 03 / 02 / TOP` 这类逐名次方向轨**。逐首揭晓时的单个当前名次数字与 `第X名` 口播仍可使用。intro 也遵守同一规则，后续名次只能在各自歌曲转场时首次揭晓。
- **标题先做层级，再做换行**：先确定主题词、歌手名、类型/数量标签的主次，再按完整语义短语断行；禁止按固定字数机械折行、留下单个孤字、把歌手名或强关联词组拆开，也不能出现上行过满、下行只剩一两个字的失衡版式。短标题宁可少换一行，长标题应在自然停顿处拆分，并人工比较至少两个排版候选。
- **单歌手 / 单组合主题封面：歌手名必须是唯一最大字号主体（硬约束）**：当整期围绕一位歌手或一个组合展开时，歌手 / 组合名必须成为封面的第一视觉落点，并使用全封面**唯一最大字号**；其字号必须严格大于主题口号、歌名、`TOP N`、类型标签、年份、期数和副标，不能与主题文字同大，更不能缩成副标、角注或说明文字。主题句只负责补充本期角度，不得与名字争夺主体。只有多歌手并列主题，或 brief 明确把非歌手对象设为封面主体时才可例外，并须在项目 `design.md` 写明主体层级与理由。
- **关键信息只使用一个安全信息区**：标题、`TOP N` 数量标签、主题、副标等不要拆成“最顶一组 + 最底一组”，避免发布页裁剪后只剩半套信息。1080×1920 默认把关键文字控制在约 `x=72–1008 / y=220–1420` 的安全带内，再按主体位置放在中上、左上或右上；非关键信息也不要贴边。
- **不死居中遮主体**：信息块不能整块压在画面正中央的脸、麦克风或主要动作上。先确定人物/主体的负空间，再把同一信息组偏到不遮主体的一侧或中上区域。
- **封面 QA**：首帧同时检查完整画面、常见顶部/底部裁剪预览和文字 bounding box；除裁剪安全外，还要人工检查语义换行、行长平衡、留白与主体避让，不能以“没有溢出”代替排版美感。单歌手 / 单组合主题必须比较实际 computed font-size：名字不是唯一最大字号，或第一眼先读到主题句，均判定封面 QA 失败。关键信息必须在裁剪后完整可读，主体仍清楚可辨。

正确做法：
```js
// cover 整体 opacity 起就 1，所有子元素也 set opacity:1
tl.set('#cover', { opacity: 1 }, 0);
tl.set('.cv-card', { opacity: 1 }, 0);
tl.set('.cv-text', { opacity: 1 }, 0);
// 6s 后开始 breathing / 闪烁，不是 fade-in
tl.to('.cv-dw', { scale: 1.025, duration: 4, yoyo: true, repeat: 1 }, 5);
```

**封面单帧选择避坑：**
1. **过曝/全白脸不要选**：彩色舞台灯打到主体上常会过曝；脸细节冲掉就毁封面（如黄色烟雾、白色 spotlight 全打脸）。优选**有黑色/暗色对比背景的镜头**。
2. **麦克风挡脸不要选**：现场演出大量"嘴对麦"的近景，麦克风+手部挡掉下半脸。优选**侧脸唱**、**举头闭眼**或**麦克风离脸**的瞬间。
3. **避平台水印**：抽 1920×1080 全图先看完整画面，标记水印位置（B 站 UP 主水印常在中下、芒果 TV "会员尊享" 在右上、美团/赞助商 logo 在 LED 屏背景中部），crop 起点必须避开这些区域。
4. **CSS blend mode 不要用 `luminosity`**：会把彩色图变成只剩明度+底色（变灰失彩）。如要让原图调色统一，用 `soft-light` 或低 alpha 的 `multiply` 替代，alpha 控制在 .20-.30。
5. **抽帧前先看完整 1920×1080 原图判断人物位置**，再算 crop 坐标（不要靠缩略图猜）。卡片纵横比记下来再 crop（cv-fw 480×680 ≈ 0.706:1，所以 crop w/h 也要 0.706）。

### HyperFrames 多 video 同层时间窗口（已踩坑）

video 元素的 `data-duration` 必须 ≤ video 文件实际时长，否则超出部分显示黑屏（HyperFrames 把 currentTime 设到超长时间，video 渲染失败）。

三层分屏 / 多 video 重叠时：
- 切 video 片段前先确定 data-duration，**clip 文件时长要等于或略大于 data-duration**。
- 实测：data-duration=14 配 6s clip → 8s 黑屏 bug。重切到 14s clip 后才正常。

### 转场卡 fade-in 时机（已踩坑）

转场卡（如 "原点 → 回声"）如果用 staggered fade-in（from 先入、arrow 跟着、to 最后入），渲染抽帧落到 stagger 中段时只会显示一半文字（"原点 → " 但 "回声" 还没渐入）。

修复：转场卡整体 0.3-0.4s fade-in（opacity:0→1），内部子元素只用轻位移 stagger（不再 fade alpha），保证任何抽帧时刻都是完整文字。

### Section 切换处 fade overlap（已踩坑）

video A fade-out 结束时刻 = video B fade-in 起始时刻 → 中间会有 0.5-0.8s 全黑。修复：让 B 的 `data-start` 比 A 的结束时间提前 1s，fade-in 持续 1s，与 A 的最后 1s 渐隐重叠。

### 一家三口同唱 DBMH 验证补充（窦唯/王菲/窦靖童纪录片格式）

> 验证项目：`production/dou-family-dbmh/`（4:49 竖屏，三段章节 + 三人同屏 + outro）。

**用户对背景白噪音零容忍**（最严格的偏好之一）：
- 全片 ambient 底床（即便 sub-bass + brown noise 综合 -47dB）**用户能听到，会立即抱怨"轰隆隆"**。
- 禁止用全片 pad、白噪音、brown noise 或无关 ambient 兜底 `silencedetect`；用户偏好顺序是：**有意图的真停顿 > 为过 gate 伪造的底床/噪声**。
- 可从内容本身修复：章节末自然 `afade out`、调整旁白/镜头时机，或使用同章节真实音乐做有叙事意义的 bridge；不能只把电平抬过检测阈值。
- 阈值没有项目级例外：`1.0–1.5s` 即使是自然停顿或跨章节，在默认本地终验中也必须记录为非阻断 advisory，显式发布终验才需真人 REVIEW；`>1.5s` 始终 hard fail，并由代理修剪/重混/重渲后复验；统一以「QA 方法论」和终片 gate 为准。

**短视频开头节奏（用户硬偏好）**：
- 0-1s **必须有视觉动作**（卡片缩放/path 绘制/光点点亮均可），不能纯静止。
- 5s 内**必须进入实质内容**（开始口播 / 切到 footage / 章节起手）。
- 即便 brief 写"0-6s 封面静止"，要按短视频节奏压缩——这是用户感知节奏 > brief 文字。
- 实测：V3 把封面排成 14s（含 stagger reveal），用户立即反馈"飞入动画太慢，观众几秒就没兴趣"。V4 压到 5.5s 满足。

**封面三卡 + 标题块 collision 安全距离（历史项目局部记录，不是新项目坐标默认）**：
- 竖屏 1080×1920，cover-title 块在底部 `bottom: 62px`，typical 块高约 370-400px（含 tag/h1/h2/歌名/副标）→ 标题顶部 y ≈ 1488。
- 三卡块中**最低的卡底部** ≤ y ≈ 1410（留 ≥ 78px 安全间距）。
- 设计 cover 时把所有绝对定位元素 `(left, top, w, h)` 列表化，**手动算 overlap**（lint 不查）。Cover frame 0 是关键封面图，碰撞最致命。
- 实测：cv-jt 初版 top:990 h:600 → 底 1590，与标题块碰撞 102px。修到 top:810 留 78px 间距。

> 上述 `bottom:62px / y≈1488` 是既有成片的历史几何记录，落在当前默认安全带之外，**新项目禁止照抄**。新封面仍以 `x=72–1008 / y=220–1420`、单一安全信息区和平台裁剪预览为准。

**AV1 输入侧 seek 不准**：
- `ffmpeg -ss 145 -i raw_av1.mp4 -frames:v 1 out.jpg` 取出来可能是 t=150-160 区间任意一帧（AV1 关键帧稀疏 + 输入端 seek 不解码到精确帧）。
- 抽帧定位必须用**输出端 seek**：`ffmpeg -i raw_av1.mp4 -ss 145 -frames:v 1 out.jpg`（慢一些但准）。
- contact sheet 拼图也要用 output-side seek 或先转 H.264 密集关键帧再抽。
- 实测：黑豹 MV `-ss 145 -i ...` 抽出来是 BOY 帽剧情演员（t=155 附近）；换 output-side seek 才能精确到 t=145 的窦唯长发侧脸 closeup。

**Legacy Kokoro 中英混读问题（不适用于当前编号 Qwen 声线）**：
- Kokoro misaki[zh] **不擅长中英混读**。旁白文本里有英文（如"Don't Break My Heart"）会念得断断续续/不自然。
- 修法：TTS 文本里把英文歌名改写成"这首歌/这段旋律/这段歌"；**屏幕字幕仍可保留英文**（视觉与听觉分流）。
- 适用于：英文歌名、品牌名、人物英文译名等夹杂场景。

**字体选择对纪录片质感的决定性影响（历史视觉经验，执行仍服从当前字体边界）**：
- 衬线主标、优雅西文斜体、清晰无衬线 UI 与 mono 数字的层级组合通常优于全局同一种系统无衬线；具体字体按当期 design 和授权选择。
- 历史项目曾使用 Noto Serif/Sans SC、Cormorant Garamond、JetBrains Mono；新项目若继续使用，必须确认授权并把实际 WOFF2 冻结到项目 `fonts/`，不能只写字体名称或依赖远程服务。
- 禁止 Google Fonts `<link>`、CSS `@import`、HyperFrames auto-fetch 等渲染时远程字体路径。`local()` 只允许在明确本机锁定的历史/本机专用项目，并记录 OS 与字体族；它不是跨机交付方案。

**Section 时间线集中管理（避免散布 hardcoded 数字）**：
- 早期版本散布在 GSAP 里的 `tl.fromTo(... , 38)` / `tl.to(... , 85)` / `transitionShow('#trans1', 85, 13)` 等硬编码 timestamp，**改一个段的时长要改十几处**。
- 重构：Python 端定义 `SECTIONS = {'cover':(0,5.5), 'open3':(5.5,15.5), ...}`，模板渲染时注入 JS 常量 `const S = {cover:0, open3:5.5, ...}; const E = {cover:5.5, ...};`，GSAP 里只引用 `S.cover` / `E.ch1`。
- 调整整体时长（如把封面从 14s 压到 5.5s 整体提前 8.5s）只需改 SECTIONS dict 一处，build.py 和 build_audio.py 都自动算 propagate。

**zsh `*` 通配 no-match 默认 exit 1**：
- 后台命令 `rm -rf renders/work-*` 在没匹配时 zsh 报 "no matches found" 并 `exit 1`，导致 `&&` 后续命令不执行。
- 修法：用 `find . -maxdepth 2 -name 'work-*' -type d -exec rm -rf {} + 2>/dev/null`；或在脚本顶部 `setopt NULL_GLOB`；或 `||true` 兜底。
- 同类坑：`ls frames/v3/*.jpg` 在空目录会报错，要 `find frames/v3 -name '*.jpg'`。

**HTML/HF 编辑后渲染验证迭代节奏**：
- 每次 full render ~5-10 分钟（5min 视频 1080×1920 30fps draft），不能每个改动都全渲。
- 推荐节奏：① 改 → lint 必须 0 error → ② 抽 frame_000000.jpg 看封面是否对（HyperFrames 渲染时 work-dir 里 worker-0 会先产 frame 0）→ ③ 觉得封面/关键时刻 OK 才等 full render → ④ mux + 抽帧 contact sheet 终验。
- 批量化：把多个修改攒起来再渲，**别每改一行就重渲**。

**用户验收时常见反馈类型 + 应对**：
- "白噪音/底噪" → 删 ambient pad，自然静音
- "动画太慢/开头静音太长" → 压缩入场动画 + TTS 前移
- "文字重叠/被挡" → 列所有元素 (x, y, w, h) 表 + 手算 collision
- "标题/字体/排版普通" → 调整衬线/Mono 层级、对齐与色彩；新项目把有授权的实际 WOFF2 放进项目，不能只写系统字体名。只有明确的本机专用工程才可按本节字体边界使用 `local()`。
- "转场文案意义不明（只有年份）" → 加诗意主文案，年份做装饰小字
- "黑屏没画面只有文字" → outro/CTA 期保持 footage 衬底，文字浮在上方

## 渲染与产物

- `npm run render` 输出到项目内 `renders/<id>_<时间戳>.mp4`。
- raw render 与 mux 后最终 MP4 必须始终留在 `renders/`；最终交付命名为 `renders/<slug>.mp4`，不得使用 `final/`、`output/` 或项目根终片。
- 渲染吃内存（headless Chrome 截帧），`doctor` 报过低内存告警；大渲染前留意可用内存。
- 产物归档策略（保留可复现输入而非仅 MP4）：见各目录 README。`renders/`、`*.mp4`、下载素材已在 `.gitignore` 排除。

## 环境坑（已踩）

- ~~npm 缓存曾有 root-owned 文件导致显式版本命令报 EEXIST/EACCES~~ **已于 2026-05-27 修复**；新项目仍使用项目 lockfile/scripts 或 `npx --yes hyperframes@0.6.69`，不因缓存恢复而省略包版本或改用浮动 latest tag。
- Docker 未装：仅容器化渲染需要，本地用系统 Chrome 渲染不需要，可忽略。
