FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY cloudflared_mcp ./cloudflared_mcp

RUN pip install --no-cache-dir .

# Cloud Run sets PORT and expects the container to listen on it (see config.py).
ENV MCP_HOST=0.0.0.0

CMD ["cloudflared-mcp-server"]
