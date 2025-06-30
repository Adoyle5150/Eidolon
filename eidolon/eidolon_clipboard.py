# eidolon_clipboard.py

"""
Eidolon - Clipboard Management Module

Provides a QML-safe ClipboardWrapper for copy/paste integration
with Eidolon's PyQt6 GUI.

- Allows copying AI outputs, snippets, or user selections.
- Integrates with system clipboard seamlessly.
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class ClipboardWrapper(QObject):
    """
    Exposes clipboard operations to QML.
    """
    textChanged = pyqtSignal(str)

    def __init__(self, clipboard):
        super().__init__()
        self.clipboard = clipboard
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)
        print("[EIDOLON_CLIPBOARD] ✅ Clipboard wrapper initialized")

    def _on_clipboard_changed(self):
        """
        Internal signal handler for clipboard updates.
        """
        text = self.clipboard.text()
        self.textChanged.emit(text)

    @pyqtSlot(str)
    def copyText(self, text):
        """
        Copy provided text to the clipboard.
        """
        self.clipboard.setText(text)
        print(f"[EIDOLON_CLIPBOARD] 📋 Text copied to clipboard ({len(text)} chars)")

    @pyqtSlot(result=str)
    def getText(self):
        """
        Retrieve current clipboard text.
        """
        return self.clipboard.text() or ""
