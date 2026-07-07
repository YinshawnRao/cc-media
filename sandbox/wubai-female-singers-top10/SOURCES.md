# 伍佰给女歌手写的歌 TOP10 — 选源

排名揭晓顺序：倒数 10 → 1。封面/片头/片尾主角 = **词曲作者伍佰本人**（多歌手盘点封面放幕后创作者）。
Cookie 统一用根目录 `all_cookies.txt`。

> ⚠️ 关键发现：10 首里有 **4 首官方 MV 是"演员主演剧情片 / 纯静态图"，没有歌手本人演唱画面** → 走**解耦**（官方录音室音频 + 歌手本人 Live / 同期 b-roll）。其余 6 首音画同源（sync）。

| 排名 | 歌手 /《歌名》| 伍佰署名 | mode | footage 源 | 音频源 | 备注 |
|---|---|---|---|---|---|---|
| 10 | 黄小琥《突然的自我》| 词曲/制作（徐克《散打》主题曲，伍佰+徐克填词）| decouple | 待定 Live（YT `hcAnGg5LCig` 竖屏2025台北 / `Jk1qmulTV4E` 横屏2023）| YT `29nTcz_7N6E` 官方Art Track | 黄版无干净MV(仅KTV电影画面)；网易云标Live；勿用伍佰原版 |
| 9 | 郁可唯《你不要我了吗》| 词曲/制作 | sync | YT `dBBWLL7Bdzo` 滚石官方MV 1080p | 同(MV自带) | 郁+伍佰台北捷运邂逅，本人出镜，干净 |
| 8 | 杨乃文《一个人》| 作词（曲林暐哲）| sync | YT `VWiPFSVZ_JY` 滚石官方Live 1080p 真世界巡演 | 同(Live自带) | 杨×伍佰对唱；专辑《One》1997（brief写Silence有误）；棚版MV仅B站VHS |
| 7 | 刘若英《最初的地方》| 作曲（词于光中）| sync | YT `OKVchw_U9v8` 刘官方MV 1080p | 同(MV自带) | ⚠️须抽帧核是否本人演唱(刘MV常剧情片)；备选Live `xTZZUmrN-aY` |
| 6 | 万芳《夜照亮了夜》| 作曲（词王中言）| decouple | B站 `BV1TK4y1o7k2` 4K屏东2021(多曲连唱,需定位) / `BV1sP411m7sM` 2013草莓 | YT `qSVz9AGQQsU` 滚石官方MV音轨 480p | 官方MV是張鈞甯主演剧情片,无万芳 |
| 5 | 那英《我不是天使》| 作曲/制作（词那英）| decouple | B站 `BV1QW411K7aR` 2018温哥华Live / `BV11A411X7bU` 悉尼 | YT `-YUAHRsSoUQ` Timeless官方MV音轨 480p | 官方MV是范植伟主演剧情片,那英仅旁白；勿用伍佰翻唱版 q0OmX7uYIwA |
| 4 | 王菲《单行道》| 作曲/编曲（词林夕，China Blue）| decouple | 王菲同期官方MV b-roll（待 follow-up agent）| YT `Ru3eO73yw4Q` FayeWongVEVO 录音室 | 全网无《单行道》MV/Live(VEVO是纯音频静图)；用同名专辑《王菲》2001其他MV特写蒙太奇 |
| 3 | 莫文蔚《坚强的理由》| 词曲/编曲/合唱 | sync | YT `22b1WnBg5LA` 滚石官方MV 480p(棚拍对唱) | 同(MV自带) | ⚠️抽帧核形态；备选1080p官方Live `A7mgo0H2_Ck` / B站修复 `BV1dG4y14796` |
| 2 | 苏慧伦《被动》| 作曲（词潘丽玉）| sync | YT `8JAvWmsX0Lc` 滚石官方MV 1080p(本人棚版) | 同(MV自带) | 《Lemon Tree》1996；备选B站4K `BV1TUEvzGEZe`(核搬运水印) |
| 1 | 王心凌《我会好好的》| 词曲 | sync | YT `Gw4Q7-NBFWs` avex官方MV 1080p(阳明山实拍本人) | 同(MV自带) | 《Cyndi With U》2005；MV5:28含非演唱片头尾,定窗避开；彩蛋:王心凌&伍佰4K合唱 `BV14D421u7sY`(4K音乐馆水印y790) |

**伍佰本人镜头（封面/片头/片尾）**：从含伍佰的源里取干净特写——真世界巡演 Live（`VWiPFSVZ_JY`/`A7mgo0H2_Ck`）或郁可唯 MV（`dBBWLL7Bdzo`）。待下载后抽帧选最佳正脸。

## 抽帧核实结果（2026-06-23）+ 竖屏 crop
| key | 源 | 维度 | mode | 内容/坑 | vfill crop（全宽 letterbox）|
|---|---|---|---|---|---|
| p1 王心凌 | YT Gw4Q7-NBFWs | 1920x1080 | sync | avex官方MV阳明山实拍,本人特写(~90/170s),干净无水印 | 1920:1080:0:0 全 |
| p2 苏慧伦 | YT 8JAvWmsX0Lc | 1390x1080 | sync | 本人特写+剧情穿插,底烧词~80px | 1390:1000:0:0 |
| p3 莫文蔚 | YT A7mgo0H2_Ck(Live,改用) | 1440x1080 | sync | 莫+伍佰同台(双人→letterbox),底小credit | 1440:1040:0:0 |
| p6 万芳 | B站 BV1sP411m7sM 2013草莓 | 1280x720 | decouple(au_p6) | 本人festival特写,顶Tsaixx+bilibili水印 | 1280:668:0:52 |
| p8 杨乃文 | YT VWiPFSVZ_JY(Live) | 1440x1080 | sync | 杨+伍佰真世界巡演,底烧词~112px | 1440:968:0:0 |
| p9 郁可唯 | YT dBBWLL7Bdzo MV | 1920x1080 | sync | 郁+伍佰捷运剧情MV,底烧词~74px | 1920:1006:0:0 |
| p10 黄小琥 | YT hcAnGg5LCig 2025台北竖屏 | 1080x1920 | decouple(au_p10) | 原生竖屏本人特写,干净,免letterbox | 1080:1920:0:0 |
| p5 那英 | ⚠️待定 | 480x852/1920x1080 | decouple(au_p5) | 两条Live均远景+顶水印;查drama MV是否有旁白特写 | TBD |
| p7 刘若英 | ⚠️官方"MV"是静态专辑封面→解耦(au_p7已提取) | - | decouple(au_p7) | 待 agent 找本人现场/同期MV b-roll | TBD |
| p4 王菲 | ⚠️无MV/Live(VEVO纯音频)→解耦(au_p4) | - | decouple(au_p4) | 待 agent 找同期官方MV特写 b-roll | TBD |

**改动**：#3 改用官方 Live(A7mgo0H2_Ck 1080p 双人同台)而非 480p 剧情MV；#7 由 sync 改 decouple(静态封面);音频 au_p7 已从静态MV提取。

## 最终对齐值（对齐闸门 10/10 OK，FAIL=0 WARN=0；master 486.2s=8:06）
| key | mode | footage 源(crop) | ch_off | show | fseek/备注 |
|---|---|---|---|---|---|
| p10 黄小琥 | decouple | YT hcAnGg5LCig 竖屏(1080:1920) | 132.4 | 26.0 | foot fseek17.7;音 au_p10 官方Art Track;**修2:vocal_segments谎报106起唱,实际真唱在源134.4(=旧成片video-43s);按用户锚点把ch_off定到让"唱声onset正好落在旁白结束34.875"→ch_off=132.4(=134.4-narr_end_audio_offset);decouple footage不变→仅重建master+remux免渲染;终检showcase first_vocal@0.0s** |
| p9 郁可唯 | sync | YT dBBWLL7Bdzo MV(1920:930) | 140.95 | 32.0 | MV偏暗(夜MRT)可接受 |
| p8 杨乃文 | sync | YT VWiPFSVZ_JY Live(1440:930) | 156.32 | 19.0 | 连唱仅~20s缩show |
| p7 刘若英 | decouple | YT cYchjzfQ2RU《为爱痴狂》MV(640:472) | 227.69 | 17.5 | foot fseek144.3 紫花特写;音 au_p7=最初的地方录音室 |
| p6 万芳 | decouple | B站 BV1sP411m7sM 2013草莓(1280:648:0:72) | 43.82 | 25.5 | foot fseek35.7;音 au_p6 滚石MV音轨 |
| p5 那英 | decouple | YT 480x852竖拍(480:480:0:100) | 181.28 | 29.0 | foot fseek41;音 au_p5;⚠️源仅480p软,唯一画质短板 |
| p4 王菲 | decouple | YT mjuS9shGYhE《流年》MV(1920:885:0:195) | 272.32 | 27.3 | foot fseek183.3 坐姿;裁顶MTV台标;音 au_p4《单行道》VEVO |
| p3 莫文蔚 | sync | YT A7mgo0H2_Ck Live(1440:**850**) | 192.3 | 40.0 | 双人同台letterbox;**修:原284finale是器乐jam(vocal_segments被人群/器乐骗报"49s连唱",用户听出"整体没人声")→改196-236真对唱段;该段有烧死歌词且行高不定到y870→crop收到1440:850才裁净** |
| p2 苏慧伦 | sync | YT 8JAvWmsX0Lc MV(1390:918) | 151.05 | 25.0 | 本人棚版 |
| p1 王心凌 | sync | YT Gw4Q7-NBFWs avex MV(1920:1080) | 171.34 | 32.7 | 阳明山实拍,干净 |

封面/片头 = vert_p8 @197.5（伍佰红光脸特写）；片尾 = vert_p3 @34（伍佰红吉他）。
intro/outro 音乐床 = #1《我会好好的》副歌（vert_p1 @171.34）。

## 状态
- [x] 下载 + 抽帧核实 + 竖屏化 vfill（全宽 letterbox，水印/烧词逐源二分测距裁净）
- [x] vocal_segments + ch_off/show/fseek + 对齐闸门 10/10 OK
- [x] 音频 QA（无>1s静音；副歌 -14.9~-16.1dB 一致；旁白 -22dB 有 ducking）+ 0 lint error + 无泄漏
- [x] 渲染(-w1单worker,-w2会某worker GPU卡死丢半成品) + mux + 终帧 QA → **成片 renders/wubai-female-singers-top10.mp4 (8:06, 1080x1920 H.264)**
  - 终帧QA：封面/10卡片/排名/CTA 文案齐、无溢出、无泄漏；#1金色；副歌-15~-16dB一致、旁白-22dB ducking、无>1s静音、末1.5s淡出干净。

所有 id 均经 yt-dlp 元数据确认或 bili_search 返回。
**唯一画质短板**：那英《我不是天使》——官方MV是范植伟主演剧情片(无她演唱)，全网她唱本曲只有 480p 竖拍现场，已裁水印但偏软（rank#5）。其余 9 首均官方MV/官方Live/同期官方MV b-roll。
