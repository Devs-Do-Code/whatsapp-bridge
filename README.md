# Whatsapp Bridge Python Library (`whatsapp-bridge`)

[![PyPI version](https://badge.fury.io/py/whatsapp.svg)](https://pypi.org/project/whatsapp-bridge/) <!-- Ensure this points to the correct PyPI page -->
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

A Python library providing a convenient wrapper to interact with your personal WhatsApp account. This package manages the underlying [whatsapp-mcp Go bridge](https://github.com/lharries/whatsapp-mcp), handling setup, process management, and providing Pythonic methods for sending messages, receiving messages, and handling media. 

It connects to your **personal WhatsApp account** directly via the Whatsapp web multidevice API (using the [whatsmeow](https://github.com/tulir/whatsmeow) library). All your messages are stored locally in a SQLite database and only sent to an LLM (such as Claude) when the agent accesses them through tools (which you control).

Here's an example of what you can do when it's connected to Claude.

**⚠️ Disclaimer:** This package interacts with WhatsApp using unofficial methods derived from WhatsApp Web, used by the underlying Go bridge. It is strongly recommended for educational purposes or personal, non-critical applications only. The developers of this package assume no responsibility for any consequences resulting from its use.

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

Install the package using pip. It's recommended to use the `-U` flag to ensure you always get the latest version:

```bash
pip install -U whatsapp-bridge
```

## Setup (First Run Experience)

When you initialize the `WhatsappClient` for the first time, it performs an automated setup process. Here's a breakdown of what happens, along with example console output (paths and details may vary slightly based on your OS):

**1. Initial Setup & Repository Cloning:**

- The client checks for prerequisites (`go`, `git`).
- It determines the data directory (e.g., `C:\Users\xxx\AppData\Roaming\Whatsapp` on Windows).
- If the `whatsapp-mcp` Go bridge repository isn't found in the data directory, it clones it from GitHub.

```
# Example Console Output (Setup & Clone):
INFO - Starting WhatsApp bot...
INFO - Bot started and polling for updates...
INFO - Attempting to initialize WhatsApp Client...
INFO - --- First Run Initialization ---
INFO - Using data directory: C:\Users\xxx\AppData\Roaming\Whatsapp
INFO - Database path: C:\Users\xxx\AppData\Roaming\Whatsapp\whatsapp-mcp\whatsapp-bridge\store\messages.db
INFO - Bridge path: C:\Users\xxx\AppData\Roaming\Whatsapp\whatsapp-mcp\whatsapp-bridge
INFO - -------------------------------
INFO - >>> Running Setup Check...
INFO - Prerequisites (Go, Git) found.
INFO - Whatsapp-mcp repository not found. Attempting to clone...
INFO - Cloning repository 'https://github.com/lharries/whatsapp-mcp.git' into 'C:\Users\xxx\AppData\Roaming\Whatsapp\whatsapp-mcp'...
Cloning into 'C:\Users\xxx\AppData\Roaming\Whatsapp\whatsapp-mcp'...
... (git clone output) ...
INFO - Repository cloned successfully.
INFO - >>> Setup Check Complete.
```

**2. Go Bridge Startup:**

- The client starts the Go bridge process (`go run main.go`) in the background from the cloned repository's `whatsapp-bridge` directory.
- It monitors the bridge's output.

```
# Example Console Output (Bridge Start):
INFO - Starting Go bridge process...
INFO - Starting Go bridge: go run main.go in C:\Users\xxx\AppData\Roaming\Whatsapp\whatsapp-mcp\whatsapp-bridge
INFO - Bridge process started with PID: xxxxx
INFO - Waiting up to 180s for bridge connection or QR Code prompt...
INFO - [Bridge STDOUT] xx:xx:xx.xxx [Client INFO] Starting WhatsApp client...
INFO - [Bridge STDOUT] xx:xx:xx.xxx [Database INFO] Upgrading database to v1
... (database upgrade messages) ...
INFO - [Bridge STDOUT] xx:xx:xx.xxx [Database INFO] Upgrading database to v6
```

**3. Authentication (QR Code Scan):**

- If this is the first time connecting this instance to your WhatsApp account, or if the session has expired, the Go bridge will output a QR code.
- The Python client detects this and displays it in your terminal, prompting you to scan it.

```
# Example Console Output (QR Code Prompt):
INFO - [Bridge STDOUT]
INFO - [Bridge STDOUT] Scan this QR code with your WhatsApp app:
█████████████████████████████████████████████████████████████████
█████████████████████████████████████████████████████████████████
████ ▄▄▄▄▄ ██▀ ▀█▄██  ██ ▄▄▄  ▄▄█▄▄ ▄  ▄   ▄█▄ ▄▄█▄ ██ ▄▄▄▄▄ ████
... (rest of QR code blocks) ...
████▄▄▄▄▄▄▄█▄▄██████▄▄▄▄▄▄▄██▄▄▄██▄▄███▄▄██▄▄▄▄▄▄██▄▄█▄▄▄██▄▄████
█████████████████████████████████████████████████████████████████
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
INFO -
============================================================
!!!!!!!!!!! ACTION REQUIRED: SCAN QR CODE ABOVE !!!!!!!!!!!!
 Please scan the QR code printed above using your WhatsApp app
        (Settings > Linked Devices > Link a Device)
            Waiting for connection after scan...
============================================================
```

- **Action Required:** Open WhatsApp on your phone, navigate to `Settings` > `Linked Devices` > `Link a Device`, and scan the QR code shown in your terminal.

**4. Connection Established:**

- After you successfully scan the QR code, the bridge authenticates with WhatsApp.
- The Python client detects the successful connection message from the bridge output.

```
# Example Console Output (Successful Connection):
INFO - [Bridge STDOUT] xx:xx:xx.xxx [Client INFO] Successfully paired 91xxxxxxxxxx:xx@s.whatsapp.net
INFO - [Bridge STDOUT]
INFO - [Bridge STDOUT] Successfully connected and authenticated!
INFO -
>>> Bridge connected successfully!

INFO - Successfully marked first run as completed in C:\Users\xxx\AppData\Roaming\Whatsapp\whatsapp_state\metadata.json
INFO - WhatsApp Client initialized and bridge connected successfully.
```

- If you were already authenticated from a recent run, the QR code step will be skipped, and you'll see the "Bridge connected successfully!" message more quickly.
- The client waits for connection confirmation or the QR prompt for a configurable timeout (default 180 seconds). If neither occurs, a `BridgeError` is raised.

**5. Ready for Operations:**

- Once the bridge is connected, the client is ready to send/receive messages. The example below shows log output when a message is received by a running bot.

```
# Example Console Output (Receiving a Message):
INFO - Determining initial message check timestamp from database...
INFO - No DB timestamp found. Starting poll from YYYY-MM-DDTHH:MM:SS.ffffff+00:00 (last minute).
INFO - Starting polling loop with interval: 1s
INFO - Received update: {'id': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'chat_jid': '91yyyyyyyyyy@s.whatsapp.net', 'sender': '91yyyyyyyyyy', 'content': 'Hello', 'timestamp': datetime.datetime(YYYY, M, D, H, M, S, tzinfo=datetime.timezone.utc), 'is_from_me': False, 'media_type': '', 'filename': '', 'needs_download': False}
INFO - Echoing message back to chat 91yyyyyyyyyy@s.whatsapp.net: 'Hello'
```

## Usage

Here's a basic example demonstrating initialization, sending messages/media, and polling for new messages:

```python
import logging
from whatsapp_bridge.bot import ApplicationBuilder, MessageHandler, TypeHandler
from whatsapp_bridge.bot import TextFilter

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__) 


async def log_update(update, context):
    """Logs any incoming update."""
    logger.info(f"Received update: {update.message}")


async def echo(update, context):
    """Echoes the user's text message."""
    if update.message and update.message.get("content"):
        chat_id = update.message.get("chat_jid")
        text = update.message.get("content")
        logger.info(f"Echoing message back to chat {chat_id}: '{text}'")
        # context.bot.send_message(chat_id, text)
    else:
        logger.warning(f"Received non-text message or non-message update: {update}")


def main():
    logger.info("Starting WhatsApp bot...")
    application = ApplicationBuilder().build()


    application.add_handler(TypeHandler(log_update), group=-1)
    echo_handler = MessageHandler(TextFilter(), echo)

    application.add_handler(echo_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
```

## API Reference

### `WhatsappClient(data_dir=None, auto_setup=True, auto_connect=True, bridge_timeout_sec=180)`

- Initializes the client.
- `data_dir` (str, optional): Override the default directory for storing the Go bridge repo, database, and state (e.g., `C:\Users\xxx\AppData\Roaming\Whatsapp`).
- `auto_setup` (bool, default: `True`): Checks prerequisites and clones the repo if needed during initialization. Set to `False` if you manage the repo manually.
- `auto_connect` (bool, default: `True`): Starts the Go bridge and waits for connection/QR scan during initialization. Set to `False` to start manually using `client.connect()`.
- `bridge_timeout_sec` (int, default: 180): How long (in seconds) to wait for the bridge to signal connection or QR prompt during `connect()` or initialization with `auto_connect=True`.

### `client.run_setup()`

- Manually triggers the prerequisite check and repository clone if needed. Raises `PrerequisitesError` or `SetupError` on failure.

### `client.connect()`

- Manually starts the Go bridge process (if not already running) and waits up to `bridge_timeout_sec` for connection or QR prompt. Raises `BridgeError` on failure or timeout. Does nothing if already connected.

### `client.disconnect()`

- Stops the background Go bridge process gracefully.

### `client.send_message(recipient, message)`

- Sends a text message.
- `recipient` (str): Target phone number (e.g., "91...") or JID (`...s.whatsapp.net` or `...g.us`).
- `message` (str): The text content.
- Returns `True` if the bridge API confirms sending, `False` otherwise. Raises `BridgeError` if the bridge is not running or `ApiError` on communication issues.

### `client.send_media(recipient, file_path, caption="")`

- Sends a media file.
- `recipient` (str): Target phone number or JID.
- `file_path` (str): **Absolute path** to the image, video, audio, or document file.
- `caption` (str, optional): Text caption for the media.
- Returns `True` if the bridge API confirms sending, `False` otherwise. Raises `BridgeError` if the bridge is not running, `ApiError` on communication issues or if the file is not found locally.

### `client.get_new_messages(chat_jid_filter=None, download_media=True)`

- Polls the local database for messages received since the last call to this method.
- `chat_jid_filter` (str, optional): If provided, only returns messages from this specific chat JID.
- `download_media` (bool, default: `True`): If `True`, attempts to automatically download media for any new incoming messages using the Go bridge API. Download status/path will be in the `local_media_path` key of the message dictionary.
- Returns: A list of message dictionaries. Each dictionary contains keys like `id` (str), `chat_jid` (str), `sender` (str), `content` (str), `timestamp` (timezone-aware UTC `datetime` object), `is_from_me` (bool), `media_type` (str, e.g., 'image', 'video', 'audio', 'document', or empty), `filename` (str, original filename if available), `needs_download` (bool, indicates if media exists but hasn't been downloaded), `local_media_path` (str, absolute path if `download_media=True` and successful, otherwise may contain error info or be None).
- Updates an internal timestamp, so the next call only gets newer messages. Raises `DbError` on database issues, `ApiError` if `download_media=True` and bridge communication fails.

### `client.download_media_manual(message_id, chat_jid)`

- Manually triggers a download for a specific media message.
- `message_id` (str): The unique ID of the message containing the media (usually obtained from a message dictionary returned by `get_new_messages`).
- `chat_jid` (str): The JID of the chat the message belongs to.
- Returns: The absolute local path (str) where the media was saved if successful, or `None` on failure (e.g., message not found, not media, download failed). Raises `BridgeError` if the bridge is not running, `ApiError` on communication issues.

### `client.is_bridge_alive()`

- Checks if the background Go bridge process is currently running.
- Returns `True` if running, `False` otherwise.

## Error Handling

The package defines several custom exceptions inheriting from a base `WhatsappError`:

- `PrerequisitesError`: Missing Go or Git executable in PATH.
- `SetupError`: Failed to clone the Go bridge repository or perform other setup tasks.
- `BridgeError`: Issues starting, stopping, or communicating with the Go bridge process (e.g., connection timeout during startup, unexpected exit, port conflict).
- `ApiError`: Errors during HTTP calls to the Go bridge's REST API (e.g., network connection error, non-200 status code, API reports an internal failure).
- `DbError`: Errors reading from or writing to the SQLite database (`messages.db`).

It's recommended to wrap client interactions in `try...except` blocks to handle these specific errors, as shown in the Usage example. Catching the base `WhatsappError` can handle any package-specific issue.

## How It Works

This package acts as a controller for the `whatsapp-mcp` Go bridge.

1.  **Setup:** Ensures Go, Git are present and clones the Go bridge source code.
2.  **Bridge Process:** Starts `whatsapp-bridge/main.go` as a background subprocess.
3.  **Communication:**
    - **Sending/Downloading:** Uses the `requests` library to make HTTP POST calls to the Go bridge's REST API (running on `http://localhost:8080`).
    - **Receiving/Reading:** Reads message history directly from the `messages.db` SQLite database (located within the cloned repo's `store` directory), which is populated by the Go bridge.
4.  **State:** The Python client keeps track of the last message timestamp checked to avoid reprocessing old messages.

## Contributing

Contributions are welcome! Please feel free to open an issue on the GitHub repository to discuss bugs or feature requests, or submit a pull request. (Consider adding a `CONTRIBUTING.md` file with guidelines).

## Reporting Issues

Please report any bugs or issues you encounter by opening an issue on the [GitHub repository Issues page](https://github.com/lharries/whatsapp-mcp/issues). <!-- UPDATE THIS LINK if the Python package has its own repo --> Include details about your OS, Python version, Go version, steps to reproduce the issue, and any relevant console output or error messages (masking personal info like phone numbers or JIDs).

## License

This project is licensed under the Mozilla Public License 2.0 License - see the [LICENSE](LICENSE) file for details.
