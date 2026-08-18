import contextlib
import io
import os
import stat
import subprocess
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from tools.video import yt_dlp_readonly


SYNTHETIC_COOKIE = (
    b"# Netscape HTTP Cookie File\n"
    b".example.invalid\tTRUE\t/\tTRUE\t4102444800\tSESSION\t"
    b"synthetic-never-real\n"
)


class ReadonlyYtDlpTests(unittest.TestCase):
    def make_layout(self, base: Path) -> tuple[Path, Path, Path]:
        repo = base / "repo"
        temp_parent = base / "private-temp"
        repo.mkdir()
        temp_parent.mkdir()
        cookie = repo / "all_cookies.txt"
        cookie.write_bytes(SYNTHETIC_COOKIE)
        os.chmod(cookie, 0o600)
        return repo, temp_parent, cookie

    def run_guard(self, repo: Path, temp_parent: Path, cookie: Path, runner):
        return yt_dlp_readonly.run_yt_dlp(
            ["--skip-download", "https://example.invalid/video"],
            canonical=cookie,
            repo_root=repo,
            temp_parent=temp_parent,
            runner=runner,
        )

    def test_cli_help_is_successful_and_does_not_read_canonical(self):
        for option in ("-h", "--help"):
            with self.subTest(option=option):
                stdout = io.StringIO()
                with mock.patch.object(
                    yt_dlp_readonly,
                    "run_yt_dlp",
                    side_effect=AssertionError("help must not start Cookie handling"),
                ), contextlib.redirect_stdout(stdout):
                    result = yt_dlp_readonly.main([option])
                output = stdout.getvalue()
                self.assertEqual(0, result)
                self.assertIn("Usage:", output)
                self.assertIn("yt_dlp_readonly.py -- <yt-dlp arguments>", output)
                self.assertNotIn(str(yt_dlp_readonly.CANONICAL_COOKIE), output)
                self.assertNotIn("synthetic-never-real", output)

    def test_runner_receives_only_private_copy_and_canonical_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            before = cookie.stat()
            seen = {}

            def fake_runner(command, *, check):
                self.assertFalse(check)
                snapshot = Path(command[command.index("--cookies") + 1])
                seen["command"] = command
                seen["snapshot"] = snapshot
                self.assertFalse(snapshot.is_relative_to(repo))
                self.assertEqual(0o700, stat.S_IMODE(snapshot.parent.stat().st_mode))
                self.assertEqual(0o600, stat.S_IMODE(snapshot.stat().st_mode))
                self.assertEqual(SYNTHETIC_COOKIE, snapshot.read_bytes())
                snapshot.write_bytes(b"yt-dlp rewrote only its disposable jar\n")
                return subprocess.CompletedProcess(command, 0)

            result = self.run_guard(repo, temp_parent, cookie, fake_runner)
            after = cookie.stat()
            self.assertEqual(0, result)
            self.assertEqual(SYNTHETIC_COOKIE, cookie.read_bytes())
            self.assertEqual(before.st_ino, after.st_ino)
            self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
            self.assertNotIn(str(cookie), seen["command"])
            self.assertFalse(seen["snapshot"].parent.exists())
            self.assertEqual([], list(temp_parent.iterdir()))

    def test_injects_config_isolation_before_disposable_cookie(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            commands = []

            def fake_runner(command, *, check):
                commands.append(command)
                return subprocess.CompletedProcess(command, 7)

            result = self.run_guard(repo, temp_parent, cookie, fake_runner)
            self.assertEqual(7, result)
            self.assertEqual(
                ["yt-dlp", "--ignore-config", "--no-config-locations", "--cookies"],
                commands[0][:4],
            )

    def test_rejects_caller_cookie_and_config_options_before_snapshot(self):
        forbidden = (
            ["--cookies", "/tmp/other.txt", "https://example.invalid"],
            ["--cookies=/tmp/other.txt", "https://example.invalid"],
            ["--cookies-from-browser", "chrome", "https://example.invalid"],
            ["--no-cookies", "https://example.invalid"],
            ["--config-locations", "/tmp/config", "https://example.invalid"],
            ["--config-locations=/tmp/config", "https://example.invalid"],
            ["--ignore-config", "https://example.invalid"],
            ["--no-config", "https://example.invalid"],
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            for arguments in forbidden:
                with self.subTest(arguments=arguments):
                    with self.assertRaises(yt_dlp_readonly.CookieGuardError):
                        yt_dlp_readonly.run_yt_dlp(
                            arguments,
                            canonical=cookie,
                            repo_root=repo,
                            temp_parent=temp_parent,
                        )
            self.assertEqual([], list(temp_parent.iterdir()))

    def test_rejects_any_argument_that_names_canonical(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            with self.assertRaises(yt_dlp_readonly.CookieGuardError):
                yt_dlp_readonly.run_yt_dlp(
                    ["--output", "all_cookies.txt", "https://example.invalid"],
                    canonical=cookie,
                    repo_root=repo,
                    temp_parent=temp_parent,
                )

    def test_exception_cleans_private_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))

            def failing_runner(command, *, check):
                snapshot = Path(command[command.index("--cookies") + 1])
                self.assertTrue(snapshot.is_file())
                raise RuntimeError("synthetic runner failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic runner failure"):
                self.run_guard(repo, temp_parent, cookie, failing_runner)
            self.assertEqual([], list(temp_parent.iterdir()))
            self.assertEqual(SYNTHETIC_COOKIE, cookie.read_bytes())

    def test_keyboard_interrupt_cleans_private_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))

            def interrupted_runner(command, *, check):
                snapshot = Path(command[command.index("--cookies") + 1])
                self.assertTrue(snapshot.is_file())
                raise KeyboardInterrupt

            with self.assertRaises(KeyboardInterrupt):
                self.run_guard(repo, temp_parent, cookie, interrupted_runner)
            self.assertEqual([], list(temp_parent.iterdir()))
            self.assertEqual(SYNTHETIC_COOKIE, cookie.read_bytes())

    def test_cli_redacts_canonical_path_and_cookie_content_on_guard_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            os.chmod(cookie, 0o640)
            captured = []

            def fake_runner(command, *, check):
                captured.append(command)
                return subprocess.CompletedProcess(command, 0)

            with self.assertRaises(yt_dlp_readonly.CookieGuardError) as caught:
                yt_dlp_readonly.run_yt_dlp(
                    ["https://example.invalid/video"],
                    canonical=cookie,
                    repo_root=repo,
                    temp_parent=temp_parent,
                    runner=fake_runner,
                )
            message = str(caught.exception)
            self.assertNotIn(str(cookie), message)
            self.assertNotIn("synthetic-never-real", message)
            self.assertEqual([], captured)

    def test_default_policy_accepts_unlocked_safe_canonical(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            with yt_dlp_readonly.private_cookie_snapshot(
                cookie,
                repo_root=repo,
                temp_parent=temp_parent,
            ) as snapshot:
                self.assertEqual(SYNTHETIC_COOKIE, snapshot.read_bytes())

    def test_rejects_symlink_fifo_hardlink_owner_and_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repo, temp_parent, cookie = self.make_layout(base)

            symlink = repo / "symlink.txt"
            symlink.symlink_to(cookie)
            fifo = repo / "fifo.txt"
            os.mkfifo(fifo, 0o600)
            hardlink = repo / "hardlink.txt"
            os.link(cookie, hardlink)

            cases = (
                (symlink, os.getuid(), "regular file"),
                (fifo, os.getuid(), "regular file"),
                (cookie, os.getuid(), "link count"),
            )
            for path, expected_uid, message in cases:
                with self.subTest(path=path.name, message=message):
                    with self.assertRaisesRegex(
                        yt_dlp_readonly.CookieGuardError, message
                    ):
                        with yt_dlp_readonly.private_cookie_snapshot(
                            path,
                            repo_root=repo,
                            temp_parent=temp_parent,
                            expected_uid=expected_uid,
                        ):
                            self.fail("unsafe input must not be yielded")

            hardlink.unlink()
            with self.assertRaisesRegex(
                yt_dlp_readonly.CookieGuardError, "owner"
            ):
                with yt_dlp_readonly.private_cookie_snapshot(
                    cookie,
                    repo_root=repo,
                    temp_parent=temp_parent,
                    expected_uid=os.getuid() + 1,
                ):
                    self.fail("unexpected owner must not be yielded")

            os.chmod(cookie, 0o640)
            with self.assertRaisesRegex(
                yt_dlp_readonly.CookieGuardError, "permissions"
            ):
                with yt_dlp_readonly.private_cookie_snapshot(
                    cookie,
                    repo_root=repo,
                    temp_parent=temp_parent,
                ):
                    self.fail("unsafe mode must not be yielded")

    def test_rejects_temp_storage_inside_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, _temp_parent, cookie = self.make_layout(Path(temporary))
            inside = repo / "temp"
            inside.mkdir()
            with self.assertRaisesRegex(
                yt_dlp_readonly.CookieGuardError, "inside the repository"
            ):
                with yt_dlp_readonly.private_cookie_snapshot(
                    cookie,
                    repo_root=repo,
                    temp_parent=inside,
                ):
                    self.fail("in-repository snapshot must not be yielded")
            self.assertEqual([], list(inside.iterdir()))

    def test_concurrent_runs_receive_independent_snapshots(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo, temp_parent, cookie = self.make_layout(Path(temporary))
            barrier = threading.Barrier(3)
            snapshot_paths = []
            snapshot_lock = threading.Lock()

            def fake_runner(command, *, check):
                snapshot = Path(command[command.index("--cookies") + 1])
                with snapshot_lock:
                    snapshot_paths.append(snapshot)
                barrier.wait(timeout=5)
                snapshot.write_bytes(str(threading.get_ident()).encode("ascii"))
                barrier.wait(timeout=5)
                return subprocess.CompletedProcess(command, 0)

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(
                        self.run_guard, repo, temp_parent, cookie, fake_runner
                    )
                    for _ in range(3)
                ]
                self.assertEqual([0, 0, 0], [future.result() for future in futures])

            self.assertEqual(3, len(snapshot_paths))
            self.assertEqual(3, len({str(path) for path in snapshot_paths}))
            self.assertTrue(all(not path.exists() for path in snapshot_paths))
            self.assertEqual([], list(temp_parent.iterdir()))
            self.assertEqual(SYNTHETIC_COOKIE, cookie.read_bytes())


if __name__ == "__main__":
    unittest.main()
