# Contributing

Create a virtual environment and install the development dependencies:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

Before submitting a change, run:

```bash
ruff format .
ruff check . --fix
mypy src
pytest
```

Keep manifests declarative, avoid bypassing access controls, and add regression
tests for changes to crawling, downloading, transcript handling, or filesystem
behavior.
