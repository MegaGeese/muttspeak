import tkinter as tk
from tkinter import ttk
import sv_ttk
import os
import sys
import threading
import pywinstyles
import main
import config

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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

def set_icon(window):
    """
    Sets the icon for the system tray.
    This function is called by pystray to set the icon.
    """
    window.iconphoto(False, tk.PhotoImage(file=resource_path("icon.PNG")))

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
        ttk.Label(about_root, text="Version 0.2.0").pack(pady=5)
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
        with main.config_lock:
            initial_bad_words = ", ".join(main.user_config["BAD_WORDS"])
        bad_words_entry = ttk.Entry(general_settings_frame)
        bad_words_entry.insert(0, initial_bad_words)
        bad_words_entry.pack(pady=5)

        # Keyboard Shortcut (read-only for now)
        ttk.Label(general_settings_frame, text="Current Exit Shortcut:").pack(pady=5)
        with main.config_lock:
            shortcut_display = ttk.Label(general_settings_frame, text=" + ".join([str(k).replace('Key.', '') for k in main.user_config["COMBINATION"]]))
        shortcut_display.pack(pady=5)

        # --- Tab 2: Shock Collar Settings Options ---
        shock_collar_settings_frame = ttk.Frame(notebook)
        notebook.add(shock_collar_settings_frame, text="Shock Collar Settings")

        # Shock Level and Duration Sliders
        shock_level_var = tk.IntVar()
        with main.config_lock:
            shock_level_var.set(main.user_config["INTENSITY"])

        shock_level_label = tk.StringVar()
        shock_level_label.set(f"Shock Level: {shock_level_var.get()}")

        def set_shock_level(new_shock_level):
            shock_level_label.set( f"Shock Level: {int(float(new_shock_level))}" )

        ttk.Label(shock_collar_settings_frame, textvariable=shock_level_label).pack(pady=5)
        ttk.Scale(shock_collar_settings_frame, from_=1, to=100, variable=shock_level_var, command=set_shock_level).pack(pady=5)
        
        shock_duration_val = tk.IntVar()
        with main.config_lock:
            shock_duration_val.set(main.user_config["DURATION"])

        shock_duration_label = tk.StringVar()
        shock_duration_label.set(f"Shock Duration: {shock_duration_val.get()} seconds")

        def set_shock_duration(new_shock_duration):
            shock_duration_label.set( f"Shock Duration: {int(float(new_shock_duration))} seconds" )

        ttk.Label(shock_collar_settings_frame, textvariable=shock_duration_label).pack(pady=5)
        ttk.Scale(shock_collar_settings_frame, from_=1, to=15, variable=shock_duration_val, command=set_shock_duration).pack(pady=5)

        # Operations combo box
        ttk.Label(shock_collar_settings_frame, text="Shock Collar Operation:").pack(pady=5)
        operations_var = tk.StringVar(value=main.OPERATIONS[main.user_config["OPERATIONS"]])
        operations_menu = ttk.OptionMenu(shock_collar_settings_frame, operations_var, main.OPERATIONS[0], *main.OPERATIONS)
        operations_menu.pack(pady=5)
        operations_menu.config(width=20)
        operations_var.set(main.OPERATIONS[main.user_config["OPERATIONS"]])  # Set initial value

        # --- Tab 2: API Settings Options ---
        api_settings_frame = ttk.Frame(notebook)
        notebook.add(api_settings_frame, text="API Settings")

        # API Key Input
        with main.config_lock:
            api_key_from_settings = main.user_config["API_KEY"]
        api_key_variable = tk.StringVar(value=api_key_from_settings)
        ttk.Label(api_settings_frame, text="API Key:").pack(pady=5)
        ttk.Entry(api_settings_frame, textvariable=api_key_variable).pack(pady=5)

        # API Username Input
        with main.config_lock:
            api_username_from_settings = main.user_config["API_USERNAME"]
        api_username_variable = tk.StringVar(value=api_username_from_settings)
        ttk.Label(api_settings_frame, text="PiShock Username:").pack(pady=5)
        ttk.Entry(api_settings_frame, textvariable=api_username_variable).pack(pady=5)

        # API code Input
        with main.config_lock:
            api_code_from_settings = main.user_config["API_CODE"]
        api_code_variable = tk.StringVar(value=api_code_from_settings)
        ttk.Label(api_settings_frame, text="Share Code:").pack(pady=5)
        ttk.Entry(api_settings_frame, textvariable=api_code_variable).pack(pady=5)

        def save_settings():
            new_bad_words_str = bad_words_entry.get()
            new_bad_words = [word.strip().lower() for word in new_bad_words_str.split(',') if word.strip()]

            operation = main.OPERATIONS.index(operations_var.get()) if operations_var.get() in main.OPERATIONS else 0
            
            # Update main.user_config, protected by lock
            with main.config_lock:
                main.user_config["BAD_WORDS"] = new_bad_words
                main.user_config["INTENSITY"] = shock_level_var.get()
                main.user_config["DURATION"] = shock_duration_val.get()
                main.user_config["API_KEY"] = api_key_variable.get()
                main.user_config["API_USERNAME"] = api_username_variable.get()
                main.user_config["API_CODE"] = api_code_variable.get()
                main.user_config["OPERATIONS"] = operation
            config.save_config()
            settings_root.destroy()

        ttk.Button(settings_root, text="Save Settings", command=save_settings).pack(pady=10)

        sv_ttk.set_theme("dark")
        apply_theme_to_titlebar(settings_root)
        settings_root.mainloop()

    threading.Thread(target=_open_settings_thread).start()