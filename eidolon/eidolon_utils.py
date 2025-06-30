# eidolon/eidolon_utils.py

import os
import json
from datetime import datetime
import ast
import re

def is_valid_python(code: str) -> bool:
    """Check if a string is valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def optimize_search_query(query, intent="general"):
    """
    Clean and enhance a user query for more effective web search.
    Adds context keywords based on detected intent.
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
