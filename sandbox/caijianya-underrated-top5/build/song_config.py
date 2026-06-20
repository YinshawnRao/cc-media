#!/usr/bin/env python3
"""Single source of truth for 蔡健雅最被低估的5首歌 — timing constants + per-song config.
Imported by prep_footage.py (cuts footage + audio windows) and full_build.py (audio segs + HTML).

Design: countdown 5->1, female VO. Per song: dark REVEAL card during narration ->
footage (clean Tanya closeup / montage) revealed at the music swell for the showcase.
Footage only spans the showcase (PREROLL + show), so each song needs ~30s footage, not ~50s.

Sourcing (all HD, all clean Tanya, diverse years/looks):
  #5 遗书      — 遗书官方MV(2018) 雨夜特写, 连续窗 153-180 (歌画同源, 对口型)
  #4 失乐园    — 解耦: 出走MV(2021)特写蒙太奇 + 失乐园录音室音频(陌生人2003)
  #3 优先权    — 解耦: 善良的我们MV(2024)夜城特写蒙太奇 + 优先权录音室音频(双栖动物2005)
  #2 谁        — 谁 DEPART to RETURN Legacy台北(2022) 木吉他弹唱特写, 连续窗 (歌画同源)
  #1 多米诺    — 解耦: 说到爱MV(2011,同专辑)特写蒙太奇 + 多米诺录音室音频(说到爱2011)
"""

# rhythm constants
LEAD = 0.35      # silence before narration in each segment
DIG = 1.5        # digest/swell ramp after narration
PREROLL = 2.5    # footage fades in this long before the full-music showcase
BED = 0.15       # ducked music-bed level under narration
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.2
OUTRO_TAIL = 2.6
DIGEST_O = 1.0   # outro 升华 -> fixed CTA digest beat

ARTIST = "蔡健雅"

# leak guard: forbidden leftover tokens from ported templates
FORBIDDEN = [
    "林忆莲", "linyilian", "周杰伦", "zhoujielun", "太阳系", "taiyangxi", "理由", "liyou",
    "我坐在这里", "wozuo", "飞的理由", "feide", "没有发生", "meiyou", "晴天", "qingtian",
    "稻香", "daoxiang", "蒲公英", "Sandy", "至少还有你", "铿锵玫瑰", "野花",
]

# countdown reveal order 5 -> 1
SONGS = [
    dict(
        key="p5_yishu", no="05", plain="遗书", title="《遗书》", album="我要给世界最悠长的湿吻",
        year="2018", tag="向内的自我清算", emo="清算",
        mode="cont", show=25.0, chorus=153.5, mgain=1.08,
        video="raw/yishu_mv.webm", audio_src="raw/yishu_mv.webm",
        crop="1920:1006:0:40",
        window=(153.0, 153.0 + 2.5 + 25.0 + 0.6),  # footage src window [start, end]
        src_label="官方 MV · 2018",
    ),
    dict(
        key="p4_shileyuan", no="04", plain="失乐园", title="《失乐园》", album="陌生人",
        year="2003", tag="最锋利的摇滚 B 面", emo="锋利",
        mode="decouple", show=22.0, chorus=175.2, mgain=1.00,
        video="raw/chuzou_mv.webm", audio_src="raw/shileyuan_audio.wav",
        crop="1920:1040:0:20",
        montage=[(27.0, 12.0), (95.0, 13.5)],  # (src_ss, dur) Tanya closeups from 出走MV (avoid male char @40 & @110)
        src_label="影像：《出走》MV · 音源：录音室",
    ),
    dict(
        key="p3_youxianquan", no="03", plain="优先权", title="《优先权》", album="双栖动物",
        year="2005", tag="都市里的优先权焦虑", emo="敏感",
        mode="decouple", show=25.0, chorus=187.3, mgain=1.02,
        video="raw/langman_legacy.mp4", audio_src="raw/youxianquan_audio.wav",
        crop="1200:880:380:120",  # 单主体居中→中心裁切放大；y偏120彻底裁掉左上UP水印(y40-100)
        montage=[(114.0, 29.0)],  # 让浪漫做主 DEPART to RETURN Legacy 2022(白裙弹唱,与谁的米色场区分)
        src_label="影像：DEPART to RETURN Live 2022 · 音源：录音室",
    ),
    dict(
        key="p2_shui", no="02", plain="谁", title="《谁》", album="若你碰到他",
        year="2009", tag="不喊出口的追问", emo="追问",
        mode="cont", show=28.0, chorus=92.5, mgain=1.05,
        video="raw/shui_legacy.mp4", audio_src="raw/shui_legacy.mp4",
        crop="1920:1040:0:20",
        window=(92.0, 92.0 + 2.5 + 28.0 + 0.6),
        src_label="DEPART to RETURN · Legacy 台北 2022",
    ),
    dict(
        key="p1_domino", no="01", plain="多米诺", title="《多米诺》", album="说到爱",
        year="2011", tag="藏在专辑后半段的宝藏", emo="宿命",
        mode="decouple", show=26.0, chorus=178.5, mgain=1.04,
        video="raw/langman_legacy.mp4", audio_src="raw/domino_audio.wav",
        crop="1200:880:380:120",  # 让浪漫做主 另一窗(305-),中心裁切放大 + 去左上UP水印
        montage=[(304.0, 29.0)],  # 说到爱MV密集穿插学生/男角无法连续→改 2022 Live 干净连续特写(与优先权不同窗,谁隔开)
        src_label="影像：DEPART to RETURN Live 2022 · 音源：录音室",
    ),
]


def full_start_local(voice_dur):
    return round(LEAD + voice_dur + 0.25 + DIG, 3)


def seg_dur(voice_dur, show):
    return round(full_start_local(voice_dur) + show, 3)


def audio_window_start(chorus, voice_dur):
    """src time where the audio window begins so the chorus vocal onset lands
    ~2s before the full-music swell."""
    return round(chorus - full_start_local(voice_dur) + 2.0, 3)
