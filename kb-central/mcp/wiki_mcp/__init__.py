"""MCP server exposing a compiled LLM Wiki to Copilot, CI jobs, bots and other MCP clients."""
from .core import WikiError, WikiStore

__all__ = ["WikiError", "WikiStore"]
__version__ = "0.1.0"
