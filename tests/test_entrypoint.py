import signal
from unittest import mock

import pytest
from coveralls.api import CoverallsException

import entrypoint


def patch_os_envirion(environ):
    return mock.patch.dict("os.environ", environ, clear=True)


def patch_coveralls_wear():
    return mock.patch("entrypoint.Coveralls.wear")


def patch_log():
    return mock.patch("entrypoint.log")


def patch_sys_argv(argv):
    return mock.patch("sys.argv", argv)


def patch_requests_post(json_response=None):
    new_mock = mock.Mock()
    if json_response:
        new_mock.return_value.json.return_value = json_response
    return mock.patch("entrypoint.requests.post", new_mock)


class TestEntryPoint:
    def test_main_no_token(self):
        """Argument `--github-token` is required."""
        argv = ["src/entrypoint.py"]
        with patch_sys_argv(argv), pytest.raises(SystemExit) as ex_info:
            entrypoint.main()
        assert ex_info.value.args == (signal.SIGINT.value,)

    def test_main(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.run_coveralls"
        ) as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [
            mock.call("TOKEN", False, False, False)
        ]

    def test_main_flag_name(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN", "--flag-name", "FLAG"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.run_coveralls"
        ) as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [
            mock.call("TOKEN", False, "FLAG", False)
        ]

    def test_main_base_path(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN", "--base-path", "SRC"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.run_coveralls"
        ) as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [
            mock.call("TOKEN", False, False, "SRC")
        ]

    def test_main_parallel_finished(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN", "--parallel-finished"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.post_webhook"
        ) as m_post_webhook:
            entrypoint.main()
        assert m_post_webhook.call_args_list == [mock.call("TOKEN")]

    def test_try_main(self):
        with mock.patch(
            "entrypoint.main", side_effect=Exception
        ) as m_main, pytest.raises(SystemExit) as ex_info:
            entrypoint.try_main()
        assert m_main.call_args_list == [mock.call()]
        assert ex_info.value.args == (entrypoint.ExitCode.FAILURE,)

    def test_run_coveralls_github_token(self):
        """Simple case when Coveralls.wear() returns some results."""
        url = "https://coveralls.io/jobs/1234"
        with patch_coveralls_wear() as m_wear, patch_log() as m_log:
            m_wear.return_value = {
                "message": "Job ##12.34",
                "url": url,
            }
            entrypoint.run_coveralls(repo_token="TOKEN")
        assert m_wear.call_args_list == [mock.call()]
        assert m_log.method_calls == [
            mock.call.info("Trying submitting coverage with service_name: github..."),
            mock.call.debug(
                "Patching os.environ with: "
                "{'COVERALLS_REPO_TOKEN': 'TOKEN', 'COVERALLS_PARALLEL': ''}"
            ),
            mock.call.debug(m_wear.return_value),
            mock.call.info(url),
        ]

    def test_run_coveralls_wear_error_once(self):
        """On Coveralls.wear() error we should try another `service_name`."""
        url = "https://coveralls.io/jobs/1234"
        side_effect = (
            CoverallsException("Error"),
            {"message": "Job ##12.34", "url": url},
        )
        with patch_coveralls_wear() as m_wear, patch_log() as m_log:
            m_wear.side_effect = side_effect
            entrypoint.run_coveralls(repo_token="TOKEN")
        assert m_wear.call_args_list == [mock.call(), mock.call()]
        assert m_log.method_calls == [
            mock.call.info("Trying submitting coverage with service_name: github..."),
            mock.call.debug(
                "Patching os.environ with: "
                "{'COVERALLS_REPO_TOKEN': 'TOKEN', 'COVERALLS_PARALLEL': ''}"
            ),
            mock.call.warning(
                "Failed submitting coverage with service_name: github",
                exc_info=side_effect[0],
            ),
            mock.call.info(
                "Trying submitting coverage with service_name: github-actions..."
            ),
            mock.call.debug(
                "Patching os.environ with: "
                "{'COVERALLS_REPO_TOKEN': 'TOKEN', 'COVERALLS_PARALLEL': ''}"
            ),
            mock.call.debug(side_effect[1]),
            mock.call.info(url),
        ]

    def test_run_coveralls_wear_error_twice(self):
        """Exits with error code if Coveralls.wear() fails twice."""
        side_effect = (
            CoverallsException("Error 1"),
            CoverallsException("Error 2"),
        )
        with patch_coveralls_wear() as m_wear, pytest.raises(SystemExit) as ex_info:
            m_wear.side_effect = side_effect
            entrypoint.run_coveralls(repo_token="TOKEN")
        assert ex_info.value.args == (entrypoint.ExitCode.FAILURE,)

    def test_post_webhook(self):
        """
        Tests different uses cases:
        1) default, no environment variable
        2) `GITHUB_RUN_ID` is set
        """
        repo_token = "TOKEN"
        json_response = {"done": True}
        # 1) default, no environment variable
        environ = {}
        with patch_requests_post(json_response) as m_post, patch_os_envirion(environ):
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                json={
                    "repo_token": "TOKEN",
                    "repo_name": None,
                    "payload": {"build_num": None, "status": "done"},
                },
            )
        ]
        # 2) `GITHUB_RUN_ID` and `GITHUB_REPOSITORY` are set
        environ = {
            "GITHUB_RUN_ID": "845347868344",
            "GITHUB_REPOSITORY": "AndreMiras/coveralls-python-action",
        }
        with patch_requests_post(json_response) as m_post, patch_os_envirion(environ):
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                json={
                    "repo_token": "TOKEN",
                    "repo_name": "AndreMiras/coveralls-python-action",
                    "payload": {
                        "build_num": "845347868344",
                        "status": "done",
                    },
                },
            )
        ]

    def test_post_webhook_error(self):
        """Coveralls.io json error response should raise an exception."""
        repo_token = "TOKEN"
        json_response = {"error": "Invalid repo token"}
        # 1) default, no environment variable
        environ = {}
        with patch_requests_post(json_response) as m_post, patch_os_envirion(
            environ
        ), pytest.raises(AssertionError) as ex_info:
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                json={
                    "repo_token": "TOKEN",
                    "repo_name": None,
                    "payload": {"build_num": None, "status": "done"},
                },
            )
        ]
        assert ex_info.value.args == (json_response,)

    @pytest.mark.parametrize(
        "value,expected",
        [
            (False, False),
            ("false", False),
            ("f", False),
            ("0", False),
            ("no", False),
            ("n", False),
            (True, True),
            ("true", True),
            ("t", True),
            ("1", True),
            ("yes", True),
            ("y", True),
        ],
    )
    def test_str_to_bool(self, value, expected):
        """Possible recognised values."""
        assert entrypoint.str_to_bool(value) is expected

    @pytest.mark.parametrize("value", ["", "yesn't"])
    def test_str_to_bool_value_error(self, value):
        """Other unrecognised string values raise a `ValueError`."""
        with pytest.raises(ValueError) as ex_info:
            entrypoint.str_to_bool(value)
        assert ex_info.value.args == (f"{value} is not a valid boolean value",)

    @pytest.mark.parametrize("value", [None, 0])
    def test_str_to_bool_attribute_error(self, value):
        """Other unrecognised non-string values raise an `AttributeError`."""
        with pytest.raises(AttributeError) as ex_info:
            entrypoint.str_to_bool(value)
        assert ex_info.value.args[0].endswith(" object has no attribute 'lower'")
