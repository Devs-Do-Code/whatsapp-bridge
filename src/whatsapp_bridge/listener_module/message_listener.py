"""
Message Listener

This module provides the MessageListener class for continuously polling
and processing new messages received by the WhatsApp client.
"""

import time
import logging
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

from ..core.client_module import WhatsappClient
from ..exceptions import WhatsappPkgError, BridgeError, ApiError

log = logging.getLogger(__name__)

# Base directory for storing downloaded media files relative to the CWD
BASE_DATA_DIR = Path("Data")
# Default interval in seconds for polling the bridge for new messages
DEFAULT_POLL_INTERVAL = 1


class MessageListener:
    """
    Listens for and processes new messages from the WhatsApp client.

    This class manages the lifecycle of the WhatsApp client connection,
    periodically polls for incoming messages, and handles the initial
    processing of these messages, including the download and organization
    of associated media files.

    Attributes
    ----------
    client : Optional[WhatsappClient]
        The initialized WhatsApp client instance used for communication
        with the Go bridge. It is None before successful initialization.
    poll_interval : int
        The duration in seconds to wait between consecutive polls for new
        messages.
    """

    def __init__(self, poll_interval: int = DEFAULT_POLL_INTERVAL):
        """
        Initializes a new instance of the MessageListener.

        Parameters
        ----------
        poll_interval : int, optional
            The interval in seconds for polling the WhatsApp bridge for new
            messages. Defaults to the value of :attr:`DEFAULT_POLL_INTERVAL`.
        """
        self.client: Optional[WhatsappClient] = None
        self.poll_interval: int = poll_interval
        self._running: bool = False
        log.debug(f"MessageListener initialized with poll_interval={poll_interval}s")

    def _initialize_client(self) -> bool:
        """
        Initializes and connects the WhatsApp client.

        Attempts to create a new :class:`.WhatsappClient` instance and connect
        to the WhatsApp bridge. This method handles potential errors during
        setup and connection, logging the outcome.

        Returns
        -------
        bool
            True if initialization and connection were successful, False otherwise.

        Raises
        ------
        WhatsappPkgError
            If a package-specific error occurs during initialization.
        BridgeError
            If an error related to the Go bridge occurs during initialization.
        ApiError
            If an API communication error occurs during initialization.
        Exception
            For any other unexpected errors during initialization.
        """
        log.info("Attempting to initialize WhatsApp Client...")
        try:
            # auto_setup and auto_connect handle the complexities of bridge setup and connection
            self.client = WhatsappClient(auto_setup=True, auto_connect=True)
            log.info("WhatsApp Client initialized and bridge connected successfully.")
            return True
        except (WhatsappPkgError, BridgeError, ApiError) as e:
            log.error(f"Failed to initialize WhatsApp Client: {e}", exc_info=True)
            return False
        except Exception as e:
            log.critical(f"An unexpected critical error occurred during WhatsApp Client initialization: {e}", exc_info=True)
            return False
            
    def _process_message(self, msg: Dict[str, Any]) -> None:
        """
        Processes a single incoming message dictionary received from the client API.

        Extracts relevant information, attempts contact name resolution, logs
        message details, and handles the download and organization of associated
        media files for incoming messages. Errors during processing a single
        message are caught and logged to prevent halting the listener loop.

        Parameters
        ----------
        msg : dict
            The raw message data dictionary from the WhatsApp client API.
            Expected structure includes keys like 'timestamp', 'sender',
            'chat_jid', 'content', 'media_type', 'local_media_path',
            'filename', and 'is_from_me'.

        Notes
        -----
        Media files are processed and moved only for incoming messages
        ('is_from_me' is False) with valid media details and a successful
        download at 'local_media_path'. Downloaded media is organized into
        chat-specific subdirectories within the :attr:`BASE_DATA_DIR`.

        Raises
        ------
        Exception
            Catches and logs any unexpected exceptions during message processing
            to ensure listener loop stability.
        """
        try:
            local_timestamp: Optional[datetime] = msg.get("timestamp")
            sender_jid: str = msg.get("sender", "Unknown_Sender")
            chat_jid: str = msg.get("chat_jid", "Unknown_Chat")
            content: str = msg.get("content", "")
            media_type: Optional[str] = msg.get("media_type")
            original_media_path_str: Optional[str] = msg.get("local_media_path")
            media_filename: Optional[str] = msg.get("filename")
            is_from_me: bool = msg.get("is_from_me", False)

            # Format timestamp for consistent logging output across different timezones.
            local_timestamp_str = (
                local_timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
                if isinstance(local_timestamp, datetime) and local_timestamp.tzinfo
                else "N/A"
            )

            contact_name = sender_jid
            # Attempt contact lookup only if the client is initialized and the sender_jid appears valid.
            if self.client and sender_jid and sender_jid != "Unknown_Sender":
                try:
                    contact_info = self.client.get_contact_info(sender_jid)
                    if contact_info and contact_info.get("name"):
                        contact_name = contact_info["name"]
                    elif msg.get("sender_name"):
                         contact_name = msg.get("sender_name")
                except AttributeError:
                    log.debug(
                        "Client object does not have a 'get_contact_info' method. Cannot look up contact name."
                    )
                except Exception as e:
                    log.warning(
                        f"Failed to lookup contact name for {sender_jid}: {e}. Using JID or message data name.",
                        exc_info=True
                    )
            elif msg.get("sender_name"):
                 contact_name = msg.get("sender_name")


            log.info("--- New Message Received ---")
            log.info(f"  Timestamp: {local_timestamp_str}")
            log.info(f"  Chat JID: {chat_jid}")
            log.info(f"  Sender: {contact_name} ({sender_jid})")
            log.info(f"  Is From Me: {is_from_me}")
            log.info(f"  Content: '{content}'")

            media_log_info = "No media attached."
            # Process media only if it's an incoming message (not from self) and media details are present.
            if media_type and original_media_path_str and media_filename and not is_from_me:
                original_media_path = Path(original_media_path_str)
                media_log_info = f"Media Type: {media_type}, Filename: {media_filename}"

                # Check if the original media path indicates a successful download and the file actually exists.
                if (
                    "FAILED" not in original_media_path_str.upper()
                    and "ERROR" not in original_media_path_str.upper()
                    and original_media_path.is_file()
                ):
                    # Construct the target directory path based on the chat JID for organization.
                    target_chat_dir = BASE_DATA_DIR / chat_jid
                    try:
                        # Ensure the chat-specific target directory exists before moving the file.
                        target_chat_dir.mkdir(parents=True, exist_ok=True)
                        log.debug(f"Ensured directory exists: {target_chat_dir}")
                    except OSError as e:
                        log.error(
                            f"Failed to create directory {target_chat_dir} for media: {e}",
                            exc_info=True,
                        )
                        media_log_info += " (Error creating target directory)"
                    else:
                        # Construct the final path for the moved media file within the chat directory.
                        new_media_path = target_chat_dir / media_filename
                        try:
                            # Copy the file to the target directory.
                            shutil.copy2(original_media_path, new_media_path)
                            media_log_info += f", Saved to: {new_media_path}"
                            log.debug(f"Copied media from {original_media_path} to {new_media_path}")
                        except OSError as e:
                            log.error(
                                f"Failed to copy media from {original_media_path} to {new_media_path}: {e}",
                                exc_info=True,
                            )
                            media_log_info += f" (Error copying: {e})"
                else:
                    # Log issues with the original media path.
                    if "FAILED" in original_media_path_str.upper() or "ERROR" in original_media_path_str.upper():
                        media_log_info += f", Download failed: {original_media_path_str}"
                    elif not original_media_path.is_file():
                        media_log_info += f", File not found: {original_media_path_str}"

            log.info(f"  Media: {media_log_info}")
            log.info("-----------------------------")

        except Exception as e:
            # Catch and log any unexpected errors during message processing.
            # This ensures that a single message processing failure doesn't halt the entire listener.
            log.error(f"Error processing message: {e}", exc_info=True)
