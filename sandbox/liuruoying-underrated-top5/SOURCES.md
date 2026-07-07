# 刘若英最被低估的5首歌 — 选源与构建记录

竖屏 1080×1920 解说盘点，倒数揭晓 第5→第1（climax=打了一把钥匙给你）。
**COUPLED 音频**：每首 footage 与音乐同源同窗（官方MV/干净Live），副歌段口型天然同步。
最终音频后期 mux master.wav（HF 压平动态）。`--sdr` 必加。

## 专辑/年份（已 web 核实，brief 多处有误，以下为准）

| 名次 | 歌 | 专辑 · 年 | brief 写的 → 实际 |
|---|---|---|---|
| 5 | 我曾爱过一个男孩 | 我等你 · 2000 | （未写）→ 我等你 2000（黄莺莺1993原唱，刘版收我等你） |
| 4 | 阁楼 | 到处乱走 · 1996 | 到处乱走~1998 → **1996** |
| 3 | 透明 | 很爱很爱你 · 1998 | 很爱很爱你 → 年份补为 **1998** |
| 2 | 点亮橘子树 | 年华 · 2001 | 年华2007 → **2001**（2007是《我的失败与伟大》） |
| 1 | 打了一把钥匙给你 | 雨季 · 1995 | （未写）→ **雨季 1995**（非少女小渔；陈昇/王中言） |

## 各首选源（footage = 音乐 同源）

### 第5名《我曾爱过一个男孩》— YT 9lsCeDkXB9s（滚石官方MV，2001）
- 640×480 4:3 VP9/opus stereo。CLEAN（无台标/水印/URL），仅底部烧词（居中 ~68-72% 高，B站版四角全是水印弃用）。
- **叙事MV**：穿插刘若英 + 男主角（“那个男孩”）。她与男孩交替出镜 = 切题（歌名即男孩）。
- 下载窗 src 95-170 → letterbox（保留居中烧词，属官方MV原生）。showcase: ch_off=56.0(vert-local) show=22.0，她/男孩交替剪辑段。

### 第4名《阁楼》— 画面 YT hV7CXIRr3cw（单身日誌Live）+ 音频 YT D_K9NF5mCwk（1996录音室版）【解耦】
- **该Live整条音轨人声被埋/疑伴奏向，用户两次听出"完全没人声"；换窗也没用→源本身的问题**。
- 终解=**解耦**：音乐用1996录音室版（D_K9NF5mCwk，到处乱走专辑音频，人声干净；副歌 180.23-205s 连续24.9s）；画面用Live她特写（crop=720:300:0:0 裁底KTV词 + letterbox）。
- showcase: 画面 ch_off=24（src140-166她特写）；音频 aud_src=p4_studio aud_ch=180.23 show=25.7。慢歌口型微差（Live画面 vs 录音室音轨）为救场代价。解耦首排除出 coupled showcase_align gate。

### 第3名《透明》— YT eu20WH2acvM（官方MV，B&W 艺术片）
- 640×480 4:3 stereo。黑白，唯一官方MV。竖排繁体歌词随镜移动（左/中/右），裁不掉 → 属原生美学保留。B站“4K修复”是假升频+粉色调弃用。
- showcase: ch_off=24.31 show=18.9（连续18s人声段，正脸特写最密，96%覆盖）。

### 第2名《点亮橘子树》— YT V0ICiPAgYtU（飞行日巡演 北京 2025-12-27 Live 4K）
- 下载≤1080p stereo。**全干净无水印**（B站同场含UP水印弃用）。无棚版MV（专辑曲）。橙色火星雨舞台 = 切题（橘色/橘子树）。
- 宽机位arena→letterbox不放大（竖裁会把她裁没）。showcase: ch_off=20.53 show=27.67（火星雨段，57%覆盖；慢live人声检测偏碎，已耳验思路=连续段）。

### 第1名《打了一把钥匙给你》— B站 BV1qSvXBYEVg（官方叙事MV 4K修复，1080p）
- 1920×1080 H.264 AAC stereo。CLEAN，仅底部烧词 y920-1010 → **crop=1920:880:0:0**。同YT 480p官方MV，B站修复版更清。
- 末段情感高潮：她特写(src250) → 钥匙在手特写(src272, 即“钥匙”题眼)。**MV结尾标题卡在 src~296 → 窗截到 src288 前避开**。
- showcase: ch_off=22.0 show=26.0（她特写→双人室内→钥匙特写，climax）。封面也取自此段她正脸B&W…（实际封面用《透明》B&W正脸特写）。

## 封面
cover_hero.png = 《透明》B&W 正脸特写（raw-local 25 = src55，hands-on-face，裁掉右侧竖词，居中填满）。真人、高辨识、贴“文艺遗珠”主题。

## 构建
- build/full_build.py：COUPLED（video & music 同 mseek 切同一 vert clip）；showcase_align.gate 5/5 OK。
- **多 footage → 单 footage_track.mp4 + 单 `<video>`**（HF 多video 帧0 protocolTimeout 挂死 + 本机GPU与并发渲染争用会 Target closed）。叠加层照常多 track。
- 渲染 build/render.sh（-w2 + 5次重试，--sdr）。mux：
  `ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/liuruoying-underrated-top5.mp4`
- 响度（showcase mean）：p5 -15.1 / p4 -15.7 / p3 -14.1 / p2 -15.5 / p1 -16.3 dB；旁白 ~-22~-23.5（duck 差7-8dB）。无 >1s 静音。
