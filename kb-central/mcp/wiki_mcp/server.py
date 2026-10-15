"""MCP surface of the wiki: resources for stable reads, tools for navigation,
and one write path (propose_edit) that only queues changes for review."""
from __future__ import annotations

import os

try:  # mcp >= 2: FastMCP was renamed MCPServer
    from mcp.server.mcpserver import Context, MCPServer as FastMCP
    MCP_V2 = True
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import Context, FastMCP
    MCP_V2 = False

from .core import WikiError, WikiStore

IDENTITY_HEADERS = ("x-forwarded-user", "x-forwarded-email", "x-auth-request-email")


def _caller(ctx: Context | None) -> str | None:
    """Identity comes from the SSO proxy header over HTTP, or WIKI_CALLER over stdio."""
    try:
        request = ctx.request_context.request if ctx else None
        if request is not None:
            for header in IDENTITY_HEADERS:
                value = request.headers.get(header)
                if value:
                    return value
    except (AttributeError, LookupError, ValueError):
        pass
    return os.environ.get("WIKI_CALLER")


def build_server(store: WikiStore, read_only: bool, name: str = "llm-wiki") -> FastMCP:
    mcp = FastMCP(name, instructions=(
        "Compiled knowledge base. Read the wiki://index resource first, then open at most "
        "8 pages with wiki://page/{slug}. Use search to find slugs and neighbors to follow "
        "links. Cite pages as [[slug]]. Never invent page content."
        + ("" if read_only else " To correct or add knowledge, call propose_edit; it is reviewed by a curator.")
    ))

    @mcp.resource("wiki://index", mime_type="text/markdown")
    def index() -> str:
        """The catalog: one line per page with a summary. Read this before anything else."""
        return store.index(_caller(None))

    @mcp.resource("wiki://page/{slug}", mime_type="text/markdown")
    def page(slug: str) -> str:
        """Full markdown of one page, frontmatter included."""
        return store.page(slug, _caller(None))

    @mcp.tool()
    def read_index(ctx: Context) -> str:
        """Return index.md (same as the wiki://index resource, for clients without resource support)."""
        return store.index(_caller(ctx))

    @mcp.tool()
    def read_page(slug: str, ctx: Context) -> str:
        """Return one page by slug (same as wiki://page/{slug})."""
        try:
            return store.page(slug, _caller(ctx))
        except WikiError as exc:
            return f"error: {exc}"

    @mcp.tool()
    def search(query: str, ctx: Context, limit: int = 10) -> list[dict]:
        """BM25 over titles, aliases, summaries and headings. Returns slug, score and one-line summary."""
        return store.search(query, limit, _caller(ctx))

    @mcp.tool()
    def neighbors(slug: str, ctx: Context, depth: int = 1) -> dict:
        """Inbound and outbound [[links]] around a page, with one-line summaries (depth 1 to 3)."""
        try:
            return store.neighbors(slug, depth, _caller(ctx))
        except WikiError as exc:
            return {"error": str(exc)}

    @mcp.tool()
    def history(slug: str, ctx: Context, limit: int = 5) -> list[dict]:
        """Recent commits touching the page: commit, date, author, summary (ingest commits name the source)."""
        try:
            return store.history(slug, limit, _caller(ctx))
        except WikiError as exc:
            return [{"error": str(exc)}]

    if not read_only:
        @mcp.tool()
        def propose_edit(slug: str, patch: str, source_ref: str, rationale: str, ctx: Context) -> dict:
            """Queue a unified diff (or full new page) for the curator. Never writes to the wiki directly.
            source_ref must point to evidence: a raw file path, PR, commit SHA or message permalink."""
            try:
                return store.propose_edit(slug, patch, source_ref, rationale, _caller(ctx))
            except WikiError as exc:
                return {"error": str(exc)}

    return mcp


def run_server(mcp: FastMCP, transport: str, host: str, port: int) -> None:
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif MCP_V2:
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.run(transport="streamable-http")
