#!/usr/bin/env python3
"""Normalize isolated samples, run mechanical audio QA, and build listen.html."""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import wave
from pathlib import Path


LAB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_ROOT.parents[3]
OUTPUT_ROOT = LAB_ROOT / "outputs"
VOICE_ROOT = OUTPUT_ROOT / "voices"
LISTEN_ROOT = OUTPUT_ROOT / "listen-audio"
RESOURCE_BUDGET = REPO_ROOT / "tools" / "video" / "resource_budget.py"
MANIFEST_PATH = LAB_ROOT / "manifest.json"
TARGET_I = -18.0
TARGET_TP = -1.5
TARGET_LRA = 11.0
THREAD_TOKEN = "__CC_MEDIA_THREADS__"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def run_budgeted_ffmpeg(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            str(RESOURCE_BUDGET),
            "ffmpeg",
            "--",
            "ffmpeg",
            "-threads",
            THREAD_TOKEN,
            *arguments,
        ]
    )


def normalize(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    edge_trim = "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-55dB"
    audio_filter = (
        f"{edge_trim},areverse,{edge_trim},areverse,"
        f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
    )
    completed = run_budgeted_ffmpeg(
        [
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-af",
            audio_filter,
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(target),
        ]
    )
    if completed.returncode:
        raise RuntimeError(
            f"normalization failed for {source.relative_to(LAB_ROOT)}: "
            f"{completed.stderr.strip()}"
        )


def prepare_persona(persona: dict) -> dict:
    persona_id = persona["id"]
    source_root = VOICE_ROOT / persona_id / "ready"
    target_root = LISTEN_ROOT / persona_id
    jobs = {
        "showcase": (source_root / "showcase.wav", target_root / "showcase.wav"),
        "master": (source_root / "voice-master.wav", target_root / "voice-master.wav"),
    }
    mixed_source = source_root / "mixed-language.wav"
    if mixed_source.is_file():
        jobs["mixed_language"] = (
            mixed_source,
            target_root / "mixed-language.wav",
        )
    missing = [source for source, _ in jobs.values() if not source.is_file()]
    if missing:
        return {
            "persona_id": persona_id,
            "status": "missing",
            "missing": [str(path.relative_to(LAB_ROOT)) for path in missing],
        }
    meta_path = target_root / "normalize-meta.json"
    inputs = {name: sha256(source) for name, (source, _) in jobs.items()}
    cached = None
    if meta_path.is_file():
        try:
            candidate = read_json(meta_path)
            if candidate.get("inputs") == inputs:
                targets = candidate.get("targets", {})
                if all(
                    target.is_file() and targets.get(name) == sha256(target)
                    for name, (_, target) in jobs.items()
                ):
                    cached = candidate
        except (OSError, ValueError, json.JSONDecodeError):
            cached = None
    if cached is None:
        for name, (source, target) in jobs.items():
            print(f"NORMALIZE {persona_id} {name}", flush=True)
            normalize(source, target)
        cached = {
            "persona_id": persona_id,
            "status": "prepared",
            "inputs": inputs,
            "targets": {name: sha256(target) for name, (_, target) in jobs.items()},
            "target_lufs": TARGET_I,
            "target_true_peak_dbtp": TARGET_TP,
        }
        write_json(meta_path, cached)
    return cached


def parse_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match or match.group(1) == "-inf":
        return None
    return float(match.group(1))


def probe(path: Path) -> dict:
    ffprobe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_name,codec_type,sample_rate,channels,bits_per_sample",
            "-of",
            "json",
            str(path),
        ]
    )
    analysis = run_budgeted_ffmpeg(
        [
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "silencedetect=n=-45dB:d=0.8,volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    errors: list[str] = []
    warnings: list[str] = []
    info = {}
    if ffprobe.returncode:
        errors.append("ffprobe_failed")
    else:
        info = json.loads(ffprobe.stdout)
    if analysis.returncode:
        errors.append("ffmpeg_analysis_failed")
    streams = info.get("streams", [])
    stream = streams[0] if streams else {}
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    mean_volume = parse_float(
        r"mean_volume:\s+(-?inf|-?\d+(?:\.\d+)?) dB", analysis.stderr
    )
    max_volume = parse_float(
        r"max_volume:\s+(-?inf|-?\d+(?:\.\d+)?) dB", analysis.stderr
    )
    silences = [
        float(value)
        for value in re.findall(r"silence_duration:\s*(\d+(?:\.\d+)?)", analysis.stderr)
    ]
    if duration < 1.0:
        errors.append("duration_too_short")
    if int(stream.get("sample_rate", 0) or 0) != 24000:
        errors.append("sample_rate_not_24000")
    if stream.get("channels") != 1:
        errors.append("not_mono")
    if max_volume is not None and max_volume >= -0.05:
        warnings.append("peak_near_zero_dbfs")
    if silences:
        warnings.append("contains_silence_over_0_8s")
    return {
        "path": str(path.relative_to(LAB_ROOT)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "duration_seconds": duration,
        "codec": stream.get("codec_name"),
        "sample_rate_hz": int(stream.get("sample_rate", 0) or 0),
        "channels": stream.get("channels"),
        "bits_per_sample": stream.get("bits_per_sample"),
        "mean_volume_db": mean_volume,
        "max_volume_db": max_volume,
        "silence_durations_over_0_8s": silences,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def audio_player(label: str, path: Path) -> str:
    relative = path.relative_to(OUTPUT_ROOT).as_posix()
    return (
        f'<div class="player"><span>{html.escape(label)} · {duration(path):.1f}s</span>'
        f'<audio controls preload="metadata" src="{html.escape(relative)}"></audio></div>'
    )


def card(persona: dict, category_label: str) -> str:
    root = LISTEN_ROOT / persona["id"]
    showcase = root / "showcase.wav"
    master = root / "voice-master.wav"
    tags = "".join(f"<i>{html.escape(tag)}</i>" for tag in persona["tags"])
    search = " ".join(
        [
            persona["id"],
            persona["label"],
            persona["group"],
            category_label,
            *persona["tags"],
            persona["description"],
        ]
    )
    return f"""
    <article class="card" data-category="{html.escape(persona['category'])}" data-group="{html.escape(persona['group'])}" data-search="{html.escape(search.lower())}">
      <div class="head"><div><small>{html.escape(category_label)}</small><h3>{html.escape(persona['label'])}</h3></div><b>{html.escape(persona['group'])}</b></div>
      <div class="tags">{tags}</div>
      <p>{html.escape(persona['description'])}</p>
      {audio_player('统一解说文案', showcase)}
      <details><summary>试听 VoiceDesign 原创母带</summary>{audio_player('原创母带', master)}</details>
      <code>{html.escape(persona['id'])}</code>
    </article>"""


def build_page(manifest: dict, available: list[dict], qa_summary: dict) -> None:
    category_labels = {item["id"]: item["label"] for item in manifest["categories"]}
    cards = "".join(card(persona, category_labels[persona["category"]]) for persona in available)
    category_buttons = "".join(
        f'<button data-filter="category:{html.escape(item["id"])}">{html.escape(item["label"])}</button>'
        for item in manifest["categories"]
    )
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Qwen 声线扩展实验室 · 69 声线试听</title>
<style>
:root{{--bg:#090b12;--panel:#141824;--line:#2a3144;--text:#f5f7ff;--muted:#98a3bd;--accent:#82f7cb;--hot:#ff8ec7;--blue:#86b8ff}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 12% 0,#273154 0,transparent 32rem),radial-gradient(circle at 90% 10%,#3a1832 0,transparent 28rem),var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,sans-serif}}
main{{width:min(1420px,94vw);margin:auto;padding:48px 0 90px}}header{{max-width:940px}}h1{{font-size:clamp(34px,5vw,65px);line-height:1.05;margin:0 0 14px}}.lead{{font-size:17px;color:var(--muted)}}.notice{{margin:22px 0;padding:14px 17px;border:1px solid #3a4968;background:#111827cc;border-radius:14px}}.controls{{position:sticky;top:0;z-index:4;background:#090b12e8;backdrop-filter:blur(16px);padding:14px 0;margin:26px 0 20px;border-bottom:1px solid var(--line)}}input{{width:100%;padding:13px 15px;background:#121725;border:1px solid var(--line);border-radius:12px;color:var(--text);font:inherit;margin-bottom:10px}}.buttons{{display:flex;flex-wrap:wrap;gap:8px}}button{{border:1px solid var(--line);background:#171d2c;color:var(--text);padding:8px 11px;border-radius:999px;cursor:pointer}}button.active{{background:var(--accent);color:#082218;border-color:var(--accent)}}.count{{color:var(--accent);margin:10px 0 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:15px}}.card{{background:linear-gradient(145deg,#181e2d,#10141f);border:1px solid var(--line);border-radius:18px;padding:17px;box-shadow:0 18px 40px #0005}}.card[hidden]{{display:none}}.head{{display:flex;justify-content:space-between;gap:12px}}small{{color:var(--accent)}}h3{{font-size:21px;margin:2px 0 0}}b{{color:var(--blue);font-size:12px}}.tags{{display:flex;flex-wrap:wrap;gap:6px;margin:11px 0}}i{{font-style:normal;font-size:11px;padding:3px 8px;background:#29314a;border-radius:999px;color:#cbd5ef}}.card>p{{color:var(--muted);min-height:88px;margin:10px 0 13px}}.player span{{display:block;font-size:11px;color:var(--hot);margin:7px 0 4px}}audio{{width:100%;height:38px}}details{{margin-top:9px}}summary{{color:var(--muted);cursor:pointer;font-size:12px}}code{{display:block;color:#687792;margin-top:10px;font-size:11px}}@media(max-width:640px){{main{{padding-top:28px}}.grid{{grid-template-columns:1fr}}.card>p{{min-height:0}}}}
</style></head><body><main>
<header><h1>Qwen 声线扩展实验室</h1><p class="lead">69 种原创成年声线的独立横向试听。重点包含短视频电影解说、悬疑、科幻、自然 / 人文 / 历史纪录片经典型，以及更广的女声、男声和中性声。所有候选与正式 cc-media TTS 注册表完全隔离。</p>
<div class="notice"><strong>同文案公平比较</strong><br>先听每张卡片的“统一解说文案”；感兴趣再展开原创母带。试听副本统一为 24kHz 单声道并做响度匹配。机械 QA：{qa_summary['passed']}/{qa_summary['total']} PASS，{qa_summary['failed']} FAIL。</div></header>
<section class="controls"><input id="search" type="search" placeholder="搜索：电影解说、纪录片、悬疑、低沉、温柔……"><div class="buttons"><button class="active" data-filter="all">全部</button>{category_buttons}<button data-filter="group:female">女声</button><button data-filter="group:male">男声</button><button data-filter="group:neutral">中性声</button></div><p class="count" id="count"></p></section>
<section class="grid" id="grid">{cards}</section>
</main><script>
const cards=[...document.querySelectorAll('.card')],buttons=[...document.querySelectorAll('button')],search=document.querySelector('#search'),count=document.querySelector('#count');let filter='all';
function render(){{const q=search.value.trim().toLowerCase();let shown=0;for(const card of cards){{let ok=filter==='all';if(filter.startsWith('category:'))ok=card.dataset.category===filter.slice(9);if(filter.startsWith('group:'))ok=card.dataset.group===filter.slice(6);ok=ok&&(!q||card.dataset.search.includes(q));card.hidden=!ok;if(ok)shown++;}}count.textContent=`当前显示 ${{shown}} / ${{cards.length}} 种声线`;}}
buttons.forEach(button=>button.addEventListener('click',()=>{{buttons.forEach(item=>item.classList.remove('active'));button.classList.add('active');filter=button.dataset.filter;render();}}));search.addEventListener('input',render);render();
</script></body></html>"""
    (OUTPUT_ROOT / "listen.html").write_text(page, encoding="utf-8")


def main() -> int:
    manifest = read_json(MANIFEST_PATH)
    prepared = [prepare_persona(persona) for persona in manifest["personas"]]
    available_ids = {
        item["persona_id"] for item in prepared if item.get("status") != "missing"
    }
    available = [persona for persona in manifest["personas"] if persona["id"] in available_ids]
    if not available:
        raise SystemExit("no generated voices found; run generate_samples.py first")

    records = []
    for index, persona in enumerate(available, 1):
        names = ["showcase.wav", "voice-master.wav"]
        if (LISTEN_ROOT / persona["id"] / "mixed-language.wav").is_file():
            names.append("mixed-language.wav")
        for name in names:
            path = LISTEN_ROOT / persona["id"] / name
            print(f"QA {index:02d}/{len(available):02d} {persona['id']} {name}", flush=True)
            records.append(probe(path))
    summary = {
        "total": len(records),
        "passed": sum(item["status"] == "PASS" for item in records),
        "failed": sum(item["status"] == "FAIL" for item in records),
        "warnings": sum(bool(item["warnings"]) for item in records),
        "available_personas": len(available),
        "missing_personas": len(manifest["personas"]) - len(available),
    }
    report = {
        "schema_version": "1.0.0",
        "experiment_id": manifest["experiment_id"],
        "normalization": {
            "target_lufs": TARGET_I,
            "target_true_peak_dbtp": TARGET_TP,
            "target_lra": TARGET_LRA,
        },
        "prepared": prepared,
        "files": records,
        "summary": summary,
    }
    write_json(OUTPUT_ROOT / "qa" / "audio-report.json", report)
    build_page(manifest, available, summary)
    print(
        f"LISTEN PAGE PASS: voices={len(available)} files={summary['total']} "
        f"qa_pass={summary['passed']} qa_fail={summary['failed']} "
        f"path={OUTPUT_ROOT / 'listen.html'}",
        flush=True,
    )
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
