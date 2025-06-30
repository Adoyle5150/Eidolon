import re
from typing import List, Dict, Set
from web.analyzer import ContentAnalyzer


class IntelligentSummarizer:
    """Summarizes and prioritizes content intelligently"""
    
    def __init__(self, analyzer: ContentAnalyzer):
        self.analyzer = analyzer
    
    def extract_key_sentences(self, content: str, query_terms: Set[str], max_sentences: int = 4) -> List[str]:
        """Extract the most relevant sentences from content"""
        if not content:
            return []
        
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return []
        
        # Score each sentence
        sentence_scores = []
        for sentence in sentences:
            score = 0.0
            sentence_lower = sentence.lower()
            
            # Term frequency scoring
            term_matches = sum(1 for term in query_terms if term in sentence_lower)
            score += (term_matches / len(query_terms)) * 2.0
            
            # Position scoring (earlier sentences often more important)
            position_score = 1.0 - (sentences.index(sentence) / len(sentences)) * 0.3
            score += position_score * 0.5
            
            # Length scoring (prefer medium-length sentences)
            word_count = len(sentence.split())
            if 10 <= word_count <= 30:
                score += 0.3
            elif word_count > 50:
                score -= 0.2
            
            sentence_scores.append((sentence, score))
        
        # Sort by score and return top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        return [sentence for sentence, _ in sentence_scores[:max_sentences]]
    
    def create_summary(self, results: List[Dict], query: str, max_length: int = 1500) -> str:
        """Create an intelligent summary from search results"""
        if not results:
            return "No relevant information found."
        
        query_terms = self.analyzer.extract_query_terms(query)
        
        # Collect key information from all sources
        key_points = []
        sources_used = []
        
        for result in results:
            if not result.get('success') or not result.get('content'):
                continue
            
            # Extract key sentences
            key_sentences = self.extract_key_sentences(
                result['content'], 
                query_terms, 
                max_sentences=2
            )
            
            if key_sentences:
                # Format with source attribution
                source_info = f"[{result['title']}]({result['url']})"
                for sentence in key_sentences:
                    key_points.append(f"• {sentence.strip()}")
                
                if source_info not in sources_used:
                    sources_used.append(source_info)
        
        if not key_points:
            return "No relevant information could be extracted from the search results."
        
        # Build summary
        summary_parts = []
        
        # Add direct answer section
        summary_parts.append(f"## 🎯 Key Information about: {query}")
        
        # Add key points (limit to prevent too long summaries)
        current_length = 0
        included_points = []
        
        for point in key_points[:8]:  # Limit to top 8 points
            if current_length + len(point) < max_length * 0.8:  # Reserve space for sources
                included_points.append(point)
                current_length += len(point)
            else:
                break
        
        if included_points:
            summary_parts.append('\n'.join(included_points))
        
        # Add sources section
        if sources_used:
            summary_parts.append("\n## 📚 Sources")
            for i, source in enumerate(sources_used[:5], 1):  # Limit to 5 sources
                summary_parts.append(f"{i}. {source}")
        
        return '\n\n'.join(summary_parts)