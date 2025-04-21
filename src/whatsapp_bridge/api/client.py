"""
Go Bridge API Client

This module provides functions for interacting with the Go bridge API.
It handles making HTTP requests to the bridge endpoint and processing
responses, including error handling.
"""

import requests
import json
import os
import sys
import logging

from ..config import settings
from typing import Dict, Any

from ..config import settings
from ..exceptions import ApiError

log = logging.getLogger(__name__)


def _make_api_request(endpoint: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Helper function to make POST requests to the Go bridge API.

    Parameters
    ----------
    endpoint : str
        The API endpoint (e.g., "send", "download").
    payload : dict
        The JSON payload to send in the request body.
    timeout : int, optional
        The request timeout in seconds. Defaults to 30.

    Returns
    -------
    dict
        The JSON response from the API if the request is successful.

    Raises
    ------
    ApiError
        If the API request fails, times out, or returns an error status.
    requests.exceptions.RequestException
        If a network or other request error occurs (caught and re-raised as ApiError).
    json.JSONDecodeError
        If the response cannot be decoded as JSON (caught and re-raised as ApiError).
    """
    url = f"{settings.GO_BRIDGE_API_URL}/{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        result = response.json()
        if not result.get("success", False):
            error_message = result.get("message", "Unknown API error")
            log.error(f"API Error ({endpoint}): {error_message}")
            raise ApiError(f"API call '{endpoint}' failed: {error_message}")
        return result
    except requests.exceptions.Timeout:
        log.error(f"API Error ({endpoint}): Timeout after {timeout}s")
        raise ApiError(f"API call '{endpoint}' timed out after {timeout}s.") from None
    except requests.exceptions.ConnectionError as e:
        log.error(
            f"API Error ({endpoint}): Connection error for '{url}': {e}. Is the Go bridge running?",
            exc_info=True # Include traceback for connection errors
        )
        raise ApiError(
            f"API connection error for '{url}': {e}. Is the Go bridge running?"
        ) from e
    except requests.exceptions.RequestException as e:
        log.error(f"API Error ({endpoint}): Request error: {e}", exc_info=True)
        raise ApiError(f"API request error for '{endpoint}': {e}") from e
    except json.JSONDecodeError:
        # Log the response text if decoding fails to help diagnose the issue
        log.error(
            f"API Error ({endpoint}): Failed to decode JSON response: {response.text if 'response' in locals() else 'No response object'}"
        )
        raise ApiError(
            f"Failed to decode JSON response from API '{endpoint}': {response.text if 'response' in locals() else 'No response object'}"
        ) from None


def send_message_api(recipient: str, message: str) -> Dict[str, Any]:
    """
    Calls the Go bridge API to send a text message.

    Parameters
    ----------
    recipient : str
        The recipient identifier (phone number or JID).
    message : str
        The text message content.

    Returns
    -------
    dict
        The API response dictionary.

    Raises
    ------
    ApiError
        If the API call fails for any reason (network, timeout, API error response, etc.).
    """
    payload: Dict[str, Any] = {"recipient": recipient, "message": message}
    # Timeout for sending a message is typically less critical than media, default 30s is fine
    return _make_api_request("send", payload)


def send_media_api(recipient: str, file_path: str, caption: str = "") -> Dict[str, Any]:
    """
    Calls the Go bridge API to send a media file.

    Ensures the local file exists before attempting to send.

    Parameters
    ----------
    recipient : str
        The recipient identifier (phone number or JID).
    file_path : str
        The local absolute or relative path to the media file.
    caption : str, optional
        The caption for the media file. Defaults to "".

    Returns
    -------
    dict
        The API response dictionary.

    Raises
    ------
    ApiError
        If the media file is not found locally or if the API call fails.
    """
    # Resolve the absolute path to ensure the Go bridge receives a consistent path
    abs_file_path = os.path.abspath(file_path)
    if not os.path.isfile(abs_file_path):
        log.error(f"API Error (send_media): Media file not found at resolved path: {abs_file_path}")
        raise ApiError(f"Media file not found at resolved path: {abs_file_path}")

    payload = {"recipient": recipient, "media_path": abs_file_path, "message": caption}
    # Sending media can take longer, increased timeout to 120 seconds
    return _make_api_request("send", payload, timeout=120)


def download_media_api(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """
    Calls the Go bridge API to download media associated with a message.

    Parameters
    ----------
    message_id : str
        The ID of the message containing the media.
    chat_jid : str
        The JID of the chat containing the message.

    Returns
    -------
    dict
        The API response dictionary, expected to contain the local media path
        if the download was successful.

    Raises
    ------
    ApiError
        If the API call fails or the download is unsuccessful according to the API response.
    """
    payload: Dict[str, Any] = {"message_id": message_id, "chat_jid": chat_jid}
    # Downloading media can take longer, increased timeout to 120 seconds
    return _make_api_request("download", payload, timeout=120)
