# eidolon/utils/helpers.py

import ast
import re

def is_valid_python(code: str) -> bool:
    """
    Check if the provided code is valid Python syntax.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def optimize_search_query(query, intent="general"):
    """
    Optimize a user query for web search by removing filler words and appending intent keywords.
    
    Parameters:
        query (str): The user's query.
        intent (str): The intent of the search ("general", "news", "technical", "current").
    
    Returns:
        str: The optimized search query.
    """
    if not query:
        return ""
    
    filler_words = ['please', 'can you', 'could you', 'tell me', 'explain', 'help me', 'i want to know']
    optimized = query.lower()
    
    for filler in filler_words:
        optimized = re.sub(r'\b' + re.escape(filler) + r'\b', '', optimized, flags=re.IGNORECASE)
    
    optimized = re.sub(r'[?!.]+$', '', optimized)
    optimized = re.sub(r'\s+', ' ', optimized).strip()
    
    if intent == "news" or any(word in optimized for word in ['latest', 'recent', 'breaking']):
        optimized += " news 2025"
    elif intent == "technical" or any(word in optimized for word in ['how to', 'tutorial', 'guide']):
        optimized += " guide tutorial"
    elif intent == "current" or any(word in optimized for word in ['current', 'now', 'today']):
        optimized += " current 2025"
    
    return optimized[:100]

def is_valid_message(msg):
    """Return True if msg is a dict with string 'role' and string 'content'."""
    return (
        isinstance(msg, dict) and
        isinstance(msg.get("role"), str) and
        isinstance(msg.get("content"), str)
    )
