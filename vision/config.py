# config.py — Eidolon System Settings

import os
import platform
import pytesseract

class VisionConfig:
    # === Vision Settings ===
    VISION_ENABLED = True
    CAPTURE_INTERVAL = 10  # Seconds between screenshots
    OCR_ENGINE = "tesseract"  # Or "custom"

    # === Memory Settings ===
    VISION_MEMORY_ENABLED = True
    MEMORY_FILE_PATH = "vision_memory.json"

    # === Logging ===
    DEBUG_MODE = True
    LOG_FILE = "eidolon.log"

    # === Web Search ===
    WEB_SEARCH_ENABLED = True
    SEARCH_ENGINE = "duckduckgo"  # Future support for "bing", "google"

    # === Assistant Identity ===
    ASSISTANT_NAME = "Eidolon"
    CREATOR_NAME = "Austin"
    IDENTITY_FILE = "identity.json"

    # === Optional Paths ===
    SCREENSHOT_FOLDER = "captures"
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Only for Windows

    # Auto-detect Tesseract
    if platform.system() == "Windows" and os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

CAPTURE_INTERVAL = VisionConfig.CAPTURE_INTERVAL
OCR_ENGINE = VisionConfig.OCR_ENGINE
VISION_MEMORY_ENABLED = VisionConfig.VISION_MEMORY_ENABLED
MEMORY_FILE_PATH = VisionConfig.MEMORY_FILE_PATH
DEBUG_MODE = VisionConfig.DEBUG_MODE
LOG_FILE = VisionConfig.LOG_FILE
WEB_SEARCH_ENABLED = VisionConfig.WEB_SEARCH_ENABLED
SEARCH_ENGINE = VisionConfig.SEARCH_ENGINE
ASSISTANT_NAME = VisionConfig.ASSISTANT_NAME
CREATOR_NAME = VisionConfig.CREATOR_NAME
IDENTITY_FILE = VisionConfig.IDENTITY_FILE
SCREENSHOT_FOLDER = VisionConfig.SCREENSHOT_FOLDER
TESSERACT_PATH = VisionConfig.TESSERACT_PATH
VISION_ENABLED = VisionConfig.VISION_ENABLED


