#!/usr/bin/env python3
"""Single source of truth for 陈慧琳最被低估的5首歌.

Countdown order is 5 -> 1, while preserving the user's ranking:
  5 陪我失眠
  4 触不到的恋人
  3 香薰恋爱治疗
  2 温柔眼泪
  1 放不开手
"""

LEAD = 0.35
DIG = 1.5
PREROLL = 2.5
BED = 0.14
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.2
OUTRO_TAIL = 2.6
DIGEST_O = 1.0

ARTIST = "陈慧琳"

FORBIDDEN = [
    "YouTube", "B站", "哔哩", "bilibili", "BV", "http", "www",
    "sandbox", "raw/", "cookies", "56.com", "素材", "路径",
]

SONGS = [
    dict(
        key="p5_peiwo", no="05", plain="陪我失眠", title="《陪我失眠》",
        album="爱情来了", tag="夜色里的陪伴感", emo="夜色",
        show=30.0, chorus=160.0, mgain=1.02,
        video="raw/bili_peiwo_repair.mp4", audio_src="raw/bili_peiwo_repair.mp4",
        crop="1920:900:0:0",
        src_label="B站 1080P 修复 MV · 同源音画",
    ),
    dict(
        key="p4_chubudao", no="04", plain="触不到的恋人", title="《触不到的恋人》",
        album="爱情来了", tag="若即若离的电影感", emo="距离",
        show=29.0, chorus=140.0, mgain=1.03,
        video="raw/bili_chubudao_official.mp4", audio_src="raw/bili_chubudao_official.mp4",
        crop="640:300:0:55",
        src_label="B站环球官方 MV · 同源音画",
    ),
    dict(
        key="p3_xiangxun", no="03", plain="香薰恋爱治疗", title="《香薰恋爱治疗》",
        album="花花宇宙", tag="千禧都市的轻失落", emo="轻盈",
        show=29.0, chorus=87.0, mgain=1.02,
        video="raw/bili_xiangxun_720.mp4", audio_src="raw/bili_xiangxun_720.mp4",
        crop="460:330:620:165",
        src_label="B站 720P 动态 MV · 右侧主体裁切同源音画",
    ),
    dict(
        key="p2_wenrou", no="02", plain="温柔眼泪", title="《温柔眼泪》",
        album="心口不一", tag="克制、柔软、耐听", emo="克制",
        show=29.0, chorus=42.0, mgain=1.05,
        video="raw/bili_wenrou.mp4", audio_src="raw/yt_p06Apzp0TVI.mp4",
        crop="352:135:0:20",
        src_label="B站旧 VCD 动态 MV + YouTube 官方人声音轨",
    ),
    dict(
        key="p1_fangbu", no="01", plain="放不开手", title="《放不开手》",
        album="心口不一", tag="成熟慢歌里的拉扯感", emo="拉扯",
        show=30.0, chorus=62.0, mgain=1.03,
        video="raw/bili_fangbu.mp4", audio_src="raw/bili_fangbu.mp4",
        crop="1920:650:0:210",
        src_label="B站 1080P 动态 MV · 同源音画",
    ),
]


def full_start_local(voice_dur):
    return round(LEAD + voice_dur + 0.25 + DIG, 3)


def seg_dur(voice_dur, show):
    return round(full_start_local(voice_dur) + show, 3)


def audio_window_start(chorus, voice_dur):
    """Source time where the audio window begins.

    The selected lyric/melody window lands about two seconds before the
    full-music showcase, so narration can swell naturally into the song.
    """
    return round(max(0.0, chorus - full_start_local(voice_dur) + 2.0), 3)


def footage_window_start(chorus):
    """Keep same-source footage and audio visually aligned."""
    return round(max(0.0, chorus + 2.0 - PREROLL), 3)
