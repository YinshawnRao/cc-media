# 张惠妹最苦的5首歌 (amei-saddest-top5)

竖屏 1080×1920 倒数盘点（第5→第1），女声 `zf_xiaoyi`，**5:01**。
成片：`renders/amei-saddest-top5.mp4`（H.264 + AAC 立体声，已 mux 预混 master.wav）。

## 揭晓顺序（倒数）
连名带姓⑤(2017) → 掉了④(2009) → 剪爱③(1996) → 我恨我爱你②(2001) → 人质①(2006，压轴)

片头封面**不公布排名**（标题 + 作品描述 + 真人正脸）；片尾揭晓完整榜单 1→5；最后固定引流 CTA。

## 选源 / footage
见 `SOURCES.md`。两平台均查证、每首抽帧核实是阿妹本人。
- 人质①/掉了④ = 官方棚版 MV 4K（人质 YT 黑白、掉了 B站华纳修复）。
- 剪爱③ = YT 官方 MV（1996，480p，裁底烧词）。
- 连名带姓⑤ = B站 2023北京 Live（官方 MV 是 Selina 主演剧情片无阿妹）→ 竖向放大填满（黑底单人，自动避开右下水印）。
- 我恨我爱你② = B站 Live'01（官方 MV 是替身女演员）→ letterbox，裁顶水印+裁底烧词。

## 复现
```bash
bash build/download.sh     # 下载 5 首 footage 窗口（YT/B站 cookie）
tools/tts/venv/bin/python build/narrate_segments.py   # 女声旁白（含固定 CTA）
bash build/clips.sh        # 竖屏化（letterbox / 单主体竖裁；剪爱裁底烧词；窗口对齐副歌）
python3 build/full_build.py # master.wav + index.html（含 MGAIN/时间轴realign）
bash build/render.sh       # render --sdr（重试循环）+ mux 预混 master
```

## QA 结论
- 无 >1s 静音；各首副歌 -14.8~-16.3dB（1.5dB 内）；旁白段音乐 duck 到低床。
- 画面无水印/网址/歌词/路径泄漏；榜单/序号正确；封面首帧可作缩略图（本人正脸）。
- 注意（源限制）：掉了=AMIT 沙漠概念 MV、剪爱=海边 MV，副歌段含官方 MV 自带的空镜/乐队/海景切换（阿妹为主但非全程特写）；两平台均无"全程特写连续版"。
