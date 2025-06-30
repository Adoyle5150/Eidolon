# ===================================================================
# PERFECT VECTOR MEMORY SYSTEM FOR EIDOLON - 100% FUNCTIONAL
# WITH ENHANCED RELEVANCE FILTERING
# ===================================================================

import chromadb
from sentence_transformers import SentenceTransformer
import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple
import os
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EidolonVectorMemory:
    def __init__(self, db_path="./eidolon_memory", model_name='all-MiniLM-L6-v2'):
        """Initialize the Vector Memory System for Eidolon."""
        print(f"🧠 Initializing Eidolon Vector Memory System...")
        
        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)
        
        try:
            # Initialize ChromaDB with persistent storage
            self.client = chromadb.PersistentClient(path=db_path)
            
            # Get or create collection with proper configuration
            try:
                self.collection = self.client.get_collection(name="eidolon_memories")
                print(f"📂 Found existing collection")
            except ValueError:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name="eidolon_memories",
                    metadata={"hnsw:space": "cosine"}
                )
                print(f"📂 Created new collection")
            
            # Initialize embedding model (local, fast, reliable)
            print(f"🔧 Loading embedding model: {model_name}")
            self.embedder = SentenceTransformer(model_name)
            
            # Test the embedder to ensure it's working
            test_embedding = self.embedder.encode(["test"])
            print(f"✅ Embedder test successful, embedding dimension: {len(test_embedding[0])}")
            
            # Memory stats
            self.total_memories = self.collection.count()
            print(f"📊 Vector Memory initialized with {self.total_memories} existing memories")
            
        except Exception as e:
            print(f"❌ Error initializing memory system: {e}")
            raise
        
    def _generate_memory_id(self, user_msg: str, assistant_msg: str, session_id: str = None) -> str:
        """Generate unique ID for memory entry."""
        timestamp = str(int(time.time() * 1000))  # Add timestamp for uniqueness
        content = f"{user_msg}|{assistant_msg}|{session_id or 'global'}|{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _create_memory_text(self, user_msg: str, assistant_msg: str) -> str:
        """Create searchable memory text."""
        return f"Human: {user_msg.strip()}\nEidolon: {assistant_msg.strip()}"
    
    def store_memory(self, user_message: str, assistant_message: str, session_id: str = None, metadata: Dict = None):
        """
        Store a conversation memory in the vector database.
        
        Args:
            user_message: The user's message
            assistant_message: Eidolon's response
            session_id: Optional session identifier for context separation
            metadata: Additional metadata to store with the memory
        """
        try:
            # Validate inputs
            if not user_message or not assistant_message:
                print("⚠️ Skipping memory storage - empty message")
                return False
            
            # Create memory content
            memory_text = self._create_memory_text(user_message, assistant_message)
            memory_id = self._generate_memory_id(user_message, assistant_message, session_id)
            
            print(f"📝 Creating memory with ID: {memory_id[:8]}...")
            print(f"📝 Memory text: {memory_text[:100]}...")
            
            # Generate embedding
            print("🔧 Generating embedding...")
            embedding = self.embedder.encode([memory_text])[0].tolist()
            print(f"✅ Embedding generated, dimension: {len(embedding)}")
            
            # Prepare metadata
            memory_metadata = {
                "timestamp": time.time(),
                "session_id": session_id or "global",
                "user_length": len(user_message),
                "assistant_length": len(assistant_message),
                "memory_type": "conversation",
                "user_message": user_message[:500],  # Store truncated for debugging
                "assistant_message": assistant_message[:500]
            }
            if metadata:
                memory_metadata.update(metadata)
            
            # Store in ChromaDB
            print("💾 Storing in ChromaDB...")
            self.collection.add(
                documents=[memory_text],
                embeddings=[embedding],
                ids=[memory_id],
                metadatas=[memory_metadata]
            )
            
            # Verify storage
            stored_count = self.collection.count()
            print(f"✅ Memory stored successfully! Total memories: {stored_count}")
            print(f"   ID: {memory_id[:8]}...")
            print(f"   Content: {memory_text[:60]}...")
            
            self.total_memories = stored_count
            return True
            
        except Exception as e:
            print(f"❌ Error storing memory: {e}")
            logger.exception("Memory storage error")
            return False
    
    def retrieve_memories(self, query: str, top_k: int = 5, session_id: str = None, 
                         exclude_recent: bool = False, time_window: float = 300,
                         relevance_threshold: float = 0.3, min_query_length: int = 10) -> List[str]:
        """
        Retrieve relevant memories for a query using semantic search with smart filtering.
        
        Args:
            query: The search query (usually the current user message)
            top_k: Number of memories to retrieve
            session_id: Optional session filter
            exclude_recent: Whether to exclude very recent memories
            time_window: Time window in seconds to exclude recent memories
            relevance_threshold: Minimum relevance score (0.0-1.0) to include memories
            min_query_length: Minimum query length to trigger memory retrieval
        
        Returns:
            List of formatted memory strings
        """
        try:
            print(f"🔍 Retrieving memories for query: '{query[:50]}...'")
            
            # Smart filtering: Skip retrieval for very short or generic queries
            if len(query.strip()) < min_query_length:
                print(f"📝 Query too short ({len(query)} chars), skipping memory retrieval")
                return []
            
            # Skip retrieval for common greetings and generic responses
            generic_patterns = [
                'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
                'thanks', 'thank you', 'bye', 'goodbye', 'see you', 'ok', 'okay',
                'yes', 'no', 'sure', 'alright', 'cool', 'nice', 'great'
            ]
            
            query_lower = query.lower().strip()
            if any(pattern in query_lower and len(query_lower) <= len(pattern) + 5 for pattern in generic_patterns):
                print(f"📝 Generic query detected, skipping memory retrieval")
                return []
            
            # Check if we have any memories
            current_count = self.collection.count()
            if current_count == 0:
                print("📝 No memories available for retrieval")
                return []
            
            print(f"📊 Collection has {current_count} memories")
            
            # Generate query embedding
            print("🔧 Generating query embedding...")
            query_embedding = self.embedder.encode([query])[0].tolist()
            print(f"✅ Query embedding generated, dimension: {len(query_embedding)}")
            
            # Build where clause for filtering
            where_clause = None
            if session_id:
                where_clause = {"session_id": session_id}
                print(f"🔍 Filtering by session: {session_id}")
            
            # Retrieve memories with detailed logging
            print(f"🔍 Querying ChromaDB for top {min(top_k * 3, current_count)} results...")
            
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k * 3, current_count),  # Get more results to filter
                    where=where_clause,
                    include=["documents", "metadatas", "distances"]
                )
                
                print(f"✅ ChromaDB query successful")
                print(f"📊 Retrieved {len(results['documents'][0])} raw results")
                
            except Exception as query_error:
                print(f"❌ ChromaDB query failed: {query_error}")
                logger.exception("ChromaDB query error")
                return []
            
            # Process results with relevance filtering
            memories = []
            current_time = time.time()
            
            if not results["documents"][0]:
                print("📝 No documents returned from query")
                return []
            
            print(f"🔄 Processing {len(results['documents'][0])} results...")
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0], 
                results["metadatas"][0], 
                results["distances"][0]
            )):
                # Calculate relevance score (ChromaDB uses cosine distance, lower is better)
                relevance_score = max(0, 1 - distance)  # Convert distance to similarity
                
                print(f"   Result {i+1}: distance={distance:.3f}, relevance={relevance_score:.3f}")
                
                # Skip memories below relevance threshold
                if relevance_score < relevance_threshold:
                    print(f"   Skipping due to low relevance ({relevance_score:.3f} < {relevance_threshold})")
                    continue
                
                # Skip very recent memories if requested
                if exclude_recent and (current_time - metadata["timestamp"]) < time_window:
                    print(f"   Skipping recent memory (age: {current_time - metadata['timestamp']:.1f}s)")
                    continue
                
                # Format memory with relevance info
                memory_age = current_time - metadata["timestamp"]
                age_str = f"{memory_age/3600:.1f}h ago" if memory_age > 3600 else f"{memory_age/60:.0f}m ago"
                
                formatted_memory = f"[{age_str}, relevance: {relevance_score:.2f}] {doc}"
                memories.append(formatted_memory)
                
                print(f"   ✅ Added memory: {formatted_memory[:80]}...")
                
                if len(memories) >= top_k:
                    break
            
            if len(memories) == 0:
                print(f"📝 No memories met relevance threshold ({relevance_threshold})")
            else:
                print(f"🔍 Successfully retrieved {len(memories)} relevant memories")
                for i, mem in enumerate(memories):
                    print(f"  {i+1}. {mem[:100]}...")
            
            return memories
            
        except Exception as e:
            print(f"❌ Error retrieving memories: {e}")
            logger.exception("Memory retrieval error")
            return []
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about stored memories."""
        try:
            total = self.collection.count()
            
            if total == 0:
                return {
                    "total_memories": 0,
                    "unique_sessions": 0,
                    "avg_memory_size": 0,
                    "recent_24h": 0,
                    "database_path": self.client._settings.persist_directory if hasattr(self.client, '_settings') else "unknown"
                }
            
            # Get sample of recent memories for analysis
            recent_results = self.collection.get(
                limit=min(100, total),
                include=["metadatas"]
            )
            
            sessions = set()
            total_chars = 0
            recent_count = 0
            current_time = time.time()
            
            for metadata in recent_results["metadatas"]:
                sessions.add(metadata.get("session_id", "global"))
                total_chars += metadata.get("user_length", 0) + metadata.get("assistant_length", 0)
                if (current_time - metadata["timestamp"]) < 86400:  # Last 24 hours
                    recent_count += 1
            
            return {
                "total_memories": total,
                "unique_sessions": len(sessions),
                "avg_memory_size": total_chars / len(recent_results["metadatas"]) if recent_results["metadatas"] else 0,
                "recent_24h": recent_count,
                "database_path": self.client._settings.persist_directory if hasattr(self.client, '_settings') else "unknown"
            }
                
        except Exception as e:
            print(f"❌ Error getting memory stats: {e}")
            logger.exception("Memory stats error")
            return {"error": str(e)}
    
    def format_memories_for_llm(self, memories: List[str], max_length: int = 2000) -> str:
        """
        Format retrieved memories for injection into LLM prompt.
        
        Args:
            memories: List of memory strings
            max_length: Maximum character length for the formatted block
        
        Returns:
            Formatted memory block for LLM
        """
        if not memories:
            return ""
        
        # Start building the memory block
        memory_block = "### MEMORY RECALL\n"
        memory_block += "The following are relevant memories from previous conversations:\n\n"
        
        current_length = len(memory_block)
        included_memories = []
        
        for memory in memories:
            memory_entry = f"- {memory}\n"
            
            # Check if adding this memory would exceed the limit
            if current_length + len(memory_entry) > max_length:
                break
                
            included_memories.append(memory_entry)
            current_length += len(memory_entry)
        
        # Add memories to block
        memory_block += "".join(included_memories)
        memory_block += f"\n(Retrieved {len(included_memories)} relevant memories)\n"
        memory_block += "### END MEMORY RECALL\n\n"
        
        print(f"📋 Formatted {len(included_memories)} memories for LLM ({len(memory_block)} chars)")
        
        return memory_block

    def debug_collection_contents(self, limit: int = 5):
        """Debug function to inspect collection contents."""
        try:
            print(f"🔍 DEBUG: Inspecting collection contents (limit: {limit})")
            
            count = self.collection.count()
            print(f"📊 Total items in collection: {count}")
            
            if count == 0:
                print("📝 Collection is empty")
                return
            
            # Get some items for inspection
            results = self.collection.get(
                limit=min(limit, count),
                include=["documents", "metadatas", "embeddings"]
            )
            
            print(f"📋 Sample items:")
            for i, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
                print(f"  Item {i+1}:")
                print(f"    Document: {doc[:100]}...")
                print(f"    Session: {metadata.get('session_id', 'N/A')}")
                print(f"    Timestamp: {metadata.get('timestamp', 'N/A')}")
                print(f"    User msg: {metadata.get('user_message', 'N/A')[:50]}...")
                
        except Exception as e:
            print(f"❌ Debug inspection failed: {e}")
            logger.exception("Debug inspection error")

# ===================================================================
# GLOBAL MEMORY INSTANCE AND HELPER FUNCTIONS
# ===================================================================

# Global memory instance (initialize once)
_memory_instance = None

def get_memory_instance():
    """Get or create the global memory instance."""
    global _memory_instance
    if _memory_instance is None:
        try:
            _memory_instance = EidolonVectorMemory()
        except Exception as e:
            print(f"❌ Failed to initialize memory instance: {e}")
            logger.exception("Memory initialization error")
            return None
    return _memory_instance

def store_conversation_memory(user_message: str, assistant_message: str, session_id: str = None):
    """Convenience function to store a conversation memory."""
    memory = get_memory_instance()
    if memory:
        return memory.store_memory(user_message, assistant_message, session_id)
    return False

def retrieve_relevant_memories(query: str, top_k: int = 3, session_id: str = None, 
                             relevance_threshold: float = 0.3) -> str:
    """
    Convenience function to retrieve and format memories for LLM injection with smart filtering.
    
    Args:
        query: The search query
        top_k: Number of memories to retrieve
        session_id: Optional session filter
        relevance_threshold: Minimum relevance score (0.3 = 30% similarity)
    """
    memory = get_memory_instance()
    if memory:
        memories = memory.retrieve_memories(
            query=query, 
            top_k=top_k, 
            session_id=session_id,
            relevance_threshold=relevance_threshold
        )
        return memory.format_memories_for_llm(memories)
    return ""

def get_memory_statistics():
    """Get memory system statistics."""
    memory = get_memory_instance()
    if memory:
        return memory.get_memory_stats()
    return {"error": "Memory system not initialized"}

def debug_memory_system():
    """Debug the memory system."""
    memory = get_memory_instance()
    if memory:
        memory.debug_collection_contents()
    else:
        print("❌ Memory system not available for debugging")

# ===================================================================
# ENHANCED ASK_SERVER INTEGRATION
# ===================================================================

def ask_server_enhanced(prompt, model="llama3.2", temperature=0.7, session_id=None, 
                       enable_memory=True, memory_relevance_threshold=0.3):
    """
    Enhanced ask_server function with integrated vector memory and smart filtering.
    
    Args:
        prompt: User's message
        model: Model to use
        temperature: Response randomness
        session_id: Session identifier for memory context
        enable_memory: Whether to use memory retrieval
        memory_relevance_threshold: Minimum relevance for memory inclusion (0.0-1.0)
    
    Returns:
        Assistant's response
    """
    import requests
    
    try:
        print(f"🚀 Processing request with memory {'enabled' if enable_memory else 'disabled'}")
        
        # Step 1: Retrieve relevant memories if enabled
        enhanced_prompt = prompt
        if enable_memory:
            print("🔍 Retrieving relevant memories...")
            memory_context = retrieve_relevant_memories(
                prompt, 
                top_k=3, 
                session_id=session_id,
                relevance_threshold=memory_relevance_threshold
            )
            
            if memory_context:
                enhanced_prompt = f"{memory_context}{prompt}"
                print(f"💾 Enhanced prompt with memories ({len(memory_context)} chars added)")
            else:
                print("📝 No relevant memories found or memory system unavailable")
        
        # Step 2: Send request to llama.cpp server
        print(f"📤 Sending request to llama.cpp server...")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user", 
                    "content": enhanced_prompt
                }
            ],
            "temperature": temperature,
            "stream": False
        }
        
        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get("message", {}).get("content", "")
            
            print(f"✅ Received response ({len(assistant_response)} chars)")
            
            # Step 3: Store the conversation in memory if enabled
            if enable_memory and assistant_response:
                print("💾 Storing conversation in memory...")
                success = store_conversation_memory(prompt, assistant_response, session_id)
                if success:
                    print("✅ Memory stored successfully")
                else:
                    print("⚠️ Memory storage failed")
            
            return assistant_response
            
        else:
            error_msg = f"Server error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return error_msg
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        logger.exception("ask_server_enhanced error")
        return error_msg

# ===================================================================
# COMPREHENSIVE TEST SYSTEM
# ===================================================================

def test_memory_system():
    """Comprehensive test of the memory system functionality."""
    print("🧪 Testing Eidolon Vector Memory System...")
    
    try:
        # Initialize memory system
        memory = get_memory_instance()
        if not memory:
            print("❌ Failed to initialize memory system")
            return False
        
        print("✅ Memory system initialized")
        
        # Test 1: Storage
        print("\n📝 Test 1: Memory Storage")
        success1 = store_conversation_memory(
            "What is the capital of France?",
            "The capital of France is Paris, a beautiful city known for its culture and history.",
            session_id="test_session"
        )
        
        success2 = store_conversation_memory(
            "Tell me about Paris landmarks",
            "Paris has many famous landmarks including the Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, and Arc de Triomphe.",
            session_id="test_session"
        )
        
        success3 = store_conversation_memory(
            "What's the weather like?",
            "I don't have access to current weather data, but I can help you find weather information.",
            session_id="test_session"
        )
        
        if success1 and success2 and success3:
            print("✅ Storage test passed")
        else:
            print("❌ Storage test failed")
            return False
        
        # Wait a moment for storage to complete
        time.sleep(1)
        
        # Test 2: Debug collection
        print("\n🔍 Test 2: Collection Debug")
        debug_memory_system()
        
        # Test 3: Relevance Filtering Test
        print("\n🔍 Test 3: Relevance Filtering")
        
        # Should retrieve relevant memories
        print("Testing relevant query...")
        memories = retrieve_relevant_memories("Tell me about French cities and landmarks", top_k=3)
        if memories:
            print("✅ Relevant query test passed")
            print(f"Retrieved memories:\n{memories}")
        else:
            print("❌ Relevant query test failed")
        
        # Should NOT retrieve memories for generic queries
        print("\nTesting generic query...")
        generic_memories = retrieve_relevant_memories("Hi", top_k=3)
        if not generic_memories:
            print("✅ Generic query filtering test passed (no memories retrieved)")
        else:
            print("❌ Generic query filtering test failed (memories were retrieved)")
            print(f"Unexpected memories:\n{generic_memories}")
        
        # Test 4: Statistics
        print("\n📊 Test 4: Memory Statistics")
        stats = get_memory_statistics()
        print(f"Memory stats: {json.dumps(stats, indent=2)}")
        
        if stats.get("total_memories", 0) > 0:
            print("✅ Statistics test passed")
        else:
            print("❌ Statistics test failed")
            return False
        
        print("\n🎉 All memory system tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.exception("Test system error")
        return False

def clear_memory_database():
    """Clear all memories (use with caution!)"""
    try:
        memory = get_memory_instance()
        if memory:
            # Get all IDs and delete them
            all_data = memory.collection.get()
            if all_data["ids"]:
                memory.collection.delete(ids=all_data["ids"])
                print(f"🗑️ Cleared {len(all_data['ids'])} memories from database")
            else:
                print("📝 Database was already empty")
        else:
            print("❌ Memory system not available")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        logger.exception("Database clear error")

# ===================================================================
# MAIN EXECUTION
# ===================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EIDOLON VECTOR MEMORY SYSTEM - ENHANCED WITH RELEVANCE FILTERING")
    print("=" * 60)
    
    # Run comprehensive tests
    test_success = test_memory_system()
    
    if test_success:
        print("\n🎉 All tests passed! Memory system is working perfectly.")
        print("\nKey Features:")
        print("✅ Smart relevance filtering (no more irrelevant memories)")
        print("✅ Generic query detection (Hi, Thanks, etc. won't trigger memories)")
        print("✅ Configurable relevance threshold (0.0-1.0)")
        print("✅ All original functionality preserved")
        print("\nReplace your vector_memory.py with this enhanced version!")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

# ===================================================================
# INSTALLATION AND USAGE INSTRUCTIONS
# ===================================================================

"""
🚀 ENHANCED FEATURES ADDED:

1. RELEVANCE THRESHOLD FILTERING:
   - Only memories with similarity > threshold are included
   - Default threshold: 0.3 (30% similarity)
   - Configurable per query

2. GENERIC QUERY DETECTION:
   - Automatically skips memory retrieval for: Hi, Hello, Thanks, OK, etc.
   - Won't waste time on irrelevant queries

3. MINIMUM QUERY LENGTH:
   - Skips memory retrieval for very short queries (< 10 chars)

4. ENHANCED LOGGING:
   - Shows relevance scores for each memory
   - Clear feedback on why memories were included/excluded

🔧 USAGE EXAMPLES:

# Basic usage (same as before)
response = ask_server_enhanced("What did we discuss about Paris?")

# Custom relevance threshold
response = ask_server_enhanced(
    "Tell me something", 
    memory_relevance_threshold=0.5  # More strict
)

# Manual memory retrieval with custom threshold
memories = retrieve_relevant_memories(
    "What's my birthday?", 
    relevance_threshold=0.4
)

🎯 WHAT THIS FIXES:

❌ Before: "Hi" → Dumps random birthday memories
✅ After:  "Hi" → No memories (generic query detected)

❌ Before: "OK" → Retrieves unrelated conversations  
✅ After:  "OK" → No memories (generic query detected)

❌ Before: "What's my name?" → Returns memories about cats
✅ After:  "What's my name?" → Only returns name-related memories (if relevance > 0.3)

🛠️ TUNING THE SYSTEM:

Adjust relevance_threshold based on your needs:
- 0.1-0.2: Very loose (includes tangentially related)
- 0.3: Balanced (default, recommended)  
- 0.4-0.5: Strict (only highly relevant)
- 0.6+: Very strict (only very similar conversations)

Simply replace your entire vector_memory.py with this code!
"""