"""Offline regressions for source availability and execution-boundary decisions."""

import contextlib
import errno
import http.cookiejar
import io
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from tools.video import bili_search
from tools.video import check_source_access as access
from tools.video.tests.test_cookie_tools import SYNTHETIC_VALUE, write_synthetic_jar


def result(platform, status):
    return access.Result(platform, status, "session", "synthetic_evidence")


class StartupDecisionTests(unittest.TestCase):
    def test_either_platform_failure_pauses_even_when_the_other_passes(self):
        for failed in ("youtube", "bilibili"):
            with self.subTest(failed=failed):
                output = io.StringIO()
                with mock.patch.object(access, "probe", side_effect=lambda platform, query:
                                       result(platform, "CONFIRM_REQUIRED" if platform == failed
                                              else "PASS")) as probe:
                    with contextlib.redirect_stdout(output):
                        code = access.main([])
                self.assertEqual(10, code)
                self.assertEqual(["youtube", "bilibili"], [c.args[0] for c in probe.call_args_list])
                self.assertIn("SOURCE ACCESS: CONFIRM_REQUIRED", output.getvalue())

    def test_permission_and_unknown_failures_neither_pass_nor_claim_platform_failure(self):
        for status, expected in (("ENVIRONMENT_BLOCKED", 11), ("RETRY_REQUIRED", 12)):
            with self.subTest(status=status):
                output = io.StringIO()
                with mock.patch.object(access, "probe", side_effect=[result("youtube", status),
                                                                      result("bilibili", "PASS")]):
                    with contextlib.redirect_stdout(output):
                        code = access.main([])
                self.assertEqual(expected, code)
                self.assertNotIn("CONFIRM_REQUIRED", output.getvalue())
                self.assertNotIn("SOURCE ACCESS: PASS", output.getvalue())

    def test_all_required_platforms_must_pass_and_explicit_scope_is_honored(self):
        for argv, platforms in (([], ["youtube", "bilibili"]),
                                (["--platform", "youtube"], ["youtube"])):
            with self.subTest(argv=argv):
                with mock.patch.object(access, "probe", side_effect=lambda p, q: result(p, "PASS")) as probe:
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(0, access.main(argv))
                self.assertEqual(platforms, [call.args[0] for call in probe.call_args_list])


class SourceProbeTests(unittest.TestCase):
    def test_cookie_reader_is_readonly_and_expired_auth_does_not_reach_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.txt"
            write_synthetic_jar(path)
            path.write_text(path.read_text().replace("4102444800", "1"))
            before = path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode
            with mock.patch.object(access.check_yt_cookie, "default_cookie_path", return_value=path):
                with mock.patch.object(access, "youtube_session") as session:
                    value = access.probe("youtube", "example")
            self.assertEqual("CONFIRM_REQUIRED", value.status)
            self.assertEqual("auth_fields_missing_or_expired", value.reason)
            session.assert_not_called()
            self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode))
            self.assertNotIn(SYNTHETIC_VALUE, str(value))

    def test_cookie_read_permission_failure_is_environment_error(self):
        with mock.patch.object(Path, "stat", side_effect=PermissionError(errno.EACCES, SYNTHETIC_VALUE)):
            value = access.load_opener("bilibili")
        self.assertEqual("ENVIRONMENT_BLOCKED", value.status)
        self.assertNotIn(SYNTHETIC_VALUE, str(value))

    def test_malformed_cookie_does_not_leak(self):
        with (mock.patch.object(Path, "stat"),
              mock.patch.object(bili_search, "build_opener", side_effect=http.cookiejar.LoadError(SYNTHETIC_VALUE))):
            value = access.load_opener("youtube")
        self.assertEqual("CONFIRM_REQUIRED", value.status)
        self.assertNotIn(SYNTHETIC_VALUE, str(value))

    def test_youtube_requires_unambiguous_live_login_evidence(self):
        for body, url, status in (
            ('{"LOGGED_IN":true}', "https://www.youtube.com/feed/subscriptions", "PASS"),
            ('{"LOGGED_IN":false}', "https://www.youtube.com/feed/subscriptions", "CONFIRM_REQUIRED"),
            (SYNTHETIC_VALUE, "https://accounts.google.com/ServiceLogin", "CONFIRM_REQUIRED"),
            (SYNTHETIC_VALUE, "https://www.youtube.com/", "RETRY_REQUIRED"),
            ('{"LOGGED_IN":true,"LOGGED_IN":false}', "https://www.youtube.com/", "RETRY_REQUIRED"),
            ('{"LOGGED_IN":true}', "https://consent.youtube.com/", "RETRY_REQUIRED"),
            ("Sign in to confirm you’re not a bot", "https://www.youtube.com/", "CONFIRM_REQUIRED"),
        ):
            with self.subTest(body=body):
                response = io.BytesIO(body.encode())
                response.geturl = lambda: url
                opener = mock.Mock()
                opener.open.return_value = response
                value = access.youtube_session(opener)
                self.assertEqual(status, value.status)
                self.assertNotIn(SYNTHETIC_VALUE, str(value))

    def test_transport_http_permission_and_dns_are_distinct(self):
        for error, status in (
            (urllib.error.HTTPError("https://example.invalid/", 412, SYNTHETIC_VALUE, {}, None), "CONFIRM_REQUIRED"),
            (urllib.error.HTTPError("https://example.invalid/", 503, SYNTHETIC_VALUE, {}, None), "RETRY_REQUIRED"),
            (urllib.error.URLError(PermissionError(errno.EPERM, SYNTHETIC_VALUE)), "ENVIRONMENT_BLOCKED"),
            (urllib.error.URLError("Name or service not known " + SYNTHETIC_VALUE), "RETRY_REQUIRED"),
        ):
            with self.subTest(error=type(error).__name__, status=status):
                opener = mock.Mock()
                opener.open.side_effect = error
                value = access.youtube_session(opener)
                self.assertEqual(status, value.status)
                self.assertNotIn(SYNTHETIC_VALUE, str(value))
                with self.assertRaises(bili_search.SearchRequestError) as caught:
                    bili_search.get_json("https://example.invalid/", opener, stage="nav")
                value = access.request_failure("bilibili", "session", caught.exception)
                self.assertEqual(status, value.status)

    def test_bilibili_session_and_search_errors_and_empty_results(self):
        nav = {"code": 0, "data": {"isLogin": True, "wbi_img": {
            "img_url": "https://example.invalid/" + "a" * 32 + ".png",
            "sub_url": "https://example.invalid/" + "b" * 32 + ".png"}}}
        for login, search, status in (
            (nav, {"code": 0, "data": {"result": []}}, "PASS"),
            (nav, {"code": -412, "message": SYNTHETIC_VALUE}, "CONFIRM_REQUIRED"),
            (nav, {"code": -352}, "CONFIRM_REQUIRED"),
            (nav, {"code": -999}, "RETRY_REQUIRED"),
            (nav, {"code": 0, "data": {}}, "RETRY_REQUIRED"),
            ({"code": -101}, {}, "CONFIRM_REQUIRED"),
            ({"code": 0, "data": {"isLogin": False}}, {}, "CONFIRM_REQUIRED"),
            ({"code": 0, "data": {}}, {}, "RETRY_REQUIRED"),
        ):
            with self.subTest(login=login, search=search):
                with mock.patch.object(bili_search, "get_json", side_effect=[login, nav, search]):
                    value = access.bilibili_session_and_search(mock.Mock(), "example")
                self.assertEqual(status, value.status)
                self.assertNotIn(SYNTHETIC_VALUE, str(value))

    def test_youtube_extraction_keeps_local_and_candidate_errors_separate_from_blocking(self):
        for code, stdout, stderr, status in (
            (0, "dQw4w9WgXcQ\n", "", "PASS"),
            (0, "", "", "RETRY_REQUIRED"),
            (1, "", "Sign in to confirm you’re not a bot", "CONFIRM_REQUIRED"),
            (1, "", "The provided YouTube account cookies are no longer valid", "CONFIRM_REQUIRED"),
            (1, "", "HTTP Error 429: Too Many Requests", "CONFIRM_REQUIRED"),
            (1, "", "HTTP Error 403: Forbidden", "RETRY_REQUIRED"),
            (1, "", "Video unavailable", "RETRY_REQUIRED"),
            (1, "", "Permission denied", "ENVIRONMENT_BLOCKED"),
        ):
            with self.subTest(stderr=stderr):
                def wrapper(args, *, runner):
                    self.assertIn("--simulate", args)
                    return runner(["synthetic-yt-dlp"], check=False).returncode
                completed = subprocess.CompletedProcess([], code, stdout, stderr + " " + SYNTHETIC_VALUE)
                with mock.patch.object(access.yt_dlp_readonly, "run_yt_dlp", side_effect=wrapper):
                    with mock.patch.object(access.subprocess, "run", return_value=completed):
                        value = access.youtube_search("example")
                self.assertEqual(status, value.status)
                self.assertNotIn(SYNTHETIC_VALUE, str(value))


if __name__ == "__main__":
    unittest.main()
