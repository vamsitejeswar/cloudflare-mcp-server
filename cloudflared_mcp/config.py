import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfig:
    """Address the HTTP server listens on (not Cloudflare auth)."""

    host: str
    port: int
    path: str


def load_server_config() -> ServerConfig:
    # Cloud Run injects PORT and requires the container to listen on it;
    # MCP_PORT (if set) takes precedence for other deployment targets.
    port = os.environ.get("MCP_PORT") or os.environ.get("PORT", "8000")
    return ServerConfig(
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        port=int(port),
        path=os.environ.get("MCP_PATH", "/mcp"),
    )
