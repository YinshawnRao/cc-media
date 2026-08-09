#!/usr/bin/env python3
"""Two-layer local Whisper QA: isolated narration and final post-mux AAC."""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
from pathlib import Path

import whisper


ROOT = Path(__file__).resolve().parents[1]
MODEL = Path.home() / ".cache" / "whisper" / "small.pt"


def compact(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fff0-9]", "", text)


def normalize_observed(text: str) -> str:
    """Normalize only variants actually emitted in this run; keep raw evidence."""
    return text.replace("薩克斯", "萨克斯").replace("評論區", "评论区").replace("點贊", "点赞")


def transcribe(model: object, wav: Path) -> str:
    result = model.transcribe(
        str(wav), language="zh", task="transcribe", fp16=False,
        condition_on_previous_text=False, temperature=0,
    )
    return str(result.get("text", "")).strip()


def isolated(model: object, narration: dict[str, dict[str, object]]) -> None:
    rows = []
    for key in ("intro", "p5", "p4", "p3", "p2", "p1", "outro", "outro_cta"):
        expected = str(narration[key]["text"])
        actual = transcribe(model, ROOT / "audio" / f"{key}.wav")
        similarity = difflib.SequenceMatcher(None, compact(expected), compact(actual)).ratio()
        rows.append({
            "key": key, "source": f"audio/{key}.wav", "expected": expected,
            "transcript_raw": actual, "similarity": round(similarity, 3),
            "forbidden_next": "接下来" in actual,
        })
        print(f"isolated {key:10s} similarity={similarity:.3f}  {actual}")
    status = "OK" if all(r["transcript_raw"] and r["similarity"] >= .55 and not r["forbidden_next"] for r in rows) else "CHECK"
    payload = {"status": status, "model": "whisper-small-local", "items": rows}
    (ROOT / "qa" / "isolated_narration_asr.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if status != "OK":
        raise RuntimeError("isolated narration ASR requires review")


def final_aac(model: object, narration: dict[str, dict[str, object]]) -> None:
    meta = json.loads((ROOT / "meta.json").read_text(encoding="utf-8"))
    final = ROOT / "renders" / "saxophone-instrumental-top5.mp4"
    clips = ROOT / "qa" / "asr_windows"
    clips.mkdir(parents=True, exist_ok=True)
    required = {
        "intro": ["五首", "萨克斯"], "p5": ["第五", "摇摆", "萨克斯"],
        "p4": ["第四", "钢琴", "浪漫"], "p3": ["第三", "城市", "萨克斯"],
        "p2": ["第二", "回家", "归途"], "p1": ["第一", "旋律", "萨克斯"],
        "outro": ["萨克斯", "评论区", "点赞"],
    }
    windows = [("intro", 0.0, float(meta["intro_end"]), str(narration["intro"]["text"]))]
    for block in meta["blocks"]:
        windows.append((
            block["key"], max(0.0, float(block["narr_start"]) - .1),
            float(block["narr_end"]) + .35, str(narration[block["key"]]["text"]),
        ))
    windows.append((
        "outro", float(meta["outro_start"]), float(meta["duration"]),
        str(narration["outro"]["text"]) + str(narration["outro_cta"]["text"]),
    ))
    rows = []
    for key, start, end, expected in windows:
        wav = clips / f"{key}.wav"
        subprocess.run([
            "ffmpeg", "-v", "error", "-ss", str(round(start, 3)), "-i", str(final),
            "-t", str(round(end - start, 3)), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(wav), "-y",
        ], check=True)
        actual = transcribe(model, wav)
        normalized = normalize_observed(actual)
        similarity = difflib.SequenceMatcher(None, compact(expected), compact(normalized)).ratio()
        context_ok = any(token in normalized for token in required[key])
        rows.append({
            "key": key, "source": "final post-mux AAC", "start": round(start, 3), "end": round(end, 3),
            "expected": expected, "transcript_raw": actual, "transcript_normalized": normalized,
            "normalization_scope": ["薩克斯->萨克斯", "評論區->评论区", "點贊->点赞"],
            "similarity": round(similarity, 3),
            "context_tokens": required[key], "context_ok": context_ok, "forbidden_next": "接下来" in actual,
        })
        print(f"final {key:10s} similarity={similarity:.3f} context={context_ok}  {actual}")
    status = "OK" if all(r["transcript_raw"] and r["similarity"] >= .25 and r["context_ok"] and not r["forbidden_next"] for r in rows) else "CHECK"
    payload = {"status": status, "model": "whisper-small-local", "audio_source": str(final.relative_to(ROOT)), "items": rows}
    (ROOT / "qa" / "final_asr.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if status != "OK":
        raise RuntimeError("final AAC ASR requires review")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("isolated", "final"))
    args = parser.parse_args()
    if not MODEL.is_file():
        raise RuntimeError(f"Whisper checkpoint is not cached: {MODEL}")
    narration = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
    model = whisper.load_model(str(MODEL), device="cpu")
    isolated(model, narration) if args.mode == "isolated" else final_aac(model, narration)


if __name__ == "__main__":
    main()
