#!/usr/bin/env python3
"""
Eidolon - Personal AI Assistant
Main application entry point that initializes the core assistant and launches the GUI.

This replaces the monolithic testQt.py with a clean modular architecture:
- eidolon_core.py: Assistant logic, LLM orchestration, memory, web search
- eidolon_gui.py: GUI setup, QML loading, PyQt6 bridge
- main.py: Application initialization and coordination
"""

import sys
import os
import atexit
import threading
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Core imports
try:
    from eidolon.eidolon_core import AssistantCore
    print("✅ AssistantCore imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AssistantCore: {e}")
    print("Make sure eidolon_core.py exists and is properly configured")
    sys.exit(1)

try:
    from eidolon.eidolon_gui import start_gui
    print("✅ GUI module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import GUI module: {e}")
    print("Make sure eidolon_gui.py exists and is properly configured")
    sys.exit(1)

# Global references for cleanup
assistant_core = None
app_instance = None

def setup_application():
    """Initialize the application environment and core components."""
    global assistant_core
    
    print("[EIDOLON] 🚀 Initializing Eidolon Personal AI Assistant")
    print(f"[EIDOLON] 📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize core assistant
    try:
        print("[EIDOLON] 🧠 Initializing AssistantCore...")
        assistant_core = AssistantCore()
        print("[EIDOLON] ✅ AssistantCore initialized successfully")
        
        # Start background services (LLM server, memory, etc.)
        print("[EIDOLON] 🔧 Starting background services...")
        assistant_core.start_services()
        print("[EIDOLON] ✅ Background services started")
        
        return assistant_core
        
    except Exception as e:
        print(f"[EIDOLON] ❌ Failed to initialize AssistantCore: {e}")
        sys.exit(1)

def setup_cleanup_handlers():
    """Register cleanup handlers for graceful shutdown."""
    global assistant_core
    
    def cleanup_on_exit():
        """Cleanup function called on application exit."""
        print("[EIDOLON] 🛑 Application shutting down...")
        
        if assistant_core:
            try:
                # Save current chat session
                if hasattr(assistant_core, 'save_current_session'):
                    assistant_core.save_current_session()
                    print("[EIDOLON] 💾 Current session saved")
                
                # Cleanup background services
                if hasattr(assistant_core, 'shutdown'):
                    assistant_core.shutdown()
                    print("[EIDOLON] 🔧 Background services stopped")
                    
            except Exception as e:
                print(f"[EIDOLON] ⚠️ Error during cleanup: {e}")
        
        print("[EIDOLON] 👋 Goodbye!")
    
    # Register cleanup handler
    atexit.register(cleanup_on_exit)

def main():
    """Main application entry point."""
    global app_instance
    
    try:
        # Setup environment and core
        assistant_core = setup_application()
        
        # Setup cleanup handlers
        setup_cleanup_handlers()
        
        # Launch GUI with core instance
        print("[EIDOLON] 🎨 Launching GUI...")
        exit_code = start_gui(assistant_core)
        
        print(f"[EIDOLON] 🏁 Application exited with code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print("\n[EIDOLON] 🛑 Interrupted by user (Ctrl+C)")
        return 0
        
    except Exception as e:
        print(f"[EIDOLON] ❌ Fatal error in main(): {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Ensure we're running from the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the application
    sys.exit(main())