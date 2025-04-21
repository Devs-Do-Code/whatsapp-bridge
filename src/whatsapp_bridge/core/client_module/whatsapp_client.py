"""
WhatsApp Client

This module provides the core WhatsappClient class for interacting with WhatsApp
via the Go bridge. It handles client initialization, connection management,
and provides the primary interface for sending messages and media.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from ...config import settings
from ...bridge.manager_module import BridgeManager
from ...exceptions import (
    PrerequisitesError, SetupError, BridgeError, ApiError, WhatsappPkgError
)
from ..connection_module import run_setup, ConnectionManager
from ...state.manager import is_first_run, mark_first_run_completed

log = logging.getLogger(__name__)


class WhatsappClient:
    """
    High-level client class to interact with WhatsApp via the Go bridge.

    This class encapsulates the functionality required to use the WhatsApp
    Go bridge. It manages the bridge process lifecycle, handles connections,
    and provides a user-friendly interface for sending messages and media,
    as well as retrieving new messages from the local database.
    """

    def __init__(self, data_dir: Optional[str] = None, auto_setup: bool = True, auto_connect: bool = True) -> None:
        """
        Initializes the WhatsappClient.

        Parameters
        ----------
        data_dir : Optional[str], optional
            Optional path to override the default data storage directory.
            Note: Setting this via the WHATSAPP_PKG_DATA_DIR environment
            variable before importing the package is the recommended approach
            for ensuring consistency across different sessions and scripts.
            If provided here, it will override the environment variable setting.
            Defaults to None.
        auto_setup : bool, optional
            If True, automatically checks system prerequisites (Go, Git) and
            clones the `whatsapp-mcp` repository if it is not already present.
            Set to False to skip this check and assume prerequisites are met
            and the repository is cloned. Defaults to True.
        auto_connect : bool, optional
            If True, automatically starts the Go bridge process and attempts
            to establish a connection to WhatsApp upon initialization.
            Set to False to require manual connection via the `connect()`
            method. Defaults to True.

        Raises
        ------
        WhatsappPkgError
            If initialization, setup, or connection fails due to underlying
            issues such as missing prerequisites, failure to clone the
            repository, or errors during the bridge process startup or
            connection attempt.
        """
        log.debug("Initializing WhatsappClient...")
        # If data_dir is provided at runtime, override settings.DATA_DIR and related paths.
        # This should ideally be set via environment variable before package import.
        if data_dir:
            log.warning(f"'data_dir' provided at runtime ({data_dir}). "
                        f"Overriding the default/environment setting ({settings.DATA_DIR}). "
                        "It's recommended to set the WHATSAPP_PKG_DATA_DIR environment variable "
                        "before importing for consistency.")

            settings.DATA_DIR = Path(data_dir)
            settings.CLONED_REPO_PATH = settings.DATA_DIR / "whatsapp-mcp"
            settings.GO_BRIDGE_DIR = settings.CLONED_REPO_PATH / "whatsapp-bridge"
            settings.DB_PATH = settings.GO_BRIDGE_DIR / "store" / "messages.db"
            settings.GO_BRIDGE_SRC_PATH = settings.GO_BRIDGE_DIR / "main.go"
            settings.DOWNLOADED_MEDIA_DIR = settings.DATA_DIR / "downloaded_media"
            try:
                settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise SetupError(f"Failed to create provided data directory {settings.DATA_DIR}: {e}") from e

        self._is_first_run = is_first_run()

        if self._is_first_run:
            log.info("--- First Run Initialization ---")
            log.info(f"Using data directory: {settings.DATA_DIR}")
            log.info(f"Database path: {settings.DB_PATH}")
            log.info(f"Bridge path: {settings.GO_BRIDGE_DIR}")
            log.info("-------------------------------")

        self._bridge_manager = BridgeManager()

        # ConnectionManager handles the lifecycle of the Go bridge and connection status.
        self._connection_manager = ConnectionManager(self._bridge_manager, self.disconnect, is_first_run=self._is_first_run)
        # Initialize to None. Will be set on the first successful call to get_new_messages.
        self._last_message_check_time = None

        # Run setup steps if auto_setup is True (checks prerequisites, clones repo).
        if auto_setup:
            try:
                run_setup(is_first_run=self._is_first_run)
            except (PrerequisitesError, SetupError) as e:
                log.error(f"Setup failed: {e}", exc_info=True)
                # Re-raise as WhatsappPkgError for consistent top-level exception handling
                raise WhatsappPkgError(f"Setup failed: {e}") from e

        # Attempt to connect to the Go bridge if auto_connect is True.
        if auto_connect:
            try:
                self.connect()
            except BridgeError as e:
                log.error(f"Auto-connect failed: {e}", exc_info=True)
                self.disconnect() # Ensure bridge is stopped on auto-connect failure
                # Re-raise as WhatsappPkgError for consistent top-level exception handling
                raise WhatsappPkgError(f"Auto-connect failed: {e}") from e

        # Mark first run as completed after successful initialization and optional setup/connect.
        if self._is_first_run:
            mark_first_run_completed()

    def connect(self, timeout_sec: int = 180) -> None:
        """
        Starts the Go bridge process and waits for connection or QR code prompt.

        This method initiates the connection process to WhatsApp by starting
        the underlying Go bridge process. It waits for either a successful
        connection confirmation or a prompt to scan a QR code for linking a
        device, up to the specified timeout.

        Parameters
        ----------
        timeout_sec : int, optional
            The maximum time in seconds to wait for the bridge to report a
            successful connection or display a QR code. Defaults to 180 seconds.

        Raises
        ------
        BridgeError
            If the bridge process fails to start, exits unexpectedly during
            startup, or if the connection attempt times out without
            successfully connecting or displaying a QR code.
        """
        self._connection_manager.connect(timeout_sec=timeout_sec)

    def disconnect(self) -> None:
        """
        Stops the running Go bridge process and cleans up resources.

        This method should be called when the `WhatsappClient` instance is no
        longer needed to properly shut down the background Go bridge process
        and release any associated system resources.
        """
        self._bridge_manager.stop()
        
    def send_message(self, recipient: str, message: str) -> bool:
        """
        Sends a text message to a specified recipient via the Go bridge API.

        Parameters
        ----------
        recipient : str
            The recipient's identifier. This can be a phone number (with
            country code, e.g., "1234567890", without any '+' symbol) or a JID
            (e.g., "1234567890@s.whatsapp.net" for a user or
            "1234567890-abcdef@g.us" for a group chat).
        message : str
            The text content of the message to send.

        Returns
        -------
        bool
            True if the API call to the Go bridge successfully queued the
            message for sending. False otherwise, which typically indicates
            an issue with the API request or the bridge.

        Raises
        ------
        ApiError
            If the underlying API call to the Go bridge fails due to a
            communication error or an error reported by the bridge.
        Exception
            For any unexpected errors encountered during the message sending process.
        """
        from .messaging import send_message
        return send_message(self._bridge_manager, recipient, message)
        
    def send_media(self, recipient: str, file_path: str, caption: str = "") -> bool:
        """
        Sends a media file (image, video, or document) to a recipient.

        This method sends a local file to the specified recipient via the
        Go bridge API. The type of media sent is determined by the file
        extension.

        Parameters
        ----------
        recipient : str
            The recipient's identifier (phone number or JID).
        file_path : str
            The local absolute path to the media file to send.
        caption : str, optional
            Optional caption text to accompany the media file. Defaults to "".

        Returns
        -------
        bool
            True if the API call to the Go bridge successfully queued the
            media file for sending. False otherwise.

        Raises
        ------
        ApiError
            If the underlying API call to the Go bridge fails.
        Exception
            For any unexpected errors during the media sending process.
        """
        from .messaging import send_media
        return send_media(self._bridge_manager, recipient, file_path, caption)
        
    def get_new_messages(self, chat_jid_filter: Optional[str] = None, download_media: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves new messages from the local database since the last check.

        This method queries the local SQLite message database managed by the
        Go bridge. It fetches messages received after the timestamp recorded
        during the last successful call to this method within the current
        `WhatsappClient` instance. On the first call, it defaults to checking
        messages from approximately one minute ago to avoid fetching the
        entire history.

        Parameters
        ----------
        chat_jid_filter : Optional[str], optional
            An optional JID string to filter the results, returning only
            messages from a specific chat. Defaults to None (no filtering).
        download_media : bool, optional
            If True, the method will automatically attempt to download media
            associated with new messages that require it. If successful,
            the local file path will be added under the 'local_media_path'
            key in the message dictionary. Defaults to True.

        Returns
        -------
        List[Dict[str, Any]]
            A list of dictionaries, where each dictionary represents a new
            message. Each message dictionary includes details retrieved from
            the database and may include a 'local_media_path' key if media
            was downloaded. Returns an empty list if no new messages are found,
            the database file does not exist, or an error occurs during
            retrieval or media download.

        Raises
        ------
        DbError
            If an error occurs while reading messages from the database.
        Exception
            For any unexpected errors during the message retrieval process.
        """
        from .message_handler import get_new_messages
        return get_new_messages(self, chat_jid_filter, download_media)
        
    def download_media_manual(self, message_id: str, chat_jid: str) -> Optional[str]:
        """
        Manually triggers media download for a specific message and saves it locally.

        This method provides a public interface to trigger the media download
        and local saving process for a specific message by its ID and chat JID.

        Parameters
        ----------
        message_id : str
            The ID of the message containing the media to download.
        chat_jid : str
            The JID of the chat containing the message.

        Returns
        -------
        Optional[str]
            The absolute path (as a string) to the locally saved file if successful.
            Returns a status string indicating failure if the Go bridge is not
            running, the API call fails, the downloaded file is invalid, or
            copying fails. Returns None if the bridge is not alive.
            The status string is intended for logging or user feedback.

        Raises
        ------
        ApiError
            If an error occurs during the API call to download media.
        Exception
            For any unexpected errors during the download or save process.
        """
        from .media_handler import download_media
        return download_media(self._bridge_manager, message_id, chat_jid)
