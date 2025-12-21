import torch
from transformers import pipeline, AutoTokenizer
import json
import re

conversation_history = []
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

# System prompt instructing the model about function calls
SYSTEM_PROMPT = """You are a helpful research assistant. You can answer questions directly or use function calls when appropriate.

You have access to two functions:
1. `calculate(expression)` - For mathematical calculations. Use this when the user asks you to compute, calculate, or solve a math problem.
2. `search_arxiv(query)` - For searching research papers on arXiv. Use this when the user asks about research topics, papers, or scientific information.

When you need to call a function, output ONLY a valid JSON object in this exact format:
{"function": "function_name", "arguments": {"argument_name": "argument_value"}}

Examples:
- For math: {"function": "calculate", "arguments": {"expression": "2+2"}}
- For research: {"function": "search_arxiv", "arguments": {"query": "quantum entanglement"}}

If the user's question can be answered directly without needing a function call, respond normally in plain text.

IMPORTANT: Output ONLY the JSON object (no markdown, no code blocks, no explanation) when making a function call. For normal responses, output plain text."""

def generate_response(user_text):
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_text})
    
    # Prepare messages with system prompt (only add system prompt once at the start)
    messages = []
    if len(conversation_history) == 1:  # First user message
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.extend(conversation_history)
    
    # Apply chat template
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Generate response with temperature=0 for deterministic output
    outputs = llm(
        prompt,
        max_new_tokens=200,
        return_full_text=False,
        temperature=0,
        do_sample=False
    )
    bot_response = outputs[0]["generated_text"].strip()
    
    # Route the output to handle function calls
    final_response = route_llm_output(bot_response)
    
    # Add assistant response to history (store the raw response, not the routed one)
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    return final_response

def search_arxiv(query):
    return "I'm sorry, I can't search the web for you."

def calculate(expression):
    """
    Evaluate a mathematical expression and return the result as a string.
    """
    try:
        from sympy import sympify
        result = sympify(expression)  # use sympy for safe evaluation
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def route_llm_output(llm_output: str) -> str:
    """
    Route LLM response to the correct tool if it's a function call, else return the text.
    Expects LLM output in JSON format like {'function': ..., 'arguments': {...}}.
    Handles cases where JSON might be embedded in text or have markdown formatting.
    """
    # Try to extract JSON from the output (handle markdown code blocks, etc.)
    text = llm_output.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```
    if text.endswith("```"):
        text = text[:-3]  # Remove closing ```
    text = text.strip()
    
    # Try to find JSON object in the text
    try:
        # First, try parsing the entire text
        output = json.loads(text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON object from the text
        json_match = re.search(r'\{[^{}]*"function"[^{}]*\}', text)
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

    if func_name == "search_arxiv":
        query = args.get("query", "")
        return search_arxiv(query)
    elif func_name == "calculate":
        expr = args.get("expression", "")
        return calculate(expr)
    else:
        return f"Error: Unknown function '{func_name}'"