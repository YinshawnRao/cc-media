# 杜德伟最难的5首歌 — 素材与复现记录

**形式**：难度盘点，按用户给定排名倒数 05→01。  
**标题**：杜德伟最难的5首歌。  
**配音**：女声 `zf_xiaoyi`。  
**画幅**：竖屏 1080×1920，默认全宽 letterbox；只用横向安全 crop 裁掉字幕/水印，不做激进竖裁。

## 排名

1. 《不走》
2. 《无心伤害》
3. 《情人》
4. 《把你宠坏》
5. 《钟爱一生》

成片揭晓顺序：05《钟爱一生》→04《把你宠坏》→03《情人》→02《无心伤害》→01《不走》。片头不列榜单，片尾完整回顾。

## 双平台候选与取舍

| # | 歌 | 最终选用源 | 取用窗口 | crop | 对照与取舍 |
|---|----|------------|----------|------|------------|
| 05 | 钟爱一生 | YT `6rNlumm_3Uw` 滚石官方 MV，1390×1080 30fps，opus 立体声 | 02:45–03:55 | `1390:820:0:0` | B站 `BV1qg411477m` 为 2160p60 LD 采集但有大面积卡拉 OK 字幕，且音轨实际偏弱；YT 官方更干净，裁底部字幕后可用。另查 B站 `BV1qg411477m` / `BV1qD7rz3Ex8`。 |
| 04 | 把你宠坏 | YT `c4GuaUH3U9U` 滚石官方 MV，1390×1080 30fps，opus 立体声 | 02:05–03:15 | `1390:900:0:0` | B站 `BV18P4y1o7Ne` 1080P HD Remaster 实际视频码率约 1Mbps 且右上有圆形水印；YT 官方更干净。另查 B站 `BV1hr4y1U71C` Live / `BV1KZ4y1W7n1`。 |
| 03 | 情人 | B站 `BV16N4y1V7ox` p1，3840×2160 30fps，aac 317k 立体声 | 下载 02:20–03:25；成片使用 `clips/vert_qingren_clean.mp4`，等效约 02:28–03:25 | `3840:1780:0:140` | YT `iXqIb2KOC3M` 为滚石官方但码率低；B站 p1 高码率高音质，字幕/顶部频道字样通过横带 crop 裁净；原窗口开头有来源标题卡，成片顺延 8 秒避开。注意 p2 是伴奏，未用。 |
| 02 | 无心伤害 | B站 `BV13N4y1F7R1` p1，2880×2160 25fps，aac 317k 立体声 | 03:15–04:35 | `2880:1450:0:0` | YT `u650A5w7Ka0` 为滚石官方但对比下载断流且规格低；B站 4K/原盘提取规格明显更好，底部字幕用更窄横带 crop 裁净。 |
| 01 | 不走 | YT `pVsdqHo_neY` 滚石官方 MV，1390×1080 30fps，opus 立体声 | 04:20–05:40 | `1390:940:0:0` | B站 `BV15z421z7EP` 为 1080p60 修复，但右上/底部有上传者水印和字幕；YT 官方干净，裁掉底部歌词后可用。另查 B站 `BV1VCpdehErv` / `BV1oPKVeuEUz`。 |

## 当前产物

- 原始候选片段：`raw/*.mp4`
- 最终竖屏片段：`clips/vert_*.mp4`
- crop 抽帧检查：`qa/probe/vert_*_sheet*.jpg`
- 旁白脚本：`build/narrate_segments.py`
- 合成脚本：`build/full_build.py`

## 复现步骤

1. 按上表用 `yt-dlp --download-sections` 重下候选片段，需要有效 `sandbox/www.youtube.com_cookies.txt` / `sandbox/www.bilibili.com_cookies.txt`。
2. 按上表 crop 执行 `tools/video/vfill.sh` 生成 `clips/vert_*.mp4`。
3. 生成女声旁白：`tools/tts/venv/bin/python build/narrate_segments.py`。
4. 合成音频与 HTML：`tools/tts/venv/bin/python build/full_build.py`。
5. 渲染必须带 `--sdr`，渲染后用 `master.wav` 后期 mux：

```bash
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/dudewei-hardest.mp4
```

成片以 mux 后的 `renders/dudewei-hardest.mp4` 为准。
