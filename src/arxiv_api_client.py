import urllib.parse
import feedparser
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class Link:
    """Represents a link associated with a paper"""
    href: str
    rel: str
    type: Optional[str] = None
    title: Optional[str] = None

@dataclass
class Category:
    """Represents a category/tag for a paper"""
    term: str
    scheme: str

@dataclass
class Paper:
    """Represents an arXiv paper"""
    id: str
    title: str
    summary: str
    published: str
    updated: str
    authors: List[str]
    links: List[Link]
    categories: List[Category]
    comment: Optional[str] = None
    journal_ref: Optional[str] = None
    primary_category: Optional[str] = None
    
    @property
    def pdf_url(self) -> Optional[str]:
        """Get the PDF URL if available"""
        for link in self.links:
            if link.type == 'application/pdf':
                return link.href
        return None
    
    @property
    def abstract_url(self) -> Optional[str]:
        """Get the abstract URL if available"""
        for link in self.links:
            if link.rel == 'alternate' and link.type == 'text/html':
                return link.href
        return None
    
    @property
    def published_date(self) -> Optional[datetime]:
        """Parse published date as datetime object"""
        try:
            return datetime.fromisoformat(self.published.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    @property
    def updated_date(self) -> Optional[datetime]:
        """Parse updated date as datetime object"""
        try:
            return datetime.fromisoformat(self.updated.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, default=str)

def _parse_arxiv_entry(entry) -> Paper:
    """Parse a single arXiv entry from feedparser entry and return as Paper object"""

    # Extract basic information
    paper_id = getattr(entry, 'id', '')
    title = getattr(entry, 'title', '')
    summary = getattr(entry, 'summary', '').strip()
    published = getattr(entry, 'published', '')
    updated = getattr(entry, 'updated', '')

    # Extract authors
    authors = []
    if hasattr(entry, 'authors'):
        for author in entry.authors:
            authors.append(getattr(author, 'name', ''))

    # Extract links
    links = []
    if hasattr(entry, 'links'):
        for link in entry.links:
            link_obj = Link(
                href=getattr(link, 'href', ''),
                rel=getattr(link, 'rel', ''),
                type=getattr(link, 'type', None),
                title=getattr(link, 'title', None)
            )
            links.append(link_obj)

    # Extract categories
    categories = []
    if hasattr(entry, 'tags'):
        for tag in entry.tags:
            cat_obj = Category(
                term=getattr(tag, 'term', ''),
                scheme=getattr(tag, 'scheme', '')
            )
            categories.append(cat_obj)

    # Extract arXiv-specific fields from entry content
    comment = getattr(entry, 'arxiv_comment', None)
    journal_ref = getattr(entry, 'arxiv_journal_ref', None)
    primary_category = getattr(entry, 'arxiv_primary_category', None)

    return Paper(
        id=paper_id,
        title=title,
        summary=summary,
        published=published,
        updated=updated,
        authors=authors,
        links=links,
        categories=categories,
        comment=comment,
        journal_ref=journal_ref,
        primary_category=primary_category
    )

@dataclass
class ArxivResponse:
    """Represents the complete arXiv API response"""
    query: str
    start: int
    max_results: int
    papers: List[Paper]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'start': self.start,
            'max_results': self.max_results,
            'papers': [paper.to_dict() for paper in self.papers]
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, default=str)

def fetch_and_parse_arxiv(query='all:electron', start=0, max_results=1) -> ArxivResponse:
    """Fetch arXiv data and return as ArxivResponse object"""
    base_url = 'http://export.arxiv.org/api/query'
    params = {
        'search_query': query,
        'start': start,
        'max_results': max_results
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        # Parse the feed directly with feedparser
        feed = feedparser.parse(url)

        # Extract papers from feed entries
        papers = []
        for entry in feed.entries:
            paper = _parse_arxiv_entry(entry)
            papers.append(paper)

        return ArxivResponse(
            query=query,
            start=start,
            max_results=max_results,
            papers=papers
        )

    except Exception as e:
        # Return empty response with error info
        error_paper = Paper(
            id="",
            title=f"Error: {str(e)}",
            summary="",
            published="",
            updated="",
            authors=[],
            links=[],
            categories=[]
        )
        return ArxivResponse(
            query=query,
            start=start,
            max_results=max_results,
            total_results=0,
            papers=[error_paper]
        )

# Example usage
if __name__ == '__main__':
    response = fetch_and_parse_arxiv()
    
    # Access individual papers
    if response.papers:
        paper = response.papers[0]
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors)}")
        print(f"PDF URL: {paper.pdf_url}")
        print(f"Abstract URL: {paper.abstract_url}")
        print(f"Published: {paper.published_date}")
    
    # Convert to JSON
    print("\nJSON Response:")
    print(response.to_json())