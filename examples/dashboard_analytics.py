"""
Example: Dashboard Analytics

This example shows how to use GovernsAI analytics to build
dashboard views and monitor usage patterns.
"""

import asyncio
from typing import Dict, Any
from governs_ai import GovernsAIClient


class DashboardApplication:
    """Example dashboard application with GovernsAI analytics."""

    def __init__(self, api_key: str, org_id: str):
        """Initialize the dashboard application."""
        self.client = GovernsAIClient(api_key=api_key, org_id=org_id)

    async def get_dashboard_data(self, time_range: str = "30d") -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.

        Args:
            time_range: Time range for analytics

        Returns:
            Dashboard data dictionary
        """
        try:
            # Get various analytics in parallel
            decisions_task = self.client.analytics.get_decisions(
                time_range=time_range,
                include_stats=True
            )
            tool_calls_task = self.client.analytics.get_tool_calls(
                time_range=time_range,
                include_stats=True
            )
            spend_data_task = self.client.analytics.get_spend_analytics(
                time_range=time_range
            )
            dashboard_summary_task = self.client.analytics.get_dashboard_summary(
                time_range=time_range
            )

            # Wait for all analytics to complete
            decisions, tool_calls, spend_data, dashboard_summary = await asyncio.gather(
                decisions_task,
                tool_calls_task,
                spend_data_task,
                dashboard_summary_task
            )

            # Calculate summary statistics
            total_requests = decisions.stats.total
            blocked_requests = decisions.stats.by_decision.get("deny", 0)
            total_cost = spend_data.total_cost

            # Find most used tool
            most_used_tool = None
            if tool_calls.stats.by_tool:
                most_used_tool = max(tool_calls.stats.by_tool.items(), key=lambda x: x[1])[0]

            return {
                "decisions": decisions,
                "tool_calls": tool_calls,
                "spend": spend_data,
                "dashboard_summary": dashboard_summary,
                "summary": {
                    "total_requests": total_requests,
                    "blocked_requests": blocked_requests,
                    "block_rate": (blocked_requests / total_requests * 100) if total_requests > 0 else 0,
                    "total_cost": total_cost,
                    "most_used_tool": most_used_tool,
                    "time_range": time_range
                }
            }

        except Exception as e:
            return {"error": f"Failed to get dashboard data: {str(e)}"}

    async def get_user_analytics(self, user_id: str, time_range: str = "30d") -> Dict[str, Any]:
        """
        Get analytics for a specific user.

        Args:
            user_id: User ID
            time_range: Time range for analytics

        Returns:
            User analytics data
        """
        try:
            # Get user-specific analytics
            decisions = await self.client.analytics.get_decisions(
                time_range=time_range,
                include_stats=True,
                user_id=user_id
            )
            tool_calls = await self.client.analytics.get_tool_calls(
                time_range=time_range,
                include_stats=True,
                user_id=user_id
            )
            spend_data = await self.client.analytics.get_spend_analytics(
                time_range=time_range,
                user_id=user_id
            )
            usage_records = await self.client.analytics.get_usage_records(
                time_range=time_range,
                user_id=user_id,
                limit=100
            )

            return {
                "user_id": user_id,
                "decisions": decisions,
                "tool_calls": tool_calls,
                "spend": spend_data,
                "usage_records": usage_records,
                "summary": {
                    "total_requests": decisions.stats.total,
                    "blocked_requests": decisions.stats.by_decision.get("deny", 0),
                    "total_cost": spend_data.total_cost,
                    "usage_count": len(usage_records)
                }
            }

        except Exception as e:
            return {"error": f"Failed to get user analytics: {str(e)}"}

    async def get_cost_breakdown(self, time_range: str = "30d") -> Dict[str, Any]:
        """
        Get cost breakdown by provider and cost type.

        Args:
            time_range: Time range for analytics

        Returns:
            Cost breakdown data
        """
        try:
            spend_data = await self.client.analytics.get_spend_analytics(time_range=time_range)

            return {
                "total_cost": spend_data.total_cost,
                "currency": spend_data.currency,
                "by_provider": spend_data.by_provider,
                "by_cost_type": spend_data.by_cost_type,
                "by_user": spend_data.by_user,
                "time_range": time_range
            }

        except Exception as e:
            return {"error": f"Failed to get cost breakdown: {str(e)}"}


async def main():
    """Example usage of the dashboard application."""
    # Initialize the application
    app = DashboardApplication(
        api_key="your-api-key",
        org_id="org-456"
    )

    # Test connection
    is_connected = await app.client.test_connection()
    print(f"Connected to GovernsAI: {is_connected}")

    if not is_connected:
        print("Failed to connect to GovernsAI. Please check your configuration.")
        return

    # Get dashboard data
    print("Getting dashboard data...")
    dashboard_data = await app.get_dashboard_data("30d")
    
    if "error" in dashboard_data:
        print(f"Error: {dashboard_data['error']}")
    else:
        summary = dashboard_data["summary"]
        print(f"Dashboard Summary:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Blocked Requests: {summary['blocked_requests']}")
        print(f"  Block Rate: {summary['block_rate']:.1f}%")
        print(f"  Total Cost: ${summary['total_cost']:.2f}")
        print(f"  Most Used Tool: {summary['most_used_tool']}")

    # Get user analytics
    print("\nGetting user analytics...")
    user_analytics = await app.get_user_analytics("user-123", "7d")
    
    if "error" in user_analytics:
        print(f"Error: {user_analytics['error']}")
    else:
        summary = user_analytics["summary"]
        print(f"User Analytics (user-123):")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Blocked Requests: {summary['blocked_requests']}")
        print(f"  Total Cost: ${summary['total_cost']:.2f}")
        print(f"  Usage Records: {summary['usage_count']}")

    # Get cost breakdown
    print("\nGetting cost breakdown...")
    cost_breakdown = await app.get_cost_breakdown("30d")
    
    if "error" in cost_breakdown:
        print(f"Error: {cost_breakdown['error']}")
    else:
        print(f"Cost Breakdown:")
        print(f"  Total Cost: ${cost_breakdown['total_cost']:.2f} {cost_breakdown['currency']}")
        print(f"  By Provider: {cost_breakdown['by_provider']}")
        print(f"  By Cost Type: {cost_breakdown['by_cost_type']}")

    # Close the client
    await app.client.close()


if __name__ == "__main__":
    asyncio.run(main())
