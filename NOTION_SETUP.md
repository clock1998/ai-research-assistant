# Notion Integration Setup

This guide explains how to set up Notion integration to upload generated research summaries.

## Prerequisites

1. A Notion account
2. A Notion workspace where you can create databases

## Setup Steps

### 1. Create a Notion Integration

1. Go to [Notion Integrations](https://www.notion.com/my-integrations)
2. Click "New integration"
3. Give it a name (e.g., "AI Research Assistant")
4. Select the workspace where you want to store research summaries
5. Choose the capabilities: Read, Write, Update (or just Write for this use case)
6. Copy the "Internal Integration Token" - this is your API key

### 2. Create a Database in Notion

1. Create a new page in your Notion workspace
2. Add a Database block (choose "Table" view)
3. Configure the database properties:
   - Name (title property - required)
   - Query (text property - for storing the original user query)
   - Created (date property - for timestamp)
4. Share the database with your integration:
   - Click the "..." menu in the top right of the database
   - Click "Add connections"
   - Find and select your integration
5. Get the database ID from the URL:
   - The URL will look like: `https://www.notion.so/workspace/12345678-abcd-1234-5678-abcdef123456?v=abcd1234-5678-90ab-cdef-123456789012`
   - The database ID is: `12345678-abcd-1234-5678-abcdef123456` (the part before the `?`)

### 3. Set Environment Variables

Create a `.env` file in the project root with:

```bash
NOTION_API_KEY=your_internal_integration_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### 4. Install Dependencies

The `notion-client` package is already included in `requirements.txt`. If you need to reinstall:

```bash
pip install -r requirements.txt
```

## How It Works

When a user asks a research question:
1. The system generates a response with paper summaries
2. A new page is created in your Notion database with:
   - Title based on the user query
   - The original query
   - Timestamp
   - Full research summary

## Troubleshooting

- **"NOTION_API_KEY environment variable not set"**: Make sure your `.env` file exists and contains the correct API key
- **"NOTION_DATABASE_ID environment variable not set"**: Ensure you've set the database ID in your `.env` file
- **Permission denied**: Make sure your integration has write access to the database
- **Invalid database ID**: Double-check that you've copied the correct ID from the Notion URL
