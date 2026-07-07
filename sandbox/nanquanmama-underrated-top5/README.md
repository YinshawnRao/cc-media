# 南拳妈妈最被低估的5首歌（竖屏盘点 1080×1920）

倒数 05→01 解说盘点，男声 `zm_yunxi`，约 4:49。成片：`renders/nanquanmama-underrated-top5.mp4`（mux 后为准）。

## 榜单（揭晓顺序 05→01）
- 05 《离家不远》— 调色盘 2006（弹头词 / 张杰曲，写给家人）
- 04 《最后一枚笑容》— 2号餐 2005（弹头词曲，与 Lara 同唱）
- 03 《人鱼的眼泪》— 调色盘 2006（黄俊郎填词）
- 02 《破晓》— 2号餐 2005（开场曲，电子摇滚+古典）
- 01 《消失》— 2号餐 2005（周杰伦力挺主打，压轴）

## 选源 / 关键决策
见 `SOURCES.md`。要点：消失/破晓/离家不远 是真官方 MV（阿爾發，SD，底部卡拉OK烧词裁底，footage+audio 同源同窗口型同步）；人鱼/最后一枚 官方上传是静态专辑封面图 → 解耦（官方录音室音轨 + 本人其他官方 MV 画面：人鱼←《無瑕》冷调救场、最后一枚←《風雪梧桐》暖棕救场）；封面/片头片尾用《河流午後》乐团镜头。

## 复现
1. 配音：`tools/tts/venv/bin/python build/narrate_segments.py`（→ audio/*.wav）。
2. 源：`raw/` 下 YT 官方源（id 见 SOURCES.md），`p*_aud.wav`=各曲录音室音轨；`fr_*`=画面救场 MV（無瑕/風雪梧桐/河流午後）。
3. 人声段：`probe/vocal_src.json`（vocal_segments 各曲音轨）→ remap 成 `probe/vocal_analysis.json`（键=vert clip 名，供对齐闸门）。
4. 构建：`tools/tts/venv/bin/python build/full_build.py` → 过 `showcase_align.gate`(5/5 OK) → master.wav + clips_seg + **footage_track.mp4（单轨）** + index.html + cover_hero.png。
   - 耦合曲 fseek=mseek（口型同步）；解耦曲 fseek 手填（独立特写窗）。footage 内联 letterbox+crop+grade。
5. 渲染（**单 footage_track 避免 HF 多 video 帧0 协议超时**，-w2 重试 + --sdr）：
   `npx hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w2`
6. mux：`ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/nanquanmama-underrated-top5.mp4`

## 踩坑记录
- **官方频道 1080×1080 方画幅常是静态专辑封面图 + 音频**（人鱼/最后一枚），必须抽帧核实，不是真 MV。
- **卡拉OK烧词比目测高**：这批阿爾發官方 MV 烧词在 y≈405–435（不是最底 y450+），crop 到 H396 才裁净（消失 356 源 H320）；烧词会进模糊 bg，crop 必须彻底。
- `colorbalance` 无 `ms` 参数（蓝中间调是 `bm`）；冷调微调用 `colorbalance=rs=-0.05:bs=0.12:bm=0.06`。
- 离家不远 brief 标"南搞小孩(2008)"实为《调色盘》(2006) 原曲；人鱼词作者是黄俊郎非成员 → 口径已纠正。
