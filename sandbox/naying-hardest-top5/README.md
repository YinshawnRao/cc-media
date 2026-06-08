# 那英最难的5首歌

Working sandbox for a vertical countdown video.

Target:

- Title: 那英最难的5首歌
- Voice: female `zf_xiaoyi`
- Order: 5 -> 1 during the countdown
- Opening: no full ranking reveal
- Ending: ranking summary allowed
- Final render must be muxed with pre-mixed `master.wav`

Expected final artifact:

- `renders/naying-hardest-top5.mp4`

Postprocess:

- `build/make_outro_card.py` generates `assets/outro_card.png`.
- The final MP4 overlays that clean card for the outro so the closing ranking has no burned karaoke lyrics behind it.
