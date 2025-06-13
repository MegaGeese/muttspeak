from pynput.keyboard import Key
import main
import pishock_helper

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
    with main.config_lock:
        combination_keys = user_config["COMBINATION"]

    if key in combination_keys:
        current_keys_pressed.add(key)
        if all(k in current_keys_pressed for k in combination_keys):
            print('Exiting muttmode (keyboard listener stopping).')
            return False # This stops the pynput listener

def released(key):
    global current_keys_pressed
    
    # Check for combination keys, protected by lock
    with main.config_lock:
        combination_keys = user_config["COMBINATION"]

    if key in combination_keys:
        if key in current_keys_pressed: # Ensure key is actually in the set before removing
            current_keys_pressed.remove(key)


def check_word(word):
    global user_config # Declare global to access the dictionary
    
    # Read BAD_WORDS from config, protected by lock
    with main.config_lock:
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