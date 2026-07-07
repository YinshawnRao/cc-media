# 张韶涵最被低估的5首歌

竖屏 1080×1920 音乐遗珠盘点，倒数 #5 → #1，4:30。成片：`renders/angela-underrated-top5.mp4`。

## 榜单（倒数揭晓顺序 = 先 #5）
| 名次 | 歌 | 专辑·年 | 词曲（非张韶涵本人） |
|---|----|--------|---------------------|
| 05 | 幻想爱 | 梦里花 · 2007 | 陈伟 |
| 04 | 听见月光 | Over The Rainbow · 2004 | 姚若龙 / 潘协庆 |
| 03 | 惊天动地 | 潘朵拉 · 2006 | 潘协庆 |
| 02 | 复活节 | 欧若拉 · 2004 | 严云农 / 陈伟 |
| 01 | 偶尔 | 第5季 · 2009 | 王雅君 |

选源与口径细节见 `SOURCES.md`。**5 首全部不是张韶涵创作，旁白不说"她写的"。**

## 结构
封面（幻想爱特写动态底，连续流入 #5）→ 5 首（转场旁白 → 消化/swell → 连续副歌展示 25-30s）→ outro 榜单 + 主题升华 → 固定 CTA。

## 复现
```bash
tools/tts/venv/bin/python build/narrate_segments.py   # 旁白
python3 build/full_build.py                            # 切 footage + 建 master + html（内置对齐闸门）
bash build/render.sh                                   # 渲染(--sdr -w1 重试) + mux master.wav
```
- 全 DECOUPLED：footage = clips_seg/<key>.mp4（letterbox，裁底烧词），music = raw/p{N}_aud.wav 切 mseek。
- 单条 footage_track（HF 长片多 video 帧0 协议超时硬规则）。
- 成片以 mux 后 mp4 为准（HF 压平音频动态）。

## QA 结果
- 展示段对齐闸门：5/5 OK（副歌入点对旁白收尾、结尾落句末/gap）。
- 副歌响度 -15~-17dB 一致；旁白段 -22~-24dB（6-8dB ducking）；无 >1s 静音；末尾 fade。
- footage 烧词全裁净（幻想爱中英 / 遗失 / 隐形 / 潘朵拉双行卡拉OK，逐源量定 crop）。
- 无水印/网址/路径/提示词泄漏；HTML 无模板残留旧名。

## 判断点（可回退）
- #5 幻想爱官方 MV 仅 SD 640×480（band+金色麦田），brief 接受低画质；封面取 t=125 白毛衣特写。
- #1 偶尔用其极简艺术 MV（空房/气球/孤身），契合"内收克制"的收尾气质（特写较少但结尾落特写）。
- #3 惊天动地用潘朵拉 MV 粉裙群舞 + 特写，契合"大场面/少女英雄"。
