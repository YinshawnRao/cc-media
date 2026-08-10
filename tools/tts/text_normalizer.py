#!/usr/bin/env python3
"""Normalize Latin words and initialisms before Qwen TTS generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parent
POLICY_PATH = TTS_ROOT / "pronunciation.json"
SEPARATED_INITIALISM = re.compile(
    r"(?<![A-Za-z0-9])((?:[A-Za-z]\s*[.\-]\s*){2,}[A-Za-z]\.?)"
    r"(?![A-Za-z0-9])"
)
ALL_CAPS_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])([A-Z]{2,}(?:[0-9]+)?(?:['’][A-Z]+)?)(?![A-Za-z0-9])"
)
VOWELS = frozenset("AEIOUY")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class PronunciationPolicy:
    policy_id: str
    policy_sha256: str
    literal_overrides: dict[str, str]
    letter_initialisms: frozenset[str]
    short_words: frozenset[str]

    @classmethod
    def load(cls, path: Path = POLICY_PATH) -> "PronunciationPolicy":
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema_version") != "1.0.0":
            raise ValueError(f"unsupported pronunciation schema: {value.get('schema_version')}")
        policy_id = value.get("policy_id")
        if not isinstance(policy_id, str) or not policy_id:
            raise ValueError("pronunciation policy_id is required")
        literal = value.get("literal_overrides")
        if not isinstance(literal, dict) or not all(
            isinstance(key, str) and key and isinstance(spoken, str) and spoken
            for key, spoken in literal.items()
        ):
            raise ValueError("literal_overrides must map non-empty strings to strings")
        initials = value.get("letter_initialisms")
        short_words = value.get("short_words")
        if not isinstance(initials, list) or not all(isinstance(item, str) for item in initials):
            raise ValueError("letter_initialisms must be a string array")
        if not isinstance(short_words, list) or not all(
            isinstance(item, str) for item in short_words
        ):
            raise ValueError("short_words must be a string array")
        return cls(
            policy_id=policy_id,
            policy_sha256=sha256_file(path),
            literal_overrides={key.upper(): spoken for key, spoken in literal.items()},
            letter_initialisms=frozenset(item.upper() for item in initials),
            short_words=frozenset(item.upper() for item in short_words),
        )


@dataclass(frozen=True)
class NormalizedText:
    source_text: str
    normalized_text: str
    policy_id: str
    policy_sha256: str
    decisions: tuple[dict, ...]

    @property
    def changed(self) -> bool:
        return self.source_text != self.normalized_text

    def metadata(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "policy_sha256": self.policy_sha256,
            "changed": self.changed,
            "decisions": list(self.decisions),
        }

    def as_dict(self) -> dict:
        return {
            "source_text": self.source_text,
            "normalized_text": self.normalized_text,
            **self.metadata(),
        }


def _boundary_pattern(token: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


def _letters(value: str) -> str:
    return " ".join(re.findall(r"[A-Za-z0-9]", value.upper()))


def _word_case(value: str) -> str:
    return value[0].upper() + value[1:].lower()


def _looks_like_word(token: str, policy: PronunciationPolicy) -> bool:
    letters = "".join(re.findall(r"[A-Z]", token.upper()))
    if letters in policy.short_words:
        return True
    if len(letters) < 4:
        return False
    # ABCD-style alphabet runs are labels/placeholders, not pronounceable
    # English words. Catch both ascending and descending runs before the broad
    # vowel heuristic; registered words/initialisms still take precedence.
    steps = [ord(right) - ord(left) for left, right in zip(letters, letters[1:])]
    if steps and (
        all(step == 1 for step in steps) or all(step == -1 for step in steps)
    ):
        return False
    return any(letter in VOWELS for letter in letters)


def validate_overrides(value: object, label: str = "pronunciation overrides") -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(
        isinstance(key, str)
        and key.strip()
        and isinstance(spoken, str)
        and spoken.strip()
        for key, spoken in value.items()
    ):
        raise ValueError(f"{label} must map non-empty source strings to spoken strings")
    return {key.strip(): spoken.strip() for key, spoken in value.items()}


def parse_override_args(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"pronunciation override needs SOURCE=SPOKEN: {value}")
        source, spoken = value.split("=", 1)
        source = source.strip()
        spoken = spoken.strip()
        if not source or not spoken:
            raise ValueError(f"pronunciation override needs SOURCE=SPOKEN: {value}")
        result[source] = spoken
    return result


def normalize_tts_text(
    text: str,
    *,
    policy: PronunciationPolicy | None = None,
    overrides: dict[str, str] | None = None,
) -> NormalizedText:
    policy = policy or PronunciationPolicy.load()
    project_overrides = validate_overrides(overrides)
    decisions: list[dict] = []
    normalized = text

    literal_overrides = dict(policy.literal_overrides)
    literal_overrides.update(project_overrides)
    for source, spoken in sorted(literal_overrides.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = _boundary_pattern(source)
        normalized, count = pattern.subn(spoken, normalized)
        if count:
            decisions.append(
                {
                    "source": source,
                    "spoken": spoken,
                    "mode": "project_override" if source in project_overrides else "literal_override",
                    "count": count,
                }
            )

    def replace_separated(match: re.Match[str]) -> str:
        source = match.group(1)
        spoken = _letters(source)
        decisions.append(
            {
                "source": source,
                "spoken": spoken,
                "mode": "explicit_initialism",
                "count": 1,
            }
        )
        return spoken

    normalized = SEPARATED_INITIALISM.sub(replace_separated, normalized)

    def replace_all_caps(match: re.Match[str]) -> str:
        source = match.group(1)
        upper = source.upper()
        if upper in policy.letter_initialisms or not _looks_like_word(source, policy):
            spoken = _letters(source)
            mode = "letter_initialism" if upper in policy.letter_initialisms else "nonword_letters"
        else:
            spoken = _word_case(source)
            mode = "word_candidate"
        decisions.append(
            {
                "source": source,
                "spoken": spoken,
                "mode": mode,
                "count": 1,
            }
        )
        return spoken

    normalized = ALL_CAPS_TOKEN.sub(replace_all_caps, normalized)
    return NormalizedText(
        source_text=text,
        normalized_text=normalized,
        policy_id=policy.policy_id,
        policy_sha256=policy.policy_sha256,
        decisions=tuple(decisions),
    )


def read_input(value: str) -> str:
    candidate = Path(value)
    try:
        is_file = candidate.is_file()
    except OSError:
        is_file = False
    return candidate.read_text(encoding="utf-8").strip() if is_file else value.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="literal text or UTF-8 text file")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="SOURCE=SPOKEN",
        help="exact project pronunciation override; repeatable",
    )
    parser.add_argument("--json", action="store_true", help="print decisions as JSON")
    args = parser.parse_args()
    try:
        overrides = parse_override_args(args.override)
    except ValueError as exc:
        parser.error(str(exc))
    result = normalize_tts_text(read_input(args.input), overrides=overrides)
    print(
        json.dumps(result.as_dict(), ensure_ascii=False, indent=2)
        if args.json
        else result.normalized_text
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
