# 张韶涵音色 AI MV

本目录生成 33 个独立 MV 视频：MV 视频轨去掉原音频，替换为训练音频快照，片头叠加女声提示，并在角落标注 `AI训练，仅供娱乐`。当前音频缓存已包含 `phase3` 全新模型副本、`批次_20260605-1209_经典批` 副本、`batch_20260608-1021` 副本和 `batch_20260605-1456` 副本。

## 近期任务总结

- 第一批 4 首：`光年之外`、`天空没有极限`、`雨爱`、`理想情人`，统一使用 e200 `_final.wav` 替换官方 MV 音轨。
- 第二批 2 首：`心墙`、`突然想起你`，使用 `test_targets/*-激进版.wav` 继续追加到同一目录和同一构建脚本。
- 第三批 6 首：`爱情讯息`、`彩虹`、`哭不出来`、`倒数`、`一个人生活`、`慢冷`，使用 `新歌试听_激进版/*.wav` 继续追加；其中 `慢冷` 官方 MV 为 7:37 长剧情版，已按音频包络对齐到原 MV `97.5s` 后预切为 `raw/manleng_aligned.mp4`。
- 第四批 2 首：`搁浅`、`心中的日月`，继续使用 `新歌试听_激进版/*.wav`；两首均选 YouTube 官方艺人频道源，其中 `搁浅` 虽只有 640x480，但与训练音频逐秒对齐，优先于 B站非官方 4K 短版/歌词重制版。
- 2026-06-05 全量重跑：旧成片归档到 `final/history/2026-06-05_before-retrain/`；从用户指定的全新模型目录只复制 WAV 到本目录 `audio/phase3_import/`，再覆盖现有 `audio/*.wav` 缓存并复用全部已验证 MV 视频源重建 14 首。
- 第五批 9 首：`只想爱你`、`小镇姑娘`、`恶作剧`、`想唱就唱`、`慢慢喜欢你`、`我还记得`、`百年孤寂`、`那么骄傲`、`雨季中`，从用户指定的 `批次_20260605-1209_经典批/` 只复制非 `废弃` WAV 到 `audio/batch_20260605-1209_classic_import/`。其中 `想唱就唱` 用顶部 crop 去掉上传者/电视台标，`那么骄傲` 用底部 crop 去掉歌词和修复者水印；`慢慢喜欢你`、`那么骄傲` 加轻微 `audio_gain` 使响度回到本目录基线。
- 第六批 10 首：`兜圈`、`回家`、`我知道`、`一个人想着一个人`、`孤单心事`、`我爱你那么多`、`残酷月光`、`浪费`、`说爱你`、`飞鸟和蝉`，从用户指定的 `batch_20260608-1021/` 和 `batch_20260605-1456/` 只复制 WAV 到本目录，文件名含 `废弃` 的直接忽略。其中 `我知道` 官方 MV 需按训练音频包络偏移 `22.3s` 预切；`孤单心事`、`飞鸟和蝉` 用全宽 crop 去掉平台/片头污染区；`回家`、`一个人想着一个人` 放弃带水印的 B站高分候选，退回更干净的 YouTube 源。
- 工作模式已固定为“一首一个最终 MP4”：下载/筛选 MV 视频轨，复制训练音频，生成女声 `如果张韶涵唱《歌名》` intro，intro 期间 ducking 歌曲音量，随后恢复全量歌曲。
- 角标统一为 `AI训练，仅供娱乐`，用 PNG 叠加而不是 FFmpeg `drawtext`，因为当前 FFmpeg 构建没有 `drawtext`。
- `SOURCES.md` 记录 YouTube + B站候选、最终取舍和限制；后续继续加歌时必须补同一份记录。

## 复用规则

明确是“AI 克隆/训练歌手音色制作 MV”“如果某歌手唱某歌”的任务，且用户给了可直接使用的训练音频时，默认继续在本目录追加，不新开 `sandbox/<slug>/`。除非用户明确要一个新项目，或输出规格已经不是“整首 MV 换训练音轨”。

`audio/` 是当前构建音频缓存，旧音频不单独归档；需要保留的是 `raw/`、`voice/`、`build/build.py`、`SOURCES.md` 和本 README。若新音频来自 `cc-voice`，只复制用户明确给出的 WAV，不对 `cc-voice` 做任何额外读取、扫描、探测或写操作；所有校验在复制到本目录后进行。

`final/` 按生成日期分目录保存，格式为 `final/YYYY-MM-DD/`。`build/build.py` 默认输出到运行当天目录；需要重建历史批次时，可用 `ANGELA_MV_FINAL_DATE=YYYY-MM-DD` 指定输出目录。

复跑：

```bash
python3 build/build.py
# 或只重建指定歌曲：
python3 build/build.py xinqiang turanxiangqini aiqingxunxi caihong kubuchulai daoshu yigerenshenghuo manleng geqian xinzhongderiyue zhixiangaini xiaozhenguniang ezuoju xiangchangjiuchang manmanxihuanni wohuanjide bainianguji namejiaao yujizhong douquan huijia wozhidao yigerenxiangzheyigeren gudanxinshi woaininameyiduo cankuyueguang langfei shuoaini feiniaohechan
# 指定重建到某个日期目录：
ANGELA_MV_FINAL_DATE=2026-06-08 python3 build/build.py douquan huijia wozhidao yigerenxiangzheyigeren gudanxinshi woaininameyiduo cankuyueguang langfei shuoaini feiniaohechan
```

产物：

`final/2026-06-05/` 共 23 个：

- `final/2026-06-05/光年之外_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/天空没有极限_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/雨爱_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/理想情人_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/心墙_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/突然想起你_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/爱情讯息_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/彩虹_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/哭不出来_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/倒数_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/一个人生活_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/慢冷_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/搁浅_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/心中的日月_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/只想爱你_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/小镇姑娘_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/恶作剧_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/想唱就唱_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/慢慢喜欢你_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/我还记得_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/百年孤寂_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/那么骄傲_AI训练张韶涵音色MV.mp4`
- `final/2026-06-05/雨季中_AI训练张韶涵音色MV.mp4`

`final/2026-06-08/` 共 10 个：

- `final/2026-06-08/兜圈_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/回家_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/我知道_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/一个人想着一个人_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/孤单心事_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/我爱你那么多_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/残酷月光_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/浪费_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/说爱你_AI训练张韶涵音色MV.mp4`
- `final/2026-06-08/飞鸟和蝉_AI训练张韶涵音色MV.mp4`

## 经验教训

- 源搜索仍按仓库硬约束：每首都查 YouTube + B站。官方源优先，但如果官方源只是低清或 Karaoke，必须和 B站修复版实际抽帧比较。
- 不要只看分辨率。B站 4K 修复版可能带平台/UP 主水印或烧死歌词；先抽 `1s`、`40s` 等关键帧，发现污染后再决定 crop 或换源。
- 对全宽横向污染区优先用全宽 crop 去掉，不做竖向激进裁切。《心墙》最终用 `crop=3840:1920:0:0` 去掉底部水印/歌词，同时保留主体完整。
- 官方 Karaoke 源的歌词属于源画面内容，不能当作平台水印；如果没有更干净的官方/高质量候选，记录限制后可保留。
- e200 音频可能自带开头、中段或结尾静音。最终 `silencedetect` 发现静音时，要同时对照源 WAV，确认不是合成过程新增。
- 当官方 MV 长度明显长于训练音频时，不要直接从 0 秒套音轨。先用原 MV 音轨与训练 WAV 做包络对齐，预切出同长视频片段再进 `Song` 配置；`慢冷` 验证偏移为 `97.5s`。
- 官方/准官方 MV 也可能带 20s+ 片头剧情或唱片片头，训练音频从正歌开始时同样要做包络对齐；`我知道` 验证偏移约 `22.3s`，预切后再合成。
- 当 B站 4K 修复版比训练音频短 2-4 秒，且标题写明歌词重制/非官方修复时，不要为了分辨率牺牲整首对齐；优先选择时长精确匹配的官方源，哪怕官方源只有标清。
- 高分辨率不是充分条件。B站 4K/1080P 候选若带平台角标、UP 主水印、修复者 logo，先判断全宽 crop 是否能干净移除；不能移除时退回低清官方/版权方源，比交付带水印成片更稳。
- 画面污染区不只在底部。`孤单心事` 用 `crop=1920:820:0:120` 同时去掉顶部 BGM 字样和底部歌词，`飞鸟和蝉` 用 `crop=1920:760:0:280` 去掉顶部 logo；这种裁切必须抽最终帧确认主体没有被裁坏。
- 当最终视频源只比 WAV 短几十毫秒到约 0.5s 时，在视频滤镜里加 `tpad=stop_mode=clone:stop_duration=2`，让 `-shortest` 按完整训练音频结束，避免截掉尾音。
- 如果最终 `volumedetect` 明显低于本目录基线（约 `-17.4 dB`），可以给单首配置轻微 `audio_gain`；已验证 `慢慢喜欢你=1.22`、`那么骄傲=1.12`、`回家=1.08`、`一个人想着一个人=1.22`、`我爱你那么多=1.25`、`飞鸟和蝉=1.10` 后都回到约 `-17.2~-17.5 dB`，max 不超过 0dB。
