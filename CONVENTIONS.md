# CONVENTIONS.md — 全局规范

本文件用于**积累和定义可复用的规范**。每当在 `sandbox/` 验证出一个值得固化的做法，就写到这里。CLAUDE.md 引用本文件作为规范的单一来源。

> 状态：探索阶段，多数条目待补。先记录约定，跑通后再回填细节。

## 目录约定

- `sandbox/` — 测试/实验，内容可丢弃。
- `production/<项目名>/` — 正式成片，每个项目独立子目录。
- `tools/` — 跨项目复用的工具（如 `tools/tts/` 配音）。

## 配音 (TTS) 规范

- **引擎**：Kokoro + **misaki[zh]**（本地、免费、无 API KEY）。横评结论见 `wemedia/tts-local-benchmark`，Kokoro 是唯一跑通的本地中文方案。
- **音色策略（硬约定）**：
  - **默认男声 `zm_yunxi`**。
  - **女声 `zf_xiaoyi` 仅在明确要求女性配音时使用**。
  - 其余 6 个中文音色（`zf_xiaobei/zf_xiaoni/zf_xiaoxiao`、`zm_yunjian/zm_yunxia/zm_yunyang`）可显式指定，不作默认。
- **工具**：`tools/tts/narrate.py`（默认男声策略已内置）。环境 Python 3.12 venv + kokoro + misaki[zh]，详见 `tools/tts/README.md`。
  ```bash
  tools/tts/venv/bin/python tools/tts/narrate.py "中文文本" -o out.wav          # 默认男声
  tools/tts/venv/bin/python tools/tts/narrate.py script.txt --female -o out.wav  # 女声
  ```
- **不要用 HyperFrames 内置 `npx hyperframes tts` 做中文**：它把语言代码 `zh` 传给 espeak，而 espeak 只认 `cmn`，中文直接报错；且 espeak 普通话质量弱。英文旁白才考虑内置 tts。
- 输出 24kHz wav，作为独立 `<audio>` 轨接入 composition（见下「全链路」）。自动字幕可对 wav 跑 `npx hyperframes transcribe`。

## 命名约定

- 项目/成片名：`kebab-case`（如 `ai-news-weekly-01`）。
- 源素材文件名包含来源标识与时间码，便于追溯（待定具体格式）。

## 素材源平台（硬约束，优先级高于 brief）

**两边都要找：YouTube + B站（哔哩哔哩）并行**。每条素材都先在两个平台各搜一遍候选，按以下维度选**质量更高**的一边：

1. **清晰度**：分辨率 + 码率（同 1080P 也可能码率差一倍）。
2. **画面干净度**：无烧死歌词字幕 / 台标 / 平台水印 / UP主水印 / 双语条；MV 中部的歌词条比底部更难裁，优先无歌词版。
3. **音频质量**：立体声优先 > 单声道；高码率优先；注意 **B站给 4K 流配的音轨常是单声道**，遇到这种"4K 单声道 vs 1080P 立体声"，**优先立体声**（MV 听感为主）。
4. **现场/版本质量**：官方 MV > 官方直拍 / Live > 综艺 Live > 翻唱/二次剪辑；多机位综艺常切镜密集（每 2-4s），难锁长特写。
5. **可用切片**：源里要有连续可用段（如至少一个完整副歌不被打断）。

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

## 固定结尾配音（硬约束，优先级高于 brief / 任务提示词）

**每条成片的最后一句旁白固定为这句引流 CTA，逐字照念，不由单期 brief 决定：**

> **你最想为哪一首投票？评论区告诉我。记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。**

**优先级（核心）**：本句是**全系列统一的固定收尾**，优先级**高于单期任务 brief / 提示词**。brief 不写它、不改它，也不能用"这期结尾说点别的 / 换个 CTA / 不要 CTA"来覆盖它。唯一能改的是**直接修改本条规范**（用户显式说"改结尾词"），否则**一律照念**。即便某期 brief 给了自己的结尾文案，那份文案只能落在「作品自身 outro」（内容总结 + 主题升华），固定句仍在其后照念。

**位置（铁律）**：永远是**全片最后一句**旁白——排在每期作品自身 outro 之后。结构：

```
[作品 outro] 总结排名 / 主题升华（收在歌手特质上，每期独有，brief 可写）
   ↓ 0.8–1.2s 消化位（床 swell，不死静）
[固定 CTA]  你最想为哪一首投票？……盘到你单曲循环过的那一首。  ← 全片最后一句，固定
   ↓ 末 1.6s fade
```

**防双 CTA（必守）**：既然固定句兜底互动，**每期作品自身 outro 不得再自带投票 / "你会怎么排" / "你心里第一名是谁"之类问句**——否则连问两次投票、像两个结尾。作品 outro 只负责把内容讲完、收在主题升华，互动 ask 一律交给固定句。

**仅两个可换槽**（只为贴合选题，不得改 CTA 本身意图）：

| 槽位 | 默认 | 可换（按选题） |
|---|---|---|
| 投票对象 | 哪一首 | 哪一位（歌手 PK）/ 哪个版本（版本对比） |
| 下期钩子 | 单曲循环过的那一首 | 你的本命 / 你的青春（纯怀旧期可换回） |

骨架（**投票互动 → 点赞收藏关注 → 下期预告**）和"关注我"必须保留，不得删减或改写为其他诉求。换槽只换上表两个名词，其余逐字不动。

**音频 / 时长**：固定句约 +6–7s，`OUTRO_D` 相应拉到 **~22–24s**；音乐床取**副歌段**铺到底再 `afade` 末 1.6s 淡出（**别用歌曲淡出尾**，太轻会 dead-air，见下「片尾 dead-air」），旁白段照常 duck 到 ~20–26%；固定句念完留尾再 fade，不硬切、不死静。

**画面**：可配轻量"投票 / 点赞关注"CTA 浮层并与投票 UI 同步亮起；但**不得出现任何平台水印、账号 ID、网址**（老铁律，成片不露 meta / 平台信息）。

## yt-dlp 规范

- **Cookie 文件（统一约定，2026-06 起）**：单一全量文件 **仓库根目录 `all_cookies.txt`**（一份浏览器**全量** cookie 导出，同时含 YouTube + Google + B站 三套登录态），YouTube 和 B站下载 / 搜索 / 校验全部读它。登录态文件含敏感凭据，已 gitignore。
  - **为什么是全量文件**：YT 过 bot 检查依赖登录态 cookie，其中 `LOGIN_INFO/SID/HSID/SSID/SAPISID` 等常落在 **`.google.com`** 域上，只导 youtube 标签页会漏 → 仍被 bot 拦（即便 `__Secure-3PSID` 在）。导"全部 cookie"才稳。
  - **唯一有效位置是仓库根目录**；**不得在 `sandbox/` 下创建、复制、覆盖第二份 cookie 文件**。所有脚本、下载命令、校验命令都必须直接读根目录 `all_cookies.txt`；发现 `sandbox/**/*cookies*.txt` 视为过期副本，应删除而不是继续使用。
  - 导出方式：浏览器装 "Get cookies.txt LOCALLY" → **导出"全部 cookie / All cookies"**（不要只导当前站）→ Netscape 格式 → 保存/覆盖到仓库根目录 `all_cookies.txt`。`document.cookie` 复制串拿不到 HttpOnly 凭据，不可用。
  - **向后兼容**：复用脚本（`check_yt_cookie.py`/`bili_search.py`/`bili_dl.py`）默认读 `all_cookies.txt`，缺失时才回退旧的 `www.youtube.com_cookies.txt` / `www.bilibili.com_cookies.txt`。新项目一律用 `all_cookies.txt`。
- **YouTube 登录态**（反爬：不带或缺登录态会报 "Sign in to confirm you're not a bot"）：
  - `all_cookies.txt` 须含 HttpOnly 认证 cookie（`LOGIN_INFO` + `SID/HSID/SSID/SAPISID/APISID` + `__Secure-3PSID`），其中多个在 `.google.com` 域 —— 全量导出才齐。`python3 tools/video/check_yt_cookie.py` 秒判。
  - **过期与更新**：标称过期约 1 年，但**实际寿命短得多**——YouTube 服务端频繁轮换 `*SIDCC`/`*SIDTS`，实践中常几天～几周失效。`check_yt_cookie.py` 只验**存在**不验**新鲜度**：cookie token 都在却仍 bot 拦 = 服务端已轮换、快照过期。
    - **bot 拦排查顺序（2026-06 实战）**：① 先 `brew upgrade yt-dlp`（旧版跟不上 YT player 改动也会恒 bot 拦，与 cookie 无关，本次从 2026.3.17→2026.6.9）；② 仍拦再判 cookie 过期 → 让用户**重新导出全量 cookie** 覆盖 `all_cookies.txt`。换 `--extractor-args player_client` 对登录态失效无效。
    - 让 cookie 更耐用：用**无痕窗口**登录 → 导出全部 → **直接关窗口、别登出**（避免主会话把快照轮换掉）。
- **B站登录态**（无登录态只能拿到 ≤720P；大会员/番剧/4K 必须）：
  - `all_cookies.txt` 须含 `SESSDATA`、`bili_jct`、`DedeUserID` 等（全量导出自带）。
  - 过期更新比 YT 更频繁（几周）；触发信号：清晰度被压回 720P 或 4K 选项消失 → 重新导出全量覆盖。
  - **B站搜索 yt-dlp 不能解析**，要用 API：`https://api.bilibili.com/x/web-interface/wbi/search/type?search_type=video&keyword=<关键词>`，response 里 `data.result[].bvid` 即视频 ID，URL 拼为 `https://www.bilibili.com/video/<bvid>`。
    - **必须 WBI 签名**（2026 验证）：普通 search 端点 + `yt-dlp bilisearchN:` 现在都返回 **HTTP 412 风控**。要先 GET `https://api.bilibili.com/x/web-interface/nav` 取 `wbi_img.img_url/sub_url` 的文件名 → mixin_key（固定 64 位重排表取前 32 位）→ 参数加 `wts` 排序 urlencode 后 `md5(query+mixin_key)` 得 `w_rid`，带 cookie + 桌面 UA 才通。**复用脚本 `tools/video/bili_search.py`**（用法 `python tools/video/bili_search.py "关键词" [n]`，读根目录 `all_cookies.txt`），输出 `bvid | 时长 | up主 | 标题`。
  - **B站下载 yt-dlp 报 HTTP 412 风控的救场（2026-06 验证）**：`yt-dlp` 的 BiliBili extractor 走的 webpage/playurl 端点会被 412 风控（即使 cookie 有效、search 与 `--skip-download --print` 偶尔能过），重试也基本恒 412。但**普通浏览器式 `curl --compressed` + 桌面 UA + `referer:https://www.bilibili.com/` + cookie 头能取到视频页**，页里内嵌 `window.__playinfo__`（DASH `baseUrl` m4s 直链）。**复用脚本 `tools/video/bili_dl.py`**（用法 `python tools/video/bili_dl.py <bvid> <out.mp4> [--max-h 1080]`）：curl 取页 → 解析 playinfo → 取 ≤max-h 优先 AVC 的 video + 最佳 audio 直链 → curl 下载 → ffmpeg mux 成 mp4。这是 B站下载被 412 挡住时的首选下载法。
- **切片**用 `--download-sections "*HH:MM:SS-HH:MM:SS"`，避免下整片（已验证：635s 视频只取 10s）。
- 已验证可用的切片命令（YouTube 与 B站同用一份 `all_cookies.txt`）：
  ```bash
  yt-dlp "<URL>" --cookies "all_cookies.txt" \
    --download-sections "*00:00:30-00:00:40" --no-playlist \
    -f "bv*[height<=1080]+ba/b[height<=1080]" \
    -o "downloads/%(id)s_%(section_start)s-%(section_end)s.%(ext)s"
  ```
- **格式选择**：
  - YouTube：默认最佳 ≤1080p 往往是 **AV1**。若下游要 FFmpeg 重剪/拼接，AV1 解码慢，改用 H.264：`-f "bv*[height<=1080][vcodec^=avc]+ba"`。
  - B站：4K 流是 AV1 + 单声道音频；想要立体声选 1080P：`-f "bv*[height<=1080]+ba"`（实测张韶涵《大小孩》4K 流为 mono）。
  - **B站「修复版」常是 Live 演唱会版本，不等于棚版 MV**：搜结果里 "修复版" 头条往往清晰度更高（甚至 4K60 杜比视界），但内容与官方棚版 MV 调性差很多。**选源先匹配 brief 意图，再看分辨率**——brief 要"原版 MV 棚拍"，就别被 1080P Live 修复版替换走。
  - **「李荣浩 直拍」「XX 直拍」类搜索常返回别人**：B站标题党严重，多个 "李荣浩直拍" 实测是红发青年乐手，不是本人。当事人特写要找具体节目源（《我是歌手》《天赐的声音》《歌手》等综艺纯享版，或本人确认的官方 Live），抓帧后**用户/我先肉眼验真再用**。
- 源信息（URL、时间码、下载时间、所选平台与原因）记录方式：_待定_（产物文件名已含 id + 时间段）。

## Bash / 后台任务

- **后台 bash（`run_in_background`）不继承前台 cwd**：foreground 用 `cd` 切到子目录后跑 bg 命令，bg 命令仍在调用时的 cwd（项目根）。**bg 命令一律用绝对路径**，相对路径会 silently fail。
- **zsh nomatch 失败终止脚本**：`rm renders/work-*` 在没匹配时 zsh 默认报错并退出（bg 任务以 exit 1 结束）。改写 `rm -rf renders/work-* 2>/dev/null` 或 `setopt -u nomatch`。
- **bg 任务空文件 ≠ 完成**：`until [ -f X ]` 在 ffmpeg 创建空头文件时立即满足条件→提前退出。判完成用文件大小 `[ "$(wc -c < X)" -gt N ]` 或 ffprobe 能解析。


## HyperFrames composition 规范

- 版本：当前用 `hyperframes@0.6.47`（init 时写入各项目 package.json scripts，含 dev/check/render/publish）。
- 渲染链路已验证：`init --example blank` → 编辑 `index.html` → `npm run check` → `npm run render`，产物 1920x1080 h264 30fps MP4。
- 每个计时元素必须 `class="clip"` + `data-start`/`data-duration`/`data-track-index`；timeline 须 `paused` 并注册到 `window.__timelines["<composition-id>"]`。
- 只允许确定性逻辑：禁用 `Date.now()`、`Math.random()`、网络 fetch（否则渲染不可复现）。
- **写/改 composition 前先调用 `/hyperframes` 等 skill**——模式不在通用 web 文档里。项目内 `CLAUDE.md` 有完整规则表。
- 统一画布尺寸 / 帧率：blank 默认 1920x1080 横屏 30fps；自媒体短视频若走竖屏需改为 1080x1920，_待定_。
- composition-id 命名规则：_待定_。
- 动画库默认选型（GSAP / anime.js / …）：blank 默认 GSAP。
- 字幕样式、品牌片头模板：_待定_。**片尾固定 CTA 已定** → 见「固定结尾配音」硬约束章节。

## 全链路（footage 进 composition）— 已验证

`sandbox/clip-demo/` 跑通：yt-dlp 切片 → HyperFrames `<video>` footage + 标题/字幕叠加 → MP4（h264 + aac，含原片音轨）。要点：

- **素材与 `index.html` 同目录**（`clip.mp4` 放项目根），`src="clip.mp4"` 相对引用。
- **视频**：`<video muted playsinline>`，计时属性(`data-start`/`data-duration`/`data-track-index`)**直接放在 video 元素上**，不要套进计时 div。全屏用 CSS `position:absolute; inset:0; object-fit:cover`。
- **音频独立**：原片声音用单独 `<audio src="同一个mp4">`，否则成片没声音。
- **层级靠 CSS `z-index`**，`data-track-index` 不决定视觉层级（footage z-index:0，叠加层更高）。
- **动画只碰视觉属性**，不要 `video.play()`；timeline `paused` 注册到 `window.__timelines["main"]`。
- **字体**：`-apple-system` 等不在自动解析表里会 lint 告警并回退通用字体。CJK 在 headless Chrome 能正常渲染（实测中文无方框），但正式成片应放 `.woff2` 到 `fonts/` 并加 `@font-face` 锁定字形。
- 渲染日志里 `[non-blocking] ... 404` 无害，可忽略。
- 10s/1080p 含 footage 渲染约 31s（blank 纯图形那条仅 6s，footage 更慢）。

## 配音 + 字幕同步（多段旁白）— 已验证

`sandbox/pipeline-demo/`（60s 成片：切片 + 7 段男声旁白 + 同步字幕 + 片头片尾）跑通。可复用做法：

- **分句配音**：旁白按句切分，每句单独用 `tools/tts/narrate.py` 生成一个 wav，拿到各自时长后再排时间轴。这样**字幕 = 正在念的那句**，天然精确同步，不必跑 transcribe。
- **顺序排轨**：多个 `<audio>` 放同一 `data-track-index`，按累计时长设 `data-start`（句间留 ~1s 间隔更自然），互不重叠即可。
- **字幕**：每句一个 `class="clip"`，`data-start`/`data-duration` 与对应音频一致；入场 `gsap.from`、结束前 `gsap.to` 淡出。
- **轨道分配**（`data-track-index` 不管层级，层级用 z-index）：footage=0、压暗 scrim=1、字幕=2、音频=3、片头/片尾=4。同轨元素时间不能重叠（scrim 跨全程要独占一轨，否则和片头片尾撞）。
- 用脚本程序化生成 `index.html`（读 `narration.json` 算时间轴）比手写多段更稳。
- **footage 关键帧坑**：yt-dlp 下来的片段关键帧可能稀疏（GOP 数秒），HyperFrames 逐帧 seek 时告警、可能卡顿。实测短片未见冻结，但正式成片建议先重编码加密关键帧：
  ```bash
  ffmpeg -i in.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 -movflags +faststart -c:a copy out.mp4
  ```
- CJK 字体：命名 `PingFang SC` 等会 lint 告警（不在自动嵌入表），但本机系统装了该字体，headless Chrome 实测能正常渲染中文。

## 自媒体视频（通用能力与默认）

> ⚠️ 不要思维定势：成片**不止 TOP 盘点**，也有不区分排名的形式（人物/歌曲解读、主题串烧、科普合集等）。下面是**跨格式通用**的能力和默认；具体"格式"只是呈现方式，按当期任务定。

**通用默认（用户已确认，可被单期任务覆盖）：**
- **画幅**：竖屏 **1080×1920**（短视频主流）。
- **素材来源**：默认**我来搜并选**——用户给歌手+歌名/主题+倾向，我**同时在 YouTube 和 B站搜**（见"素材源平台"硬约束），按质量挑段（默认现场/官方演出的名场面/副歌段）、切片；拿不准的版本先给候选并标明各平台候选规格。
- **解说文案**：默认**混合模式**——用户写重点句/必须准确的点，其余我扩写成口播稿，出片前可审。
- **配音**：默认男声 `zm_yunxi`，女声 `zf_xiaoyi` 仅在要求时（见配音规范）。
- **审美**：开期先定一份 `design.md`（配色/字体/动效基调）并全期统一，参考 `/hyperframes` 的 design 流程。默认"干净高级、暗底 + 单一强调色"，除非指定综艺花字等其他风格。
- **结构通用件**：footage（`<video muted>`）打底 + 大字标题/信息 + 解说字幕 + 片头片尾；原声可作 BGM 并按下面 ducking 处理。
- **信息层级去重**：同一个语义只保留一个主标识源，尤其是排名 / 序号 / 歌名。若画面已有"第X首 + 歌名"标题，就不要再叠右上角流水号、左上角浮层 bug、二级角标等同类元素；进入 full-music 展示段后，除非用户明确要常驻信息条，否则排名/歌名浮层应淡出，避免压住 MV 也避免重复标记。QA contact sheet 必须专门看一遍是否有同义元素堆砌。

### 展示段硬规则（竖屏画面比例 + 副歌时长）— ⚠️ 用户多次反馈，**默认必须遵守，不要再犯**

**(A) 竖屏化默认 = letterbox 保原比例，禁止激进裁切放大。**
- **默认**：footage **全宽呈现、保留 MV/Live 原始横纵比**（信箱式：fg 缩到 1080 宽居中、上下用模糊背景填充），**不放大画面**。只裁掉烧死歌词/台标/水印的**横向窄带**（全宽保留）。
- **禁止**：把画面裁成竖条再放大贴宽——会把主体裁出画 / 只剩半边。**男女合唱 / 双人 / 多人 / 宽机位**素材尤其禁止（两个主体分布在画面左右，任何竖裁都会切掉一个人）。
- **唯一例外**：单主体**全程稳定居中**且逐帧确认裁切框不切到主体时，才可用"竖向裁切放大贴宽"。拿不准就 letterbox。
- 实现：复用 `tools/video/vfill.sh`——把 crop 传**全宽横带**（`W=源宽 : H=裁掉烧词后的高度 : 0 : Y`）即得 letterbox；传**窄竖条**才是放大裁切（默认别这么做）。
- "清晰度 / 画幅没源那么满"可接受（用户已确认）；"人物被裁半 / 看不全"**不可接受**。

**(B) 展示段 = 一段连续副歌（含前后余量），不要碎镜快闪、不要把歌切短。**
- 每首给**一段连续**的副歌 / 代表段，**前后都留余量**（前奏带入 + 副歌 + 收尾），让观众"听得爽"。
- **时长与旁白体量匹配**：旁白长，展示也要长——**不得旁白讲很久、歌却随便放一小段就跳过**。解说盘点类单首展示 **≥ ~25s**（甚至更长，**不设上限，以观赏体验为准**）；只有 60–90s 快节奏短盘点才用 12–18s 短段。
- **优先「连续整段 + letterbox」**：让 footage 窗 == 音乐窗（同源同窗）→ 口型天然同步，且 MV 自身的内部剪辑照常出现没问题。**不要**默认把多个碎镜头拼成蒙太奇。
- **「歌手镜头蒙太奇」仅作救场**：当连续段实在不可用（全程拍不到主体 / 大量空镜 / 烧字裁不净）时才拼，且救场段也要够长、并逐镜抽帧验证。
- QA：抽帧确认长 clip **播放到末尾无黑屏 / 冻结**（`<video> data-duration ≤ clip 实际时长`，clip 切到 SHOW+余量）；各首副歌响度一致（~-15dB）。

**(C) 展示段两条入/出对齐硬规则 — ⚠️ 用户实测反馈，反复犯，已机械化闸门强制（见文末「展示段对齐闸门」）。**

> **入点（问题1）**：副歌人声要在**转场配音快收尾时正好进来**并贯穿展示段，别让副歌被旁白盖走、推满音量的展示段落到纯器乐。
> **出点（问题2）**：展示段结尾要落在**唱完一句之后或纯器乐 gap**，**绝不因时长限制把一句唱到半路硬切**（人声戛然而止，观感最差）。

切片时**必须把转场配音的时间差算进去**。每首结构是：`转场旁白（音乐 duck 成床）→ 消化位/swell → full-music 展示段`。旁白会盖住片段开头约 `LEAD + voice_dur` 秒（≈15-19s）。**问题1 的坑：把唱的副歌放在了片段开头，结果整段副歌都被旁白盖住，旁白一结束、音量推满的展示段反而落在了间奏/前奏/outro 纯器乐段——观众真正想听的"炸点"全程没人声，只剩背景乐。**（华晨宇期 斗牛九周年：副歌"野性坦露"在旁白下，展示段是管弦 outro；烟火：展示段落在 30s 间奏。用户一耳听出。）

- **对齐原则（理想）**：让一段连续唱的副歌 **在转场旁白结束前约 2 秒入声**（vocal onset），唱声先在旁白尾巴下起来，再随 swell 推满进展示段——既丝滑、展示段又全程有唱。
- **切片公式**：`clip_start_src = vocal_onset_src − (LEAD + voice_dur − 2)`。即把"副歌入声"对到 segment-local 时间 `narr_end_local − 2`。（`full_start_local = LEAD + voice_dur + 0.25 + DIG`；展示段 = `clip_start + full_start_local` 起的 `SHOW` 秒，必须整段落在唱的区间。）
- **副歌不够长就缩 SHOW**：不少歌单段连唱只有 ~22-26s，硬铺 38s 会把尾巴拖进器乐。这种把 `SHOW` 调到刚好盖住连唱段（≥25s 即可），别让展示段尾段变纯器乐。
- **变量命名防误用**：如果 build 脚本使用 `show_start` / `W` / `highlight_start` 这类字段，它必须表示**成片 full-music 展示段开始时对应的源时间码**，不是"这首歌从哪开始切"，也不是"副歌大概从哪开始"。实际预切起点应由脚本倒推：`media_seek = show_start - full_start_local`。改完必须抽成片 `full_start` 后 20-30s 的 contact sheet，确认画面歌词/口型已经进入人声段。
- **怎么判"在唱"（关键，单一方法都不可靠）**：
  - `vocal_segments.py` 对**慢歌/民谣可靠**（人声清晰），对**响摇滚/满编曲管弦乐会漏报**（人声频带被乐器淹没 → 整段被判无人声，华晨宇《我管你》整首漏）。
  - 这类源用**烧死卡拉OK歌词是否在"逐句推进"**当可靠指示：歌词逐行换 = 在唱；同一行**静止不动十几秒** = 唱过一次后歌词 lingering、实际是器乐/holding（华晨宇斗牛"野性坦露"静止42s即此坑）。
  - 拿不准 / 是用户重点曲：**导 26s showcase mp3 给用户耳听确认**（`ffmpeg -ss <local> -t 26 -i clip.mp4 -vn -af loudnorm out.mp3`），别只靠工具下结论。
- **出点对齐（问题2，硬规则）**：展示段结尾 `show_end_src` **不得落在某句人声的半路**。允许落在：① 一句人声段结束后 ~1.2s 内（唱完整句再切），或 ② 两句之间的器乐 gap。**副歌不够长就缩 SHOW 对齐到最近的句末/gap，宁可短一点也别切半句**；副歌够长但 SHOW 设过头会把结尾顶进下一句开头（同样违规）——把 `show` 调到落在句末。
- QA 收尾：成片对每首展示段（旁白结束后那 30s）抽查确实有人声，不是只有伴奏；并核展示段最后 2s 是收在句末/器乐，不是切在唱字中间。

**🔒 展示段对齐闸门（机械化强制，build 不过就不出 master）— 反复犯 → 不再靠人肉算。**

`tools/video/showcase_align.py`：用各 clip 的人声段（`vocal_segments.py` 产出的 `vocal_analysis.json`）机械校验上面两条，**违规 `raise SystemExit`**。它把"凭感觉填 `ch_off`/`show`"变成可验证的闸门。

- **接入（build 算完 blocks、建 master 之前，一行）**——`countdown_build.py` 模板已内置，复用 `full_build.py` 时照抄：
  ```python
  import sys; sys.path.insert(0, str(ROOT.parents[2]))   # 让 tools 可 import（ROOT=项目目录）
  from tools.video import showcase_align
  showcase_align.gate(blocks, ROOT/"probe"/"vocal_analysis.json",
                      consts=dict(POST=POST, DIG=DIG), plan_path=ROOT/"probe"/"showcase_plan.json")
  ```
  `blocks` 每首需含 `clip/start/narr_end/full_start/end`（可选 `mseek`=预切 `-ss`）。闸门自动换算源时间码：
  `narr_end_src=mseek+(narr_end-start)`、`show_start_src=mseek+(full_start-start)`、`show_end_src=mseek+(end-start)`。
- **前置**：build 前先跑 `tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 -o probe/vocal_analysis.json`（人声段基准 = 各 vert clip 源时间，与 `ch_off` 同基准）。
- **反推切点（别手填）**：拿不准 `ch_off`/`show` 就让工具算：
  ```bash
  tools/tts/venv/bin/python tools/video/showcase_align.py plan \
      --vocals probe/vocal_analysis.json --clip vert_p4_wait --voice-dur 14.0 --near 105
  ```
  它按"人声入点 = 旁白收尾前 2s"给 `ch_off`，按"结尾落句末/gap 且 ≥25s"给 `show`。
- **单独复核**（QA 阶段，不接 build 也能跑）：`showcase_align.py check --plan probe/showcase_plan.json --vocals probe/vocal_analysis.json`，违规 exit 1。
- **降级而非误杀**：响摇滚/满编曲人声检测不可靠（`vocal_segments` 漏报）→ 闸门判 `WARN` 不阻断，但**必须导 26s mp3 人工耳验**（命令工具会打印）。慢歌/民谣检测可靠，照 FAIL 阻断。
- **误报逃生**：确属工具误判时 `SHOWCASE_OVERRIDE=1 python build/full_build.py` 跳过，但要在交付里说明为何跳过。

> 验证项目：`sandbox/zwtl-duet-pk/`（周王陶林男女合唱PK，4:25）。早期用竖裁放大→双人被裁半、副歌 14s 太短被吐槽；改 letterbox 全宽 + 连续 27–32s 副歌后达标。
> 验证项目：`sandbox/huachenyu-hardest-top5/`（华晨宇最难5首）。初版 4/5 首展示段落在器乐段（唱声全被转场旁白盖住），按 (C) 重对齐 vocal onset 到旁白收尾前 2s 后修复。

### 冷启动执行：从 brief 到成片

新窗口接到视频 brief，照 **`tools/video/README.md` 的 Runbook** 跑（0 启动自检 → 1 解析 → 2 样片 → 3 素材 → 4 旁白 → 5 音频 → 6 合成 → 7 渲染+mux → 8 QA）。复用脚本都在 `tools/`，不在可丢弃的 `sandbox/`：
- `tools/tts/narrate.py`、`tools/video/narrate_segments.py` — 配音
- `tools/video/vfill.sh` — 竖屏填充
- `tools/video/countdown_build.py` — 音轨 + 合成构建模板（按 brief 改 songs/时长/文案）

**用户 brief 的标准格式**（缺省项按本规范默认值处理）：
```
盘点主题/标题：
项目slug：
画幅：默认竖屏1080x1920 | 时长：默认按内容
揭晓顺序：难度排名→倒数N→1 | 主题/代表作→按脚本叙事序
配音：默认男声 zm_yunxi（写“女声”则 zf_xiaoyi）
每首：序号 / 歌手 /《歌名》
  素材：URL+切点 | 或 搜索倾向(官方MV/Live/原唱 + 想要的段落)
  旁白：逐字稿(照念) | 或 要点(我扩写)；节奏需要可适当精简
  字幕短标签：(可选)
开头文案与画面意图：(可选)
结尾文案：(可选，仅作品 outro 的内容总结/升华) —— 固定引流 CTA 自动追加为最后一句，brief 不写、不覆盖（见「固定结尾配音」硬约束）
```

### QA 方法论（我看不到画面、听不到声音 → 必须用工具验证，不能凭感觉说“好了”）

- **画面**：`ffmpeg -ss N -i v.mp4 -frames:v 1 f.png` 抽帧，用 **Read 工具实际查看**；多帧可 `hstack` 成 contact sheet。下载的每段素材也要先抽帧确认是真动态 MV、记录水印/字幕/画幅。
- **音频**：`silencedetect`（无 >1s 静音）、`volumedetect`（各首副歌均值一致、旁白段音乐明显更低）。**绝不靠“应该没问题”下结论**。
- **泄漏**：确认成片画面内无水印/网址/提示词/路径/项目内部词（裁切 + 干净叠层）。

### 旁白与音乐的节奏（硬规则，来自 wemedia/AGENTS.md 实战经验）

- **先配音，后进音乐**：章节/开场的介绍旁白先讲，期间音乐**最多是低音量床**（或无），不要一上来 voice+music 同时全量"轰炸"。**真正全量的音乐留给无旁白的副歌/展示段**。
- **旁白收尾留消化位**：每段介绍旁白讲完保留 **0.8–1.2s** 缓冲再切歌/进下一段；不得最后一个字刚落就硬切，也不得变成死静——这段用音乐床淡入 / 画面轻微运动 / 素材预入声支撑。
- **章节交界**不得出现"配音停 + 音乐未起 + 画面静止"的空等。
- 典型每首结构：介绍旁白（音乐床）→ 消化位（床淡入/swell 起）→ 副歌展示（音乐全量、无旁白）。
- **QA**：成片跑 `ffmpeg -af silencedetect=n=-35dB:d=1`，不得有 >1s 整片静音；并抽测旁白段 vs 展示段音乐音量确认有明显高低差。

### 多段成片的实战经验（张韶涵暗黑面全片验证）

- **全片响度统一**：不同歌曲源响度差异大（实测副歌 -11～-28dB）。每首音乐先 `loudnorm=I=-14:TP=-1.0:LRA=11` 归一化；暗调/安静的歌（如《全面沦陷》）loudnorm 后仍偏低，再加一档静态增益（+7dB 左右）补偿。目标各首副歌均落在 ~-15dB。
- **逐段建音轨再 concat**：每首一个自包含音频段（旁白+该曲 床→swell→展示），用 `ffmpeg -f concat` 拼成总 master，比一条巨型 filtergraph 可控。
- **竖屏适配**：中心**竖向裁切(~4:5)放大贴宽 + 模糊背景填满边距**，比"16:9 居中小带"饱满得多，且顺带裁掉边角台标。**暗调/Live 多机位**素材要用更温和的裁切（保留更多宽度），否则镜头切到全景时主体被切出画。
  > ⚠️ **此条仅适用「单主体全程居中」**。双人/合唱/多人/宽机位一律改 **letterbox 保原比例**（不放大），否则主体被裁半——见上「展示段硬规则 (A)」。
- **相邻 footage 交替轨道**（track 0/6 轮换）：HyperFrames 里同轨片段**首尾相接也算重叠**会报错；交替轨道规避（视觉层级仍靠 z-index）。
- **媒体元素必须有 `id`**：`<video>`/`<audio>` 没 id 渲染会被冻结/静音（lint 会报 media_missing_id）。
- **主题盘点 ≠ 难度排名**：本片按脚本 1→5 叙事顺序（立论曲→高潮收尾），不套"倒数揭晓"。是否倒序看选题性质。

### 老素材 / 难度盘点的实战补充（窦唯最难5首验证）

- **难度排名默认倒数 5→1**：把最难/最炸的留作压轴（窦唯片压轴《别来纠缠我》），第1名给红色"公认天花板"角标强化。
- **成片内禁出现描述视频自身机制的 meta 文案**（如"倒数开始/从第5名"）——属项目内部框架，用户明确不接受出现在画面。口播里的"第五…第四…"排名播报和数字角标 OK，旁白式 meta 旁注不 OK。
- **密集摇滚定不了副歌位**：满编曲老摇滚整首 RMS 几乎持平（`volumedetect` 各 5s 切片差 <1dB），靠响度找高潮无效。改用**歌曲结构常识 + 抽帧看画面**定展示段，并把"高光是否最具代表性"明确交回用户耳朵定夺。
- **老素材普遍标清且带烧死字幕/台标**：4:3 标清用顶部对齐 crop（如 `384:400:128:0`）裁掉底部歌词字幕；做旧/发暗的源（如《靠近我》）vfill 前先 `eq=brightness=0.10:saturation=1.12:contrast=1.06` 提亮（vfill 的 BR 只作用于模糊背景，不提亮前景）。
- **水印垂直范围常超目测**（李×杨时间线《幸福菓子》验证）：SONY BMG 等老唱片公司水印实际占 y:0-75（看起来只在 y:0-45），底部烧字常占 y:340-480（不止最后两行）。**crop 前先二分抽断面**：`ffmpeg -ss N -i src -vf "crop=W:60:0:y" -frames:v 1 probe.png`，y 取 50/100/150/200/300/350，看哪一行水印/字幕消失，定 crop 安全区。**bg 也会显示残留水印**：vfill 的 bg 用 fg 同样的 crop 区域 scale up 后模糊，fg crop 内有水印 → bg 模糊层也露出（模糊后的文字仍可识别）。所以 crop 必须把水印**完全**裁掉。
- **极冷门曲只有超低清源**：窦唯《别来纠缠我》全网最佳仅 320×246 黑白——黑白颗粒反而贴合"金属嘶吼"压轴，但务必先把"能接受的最高源清晰度"回报用户。排除 Topic 静态图 / 歌词视频（静态+第三方水印）/ 双字幕无法裁净 / 非原唱者的后期重组现场。
- **跨歌响度统一**：逐首 `loudnorm=I=-14` 后五首副歌落 -18~-19dB、彼此差 <1dB 即达标（一致性 > 绝对值；偏轻可整体抬 2–3dB 再 mux）。

### 老素材 / 难度盘点的实战补充（周深最难5首验证）

- **yt-dlp webm 音轨被 download-sections 截断的坑**：opus-in-webm 切片，从 `-ss 0` 再 `-t` 重剪时，**音频流会比视频短几秒**（实测 video 26.4s / audio 21.5s），ffprobe 还读不出 opus 流时长（N/A）。后果：成片展示段音乐戛然而止。**修法**：先把整段 webm 整体重编码成 mp4（`-c:v libx264 -c:a aac`，音频补全），再从 mp4 切；或干脆用 **输出端 seek**（`-i in -ss S -t L -vn -c:a pcm_s16le out.wav`）抽干净音轨，build 里用这条 wav 当音乐源（与视频同区间→口型仍对齐）。中段 `-ss` 切的片不受影响，只有从头切才坑。
- **多机位综艺极难锁长特写**：周深现场（微博盛典/歌手/声入人心等）每 2–4 秒在特写↔全景间切，没有连续 5s+ 的稳定特写。策略：每首一条**连续素材**（自带音轨保口型），把片段**结尾 trim 到一个特写帧**，展示段=片段最后 ~6s（用户已确认"优先锁特写、可接受略短展示"）；narration 期混入全景无妨（标签压下三分之一）。
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
  ffmpeg -i rendered.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest final.mp4
  ```
  成片以 `final.mp4`（mux 后）为准，而非 HyperFrames 直接产物。

### HyperFrames render 默认参数（短视频自媒体）

- **`--sdr` 必加**：HF 渲染会从 **任意一个** 源做 HDR auto-detect。Bili「杜比视界」流（如 LIKE A STAR 巡演 BV15m411k7Yi）一旦进 footage，整片输出会被升级成 **HLG (BT.2020) 10-bit H.265**——抖音/小红书/视频号普遍不收，播放器色彩翻车。Render 命令一律：
  ```bash
  npx hyperframes render --output renders/full_raw.mp4 --sdr
  ```
- **`<video>` 不能控 `currentTime`**：HF 渲染期间会把 video 元素的 currentTime 锁到合成时间。要让 footage 从源的某个时间码起播，**必须 ffmpeg 输出端预切**（`-ss S -i in -t L -c:v libx264 -g 30 -keyint_min 30 -an out.mp4`），切完的视频从 0 开始播。
- **同轨 footage 不能贴边**：相邻 footage 片段交替放在 track 0/6（详见上文）。
- **⚠ 多段 footage 长片：拼成单条 footage_track，HTML 只挂 1 个 `<video>`（硬规则，2026-06 柯南TOP10 验证）**：一条竖屏长片若挂 **多个 `<video>` 元素**（如 12 段 footage 各一个），HF 渲染会在页面初始化时**同时为每个 video 建 frame-player**，Chrome 直接挂死——报 `Runtime.callFunctionOn timed out / protocolTimeout`，**帧 0 就超时**，多 worker（-w4）会 thrash 更快崩、**单 worker（-w1）也卡在 setup 不出帧**。**解法**：把所有 footage 段按时间线顺序 ffmpeg concat 成**一条连续 `footage_track.mp4`**（与各段时长对齐），HTML 只挂**一个** `<video data-start=0 data-duration=total src="footage_track.mp4">`。单 video = 已验证的 clip-demo 轻量模式，一次过（16110 帧 -w2 约 11min）。叠加层（scrim/卡片/字幕）照常多 track。**`HYPERFRAMES_EXTRACT_CACHE_DIR` 环境变量**可缓存抽帧、重试不重抽。
- **GSAP exit hard kill**：每个 `tl.to(..., {opacity:0})` 后要加 `tl.set("...", {opacity:0}, end_time)`；否则非线性 seek 时 footage / overlay 可能残留可见——lint 会以 `gsap_exit_missing_hard_kill` 告警。
- **字体：用本机 @font-face local()，别指望 Noto auto-fetch（0.6.69 验证）**：`hyperframes@0.6.69` 的 lint 把 `Noto Serif/Sans SC/JP` 判为**不在 auto-resolve 列表**→ 渲染回退默认字体、字形错。**改用本机系统字体 + `@font-face{src:local(...)}`**：中文无衬线 `PingFang SC`、中文衬线 `Songti SC`、**日文（含片假名，如クロノスタシス/スピッツ）用 `Hiragino Mincho ProN`/`Hiragino Sans`**；等宽 `JetBrains Mono` 仍可 auto-fetch。headless Chrome 能正常渲染这些 local 字体。
- **`composition_file_too_large` warning 可忽略**：单线性长片（330+ 行）不适合拆 sub-composition；这条 warning 是文档建议不是 error。

### 长篇叙事盘点 / 音乐时间线的实战补充（李荣浩×杨丞琳时间线验证）

> 验证项目：`sandbox/lirh-yangcl-timeline/`（5 首歌 6:33 竖屏纪录片式时间线，按叙事序而非倒数）。

**与 60-90s TOP 盘点的关键差异**：单片 6-8 分钟，5 首歌每首 60-90s，每首要求"进入 → 旁白铺垫 → 消化位 → swell → 副歌展示 → 中段金句 → 转场"七阶段。

- **时长基线**（5 首歌 ~7 分钟总时长）：
  - `LEAD ≈ 0.15s`（不要用 0.6，否则章节交界会出现 >1s 静音）
  - `PRE_VOICE ≈ 0.8s` 音乐床起 ramp
  - `POST_VOICE ≈ 1.2s` 消化位
  - `SWELL ≈ 1.5s` 音乐升起
  - `HIGH_BASE ≈ 40-45s` 副歌展示（前 4 首），`HIGH_LAST ≈ 55s`（finale）
  - `MID_OVER ≈ 5s` 中段金句叠副歌后半段
  - 整片 ≈ `intro 17s + 5 首 × (~70s) + outro 16s ≈ 393s = 6:33`，落在 brief 6:30-8:30 的目标区。
- **章节交界防死静**（CRITICAL，QA 必查）：每首歌段开头 `LEAD` 是音乐床为 0 的硅。如果上一段（如 intro）结尾也无音乐，跨段会形成 **>1s 静音**——违反节奏硬规则。**修法：intro 段必须铺低音量 ambient bed**（用 s5 或任意一首歌的器乐尾声作 0.18-0.20 增益床，全程 fade in/out）。intro 不能是"纯人声 + 静音背景"。
- **多 footage 段必须预切**（见上 HyperFrames render 章节）：每首歌段 `<video src="clips_seg/<key>.mp4">`，其中 `clips_seg/<key>.mp4` 是从 `vert_<song>.mp4` 输出端切出的对应段（按 mseek 起始）。HF 不能在 render 时控 currentTime。
- **跨章节响度统一**（同张韶涵章节规则）：副歌段 5 首 -14.8 ~ -16dB，差 <1.2dB 即达标；旁白段 -21 ~ -24dB（与副歌差 7-10dB 体现 ducking）。

### 长篇片的封面（cover frame）

封面要求**第 1 帧可直接作社交平台缩略图**。**必带真人头像**（用户多次明确要求 — 见 [cover-needs-real-people 用户偏好]）。

- **头像优先级**：① **用户直接提供合照**（如 `raw/li-yang.jpg` 婚纱照） > ② 当事人确认的官方 4K Live 直拍 > ③ 综艺纯享版正脸帧。**绝不**用：MV 演员替身（如李荣浩《年少有为》《模特》MV 主角是演员不是他本人）、Topic 静态图、第三方搜出来的 "XX 直拍"（标题党严重）。
- **当 brief 涉及双人**（如"A 写给 B 的歌"），**第一时间问用户要 2 人合照**，比花 30 分钟在源里翻找快几倍。把图放 `raw/li-yang.jpg` 这类位置，build 时 ffmpeg crop 两个 280×280 头像到 `hf/cover_assets/`。
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
- **封面 5 节点列表**：节点 padding `18px 0`、序号 32px、歌名 44px、年份 22px 右对齐。**不要**用默认 padding 14px + 22px 序号——行间太挤、扫不到。

### 渲染迭代成本

- 一次 1080×1920 6:30 全片渲染 ≈ **8-10 分钟**（5 workers），加 mux/QA 抽帧约 12 分钟一轮。
- **每次迭代前先把 QA frames 全列给用户审**，避免"改了一处再渲 10 分钟才发现另一处也错"。
- **样片先行铁律的例外**：当 brief 极详细（设计稿/调色/排版都明示），且用户希望直接出全片，可跳过 90s 样片步骤直接全渲——但必须提前对齐缩水的部分（粒子动画、专业 AE 形变转场等），避免渲完才发现缺。

### 展示段选源：概念/多机位 MV 的「歌手镜头蒙太奇」（吴青峰为别人写的歌 TOP5 验证）

> ⚠️ **默认优先「连续整段 + letterbox」**（见「展示段硬规则」），蒙太奇仅在连续段实在不可用时救场。本节是救场技法，不是首选。

> 验证项目：`sandbox/wuqingfeng-for-others/`（5 首竖屏盘点 3:32，一次渲染成功）。

并非所有 MV 都能切出 14s 连续歌手特写。**快切概念 MV（蔡依林《怪美的》护士/法庭/舞群每 1-2s 切，含空镜）、艺术柔焦 MV（杨丞琳《年轮说》大量抽象纸环空镜）、剧情 MV（张韶涵《有形的翅膀》全程高频穿插男主角/小孩；杨丞琳《带我走》男主角情侣戏）** 都给不到连续主体特写。处理分两类：

- **实拍同步（首选）**：单主体 MV（张惠妹《掉了》）或干净 Live（杨丞琳《带我走》2026 红裙纯净收音）能连续锁主体时，`clips.sh` 切片 `start` == `full_build` 的 `W`（音乐窗起点），footage 与音乐口型同步。
- **歌手镜头蒙太奇（救场）**：概念 MV 拼 3-4 个该歌手的独立镜头（`build/montage.sh`：每镜 `输出端seek 切→各自 crop 居中→vfill→concat`），**音乐另取该曲副歌**（与画面解耦）。慢歌/快切歌口型微差不可察。每个子镜头要**逐一抽帧验证**：剔除他人（男主角/伴舞/观众）、空镜、烧死字幕（各镜头 crop 的 H 单独压低排除底部歌词）。
- **找连续窗的工具链**：① 6 帧总览联系表定场景；② 候选窗每 2s 密集抽帧确认主体是否全程在场；③ RMS 扫描（`ffmpeg volumedetect` 逐 5s 窗）定副歌能量峰做音乐 `W`，比凭感觉准。
- **「主题同框」可凌驾画质**：本片压轴《有形的翅膀》弃官方 MV（穿插男主角），改用 **张韶涵 feat. 吴青峰同台合唱 Live**——词作者与演唱者同框、结尾相拥，把"为别人写歌"主题在压轴收束。盘点选源不只看清晰度，**叙事收束 > 分辨率**时大胆换源（旁白同步改写衔接画面）。
- **多歌手盘点封面**：主题围绕"幕后创作者"时，封面主角放**词曲作者本人正脸**（非各演唱者拼贴），更聚焦、更切题（满足真人封面硬约束）。
- **片头/片尾 dead-air**：封面 5s 若纯静音→silencedetect 报开头 >1.5s 静音。补**低音乐床**（该期某曲 loudnorm 后 vol~0.20 fade-in，非白噪音）。outro 床**别用歌曲淡出尾**（本身太轻→片尾又 dead-air），取副歌段，末 1.6s fade。

### 格式之一：音乐 TOP 盘点

在通用能力之上加排名呈现：**倒数揭晓 N→1**（悬念感）、每条大号排名 + 歌手 + 歌名、整期 60–90s 时每首展示 12–18s。其余（搜素材、配音、ducking、design）同上通用规范。非排名类视频不套这些排名件。
> ⚠️ 12–18s 仅限 **60–90s 快节奏短盘点**。**带长解说的盘点**（旁白每首 15s+）必须按「展示段硬规则 (B)」给**连续 ≥~25s** 的副歌，别用短段把歌切了。

### 格式之二：AI 跨时空同台（音乐实验）

> 验证项目：`sandbox/dbmh-ai-stage/`（窦唯/王菲/窦靖童《Don't Break My Heart》三人接力实验，2:54）。

把同一首歌的多个不同年代/不同版本拼成"AI 同台接力"，让观众感觉三人/多人像在同一场演出里依次接唱。本质上是**音乐实验**，不是盘点解说。

**与盘点格式的关键差异：**
- 不分排名、不分章节解说，**主体是音乐而非旁白**。
- 旁白只用在**开头 + 结尾**（声明 + 收尾），中段全程让音乐和画面说话。
- 必须显式声明 **"AI 剪辑实验｜非真实同台演出"**（开头小字 + 全程右下角小角标 + 结尾文案），避免误导观众以为是真实演出。
- 不能出现描述视频自身机制的 meta 文案（同[no-meta-text-in-video 用户偏好]）。

**接力时间码定位（核心）：**

错误做法：用 RMS 能量峰找"高潮段"做接入点 — 能量峰常在副歌中段，错过了 verse/chorus 入口；同一首歌不同版本的 verse / chorus 入口时间码完全不同，必须**逐版本精确定位**。

正确做法：用**人声段检测**找每个版本的 verse 1 / verse 2 / final chorus **入口时间码**，再让接力对齐到歌曲结构而非时间偏移：

```python
# tools/video/vocal_segments.py (可复用)
y_harm, _ = librosa.effects.hpss(y, margin=3.0)         # 谐波分离
S = np.abs(librosa.stft(y_harm))
voice_mask = (freqs >= 200) & (freqs <= 3000)            # 人声频带 200-3000Hz
voice_rms = np.sqrt(np.mean(S[voice_mask] ** 2, axis=0))
# 平滑 + 60th percentile 阈值 → 连续 >2s 视为有效 vocal 段；>1.5s gap 视为段间
```

输出每段的 `vocal_segments=[[t_start, t_end], ...]`，根据 vocal 段密度判断 verse / chorus / 桥段：
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

> 验证项目：`sandbox/angela-ai-mv-covers/`（张韶涵 e200 / 激进版音色 MV，已持续追加多批独立 MP4，完整清单见该目录 `README.md`）。

当 brief 明确是“AI 克隆/训练歌手音色制作 MV”“如果某歌手唱某歌”，且用户给了可直接使用的训练音频 WAV 时，默认复用 `sandbox/angela-ai-mv-covers/` 继续追加歌曲，不新开实验目录。只有当用户明确要求新项目，或任务不再是“整首 MV 视频轨 + 训练音频替换”时，才另建目录。

**固定流程：**
- 源音频：把用户给的训练 WAV 复制到 `sandbox/angela-ai-mv-covers/audio/`，不要重新推理、不要改训练音色文件本身。若音频来自 `cc-voice`，只允许复制用户明确给出的 WAV 路径或目录内 WAV 到本项目；不得对 `cc-voice` 做目录扫描、状态检查、哈希/时长探测、进程检查或任何写操作。时长/静音/哈希等校验一律在复制到 `cc-media` 后对本地副本执行。批量目录导入时，文件名含 `废弃` 的 WAV 直接跳过。
- 源视频：每首仍按“素材源平台”硬约束同时查 YouTube + B站。优先官方 MV/官方 4K 升级源；但必须抽帧确认画面干净度，不能只看“官方”或分辨率。
- 构建：复用 `sandbox/angela-ai-mv-covers/build/build.py`，新增 `Song` 配置；一首输出一个 `final/YYYY-MM-DD/<歌名>_AI训练张韶涵音色MV.mp4`。脚本默认用运行当天日期，也可用 `ANGELA_MV_FINAL_DATE=YYYY-MM-DD` 指定历史/批次目录。若视频轨只比训练 WAV 短几十毫秒到约 0.5s，在视频滤镜加 `tpad=stop_mode=clone:stop_duration=2` 后再 `-shortest`，避免截掉尾音。
- intro：用 `tools/tts/narrate.py --female --speed 1.12` 生成“如果张韶涵唱《歌名》。”这类女声提示；构建脚本会自动修剪 TTS 首尾静音。
- 混音：intro 期间训练音频 duck 到约 25%，intro 结束后 350ms 恢复；最终音频直接由 FFmpeg 预混/编码，不走 HyperFrames 音频归一化。单首训练音频若明显低于本目录响度基线，可在 `Song` 配置轻微 `audio_gain`，但最终 max volume 必须低于 0dB。
- 角标：全程叠加 `AI训练，仅供娱乐`。当前 FFmpeg 没有 `drawtext`，用 Swift/AppKit 生成透明 PNG 水印再 `overlay`。
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
- `silencedetect` 若报静音，必须对照训练 WAV。e200 源可能自带开头/中段/结尾静音；源自带静音不强行剪掉，以免破坏音频与 MV 时长对齐。
- `volumedetect` 目标与上一批保持接近，实测本目录多首 mean volume 约 `-17.4 dB`，max volume 保持低于 0dB。

### 首屏封面（首帧可作封面，硬约束）

**第 0 秒第一帧必须可作为静态封面图。** 不要给封面元素加 `fade-in` 入场动画（否则 t=0 时 opacity 仍是 0，整张封面黑屏）。

**短视频 TOP / 音乐盘点封面底片**：
- **默认优先歌手本人出镜**：封面背景不要默认用空镜、抽象景、剧情演员或纯舞台灯；先从本期素材里抽 6-12 张候选帧，优先选歌手本人正脸/半身/演唱动作清楚的段落。找不到本人清晰帧时，再用主题性强的空镜，并在交付里说明取舍。
- **标题区默认居中靠上**：竖屏封面标题和描述默认放在上半屏或中上区域，避免压在底部像普通字幕卡，也给下半屏保留歌手脸/身体辨识度。只有当真人主体稳定在上半屏时，才把标题区下移。
- **封面底片可与第一首展示段不同窗**：开场可单独预切 `intro_<song>.mp4`，选更有辨识度的人像段；不要因为 intro 音乐来自某首歌开头，就被迫使用该歌开头空镜。

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
- 别用全片 pad 兜底 silencedetect。允许少量 1-1.5s **自然短暂静音**（叙事性停顿/段间气口），用户的偏好顺序是：**真静音 > 任何形式的底床/白噪音**。
- 替代策略：① 章节末 `afade out` 拉长到 2-2.5s 形成自然衰落；② 段间气口用对应章节音乐的极低音量（-14 ~ -16dB）做 4-8s 桥接 lead-in；③ 接受 silence_duration < 1.5s 的短暂停顿。
- **修正 L171 节奏规则**：原"不得有 >1s 整片静音"过严。新规则：**段内 > 1.5s 整片静音不可接受，但段与段交界 1-1.5s 自然停顿 OK**；判别看是否有"音乐床淡入预热"或"画面运动接续"，有就行。

**短视频开头节奏（用户硬偏好）**：
- 0-1s **必须有视觉动作**（卡片缩放/path 绘制/光点点亮均可），不能纯静止。
- 5s 内**必须进入实质内容**（开始口播 / 切到 footage / 章节起手）。
- 即便 brief 写"0-6s 封面静止"，要按短视频节奏压缩——这是用户感知节奏 > brief 文字。
- 实测：V3 把封面排成 14s（含 stagger reveal），用户立即反馈"飞入动画太慢，观众几秒就没兴趣"。V4 压到 5.5s 满足。

**封面三卡 + 标题块 collision 安全距离**：
- 竖屏 1080×1920，cover-title 块在底部 `bottom: 62px`，typical 块高约 370-400px（含 tag/h1/h2/歌名/副标）→ 标题顶部 y ≈ 1488。
- 三卡块中**最低的卡底部** ≤ y ≈ 1410（留 ≥ 78px 安全间距）。
- 设计 cover 时把所有绝对定位元素 `(left, top, w, h)` 列表化，**手动算 overlap**（lint 不查）。Cover frame 0 是关键封面图，碰撞最致命。
- 实测：cv-jt 初版 top:990 h:600 → 底 1590，与标题块碰撞 102px。修到 top:810 留 78px 间距。

**AV1 输入侧 seek 不准**：
- `ffmpeg -ss 145 -i raw_av1.mp4 -frames:v 1 out.jpg` 取出来可能是 t=150-160 区间任意一帧（AV1 关键帧稀疏 + 输入端 seek 不解码到精确帧）。
- 抽帧定位必须用**输出端 seek**：`ffmpeg -i raw_av1.mp4 -ss 145 -frames:v 1 out.jpg`（慢一些但准）。
- contact sheet 拼图也要用 output-side seek 或先转 H.264 密集关键帧再抽。
- 实测：黑豹 MV `-ss 145 -i ...` 抽出来是 BOY 帽剧情演员（t=155 附近）；换 output-side seek 才能精确到 t=145 的窦唯长发侧脸 closeup。

**Kokoro 中英混读问题**：
- Kokoro misaki[zh] **不擅长中英混读**。旁白文本里有英文（如"Don't Break My Heart"）会念得断断续续/不自然。
- 修法：TTS 文本里把英文歌名改写成"这首歌/这段旋律/这段歌"；**屏幕字幕仍可保留英文**（视觉与听觉分流）。
- 适用于：英文歌名、品牌名、人物英文译名等夹杂场景。

**字体选择对纪录片质感的决定性影响**：
- 中文系统 fallback（PingFang SC）虽能渲染，但**没有衬线字体的纪录片质感**。
- 用户对 V3 之前的"普通无衬线 + 居中对齐"评价是"PPT 解说不够漂亮"。换 Google Fonts 后明显升级。
- 推荐组合（V5 验证）：
  - 中文衬线主标：**Noto Serif SC** (400/600/700)
  - 西文斜体优雅：**Cormorant Garamond** (italic 300/400)（封面英文歌名 / 强调短语）
  - 中文无衬线 UI：**Noto Sans SC**
  - 数字/代码 mono：**JetBrains Mono**（年份、章节番号、tag）
- HyperFrames 编译时自动 fetch Google Fonts 并 inline，**不需要本地 woff2**（lint 会提示但渲染正常）。
- `<link href="https://fonts.googleapis.com/css2?family=...&display=swap" rel="stylesheet">` 直接放 `<head>`，HF 会处理。

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
- "标题/字体/排版普通" → 引入衬线 + Mono 系统字体；左对齐 > 全局居中；金/银/紫色调取代纯白
- "转场文案意义不明（只有年份）" → 加诗意主文案，年份做装饰小字
- "黑屏没画面只有文字" → outro/CTA 期保持 footage 衬底，文字浮在上方

## 渲染与产物

- `npm run render` 输出到项目内 `renders/<id>_<时间戳>.mp4`。
- 渲染吃内存（headless Chrome 截帧），`doctor` 报过低内存告警；大渲染前留意可用内存。
- 产物归档策略（保留可复现输入而非仅 MP4）：见各目录 README。`renders/`、`*.mp4`、下载素材已在 `.gitignore` 排除。

## 环境坑（已踩）

- ~~npm 缓存有 root-owned 文件导致 `npx hyperframes` 报 EEXIST/EACCES~~ **已于 2026-05-27 用 `sudo chown -R $(whoami) ~/.npm-cache` 根治**，现在 npx 用默认缓存正常。
- Docker 未装：仅容器化渲染需要，本地用系统 Chrome 渲染不需要，可忽略。

## 待办 / 决策记录

- [ ] 确定竖屏/横屏与默认分辨率帧率
- [ ] 确定源素材与时间码的记录格式
- [ ] 沉淀第一个可复用的 composition 模板
