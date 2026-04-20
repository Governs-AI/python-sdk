# PROJECT_SPECS.md

## Project Overview
- **Project Name**: GovernsAI Python SDK
- **Version**: `0.1.0-alpha.1`
- **Last Updated**: 2026-04-20 19:20 UTC
- **Primary Purpose**: Ship a Python client library for calling GovernsAI governance endpoints from application code.
- **Target Audience**: Python application developers integrating GovernsAI policy checks, budget controls, and context-memory features.

## Current Project Status
- **Development Stage**: Alpha
- **Build Status**: Passing locally: `black --check src/governs_ai tests`, `flake8 src/governs_ai tests --max-line-length=88 --extend-ignore=E203,W503`, `mypy src/governs_ai --ignore-missing-imports`, and `pytest` (`36 passed`, `2 deselected` integration tests).
- **Test Coverage**: Not measured in-repo.
- **Known Issues**: Integration tests require a local precheck service and are excluded from default `pytest`; `docs/README.md` still contains historical broader-SDK examples and should be treated as supplemental.
- **Next Milestone**: Push the cleaned `dev` branch to GitHub and resume follow-on alpha release work once external publish blockers are cleared.

## Architecture Overview

### Tech Stack
- **Frontend**: None.
- **Backend**: Python package built with `setuptools`; HTTP clients use `httpx` for the core shipped client and `aiohttp` for lower-level helper modules.
- **Database**: None in-repo; this SDK talks to external GovernsAI services.
- **Infrastructure**: GitHub Actions for CI, PR labeling, and tag-based PyPI publishing.
- **Development Tools**: `pytest`, `pytest-asyncio`, `pytest-httpx`, `respx`, `black`, `flake8`, `mypy`.

### System Architecture
- **Architecture Pattern**: SDK/library with a `src/` package layout and typed helper modules.
- **Key Components**:
  - `src/governs_ai/client.py`: main sync/async client for precheck, budget, and usage calls
  - `src/governs_ai/memory.py`: context-memory store/search/delete helpers
  - `src/governs_ai/types.py`: lightweight typed result objects used by the top-level client
  - `src/governs_ai/clients/`: lower-level async clients for budget, precheck, context, documents, confirmation, tool, and analytics endpoints
  - `src/governs_ai/models/`: request/response dataclasses for helper modules
  - `src/governs_ai/utils/`: retry, logging, and HTTP utilities
- **Data Flow**: Application code calls `GovernsAIClient` or a lower-level helper -> request is serialized into JSON or multipart form data -> request is sent to the GovernsAI API -> response is normalized into typed Python objects.
- **External Dependencies**: GovernsAI API endpoints (default public base URL `https://api.governs.ai`), GitHub Actions, PyPI publishing workflow.

### Directory Structure
```text
python-sdk/
├── .github/workflows/        # CI, publish, and PR labeling automation
├── docs/README.md            # Supplemental package reference with legacy-context note
├── src/governs_ai/           # Canonical packaged source tree
│   ├── client.py             # Main sync/async SDK client
│   ├── memory.py             # Context-memory helpers
│   ├── types.py              # Top-level result dataclasses
│   ├── clients/             # Lower-level async endpoint clients
│   ├── models/              # Typed request/response models
│   ├── exceptions/          # SDK exception hierarchy
│   └── utils/               # HTTP, retry, and logging helpers
├── tests/                    # Unit tests plus integration tests
├── LICENSE                   # MIT license
├── pyproject.toml            # Packaging, dependency, and pytest config
├── README.md                 # Current top-level developer guide
└── PROJECT_SPECS.md          # Living project state document
```

## Core Features & Modules
- **Precheck Client**: Sync and async `/api/v1/precheck` helpers via `GovernsAIClient.precheck()` and `GovernsAIClient.async_precheck()`; status: active.
- **Budget Helpers**: `budget_check()` plus `record_usage()` helpers for usage enforcement and accounting; status: active.
- **Context Memory**: `client.memory.store/search/delete` and async variants for context-memory operations; status: active.
- **Advanced Helper Modules**: `governs_ai.clients`, `governs_ai.models`, `governs_ai.utils`, and `governs_ai.exceptions` provide lower-level access and typed helpers; status: active but documented more fully in supplemental docs than in the top-level README.
- **Integration Tests**: Local-service tests under `tests/integration/` validate real precheck flows when a local API is available; status: optional/manual.

## API Documentation
- **Base URL**: `https://api.governs.ai` by default; integration tests can point to `http://localhost:8000`.
- **Authentication**: API key passed in the `X-Governs-Key` header by the shipped top-level client; lower-level helpers also set SDK-specific headers via utility clients.
- **Key Endpoints**:
  - `POST /api/v1/precheck`
  - `GET /api/v1/budget/context`
  - `POST /api/v1/usage`
  - `POST /api/v1/context/store`
  - `POST /api/v1/context/search`
  - `POST /api/v1/context/delete`
- **Data Models**: `PrecheckResult`, `BudgetResult`, `MemoryResult`, plus helper dataclasses in `src/governs_ai/models/`.

## Database Schema
- **Tables/Collections**: None in-repo.
- **Key Relationships**: Not applicable; persistence lives in external GovernsAI services.
- **Indexes**: Not applicable.

## Development Workflow

### Setup Instructions
1. Create a virtual environment: `python3 -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install the package and dev dependencies: `pip install -e ".[dev]"`
4. Run local validation: `pytest`, `black --check src/governs_ai tests`, `flake8 src/governs_ai tests --max-line-length=88 --extend-ignore=E203,W503`, `mypy src/governs_ai --ignore-missing-imports`

### Testing Strategy
- **Unit Tests**: `tests/test_*.py`; run with `pytest`
- **Integration Tests**: `tests/integration/` and `tests/integration_test.py`; run with `pytest -m integration`
- **E2E Tests**: None in-repo

### Deployment Process
- **Staging**: Push to `dev` and rely on CI for lint/typecheck/test checks.
- **Production**: Push a version tag matching `v*` to trigger `.github/workflows/publish.yml`.
- **Rollback**: Revert the bad commit and publish a corrected follow-up version; no in-repo rollback automation exists.

## Configuration Management
- **Environment Variables**:
  - `GOVERNS_API_KEY`: used by local examples/integration tests
  - `GOVERNS_BASE_URL`: overrides the service URL in integration tests/examples
  - `GOVERNS_ORG_ID`: org identifier used by integration tests/examples
- **Config Files**:
  - `pyproject.toml`: package metadata, dependencies, pytest defaults
  - `.github/workflows/ci.yml`: lint, typecheck, test, and secret scan automation
  - `.github/workflows/publish.yml`: tag-driven PyPI publishing
- **Secrets Management**: GitHub Actions uses repository/environment secrets for publish and secret-scan workflows; no secrets are stored in the repo.

## Performance & Monitoring
- **Key Metrics**: Request latency (`PrecheckResult.latency_ms`), retry behavior, and API error rates.
- **Performance Benchmarks**: No formal benchmarks tracked in-repo.
- **Alerting**: None in-repo; GitHub Actions failures act as the current automation signal.

## Security Considerations
- **Authentication/Authorization**: Requests use API-key headers and rely on upstream GovernsAI authorization.
- **Data Protection**: The repo contains no embedded credentials; a GitHub Actions secret scan workflow is present.
- **Security Audits**: No formal audit record is tracked here; current safeguards are dependency pinning plus CI secret scanning.

## Recent Changes Log
- **2026-04-20**: Consolidated the package into a single `src/governs_ai` tree, removing the duplicate root package layout that broke packaging and imports.
- **2026-04-20**: Corrected `pyproject.toml` license metadata to MIT, updated the LICENSE year to 2026, and added missing runtime/dev dependencies needed for the shipped code and tests.
- **2026-04-20**: Updated CI to validate `src/governs_ai`, enabled checks on `dev`, and verified `black`, `flake8`, `mypy`, and `pytest` locally.
- **2026-04-20**: Rewrote the top-level README to match the currently shipped client surface and added this living project spec.

## Team & Contacts
- **Project Lead**: Pixel (SDK & Developer Experience)
- **Key Contributors**: Pixel for SDK implementation; Atlas for API contract coordination
- **Code Reviewers**: Nexus (code quality), Cipher (security/architecture)

## Documentation Links
- **API Docs**: `docs/README.md`
- **User Manual**: `README.md`
- **Development Docs**: `PROJECT_SPECS.md`, `.github/workflows/ci.yml`, `pyproject.toml`
