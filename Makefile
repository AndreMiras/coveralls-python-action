VIRTUAL_ENV ?= venv
PYTHON_MAJOR_VERSION=3
PYTHON_MINOR_VERSION=8
PYTHON_VERSION=$(PYTHON_MAJOR_VERSION).$(PYTHON_MINOR_VERSION)
PYTHON_WITH_VERSION=python$(PYTHON_VERSION)
PYTHON=$(VIRTUAL_ENV)/bin/python
PIP=$(VIRTUAL_ENV)/bin/pip
ISORT=$(VIRTUAL_ENV)/bin/isort
FLAKE8=$(VIRTUAL_ENV)/bin/flake8
PYTEST=$(VIRTUAL_ENV)/bin/pytest
COVERAGE=$(VIRTUAL_ENV)/bin/coverage
BLACK=$(VIRTUAL_ENV)/bin/black
SOURCES=src/ tests/
DOCKER_IMAGE_LINUX=andremiras/coveralls-python-action
DOCKER_WORKDIR=/github/workspace
DOCKER_WORKDIR_FLAG=--workdir $(DOCKER_WORKDIR)
DOCKER_VOLUME=$(CURDIR):$(DOCKER_WORKDIR)
DOCKER_VOLUME_FLAG=--volume $(DOCKER_VOLUME)



$(VIRTUAL_ENV):
	$(PYTHON_WITH_VERSION) -m venv $(VIRTUAL_ENV)
	$(PIP) install --requirement requirements.txt

virtualenv: $(VIRTUAL_ENV)

run: virtualenv
	$(PYTHON) src/entrypoint.py

pytest: virtualenv
	PYTHONPATH=src/ $(COVERAGE) run --source src/ -m pytest tests/
	$(COVERAGE) report -m

test: pytest lint

lint/isort: virtualenv
	$(ISORT) --check-only --recursive --diff $(SOURCES)

lint/flake8: virtualenv
	$(FLAKE8) $(SOURCES)

lint/black: virtualenv
	$(BLACK) --check $(SOURCES)

lint: lint/isort lint/flake8 lint/black

format/isort: virtualenv
	$(ISORT) --recursive $(SOURCES)

format/black: virtualenv
	$(BLACK) $(SOURCES)

format: format/isort format/black

clean:
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +

docker/build:
	docker build --tag=$(DOCKER_IMAGE_LINUX) .

docker/run:
	docker run -it --rm --env-file .env $(DOCKER_WORKDIR_FLAG) $(DOCKER_VOLUME_FLAG) $(DOCKER_IMAGE_LINUX)

docker/run/shell:
	docker run -it --rm --env-file .env $(DOCKER_WORKDIR_FLAG) $(DOCKER_VOLUME_FLAG) --entrypoint /bin/sh $(DOCKER_IMAGE_LINUX)
