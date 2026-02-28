# Contributing to GovernsAI Python SDK

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Validation

```bash
pytest
```

## Pull Request Checklist

- Preserve API compatibility unless versioned.
- Add tests for new clients or transport behavior.
- Update README and SDK docs for public API changes.
