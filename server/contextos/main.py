import sys
import argparse
import uvicorn
from contextos.config import settings

def main():
    parser = argparse.ArgumentParser(description="ContextOS AI Operating Layer Daemon & MCP Server")
    parser.add_argument("--mcp", action="store_true", help="Run in MCP Stdio mode for IDE/agent connections")
    parser.add_argument("--mcp-stdio", action="store_true", help="Alias for --mcp")
    args = parser.parse_args()

    if args.mcp or args.mcp_stdio:
        from contextos.mcp.server import mcp_server
        mcp_server.run(transport="stdio")
    else:
        print(f"[ContextOS Daemon] Starting local AI operating layer on {settings.HOST}:{settings.PORT}")
        uvicorn.run(
            "contextos.api.app:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            log_level="info",
        )

if __name__ == "__main__":
    main()

