import torch
from transformers import pipeline, AutoTokenizer
import json
import re

from src.arxiv_api_client import fetch_and_parse_arxiv
from src.reranker import rerank_crossencoder


class ResearchAssistant:
    """Research assistant that generates responses and handles arXiv searches."""

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

    def __init__(self, model_name="meta-llama/Llama-3.1-8B-Instruct"):
        self.model_name = model_name
        self.conversation_history = []
        self.original_user_question = ""

        # Initialize tokenizer for chat template
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Initialize LLM pipeline
        self.llm = pipeline(
            "text-generation",
            model=self.model_name,
            model_kwargs={"dtype": torch.bfloat16},
            device_map="auto",
            tokenizer=self.tokenizer
        )

    def generate_response(self, user_text):
        """Generate a response to user input, handling conversation history and function calls."""
        # Prepare messages with system prompt (only add system prompt once at the start)
        if len(self.conversation_history) == 0:  # First user message
            self.conversation_history.append({"role": "system", "content": self.SYSTEM_PROMPT})
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_text})
        self.original_user_question = user_text

        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            self.conversation_history,
            tokenize=False,
            add_generation_prompt=True
        )

        # Generate response with temperature=0 for deterministic output
        outputs = self.llm(
            prompt,
            temperature=0.0,
            max_new_tokens=200,
            return_full_text=False,
            do_sample=False
        )
        bot_response = outputs[0]["generated_text"].strip()

        # Route the output to handle function calls
        final_response = self._route_llm_output(bot_response)

        # Add assistant response to history (store the raw response, not the routed one)
        self.conversation_history.append({"role": "assistant", "content": bot_response})

        return final_response

    def _route_llm_output(self, llm_output: str) -> str:
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
            return self._search_arxiv(query)
        else:
            return f"Error: Unknown function '{func_name}'"

    def _search_arxiv(self, query):
        """Search arXiv and return formatted results with reranking."""
        arxiv_response = fetch_and_parse_arxiv(query, max_results=50)

        if arxiv_response.papers and len(arxiv_response.papers) > 0:
            # Prepare summaries to rerank
            paper_summaries = [paper.summary for paper in arxiv_response.papers]
            scores = rerank_crossencoder(self.original_user_question, paper_summaries)

            # Pair each paper with its score, then sort by score descending
            papers_and_scores = list(zip(arxiv_response.papers, scores))
            papers_and_scores.sort(key=lambda x: x[1], reverse=True)

            # Take only the first 3 papers
            top_papers = papers_and_scores[:3]

            # Generate human-readable summaries for all papers at once
            return self._generate_paper_summary(top_papers)
        else:
            return f"No papers found for query: {query}"

    def _generate_paper_summary(self, papers_and_scores):
        """Generate a human-readable summary of multiple papers using the LLM."""
        prompt_parts = [
            "You are a research assistant summarizing academic papers. Create natural, engaging summaries of the following papers that include all key information in a conversational tone."
        ]

        for i, (paper, score) in enumerate(papers_and_scores, 1):
            prompt_parts.append(f"""
            Title: {paper.title}
            Abstract: {paper.summary}
            PDF URL: {paper.pdf_url}
            """)

        prompt_parts.append("""
            For each paper, write a comprehensive summary that covers:
            1. What the paper is about (based on title and abstract)
            2. Links to access the full paper

            Make it sound natural and informative, like you're explaining it to someone interested in the field. Organize the response clearly with titles.
            """)

        prompt = "\n".join(prompt_parts)

        # Apply chat template for single-turn conversation
        messages = [{"role": "user", "content": prompt}]
        chat_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Generate response
        outputs = self.llm(
            chat_prompt,
            temperature=0.5,  # Slightly higher temperature for more natural language
            max_new_tokens=1200,  # Increased for multiple papers
            return_full_text=False,
            do_sample=True
        )

        return outputs[0]["generated_text"].strip()


# Create a module-level instance for backward compatibility
_assistant = ResearchAssistant()

def generate_response(user_text):
    """Module-level function for backward compatibility."""
    return _assistant.generate_response(user_text)