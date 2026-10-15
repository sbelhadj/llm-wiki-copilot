"""Guards for the starter repo itself: shared tools stay in sync, config files stay valid."""
import json
import re

import pytest

from conftest import ROOT

SHARED = ["wiki_check.py", "wiki_manifest.py"]


@pytest.mark.parametrize("name", SHARED)
@pytest.mark.parametrize("copy", ["kb-central/tools", "repo-template/tools"])
def test_tool_copies_match_canonical(copy, name):
    assert (ROOT / copy / name).read_bytes() == (ROOT / "tools" / name).read_bytes(), \
        f"{copy}/{name} drifted from tools/{name}; run: make sync"


@pytest.mark.parametrize("path", sorted(ROOT.glob("*/.vscode/mcp.json")))
def test_mcp_json_is_valid(path):
    servers = json.loads(path.read_text())["servers"]
    assert "llm-wiki" in servers


@pytest.mark.parametrize("path", sorted(ROOT.glob("*/.github/agents/*.agent.md")) + sorted(ROOT.glob("*/.github/prompts/*.prompt.md")))
def test_copilot_files_have_frontmatter(path):
    text = path.read_text()
    assert text.startswith("---\n") and "\n---\n" in text[4:]
    fm = text[4:text.index("\n---\n", 4)]
    assert re.search(r"^description:", fm, re.M)
    if path.name.endswith(".prompt.md"):
        assert re.search(r"^agent: wiki-(curator|reader)$", fm, re.M)


def test_prompts_reference_existing_agents():
    for repo in ("kb-central", "repo-template"):
        agents = {p.name.removesuffix(".agent.md") for p in (ROOT / repo / ".github/agents").glob("*.agent.md")}
        for prompt in (ROOT / repo / ".github/prompts").glob("*.prompt.md"):
            agent = re.search(r"^agent: (\S+)$", prompt.read_text(), re.M).group(1)
            assert agent in agents, f"{prompt} uses unknown agent {agent}"
