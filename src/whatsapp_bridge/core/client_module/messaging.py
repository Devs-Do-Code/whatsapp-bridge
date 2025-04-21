"""
Messaging Module

This module provides functions for sending text messages and media files
via the WhatsApp Go bridge API.
"""

import logging
from typing import Dict, Any

from ...api import client as api_client
from ...exceptions import ApiError

log = logging.getLogger(__name__)


def send_message(bridge_manager, recipient: str, message: str) -> bool:
    """
    Sends a text message to a specified recipient via the Go bridge API.

    Parameters
    ----------
    bridge_manager : BridgeManager
        The bridge manager instance to check connection status.
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
    if not bridge_manager.check_if_alive():
        log.error("Go bridge is not running. Cannot send message.")
        return False
    try:
        result = api_client.send_message_api(recipient, message)
        success = result.get("success", False)
        if not success:
            log.error(f"API Error sending message: {result.get('message', 'Unknown API error')}")
        return success
    except ApiError as e:
        log.error(f"Error sending message via API: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"Unexpected error sending message: {e}", exc_info=True)
        raise


def send_media(bridge_manager, recipient: str, file_path: str, caption: str = "") -> bool:
    """
    Sends a media file (image, video, or document) to a recipient.

    This method sends a local file to the specified recipient via the
    Go bridge API. The type of media sent is determined by the file
    extension.

    Parameters
    ----------
    bridge_manager : BridgeManager
        The bridge manager instance to check connection status.
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
    if not bridge_manager.check_if_alive():
        log.error("Go bridge is not running. Cannot send media.")
        return False
    try:
        result = api_client.send_media_api(recipient, file_path, caption)
        success = result.get("success", False)
        if not success:
            log.error(f"API Error sending media: {result.get('message', 'Unknown API error')}")
        return success
    except ApiError as e:
        log.error(f"Error sending media via API: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"Unexpected error sending media: {e}", exc_info=True)
        raise
