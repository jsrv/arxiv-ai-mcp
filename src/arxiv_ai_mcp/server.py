from __future__ import annotations

import logging
import sys

from mcp.server.mcpserver import MCPServer

from arxiv_ai_mcp.client import ArxivClient
from arxiv_ai_mcp.storage import get_vault_dir, list_saved_digests, save_digest_markdown

# stdio transport reserves stdout strictly for JSON-RPC frames
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("arxiv-ai-mcp")

mcp = MCPServer("arxiv-ai")
client = ArxivClient()


@mcp.resource("arxiv://categories")
def get_ai_categories() -> str:
    """Reference taxonomy of primary arXiv categories for AI and ML research."""
    return (
        "Primary AI/ML arXiv Categories:\n"
        "- cs.AI: Artificial Intelligence (agents, planning, reasoning)\n"
        "- cs.LG: Machine Learning (training, optimization, architectures)\n"
        "- cs.CL: Computation and Language (LLMs, RAG, alignment, evals)\n"
        "- cs.CV: Computer Vision and Pattern Recognition\n"
        "- cs.MA: Multiagent Systems\n"
        "- stat.ML: Statistical Machine Learning Theory\n"
    )


@mcp.prompt()
def literature_review(topic: str, category: str = "cs.AI") -> str:
    """Structured workflow to survey recent arXiv papers on a topic and archive top findings."""
    return (
        f"Conduct a focused arXiv literature survey on '{topic}' (primary category: {category}).\n"
        "1. Call `list_saved_papers` first so we do not duplicate papers already in the vault.\n"
        "2. Search recent papers with `search_arxiv` using `sort_by='submittedDate'` "
        "and relevant papers with `sort_by='relevance'`.\n"
        "3. Call `get_paper` on the top 2-3 most impactful papers to inspect full abstracts.\n"
        "4. Synthesize key methodological trends, trade-offs, and open problems, "
        "then call `save_paper_note` for the strongest paper."
    )


@mcp.tool()
async def search_arxiv(
    query: str,
    category: str = "",
    sort_by: str = "relevance",
    max_results: int = 5,
) -> str:
    """Search arXiv for AI/ML papers and return token-efficient Markdown summaries.

    Args:
        query: Search keywords or phrase (e.g., 'KV cache quantization' or 'agentic benchmarks').
        category: Optional arXiv category filter ('cs.AI', 'cs.LG', 'cs.CL', 'cs.MA', 'cs.CV').
        sort_by: 'relevance' (default) or 'submittedDate' (for newest preprints).
        max_results: Number of results to return (1 to 15, default 5).
    """
    papers = await client.search(
        query=query,
        category=category,
        sort_by=sort_by,
        max_results=max_results,
    )
    if not papers:
        return f"No papers matched query='{query}' (category='{category or 'any'}')."

    header = f"Found {len(papers)} paper(s) for '{query}':\n\n"
    return header + "\n\n".join(p.to_compact_markdown() for p in papers)


@mcp.tool()
async def get_paper(arxiv_id: str) -> str:
    """Fetch complete metadata, full abstract, PDF link, and BibTeX for an arXiv ID.

    Args:
        arxiv_id: Canonical arXiv ID or URL (e.g., '2402.01322' or 'https://arxiv.org/abs/1706.03762').
    """
    paper = await client.fetch_by_id(arxiv_id)
    if paper is None:
        return f"No arXiv paper found for ID '{arxiv_id}'."
    return paper.to_full_markdown()


@mcp.tool()
async def find_related_papers(arxiv_id: str, max_results: int = 5) -> str:
    """Find related arXiv papers sharing the same primary category and core title concepts.

    Args:
        arxiv_id: Seed paper arXiv ID (e.g., '1706.03762').
        max_results: Number of related papers to return (1 to 10, default 5).
    """
    seed = await client.fetch_by_id(arxiv_id)
    if seed is None:
        return f"Seed paper '{arxiv_id}' not found."

    keywords = [w for w in seed.title.split() if len(w) > 4][:5]
    query = " ".join(keywords) if keywords else seed.title
    candidates = await client.search(
        query=query,
        category=seed.primary_category,
        sort_by="relevance",
        max_results=min(max_results + 1, 15),
    )
    related = [p for p in candidates if p.arxiv_id != seed.arxiv_id][:max_results]
    if not related:
        return f"No related papers found for [{seed.arxiv_id}] {seed.title}."

    return f"Papers related to **[{seed.arxiv_id}] {seed.title}** (`{seed.primary_category}`):\n\n" + "\n\n".join(
        p.to_compact_markdown() for p in related
    )


@mcp.tool()
def save_paper_note(arxiv_id: str, title: str, key_takeaways: str, tags: list[str]) -> str:
    """Save a structured Markdown research note with YAML frontmatter to the local vault.

    Args:
        arxiv_id: Canonical arXiv ID (e.g., '2402.01322').
        title: Paper title.
        key_takeaways: Bulleted summary of methodology, benchmarks, and practical significance.
        tags: Topic tags for indexing (e.g., ["quantization", "inference", "llm"]).
    """
    saved_path = save_digest_markdown(
        arxiv_id=arxiv_id,
        title=title,
        key_takeaways=key_takeaways,
        tags=tags,
    )
    return f"Saved research note to {saved_path}"


@mcp.tool()
def list_saved_papers() -> str:
    """List all arXiv papers currently saved in the configured local research vault."""
    vault = get_vault_dir()
    items = list_saved_digests(vault)
    if not items:
        return f"Vault at {vault} is currently empty."
    return f"Saved papers in `{vault}` ({len(items)} total):\n" + "\n".join(items)


def main() -> None:
    logger.info("Starting arxiv-ai-mcp server (vault=%s)", get_vault_dir())
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
