"""Synthetic regressions for the fail-closed project authoring contract."""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from tools.video import verify_project as gate


REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = REPO_ROOT / "tools" / "video" / "examples" / "project-contract"
SCHEMA = REPO_ROOT / "tools" / "video" / "project-manifest.schema.json"
COUNTDOWN_TEMPLATE = REPO_ROOT / "tools" / "video" / "countdown_build.py"
NARRATION_TEMPLATE = REPO_ROOT / "tools" / "video" / "narrate_segments.py"
TTS_ROOT = REPO_ROOT / "tools" / "tts"

if str(TTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TTS_ROOT))

from model_provenance import canonical_sha256
from qwen_contract import derived_seed, fingerprint, fingerprint_inputs
from text_normalizer import PronunciationPolicy, normalize_tts_text
from voice_registry import VoiceRegistry, file_sha256, resolve_selector


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class VerifyProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            raise unittest.SkipTest("ffmpeg and ffprobe are required for project-gate tests")
        cls._baseline_temp = tempfile.TemporaryDirectory()
        cls.registry = VoiceRegistry.load()
        cls.current_model_validation = cls.synthetic_model_validation()
        cls.hydrated_example = Path(cls._baseline_temp.name).resolve() / "hydrated-project"
        shutil.copytree(EXAMPLE, cls.hydrated_example)
        cls.hydrate_example(cls.hydrated_example)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._baseline_temp.cleanup()
        super().tearDownClass()

    @classmethod
    def synthetic_model_validation(cls, *, receipt_sha256: str = "b" * 64) -> dict:
        qwen = cls.registry.config["qwen_base"]
        manifest_path = TTS_ROOT / qwen["model_file_manifest"]
        model_manifest = load_json(manifest_path)
        claim = {
            "portable_claim_kind": "qwen-model-portable-claim-v1",
            "verification_kind": "qwen-full-model-hash-receipt-v1",
            "model_id": qwen["model_id"],
            "model_revision": qwen["model_revision"],
            "qwen_config_sha256": canonical_sha256(qwen),
            "manifest_sha256": file_sha256(manifest_path),
            "verified_model_tree_sha256": qwen["model_tree_sha256"],
            "model_file_count": model_manifest["file_count"],
            "model_total_bytes": model_manifest["total_bytes"],
            "mlx_audio_version": qwen["mlx_audio_version"],
        }
        return {
            **claim,
            "portable_claim_sha256": canonical_sha256(claim),
            "receipt_sha256": receipt_sha256,
            "full_tree_hash_verified": True,
        }

    @classmethod
    def write_qwen_sidecar(
        cls,
        *,
        wav_path: Path,
        sidecar_path: Path,
        item_id: str,
        text: str,
        selection: dict,
        model_validation: dict | None = None,
        source_text: str | None = None,
        text_normalization: dict | None = None,
    ) -> None:
        """Write the exact current worker contract around a synthetic test WAV."""

        if wav_path.parent != sidecar_path.parent:
            raise AssertionError("worker sidecars must be adjacent to their WAV")
        voice = cls.registry.by_id(selection["resolved_voice_id"])
        assert voice is not None
        qwen = cls.registry.config["qwen_base"]
        language = qwen["language"]
        speed = 1.0
        item = {"id": item_id, "text": text}
        normalized = source_text is not None
        if normalized:
            if not isinstance(text_normalization, dict):
                raise AssertionError("normalized worker sidecars need text_normalization")
            item.update(
                {
                    "source_text": source_text,
                    "text_normalization": text_normalization,
                }
            )
        fp_inputs = fingerprint_inputs(
            qwen=qwen,
            selection=selection,
            voice_id=voice["id"],
            reference_sha256=voice["reference_sha256"],
            reference_text=cls.registry.registry["reference_text"],
            item=item,
            language=language,
            speed=speed,
        )
        with wave.open(str(wav_path), "rb") as stream:
            frames = stream.getnframes()
            sample_rate = stream.getframerate()
            wav = {
                "channels": stream.getnchannels(),
                "sample_rate_hz": sample_rate,
                "sample_width_bytes": stream.getsampwidth(),
                "frames": frames,
                "duration_seconds": frames / sample_rate,
            }
        sidecar = {
            "schema_version": "1.1.0" if normalized else "1.0.0",
            "item_id": item_id,
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "selection": selection,
            "resolved_voice_id": voice["id"],
            "engine": qwen["engine"],
            "model_id": qwen["model_id"],
            "model_revision": qwen["model_revision"],
            "model_tree_sha256": qwen["model_tree_sha256"],
            "model_validation": model_validation
            or cls.synthetic_model_validation(receipt_sha256="a" * 64),
            "reference_audio": f"voices/{voice['reference_audio']}",
            "reference_sha256": voice["reference_sha256"],
            "language": language,
            "speed": speed,
            "seed": derived_seed(
                qwen["generation"]["seed"], voice["id"], text, language
            ),
            "generation_seconds": 0.1,
            "model_load_seconds": 0.2,
            "model_metrics": [
                {
                    "processing_seconds": 0.1,
                    "peak_memory_gb": 0.25,
                    "token_count": 10,
                }
            ],
            "fingerprint": fingerprint(fp_inputs),
            "fingerprint_inputs": fp_inputs,
            "output": wav_path.name,
            "output_sha256": gate.sha256_file(wav_path),
            "wav": wav,
        }
        if normalized:
            sidecar.update(
                {
                    "source_text": source_text,
                    "normalized_text": text,
                    "text_normalization": text_normalization,
                }
            )
        write_json(sidecar_path, sidecar)

    @classmethod
    def hydrate_example(cls, root: Path) -> None:
        manifest = load_json(root / "project-manifest.json")
        selection = resolve_selector(cls.registry, "CV002")
        write_json(root / manifest["voice_selection"], selection)
        sidecar_model_validation = cls.synthetic_model_validation(receipt_sha256="a" * 64)
        generated = root / "generated-base.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=64x64:r=5:d=45",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=24000:duration=45",
                "-shortest",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "64k",
                str(generated),
            ],
            check=True,
        )
        raw_dir = root / "sources" / "raw"
        clip_dir = root / "clips"
        narration_dir = root / "narration"
        raw_dir.mkdir(parents=True, exist_ok=True)
        clip_dir.mkdir(parents=True, exist_ok=True)
        narration_dir.mkdir(parents=True, exist_ok=True)

        for row in manifest["narration_sequence"]:
            wav_path = root / row["wav"]
            with wave.open(str(wav_path), "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(24000)
                stream.writeframes(b"\0\0" * 2400)
            sidecar_path = root / row["sidecar"]
            cls.write_qwen_sidecar(
                wav_path=wav_path,
                sidecar_path=sidecar_path,
                item_id=row["id"],
                text=row["text"],
                selection=selection,
                model_validation=sidecar_model_validation,
            )

        for item in manifest["items"]:
            item_id = item["id"]
            clip_path = root / item["clip"]
            raw_path = raw_dir / f"{item_id}.mp4"
            shutil.copyfile(generated, clip_path)
            shutil.copyfile(generated, raw_path)
            clip_hash = gate.sha256_file(clip_path)
            raw_hash = gate.sha256_file(raw_path)
            item["clip_sha256"] = clip_hash

            receipt_ref = item["sources"]["selection"]["download_receipt"]
            receipt_path = root / receipt_ref["path"]
            receipt = load_json(receipt_path)
            receipt["raw_asset"] = {
                "path": str(raw_path.relative_to(root)),
                "sha256": raw_hash,
            }
            receipt["raw_duration_sec"] = 45.0
            receipt["derivation"]["input_sha256"] = raw_hash
            receipt["derivation"]["output"] = {
                "path": item["clip"],
                "sha256": clip_hash,
            }
            receipt["derivation"]["output_duration_sec"] = 45.0
            write_json(receipt_path, receipt)
            receipt_ref["sha256"] = gate.sha256_file(receipt_path)

            evidence_path = root / item["evidence"]["path"]
            evidence = load_json(evidence_path)
            evidence["clip"] = item["clip"]
            evidence["clip_sha256"] = clip_hash
            if item["audio_mode"] == "vocal":
                analysis_path = root / evidence["analysis"]["path"]
                analysis = load_json(analysis_path)
                analysis["source_sha256"] = clip_hash
                analysis["duration"] = 45.0
                write_json(analysis_path, analysis)
                evidence["analysis"]["sha256"] = gate.sha256_file(analysis_path)
            else:
                evidence["clip_duration_sec"] = 45.0
            write_json(evidence_path, evidence)
            item["evidence"]["sha256"] = gate.sha256_file(evidence_path)
        generated.unlink()
        write_json(root / "project-manifest.json", manifest)

    @contextmanager
    def project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "project"
            shutil.copytree(self.hydrated_example, root)
            yield root

    def errors(
        self,
        root: Path,
        *,
        require_human_review: bool = False,
    ) -> list[str]:
        return gate.verify_project(
            root,
            voice_registry=self.registry,
            current_model_validation=self.current_model_validation,
            require_human_review=require_human_review,
        )

    def assert_error(self, errors: list[str], text: str) -> None:
        self.assertTrue(
            any(text in error for error in errors),
            f"missing error containing {text!r}; got {errors}",
        )

    def save_manifest(self, root: Path, manifest: dict) -> None:
        write_json(root / "project-manifest.json", manifest)

    def test_custom_output_format_requires_explicit_user_request(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["output_format"] = {"width": 1920, "height": 1080}
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "requires user_request")
            manifest["output_format"]["user_request"] = "本期请做 1920×1080 横屏。"
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root))

    def test_output_format_defaults_and_invalid_declarations(self) -> None:
        self.assertEqual((1080, 1920), gate.resolve_output_format({}))
        self.assertEqual((1080, 1920), gate.resolve_output_format(
            {"output_format": {"width": 1080, "height": 1920}}))
        for row in (None, {}, {"width": True, "height": 1920},
                    {"width": 1081, "height": 1920},
                    {"width": 1920, "height": 1080, "user_request": " "},
                    {"width": 1920, "height": 1080, "reason": "保留全景"}):
            with self.subTest(row=row), self.assertRaises(ValueError):
                gate.resolve_output_format({"output_format": row})

    def update_item_evidence_hash(self, root: Path, manifest: dict, index: int) -> None:
        evidence = root / manifest["items"][index]["evidence"]["path"]
        manifest["items"][index]["evidence"]["sha256"] = gate.sha256_file(evidence)

    def rewrite_narration_duration(
        self,
        root: Path,
        manifest: dict,
        narration_index: int,
        duration_seconds: float,
    ) -> None:
        row = manifest["narration_sequence"][narration_index]
        wav_path = root / row["wav"]
        frame_count = round(24000 * duration_seconds)
        with wave.open(str(wav_path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(24000)
            stream.writeframes(b"\0\0" * frame_count)
        self.write_qwen_sidecar(
            wav_path=wav_path,
            sidecar_path=root / row["sidecar"],
            item_id=row["id"],
            text=row["text"],
            selection=load_json(root / manifest["voice_selection"]),
            model_validation=self.current_model_validation,
        )

    def test_schema_and_hydrated_contract_pass_while_static_example_is_template(self) -> None:
        schema = load_json(SCHEMA)
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        self.assertEqual(
            set(gate.SUPPORTED_SCHEMA_VERSIONS),
            set(schema["properties"]["schema_version"]["enum"]),
        )
        self.assertEqual(
            gate.SCHEMA_VERSION,
            load_json(EXAMPLE / "project-manifest.json")["schema_version"],
        )
        self.assertEqual([], self.errors(self.hydrated_example))
        self.assertTrue(self.errors(EXAMPLE), "the checked-in no-media template must not fake PASS")

    def test_schema_external_contracts_match_verifier_required_fields(self) -> None:
        defs = load_json(SCHEMA)["$defs"]
        self.assertEqual(
            set(gate.SOURCE_RECEIPT_REQUIRED),
            set(defs["selectedDownloadReceipt"]["required"]),
        )
        self.assertEqual(
            set(gate.SOURCE_DERIVATION_REQUIRED),
            set(defs["sourceDerivation"]["required"]),
        )
        self.assertEqual(
            set(gate.VOCAL_EVIDENCE_REQUIRED),
            set(defs["vocalShowcaseEvidence"]["required"]),
        )
        self.assertEqual(
            set(gate.INSTRUMENTAL_EVIDENCE_REQUIRED),
            set(defs["instrumentalEvidence"]["required"]),
        )
        self.assertEqual(
            set(gate.REVIEW_APPROVAL_REQUIRED),
            set(defs["reviewApproval"]["required"]),
        )
        self.assertEqual(
            {"agent", "human"},
            set(defs["reviewApproval"]["properties"]["reviewer_kind"]["enum"]),
        )
        self.assertEqual(
            {"observed", "approved"},
            set(defs["reviewApproval"]["properties"]["status"]["enum"]),
        )
        self.assertEqual(
            {
                ("observed", "agent"),
                ("approved", "human"),
            },
            {
                (
                    branch["properties"]["status"]["const"],
                    branch["properties"]["reviewer_kind"]["const"],
                )
                for branch in defs["reviewApproval"]["oneOf"]
            },
        )
        self.assertEqual(
            {"OK", "OBSERVED", "APPROVED"},
            set(defs["vocalShowcaseEvidence"]["properties"]["status"]["enum"]),
        )

    def test_cli_propagates_explicit_release_mode(self) -> None:
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "verify_project.py",
                    "--project",
                    "project",
                    "--require-human-review",
                ],
            ),
            mock.patch.object(gate, "verify_project", return_value=[]) as verify,
            mock.patch("builtins.print"),
        ):
            self.assertEqual(0, gate.main())
        verify.assert_called_once_with(
            Path("project"),
            "project-manifest.json",
            require_human_review=True,
        )

    def test_top_requires_strict_descending_ranks(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["items"][0]["rank"] = 1
            manifest["items"][1]["rank"] = 2
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "TOP ranks must be strict N->1")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["items"][1]["rank"] = True
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "TOP ranks must be strict N->1")

    def test_top_cover_and_intro_cannot_disclose_items_or_first_place(self) -> None:
        mutations = (
            (
                "explicit disclosure",
                lambda manifest: manifest["cover"].update(
                    {"disclosed_item_ids": ["rank-02"]}
                ),
                "cover.disclosed_item_ids must be []",
            ),
            (
                "missing explicit intro disclosure",
                lambda manifest: manifest["narration_sequence"][0].pop(
                    "disclosed_item_ids"
                ),
                "intro.disclosed_item_ids must be an explicit string array",
            ),
            (
                "first title",
                lambda manifest: manifest["cover"].update(
                    {"text": "合成素材 TOP 2，示例歌曲乙最终夺冠"}
                ),
                "first-place item title",
            ),
            (
                "first rank marker",
                lambda manifest: manifest["narration_sequence"][0].update(
                    {"text": "第一名会在后面出现。"}
                ),
                "first-place rank",
            ),
            (
                "complete list",
                lambda manifest: manifest["cover"].update(
                    {"text": "示例歌曲甲、示例歌曲乙完整名单"}
                ),
                "complete item list",
            ),
        )
        for name, mutate, expected in mutations:
            with self.subTest(name=name), self.project() as root:
                manifest = load_json(root / "project-manifest.json")
                mutate(manifest)
                self.save_manifest(root, manifest)
                self.assert_error(self.errors(root), expected)

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["items"][-1]["title"] = "A"
            manifest["cover"]["text"] = "A 类音乐 TOP 2"
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root), "one-character titles are ambiguous")

    def test_top_cover_rejects_internal_countdown_order_hints(self) -> None:
        for hint in ("05→01", "05->01", "N→1", "倒数揭晓", "倒序揭晓", "从第5名开始"):
            with self.subTest(hint=hint), self.project() as root:
                manifest = load_json(root / "project-manifest.json")
                manifest["cover"]["text"] = f"示例歌手 TOP 2 {hint}"
                self.save_manifest(root, manifest)
                self.assert_error(
                    self.errors(root),
                    "cover.text must not expose internal countdown order hints",
                )

    def test_non_free_narration_order_intro_word_and_canonical_cta(self) -> None:
        mutations = (
            (
                "order",
                lambda rows: rows.__setitem__(slice(1, 3), list(reversed(rows[1:3]))),
                "must be exactly intro",
            ),
            (
                "cta",
                lambda rows: rows[-1].update({"text": "点赞关注。"}),
                "must exactly equal",
            ),
        )
        for name, mutate, expected in mutations:
            with self.subTest(name=name), self.project() as root:
                manifest = load_json(root / "project-manifest.json")
                mutate(manifest["narration_sequence"])
                self.save_manifest(root, manifest)
                self.assert_error(self.errors(root), expected)

    def test_intro_wording_is_editorial_but_still_bound_to_qwen_output(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["narration_sequence"][0]["text"] = "接下来聊聊这些作品的变化。"
            self.rewrite_narration_duration(root, manifest, 0, 1.0)
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root))

    def test_search_exceptions_are_truthful_and_do_not_drop_source_evidence(self) -> None:
        for direct in (False, True):
            with self.subTest(direct=direct), self.project() as root:
                manifest = load_json(root / "project-manifest.json")
                source = manifest["items"][0]["sources"]
                selected = source["selection"]["platform"]
                other = "bilibili" if selected == "youtube" else "youtube"
                record = source["platforms"][selected if direct else other]
                record.update(searched=False, search_queries=[], search_exception={
                    "kind": "user_specified_url" if direct else "user_excluded_platform",
                    "reason": "用户指定该链接" if direct else "用户排除另一平台",
                })
                if not direct:
                    record["candidates"] = []
                self.save_manifest(root, manifest)
                self.assertEqual([], self.errors(root))
                record.pop("search_exception")
                self.save_manifest(root, manifest)
                self.assert_error(self.errors(root), "search_exception requires")

    def test_custom_cta_requires_reason_and_real_matching_sidecar(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["editorial"] = {"cta": "custom", "reason": "用户指定本期结尾"}
            manifest["narration_sequence"][-1]["text"] = "愿这段旋律陪你度过今晚。"
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "does not exactly match")
            self.rewrite_narration_duration(root, manifest, -1, 1.0)
            self.assertEqual([], self.errors(root))
            manifest["editorial"].pop("reason")
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "overrides require")

    def test_explicit_custom_structure_and_silent_project_preserve_item_gates(self) -> None:
        for silent in (False, True):
            with self.subTest(silent=silent), self.project() as root:
                manifest = load_json(root / "project-manifest.json")
                manifest["editorial"] = {"narration": "custom", "cta": "omit", "reason": "本期采用音乐为主的结构"}
                removed = manifest["narration_sequence"][0 if silent else 1:]
                manifest["narration_sequence"] = [] if silent else manifest["narration_sequence"][:1]
                for row in removed:
                    (root / row["wav"]).unlink()
                    (root / row["sidecar"]).unlink()
                if silent:
                    manifest.pop("voice_selection")
                self.save_manifest(root, manifest)
                self.assertEqual([], self.errors(root))
                manifest["items"][0]["clip_sha256"] = "0" * 64
                self.save_manifest(root, manifest)
                self.assertTrue(self.errors(root), "custom structure must retain clip hash validation")

    def test_schema_v2_top_transition_narration_has_eight_second_hard_limit(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            self.rewrite_narration_duration(root, manifest, 1, 8.0)
            self.assertEqual([], self.errors(root))

            self.rewrite_narration_duration(root, manifest, 1, 8.01)
            self.assert_error(
                self.errors(root),
                "exceeds top_ranking transition narration hard limit 8.000s",
            )

    def test_schema_v2_narrative_transition_narration_has_ten_second_hard_limit(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["project_kind"] = "narrative"
            for item in manifest["items"]:
                item.pop("rank")
            self.save_manifest(root, manifest)

            self.rewrite_narration_duration(root, manifest, 1, 10.0)
            self.assertEqual([], self.errors(root))

            self.rewrite_narration_duration(root, manifest, 1, 10.01)
            self.assert_error(
                self.errors(root),
                "exceeds narrative transition narration hard limit 10.000s",
            )

    def test_schema_v1_historical_project_does_not_gain_transition_duration_failures(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["schema_version"] = 1
            self.save_manifest(root, manifest)
            self.rewrite_narration_duration(root, manifest, 1, 20.0)
            self.assertEqual([], self.errors(root))

    def test_all_sidecars_must_use_the_same_selection(self) -> None:
        with self.project() as root:
            sidecar = root / "narration" / "rank-02.wav.tts.json"
            value = load_json(sidecar)
            value["selection"]["resolved_voice_id"] = "CV003"
            write_json(sidecar, value)
            self.assert_error(self.errors(root), "was not generated from this project selection")

    def test_manifest_text_is_exactly_bound_to_canonical_sidecar_input(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["narration_sequence"][1]["text"] = "被改写但没有重新生成的旁白。"
            self.save_manifest(root, manifest)
            self.assert_error(
                self.errors(root), "does not exactly match the sidecar canonical input text"
            )

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            row = manifest["narration_sequence"][1]
            source_text = row["text"]
            generated_text = "第二名的转场旁白，在这一项出现时才揭晓 title。"
            normalization = normalize_tts_text(
                source_text,
                policy=PronunciationPolicy.load(),
                overrides={source_text: generated_text},
            )
            self.assertEqual(generated_text, normalization.normalized_text)
            sidecar_path = root / row["sidecar"]
            self.write_qwen_sidecar(
                wav_path=root / row["wav"],
                sidecar_path=sidecar_path,
                item_id=row["id"],
                text=normalization.normalized_text,
                selection=load_json(root / manifest["voice_selection"]),
                source_text=normalization.source_text,
                text_normalization=normalization.metadata(),
            )
            self.assertEqual([], self.errors(root))

    def test_central_voice_gate_binds_format_model_and_manifest_inventory(self) -> None:
        with self.project() as root:
            wav_path = root / "narration" / "intro.wav"
            with wave.open(str(wav_path), "wb") as stream:
                stream.setnchannels(2)
                stream.setsampwidth(2)
                stream.setframerate(16000)
                stream.writeframes(b"\0\0\0\0" * 1600)
            sidecar_path = root / "narration" / "intro.wav.tts.json"
            sidecar = load_json(sidecar_path)
            sidecar["output_sha256"] = gate.sha256_file(wav_path)
            write_json(sidecar_path, sidecar)
            self.assert_error(self.errors(root), "output is not 24kHz mono WAV")

        with self.project() as root:
            sidecar_path = root / "narration" / "intro.wav.tts.json"
            sidecar = load_json(sidecar_path)
            sidecar["model_validation"]["qwen_config_sha256"] = "0" * 64
            write_json(sidecar_path, sidecar)
            self.assert_error(self.errors(root), "model validation mismatch: qwen_config_sha256")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            original_wav = root / "narration" / "intro.wav"
            extra_wav = root / "narration" / "undeclared.wav"
            extra = root / "narration" / "undeclared.wav.tts.json"
            shutil.copyfile(original_wav, extra_wav)
            self.write_qwen_sidecar(
                wav_path=extra_wav,
                sidecar_path=extra,
                item_id="undeclared",
                text="这是一条有效但未在项目清单声明的合成旁白。",
                selection=load_json(root / manifest["voice_selection"]),
            )
            self.assert_error(
                self.errors(root), "central voice sidecar is not declared in narration_sequence"
            )

    def test_historical_qwen_sidecar_has_no_project_gate_opt_in(self) -> None:
        with self.project() as root:
            sidecar_path = root / "narration" / "intro.wav.tts.json"
            sidecar = load_json(sidecar_path)
            sidecar.pop("model_validation")
            sidecar["output"] = str((root / "narration" / "intro.wav").resolve())
            write_json(sidecar_path, sidecar)
            self.assert_error(
                self.errors(root), "historical absolute-path Qwen sidecars require explicit legacy opt-in"
            )

    def test_relative_sidecar_outputs_follow_a_moved_project(self) -> None:
        with self.project() as root:
            sidecar = load_json(root / "narration" / "intro.wav.tts.json")
            self.assertEqual("intro.wav", sidecar["output"])
            self.assertEqual([], self.errors(root))

    def test_absolute_sidecar_output_is_rejected_and_cannot_escape_project(self) -> None:
        with self.project() as root:
            sidecar_path = root / "narration" / "intro.wav.tts.json"
            sidecar = load_json(sidecar_path)
            sidecar["output"] = str((root / "narration" / "intro.wav").resolve())
            write_json(sidecar_path, sidecar)
            self.assert_error(
                self.errors(root), "output must be the adjacent WAV filename"
            )

            outside = root.parent / "outside.wav"
            outside.write_text("external output sentinel\n", encoding="utf-8")
            sidecar["output"] = str(outside)
            sidecar["output_sha256"] = gate.sha256_file(outside)
            write_json(sidecar_path, sidecar)
            self.assert_error(self.errors(root), "output WAV is outside the project")

    def test_relative_sidecar_output_cannot_escape_or_follow_a_symlink(self) -> None:
        with self.project() as root:
            sidecar_path = root / "narration" / "intro.wav.tts.json"
            sidecar = load_json(sidecar_path)
            sidecar["output"] = "../outside.wav"
            write_json(sidecar_path, sidecar)
            self.assert_error(self.errors(root), "cannot inspect")

        with self.project() as root:
            output = root / "narration" / "intro.wav"
            output.unlink()
            outside = root.parent / "outside.wav"
            outside.write_text("external output sentinel\n", encoding="utf-8")
            output.symlink_to(outside)
            self.assert_error(
                self.errors(root), "output WAV or one of its parents must not be a symlink"
            )

    def test_external_sidecar_symlink_is_rejected(self) -> None:
        with self.project() as root:
            sidecar = root / "narration" / "intro.wav.tts.json"
            sidecar.unlink()
            outside = root.parent / "external-sidecar.json"
            outside.write_text("{invalid external sentinel", encoding="utf-8")
            sidecar.symlink_to(outside)
            self.assert_error(self.errors(root), "sidecar must not be a symlink")

    def test_project_root_or_parent_symlink_is_rejected_without_throwing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            real_project = base / "real-project"
            shutil.copytree(self.hydrated_example, real_project)
            linked_project = base / "linked-project"
            linked_project.symlink_to(real_project, target_is_directory=True)
            self.assert_error(
                self.errors(linked_project),
                "project root or one of its parents must not be a symlink",
            )

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            real_parent = base / "real-parent"
            real_parent.mkdir()
            real_project = real_parent / "project"
            shutil.copytree(self.hydrated_example, real_project)
            linked_parent = base / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            self.assert_error(
                self.errors(linked_parent / "project"),
                "project root or one of its parents must not be a symlink",
            )

    def test_external_manifest_and_evidence_symlinks_are_rejected(self) -> None:
        with self.project() as root:
            manifest_path = root / "project-manifest.json"
            manifest_path.unlink()
            outside = root.parent / "external-manifest.json"
            outside.write_text("{external sentinel", encoding="utf-8")
            manifest_path.symlink_to(outside)
            self.assert_error(self.errors(root), "manifest must not be a symlink")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            evidence = root / manifest["items"][0]["evidence"]["path"]
            evidence.unlink()
            outside = root.parent / "external-evidence.json"
            outside.write_text("{external sentinel", encoding="utf-8")
            evidence.symlink_to(outside)
            self.assert_error(self.errors(root), "evidence.path must not be a symlink")

    def test_free_exploration_requires_rationale_and_forbids_rank(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["project_kind"] = "free_exploration"
            manifest["rationale"] = ""
            self.save_manifest(root, manifest)
            errors = self.errors(root)
            self.assert_error(errors, "requires a non-empty rationale")
            self.assert_error(errors, "rank is forbidden")

    def test_both_platforms_and_real_hostnames_are_required(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            item = manifest["items"][0]
            item["sources"]["platforms"]["youtube"]["candidates"][0]["url"] = (
                "https://www.bilibili.com/video/BVFakeYoutube"
            )
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "url does not belong to youtube")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            item = manifest["items"][0]
            item["sources"]["platforms"]["youtube"]["candidates"][0]["url"] = (
                "file://youtube.com/not-a-network-source"
            )
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "url does not belong to youtube")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            del manifest["items"][0]["sources"]["platforms"]["bilibili"]
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "platforms.bilibili must be an object")

    def test_item_performer_must_match_target_version(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            manifest["items"][0]["performer"] = "另一个表演者"
            self.save_manifest(root, manifest)
            self.assert_error(
                self.errors(root), "performer must match sources.target_version.performer"
            )

    def test_selected_download_receipt_is_redacted_and_closes_url_hash_chain(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            selection = manifest["items"][0]["sources"]["selection"]
            receipt_path = root / selection["download_receipt"]["path"]
            receipt = load_json(receipt_path)
            receipt["http_headers"] = {"Cookie": "synthetic-secret-sentinel"}
            write_json(receipt_path, receipt)
            selection["download_receipt"]["sha256"] = gate.sha256_file(receipt_path)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "exactly the redacted local fields")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            selection = manifest["items"][0]["sources"]["selection"]
            receipt_path = root / selection["download_receipt"]["path"]
            receipt = load_json(receipt_path)
            receipt["url"] = "https://www.youtube.com/watch?v=different"
            write_json(receipt_path, receipt)
            selection["download_receipt"]["sha256"] = gate.sha256_file(receipt_path)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "not bound to the selected platform/url")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            selection = manifest["items"][0]["sources"]["selection"]
            receipt_path = root / selection["download_receipt"]["path"]
            receipt = load_json(receipt_path)
            receipt["derivation"]["output"]["sha256"] = "a" * 64
            write_json(receipt_path, receipt)
            selection["download_receipt"]["sha256"] = gate.sha256_file(receipt_path)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "output SHA is not the item clip SHA")

    def test_clip_must_be_ffprobe_decodable(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            clip = root / manifest["items"][0]["clip"]
            clip.write_bytes(b"not media")
            manifest["items"][0]["clip_sha256"] = gate.sha256_file(clip)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "is not ffprobe-decodable media")

    def test_cover_fallback_requires_both_platform_failures_and_no_usable_cover(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            sources = manifest["items"][1]["sources"]
            selected = sources["platforms"]["bilibili"]["candidates"][0]
            selected["version_kind"] = "original"
            selected["performer"] = "原唱示例"
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "without explicit cover_fallback")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            sources = manifest["items"][1]["sources"]
            selected = sources["platforms"]["bilibili"]["candidates"][0]
            selected["version_kind"] = "original"
            selected["performer"] = "原唱示例"
            sources["cover_fallback"] = {
                "used": True,
                "youtube_reason": "声称没有翻唱",
                "bilibili_reason": "声称没有翻唱",
            }
            self.save_manifest(root, manifest)
            self.assert_error(
                self.errors(root), "cannot fall back: a usable target cover exists"
            )

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            sources = manifest["items"][1]["sources"]
            for record in sources["platforms"].values():
                for candidate in record["candidates"]:
                    if candidate["version_kind"] == "cover":
                        candidate["usable"] = False
                        candidate["reject_reason"] = "synthetic unavailable cover"
            selected = sources["platforms"]["bilibili"]["candidates"][0]
            selected.update(
                {
                    "url": "https://www.bilibili.com/video/BVWrongOriginal",
                    "version_kind": "original",
                    "performer": "无关原唱",
                    "usable": True,
                    "reject_reason": None,
                }
            )
            sources["selection"]["url"] = selected["url"]
            sources["cover_fallback"] = {
                "used": True,
                "youtube_reason": "target cover unavailable",
                "bilibili_reason": "target cover unavailable",
            }
            self.save_manifest(root, manifest)
            self.assert_error(
                self.errors(root), "must select the declared original artist/version"
            )

    def test_official_mv_beats_nonofficial_candidate(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            sources = manifest["items"][1]["sources"]
            sources["selection"] = {
                "platform": "youtube",
                "url": "https://youtu.be/contractRank01",
                "decision_reason": "错误地偏好非官方现场",
            }
            sources["official_choice"] = {
                "selected_tier": "secondary",
                "fallback_reason": "错误地忽略了官方 MV",
            }
            self.save_manifest(root, manifest)
            self.assert_error(
                self.errors(root), "did not select the best available official source tier"
            )

    def test_vocal_evidence_is_bound_to_current_clip_hash(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            clip = root / manifest["items"][0]["clip"]
            clip.write_text("changed synthetic clip\n", encoding="utf-8")
            manifest["items"][0]["clip_sha256"] = gate.sha256_file(clip)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "not bound to the current clip path/hash")

    def test_vocal_analysis_must_bind_clip_sha_duration_and_window(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            evidence_path = root / manifest["items"][0]["evidence"]["path"]
            evidence = load_json(evidence_path)
            analysis_path = root / evidence["analysis"]["path"]
            analysis = load_json(analysis_path)
            analysis["source_sha256"] = "a" * 64
            write_json(analysis_path, analysis)
            evidence["analysis"]["sha256"] = gate.sha256_file(analysis_path)
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "analysis source_sha256 is not the current clip SHA")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            evidence_path = root / manifest["items"][0]["evidence"]["path"]
            evidence = load_json(evidence_path)
            evidence["window"]["show_end_src"] = 50.0
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "window exceeds the current clip duration")

    def test_vocal_evidence_supports_intro_hard_restart_mode(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            item = manifest["items"][0]
            evidence_path = root / item["evidence"]["path"]
            evidence = load_json(evidence_path)
            analysis_path = root / evidence["analysis"]["path"]
            analysis = load_json(analysis_path)
            analysis.update(
                {
                    "evidence_level": "multi_evidence",
                    "lead_segments": [[30.0, 39.7]],
                    "vocal_segments": [[30.0, 39.7]],
                    "boundary_segments": [[30.0, 39.7]],
                    "boundary_evidence": "whisper_word_timestamps",
                    "safe_cut_intervals": [[39.95, 40.2]],
                }
            )
            write_json(analysis_path, analysis)
            evidence.update(
                {
                    "mode": "intro_hard_restart",
                    "window": {
                        "narr_end_src": 0.0,
                        "show_start_src": 0.0,
                        "show_end_src": 40.0,
                    },
                    "status": "OK",
                }
            )
            evidence["analysis"]["sha256"] = gate.sha256_file(analysis_path)
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root))

            evidence["mode"] = "chorus_restart"
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "evidence.mode is invalid")

    def test_vocal_approval_is_bound_to_current_analysis_hash(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            analysis_path = root / "probe" / "vocal-analysis.json"
            analysis = load_json(analysis_path)
            analysis["evidence_level"] = "candidate"
            write_json(analysis_path, analysis)

            review_evidence_path = root / "probe" / "rank-02-review.txt"
            review_evidence_path.write_text(
                "Synthetic listening and performer-identity review\n", encoding="utf-8"
            )
            approval_path = root / "probe" / "rank-02-approval.json"
            approval = {
                "schema_version": 1,
                "approvals": {
                    "rank-02": {
                        "status": "approved",
                        "clip": "clips/rank-02.mp4",
                        "analysis_sha256": gate.showcase_align._analysis_fingerprint(analysis),
                        "window": {
                            "narr_end_src": 8.0,
                            "show_start_src": 10.0,
                            "show_end_src": 40.0,
                        },
                        "reason": "Synthetic manual identity and phrase-boundary review",
                        "evidence": ["synthetic listening record"],
                        "reviewer_kind": "human",
                        "reviewer": "fixture-human-reviewer",
                        "reviewed_at": "2026-08-10T12:00:00+08:00",
                        "evidence_files": [
                            {
                                "path": "probe/rank-02-review.txt",
                                "sha256": gate.sha256_file(review_evidence_path),
                            }
                        ],
                    }
                },
            }
            write_json(approval_path, approval)

            evidence_path = root / "probe" / "rank-02-showcase.json"
            evidence = load_json(evidence_path)
            evidence["status"] = "APPROVED"
            evidence["analysis"]["sha256"] = gate.sha256_file(analysis_path)
            evidence["approval"] = {
                "path": "probe/rank-02-approval.json",
                "sha256": gate.sha256_file(approval_path),
            }
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root))
            self.assertEqual([], self.errors(root, require_human_review=True))

            agent_observation = json.loads(json.dumps(approval))
            agent_row = agent_observation["approvals"]["rank-02"]
            agent_row.update({
                "status": "observed",
                "reviewer_kind": "agent",
                "reviewer": "codex-tool-assisted-review",
                "reason": "Tool-assisted audiovisual observation; human ear pending",
            })
            write_json(approval_path, agent_observation)
            evidence["status"] = "OBSERVED"
            evidence["approval"]["sha256"] = gate.sha256_file(approval_path)
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root))
            self.assert_error(
                self.errors(root, require_human_review=True),
                "approval.reviewer_kind must be human in release mode",
            )

            evidence["status"] = "APPROVED"

            invalid_reviews = (
                (
                    "unknown reviewer kind",
                    lambda row: row.update({"reviewer_kind": "automation"}),
                    "approval.reviewer_kind must be agent or human",
                ),
                (
                    "null reviewer kind",
                    lambda row: row.update({"reviewer_kind": None}),
                    "approval.reviewer_kind must be agent or human",
                ),
                (
                    "blank reviewer",
                    lambda row: row.update({"reviewer": ""}),
                    "approval.reviewer must be non-empty",
                ),
                (
                    "naive review time",
                    lambda row: row.update({"reviewed_at": "2026-08-10T12:00:00"}),
                    "approval.reviewed_at must be ISO-8601 with timezone",
                ),
            )
            for name, mutate, expected in invalid_reviews:
                with self.subTest(name=name):
                    invalid = json.loads(json.dumps(approval))
                    mutate(invalid["approvals"]["rank-02"])
                    write_json(approval_path, invalid)
                    evidence["approval"]["sha256"] = gate.sha256_file(approval_path)
                    write_json(evidence_path, evidence)
                    self.update_item_evidence_hash(root, manifest, 0)
                    self.save_manifest(root, manifest)
                    self.assert_error(self.errors(root), expected)

            write_json(approval_path, approval)
            evidence["approval"]["sha256"] = gate.sha256_file(approval_path)
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assertEqual([], self.errors(root))
            self.assertEqual([], self.errors(root, require_human_review=True))

            analysis["detector"] = "changed-after-approval"
            write_json(analysis_path, analysis)
            evidence["analysis"]["sha256"] = gate.sha256_file(analysis_path)
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 0)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "approval is invalid")

    def test_instrumental_plan_needs_continuity_and_manual_boundary_evidence(self) -> None:
        mutations = (
            (
                "continuity",
                lambda evidence: evidence["continuity"].update({"status": "declared"}),
                "continuity.status must be verified",
            ),
            (
                "boundary review",
                lambda evidence: evidence["boundaries"]["end"].pop("review"),
                "review.method must document the manual review",
            ),
            (
                "boundary evidence",
                lambda evidence: evidence["boundaries"]["start"].update(
                    {"evidence_files": []}
                ),
                "must contain at least one hash-bound evidence file",
            ),
        )
        for name, mutate, expected in mutations:
            with self.subTest(name=name), self.project() as root:
                manifest = load_json(root / "project-manifest.json")
                evidence_path = root / "probe" / "rank-01-instrumental.json"
                evidence = load_json(evidence_path)
                mutate(evidence)
                write_json(evidence_path, evidence)
                self.update_item_evidence_hash(root, manifest, 1)
                self.save_manifest(root, manifest)
                self.assert_error(self.errors(root), expected)

    def test_instrumental_plan_binds_real_clip_duration_and_window(self) -> None:
        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            evidence_path = root / manifest["items"][1]["evidence"]["path"]
            evidence = load_json(evidence_path)
            evidence["clip_duration_sec"] = 44.0
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 1)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "clip_duration_sec is stale")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            evidence_path = root / manifest["items"][1]["evidence"]["path"]
            evidence = load_json(evidence_path)
            evidence["window"]["end_sec"] = 50.0
            evidence["continuity"]["continuous_duration_sec"] = 50.0
            evidence["boundaries"]["end"]["time_sec"] = 50.0
            write_json(evidence_path, evidence)
            self.update_item_evidence_hash(root, manifest, 1)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "window exceeds the current clip duration")

    def test_nonfinite_or_malformed_json_fails_without_traceback(self) -> None:
        with self.project() as root:
            manifest_path = root / "project-manifest.json"
            payload = manifest_path.read_text(encoding="utf-8").replace(
                '"rank": 2', '"rank": NaN', 1
            )
            manifest_path.write_text(payload, encoding="utf-8")
            self.assert_error(self.errors(root), "non-standard numeric constant NaN")

        with self.project() as root:
            manifest_path = root / "project-manifest.json"
            payload = manifest_path.read_text(encoding="utf-8").replace(
                '"rank": 2', '"rank": 1e999', 1
            )
            manifest_path.write_text(payload, encoding="utf-8")
            self.assert_error(self.errors(root), "must be finite")

        with self.project() as root:
            manifest_path = root / "project-manifest.json"
            payload = manifest_path.read_text(encoding="utf-8").replace(
                '"schema_version": 2,', '"schema_version": 2,\n  "schema_version": 2,', 1
            )
            manifest_path.write_text(payload, encoding="utf-8")
            self.assert_error(self.errors(root), "duplicate JSON key 'schema_version'")

        with self.project() as root:
            manifest = load_json(root / "project-manifest.json")
            evidence_path = root / manifest["items"][0]["evidence"]["path"]
            evidence_path.write_text("{broken", encoding="utf-8")
            manifest["items"][0]["evidence"]["sha256"] = gate.sha256_file(evidence_path)
            self.save_manifest(root, manifest)
            self.assert_error(self.errors(root), "is not valid JSON")

    def test_countdown_build_stops_at_project_gate_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            process = subprocess.run(
                [sys.executable, str(COUNTDOWN_TEMPLATE)],
                cwd=root,
                text=True,
                capture_output=True,
            )
            self.assertEqual(2, process.returncode)
            self.assertIn("PROJECT CONTRACT: FAIL", process.stderr)
            self.assertEqual([], list(root.iterdir()))

    def test_checked_in_top_templates_are_five_to_one_with_full_cta(self) -> None:
        tree = ast.parse(COUNTDOWN_TEMPLATE.read_text(encoding="utf-8"))
        songs = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "songs"
                for target in node.targets
            ):
                songs = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(songs)
        self.assertEqual(
            ["05", "04", "03", "02", "01"], [song[2] for song in songs]
        )

        countdown_source = COUNTDOWN_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "from tools.video.outro_cta import FIXED_OUTRO_CTA", countdown_source
        )
        self.assertIn(
            '{FIXED_OUTRO_CTA.replace("。记得", "。<br>记得")}',
            countdown_source,
        )

        narration_source = NARRATION_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('"p1_pandora": "第五名', narration_source)
        self.assertIn('"p2_nahan": "第四名', narration_source)
        self.assertIn('"p3_pojian": "第三名', narration_source)
        self.assertIn('"p4_quanmian": "第二名', narration_source)
        self.assertIn('"p5_adiao": "第一名', narration_source)
        self.assertIn('"outro_cta": FIXED_OUTRO_CTA', narration_source)


if __name__ == "__main__":
    unittest.main()
