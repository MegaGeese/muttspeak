import main
import json
import main

def load_config():
    """Loads configuration from a JSON file."""
    try:
        with open(main.CONFIG_FILE, 'r') as f:
            loaded_data = json.load(f)
            print(f"Loaded configuration: {loaded_data}")
        
        with main.config_lock:
            # Update only existing keys to avoid overriding new defaults
            for key, value in loaded_data.items():
                # Special handling for COMBINATION
                if key == "COMBINATION" and isinstance(value, list):
                    # Convert list of strings back to pynput Key objects
                    main.user_config[key] = {main.KEY_MAP.get(k, k) for k in value if main.KEY_MAP.get(k)}
                    # Filter out any keys that weren't successfully mapped
                    if len(main.user_config[key]) != len(value):
                        print(f"Warning: Some combination keys in config file were not recognized: {value}")
                else:
                    main.user_config[key] = value
        print(f"Configuration loaded from {main.CONFIG_FILE}")
        print(f"Current configuration: {main.user_config}")
    except FileNotFoundError:
        print(f"Configuration file {main.CONFIG_FILE} not found. Using default settings.")
        # No need to acquire lock here, as main.user_config is initialized at global scope
        # and this is the first access.
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {main.CONFIG_FILE}. Using default settings.")
    except Exception as e:
        print(f"An unexpected error occurred while loading config: {e}. Using default settings.")


def save_config():
    """Saves current configuration to a JSON file."""
    # Create a copy of the config to modify for saving,
    # converting non-JSON-serializable types
    config_to_save = main.user_config.copy()
    
    with main.config_lock:
        # Convert set of pynput Key objects to a list of strings
        if "COMBINATION" in config_to_save and isinstance(config_to_save["COMBINATION"], set):
            string_keys = []
            for key_obj in config_to_save["COMBINATION"]:
                string_rep = main.REVERSE_KEY_MAP.get(key_obj)
                if string_rep:
                    string_keys.append(string_rep)
                else:
                    print(f"Warning: Could not serialize pynput Key object: {key_obj}")
            config_to_save["COMBINATION"] = sorted(string_keys) # Sort for consistent file content

        try:
            with open(main.CONFIG_FILE, 'w') as f:
                json.dump(config_to_save, f, indent=4) # indent for pretty printing
            print(f"Configuration saved to {main.CONFIG_FILE}")
        except Exception as e:
            print(f"Error saving configuration to {main.CONFIG_FILE}: {e}")