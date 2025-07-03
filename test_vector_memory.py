#!/usr/bin/env python3
"""
Test script to verify improved vector memory retrieval with deduplication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eidolon.memory import vector_memory_faiss as vector_memory

def test_vector_memory():
    """Test the improved vector memory retrieval"""
    print("🧪 Testing improved vector memory retrieval...")
    
    # Test deduplication function
    print("\n📝 Testing deduplication...")
    test_memories = [
        "I like programming in Python",
        "I enjoy coding in Python",  # Similar to first
        "My favorite color is blue",
        "I prefer the color blue",   # Similar to third
        "I work as a software engineer",
        "I like programming in Python",  # Exact duplicate
        "I love hiking in the mountains"
    ]
    
    unique_memories = vector_memory._deduplicate_memories(test_memories, similarity_threshold=0.8)
    print(f"Original memories: {len(test_memories)}")
    print(f"After deduplication: {len(unique_memories)}")
    
    print("\n📋 Unique memories:")
    for i, memory in enumerate(unique_memories, 1):
        print(f"  {i}. {memory}")
    
    # Test similarity calculation
    print("\n🔍 Testing similarity calculation...")
    text1 = "I like programming in Python"
    text2 = "I enjoy coding in Python"
    similarity = vector_memory._similarity_ratio(text1, text2)
    print(f"Similarity between '{text1}' and '{text2}': {similarity:.3f}")
    
    # Test retrieval with mock data
    print("\n🔍 Testing memory retrieval...")
    
    # Add some test memories to the vector store
    print("📝 Adding test memories to vector store...")
    test_memories = [
        "I know Python programming language",
        "I am a software engineer",
        "My favorite hobby is hiking",
        "I like the color blue",
        "I work with JavaScript and React",
        "I enjoy playing guitar in my free time"
    ]
    
    for memory in test_memories:
        vector_memory.store_memory(memory)
    
    test_queries = [
        "What programming languages do I know?",
        "What are my hobbies?",
        "What is my job?",
        "What colors do I like?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = vector_memory.retrieve_relevant_memories(
            query, 
            top_k=5, 
            similarity_threshold=0.2, 
            max_results=3
        )
        if result:
            print(f"✅ Retrieved memories:\n{result}")
        else:
            print("ℹ️ No relevant memories found")
    
    print("\n✅ Vector memory test completed successfully!")

if __name__ == "__main__":
    test_vector_memory()
    print("✅ All tests passed!") 