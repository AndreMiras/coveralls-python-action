#!/usr/bin/env python3

import argparse
import logging
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
    log.error(message)
    sys.exit(ExitCode.FAILURE)


def patch_os_environ(repo_token, parallel):
    """
    Temporarily updates the environment variable to satisfy coveralls Python API.
    That is because the coveralls package API consumes mostly environment variables.
    """
    # https://github.com/coveralls-clients/coveralls-python/blob/2.0.0/coveralls/api.py#L146
    parallel = "true" if parallel else ""
    environ = {"COVERALLS_REPO_TOKEN": repo_token, "COVERALLS_PARALLEL": parallel}
    log.debug(f"Patching os.environ with: {environ}")
    return mock.patch.dict("os.environ", environ)


def run_coveralls(repo_token, parallel=False):
    """Submits job to coveralls."""
    # note that coveralls.io "service_name" can either be:
    # - "github-actions" (local development?)
    # - "github" (from GitHub jobs?)
    # for some reasons the "service_name" can be one or the other
    # (depending on where it's ran from?)
    service_names = ("github", "github-actions")
    result = None
    for service_name in service_names:
        log.info(f"Trying submitting coverage with service_name: {service_name}...")
        with patch_os_environ(repo_token, parallel):
            coveralls = Coveralls(service_name=service_name)
            try:
                result = coveralls.wear()
                break
            except CoverallsException as e:
                log.warning(
                    f"Failed submitting coverage with service_name: {service_name}"
                )
                log.warning(e)
    if result is None:
        set_failed("Failed to submit coverage")
    log.debug(result)
    log.info(result["url"])


def post_webhook(repo_token, build_num):
    """"
    # https://docs.coveralls.io/parallel-build-webhook
    coveralls_finish:
      name: Coveralls finished webhook
      needs: ["Tests"]
      runs-on: ubuntu-latest
      steps:
        - name: webhook
          env:
            COVERALLS_REPO_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            COVERALLS_SERVICE_NAME: github
            TRAVIS_JOB_ID: ${{ github.ref }}:${{ github.sha }}
          run: |
            curl "https://coveralls.io/webhook?repo_token=$COVERALLS_REPO_TOKEN" \
            --data "payload[job_id]=$TRAVIS_JOB_ID&payload[status]=done"
    """
    url = f"https://coveralls.io/webhook?repo_token={repo_token}"
    # TRAVIS_JOB_ID: ${{ github.ref }}:${{ github.sha }}
    # data = "payload[job_id]=$TRAVIS_JOB_ID&payload[status]=done"
    data = {
        "payload": {
            # TODO job_id?
            "build_num": build_num,
            "status": "done",
        }
    }
    requests.post(url, data)


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
    parallel_finished = args.parallel_finished
    set_log_level(debug)
    if parallel_finished:
        # TODO
        # post_webhook(repo_token, build_num)
        pass
    else:
        run_coveralls(repo_token, parallel)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        set_failed(e)
