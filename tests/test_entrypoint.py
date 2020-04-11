import signal
from unittest import mock

import pytest

import entrypoint


def patch_os_envirion(environ):
    return mock.patch.dict("os.environ", environ, clear=True)


def patch_coveralls_wear():
    return mock.patch("entrypoint.Coveralls.wear")


def patch_log():
    return mock.patch("entrypoint.log")


def patch_sys_argv(argv):
    return mock.patch("sys.argv", argv)


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
        assert m_run_coveralls.call_args_list == [mock.call("TOKEN", False)]

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
