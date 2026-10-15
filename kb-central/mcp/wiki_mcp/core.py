"""Read model of an LLM Wiki: pages, link graph, BM25 search, git history, review queue.

No MCP dependency here, so the logic is testable on its own and reusable
from scripts. server.py wraps it as MCP resources and tools.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
TOKEN_RE = re.compile(r"[a-z0-9À-ɏ]+")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PAGE_DIRS = ("entities", "concepts", "syntheses", "playbooks", "sources")


class WikiError(Exception):
    """Raised for requests the server must refuse (unknown page, no access)."""


@dataclass
class Page:
    slug: str
    path: Path
    category: str
    title: str
    summary: str
    aliases: list[str]
    headings: list[str]
    links: list[str]
    meta: dict = field(default_factory=dict)


def _frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    meta: dict = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        meta[k.strip()] = v
    return meta, text[end + 4:]


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class WikiStore:
    def __init__(self, root: Path, queue_dir: Path | None = None, acl_file: Path | None = None):
        self.root = Path(root).resolve()
        if (self.root / ".wiki").is_dir():
            self.wiki = self.root / ".wiki"
        elif (self.root / "wiki").is_dir():
            self.wiki = self.root / "wiki"
        else:
            raise WikiError(f"no wiki/ or .wiki/ under {self.root}")
        self.queue_dir = Path(queue_dir) if queue_dir else self.root / "review-queue"
        self.acl = json.loads(Path(acl_file).read_text(encoding="utf-8")) if acl_file else None
        self._pages: dict[str, Page] = {}
        self._mtime = -1.0
        self.reload()

    # ---------------------------------------------------------------- loading
    def _wiki_mtime(self) -> float:
        files = [self.wiki / "index.md"] + [p for d in PAGE_DIRS for p in (self.wiki / d).rglob("*.md")]
        return max((p.stat().st_mtime for p in files if p.exists()), default=0.0)

    def reload(self, force: bool = False) -> None:
        mtime = self._wiki_mtime()
        if not force and mtime == self._mtime:
            return
        pages: dict[str, Page] = {}
        for d in PAGE_DIRS:
            base = self.wiki / d
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.md")):
                meta, body = _frontmatter(path.read_text(encoding="utf-8"))
                lines = [l.strip() for l in body.splitlines()]
                title = next((l.lstrip("#").strip() for l in lines if l.startswith("# ")), path.stem)
                summary = next((l for l in lines if l and not l.startswith(("#", "|", "-", "```"))), "")
                summary = re.sub(r"\s*\[src:[^\]]+\]", "", summary)
                aliases = meta.get("aliases", [])
                pages[path.stem] = Page(
                    slug=path.stem, path=path, category=d, title=title,
                    summary=summary[:200], aliases=aliases if isinstance(aliases, list) else [aliases],
                    headings=[l.lstrip("#").strip() for l in lines if l.startswith("##")],
                    links=sorted({m.group(1).strip() for m in LINK_RE.finditer(body)}),
                    meta=meta,
                )
        self._pages = pages
        self._mtime = mtime
        self._build_bm25()

    # ------------------------------------------------------------ access control
    def allowed(self, slug: str, caller: str | None) -> bool:
        """ACL file format: {"default": ["entities", ...], "users": {"alice@corp": ["*"]}}."""
        if self.acl is None:
            return True
        page = self._pages.get(slug)
        if page is None:
            return False
        dirs = self.acl.get("users", {}).get(caller or "", self.acl.get("default", []))
        rel_dir = str(page.path.parent.relative_to(self.wiki))
        return "*" in dirs or any(rel_dir == d or rel_dir.startswith(d + "/") for d in dirs)

    # ---------------------------------------------------------------- reads
    def index(self, caller: str | None = None) -> str:
        self.reload()
        text = (self.wiki / "index.md").read_text(encoding="utf-8")
        if self.acl is None:
            return text
        kept = []
        for line in text.splitlines():
            targets = [m.group(1).strip() for m in LINK_RE.finditer(line)]
            if targets and not any(self.allowed(t, caller) for t in targets):
                continue
            kept.append(line)
        return "\n".join(kept) + "\n"

    def page(self, slug: str, caller: str | None = None) -> str:
        self.reload()
        if not SLUG_RE.match(slug) or slug not in self._pages:
            raise WikiError(f"no page named '{slug}'")
        if not self.allowed(slug, caller):
            raise WikiError(f"no access to '{slug}'")
        return self._pages[slug].path.read_text(encoding="utf-8")

    def neighbors(self, slug: str, depth: int = 1, caller: str | None = None) -> dict:
        self.reload()
        if slug not in self._pages or not self.allowed(slug, caller):
            raise WikiError(f"no page named '{slug}'")
        depth = max(1, min(depth, 3))
        inbound: dict[str, set[str]] = {s: set() for s in self._pages}
        for p in self._pages.values():
            for l in p.links:
                if l in inbound and l != p.slug:
                    inbound[l].add(p.slug)
        seen, frontier, nodes = {slug}, deque([(slug, 0)]), []
        while frontier:
            current, d = frontier.popleft()
            if d == depth:
                continue
            for nxt in set(self._pages[current].links) | inbound[current]:
                if nxt in self._pages and nxt not in seen and self.allowed(nxt, caller):
                    seen.add(nxt)
                    frontier.append((nxt, d + 1))
                    nodes.append({"slug": nxt, "distance": d + 1, "summary": self._pages[nxt].summary,
                                  "category": self._pages[nxt].category})
        page = self._pages[slug]
        return {
            "slug": slug,
            "outbound": [l for l in page.links if l in self._pages and self.allowed(l, caller)],
            "inbound": sorted(s for s in inbound[slug] if self.allowed(s, caller)),
            "missing": [l for l in page.links if l not in self._pages],
            "neighborhood": nodes,
        }

    def history(self, slug: str, limit: int = 5, caller: str | None = None) -> list[dict]:
        self.reload()
        if slug not in self._pages or not self.allowed(slug, caller):
            raise WikiError(f"no page named '{slug}'")
        fmt = "%H%x1f%ad%x1f%an%x1f%s"
        proc = subprocess.run(
            ["git", "log", f"-{max(1, min(limit, 50))}", "--follow", "--date=short", f"--format={fmt}",
             "--", str(self._pages[slug].path)],
            cwd=self.wiki, capture_output=True, text=True,
        )
        out = []
        for line in proc.stdout.splitlines():
            sha, date, author, subject = line.split("\x1f", 3)
            out.append({"commit": sha[:12], "date": date, "author": author, "summary": subject})
        return out

    # ---------------------------------------------------------------- search
    def _build_bm25(self) -> None:
        self._docs: dict[str, list[str]] = {}
        for p in self._pages.values():
            text = " ".join([p.slug.replace("-", " "), p.title, p.title, " ".join(p.aliases) * 2,
                             p.summary, " ".join(p.headings)])
            self._docs[p.slug] = _tokens(text)
        n = len(self._docs) or 1
        self._avgdl = sum(len(t) for t in self._docs.values()) / n
        df = Counter(tok for toks in self._docs.values() for tok in set(toks))
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, limit: int = 10, caller: str | None = None,
               k1: float = 1.5, b: float = 0.75) -> list[dict]:
        self.reload()
        q = _tokens(query)
        scored = []
        for slug, toks in self._docs.items():
            if not self.allowed(slug, caller):
                continue
            tf = Counter(toks)
            score = 0.0
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                score += self._idf.get(t, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * len(toks) / (self._avgdl or 1)))
            if score > 0:
                scored.append((score, slug))
        scored.sort(reverse=True)
        return [{"slug": s, "score": round(sc, 3), "category": self._pages[s].category,
                 "summary": self._pages[s].summary} for sc, s in scored[:max(1, min(limit, 50))]]

    # ---------------------------------------------------------------- writes
    def propose_edit(self, slug: str, patch: str, source_ref: str, rationale: str,
                     caller: str | None = None) -> dict:
        """Queue a proposed change for the curator. Never touches the wiki."""
        if not SLUG_RE.match(slug):
            raise WikiError("slug must be kebab-case")
        if not patch.strip() or not source_ref.strip():
            raise WikiError("patch and source_ref are required")
        if len(patch) > 50_000:
            raise WikiError("patch too large (50 kB max)")
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        proposal_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
        record = {
            "id": proposal_id, "slug": slug, "page_exists": slug in self._pages,
            "patch": patch, "source_ref": source_ref, "rationale": rationale,
            "caller": caller or "unknown",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "pending",
        }
        (self.queue_dir / f"{proposal_id}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False),
                                                          encoding="utf-8")
        return {"id": proposal_id, "status": "queued for curator review"}
