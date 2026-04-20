import asyncio
import os

from governs_ai.client import GovernsAIClient


async def main():
    api_key = os.getenv("GOVERNS_API_KEY", "test-key")
    base_url = os.getenv("GOVERNS_BASE_URL", "http://localhost:8000")
    org_id = os.getenv("GOVERNS_ORG_ID", "test-org")

    client = GovernsAIClient(api_key=api_key, base_url=base_url, org_id=org_id)

    print(f"Checking precheck against {base_url}...")
    try:
        result = await client.async_precheck(
            content="Hello, is this safe?", tool="chat"
        )
        print(f"Decision: {result.decision}")
        print(f"Redacted: {result.redacted_content}")
        print(f"Reasons: {result.reasons}")
        print(f"Latency: {result.latency_ms:.2f}ms")
    except Exception as e:
        print(f"Precheck failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
