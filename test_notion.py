#!/usr/bin/env python3
"""
Test script for Notion integration.
Run this to verify that your Notion setup is working.
"""

import os
from dotenv import load_dotenv
from src.notion_uploader import upload_research_summary

def test_notion_upload():
    """Test the Notion upload functionality."""
    # Load environment variables
    load_dotenv()

    # Check if environment variables are set
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key:
        print("❌ NOTION_API_KEY environment variable not set")
        print("Please create a .env file with your Notion API key")
        return

    if not database_id:
        print("❌ NOTION_DATABASE_ID environment variable not set")
        print("Please add your Notion database ID to the .env file")
        return

    print("✅ Environment variables are set")

    # Test data
    user_query = "Test research query about machine learning"
    generated_text = """This is a test research summary.

Here are some key findings:
1. Machine learning is a subset of AI
2. Deep learning uses neural networks
3. Transformers revolutionized NLP

For more information, check the referenced papers."""

    try:
        print("📤 Attempting to upload to Notion...")
        notion_url = upload_research_summary(user_query, generated_text, "Test Research Summary")
        print(f"✅ Successfully uploaded to Notion: {notion_url}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print("Please check your Notion setup in NOTION_SETUP.md")

if __name__ == "__main__":
    test_notion_upload()
