#!/usr/bin/env python3

import argparse
import logging
import os
import sys
from datetime import datetime
from enum import Enum

from coveralls.api import Coveralls, CoverallsException

log = logging.getLogger(__name__)


class ExitCode(Enum):
    SUCCESS = 0
    FAILURE = 1


def set_failed(message):
    log.error(message)
    sys.exit(ExitCode.FAILURE)


def run_coveralls():
    """Submits to coveralls using either GITHUB_TOKEN or COVERALLS_REPO_TOKEN."""
    # note that coveralls.io "service_name" can either be:
    # - "github-actions" (local development?)
    # - "github" (from GitHub jobs?)
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    COVERALLS_REPO_TOKEN = os.environ.get("COVERALLS_REPO_TOKEN")
    repo_token = GITHUB_TOKEN or COVERALLS_REPO_TOKEN
    if GITHUB_TOKEN and COVERALLS_REPO_TOKEN:
        log.warning("Both GITHUB_TOKEN  and COVERALLS_REPO_TOKEN defined.")
    assert repo_token, "Either GITHUB_TOKEN or COVERALLS_REPO_TOKEN must be set."
    # for some reasons the "service_name" can be one or the other
    # (depending on where it's ran from?)
    service_names = ("github", "github-actions")
    kwargs = {"repo_token": repo_token}
    for service_name in service_names:
        log.info(f"Trying submitting coverage with service_name: {service_name}...")
        coveralls = Coveralls(service_name=service_name, **kwargs)
        try:
            result = coveralls.wear()
            break
        except CoverallsException as e:
            log.warning(f"Failed submitting coverage with service_name: {service_name}")
            log.warning(e)
    if result is None:
        set_failed("Failed to submit coverage")
    log.info(result)


def parse_args():
    parser = argparse.ArgumentParser(description="Greetings")
    parser.add_argument("who_to_greet", help="Who to greet", nargs="?", default="World")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def set_log_level(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    log.addHandler(logging.StreamHandler())
    log.setLevel(level)


def main():
    args = parse_args()
    verbose = args.verbose
    set_log_level(verbose)
    who_to_greet = args.who_to_greet
    print(f"Hello {who_to_greet} from Python")
    time = datetime.now().isoformat()
    print(f"::set-output name=time::{time}")
    run_coveralls()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        set_failed(e)
