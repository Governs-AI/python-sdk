# GovernsAI Python SDK Documentation

## Overview

The GovernsAI Python SDK provides a comprehensive interface for integrating AI governance capabilities into Python applications. It offers secure control over AI interactions, budget management, policy enforcement, and compliance monitoring.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Core Client](#core-client)
- [Feature Modules](#feature-modules)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

```bash
pip install governs-ai-sdk
```

### Requirements

- Python 3.8+
- requests >= 2.25.0
- pydantic >= 1.8.0
- typing-extensions >= 3.10.0

## Quick Start

```python
from governs_ai import GovernsAIClient

# Create client with organization context
client = GovernsAIClient(
    api_key="your-api-key",
    base_url="http://localhost:3002",
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

## Configuration

### Environment Variables

```bash
export GOVERNS_API_KEY="your-api-key"
export GOVERNS_BASE_URL="http://localhost:3002"
export GOVERNS_ORG_ID="org-456"
export GOVERNS_TIMEOUT="30000"
export GOVERNS_RETRIES="3"
export GOVERNS_RETRY_DELAY="1000"
```

### Programmatic Configuration

```python
from governs_ai import GovernsAIClient, GovernsAIConfig

# Explicit configuration
config = GovernsAIConfig(
    api_key="your-api-key",
    base_url="http://localhost:3002",
    org_id="org-456",
    timeout=30000,
    retries=3,
    retry_delay=1000
)

client = GovernsAIClient(config)

# Or create from environment
client = GovernsAIClient.from_env()
```

## Core Client

### GovernsAIClient

The main client class that orchestrates all SDK functionality.

```python
from governs_ai import GovernsAIClient

client = GovernsAIClient(
    api_key="your-api-key",
    org_id="org-456"
)

# Core methods
await client.test_connection()
await client.precheck_request(request, user_id)
await client.get_budget_context(user_id)
await client.record_usage(usage_record)
await client.get_health_status()
```

### Configuration Management

```python
# Update configuration
client.update_config({
    "timeout": 60000,
    "retries": 5
})

# Get current configuration
config = client.get_config()
print(f"Base URL: {config.base_url}")
```

## Feature Modules

### 1. PrecheckClient

Handles request validation and governance compliance.

```python
from governs_ai import PrecheckClient

precheck = client.precheck

# Check a request
response = await precheck.check_request(
    tool="model.chat",
    scope="net.external",
    raw_text="User message",
    payload={"messages": [...]},
    tags=["chat"],
    user_id="user-123"
)

# Check a tool call
response = await precheck.check_tool_call(
    tool="payment_process",
    args={"amount": 100, "currency": "USD"},
    scope="net.external",
    user_id="user-123"
)

# Check chat message
response = await precheck.check_chat_message(
    messages=[{"role": "user", "content": "Hello"}],
    provider="openai",
    user_id="user-123"
)
```

### 2. ConfirmationClient

Manages WebAuthn-based approval workflows.

```python
from governs_ai import ConfirmationClient

confirmation = client.confirmation

# Create confirmation request
confirmation_response = await confirmation.create_confirmation(
    request_type="tool_call",
    request_desc="Payment processing",
    request_payload={"amount": 100},
    reasons=["High amount transaction"],
    user_id="user-123"
)

# Get confirmation status
status = await confirmation.get_confirmation_status(
    correlation_id=confirmation_response.correlation_id
)

# Poll for approval
approved_confirmation = await confirmation.poll_confirmation(
    correlation_id=confirmation_response.correlation_id,
    max_duration=300000,  # 5 minutes
    poll_interval=5000    # 5 seconds
)
```

### 3. BudgetClient

Manages usage tracking and budget enforcement.

```python
from governs_ai import BudgetClient

budget = client.budget

# Get budget context
context = await budget.get_budget_context(user_id="user-123")
print(f"Monthly limit: {context.monthly_limit}")
print(f"Current spend: {context.current_spend}")
print(f"Remaining: {context.remaining_budget}")

# Check budget before operation
budget_status = await budget.check_budget(
    estimated_cost=0.15,
    user_id="user-123"
)

if not budget_status.allowed:
    print(f"Budget exceeded: {budget_status.reason}")

# Record usage after AI call
await budget.record_usage(
    user_id="user-123",
    org_id="org-456",
    provider="openai",
    model="gpt-4",
    input_tokens=100,
    output_tokens=50,
    cost=0.15,
    cost_type="external"
)
```

### 4. ToolClient

Manages tool registration and execution.

```python
from governs_ai import ToolClient

tools = client.tools

# Register tools
await tools.register_tools([
    {
        "name": "weather_current",
        "description": "Get current weather",
        "parameters": {
            "location": {"type": "string", "description": "City name"}
        }
    }
])

# Get tool metadata
metadata = await tools.get_tool_metadata("weather_current")

# Execute tool with governance
result = await tools.execute_tool(
    tool_name="weather_current",
    args={"location": "New York"},
    user_id="user-123"
)
```

### 5. AnalyticsClient

Provides dashboard data and usage insights.

```python
from governs_ai import AnalyticsClient

analytics = client.analytics

# Get decision analytics
decisions = await analytics.get_decisions(
    time_range="30d",
    include_stats=True
)

# Get tool call analytics
tool_calls = await analytics.get_tool_calls(
    time_range="7d",
    include_stats=True
)

# Get spend analytics
spend_data = await analytics.get_spend_analytics(
    time_range="30d"
)

# Get usage records
usage_records = await analytics.get_usage_records(
    time_range="7d",
    user_id="user-123"
)
```

## Error Handling

### Custom Exception Classes

```python
from governs_ai.exceptions import (
    GovernsAIError,
    PrecheckError,
    ConfirmationError,
    BudgetError,
    ToolError,
    AnalyticsError
)

try:
    response = await client.precheck_request(request, user_id)
except PrecheckError as e:
    print(f"Precheck failed: {e.message}")
    print(f"Status code: {e.status_code}")
    print(f"Retryable: {e.retryable}")
except GovernsAIError as e:
    print(f"SDK error: {e.message}")
```

### Retry Logic

```python
from governs_ai.utils import with_retry, RetryConfig

# Custom retry configuration
retry_config = RetryConfig(
    max_retries=5,
    retry_delay=2000,
    retry_condition=lambda error: isinstance(error, NetworkError)
)

# Use with retry
@with_retry(retry_config)
async def risky_operation():
    return await client.precheck_request(request, user_id)

result = await risky_operation()
```

## Advanced Usage

### Multi-User Support

```python
# Same client instance for multiple users
client = GovernsAIClient(
    api_key="your-api-key",
    org_id="org-456"  # Static organization context
)

# Different users
user1 = "user-123"
user2 = "user-456"

# User-specific operations
budget1 = await client.get_budget_context(user1)
budget2 = await client.get_budget_context(user2)

precheck1 = await client.precheck_request(request, user1)
precheck2 = await client.precheck_request(request, user2)
```

### Async Context Manager

```python
async with GovernsAIClient(api_key="key", org_id="org") as client:
    response = await client.precheck_request(request, user_id)
    # Client automatically cleaned up
```

### Custom HTTP Client

```python
import aiohttp
from governs_ai import GovernsAIClient

# Custom session with specific settings
session = aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=60),
    connector=aiohttp.TCPConnector(limit=100)
)

client = GovernsAIClient(
    api_key="your-api-key",
    org_id="org-456",
    http_client=session
)
```

### Logging Configuration

```python
import logging
from governs_ai import GovernsAIClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("governs_ai")

client = GovernsAIClient(
    api_key="your-api-key",
    org_id="org-456",
    logger=logger
)
```

## API Reference

### GovernsAIClient

#### Constructor

```python
GovernsAIClient(
    api_key: str,
    base_url: str = "http://localhost:3002",
    org_id: str,
    timeout: int = 30000,
    retries: int = 3,
    retry_delay: int = 1000,
    logger: Optional[Logger] = None,
    http_client: Optional[aiohttp.ClientSession] = None
)
```

#### Methods

```python
async def test_connection(self) -> bool
async def precheck_request(self, request: PrecheckRequest, user_id: str) -> PrecheckResponse
async def get_budget_context(self, user_id: str) -> BudgetContext
async def record_usage(self, usage: UsageRecord) -> None
async def create_confirmation(self, request: ConfirmationRequest, user_id: str) -> ConfirmationResponse
async def get_health_status(self) -> HealthStatus
def update_config(self, new_config: Partial[GovernsAIConfig]) -> None
def get_config(self) -> GovernsAIConfig
```

### Data Models

#### PrecheckRequest

```python
@dataclass
class PrecheckRequest:
    tool: str
    scope: str
    raw_text: str
    payload: Dict[str, Any]
    tags: List[str]
    corr_id: Optional[str] = None
    user_id: Optional[str] = None
```

#### PrecheckResponse

```python
@dataclass
class PrecheckResponse:
    decision: Decision  # "allow" | "deny" | "confirm" | "redact" (legacy "block" maps to "deny")
    reasons: List[str]
    metadata: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_url: Optional[str] = None
```

#### BudgetContext

```python
@dataclass
class BudgetContext:
    monthly_limit: float
    current_spend: float
    remaining_budget: float
    currency: str = "USD"
    period_start: Optional[str] = None
    period_end: Optional[str] = None
```

#### UsageRecord

```python
@dataclass
class UsageRecord:
    user_id: str
    org_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    cost_type: str  # "internal" | "external"
    timestamp: Optional[str] = None
```

## Examples

### Chat Application Integration

```python
import asyncio
from governs_ai import GovernsAIClient

class ChatApplication:
    def __init__(self, api_key: str, org_id: str):
        self.client = GovernsAIClient(api_key=api_key, org_id=org_id)

    async def process_message(self, messages: List[Dict], user_id: str) -> Dict:
        # Precheck the message
        precheck_response = await self.client.precheck_request(
            tool="model.chat",
            scope="net.external",
            raw_text=messages[-1]["content"],
            payload={"messages": messages},
            tags=["chat", "integration"],
            user_id=user_id
        )

        if precheck_response.decision == "deny":
            return {"allowed": False, "response": "Message blocked"}

        if precheck_response.decision == "confirm":
            return {
                "allowed": False,
                "confirmation_required": True,
                "confirmation_url": precheck_response.confirmation_url
            }

        # Process with AI
        ai_response = await self.call_ai(messages)

        # Record usage
        await self.client.record_usage({
            "user_id": user_id,
            "org_id": self.client.get_config().org_id,
            "provider": "openai",
            "model": "gpt-4",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost": 0.15,
            "cost_type": "external"
        })

        return {"allowed": True, "response": ai_response}

    async def call_ai(self, messages: List[Dict]) -> str:
        # Your AI provider integration
        return "AI response"

# Usage
app = ChatApplication(api_key="your-key", org_id="org-456")
result = await app.process_message(
    messages=[{"role": "user", "content": "Hello"}],
    user_id="user-123"
)
```

### Tool Calling with Governance

```python
from governs_ai import GovernsAIClient

class ToolCallingApplication:
    def __init__(self, api_key: str, org_id: str, user_id: str):
        self.client = GovernsAIClient(api_key=api_key, org_id=org_id)
        self.user_id = user_id

    async def execute_tool_call(self, tool_call: Dict) -> Dict:
        # Precheck the tool call
        precheck_response = await self.client.precheck.check_tool_call(
            tool=tool_call["function"]["name"],
            args=json.loads(tool_call["function"]["arguments"]),
            scope="net.external",
            user_id=self.user_id
        )

        if precheck_response.decision == "deny":
            return {"success": False, "error": "Tool call blocked by policy"}

        if precheck_response.decision == "confirm":
            return {
                "success": False,
                "confirmation_required": True,
                "confirmation_url": precheck_response.confirmation_url
            }

        # Execute the tool
        try:
            result = await self.execute_tool(
                tool_call["function"]["name"],
                json.loads(tool_call["function"]["arguments"])
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_tool(self, tool_name: str, args: Dict) -> Any:
        # Your tool execution logic
        if tool_name == "weather_current":
            return {"temperature": 72, "condition": "sunny"}
        # ... other tools
```

### Dashboard Analytics

```python
from governs_ai import GovernsAIClient
from datetime import datetime, timedelta

class DashboardApplication:
    def __init__(self, api_key: str, org_id: str):
        self.client = GovernsAIClient(api_key=api_key, org_id=org_id)

    async def get_dashboard_data(self, time_range: str = "30d") -> Dict:
        # Get various analytics
        decisions = await self.client.analytics.get_decisions(
            time_range=time_range,
            include_stats=True
        )

        tool_calls = await self.client.analytics.get_tool_calls(
            time_range=time_range,
            include_stats=True
        )

        spend_data = await self.client.analytics.get_spend_analytics(
            time_range=time_range
        )

        return {
            "decisions": decisions,
            "tool_calls": tool_calls,
            "spend": spend_data,
            "summary": {
                "total_requests": decisions.stats.total,
                "blocked_requests": decisions.stats.by_decision.get("deny", 0),
                "total_cost": spend_data.total_cost,
                "most_used_tool": max(tool_calls.stats.by_tool.items(), key=lambda x: x[1])[0]
            }
        }
```

## Troubleshooting

### Common Issues

#### 1. Connection Errors

```python
try:
    is_connected = await client.test_connection()
except GovernsAIError as e:
    print(f"Connection failed: {e.message}")
    # Check your base_url and network connectivity
```

#### 2. Authentication Errors

```python
try:
    response = await client.precheck_request(request, user_id)
except GovernsAIError as e:
    if e.status_code == 401:
        print("Invalid API key")
    elif e.status_code == 403:
        print("Insufficient permissions")
```

#### 3. Rate Limiting

```python
from governs_ai.utils import with_retry, RetryConfig

# Configure retry for rate limiting
retry_config = RetryConfig(
    max_retries=5,
    retry_delay=1000,
    retry_condition=lambda error: error.status_code == 429
)

@with_retry(retry_config)
async def rate_limited_operation():
    return await client.precheck_request(request, user_id)
```

#### 4. Timeout Issues

```python
# Increase timeout for slow operations
client = GovernsAIClient(
    api_key="your-key",
    org_id="org-456",
    timeout=60000  # 60 seconds
)
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("governs_ai")

client = GovernsAIClient(
    api_key="your-key",
    org_id="org-456",
    logger=logger
)
```

### Health Monitoring

```python
# Check service health
health = await client.get_health_status()
print(f"Status: {health.status}")
print(f"Services: {health.services}")

if health.status != "healthy":
    print("Some services are degraded or unavailable")
```

## Best Practices

### 1. Error Handling

```python
async def safe_precheck(client, request, user_id):
    try:
        return await client.precheck_request(request, user_id)
    except PrecheckError as e:
        if e.retryable:
            # Retry logic here
            pass
        else:
            # Handle non-retryable error
            pass
    except GovernsAIError as e:
        # Handle general SDK errors
        pass
```

### 2. Resource Management

```python
# Use async context manager
async with GovernsAIClient(api_key="key", org_id="org") as client:
    # Your operations here
    pass  # Client automatically cleaned up
```

### 3. Configuration Management

```python
# Use environment variables for sensitive data
import os

client = GovernsAIClient(
    api_key=os.getenv("GOVERNS_API_KEY"),
    org_id=os.getenv("GOVERNS_ORG_ID"),
    base_url=os.getenv("GOVERNS_BASE_URL", "http://localhost:3002")
)
```

### 4. Performance Optimization

```python
# Reuse client instances
client = GovernsAIClient(api_key="key", org_id="org")

# Multiple operations with same client
for user_id in user_ids:
    budget = await client.get_budget_context(user_id)
    # Process budget data
```

## Migration Guide

### From TypeScript SDK

The Python SDK follows the same architectural patterns as the TypeScript SDK:

- **Static orgId**: Set once per client instance
- **Dynamic userId**: Passed per operation
- **Same API structure**: Methods and parameters match
- **Same error handling**: Similar exception hierarchy

### Key Differences

1. **Async/Await**: Python uses `async`/`await` syntax
2. **Type Hints**: Python uses type hints instead of TypeScript types
3. **Data Classes**: Python uses `@dataclass` instead of interfaces
4. **Exception Handling**: Python uses `try`/`except` instead of `try`/`catch`

## Support

- **Documentation**: [GitHub Repository](https://github.com/governs-ai/python-sdk)
- **Issues**: [GitHub Issues](https://github.com/governs-ai/python-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/governs-ai/python-sdk/discussions)

## License

MIT License - see [LICENSE](LICENSE) file for details.
