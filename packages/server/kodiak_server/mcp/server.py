"""MCP server for Kodiak (streamable HTTP transport).

Uses the same tool definitions from kodiak.mcp.tools, served over
streamable HTTP for remote agents (Panda iOS, Bear Claw, etc.).
"""

from __future__ import annotations


def create_mcp_app():
    """Create the MCP ASGI application for mounting in FastAPI.

    Returns an ASGI app that handles the MCP streamable-http protocol.
    """
    from kodiak.mcp.tools import build_server

    server = build_server()
    return server.streamable_http_app()
