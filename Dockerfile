FROM stickerdaniel/linkedin-mcp-server:latest

# That's it! The image is already built and ready
# Just needs the cookie via environment variable

ENV PORT=8080
EXPOSE 8080

# The image already has the CMD set up correctly
# We just need to override the transport mode for Railway
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080", "--path",