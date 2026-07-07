# 素材来源与取舍

## 总原则

按仓库约束，每首都查 YouTube 与 B站候选，优先级为：清晰度、画面干净度、立体声、现场/正片质量、是否有明显平台或 UP 主水印。最终源均使用根目录 `all_cookies.txt` 获取或校验，不在 `sandbox/` 复制 cookie。

## 第 5 名：《夏令时》

- YouTube 候选：`NP4xNDLcul0`，风华秋实 RF ENTERTAINMENT，鹿晗 2023 「πDAY演唱会」武汉站现场，1080p60，立体声。
- B站候选：`BV1tG4y1N7hW`、`BV16N411D7Ra`，以粉丝/现场竖屏源为主。
- 取舍：未找到更干净的官方 MV。最终选 YouTube 风华秋实现场源，清晰度和声音更稳定，无平台水印，现场近景足够多。
- 本地文件：`raw/p5_xialingshi.mp4` → `clips/vert_xialingshi.mp4`。

## 第 4 名：《梦寐之地》

- YouTube 候选：`giazjcYDjzk`，风华秋实 RF ENTERTAINMENT，1080p，但抽帧显示几乎为静态封面。
- B站候选：`BV1Li4y137tF`，官方1080P影视片段；`BV1Vu41157W1`，鹿晗工作室 LuhanStudio 三巡演唱会现场。
- 取舍：YouTube 源虽然官方但静态，不适合成片；`BV1Li4y137tF` 人物主体不是鹿晗为主。最终选 `BV1Vu41157W1` 工作室现场，主体明确、画面有运动、无平台水印。
- 本地文件：`raw/p4_mengmei_live.mp4` → `clips/vert_mengmei.mp4`。

## 第 3 名：《夜的尽头》

- YouTube 候选：`V4lI2Oo8NGI`，风华秋实 RF ENTERTAINMENT，Official Music Video，1080p25，立体声。
- B站候选：`BV1bk4y167sw`，风华秋实官方频道，1080p25；`BV1R441117Jt`，Sunflower 鹿晗转存。
- 取舍：YouTube 与 B站官方源画面规格接近。最终选 YouTube 官方 MV，下载稳定、音视频规格完整，未见平台水印。
- 本地文件：`raw/p3_yedejintou.mp4` → `clips/vert_yedejintou.mp4`。

## 第 2 名：《某时某刻》

- YouTube 候选：`bcHsWONb27o`，LuHan Studio，Music Video，1080p25；`3BmE9cJoMdg`，风华秋实 RF ENTERTAINMENT。
- B站候选：`BV1ep4y1Q7dy`，风华秋实官方频道，2048x1080；`BV1os411476f`，Sunflower 鹿晗转存。
- 取舍：YouTube LuHan Studio 源画面干净、音视频完整；B站官方源规格略宽但整体差距不影响竖屏填充。最终选 YouTube LuHan Studio。
- 本地文件：`raw/p2_moushi.mp4` → `clips/vert_moushi.mp4`。

## 第 1 名：《微白城市》

- YouTube 候选：`G6zaUvf7YWk`，LuHan Studio，Official Music Video，1080p25；`MYVIlFVnRQE`，风华秋实 RF ENTERTAINMENT。
- B站候选：`BV1ei4y147ep`，风华秋实官方频道，1080p25；`BV1Zs41187r3`，Sunflower 鹿晗转存。
- 取舍：YouTube LuHan Studio 官方源清晰度、下载稳定性和音频完整性都满足要求；片尾 Rock Forward 标识不进入展示核心段。最终选 YouTube LuHan Studio。
- 本地文件：`raw/p1_weibai.mp4` → `clips/vert_weibai.mp4`。

## 竖屏处理

所有素材使用 `tools/video/vfill.sh` 做 1080x1920 竖屏填充。裁切策略为保守中心 `1280:900`，尽量保留原 MV / 现场构图，同时裁掉部分上下边缘字幕或片尾信息。
