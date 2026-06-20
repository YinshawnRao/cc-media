#!/usr/bin/env python3
"""Single source of truth for 薛之谦最被低估的5首歌."""

LEAD = 0.35
DIG = 1.5
PREROLL = 2.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.15
OUTRO_TAIL = 2.6
DIGEST_O = 1.0

ARTIST = "薛之谦"

FORBIDDEN = [
    "蔡健雅", "caijianya", "方大同", "fangdatong", "张韶涵", "angela",
    "遗书", "失乐园", "优先权", "多米诺", "Take Me", "Orange Moon",
]

SONGS = [
    dict(
        key="p5_yinhe", no="05", plain="银河少年", title="《银河少年》",
        album="单曲", year="2023", tag="宇宙感和少年气", emo="少年",
        show=28.0, chorus=80.0, mgain=1.04,
        video="raw/yinhe_yt.mp4", audio_src="raw/yinhe_yt.mp4",
        crop="1920:780:0:100",
        src_label="官方动态歌词版 · 腾讯音乐",
    ),
    dict(
        key="p4_beiguoshou", no="04", plain="背过手", title="《背过手》",
        album="渡", year="2017", tag="把痛背过去", emo="冷感",
        show=28.0, chorus=160.0, mgain=1.02,
        video="raw/beiguoshou_yt.mp4", audio_src="raw/beiguoshou_yt.mp4",
        crop="1920:820:0:130",
        src_label="官方动态歌词版 · 腾讯音乐",
    ),
    dict(
        key="p3_xiaohai", no="03", plain="小孩", title="《小孩》",
        album="初学者", year="2016", tag="脆弱和自尊", emo="脆弱",
        show=30.0, chorus=175.0, mgain=1.02,
        video="raw/xiaohai_yt.mp4", audio_src="raw/xiaohai_yt.mp4",
        crop="1920:960:0:60",
        src_label="官方 MV · 薛之谦频道",
    ),
    dict(
        key="p2_deng", no="02", plain="等我回家", title="《等我回家》",
        album="意外", year="2013", tag="疲惫后的归属感", emo="归属",
        show=30.0, chorus=240.0, mgain=1.05,
        video="raw/deng_yt.mp4", audio_src="raw/deng_yt.mp4",
        crop="1920:810:0:160",
        src_label="官方动态歌词版 · 腾讯音乐",
    ),
    dict(
        key="p1_weibei", no="01", plain="违背的青春", title="《违背的青春》",
        album="怪咖", year="2018", tag="回头看见青春", emo="回望",
        show=32.0, chorus=250.0, mgain=1.35,
        video="raw/weibei_yt.mp4", audio_src="raw/weibei_yt.mp4",
        crop="1920:900:0:40",
        src_label="官方 MV · 薛之谦频道",
    ),
]


def full_start_local(voice_dur):
    return round(LEAD + voice_dur + 0.25 + DIG, 3)


def seg_dur(voice_dur, show):
    return round(full_start_local(voice_dur) + show, 3)


def audio_window_start(chorus, voice_dur):
    """Make vocal onset land about 2s before the full-volume showcase."""
    return round(chorus - full_start_local(voice_dur) + 2.0, 3)


def video_window_start(chorus):
    """Footage begins PREROLL seconds before full music starts."""
    return round(chorus + 2.0 - PREROLL, 3)
