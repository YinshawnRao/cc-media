# design.md — 谭咏麟最被低估的5首歌

竖屏 1080×1920 · 女声 zf_xiaoyi · 倒数 5→1（片头不剧透排名，片尾列完整榜单）。

## 基调：暮色 / 黄昏（区别于刘德华那期的「午夜蓝 + 琥珀金」）

主题贯穿这五首歌的气质——成熟、克制、阴郁而耐听，像黄昏时分的自言自语（呼应 #5《黄昏的声音》、#2《墙上的肖像》的暗色画意象）。所以基调走**暮色暖调**：深茄紫夜空底 + 暮光铜玫瑰色 + 古铜金，底部一道「地平线余晖」暖光。比刘德华那期更暖、更忧郁。

## 配色

| 角色 | 色值 | 用途 |
|---|---|---|
| 底色 base | `#120e18` 深茄紫黑 | html/body 背景 |
| 暖强调 accent | `#e0936c` 暮光铜玫瑰 | 主强调（序号高光、点缀、压轴） |
| 金强调 gold | `#d8a86a` 古铜金 | 次强调（kicker、tag、年份） |
| 主文字 | `#f0e8df` 暖米白 | 标题/歌名/正文 |
| 弱文字 muted | `#9b8fa0` 暮霭灰紫 | meta、注释 |
| 标题渐变 | `#f7e6cf → #e6a878 → #c47a52` | 封面/歌名 webkit-clip 铜色夕阳渐变 |
| 压轴渐变 | `#fff0d8 → #f0b48c → #e0795a` | #1 序号/歌名（更暖更亮） |

层叠：footage(z0) → scrim 渐变压暗(z1) → vignette(z1) → 底部暖光 horizon glow(z1) → grain(z9) → 文案层(z5/6)。

- scrim：`linear-gradient(to bottom, rgba(12,9,18,.82) 0%, rgba(14,10,20,.18) 32%, rgba(12,9,18,.32) 58%, rgba(8,6,12,.94) 100%)`
- horizon glow（暮色motif）：底部 `radial-gradient(120% 56% at 50% 104%, rgba(224,147,108,.20) 0%, rgba(0,0,0,0) 60%)` mix-blend screen
- vignette：`radial-gradient(118% 80% at 50% 36%, rgba(0,0,0,0) 38%, rgba(0,0,0,.66) 100%)`
- grain：svg fractalNoise，opacity .05，soft-light（同 liudehua）

## 字体（Google Fonts 自动 fetch，CONVENTIONS 验证）

- 中文衬线主标 / 歌名：**Noto Serif SC** (500/700/900)
- 中文无衬线 UI / 标签：**Noto Sans SC** (400/500/700/900)
- 数字 / 年份 / 序号：**JetBrains Mono** (700/800)
- 西文斜体副标：**Cormorant Garamond** italic (500/600) — 封面英文副标 "The Underrated Five"

## 字号基线（1080×1920，手机端，比 desktop 直觉大一倍）

- 封面：cv-kick 26、cv-name 64、cv-title 156(serif 900)、cv-en 44(italic)、cv-sub 36
- 排名大卡：no 198(mono)、meta 29(mono)、song 84(serif 900，压轴 74)、tags span 29、tagline 43
- 展示期角标 labelMin：no 60(mono)、song 46(serif)
- 片尾 recap：rn 46(mono)、rs 46(serif)

## 结构（沿用 liudehua-underrated 验证过的时间轴模板）

封面(首帧=缩略图，不剧透排名，仅谭咏麟头像+作品描述) → intro 钩子(校长金曲太多→最好的藏在专辑深处→「遗珠 5」桥) → 5首(介绍旁白 床→消化位→swell→连续副歌展示 ≥26s) → 片尾(完整榜单 5→1 逐行揭晓 + 提问)。

- 揭晓顺序：05《黄昏的声音》→ 04《此刻你在何处》→ 03《永不想你》→ 02《墙上的肖像》→ 01《还是你懂得爱我》。
- 封面真人：用最干净的谭咏麟本人特写帧（从选定 footage 抽，优先正脸、避麦克风挡脸/过曝）。

## 动效基调

干净克制：序号 mono 上移入场、歌名 serif 上浮、tag chips stagger、卡整体淡出 hard-kill。封面首帧 opacity=1（不 fade-in），6s 后轻微 breathing。暮色暖光层全程极慢呼吸。
