import asyncio
import json

import pytest

from conftest import ROOT
from wiki_mcp.core import WikiError, WikiStore


@pytest.fixture
def store(kb):
    return WikiStore(kb)


def test_search_ranks_the_relevant_page_first(store):
    results = store.search("gateway timeout")
    slugs = [r["slug"] for r in results]
    assert slugs[0] in {"request-timeouts", "payment-gateway"}
    assert {"request-timeouts", "payment-gateway"} <= set(slugs[:3])


def test_search_matches_aliases(store):
    assert store.search("payments-gw")[0]["slug"] == "payment-gateway"


def test_neighbors_reports_both_directions(store):
    n = store.neighbors("idempotency-keys")
    assert "request-timeouts" in n["outbound"]
    assert "payment-gateway" in n["inbound"]


def test_page_rejects_unknown_and_traversal(store):
    assert "# Payment gateway" in store.page("payment-gateway")
    for bad in ("../raw/manifest", "nope", "Payment-Gateway"):
        with pytest.raises(WikiError):
            store.page(bad)


def test_history_lists_commits(store):
    assert store.history("payment-gateway")[0]["summary"] == "init"


def test_acl_filters_pages_and_index(kb, tmp_path):
    acl = tmp_path / "acl.json"
    acl.write_text(json.dumps({"default": ["concepts"], "users": {"lead@corp": ["*"]}}))
    s = WikiStore(kb, acl_file=acl)
    assert "[[payment-gateway]]" not in s.index("someone@corp")
    assert "[[request-timeouts]]" in s.index("someone@corp")
    assert "[[payment-gateway]]" in s.index("lead@corp")
    with pytest.raises(WikiError):
        s.page("payment-gateway", "someone@corp")
    assert all(r["category"] == "concepts" for r in s.search("gateway", caller="someone@corp"))


def test_propose_edit_queues_without_touching_the_wiki(store, kb):
    before = (kb / "wiki" / "entities" / "payment-gateway.md").read_text()
    out = store.propose_edit("payment-gateway", "- Rate limit is 900 rps.", "pr:4521", "load test", "bot@corp")
    queued = json.loads((kb / "review-queue" / f"{out['id']}.json").read_text())
    assert queued["status"] == "pending" and queued["caller"] == "bot@corp"
    assert (kb / "wiki" / "entities" / "payment-gateway.md").read_text() == before
    with pytest.raises(WikiError):
        store.propose_edit("../escape", "x", "y", "z")


def test_reload_picks_up_new_pages(store, kb):
    (kb / "wiki" / "concepts" / "circuit-breaker.md").write_text(
        "---\ntype: concept\nupdated: 2026-10-15\n---\n# Circuit breaker\n\nStops calls to a failing acquirer.\n")
    assert store.search("circuit breaker")[0]["slug"] == "circuit-breaker"


def test_mcp_server_exposes_expected_tools(kb):
    pytest.importorskip("mcp")
    from wiki_mcp.server import build_server

    async def names(read_only):
        server = build_server(WikiStore(kb), read_only=read_only)
        templates = await server.list_resource_templates()
        uris = {str(getattr(r, "uri_template", None) or getattr(r, "uriTemplate")) for r in templates}
        return {t.name for t in await server.list_tools()}, uris

    tools, templates = asyncio.run(names(read_only=False))
    assert {"read_index", "read_page", "search", "neighbors", "history", "propose_edit"} <= tools
    assert "wiki://page/{slug}" in templates
    tools_ro, _ = asyncio.run(names(read_only=True))
    assert "propose_edit" not in tools_ro


def test_mcp_tool_call_roundtrip(kb):
    pytest.importorskip("mcp")
    from wiki_mcp.server import build_server

    async def call():
        server = build_server(WikiStore(kb), read_only=True)
        return await server.call_tool("search", {"query": "idempotency"})

    result = asyncio.run(call())
    assert "idempotency-keys" in str(result)
