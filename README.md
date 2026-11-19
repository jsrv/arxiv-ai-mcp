# arxiv-ai-mcp

A lightweight, token-efficient **Model Context Protocol (MCP)** server for searching, inspecting, and curating AI/ML research papers from arXiv.

Designed for both frontier cloud models and local quantized models (e.g., Qwen 3.5 via Ollama), `arxiv-ai-mcp` parses arXiv's Atom XML feeds into compact, structured Markdown—avoiding raw XML bloat in your agent's context window—while respecting arXiv's 3-second API rate-limiting etiquette.

## Architecture

```text
MCP Host / Agent Harness (Claude Desktop, OpenCode, Cursor, Pi)
       │  JSON-RPC 2.0 (stdio)
       ▼
┌─────────────────────────────────────────┐
│  arxiv-ai-mcp                           │
│  ├── Tools: search, get, related, vault │
│  ├── Resource: arxiv://categories       │
│  └── Prompt: literature_review          │
└──────┬──────────────────────────┬───────┘
       │ HTTPS (3s paced)         │ Local FS
       ▼                          ▼
  export.arxiv.org          ~/arxiv-vault/*.md
```

## Quickstart (Zero-Install via `uvx`)

Add this block to your MCP host configuration to run directly from GitHub:

```json
{
  "mcpServers": {
    "arxiv-ai": {
      "command": "uvx",
      "args": [
        "--from",
        "git+[https://github.com/jsrv/arxiv-ai-mcp](https://github.com/jsrv/arxiv-ai-mcp)",
        "arxiv-ai-mcp"
      ],
      "env": {
        "ARXIV_VAULT_DIR": "/path/to/your/arxiv-vault"
      }
    }
  }
}
```

## Capabilities

| Primitive | Name | Description |
| :--- | :--- | :--- |
| **Tool** | `search_arxiv` | Query arXiv by keywords, category (`cs.AI`, `cs.LG`, `cs.CL`, `cs.MA`, `cs.CV`), and sort order with bounded abstract snippets. |
| **Tool** | `get_paper` | Retrieve full metadata, complete abstract, PDF URL, and ready-to-paste BibTeX for any arXiv ID or URL. |
| **Tool** | `find_related_papers` | Discover adjacent preprints sharing a seed paper's primary category and core title concepts. |
| **Tool** | `save_paper_note` | Archive a structured YAML-frontmatter Markdown digest into `ARXIV_VAULT_DIR`. |
| **Tool** | `list_saved_papers` | Check papers already saved in your local research vault to prevent duplicate synthesis. |
| **Resource** | `arxiv://categories` | Quick reference taxonomy of primary AI/ML arXiv subject classifications. |
| **Prompt** | `literature_review` | End-to-end guided workflow to survey recent papers on a topic and archive top picks. |

## Local Development

```bash
git clone [https://github.com/jsrv/arxiv-ai-mcp.git](https://github.com/jsrv/arxiv-ai-mcp.git)
cd arxiv-ai-mcp
uv sync
uv run ruff check src tests
uv run pytest -v
uv run mcp dev src/arxiv_ai_mcp/server.py
```
