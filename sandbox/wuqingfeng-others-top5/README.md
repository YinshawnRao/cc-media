# 吴青峰为别人写的歌 TOP5（竖屏 1080×1920 音乐盘点剪辑作品）

**成片**：`renders/wuqingfeng-others-top5.mp4`（3:57，h264 1080×1920 SDR/bt709 + aac，= `hf/renders/full_raw.mp4` 渲染 + 预混 `master.wav` 后期 mux）。
**形式**：固定排名 1→5 叙事序（#1 最大热门《有形的翅膀》先放、让榜单立刻成立），不倒数。每首展示**完整副歌**，副歌期纯音乐无旁白。本地测试，未发布。

## 风格
- 黑金 / 深蓝 / 银白 高级音乐杂志感 + 每首主题色（s1 暖金·励志 / s2 冷蓝·青春离别 / s3 暗红·失去重量 / s4 银白·时间年轮 / s5 红黑·态度重建）。
- 字体：Noto Serif SC（标题/歌名）+ Noto Sans SC（UI/词曲）+ JetBrains Mono（排名数字/年份）。
- 封面真人=**吴青峰本人**（睡美人 MV 云中正脸，复用自 wuqingfeng-yizhu）；封面标题「吴青峰写给别人TOP5 / 原来这些歌都是他写的」。
- 开场屏幕主标题「吴青峰为别人写的歌TOP5 / 不只是会唱，他写给别人也首首有戏」+ 5 首歌名歌手闪现（与封面标题分开，按 brief 第三节）。

## 结构（每段时长见 build 输出）
封面(3.6s) → 钩子/开场标题(到21.75s) → 5 章节[排名卡(序号/歌名/歌手/词曲/标签)→引入旁白(音乐床+ducking)→swell→**完整副歌**展示(纯音乐+大字关键词+观点金句字幕)→收束] → outro(5首回顾 + 结尾字幕「他写给别人的歌，也是一部隐藏的吴青峰作品集。」)。

## 素材源（两平台对照，详见 `SOURCES.md`）
| # | 歌/歌手 | 源 | 平台 | 副歌(原片) | crop |
|---|--------|----|------|-----------|------|
|1|有形的翅膀/张韶涵|`cBp-QhO63Us` 官方MV|YT|53.5–69.5|864:820:528:0|
|2|带我走/杨丞琳|`BV1RV4y1p75A` 4K修复|B站|85–108|864:820:528:0|
|3|掉了/张惠妹|`BV1L14y1q7aM` 华纳官方修复4K|B站|151–180|864:1080:528:0|
|4|年轮说/杨丞琳|`anurOHpo0aY` 官方HD MV|YT|187–215|864:820:528:0|
|5|怪美的/蔡依林|`-wIHmPAvMBo` 官方MV|YT|62–86|864:1080:528:0|

烧死歌词/水印：s1/s2/s4 顶对齐 `864:820:528:0` 裁净底部歌词 + s2 右上水印；s3/s5 副歌段干净用全高 `864:1080:528:0`。

## 复现
1. cookie：`sandbox/www.youtube.com_cookies.txt` / `sandbox/www.bilibili.com_cookies.txt`。B站搜索用 `tools/video/bili_search.py`（WBI 签名）。
2. 下源切片（上表 URL），AV1 源(s1/s4/s5)先转 h264 到 `raw_h264/` 加速 seek。
3. 配音（男声 zm_yunxi）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav` + `narration.json`。
4. 合成+音频：`tools/tts/venv/bin/python build/full_build.py`（每首 mseek=chorus−full0 使副歌落在 swell 后；切竖屏 footage → `clips_seg/`；逐段 床→swell→完整副歌 + 旁白ducking + 逐首 loudnorm I=-14 → `master.wav`；生成 `hf/index.html`）。
5. 渲染+mux：`bash build/retry_render.sh`（本机 GPU 截帧随机崩，`-w1` 重试到产物完整；本片两次均首试成功）→ `bash build/finish.sh`（mux + QA 抽帧）。

## QA 结论（工具验证）
- 画面：封面真人吴青峰正脸 + 金色大标题；5 张排名卡序号/歌名/歌手/词曲准确（s4 正确区分「作词 吴青峰 · 作曲 郑宇界」）；各副歌段对应歌手特写；**无水印/烧死歌词/路径/meta 文案残留**；SDR bt709。
- 音频：5 首副歌 **-14.3~-15.9dB**（差<1.7dB，一致）；旁白段 ~-21.7dB（比副歌低 ~7dB，ducking 清晰）；无 >1.5s 整片静音（开头 1.27s 为封面 ambient 渐入）。
- lint：0 error（仅 Google Fonts 字体 warning，HF 编译期自动拉取、中文渲染正常）。

## 仍需人工耳/眼定夺
- 各首副歌展示段是否为**最具代表性**的那一段副歌（已按人声段检测 + 歌手特写簇 + 歌曲结构定位，但「哪段副歌最对」最终凭耳朵）。
- 跨首响度听感是否舒适（数值已统一到 ~-15dB）。
