# Container image that runs your code
FROM andremiras/coveralls:latest

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY src/ /src/

# Code file to execute when the docker container starts up (`entrypoint.py`)
ENTRYPOINT ["/src/entrypoint.py"]
