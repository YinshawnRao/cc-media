import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.video import resource_budget


REPO_ROOT = Path(__file__).resolve().parents[3]


class ResourceBudgetTests(unittest.TestCase):
    @staticmethod
    def fake_identity(pid: int) -> resource_budget.ProcessIdentity:
        return resource_budget.ProcessIdentity(pid, os.getuid(), 123456789, 42)

    def test_adaptive_leases_select_4_then_3_then_2_without_waiting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            leases = []
            try:
                for _ in range(3):
                    leases.append(
                        resource_budget.resolve_ffmpeg_threads(
                            environ={},
                            registry_dir=registry,
                            identity_reader=self.fake_identity,
                        )
                    )
                self.assertEqual([4, 3, 2], [lease.threads for lease in leases])
                self.assertEqual([1, 2, 3], [lease.active_workers for lease in leases])
                self.assertTrue(all(lease.adaptive for lease in leases))
            finally:
                for lease in reversed(leases):
                    lease.close()

    def test_finished_and_pid_reused_markers_do_not_keep_future_work_throttled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            identities = {
                101: resource_budget.ProcessIdentity(101, os.getuid(), 1000, 1),
                102: resource_budget.ProcessIdentity(102, os.getuid(), 1000, 2),
            }

            def reader(pid: int):
                return identities.get(pid)

            stale = resource_budget.resolve_ffmpeg_threads(
                environ={}, registry_dir=registry, identity_reader=reader, pid=101
            )
            self.assertEqual(4, stale.threads)
            # The same PID now identifies a different process. The old marker
            # must be discarded rather than counted as a live worker.
            identities[101] = resource_budget.ProcessIdentity(
                101, os.getuid(), 2000, 1
            )
            current = resource_budget.resolve_ffmpeg_threads(
                environ={}, registry_dir=registry, identity_reader=reader, pid=102
            )
            try:
                self.assertEqual(4, current.threads)
                self.assertEqual(1, current.active_workers)
            finally:
                current.close()
                stale.close()

    def test_marker_scanner_never_follows_symlink_fifo_directory_or_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = root / "registry"
            registry.mkdir(mode=0o700)
            sentinel = root / "sentinel"
            sentinel.write_text("do-not-read-or-delete", encoding="utf-8")
            (registry / "lease-symlink.json").symlink_to(sentinel)
            (registry / "lease-directory.json").mkdir()
            os.mkfifo(registry / "lease-fifo.json", 0o600)
            hardlink_source = root / "hardlink-source"
            hardlink_source.write_text("{}", encoding="utf-8")
            hardlink_source.chmod(0o600)
            os.link(hardlink_source, registry / "lease-hardlink.json")

            lease = resource_budget.resolve_ffmpeg_threads(
                environ={},
                registry_dir=registry,
                identity_reader=self.fake_identity,
            )
            try:
                self.assertEqual(4, lease.threads)
                self.assertEqual(1, lease.active_workers)
                self.assertEqual("do-not-read-or-delete", sentinel.read_text(encoding="utf-8"))
                self.assertEqual(2, hardlink_source.stat().st_nlink)
            finally:
                lease.close()

    def test_registry_symlink_fails_safe_to_two_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir(mode=0o700)
            registry = root / "registry"
            registry.symlink_to(target, target_is_directory=True)
            lease = resource_budget.resolve_ffmpeg_threads(
                environ={},
                registry_dir=registry,
                identity_reader=self.fake_identity,
            )
            self.assertEqual(2, lease.threads)
            self.assertEqual(0, lease.active_workers)
            self.assertEqual([], list(target.iterdir()))
            lease.close()

    def test_overlapping_real_processes_all_start_and_receive_4_3_2(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            code = (
                "import sys; from pathlib import Path; "
                "from tools.video import resource_budget as r; "
                "lease=r.resolve_ffmpeg_threads(environ={},registry_dir=Path(sys.argv[1])); "
                "print(lease.threads,flush=True); sys.stdin.read(1); lease.close()"
            )
            processes: list[subprocess.Popen[str]] = []
            observed: list[int] = []
            try:
                for _ in range(3):
                    process = subprocess.Popen(
                        [sys.executable, "-c", code, str(registry)],
                        cwd=REPO_ROOT,
                        text=True,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    processes.append(process)
                    assert process.stdout is not None
                    observed.append(int(process.stdout.readline().strip()))
                self.assertEqual([4, 3, 2], observed)
                self.assertTrue(all(process.poll() is None for process in processes))
            finally:
                for process in processes:
                    if process.stdin is not None:
                        process.stdin.write("x")
                        process.stdin.flush()
                        process.stdin.close()
                    process.wait(timeout=5)
                    if process.stdout is not None:
                        process.stdout.close()
                    if process.stderr is not None:
                        process.stderr.close()

    def test_manual_ffmpeg_override_wins_over_adaptive_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            first = resource_budget.resolve_ffmpeg_threads(
                environ={},
                registry_dir=registry,
                identity_reader=self.fake_identity,
            )
            try:
                manual = resource_budget.resolve_ffmpeg_threads(
                    environ={resource_budget.FFMPEG_THREADS_ENV: "1"},
                    registry_dir=registry,
                    identity_reader=self.fake_identity,
                )
                try:
                    self.assertEqual(1, manual.threads)
                    self.assertEqual(2, manual.active_workers)
                    self.assertFalse(manual.adaptive)
                finally:
                    manual.close()
            finally:
                first.close()

    def test_registry_failure_falls_back_to_two_without_blocking(self) -> None:
        def unavailable(_pid: int):
            raise OSError("synthetic process registry failure")

        lease = resource_budget.resolve_ffmpeg_threads(
            environ={}, identity_reader=unavailable
        )
        self.assertEqual(2, lease.threads)
        self.assertEqual(0, lease.active_workers)
        self.assertTrue(lease.adaptive)
        lease.close()

    def test_ffmpeg_cli_holds_lease_and_substitutes_thread_tokens(self) -> None:
        env = {
            **os.environ,
            resource_budget.FFMPEG_THREADS_ENV: "3",
        }
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "tools/video/resource_budget.py"),
                "ffmpeg",
                "--",
                "/bin/echo",
                resource_budget.THREAD_TOKEN,
                resource_budget.THREAD_TOKEN,
            ],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("3 3", completed.stdout.strip())

    def test_hyperframes_cli_injects_workers_without_queueing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            capture = Path(temporary) / "capture-args"
            capture.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\"\n",
                encoding="utf-8",
            )
            capture.chmod(0o755)
            env = {
                **os.environ,
                resource_budget.HYPERFRAMES_WORKERS_ENV: "3",
            }
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools/video/resource_budget.py"),
                    "hyperframes",
                    "--",
                    str(capture),
                    "render",
                    "--sdr",
                ],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            ["render", "--sdr", "--workers", "3"],
            completed.stdout.splitlines(),
        )

    def test_hyperframes_explicit_workers_win_and_invalid_values_fail_closed(self) -> None:
        self.assertEqual(
            4,
            resource_budget._hyperframes_explicit_workers(
                ["npx", "hyperframes", "render", "--workers", "4"]
            ),
        )
        for command in (
            ["render", "--workers", "auto"],
            ["render", "--workers", "0"],
            ["render", "--workers=5"],
            ["render", "--workers", "2", "--workers=3"],
        ):
            with self.subTest(command=command), self.assertRaises(ValueError):
                resource_budget._hyperframes_explicit_workers(command)

    def test_default_asr_budget_overrides_inherited_unbounded_pools(self) -> None:
        environ = {
            "OMP_NUM_THREADS": "64",
            "OPENBLAS_NUM_THREADS": "64",
            "TOKENIZERS_PARALLELISM": "true",
        }
        budget = resource_budget.configure_asr_environment(environ)
        self.assertEqual(2, budget.threads)
        self.assertEqual(1, budget.interop_threads)
        for key in (
            "OMP_NUM_THREADS",
            "OMP_THREAD_LIMIT",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "BLIS_NUM_THREADS",
        ):
            self.assertEqual("2", environ[key])
        self.assertEqual("false", environ["TOKENIZERS_PARALLELISM"])

    def test_asr_budget_has_explicit_per_process_overrides(self) -> None:
        environ = {
            resource_budget.ASR_THREADS_ENV: "3",
            resource_budget.ASR_INTEROP_THREADS_ENV: "2",
        }
        budget = resource_budget.configure_asr_environment(environ)
        self.assertEqual((3, 2), (budget.threads, budget.interop_threads))
        self.assertEqual("3", environ["OMP_NUM_THREADS"])

    def test_invalid_budget_is_rejected_instead_of_becoming_unbounded(self) -> None:
        for raw in ("0", "00", "-1", "5", "999999", "many"):
            with self.subTest(raw=raw), self.assertRaisesRegex(
                ValueError,
                "must be an integer from 1 to 4",
            ):
                resource_budget.configure_asr_environment(
                    {resource_budget.ASR_THREADS_ENV: raw}
                )

    def test_torch_intra_and_interop_pools_are_limited(self) -> None:
        class FakeTorch:
            def __init__(self) -> None:
                self.intra = None
                self.interop = None

            def set_num_threads(self, value: int) -> None:
                self.intra = value

            def set_num_interop_threads(self, value: int) -> None:
                self.interop = value

            def get_num_interop_threads(self) -> int:
                return int(self.interop)

        fake = FakeTorch()
        resource_budget.configure_torch_runtime(
            fake,
            resource_budget.ASRResourceBudget(threads=3, interop_threads=1),
        )
        self.assertEqual(3, fake.intra)
        self.assertEqual(1, fake.interop)

    def test_python_budget_module_contains_no_waiting_primitives(self) -> None:
        for relative in (
            "tools/video/resource_budget.py",
            "tools/video/offline_asr.py",
            "tools/video/vocal_segments.py",
        ):
            with self.subTest(relative=relative):
                source_path = REPO_ROOT / relative
                tree = ast.parse(source_path.read_text(encoding="utf-8"))
                imported_roots = {
                    alias.name.split(".")[0]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                imported_from = {
                    (node.module or "").split(".")[0]
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                }
                called_names = {
                    node.func.id
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                }
                called_attributes = {
                    node.func.attr
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                }
                self.assertTrue(
                    {"threading", "multiprocessing", "fcntl", "time"}.isdisjoint(
                        imported_roots | imported_from
                    )
                )
                self.assertTrue(
                    {"sleep", "wait", "acquire", "flock"}.isdisjoint(
                        called_names | called_attributes
                    )
                )
        shell_source = (REPO_ROOT / "tools/video/vfill.sh").read_text(encoding="utf-8")
        for forbidden in ("flock ", "sleep ", "wait "):
            self.assertNotIn(forbidden, shell_source)

    def test_offline_asr_applies_override_before_loading_whisper(self) -> None:
        env = {
            **os.environ,
            resource_budget.ASR_THREADS_ENV: "3",
            resource_budget.ASR_INTEROP_THREADS_ENV: "1",
        }
        code = (
            "import json, os; "
            "from tools.video import offline_asr; "
            "print(json.dumps({k: os.environ[k] for k in "
            "['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', "
            "'VECLIB_MAXIMUM_THREADS', 'TOKENIZERS_PARALLELISM']}))"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            {
                "OMP_NUM_THREADS": "3",
                "OPENBLAS_NUM_THREADS": "3",
                "VECLIB_MAXIMUM_THREADS": "3",
                "TOKENIZERS_PARALLELISM": "false",
            },
            json.loads(completed.stdout),
        )

    def test_vfill_passes_configured_budget_to_decoder_filters_and_encoder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capture = root / "ffmpeg-args.txt"
            fake_ffmpeg = root / "ffmpeg"
            fake_ffprobe = root / "ffprobe"
            fake_ffmpeg.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$CC_MEDIA_TEST_CAPTURE\"\n",
                encoding="utf-8",
            )
            fake_ffprobe.write_text("#!/bin/sh\necho 1080x1920\n", encoding="utf-8")
            fake_ffmpeg.chmod(0o755)
            fake_ffprobe.chmod(0o755)
            source = root / "input.mp4"
            source.write_bytes(b"synthetic")
            output = root / "output.mp4"
            env = {
                **os.environ,
                "PATH": f"{root}:/usr/bin:/bin",
                "CC_MEDIA_FFMPEG_THREADS": "3",
                "CC_MEDIA_TEST_CAPTURE": str(capture),
            }
            completed = subprocess.run(
                [
                    "bash",
                    str(REPO_ROOT / "tools/video/vfill.sh"),
                    str(source),
                    str(output),
                    "864:1080:528:0",
                ],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            args = capture.read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, args.count("-threads"))
            self.assertEqual("3", args[args.index("-filter_threads") + 1])
            self.assertEqual("3", args[args.index("-filter_complex_threads") + 1])
            thread_positions = [i for i, value in enumerate(args) if value == "-threads"]
            self.assertEqual(["3", "3"], [args[i + 1] for i in thread_positions])

    def test_vfill_rejects_invalid_thread_override_before_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "ffmpeg-ran"
            fake_ffmpeg = root / "ffmpeg"
            fake_ffmpeg.write_text(
                "#!/bin/sh\ntouch \"$CC_MEDIA_TEST_MARKER\"\n",
                encoding="utf-8",
            )
            fake_ffmpeg.chmod(0o755)
            for raw in ("0", "00", "5", "999999", "many"):
                with self.subTest(raw=raw):
                    env = {
                        **os.environ,
                        "PATH": f"{root}:/usr/bin:/bin",
                        "CC_MEDIA_FFMPEG_THREADS": raw,
                        "CC_MEDIA_TEST_MARKER": str(marker),
                    }
                    completed = subprocess.run(
                        [
                            "bash",
                            str(REPO_ROOT / "tools/video/vfill.sh"),
                            "input.mp4",
                            "output.mp4",
                            "864:1080:528:0",
                        ],
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(2, completed.returncode)
                    self.assertFalse(marker.exists())

    def test_countdown_runner_holds_lease_and_scopes_ffmpeg_threads(self) -> None:
        source = (REPO_ROOT / "tools/video/countdown_build.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        selected = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"_budgeted_ffmpeg_command", "run"}
        ]

        class FakeLease:
            threads = 3
            active = False

            def __enter__(self):
                self.active = True
                return self

            def __exit__(self, *_args):
                self.active = False

        lease = FakeLease()
        captured: list[list[str]] = []

        def fake_run(command, *, check):
            self.assertTrue(check)
            self.assertTrue(lease.active)
            captured.append(command)

        namespace = {
            "Path": Path,
            "subprocess": SimpleNamespace(run=fake_run),
            "_resource_budget": SimpleNamespace(
                resolve_ffmpeg_threads=lambda: lease
            ),
        }
        exec(compile(ast.Module(body=selected, type_ignores=[]), "countdown", "exec"), namespace)
        command = [
            "ffmpeg", "-v", "error",
            "-i", "clip.mp4", "-i", "voice.wav",
            "-filter_complex", "[0:a][1:a]amix[out]",
            "-map", "[out]", "segment.wav", "-y",
        ]
        namespace["run"](command)

        self.assertFalse(lease.active)
        self.assertEqual(1, len(captured))
        budgeted = captured[0]
        self.assertEqual(
            ["-filter_threads", "3", "-filter_complex_threads", "3"],
            budgeted[1:5],
        )
        for index, token in enumerate(budgeted):
            if token == "-i":
                self.assertEqual(["-threads", "3"], budgeted[index - 2:index])
        output_index = budgeted.index("segment.wav")
        self.assertEqual(["-threads", "3"], budgeted[output_index - 2:output_index])

    def test_countdown_runner_leaves_non_ffmpeg_commands_unregistered(self) -> None:
        source = (REPO_ROOT / "tools/video/countdown_build.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        selected = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"_budgeted_ffmpeg_command", "run"}
        ]
        captured: list[list[str]] = []

        def unexpected_lease():
            self.fail("non-FFmpeg command must not acquire a media lease")

        namespace = {
            "Path": Path,
            "subprocess": SimpleNamespace(
                run=lambda command, *, check: captured.append([*command, str(check)])
            ),
            "_resource_budget": SimpleNamespace(
                resolve_ffmpeg_threads=unexpected_lease
            ),
        }
        exec(compile(ast.Module(body=selected, type_ignores=[]), "countdown", "exec"), namespace)
        namespace["run"](["echo", "ready"])
        self.assertEqual([["echo", "ready", "True"]], captured)


if __name__ == "__main__":
    unittest.main()
