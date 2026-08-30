#!/usr/bin/env python3
"""Project-scoped character-voice registry and task-prompt resolver."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import unicodedata
from collections import Counter
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
    def preflight_id(self) -> str:
        return self.config["preflight_voice_id"]

    @property
    def random_pool_ids(self) -> list[str]:
        return list(self.config["random_voice_pool"])

    @property
    def random_pool(self) -> list[dict]:
        voices = {voice["id"]: voice for voice in self.voices}
        return [voices[voice_id] for voice_id in self.random_pool_ids]

    @property
    def decision_pool_ids(self) -> list[str]:
        return list(self.config.get("decision_voice_pool", self.random_pool_ids))

    @property
    def decision_pool(self) -> list[dict]:
        voices = {voice["id"]: voice for voice in self.voices}
        return [voices[voice_id] for voice_id in self.decision_pool_ids]

    @property
    def registry_sha256(self) -> str:
        return file_sha256(REGISTRY_PATH)

    @property
    def config_sha256(self) -> str:
        return file_sha256(CONFIG_PATH)

    def accepts_selection_hashes(self, selection: dict) -> bool:
        """Accept current hashes or an explicitly paired pre-migration selection."""

        pair = {
            "config_sha256": selection.get("config_sha256"),
            "registry_sha256": selection.get("registry_sha256"),
        }
        current = {
            "config_sha256": self.config_sha256,
            "registry_sha256": self.registry_sha256,
        }
        if pair == current:
            return True
        schema = selection.get("schema_version")
        for compatible in self.config.get("compatible_selection_hashes", []):
            compatible_pair = {
                "config_sha256": compatible.get("config_sha256"),
                "registry_sha256": compatible.get("registry_sha256"),
            }
            if pair != compatible_pair:
                continue
            versions = compatible.get("schema_versions", ["1.0.0"])
            return schema in versions
        return False

    def by_id(self, voice_id: str) -> dict | None:
        wanted = voice_id.upper()
        return next((voice for voice in self.voices if voice["id"] == wanted), None)

    def reference_text_for(self, voice: dict) -> str:
        """Return the transcript that exactly matches this voice's reference WAV."""

        return voice.get("reference_text", self.registry["reference_text"])

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
        default_reference_text = self.registry.get("reference_text")
        if self.registry.get("schema_version") is not None and (
            not isinstance(default_reference_text, str)
            or not default_reference_text.strip()
        ):
            raise ValueError("registry reference_text must be a non-empty string")
        ids: set[str] = set()
        exact_tokens: dict[str, str] = {}
        for voice in self.registry.get("voices", []):
            voice_id = voice.get("id", "")
            if not re.fullmatch(r"CV\d{3}", voice_id):
                raise ValueError(f"invalid voice id: {voice_id!r}")
            if voice_id in ids:
                raise ValueError(f"duplicate voice id: {voice_id}")
            ids.add(voice_id)
            reference_text = voice.get("reference_text")
            if reference_text is not None and (
                not isinstance(reference_text, str) or not reference_text.strip()
            ):
                raise ValueError(f"voice reference_text must be non-empty: {voice_id}")
            for token, _ in self.tokens_for(voice):
                owner = exact_tokens.get(token)
                if owner and owner != voice_id:
                    raise ValueError(f"selector collision: {token!r} -> {owner}, {voice_id}")
                exact_tokens[token] = voice_id
        enabled_ids = {voice["id"] for voice in self.voices}
        preflight_id = self.config.get("preflight_voice_id")
        if preflight_id not in enabled_ids:
            raise ValueError("preflight_voice_id is not an enabled registry voice")
        random_pool = self.config.get("random_voice_pool")
        if not isinstance(random_pool, list) or not random_pool:
            raise ValueError("random_voice_pool must be a non-empty list")
        if len(random_pool) != len(set(random_pool)):
            raise ValueError("random_voice_pool contains duplicate IDs")
        for voice_id in random_pool:
            if voice_id not in enabled_ids:
                raise ValueError(f"random_voice_pool contains unavailable voice: {voice_id}")
        decision_pool = self.config.get("decision_voice_pool", random_pool)
        if not isinstance(decision_pool, list) or not decision_pool:
            raise ValueError("decision_voice_pool must be a non-empty list")
        if len(decision_pool) != len(set(decision_pool)):
            raise ValueError("decision_voice_pool contains duplicate IDs")
        for voice_id in decision_pool:
            if voice_id not in enabled_ids:
                raise ValueError(f"decision_voice_pool contains unavailable voice: {voice_id}")
        if "decision_voice_pool" in self.config:
            if decision_pool != random_pool:
                raise ValueError("random_voice_pool must equal decision_voice_pool")
            for voice_id in decision_pool:
                voice = next(voice for voice in self.voices if voice["id"] == voice_id)
                profile = voice.get("decision_profile")
                if not isinstance(profile, dict):
                    raise ValueError(f"decision pool voice has no profile: {voice_id}")
                for key in ("emotion_tags", "best_for", "avoid_for"):
                    values = profile.get(key)
                    if (
                        not isinstance(values, list)
                        or not values
                        or any(not isinstance(value, str) or not value.strip() for value in values)
                    ):
                        raise ValueError(f"decision pool voice has invalid {key}: {voice_id}")
            expected_groups = self.config.get("decision_pool_expected_groups")
            if expected_groups is not None:
                actual_groups = Counter(
                    next(voice for voice in self.voices if voice["id"] == voice_id)["group"]
                    for voice_id in decision_pool
                )
                if dict(actual_groups) != expected_groups:
                    raise ValueError(
                        "decision_voice_pool group counts do not match decision_pool_expected_groups"
                    )
        compatible_pairs = self.config.get("compatible_selection_hashes", [])
        if not isinstance(compatible_pairs, list):
            raise ValueError("compatible_selection_hashes must be a list")
        for pair in compatible_pairs:
            if not isinstance(pair, dict) or set(pair) != {
                "config_sha256",
                "registry_sha256",
                "schema_versions",
            }:
                raise ValueError("compatible_selection_hashes contains an invalid pair")
            if any(
                not isinstance(value, str)
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                for key, value in pair.items()
                if key != "schema_versions"
            ):
                raise ValueError("compatible_selection_hashes contains an invalid digest")
            versions = pair["schema_versions"]
            if (
                not isinstance(versions, list)
                or not versions
                or any(version not in {"1.0.0", "1.1.0", "1.2.0"} for version in versions)
            ):
                raise ValueError("compatible_selection_hashes contains invalid schema versions")


STRUCTURED_FIELD = re.compile(
    r"(?im)^\s*(?:配音|音色|声线|旁白声音|voice)\s*[:：=]\s*(.+?)\s*$"
)
IMPERATIVE = re.compile(
    r"(?:请)?(?:改用|换成|指定|选择|使用|用)\s*[“\"「]?([^，。；;\n]{1,32}?)[”\"」]?\s*(?:来)?(?:配音|音色|声线|声音|旁白|解说|来讲|来配)"
)
REVERSED_IMPERATIVE = re.compile(
    r"(?:配音|音色|声线|旁白声音)\s*(?:请)?(?:改用|换成|指定|选择|使用|用)?\s*[“\"「]?([^，。；;\n]{1,32})"
)
POSITIVE_REPLACEMENT_START = r"(?:而是|(?:请\s*)?(?:改用|换成|指定|选择|使用|用))"
NEGATIVE_PREFIX = re.compile(
    r"(?:不要(?:了)?|别(?:再)?用?|禁止|不用|不使用|不想(?:使用|用)?|"
    r"拒绝(?:使用|用)?|不考虑|请\s*勿|勿用?|不能用?|不可用?|"
    r"并非|不是|排除|避免|除了?)\s*$"
)
NEGATIVE_PREFIX_CLAUSE = re.compile(
    r"(?:(?:我|这期|本期|这次)\s*)?(?:请\s*)?"
    r"(?:不要(?:了)?|别(?:再)?|禁止|不用|不使用|不想|拒绝|"
    r"不考虑|勿|不能|不可|并非|不是|排除|避免|除了?)\s*"
    r"(?:再\s*)?(?:使用|用|选择|指定|换成|改用)?\s*"
    rf"(?:(?![，,。；;\n]|{POSITIVE_REPLACEMENT_START}\s)[^，,。；;\n])*"
)
NEGATIVE_POSTFIX_CLAUSE = re.compile(
    r"(?i)\b(?:CV\d{3}|kokoro:[a-z0-9_]+)\b\s*"
    r"(?:也\s*)?(?:不要(?:了)?|别用|不用|不使用|不考虑|不能用|不可用|不行|除外)"
)
NEGATIVE_NAMED_POSTFIX_CLAUSE = re.compile(
    r"[A-Za-z_\-\u3400-\u9fff]{2,32}\s*(?:也\s*)?(?:不考虑|不要了)"
)
POSITIVE_REPLACEMENT = re.compile(
    r"(?:而是|(?:请\s*)?(?:改用|换成))\s*[“\"「]?"
    r"([^，。；;\n]{1,32}?)[”\"」]?\s*"
    r"(?:(?:来)?(?:配音|音色|声线|声音|旁白|解说|来讲|来配))?"
    r"(?=$|[，,。；;\n])"
)


def _without_negative_clauses(value: str) -> str:
    """Mask negative voice clauses before any selector or bare-ID matching."""

    # Postfix forms must be removed first. Otherwise the prefix grammar can
    # consume only the trailing marker (for example ``除外``) and leave its
    # rejected selector behind as a false positive.
    value = NEGATIVE_POSTFIX_CLAUSE.sub(" ", value)
    value = NEGATIVE_NAMED_POSTFIX_CLAUSE.sub(" ", value)
    return NEGATIVE_PREFIX_CLAUSE.sub(" ", value)


def _positive_imperative_fragments(prompt: str) -> list[str]:
    values: list[str] = []
    for pattern in (POSITIVE_REPLACEMENT, IMPERATIVE, REVERSED_IMPERATIVE):
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
    selection_mode: str,
    candidate_voice_ids: list[str],
    model_decision_reason: str | None,
    model_decision_confidence: str | None,
) -> dict:
    return {
        "schema_version": "1.2.0",
        "requested_voice": requested,
        "resolved_voice_id": voice["id"],
        "resolved_voice_name": voice["name"],
        "engine": voice["engine"],
        "resolution_reason": reason,
        "matched_by": matched_by,
        "fallback": fallback,
        "selection_mode": selection_mode,
        "candidate_voice_ids": candidate_voice_ids,
        "model_decision_reason": model_decision_reason,
        "model_decision_confidence": model_decision_confidence,
        "registry_sha256": registry.registry_sha256,
        "config_sha256": registry.config_sha256,
        "task_prompt_sha256": text_sha256(task_prompt) if task_prompt is not None else None,
    }


def random_pool_selection(
    registry: VoiceRegistry,
    *,
    requested: str | None,
    reason: str,
    task_prompt: str | None = None,
    model_decision_reason: str | None = None,
) -> dict:
    candidates = registry.random_pool
    voice = secrets.choice(candidates)
    return _selection(
        registry,
        voice=voice,
        requested=requested,
        reason=reason,
        matched_by="random_pool",
        fallback=reason != "default_no_request",
        task_prompt=task_prompt,
        selection_mode="random_pool",
        candidate_voice_ids=[candidate["id"] for candidate in candidates],
        model_decision_reason=model_decision_reason
        or "模型未提供可用的作品情绪判断，按标准十声线池随机兜底。",
        model_decision_confidence="low",
    )


def model_decision_or_random(
    registry: VoiceRegistry,
    *,
    requested: str | None,
    task_prompt: str | None,
    model_choice: str | None,
    model_reason: str | None,
    model_confidence: str | None,
) -> dict:
    reason = model_reason.strip() if isinstance(model_reason, str) else ""
    confidence = (
        model_confidence.strip().lower()
        if isinstance(model_confidence, str)
        else None
    )
    voice = None
    if isinstance(model_choice, str) and model_choice.strip():
        voice, _ = registry.exact_selector(model_choice)
    if (
        voice is not None
        and voice["id"] in registry.decision_pool_ids
        and reason
        and confidence in {"high", "medium"}
    ):
        return _selection(
            registry,
            voice=voice,
            requested=requested,
            reason="model_emotion_match",
            matched_by="model_decision",
            fallback=False,
            task_prompt=task_prompt,
            selection_mode="model_decision",
            candidate_voice_ids=registry.decision_pool_ids,
            model_decision_reason=reason,
            model_decision_confidence=confidence,
        )
    fallback_reason = reason or "作品信息不足，模型无法可靠判断整体情绪与叙事表达。"
    return random_pool_selection(
        registry,
        requested=requested,
        reason="fallback_model_unavailable",
        task_prompt=task_prompt,
        model_decision_reason=fallback_reason,
    )


def resolve_selector(registry: VoiceRegistry, selector: str) -> dict:
    voice, matched_by = registry.exact_selector(selector)
    if voice is None:
        return random_pool_selection(
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
        selection_mode="explicit",
        candidate_voice_ids=[voice["id"]],
        model_decision_reason=None,
        model_decision_confidence=None,
    )


def resolve_task_prompt(
    registry: VoiceRegistry,
    prompt: str,
    *,
    model_choice: str | None = None,
    model_reason: str | None = None,
    model_confidence: str | None = None,
) -> dict:
    fields = [
        _without_negative_clauses(value).strip()
        for value in STRUCTURED_FIELD.findall(prompt)
    ]
    fields = [
        value
        for value in fields
        if re.search(r"[A-Za-z0-9\u3400-\u9fff]", value)
    ]
    # Remove complete structured lines before examining prose. A fully masked
    # negative field otherwise leaves a bare "配音：" label that the reversed
    # imperative grammar could mistake for an unmatched positive request.
    body_prompt = STRUCTURED_FIELD.sub("", prompt)
    positive_prompt = _without_negative_clauses(body_prompt)
    fragments = fields if fields else _positive_imperative_fragments(positive_prompt)

    # Direct IDs are only a last-resort positive signal. Read them from the
    # negation-masked prompt so "不要使用 CV004" cannot re-enter here after
    # the imperative parser correctly ignored it.
    direct_ids = re.findall(r"(?i)\bCV\d{3}\b", positive_prompt)
    if not fragments and direct_ids:
        fragments = direct_ids

    if not fragments:
        return model_decision_or_random(
            registry,
            requested=None,
            task_prompt=prompt,
            model_choice=model_choice,
            model_reason=model_reason,
            model_confidence=model_confidence,
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
        return model_decision_or_random(
            registry,
            requested=requested,
            task_prompt=prompt,
            model_choice=model_choice,
            model_reason=model_reason,
            model_confidence=model_confidence,
        )
    if len(matches) != 1:
        return model_decision_or_random(
            registry,
            requested=requested,
            task_prompt=prompt,
            model_choice=model_choice,
            model_reason=model_reason,
            model_confidence=model_confidence,
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
        selection_mode="explicit",
        candidate_voice_ids=[voice["id"]],
        model_decision_reason=None,
        model_decision_confidence=None,
    )
