# GovernsAI Python SDK

A comprehensive Python SDK for integrating AI governance capabilities into your applications. Provides secure control over AI interactions, budget management, policy enforcement, and compliance monitoring.

## Features

- **Request Prechecking**: Validate AI requests against governance policies
- **Budget Management**: Track and enforce usage budgets
- **Confirmation Workflows**: WebAuthn-based approval processes
- **Tool Management**: Register and execute tools with governance
- **Analytics**: Comprehensive usage and decision analytics
- **Multi-User Support**: Organization-level context with user-specific operations

## Installation

```bash
pip install governs-ai-sdk
```

## Quick Start

```python
from governs_ai import GovernsAIClient

# Create client with organization context
client = GovernsAIClient(
    api_key="your-api-key",
    base_url="https://api.governsai.com",
    org_id="org-456"  # Organization context (static)
)

# Test connection
is_connected = await client.test_connection()
print(f"Connected: {is_connected}")

# Precheck a request for a specific user (userId is dynamic)
user_id = "user-123"
precheck_response = await client.precheck_request(
    tool="model.chat",
    scope="net.external",
    raw_text="Hello, how are you?",
    payload={"messages": [{"role": "user", "content": "Hello"}]},
    tags=["demo", "chat"],
    user_id=user_id
)

print(f"Decision: {precheck_response.decision}")
if precheck_response.decision == "deny":
    print(f"Blocked: {precheck_response.reasons}")
elif precheck_response.decision == "confirm":
    print("Confirmation required")
```

## Documentation

For complete documentation, see [docs/README.md](docs/README.md).

## License

MIT License - see [LICENSE](LICENSE) file for details.
