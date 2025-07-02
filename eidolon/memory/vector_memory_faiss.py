# eidolon/memory/vector_memory_faiss.py

import faiss
import numpy as np
import os
import json
from sentence_transformers import SentenceTransformer
import threading

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

def retrieve_relevant_memories(query, top_k=5):
    """Retrieve top_k relevant memories for a query."""
    with lock:
        if index.ntotal == 0:
            return ""
        query_emb = model.encode([query])[0]
        norm = np.linalg.norm(query_emb)
        if norm != 0:
            query_emb = query_emb / norm
        D, I = index.search(np.array([query_emb], dtype=np.float32), k=top_k)
        results = [metadata[i] for i in I[0] if i < len(metadata)]
        return "\n".join(results)
