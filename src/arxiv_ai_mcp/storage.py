from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path


def get_vault_dir() -> Path:
    raw = os.environ.get("ARXIV_VAULT_DIR", "").strip()
    base = Path(raw).expanduser() if raw else (Path.home() / "arxiv-vault")
    return base.resolve()


def save_digest_markdown(
    arxiv_id: str,
    title: str,
    key_takeaways: str,
    tags: list[str],
    vault_dir: Path | None = None,
) -> Path:
    root = (vault_dir or get_vault_dir()).resolve()
    root.mkdir(parents=True, exist_ok=True)

    raw_id = arxiv_id.strip()
    if not raw_id or ".." in raw_id or raw_id.startswith(("/", "\\")):
        raise ValueError(f"Invalid or unsafe arxiv_id: {arxiv_id!r}")

    safe_slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw_id)
    target = (root / f"{safe_slug}.md").resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path traversal detected in arxiv_id")

    saved_at = datetime.now(UTC).strftime("%Y-%m-%d")
    sanitized_title = title.replace('"', "'").strip()
    formatted_tags = ", ".join(t.strip() for t in tags if t.strip())

    doc = (
        f"---\n"
        f'arxiv_id: "{arxiv_id.strip()}"\n'
        f'title: "{sanitized_title}"\n'
        f"tags: [{formatted_tags}]\n"
        f"saved_at: {saved_at}\n"
        f"url: https://arxiv.org/abs/{arxiv_id.strip()}\n"
        f"---\n\n"
        f"# {title.strip()}\n\n"
        f"## Key Takeaways\n{key_takeaways.strip()}\n"
    )
    target.write_text(doc, encoding="utf-8")
    return target


def list_saved_digests(vault_dir: Path | None = None) -> list[str]:
    root = (vault_dir or get_vault_dir()).resolve()
    if not root.exists():
        return []
    summaries: list[str] = []
    for path in sorted(root.glob("*.md")):
        first_heading = next(
            (line[2:].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("# ")),
            path.stem,
        )
        summaries.append(f"- `{path.stem}`: {first_heading}")
    return summaries
