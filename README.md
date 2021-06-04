# coveralls-python-action

[![push](https://github.com/AndreMiras/coveralls-python-action/workflows/push/badge.svg?branch=develop)](https://github.com/AndreMiras/coveralls-python-action/actions?query=workflow%3Apush)
[![Coverage Status](https://coveralls.io/repos/github/AndreMiras/coveralls-python-action/badge.svg?branch=develop)](https://coveralls.io/github/AndreMiras/coveralls-python-action?branch=develop)

GitHub Action for Python [Coveralls.io](https://coveralls.io/)

## Screenshot
![coveralls-python-action](https://i.imgur.com/GMLdGT7.png "Screenshot")


## Usage
First make sure your `coverage.py` is configured with [`relative_files = True`](https://coverage.readthedocs.io/en/coverage-5.2.1/config.html#config-run-relative-files).
See the [Coverage.py configuration](#coveragepy-configuration) section for examples.
If this setting is missing you will likely get an error "not a git repository".

Then assuming you have a `make test` that runs coverage testing.
The following workflow will upload it to coveralls.io.

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
        flag-name: Unit Test

  coveralls_finish:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - name: Coveralls Finished
      uses: AndreMiras/coveralls-python-action@develop
      with:
        parallel-finished: true
```

## Configuration
```yaml
- uses: AndreMiras/coveralls-python-action@develop
  with:
    # The `GITHUB_TOKEN` or `COVERALLS_REPO_TOKEN`.
    # Default: ${{ github.token }}
    github-token: ''
    # Set to `true` if you are using parallel jobs, then use `parallel-finished: true` for the last action.
    # Default: false
    parallel: ''
    # Set to `true` for the last action when using `parallel: true`.
    # Default: false
    parallel-finished: ''
    # A name to identify the current job. This is useful in combination with `parallel: true`.
    # Default: null
    flag-name: ''
    # A sub-directory in which coverage was executed.
    # Default: '.'
    base-path: ''
    # Set to true to increase logger verbosity.
    # Default: false
    debug: ''
```

## Coverage.py configuration

The `relative_files = True` setting can be handled via different files such as `.coveragerc`, `tox.ini` and more, all covered in the examples below.
Also see the [Coverage.py configuration reference](https://coverage.readthedocs.io/en/coverage-5.2.1/config.html#configuration-reference) for full details.

### .coveragerc
Under the `[run]` section:
```ini
[run]
relative_files = True
```

### setup.cfg or tox.ini
Under the `[coverage:run]` section:
```ini
[coverage:run]
relative_files = True
```

### pyproject.toml
Under the `[tool.coverage.run]` section.
It also requires `coverage` to be installed with the `toml` extra (`pip install coverage[toml]`):
```ini
[tool.coverage.run]
relative_files = true
```
