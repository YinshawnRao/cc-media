from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import setup_qwen_models as setup


class ModelInstallationTests(unittest.TestCase):
    def test_verify_only_checks_contents_without_runtime_or_network(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            model = root / "models" / "test@fixed-revision"
            model.mkdir(parents=True)
            payload = b"fixed model bytes"
            weight = model / "model.safetensors"
            weight.write_bytes(payload)
            manifest = {
                "source": "models/test@fixed-revision",
                "file_count": 1,
                "total_bytes": len(payload),
                "files": [{"path": weight.name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}],
            }
            manifests = root / "model-manifests"
            manifests.mkdir()
            (manifests / "test.json").write_text(json.dumps(manifest))
            with patch.object(setup, "TTS_ROOT", root), patch.object(setup, "MODELS", {"base": "test.json"}), patch.object(sys, "argv", ["setup", "--verify-only"]), patch.dict(sys.modules, {"huggingface_hub": None}), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(setup.main(), 0)
                # Same length, different contents must still be rejected.
                weight.write_bytes(b"x" * len(payload))
                with self.assertRaisesRegex(SystemExit, "checksum mismatch"):
                    setup.main()
                weight.unlink()
                with self.assertRaisesRegex(SystemExit, "missing:"):
                    setup.main()
                external = root / "external.safetensors"
                external.write_bytes(payload)
                weight.symlink_to(external)
                with patch.object(sys, "argv", ["setup"]):
                    with self.assertRaisesRegex(SystemExit, "outside model directory"):
                        setup.main()

    def test_external_weight_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            model = root / "model"
            model.mkdir()
            external = root / "external.safetensors"
            external.write_bytes(b"model")
            (model / "model.safetensors").symlink_to(external)
            manifest = {"files": [{"path": "model.safetensors", "bytes": 5, "sha256": hashlib.sha256(b"model").hexdigest()}]}
            self.assertEqual(setup.verify_files(model, manifest), ["outside model directory: model.safetensors"])


if __name__ == "__main__":
    unittest.main()
