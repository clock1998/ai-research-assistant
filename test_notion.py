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

    # Test data - create a longer text to test chunking
    user_query = "Test research query about machine learning"
    generated_text = """This is a test research summary with longer content to verify that the chunking algorithm works correctly when content exceeds Notion's 2000 character limit per block.

Here are some key findings from the research:
1. Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data without being explicitly programmed
2. Deep learning uses neural networks with multiple layers to process complex patterns in data
3. Transformers revolutionized natural language processing through attention mechanisms
4. Reinforcement learning enables agents to learn optimal behavior through trial and error
5. Computer vision applications include image classification, object detection, and facial recognition

The field has seen tremendous growth in recent years, with applications spanning healthcare, finance, transportation, and entertainment. Neural networks, particularly convolutional neural networks (CNNs) and recurrent neural networks (RNNs), have become foundational technologies.

Research continues to advance in areas such as:
- Explainable AI to make model decisions more interpretable
- Federated learning for privacy-preserving distributed training
- Meta-learning for few-shot learning scenarios
- Multi-modal learning combining text, images, and other data types

The impact of these technologies on society is profound, enabling new capabilities while raising important ethical considerations around bias, privacy, and responsible AI development.

For more information, check the referenced papers and ongoing research in top conferences like NeurIPS, ICML, and CVPR. The field continues to evolve rapidly with new architectures and applications emerging regularly."""

    try:
        print("📤 Attempting to upload to Notion...")
        notion_url = upload_research_summary(user_query, generated_text, "Test Research Summary")
        print(f"✅ Successfully uploaded to Notion: {notion_url}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        print("Please check your Notion setup in NOTION_SETUP.md")

if __name__ == "__main__":
    test_notion_upload()
