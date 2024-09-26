FROM thekevjames/coveralls:4.0.0

COPY src/ /src/
RUN python3 -m pip install Cython

RUN python3 -m pip install "coverage[toml]"

RUN git config --system --add safe.directory "/github/workspace"

ENTRYPOINT ["/src/entrypoint.py"]
