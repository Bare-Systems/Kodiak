"""Kodiak Server entry point.

Runs a FastAPI application with:
- REST API at /api/
- MCP server (streamable HTTP) at /mcp/
- Web UI at /
"""

from __future__ import annotations

import argparse
import os
import sys


def create_app():
    """Create the combined FastAPI + MCP application."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    from kodiak_server.mcp.server import create_mcp_app
    from kodiak_server.rest.app import create_rest_app
    from kodiak_server.web import create_web_app

    app = FastAPI(
        title="Kodiak Server",
        description="Automated trading server with REST API and MCP",
        version="2.0.0",
    )

    # API key auth — protects /api/* and /mcp/* routes.
    # Set KODIAK_API_TOKEN in the environment; /health is always exempt.
    @app.middleware("http")
    async def api_key_auth(request: Request, call_next):
        protected = request.url.path.startswith("/api") or request.url.path.startswith("/mcp")
        if protected:
            token = os.environ.get("KODIAK_API_TOKEN", "")
            auth = request.headers.get("Authorization", "")
            if not token or auth != f"Bearer {token}":
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)

    # Health endpoint — no auth required, checked by blink and BearClawWeb.
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "kodiak"}

    # Mount REST API
    rest_app = create_rest_app()
    app.mount("/api", rest_app)

    # Mount MCP (streamable HTTP)
    mcp_app = create_mcp_app()
    app.mount("/mcp", mcp_app)

    # Mount Web UI (must be last — catches remaining routes)
    web_app = create_web_app()
    app.mount("/", web_app)

    return app


def main() -> None:
    """CLI entry point for kodiak-server."""
    parser = argparse.ArgumentParser(description="Kodiak Trading Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--ssl-certfile", default=None, help="TLS certificate file")
    parser.add_argument("--ssl-keyfile", default=None, help="TLS private key file")
    args = parser.parse_args()

    import uvicorn

    ssl_kwargs = {}
    if args.ssl_certfile and args.ssl_keyfile:
        ssl_kwargs["ssl_certfile"] = args.ssl_certfile
        ssl_kwargs["ssl_keyfile"] = args.ssl_keyfile

    print(f"Starting Kodiak Server on {args.host}:{args.port}", file=sys.stderr)
    print(f"  REST API: http://{args.host}:{args.port}/api/", file=sys.stderr)
    print(f"  MCP:      http://{args.host}:{args.port}/mcp/", file=sys.stderr)
    print(f"  Web UI:   http://{args.host}:{args.port}/", file=sys.stderr)

    uvicorn.run(
        "kodiak_server.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        **ssl_kwargs,
    )


if __name__ == "__main__":
    main()
