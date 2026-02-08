FROM stickerdaniel/linkedin-mcp-server:latest
ENV PORT=8080
ENV HOST=0.0.0.0
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1
ENTRYPOINT ["python", "-m", "linkedin_mcp_server"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080", "--path", "/mcp"]