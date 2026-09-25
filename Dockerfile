# SourceTrace MCP server — zero-dependency container image
# Used by MCP directory sites (Glama et al.) to run tools/list introspection in a sandbox.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcp_server.py trace_engine.py config.py store.py alipay.py newsylist_client.py compliance_db.py ./

RUN pip install --no-cache-dir .

# The server is a stdio MCP server: stdio must stay free for protocol traffic.
# All diagnostics go to stderr (see mcp_server.py _log()).
ENTRYPOINT ["source-trace"]
