from pathlib import Path

import pytest

from arxiv_ai_mcp.parser import normalize_arxiv_id, parse_atom_feed
from arxiv_ai_mcp.storage import list_saved_digests, save_digest_markdown

FIXTURE = Path(__file__).parent / "fixtures" / "sample_arxiv.xml"


def test_normalize_arxiv_id() -> None:
    assert normalize_arxiv_id("https://arxiv.org/abs/1706.03762v7") == "1706.03762"
    assert normalize_arxiv_id("arXiv:2402.01322") == "2402.01322"
    assert normalize_arxiv_id("2402.01322.pdf") == "2402.01322"


def test_parse_atom_feed_and_bibtex() -> None:
    papers = parse_atom_feed(FIXTURE.read_text(encoding="utf-8"))
    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "1706.03762"
    assert paper.title == "Attention Is All You Need"
    assert paper.primary_category == "cs.CL"
    assert "@article{vaswani2017_1706_03762," in paper.to_bibtex()


def test_save_and_list_vault_notes(tmp_path: Path) -> None:
    saved = save_digest_markdown(
        arxiv_id="1706.03762",
        title="Attention Is All You Need",
        key_takeaways="- Introduced the Transformer architecture.",
        tags=["transformers", "nlp"],
        vault_dir=tmp_path,
    )
    assert saved.exists()
    listing = list_saved_digests(tmp_path)
    assert listing == ["- `1706.03762`: Attention Is All You Need"]


def test_path_traversal_blocked(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        save_digest_markdown(
            arxiv_id="../../etc/passwd",
            title="Malicious",
            key_takeaways="- Bad",
            tags=[],
            vault_dir=tmp_path,
        )
