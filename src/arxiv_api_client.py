import arxiv
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
    entry_id: str
    title: str
    summary: str
    published: datetime
    updated: datetime
    authors: List[str]
    pdf_url: Optional[str] = None
    links: List[Link] = None
    categories: List[str] = None
    comment: Optional[str] = None
    journal_ref: Optional[str] = None
    primary_category: Optional[str] = None

    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.categories is None:
            self.categories = []
    
    @property
    def abstract_url(self) -> Optional[str]:
        """Get the abstract URL if available"""
        return f"https://arxiv.org/abs/{self.entry_id.split('/')[-1]}" if self.entry_id else None

    @property
    def published_date(self) -> Optional[datetime]:
        """Get published date as datetime object"""
        return self.published

    @property
    def updated_date(self) -> Optional[datetime]:
        """Get updated date as datetime object"""
        return self.updated
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, default=str)

def _parse_arxiv_result(result) -> Paper:
    """Parse a single arXiv result from arxiv.py Result object and return as Paper object"""

    # Extract authors as strings
    authors = [str(author) for author in result.authors]

    # Extract links from arxiv.Result
    links = []
    if hasattr(result, 'links'):
        for link in result.links:
            link_obj = Link(
                href=link.href,
                rel=getattr(link, 'rel', ''),
                type=getattr(link, 'content_type', None),
                title=getattr(link, 'title', None)
            )
            links.append(link_obj)

    return Paper(
        entry_id=result.entry_id,
        title=result.title,
        summary=result.summary,
        published=result.published,
        updated=result.updated,
        authors=authors,
        pdf_url=result.pdf_url,
        links=links,
        categories=result.categories,
        comment=result.comment,
        journal_ref=result.journal_ref,
        primary_category=result.primary_category
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

    try:
        # Use arxiv.py to search
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        # Extract papers from search results
        papers = []
        for result in client.results(search):
            paper = _parse_arxiv_result(result)
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
            entry_id="",
            title=f"Error: {str(e)}",
            summary="",
            published=datetime.now(),
            updated=datetime.now(),
            authors=[]
        )
        return ArxivResponse(
            query=query,
            start=start,
            max_results=max_results,
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