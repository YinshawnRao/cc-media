# 杨千嬅最难的5首歌 — 选源与制作记录

竖屏 1080×1920，倒数 5→1，全程女声旁白 (zf_xiaoyi)。片头不剧透排名（仅封面+作品描述），片尾完整榜单。
成片：`renders/yangqianhua-hardest.mp4`（HF 渲染 → 预混 master.wav 后期 mux）。总时长 ~4:39。

## 排名（用户给定）/ 揭晓倒数 05→01
| 名次 | 歌曲 | 难点（brief） |
|---|---|---|
| 01 | 小城大事 | 副歌爆发但不苦情大嗓；看破还要体面地碎掉（压轴） |
| 02 | 可惜我是水瓶座 | 气息+情绪控制；长句拧巴，克制里的拉扯 |
| 03 | 少女的祈祷 | 轻快旋律里的密集控制；咬字/节奏/少女感并存 |
| 04 | 野孩子 | 词即是曲；粤语声调贴死旋律，收放见层次 |
| 05 | 假如让我说下去 | 情绪稳定地狱；中低区唱崩溃感、声音还要稳 |

## 展示段选源（两平台对照后定）

> 千禧粤语金曲普遍坑：官方 MV / B站修复版多带**烧死卡拉OK歌词**；B站 4K 现场多带 **UP主水印**；
> "MY LIVE TV"(杨千嬅官方YT频道) 多条"MV"实为**专辑预告静图**或拉阔 Live。逐源抽帧验真后定。

| # | 歌 | 最终源 | 规格 | 展示窗(源时间) | 裁切/处理 |
|---|---|---|---|---|---|
| 01 | 小城大事 | B站 4K Live「最美现场」AK老黄瓜 `BV14y4y1h7wn` | H264 1080p 立体声 | 80–112s(副歌「再来也许要天上团聚」) | delogo去左上UP水印 + crop 1920:900 去底字幕 + letterbox |
| 02 | 可惜我是水瓶座 | B站蓝台 Live(深发黑纱) 音乐私藏馆 `BV1Rv41117JG` | H264 1080p 立体声 | 144–170s(hook「水瓶座最爱是流泪」) | crop 1920:900 去底字幕 + letterbox |
| 03 | 少女的祈祷 | B站 4K60 Live(白金发) 音乐私藏馆 `BV1sK411J74T` | H264 1080p 立体声 | 110–136s(副歌) | crop 1920:900 去底字幕 + letterbox |
| 04 | 野孩子 | YT Concert YY 黄伟文作品展 `9jlW7zoO_eM` | VP9 720p | 136–162s(副歌「明知爱这种男孩子」) | crop 1280:608 去底字幕 + letterbox |
| 05 | 假如让我说下去 | B站个人 2015 Let's Begin 巡演(红羽裙) `BV155411T7so` | H264 1080p 立体声 | 124–150s(副歌「你可不可以暂时别要睡」) | crop 1920:900 去底字幕 + letterbox |

- **intro/outro 底**：小城大事 Timeless 官方 MV `WJaufugjeSQ` 黑白月台开场 [5–34s]（crop 1920:720 letterbox，避开 38s 起的歌词+Warner水印）。
- **封面主图**：假如个人 2015 红羽裙特写 @146s（裁 9:16 聚焦脸、避开底字幕）→ `hf/cover_assets/cover_bg.jpg`。

### 弃用 / 坑记录
- 小城大事 Timeless 官方 MV：真 MV(公路/电塔戏剧化)，但**底部烧死卡拉OK双行歌词**→裁后 letterbox 带过窄(405)、她偏小，不如 Live 特写饱满 → 仅用其黑白开场作 intro 底。
- 小城大事 "MY LIVE TV `rBZ0nnQ1NOI`"：实为《电光幻影》专辑预告静态(右侧烧死大logo)，**非 MV**，弃。
- 少女的祈祷 華星官方 `CvKvXNiXQZc`：1999 真 MV 但烧死卡拉OK歌词+4:3 pillarbox+三分屏蒙太奇 → 改用 B站 HD Live 大特写。
- 少女的祈祷 "MY LIVE TV `UiLmSS418Go`"：专辑「Play It Loud」预告静图，弃。
- 可惜我是水瓶座 官方 MV `Fz0erNNpTGQ`(480p)：干净无烧词但**故事/情侣戏(拳击+男主)太重**，无连续她演唱窗 → 改 B站 HD Live。
- 可惜 Concert YY `Y8b-cOBVeSI`：字幕显示歌词疑似该作品展另一首/串烧，song 匹配存疑，弃。
- 假如让我说下去 903拉阔 `n2cB8kHA7No` / B站 `BV1Zf4y1B76x`：实为**容祖儿+杨千嬅二重唱**（另一歌手戏份重），个人盘点不宜 → 改杨千嬅 2015 个人巡演 SOLO。

## 配音
- 全程女声 `zf_xiaoyi`（Kokoro+misaki[zh]）。逐字稿见 `narration.json`。TTS 安全：无英文字母、歌名全中文。
- 旁白节奏：床→swell→展示；副歌展示段无旁白、音乐全量。

## 音频（master.wav，后期 mux）
- 逐段 床(0.20)→swell→展示(1.0) 包络 + 旁白 ducking；逐首 loudnorm I=-14 + MGAIN 微调。
- QA：5 首副歌展示段响度 -12.4~-12.7dB（spread 0.3dB）；无 >1s 整片静音。
- MGAIN：p5_jiaru=0.83, p2_shuiping=1.05, p1_xiaocheng=1.15。

## 复现
1. `build/narrate_segments.py`（女声旁白 → audio/*.wav + narration.json）
2. `build/clips.sh`（raw → 展示段竖屏 letterbox clips，含 delogo/crop）
3. `build/full_build.py`（master.wav + index.html）
4. `build/render_retry.sh`（HF render --sdr -w1 重试循环 → renders/full_raw.mp4）
5. `build/finalize.sh`（mux master.wav + QA → renders/yangqianhua-hardest.mp4）

> 版权：当前仅本地测试，不发布、不商用。
