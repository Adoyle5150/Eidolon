import re
from datetime import datetime
from typing import Set  # ✅ Add this



# Global searcher instance
_searcher = None

class ContentAnalyzer:
    """Analyzes content for relevance, recency, and quality"""
    
    def __init__(self):
        # Keywords that indicate recency
        self.recency_indicators = {
            'very_recent': ['today', 'now', 'currently', 'latest', 'breaking', 'just announced', 'this morning', 'this week'],
            'recent': ['recently', 'new', 'updated', '2024', '2025', 'this year', 'this month'],
            'dated': ['yesterday', 'last week', 'last month', 'earlier'],
            'old': ['2023', '2022', '2021', 'years ago', 'previously', 'historical']
        }
        
        # Common stop words to ignore in relevance scoring
        self.stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        ])
    
    def extract_query_terms(self, query: str) -> Set[str]:
        """Extract meaningful terms from search query"""
        # Remove common search operators and clean
        query = re.sub(r'["\-+]', ' ', query.lower())
        terms = set()
        
        for word in query.split():
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 2 and word not in self.stop_words:
                terms.add(word)
        
        return terms
    
    def calculate_relevance_score(self, content: str, title: str, query_terms: Set[str]) -> float:
        """Calculate relevance score based on term frequency and position"""
        if not content or not query_terms:
            return 0.0
        
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Count term occurrences
        title_matches = sum(1 for term in query_terms if term in title_lower)
        content_matches = sum(content_lower.count(term) for term in query_terms)
        
        # Calculate scores
        title_score = (title_matches / len(query_terms)) * 2.0  # Title matches are weighted more
        content_score = min(content_matches / len(content.split()) * 100, 1.0)  # Normalize by content length
        
        # Check for exact phrase matches
        query_phrase = ' '.join(query_terms)
        if query_phrase in content_lower:
            content_score += 0.3
        if query_phrase in title_lower:
            title_score += 0.5
        
        return min(title_score + content_score, 1.0)
    
    def calculate_recency_score(self, content: str, title: str) -> float:
        """Calculate recency score based on temporal indicators"""
        text = (title + ' ' + content).lower()
        
        # Check for date patterns
        current_year = datetime.now().year
        year_pattern = r'\b(20\d{2})\b'
        years_found = re.findall(year_pattern, text)
        
        recency_score = 0.5  # Default neutral score
        
        # Score based on years mentioned
        if years_found:
            latest_year = max(int(year) for year in years_found)
            year_diff = current_year - latest_year
            if year_diff == 0:
                recency_score += 0.4
            elif year_diff == 1:
                recency_score += 0.2
            elif year_diff > 2:
                recency_score -= 0.2
        
        # Score based on recency indicators
        for category, indicators in self.recency_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    if category == 'very_recent':
                        recency_score += 0.3
                    elif category == 'recent':
                        recency_score += 0.2
                    elif category == 'dated':
                        recency_score -= 0.1
                    elif category == 'old':
                        recency_score -= 0.3
                    break
        
        return max(0.0, min(1.0, recency_score))
    
    def calculate_quality_score(self, content: str, title: str) -> float:
        """Calculate content quality score"""
        if not content:
            return 0.0
        
        quality_score = 0.5  # Base score
        
        # Length indicators
        word_count = len(content.split())
        if 50 <= word_count <= 1000:
            quality_score += 0.2
        elif word_count > 1000:
            quality_score += 0.1
        else:
            quality_score -= 0.1
        
        # Structure indicators
        sentence_count = len(re.split(r'[.!?]+', content))
        if sentence_count > 3:
            quality_score += 0.1
        
        # Professional writing indicators
        professional_indicators = ['according to', 'research shows', 'study found', 'experts say', 'data indicates']
        for indicator in professional_indicators:
            if indicator in content.lower():
                quality_score += 0.1
                break
        
        # Spam indicators (negative scoring)
        spam_indicators = ['click here', 'buy now', 'limited time', 'act fast', 'call now']
        for indicator in spam_indicators:
            if indicator in content.lower():
                quality_score -= 0.2
                break
        
        return max(0.0, min(1.0, quality_score))
