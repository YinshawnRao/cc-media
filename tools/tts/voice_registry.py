#!/usr/bin/env python3
"""Deterministic character-voice registry and task-prompt resolver."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = TTS_ROOT / "config.json"
REGISTRY_PATH = TTS_ROOT / "voices" / "registry.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\s_\-—–/\\'\"“”‘’「」『』()（）\[\]【】]+", "", value)


@dataclass(frozen=True)
class VoiceRegistry:
    config: dict
    registry: dict

    @classmethod
    def load(cls) -> "VoiceRegistry":
        value = cls(read_json(CONFIG_PATH), read_json(REGISTRY_PATH))
        value.validate()
        return value

    @property
    def voices(self) -> list[dict]:
        return [voice for voice in self.registry["voices"] if voice.get("enabled", True)]

    @property
    def default_id(self) -> str:
        return self.config["default_voice_id"]

    @property
    def registry_sha256(self) -> str:
        return file_sha256(REGISTRY_PATH)

    @property
    def config_sha256(self) -> str:
        return file_sha256(CONFIG_PATH)

    def by_id(self, voice_id: str) -> dict | None:
        wanted = voice_id.upper()
        return next((voice for voice in self.voices if voice["id"] == wanted), None)

    def tokens_for(self, voice: dict) -> list[tuple[str, str]]:
        values = [
            (voice["id"], "id"),
            (voice["name"], "name"),
            (voice["slug"], "slug"),
            (voice.get("legacy_persona_id", ""), "legacy_persona_id"),
        ]
        values.extend((alias, "alias") for alias in voice.get("aliases", []))
        return [(normalize(value), kind) for value, kind in values if value]

    def legacy_voice(self, selector: str) -> str | None:
        raw = selector.strip()
        if raw.casefold().startswith("kokoro:"):
            raw = raw.split(":", 1)[1]
        return raw if raw in self.config["legacy_kokoro"]["voices"] else None

    def match_fragment(self, fragment: str) -> tuple[list[dict], str | None]:
        normalized = normalize(fragment)
        matched: dict[str, dict] = {}
        matched_by: set[str] = set()
        legacy = self.legacy_voice(fragment)
        if legacy:
            return [
                {
                    "id": f"kokoro:{legacy}",
                    "name": legacy,
                    "engine": self.config["legacy_kokoro"]["engine"],
                    "legacy_voice": legacy,
                }
            ], "legacy_id"
        for voice in self.voices:
            for token, kind in self.tokens_for(voice):
                if token and token in normalized:
                    matched[voice["id"]] = voice
                    matched_by.add(kind)
        if not matched:
            return [], None
        priority = ["id", "name", "slug", "legacy_persona_id", "alias"]
        by = next((kind for kind in priority if kind in matched_by), "alias")
        return list(matched.values()), by

    def exact_selector(self, selector: str) -> tuple[dict | None, str | None]:
        legacy = self.legacy_voice(selector)
        if legacy:
            return {
                "id": f"kokoro:{legacy}",
                "name": legacy,
                "engine": self.config["legacy_kokoro"]["engine"],
                "legacy_voice": legacy,
            }, "legacy_id"
        wanted = normalize(selector)
        matches: list[tuple[dict, str]] = []
        for voice in self.voices:
            for token, kind in self.tokens_for(voice):
                if wanted == token:
                    matches.append((voice, kind))
        ids = {voice["id"] for voice, _ in matches}
        if len(ids) != 1:
            return None, None
        voice = matches[0][0]
        priority = ["id", "name", "slug", "legacy_persona_id", "alias"]
        kinds = {kind for _, kind in matches}
        return voice, next(kind for kind in priority if kind in kinds)

    def validate(self) -> None:
        ids: set[str] = set()
        exact_tokens: dict[str, str] = {}
        for voice in self.registry.get("voices", []):
            voice_id = voice.get("id", "")
            if not re.fullmatch(r"CV\d{3}", voice_id):
                raise ValueError(f"invalid voice id: {voice_id!r}")
            if voice_id in ids:
                raise ValueError(f"duplicate voice id: {voice_id}")
            ids.add(voice_id)
            for token, _ in self.tokens_for(voice):
                owner = exact_tokens.get(token)
                if owner and owner != voice_id:
                    raise ValueError(f"selector collision: {token!r} -> {owner}, {voice_id}")
                exact_tokens[token] = voice_id
        for key in ("default_voice_id", "fallback_voice_id"):
            if self.config.get(key) not in ids:
                raise ValueError(f"{key} is not present in registry")


STRUCTURED_FIELD = re.compile(
    r"(?im)^\s*(?:配音|音色|声线|旁白声音|voice)\s*[:：=]\s*(.+?)\s*$"
)
IMPERATIVE = re.compile(
    r"(?:请)?(?:改用|换成|指定|选择|使用|用)\s*[“\"「]?([^，。；;\n]{1,32}?)[”\"」]?\s*(?:来)?(?:配音|音色|声线|声音|旁白|解说|来讲|来配)"
)
REVERSED_IMPERATIVE = re.compile(
    r"(?:配音|音色|声线|旁白声音)\s*(?:请)?(?:改用|换成|指定|选择|使用|用)?\s*[“\"「]?([^，。；;\n]{1,32})"
)
NEGATIVE_PREFIX = re.compile(r"(?:不要|别用|禁止|不用|排除)\s*$")


def _positive_imperative_fragments(prompt: str) -> list[str]:
    values: list[str] = []
    for pattern in (IMPERATIVE, REVERSED_IMPERATIVE):
        for match in pattern.finditer(prompt):
            prefix = prompt[max(0, match.start() - 6) : match.start()]
            if NEGATIVE_PREFIX.search(prefix):
                continue
            values.append(match.group(1).strip())
    return values


def _selection(
    registry: VoiceRegistry,
    *,
    voice: dict,
    requested: str | None,
    reason: str,
    matched_by: str,
    fallback: bool,
    task_prompt: str | None,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "requested_voice": requested,
        "resolved_voice_id": voice["id"],
        "resolved_voice_name": voice["name"],
        "engine": voice["engine"],
        "resolution_reason": reason,
        "matched_by": matched_by,
        "fallback": fallback,
        "registry_sha256": registry.registry_sha256,
        "config_sha256": registry.config_sha256,
        "task_prompt_sha256": text_sha256(task_prompt) if task_prompt is not None else None,
    }


def default_selection(
    registry: VoiceRegistry,
    *,
    requested: str | None,
    reason: str,
    task_prompt: str | None = None,
) -> dict:
    voice = registry.by_id(registry.default_id)
    assert voice is not None
    return _selection(
        registry,
        voice=voice,
        requested=requested,
        reason=reason,
        matched_by="default",
        fallback=reason != "default_no_request",
        task_prompt=task_prompt,
    )


def resolve_selector(registry: VoiceRegistry, selector: str) -> dict:
    voice, matched_by = registry.exact_selector(selector)
    if voice is None:
        return default_selection(
            registry, requested=selector, reason="fallback_unmatched_selector"
        )
    return _selection(
        registry,
        voice=voice,
        requested=selector,
        reason="explicit_selector_match",
        matched_by=matched_by or "selector",
        fallback=False,
        task_prompt=None,
    )


def resolve_task_prompt(registry: VoiceRegistry, prompt: str) -> dict:
    fields = [value.strip() for value in STRUCTURED_FIELD.findall(prompt)]
    fragments = fields if fields else _positive_imperative_fragments(prompt)

    direct_ids = re.findall(r"(?i)\bCV\d{3}\b", prompt)
    if not fragments and direct_ids:
        fragments = direct_ids

    if not fragments:
        return default_selection(
            registry,
            requested=None,
            reason="default_no_request",
            task_prompt=prompt,
        )

    matches: dict[str, dict] = {}
    matched_by: set[str] = set()
    for fragment in fragments:
        found, kind = registry.match_fragment(fragment)
        for voice in found:
            matches[voice["id"]] = voice
        if kind:
            matched_by.add(kind)

    requested = " | ".join(fragments)
    if not matches:
        return default_selection(
            registry,
            requested=requested,
            reason="fallback_unmatched_prompt",
            task_prompt=prompt,
        )
    if len(matches) != 1:
        return default_selection(
            registry,
            requested=requested,
            reason="fallback_ambiguous_prompt",
            task_prompt=prompt,
        )
    voice = next(iter(matches.values()))
    priority = ["id", "name", "slug", "legacy_persona_id", "legacy_id", "alias"]
    match_kind = next((kind for kind in priority if kind in matched_by), "prompt")
    return _selection(
        registry,
        voice=voice,
        requested=requested,
        reason="explicit_prompt_match",
        matched_by=match_kind,
        fallback=False,
        task_prompt=prompt,
    )
