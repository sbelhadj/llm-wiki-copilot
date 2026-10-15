import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "kb-central" / "mcp"))


@pytest.fixture
def kb(tmp_path) -> Path:
    """A throwaway copy of the sample kb-central, committed to a fresh git repo."""
    dst = tmp_path / "kb"
    shutil.copytree(ROOT / "kb-central", dst, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    run = lambda *a: subprocess.run(a, cwd=dst, check=True, capture_output=True)  # noqa: E731
    run("git", "init", "-q", "-b", "main")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "test")
    run("git", "add", "-A")
    run("git", "commit", "-q", "-m", "init")
    return dst


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout
