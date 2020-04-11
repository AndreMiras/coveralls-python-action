# Container image that runs your code
FROM python:3.8

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY src/ /src/
# TODO: use setup.py
RUN pip install coveralls

# Code file to execute when the docker container starts up (`entrypoint.py`)
ENTRYPOINT ["/src/entrypoint.py"]
