"""
Example: Chat Application Integration

This example shows how to integrate GovernsAI into a chat application
to provide governance and compliance for AI interactions.
"""

import asyncio
from typing import List, Dict, Any
from governs_ai import GovernsAIClient


class ChatApplication:
    """Example chat application with GovernsAI integration."""

    def __init__(self, api_key: str, org_id: str):
        """Initialize the chat application."""
        self.client = GovernsAIClient(api_key=api_key, org_id=org_id)

    async def process_message(self, messages: List[Dict], user_id: str) -> Dict:
        """
        Process a chat message with governance.

        Args:
            messages: List of chat messages
            user_id: User ID

        Returns:
            Response dictionary with allowed status and response
        """
        try:
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
                return {
                    "allowed": False,
                    "response": "Message blocked by governance policy",
                    "reasons": precheck_response.reasons
                }

            if precheck_response.decision == "confirm":
                return {
                    "allowed": False,
                    "confirmation_required": True,
                    "confirmation_url": precheck_response.confirmation_url
                }

            # Check budget before processing
            budget_context = await self.client.get_budget_context(user_id)
            if budget_context.remaining_budget <= 0:
                return {
                    "allowed": False,
                    "response": "Budget exceeded. Please contact administrator."
                }

            # Process with AI (simulated)
            ai_response = await self.call_ai(messages)

            # Record usage
            await self.client.record_usage({
                "user_id": user_id,
                "org_id": self.client.get_config().org_id,
                "provider": "openai",
                "model": "gpt-4",
                "input_tokens": 100,  # Calculate actual tokens
                "output_tokens": 50,   # Calculate actual tokens
                "cost": 0.15,          # Calculate actual cost
                "cost_type": "external"
            })

            return {
                "allowed": True,
                "response": ai_response,
                "budget_remaining": budget_context.remaining_budget
            }

        except Exception as e:
            return {
                "allowed": False,
                "response": f"Error processing message: {str(e)}"
            }

    async def call_ai(self, messages: List[Dict]) -> str:
        """Simulate AI provider call."""
        # In a real application, this would call your AI provider
        return "AI response based on your message"


async def main():
    """Example usage of the chat application."""
    # Initialize the application
    app = ChatApplication(
        api_key="your-api-key",
        org_id="org-456"
    )

    # Test connection
    is_connected = await app.client.test_connection()
    print(f"Connected to GovernsAI: {is_connected}")

    if not is_connected:
        print("Failed to connect to GovernsAI. Please check your configuration.")
        return

    # Example messages
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    user_id = "user-123"

    # Process the message
    result = await app.process_message(messages, user_id)

    print(f"Message processing result: {result}")

    # Close the client
    await app.client.close()


if __name__ == "__main__":
    asyncio.run(main())
