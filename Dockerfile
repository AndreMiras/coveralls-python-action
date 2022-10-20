FROM thekevjames/coveralls:latest

COPY src/ /src/
RUN python3 -m pip install Cython

ENTRYPOINT ["/src/entrypoint.py"]
