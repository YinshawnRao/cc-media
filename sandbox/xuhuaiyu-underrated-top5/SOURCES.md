# 徐怀钰最被低估的5首歌 - 素材来源记录

检查日期：2026-06-17；第五首替换复查：2026-06-20

Cookie 状态：
- YouTube: `sandbox/www.youtube.com_cookies.txt` 可用，本地 cookie 结构检查通过。
- B站：`sandbox/www.bilibili.com_cookies.txt` 可用，搜索接口可返回候选。

## 双平台候选与取舍

| 排名 | 歌曲 | YouTube 候选 | B站候选 | 当前选择 | 取舍原因 |
| --- | --- | --- | --- | --- | --- |
| 05 | 《我不要》 | `FdERF6fs6iA`，滚石唱片官方 MV，4:06；当前 YouTube cookie 已失效，无法下载规格和原片。 | `BV1YC4y1a7Et`，1080P 修复 MV，1280x960，H.264，stereo；另有 `BV1hC4y1e7j8` 普通 MV 候选。 | B站 `BV1YC4y1a7Et`。 | YouTube 官方源可确认但当前 cookie 失效无法下载；B站修复源清晰、双声道，crop 后去除顶部小水印和底部烧词。 |
| 04 | 《等不及》 | `O_1bRY3bxV8`，滚石唱片官方 MV，640x480，stereo。 | `BV1b54y1Q7C4` 1080P 修复；`BV13G9FBXEQD` 原版 4K 修复候选。 | YouTube `O_1bRY3bxV8`。 | 官方源稳定，老 MV 低清可接受；裁切后底部字幕已移除。 |
| 03 | 《乱了》 | `_JgorcJcyus`，滚石唱片官方 MV，640x480，stereo。 | `BV1tt4y1z7x3` 1080P 修复；`BV1Q24y1W7Cn` 1080P 修复候选。 | YouTube `_JgorcJcyus`。 | B站源清晰度更高但下载路径过慢/中断；YouTube 官方源可稳定下载，裁切后干净。 |
| 02 | 《友情卡片》 | `6tLUnO2oU-E`，滚石唱片官方 MV，1440x1080，stereo。 | `BV1nK411s7QY` 1080P 修复及其他 4K 修复候选。 | YouTube `6tLUnO2oU-E`。 | 官方源已达到高分辨率，画面稳定，裁切后无明显平台水印。 |
| 01 | 《温习》 | `TbRoM9onRwE`，滚石唱片官方 MV，1440x1080，stereo。 | `BV14T4y1J7Ko` 1080P 修复；`BV1op9gBdEKZ` DVD 原档候选。 | YouTube `TbRoM9onRwE`。 | 官方源清晰、稳定，裁切后底部歌词已移除。 |

## 已生成素材

| 歌曲 | 原始文件 | 竖屏文件 | 裁切 |
| --- | --- | --- | --- |
| 温习 | `raw/p1_wenxi_yt.mp4` | `clips/vert_p1_wenxi.mp4` | `1440:900:0:0` |
| 友情卡片 | `raw/p2_friend_yt.mp4` | `clips/vert_p2_friend.mp4` | `1440:700:0:0` |
| 乱了 | `raw/p3_luan_yt.mp4` | `clips/vert_p3_luan.mp4` | `640:390:0:0` |
| 等不及 | `raw/p4_wait_yt.mp4` | `clips/vert_p4_wait.mp4` | `640:360:0:0` |
| 我不要 | `raw/p5_wobuyao_bili.mp4` | `clips/vert_p5_wobuyao.mp4` | `1280:720:0:50` |

## 抽帧检查

- 原始素材抽帧：`probe/raw_p1_wenxi.jpg`、`probe/raw_p2_friend.jpg`、`probe/raw_p3_luan.jpg`、`probe/raw_p4_wait.jpg`、`probe/raw_p5_wobuyao_contact.jpg`。
- 竖屏素材抽帧：`probe/vert_p1_wenxi.jpg`、`probe/vert_p2_friend.jpg`、`probe/vert_p3_luan.jpg`、`probe/vert_p4_wait.jpg`、`probe/vert_p5_wobuyao_contact.jpg`。
- 五首竖屏素材裁切后未见平台水印、网址、路径、提示词泄漏；底部烧词/字幕已通过全宽横带 crop 移除。

## 历史阻塞

《不吵不闹》疑似曲名归属错误：仓库现有温岚项目中该曲来自温岚《蓝色雨》，而不是徐怀钰。徐怀钰公开唱片资料里未能确认该曲名；YouTube 与 B站也未检索到徐怀钰版本。因此当前不能生成最终成片，除非确认第五首替换曲目，或明确允许用其他歌手/其他歌曲替代。

2026-06-20 用户已确认第五首替换为《我不要》，当前阻塞解除。

## 2026-06-20 展示段重对齐

用户反馈初版《我不要》展示段把 70-100s 的核心“我不要”副歌压在旁白下，音量推满时已经接近收尾。复查原片抽帧后，当前构建改为：

- 片段从原片约 `56.5s` 起。
- 旁白结束约对应原片 `72.0s`。
- 全量展示从原片 `73.7s` 起，展示约 `32s`，覆盖到 `105.7s`。
- 副歌人声在旁白尾声前约 2s 进入，随后进入无旁白的完整展示段。

## 2026-06-18 复查记录

为避免网页索引遗漏，继续用本地平台工具复查：

### B站搜索

```text
python3 tools/video/bili_search.py "徐怀钰 不吵不闹" 10
python3 tools/video/bili_search.py "徐懷鈺 不吵不鬧" 10
python3 tools/video/bili_search.py "徐怀钰 Bad Girl 全专辑" 10
```

结果：
- `徐怀钰 不吵不闹` / `徐懷鈺 不吵不鬧` 返回的是徐怀钰综艺、其它 MV、其它歌手或泛娱乐内容，没有目标曲。
- `徐怀钰 Bad Girl 全专辑` 命中 `BV1uirYYXEzK`，标题列出的专辑曲目为：`堕落天使`、`如果在你怀里满足的死掉`、`Wait A Minute`、`心中的遗憾`、`秘密花园`、`跟我走`、`比舞大会`、`小女人的心`。没有《不吵不闹》。

### YouTube 搜索

```text
yt-dlp --cookies sandbox/www.youtube.com_cookies.txt "ytsearch10:徐怀钰 不吵不闹" --skip-download --print "%(id)s | %(duration_string)s | %(uploader)s | %(title)s"
yt-dlp --cookies sandbox/www.youtube.com_cookies.txt "ytsearch10:徐懷鈺 不吵不鬧" --skip-download --print "%(id)s | %(duration_string)s | %(uploader)s | %(title)s"
yt-dlp --cookies sandbox/www.youtube.com_cookies.txt "ytsearch10:徐懷鈺 Bad Girl 全專輯" --skip-download --print "%(id)s | %(duration_string)s | %(uploader)s | %(title)s"
```

结果：
- `不吵不闹` / `不吵不鬧` 查询返回《我不要》《乱了》《飞起来》《向前冲》《爱像一场重感冒》《谁不乖》等其它徐怀钰 MV，未命中目标曲。
- `Bad Girl 全專輯` 查询返回《Bad girl》官方 MV `aoNCCWLQp1o`、《秘密花園》`L-H8umg8ygw` 以及其它徐怀钰 MV，未命中《不吵不闹》。

结论不变：第五首仍不能作为徐怀钰《不吵不闹》继续制作。

## 2026-06-20 公开资料复核

继续查公开资料以判断是否为曲名误归属：

- 徐怀钰公开资料页只确认其 2007 年发行《Bad Girl》专辑，未能找到《不吵不闹》作为徐怀钰曲目的记录：https://zh.wikipedia.org/wiki/徐懷鈺
- 温岚公开资料页把《不吵不闹》列在 2002 年《蓝色雨》专辑曲目中：https://zh.wikipedia.org/wiki/温嵐
- 编曲/词作者相关公开资料也把《不吵不闹》归到温岚作品列表：
  - 林迈可作品页列有温岚《不吵不闹》：https://zh.wikipedia.org/wiki/林邁可
  - 方文山填词作品页在 2002 年列有温岚《不吵不闹》：https://zh.wikipedia.org/wiki/方文山

结论继续保持：当前第五首更像是温岚曲目混入了徐怀钰榜单，而不是徐怀钰《Bad Girl》时期遗珠。
