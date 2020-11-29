#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from enum import Enum
from unittest import mock

import requests
from coveralls.api import Coveralls, CoverallsException

log = logging.getLogger(__name__)


class ExitCode(Enum):
    SUCCESS = 0
    FAILURE = 1


def set_failed(message):
    exc_info = message if isinstance(message, Exception) else None
    log.error(message, exc_info=exc_info)
    sys.exit(ExitCode.FAILURE)


def patch_os_environ(repo_token, parallel, flag_name):
    """
    Temporarily updates the environment variable to satisfy coveralls Python API.
    That is because the coveralls package API consumes mostly environment variables.
    """
    # https://github.com/coveralls-clients/coveralls-python/blob/2.0.0/coveralls/api.py#L146
    parallel = "true" if parallel else ""
    environ = {"COVERALLS_REPO_TOKEN": repo_token, "COVERALLS_PARALLEL": parallel}
    if flag_name:
        environ["COVERALLS_FLAG_NAME"] = flag_name
    log.debug(f"Patching os.environ with: {environ}")
    return mock.patch.dict("os.environ", environ)


def run_coveralls(repo_token, parallel=False, flag_name=False, base_path=False):
    """Submits job to coveralls."""
    # note that coveralls.io "service_name" can either be:
    # - "github-actions" (local development?)
    # - "github" (from GitHub jobs?)
    # for some reasons the "service_name" can be one or the other
    # (depending on where it's ran from?)
    service_names = ("github", "github-actions")
    result = None
    if base_path and os.path.exists(base_path):
        os.chdir(base_path)
    for service_name in service_names:
        log.info(f"Trying submitting coverage with service_name: {service_name}...")
        with patch_os_environ(repo_token, parallel, flag_name):
            coveralls = Coveralls(service_name=service_name)
            try:
                result = coveralls.wear()
                break
            except CoverallsException as e:
                log.warning(
                    f"Failed submitting coverage with service_name: {service_name}",
                    exc_info=e,
                )
    if result is None:
        set_failed("Failed to submit coverage")
    log.debug(result)
    log.info(result["url"])


def get_github_sha():
    """e.g. ffac537e6cbbf934b08745a378932722df287a53"""
    return os.environ.get("GITHUB_SHA")


def get_github_ref():
    """
    The branch or tag ref that triggered the workflow.
    For example, refs/heads/feature-branch-1.
    If neither a branch or tag is available for the variable will not exist.
    - for pull_request events: refs/pull/<pull_request_number>/merge
    - for push event: refs/heads/<branch>
    https://help.github.com/en/actions/configuring-and-managing-workflows/using-environment-variables
    """
    return os.environ.get("GITHUB_REF")


def get_github_repository():
    """e.g. octocat/Hello-World"""
    return os.environ.get("GITHUB_REPOSITORY")


def get_github_run_id():
    """e.g. 88748489334"""
    return os.environ.get("GITHUB_RUN_ID")


def get_pull_request_number(github_ref):
    """
    >>> get_pull_request_number("refs/pull/<pull_request_number>/merge")
    "<pull_request_number>"
    """
    return github_ref.split("/")[2]


def is_pull_request(github_ref):
    return github_ref and github_ref.startswith("refs/pull/")


def post_webhook(repo_token):
    """https://docs.coveralls.io/parallel-build-webhook"""
    url = "https://coveralls.io/webhook"
    build_num = get_github_run_id()
    # note this (undocumented) parameter is optional, but needed for using
    # `GITHUB_TOKEN` rather than `COVERALLS_REPO_TOKEN`
    repo_name = get_github_repository()
    json = {
        "repo_token": repo_token,
        "repo_name": repo_name,
        "payload": {"build_num": build_num, "status": "done"},
    }
    log.debug(f'requests.post("{url}", json={json})')
    response = requests.post(url, json=json)
    response.raise_for_status()
    result = response.json()
    log.debug(f"response.json(): {result}")
    assert result.get("done", False), result


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in {"false", "f", "0", "no", "n"}:
        return False
    elif value.lower() in {"true", "t", "1", "yes", "y"}:
        return True
    raise ValueError(f"{value} is not a valid boolean value")


def parse_args():
    parser = argparse.ArgumentParser(description="Greetings")
    parser.add_argument("--github-token", nargs=1, required=True)
    parser.add_argument("--flag-name", required=False, default=False)
    parser.add_argument("--base-path", required=False, default=False)
    parser.add_argument(
        "--parallel", type=str_to_bool, nargs="?", const=True, default=False
    )
    parser.add_argument(
        "--parallel-finished", type=str_to_bool, nargs="?", const=True, default=False
    )
    parser.add_argument(
        "--debug", type=str_to_bool, nargs="?", const=True, default=False
    )
    return parser.parse_args()


def set_log_level(debug):
    level = logging.DEBUG if debug else logging.INFO
    log.addHandler(logging.StreamHandler())
    log.setLevel(level)


def main():
    args = parse_args()
    debug = args.debug
    repo_token = args.github_token[0]
    parallel = args.parallel
    flag_name = args.flag_name
    base_path = args.base_path
    parallel_finished = args.parallel_finished
    set_log_level(debug)
    log.debug(f"args: {args}")
    if parallel_finished:
        post_webhook(repo_token)
    else:
        run_coveralls(repo_token, parallel, flag_name, base_path)


def try_main():
    try:
        main()
    except Exception as e:
        set_failed(e)


if __name__ == "__main__":
    try_main()  # pragma: no cover
