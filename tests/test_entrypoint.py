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


def patch_requests_post():
    return mock.patch("entrypoint.requests.post")


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

    def test_get_build_number(self):
        github_sha = "ffac537e6cbbf934b08745a378932722df287a53"
        github_ref = "refs/pull/123/merge"
        assert (
            entrypoint.get_build_number(github_sha, github_ref)
            == "ffac537e6cbbf934b08745a378932722df287a53-PR-123"
        )
        github_ref = "refs/heads/feature-branch-1"
        assert (
            entrypoint.get_build_number(github_sha, github_ref)
            == "ffac537e6cbbf934b08745a378932722df287a53"
        )
        github_ref = None
        assert (
            entrypoint.get_build_number(github_sha, github_ref)
            == "ffac537e6cbbf934b08745a378932722df287a53"
        )

    def test_post_webhook(self):
        """
        Tests different uses cases:
        1) default, no environment variable
        2) only `GITHUB_SHA` is set
        3) `GITHUB_REF` is a branch
        4) `GITHUB_REF` is a pull request
        """
        repo_token = "TOKEN"
        # 1) default, no environment variable
        environ = {}
        with patch_requests_post() as m_post, patch_os_envirion(environ):
            m_post.return_value.json.return_value = {"done": True}
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                params={"repo_token": "TOKEN"},
                json={"payload": {"build_num": None, "status": "done"}},
            )
        ]
        # 2) only `GITHUB_SHA` is set
        environ = {
            "GITHUB_SHA": "ffac537e6cbbf934b08745a378932722df287a53",
        }
        with patch_requests_post() as m_post, patch_os_envirion(environ):
            m_post.return_value.json.return_value = {"done": True}
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                params={"repo_token": "TOKEN"},
                json={
                    "payload": {
                        "build_num": "ffac537e6cbbf934b08745a378932722df287a53",
                        "status": "done",
                    }
                },
            )
        ]
        # 3) `GITHUB_REF` is a branch
        environ = {
            "GITHUB_SHA": "ffac537e6cbbf934b08745a378932722df287a53",
            "GITHUB_REF": "refs/heads/feature-branch-1",
        }
        with patch_requests_post() as m_post, patch_os_envirion(environ):
            m_post.return_value.json.return_value = {"done": True}
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                params={"repo_token": "TOKEN"},
                json={
                    "payload": {
                        "build_num": "ffac537e6cbbf934b08745a378932722df287a53",
                        "status": "done",
                    }
                },
            )
        ]
        # 4) `GITHUB_REF` is a pull request
        environ = {
            "GITHUB_SHA": "ffac537e6cbbf934b08745a378932722df287a53",
            "GITHUB_REF": "refs/pull/123/merge",
        }
        with patch_requests_post() as m_post, patch_os_envirion(environ):
            m_post.return_value.json.return_value = {"done": True}
            entrypoint.post_webhook(repo_token)
        assert m_post.call_args_list == [
            mock.call(
                "https://coveralls.io/webhook",
                params={"repo_token": "TOKEN"},
                json={
                    "payload": {
                        "build_num": "ffac537e6cbbf934b08745a378932722df287a53-PR-123",
                        "status": "done",
                    }
                },
            )
        ]
