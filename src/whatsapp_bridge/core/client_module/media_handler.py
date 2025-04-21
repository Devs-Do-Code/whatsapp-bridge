"""
Media Handler

This module provides functions for downloading and managing media files
from WhatsApp messages via the Go bridge API.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from ...config import settings
from ...api import client as api_client
from ...exceptions import ApiError

log = logging.getLogger(__name__)


def download_media(bridge_manager, message_id: str, chat_jid: str) -> Optional[str]:
    """
    Downloads media from a message via the API and saves it locally.

    This function delegates the media download API call to the `api_client`
    and then handles saving the downloaded file to the configured local
    media directory (`settings.DOWNLOADED_MEDIA_DIR`). It includes basic
    filename sanitization and error handling for the download and copy process.

    Parameters
    ----------
    bridge_manager : BridgeManager
        The bridge manager instance to check connection status.
    message_id : str
        The ID of the message containing the media to download.
    chat_jid : str
        The JID of the chat containing the message.

    Returns
    -------
    Optional[str]
        The absolute path (as a string) to the locally saved file if the
        download and save operations were successful. Returns a status
        string indicating failure if the Go bridge is not running, the
        API call fails, the downloaded file is invalid, or copying fails.
        Returns None if the bridge is not alive.

    Raises
    ------
    ApiError
        If an error occurs during the API call to download media.
    Exception
        For any unexpected errors during the download or save process.
    """
    if not bridge_manager.check_if_alive():
        log.error("Go bridge is not running. Cannot download media.")
        return "Download FAILED: Bridge not running"

    try:
        dl_result = api_client.download_media_api(message_id, chat_jid)
        if dl_result.get("success") and dl_result.get("path"):
            source_path_str = dl_result["path"]
            source_path = Path(source_path_str)

            if not source_path.is_file():
                log.error(f"API reported success but download path is invalid: {source_path_str}")
                return f"Download FAILED: Invalid path from API ({source_path_str})"

            filename = dl_result.get("filename", source_path.name)
            safe_filename = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in filename)
            if not safe_filename:
                safe_filename = f"downloaded_media_{message_id}"

            local_dest = settings.DOWNLOADED_MEDIA_DIR / safe_filename

            try:
                # Ensure the media directory exists
                settings.DOWNLOADED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
                # Copy the downloaded file to our media directory
                shutil.copy2(source_path, local_dest)
                log.info(f"Media downloaded and saved to: {local_dest}")
                return str(local_dest)
            except OSError as e:
                log.error(f"Failed to copy downloaded media from {source_path} to {local_dest}: {e}", exc_info=True)
                return f"Download FAILED: Copy error ({e})"
        else:
            error_msg = dl_result.get("message", "Unknown API error")
            log.error(f"API Error downloading media: {error_msg}")
            return f"Download FAILED: API error ({error_msg})"
    except ApiError as e:
        log.error(f"Error downloading media via API: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"Unexpected error downloading media: {e}", exc_info=True)
        raise
