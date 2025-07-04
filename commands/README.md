# Commands Module

This module contains local command handling functionality for the Eidolon application.

## Location

The commands module has been moved from the root directory to the `commands/` folder and is now properly organized as a Python package.

## Structure

- `commands/__init__.py` - Contains the main `handle_commands()` function

## Usage

The module is imported and used in `eidolon/core/prompt_processor.py`:

```python
import commands
local_response = commands.handle_commands(prompt)
```

## Available Commands

The module handles various local commands including:

- **Web Search**: `search: <query>` - Manual web search trigger
- **Browser Commands**: 
  - `open youtube` - Opens YouTube
  - `open google` - Opens Google
- **System Commands**:
  - `say <text>` - Text-to-speech output
  - `move mouse` - Moves mouse to center position
  - `click mouse` - Clicks mouse
  - `type <text>` - Types text
  - `press enter` - Presses Enter key
  - `list files` - Lists files in current directory
  - `what time is it` - Shows current time
  - `get ip` - Shows public IP address
  - `stop listening` - Stops hands-free mode

## Dependencies

The module requires several dependencies that are listed in the main `requirements.txt`:

- `pyttsx3` - Text-to-speech
- `pyautogui` - Mouse and keyboard control
- `keyboard` - Keyboard input
- `requests` - HTTP requests
- `webbrowser` - Browser control (built-in)
- `os` - File system operations (built-in)
- `datetime` - Date/time operations (built-in)

## Testing

Run the test script to verify the module works correctly:

```bash
python test_commands_simple.py
```

This will test the module structure and basic functionality without requiring all dependencies to be installed. 