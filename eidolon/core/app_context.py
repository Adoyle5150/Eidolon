

from typing import Any, Callable, List, Optional
from PyQt6.QtCore import QObject

class AppContext:
    def __init__(self):
        # Chat management
        self.chat_history: List[dict] = []
        self.current_chat_name: str = "Untitled"
        self.unsaved_changes: bool = False

        # UI control
        self.animated_typing_enabled: bool = True
        self.typing_state: bool = False
        self.root: Optional[QObject] = None
        self.qml_bridge: Optional[Any] = None
        self.sidebar_backend: Optional[Any] = None

        # Communication hooks
        self.push_message_func: Optional[Callable[[str, str], None]] = None
        self.gui: Optional[Any] = None

        # Config references (optional, add as needed)
        self.config: Optional[Any] = None

        # Vision / Web modules if you want to attach them later
        self.vision_service: Optional[Any] = None
        self.web_search_func: Optional[Callable[[str, Optional[Callable]], str]] = None
