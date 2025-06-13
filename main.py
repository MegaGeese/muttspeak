import pystray
from PIL import Image
import threading
import sys
import os
import json
from pynput.keyboard import Key, Listener
import menus
import config
import logger

# --- Configuration File Path ---
CONFIG_FILE = "muttspeak_config.json"
# create CONFIG_FILE if it doesn't exist
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        # Initialize with default values
        default_config = {
            "BAD_WORDS": [],  # Default no bad words
            "COMBINATION": ["ctrl_l", "f1"],  # Default key combination to exit mutt mode
            "INTENSITY": 1,  # Default shock intensity
            "DURATION": 1,  # Default shock duration in seconds
            "API_KEY": "",  # Placeholder for API key
            "API_USERNAME": "",  # Placeholder for API username
            "API_CODE": "",  # Placeholder for share code
            "OPERATIONS": 0,  # Default operation index (0 for shock)
        }
        json.dump(default_config, f, indent=4)  # Save with pretty printing

# --- Shared Configuration ---
# Use a dictionary to hold all user-settable parameters
# This makes it easier to pass around and manage
user_config = {}
config_lock = threading.Lock() # Lock to protect user_config

# --- Global State (not user-set, but still shared) ---
current_word = ""
current_keys_pressed = set()

# --- Helper for pynput Key conversion ---
# Map string representations back to pynput Key objects
KEY_MAP = {
    "ctrl_l": Key.ctrl_l,
    "ctrl_r": Key.ctrl_r,
    "alt_l": Key.alt_l,
    "alt_r": Key.alt_r,
    "shift_l": Key.shift_l,
    "shift_r": Key.shift_r,
    "cmd": Key.cmd, # Windows/Mac command key
    "cmd_r": Key.cmd_r,
    # Add other special keys you might want to use
    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
}
# Reverse map for saving
REVERSE_KEY_MAP = {v: k for k, v in KEY_MAP.items()}

OPERATIONS = ["shock", "vibrate", "beep"]

"""
TODO
add way to change keyboard shortcut
"""

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def begin_logging():
    print("Beginning keyboard logging.")
    # You might want to disable this menu item or provide feedback that it's running
    # to prevent multiple listeners from starting.
    # A global flag could manage this.

    # Ensure the listener runs in its own thread, separate from the main pystray thread.
    # The `with Listener(...) as detector:` already handles threading internally for pynput,
    # but the `detector.join()` call would block the main thread.
    # So, we need to put `begin_logging` itself into a new thread.
    def _start_listener():
        with Listener(on_press=logger.pressed, on_release=logger.released) as detector:
            detector.join()
    
    threading.Thread(target=_start_listener, name="KeyboardListener").start()

def run_app():
    config.load_config()  # Load configuration at startup

    icon_image = Image.open(resource_path("icon.PNG"))

    menu = (
        pystray.MenuItem('Settings', menus.on_settings_clicked),
        pystray.MenuItem('Become Mutt', begin_logging),
        pystray.MenuItem('About', menus.on_about_clicked),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Quit', menus.on_quit_clicked)
    )

    icon = pystray.Icon('muttspeak', icon_image, 'Muttspeak', menu)
    icon.run()

if __name__ == '__main__':
    run_app()