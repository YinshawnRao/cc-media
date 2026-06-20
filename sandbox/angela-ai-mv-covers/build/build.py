#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATERMARK_TEXT = "AI训练，仅供娱乐"
FINAL_DATE_ENV = "ANGELA_MV_FINAL_DATE"


@dataclass(frozen=True)
class Song:
    key: str
    title: str
    video: str
    song_audio: str
    intro_voice: str
    output: str
    crop: tuple[int, int, int, int] | None = None
    audio_gain: float = 1.0


SONGS = [
    Song(
        key="guangnianzhiwai",
        title="光年之外",
        video="raw/guangnianzhiwai.mp4",
        song_audio="audio/guangnianzhiwai_e200_final.wav",
        intro_voice="voice/guangnianzhiwai_intro.wav",
        output="final/光年之外_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="tiankongmeiyoujixian",
        title="天空没有极限",
        video="raw/tiankongmeiyoujixian.mp4",
        song_audio="audio/tiankongmeiyoujixian_e200_final.wav",
        intro_voice="voice/tiankongmeiyoujixian_intro.wav",
        output="final/天空没有极限_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="yuai",
        title="雨爱",
        video="raw/yuai.mp4",
        song_audio="audio/yuai_e200_final.wav",
        intro_voice="voice/yuai_intro.wav",
        output="final/雨爱_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="lixiangqingren",
        title="理想情人",
        video="raw/lixiangqingren.mp4",
        song_audio="audio/lixiangqingren_e200_final.wav",
        intro_voice="voice/lixiangqingren_intro.wav",
        output="final/理想情人_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="xinqiang",
        title="心墙",
        video="raw/xinqiang.mp4",
        song_audio="audio/xinqiang_e200_jijin.wav",
        intro_voice="voice/xinqiang_intro.wav",
        output="final/心墙_AI训练张韶涵音色MV.mp4",
        crop=(3840, 1920, 0, 0),
    ),
    Song(
        key="turanxiangqini",
        title="突然想起你",
        video="raw/turanxiangqini.mp4",
        song_audio="audio/turanxiangqini_e200_jijin.wav",
        intro_voice="voice/turanxiangqini_intro.wav",
        output="final/突然想起你_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="aiqingxunxi",
        title="爱情讯息",
        video="raw/aiqingxunxi.mp4",
        song_audio="audio/aiqingxunxi_jijin.wav",
        intro_voice="voice/aiqingxunxi_intro.wav",
        output="final/爱情讯息_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="caihong",
        title="彩虹",
        video="raw/caihong.mp4",
        song_audio="audio/caihong_jijin.wav",
        intro_voice="voice/caihong_intro.wav",
        output="final/彩虹_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="kubuchulai",
        title="哭不出来",
        video="raw/kubuchulai.mp4",
        song_audio="audio/kubuchulai_jijin.wav",
        intro_voice="voice/kubuchulai_intro.wav",
        output="final/哭不出来_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="daoshu",
        title="倒数",
        video="raw/daoshu.mp4",
        song_audio="audio/daoshu_jijin.wav",
        intro_voice="voice/daoshu_intro.wav",
        output="final/倒数_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="yigerenshenghuo",
        title="一个人生活",
        video="raw/yigerenshenghuo.mp4",
        song_audio="audio/yigerenshenghuo_jijin.wav",
        intro_voice="voice/yigerenshenghuo_intro.wav",
        output="final/一个人生活_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="manleng",
        title="慢冷",
        video="raw/manleng_aligned.mp4",
        song_audio="audio/manleng_jijin.wav",
        intro_voice="voice/manleng_intro.wav",
        output="final/慢冷_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="geqian",
        title="搁浅",
        video="raw/geqian.mp4",
        song_audio="audio/geqian_jijin.wav",
        intro_voice="voice/geqian_intro.wav",
        output="final/搁浅_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="xinzhongderiyue",
        title="心中的日月",
        video="raw/xinzhongderiyue.mp4",
        song_audio="audio/xinzhongderiyue_jijin.wav",
        intro_voice="voice/xinzhongderiyue_intro.wav",
        output="final/心中的日月_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="zhixiangaini",
        title="只想爱你",
        video="raw/zhixiangaini.mp4",
        song_audio="audio/zhixiangaini_classic.wav",
        intro_voice="voice/zhixiangaini_intro.wav",
        output="final/只想爱你_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="xiaozhenguniang",
        title="小镇姑娘",
        video="raw/xiaozhenguniang.mp4",
        song_audio="audio/xiaozhenguniang_classic.wav",
        intro_voice="voice/xiaozhenguniang_intro.wav",
        output="final/小镇姑娘_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="ezuoju",
        title="恶作剧",
        video="raw/ezuoju.mp4",
        song_audio="audio/ezuoju_classic.wav",
        intro_voice="voice/ezuoju_intro.wav",
        output="final/恶作剧_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="xiangchangjiuchang",
        title="想唱就唱",
        video="raw/xiangchangjiuchang.mp4",
        song_audio="audio/xiangchangjiuchang_classic.wav",
        intro_voice="voice/xiangchangjiuchang_intro.wav",
        output="final/想唱就唱_AI训练张韶涵音色MV.mp4",
        crop=(1440, 820, 0, 260),
    ),
    Song(
        key="manmanxihuanni",
        title="慢慢喜欢你",
        video="raw/manmanxihuanni.mp4",
        song_audio="audio/manmanxihuanni_classic.wav",
        intro_voice="voice/manmanxihuanni_intro.wav",
        output="final/慢慢喜欢你_AI训练张韶涵音色MV.mp4",
        audio_gain=1.22,
    ),
    Song(
        key="wohuanjide",
        title="我还记得",
        video="raw/wohuanjide.mp4",
        song_audio="audio/wohuanjide_classic.wav",
        intro_voice="voice/wohuanjide_intro.wav",
        output="final/我还记得_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="bainianguji",
        title="百年孤寂",
        video="raw/bainianguji.mp4",
        song_audio="audio/bainianguji_classic.wav",
        intro_voice="voice/bainianguji_intro.wav",
        output="final/百年孤寂_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="namejiaao",
        title="那么骄傲",
        video="raw/namejiaao.mp4",
        song_audio="audio/namejiaao_classic.wav",
        intro_voice="voice/namejiaao_intro.wav",
        output="final/那么骄傲_AI训练张韶涵音色MV.mp4",
        crop=(1920, 880, 0, 0),
        audio_gain=1.12,
    ),
    Song(
        key="yujizhong",
        title="雨季中",
        video="raw/yujizhong.mp4",
        song_audio="audio/yujizhong_classic.wav",
        intro_voice="voice/yujizhong_intro.wav",
        output="final/雨季中_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="douquan",
        title="兜圈",
        video="raw/douquan.mp4",
        song_audio="audio/douquan_20260608.wav",
        intro_voice="voice/douquan_intro.wav",
        output="final/兜圈_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="huijia",
        title="回家",
        video="raw/huijia_youtube_candidate.mp4",
        song_audio="audio/huijia_20260608.wav",
        intro_voice="voice/huijia_intro.wav",
        output="final/回家_AI训练张韶涵音色MV.mp4",
        audio_gain=1.08,
    ),
    Song(
        key="wozhidao",
        title="我知道",
        video="raw/wozhidao_aligned.mp4",
        song_audio="audio/wozhidao_20260608.wav",
        intro_voice="voice/wozhidao_intro.wav",
        output="final/我知道_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="yigerenxiangzheyigeren",
        title="一个人想着一个人",
        video="raw/yigerenxiangzheyigeren_youtube_candidate.mp4",
        song_audio="audio/yigerenxiangzheyigeren_20260605.wav",
        intro_voice="voice/yigerenxiangzheyigeren_intro.wav",
        output="final/一个人想着一个人_AI训练张韶涵音色MV.mp4",
        audio_gain=1.22,
    ),
    Song(
        key="gudanxinshi",
        title="孤单心事",
        video="raw/gudanxinshi.mp4",
        song_audio="audio/gudanxinshi_20260605.wav",
        intro_voice="voice/gudanxinshi_intro.wav",
        output="final/孤单心事_AI训练张韶涵音色MV.mp4",
        crop=(1920, 820, 0, 120),
    ),
    Song(
        key="woaininameyiduo",
        title="我爱你那么多",
        video="raw/woaininameyiduo.mp4",
        song_audio="audio/woaininameyiduo_20260605.wav",
        intro_voice="voice/woaininameyiduo_intro.wav",
        output="final/我爱你那么多_AI训练张韶涵音色MV.mp4",
        audio_gain=1.25,
    ),
    Song(
        key="cankuyueguang",
        title="残酷月光",
        video="raw/cankuyueguang.mp4",
        song_audio="audio/cankuyueguang_20260605.wav",
        intro_voice="voice/cankuyueguang_intro.wav",
        output="final/残酷月光_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="langfei",
        title="浪费",
        video="raw/langfei.mp4",
        song_audio="audio/langfei_20260605.wav",
        intro_voice="voice/langfei_intro.wav",
        output="final/浪费_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="shuoaini",
        title="说爱你",
        video="raw/shuoaini.mp4",
        song_audio="audio/shuoaini_20260605.wav",
        intro_voice="voice/shuoaini_intro.wav",
        output="final/说爱你_AI训练张韶涵音色MV.mp4",
    ),
    Song(
        key="feiniaohechan",
        title="飞鸟和蝉",
        video="raw/feiniaohechan_youtube_candidate.mp4",
        song_audio="audio/feiniaohechan_20260605.wav",
        intro_voice="voice/feiniaohechan_intro.wav",
        output="final/飞鸟和蝉_AI训练张韶涵音色MV.mp4",
        crop=(1920, 760, 0, 280),
        audio_gain=1.10,
    ),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def probe_json(path: Path, entries: str, streams: bool = False) -> dict:
    cmd = ["ffprobe", "-v", "error"]
    if streams:
        cmd += ["-select_streams", "v:0"]
    cmd += ["-show_entries", entries, "-of", "json", str(path)]
    out = subprocess.check_output(cmd, cwd=ROOT, text=True)
    return json.loads(out)


def duration(path: Path) -> float:
    info = probe_json(path, "format=duration")
    return float(info["format"]["duration"])


def video_size(path: Path) -> tuple[int, int]:
    info = probe_json(path, "stream=width,height", streams=True)
    stream = info["streams"][0]
    return int(stream["width"]), int(stream["height"])


def even(value: float) -> int:
    rounded = int(round(value))
    return rounded if rounded % 2 == 0 else rounded - 1


def output_size(width: int, height: int) -> tuple[int, int]:
    if width <= 1920:
        return width, height
    return 1920, even(height * 1920 / width)


def compile_watermark_renderer() -> Path:
    source = ROOT / "build" / "watermark.swift"
    binary = ROOT / "build" / "watermark_renderer"
    if binary.exists() and binary.stat().st_mtime >= source.stat().st_mtime:
        return binary

    cache = ROOT / "build" / ".clang-module-cache"
    cache.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CLANG_MODULE_CACHE_PATH"] = str(cache)
    cmd = [
        "swiftc",
        "-target",
        "arm64-apple-macosx15.0",
        str(source),
        "-o",
        str(binary),
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)
    return binary


def make_watermark(renderer: Path, song: Song, out_w: int) -> Path:
    font_size = max(18, round(out_w / 60))
    output = ROOT / "build" / f"{song.key}_watermark.png"
    run([str(renderer), str(output), WATERMARK_TEXT, str(font_size)])
    return output


def final_output_path(song: Song) -> Path:
    output = Path(song.output)
    if not output.is_absolute() and len(output.parts) == 2 and output.parts[0] == "final":
        final_date = os.environ.get(FINAL_DATE_ENV) or date.today().isoformat()
        return ROOT / "final" / final_date / output.name
    return ROOT / output


def speech_window(path: Path) -> tuple[float, float]:
    info = duration(path)
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "silencedetect=n=-35dB:d=0.15",
            "-f",
            "null",
            "-",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    segments: list[tuple[float, float]] = []
    active_start: float | None = None
    for line in proc.stderr.splitlines():
        start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if start_match:
            active_start = float(start_match.group(1))
            continue
        end_match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if end_match:
            segments.append((active_start or 0.0, float(end_match.group(1))))
            active_start = None

    start = 0.0
    end = info
    if segments and segments[0][0] <= 0.05:
        start = min(segments[0][1], info)
    if segments and abs(segments[-1][1] - info) <= 0.08:
        end = max(start + 0.10, segments[-1][0])
    return start, end


def trim_intro_voice(song: Song) -> Path:
    source = ROOT / song.intro_voice
    output = ROOT / "build" / f"{song.key}_intro_trimmed.wav"
    start, end = speech_window(source)
    trimmed_duration = end - start
    fade_out_start = max(0.0, trimmed_duration - 0.04)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            song.intro_voice,
            "-af",
            (
                f"atrim=start={start:.3f}:end={end:.3f},"
                "asetpts=N/SR/TB,"
                "afade=t=in:st=0:d=0.03,"
                f"afade=t=out:st={fade_out_start:.3f}:d=0.04"
            ),
            str(output.relative_to(ROOT)),
        ]
    )
    return output


def filtered_video_size(song: Song) -> tuple[int, int]:
    video_path = ROOT / song.video
    width, height = video_size(video_path)
    if song.crop:
        width, height = song.crop[0], song.crop[1]
    return output_size(width, height)


def ffmpeg_filter(song: Song, voice_path: Path) -> str:
    out_w, out_h = filtered_video_size(song)
    crop_filter = ""
    if song.crop:
        cw, ch, cx, cy = song.crop
        crop_filter = f"crop={cw}:{ch}:{cx}:{cy},"
    inset = max(18, round(out_w / 60))
    voice_delay = 0.15
    duck_end = voice_delay + duration(voice_path) + 0.15
    recover = 0.35
    duck_expr = (
        f"if(lt(t,{duck_end:.3f}),0.25,"
        f"if(lt(t,{duck_end + recover:.3f}),"
        f"0.25+(t-{duck_end:.3f})/{recover:.3f}*0.75,1))"
    )
    video = (
        f"[0:v]{crop_filter}tpad=stop_mode=clone:stop_duration=2,"
        f"scale={out_w}:{out_h}:flags=lanczos,"
        f"format=rgba[base];"
        f"[3:v]format=rgba[wm];"
        f"[base][wm]overlay=x={inset}:y={inset}:eof_action=repeat,"
        f"format=yuv420p[vout]"
    )
    audio = (
        f"[1:a]volume='{song.audio_gain:.4f}*({duck_expr})':eval=frame[song];"
        f"[2:a]adelay={int(voice_delay * 1000)}:all=1,volume=1.15[voice];"
        f"[song][voice]amix=inputs=2:duration=first:dropout_transition=0:"
        f"normalize=0,alimiter=limit=0.95[aout]"
    )
    return f"{video};{audio}"


def main() -> None:
    renderer = compile_watermark_renderer()
    (ROOT / "final").mkdir(exist_ok=True)
    requested = set(sys.argv[1:])
    if requested:
        known = {song.key for song in SONGS}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"Unknown song key(s): {', '.join(unknown)}")
    songs = [song for song in SONGS if not requested or song.key in requested]
    for song in songs:
        output = final_output_path(song)
        output.parent.mkdir(parents=True, exist_ok=True)
        out_w, _ = filtered_video_size(song)
        voice = trim_intro_voice(song)
        watermark = make_watermark(renderer, song, out_w)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                song.video,
                "-i",
                song.song_audio,
                "-i",
                str(voice.relative_to(ROOT)),
                "-loop",
                "1",
                "-i",
                str(watermark.relative_to(ROOT)),
                "-filter_complex",
                ffmpeg_filter(song, voice),
                "-map",
                "[vout]",
                "-map",
                "[aout]",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                "-shortest",
                song.output,
            ]
        )


if __name__ == "__main__":
    main()
