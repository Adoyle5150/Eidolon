import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict

class ContentCache:
    """Enhanced cache with expiration and metadata"""
    
    def __init__(self, cache_dir="web_cache", max_age_hours=2):
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, url: str) -> Optional[Dict]:
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cache_time = datetime.fromisoformat(data['timestamp'])
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600
            
            if age_hours > self.max_age_hours:
                os.remove(cache_path)
                return None
            
            return data['content']
            
        except Exception as e:
            logger.warning(f"Cache read error for {url}: {e}")
            return None
    
    def set(self, url: str, content: Dict):
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'content': content
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"Cache write error for {url}: {e}")

