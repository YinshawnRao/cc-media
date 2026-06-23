# 任贤齐最被低估的5首歌 - Sources

双平台检查：每首均查 YouTube + B站。YouTube flat search 可返回候选元数据，但当前 `sandbox/www.youtube.com_cookies.txt` 在单视频提取/下载阶段被 YouTube 判定 `Sign in to confirm you’re not a bot`，因此本轮实际素材采用 B站可下载候选。

## 05.《爱伤了》

- YouTube: `cbKC-Fg-zL8` | 任賢齊 - 愛傷了 ft. 金池 | T Yensheng | 3:37 | 非官方上传候选
- YouTube: `fH-4Io_U6JE` | Ai Shang Le | RICHIE JEN 任賢齊 | 3:40 | 频道音频候选
- B站: `BV1uK411C7oD` | 1440x1080 | stereo | 动态 MV，底部中英歌词
- 选择：B站 `BV1uK411C7oD`。用全宽横带 crop `1440:640:0:45` 去掉歌词，保留 4:3 MV 主体。该首为用户确认可接受窗口，最终未重切。

## 04.《约定蓝天》

- YouTube: `VGpfiMpocRU` | Yue Ding Lan Tian | RICHIE JEN 任賢齊 | 5:09 | 频道音频候选
- YouTube: `R-0_aehkOtY` | 逐日英雄片尾曲 | BichThuy8856 | 3:34 | 非官方视频候选
- B站: `BV19KS7YiEP3` | 480x320 | stereo | 动态 MV，低清，有顶部水印和底部歌词
- 选择：B站 `BV19KS7YiEP3`。老 MV 画质低但动态画面可用，用全宽横带 crop `480:125:0:88` 避开水印/歌词。按反馈重切到源约 `262.0s` 的人声段，最终展示 `12.0s`，让人声在配音快结束时进入。

## 03.《心情车站》

- YouTube: `zlMfsqTImys` | Official Music Video | 滾石唱片 ROCK RECORDS | 5:43
- B站: `BV1U54y1M74V` | 1920x1080 | stereo | 官方原版 MV 标题候选，动态画面，顶部水印和底部歌词
- B站: `BV1pF4cz4ELE` | 4K 修复候选
- 选择：B站 `BV1U54y1M74V`。码率和动态画面质量够好，用全宽横带 crop `1920:760:0:90` 避开污染带。该首为用户确认可接受窗口，最终未重切。

## 02.《别哭》

- YouTube: `J-K6MWxsCs8` | 別哭 (我想愛的你) | RICHIE JEN 任賢齊 | 4:02
- B站: `BV1Aw4m1e79C` | 1920x1080 | stereo | Hi-Res 静态唱片封面/音乐背景
- B站: `BV1KV4y1G7df` | 4:02 | 单曲静态候选
- 选择：B站 `BV1Aw4m1e79C`。未找到可下载动态 MV 单曲源；用高音质静态源，画面由统一设计层承接。最终用 crop `1500:900:180:90` 去掉原始右上角平台标识和底部细字。按反馈再次重切到源约 `185.0s` 的人声段，最终展示 `36.0s`；Whisper 校验可转出 `别哭 我想爱的你`、`爱你 爱我之后` 等连续歌词。

## 01.《安静的人》

- YouTube: `sHMbjKOBBDI` | 安靜的人 | RICHIE JEN 任賢齊 | 5:17
- B站: `BV13SS7YTEXS` | 720x480 | stereo | 动态老 MV，有顶部水印和底部歌词
- B站: `BV1eZ4y1p78C` | 任贤齐经典 MV 精选大合集 | 合集兜底
- B站: `BV1Ny411h7XC` | 任贤齐专辑《爱像太平洋》完整音频 | 交叉确认用，不作为最终画面源
- 选择：B站 `BV13SS7YTEXS`。单曲动态源可下载，用全宽横带 crop `720:245:0:75` 优先去掉水印/歌词。按反馈再次重切到源约 `211.9s` 后的更长人声段，最终展示 `62.0s`。
