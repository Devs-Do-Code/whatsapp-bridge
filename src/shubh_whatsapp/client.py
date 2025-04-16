import time
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import shutil
from . import config
from . import bridge
from . import api_client
from . import db_reader
from .exceptions import PrerequisitesError, SetupError, BridgeError, ApiError, DbError

class WhatsappClient:
    """
    Client class to interact with WhatsApp via the Go bridge.
    Handles setup, bridge management, and provides methods for interaction.
    """
    def __init__(self, data_dir: Optional[str] = None, auto_setup: bool = True, auto_connect: bool = True):
        """
        Initializes the client.

        Args:
            data_dir: Optional path to store cloned repo and DB. Defaults to user-specific dir.
            auto_setup: If True, automatically checks prerequisites and clones repo if needed.
            auto_connect: If True, automatically starts the Go bridge on initialization.
        """
        if data_dir:
            config.DATA_DIR = Path(data_dir)
            # Re-derive paths if data_dir is overridden
            config.CLONED_REPO_PATH = config.DATA_DIR / "whatsapp-mcp"
            config.GO_BRIDGE_DIR = config.CLONED_REPO_PATH / "whatsapp-bridge"
            config.DB_PATH = config.GO_BRIDGE_DIR / "store" / "messages.db"
            config.GO_BRIDGE_SRC_PATH = config.GO_BRIDGE_DIR / "main.go"
            config.DATA_DIR.mkdir(parents=True, exist_ok=True) # Ensure overridden dir exists

        print(f"Using data directory: {config.DATA_DIR}")
        self._bridge_manager = bridge.BridgeManager()
        self._last_message_check_time = datetime.now(timezone.utc) - timedelta(minutes=10) # Start check reasonably far back

        if auto_setup:
            self.run_setup() # Check prereqs and clone if necessary

        if auto_connect:
            self.connect()

    def run_setup(self):
        """Checks prerequisites and clones the repository if needed."""
        print("--- Running Setup ---")
        missing = config.check_prerequisites()
        if missing:
            raise PrerequisitesError("Missing prerequisites:\n" + "\n".join(f"- {m}" for m in missing))
        print("Prerequisites (Go, Git) found.")

        if not config.is_repo_cloned():
            print("Whatsapp-mcp repository not found.")
            if not config.clone_repo():
                raise SetupError("Failed to clone the necessary repository.")
        else:
             print("Repository found.")
        print("--- Setup Complete ---")

    def connect(self, timeout_sec=180):
        """
        Starts the Go bridge and waits for connection or QR code prompt.

        Args:
            timeout_sec: How long to wait for connection confirmation or QR prompt.
        """
        if self._bridge_manager.is_running and self._bridge_manager.check_if_alive():
            print("Bridge is already running.")
            return

        print("Starting Go bridge process...")
        try:
            self._bridge_manager.start()
        except BridgeError as e:
             print(f"Error starting bridge: {e}")
             raise # Re-raise

        print(f"Waiting up to {timeout_sec}s for bridge connection or QR Code prompt...")
        start_time = time.monotonic()
        qr_code_detected = False
        connection_success = False

        while time.monotonic() - start_time < timeout_sec:
            if not self._bridge_manager.check_if_alive():
                 # Check if an error was detected during startup
                 last_err = self._bridge_manager.last_error
                 raise BridgeError(f"Bridge process exited unexpectedly during startup. Last error: {last_err or 'Unknown'}")

            stdout, stderr = self._bridge_manager.read_output()

            for line in stderr:
                print(f"[Bridge STDERR] {line.strip()}", file=sys.stderr)
                # Check for fatal startup errors in stderr
                if self._bridge_manager.last_error:
                     self.disconnect() # Stop the failed process
                     raise BridgeError(f"Bridge failed to start: {self._bridge_manager.last_error}")

            for line in stdout:
                print(f"[Bridge STDOUT] {line.strip()}")
                # Check for specific keywords indicating state
                if "Scan this QR code" in line or "github.com/mdp/qrterminal" in line:
                     print("\n" + "="*40)
                     print("!!! ACTION REQUIRED: SCAN QR CODE !!!")
                     print("Please scan the QR code printed above using your WhatsApp app")
                     print("(Settings > Linked Devices > Link a Device)")
                     print("Waiting for connection after scan...")
                     print("="*40 + "\n")
                     qr_code_detected = True
                     # Reset timeout slightly after QR code appears? Or keep overall timeout?
                     # start_time = time.monotonic() # Optional: Reset timer after QR

                if "Successfully connected and authenticated!" in line or "Connected to WhatsApp!" in line:
                     print("\n" + "*"*40)
                     print("Bridge connected successfully!")
                     print("*"*40 + "\n")
                     connection_success = True
                     break # Exit the waiting loop

                if "Starting REST API server on :8080" in line:
                     print("Bridge API server starting...")
                     # This often comes after connection success, but good to see

            if connection_success:
                break

            time.sleep(0.5) # Small delay to avoid busy-waiting

        if not connection_success:
             err_msg = "Timed out waiting for bridge connection."
             if qr_code_detected:
                  err_msg += " QR Code was shown, but connection confirmation wasn't received. Did you scan it?"
             self.disconnect() # Stop the non-responsive process
             raise BridgeError(err_msg)

    def disconnect(self):
        """Stops the Go bridge process."""
        self._bridge_manager.stop()

    def send_message(self, recipient: str, message: str) -> bool:
        """Sends a text message."""
        if not self._bridge_manager.check_if_alive():
             raise BridgeError("Go bridge is not running. Cannot send message.")
        try:
             result = api_client.send_message_api(recipient, message)
             return result.get("success", False)
        except ApiError as e:
             print(f"Error sending message: {e}")
             return False

    def send_media(self, recipient: str, file_path: str, caption: str = "") -> bool:
         """Sends a media file."""
         if not self._bridge_manager.check_if_alive():
              raise BridgeError("Go bridge is not running. Cannot send media.")
         try:
              result = api_client.send_media_api(recipient, file_path, caption)
              return result.get("success", False)
         except ApiError as e:
              print(f"Error sending media: {e}")
              return False

    def get_new_messages(self, chat_jid_filter: Optional[str] = None, download_media: bool = True) -> List[Dict[str, Any]]:
         """
         Gets new messages since the last check.

         Args:
             chat_jid_filter: Optional JID to filter for a specific chat.
             download_media: If True, automatically attempts to download media for new messages.

         Returns:
             A list of new message dictionaries. Updates internal timestamp.
         """
         if not config.DB_PATH.exists():
              # Don't raise error here, just warn and return empty
              print(f"Warning: Database path {config.DB_PATH} not found. Cannot get messages.")
              return []
         try:
              new_messages_list, new_last_ts = db_reader.get_messages_since_db(
                   self._last_message_check_time, chat_jid_filter
              )

              # Process downloads if requested
              if download_media and new_messages_list:
                  for msg_data in new_messages_list:
                      if msg_data.get("needs_download"):
                          print(f"Attempting auto-download for message ID: {msg_data['id']}")
                          try:
                              dl_result = api_client.download_media_api(msg_data['id'], msg_data['chat_jid'])
                              if dl_result.get("success") and dl_result.get("path"):
                                   # Copy file locally (optional, API already downloaded it)
                                   # This logic could be moved into api_client or stay here
                                   source_path = dl_result["path"]
                                   filename = dl_result.get("filename", os.path.basename(source_path))
                                   safe_filename = filename.replace(':', '_').replace('\\', '_').replace('/', '_')
                                   local_dest = config.DATA_DIR / "downloaded_media" / safe_filename
                                   local_dest.parent.mkdir(parents=True, exist_ok=True)
                                   try:
                                       shutil.copy2(source_path, local_dest) # copy2 preserves metadata
                                       msg_data["local_media_path"] = str(local_dest)
                                       print(f"Auto-downloaded and saved to: {local_dest}")
                                   except Exception as copy_e:
                                        print(f"Error copying downloaded file {source_path} to {local_dest}: {copy_e}")
                                        msg_data["local_media_path"] = f"Download OK, Copy FAILED: {source_path}"

                              else:
                                   print(f"Auto-download failed for msg {msg_data['id']}: {dl_result.get('message')}")
                                   msg_data["local_media_path"] = "Download FAILED"

                          except ApiError as dl_e:
                               print(f"API Error during auto-download for msg {msg_data['id']}: {dl_e}")
                               msg_data["local_media_path"] = f"Download API FAILED: {dl_e}"
                          except Exception as general_e:
                               print(f"Unexpected error during auto-download for msg {msg_data['id']}: {general_e}")
                               msg_data["local_media_path"] = "Download UNEXPECTED ERROR"


              # Update the last check time *after* processing
              self._last_message_check_time = new_last_ts + timedelta(milliseconds=1) # Add buffer

              return new_messages_list

         except DbError as e:
              print(f"Error reading messages from DB: {e}")
              return [] # Return empty list on DB error
         except Exception as e:
              print(f"Unexpected error getting new messages: {e}")
              return []

    def download_media_manual(self, message_id: str, chat_jid: str) -> Optional[str]:
        """Manually triggers media download and returns the local path."""
        if not self._bridge_manager.check_if_alive():
             raise BridgeError("Go bridge is not running. Cannot download media.")
        try:
            dl_result = api_client.download_media_api(message_id, chat_jid)
            if dl_result.get("success") and dl_result.get("path"):
                 source_path = dl_result["path"]
                 filename = dl_result.get("filename", os.path.basename(source_path))
                 safe_filename = filename.replace(':', '_').replace('\\', '_').replace('/', '_')
                 local_dest = config.DATA_DIR / "downloaded_media" / safe_filename
                 local_dest.parent.mkdir(parents=True, exist_ok=True)
                 try:
                     shutil.copy2(source_path, local_dest)
                     print(f"Manually downloaded and saved to: {local_dest}")
                     return str(local_dest)
                 except Exception as copy_e:
                      print(f"Error copying downloaded file {source_path} to {local_dest}: {copy_e}")
                      return f"Download OK, Copy FAILED: {source_path}" # Return source path maybe?
            else:
                 print(f"Manual download failed: {dl_result.get('message')}")
                 return None
        except ApiError as e:
             print(f"API Error during manual download: {e}")
             return None
        except Exception as e:
             print(f"Unexpected error during manual download: {e}")
             return None