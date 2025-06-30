# globals_state.py

# ============================
# ✅ Animated typing state
# ============================
animated_typing_enabled = True

def toggle_animated_typing():
    global animated_typing_enabled
    animated_typing_enabled = not animated_typing_enabled
    print(f"[EIDOLON] 🧠 Animated typing {'enabled' if animated_typing_enabled else 'disabled'}")

# ============================
# ✅ Global session/chat states
# ============================
chat_history = []
current_chat_name = None
push_message_func = None
qml_bridge = None
gui = None
sidebar_backend = None
root = None

# ============================
# ✅ Helper setter functions
# ============================

def reset_chat_state():
    """Reset chat history and current chat name."""
    global chat_history, current_chat_name
    chat_history = []
    current_chat_name = "Untitled"
    print("🆕 Chat state reset to Untitled")

def set_push_message_func(func):
    """Set the global push_message_func reference."""
    global push_message_func
    push_message_func = func
    print("✅ push_message_func set")

def set_qml_bridge(bridge):
    """Set the global qml_bridge reference."""
    global qml_bridge
    qml_bridge = bridge
    print("✅ qml_bridge set")

def set_sidebar_backend(backend):
    """Set the global sidebar_backend reference."""
    global sidebar_backend
    sidebar_backend = backend
    print("✅ sidebar_backend set")

def set_gui_instance(gui_instance):
    """Set the global gui reference."""
    global gui
    gui = gui_instance
    print("✅ gui instance set")

def set_root_instance(root_instance):
    """Set the global root reference."""
    global root
    root = root_instance
    print("✅ root instance set")

# ============================
# ✅ State verification utility
# ============================

def print_global_state():
    """Print current global state for debugging."""
    print("\n✅ Current Global State:")
    print(f"animated_typing_enabled: {animated_typing_enabled}")
    print(f"chat_history length: {len(chat_history)}")
    print(f"current_chat_name: {current_chat_name}")
    print(f"push_message_func set: {push_message_func is not None}")
    print(f"qml_bridge set: {qml_bridge is not None}")
    print(f"gui set: {gui is not None}")
    print(f"sidebar_backend set: {sidebar_backend is not None}")
    print(f"root set: {root is not None}\n")