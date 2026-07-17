#!/usr/bin/env python3
"""多证据主唱候选检测。

旧版只用 HPSS + 200–3000Hz 能量，乐器和观众都可能被误判。新版保留同一 CLI、
``detect()`` 签名和 ``vocal_segments`` 字段，同时增加：

1. stereo mid/side 证据（目标主唱通常比观众更靠混音中央，但不单独下结论）；
2. 本机 Whisper small 的有效歌词密度与 word timestamps；
3. 固定 ASR 幻觉/字幕 credit 过滤；
4. ``lead_segments``、``safe_cut_intervals``、逐段证据和明确降级状态。

默认 ``--mode auto``：本机已有缓存的 Whisper 模型时跑多证据分析；没有则只输出
``evidence_level=candidate``，不得被展示段闸门自动当作主唱真值。不会自动下载模型。

兼容用法：
  tools/tts/venv/bin/python tools/video/vocal_segments.py <audio> [audio2 ...]
  tools/tts/venv/bin/python tools/video/vocal_segments.py clips/vert_*.mp4 \
      -o probe/vocal_analysis.json --language zh
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import librosa
import numpy as np

SR = 22050
WHISPER_SR = 16000
SCHEMA_VERSION = 2

# 三组仓库历史坏/好窗的首轮保守阈值；需持续由真实音频回归校准。
LEXICAL_NEG_CHAR_RATE = 0.25
LEXICAL_NEG_COVERAGE = 0.15
LEXICAL_POS_CHAR_RATE = 0.60
LEXICAL_POS_COVERAGE = 0.40
LEXICAL_MIN_UNITS = 6
LEXICAL_MIN_WORD_PROB = 0.12
LEXICAL_LOW_LOGPROB = -1.60
ASR_GROUP_GAP = 2.5
WORD_MERGE_GAP = 0.65
SAFE_GAP_MIN = 0.85
SAFE_RELEASE = 0.30
SAFE_NEXT_PAD = 0.15
LEAD_CENTER_DB = 4.0
STEREO_MAX_CENTER_DB = 30.0
MIN_ACOUSTIC_OVERLAP = 0.25

_HALLUCINATION_PATTERNS = (
    "字幕by索兰娅",
    "字幕製作人",
    "字幕制作人",
    "zitherharp",
    "amara.org",
    "thankyouforwatching",
    "谢谢观看",
    "感謝觀看",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_stereo(path: Path):
    y, sr = librosa.load(str(path), sr=SR, mono=False)
    if y.ndim == 1:
        channels = 1
        left = right = y.astype(np.float32, copy=False)
    else:
        channels = int(y.shape[0])
        left = y[0].astype(np.float32, copy=False)
        right = y[1].astype(np.float32, copy=False) if channels > 1 else left
    n = min(len(left), len(right))
    left, right = left[:n], right[:n]
    mid = ((left + right) * 0.5).astype(np.float32, copy=False)
    side = ((left - right) * 0.5).astype(np.float32, copy=False)
    return left, right, mid, side, sr, channels


def _center_stats(left, right, mid, side, sr, start=0.0, end=None):
    lo = max(0, int(float(start) * sr))
    hi = len(mid) if end is None else min(len(mid), int(float(end) * sr))
    if hi <= lo:
        return {"center_db": None, "lr_correlation": None, "stereo_informative": False}
    l, r, m, s = left[lo:hi], right[lo:hi], mid[lo:hi], side[lo:hi]
    mid_rms = float(np.sqrt(np.mean(m * m) + 1e-12))
    side_rms = float(np.sqrt(np.mean(s * s) + 1e-12))
    center_db = float(20.0 * np.log10((mid_rms + 1e-12) / (side_rms + 1e-12)))
    if float(np.std(l)) < 1e-8 or float(np.std(r)) < 1e-8:
        corr = None
    else:
        corr = float(np.corrcoef(l, r)[0, 1])
    informative = center_db < STEREO_MAX_CENTER_DB and (corr is None or corr < 0.9995)
    return {
        "center_db": round(center_db, 3),
        "lr_correlation": None if corr is None else round(corr, 4),
        "stereo_informative": bool(informative),
    }


def _segments_from_active(times, active, min_dur, gap_tol):
    segments = []
    in_seg = False
    seg_start = 0.0
    last_active = None
    for idx, is_active in enumerate(active):
        t = float(times[idx])
        if is_active:
            if not in_seg:
                seg_start = t
                in_seg = True
            last_active = t
        elif in_seg and last_active is not None and (t - last_active) > gap_tol:
            if last_active - seg_start >= min_dur:
                segments.append([round(seg_start, 2), round(last_active, 2)])
            in_seg = False
            last_active = None
    if in_seg and last_active is not None and (last_active - seg_start) >= min_dur:
        segments.append([round(seg_start, 2), round(last_active, 2)])
    return segments


def _acoustic_candidates(mid, sr, min_dur, gap_tol, percentile):
    if len(mid) < 2048:
        return [], {"threshold": 0.0, "active_ratio": 0.0}
    harmonic, _ = librosa.effects.hpss(mid, margin=3.0)
    spectrum = np.abs(librosa.stft(harmonic, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    voice_mask = (freqs >= 200) & (freqs <= 3000)
    voice_rms = np.sqrt(np.mean(spectrum[voice_mask, :] ** 2, axis=0))
    times = librosa.frames_to_time(np.arange(len(voice_rms)), sr=sr, hop_length=512)
    frame_step = float(times[1] - times[0]) if len(times) > 1 else 512.0 / sr
    win = max(1, int(round(1.0 / frame_step)))
    smoothed = np.convolve(voice_rms, np.ones(win) / win, mode="same")
    threshold = float(np.percentile(smoothed, percentile)) if len(smoothed) else 0.0
    active = smoothed > threshold
    segments = _segments_from_active(times, active, min_dur, gap_tol)
    return segments, {
        "threshold": round(threshold, 8),
        "active_ratio": round(float(np.mean(active)) if len(active) else 0.0, 4),
    }


def _candidate_result(path, left, right, mid, side, sr, channels,
                      min_dur, gap_tol, percentile):
    duration = len(mid) / sr
    candidates, acoustic = _acoustic_candidates(
        mid, sr, min_dur=min_dur, gap_tol=gap_tol, percentile=percentile)
    stereo = _center_stats(left, right, mid, side, sr)
    stereo["channels"] = channels
    if channels < 2:
        stereo["stereo_informative"] = False
    return {
        "schema_version": SCHEMA_VERSION,
        "name": path.stem,
        "duration": round(duration, 2),
        "source_sha256": _sha256(path),
        "detector": "librosa_band_energy_v2",
        "evidence_level": "candidate",
        "classification": "acoustic_candidate_only",
        # 保留旧字段和语义，供直接 import detect() 的历史调用方渐进迁移。
        "vocal_segments": candidates,
        "candidate_segments": candidates,
        "boundary_segments": [],
        "boundary_evidence": "unavailable",
        "safe_cut_intervals": [],
        "segment_scores": [],
        "capabilities": {
            "acoustic": "available",
            "stereo": "available" if stereo["stereo_informative"] else "uninformative",
            "whisper": "not_run",
        },
        "evidence": {
            "acoustic": {**acoustic, "percentile": percentile},
            "stereo": stereo,
            "warnings": ["频带能量不能区分主唱、乐器和观众；此结果只可用于候选定位"],
        },
    }


def detect(path: Path, min_dur: float = 2.0, gap_tol: float = 1.5,
           percentile: float = 60) -> dict:
    """兼容旧调用的廉价声学候选检测；结果永远只是 ``candidate``。"""
    path = Path(path)
    loaded = _load_stereo(path)
    return _candidate_result(
        path, *loaded, min_dur=min_dur, gap_tol=gap_tol, percentile=percentile)


def _normalized_text(text: str) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]+", "", text.lower())


def _is_hallucination(text: str) -> bool:
    normalized = _normalized_text(text)
    return any(_normalized_text(pattern) in normalized for pattern in _HALLUCINATION_PATTERNS)


def _meaningful_units(text: str) -> int:
    # CJK/日文/韩文按字计；拉丁文本按单词计，避免英文每个字母放大密度。
    cjk = re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)?", text)
    return len(cjk) + len(latin_words)


def _meaningful_words(segment):
    if _is_hallucination(str(segment.get("text", ""))):
        return []
    words = []
    for word in segment.get("words", []):
        text = str(word.get("word", "")).strip()
        if not text or _is_hallucination(text) or _meaningful_units(text) == 0:
            continue
        start = float(word.get("start", segment.get("start", 0.0)))
        end = float(word.get("end", start))
        if end < start:
            start, end = end, start
        words.append({
            "start": start,
            "end": end,
            "text": text,
            "units": _meaningful_units(text),
            "probability": float(word.get("probability", 0.0)),
        })
    return words


def _group_asr_segments(result):
    usable, rejected = [], []
    for raw in result.get("segments", []):
        text = str(raw.get("text", "")).strip()
        words = _meaningful_words(raw)
        if not words:
            rejected.append({
                "start": round(float(raw.get("start", 0.0)), 2),
                "end": round(float(raw.get("end", 0.0)), 2),
                "text": text,
                "reason": "hallucination_or_no_meaningful_words",
            })
            continue
        usable.append({
            "start": min(w["start"] for w in words),
            "end": max(w["end"] for w in words),
            "text": text,
            "words": words,
            "avg_logprob": float(raw.get("avg_logprob", 0.0)),
            "no_speech_prob": float(raw.get("no_speech_prob", 0.0)),
        })

    groups = []
    for item in usable:
        if groups and item["start"] - groups[-1]["end"] <= ASR_GROUP_GAP:
            group = groups[-1]
            group["items"].append(item)
            group["end"] = max(group["end"], item["end"])
        else:
            groups.append({"start": item["start"], "end": item["end"], "items": [item]})

    for group in groups:
        words = [word for item in group["items"] for word in item["words"]]
        span = max(1e-6, group["end"] - group["start"])
        units = sum(word["units"] for word in words)
        word_coverage = sum(max(0.0, word["end"] - word["start"]) for word in words) / span
        mean_word_probability = float(np.mean([word["probability"] for word in words]))
        avg_logprob = float(np.mean([item["avg_logprob"] for item in group["items"]]))
        mean_no_speech_prob = float(np.mean(
            [item["no_speech_prob"] for item in group["items"]]))
        confidence_conflict = bool(
            mean_word_probability < LEXICAL_MIN_WORD_PROB or
            (avg_logprob < LEXICAL_LOW_LOGPROB and mean_word_probability < 0.25))
        group.update({
            "words": words,
            "units": units,
            "char_rate": units / span,
            "word_coverage": min(1.0, word_coverage),
            "word_count": len(words),
            "mean_word_probability": mean_word_probability,
            "avg_logprob": avg_logprob,
            "mean_no_speech_prob": mean_no_speech_prob,
            "confidence_conflict": confidence_conflict,
        })
        group["lexical_content_positive"] = bool(
            units >= LEXICAL_MIN_UNITS and
            (group["char_rate"] >= LEXICAL_POS_CHAR_RATE or
             group["word_coverage"] >= LEXICAL_POS_COVERAGE))
        # 密度证明“像歌词”；置信度冲突只阻止自动信任，仍保留为 REVIEW 候选和边界。
        group["lexical_positive"] = bool(
            group["lexical_content_positive"] and not confidence_conflict)
        group["lexical_negative"] = bool(
            group["char_rate"] < LEXICAL_NEG_CHAR_RATE and
            group["word_coverage"] < LEXICAL_NEG_COVERAGE)
    return groups, rejected


def _merge_intervals(intervals, gap=0.0, pad_start=0.0, pad_end=0.0, duration=None):
    prepared = []
    for start, end in sorted(intervals):
        start = max(0.0, float(start) - pad_start)
        end = float(end) + pad_end
        if duration is not None:
            end = min(float(duration), end)
        if end > start:
            prepared.append([start, end])
    merged = []
    for start, end in prepared:
        if merged and start - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [[round(start, 2), round(end, 2)] for start, end in merged]


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def _coverage(intervals, start, end):
    span = max(1e-6, end - start)
    return sum(_overlap(s, e, start, end) for s, e in intervals) / span


def _safe_intervals(lead_segments, duration):
    safe = []
    for idx, (_, end) in enumerate(lead_segments):
        next_start = lead_segments[idx + 1][0] if idx + 1 < len(lead_segments) else None
        start = end + SAFE_RELEASE
        if next_start is None:
            finish = min(duration, end + 2.5)
        else:
            if next_start - end < SAFE_GAP_MIN:
                continue
            finish = next_start - SAFE_NEXT_PAD
        if finish >= start:
            safe.append([round(start, 2), round(finish, 2)])
    return safe


def _whisper_cache_exists(name: str) -> bool:
    path = Path(name).expanduser()
    if path.is_file():
        return True
    return (Path.home() / ".cache" / "whisper" / f"{name}.pt").is_file()


def load_whisper_model(name="small", device="cpu"):
    """只加载显式路径或已有缓存；绝不由正常 build 隐式下载。"""
    if not _whisper_cache_exists(name):
        raise FileNotFoundError(
            f"Whisper 模型未缓存：{name}。正常 build 禁止自动下载；请先显式预取模型。")
    import whisper
    supplied = Path(name).expanduser()
    checkpoint = supplied if supplied.is_file() else (
        Path.home() / ".cache" / "whisper" / f"{name}.pt")
    # 传本地 checkpoint 路径，避免 whisper.load_model(name) 在缓存损坏时隐式联网重下。
    model = whisper.load_model(str(checkpoint), device=device)
    # 命名官方模型从文件路径加载时需补回 word-timestamp alignment heads。
    alignment_heads = getattr(whisper, "_ALIGNMENT_HEADS", {}).get(name)
    if alignment_heads is not None:
        model.set_alignment_heads(alignment_heads)
    return model


def _transcribe(model, mid, sr, language=None):
    audio = librosa.resample(mid, orig_sr=sr, target_sr=WHISPER_SR)
    return model.transcribe(
        audio.astype(np.float32, copy=False),
        language=language,
        task="transcribe",
        fp16=False,
        temperature=0,
        condition_on_previous_text=False,
        word_timestamps=True,
        no_speech_threshold=None,
        hallucination_silence_threshold=1.0,
        verbose=None,
    )


def analyze(path: Path, min_dur: float = 2.0, gap_tol: float = 1.5,
            percentile: float = 60, *, whisper_model=None,
            whisper_model_name="small", language=None, source_kind="auto") -> dict:
    """运行多证据分析；模型对象由 CLI 复用，也方便测试注入。"""
    path = Path(path)
    left, right, mid, side, sr, channels = _load_stereo(path)
    base = _candidate_result(
        path, left, right, mid, side, sr, channels,
        min_dur=min_dur, gap_tol=gap_tol, percentile=percentile)
    if whisper_model is None:
        return base

    duration = len(mid) / sr
    try:
        transcript = _transcribe(whisper_model, mid, sr, language=language)
    except Exception as exc:  # 模型故障必须显式降级，不能把缺失分数当 0。
        base["capabilities"]["whisper"] = "failed"
        base["evidence"]["warnings"].append(f"Whisper 失败：{type(exc).__name__}: {exc}")
        return base

    groups, rejected = _group_asr_segments(transcript)
    acoustic = base["candidate_segments"]
    segment_scores = []
    lexical_intervals = []
    boundary_intervals = []
    trusted_intervals = []
    ambiguous_intervals = []
    for group in groups:
        center = _center_stats(left, right, mid, side, sr, group["start"], group["end"])
        if channels < 2:
            center["stereo_informative"] = False
        acoustic_overlap = _coverage(acoustic, group["start"], group["end"])
        lexical_positive = group["lexical_positive"]
        lexical_candidate = group["lexical_content_positive"]
        centered = bool(
            center["stereo_informative"] and center["center_db"] is not None and
            center["center_db"] >= LEAD_CENTER_DB)
        acoustic_support = acoustic_overlap >= MIN_ACOUSTIC_OVERLAP
        # 当前无 crowd/choir 事件模型时，显式 Live 源禁止自动信任；观众整齐合唱也可能
        # 同时满足歌词密度和中心性，必须保留 REVIEW。
        live_guard = source_kind == "live"
        trusted = lexical_positive and centered and acoustic_support and not live_guard

        words = [(w["start"], w["end"]) for w in group["words"]]
        word_intervals = _merge_intervals(
            words, gap=WORD_MERGE_GAP, pad_start=0.08, pad_end=0.20, duration=duration)
        # 即使歌词证据太弱，word timestamp 仍是“此处可能正在咬字”的边界阻挡证据，
        # 不能因为没有通过主唱阈值就允许切在它中间。
        boundary_intervals.extend(word_intervals)
        if lexical_candidate:
            lexical_intervals.extend(word_intervals)
            if trusted:
                trusted_intervals.extend(word_intervals)
                label = "lead_singing"
            else:
                ambiguous_intervals.extend(word_intervals)
                label = (
                    "low_confidence_lyrics_review" if group["confidence_conflict"] else
                    "live_singing_review" if live_guard else
                    "singing_or_group_review")
        elif group["lexical_negative"]:
            label = "instrumental_or_crowd"
        else:
            label = "weak_lexical_review"

        segment_scores.append({
            "start": round(group["start"], 2),
            "end": round(group["end"], 2),
            "label": label,
            "lexical_units": group["units"],
            "word_count": group["word_count"],
            "char_rate": round(group["char_rate"], 3),
            "word_coverage": round(group["word_coverage"], 3),
            "mean_word_probability": round(group["mean_word_probability"], 3),
            "avg_logprob": round(group["avg_logprob"], 3),
            "mean_no_speech_prob": round(group["mean_no_speech_prob"], 3),
            "confidence_conflict": group["confidence_conflict"],
            "acoustic_overlap": round(acoustic_overlap, 3),
            **center,
        })

    lexical_intervals = _merge_intervals(lexical_intervals, gap=0.0, duration=duration)
    boundary_intervals = _merge_intervals(boundary_intervals, gap=0.0, duration=duration)
    trusted_intervals = _merge_intervals(trusted_intervals, gap=0.0, duration=duration)
    ambiguous_intervals = _merge_intervals(ambiguous_intervals, gap=0.0, duration=duration)
    safe = _safe_intervals(boundary_intervals, duration)
    trusted_duration = sum(e - s for s, e in trusted_intervals)
    lexical_duration = sum(e - s for s, e in lexical_intervals)
    trusted_ratio = trusted_duration / max(1e-6, lexical_duration)
    evidence_level = (
        "multi_evidence" if trusted_intervals and trusted_ratio >= 0.70 else "candidate")

    base.update({
        "detector": "librosa_whisper_stereo_v2",
        "evidence_level": evidence_level,
        "classification": (
            "lead_singing" if evidence_level == "multi_evidence" else
            "singing_or_group_review" if lexical_intervals else
            "no_lexical_singing_detected"),
        # multi 模式下旧字段也升级为词时间戳候选，避免旧调用方继续吃频带误报。
        "vocal_segments": lexical_intervals,
        "lead_segments": trusted_intervals,
        "boundary_segments": boundary_intervals,
        "boundary_evidence": "whisper_word_timestamps",
        "ambiguous_segments": ambiguous_intervals,
        "safe_cut_intervals": safe,
        "segment_scores": segment_scores,
    })
    base["capabilities"]["whisper"] = "available"
    base["evidence"]["whisper"] = {
        "model": whisper_model_name,
        "language": transcript.get("language"),
        "text": str(transcript.get("text", "")).strip(),
        "rejected_segments": rejected,
        "thresholds": {
            "negative_char_rate": LEXICAL_NEG_CHAR_RATE,
            "negative_word_coverage": LEXICAL_NEG_COVERAGE,
            "positive_char_rate": LEXICAL_POS_CHAR_RATE,
            "positive_word_coverage": LEXICAL_POS_COVERAGE,
            "minimum_units": LEXICAL_MIN_UNITS,
            "minimum_mean_word_probability": LEXICAL_MIN_WORD_PROB,
            "low_avg_logprob": LEXICAL_LOW_LOGPROB,
        },
    }
    base["evidence"]["source_kind"] = source_kind
    if source_kind == "live" and lexical_intervals:
        base["evidence"]["warnings"].append(
            "Live 源尚无 crowd/choir 事件模型：即使歌词/中心性强也保持 REVIEW")
    if ambiguous_intervals:
        base["evidence"]["warnings"].append(
            "检测到歌词但立体声中心性/声学证据不足：可能是观众、合唱或宽混音，需 REVIEW")
    if not lexical_intervals:
        base["evidence"]["warnings"].append(
            "未发现达到阈值的有效歌词；器乐/观众窗不会再自动当作主唱")
    return base


def main():
    parser = argparse.ArgumentParser(description="多证据主唱候选检测")
    parser.add_argument("inputs", nargs="+", help="audio/video files（librosa 可解码格式）")
    parser.add_argument("-o", "--out", help="合并 JSON；缺省时写 <name>.vocal.json")
    parser.add_argument("--min-dur", type=float, default=2.0, help="旧声学候选最短段 (s)")
    parser.add_argument("--gap-tol", type=float, default=1.5, help="旧声学候选段内 gap (s)")
    parser.add_argument("--percentile", type=float, default=60, help="旧声学阈值百分位")
    parser.add_argument(
        "--mode", choices=("auto", "multi", "acoustic"), default="auto",
        help="auto=有离线 Whisper 即多证据；multi=缺模型即失败；acoustic=仅候选")
    parser.add_argument("--whisper-model", default="small", help="已有缓存的模型名或本地 checkpoint")
    parser.add_argument("--device", default="cpu", help="Whisper device；当前默认 cpu")
    parser.add_argument("--language", default=None, help="Whisper 语言，如 zh；缺省自动识别")
    parser.add_argument(
        "--source-kind", choices=("auto", "studio", "live"), default="auto",
        help="Live/演唱会必须传 live；无 crowd 模型时禁止自动认作目标主唱")
    args = parser.parse_args()

    model = None
    if args.mode != "acoustic":
        try:
            model = load_whisper_model(args.whisper_model, args.device)
            print(f"多证据模式：Whisper {args.whisper_model} / {args.device}", flush=True)
        except Exception as exc:
            if args.mode == "multi":
                print(f"多证据模式不可用：{exc}", file=sys.stderr)
                return 2
            print(f"⚠ Whisper 不可用，降级为 acoustic candidate：{exc}", file=sys.stderr)

    combined = {}
    multi_failed = False
    for raw_path in args.inputs:
        path = Path(raw_path)
        if not path.exists():
            print(f"skip {raw_path} (not found)", file=sys.stderr)
            continue
        print(f"分析 {path.name} ...", flush=True)
        result = analyze(
            path, args.min_dur, args.gap_tol, args.percentile,
            whisper_model=model, whisper_model_name=args.whisper_model,
            language=args.language, source_kind=args.source_kind)
        if args.mode == "multi" and result["capabilities"].get("whisper") != "available":
            multi_failed = True
            print(
                f"  ✗ --mode multi 要求 Whisper 成功，实际为 "
                f"{result['capabilities'].get('whisper')}", file=sys.stderr)
        print(
            f"  dur={result['duration']}s  candidate={len(result['candidate_segments'])} "
            f"vocal={len(result['vocal_segments'])} lead={len(result.get('lead_segments', []))} "
            f"evidence={result['evidence_level']}")
        for score in result.get("segment_scores", []):
            print(
                f"    {score['start']:6.2f}-{score['end']:6.2f}  {score['label']} "
                f"chars/s={score['char_rate']:.2f} words={score['word_coverage']:.2f} "
                f"center={score['center_db']}")
        if args.out:
            combined[path.stem] = result
        else:
            output = path.with_suffix(".vocal.json")
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  -> {output}")
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"-> {output}")
    return 2 if multi_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
