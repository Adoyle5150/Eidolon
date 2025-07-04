# Eidolon Memory Module 

# Import vector memory functionality
from .vector_memory_faiss import (
    store_memory,
    retrieve_relevant_memories,
    save_index
)

# Create a vector_memory object that provides the main interface
class VectorMemory:
    """Vector memory interface for storing and retrieving semantic memories."""
    
    def store(self, text):
        """Store text in vector memory."""
        return store_memory(text)
    
    def retrieve(self, query, top_k=5, similarity_threshold=0.3, max_results=3):
        """Retrieve relevant memories for a query."""
        return retrieve_relevant_memories(query, top_k, similarity_threshold, max_results)
    
    def save(self):
        """Save the current index and metadata."""
        return save_index()

# Create a singleton instance
vector_memory = VectorMemory()

# Also expose the functions directly for backward compatibility
__all__ = [
    'vector_memory',
    'store_memory',
    'retrieve_relevant_memories',
    'save_index',
    'VectorMemory'
] 