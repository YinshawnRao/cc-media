# 陈楚生最被低估的5首歌

工作目录：`sandbox/chenchusheng-underrated-top5/`

## Build

```bash
tools/tts/venv/bin/python sandbox/chenchusheng-underrated-top5/build/narrate_segments.py
bash sandbox/chenchusheng-underrated-top5/build/make_clips.sh
cd sandbox/chenchusheng-underrated-top5
python3 build/full_build.py
npx hyperframes lint
npx hyperframes inspect --samples 15
npx hyperframes render --output renders/full_raw.mp4 --sdr
ffmpeg -i renders/full_raw.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest renders/chenchusheng-underrated-top5.mp4
```

## Notes

- 排名按用户给定顺序反向揭晓：5《先这样吧》 -> 1《一个人唱情歌》。
- 旁白全部女声 `zf_xiaoyi`。
- 每首都已做 YouTube + B站候选搜索；初选记录见 `SOURCES.md`。
- 最终成片必须以后期 mux 的 `renders/chenchusheng-underrated-top5.mp4` 为准。
