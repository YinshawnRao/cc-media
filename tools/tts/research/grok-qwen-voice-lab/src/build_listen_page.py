#!/usr/bin/env python3
"""Normalize isolated samples, run mechanical audio QA, and build a tabbed listen.html."""

from __future__ import annotations

import html
import importlib.util
from pathlib import Path


LAB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_ROOT.parents[3]
SHARED = (
    REPO_ROOT
    / "tools"
    / "tts"
    / "research"
    / "qwen-voice-expansion-lab"
    / "src"
    / "build_listen_page.py"
)
TEMPLATE = Path(__file__).with_name("listen_template.html")


def load_shared():
    research_root = (REPO_ROOT / "tools" / "tts" / "research").resolve()
    if research_root not in LAB_ROOT.resolve().parents:
        raise SystemExit("refusing to run outside tools/tts/research")
    spec = importlib.util.spec_from_file_location("qwen_voice_lab_page", SHARED)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load shared page builder: {SHARED}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.LAB_ROOT = LAB_ROOT
    module.REPO_ROOT = REPO_ROOT
    module.OUTPUT_ROOT = LAB_ROOT / "outputs"
    module.VOICE_ROOT = module.OUTPUT_ROOT / "voices"
    module.LISTEN_ROOT = module.OUTPUT_ROOT / "listen-audio"
    module.MANIFEST_PATH = LAB_ROOT / "manifest.json"
    module.RESOURCE_BUDGET = REPO_ROOT / "tools" / "video" / "resource_budget.py"
    return module


def card(module, persona: dict, category_label: str) -> str:
    root = module.LISTEN_ROOT / persona["id"]
    showcase = root / "showcase.wav"
    master = root / "voice-master.wav"
    mixed = root / "mixed-language.wav"
    mixed_player = module.audio_player("中英日混读", mixed) if mixed.is_file() else ""
    tags = "".join(f"<i>{html.escape(tag)}</i>" for tag in persona["tags"])
    code = persona.get("code", persona["id"])
    summary = persona.get("summary", persona["description"])
    search = " ".join(
        [
            persona["id"],
            code,
            persona["label"],
            persona["group"],
            category_label,
            *persona["tags"],
            summary,
            persona["description"],
        ]
    )
    gender = "女声" if persona["group"] == "female" else "男声"
    return f"""
    <article class="card" id="{html.escape(code)}" data-code="{html.escape(code)}" data-category="{html.escape(persona['category'])}" data-group="{html.escape(persona['group'])}" data-search="{html.escape(search.lower())}">
      <div class="head"><div><small>{html.escape(category_label)} · {gender}</small><div class="code">{html.escape(code)}</div><h3>{html.escape(persona['label'])}</h3></div><button type="button" class="pick">标记编号</button></div>
      <div class="tags">{tags}</div>
      <p>{html.escape(summary)}</p>
      {module.audio_player('统一解说文案', showcase)}
      <details><summary>展开简介、原创母带与混合语言</summary><p>{html.escape(persona['description'])}</p>{module.audio_player('原创母带', master)}{mixed_player}</details>
      <div class="meta"><code>{html.escape(persona['id'])}</code></div>
    </article>"""


def build_page(module, manifest: dict, available: list[dict], qa_summary: dict) -> None:
    category_labels = {item["id"]: item["label"] for item in manifest["categories"]}
    cards = "".join(card(module, persona, category_labels[persona["category"]]) for persona in available)
    category_buttons = "".join(
        f'<button data-filter="{html.escape(item["id"])}">{html.escape(item["label"])}</button>'
        for item in manifest["categories"]
    )
    page_config = manifest.get("listen_page", {})
    comparison_href = page_config.get("comparison_href")
    comparison_label = page_config.get("comparison_label", "打开当前正式声线试听页")
    comparison_html = (
        f'<p><a class="compare" href="{html.escape(comparison_href)}">{html.escape(comparison_label)}</a></p>'
        if comparison_href
        else ""
    )
    qa = (
        f"{qa_summary['passed']}/{qa_summary['total']} PASS，"
        f"{qa_summary['failed']} FAIL"
    )
    page = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__TITLE__": page_config.get("document_title", "Grok Qwen 声线实验室"),
        "__HEADING__": page_config.get("heading", "Grok × Qwen 一百声线"),
        "__LEAD__": page_config.get("lead", ""),
        "__COMPARE__": comparison_html,
        "__QA__": qa,
        "__CATEGORY_BUTTONS__": category_buttons,
        "__CARDS__": cards,
    }
    for key, value in replacements.items():
        page = page.replace(key, value)
    (module.OUTPUT_ROOT / "listen.html").write_text(page, encoding="utf-8")


def main() -> int:
    module = load_shared()
    module.card = lambda persona, category_label: card(module, persona, category_label)
    module.build_page = lambda manifest, available, qa_summary: build_page(
        module, manifest, available, qa_summary
    )
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
