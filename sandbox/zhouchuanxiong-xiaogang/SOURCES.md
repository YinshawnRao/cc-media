# 周传雄最“小刚”的5首 — 选源记录

主题：《周传雄最"小刚"的5首》。竖屏 1080×1920，**倒数盘点 5→1**（全新主题，非最难/非低估）。
女声 zf_xiaoyi。封面只给主题+作品描述、**不暴露排名**；排名片尾再列。
倒数顺序：#5 舍不得你走 → #4 风干我的悲伤 → #3 陪着我一直到世界的尽头 → #2 吉普赛情人 → #1 哈萨雅琪。

## 选源硬约束执行
- 每首两边都搜（YouTube + B站）。所有"MV 讲什么/有无本人/有无烧词/水印"均**抽帧核实**后定（[official-mv-may-be-live]）。
- **关键发现（早期小刚 1991-1993）**：① 这些早期 MV 是台版 LD/歌林/DVD 的 **KTV 卡拉OK 版，普遍底部烧繁体歌词**（源内禀，全宽裁底）；② **官方"周傳雄 Steve Chou"频道上传都是静态专辑封面音轨**（非画面），不可用；③ **B站/YT 的"HD/4K 修复版"多是现代风景/彩虹/演唱会二次剪辑（无年轻小刚）**（吉普赛 Bluemusic、陪着我 無名小刀 均为纯风景重剪）——原始年轻小刚画面只存在于 **SD 或带粉丝频道水印的版本**。选源以"年轻小刚本人画面 + 可裁净水印"为先，清晰度次之。
- **B站 412 风控**：yt-dlp 的 BiliBili extractor 被 412 风控（playurl 端点），但 `curl --compressed`+桌面UA+referer+cookie 能取页内嵌 `window.__playinfo__` 直链 → 复用 **`tools/video/bili_dl.py`** 救场。

## 逐首（倒数顺序）

### #5 舍不得你走（1991）挽留 — B站 官方MV DVD ✅HD
- B站 `BV1cVApz9ELY`（樱花色季节, 舍不得你走【官方MV】DVD MTV Karaoke 1080P）：**1920×1080 h264 立体声, 干净（无频道水印）**, 年轻小刚 + 女主 sepia 剧情。底部烧繁体歌词。
- YT `rMS2hSyhsSo`（棉花糖 1080p）：单车镜头, 右上 "TuneInTube.com" 水印 + 4:3 pillarbox → 次选。
- **最终：B站 `BV1cVApz9ELY`**。chorus "舍不得让你走" ~94/112s。crop 裁底烧词, letterbox。

### #4 风干我的悲伤（1993）失落 — YT 江男 ✅HD
- YT `WiCj__HLR_M`（江男, 風乾我的悲傷 小剛）：**1920×1080, 干净（无频道 logo）**, 年轻小刚 + 马 絲路场景。底部 2 行烧繁体歌词。
- B站 `BV1bQGRzJEUm`（歌林原版KTV）：1080×720, 右上小 logo + 烧词 → 次选。YT 後援會 `UD3OWwIZCzI` 圆形 logo 弃。
- **最终：YT `WiCj__HLR_M`**。chorus "风干我的悲伤" ~92-102s。crop 裁底 2 行烧词, letterbox。

### #3 陪着我一直到世界的尽头（早期）纯情 — YT 後援會 高清MV ✅HD
- YT `nPhQn1ru_XI`（周傳雄全球後援會, 高清MV）：**1920×1080**, 年轻小刚 艺术 MV（黄昏海边漫步 + 暖光特写 + 沙漠/抽象镜头）。水印=**左上专辑缩略图（角）+ 底部 URL/QR 横带**（均可裁/delogo, 此窗无中部圆 logo）。
- B站 Micronorth `BV1gJ411M7gM`：576×432 同 MV 但太糊；YT 無名小刀 `To1ASZg2s04` 1080p 是**纯风景重剪无小刚** → 弃。
- **最终：YT `nPhQn1ru_XI`**。小刚镜头 ~158-185s（海边漫步→特写）。delogo 左上缩略图 + crop 裁底 URL/QR, letterbox。（艺术 MV 自带抽象镜头属源特征）

### #2 吉普赛情人（早期）心动 — B站 480p（标志絲路造型）⚠️SD
- B站 `BV1HtwizoEKb`（耍姑娘的小猴子, 小刚-吉普赛情人mv）：**720×480 SD**, 年轻小刚 **絲路/吉普赛造型（金绣马甲, 蓝天张臂）标志镜头**, 无烧词。水印=左上 UP名+bili / 右上 酷我 KUWO+URL（均在顶部, crop 裁顶可去）。
- YT 後援會 `NV_W1dmcxqY` 720p 絲路版=中部圆 logo（裁不掉）弃；棉花糖静图弃；Bluemusic/環球=现代重剪/剧情无小刚弃。
- **最终：B站 `BV1HtwizoEKb`（SD）**。标志造型 ~120s。crop 裁顶（去 bili+酷我 水印）, letterbox。SD 是 1991 早期遗珠的源现实（[官方频道仅静图, HD 版均现代重剪无本人]）。

### #1 哈萨雅琪（1992）声音名片 — B站 台版LD ✅近HD
- B站 `BV13Q4y1A7eS`（DAVE2013, 台版/LD采集 KTV）：**1470×1080 h264 立体声**, 年轻小刚 海盗/罗宾汉嬉游造型 跳唱（早期偶像感拉满）。水印=**左上"奇歌伴唱"KTV logo + 右上"@DAVE2013"**（两个顶角, delogo 去）+ 底部烧繁体歌词。
- YT 後援會 `Au7LQWm2FtY`（1992HDMV 1080p）：同期但**中部圆 logo 裁不掉** → 弃。
- **最终：B站 `BV13Q4y1A7eS`**。chorus "哈萨雅琪哈萨雅琪 一朵小野菊" ~126s。delogo 两顶角 logo + crop 裁底烧词, letterbox。压轴 #1。

## 处理总览
- 全部 **letterbox 保原比例**（早期 MV 多 4:3/单主体, 但保守起见统一信箱式不放大）。
- 烧词/水印：能 crop 全宽横带就 crop（裁顶/裁底）；角落 logo 用 delogo（hasa 两顶角 / peizhe 左上缩略图）。
- 色温弧（少年明亮→怀旧→暮色）：见 build/prep_footage.sh。
- 音乐源=各 MV 自带录音室原声（footage 窗==音乐窗→口型同步）。jipu 无烧词, chorus 窗以标志造型+RMS 复核。
