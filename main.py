import pystray
from PIL import Image, ImageDraw
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sv_ttk
import requests
import threading
import sys
import os
import json
from pynput.keyboard import Key, Listener
import pishock_helper
import pywinstyles

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

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

def set_icon(window):
    """
    Sets the icon for the system tray.
    This function is called by pystray to set the icon.
    """
    window.iconphoto(False, tk.PhotoImage(file=resource_path("icon.PNG")))

def load_config():
    """Loads configuration from a JSON file."""
    global user_config
    try:
        with open(CONFIG_FILE, 'r') as f:
            loaded_data = json.load(f)
            print(f"Loaded configuration: {loaded_data}")
        
        with config_lock:
            # Update only existing keys to avoid overriding new defaults
            for key, value in loaded_data.items():
                # Special handling for COMBINATION
                if key == "COMBINATION" and isinstance(value, list):
                    # Convert list of strings back to pynput Key objects
                    user_config[key] = {KEY_MAP.get(k, k) for k in value if KEY_MAP.get(k)}
                    # Filter out any keys that weren't successfully mapped
                    if len(user_config[key]) != len(value):
                        print(f"Warning: Some combination keys in config file were not recognized: {value}")
                else:
                    user_config[key] = value
        print(f"Configuration loaded from {CONFIG_FILE}")
        print(f"Current configuration: {user_config}")
    except FileNotFoundError:
        print(f"Configuration file {CONFIG_FILE} not found. Using default settings.")
        # No need to acquire lock here, as user_config is initialized at global scope
        # and this is the first access.
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {CONFIG_FILE}. Using default settings.")
    except Exception as e:
        print(f"An unexpected error occurred while loading config: {e}. Using default settings.")


def save_config():
    """Saves current configuration to a JSON file."""
    global user_config
    # Create a copy of the config to modify for saving,
    # converting non-JSON-serializable types
    config_to_save = user_config.copy()
    
    with config_lock:
        # Convert set of pynput Key objects to a list of strings
        if "COMBINATION" in config_to_save and isinstance(config_to_save["COMBINATION"], set):
            string_keys = []
            for key_obj in config_to_save["COMBINATION"]:
                string_rep = REVERSE_KEY_MAP.get(key_obj)
                if string_rep:
                    string_keys.append(string_rep)
                else:
                    print(f"Warning: Could not serialize pynput Key object: {key_obj}")
            config_to_save["COMBINATION"] = sorted(string_keys) # Sort for consistent file content

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_to_save, f, indent=4) # indent for pretty printing
            print(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            print(f"Error saving configuration to {CONFIG_FILE}: {e}")

def create_image(width, height, color1, color2):
    """
    Creates a simple square image for the tray icon.
    """
    image = Image.open(resource_path("icon.PNG"))
    return image

def show_about():
    """
    Function to display an 'About' window.
    This runs in a separate thread to avoid blocking the main UI loop.
    """
    def _show_about_thread():
        about_root = tk.Tk()
        about_root.title("Muttspeak")
        about_root.geometry("300x150")
        about_root.resizable(False, False)
        set_icon(about_root)

        ttk.Label(about_root, text="mutts arent supposed to use bad words", font=("Arial", 10, "bold")).pack(pady=10)
        ttk.Label(about_root, text="Version 0.1.0").pack(pady=5)
        ttk.Label(about_root, text="Made with 💜 for my lil mutt").pack(pady=5)
        ttk.Label(about_root, text="© 2025 August").pack(pady=5)

        # Center the window
        about_root.update_idletasks()
        screen_width = about_root.winfo_screenwidth()
        screen_height = about_root.winfo_screenheight()
        center_x = int(screen_width/2 - about_root.winfo_width()/2)
        center_y = int(screen_height/2 - about_root.winfo_height()/2)
        about_root.geometry(f"+{center_x}+{center_y}")

        sv_ttk.set_theme("dark")
        apply_theme_to_titlebar(about_root)

        about_root.mainloop()

    threading.Thread(target=_show_about_thread).start()

def open_settings_window():
    """
    Function to open a settings window where the user can update parameters.
    This runs in a separate thread to avoid blocking the main UI loop.
    """
    def _open_settings_thread():
        settings_root = tk.Tk()
        settings_root.title("Muttspeak Settings")
        settings_root.geometry("400x400")
        set_icon(settings_root)

        notebook = ttk.Notebook(settings_root)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Tab 1: General Settings ---
        general_settings_frame = ttk.Frame(notebook)
        notebook.add(general_settings_frame, text="General")

        # Bad Words List
        ttk.Label(general_settings_frame, text="Bad Words (comma-separated):").pack(pady=5)
        # Read current bad words from config, protected by lock
        with config_lock:
            initial_bad_words = ", ".join(user_config["BAD_WORDS"])
        bad_words_entry = ttk.Entry(general_settings_frame)
        bad_words_entry.insert(0, initial_bad_words)
        bad_words_entry.pack(pady=5)

        # Keyboard Shortcut (read-only for now)
        ttk.Label(general_settings_frame, text="Current Exit Shortcut:").pack(pady=5)
        with config_lock:
            shortcut_display = ttk.Label(general_settings_frame, text=" + ".join([str(k).replace('Key.', '') for k in user_config["COMBINATION"]]))
        shortcut_display.pack(pady=5)

        # --- Tab 2: Shock Collar Settings Options ---
        shock_collar_settings_frame = ttk.Frame(notebook)
        notebook.add(shock_collar_settings_frame, text="Shock Collar Settings")

        # Shock Level and Duration Sliders
        shock_level_var = tk.IntVar()
        with config_lock:
            shock_level_var.set(user_config["INTENSITY"])

        shock_level_label = tk.StringVar()
        shock_level_label.set(f"Shock Level: {shock_level_var.get()}")

        def set_shock_level(new_shock_level):
            shock_level_label.set( f"Shock Level: {int(float(new_shock_level))}" )

        ttk.Label(shock_collar_settings_frame, textvariable=shock_level_label).pack(pady=5)
        ttk.Scale(shock_collar_settings_frame, from_=1, to=100, variable=shock_level_var, command=set_shock_level).pack(pady=5)
        
        shock_duration_val = tk.IntVar()
        with config_lock:
            shock_duration_val.set(user_config["DURATION"])

        shock_duration_label = tk.StringVar()
        shock_duration_label.set(f"Shock Duration: {shock_duration_val.get()} seconds")

        def set_shock_duration(new_shock_duration):
            shock_duration_label.set( f"Shock Duration: {int(float(new_shock_duration))} seconds" )

        ttk.Label(shock_collar_settings_frame, textvariable=shock_duration_label).pack(pady=5)
        ttk.Scale(shock_collar_settings_frame, from_=1, to=15, variable=shock_duration_val, command=set_shock_duration).pack(pady=5)

        # Operations combo box
        ttk.Label(shock_collar_settings_frame, text="Shock Collar Operation:").pack(pady=5)
        operations_var = tk.StringVar(value=OPERATIONS[user_config["OPERATIONS"]])
        operations_menu = ttk.OptionMenu(shock_collar_settings_frame, operations_var, OPERATIONS[0], *OPERATIONS)
        operations_menu.pack(pady=5)
        operations_menu.config(width=20)
        operations_var.set(OPERATIONS[user_config["OPERATIONS"]])  # Set initial value

        # --- Tab 2: API Settings Options ---
        api_settings_frame = ttk.Frame(notebook)
        notebook.add(api_settings_frame, text="API Settings")

        # API Key Input
        with config_lock:
            api_key_from_settings = user_config["API_KEY"]
        api_key_variable = tk.StringVar(value=api_key_from_settings)
        ttk.Label(api_settings_frame, text="API Key:").pack(pady=5)
        ttk.Entry(api_settings_frame, textvariable=api_key_variable).pack(pady=5)

        # API Username Input
        with config_lock:
            api_username_from_settings = user_config["API_USERNAME"]
        api_username_variable = tk.StringVar(value=api_username_from_settings)
        ttk.Label(api_settings_frame, text="PiShock Username:").pack(pady=5)
        ttk.Entry(api_settings_frame, textvariable=api_username_variable).pack(pady=5)

        # API code Input
        with config_lock:
            api_code_from_settings = user_config["API_CODE"]
        api_code_variable = tk.StringVar(value=api_code_from_settings)
        ttk.Label(api_settings_frame, text="Share Code:").pack(pady=5)
        ttk.Entry(api_settings_frame, textvariable=api_code_variable).pack(pady=5)

        def save_settings():
            new_bad_words_str = bad_words_entry.get()
            new_bad_words = [word.strip().lower() for word in new_bad_words_str.split(',') if word.strip()]

            operation = OPERATIONS.index(operations_var.get()) if operations_var.get() in OPERATIONS else 0
            
            # Update user_config, protected by lock
            with config_lock:
                user_config["BAD_WORDS"] = new_bad_words
                user_config["INTENSITY"] = shock_level_var.get()
                user_config["DURATION"] = shock_duration_val.get()
                user_config["API_KEY"] = api_key_variable.get()
                user_config["API_USERNAME"] = api_username_variable.get()
                user_config["API_CODE"] = api_code_variable.get()
                user_config["OPERATIONS"] = operation
            save_config()
            settings_root.destroy()

        ttk.Button(settings_root, text="Save Settings", command=save_settings).pack(pady=10)

        sv_ttk.set_theme("dark")
        apply_theme_to_titlebar(settings_root)
        settings_root.mainloop()

    threading.Thread(target=_open_settings_thread).start()

def exit_app(icon):
    """
    Function to exit the application.
    """
    icon.stop()
    sys.exit(0) # Ensure the Python process fully exits

def on_quit_clicked(icon, item):
    """
    Handler for the 'Quit' menu item.
    """
    exit_app(icon)

def on_about_clicked(icon, item):
    """
    Handler for the 'About' menu item.
    """
    show_about()

def on_settings_clicked(icon, item):
    """
    Handler for the 'Settings' menu item.
    """
    open_settings_window()

def pressed(key):
    global current_word
    global current_keys_pressed

    key_string = str(key)
    print('Pressed:', key_string) # Uncomment for debugging key presses

    if "Key" not in key_string:
        if hasattr(key, 'char') and key.char is not None:
            current_word += key.char.lower() # Ensure lowercase for comparison
    elif key == Key.space or key == Key.enter:
        check_word(current_word)
        current_word = ""
    elif key == Key.backspace:
        current_word = current_word[:-1]
    
    # Check for combination keys, protected by lock
    with config_lock:
        combination_keys = user_config["COMBINATION"]

    if key in combination_keys:
        current_keys_pressed.add(key)
        if all(k in current_keys_pressed for k in combination_keys):
            print('Exiting muttmode (keyboard listener stopping).')
            return False # This stops the pynput listener

def released(key):
    global current_keys_pressed
    
    # Check for combination keys, protected by lock
    with config_lock:
        combination_keys = user_config["COMBINATION"]

    if key in combination_keys:
        if key in current_keys_pressed: # Ensure key is actually in the set before removing
            current_keys_pressed.remove(key)

def begin_logging(icon, item):
    print("Beginning keyboard logging.")
    # You might want to disable this menu item or provide feedback that it's running
    # to prevent multiple listeners from starting.
    # A global flag could manage this.

    # Ensure the listener runs in its own thread, separate from the main pystray thread.
    # The `with Listener(...) as detector:` already handles threading internally for pynput,
    # but the `detector.join()` call would block the main thread.
    # So, we need to put `begin_logging` itself into a new thread.
    def _start_listener():
        with Listener(on_press=pressed, on_release=released) as detector:
            detector.join()
    
    threading.Thread(target=_start_listener, name="KeyboardListener").start()


def check_word(word):
    global user_config # Declare global to access the dictionary
    
    # Read BAD_WORDS from config, protected by lock
    with config_lock:
        bad_words_list = user_config["BAD_WORDS"]
        operation = user_config["OPERATIONS"]
        intensity = user_config["INTENSITY"]
        duration = user_config["DURATION"]
        username = user_config["API_USERNAME"]
        apikey = user_config["API_KEY"]
        code = user_config["API_CODE"]

    print(f"Checking word: '{word}'")
    if word.lower() in bad_words_list: # Ensure word is lowercase for comparison
        print(f"Mutt activity detected for '{word}', administering treatment")
        pishock_helper.operate(operation, intensity, duration, username, apikey, code)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def run_app():
    load_config()  # Load configuration at startup

    icon_image = create_image(64, 64, 'darkblue', 'yellow')

    menu = (
        pystray.MenuItem('Settings', on_settings_clicked),
        pystray.MenuItem('Become Mutt', begin_logging),
        pystray.MenuItem('About', on_about_clicked),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Quit', on_quit_clicked)
    )

    icon = pystray.Icon('muttspeak', icon_image, 'Muttspeak', menu)
    icon.run()

if __name__ == '__main__':
    # It's good practice to ensure Tkinter is initialized on the main thread if
    # you were to create a main Tkinter window for the app itself, but for
    # simple message boxes in separate threads, it's often not strictly needed
    # for basic functionality. However, if you see issues, consider explicit init.
    # For now, keep as is.
    run_app()