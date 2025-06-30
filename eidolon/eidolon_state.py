# eidolon_state.py

"""
Eidolon - State Management Module

Handles assistant state transitions and consistent communication
with the GUI (via QML bridge) for status updates:
- 'ready'
- 'thinking'
- 'typing'
"""

# Dependencies
from PyQt6.QtCore import QMetaObject, Q_ARG, QVariant

# Globals (injected during initialization)
qml_bridge = None
root = None

VALID_STATES = ["ready", "thinking", "typing"]

def inject_gui_references(qml_bridge_ref=None, root_ref=None):
    """
    Inject QML bridge and root references at runtime.
    Call this once in your GUI initialization.
    """
    global qml_bridge, root
    qml_bridge = qml_bridge_ref
    root = root_ref
    print("[EIDOLON_STATE] ✅ GUI references injected")


def set_assistant_state(state):
    """
    Transition assistant to a new state ('ready', 'thinking', 'typing'),
    updating GUI appropriately.
    """
    if state not in VALID_STATES:
        print(f"[EIDOLON_STATE] ⚠️ Invalid state: {state} (valid: {VALID_STATES})")
        return

    print(f"[EIDOLON_STATE] 🔄 Setting state: {state}")

    if qml_bridge and hasattr(qml_bridge, 'set_assistant_state'):
        try:
            qml_bridge.set_assistant_state(state)
        except Exception as e:
            print(f"[EIDOLON_STATE] ⚠️ Error setting state via qml_bridge: {e}")

    elif root:
        try:
            QMetaObject.invokeMethod(
                root,
                "setAssistantState",
                Q_ARG(QVariant, state)
            )
        except Exception as e:
            print(f"[EIDOLON_STATE] ⚠️ Error setting state via root: {e}")
    else:
        print(f"[EIDOLON_STATE] ⚠️ No GUI reference available to set state: {state}")
