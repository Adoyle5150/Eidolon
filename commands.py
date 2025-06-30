def handle_commands(text):
    import os
    import webbrowser
    import pyttsx3
    import pyautogui
    import keyboard
    import datetime
    import requests
    from web.searcher import web_search



    text = text.lower()
    response = ""

    # === Manual web search trigger ===
    if text.startswith("search:"):
        query = text.replace("search:", "").strip()
        if query:
            response = f"🌐 Searching for: {query}\n\n" + web_search(query)
        else:
            response = "❌ Please include a search term after 'search:'."
        return response

    # === Local Commands Only ===

    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        response = "📺 Opening YouTube."

    elif "open google" in text:
        webbrowser.open("https://google.com")
        response = "🌐 Opening Google."

    elif "say" in text:
        to_say = text.split("say", 1)[-1].strip()
        engine = pyttsx3.init()
        engine.say(to_say)
        engine.runAndWait()
        response = f"🗣️ Saying: {to_say}"

    elif "move mouse" in text:
        pyautogui.moveTo(600, 400, duration=1)
        response = "🖱️ Moved mouse to center-ish position."

    elif "click mouse" in text:
        pyautogui.click()
        response = "🖱️ Clicked mouse."

    elif "type" in text:
        to_type = text.split("type", 1)[-1].strip()
        pyautogui.write(to_type, interval=0.05)
        response = f"⌨️ Typed: {to_type}"

    elif "press enter" in text:
        keyboard.press("enter")
        keyboard.release("enter")
        response = "🔘 Pressed Enter."

    elif "list files" in text:
        files = os.listdir(".")
        response = "📂 Current directory:\n" + "\n".join(files)

    elif "what time is it" in text or "what year" in text:
        now = datetime.datetime.now()
        response = f"🕒 It's currently {now.strftime('%A, %B %d, %Y %I:%M %p')}."

    elif "get ip" in text:
        try:
            ip = requests.get("https://api.ipify.org").text
            response = f"🌍 Your public IP address is: {ip}"
        except Exception as e:
            response = f"❌ Couldn't fetch IP: {e}"

    return response if response else None
