# globals_state.py
animated_typing_enabled = True

def toggle_animated_typing():
    global animated_typing_enabled
    animated_typing_enabled = not animated_typing_enabled
    print(f"[EIDOLON] 🧠 Animated typing {'enabled' if animated_typing_enabled else 'disabled'}")
