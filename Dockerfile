FROM thekevjames/coveralls:latest

COPY src/ /src/
RUN python3 -m pip install Cython

RUN python3 -m pip install "coverage[toml]"

ENTRYPOINT ["/src/entrypoint.py"]
