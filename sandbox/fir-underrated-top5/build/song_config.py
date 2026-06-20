#!/usr/bin/env python3
"""Single source of truth for 飞儿乐队最被低估的5首歌.

Countdown order is 5 -> 1, while preserving the user's ranking:
  5 眷恋
  4 天天夜夜
  3 后乐园
  2 把爱放开
  1 应许之地

All five selected sources are Bilibili 1080p H.264 candidates after YouTube +
Bilibili comparison. They are treated as song-and-picture-synced MV/live sources.
"""

# rhythm constants
LEAD = 0.35
DIG = 1.5
PREROLL = 2.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.2
OUTRO_TAIL = 2.6
DIGEST_O = 1.0

ARTIST = "F.I.R. 飞儿乐团"

FORBIDDEN = [
    "蔡健雅", "Tanya", "多米诺", "遗书", "失乐园", "优先权", "红色高跟鞋",
    "Letting Go", "林忆莲", "周杰伦", "张韶涵", "华晨宇",
]

SONGS = [
    dict(
        key="p5_juanlian", no="05", plain="眷恋", title="《眷恋》",
        album="爱·歌姬", year="2007", tag="克制型伤感遗珠", emo="克制",
        show=26.0, chorus=176.0, mgain=1.04,
        video="raw/bili_juanlian.mp4", audio_src="raw/bili_juanlian.mp4",
        crop="1920:960:0:40",
        src_label="B站 1080P 修复 MV · 同源音画",
    ),
    dict(
        key="p4_tiantiianye", no="04", plain="天天夜夜", title="《天天夜夜》",
        album="飞行部落", year="2006", tag="夜色里的旋律感", emo="柔软",
        show=28.0, chorus=67.9, mgain=1.02,
        video="raw/bili_tiantiianye.mp4", audio_src="raw/bili_tiantiianye.mp4",
        crop="1920:1000:0:40",
        src_label="B站 1080P 修复 MV · 同源音画",
    ),
    dict(
        key="p3_houleyuan", no="03", plain="后乐园", title="《后乐园》",
        album="F.I.R. 飞儿乐团", year="2004", tag="奇幻摇滚入口", emo="奇幻",
        show=29.0, chorus=168.8, mgain=1.03,
        video="raw/bili_houleyuan_restore.mp4", audio_src="raw/bili_houleyuan_restore.mp4",
        crop="1920:850:0:115",
        src_label="B站 1080P 重制 Live/MV · 同源音画",
    ),
    dict(
        key="p2_baaifangkai", no="02", plain="把爱放开", title="《把爱放开》",
        album="无限", year="2005", tag="慢热的大歌痛感", emo="放手",
        show=29.0, chorus=38.0, mgain=1.04,
        video="raw/bili_baaifangkai.mp4", audio_src="raw/bili_baaifangkai.mp4",
        crop="1920:960:0:55",
        src_label="B站 1080P MV · 同源音画",
    ),
    dict(
        key="p1_yingxuzhidi", no="01", plain="应许之地", title="《应许之地》",
        album="无限", year="2005", tag="史诗感、摇滚感、信念感", emo="信念",
        show=25.0, chorus=294.0, mgain=1.05,
        video="raw/bili_yingxuzhidi.mp4", audio_src="raw/bili_yingxuzhidi.mp4",
        crop="1920:720:0:0",
        src_label="B站 1080P 官方 MV · 同源音画",
    ),
]


def full_start_local(voice_dur):
    return round(LEAD + voice_dur + 0.25 + DIG, 3)


def seg_dur(voice_dur, show):
    return round(full_start_local(voice_dur) + show, 3)


def audio_window_start(chorus, voice_dur):
    """Source time where the audio window begins so the chorus vocal onset lands
    about 2s before the full-music showcase.
    """
    return round(chorus - full_start_local(voice_dur) + 2.0, 3)


def footage_window_start(chorus):
    """For same-source video/audio, keep footage synced with audio.

    At segment local time full_start - PREROLL, the source video should be at
    chorus + 2s - PREROLL. With PREROLL=2.5 this starts 0.5s before chorus.
    """
    return round(chorus + 2.0 - PREROLL, 3)
