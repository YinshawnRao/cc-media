#!/usr/bin/env python3
"""Single source of truth for 徐良最被低估的5首歌."""

LEAD = 0.35
DIG = 1.45
PREROLL = 2.4
BED = 0.13
VOICE_GAIN = 2.05
INTRO_VOICE_START = 0.5
INTRO_GAP = 1.1
OUTRO_TAIL = 2.4
DIGEST_O = 1.0

ARTIST = "徐良"

FORBIDDEN = [
    "薛之谦", "xuezhiqian", "蔡徐坤", "caixukun", "蔡健雅", "caijianya",
    "方大同", "fangdatong", "张韶涵", "angela", "银河少年", "背过手",
    "小孩", "等我回家", "违背的青春",
]

SONGS = [
    dict(
        key="p5_zihuaxiang", no="05", plain="自画像", title="《自画像》",
        era="早期单曲", tag="把镜头转向自己", emo="自省",
        show=24.0, chorus=74.0, mgain=1.06,
        video="raw/p5_zihuaxiang.mp4", audio_src="raw/p5_zihuaxiang.mp4",
        crop="900:560:240:40",
        src_label="YouTube 单曲素材",
    ),
    dict(
        key="p4_yigongli", no="04", plain="一公里的幸福", title="《一公里的幸福》",
        era="官方歌词版", tag="幸福差一点到达", emo="距离",
        show=25.0, chorus=82.0, mgain=1.05,
        video="raw/p4_yigongli.mp4", audio_src="raw/p4_yigongli.mp4",
        crop="1920:900:0:70",
        src_label="官方歌词版 · XuLiangMusic",
    ),
    dict(
        key="p3_huanmie", no="03", plain="幻灭", title="《幻灭》",
        era="官方 MV", tag="清醒以后才开始痛", emo="失落",
        show=29.0, chorus=86.0, mgain=1.04,
        video="raw/p3_huanmie.mp4", audio_src="raw/p3_huanmie.mp4",
        crop="1920:850:0:70",
        src_label="官方 MV · XuLiangMusic",
    ),
    dict(
        key="p2_dianhua", no="02", plain="电话里的秘密", title="《电话里的秘密》",
        era="Official MV", tag="没说出口的那一段", emo="秘密",
        show=29.0, chorus=78.0, mgain=1.05,
        video="raw/p2_dianhua.mp4", audio_src="raw/p2_dianhua.mp4",
        crop="1920:850:0:70",
        src_label="Official MV · XuLiangMusic",
    ),
    dict(
        key="p1_beijing", no="01", plain="北京巷弄", title="《北京巷弄》",
        era="手绘 PV", tag="旧巷子里最有画面的一首", emo="回望",
        show=32.0, chorus=76.0, mgain=1.08,
        video="raw/p1_beijing_bili.mp4", audio_src="raw/p1_beijing_bili.mp4",
        crop="720:404:0:0",
        src_label="B站手绘 PV",
    ),
]


def full_start_local(voice_dur):
    return round(LEAD + voice_dur + 0.25 + DIG, 3)


def seg_dur(voice_dur, show):
    return round(full_start_local(voice_dur) + show, 3)


def audio_window_start(chorus, voice_dur):
    """Make the chosen vocal section arrive just before full-volume showcase."""
    return max(0, round(chorus - full_start_local(voice_dur) + 2.0, 3))


def video_window_start(chorus):
    """Footage begins PREROLL seconds before full music starts."""
    return max(0, round(chorus + 2.0 - PREROLL, 3))
