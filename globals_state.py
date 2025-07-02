# globals_state.py - Stub module for backward compatibility
# This module is being replaced by AppContext but kept for compatibility

# Global state variables
current_chat_name: str | None = None
chat_history: list = []
animated_typing_enabled: bool = True

def toggle_animated_typing() -> bool:
    """Toggle animated typing feature"""
    global animated_typing_enabled
    animated_typing_enabled = not animated_typing_enabled
    return animated_typing_enabled 