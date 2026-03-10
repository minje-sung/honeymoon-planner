import os
from pathlib import Path

_project_root = Path(__file__).parent.parent
FLIGHTS_MCP_DIR = str(_project_root / "mcp_servers" / "flights-mcp")

# Streamlit Cloud 環境かどうかの判定
# mcp_servers フォルダが存在しない = Cloud 環境とみなす
IS_CLOUD = not Path(FLIGHTS_MCP_DIR).exists()


class _DummyMCPServer:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass


def create_flight_mcp_server():
    if IS_CLOUD:
        return _DummyMCPServer()
    from agents.mcp import MCPServerStdio
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    return MCPServerStdio(
        params={"command": "uv", "args": ["run", "--directory", FLIGHTS_MCP_DIR, "flights-mcp"], "env": env},
        cache_tools_list=True,
    )


def create_playwright_mcp_server():
    if IS_CLOUD:
        return _DummyMCPServer()
    from agents.mcp import MCPServerStdio
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    return MCPServerStdio(
        params={"command": "npx", "args": ["@playwright/mcp@latest"], "env": env},
        cache_tools_list=True,
        client_session_timeout_seconds=30,
    )

