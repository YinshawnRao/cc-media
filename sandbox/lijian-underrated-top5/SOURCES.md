# 李健最被低估的5首歌 - Sources

## Final ranking and playback order

The user-provided ranking is fixed as:

1. 《异乡人》
2. 《一辈子的十分钟》
3. 《抚仙湖》
4. 《在海上》
5. 《深海之寻》

The rendered video plays back as a countdown: 05 -> 01.

## Source policy

Each song was searched on both YouTube and B站. Final selection prioritized:

- clean picture with no platform watermark, creator watermark, URL, prompt, or path
- usable official or official-like MV/live source
- vertical crop viability
- stereo audio and strong showcase segment
- overall clarity

Cookie files were used only from the repository root.

## Selected sources

| Rank in video | Song | Selected file | Platform/source | Reason |
| --- | --- | --- | --- | --- |
| 05 | 《深海之寻》 | `raw/p5_shenhai_bili_repair.mp4` | B站 `BV1re4y1K7tX` | Higher clarity and frame rate than the YouTube candidate; clean after vertical crop. |
| 04 | 《在海上》 | `raw/p4_zaaishanghai_bili.mp4` | B站 `BV1Vs411i7H6` | Best available official MV-style source found; top/bottom crop removes subtitle/logo area. |
| 03 | 《抚仙湖》 | `raw/p3_fuxianhu.mp4` | YouTube `FdDhIi-VqSU`, 李健LIJIAN_OFFICIAL | Official 1080p upload; clean after crop. |
| 02 | 《一辈子的十分钟》 | `raw/p2_shifenzhong_bili.mp4` | B站 `BV1Ym4y1R7mz` | Official MV source; old 4:3 frame retained with clean center crop. |
| 01 | 《异乡人》 | `raw/p1_yixiangren.mp4` | YouTube `sHAqAOIXPiA`, 李健LIJIAN_OFFICIAL | Official 1080p upload; right-side vertical lyric avoided by crop. |

## Rejected or secondary candidates

- 《深海之寻》 YouTube `gw4rMzOOibc`: downloaded as `raw/p5_shenhai.mp4`; usable, but B站 repair source was sharper.
- 《异乡人》 B站 `BV1Vv4y1e7Hs`: downloaded as `raw/p1_yixiangren_bili_repair.mp4`; rejected because large karaoke subtitles dominate the frame.
- 《一辈子的十分钟》 YouTube lyric/non-official candidates such as `JgeAi0sbvEA`: lower source confidence than B站 official MV.
- 《在海上》 YouTube search did not produce a comparable official clean source during this run.

## QA artifacts

- Raw source sheets: `qa/raw_*_sheet.jpg`
- Final vertical crop sheets: `qa/vert_*_sheet.jpg`
- Final mux contact sheet: `qa/final_contact_sheet.jpg`
- Vocal-segment analysis: `probe/vocal_analysis.json`
- Showcase alignment plan: `probe/showcase_plan.json`
