# 孟庭苇最被低估的5首歌

竖屏 1080×1920 音乐盘点，倒数 05→01（#1=《情愿一个人》压轴），男声旁白 `zm_yunxi`。
成片：`renders/mengtingwei-underrated-top5.mp4`（h264 1080×1920 + aac，约 4:31 / 271s）。

## 榜单（倒数）
05 爱你太真 · 04 不下雨就出太阳吧 · 03 手语 · 02 第二道彩虹 · 01 情愿一个人

选源/事实/对齐细节见 `SOURCES.md`。5 首全部非孟庭苇本人创作（她是演唱者），文案统一署词曲作者、不说"她写的"。

## 复现
```bash
# 1) 配音（男声 zm_yunxi）
tools/tts/venv/bin/python build/narrate_segments.py
# 2) 竖屏化 + 蒙太奇 + 封面（coupled 按 mseek 预切口型同步）
bash build/prep_clips.sh
# 3) 人声段分析 → vocal_analysis.json（keyed vert_<key>）
tools/tts/venv/bin/python tools/video/vocal_segments.py raw/p*_aud.wav -o probe/vocal_raw.json
#    （再 remap keys "<key>_aud"→"vert_<key>" 落 probe/vocal_analysis.json）
# 4) 构建 master.wav + index.html（内置展示段对齐闸门，违规不出 master）
tools/tts/venv/bin/python build/full_build.py
# 5) 渲染 + mux（--sdr 必加；HF 压平动态→必须后期 mux master.wav）
bash build/render.sh && bash build/mux_qa.sh
```

## 关键决策
- coupled（#5/#4/#3）：footage 与 audio 同源同窗，vert clip 按 `mseek` 预切 → 口型同步。
- decoupled（#2 蒙太奇 / #1）：footage 与 audio 分离；#2 取第二道彩虹 MV 她干净 B&W 特写拼接（剧情过重），#1 无 MV → 用《冬季到台北来看雨》她暖调特写救场。
- 烧词：爱你太真/不下雨 底部卡拉OK烧词全宽 crop 裁净；手语/第二道彩虹/冬季 官方源全宽干净。
- 展示段对齐闸门 5/5 OK；5 首副歌响度 -14.7~-15.1 dB。
- 已知取舍：#2 第二道彩虹展示段 17.8s（该曲官方 MV 剧情过重、最长连续副歌仅 ~21.5s，取她干净特写蒙太奇）；#5 爱你太真裁烧词后中心带偏窄（letterbox）。
```
