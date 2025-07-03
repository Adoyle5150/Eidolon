# eidolon/memory/vector_memory_faiss.py

import faiss
import numpy as np
import os
import json
from sentence_transformers import SentenceTransformer
import threading
from difflib import SequenceMatcher

# Load local embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# File paths for persistence
index_file = "data/eidolon_vectors.index"
meta_file = "data/eidolon_vectors_meta.json"

# Load or initialize FAISS index
dimension = 384  # all-MiniLM-L6-v2 output dimension
if os.path.exists(index_file):
    index = faiss.read_index(index_file)
else:
    index = faiss.IndexFlatIP(dimension)

# Load or initialize metadata
if os.path.exists(meta_file):
    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
else:
    metadata = []

lock = threading.Lock()

def save_index():
    faiss.write_index(index, index_file)
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def store_memory(text):
    """Add text to the vector store with semantic embedding."""
    with lock:
        embedding = model.encode([text])[0]
        norm = np.linalg.norm(embedding)
        if norm != 0:
            embedding = embedding / norm
        index.add(np.array([embedding], dtype=np.float32))
        metadata.append(text)
        save_index()
        print(f"✅ Stored in FAISS vector memory: {text[:50]}...")

def _similarity_ratio(text1, text2):
    """Calculate similarity ratio between two texts using SequenceMatcher."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def _deduplicate_memories(memories, similarity_threshold=0.8):
    """
    Remove duplicate or highly similar memories.
    Returns a list of unique memories with lower similarity removed.
    """
    if not memories:
        return []
    
    unique_memories = []
    for memory in memories:
        # Check if this memory is too similar to any already selected memory
        is_duplicate = False
        for existing in unique_memories:
            if _similarity_ratio(memory, existing) > similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_memories.append(memory)
    
    return unique_memories

def retrieve_relevant_memories(query, top_k=5, similarity_threshold=0.3, max_results=3):
    """
    Retrieve top_k relevant memories for a query with deduplication and filtering.
    
    Args:
        query: The search query
        top_k: Maximum number of memories to retrieve from FAISS
        similarity_threshold: Minimum similarity score to include (0.0 to 1.0)
        max_results: Maximum number of final results to return
    
    Returns:
        Formatted string of relevant memories or empty string if none found
    """
    with lock:
        if index.ntotal == 0:
            return ""
        
        # Encode query
        query_emb = model.encode([query])[0]
        norm = np.linalg.norm(query_emb)
        if norm != 0:
            query_emb = query_emb / norm
        
        # Search for top_k results with similarity scores
        D, I = index.search(np.array([query_emb], dtype=np.float32), k=min(top_k, index.ntotal))
        
        # Filter results by similarity threshold and get unique memories
        relevant_memories = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(metadata) and score >= similarity_threshold:
                relevant_memories.append(metadata[idx])
        
        # Deduplicate memories
        unique_memories = _deduplicate_memories(relevant_memories, similarity_threshold=0.8)
        
        # Limit to max_results
        final_memories = unique_memories[:max_results]
        
        if not final_memories:
            return ""
        
        # Format memories clearly
        formatted_memories = []
        for i, memory in enumerate(final_memories, 1):
            # Clean up the memory text
            clean_memory = memory.strip()
            if clean_memory:
                formatted_memories.append(f"Memory {i}: {clean_memory}")
        
        result = "\n".join(formatted_memories)
        
        print(f"🧠 Retrieved {len(final_memories)} relevant memories (from {len(relevant_memories)} candidates)")
        return result
