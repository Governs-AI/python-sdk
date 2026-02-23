# SPDX-License-Identifier: MIT
# Copyright (c) 2024 GovernsAI. All rights reserved.
"""
Tool client for tool registration and execution.
"""

from typing import Dict, Any, List, Optional
from ..utils.http import HTTPClient
from ..utils.logging import GovernsAILogger
from ..exceptions.tool import ToolError, ToolNotFoundError, ToolExecutionError


class ToolClient:
    """Client for tool operations."""

    def __init__(self, http_client: HTTPClient, logger: GovernsAILogger):
        """Initialize tool client."""
        self.http_client = http_client
        self.logger = logger

    async def register_tools(self, tools: List[Dict[str, Any]]) -> bool:
        """
        Register tools with the GovernsAI service.

        Args:
            tools: List of tool definitions

        Returns:
            True if registration was successful
        """
        try:
            self.logger.debug(f"Registering {len(tools)} tools")
            response = await self.http_client.post(
                "/tools",
                data={"tools": tools},
            )
            return response.is_success
        except Exception as e:
            self.logger.error(f"Register tools failed: {str(e)}")
            raise ToolError(f"Register tools failed: {str(e)}")

    async def get_tool_metadata(self, tool_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool metadata
        """
        try:
            self.logger.debug(f"Getting tool metadata: {tool_name}")
            response = await self.http_client.get(f"/tools/{tool_name}")
            return response.data
        except Exception as e:
            self.logger.error(f"Get tool metadata failed: {str(e)}")
            if "not found" in str(e).lower():
                raise ToolNotFoundError(f"Tool not found: {tool_name}", tool_name=tool_name)
            raise ToolError(f"Get tool metadata failed: {str(e)}")

    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        user_id: str,
        corr_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool with governance.

        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments
            user_id: User ID
            corr_id: Correlation ID

        Returns:
            Tool execution result
        """
        try:
            self.logger.debug(f"Executing tool: {tool_name}")
            response = await self.http_client.post(
                f"/tools/{tool_name}/execute",
                data={
                    "args": args,
                    "userId": user_id,
                    "corrId": corr_id,
                },
            )
            return response.data
        except Exception as e:
            self.logger.error(f"Execute tool failed: {str(e)}")
            if "not found" in str(e).lower():
                raise ToolNotFoundError(f"Tool not found: {tool_name}", tool_name=tool_name)
            raise ToolExecutionError(f"Execute tool failed: {str(e)}", tool_name=tool_name)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.

        Returns:
            List of tool definitions
        """
        try:
            self.logger.debug("Listing tools")
            response = await self.http_client.get("/tools")
            return response.data.get("tools", [])
        except Exception as e:
            self.logger.error(f"List tools failed: {str(e)}")
            raise ToolError(f"List tools failed: {str(e)}")

    async def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool.

        Args:
            tool_name: Name of the tool to unregister

        Returns:
            True if unregistration was successful
        """
        try:
            self.logger.debug(f"Unregistering tool: {tool_name}")
            response = await self.http_client.delete(f"/tools/{tool_name}")
            return response.is_success
        except Exception as e:
            self.logger.error(f"Unregister tool failed: {str(e)}")
            raise ToolError(f"Unregister tool failed: {str(e)}")

    async def update_tool(
        self,
        tool_name: str,
        tool_definition: Dict[str, Any],
    ) -> bool:
        """
        Update a tool definition.

        Args:
            tool_name: Name of the tool to update
            tool_definition: New tool definition

        Returns:
            True if update was successful
        """
        try:
            self.logger.debug(f"Updating tool: {tool_name}")
            response = await self.http_client.put(
                f"/tools/{tool_name}",
                data=tool_definition,
            )
            return response.is_success
        except Exception as e:
            self.logger.error(f"Update tool failed: {str(e)}")
            raise ToolError(f"Update tool failed: {str(e)}")
