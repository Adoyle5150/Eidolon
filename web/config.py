import os
import json
import logging

CONFIG_PATH = "eidolon_config.json"

DEFAULT_CONFIG = {
    "auto_search_enabled": True,
    "search_delay_min": 0.3,
    "search_delay_max": 0.8,
    "max_results": 8,
    "page_timeout": 12,
    "max_content_length": 3000,
    "min_content_length": 100,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "max_concurrent_requests": 4,
    "use_selenium_fallback": True,
    "cache_enabled": True,
    "search_engines": ["duckduckgo", "bing_fallback"],
    "content_quality_threshold": 0.3,
    "extract_metadata": True,
    "smart_summarization": True,
    "relevance_threshold": 0.4,
    "max_summary_length": 1500,
    "include_timestamps": True,
    "prioritize_recent": True
}

# Optional logger setup for config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path: str = CONFIG_PATH) -> dict:
    if not os.path.exists(config_path):
        save_config(DEFAULT_CONFIG, config_path)
        return DEFAULT_CONFIG
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return DEFAULT_CONFIG

def save_config(config: dict, config_path: str = CONFIG_PATH):
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
