from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtGui import QClipboard

class ClipboardWrapper(QObject):
    def __init__(self, clipboard: QClipboard):
        super().__init__()
        self.clipboard = clipboard

    @pyqtSlot(str)
    def setText(self, text):
        self.clipboard.setText(text) 