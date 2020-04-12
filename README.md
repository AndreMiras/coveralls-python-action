# coveralls-python-action

[![push](https://github.com/AndreMiras/coveralls-python-action/workflows/push/badge.svg?branch=develop)](https://github.com/AndreMiras/coveralls-python-action/actions?query=workflow%3Apush)
[![Coverage Status](https://coveralls.io/repos/github/AndreMiras/coveralls-python-action/badge.svg?branch=develop)](https://coveralls.io/github/AndreMiras/coveralls-python-action?branch=develop)

GitHub Action for Python Coveralls.io

## Usage
Makes sure your `coverage.py` is configured with `relative_files = True`.
https://coverage.readthedocs.io/en/coverage-5.0.4/config.html#config-run-relative-files

```yaml
- uses: AndreMiras/coveralls-python-action@develop
  with:
    # The `GITHUB_TOKEN` or `COVERALLS_REPO_TOKEN`.
    # Default: ${{ github.token }}
    github-token: ''
    # Set to `true` if you are running parallel jobs, then use `parallel-finished: true` for the last action.
    # Default: false
    parallel: ''
    # Set to `true` for the last action when using `parallel: true`.
    # Note this phase requires `github-token: ${{ secrets.COVERALLS_REPO_TOKEN }}`.
    # Default: false
    parallel-finished: ''
    # Set to true to increase logger verbosity.
    # Default: false
    debug: ''
```

## Example usage
Assuming you have a `make test` that runs coverage testing.
The following will upload it to coveralls.io.
```yaml
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
      with:
        parallel: true

   coveralls_finish:
     needs: test
     runs-on: ubuntu-latest
     steps:
     - name: Coveralls Finished
       uses: AndreMiras/coveralls-python-action@develop
       with:
         parallel-finished: true
         github-token: ${{ secrets.COVERALLS_REPO_TOKEN }}
```
