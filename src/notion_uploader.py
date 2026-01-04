import os
from notion_client import Client
from datetime import datetime

class NotionUploader:
    """Class to handle uploading content to Notion."""

    def __init__(self):
        """Initialize Notion client with API key from environment variables."""
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise ValueError("NOTION_API_KEY environment variable not set")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable not set")

        self.client = Client(auth=self.api_key)

    def _split_text_into_chunks(self, text: str, max_length: int = 2000) -> list[str]:
        """
        Split text into chunks that fit within Notion's character limits.

        Args:
            text: The text to split
            max_length: Maximum characters per chunk (default 2000 for Notion)

        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        words = text.split(' ')
        current_chunk = ""

        for word in words:
            # Check if adding this word would exceed the limit
            potential_chunk = current_chunk + " " + word if current_chunk else word

            if len(potential_chunk) <= max_length:
                current_chunk = potential_chunk
            else:
                # Save current chunk and start a new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word

        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def upload_research_summary(self, user_query: str, generated_text: str, title: str = None):
        """
        Upload a research summary to Notion.

        Args:
            user_query: The original user query
            generated_text: The generated research summary
            title: Optional custom title for the page

        Returns:
            str: URL of the created Notion page
        """
        try:
            # Create a default title if none provided
            if not title:
                # Use first 50 characters of user query as title
                title = f"Research: {user_query[:50]}{'...' if len(user_query) > 50 else ''}"

            # Split the generated text into chunks that fit Notion's limits
            text_chunks = self._split_text_into_chunks(generated_text)

            # Create paragraph blocks for each chunk
            children_blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": "Research Summary"
                                }
                            }
                        ]
                    }
                }
            ]

            # Add each text chunk as a separate paragraph block
            for chunk in text_chunks:
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": chunk
                                }
                            }
                        ]
                    }
                })

            # Create the page content
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    },
                    "Query": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user_query[:2000]  # Limit query length too
                                }
                            }
                        ]
                    },
                    "Created": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    }
                },
                "children": children_blocks
            }

            # Create the page
            response = self.client.pages.create(**page_data)

            # Return the URL of the created page
            return response["url"]

        except Exception as e:
            print(f"Error uploading to Notion: {str(e)}")
            raise

# Global instance for backward compatibility
_uploader = None

def upload_research_summary(user_query: str, generated_text: str, title: str = None):
    """
    Module-level function to upload research summary to Notion.

    Args:
        user_query: The original user query
        generated_text: The generated research summary
        title: Optional custom title for the page

    Returns:
        str: URL of the created Notion page
    """
    global _uploader
    if _uploader is None:
        _uploader = NotionUploader()
    return _uploader.upload_research_summary(user_query, generated_text, title)
