#!/usr/bin/env python3
"""Build a self-contained local HTML index for the generated WAV samples."""

from __future__ import annotations

import html
import json
import wave
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = EXPERIMENT_ROOT / "outputs"


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def audio_card(title: str, subtitle: str, path: Path) -> str:
    relative = path.relative_to(OUTPUT_ROOT).as_posix()
    return f"""
    <article class=\"card\">
      <div class=\"card-head\"><div><h3>{html.escape(title)}</h3><p>{html.escape(subtitle)}</p></div><span>{duration(path):.1f}s</span></div>
      <audio controls preload=\"metadata\" src=\"{html.escape(relative)}\"></audio>
      <code>{html.escape(relative)}</code>
    </article>"""


def main() -> int:
    manifest = json.loads((EXPERIMENT_ROOT / "manifest.json").read_text(encoding="utf-8"))
    cards_qwen_show = []
    cards_qwen_mixed = []
    cards_qwen_master = []
    for persona in manifest["personas"]:
        root = OUTPUT_ROOT / "listen-audio" / "qwen3-tts" / persona["id"]
        showcase = root / "showcase.wav"
        mixed = root / "mixed_language.wav"
        master = root / "voice-master.wav"
        subtitle = f"{persona['group']} · {persona['description']}"
        if showcase.is_file():
            cards_qwen_show.append(audio_card(persona["label"], subtitle, showcase))
        if mixed.is_file():
            cards_qwen_mixed.append(audio_card(persona["label"], "中英日混读一致性", mixed))
        if master.is_file():
            cards_qwen_master.append(audio_card(persona["label"], "VoiceDesign 原创母带", master))

    cards_kokoro = []
    for voice in manifest["kokoro_voices"]:
        path = OUTPUT_ROOT / "listen-audio" / "kokoro" / f"{voice}.wav"
        if path.is_file():
            marker = "当前默认" if voice in {"zm_yunxi", "zf_xiaoyi"} else "当前可选"
            cards_kokoro.append(audio_card(voice, f"Kokoro 基线 · {marker}", path))

    if not cards_qwen_show and not cards_kokoro:
        raise SystemExit("no generated samples found")
    page = f"""<!doctype html>
<html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>角色化本地 TTS 试听</title>
<style>
:root{{--bg:#0d1117;--panel:#161b22;--line:#30363d;--text:#f0f6fc;--muted:#8b949e;--accent:#ff75bd;--accent2:#79c0ff}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 15% 0,#301b38 0,transparent 32rem),var(--bg);color:var(--text);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:auto;padding:52px 24px 90px}} header{{max-width:800px;margin-bottom:42px}} h1{{font-size:clamp(34px,6vw,66px);line-height:1.03;margin:0 0 18px;background:linear-gradient(100deg,#fff,var(--accent),var(--accent2));-webkit-background-clip:text;color:transparent}} h2{{font-size:27px;margin:58px 0 8px}} .lead,.section-note{{color:var(--muted);font-size:17px}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px;margin-top:22px}} .card{{background:linear-gradient(145deg,#1b212b,#12161d);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 16px 36px #0005}} .card-head{{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}} h3{{margin:0;font-size:19px}} .card p{{margin:5px 0 15px;color:var(--muted);font-size:13px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}} .card span{{font:12px ui-monospace;color:var(--accent2);white-space:nowrap}} audio{{width:100%;height:40px}} code{{display:block;margin-top:10px;color:#a5d6ff;font-size:11px;overflow-wrap:anywhere}} .tip{{border-left:3px solid var(--accent);padding:9px 15px;background:#ff75bd12;border-radius:0 10px 10px 0}}
</style></head><body><main>
<header><h1>角色化本地 TTS 试听</h1><p class=\"lead\">同一段盘点文案，先听 8 种 Qwen 原创角色声线，再与当前 Kokoro 8 音色公平对照。全部试听副本统一到 -18 LUFS / -1.5 dBTP；请戴耳机，重点听角色辨识度、中文自然度、节奏和长期耐听度。</p><p class=\"tip\">建议先只听“固化后盘点样音”，选出 2–4 个候选；再听母带与混合语言，判断音色一致性和作品名可懂度。</p></header>
<section><h2>Qwen 固化后盘点样音</h2><p class=\"section-note\">VoiceDesign 只负责创建母带；这些样音由 Base 模型克隆母带，代表未来批量生产的实际声音。</p><div class=\"grid\">{''.join(cards_qwen_show)}</div></section>
<section><h2>Qwen 中英日混读</h2><p class=\"section-note\">统一测试 AI、One Piece 与進撃の巨人。自动 QA 不替代逐条听写。</p><div class=\"grid\">{''.join(cards_qwen_mixed)}</div></section>
<section><h2>VoiceDesign 原创母带</h2><p class=\"section-note\">对比母带与固化样音，判断 Base 克隆有没有明显丢失角色特征。</p><div class=\"grid\">{''.join(cards_qwen_master)}</div></section>
<section><h2>当前 Kokoro 8 音色基线</h2><p class=\"section-note\">全部由现有 tools/tts/narrate.py 生成；zm_yunxi 与 zf_xiaoyi 是当前默认男/女声。</p><div class=\"grid\">{''.join(cards_kokoro)}</div></section>
</main></body></html>"""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_ROOT / "listen.html"
    path.write_text(page, encoding="utf-8")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
