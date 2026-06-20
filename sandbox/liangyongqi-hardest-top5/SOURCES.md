# Sources — 梁咏琪最难的5首歌

Cookie files checked: YouTube `sandbox/www.youtube.com_cookies.txt`, B站 `sandbox/www.bilibili.com_cookies.txt`.

Selection rule (硬约束): both YouTube and B站 searched for every song; prefer clean official MV, but **当官方上传是静态专辑图 / 剧情片 / 烧死大卡拉OK歌词时，改用干净的官方频道 Studio Live 或修复源**（见 [[official-mv-may-be-live]]）。每段抽帧核验本人特写 / 烧死歌词位置 / 平台·UP水印 / 画幅后才定窗。倒数 5→1，女声配音。

关键事实：
- **官方频道「Gigi Leung 梁詠琪官方專屬頻道」的 5 首上传都是 1080×1080 静态专辑封面图 + 音轨**（《花火》抽帧 = 沙滩专辑封面静图），不能做展示素材，全部弃用。
- **谷Live「Studio Live」系列**（YouTube 同名频道）= 同一场绿西装棚拍，梁咏琪本人贯穿真唱，最契合「最难唱」主题；缺点是 顶部 `谷LIVE` 角标 + 底部卡拉OK歌词（按句出现），均可全宽 letterbox crop 掉。三首（高妹/嫌弃/花火）共用此场 → 用分镜/取段差异化。
- 多支「修复MV」自带平台/UP/修复者水印 + 烧死歌词，crop 前**必须按真实分辨率二分抽断面定位**（本期踩坑：先用缩放图目测导致 crop 少裁 ~6px/半行歌词，按 0.5 缩放系数复算后才裁净）。

## 5. 《高妹正传》— 谷Live Studio Live（YouTube）
- 候选 YT：官方频道 `HAWL4DN2kHc` 1080² = 静态专辑图，弃；`LBloKAzyJas`（Digital learning 完整剪辑版）1080P 但烧死粵語中字 + 夜景剧情少演唱；**谷Live `x21sCp25pMA`**（Studio Live）1080P 绿西装真唱，干净（仅角标+歌词可裁）。ViuTV/陈慧琳 Live 均为双人合唱，弃。
- 候选 B站：`BV1Q34y1D7AN`（AlfredSE 高清修复MV）= 夜景剧情 + 大卡拉OK歌词，弃；其余多为合唱/演唱会。
- **最终：YT `x21sCp25pMA`**。窗 file 34–94（abs ~1:24–2:24），letterbox crop `1920:812:0:92`（裁顶 `谷LIVE` 角标 y≤83 + 底部歌词 y≥918）。

## 4. 《嫌弃》— 谷Live Studio Live（YouTube）
- 候选：AlfredSE `BV1ZT4y1Z7yk` / QAF HK `o64nGuR-wys` 真情MV = 4:3 SD 柔焦 + 大卡拉OK歌词 + TVB台标 + 男主角双人（QAF），crop 后变软薄窄条，画质明显逊于其它首，弃；谷Live `qT1JYGOvE38`（Studio Live）蓝光绿西装真唱，锐利干净。
- **最终：YT `qT1JYGOvE38`**。源含 6.06s 视频起始偏移（音轨 start_time 0 / 视频 6.059）→ 必须从 ≥6s 处 input-seek 切，否则音轨被截 6s（见 [[ytdlp-webm-audio-truncation]] 同类）。窗 file 8–68，crop `1920:812:0:92`。

## 3. 《烟雾弥漫》— 甄爱SHE 4K修复MV（B站）
- 候选：weazegigi `BV1Cu411z7VX`（第二版MV）= 4:3 SD 黄衣剧情 + TVB台标 + WG水印，软；2023/2014 Live 多机位过暗拍不到主体；官方频道静图弃。**甄爱SHE `BV1Ho4y1r7bo`（SeedVR2-4K修复）** = 16:9 锐利浴缸/床的本人亲密近景，氛围契合「烟雾」，仅顶左 `甄爱SHE bilibili` 水印（到 y≈104）+ 底右单行重制歌词（y≈1016）。
- **最终：B站 `BV1Ho4y1r7bo`**（4K 锐度 > weazegigi SD）。窗 file 16–76，crop `1920:860:0:120`（裁顶水印 + 底歌词）。立体声。

## 2. 《花火》— 谷Live Studio Live（YouTube）
- 候选：央视频 `BV1FvoEBhEdj`（航天盛典 Live）= 漂亮红色花火舞台近景，**但宽景/近景碎镜（每 5–10s 切），连续段多为无主体宽镜，违反「不碎镜」展示硬规则**，且疑似国语 → 作 backup；weazegigi 国语版 B&W 多人 + 水印弃；官方频道静图弃。**谷Live `GMjsHM867YQ`**（Studio Live）= 连续真唱（粤语，匹配 brief 粤语专辑），干净。
- **最终：YT `GMjsHM867YQ`**（连续副歌 + 粤语 > 央视碎镜+疑似国语）。窗 file 38–99，crop `1920:812:0:92`。绿西装与 #5 同场 → 取不同段/取景差异化。

## 1. 《原来爱情这么伤》— weazegigi 4K修复MV（B站）
- 候选：官方频道 `KCDMucUEjfw` 静图弃；阿杜 Topic/Live = 阿杜唱非本人，弃；各 Live 带台标。**weazegigi `BV1aL411479N`（超清4K版MV）** = 大量本人深情演唱面部特写（国语，匹配本曲），16:9 锐利，仅顶右 `weazegigi bilibili` 水印（到 y≈108）+ 底部双行歌词（y≈865–970）。
- **最终：B站 `BV1aL411479N`**。窗 file 6–66，crop `1920:736:0:118`（裁顶水印 + 底双行歌词；带较窄但面部特写大，压轴情绪足）。立体声。

## 备注
- 全部展示窗 letterbox 保原比例（footage 窗 == 音乐窗，自带音轨即音乐源，口型同步）；逐首 `loudnorm=I=-14`，花火 谷Live 偏轻补 `+1.18×`；展示段目标均值 ~-15dB。
- 成片画面无任何平台水印 / UP / 网址 / 路径 / 提示词（crop + 干净叠层，已抽帧逐边核验）。
- 封面/intro 底用 #5 谷Live（本人真唱，不剧透排名）；outro 底用 #1 weazegigi 4K 深情特写收束。
- 本地测试用，未授权发布；发布前需分别评估 YouTube/B站源素材授权。
