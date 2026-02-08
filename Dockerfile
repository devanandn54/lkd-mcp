# Dockerfile - LinkedIn MCP Server for Railway
# This fixes the font dependency issues

FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install additional tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Clone and install the MCP server
RUN git clone https://github.com/stickerdaniel/linkedin-mcp-server.git /app/linkedin-mcp-server

WORKDIR /app/linkedin-mcp-server

# Install with uv
RUN uv pip install --system -e .

# Set environment
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# The server should be runnable via the installed package
# Check the actual entry point from the repo
CMD ["uvicorn", "linkedin_mcp_server.server:mcp.app", "--host", "0.0.0.0", "--port", "8080"]