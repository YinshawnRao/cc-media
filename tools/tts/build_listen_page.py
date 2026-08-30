#!/usr/bin/env python3
"""Build the local numbered voice-library listening page."""

from __future__ import annotations

import html
import json
import wave
from collections import Counter
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parent
VOICE_ROOT = TTS_ROOT / "voices"


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


def card(title: str, subtitle: str, path: Path, badge: str = "") -> str:
    relative = path.relative_to(VOICE_ROOT).as_posix()
    badge_html = f'<span class="badge">{html.escape(badge)}</span>' if badge else ""
    return f"""
    <article class="card">
      <div class="head"><div><h3>{html.escape(title)} {badge_html}</h3><p>{html.escape(subtitle)}</p></div><b>{duration(path):.1f}s</b></div>
      <audio controls preload="metadata" src="{html.escape(relative)}"></audio>
      <code>{html.escape(relative)}</code>
    </article>"""


def main() -> int:
    registry = json.loads((VOICE_ROOT / "registry.json").read_text(encoding="utf-8"))
    config = json.loads((TTS_ROOT / "config.json").read_text(encoding="utf-8"))
    decision_ids = config["decision_voice_pool"]
    if len(decision_ids) != len(set(decision_ids)):
        raise ValueError("decision_voice_pool must not contain duplicate IDs")
    voices_by_id = {voice["id"]: voice for voice in registry["voices"]}
    missing_ids = [voice_id for voice_id in decision_ids if voice_id not in voices_by_id]
    if missing_ids:
        raise ValueError(f"decision_voice_pool contains unknown IDs: {missing_ids}")

    current_voices = [voices_by_id[voice_id] for voice_id in decision_ids]
    decision_pool = set(decision_ids)
    archived_voices = [
        voice for voice in registry["voices"] if voice["id"] not in decision_pool
    ]
    references = []
    ranking = []
    mixed = []
    rows = []
    for voice in current_voices:
        badge = "当前池"
        label = f"{voice['id']} · {voice['name']}"
        references.append(
            card(label, "VoiceDesign 原创参考母带", VOICE_ROOT / voice["reference_audio"], badge)
        )
        ranking.append(
            card(label, voice["description"], VOICE_ROOT / voice["examples"]["ranking"], badge)
        )
        mixed.append(
            card(label, "中英日混读测试", VOICE_ROOT / voice["examples"]["mixed_language"], badge)
        )
        aliases = " / ".join(voice["aliases"][:4])
        group = {"female": "女声", "male": "男声"}.get(voice["group"], voice["group"])
        rows.append(
            f"<tr><td>{voice['id']}</td><td>{html.escape(voice['name'])}</td>"
            f"<td>{html.escape(group)}</td><td>{html.escape(aliases)}</td></tr>"
        )

    archived_ranking = []
    archived_references = []
    archived_mixed = []
    for voice in archived_voices:
        label = f"{voice['id']} · {voice['name']}"
        archived_ranking.append(
            card(label, voice["description"], VOICE_ROOT / voice["examples"]["ranking"])
        )
        archived_references.append(
            card(label, "VoiceDesign 原创参考母带", VOICE_ROOT / voice["reference_audio"])
        )
        archived_mixed.append(
            card(label, "中英日混读测试", VOICE_ROOT / voice["examples"]["mixed_language"])
        )

    kokoro = []
    baseline_root = VOICE_ROOT / "baselines" / "kokoro"
    for path in sorted(baseline_root.glob("*.wav")):
        kokoro.append(card(path.stem, "Legacy Kokoro 同文案基线", path))

    decision_id_text = "、".join(decision_ids)
    group_counts = Counter(voice["group"] for voice in current_voices)
    group_text = f"{group_counts.get('male', 0)} 男 {group_counts.get('female', 0)} 女"
    archived_id_text = "、".join(voice["id"] for voice in archived_voices)

    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>cc-media 当前十声线试听</title>
<style>
:root{{--bg:#0d1020;--panel:#171b31;--line:#2a3153;--text:#f5f7ff;--muted:#aab3d1;--accent:#8ee7cf;--pink:#ff9fca}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 10% 0,#22284b 0,transparent 38%),var(--bg);color:var(--text);font:15px/1.6 system-ui,-apple-system,sans-serif}}
main{{width:min(1160px,92vw);margin:0 auto;padding:56px 0 80px}}h1{{font-size:clamp(30px,5vw,58px);margin:0 0 8px}}h2{{margin:48px 0 6px;font-size:25px}}.lead,.section-note{{color:var(--muted);max-width:850px}}.section-note{{margin:0 0 16px}}.notice{{padding:16px 18px;border:1px solid var(--accent);border-radius:14px;background:#102821;margin:24px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}.card{{background:linear-gradient(145deg,#1b203a,#14182c);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 12px 30px #05071466}}.head{{display:flex;justify-content:space-between;gap:16px}}h3{{margin:0;font-size:18px}}p{{margin:5px 0 13px;color:var(--muted)}}audio{{width:100%;height:38px}}code{{display:block;color:#8390b8;font-size:11px;margin-top:8px;overflow-wrap:anywhere}}.badge{{font-size:11px;background:var(--pink);color:#25091a;border-radius:999px;padding:3px 8px;vertical-align:2px}}table{{width:100%;border-collapse:collapse;background:#12162a;border:1px solid var(--line)}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left}}th{{color:var(--accent)}}details.archive{{margin-top:52px;border:1px solid var(--line);border-radius:16px;background:#101426;padding:4px 18px 22px}}details.archive summary{{cursor:pointer;padding:16px 0;font-size:18px;color:var(--accent)}}details.archive h2{{margin-top:32px}}@media(max-width:600px){{main{{padding-top:30px}}.grid{{grid-template-columns:1fr}}table{{font-size:12px}}th:nth-child(4),td:nth-child(4){{display:none}}}}
</style></head><body><main>
<h1>当前十声线试听</h1>
<p class="lead">本页优先展示当前自动决策池，便于用同一段文案横向试听并决定下一步调整。角色编号永久稳定，不因排序或新增声音而改变。</p>
<div class="notice"><strong>当前标准：模型先按作品情绪与叙事表达选择</strong><br>标准池共 {len(current_voices)} 个声音（{group_text}）：{decision_id_text}。建议先听“统一盘点文案”；只有模型无法可靠决策时才从同一池随机一次，结果写入 voice-selection.json 后整期固定。</div>
<h2>当前池编号</h2><table><thead><tr><th>编号</th><th>名称</th><th>类型</th><th>常用别名</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>统一盘点文案</h2><p class="section-note">最适合先横向比较中文自然度、角色辨识度、节奏与长期耐听度。</p><div class="grid">{''.join(ranking)}</div>
<h2>原创参考母带</h2><p class="section-note">用于确认克隆目标本身的音色、气息与表达基线。</p><div class="grid">{''.join(references)}</div>
<h2>中英日混读</h2><p class="section-note">用于复核外文作品名和混合语言的可懂度；纯中文项目不以这一组作为首要取舍依据。</p><div class="grid">{''.join(mixed)}</div>
<details class="archive"><summary>历史声音与 Legacy 基线（折叠，不参与当前自动决策）</summary>
<p class="section-note">未进入当前池的正式编号（{archived_id_text}）仍保留显式指定和历史复现能力；Legacy Kokoro 只用于旧工程兼容。</p>
<h2>历史编号 · 统一盘点文案</h2><div class="grid">{''.join(archived_ranking)}</div>
<h2>历史编号 · 原创参考母带</h2><div class="grid">{''.join(archived_references)}</div>
<h2>历史编号 · 中英日混读</h2><div class="grid">{''.join(archived_mixed)}</div>
<h2>Legacy Kokoro 基线</h2><div class="grid">{''.join(kokoro)}</div>
</details>
</main><script>document.querySelectorAll('audio').forEach((player)=>player.addEventListener('play',()=>document.querySelectorAll('audio').forEach((other)=>{{if(other!==player)other.pause()}})))</script></body></html>"""
    output = VOICE_ROOT / "listen.html"
    output.write_text(page, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
