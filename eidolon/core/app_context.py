

class AppContext:
    def __init__(self):
        # Chat management
        self.chat_history = []
        self.current_chat_name = "Untitled"
        self.unsaved_changes = False

        # UI control
        self.animated_typing_enabled = True
        self.typing_state = False
        self.root = None
        self.qml_bridge = None

        # Communication hooks
        self.push_message_func = None
        self.gui = None

        # Config references (optional, add as needed)
        self.config = None

        # Vision / Web modules if you want to attach them later
        self.vision_service = None
        self.web_search_func = None
