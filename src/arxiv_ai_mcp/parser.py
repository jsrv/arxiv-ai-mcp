from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def clean_whitespace(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def normalize_arxiv_id(raw_id: str) -> str:
    """Normalize URLs, prefixes, and version suffixes into a canonical arXiv ID."""
    cleaned = raw_id.strip().rstrip("/")
    cleaned = re.sub(r"^(arxiv:|https?://arxiv\.org/(abs|pdf)/)", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\.pdf$", "", cleaned, flags=re.I)
    return re.sub(r"v\d+$", "", cleaned)


@dataclass(frozen=True, slots=True)
class ArxivPaper:
    arxiv_id: str
    title: str
    authors: tuple[str, ...]
    abstract: str
    published: str
    updated: str
    primary_category: str
    categories: tuple[str, ...]
    abs_url: str
    pdf_url: str

    def to_bibtex(self) -> str:
        year = self.published[:4] or "2026"
        first_last = re.sub(r"[^a-zA-Z]", "", self.authors[0].split()[-1]).lower() if self.authors else "author"
        cite_key = f"{first_last}{year}_{self.arxiv_id.replace('.', '_')}"
        author_field = " and ".join(self.authors)
        return (
            f"@article{{{cite_key},\n"
            f"  title={{{self.title}}},\n"
            f"  author={{{author_field}}},\n"
            f"  journal={{arXiv preprint arXiv:{self.arxiv_id}}},\n"
            f"  year={{{year}}},\n"
            f"  url={{{self.abs_url}}}\n"
            f"}}"
        )

    def to_compact_markdown(self, snippet_chars: int = 300) -> str:
        author_list = ", ".join(self.authors[:3]) + (" et al." if len(self.authors) > 3 else "")
        snippet = self.abstract[:snippet_chars] + ("..." if len(self.abstract) > snippet_chars else "")
        cats = ", ".join(self.categories[:4])
        return (
            f"### [{self.arxiv_id}] {self.title}\n"
            f"- **Published:** {self.published} | **Categories:** {cats}\n"
            f"- **Authors:** {author_list}\n"
            f"- **Summary:** {snippet}"
        )

    def to_full_markdown(self) -> str:
        return (
            f"# {self.title}\n"
            f"- **arXiv ID:** `{self.arxiv_id}`\n"
            f"- **Published:** {self.published} (Updated: {self.updated})\n"
            f"- **Primary Category:** `{self.primary_category}`\n"
            f"- **All Categories:** {', '.join(self.categories)}\n"
            f"- **Abstract URL:** {self.abs_url}\n"
            f"- **PDF URL:** {self.pdf_url}\n"
            f"- **Authors:** {', '.join(self.authors)}\n\n"
            f"## Abstract\n{self.abstract}\n\n"
            f"## BibTeX\n```bibtex\n{self.to_bibtex()}\n```"
        )


def parse_atom_feed(xml_text: str) -> list[ArxivPaper]:
    """Parse an arXiv Atom XML response into structured ArxivPaper objects."""
    root = ET.fromstring(xml_text)
    papers: list[ArxivPaper] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        raw_id = entry.findtext("atom:id", "", ATOM_NS)
        title = clean_whitespace(entry.findtext("atom:title", "", ATOM_NS))
        if not raw_id or not title:
            continue

        arxiv_id = normalize_arxiv_id(raw_id)
        authors = tuple(
            clean_whitespace(a.findtext("atom:name", "", ATOM_NS))
            for a in entry.findall("atom:author", ATOM_NS)
            if clean_whitespace(a.findtext("atom:name", "", ATOM_NS))
        )
        categories = tuple(c.attrib["term"] for c in entry.findall("atom:category", ATOM_NS) if c.attrib.get("term"))
        primary_el = entry.find("arxiv:primary_category", ATOM_NS)
        primary_cat = (
            primary_el.attrib.get("term", "") if primary_el is not None else (categories[0] if categories else "")
        )

        papers.append(
            ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=clean_whitespace(entry.findtext("atom:summary", "", ATOM_NS)),
                published=entry.findtext("atom:published", "", ATOM_NS)[:10],
                updated=entry.findtext("atom:updated", "", ATOM_NS)[:10],
                primary_category=primary_cat,
                categories=categories,
                abs_url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            )
        )

    return papers
