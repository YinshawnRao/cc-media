"""Pure helpers that define the stable Qwen request/cache identity contract."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import PurePosixPath


QWEN_SIDECAR_COMMON_FIELDS = frozenset(
    {
        "schema_version",
        "item_id",
        "text",
        "text_sha256",
        "selection",
        "resolved_voice_id",
        "engine",
        "model_id",
        "model_revision",
        "model_tree_sha256",
        "model_validation",
        "reference_audio",
        "reference_sha256",
        "language",
        "speed",
        "seed",
        "generation_seconds",
        "model_load_seconds",
        "model_metrics",
        "fingerprint",
        "fingerprint_inputs",
        "output",
        "output_sha256",
        "wav",
    }
)
QWEN_SIDECAR_NORMALIZATION_FIELDS = frozenset(
    {"source_text", "normalized_text", "text_normalization"}
)
QWEN_FINGERPRINT_COMMON_FIELDS = (
    "engine",
    "model_id",
    "model_revision",
    "model_tree_sha256",
    "mlx_audio_version",
    "voice_id",
    "selection",
    "reference_sha256",
    "reference_text",
    "text",
    "language",
    "speed",
    "generation",
)
QWEN_WAV_FIELDS = frozenset(
    {"channels", "sample_rate_hz", "sample_width_bytes", "frames", "duration_seconds"}
)
QWEN_MODEL_METRIC_FIELDS = frozenset(
    {"processing_seconds", "peak_memory_gb", "token_count"}
)
QWEN_NORMALIZATION_FIELDS = frozenset(
    {"policy_id", "policy_sha256", "changed", "decisions"}
)
QWEN_NORMALIZATION_DECISION_FIELDS = frozenset(
    {"source", "spoken", "mode", "count"}
)
QWEN_NORMALIZATION_MODES = frozenset(
    {
        "project_override",
        "literal_override",
        "explicit_initialism",
        "letter_initialism",
        "nonword_letters",
        "word_candidate",
    }
)
VOICE_SELECTION_FIELDS = frozenset(
    {
        "schema_version",
        "requested_voice",
        "resolved_voice_id",
        "resolved_voice_name",
        "engine",
        "resolution_reason",
        "matched_by",
        "fallback",
        "registry_sha256",
        "config_sha256",
        "task_prompt_sha256",
    }
)
VOICE_SELECTION_REASONS = frozenset(
    {
        "default_no_request",
        "fallback_unmatched_selector",
        "explicit_selector_match",
        "fallback_unmatched_prompt",
        "fallback_ambiguous_prompt",
        "explicit_prompt_match",
    }
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


MODEL_VALIDATION_CACHE_KEYS = (
    "portable_claim_kind",
    "verification_kind",
    "model_id",
    "model_revision",
    "qwen_config_sha256",
    "manifest_sha256",
    "verified_model_tree_sha256",
    "model_file_count",
    "model_total_bytes",
    "mlx_audio_version",
    "portable_claim_sha256",
    "full_tree_hash_verified",
)
QWEN_MODEL_VALIDATION_FIELDS = frozenset(
    set(MODEL_VALIDATION_CACHE_KEYS) | {"receipt_sha256"}
)


def fingerprint(value: dict) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def derived_seed(base: int, voice_id: str, text: str, language: str) -> int:
    payload = f"{base}\0{voice_id}\0{language}\0{text}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def model_validation_cache_matches(sidecar: object, current: dict) -> bool:
    """Return whether cached audio carries the current portable model claim.

    The raw receipt hash is generation-machine audit metadata, so it must be a
    valid digest but need not equal the current workstation's receipt hash.
    """

    if not isinstance(sidecar, dict):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", str(sidecar.get("receipt_sha256", ""))):
        return False
    return all(sidecar.get(key) == current.get(key) for key in MODEL_VALIDATION_CACHE_KEYS)


def fingerprint_inputs(
    *,
    qwen: dict,
    selection: dict,
    voice_id: str,
    reference_sha256: str,
    reference_text: str,
    item: dict,
    language: str,
    speed: float,
) -> dict:
    """Build the historical fingerprint shape; do not add receipt metadata here."""

    value = {
        "engine": qwen["engine"],
        "model_id": qwen["model_id"],
        "model_revision": qwen["model_revision"],
        "model_tree_sha256": qwen["model_tree_sha256"],
        "mlx_audio_version": qwen["mlx_audio_version"],
        "voice_id": voice_id,
        "selection": selection,
        "reference_sha256": reference_sha256,
        "reference_text": reference_text,
        "text": item["text"],
        "language": language,
        "speed": speed,
        "generation": qwen["generation"],
    }
    if "source_text" in item:
        value["source_text"] = item["source_text"]
        value["text_normalization"] = item["text_normalization"]
    return value


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _digest(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _field_set_errors(value: object, expected: frozenset[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"Qwen sidecar contract {label} must be an object"]
    actual = set(value)
    errors: list[str] = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(
            f"Qwen sidecar contract {label} is missing fields: {', '.join(missing)}"
        )
    if extra:
        errors.append(
            f"Qwen sidecar contract {label} has unexpected fields: {', '.join(extra)}"
        )
    return errors


def _selection_contract_errors(
    selection: object,
    *,
    qwen: dict,
    voice_id: str,
    voice_name: str,
) -> list[str]:
    errors = _field_set_errors(selection, VOICE_SELECTION_FIELDS, "selection")
    if not isinstance(selection, dict):
        return errors
    if selection.get("schema_version") != "1.0.0":
        errors.append("Qwen sidecar contract selection schema_version must be 1.0.0")
    requested = selection.get("requested_voice")
    if requested is not None and (not isinstance(requested, str) or not requested.strip()):
        errors.append(
            "Qwen sidecar contract selection requested_voice must be null or a non-empty string"
        )
    if selection.get("resolved_voice_id") != voice_id:
        errors.append("Qwen sidecar contract selection resolved_voice_id is inconsistent")
    if selection.get("resolved_voice_name") != voice_name:
        errors.append("Qwen sidecar contract selection resolved_voice_name is inconsistent")
    if selection.get("engine") != qwen.get("engine"):
        errors.append("Qwen sidecar contract selection engine is inconsistent")
    reason = selection.get("resolution_reason")
    if reason not in VOICE_SELECTION_REASONS:
        errors.append("Qwen sidecar contract selection resolution_reason is invalid")
    fallback = selection.get("fallback")
    if not isinstance(fallback, bool):
        errors.append("Qwen sidecar contract selection fallback must be boolean")
    elif isinstance(reason, str) and fallback != reason.startswith("fallback_"):
        errors.append("Qwen sidecar contract selection fallback contradicts resolution_reason")
    matched_by = selection.get("matched_by")
    if not isinstance(matched_by, str) or not matched_by.strip():
        errors.append("Qwen sidecar contract selection matched_by must be non-empty")
    for key in ("registry_sha256", "config_sha256"):
        if not _digest(selection.get(key)):
            errors.append(f"Qwen sidecar contract selection {key} is invalid")
    prompt_hash = selection.get("task_prompt_sha256")
    if prompt_hash is not None and not _digest(prompt_hash):
        errors.append("Qwen sidecar contract selection task_prompt_sha256 is invalid")
    return errors


def _normalization_contract_errors(value: object) -> list[str]:
    errors = _field_set_errors(
        value, QWEN_NORMALIZATION_FIELDS, "text_normalization"
    )
    if not isinstance(value, dict):
        return errors
    policy_id = value.get("policy_id")
    if not isinstance(policy_id, str) or not policy_id.strip():
        errors.append("Qwen sidecar contract text_normalization policy_id is invalid")
    if not _digest(value.get("policy_sha256")):
        errors.append("Qwen sidecar contract text_normalization policy_sha256 is invalid")
    if value.get("changed") is not True:
        errors.append("Qwen sidecar contract text_normalization changed must be true")
    decisions = value.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        errors.append("Qwen sidecar contract text_normalization decisions must be non-empty")
        return errors
    for index, decision in enumerate(decisions):
        label = f"text_normalization.decisions[{index}]"
        errors.extend(
            _field_set_errors(decision, QWEN_NORMALIZATION_DECISION_FIELDS, label)
        )
        if not isinstance(decision, dict):
            continue
        for key in ("source", "spoken"):
            candidate = decision.get(key)
            if not isinstance(candidate, str) or not candidate:
                errors.append(f"Qwen sidecar contract {label}.{key} is invalid")
        if decision.get("mode") not in QWEN_NORMALIZATION_MODES:
            errors.append(f"Qwen sidecar contract {label}.mode is invalid")
        count = decision.get("count")
        if not _is_int(count) or count <= 0:
            errors.append(f"Qwen sidecar contract {label}.count is invalid")
    return errors


def qwen_sidecar_contract_errors(
    sidecar: object,
    *,
    qwen: dict,
    selection: dict,
    voice: dict,
    reference_text: str,
    expected_output_name: str,
    actual_output_sha256: str,
    actual_wav: dict,
) -> tuple[str, ...]:
    """Recompute the canonical Qwen worker sidecar contract.

    This detects incomplete, stale, and internally contradictory evidence.  It
    deliberately does not claim that a same-UID attacker could not replace both
    the WAV and every JSON/hash field; that trust boundary is documented by the
    caller-facing gate.
    """

    if not isinstance(sidecar, dict):
        return ("Qwen sidecar contract must be an object",)
    errors: list[str] = []
    schema = sidecar.get("schema_version")
    if schema == "1.0.0":
        expected_fields = QWEN_SIDECAR_COMMON_FIELDS
        normalized = False
    elif schema == "1.1.0":
        expected_fields = QWEN_SIDECAR_COMMON_FIELDS | QWEN_SIDECAR_NORMALIZATION_FIELDS
        normalized = True
    else:
        errors.append(
            f"Qwen sidecar contract schema_version is unsupported: {schema!r}"
        )
        expected_fields = QWEN_SIDECAR_COMMON_FIELDS
        normalized = False
    errors.extend(_field_set_errors(sidecar, expected_fields, "root"))

    voice_id = voice.get("id")
    voice_name = voice.get("name")
    errors.extend(
        _selection_contract_errors(
            selection,
            qwen=qwen,
            voice_id=str(voice_id),
            voice_name=str(voice_name),
        )
    )
    if sidecar.get("selection") != selection:
        errors.append("Qwen sidecar contract selection does not match the project selection")
    if sidecar.get("resolved_voice_id") != voice_id:
        errors.append("Qwen sidecar contract resolved_voice_id is inconsistent")

    expected_scalars = {
        "engine": qwen.get("engine"),
        "model_id": qwen.get("model_id"),
        "model_revision": qwen.get("model_revision"),
        "model_tree_sha256": qwen.get("model_tree_sha256"),
        "reference_audio": str(PurePosixPath("voices") / str(voice.get("reference_audio"))),
        "reference_sha256": voice.get("reference_sha256"),
    }
    for key, expected in expected_scalars.items():
        if sidecar.get(key) != expected:
            errors.append(f"Qwen sidecar contract {key} is inconsistent")

    item_id = sidecar.get("item_id")
    if not isinstance(item_id, str) or not item_id.strip():
        errors.append("Qwen sidecar contract item_id must be a non-empty string")
    text = sidecar.get("text")
    if not isinstance(text, str) or not text:
        errors.append("Qwen sidecar contract text must be a non-empty string")
        text = ""
    expected_text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if sidecar.get("text_sha256") != expected_text_sha:
        errors.append("Qwen sidecar contract text_sha256 is inconsistent")

    language = sidecar.get("language")
    if not isinstance(language, str) or not language.strip():
        errors.append("Qwen sidecar contract language must be a non-empty string")
        language = ""
    speed = sidecar.get("speed")
    if not isinstance(speed, float) or not math.isfinite(speed) or not 0.5 <= speed <= 2.0:
        errors.append("Qwen sidecar contract speed must be a finite JSON float from 0.5 to 2.0")
        speed_for_contract = 0.0
    else:
        speed_for_contract = speed

    seed = sidecar.get("seed")
    expected_seed = derived_seed(
        int(qwen.get("generation", {}).get("seed", 0)),
        str(voice_id),
        text,
        language,
    )
    if not _is_int(seed) or seed != expected_seed:
        errors.append("Qwen sidecar contract seed is inconsistent")

    for key in ("generation_seconds", "model_load_seconds"):
        value = sidecar.get(key)
        if not _is_finite_number(value) or float(value) < 0:
            errors.append(f"Qwen sidecar contract {key} must be finite and non-negative")

    metrics = sidecar.get("model_metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append("Qwen sidecar contract model_metrics must be a non-empty array")
    else:
        for index, metric in enumerate(metrics):
            label = f"model_metrics[{index}]"
            errors.extend(_field_set_errors(metric, QWEN_MODEL_METRIC_FIELDS, label))
            if not isinstance(metric, dict):
                continue
            for key in ("processing_seconds", "peak_memory_gb"):
                value = metric.get(key)
                if value is not None and (
                    not _is_finite_number(value) or float(value) < 0
                ):
                    errors.append(f"Qwen sidecar contract {label}.{key} is invalid")
            token_count = metric.get("token_count")
            if token_count is not None and (
                not _is_int(token_count) or token_count < 0
            ):
                errors.append(f"Qwen sidecar contract {label}.token_count is invalid")

    validation = sidecar.get("model_validation")
    errors.extend(
        _field_set_errors(
            validation, QWEN_MODEL_VALIDATION_FIELDS, "model_validation"
        )
    )
    if isinstance(validation, dict):
        for key in (
            "qwen_config_sha256",
            "manifest_sha256",
            "verified_model_tree_sha256",
            "portable_claim_sha256",
            "receipt_sha256",
        ):
            if not _digest(validation.get(key)):
                errors.append(f"Qwen sidecar contract model_validation.{key} is invalid")
        for key in ("model_file_count", "model_total_bytes"):
            value = validation.get(key)
            if not _is_int(value) or value <= 0:
                errors.append(f"Qwen sidecar contract model_validation.{key} is invalid")
        if validation.get("full_tree_hash_verified") is not True:
            errors.append(
                "Qwen sidecar contract model_validation.full_tree_hash_verified must be true"
            )

    item = {"text": text}
    if normalized:
        source_text = sidecar.get("source_text")
        normalized_text = sidecar.get("normalized_text")
        normalization = sidecar.get("text_normalization")
        if not isinstance(source_text, str) or not source_text:
            errors.append("Qwen sidecar contract source_text must be non-empty")
            source_text = ""
        if normalized_text != text:
            errors.append("Qwen sidecar contract normalized_text must equal text")
        if source_text == text:
            errors.append("Qwen sidecar contract normalized source_text must differ from text")
        errors.extend(_normalization_contract_errors(normalization))
        item.update(
            {
                "source_text": source_text,
                "text_normalization": normalization,
            }
        )

    expected_inputs = fingerprint_inputs(
        qwen=qwen,
        selection=selection,
        voice_id=str(voice_id),
        reference_sha256=str(voice.get("reference_sha256")),
        reference_text=reference_text,
        item=item,
        language=language,
        speed=speed_for_contract,
    )
    actual_inputs = sidecar.get("fingerprint_inputs")
    expected_input_fields = frozenset(QWEN_FINGERPRINT_COMMON_FIELDS)
    if normalized:
        expected_input_fields |= frozenset({"source_text", "text_normalization"})
    errors.extend(
        _field_set_errors(actual_inputs, expected_input_fields, "fingerprint_inputs")
    )
    if actual_inputs != expected_inputs:
        errors.append("Qwen sidecar contract fingerprint_inputs are inconsistent")
    expected_fingerprint = fingerprint(expected_inputs)
    if sidecar.get("fingerprint") != expected_fingerprint:
        errors.append("Qwen sidecar contract fingerprint is inconsistent")

    output = sidecar.get("output")
    if output != expected_output_name:
        errors.append(
            "Qwen sidecar contract output must be the adjacent WAV filename"
        )
    if sidecar.get("output_sha256") != actual_output_sha256:
        errors.append("Qwen sidecar contract output_sha256 is inconsistent")

    wav = sidecar.get("wav")
    errors.extend(_field_set_errors(wav, QWEN_WAV_FIELDS, "wav"))
    if isinstance(wav, dict):
        if wav != actual_wav:
            errors.append("Qwen sidecar contract wav metadata does not match the WAV")
        if (
            wav.get("channels") != 1
            or wav.get("sample_rate_hz") != qwen.get("sample_rate_hz")
            or wav.get("sample_width_bytes") != 2
            or not _is_int(wav.get("frames"))
            or wav.get("frames", 0) <= 0
            or not _is_finite_number(wav.get("duration_seconds"))
            or float(wav.get("duration_seconds", 0)) <= 0
        ):
            errors.append("Qwen sidecar contract wav format is invalid")

    return tuple(errors)
