# Sources — 动力火车最难的5首歌

Cookie files checked: YouTube `sandbox/www.youtube.com_cookies.txt` · B站 `sandbox/www.bilibili.com_cookies.txt`

Selection rule (硬约束): both YouTube and B站 searched for every song. 动力火车是**双人组合**（尤秋兴 + 颜志琳）→ footage 一律 **letterbox 保原比例**，禁止竖裁放大。这是声乐难度盘点，展示段优先**双人真唱画面**；官方 MV 若是概念/剧情片（不露双人）则改 Live。早期(1997–1998)歌官方 MV 多为 480p + 烧死歌词，属源限制，底部烧词用全宽 crop + 合成期遮罩处理。

排名（难度 1=最难）→ 倒数揭晓 5→1：
1.《明天的明天的明天》 2.《彩虹》 3.《无情的情书》 4.《背叛情歌》 5.《除了爱你还能爱谁》

---

## 05.《除了爱你还能爱谁》(p5_chule) — 张雨生 作曲
- YT 候选：`MmB89uh_pnU` 華研官方MV 1280x720 — **概念片**（鸟/落叶/鱼缸，窗内无歌手）+ 烧词 + HIM 角标 → 弃（不露双人）
- YT 候选：`gFlB24klCCE` 下一站Live 834x480 低清；`mE_DL6bfEDw` 2026红白純享
- B站 候选：`BV1wt4y1B7bA` 下一站巡演 1080P，双人 + 特写，底部仅唱词行时有烧字幕（可全宽裁） ← **选用**
- B站 候选：`BV1ca411K7Lw` Live'98 VCD修复 3:55；`BV13b4y1z7xb` 磁带音频
- 最终：B站 `BV1wt4y1B7bA`（1080P 现场，双人真唱，裁底部唱词带）

## 04.《背叛情歌》(p4_beipan)
- YT 候选：`2t0P9zKj4OQ` 華研官方MV 712x480 — 剧情片(女演员/打电话) 穿插双人(火车窗弹唱) + 烧词 ← **选用**（取双人演奏段，裁烧词）
- YT 候选：`74WHIl4KqMY` 现场版 + 烧字幕/反应镜头；`u-xbxPl1kj0` 公视音乐万万岁 480p
- B站 候选：`BV1Rywfz5EAs` 官方MV HD版 1080P 但 "ABmusic" UP水印居中 → 弃；`BV1ns4y1D782` Live'99 VCD 烧词 + "LiLi" 左上水印 → 弃
- 最终：YT 官方MV `2t0P9zKj4OQ`（取双人弹唱连续段，全宽裁烧词；剧情段回避）

## 03.《无情的情书》(p3_wuqing) — 首张专辑同名招牌难歌
- YT 候选：`pPr8vkMAe9w` 華研官方MV 712x480 — 屋顶乐队演奏(露双人)+ 底部烧词 ← **选用**（裁烧词）
- YT 候选：`khZJei9TWhg` 下一站Live 1080P 但烧字幕 + 右上频道水印 → 弃
- B站 候选：`BV1TY4y137SU` Live'98修复 1584x1080 但右上"Live'98"水印 + 暗 → 弃；`BV1KgVs6SE1y` 4K专辑(静图音频)
- 最终：YT 官方MV `pPr8vkMAe9w`（屋顶演奏，裁底部烧词）

## 02.《彩虹》(p2_caihong)
- YT 候选：`fYrBo8XEssE` 華研官方MV 712x480 — **干净**、双人特写、无烧词 ← **选用**
- B站 候选：`BV1kv4y1f7wz` 下一站巨蛋Live 1080P 但底部烧字幕 + 歌手偏小(宽景) → 次选；`BV1vM411676J` KTV修复
- 最终：YT 官方MV `fYrBo8XEssE`（干净双人特写，480p 属源限制）

## 01.《明天的明天的明天》(p1_mingtian) — 6:47 长曲，双人和声 + 尾段体能
- YT 候选：`Z_GwKSC1kF8` 華研官方MV 712x480 — 概念叙事(荒漠/隧道/吉他房)，双人无清晰特写 → 弃
- YT 候选：`REhDFA6zLhU` 下一站Live 1080P 但右上频道水印 → 弃
- B站 候选：`BV1ht4y1B7k6` 下一站巡演 1080P，室内 arena，**干净**(无烧字幕/无水印)，双人特写 ← **选用**
- B站 候选：`BV153411u76c` Live'98修复 6:39；`BV1kHVB6UEf5` 4K专辑(静图音频)
- 最终：B站 `BV1ht4y1B7k6`（1080P 室内现场，干净，双人真唱）

---

## 最终切窗 / crop（letterbox，全宽去污染带）
窗按"副歌展示满量"定位（人声段检测 + 响度 + 抽帧三重核实）。clip 从 (chorus − PRE) 切起（PRE=旁白时长+约2s），footage 窗==音乐窗 → 口型同步。

| # | key | 源 | 副歌起点(源s) | show | crop | 说明 |
|---|---|---|---|---|---|---|
| 05 | p5_chule | B站 BV1wt4y1B7bA 下一站Live 1080P | 82 (早段 79–118 唱段, -13.6dB) | 34s | `1920:800:0:0` | 裁底部烧字幕(源y865–935)；早段歌手特写多、无观众切镜，胜终段窗 |
| 04 | p4_beipan | B站 BV1PwrhYMEBF 室内Live 1080P | 232 (终段 234–259, -18.4dB) | 32s | `1920:852:0:92` | 顶裁"牛虻仰望星空 bilibili"水印(y50–88)+底裁烧字幕(y955–990)；MGAIN 1.12 |
| 03 | p3_wuqing | YT 官方MV pPr8vkMAe9w 屋顶 480p | 193 (193–227 连续34s, -24dB) | 34s | `712:380:0:28` | 顶+底裁烧词；屋顶白天双人弹唱(可见)，胜过暗调Live'98；MGAIN 1.18 |
| 02 | p2_caihong | B站 BV1Z54y1W7Z3 巨蛋演唱会2021 1080P | 226 (终段 224–271, -15.6dB) | 36s | `1920:1080:0:0` | 干净(无烧字/无水印)双人特写满屏；弃橄榄球剧情官方MV |
| 01 | p1_mingtian | B站 BV1ht4y1B7k6 下一站Live 1080P | 256 (225–337 大唱段内, -13.8dB) | 44s | `1920:900:0:0` | 室内arena；**该源底部有烧字幕(源y915–975，下一站系列加的歌词条)→裁掉**；双人特写+LED宽景；弃荒漠概念官方MV；finale 给最长展示 |

> ⚠️ 坑：B站「下一站巡回演唱会」系列(明天)烧入了歌词字幕条(底部 y~915-975)，初版抽帧恰好避开带词帧而漏判；务必抽多帧查底部。彩虹用的「巨蛋演唱会2021」(BV1Z54y1W7Z3)则无烧字。

intro 背景底 = vert_mingtian（暗调 arena，封面文字易读）；outro 背景底 = vert_caihong（巨蛋终场）。
QA（master.wav）：展示段副歌 mean −14.3 ~ −16.8dB（差<2.5dB）；旁白段 −18.9 ~ −20.1dB（ducking 差 4–5dB）；max 全 <0dB；无 >1s 整片静音。
