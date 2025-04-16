import requests
import json
import os
from . import config
from .exceptions import ApiError

def _make_api_request(endpoint, payload, timeout=30):
    """Helper function to make POST requests to the Go bridge API."""
    url = f"{config.GO_BRIDGE_API_URL}/{endpoint}"
    print(f"Calling API: {url} with payload: {payload}")
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status() # Check for HTTP errors
        result = response.json()
        print(f"API Response: {result}")
        if not result.get("success", False):
            # Raise specific error if API reports failure
            raise ApiError(f"API call '{endpoint}' failed: {result.get('message', 'Unknown API error')}")
        return result
    except requests.exceptions.Timeout:
        raise ApiError(f"API call '{endpoint}' timed out after {timeout}s.") from None
    except requests.exceptions.ConnectionError as e:
         raise ApiError(f"API connection error for '{url}': {e}. Is the Go bridge running?") from e
    except requests.exceptions.RequestException as e:
        raise ApiError(f"API request error for '{endpoint}': {e}") from e
    except json.JSONDecodeError:
        raise ApiError(f"Failed to decode JSON response from API '{endpoint}': {response.text}") from None


def send_message_api(recipient: str, message: str) -> dict:
    """Calls the Go bridge API to send a text message."""
    payload = {"recipient": recipient, "message": message}
    return _make_api_request("send", payload)

def send_media_api(recipient: str, file_path: str, caption: str = "") -> dict:
    """Calls the Go bridge API to send a media file."""
    # API expects absolute path
    abs_file_path = os.path.abspath(file_path)
    if not os.path.isfile(abs_file_path):
        raise ApiError(f"Media file not found at resolved path: {abs_file_path}")

    payload = {"recipient": recipient, "media_path": abs_file_path, "message": caption}
    return _make_api_request("send", payload, timeout=120) # Longer timeout for media

def download_media_api(message_id: str, chat_jid: str) -> dict:
    """Calls the Go bridge API to download media."""
    payload = {"message_id": message_id, "chat_jid": chat_jid}
    # Returns dict like {"success": true, "path": "...", "filename": "...", "message": "..."}
    return _make_api_request("download", payload, timeout=120) # Longer timeout