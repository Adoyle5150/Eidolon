# eidolon_vector.py

"""
Eidolon - Vector Memory Management

Handles:
- Storing text embeddings for conversation memory
- Retrieving top-K relevant memories using vector similarity
"""

import os
import json
import numpy as np

# === Configuration ===

VECTOR_DB_DIR = "vector_db"
EMBEDDING_DIM = 384  # adjust based on your embedding model

# === Utilities ===

def _sanitize_filename(name):
    """Sanitize a string for safe filesystem usage."""
    return name.replace(' ', '_').replace('/', '_').replace('\\', '_').replace(':', '-')

def _cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# === Embedding Operations ===

def embed_text(text):
    """
    Embed text using your local embedding model or API.
    Replace with your embedding method.
    """
    import hashlib
    # For placeholder, return a deterministic pseudo-embedding:
    hash_digest = hashlib.sha256(text.encode()).digest()
    return np.frombuffer(hash_digest, dtype=np.uint8)[:EMBEDDING_DIM].astype(np.float32)

# === Store Memory ===

def store_memory(prompt, reply):
    """
    Store a prompt and reply as a memory embedding for future retrieval.
    """
    try:
        os.makedirs(VECTOR_DB_DIR, exist_ok=True)
        combined_text = f"User: {prompt}\nAssistant: {reply}"
        embedding = embed_text(combined_text)

        entry = {
            "text": combined_text,
            "embedding": embedding.tolist()
        }

        file_name = _sanitize_filename(datetime.now().isoformat()) + ".json"
        file_path = os.path.join(VECTOR_DB_DIR, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

        print(f"🧠 Stored memory in {file_path}")

    except Exception as e:
        print(f"❌ Failed to store memory: {e}")

# === Query Memory ===

def query_memory(prompt, top_k=5):
    """
    Retrieve top-k relevant memories for a given prompt.
    """
    try:
        prompt_embedding = embed_text(prompt)

        similarities = []
        for fname in os.listdir(VECTOR_DB_DIR):
            fpath = os.path.join(VECTOR_DB_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                    entry_embedding = np.array(entry["embedding"], dtype=np.float32)
                    similarity = _cosine_similarity(prompt_embedding, entry_embedding)
                    similarities.append((similarity, entry["text"]))
            except Exception as e:
                print(f"⚠️ Failed to read {fpath}: {e}")
                continue

        # Sort by similarity
        similarities.sort(reverse=True, key=lambda x: x[0])

        # Return top-k
        top_memories = [text for _, text in similarities[:top_k]]
        print(f"🔍 Retrieved {len(top_memories)} relevant memories for context injection")
        return top_memories

    except Exception as e:
        print(f"❌ Memory query failed: {e}")
        return []

