# Remote/hosted MCP server image — the governed clinical tool boundary over HTTP.
# The same server.py also runs stdio locally; here we default it to the streamable-http transport
# so it can be fronted by an Azure Container App with internal ingress.
FROM python:3.12-slim

WORKDIR /app

# Runtime deps (the mcp SDK). governed_tools.py + contracts are dependency-free.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Server code, pure tool logic, and the JSON contracts it validates against.
COPY governed_tools.py server.py ./
COPY tool-contracts ./tool-contracts

# HTTP transport on 0.0.0.0:8080 by default. Override MCP_TRANSPORT=stdio for local stdio use.
ENV MCP_TRANSPORT=http \
    HOST=0.0.0.0 \
    PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
