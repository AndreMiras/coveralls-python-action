FROM thekevjames/coveralls:latest

COPY src/ /src/

ENTRYPOINT ["/src/entrypoint.py"]
