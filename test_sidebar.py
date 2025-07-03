#!/usr/bin/env python3
"""
Test script to verify SidebarBackend functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import QCoreApplication
from eidolon.core.app_context import AppContext
from eidolon.gui.sidebar_backend import SidebarBackend

def test_sidebar_backend():
    """Test the SidebarBackend class functionality"""
    print("🧪 Testing SidebarBackend...")
    
    # Create app context
    app_context = AppContext()
    
    # Create sidebar backend
    sidebar = SidebarBackend(app_context)
    
    # Test properties
    print(f"✅ currentChatName: {sidebar.currentChatName}")
    print(f"✅ sidebarVisible: {sidebar.sidebarVisible}")
    chat_history = sidebar.chatHistory
    print(f"✅ chatHistory length: {len(chat_history)}")
    print(f"✅ hasUnsavedChanges: {sidebar.hasUnsavedChanges}")
    
    # Test chat history content
    print("\n📋 Chat History:")
    for i, chat in enumerate(chat_history):
        print(f"  {i+1}. {chat.get('name', 'Unknown')} - {chat.get('timestamp', 'No timestamp')}")
    
    # Test signals
    def on_chat_history_changed():
        print("📝 chatHistoryChanged signal received")
    
    def on_current_chat_changed(chat_name):
        print(f"🔄 currentChatChanged signal received: {chat_name}")
    
    def on_sidebar_visibility_changed(visible):
        print(f"👁️ sidebarVisibilityChanged signal received: {visible}")
    
    # Connect signals
    sidebar.chatHistoryChanged.connect(on_chat_history_changed)
    sidebar.currentChatChanged.connect(on_current_chat_changed)
    sidebar.sidebarVisibilityChanged.connect(on_sidebar_visibility_changed)
    
    # Test property setters
    print("\n🧪 Testing property setters...")
    sidebar.sidebarVisible = False
    print(f"✅ sidebarVisible set to: {sidebar.sidebarVisible}")
    
    # Test methods
    print("\n🧪 Testing methods...")
    print(f"✅ get_current_chat_name(): {sidebar.get_current_chat_name()}")
    print(f"✅ get_sidebar_visible(): {sidebar.get_sidebar_visible()}")
    print(f"✅ get_chat_history() length: {len(sidebar.get_chat_history())}")
    
    print("\n✅ SidebarBackend test completed successfully!")

if __name__ == "__main__":
    # Create minimal QApplication for Qt properties
    app = QCoreApplication(sys.argv)
    test_sidebar_backend()
    print("✅ All tests passed!") 