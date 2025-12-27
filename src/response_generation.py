import torch
from transformers import pipeline, AutoTokenizer
import json
import re

from src.arxiv_api_client import fetch_and_parse_arxiv
from src.reranker import rerank_crossencoder

conversation_history = []
original_user_question = ""
model_name = "meta-llama/Llama-3.1-8B-Instruct"
# Initialize tokenizer for chat template
tokenizer = AutoTokenizer.from_pretrained(model_name)

llm = pipeline(
    "text-generation", 
    model=model_name,
    model_kwargs={"dtype": torch.bfloat16}, 
    device_map="auto",
    tokenizer=tokenizer
)

SYSTEM_PROMPT = """
You are a search query engineer. Your goal is to transform a user's research question into a precise arXiv API query string.

Rules:
Use field prefixes: ti: (title), au: (author), abs: (abstract), cat: (category).
Use Boolean operators: AND, OR, ANDNOT (must be capitalized).
Group terms using parentheses.
If the user mentions a specific field (e.g., "find papers by Hinton"), use au:.
If a user is looking for a specific concept, you should use Title(ti:) or Abstract(abs:).
Query Expansion: Include synonyms (e.g., "LLM" OR "Large Language Model").

[FUNCTION_SCHEMA]
{"function": "search_arxiv", "arguments": {"query": "string"}}

[EXAMPLES]
User: "Search for quantum computing."
Assistant: {"function": "search_arxiv", "arguments": {"query": "all:quantum AND all:computing"}}

User: "Find papers by Einstein."
Assistant: {"function": "search_arxiv", "arguments": {"query": "au:Einstein"}}
"""

def generate_response(user_text):
    global original_user_question
    # Prepare messages with system prompt (only add system prompt once at the start)
    if len(conversation_history) == 0:  # First user message
        conversation_history.append({"role": "system", "content": SYSTEM_PROMPT})
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_text})
    original_user_question = user_text;
    # Apply chat template
    prompt = tokenizer.apply_chat_template(
        conversation_history,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Generate response with temperature=0 for deterministic output
    outputs = llm(
        prompt,
        temperature=0.0,
        max_new_tokens=200,
        return_full_text=False,
        do_sample=False
    )
    bot_response = outputs[0]["generated_text"].strip()
    
    # Route the output to handle function calls
    final_response = route_llm_output(bot_response)
    
    # Add assistant response to history (store the raw response, not the routed one)
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    return final_response

def route_llm_output(llm_output: str) -> str:
    """
    Route LLM response to the correct tool if it's a function call, else return the text.
    Expects LLM output in JSON format like {"function": "...", "arguments": {...}}.
    """
    # Try to parse the entire output as JSON directly
    try:
        output = json.loads(llm_output.strip())
    except json.JSONDecodeError:
        # If that fails, try to extract JSON object from the text
        json_match = re.search(r'\{[^{}]*"function"[^{}]*\}', llm_output)
        if json_match:
            try:
                output = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Not a JSON function call; return the text directly
                return llm_output
        else:
            # Not a JSON function call; return the text directly
            return llm_output

    # Extract function name and arguments
    func_name = output.get("function")
    args = output.get("arguments", {})

    if not func_name:
        # Invalid JSON structure; return the text directly
        return llm_output

    if func_name == "none":
        # No function call needed; return empty or default response
        return ""
    elif func_name == "search_arxiv":
        query = args.get("query", "")
        return _search_arxiv(query)
    else:
        return f"Error: Unknown function '{func_name}'"

def _search_arxiv(query):
    arxiv_response = fetch_and_parse_arxiv(query, max_results=50)

    if arxiv_response.papers and len(arxiv_response.papers) > 0:
        # Prepare summaries to rerank
        paper_summaries = [paper.summary for paper in arxiv_response.papers]
        scores = rerank_crossencoder(original_user_question, paper_summaries)
        
        # Pair each paper with its score, then sort by score descending
        papers_and_scores = list(zip(arxiv_response.papers, scores))
        papers_and_scores.sort(key=lambda x: x[1], reverse=True)

        # Format the sorted results
        results = []
        for paper, _ in papers_and_scores:
            result = f"**{paper.title}**\n"
            result += f"Authors: {', '.join(paper.authors)}\n"
            result += f"Published: {paper.published_date.strftime('%Y-%m-%d') if paper.published_date else 'Unknown'}\n"
            result += f"Abstract: {paper.summary}\n"
            result += f"PDF: {paper.pdf_url}\n"
            result += f"Abstract URL: {paper.abstract_url}\n"
            results.append(result)

        return "\n\n".join(results)
    else:
        return f"No papers found for query: {query}"