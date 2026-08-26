from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.video import verify_publishing as gate


REPO_ROOT = Path(__file__).resolve().parents[3]
CLI = REPO_ROOT / "tools" / "video" / "verify_publishing.py"


class PublishingFixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name).resolve() / "project"
        self.project.mkdir()
        (self.project / "publishing").mkdir()
        self.manifest = {
            "schema_version": 1,
            "project_kind": "top_ranking",
            "cover": {
                "text": "郑中基｜被低估的声音层次｜五首作品",
                "disclosed_item_ids": [],
            },
            "items": [
                {"title": "Good-bye My Loneliness", "performer": "郑中基"},
                {"title": "不得不爱", "performer": "郑中基"},
            ],
        }
        self.prose = """很多人提到郑中基，第一反应可能还是高音、喜剧形象，以及那些传唱度最高的情歌。

但如果只停在这些印象里，就会错过他声音里更复杂的一面。他的音色并不只是高和亮，真正耐听的是强弱转换、语气收放，以及唱到克制处仍然保留的情绪重量。

这期没有把知名度当成唯一标准，也不是为了冷门而冷门。我们沿着不同阶段往作品深处听，看一位已经被大众熟悉的歌手，怎样在更少被讨论的表达里处理失去、迟疑和成年人不愿说破的体面。

有些段落不急着把情绪推到最高点，而是先让一句话在气息里停住；有些旋律听起来平静，真正难的却是不能多给一分力。越往后听，越能明白技巧不是为了证明能唱，而是为了让人物和情绪自然成立。

所以所谓被低估，并不只是还有几首作品没有进入大众歌单。更值得重听的，是他早已拥有一套完整的声音表达，只是最热闹的标签常常把这些细节盖住了。

重听一个熟悉歌手最有意思的地方，是旧印象会被一点点改写。你以为自己已经知道他是什么样子，作品却会从另一个角度把人重新打开。

你最想让更多人重新认识郑中基声音里的哪一种层次？"""
        self.hashtag_line = (
            "#郑中基 #粤语歌 #华语音乐 #港乐 #音乐分享 "
            "#实力派歌手 #唱片时代 #音乐故事"
        )
        self.copy = f"""# 小红书发布文案

## 标题候选（第一条为首选）

- 很多人只记得他的高音，却忽略了另一面
- 郑中基真正被低估的，可能不只是几首歌
- 越往专辑深处翻，越能听见他的完整面貌

## 正文

{self.prose}

{self.hashtag_line}
"""
        self.write_manifest()
        self.write_copy()

    def close(self) -> None:
        self.temporary.cleanup()

    def write_manifest(self) -> None:
        (self.project / gate.MANIFEST_PATH).write_text(
            json.dumps(self.manifest, ensure_ascii=False),
            encoding="utf-8",
        )

    def write_copy(self, value: str | None = None) -> None:
        (self.project / gate.PUBLISHING_PATH).write_text(
            self.copy if value is None else value,
            encoding="utf-8",
        )


class VerifyPublishingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = PublishingFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_valid_copy_passes_with_counts_and_performer_relevance(self) -> None:
        summary = gate.verify_publishing(self.fixture.project)
        self.assertEqual(gate.PUBLISHING_PATH, summary.path)
        self.assertEqual(3, summary.title_count)
        self.assertEqual(8, summary.hashtag_count)
        self.assertEqual(("performer", "郑中基"), (
            summary.relevance_kind,
            summary.relevance_value,
        ))

    def test_one_and_five_unique_titles_are_valid_boundaries(self) -> None:
        for count in (1, 5):
            with self.subTest(count=count):
                titles = "\n".join(f"- 郑中基被忽略的声音侧面之{index}" for index in range(count))
                self.fixture.write_copy(
                    f"""# 小红书发布文案

## 标题候选（第一条为首选）

{titles}

## 正文

{self.fixture.prose}

{self.fixture.hashtag_line}
"""
                )
                self.assertEqual(count, gate.verify_publishing(self.fixture.project).title_count)

    def test_title_count_must_be_between_one_and_five(self) -> None:
        for count in (0, 6):
            with self.subTest(count=count):
                titles = "\n".join(f"- 郑中基标题{index}" for index in range(count))
                self.fixture.write_copy(
                    f"""# 小红书发布文案

## 标题候选（第一条为首选）

{titles}

## 正文

郑中基的声音还有另一面。

#郑中基 #粤语歌 #音乐分享
"""
                )
                with self.assertRaisesRegex(gate.PublishingError, "1-5 entries"):
                    gate.verify_publishing(self.fixture.project)

    def test_titles_are_unique_after_unicode_and_punctuation_normalization(self) -> None:
        self.fixture.write_copy(self.fixture.copy.replace(
            "- 郑中基真正被低估的，可能不只是几首歌",
            "- 很多人只记得他的高音 却忽略了另一面！",
        ))
        with self.assertRaisesRegex(gate.PublishingError, "must be unique"):
            gate.verify_publishing(self.fixture.project)

    def test_body_requires_prose_before_hashtags(self) -> None:
        self.fixture.write_copy("""# 小红书发布文案

## 标题候选（第一条为首选）

- 郑中基还有多少面没有被听见

## 正文

#郑中基 #粤语歌 #华语音乐 #港乐 #音乐分享 #实力派歌手 #唱片时代 #音乐故事
""")
        with self.assertRaisesRegex(gate.PublishingError, "publishable prose"):
            gate.verify_publishing(self.fixture.project)

    def test_final_line_requires_eight_to_ten_hashtags(self) -> None:
        for count in (7, 11):
            with self.subTest(count=count):
                tags = " ".join(f"#标签{index}" for index in range(count))
                self.fixture.write_copy(self.fixture.copy.rsplit("\n#", 1)[0] + "\n" + tags + "\n")
                with self.assertRaisesRegex(gate.PublishingError, "8-10 hashtags"):
                    gate.verify_publishing(self.fixture.project)

    def test_final_nonempty_line_must_be_hashtags_only(self) -> None:
        self.fixture.write_copy(self.fixture.copy + "这不是 hashtag。\n")
        with self.assertRaisesRegex(gate.PublishingError, "8-10 hashtags|hashtags only"):
            gate.verify_publishing(self.fixture.project)

    def test_body_prose_length_accepts_boundaries_and_rejects_outside(self) -> None:
        for count in (420, 900):
            with self.subTest(valid=count):
                prose = "郑中基" + "声" * (count - 4) + "？"
                self.fixture.write_copy(self.fixture.copy.replace(self.fixture.prose, prose))
                gate.verify_publishing(self.fixture.project)

        for count in (419, 901):
            with self.subTest(invalid=count):
                prose = "郑中基" + "声" * (count - 4) + "？"
                self.fixture.write_copy(self.fixture.copy.replace(self.fixture.prose, prose))
                with self.assertRaisesRegex(gate.PublishingError, "420-900 non-whitespace"):
                    gate.verify_publishing(self.fixture.project)

    def test_publishing_copy_rejects_emoji(self) -> None:
        self.fixture.write_copy(self.fixture.copy.replace("复杂的一面", "复杂的一面🎧"))
        with self.assertRaisesRegex(gate.PublishingError, "must not contain emoji"):
            gate.verify_publishing(self.fixture.project)

    def test_body_requires_a_specific_interaction_question(self) -> None:
        self.fixture.write_copy(self.fixture.copy.replace("？", "。"))
        with self.assertRaisesRegex(gate.PublishingError, "interaction question"):
            gate.verify_publishing(self.fixture.project)

    def test_hashtags_must_be_unique_after_normalization(self) -> None:
        self.fixture.write_copy(self.fixture.copy.replace("#音乐故事", "#港乐"))
        with self.assertRaisesRegex(gate.PublishingError, "hashtags must be unique"):
            gate.verify_publishing(self.fixture.project)

    def test_song_titles_are_rejected_in_every_outward_area_and_normalized(self) -> None:
        cases = {
            "candidate": self.fixture.copy.replace(
                "很多人只记得他的高音，却忽略了另一面",
                "Good bye，MY loneliness 为什么被忽略",
                1,
            ),
            "body": self.fixture.copy.replace(
                "但如果只停在这些印象里",
                "但真正听到 GOOD—BYE MY LONELINESS，如果只停在这些印象里",
            ),
            "hashtag": self.fixture.copy.replace(
                "#郑中基 #粤语歌",
                "#不得_不爱 #郑中基 #粤语歌",
            ),
        }
        for area, content in cases.items():
            with self.subTest(area=area):
                self.fixture.write_copy(content)
                with self.assertRaisesRegex(gate.PublishingError, "reveals project song title"):
                    gate.verify_publishing(self.fixture.project)

    def test_nfkc_and_casefold_song_title_match(self) -> None:
        self.fixture.manifest["items"][0]["title"] = "ＡＢＣ Story"
        self.fixture.write_manifest()
        self.fixture.write_copy(self.fixture.copy.replace(
            "完整面貌",
            "abc-story 背后的完整面貌",
        ))
        with self.assertRaisesRegex(gate.PublishingError, "reveals project song title"):
            gate.verify_publishing(self.fixture.project)

    def test_one_character_title_uses_explicit_boundaries_without_plain_substring_false_positive(self) -> None:
        self.fixture.manifest["items"][0]["title"] = "爱"
        self.fixture.write_manifest()
        self.fixture.write_copy(self.fixture.copy.replace("完整面貌", "令人喜爱的完整面貌"))
        gate.verify_publishing(self.fixture.project)

        variants = ("《爱》", "#爱", "，爱，")
        for variant in variants:
            with self.subTest(variant=variant):
                self.fixture.write_copy(self.fixture.copy.replace("完整面貌", f"{variant} 背后的完整面貌"))
                with self.assertRaisesRegex(gate.PublishingError, "reveals project song title"):
                    gate.verify_publishing(self.fixture.project)

    def test_cover_theme_can_supply_relevance_without_performer(self) -> None:
        self.fixture.manifest["cover"]["text"] = "冒险岛 BGM TOP 5｜青春回忆"
        for item in self.fixture.manifest["items"]:
            item["performer"] = "Studio Composer"
        self.fixture.write_manifest()
        content = self.fixture.copy.replace("郑中基", "冒险岛")
        self.fixture.write_copy(content)
        summary = gate.verify_publishing(self.fixture.project)
        self.assertEqual(("cover_theme", "冒险岛"), (
            summary.relevance_kind,
            summary.relevance_value,
        ))

    def test_free_exploration_without_items_uses_distinct_cover_theme(self) -> None:
        self.fixture.manifest["project_kind"] = "free_exploration"
        self.fixture.manifest["cover"]["text"] = "深夜城市声景｜情绪漫游"
        self.fixture.manifest["items"] = []
        self.fixture.write_manifest()
        self.fixture.write_copy(self.fixture.copy.replace("郑中基", "深夜城市声景"))
        summary = gate.verify_publishing(self.fixture.project)
        self.assertEqual(("cover_theme", "深夜城市声景"), (
            summary.relevance_kind,
            summary.relevance_value,
        ))

    def test_free_exploration_without_items_rejects_generic_only_cover(self) -> None:
        self.fixture.manifest["project_kind"] = "free_exploration"
        self.fixture.manifest["cover"]["text"] = "音乐｜盘点｜TOP 5"
        self.fixture.manifest["items"] = []
        self.fixture.write_manifest()
        self.fixture.write_copy(self.fixture.copy.replace("郑中基", "这期内容"))
        with self.assertRaisesRegex(gate.PublishingError, "performer or cover-theme"):
            gate.verify_publishing(self.fixture.project)

    def test_copy_without_performer_or_cover_theme_fails(self) -> None:
        self.fixture.write_copy(self.fixture.copy.replace("郑中基", "这位歌手"))
        with self.assertRaisesRegex(gate.PublishingError, "performer or cover-theme"):
            gate.verify_publishing(self.fixture.project)

    def test_fixed_markdown_structure_rejects_wrong_order_extra_heading_and_bad_bullet(self) -> None:
        cases = (
            self.fixture.copy.replace(
                "## 标题候选（第一条为首选）",
                "## 候选标题",
            ),
            self.fixture.copy.replace("## 正文", "## 正文\n\n### 说明"),
            self.fixture.copy.replace(
                "- 很多人只记得他的高音，却忽略了另一面",
                "1. 很多人只记得他的高音，却忽略了另一面",
            ),
        )
        for content in cases:
            with self.subTest(content=content[:60]):
                self.fixture.write_copy(content)
                with self.assertRaises(gate.PublishingError):
                    gate.verify_publishing(self.fixture.project)

    def test_manifest_parser_rejects_duplicate_keys_and_nonstandard_constants(self) -> None:
        path = self.fixture.project / gate.MANIFEST_PATH
        values = (
            '{"schema_version":1,"schema_version":1,"cover":{},"items":[]}',
            '{"schema_version":1,"cover":{"text":"主题"},"items":[],"x":NaN}',
            '{"schema_version":1,"cover":{"text":"主题"},"items":[],"x":1e999}',
        )
        for value in values:
            with self.subTest(value=value):
                path.write_text(value, encoding="utf-8")
                with self.assertRaisesRegex(gate.PublishingError, "not strict JSON"):
                    gate.verify_publishing(self.fixture.project)

    def test_project_manifest_schema_v2_is_accepted(self) -> None:
        self.assertEqual({1, 2}, set(gate.SUPPORTED_PROJECT_SCHEMA_VERSIONS))
        self.fixture.manifest["schema_version"] = 2
        self.fixture.write_manifest()
        summary = gate.verify_publishing(self.fixture.project)
        self.assertEqual(3, summary.title_count)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support is required")
    def test_manifest_and_publishing_copy_symlinks_are_rejected(self) -> None:
        for relative_path, label in (
            (gate.MANIFEST_PATH, "project manifest"),
            (gate.PUBLISHING_PATH, "Xiaohongshu publishing copy"),
        ):
            with self.subTest(relative_path=relative_path):
                for fixture_path in (
                    self.fixture.project / gate.MANIFEST_PATH,
                    self.fixture.project / gate.PUBLISHING_PATH,
                ):
                    if fixture_path.is_symlink():
                        fixture_path.unlink()
                self.fixture.write_manifest()
                self.fixture.write_copy()
                target = self.fixture.project / relative_path
                outside = self.fixture.project.parent / (target.name + ".outside")
                outside.write_bytes(target.read_bytes())
                target.unlink()
                target.symlink_to(outside)
                with self.assertRaisesRegex(gate.PublishingError, f"{label} must not be a symlink"):
                    gate.verify_publishing(self.fixture.project)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support is required")
    def test_project_root_symlink_is_rejected(self) -> None:
        alias = self.fixture.project.parent / "project-alias"
        alias.symlink_to(self.fixture.project, target_is_directory=True)
        with self.assertRaisesRegex(gate.PublishingError, "project root.*symlink"):
            gate.verify_publishing(alias)

    def test_cli_has_stable_pass_and_fail_status(self) -> None:
        passed = subprocess.run(
            [sys.executable, str(CLI), "--project", str(self.fixture.project)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(0, passed.returncode, passed.stderr)
        self.assertIn("PUBLISHING COPY: PASS titles=3 hashtags=8", passed.stdout)

        (self.fixture.project / gate.PUBLISHING_PATH).unlink()
        failed = subprocess.run(
            [sys.executable, str(CLI), "--project", str(self.fixture.project)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(1, failed.returncode)
        self.assertIn("PUBLISHING COPY: FAIL", failed.stderr)


if __name__ == "__main__":
    unittest.main()
