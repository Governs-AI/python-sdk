# GovernsAI Python SDK

[![npm](https://img.shields.io/npm/v/%40governs-ai%2Fsdk?label=npm%20%40governs-ai%2Fsdk)](https://www.npmjs.com/package/@governs-ai/sdk)
[![PyPI](https://img.shields.io/pypi/v/governs-ai-sdk?label=PyPI%20governs-ai-sdk)](https://pypi.org/project/governs-ai-sdk/)
[![License](https://img.shields.io/badge/license-Elastic%202.0-blue.svg)](LICENSE)

A Python SDK for integrating GovernsAI governance checks into application code. The current package ships a lightweight `src/` layout centered on precheck requests, budget helpers, usage recording, and context-memory operations, with lower-level models and client utilities available under `governs_ai.models`, `governs_ai.clients`, `governs_ai.utils`, and `governs_ai.exceptions`.

## Features

- **Sync and async precheck helpers** for `/api/v1/precheck`
- **Budget checks and usage recording** for governed model traffic
- **Context memory store/search/delete helpers** via `client.memory`
- **Typed result objects** for precheck, budget, and memory flows
- **Lower-level modules** for advanced integrations under `governs_ai.clients`, `governs_ai.models`, `governs_ai.utils`, and `governs_ai.exceptions`

## Installation

```bash
pip install governs-ai-sdk
```

## Quick Start

```python
from governs_ai import GovernsAIClient

client = GovernsAIClient(
    api_key="your-api-key",
    base_url="https://api.governs.ai",
    org_id="org-456",
)

result = client.precheck(
    content="Summarize this document",
    tool="model.chat",
)

print(result.decision)
print(result.reasons)
```

```python
import asyncio

from governs_ai import GovernsAIClient


async def main() -> None:
    client = GovernsAIClient(api_key="your-api-key", org_id="org-456")
    result = await client.async_precheck(
        content="Hello from asyncio",
        tool="model.chat",
    )
    print(result.decision)


asyncio.run(main())
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
pytest -m integration
```

## Documentation

Additional package notes live in [docs/README.md](docs/README.md). The most up-to-date repository state and architecture summary lives in `PROJECT_SPECS.md`.

## License

Elastic License 2.0 — see [LICENSE](LICENSE) for details. Production hosting of the SDK as a managed service requires a separate agreement; normal application-side use in your own product is unrestricted.
