from __future__ import annotations

import ast
import ctypes
import importlib.util
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


TTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TTS_ROOT))

import metal_preflight
import narrate


def load_qwen_worker():
    worker_path = TTS_ROOT / "engines" / "qwen_mlx.py"
    spec = importlib.util.spec_from_file_location("qwen_mlx_preflight_test", worker_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCreateDefaultDevice:
    def __init__(self, result: int | None) -> None:
        self.result = result
        self.argtypes = None
        self.restype = None

    def __call__(self) -> int | None:
        return self.result


class MetalProbeTests(unittest.TestCase):
    def test_non_null_default_device_passes(self) -> None:
        create = FakeCreateDefaultDevice(1)
        library = type("FakeMetal", (), {"MTLCreateSystemDefaultDevice": create})()
        loader = Mock(return_value=library)

        available = metal_preflight.default_metal_device_available(
            platform_name="darwin", library_loader=loader
        )

        self.assertTrue(available)
        loader.assert_called_once_with(metal_preflight.METAL_FRAMEWORK)
        self.assertEqual(create.argtypes, [])
        self.assertIs(create.restype, ctypes.c_void_p)

    def test_null_default_device_fails_without_exception_details(self) -> None:
        create = FakeCreateDefaultDevice(None)
        library = type("FakeMetal", (), {"MTLCreateSystemDefaultDevice": create})()

        self.assertFalse(
            metal_preflight.default_metal_device_available(
                platform_name="darwin", library_loader=Mock(return_value=library)
            )
        )

    def test_loader_error_is_a_clean_failure(self) -> None:
        def failing_loader(_path: str) -> object:
            raise OSError("native detail /private/secret")

        self.assertFalse(
            metal_preflight.default_metal_device_available(
                platform_name="darwin", library_loader=failing_loader
            )
        )

    def test_non_darwin_does_not_load_framework(self) -> None:
        loader = Mock(side_effect=AssertionError("loader must not run"))

        self.assertFalse(
            metal_preflight.default_metal_device_available(
                platform_name="linux", library_loader=loader
            )
        )
        loader.assert_not_called()

    def test_cli_failure_is_fixed_and_path_free(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(
            metal_preflight, "default_metal_device_available", return_value=False
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = metal_preflight.main()

        self.assertEqual(code, metal_preflight.EXIT_UNAVAILABLE)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), metal_preflight.FAIL_MESSAGE)
        self.assertNotIn("/private/", stderr.getvalue())

    def test_cli_success_has_stable_contract(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(
            metal_preflight, "default_metal_device_available", return_value=True
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = metal_preflight.main()

        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue().strip(), metal_preflight.PASS_MESSAGE)
        self.assertEqual(stderr.getvalue(), "")

    def test_probe_module_never_imports_mlx(self) -> None:
        tree = ast.parse(
            (TTS_ROOT / "metal_preflight.py").read_text(encoding="utf-8")
        )
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        self.assertFalse(
            [name for name in imported if name == "mlx" or name.startswith("mlx.")]
        )
        self.assertFalse([name for name in imported if name.startswith("mlx_audio")])


class DispatcherGuardTests(unittest.TestCase):
    def test_qwen_failure_never_launches_worker_and_hides_child_error(self) -> None:
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(
                command,
                metal_preflight.EXIT_UNAVAILABLE,
                stdout="",
                stderr="native failure at /private/secret",
            )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = narrate.run_worker(
                python=Path("qwen-python"),
                worker=Path("qwen-worker.py"),
                request={"items": []},
                requires_metal=True,
                runner=runner,
            )

        self.assertEqual(code, metal_preflight.EXIT_UNAVAILABLE)
        self.assertEqual(len(calls), 1)
        self.assertEqual(Path(calls[0][0][1]).name, "metal_preflight.py")
        self.assertEqual(stderr.getvalue().strip(), metal_preflight.FAIL_MESSAGE)
        self.assertNotIn("/private/secret", stderr.getvalue())

    def test_qwen_success_launches_worker_after_preflight(self) -> None:
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            if len(calls) == 1:
                return subprocess.CompletedProcess(
                    command, 0, stdout=metal_preflight.PASS_MESSAGE + "\n", stderr=""
                )
            return subprocess.CompletedProcess(command, 0)

        code = narrate.run_worker(
            python=Path("qwen-python"),
            worker=Path("qwen-worker.py"),
            request={"items": []},
            requires_metal=True,
            runner=runner,
        )

        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(Path(calls[0][0][1]).name, "metal_preflight.py")
        self.assertEqual(Path(calls[1][0][1]).name, "qwen-worker.py")

    def test_kokoro_bypasses_metal_preflight(self) -> None:
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0)

        code = narrate.run_worker(
            python=Path("kokoro-python"),
            worker=Path("kokoro-worker.py"),
            request={"items": []},
            requires_metal=False,
            runner=runner,
        )

        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(Path(calls[0][0][1]).name, "kokoro-worker.py")

    def test_timeout_fails_closed_without_launching_worker(self) -> None:
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            raise subprocess.TimeoutExpired(command, 1, stderr="/private/secret")

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = narrate.run_worker(
                python=Path("qwen-python"),
                worker=Path("qwen-worker.py"),
                request={"items": []},
                requires_metal=True,
                runner=runner,
            )

        self.assertEqual(code, metal_preflight.EXIT_UNAVAILABLE)
        self.assertEqual(len(calls), 1)
        self.assertEqual(stderr.getvalue().strip(), metal_preflight.FAIL_MESSAGE)
        self.assertNotIn("/private/secret", stderr.getvalue())


class WorkerImportBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.worker = load_qwen_worker()

    def test_worker_has_no_top_level_mlx_import(self) -> None:
        tree = ast.parse(
            (TTS_ROOT / "engines" / "qwen_mlx.py").read_text(encoding="utf-8")
        )
        top_level_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_level_imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_level_imports.append(node.module)
        self.assertFalse(
            [
                name
                for name in top_level_imports
                if name == "mlx"
                or name.startswith("mlx.")
                or name.startswith("mlx_audio")
            ]
        )

    def test_direct_worker_failure_never_calls_runtime_loader(self) -> None:
        runtime_loader = Mock(side_effect=AssertionError("MLX loader must not run"))
        bootstrap = Mock(side_effect=AssertionError("bootstrap must not run"))
        stderr = io.StringIO()
        with patch.object(
            self.worker,
            "require_default_metal_device",
            side_effect=metal_preflight.MetalUnavailable(
                metal_preflight.FAIL_MESSAGE
            ),
        ):
            with patch.object(self.worker, "bootstrap_offline_runtime", bootstrap):
                with patch.object(self.worker, "load_mlx_runtime", runtime_loader):
                    with redirect_stderr(stderr):
                        code = self.worker.main(["--request", "never-read.json"])

        self.assertEqual(code, metal_preflight.EXIT_UNAVAILABLE)
        bootstrap.assert_not_called()
        runtime_loader.assert_not_called()
        self.assertEqual(stderr.getvalue().strip(), metal_preflight.FAIL_MESSAGE)

    def test_authorized_worker_initializes_without_global_serialization(self) -> None:
        events = []
        runtime = (object(), object(), object(), object())

        def preflight() -> None:
            events.append("preflight")

        def bootstrap() -> None:
            events.append("bootstrap")

        def loader():
            events.append("load")
            return runtime

        with patch.object(self.worker, "require_default_metal_device", preflight):
            with patch.object(self.worker, "bootstrap_offline_runtime", bootstrap):
                with patch.object(self.worker, "load_mlx_runtime", loader):
                    actual = self.worker.initialize_mlx_runtime()

        self.assertEqual(actual, runtime)
        self.assertEqual(events, ["preflight", "bootstrap", "load"])
        source = (TTS_ROOT / "engines" / "qwen_mlx.py").read_text(encoding="utf-8")
        self.assertNotIn("threading.Lock", source)
        self.assertNotIn("FileLock", source)
        self.assertNotIn("Semaphore", source)


if __name__ == "__main__":
    unittest.main()
