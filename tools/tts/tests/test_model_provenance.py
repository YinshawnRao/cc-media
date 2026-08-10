from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


TTS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TTS_ROOT.parents[1]
sys.path.insert(0, str(TTS_ROOT))

from model_provenance import (
    ProvenanceError,
    create_full_hash_receipt,
    model_candidates,
    tree_sha256,
    validate_receipt,
)


class ModelProvenanceTests(unittest.TestCase):
    def create_fixture(self, root: Path) -> tuple[Path, Path, Path, dict, Path]:
        root = root.resolve()
        tts_root = root / "tts"
        manifest_root = tts_root / "model-manifests"
        manifest_root.mkdir(parents=True)
        model = root / "model"
        (model / "speech_tokenizer").mkdir(parents=True)
        files = {
            "config.json": b'{"model":"synthetic"}\n',
            "model.safetensors": b"WEIGHTS-0001",
            "speech_tokenizer/config.json": b'{"codec":"synthetic"}\n',
            "speech_tokenizer/model.safetensors": b"CODEC-0001",
        }
        records = []
        for relative, payload in files.items():
            path = model / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            records.append(
                {
                    "bytes": len(payload),
                    "path": relative,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        records.sort(key=lambda item: item["path"])
        tree_digest = tree_sha256(records)
        manifest = {
            "schema_version": 1,
            "kind": "tree",
            "passed": True,
            "errors": [],
            "excluded_directories": [".cache"],
            "file_count": len(records),
            "total_bytes": sum(item["bytes"] for item in records),
            "files": records,
            "sha256": tree_digest,
        }
        manifest_file = manifest_root / "manifest.json"
        manifest_file.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        qwen = {
            "engine": "qwen3-tts-base-mlx",
            "model_id": "synthetic/qwen",
            "model_revision": "fixed-revision",
            "model_tree_sha256": tree_digest,
            "model_file_manifest": "model-manifests/manifest.json",
            "mlx_audio_version": "0.4.5",
            "generation": {"seed": 20260809},
        }
        manifest_digest = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
        receipt = (
            tts_root
            / "runtime"
            / "model-verifications"
            / f"manifest-{manifest_digest[:16]}.json"
        )
        return tts_root, model, manifest_file, qwen, receipt

    def issue_receipt(
        self, tts_root: Path, model: Path, manifest: Path, qwen: dict
    ) -> dict:
        return create_full_hash_receipt(
            model_root=model,
            manifest_file=manifest,
            qwen=qwen,
            mlx_audio_version="0.4.5",
            tts_root=tts_root,
        )

    def validate(
        self, tts_root: Path, model: Path, manifest: Path, qwen: dict
    ) -> dict:
        return validate_receipt(
            model_root=model,
            manifest_file=manifest,
            qwen=qwen,
            mlx_audio_version="0.4.5",
            tts_root=tts_root,
        )

    def test_full_hash_receipt_allows_cheap_current_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, receipt = self.create_fixture(Path(temporary))
            self.issue_receipt(tts_root, model, manifest, qwen)
            validation = self.validate(tts_root, model, manifest, qwen)
            self.assertTrue(validation["full_tree_hash_verified"])
            self.assertEqual(
                validation["verified_model_tree_sha256"],
                qwen["model_tree_sha256"],
            )
            self.assertNotIn(str(model.resolve()), json.dumps(validation))
            self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
            self.assertRegex(validation["qwen_config_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(validation["portable_claim_sha256"], r"^[0-9a-f]{64}$")

    def test_missing_receipt_fails_closed_with_recovery_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            with self.assertRaisesRegex(ProvenanceError, "doctor.py --full-model-hash"):
                self.validate(tts_root, model, manifest, qwen)

    def test_actual_mlx_audio_version_must_match_fixed_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            with self.assertRaisesRegex(ProvenanceError, "version mismatch"):
                self.issue_receipt(
                    tts_root,
                    model,
                    manifest,
                    {**qwen, "mlx_audio_version": "9.9.9"},
                )

    def test_same_size_weight_change_invalidates_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            issued = self.issue_receipt(tts_root, model, manifest, qwen)
            weight = model / "model.safetensors"
            old_mtime = weight.stat().st_mtime_ns
            weight.write_bytes(b"X" * len(b"WEIGHTS-0001"))
            os.utime(
                weight,
                ns=(weight.stat().st_atime_ns, old_mtime),
            )
            with self.assertRaisesRegex(ProvenanceError, "changed since full verification"):
                self.validate(tts_root, model, manifest, qwen)
            self.assertIn(
                "ctime_ns",
                next(item for item in issued["files"] if item["path"] == "model.safetensors"),
            )

    def test_full_hash_refuses_same_size_wrong_weight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, receipt = self.create_fixture(Path(temporary))
            weight = model / "model.safetensors"
            weight.write_bytes(b"X" * len(b"WEIGHTS-0001"))
            with self.assertRaisesRegex(
                ProvenanceError, "full model tree SHA-256 mismatch"
            ):
                self.issue_receipt(tts_root, model, manifest, qwen)
            self.assertFalse(receipt.exists())

    def test_file_collection_change_invalidates_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            self.issue_receipt(tts_root, model, manifest, qwen)
            (model / "unexpected.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ProvenanceError, "file set mismatch"):
                self.validate(tts_root, model, manifest, qwen)

    def test_receipt_requires_0600_and_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, receipt = self.create_fixture(Path(temporary))
            self.issue_receipt(tts_root, model, manifest, qwen)
            receipt.chmod(0o644)
            with self.assertRaisesRegex(ProvenanceError, "mode must be 0600"):
                self.validate(tts_root, model, manifest, qwen)
            receipt.chmod(0o600)
            outside = Path(temporary).resolve() / "outside-receipt.json"
            shutil.copy2(receipt, outside)
            receipt.unlink()
            receipt.symlink_to(outside)
            with self.assertRaisesRegex(ProvenanceError, "must not be a symlink"):
                self.validate(tts_root, model, manifest, qwen)

    def test_receipt_parent_symlink_is_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, receipt = self.create_fixture(Path(temporary))
            self.issue_receipt(tts_root, model, manifest, qwen)
            outside = Path(temporary).resolve() / "outside-runtime"
            outside.mkdir()
            shutil.copy2(receipt, outside / receipt.name)
            receipt.unlink()
            receipt.parent.rmdir()
            receipt.parent.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ProvenanceError, "parent must not be a symlink"):
                self.validate(tts_root, model, manifest, qwen)

    def test_manifest_is_fixed_to_secure_manifest_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            outside = Path(temporary).resolve() / "outside-manifest.json"
            shutil.copy2(manifest, outside)
            manifest.unlink()
            manifest.symlink_to(outside)
            with self.assertRaisesRegex(ProvenanceError, "must not be a symlink"):
                self.issue_receipt(tts_root, model, manifest, qwen)
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            unsafe = {**qwen, "model_file_manifest": "../outside.json"}
            with self.assertRaisesRegex(ProvenanceError, "must stay under"):
                self.issue_receipt(tts_root, model, manifest, unsafe)

    def test_group_or_world_writable_model_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            (model / "model.safetensors").chmod(0o666)
            with self.assertRaisesRegex(ProvenanceError, "group/world writable"):
                self.issue_receipt(tts_root, model, manifest, qwen)

    def test_relative_config_candidate_preserves_symlink_for_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            tts_root, model, manifest, qwen, _ = self.create_fixture(Path(temporary))
            configured = tts_root / "models" / "configured-model"
            configured.parent.mkdir()
            configured.symlink_to(model, target_is_directory=True)
            config = {
                "runtime": {
                    "qwen_base_model_envs": [],
                    "qwen_base_model_candidates": ["models/configured-model"],
                }
            }
            candidate = model_candidates(config, tts_root)[0]
            self.assertEqual(candidate, configured)
            self.assertTrue(candidate.is_symlink())
            with self.assertRaisesRegex(ProvenanceError, "must not be a symlink"):
                self.issue_receipt(tts_root, candidate, manifest, qwen)

    def test_portable_claim_is_stable_across_trusted_model_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            first = self.create_fixture(base / "first")
            second = self.create_fixture(base / "second")
            self.issue_receipt(first[0], first[1], first[2], first[3])
            self.issue_receipt(second[0], second[1], second[2], second[3])
            first_validation = self.validate(first[0], first[1], first[2], first[3])
            second_validation = self.validate(second[0], second[1], second[2], second[3])
            self.assertEqual(
                first_validation["portable_claim_sha256"],
                second_validation["portable_claim_sha256"],
            )
            self.assertNotEqual(
                first_validation["receipt_sha256"], second_validation["receipt_sha256"]
            )

    def test_runtime_receipt_directory_is_gitignored(self) -> None:
        ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("tools/tts/runtime/", ignore)


if __name__ == "__main__":
    unittest.main()
