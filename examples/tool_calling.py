"""
Example: Tool Calling with Governance

This example shows how to integrate GovernsAI into a tool calling system
to provide governance and compliance for tool executions.
"""

import asyncio
import json
from typing import Dict, Any
from governs_ai import GovernsAIClient


class ToolCallingApplication:
    """Example tool calling application with GovernsAI integration."""

    def __init__(self, api_key: str, org_id: str, user_id: str):
        """Initialize the tool calling application."""
        self.client = GovernsAIClient(api_key=api_key, org_id=org_id)
        self.user_id = user_id

    async def execute_tool_call(self, tool_call: Dict) -> Dict:
        """
        Execute a tool call with governance.

        Args:
            tool_call: Tool call dictionary

        Returns:
            Result dictionary with success status and result
        """
        try:
            tool_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])

            # Precheck the tool call
            precheck_response = await self.client.precheck.check_tool_call(
                tool=tool_name,
                args=args,
                scope="net.external",
                user_id=self.user_id
            )

            if precheck_response.decision == "deny":
                return {
                    "success": False,
                    "error": "Tool call blocked by governance policy",
                    "reasons": precheck_response.reasons
                }

            if precheck_response.decision == "confirm":
                # Handle confirmation workflow
                confirmation_response = await self.client.create_confirmation(
                    request_type="tool_call",
                    request_desc=f"Execute {tool_name}",
                    request_payload={"tool": tool_name, "args": args},
                    reasons=precheck_response.reasons,
                    user_id=self.user_id
                )

                return {
                    "success": False,
                    "confirmation_required": True,
                    "confirmation_url": confirmation_response.confirmation_url,
                    "correlation_id": confirmation_response.correlation_id
                }

            # Execute the tool
            result = await self.execute_tool(tool_name, args)
            return {"success": True, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_tool(self, tool_name: str, args: Dict) -> Any:
        """Execute a tool (simulated)."""
        # In a real application, this would execute the actual tool
        if tool_name == "weather_current":
            return {"temperature": 72, "condition": "sunny", "location": args.get("location")}
        elif tool_name == "calculator":
            expression = args.get("expression", "0")
            return {"result": eval(expression)}  # Note: eval is unsafe in production
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def wait_for_confirmation(self, correlation_id: str) -> Dict:
        """
        Wait for confirmation approval.

        Args:
            correlation_id: Correlation ID of the confirmation

        Returns:
            Confirmation result
        """
        try:
            # Poll for confirmation approval
            confirmation_status = await self.client.confirmation.poll_confirmation(
                correlation_id=correlation_id,
                max_duration=300000,  # 5 minutes
                poll_interval=5000    # 5 seconds
            )

            if confirmation_status.approved:
                return {"approved": True, "status": confirmation_status.status}
            else:
                return {"approved": False, "status": confirmation_status.status}

        except Exception as e:
            return {"approved": False, "error": str(e)}


async def main():
    """Example usage of the tool calling application."""
    # Initialize the application
    app = ToolCallingApplication(
        api_key="your-api-key",
        org_id="org-456",
        user_id="user-123"
    )

    # Test connection
    is_connected = await app.client.test_connection()
    print(f"Connected to GovernsAI: {is_connected}")

    if not is_connected:
        print("Failed to connect to GovernsAI. Please check your configuration.")
        return

    # Example tool calls
    tool_calls = [
        {
            "function": {
                "name": "weather_current",
                "arguments": json.dumps({"location": "New York"})
            }
        },
        {
            "function": {
                "name": "calculator",
                "arguments": json.dumps({"expression": "2 + 2"})
            }
        }
    ]

    # Execute tool calls
    for tool_call in tool_calls:
        print(f"\nExecuting tool call: {tool_call['function']['name']}")
        result = await app.execute_tool_call(tool_call)
        print(f"Result: {result}")

    # Close the client
    await app.client.close()


if __name__ == "__main__":
    asyncio.run(main())
