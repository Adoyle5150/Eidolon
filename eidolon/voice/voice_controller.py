# voice_controller.py

_hands_free_active = False

def start_hands_free():
    global _hands_free_active
    _hands_free_active = True
    print("[VoiceController] Hands-free mode activated.")

def stop_hands_free():
    global _hands_free_active
    _hands_free_active = False
    print("[VoiceController] Hands-free mode deactivated.")

def is_hands_free_active():
    return _hands_free_active 