# SOURCES — 林夕给王菲写的歌，10首最封神（竖屏长片）

成片画幅 1080×1920 / 30fps / H.264 + AAC。render 加 `--sdr`，后期 mux `master.wav`。

## 词作 credits（已双源核实，全部林夕作词 ✓）

| # | 歌名 | 词 | 曲 | 专辑 | 年 | 语 | 主题标签 | 选源备注 |
|---|---|---|---|---|---|---|---|---|
| 10 | 人间 | 林夕 | 中岛美雪 | 《王菲》 | 1997 | 国 | 人间 | 官方MV有；本片用 B站 BV15N411Q7Lq 1080p（卡拉OK修复，烧词在底，裁顶660去除）|
| 9 | 红豆 | 林夕 | 柳重言 | 《唱游》 | 1998 | 国 | 相思 | 官方MV有、画面较干净 |
| 8 | 约定 | 林夕 | 陈小霞 | 《玩具》EP | 1997 | 粤 | 时间 | 粤语原唱（国语版周蕙）；官方MV有 |
| 7 | 暗涌 | 林夕 | 陈辉阳 | 《玩具》EP | 1997 | 粤 | 暗涌 | 官方MV系剪自《无常》素材；注意 |
| 6 | 流年 | 林夕 | 陈晓娟 | 《王菲》 | 2001 | 国 | 命运 | 2001同名专辑（非《寓言》）；洋娃娃/红色军装概念MV |
| 5 | 邮差 | 林夕 | 陈伟文 | 《只爱陌生人》 | 1999 | 粤 | 错过 | 国语版《蝴蝶》的粤语版；**无独立棚版MV，多为Live/Karaoke——预留Live救场** |
| 4 | 给自己的情书 | 林夕 | C.Y.Kong(江志仁) | 《寓言》 | 2000 | 粤 | 自爱 | 剧《婚前昏后》主题曲；国语版《笑忘书》；流通多Karaoke版，注意烧词 |
| 3 | 百年孤寂 | 林夕 | C.Y.Kong & 陈伟文 | 《只爱陌生人》 | 1999 | 国 | 孤寂 | 官方MV约1999 |
| 2 | 开到荼蘼 | 林夕 | C.Y.Kong(江志仁) | 《只爱陌生人》 | 1999 | 国 | 盛放 | 区雪儿执导官方MV，较干净 |
| 1 | 彼岸花 | 林夕 | 王菲 | 《寓言》 | 2000 | 国 | 彼岸 | 王菲自己作曲；"寓言五部曲"终章；**无独立棚版MV，多为巡演Live——预留Live救场** |

> 风险曲（无干净棚版MV，需Live/替代源 + 意象空镜救场）：**邮差、彼岸花**；**给自己的情书** 注意Karaoke烧词。

## 样片实际素材（封面 + 开头 + 第10首《人间》）

| 用途 | 平台 | URL / ID | 规格 | 处理 |
|---|---|---|---|---|
| 《人间》展示+开头王菲+封面主图 | B站 | `BV15N411Q7Lq` | 1080p AVC 立体声 | 卡拉OK修复，烧词在底部(y≈700+)；letterbox crop 顶部 660px 去词；含 MV110-118 的"Production House"制作署名(避开) |
| 《人间》全曲音频 | B站 | `BV15N411Q7Lq`(同) | 281s wav | 做音乐床+副歌；MV70 = 副歌入，与展示视频同窗→口型同步 |
| 城市夜景(港风) | YouTube | `ruZOvtJUS0g` | 1080p 干净 | full-bleed 压暗 |
| 老唱片转动 | — | CSS 旋转环 | — | 实拍黑胶 `tBBORlAa5WM`(Videli,干净)备用；本机渲染器 ≥7 video 超时，故样片改 CSS |

> YT 官方频道《人間》(`US54FpncMz4`) 仅 480p 且同样卡拉OK烧词 → 取 B站 1080p。

## 全片确认源（agent 抽帧核实；crop 为**原生宽度**，先裁再 scale 到 1080 宽 letterbox）

> 每首：`raw/<key>_audio.wav`（整曲，做床+同步）+ `raw/<key>_show.mp4`（副歌段，section 起点 = Tc−3）。
> 同步：music 从 source 偏移使 (Tc−3) 落在该首 SHOW_START；展示视频 _show 从 local0 播（=source Tc−3）。

> S0 = _show.mp4 local0 在源中的时间（=下载 section 起点）；crop 为**原生宽度** `W:H:X:Y`，先裁再 scale 到 1080 宽 letterbox。crop 的 H 我已逐首抽帧核实卡拉OK位置后收紧。

| key | 歌 | 平台 | ID | 源规格 | S0(s) | crop(原生) | 备注 |
|---|---|---|---|---|---|---|---|
| s10 人间 | B站 | BV15N411Q7Lq | 1920×1080 stereo 282s | 70 | `1920:660:0:0` | 卡拉OK修复,底烧词;已出样片 |
| hongdou 红豆 | B站 | BV1NJ411r7oz | 1440×1080 av1 stereo 254s | 115 | `1440:900:0:0` | 棚MV,黑白+彩发特写,底1行词 |
| yueding 约定 | YT | ygf2uiEUg64 | 640×480 stereo 266s | 65 | `640:285:0:0` | 粤语棚MV,软(480p),底2行词(收紧到285);B站带DECCA台标弃 |
| anyong 暗涌 | B站 | BV1pg411K7yb | 1440×1080 hevc stereo 267s | 127 | `1440:660:0:0` | 《无常》MV末段副歌(有特写),底2行词(收紧到660) |
| liunian 流年 | YT | mjuS9shGYhE | 1920×1080(active1406@x256) stereo 264s | 93 | `1406:980:256:100` | VEVO概念MV(洋娃娃),中景为主;左上MTV"NOW"台标→裁顶100 |
| youchai 邮差 | B站 | BV1Zq4y1E7C8 | 1440×1080 stereo 246s | 53 | `1440:1080:0:0` | 1999拉阔Live,紧特写,**全净无词无水印**;棚版是Karaoke弃 |
| qingshu 给自己的情书 | B站 | BV1sS4y1L7UH | 1920×1080 stereo 266s | 116 | `1920:970:0:0` | 菲比寻常Live,蓝眼妆特写(前~26s,后段转宽→展示控26s),底细词条 |
| bainian 百年孤寂 | B站 | BV1ZfHSzrEs9 | 1440×1080 stereo 317s | 93 | `1440:880:0:0` | 守望麦田国语MV修复,金属地/走廊特写,底繁体词;署名仅0:10 |
| kaidao 开到荼蘼 | YT | 8rnnsxbKBNw | 1920×1080(content1418@x246) stereo 316s | 89 | `1418:870:246:0` | VEVO官方MV(区雪儿),金裙特写,底简体词 |
| bianhua 彼岸花 | B站 | BV1Gp4y1y7BP | 1920×1080(content1920×750@y172) stereo 367s | 149 | `1920:720:0:175` | 2010唱游大世界Live,蓝银眼妆特写+宽镜,花瓣VFX(属画面);裁掉粉丝署名+黑边;棚版是中间烧词Karaoke弃 |

注：4:3 老 MV 裁底卡拉OK后约 4:3.x → scale 1080 宽得 ~1080×500-750，多数比《人间》(1080×372)更满。展示段抽帧逐首确认 Faye 在场窗口（部分 Live 中段转宽镜，展示窗口取特写密集段）。

## 复现命令

```bash
# 1 旁白   tools/tts/venv/bin/python build/narrate.py
# 2 素材   bash build/prep_clips.sh        # 主体 letterbox 裁顶660，氛围 full-bleed
# 3 音频   python3 build/build_audio.py    # master.wav + timeline.json（口型同步偏移 T0=70-SHOW_START）
# 4 合成   python3 build/build_html.py     # hf/index.html（4 video 上限：本机渲染器限制）
# 5 渲染   bash build/render.sh 30 auto full_raw    # --sdr，崩则重试
# 6 mux    bash build/finish.sh            # 覆盖音轨 → renders/linxi-faye-fengshen-sample.mp4
```

## 待全片注意
- footage 主体一律 letterbox（不竖裁放大）；展示段连续副歌 ≥25s。
- 本机渲染器 **≤4 个 `<video>`/composition**（≥7 必崩）→ 全片 10 首需**按歌分段渲染**再 concat（见 CONVENTIONS「长片切段」）。
- 邮差/彼岸花 预留 Live + 意象空镜；千禧台版 MV 普遍烧词，裁底。
</content>
