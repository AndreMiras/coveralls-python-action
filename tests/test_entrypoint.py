import json
import signal
from unittest import mock

import pytest
from coveralls.api import CoverallsException
from requests.models import Response

import entrypoint


def patch_os_envirion(environ):
    return mock.patch.dict("os.environ", environ, clear=True)


def patch_coveralls_wear():
    return mock.patch("entrypoint.Coveralls.wear")


def patch_log():
    return mock.patch("entrypoint.log")


def patch_sys_argv(argv):
    return mock.patch("sys.argv", argv)


def patch_requests_post(json_response=mock.Mock(), status_code=200):
    response = Response()
    response.status_code = status_code
    response.json = lambda: json_response
    m_post = mock.Mock(return_value=response)
    return mock.patch("entrypoint.requests.post", m_post)


class TestEntryPoint:
    def test_main_no_token(self):
        """Argument `--github-token` is required."""
        argv = ["src/entrypoint.py"]
        with patch_sys_argv(argv), pytest.raises(
            SystemExit, match=f"{signal.SIGINT.value}"
        ):
            entrypoint.main()

    def test_main(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.run_coveralls"
        ) as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [mock.call("TOKEN", False, None, ".")]

    def test_main_flag_name(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN", "--flag-name", "FLAG"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.run_coveralls"
        ) as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [
            mock.call("TOKEN", False, "FLAG", ".")
        ]

    def test_main_base_path(self):
        argv = ["src/entrypoint.py", "--github-token", "TOKEN", "--base-path", "SRC"]
        with patch_sys_argv(argv), mock.patch(
            "entrypoint.run_coveralls"
        ) as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [
            mock.call("TOKEN", False, None, "SRC")
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
        ) as m_main, pytest.raises(SystemExit, match=f"{entrypoint.ExitCode.FAILURE}"):
            entrypoint.try_main()
        assert m_main.call_args_list == [mock.call()]

    def test_run_coveralls_github_token(self):
        """Simple case when Coveralls.wear() returns some results."""
        token = "TOKEN"
        url = "https://coveralls.io/jobs/1234"
        json_response = {
            "message": "Job ##12.34",
            "url": url,
        }
        with patch_requests_post(
            json_response=json_response
        ) as m_post, patch_log() as m_log:
            entrypoint.run_coveralls(repo_token=token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/api/v1/jobs",
                files={"json_file": mock.ANY},
                verify=True,
            )
        ]
        json_file = json.loads(m_post.call_args_list[0][1]["files"]["json_file"])
        assert json_file["repo_token"] == token
        assert m_log.method_calls == [
            mock.call.info("Trying submitting coverage with service_name: github..."),
            mock.call.debug(
                "Patching os.environ with: "
                "{'COVERALLS_REPO_TOKEN': 'TOKEN', 'COVERALLS_PARALLEL': ''}"
            ),
            mock.call.info("cd ."),
            mock.call.info(mock.ANY),
            mock.call.debug(json_response),
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
            mock.call.info("cd ."),
            mock.call.warning(
                "Failed submitting coverage with service_name: github",
                exc_info=side_effect[0],
            ),
            mock.call.info(mock.ANY),
            mock.call.info(
                "Trying submitting coverage with service_name: github-actions..."
            ),
            mock.call.debug(
                "Patching os.environ with: "
                "{'COVERALLS_REPO_TOKEN': 'TOKEN', 'COVERALLS_PARALLEL': ''}"
            ),
            mock.call.info("cd ."),
            mock.call.info(mock.ANY),
            mock.call.debug(side_effect[1]),
            mock.call.info(url),
        ]

    def test_run_coveralls_wear_error_twice(self):
        """Exits with error code if Coveralls.wear() fails twice."""
        side_effect = (
            CoverallsException("Error 1"),
            CoverallsException("Error 2"),
        )
        with patch_coveralls_wear() as m_wear, pytest.raises(
            SystemExit, match=f"{entrypoint.ExitCode.FAILURE}"
        ):
            m_wear.side_effect = side_effect
            entrypoint.run_coveralls(repo_token="TOKEN")

    def test_status_code_422(self):
        """
        Makes sure the coveralls package retries on "422 Unprocessable Entry" error
        rather than crashing while trying to access the `service_job_id` key, refs:
        https://github.com/coveralls-clients/coveralls-python/pull/241/files#r532248047
        """
        status_code = 422
        with patch_requests_post(status_code=status_code) as m_post, pytest.raises(
            SystemExit, match=f"{entrypoint.ExitCode.FAILURE}"
        ), patch_log() as m_log:
            entrypoint.run_coveralls(repo_token="TOKEN")
        # coveralls package will retry once per service we call it with
        assert m_post.call_count == 4
        assert m_log.error.call_args_list == [
            mock.call("Failed to submit coverage", exc_info=None)
        ]
        assert m_log.warning.call_args_list == [
            mock.call(
                "Failed submitting coverage with service_name: github",
                exc_info=CoverallsException(
                    "Could not submit coverage: 422 Client Error: None for url: None"
                ),
            ),
            mock.call(
                "Failed submitting coverage with service_name: github-actions",
                exc_info=CoverallsException(
                    "Could not submit coverage: 422 Client Error: None for url: None"
                ),
            ),
        ]

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
        ), pytest.raises(AssertionError, match=f"{json_response}"):
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
        with pytest.raises(ValueError, match=f"{value} is not a valid boolean value"):
            entrypoint.str_to_bool(value)

    @pytest.mark.parametrize("value", [None, 0])
    def test_str_to_bool_attribute_error(self, value):
        """Other unrecognised non-string values raise an `AttributeError`."""
        with pytest.raises(AttributeError, match=" object has no attribute 'lower'"):
            entrypoint.str_to_bool(value)
