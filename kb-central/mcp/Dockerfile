# Central wiki MCP server. Mount or clone kb-central at /kb and keep it in sync (git pull on a timer).
#   docker build -t wiki-mcp ./mcp
#   docker run -p 8765:8765 -v /srv/kb-central:/kb:ro wiki-mcp
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'
WORKDIR /app
COPY pyproject.toml README.md ./
COPY wiki_mcp ./wiki_mcp
RUN pip install --no-cache-dir .
RUN useradd --system wiki
USER wiki
EXPOSE 8765
# --queue must point to a writable volume if propose_edit is enabled.
CMD ["python", "-m", "wiki_mcp", "--root", "/kb", "--transport", "http", "--host", "0.0.0.0", "--port", "8765", "--queue", "/queue"]
