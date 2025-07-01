# eidolon/core/prompt_processor.py

import re
import os
import traceback

from datetime import datetime

from eidolon.core.ai_handler import ask_server
from eidolon.core.state_manager import set_assistant_state
from eidolon.utils.helpers import is_valid_python
from web.searcher import web_search


from eidolon.memory.chat_storage import save_current_chat


WEB_SEARCH_AVAILABLE = True  # or False if you want to disable




def process_prompt(prompt, app_context):
    print(f"🚀 Processing prompt: {prompt[:50]}...")
    print(f"🔧 App context - chat_name: {app_context.current_chat_name}, has_push_func: {app_context.push_message_func is not None}, has_gui: {app_context.gui is not None}")

    # Local imports to avoid circular dependency
    try:
        import commands
        # Handle local commands first
        local_response = commands.handle_commands(prompt)
        if local_response:
            if app_context.push_message_func:
                app_context.push_message_func("assistant", "🤖 " + local_response)
            return
    except ImportError:
        print("⚠️ Commands module not found, skipping command handling")

    # Set thinking state
    print("⚙️ Setting state: thinking (generating tokens)")
    try:
        set_assistant_state("thinking", qml_bridge=app_context.qml_bridge, root=None)
    except Exception as e:
        print(f"⚠️ Error setting assistant state: {e}")
    
    if app_context.gui:
        try:
            app_context.gui.set_typing(True)
        except Exception as e:
            print(f"⚠️ Error setting GUI typing state: {e}")

    # Add user prompt to history
    app_context.chat_history.append({"role": "user", "content": prompt})
    if len(app_context.chat_history) > 40:
        app_context.chat_history = app_context.chat_history[-40:]

    # Check if search is needed
    search_keywords = [
        "latest", "recent", "current", "today", "now", "2024", "2025", "2026",
        "news", "update", "what happened", "status", "developments", "breaking",
        "this year", "this month", "this week", "new", "happening",
        "price", "stock", "weather", "score", "result", "winner",
        "who won", "what's", "search for", "find", "look up"
    ]
    urgent_keywords = [
        "breaking", "urgent", "emergency", "alert", "crisis",
        "just happened", "right now", "live", "real time"
    ]

    needs_search = any(keyword in prompt.lower() for keyword in search_keywords)
    is_urgent = any(keyword in prompt.lower() for keyword in urgent_keywords)

    if not needs_search:
        search_patterns = [
            r'\b(what|who|where|when|how|why)\s+(is|are|was|were|did|does|do)\b.*\b(now|today|currently|recent|latest)\b',
            r'\b(current|latest|recent|new|updated)\b.*\b(information|data|news|report|study)\b',
            r'\b(happening|going on|occurring)\b.*\b(now|today|recently)\b',
            r'\b(price|cost|value)\b.*\b(today|now|current|latest)\b'
        ]
        needs_search = any(re.search(pattern, prompt.lower()) for pattern in search_patterns)

    # Get model reply
    try:
        reply = ask_server(app_context.chat_history)
    except Exception as e:
        print(f"❌ Error getting server reply: {e}")
        reply = "I apologize, but I encountered an error while processing your request. Please try again."
    
    search_performed = False

    # Handle web search
    if ("<search>" in reply or needs_search) and WEB_SEARCH_AVAILABLE:
        search_query = _extract_search_query(reply, prompt, needs_search)
        if search_query:
            search_performed = _perform_web_search(search_query, prompt, app_context)
            if search_performed:
                reply = _get_search_enhanced_reply(search_query, prompt, app_context)
            else:
                reply = _handle_search_failure(reply, search_query, prompt, app_context)
    elif "<search>" in reply and not WEB_SEARCH_AVAILABLE:
        reply = _handle_search_unavailable(reply)
    elif needs_search and not search_performed and "<search>" not in reply:
        reply = _handle_fallback_search(reply, prompt, app_context)

    # Fallback reply
    if not reply or not reply.strip():
        reply = "I apologize, but I wasn't able to generate a proper response. Could you please rephrase your question?"

    # Auto-rename chat if still called 'Untitled'
    _auto_rename_chat(prompt, app_context)

    # Save chat data
    _save_chat_data(app_context)

    # Send to UI
    _send_response_to_ui(reply, app_context)

    if app_context.gui:
        try:
            app_context.gui.set_typing(False)
        except Exception as e:
            print(f"⚠️ Error setting GUI typing state: {e}")

def _extract_search_query(reply, prompt, needs_search):
    """Extract search query from reply or construct from prompt"""
    search_query = None
    
    if "<search>" in reply:
        search_match = re.search(r"<search>(.*?)</search>", reply, re.DOTALL)
        if search_match:
            search_query = search_match.group(1).strip()
    
    if not search_query and needs_search:
        search_query = prompt
        search_query = re.sub(r'\b(please|can you|could you|tell me|explain|what is|who is|where is|when is|how is|why is)\b', '', search_query, flags=re.IGNORECASE)
        search_query = re.sub(r'\?', '', search_query).strip()
        
        if any(word in search_query.lower() for word in ['latest', 'current', 'recent', 'now', 'today']):
            search_query += " 2025"
    
    return search_query


def _perform_web_search(search_query, prompt, app_context):
    """Perform web search and return success status"""
    print(f"🔍 Searching for: {search_query}")
    
    if app_context.push_message_func:
        try:
            app_context.push_message_func("assistant", f"🔎 Searching the web for: \"{search_query}\"...")
        except Exception as e:
            print(f"⚠️ Push message error: {e}")

    try:
        search_results = web_search(search_query, app_context.push_message_func)
        
        if search_results and not search_results.startswith("❌") and not search_results.startswith("🔒"):
            print("✅ Web search successful, processing results...")
            if app_context.push_message_func:
                try:
                    app_context.push_message_func("assistant", "🧠 Processing search results and generating response...")
                except Exception as e:
                    print(f"⚠️ Push message error: {e}")
            
            # Store search results in chat history
            if len(app_context.chat_history) >= 2 and app_context.chat_history[-2].get("role") == "system" and "search" in app_context.chat_history[-2].get("content", "").lower():
                app_context.chat_history.pop(-2)
            
            app_context.chat_history.append({"role": "assistant", "content": f"Here are the web search results for '{search_query}':\n\n{search_results}"})
            return True
        else:
            print(f"❌ Web search failed: {search_results}")
            return False
            
    except Exception as e:
        print(f"❌ Web search failed with exception: {e}")
        return False


def _get_search_enhanced_reply(search_query, prompt, app_context):
    """Get enhanced reply using search results"""
    search_context = f"""You searched for: "{search_query}"

Here are the current web search results:

{app_context.chat_history[-1]['content'].split(":\n\n", 1)[1] if ":\n\n" in app_context.chat_history[-1]['content'] else app_context.chat_history[-1]['content']}


Based on these search results, please provide a comprehensive and accurate answer to the original question: {prompt}

Important instructions:
- Use the information from the search results to give an accurate, up-to-date response
- Cite specific sources when making claims
- If the search results don't contain relevant information, acknowledge this
- Synthesize information from multiple sources when possible
- Focus on the most recent and reliable information"""

    app_context.chat_history.append({"role": "user", "content": search_context})
    try:
        reply = ask_server(app_context.chat_history, use_web_search=False)
        print("✅ Web search completed, got enhanced reply")
        return reply
    except Exception as e:
        print(f"❌ Error getting enhanced reply: {e}")
        return f"I found some search results but encountered an error processing them: {str(e)}"


def _handle_search_failure(reply, search_query, prompt, app_context):
    """Handle failed search attempts"""
    reply = re.sub(r"<search>.*?</search>", "", reply, flags=re.DOTALL).strip()
    
    if not reply.strip():
        reply = f"I tried to search for more information about '{search_query}', but the search failed. Let me answer based on my existing knowledge.\n\n"
        try:
            basic_reply = ask_server([{"role": "user", "content": f"Answer this question based only on your training data: {prompt}"}], use_web_search=False)
            reply += basic_reply
        except Exception as e:
            print(f"❌ Error getting basic reply: {e}")
            reply += "I apologize, but I'm unable to provide a complete answer at this time."
    else:
        reply += f"\n\n*Note: I wanted to search for more current information, but the search was unavailable.*"
    
    return reply


def _handle_search_unavailable(reply):
    """Handle when AI requests search but it's unavailable"""
    print("⚠️ AI requested web search but web search is not available")
    reply = re.sub(r"<search>.*?</search>", "", reply, flags=re.DOTALL).strip()
    search_match = re.search(r"<search>(.*?)</search>", reply, re.DOTALL)
    search_intent = search_match.group(1).strip() if search_match else "current information"
    
    if not reply:
        reply = f"I wanted to search for {search_intent} to give you the most current information, but web search functionality is not currently available. Let me answer based on my existing knowledge."
    else:
        reply += f"\n\n*Note: I wanted to search for {search_intent}, but web search is not currently available.*"
    
    return reply


def _handle_fallback_search(reply, prompt, app_context):
    """Handle fallback search when query needs search but AI didn't initiate it"""
    print("⚠️ Query needs search but AI didn't search and no search was performed")
    
    if WEB_SEARCH_AVAILABLE:
        search_query = prompt.strip()
        search_query = re.sub(r'\b(please|can you|could you|tell me|explain)\b', '', search_query, flags=re.IGNORECASE)
        search_query = re.sub(r'\?', '', search_query).strip()
        
        if search_query:
            print(f"🔍 Forcing search for: {search_query}")
            try:
                search_results = web_search(search_query, app_context.push_message_func)
                if search_results and not search_results.startswith("❌"):
                    reply += f"\n\n**📊 Current Information:**\n{search_results}"
            except Exception as e:
                print(f"❌ Forced search failed: {e}")
                reply += f"\n\n*Note: I tried to find current information but encountered an issue: {e}*"
    else:
        reply += "\n\n*Note: This question might benefit from current information, but web search is not available.*"
    
    return reply


def _auto_rename_chat(prompt, app_context):
    """Auto-rename chat if still called 'Untitled'"""
    if app_context.current_chat_name == "Untitled" and prompt.strip():
        summary = prompt.strip().splitlines()[0][:30]
        new_name = re.sub(r'[\\/:*?"<>|]', '_', summary).strip() or f"Chat {datetime.now().strftime('%m/%d %H:%M')}"
        
        try:
            # Ensure chats directory exists
            os.makedirs("chats", exist_ok=True)
            
            old_path = os.path.join("chats", "Untitled.json")
            new_path = os.path.join("chats", f"{new_name}.json")

            if os.path.exists(old_path):
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(old_path, new_path)
                print(f"✏️ Renamed chat file to: {new_name}.json")

            app_context.current_chat_name = new_name
            if app_context.sidebar_backend:
                app_context.sidebar_backend._current_chat_name = new_name
                if hasattr(app_context.sidebar_backend, 'currentChatChanged'):
                    app_context.sidebar_backend.currentChatChanged.emit(new_name)
                app_context.sidebar_backend.add_chat_to_history(new_name)
        except Exception as e:
            print(f"⚠️ Error renaming chat: {e}")


def _save_chat_data(app_context):
    """Save chat history and update sidebar"""
    if app_context.current_chat_name:
        try:
            save_current_chat(app_context.current_chat_name, app_context.chat_history)
        except Exception as e:
            print(f"⚠️ Error saving current chat: {e}")

    if app_context.sidebar_backend and app_context.current_chat_name:
        try:
            exists = any(chat['name'] == app_context.current_chat_name for chat in app_context.sidebar_backend._chat_history)
            if not exists and len(app_context.chat_history) <= 2:
                app_context.sidebar_backend.add_chat_to_history(app_context.current_chat_name)
            save_individual_chat(app_context.current_chat_name, app_context.chat_history)
        except Exception as e:
            print(f"⚠️ Error updating sidebar: {e}")


def _send_response_to_ui(reply, app_context):
    """Send response to UI"""
    print("📤 Sending message to QML")
    if app_context.push_message_func:
        try:
            app_context.push_message_func("assistant", reply)
            print("✅ Message sent via push_message_func")
        except Exception as e:
            print(f"⚠️ Push message error: {e}")
            # Fallback to GUI injection
            if app_context.gui:
                try:
                    app_context.gui.inject_response("🤖 " + reply + "\n")
                    print("✅ Message sent via GUI fallback")
                except Exception as gui_e:
                    print(f"⚠️ GUI injection error: {gui_e}")
    elif app_context.gui:
        try:
            app_context.gui.inject_response("🤖 " + reply + "\n")
            print("✅ Message sent via GUI")
        except Exception as e:
            print(f"⚠️ GUI injection error: {e}")
    else:
        print("⚠️ No UI method available - printing response to console")
        print(f"🤖 {reply}")