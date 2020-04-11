# coveralls-python-action

[![push](https://github.com/AndreMiras/coveralls-python-action/workflows/push/badge.svg?branch=develop)](https://github.com/AndreMiras/coveralls-python-action/actions?query=workflow%3Apush)
[![Coverage Status](https://coveralls.io/repos/github/AndreMiras/coveralls-python-action/badge.svg?branch=develop)](https://coveralls.io/github/AndreMiras/coveralls-python-action?branch=develop)

GitHub Action for Python Coveralls.io

## Usage
You simply need to set one of the following two environment variables:
- `GITHUB_TOKEN`
- `COVERALLS_REPO_TOKEN`

Also configure your `coverage.py` with `relative_files = True`.
https://coverage.readthedocs.io/en/coverage-5.0.4/config.html#config-run-relative-files

## Example usage
Assuming you have a `make test` that runs coverage testing.
The following will upload it to coveralls.io.
```yml
name: push
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v1

    - name: Unit tests
      run: make test

    - name: Coveralls
      uses: AndreMiras/coveralls-python-action@develop
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
