# eidolon/core/state_manager.py

def set_assistant_state(state, qml_bridge=None, root=None):
    """
    Sets the assistant's state in the UI ('ready', 'thinking', 'typing').

    Parameters:
        state (str): The state to set.
        qml_bridge: The QML bridge object (optional).
        root: The QML root object (optional).
    """
    valid_states = ["ready", "thinking", "typing"]
    if state not in valid_states:
        print(f"⚠️ Invalid state: {state}, must be one of {valid_states}")
        return

    print(f"🔄 State transition: {state}")

    if qml_bridge and hasattr(qml_bridge, 'set_assistant_state'):
        qml_bridge.set_assistant_state(state)
    elif root:
        root.setProperty("assistantState", state)
    else:
        print(f"⚠️ Cannot set assistant state (bridge/root not available): {state}")
