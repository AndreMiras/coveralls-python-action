from unittest import mock

import pytest

import entrypoint


def patch_os_envirion(environ):
    return mock.patch.dict("os.environ", environ, clear=True)


def patch_coveralls_wear():
    return mock.patch("entrypoint.Coveralls.wear")


def patch_log():
    return mock.patch("entrypoint.log")


class TestEntryPoint:
    def test_main(self):
        with mock.patch("entrypoint.run_coveralls") as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [mock.call()]

    def test_run_coveralls_no_token(self):
        with pytest.raises(AssertionError) as ex_info:
            entrypoint.run_coveralls()
        assert ex_info.value.args == (
            "Either GITHUB_TOKEN or COVERALLS_REPO_TOKEN must be set.",
        )

    def test_run_coveralls_github_token(self):
        """Simple case when Coveralls.wear() returns some results."""
        with patch_os_envirion(
            {"GITHUB_TOKEN": "TOKEN"}
        ), patch_coveralls_wear() as m_wear, patch_log() as m_log:
            entrypoint.run_coveralls()
        assert m_wear.call_args_list == [mock.call()]
        assert m_log.method_calls == [
            mock.call.info("Trying submitting coverage with service_name: github..."),
            mock.call.info(m_wear.return_value),
        ]
