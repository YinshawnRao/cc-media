# Sources — 陈慧琳最被低估的5首歌

执行规则：每首都查 YouTube + B站。最终选择按清晰度、画面干净度、立体声、现场/官方质量综合判断。YouTube 官方源里有三首为静态封面音频，不适合做画面；动态 MV 以 B站源为主，并通过全宽横带裁切避开水印、台标和歌词污染。

Cookie 文件：根目录 `all_cookies.txt` / `www.youtube.com_cookies.txt` / `www.bilibili.com_cookies.txt`，没有在 `sandbox/` 下复制 cookie。

## 5. 《陪我失眠》

- YouTube: `Rrq81PRoy6Y` | Kelly Chen 官方频道 | 640×480 动态 MV，底部原片歌词。
- YouTube: `hxgzEqIuxj8` | Kelly Chen 官方频道 | 官方音频/候选。
- B站: `BV1SG4y1M7Wx` | 1080P 修复 MV | 1920×1080，动态画面，底部原片歌词。
- B站: `BV12a4y1j7jN` | 环球音乐中国 | 官方候选。
- 选择：`raw/bili_peiwo_repair.mp4`。理由：比 YouTube 官方动态 MV 清晰，未见额外平台/UP 水印；底部歌词可通过 `1920:900:0:0` 裁切规避。展示窗口约 `160s`。

## 4. 《触不到的恋人》

- YouTube: `vrpi0mCbUHc` | Kelly Chen 官方频道 | 640×480 动态 MV，底部原片歌词。
- YouTube: `Mszkn1QjDlw` | Kelly Chen 官方频道 | 官方候选。
- B站: `BV1AX4y1o7nb` | 修复版 MV | 下载到的 DASH 流异常过小，不可用。
- B站: `BV1WV411m79c` | 环球音乐中国 | 640×480 官方动态 MV。
- 选择：`raw/bili_chubudao_official.mp4`。理由：官方动态 MV，码率略优于 YouTube；底部歌词用 `640:300:0:55` 裁掉。展示窗口约 `140s`。

## 3. 《香薰恋爱治疗》

brief 写作《香薰治疗恋爱》，官方源标题为《香薰恋爱治疗》，成片采用官方标题。

- YouTube: `0flh-yK6WHA` | Kelly Chen 官方频道 | 1080×1080 静态封面音频，不适合做画面。
- YouTube: `YeIcL2eRUCE` | 用户动态候选。
- B站: `BV1TN411T77G` | 动态 MV | 1080×720，MTV 台标 + 原片歌词。
- B站: `BV1yq4y1u7Zq` | 滚动歌词候选，不适合做画面主源。
- 选择：`raw/bili_xiangxun_720.mp4`。理由：YouTube 官方为静态封面，B站动态 MV 画面更可用；原全宽横带虽能裁掉顶部 MTV 台标和底部歌词，但局部会露出淡水印，最终改用 `460:330:620:165` 右侧主体裁切避开水印区。展示窗口约 `87s`。

## 2. 《温柔眼泪》

- YouTube: `p06Apzp0TVI` | Kelly Chen 官方频道 | 796×1080 静态封面音频，不适合做画面。
- YouTube: `501QJWXeN90` | 用户动态 MV | 352×288，但全程有 `56.com` 台标。
- B站: `BV1Hs4y1W7DS` | 旧 VCD 动态 MV | 352×240，无额外平台台标，原片字幕可裁。
- B站: `BV1g64y1v7ej` / `BV12P411y7hK` | MV 合集候选。
- 选择：画面用 `raw/bili_wenrou.mp4`，音频改用 YouTube 官方 `raw/yt_p06Apzp0TVI.mp4`。理由：B站旧 VCD 动态画面较干净，但原音轨偏卡拉 OK/伴奏感；按反馈改用官方人声音轨，并把展示窗口提前到约 `42s` 的歌手/歌词段。画面用 `352:135:0:20` 裁掉字幕区。

## 1. 《放不开手》

- YouTube: `WWGErihd0u4` | Kelly Chen 官方频道 | 796×1080 静态封面音频，不适合做画面。
- YouTube: `llNLeEi3zSc` | 用户动态 MV | 352×262，右上台标，清晰度低。
- B站: `BV1gX4y167vG` | 动态 MV | 1920×1080，画面清晰，但带 MTV/电视台台标和底部歌词。
- B站: `BV1Te4y1W7HZ` | 高清合集候选 | 格式探测到 1450×928，下载过程长时间无进度，未纳入主源。
- 选择：`raw/bili_fangbu.mp4`。理由：YouTube 官方为静态封面，YouTube 动态候选清晰度和污染都不优；B站源清晰度最高，通过 `1920:650:0:210` 中间横带裁切避开上下台标/歌词污染。展示窗口约 `62s`。

## 当前 QA 素材

- 源候选抽帧：`qa/*_sheet.jpg`
- 时间窗口抽帧：`qa/timing_*.jpg`
- 裁切验证：`qa/crop_*.jpg`
- 最终成片：`hf/renders/chenhuilin-underrated-top5.mp4`
- 最终 QA：1080×1920 H.264, AAC stereo, 279.800s；`silencedetect=n=-35dB:d=1` 无静音段；`volumedetect` mean `-17.2 dB`, max `-0.4 dB`。
