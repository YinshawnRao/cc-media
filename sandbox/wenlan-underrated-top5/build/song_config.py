#!/usr/bin/env python3
"""Single source of truth for 温岚最被低估的5首歌.

Countdown reveal order is 5 -> 1:
  05 爱太急, 04 不吵不闹, 03 动心, 02 爱你的两个我, 01 荒唐.

Most sources are official YouTube MVs from 阿尔发音乐. 《爱太急》 has no official
dynamic MV in the checked candidates, so it uses the official audio plus a
same-album early-era official MV as clean visual fallback.
"""

LEAD = 0.35
DIG = 1.5
PREROLL = 2.5
BED = 0.15
VOICE_GAIN = 2.0
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.15
OUTRO_TAIL = 2.6
DIGEST_O = 1.0

ARTIST = "温岚"

FORBIDDEN = [
    "蔡健雅", "caijianya", "Tanya", "遗书", "失乐园", "优先权", "多米诺", "谁",
    "张韶涵", "林忆莲", "周杰伦", "Sandy", "Noto Serif SC", "Noto Sans SC",
]

SONGS = [
    dict(
        key="p5_aitaiji", no="05", plain="爱太急", title="《爱太急》", album="有点野",
        year="2001", tag="爱得太满，反而失控", emo="后知后觉",
        mode="decouple", show=26.0, chorus=233.9, mgain=1.18,
        video="raw/beidouxing.mp4", audio_src="raw/aitaiji_audio.wav",
        crop="1440:700:0:180",
        montage=[(205.0, 31.0)],
        src_label="音源：官方音轨 · 画面：同专辑官方 MV",
    ),
    dict(
        key="p4_buchaobunao", no="04", plain="不吵不闹", title="《不吵不闹》", album="蓝色雨",
        year="2002", tag="不是爆发，是冷下来", emo="克制",
        mode="cont", show=27.0, chorus=153.0, mgain=1.05,
        video="raw/buchaobunao.mp4", audio_src="raw/buchaobunao.mp4",
        crop="640:300:0:60",
        window=(150.5, 150.5 + 2.5 + 27.0 + 0.8),
        src_label="阿尔发官方 MV",
    ),
    dict(
        key="p3_dongxin", no="03", plain="动心", title="《动心》", album="有点野",
        year="2001", tag="暧昧、试探和心跳", emo="暧昧",
        mode="cont", show=28.0, chorus=225.7, mgain=1.04,
        video="raw/dongxin.mp4", audio_src="raw/dongxin.mp4",
        crop="606:285:0:0",
        window=(223.2, 223.2 + 2.5 + 28.0 + 0.8),
        src_label="阿尔发官方 MV",
    ),
    dict(
        key="p2_lianggewo", no="02", plain="爱你的两个我", title="《爱你的两个我》", album="温式效应",
        year="2004", tag="一个想爱，一个快撑不下去", emo="拉扯",
        mode="cont", show=27.0, chorus=61.2, mgain=1.08,
        video="raw/lianggewo.mp4", audio_src="raw/lianggewo.mp4",
        crop="640:270:0:105",
        window=(58.7, 58.7 + 2.5 + 27.0 + 0.8),
        src_label="阿尔发官方 MV",
    ),
    dict(
        key="p1_huangtang", no="01", plain="荒唐", title="《荒唐》", album="爱回温",
        year="2005", tag="清醒、疼痛、带一点锋利", emo="锋利",
        mode="cont", show=30.0, chorus=199.6, mgain=1.06,
        video="raw/huangtang.mp4", audio_src="raw/huangtang.mp4",
        crop="640:360:0:0",
        window=(197.1, 197.1 + 2.5 + 30.0 + 0.8),
        src_label="阿尔发官方 MV",
    ),
]


def full_start_local(voice_dur):
    return round(LEAD + voice_dur + 0.25 + DIG, 3)


def seg_dur(voice_dur, show):
    return round(full_start_local(voice_dur) + show, 3)


def audio_window_start(chorus, voice_dur):
    """Start music window so vocal hook begins during the swell, before full volume."""
    return round(chorus - full_start_local(voice_dur) + 2.0, 3)
