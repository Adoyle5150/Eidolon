import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import random
import json
import os
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse, urljoin
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import List, Dict, Optional, Tuple, Set
import hashlib
from collections import Counter
import math
from web.analyzer import ContentAnalyzer
from web.summarizer import IntelligentSummarizer
from web.cache import ContentCache

_searcher = None



# Readability for cleaner extraction
try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

# DuckDuckGo search
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False

# Selenium fallback
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config imports
from web.config import CONFIG_PATH, DEFAULT_CONFIG, load_config, save_config


# Future:
# from eidolon.web.analyzer import ContentAnalyzer
# from eidolon.web.summarizer import IntelligentSummarizer
# from eidolon.web.cache import ContentCache


class EnhancedWebSearcher:
    """Enhanced web searcher with intelligent summarization"""
    
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config = self._load_config(config_path)
        self.cache = ContentCache() if self.config.get("cache_enabled") else None
        self.session = self._create_session()
        self.analyzer = ContentAnalyzer()
        self.summarizer = IntelligentSummarizer(self.analyzer)
    
    def _load_config(self, config_path: str) -> Dict:
        if not os.path.exists(config_path):
            self._save_config(config_path, DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return DEFAULT_CONFIG
    
    def _save_config(self, config_path: str, config: Dict):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def _is_valid_url(self, url: str) -> bool:
        if not url:
            return False
        
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
            
            if result.scheme not in ['http', 'https']:
                return False
            
            if '.' not in result.netloc:
                return False
            
            return True
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove common navigation/footer elements
        lines = text.split('\n')
        cleaned_lines = []
        
        skip_patterns = [
            r'cookie', r'privacy policy', r'terms of service',
            r'subscribe', r'newsletter', r'advertisement',
            r'skip to content', r'menu', r'navigation'
        ]
        
        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue
            
            if any(re.search(pattern, line.lower()) for pattern in skip_patterns):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _extract_with_requests(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            response = self.session.get(url, timeout=self.config['page_timeout'])
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return None, f"Non-HTML content type: {content_type}", None
            
            if READABILITY_AVAILABLE:
                doc = Document(response.text)
                title = doc.title()
                content = doc.summary()
                
                if content.startswith('<'):
                    soup = BeautifulSoup(content, 'html.parser')
                    content = soup.get_text(separator='\n', strip=True)
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else ""
                
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
                if main_content:
                    content = main_content.get_text(separator='\n', strip=True)
                else:
                    content = soup.get_text(separator='\n', strip=True)
            
            content = self._clean_text(content)
            
            if len(content) < self.config['min_content_length']:
                return None, "Content too short after cleaning", title
            
            return content, None, title
            
        except requests.RequestException as e:
            return None, f"Request failed: {str(e)}", None
        except Exception as e:
            return None, f"Extraction failed: {str(e)}", None
    
    def _extract_with_selenium(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not SELENIUM_AVAILABLE:
            return None, "Selenium not available", None
        
        driver = None
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-images")
            options.add_argument(f"--user-agent={self.config['user_agent']}")
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.config['page_timeout'])
            
            driver.get(url)
            
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            title = driver.title
            
            if READABILITY_AVAILABLE:
                doc = Document(driver.page_source)
                content = doc.summary()
                
                if content.startswith('<'):
                    soup = BeautifulSoup(content, 'html.parser')
                    content = soup.get_text(separator='\n', strip=True)
            else:
                body = driver.find_element(By.TAG_NAME, "body")
                content = body.text
            
            content = self._clean_text(content)
            
            if len(content) < self.config['min_content_length']:
                return None, "Content too short", title
            
            return content, None, title
            
        except Exception as e:
            return None, f"Selenium extraction failed: {str(e)}", None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def extract_content(self, url: str) -> Dict:
        if not self._is_valid_url(url):
            return {
                'success': False,
                'error': 'Invalid URL',
                'content': '',
                'title': '',
                'url': url
            }
        
        if self.cache:
            cached = self.cache.get(url)
            if cached:
                logger.info(f"Using cached content for {url}")
                return cached
        
        content, error, title = self._extract_with_requests(url)
        
        if not content and error and self.config.get('use_selenium_fallback') and SELENIUM_AVAILABLE:
            logger.info(f"Trying Selenium fallback for {url}")
            content, error, title = self._extract_with_selenium(url)
        
        result = {
            'success': bool(content),
            'error': error,
            'content': content or '',
            'title': title or '',
            'url': url,
            'length': len(content) if content else 0
        }
        
        if self.cache and result['success']:
            self.cache.set(url, result)
        
        return result
    
    def search_duckduckgo(self, query: str) -> List[Dict]:
        if not DUCKDUCKGO_AVAILABLE:
            logger.warning("DuckDuckGo not available")
            return []
        
        try:
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=self.config['max_results'],
                    region='us-en',
                    safesearch='moderate'
                )
                
                for result in search_results:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('href', ''),
                        'snippet': result.get('body', ''),
                        'source': 'duckduckgo'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    def search_bing_fallback(self, query: str) -> List[Dict]:
        try:
            search_url = f"https://www.bing.com/search?q={quote(query)}"
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result_div in soup.find_all('li', class_='b_algo')[:self.config['max_results']]:
                title_tag = result_div.find('h2')
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                if not link_tag:
                    continue
                
                title = title_tag.get_text().strip()
                url = link_tag.get('href', '')
                
                snippet_tag = result_div.find('p') or result_div.find('div', class_='b_caption')
                snippet = snippet_tag.get_text().strip() if snippet_tag else ''
                
                if self._is_valid_url(url):
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'bing_fallback'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Bing fallback search failed: {e}")
            return []
    
    def search(self, query: str, progress_callback=None) -> str:
        if not self.config.get('auto_search_enabled', True):
            return "🔒 Web search is currently disabled."
        
        if not query or not query.strip():
            return "❌ Empty search query provided."
        
        query = query.strip()
        logger.info(f"Starting intelligent web search for: {query}")
        
        if progress_callback:
            try:
                progress_callback("assistant", f"🔎 Searching for: \"{query}\"...")
            except TypeError:
                try:
                    progress_callback(f"🔎 Searching for: \"{query}\"...")
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
        
        time.sleep(random.uniform(
            self.config['search_delay_min'],
            self.config['search_delay_max']
        ))
        
        # Get search results
        search_results = []
        for engine in self.config.get('search_engines', ['duckduckgo']):
            if engine == 'duckduckgo':
                results = self.search_duckduckgo(query)
            elif engine == 'bing_fallback':
                results = self.search_bing_fallback(query)
            else:
                continue
            
            if results:
                search_results = results
                break
        
        if not search_results:
            return "❌ No search results found from any search engine."
        
        logger.info(f"Found {len(search_results)} search results")
        
        if progress_callback:
            try:
                progress_callback("assistant", f"📄 Analyzing content from {len(search_results)} sources...")
            except TypeError:
                try:
                    progress_callback(f"📄 Analyzing content from {len(search_results)} sources...")
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
        
        # Extract content in parallel
        final_results = []
        max_workers = min(self.config['max_concurrent_requests'], len(search_results))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_result = {
                executor.submit(self.extract_content, result['url']): result
                for result in search_results
            }
            
            for future in as_completed(future_to_result, timeout=60):
                search_result = future_to_result[future]
                try:
                    extraction_result = future.result(timeout=30)
                    
                    if extraction_result['success']:
                        content = extraction_result['content']
                        
                        if len(content) > self.config['max_content_length']:
                            content = content[:self.config['max_content_length']] + "..."
                        
                        # Calculate scores
                        query_terms = self.analyzer.extract_query_terms(query)
                        relevance_score = self.analyzer.calculate_relevance_score(
                            content, extraction_result['title'], query_terms
                        )
                        recency_score = self.analyzer.calculate_recency_score(
                            content, extraction_result['title']
                        )
                        quality_score = self.analyzer.calculate_quality_score(
                            content, extraction_result['title']
                        )
                        
                        # Combined score for ranking
                        combined_score = (relevance_score * 0.5 + 
                                        recency_score * 0.3 + 
                                        quality_score * 0.2)
                        
                        final_results.append({
                            'title': extraction_result['title'] or search_result['title'],
                            'url': search_result['url'],
                            'content': content,
                            'snippet': search_result.get('snippet', ''),
                            'success': True,
                            'relevance_score': relevance_score,
                            'recency_score': recency_score,
                            'quality_score': quality_score,
                            'combined_score': combined_score
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing {search_result['url']}: {e}")
        
        if not final_results:
            return "❌ No content could be extracted from search results."
        
        # Filter and sort by relevance
        relevant_results = [r for r in final_results if r['combined_score'] >= self.config.get('relevance_threshold', 0.4)]
        relevant_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        if not relevant_results:
            # Fallback to all results if none meet threshold
            relevant_results = sorted(final_results, key=lambda x: x['combined_score'], reverse=True)
        
        logger.info(f"Found {len(relevant_results)} relevant results out of {len(final_results)} total")
        
        if progress_callback:
            try:
                progress_callback("assistant", f"🧠 Creating intelligent summary...")
            except TypeError:
                try:
                    progress_callback(f"🧠 Creating intelligent summary...")
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
        
        # Create intelligent summary
        if self.config.get('smart_summarization', True):
            summary = self.summarizer.create_summary(
                relevant_results[:5],  # Use top 5 most relevant results
                query,
                max_length=self.config.get('max_summary_length', 1500)
            )
        else:
            # Fallback to basic formatting
            summary = self._create_basic_summary(relevant_results[:3], query)
        
        # Add performance stats
        successful_count = len([r for r in final_results if r['success']])
        stats = f"\n\n---\n📊 **Search Stats**: Found {len(search_results)} results, extracted {successful_count}, {len(relevant_results)} relevant"
        
        if self.config.get('include_timestamps', True):
            stats += f" • {datetime.now().strftime('%H:%M:%S')}"
        
        final_output = summary + stats
        
        # Log the search
        self._log_search(query, final_output, successful_count, len(search_results))
        
        logger.info(f"Intelligent search completed: {len(relevant_results)} relevant results")
        return final_output
    
    def _create_basic_summary(self, results: List[Dict], query: str) -> str:
        """Fallback basic summary format"""
        if not results:
            return "No relevant information found."
        
        summary_parts = [f"## 🔍 Search Results for: {query}\n"]
        
        for i, result in enumerate(results[:3], 1):
            content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
            
            summary_parts.append(
                f"### {i}. [{result['title']}]({result['url']})\n"
                f"{content_preview}\n"
                f"*Relevance: {result.get('combined_score', 0):.2f}*\n"
            )
        
        return '\n'.join(summary_parts)
    
    def _log_search(self, query: str, results: str, successful: int, total: int):
        """Enhanced search logging"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'successful_extractions': successful,
                'total_results': total,
                'success_rate': successful / total if total > 0 else 0,
                'results_length': len(results),
                'intelligent_mode': self.config.get('smart_summarization', True)
            }
            
            log_path = "intelligent_search_log.json"
            log_data = []
            
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                except json.JSONDecodeError:
                    log_data = []
            
            log_data.append(log_entry)
            
            # Keep only last 100 entries
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data[-100:], f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to log search: {e}")
    
    def get_search_stats(self) -> Dict:
        """Get search performance statistics"""
        log_path = "intelligent_search_log.json"
        if not os.path.exists(log_path):
            return {"total_searches": 0, "average_success_rate": 0.0}
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            if not log_data:
                return {"total_searches": 0, "average_success_rate": 0.0}
            
            total_searches = len(log_data)
            avg_success_rate = sum(entry['success_rate'] for entry in log_data) / total_searches
            recent_searches = [entry for entry in log_data if 
                             datetime.now() - datetime.fromisoformat(entry['timestamp']) < timedelta(days=7)]
            
            return {
                "total_searches": total_searches,
                "average_success_rate": avg_success_rate,
                "recent_searches": len(recent_searches),
                "intelligent_mode_usage": sum(1 for entry in log_data if entry.get('intelligent_mode', False))
            }
            
        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {"total_searches": 0, "average_success_rate": 0.0, "error": str(e)}

def get_searcher() -> EnhancedWebSearcher:
    """Get global searcher instance"""
    global _searcher
    if _searcher is None:
        _searcher = EnhancedWebSearcher()
    return _searcher

def web_search(query: str, push_message_func=None) -> str:
    """Main web search function - now with intelligent summarization"""
    searcher = get_searcher()
    return searcher.search(query, push_message_func)

def toggle_auto_search() -> bool:
    """Toggle auto search functionality"""
    searcher = get_searcher()
    searcher.config["auto_search_enabled"] = not searcher.config["auto_search_enabled"]
    searcher._save_config(CONFIG_PATH, searcher.config)
    logger.info(f"Auto search {'enabled' if searcher.config['auto_search_enabled'] else 'disabled'}")
    return searcher.config["auto_search_enabled"]

def toggle_smart_summarization() -> bool:
    """Toggle intelligent summarization"""
    searcher = get_searcher()
    searcher.config["smart_summarization"] = not searcher.config["smart_summarization"]
    searcher._save_config(CONFIG_PATH, searcher.config)
    logger.info(f"Smart summarization {'enabled' if searcher.config['smart_summarization'] else 'disabled'}")
    return searcher.config["smart_summarization"]

def set_relevance_threshold(threshold: float) -> bool:
    """Set the relevance threshold (0.0 to 1.0)"""
    if not 0.0 <= threshold <= 1.0:
        logger.error("Relevance threshold must be between 0.0 and 1.0")
        return False
    
    searcher = get_searcher()
    searcher.config["relevance_threshold"] = threshold
    searcher._save_config(CONFIG_PATH, searcher.config)
    logger.info(f"Relevance threshold set to {threshold}")
    return True

def get_search_config() -> Dict:
    """Get current search configuration"""
    searcher = get_searcher()
    return {
        "auto_search_enabled": searcher.config.get("auto_search_enabled", True),
        "smart_summarization": searcher.config.get("smart_summarization", True),
        "relevance_threshold": searcher.config.get("relevance_threshold", 0.4),
        "max_results": searcher.config.get("max_results", 8),
        "max_summary_length": searcher.config.get("max_summary_length", 1500),
        "cache_enabled": searcher.config.get("cache_enabled", True),
        "use_selenium_fallback": searcher.config.get("use_selenium_fallback", True)
    }

def update_search_config(**kwargs) -> Dict:
    """Update search configuration"""
    searcher = get_searcher()
    
    valid_keys = {
        "auto_search_enabled", "smart_summarization", "relevance_threshold",
        "max_results", "max_summary_length", "cache_enabled", 
        "use_selenium_fallback", "max_content_length", "min_content_length",
        "search_delay_min", "search_delay_max", "page_timeout"
    }
    
    updated = {}
    for key, value in kwargs.items():
        if key in valid_keys:
            searcher.config[key] = value
            updated[key] = value
        else:
            logger.warning(f"Invalid config key: {key}")
    
    if updated:
        searcher._save_config(CONFIG_PATH, searcher.config)
        logger.info(f"Updated config: {updated}")
    
    return updated

def test_intelligent_search():
    """Test function for intelligent search"""
    test_queries = [
        "latest AI developments January 2025",
        "Python async programming best practices",
        "current status of renewable energy adoption",
        "ChatGPT vs Claude comparison 2024",
        "how to improve web scraping performance"
    ]
    
    searcher = get_searcher()
    
    print("🧠 Testing Intelligent Web Search")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 30)
        
        start_time = time.time()
        result = searcher.search(query)
        end_time = time.time()
        
        print(result)
        print(f"\n⏱️ Search completed in {end_time - start_time:.2f} seconds")
        print("=" * 50)
        
        if i < len(test_queries):
            time.sleep(3)  # Delay between tests
    
    # Show stats
    stats = searcher.get_search_stats()
    print(f"\n📊 Search Statistics:")
    print(f"Total searches: {stats.get('total_searches', 0)}")
    print(f"Average success rate: {stats.get('average_success_rate', 0):.2%}")
    print(f"Recent searches (7 days): {stats.get('recent_searches', 0)}")

if __name__ == "__main__":
    # Example usage
    print("🚀 Enhanced Web Search with AI-like Summarization")
    print("=" * 50)
    
    # Show current config
    config = get_search_config()
    print("📋 Current Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    
    # Run test
    test_intelligent_search()