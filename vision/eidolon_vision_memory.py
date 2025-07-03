# vision/eidolon_vision_memory.py
import os
import json
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Optional

MEMORY_FILE = "data/vision_memory.json"

class EidolonVisionMemory:
    def __init__(self) -> None:
        self.memory: List[Dict[str, Any]] = self.load_memory()

    def load_memory(self) -> List[Dict[str, Any]]:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_memory(self) -> None:
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Failed to save vision memory: {e}")

    def hash_context(self, context: Dict[str, Any]) -> str:
        combined = context["window_title"] + " " + " ".join(context["tags"])
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def remember(self, context: Dict[str, Any]) -> None:
        hash_key = self.hash_context(context)
        for entry in self.memory:
            if entry["hash"] == hash_key:
                return  # Already stored
        print(f"🧠 Saving new vision context: {context['tags']}")
        self.memory.append({
            "hash": hash_key,
            "timestamp": datetime.now().isoformat(),
            "window": context["window_title"],
            "tags": context["tags"],
            "ocr_snippet": context["ocr_text"][:100]
        })
        self.save_memory()

    def recall(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        hash_key = self.hash_context(context)
        for entry in self.memory:
            if entry["hash"] == hash_key:
                return entry
        return None

    def get_recent_contexts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent context entries"""
        return self.memory[-count:] if self.memory else []

# For testing
if __name__ == "__main__":
    from context_interpreter import ContextInterpreter

    ci = ContextInterpreter()
    em = EidolonVisionMemory()

    context = ci.analyze_context("captures/screen_20250627_004437.png")
    if context:
        em.remember(context)
        match = em.recall(context)
        print("📖 Recalled:", match)
    else:
        print("❌ No context found")
