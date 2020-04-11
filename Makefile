DOCKER_IMAGE_LINUX=andremiras/coveralls-python-action

docker/build:
	docker build --tag=$(DOCKER_IMAGE_LINUX) .

docker/run:
	docker run -it --rm $(DOCKER_IMAGE_LINUX)

docker/run/shell:
	docker run -it --rm --entrypoint /bin/sh $(DOCKER_IMAGE_LINUX)
