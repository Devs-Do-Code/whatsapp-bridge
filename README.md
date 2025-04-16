# Shubh-WhatsApp Package (shubh-whatsapp)

[![PyPI version](https://badge.fury.io/py/my-whatsapp-pkg.svg)](https://badge.fury.io/py/my-whatsapp-pkg) <!-- Replace with your actual PyPI badge if published -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library providing a convenient wrapper to interact with your personal WhatsApp account. This package manages the underlying [whatsapp-mcp Go bridge](https://github.com/lharries/whatsapp-mcp), handling setup, process management, and providing Pythonic methods for sending and receiving messages and media.

**⚠️ Disclaimer:** This package interacts with WhatsApp using unofficial methods derived from WhatsApp Web, primarily through the `whatsmeow` library used by the underlying Go bridge. **This is against WhatsApp's Terms of Service.** Using this library could potentially lead to your WhatsApp account being temporarily or permanently banned. **Use this package entirely at your own risk.** It is strongly recommended for educational purposes or personal, non-critical applications only. The developers of this package assume no responsibility for any consequences resulting from its use.

## Features

- **Automated Setup:** Checks for prerequisites (Go, Git) and automatically clones the required `whatsapp-mcp` Go bridge repository on first use.
- **Go Bridge Management:** Starts and stops the background Go bridge process required for WhatsApp connectivity.
- **QR Code Handling:** Detects when WhatsApp requires QR code scanning for authentication and informs the user via console output.
- **Send Messages:** Send text messages to individual contacts or groups using phone numbers or JIDs.
- **Send Media:** Send images, videos, documents, and audio files with optional captions.
- **Receive Messages:** Poll for new incoming messages since the last check.
- **Media Downloads:** Automatically (or manually) download incoming media files (images, videos, audio, documents) to a local directory.

## Prerequisites

Before using this package, ensure you have the following installed and configured on your system:

1.  **Python:** Version 3.8 or higher.
2.  **Go:** Latest stable version recommended.
    - Download from: [https://go.dev/dl/](https://go.dev/dl/)
    - **Crucially, ensure the Go `bin` directory is added to your system's `PATH` environment variable.** (e.g., `C:\Program Files\Go\bin` on Windows, `/usr/local/go/bin` or similar on Linux/macOS).
3.  **Git:** Required for cloning the Go bridge repository.
    - Download from: [https://git-scm.com/downloads](https://git-scm.com/downloads)
    - **Ensure Git executable is in your system's `PATH`.**
4.  **C Compiler (Windows Only):** The Go bridge uses a database library (`go-sqlite3`) that requires CGO. If you are on Windows:
    - Install a C compiler like MSYS2 + MinGW toolchain. Follow the [MSYS2 installation guide](https://www.msys2.org/) and install the UCRT64 toolchain (`pacman -S --needed base-devel mingw-w64-ucrt-x86_64-toolchain`).
    - **Add the compiler's `bin` directory to your `PATH`** (e.g., `C:\msys64\ucrt64\bin`).
    - The package attempts to set `CGO_ENABLED=1` when running the Go bridge, but having the compiler in PATH is necessary.
5.  **FFmpeg (Optional, for sending non-OGG audio as voice notes):**
    - The Go bridge can convert audio files (like MP3, WAV) to the `.ogg Opus` format required for sending playable WhatsApp _voice_ messages. This requires `ffmpeg`.
    - Download from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
    - **Ensure the `ffmpeg` executable is in your system's `PATH`.**
    - If FFmpeg is not found, you can still send `.ogg Opus` files as voice notes, or other audio formats will be sent as regular file attachments using `send_media`.

## Installation

Install the package using pip:

```bash
pip install my-whatsapp-pkg # Replace with the actual name on PyPI if different
```

Or, if installing from a local source directory:

```bash
pip install .
```

## Setup (First Run Experience)

The first time you initialize the `WhatsappClient`, it will perform several setup steps automatically:

1.  **Prerequisite Check:** It verifies if `go` and `git` commands are accessible in your PATH. If not, it will raise a `PrerequisitesError`.
2.  **Repository Clone:** It checks for the presence of the `whatsapp-mcp` Go bridge code in its data directory (default: `~/.shubh_whatsapp_data` on Linux/macOS, `%APPDATA%\ShubhWhatsApp` on Windows). If not found, it clones the repository from GitHub using `git`.
    ```
    # Console Output Example during cloning:
    Using data directory: /home/user/.shubh_whatsapp_data
    --- Running Setup ---
    Prerequisites (Go, Git) found.
    Whatsapp-mcp repository not found.
    Cloning repository 'https://github.com/lharries/whatsapp-mcp.git' into '/home/user/.shubh_whatsapp_data/whatsapp-mcp'...
    Running command: git clone https://github.com/lharries/whatsapp-mcp.git /home/user/.shubh_whatsapp_data/whatsapp-mcp
    Command stdout:
    Cloning into '/home/user/.shubh_whatsapp_data/whatsapp-mcp'...
    ... (git clone output) ...
    Repository cloned successfully.
    --- Setup Complete ---
    ```
3.  **Go Bridge Startup:** The client then attempts to start the Go bridge process in the background.
4.  **Authentication (QR Code):** The Go bridge connects to WhatsApp.

    - If it's the **first time** connecting this bridge to your account, or if your session has expired, the Go bridge will generate a QR code.
    - The Python client monitors the bridge's output. When it detects the QR code prompt, it will print a message like this in _your_ console:

      ```
      # Console Output Example needing QR Scan:
      [Bridge STDOUT] Starting WhatsApp client...
      [Bridge STDOUT]
      [Bridge STDOUT] Scan this QR code with your WhatsApp app:
      [Bridge STDOUT] ########################################
      [Bridge STDOUT] #       ██████████████████████████       #
      [Bridge STDOUT] #       █ ▄▄▄▄▄ █▄██▄██▄█ ▄▄▄▄▄ █       #
      [Bridge STDOUT] #       ... (rest of QR code blocks) ... #
      [Bridge STDOUT] ########################################

      ========================================
      !!! ACTION REQUIRED: SCAN QR CODE !!!
      Please scan the QR code printed above using your WhatsApp app
      (Settings > Linked Devices > Link a Device)
      Waiting for connection after scan...
      ========================================
      ```

      <!-- Placeholder for Screenshot 1 -->
      <!-- [Screenshot of terminal showing QR code prompt] -->

    - **Action:** You need to open WhatsApp on your phone, go to `Settings` > `Linked Devices` > `Link a Device`, and scan the QR code displayed in the terminal where your Python script is running.

      <!-- Placeholder for Screenshot 2 -->
      <!-- [Screenshot of WhatsApp Linked Devices screen on phone] -->

    - Once scanned, the Go bridge will authenticate, and the Python client will detect the connection success message:

      ```
      # Console Output Example after successful scan:
      [Bridge STDOUT] Successfully connected and authenticated!
      [Bridge STDOUT] Connected to WhatsApp!
      [Bridge STDOUT] Starting REST API server on :8080...
      [Bridge STDOUT] REST server is running. Press Ctrl+C to disconnect and exit.

      ****************************************
      Bridge connected successfully!
      ****************************************
      ```

    - If you are **already authenticated** (e.g., you ran it recently), the bridge will connect directly without showing a QR code, and you'll see the "Bridge connected successfully!" message sooner.
    - The client waits for a confirmation message or the QR code prompt for a configurable timeout (default 180 seconds). If neither happens, it raises a `BridgeError`.

## Usage

```python
from my_whatsapp_pkg import WhatsappClient, WhatsappPkgError, BridgeError
import time
import os
from pathlib import Path

# --- Initialization ---
# Best practice: Use a try-finally block to ensure disconnection
client = None
try:
    print("Initializing WhatsApp Client...")
    # On first run, this handles setup and waits for connection/QR scan
    client = WhatsappClient(auto_setup=True, auto_connect=True)
    print("Client initialized and bridge connected.")

    # --- Sending Text ---
    recipient_number = "91xxxxxxxxxx" # Replace with target phone number
    # Or use JID for groups/contacts: "xxxxxxxxxx@s.whatsapp.net" or "xxxx-yyyy@g.us"
    print(f"\nSending text to {recipient_number}...")
    if client.send_message(recipient_number, "Hello from the Python Package! 😊"):
        print("Text sent.")
    else:
        print("Failed to send text.")

    time.sleep(2) # Small pause

    # --- Sending Media ---
    # Create a dummy file for example, replace with your actual file path
    media_file = Path("./example_image.png") # Path relative to script
    # Make sure the file exists for the example to work!
    # Example: Create a dummy file if it doesn't exist
    if not media_file.exists():
         try:
             with open(media_file, "w") as f: f.write("dummy image data")
             print(f"Created dummy file: {media_file.resolve()}")
         except Exception as e:
              print(f"Could not create dummy file: {e}")

    if media_file.exists():
         print(f"\nSending media '{media_file.name}' to {recipient_number}...")
         # send_media needs the *absolute* path
         if client.send_media(recipient_number, str(media_file.resolve()), caption="Here's a test file!"):
             print("Media sent.")
         else:
             print("Failed to send media.")
    else:
         print(f"Skipping media send, file not found: {media_file}")

    # --- Receiving Messages (Polling) ---
    print("\nStarting message polling (checking every 20s for 1 minute)...")
    start_poll_time = time.monotonic()
    while time.monotonic() - start_poll_time < 60:
        if not client._bridge_manager.check_if_alive(): # Good practice to check bridge
             print("Bridge died. Stopping poll.")
             break

        print(f"[{time.strftime('%H:%M:%S')}] Checking for new messages...")
        # By default, get_new_messages attempts to download media for incoming messages
        new_msgs = client.get_new_messages(download_media=True)

        if new_msgs:
            print(f"--- Found {len(new_msgs)} New Message(s) ---")
            for msg in new_msgs:
                if msg['is_from_me']: continue # Skip messages sent by you

                local_ts_str = msg['timestamp'].astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
                sender = msg.get('sender', 'Unknown')
                chat = msg.get('chat_jid', 'Unknown Chat')
                content = msg.get('content', '')
                media_info = ""
                if msg.get('media_type'):
                     media_info = f" [{msg['media_type']}: {msg.get('filename', 'N/A')}]"
                     dl_path = msg.get('local_media_path')
                     if dl_path:
                          status = "Downloaded"
                          if "FAIL" in dl_path or "ERROR" in dl_path: status = dl_path # Show error status
                          else: status += f": {os.path.basename(dl_path)}"
                          media_info += f" ({status})"
                     else: media_info += " (Download Pending/Failed)"

                print(f"[{local_ts_str}] From: {sender} in Chat: {chat}")
                print(f"  Content: '{content}'{media_info}")
                print("-" * 10)
        else:
            print("No new messages.")

        time.sleep(20) # Wait before next poll

    print("\nFinished polling example.")

    # --- Manual Media Download (Example) ---
    # You would typically get message_id and chat_jid from a received message dictionary
    # msg_id_to_download = "ABCDEF12345" # Example ID from logs/received message
    # chat_jid_for_download = "91yyyyyyyyyy@s.whatsapp.net" # Example chat
    # print(f"\nAttempting manual download for msg {msg_id_to_download}...")
    # downloaded_path = client.download_media_manual(msg_id_to_download, chat_jid_for_download)
    # if downloaded_path:
    #     print(f"Manual download successful, file at: {downloaded_path}")
    # else:
    #     print("Manual download failed.")


except (WhatsappPkgError, BridgeError) as e:
    print(f"\nAn error occurred: {e}")
except KeyboardInterrupt:
    print("\nOperation interrupted by user.")
finally:
    # --- Clean Shutdown ---
    if client:
        print("\nDisconnecting bridge...")
        client.disconnect()
        print("Client disconnected.")

```

## API Reference

### `WhatsappClient(data_dir=None, auto_setup=True, auto_connect=True)`

- Initializes the client.
- `data_dir`: (Optional) Override the default directory for storing the Go bridge repo and database.
- `auto_setup`: (Default: `True`) Checks prerequisites and clones the repo if needed. Set to `False` if you manage the repo manually.
- `auto_connect`: (Default: `True`) Starts the Go bridge and waits for connection/QR scan. Set to `False` to start manually using `client.connect()`.

### `client.run_setup()`

- Manually triggers the prerequisite check and repository clone if needed. Raises `PrerequisitesError` or `SetupError` on failure.

### `client.connect(timeout_sec=180)`

- Manually starts the Go bridge process and waits for connection or QR prompt. Raises `BridgeError` on failure or timeout.

### `client.disconnect()`

- Stops the background Go bridge process gracefully.

### `client.send_message(recipient, message)`

- Sends a text message.
- `recipient` (str): Target phone number (e.g., "91...") or JID (`...s.whatsapp.net` or `...g.us`).
- `message` (str): The text content.
- Returns `True` on API success indication, `False` otherwise. Raises `BridgeError` if the bridge is not running.

### `client.send_media(recipient, file_path, caption="")`

- Sends a media file.
- `recipient` (str): Target phone number or JID.
- `file_path` (str): **Absolute path** to the image, video, audio, or document file.
- `caption` (str, optional): Text caption for the media.
- Returns `True` on API success indication, `False` otherwise. Raises `BridgeError` if the bridge is not running, `ApiError` if the file is not found.

### `client.get_new_messages(chat_jid_filter=None, download_media=True)`

- Polls the local database for messages received since the last call to this method.
- `chat_jid_filter` (str, optional): If provided, only returns messages from this specific chat JID.
- `download_media` (bool, default: `True`): If `True`, attempts to automatically download media for any new incoming messages using the Go bridge API. Download status/path will be in the `local_media_path` key of the message dictionary.
- Returns: A list of message dictionaries. Each dictionary contains keys like `id`, `chat_jid`, `sender`, `content`, `timestamp` (timezone-aware UTC datetime object), `is_from_me`, `media_type`, `filename`, `local_media_path` (if downloaded).
- Updates an internal timestamp, so the next call only gets newer messages. Raises `DbError` on database issues.

### `client.download_media_manual(message_id, chat_jid)`

- Manually triggers a download for a specific media message.
- `message_id` (str): The unique ID of the message containing the media (usually obtained from a message dictionary returned by `get_new_messages`).
- `chat_jid` (str): The JID of the chat the message belongs to.
- Returns: The absolute local path (str) where the media was saved if successful, or `None` on failure. Raises `BridgeError` if the bridge is not running.

## Error Handling

The package defines several custom exceptions inheriting from `WhatsappPkgError`:

- `PrerequisitesError`: Missing Go or Git.
- `SetupError`: Failed to clone the Go bridge repository.
- `BridgeError`: Issues starting, stopping, or communicating with the Go bridge process (e.g., timeout, unexpected exit, port conflict).
- `ApiError`: Errors during HTTP calls to the Go bridge's REST API (e.g., connection error, bad response, API reports failure).
- `DbError`: Errors reading from the SQLite database.

It's recommended to wrap client interactions in `try...except` blocks to handle these potential issues.

## How It Works

This package acts as a controller for the `whatsapp-mcp` Go bridge.

1.  **Setup:** Ensures Go, Git are present and clones the Go bridge source code.
2.  **Bridge Process:** Starts `whatsapp-bridge/main.go` as a background subprocess.
3.  **Communication:**
    - **Sending/Downloading:** Uses the `requests` library to make HTTP POST calls to the Go bridge's REST API (running on `http://localhost:8080`).
    - **Receiving/Reading:** Reads message history directly from the `messages.db` SQLite database (located within the cloned repo's `store` directory), which is populated by the Go bridge.
4.  **State:** The Python client keeps track of the last message timestamp checked to avoid reprocessing old messages.

## Contributing

Contributions are welcome! Please feel free to open an issue on GitHub to discuss bugs or feature requests, or submit a pull request. (Link to your contribution guidelines if you create them).

## Reporting Issues

Please report any bugs or issues you encounter by opening an issue on the [GitHub repository Issues page](https://github.com/yourusername/my_whatsapp_pkg/issues). Include details about your OS, Python version, Go version, steps to reproduce the issue, and any relevant console output or error messages.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```

---

```
