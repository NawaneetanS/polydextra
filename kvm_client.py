import socket
import json
import sys
import os
from evdev import UInput, ecodes as e

VERSION = "v4.0-evdev"

# This script must be run as root to create a virtual input device.
def check_permissions():
    if os.geteuid() != 0:
        print("Error: This script must be run as root to create a virtual keyboard.")
        print("Please run it with 'sudo'.")
        sys.exit(1)

# Maps pynput key names to evdev event codes.
PYNPUT_TO_EVDEV = {
    # Special Keys
    'alt': e.KEY_LEFTALT,
    'alt_l': e.KEY_LEFTALT,
    'alt_r': e.KEY_RIGHTALT,
    'alt_gr': e.KEY_RIGHTALT,
    'backspace': e.KEY_BACKSPACE,
    'caps_lock': e.KEY_CAPSLOCK,
    'cmd': e.KEY_LEFTMETA,
    'cmd_l': e.KEY_LEFTMETA,
    'cmd_r': e.KEY_RIGHTMETA,
    'ctrl': e.KEY_LEFTCTRL,
    'ctrl_l': e.KEY_LEFTCTRL,
    'ctrl_r': e.KEY_RIGHTCTRL,
    'delete': e.KEY_DELETE,
    'down': e.KEY_DOWN,
    'end': e.KEY_END,
    'enter': e.KEY_ENTER,
    'esc': e.KEY_ESC,
    'f1': e.KEY_F1, 'f2': e.KEY_F2, 'f3': e.KEY_F3, 'f4': e.KEY_F4,
    'f5': e.KEY_F5, 'f6': e.KEY_F6, 'f7': e.KEY_F7, 'f8': e.KEY_F8,
    'f9': e.KEY_F9, 'f10': e.KEY_F10, 'f11': e.KEY_F11, 'f12': e.KEY_F12,
    'f13': e.KEY_F13, 'f14': e.KEY_F14, 'f15': e.KEY_F15, 'f16': e.KEY_F16,
    'f17': e.KEY_F17, 'f18': e.KEY_F18, 'f19': e.KEY_F19, 'f20': e.KEY_F20,
    'home': e.KEY_HOME,
    'insert': e.KEY_INSERT,
    'left': e.KEY_LEFT,
    'media_next': e.KEY_NEXTSONG,
    'media_play_pause': e.KEY_PLAYPAUSE,
    'media_previous': e.KEY_PREVIOUSSONG,
    'media_volume_down': e.KEY_VOLUMEDOWN,
    'media_volume_mute': e.KEY_MUTE,
    'media_volume_up': e.KEY_VOLUMEUP,
    'menu': e.KEY_MENU,
    'num_lock': e.KEY_NUMLOCK,
    'page_down': e.KEY_PAGEDOWN,
    'page_up': e.KEY_PAGEUP,
    'pause': e.KEY_PAUSE,
    'print_screen': e.KEY_SYSRQ,
    'right': e.KEY_RIGHT,
    'scroll_lock': e.KEY_SCROLLLOCK,
    'shift': e.KEY_LEFTSHIFT,
    'shift_l': e.KEY_LEFTSHIFT,
    'shift_r': e.KEY_RIGHTSHIFT,
    'space': e.KEY_SPACE,
    'tab': e.KEY_TAB,
    'up': e.KEY_UP,

    # Character Keys (pynput server sends them as chars)
    'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D, 'e': e.KEY_E,
    'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H, 'i': e.KEY_I, 'j': e.KEY_J,
    'k': e.KEY_K, 'l': e.KEY_L, 'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O,
    'p': e.KEY_P, 'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
    'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X, 'y': e.KEY_Y,
    'z': e.KEY_Z,
    '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3, '4': e.KEY_4, '5': e.KEY_5,
    '6': e.KEY_6, '7': e.KEY_7, '8': e.KEY_8, '9': e.KEY_9, '0': e.KEY_0,
    '-': e.KEY_MINUS, '=': e.KEY_EQUAL,
    '[': e.KEY_LEFTBRACE, ']': e.KEY_RIGHTBRACE, '\\': e.KEY_BACKSLASH,
    ';': e.KEY_SEMICOLON, "'": e.KEY_APOSTROPHE, '`': e.KEY_GRAVE,
    ',': e.KEY_COMMA, '.': e.KEY_DOT, '/': e.KEY_SLASH,
    
    # Numpad keys (server sends these as chars too)
    '*': e.KEY_KPASTERISK,
    '+': e.KEY_KPPLUS,
    # '/': e.KEY_KPSLASH, # Already mapped
    # '-': e.KEY_KPMINUS, # Already mapped
    # '.': e.KEY_KPDOT,   # Already mapped
}

def handle_event(event, ui):
    """Looks up the evdev keycode and writes the press/release event."""
    value = event.get('value')
    keycode = PYNPUT_TO_EVDEV.get(str(value).lower())

    if keycode is None:
        print(f"Warning: No key mapping found for event: {event}")
        return

    state = 1 if event.get('type') == 'press' else 0
    try:
        ui.write(e.EV_KEY, keycode, state)
        ui.syn()
    except Exception as err:
        print(f"Error writing event to uinput: {err}")

def start_client(host='0.0.0.0', port=65432):
    print(f"KVM Client {VERSION}")
    check_permissions()

    # Define the capabilities of our virtual keyboard
    capabilities = {
        e.EV_KEY: PYNPUT_TO_EVDEV.values()
    }

    try:
        with UInput(capabilities, name='kvm-virtual-keyboard') as ui:
            print("Virtual keyboard created. Waiting for server connection...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                s.listen()
                print(f"Listening for connections on {host}:{port}")
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    buffer = ""
                    while True:
                        data = conn.recv(4096).decode()
                        if not data:
                            print("Connection closed by server.")
                            break
                        buffer += data
                        
                        while '{' in buffer and '}' in buffer:
                            start_index = buffer.find('{')
                            end_index = buffer.find('}')
                            if start_index > end_index:
                                buffer = buffer[start_index:]
                                continue

                            json_str = buffer[start_index:end_index+1]
                            buffer = buffer[end_index+1:]
                            
                            try:
                                event = json.loads(json_str)
                                handle_event(event, ui)
                            except json.JSONDecodeError:
                                print(f"Warning: Could not decode JSON: {json_str}")
                                continue
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
        print("This may be a permissions error. Make sure you are running with 'sudo'.")

if __name__ == "__main__":
    start_client()
