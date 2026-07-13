from cloudflared_mcp.app import mcp
from cloudflared_mcp import tools  # noqa: F401  (imported for tool registration side-effects)
from cloudflared_mcp.config import load_server_config


def main():
    cfg = load_server_config()
    mcp.run(transport="http", host=cfg.host, port=cfg.port, path=cfg.path)


if __name__ == "__main__":
    main()
