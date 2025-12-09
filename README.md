# Polydextra - A KVM Project

This project provides a simple solution for sharing keyboard input between two Linux machines over a network. One machine acts as the "server," capturing local keyboard input, while the other acts as the "client," receiving these inputs and simulating them using a virtual keyboard device.

## Features

*   **Keyboard Input Capture:** The server component captures all keyboard events from the local machine.
*   **Virtual Keyboard Simulation:** The client component creates a virtual keyboard device and injects received events, effectively simulating keyboard input on the client machine.
*   **Toggle Control:** Keyboard input sharing can be easily toggled on/off using the `F12` key on the server machine.

## Requirements

*   Python 3
*   `pynput` library (for the server)
*   `evdev` library (for the client)
*   `sudo` privileges (required to run the client, as it creates a virtual input device)

## Setup

### 1. Install Dependencies

**On the Server Machine:**

```bash
pip install pynput
```

**On the Client Machine:**

```bash
pip install evdev
```

### 2. Run the Client (Receiver)

On the machine where you want to *receive* keyboard input:

```bash
sudo python3 kvm_client.py
```

The client will bind to `0.0.0.0:65432` and wait for a connection from the server. It must be run with `sudo` to create the virtual keyboard device.

### 3. Run the Server (Sender)

On the machine where you want to *capture and send* keyboard input:

```bash
python3 kvm_server.py <client_ip_address>
```

Replace `<client_ip_address>` with the IP address of the machine running `kvm_client.py`. The server will connect to the client on port `65432`.

## Usage

Once both the client and server are running and connected:

*   **F12 Key:** Pressing `F12` on the server machine will toggle the keyboard control.
    *   When enabled, your keyboard input on the server will be sent to the client.
    *   When disabled, your keyboard input will only affect the server machine.

## Limitations

*   Currently, only keyboard input is supported. Mouse input is not yet implemented.
*   The client requires root privileges to function.
