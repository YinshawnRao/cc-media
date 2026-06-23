# 《杨丞琳最超神的5段Bridge》素材记录

本轮按最新规范只读取仓库根目录 cookie：

- YouTube: `www.youtube.com_cookies.txt`
- B站: `www.bilibili.com_cookies.txt`

旧的 `sandbox/www.*_cookies.txt` 未使用。

## 平台复核结论

YouTube 官方 MV 候选已重新逐条验证，但 `yt-dlp --cookies www.youtube.com_cookies.txt --skip-download` 仍统一触发：

> Sign in to confirm you’re not a bot.

受影响候选：

- 《匿名的好友》Rainie Yang 官方 MV: `https://www.youtube.com/watch?v=s9hGDIpwfXw`
- 《带我走》YouTube 官方 MV: `https://www.youtube.com/watch?v=KOLDiXnQC7Q`
- 《仰望》YouTube 官方 MV: `https://www.youtube.com/watch?v=had4aS-ludw`
- 《喜剧收场》YouTube 官方 MV: `https://www.youtube.com/watch?v=BtZoaPq8KSQ`

B站根 cookie 验证可用；用户指定《左边》源 `BV1GZ4y1f7md` 可列出 1080P 与 4K 档位。

## 最终选源

### TOP 5《喜剧收场》

- YouTube: 官方 MV 候选存在，但 cookie 仍被 bot challenge 拦截，无法下载。
- B站: `BV1MW411N78H?p=38`，合集 P38，1280x720，立体声。
- 选择: B站 P38。理由：可下载、画面为 MV 内容，清晰度和音频可接受；此前 `BV11M4y1E7zk` 是手机拍音乐播放器，已拒用。
- 成片切点: 源 150s-213s。该源字幕与 brief 起句不完全一致，按 MV 内实际 bridge 连续段保留到“再次拥抱我”附近。

### TOP 4《仰望》

- YouTube: 官方 MV 候选存在，但 cookie 仍被 bot challenge 拦截，无法下载。
- B站: `BV1iM4y1A7fj`，MV 4K 修复源，1920x1080，立体声。
- 选择: B站修复源。理由：B站官方低清源只有 640x480；该源是同 MV 内容的高清修复版，可裁掉顶部标识和底部烧字。
- 成片切点: 源 157s-187.8s，从“无法预知”附近进入，到 bridge 结束前收住；不带后续“仰望你”副歌段。

### TOP 3《带我走》

- YouTube: 官方 MV 候选存在，但 cookie 仍被 bot challenge 拦截，无法下载。
- B站: `BV1RV4y1p75A`，MV 4K 修复源，1920x1080，立体声。
- 选择: B站修复源。理由：B站官方源 `BV1iJ411x7PY` 只有 640x480；该修复源为同 MV 内容的高质量版本。
- 成片切点: 源 150s-168s。brief 中“白马溜过漆黑尽头 / 刻在心中拍打着脉搏”未在当前 MV 字幕和可检索公开歌词中匹配；成片采用 MV 内实际 bridge 段，并在“带我走”副歌反复开始前结束。

### TOP 2《匿名的好友》

- YouTube: Rainie Yang 官方 MV 候选存在，但 cookie 仍被 bot challenge 拦截，无法下载。
- B站: `BV1tVCMYEEA9`，4K 修复源，1920x1080，立体声。
- 选择: B站修复源。理由：可下载，画面干净度可通过横带 crop 控制，音频为立体声。
- 成片切点: 源 53s-70s，覆盖“也许我们当时年纪真的太小”到“但思念还转动”。

### TOP 1《左边》

- 固定源: `https://www.bilibili.com/video/BV1GZ4y1f7md`
- 选择: 保持用户指定 B站源，不替换。
- 可用规格: 1438x1080 1080P/2878x2160 4K 档均可列出；成片使用已下载的高质量版本 `raw/left_fixed_hq.mp4`。
- 成片切点: 源 92s-126s，覆盖“我一直相信总有一天”到“你说的那句我爱你”。

## 画面处理

全部展示段先预切，再通过 `tools/video/vfill.sh` 做 1080x1920 竖屏 letterbox。只裁全宽横带以去除顶部标识和底部源字幕，不做窄竖裁放大。

已抽帧确认：

- `probe/qa_xiju_vert.jpg`
- `probe/qa_yangwang_vert.jpg`
- `probe/qa_daiwozou_vert.jpg`
- `probe/qa_niming_vert.jpg`
- `probe/qa_left_vert.jpg`
