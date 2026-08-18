import contextlib
import http.cookiejar
import importlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.video import bili_dl
from tools.video import bili_search
from tools.video import check_yt_cookie
from tools.video import filter_cookie_jar


FUTURE_EXPIRY = "4102444800"
SYNTHETIC_VALUE = "synthetic-cookie-value-never-from-a-real-session"


def netscape_line(domain: str, name: str, *, httponly: bool = False) -> str:
    prefix = "#HttpOnly_" if httponly else ""
    return (
        f"{prefix}{domain}\tTRUE\t/\tTRUE\t{FUTURE_EXPIRY}\t"
        f"{name}\t{SYNTHETIC_VALUE}"
    )


def write_synthetic_jar(path: Path, mode: int = 0o600) -> None:
    names = [*check_yt_cookie.REQUIRED, "__Secure-3PAPISID"]
    lines = ["# Netscape HTTP Cookie File"]
    for index, name in enumerate(names):
        domain = ".youtube.com" if name == "LOGIN_INFO" else ".google.com"
        lines.append(netscape_line(domain, name, httponly=index % 2 == 0))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, mode)


class YoutubeCookiePreflightTests(unittest.TestCase):
    def test_http_only_rows_are_data_not_comments(self):
        row = check_yt_cookie._parse_netscape_line(
            netscape_line(".youtube.com", "LOGIN_INFO", httponly=True)
        )
        self.assertEqual((".youtube.com", "LOGIN_INFO", FUTURE_EXPIRY), row)

    def test_default_path_is_always_the_repository_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "www.youtube.com_cookies.txt"
            legacy.touch()
            with tempfile.TemporaryDirectory() as unrelated_cwd:
                previous_cwd = Path.cwd()
                try:
                    os.chdir(unrelated_cwd)
                    with mock.patch("tools.video.check_yt_cookie.REPO_ROOT", root):
                        self.assertEqual(
                            root / "all_cookies.txt",
                            check_yt_cookie.default_cookie_path(),
                        )
                finally:
                    os.chdir(previous_cwd)

    def test_missing_path_is_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / SYNTHETIC_VALUE
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = check_yt_cookie.main([str(missing)])
            self.assertEqual(2, result)
            self.assertIn("Cookie 文件不存在", stdout.getvalue())
            self.assertNotIn(SYNTHETIC_VALUE, stdout.getvalue())

    def test_static_preflight_accepts_synthetic_http_only_jar_without_leaking_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "filtered cookies.txt"
            write_synthetic_jar(jar)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = check_yt_cookie.main([str(jar)])
            output = stdout.getvalue()
            self.assertEqual(0, result)
            self.assertIn("静态预检结果: ✓", output)
            self.assertIn("不验证服务端会话新鲜度", output)
            self.assertNotIn(SYNTHETIC_VALUE, output)

    def test_group_readable_jar_fails_static_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "cookies.txt"
            write_synthetic_jar(jar, mode=0o640)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = check_yt_cookie.main([str(jar)])
            self.assertEqual(1, result)
            self.assertIn("仅用户本人可以修正 canonical 权限", stdout.getvalue())

    def test_non_target_domain_is_advisory_without_printing_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "cookies.txt"
            write_synthetic_jar(jar)
            with jar.open("a", encoding="utf-8") as handle:
                handle.write(netscape_line(".unrelated.invalid", "SESSION") + "\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = check_yt_cookie.main([str(jar)])
            output = stdout.getvalue()
            self.assertEqual(0, result)
            self.assertIn("非目标域", output)
            self.assertIn("不影响静态有效性", output)
            self.assertNotIn("unrelated.invalid", output)

    def test_default_canonical_does_not_require_immutable_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "all_cookies.txt"
            write_synthetic_jar(canonical)
            stdout = io.StringIO()
            with mock.patch("tools.video.check_yt_cookie.REPO_ROOT", root):
                with contextlib.redirect_stdout(stdout):
                    result = check_yt_cookie.main([])
            self.assertEqual(0, result)
            self.assertIn("静态预检结果: ✓", stdout.getvalue())
            self.assertNotIn("锁", stdout.getvalue())


class BilibiliCookieJarTests(unittest.TestCase):
    def test_download_default_path_is_always_the_repository_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "www.bilibili.com_cookies.txt").touch()
            self.assertEqual(
                root / "all_cookies.txt", bili_dl.default_cookie_path(root)
            )

    def test_curl_argv_uses_jar_path_and_never_cookie_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "filtered cookies.txt"
            write_synthetic_jar(jar)
            command = bili_dl.build_curl_command(
                "https://www.bilibili.com/video/BVsynthetic", jar
            )
            self.assertIn("--cookie", command)
            self.assertIn(str(jar), command)
            self.assertNotIn("-H", command)
            self.assertNotIn(SYNTHETIC_VALUE, " ".join(command))

    def test_curl_passes_space_containing_jar_path_as_one_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "cookie jar with spaces.txt"
            write_synthetic_jar(jar)
            with mock.patch.object(
                bili_dl.subprocess, "check_output", return_value=b"synthetic"
            ) as check_output:
                bili_dl.curl("https://www.bilibili.com/", jar)
            command = check_output.call_args.args[0]
            cookie_index = command.index("--cookie")
            self.assertEqual(str(jar), command[cookie_index + 1])
            self.assertNotIn(SYNTHETIC_VALUE, " ".join(command))

    def test_insecure_jar_is_rejected_before_curl(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "cookies.txt"
            write_synthetic_jar(jar, mode=0o644)
            with self.assertRaisesRegex(SystemExit, "只允许用户本人维护"):
                bili_dl.validate_cookie_jar(jar)

    def test_equals_in_jar_path_is_rejected_as_ambiguous_curl_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "cookies=ambiguous.txt"
            write_synthetic_jar(jar)
            with self.assertRaisesRegex(SystemExit, "不能包含 '='"):
                bili_dl.validate_cookie_jar(jar)

    def test_cookie_cli_option_accepts_both_forms_and_positions(self):
        cases = [
            ["--cookies", "/tmp/cookie jar.txt", "BVsynthetic", "out.mp4"],
            ["BVsynthetic", "out.mp4", "--cookies=/tmp/cookie jar.txt"],
            ["BVsynthetic", "--cookies", "/tmp/cookie jar.txt", "out.mp4"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                args = bili_dl.parse_args(argv)
                self.assertEqual("BVsynthetic", args.bvid)
                self.assertEqual("out.mp4", args.out)
                self.assertEqual("/tmp/cookie jar.txt", args.cookies)

    def test_duplicate_cookie_option_uses_last_complete_value(self):
        args = bili_dl.parse_args(
            [
                "BVsynthetic",
                "out.mp4",
                "--cookies",
                "/tmp/first.txt",
                "--cookies=/tmp/second.txt",
            ]
        )
        self.assertEqual("/tmp/second.txt", args.cookies)

    def test_missing_cookie_option_value_is_rejected_without_sensitive_output(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                bili_dl.parse_args(["BVsynthetic", "out.mp4", "--cookies"])
        self.assertNotIn(SYNTHETIC_VALUE, stderr.getvalue())


class BilibiliSearchCookieTests(unittest.TestCase):
    @staticmethod
    def nav_payload() -> dict:
        return {
            "code": 0,
            "data": {
                "wbi_img": {
                    "img_url": f"https://i0.hdslb.com/bfs/wbi/{'a' * 32}.png",
                    "sub_url": f"https://i0.hdslb.com/bfs/wbi/{'b' * 32}.png",
                }
            },
        }

    def run_search_main(self, search_payload: object) -> tuple[int, str]:
        stdout = io.StringIO()
        with (
            mock.patch.object(bili_search, "build_opener", return_value=object()),
            mock.patch.object(
                bili_search,
                "get_json",
                side_effect=[self.nav_payload(), search_payload],
            ),
            mock.patch.object(bili_search.time, "sleep"),
            contextlib.redirect_stdout(stdout),
        ):
            result = bili_search.main(
                ["synthetic keyword", "--cookies", "/tmp/synthetic-jar.txt"]
            )
        return result, stdout.getvalue()

    def test_import_does_not_load_any_cookie_jar(self):
        with mock.patch.object(
            http.cookiejar.MozillaCookieJar, "load"
        ) as load_cookie_jar:
            importlib.reload(bili_search)
        load_cookie_jar.assert_not_called()

    def test_lazy_loader_preserves_netscape_http_only_cookie(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "bilibili cookies.txt"
            jar.write_text(
                "# Netscape HTTP Cookie File\n"
                + netscape_line(
                    ".bilibili.com", "SESSDATA", httponly=True
                )
                + "\n",
                encoding="utf-8",
            )
            os.chmod(jar, 0o600)
            loaded = bili_search.load_cookie_jar(jar)
            cookies = list(loaded)
            self.assertEqual(1, len(cookies))
            self.assertEqual("SESSDATA", cookies[0].name)
            self.assertEqual(SYNTHETIC_VALUE, cookies[0].value)
            self.assertTrue(cookies[0].has_nonstandard_attr("HTTPOnly"))

    def test_search_consumer_rejects_insecure_and_equals_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            insecure = Path(tmp) / "cookies.txt"
            write_synthetic_jar(insecure, mode=0o644)
            with self.assertRaisesRegex(ValueError, "只允许用户本人维护"):
                bili_search.load_cookie_jar(insecure)

            ambiguous = Path(tmp) / "cookies=inline.txt"
            write_synthetic_jar(ambiguous)
            with self.assertRaisesRegex(ValueError, "不能包含 '='"):
                bili_search.load_cookie_jar(ambiguous)

    def test_search_default_path_is_always_the_repository_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "www.bilibili.com_cookies.txt"
            legacy.touch()
            with mock.patch("tools.video.bili_search.REPO_ROOT", root):
                self.assertEqual(
                    root / "all_cookies.txt", bili_search.default_cookie_path()
                )

    def test_load_error_is_sanitized_without_cookie_value(self):
        stdout = io.StringIO()
        with mock.patch.object(
            bili_search,
            "build_opener",
            side_effect=http.cookiejar.LoadError(SYNTHETIC_VALUE),
        ):
            with contextlib.redirect_stdout(stdout):
                result = bili_search.main(["synthetic", "--cookies", "/tmp/jar.txt"])
        output = stdout.getvalue()
        self.assertEqual(2, result)
        self.assertIn("格式无效", output)
        self.assertNotIn(SYNTHETIC_VALUE, output)

    def test_missing_cookie_path_does_not_echo_accidentally_pasted_token(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / SYNTHETIC_VALUE
            with contextlib.redirect_stdout(stdout):
                result = bili_search.main(
                    ["synthetic", "--cookies", str(missing)]
                )
        output = stdout.getvalue()
        self.assertEqual(bili_search.EXIT_COOKIE_PRECHECK, result)
        self.assertIn("COOKIE PRECHECK: FAIL", output)
        self.assertIn("路径/存在性/权限检查未通过", output)
        self.assertIn("只允许用户本人维护", output)
        self.assertNotIn("chmod", output)
        self.assertNotIn(SYNTHETIC_VALUE, output)

    def test_api_business_error_is_nonzero_and_does_not_echo_api_message(self):
        result, output = self.run_search_main(
            {
                "code": -412,
                "message": SYNTHETIC_VALUE,
                "data": {"remote_detail": SYNTHETIC_VALUE},
            }
        )
        self.assertEqual(bili_search.EXIT_API_ERROR, result)
        self.assertIn("BILI SEARCH: API_ERROR stage=search code=-412", output)
        self.assertNotIn("RESPONSE_INVALID", output)
        self.assertNotIn("BILI SEARCH: EMPTY", output)
        self.assertNotIn(SYNTHETIC_VALUE, output)
        self.assert_recovery_hint(output)

    def test_malformed_success_payload_is_not_misreported_as_empty(self):
        result, output = self.run_search_main(
            {
                "code": 0,
                "message": SYNTHETIC_VALUE,
                "data": {"result": {"remote_detail": SYNTHETIC_VALUE}},
            }
        )
        self.assertEqual(bili_search.EXIT_RESPONSE_INVALID, result)
        self.assertIn("BILI SEARCH: RESPONSE_INVALID stage=search", output)
        self.assertNotIn("API_ERROR", output)
        self.assertNotIn("BILI SEARCH: EMPTY", output)
        self.assertNotIn(SYNTHETIC_VALUE, output)
        self.assert_recovery_hint(output)

    def test_invalid_json_body_is_sanitized_as_response_invalid(self):
        opener = mock.Mock()
        opener.open.side_effect = [
            io.BytesIO(json.dumps(self.nav_payload()).encode("utf-8")),
            io.BytesIO(f"not-json:{SYNTHETIC_VALUE}".encode("utf-8")),
        ]
        stdout = io.StringIO()
        with (
            mock.patch.object(bili_search, "build_opener", return_value=opener),
            mock.patch.object(bili_search.time, "sleep"),
            contextlib.redirect_stdout(stdout),
        ):
            result = bili_search.main(
                ["synthetic keyword", "--cookies", "/tmp/synthetic-jar.txt"]
            )
        output = stdout.getvalue()
        self.assertEqual(bili_search.EXIT_RESPONSE_INVALID, result)
        self.assertIn("BILI SEARCH: RESPONSE_INVALID stage=search", output)
        self.assertNotIn(SYNTHETIC_VALUE, output)
        self.assert_recovery_hint(output)

    def test_oversized_json_integer_is_sanitized_as_response_invalid(self):
        opener = mock.Mock()
        opener.open.side_effect = [
            io.BytesIO(json.dumps(self.nav_payload()).encode("utf-8")),
            io.BytesIO(("{\"code\":0,\"data\":{\"result\":" + "9" * 5000 + "}}")
                       .encode("utf-8")),
        ]
        stdout = io.StringIO()
        with (
            mock.patch.object(bili_search, "build_opener", return_value=opener),
            mock.patch.object(bili_search.time, "sleep"),
            contextlib.redirect_stdout(stdout),
        ):
            result = bili_search.main(
                ["synthetic keyword", "--cookies", "/tmp/synthetic-jar.txt"]
            )
        output = stdout.getvalue()
        self.assertEqual(bili_search.EXIT_RESPONSE_INVALID, result)
        self.assertIn("BILI SEARCH: RESPONSE_INVALID stage=search", output)
        self.assertNotIn("Traceback", output)
        self.assert_recovery_hint(output)

    def test_true_empty_result_is_a_distinct_nonzero_outcome(self):
        result, output = self.run_search_main(
            {"code": 0, "message": SYNTHETIC_VALUE, "data": {"result": []}}
        )
        self.assertEqual(bili_search.EXIT_EMPTY, result)
        self.assertIn("BILI SEARCH: EMPTY", output)
        self.assertNotIn("API_ERROR", output)
        self.assertNotIn("RESPONSE_INVALID", output)
        self.assertNotIn(SYNTHETIC_VALUE, output)
        self.assert_recovery_hint(output)

    def test_successful_nonempty_search_is_the_only_remote_exit_zero(self):
        result, output = self.run_search_main(
            {
                "code": 0,
                "data": {
                    "result": [
                        {
                            "bvid": "BVsynthetic",
                            "duration": "03:21",
                            "author": "synthetic author",
                            "title": "<em class=\"keyword\">synthetic</em> title",
                        }
                    ]
                },
            }
        )
        self.assertEqual(0, result)
        self.assertIn("BVsynthetic | 03:21 | synthetic author | synthetic title", output)
        self.assertIn("BILI SEARCH: PASS results=1", output)
        self.assertNotIn("RECOVERY:", output)

    def assert_recovery_hint(self, output: str) -> None:
        self.assertIn("自动换关键词", output)
        self.assertIn("直接按 BV", output)
        self.assertIn("另一平台（YouTube）", output)
        self.assertIn("不因单次 B站搜索失败停止整个 goal", output)


class FilterCookieJarTests(unittest.TestCase):
    def make_layout(self, base: Path) -> tuple[Path, Path]:
        repo = base / "repo"
        outside = base / "outside"
        repo.mkdir()
        outside.mkdir()
        return repo, outside

    def write_raw_source(self, path: Path, mode: int = 0o600) -> None:
        lines = ["# Netscape HTTP Cookie File"]
        for index, name in enumerate(sorted(filter_cookie_jar.REQUIRED_YOUTUBE_NAMES)):
            domain = ".youtube.com" if name == b"LOGIN_INFO" else ".google.com"
            lines.append(
                netscape_line(domain, name.decode("ascii"), httponly=index % 2 == 0)
            )
        for index, name in enumerate(sorted(filter_cookie_jar.REQUIRED_BILIBILI_NAMES)):
            lines.append(
                netscape_line(
                    ".bilibili.com", name.decode("ascii"), httponly=index % 2 == 0
                )
            )
        lines.append(netscape_line(".unrelated.invalid", "SESSION"))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(path, mode)

    def test_filters_external_source_preserves_http_only_and_writes_atomic_0600(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, outside = self.make_layout(Path(tmp))
            source = outside / "raw browser export.txt"
            output = outside / "filtered candidate.txt"
            self.write_raw_source(source)

            result = filter_cookie_jar.filter_cookie_jar(
                source, output=output, repo_root=repo
            )
            payload = output.read_text(encoding="utf-8")

            self.assertEqual(output.resolve(), result.output.resolve())
            self.assertEqual(
                len(filter_cookie_jar.REQUIRED_YOUTUBE_NAMES)
                + len(filter_cookie_jar.REQUIRED_BILIBILI_NAMES),
                result.retained,
            )
            self.assertEqual(1, result.discarded)
            self.assertEqual(0o600, output.stat().st_mode & 0o777)
            self.assertIn("#HttpOnly_.youtube.com", payload)
            self.assertIn("#HttpOnly_.bilibili.com", payload)
            self.assertNotIn("unrelated.invalid", payload)
            self.assertEqual([], list(outside.glob(".filtered candidate.txt.next.*.tmp")))
            self.assertFalse((repo / "all_cookies.txt").exists())

    def test_source_inside_repository_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            source = repo / "raw.txt"
            self.write_raw_source(source)
            with self.assertRaisesRegex(ValueError, "必须位于仓库外"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=outside / "candidate.txt", repo_root=repo
                )

    def test_source_equal_to_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, outside = self.make_layout(Path(tmp))
            source = outside / "raw.txt"
            self.write_raw_source(source)
            with self.assertRaisesRegex(ValueError, "不能与原始 cookie 源文件相同"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=source, repo_root=repo
                )

            hardlink = outside / "raw-hardlink.txt"
            os.link(source, hardlink)
            with self.assertRaisesRegex(ValueError, "不能与原始 cookie 源文件相同"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=hardlink, repo_root=repo
                )

    def test_workspace_symlink_to_external_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, outside = self.make_layout(Path(tmp))
            external = outside / "raw.txt"
            self.write_raw_source(external)
            workspace_link = repo / "raw-link.txt"
            workspace_link.symlink_to(external)
            with self.assertRaisesRegex(ValueError, "必须位于仓库外"):
                filter_cookie_jar.filter_cookie_jar(
                    workspace_link, output=outside / "candidate.txt", repo_root=repo
                )

    def test_repository_output_and_symlink_boundaries_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, outside = self.make_layout(Path(tmp))
            source = outside / "raw.txt"
            self.write_raw_source(source)
            canonical = repo / "all_cookies.txt"
            original = b"user-owned-canonical-placeholder\n"
            canonical.write_bytes(original)
            os.chmod(canonical, 0o600)

            with self.assertRaisesRegex(ValueError, "必须位于仓库外"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=canonical, repo_root=repo
                )

            output_link = outside / "candidate-link.txt"
            output_link.symlink_to(canonical)
            with self.assertRaisesRegex(ValueError, "不能是符号链接"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=output_link, repo_root=repo
                )

            linked_parent = outside / "linked-repo"
            linked_parent.symlink_to(repo, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "输出目录不能是符号链接"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=linked_parent / "candidate.txt", repo_root=repo
                )

            real_external_parent = outside / "real-parent"
            (real_external_parent / "nested").mkdir(parents=True)
            linked_external_parent = outside / "linked-parent"
            linked_external_parent.symlink_to(real_external_parent, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "不能经过符号链接"):
                filter_cookie_jar.filter_cookie_jar(
                    source,
                    output=linked_external_parent / "nested" / "candidate.txt",
                    repo_root=repo,
                )

            self.assertEqual(original, canonical.read_bytes())

    def test_missing_required_fields_does_not_replace_existing_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, outside = self.make_layout(Path(tmp))
            destination = outside / "candidate.txt"
            original = b"existing-known-good-placeholder\n"
            destination.write_bytes(original)
            os.chmod(destination, 0o600)
            source = outside / "incomplete.txt"
            source.write_text(
                netscape_line(".youtube.com", "LOGIN_INFO", httponly=True) + "\n",
                encoding="utf-8",
            )
            os.chmod(source, 0o600)
            with self.assertRaisesRegex(ValueError, "关键字段不完整"):
                filter_cookie_jar.filter_cookie_jar(
                    source, output=destination, repo_root=repo
                )
            self.assertEqual(original, destination.read_bytes())

    def test_filter_cli_requires_output_and_reports_candidate_without_cookie_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, outside = self.make_layout(Path(tmp))
            source = outside / "raw.txt"
            candidate = outside / "candidate.txt"
            self.write_raw_source(source)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = filter_cookie_jar.main(
                    [str(source), "--output", str(candidate)], repo_root=repo
                )
            output = stdout.getvalue()
            self.assertEqual(0, result)
            self.assertIn("COOKIE FILTER: PASS", output)
            self.assertIn("output=candidate.txt", output)
            self.assertNotIn(str(repo), output)
            self.assertNotIn(SYNTHETIC_VALUE, output)
            self.assertTrue(candidate.is_file())
            self.assertFalse((repo / "all_cookies.txt").exists())

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                missing_output_result = filter_cookie_jar.main(
                    [str(source)], repo_root=repo
                )
            self.assertEqual(2, missing_output_result)
            self.assertIn("--output", stderr.getvalue())
            self.assertFalse((repo / "all_cookies.txt").exists())


if __name__ == "__main__":
    unittest.main()
