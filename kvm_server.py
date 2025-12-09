import socket
import json
from pynput import mouse, keyboard
import sys
import threading
import time

# --- Globals ---
VERSION = "v3.0-json"
client_socket = None
keyboard_control_enabled = False
control_lock = threading.Lock()
keyboard_listener = None

# --- Event Handlers ---

def send_event(event):
    """Sends a JSON-serialized event to the client."""
    global client_socket
    if keyboard_control_enabled and client_socket:
        try:
            payload = json.dumps(event).encode()
            client_socket.sendall(payload)
        except (ConnectionError, BrokenPipeError) as e:
            print(f"Connection lost: {e}")
            if client_socket:
                client_socket.close()
            client_socket = None
        except Exception as e:
            print(f"Error sending event: {e}")

# Map virtual key codes for numpad numbers to their character representation
VK_NUMPAD_MAP = {
    96: '0', 97: '1', 98: '2', 99: '3', 100: '4',
    101: '5', 102: '6', 103: '7', 104: '8', 105: '9',
    110: '.' # Numpad decimal
}

def on_key_event(key, is_press):
    """Determines the correct event type and sends it."""
    event_type = 'press' if is_press else 'release'
    event = None

    if isinstance(key, keyboard.Key):
        key_name = key.name
        # Workaround for AltGr incompatibility between Windows and Linux
        if key_name == 'alt_gr':
            key_name = 'alt_r'
        event = {'type': event_type, 'key_type': 'name', 'value': key_name}
    elif isinstance(key, keyboard.KeyCode):
        # Block the problematic Numpad-5-with-NumLock-Off key (VK_CLEAR = 12)
        if hasattr(key, 'vk') and key.vk == 12:
            return # Do nothing, ignore this key

        # Check if it's a numpad number key by its virtual key code
        if hasattr(key, 'vk') and key.vk in VK_NUMPAD_MAP:
            # Send it as a character event with the correct digit
            event = {'type': event_type, 'key_type': 'char', 'value': VK_NUMPAD_MAP[key.vk]}
        elif key.char:
            # It's a printable character (e.g., 'a', '1' from main keyboard). Send by character.
            event = {'type': event_type, 'key_type': 'char', 'value': key.char}
        else:
            # It's a non-printable keycode (e.g., function keys). Send by virtual keycode.
            if hasattr(key, 'vk'):
                event = {'type': event_type, 'key_type': 'vk', 'value': key.vk}
            else:
                event = None
    
    if event:
        send_event(event)
    else:
        print(f"Warning: Could not serialize key: {key}")

def on_press(key):
    if key == keyboard.Key.f12:
        threading.Thread(target=toggle_keyboard_control).start()
        return
    on_key_event(key, is_press=True)

def on_release(key):
    if key == keyboard.Key.f12:
        return
    on_key_event(key, is_press=False)

# --- Control Toggle Logic ---

def start_keyboard_listener(suppress):
    """Stops/starts the keyboard listener with correct suppression."""
    global keyboard_listener
    if keyboard_listener:
        keyboard_listener.stop()
    time.sleep(0.1)
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=suppress)
    keyboard_listener.start()
    print(f"Keyboard input suppression is {'ON' if suppress else 'OFF'}")

def toggle_keyboard_control():
    """Toggles keyboard input control."""
    global keyboard_control_enabled
    with control_lock:
        keyboard_control_enabled = not keyboard_control_enabled
        print(f"--- Keyboard control to client: {'ENABLED' if keyboard_control_enabled else 'DISABLED'} ---")
        start_keyboard_listener(suppress=keyboard_control_enabled)

# --- Main Server Function ---

def start_server(host, port=65432):
    global client_socket
    print(f"KVM Server {VERSION}")
    start_keyboard_listener(suppress=False)
    mouse_listener = mouse.Listener()
    mouse_listener.start()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print(f"Connected to {host}:{port}")
            client_socket = s
            # Enable TCP keep-alives
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            print("--- Server running. Press F12 to toggle KEYBOARD control. ---")
            while client_socket:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client_socket:
            client_socket.close()
        client_socket = None
        if keyboard_listener:
            keyboard_listener.stop()
        if mouse_listener:
            mouse_listener.stop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kvm_server.py <client_ip>")
        sys.exit(1)
    
    client_ip = sys.argv[1]
    start_server(client_ip)