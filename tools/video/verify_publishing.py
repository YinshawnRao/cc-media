#!/usr/bin/env python3
"""Validate the project-local Xiaohongshu publishing-copy contract.

The fixed input is ``publishing/xiaohongshu.md`` under one project.  This gate
checks deterministic structure, body length, emoji absence, hashtag quality
boundaries, explicit song-title leakage and a minimum project-relevance signal.
It does not judge whether a title will become viral or whether the prose is
aesthetically strong.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn


MANIFEST_PATH = "project-manifest.json"
SUPPORTED_PROJECT_SCHEMA_VERSIONS = frozenset({1, 2})
PUBLISHING_PATH = "publishing/xiaohongshu.md"
DOCUMENT_TITLE = "# 小红书发布文案"
TITLES_HEADING = "## 标题候选（第一条为首选）"
BODY_HEADING = "## 正文"
TITLE_BULLET_RE = re.compile(r"^-\s+(.+?)\s*$")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+")
HASHTAG_RE = re.compile(r"#[^\s#]+")
THEME_SPLIT_RE = re.compile(r"[\n|｜/／,，;；:：!！?？。·•—–]+")
PERFORMER_SPLIT_RE = re.compile(
    r"(?:\s*(?:、|/|／|&|＆|,|，|;|；|\+|＋|×)\s*|"
    r"\s+(?:feat\.?|ft\.?|featuring|with|x)\s+)",
    re.IGNORECASE,
)
GENERIC_COVER_TERMS = frozenset(
    {
        "top",
        "top5",
        "bgm",
        "音乐",
        "歌曲",
        "主题曲",
        "盘点",
        "视频",
        "五首",
        "5首",
        "前奏",
        "进化史",
        "最难",
        "最被低估",
    }
)
MIN_PROSE_NONSPACE_CHARACTERS = 420
MAX_PROSE_NONSPACE_CHARACTERS = 900
MIN_HASHTAGS = 8
MAX_HASHTAGS = 10
EMOJI_RANGES = (
    (0x2600, 0x27BF),
    (0x1F000, 0x1FAFF),
)


class PublishingError(ValueError):
    """A deterministic publishing-copy validation failure."""


@dataclass(frozen=True)
class PublishingDocument:
    titles: tuple[str, ...]
    body: str
    hashtags: tuple[str, ...]

    @property
    def outward_text(self) -> str:
        return "\n".join((*self.titles, self.body))


@dataclass(frozen=True)
class PublishingSummary:
    path: str
    title_count: int
    hashtag_count: int
    relevance_kind: str
    relevance_value: str


def fail(message: str) -> NoReturn:
    raise PublishingError(message)


def compact_text(value: str) -> str:
    """Normalize compatibility, case, whitespace and punctuation variants."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def normalized_surface(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def contains_emoji(value: str) -> bool:
    for character in value:
        codepoint = ord(character)
        if codepoint in (0x20E3, 0xFE0F) or any(
            start <= codepoint <= end for start, end in EMOJI_RANGES
        ):
            return True
    return False


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def strict_json(path: Path, label: str) -> dict[str, Any]:
    def finite_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number {token}")
        return value

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard numeric constant {token}")
            ),
            object_pairs_hook=reject_duplicate_json_keys,
            parse_float=finite_float,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        fail(f"{label} is not strict JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{label} must contain a JSON object")
    return value


def real_project_root(project: Path) -> Path:
    logical = Path(os.path.abspath(project))
    try:
        resolved = logical.resolve(strict=True)
        info = logical.lstat()
    except OSError as exc:
        fail(f"cannot inspect project root: {exc}")
    if resolved != logical:
        fail("project root or one of its parents must not be a symlink")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        fail("project root must be a real directory, not a symlink")
    return logical


def project_file(project: Path, relative_path: str, label: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        fail(f"{label} must use a project-relative path without '..'")
    candidate = project / relative
    cursor = project
    for part in relative.parent.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            fail(f"{label} parent must not be a symlink: {relative.parent.as_posix()}")
    if candidate.is_symlink():
        fail(f"{label} must not be a symlink: {relative_path}")
    try:
        info = candidate.lstat()
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(project)
    except FileNotFoundError:
        fail(f"{label} is missing: {relative_path}")
    except (OSError, ValueError) as exc:
        fail(f"cannot inspect {label}: {exc}")
    if not stat.S_ISREG(info.st_mode):
        fail(f"{label} must be a regular file: {relative_path}")
    return candidate


def parse_markdown(text: str) -> PublishingDocument:
    lines = text.splitlines()
    nonempty = [index for index, line in enumerate(lines) if line.strip()]
    if not nonempty:
        fail("publishing copy is empty")
    if lines[nonempty[0]].strip() != DOCUMENT_TITLE:
        fail(f"first non-empty line must be {DOCUMENT_TITLE!r}")

    required = (DOCUMENT_TITLE, TITLES_HEADING, BODY_HEADING)
    for heading in required:
        occurrences = [index for index, line in enumerate(lines) if line.strip() == heading]
        if len(occurrences) != 1:
            fail(f"publishing copy must contain exactly one {heading!r}")
    document_index = next(
        index for index, line in enumerate(lines) if line.strip() == DOCUMENT_TITLE
    )
    titles_index = next(
        index for index, line in enumerate(lines) if line.strip() == TITLES_HEADING
    )
    body_index = next(index for index, line in enumerate(lines) if line.strip() == BODY_HEADING)
    if not document_index < titles_index < body_index:
        fail("Markdown sections must be ordered as document title, title candidates, body")
    if any(line.strip() for line in lines[document_index + 1 : titles_index]):
        fail("unexpected content before the title-candidate section")

    titles: list[str] = []
    for line in lines[titles_index + 1 : body_index]:
        if not line.strip():
            continue
        match = TITLE_BULLET_RE.fullmatch(line.strip())
        if match is None:
            fail("title candidates must contain only '- <title>' Markdown bullets")
        title = match.group(1).strip()
        if not title:
            fail("title candidates must not be empty")
        titles.append(title)
    if not 1 <= len(titles) <= 5:
        fail(f"title candidates must contain 1-5 entries, got {len(titles)}")
    normalized_titles = [compact_text(title) for title in titles]
    if any(not title for title in normalized_titles):
        fail("each title candidate must contain at least one letter or number")
    if len(set(normalized_titles)) != len(normalized_titles):
        fail("title candidates must be unique after Unicode/punctuation normalization")

    body_lines = lines[body_index + 1 :]
    if any(MARKDOWN_HEADING_RE.match(line.strip()) for line in body_lines):
        fail("the body section must not contain additional Markdown headings")
    body_nonempty = [index for index, line in enumerate(body_lines) if line.strip()]
    if not body_nonempty:
        fail("body section is empty")
    hashtag_index = body_nonempty[-1]
    hashtag_line = body_lines[hashtag_index].strip()
    hashtag_parts = hashtag_line.split()
    if not MIN_HASHTAGS <= len(hashtag_parts) <= MAX_HASHTAGS:
        fail(
            "final hashtag line must contain "
            f"{MIN_HASHTAGS}-{MAX_HASHTAGS} hashtags, got {len(hashtag_parts)}"
        )
    if any(HASHTAG_RE.fullmatch(part) is None for part in hashtag_parts):
        fail("final non-empty line must contain hashtags only")
    normalized_hashtags = [compact_text(part) for part in hashtag_parts]
    if any(not hashtag for hashtag in normalized_hashtags):
        fail("each hashtag must contain at least one letter or number")
    if len(set(normalized_hashtags)) != len(normalized_hashtags):
        fail("hashtags must be unique after Unicode/punctuation normalization")
    prose = "\n".join(body_lines[:hashtag_index]).strip()
    if not prose:
        fail("body must contain publishable prose before the hashtag line")
    prose_length = sum(not character.isspace() for character in prose)
    if not MIN_PROSE_NONSPACE_CHARACTERS <= prose_length <= MAX_PROSE_NONSPACE_CHARACTERS:
        fail(
            "body prose must contain "
            f"{MIN_PROSE_NONSPACE_CHARACTERS}-{MAX_PROSE_NONSPACE_CHARACTERS} "
            f"non-whitespace characters, got {prose_length}"
        )
    if re.search(r"[?？]", prose) is None:
        fail("body prose must include a specific interaction question")
    body = "\n".join(body_lines[: hashtag_index + 1]).strip()
    return PublishingDocument(tuple(titles), body, tuple(hashtag_parts))


def manifest_contract(manifest: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    schema_version = manifest.get("schema_version")
    if (
        type(schema_version) is not int
        or schema_version not in SUPPORTED_PROJECT_SCHEMA_VERSIONS
    ):
        fail("project-manifest.json schema_version must be 1 or 2")
    cover = manifest.get("cover")
    if not isinstance(cover, dict):
        fail("project-manifest.json cover must be an object")
    cover_text = cover.get("text")
    if not isinstance(cover_text, str) or not cover_text.strip():
        fail("project-manifest.json cover.text must be non-empty")
    items = manifest.get("items")
    if not isinstance(items, list):
        fail("project-manifest.json items must be an array")
    song_titles: list[str] = []
    performers: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            fail(f"project-manifest.json items[{index}] must be an object")
        title = item.get("title")
        performer = item.get("performer")
        if not isinstance(title, str) or not title.strip():
            fail(f"project-manifest.json items[{index}].title must be non-empty")
        if not isinstance(performer, str) or not performer.strip():
            fail(f"project-manifest.json items[{index}].performer must be non-empty")
        song_titles.append(title.strip())
        performers.append(performer.strip())
    return cover_text.strip(), song_titles, performers


def theme_terms(cover_text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in THEME_SPLIT_RE.split(cover_text) if chunk.strip()]
    candidates = list(chunks)
    for chunk in chunks:
        candidates.extend(token for token in chunk.split() if token)
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = compact_text(candidate)
        if (
            len(normalized) < 2
            or normalized.isdecimal()
            or normalized in GENERIC_COVER_TERMS
            or normalized in seen
        ):
            continue
        seen.add(normalized)
        result.append(candidate)
    return result


def performer_terms(performers: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for performer in performers:
        for candidate in (performer, *PERFORMER_SPLIT_RE.split(performer)):
            candidate = candidate.strip()
            normalized = compact_text(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(candidate)
    return result


def validate_no_song_titles(outward_text: str, song_titles: list[str]) -> None:
    normalized_copy = compact_text(outward_text)
    surface_copy = normalized_surface(outward_text)
    for title in song_titles:
        normalized_title = compact_text(title)
        if not normalized_title:
            fail(f"project song title cannot be normalized safely: {title!r}")
        if len(normalized_title) >= 2:
            revealed = normalized_title in normalized_copy
        else:
            # A one-character CJK title must not make every ordinary occurrence
            # of that character a spoiler.  It is explicit only when presented
            # as a book-title token, an exact hashtag, or a standalone token.
            token = re.escape(normalized_title)
            revealed = any(
                re.search(pattern, surface_copy) is not None
                for pattern in (
                    rf"[《〈]\s*{token}\s*[》〉]",
                    rf"(?<![\w#])#{token}(?!\w)",
                    rf"(?<!\w){token}(?!\w)",
                )
            )
        if revealed:
            fail(f"publishing copy reveals project song title: {title!r}")


def find_relevance(
    outward_text: str,
    cover_text: str,
    performers: list[str],
) -> tuple[str, str]:
    normalized_copy = compact_text(outward_text)
    for performer in performer_terms(performers):
        if compact_text(performer) in normalized_copy:
            return "performer", performer
    for theme in theme_terms(cover_text):
        if compact_text(theme) in normalized_copy:
            return "cover_theme", theme
    fail("publishing copy must mention at least one project performer or cover-theme term")


def verify_publishing(project: Path) -> PublishingSummary:
    root = real_project_root(project)
    manifest_path = project_file(root, MANIFEST_PATH, "project manifest")
    copy_path = project_file(root, PUBLISHING_PATH, "Xiaohongshu publishing copy")
    manifest = strict_json(manifest_path, MANIFEST_PATH)
    cover_text, song_titles, performers = manifest_contract(manifest)
    try:
        copy_text = copy_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"{PUBLISHING_PATH} is not valid UTF-8 text: {exc}")
    if contains_emoji(copy_text):
        fail("publishing copy must not contain emoji")
    document = parse_markdown(copy_text)
    validate_no_song_titles(document.outward_text, song_titles)
    relevance_kind, relevance_value = find_relevance(
        document.outward_text,
        cover_text,
        performers,
    )
    return PublishingSummary(
        path=PUBLISHING_PATH,
        title_count=len(document.titles),
        hashtag_count=len(document.hashtags),
        relevance_kind=relevance_kind,
        relevance_value=relevance_value,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = verify_publishing(args.project)
    except PublishingError as exc:
        print(f"PUBLISHING COPY: FAIL — {exc}", file=sys.stderr)
        return 1
    print(
        "PUBLISHING COPY: PASS "
        f"titles={summary.title_count} hashtags={summary.hashtag_count} "
        f"relevance={summary.relevance_kind}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
