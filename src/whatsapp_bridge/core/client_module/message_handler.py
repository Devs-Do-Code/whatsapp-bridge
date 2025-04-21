"""
Message Handler

This module provides functions for retrieving and processing messages
from the WhatsApp database via the Go bridge.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple

from ...config import settings
from ...db import reader as db_reader
from ...exceptions import DbError
from .media_handler import download_media

log = logging.getLogger(__name__)


def get_new_messages(client, chat_jid_filter: Optional[str] = None, download_media_files: bool = True) -> List[Dict[str, Any]]:
    """
    Retrieves new messages from the local database since the last check.

    This function queries the local SQLite message database managed by the
    Go bridge. It fetches messages received after the timestamp recorded
    during the last successful call to this method within the current
    `WhatsappClient` instance. On the first call, it defaults to checking
    messages from approximately one minute ago to avoid fetching the
    entire history.

    Parameters
    ----------
    client : WhatsappClient
        The WhatsApp client instance with bridge manager and timestamp tracking.
    chat_jid_filter : Optional[str], optional
        An optional JID string to filter the results, returning only
        messages from a specific chat. Defaults to None (no filtering).
    download_media_files : bool, optional
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
    if not settings.DB_PATH.exists():
        log.warning(f"Database path {settings.DB_PATH} not found. Cannot get messages.")
        return []

    start_time_utc = client._last_message_check_time
    if start_time_utc is None:
        log.info("Client._last_message_check_time not set before first get_new_messages call. Defaulting to 1 min ago.")
        start_time_utc = datetime.now(timezone.utc) - timedelta(minutes=1)
        client._last_message_check_time = start_time_utc
    elif start_time_utc.tzinfo is None or start_time_utc.tzinfo.utcoffset(start_time_utc) != timedelta(0):
        log.warning(f"Received non-UTC start_time_utc: {start_time_utc.tzinfo}. Converting to UTC.")
        start_time_utc = start_time_utc.astimezone(timezone.utc)
        client._last_message_check_time = start_time_utc

    try:
        new_messages_list, new_last_ts_utc = db_reader.get_messages_since_db(
            start_time_utc, chat_jid_filter
        )

        if download_media_files and new_messages_list:
            try:
                settings.DOWNLOADED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                log.warning(f"Could not create media download directory "
                            f"{settings.DOWNLOADED_MEDIA_DIR}: {e}. Downloads will likely fail.", exc_info=True)

            for msg_data in new_messages_list:
                if msg_data.get("id") and msg_data.get("chat_jid") and msg_data.get("needs_download"):
                    log.info(f"Attempting auto-download for message ID: {msg_data['id']}")
                    local_path = download_media(client._bridge_manager, msg_data['id'], msg_data['chat_jid'])
                    msg_data["local_media_path"] = local_path

        if new_last_ts_utc and new_last_ts_utc > start_time_utc:
            client._last_message_check_time = new_last_ts_utc + timedelta(milliseconds=1)

        return new_messages_list

    except DbError as e:
        log.error(f"Error reading messages from DB: {e}", exc_info=True)
        raise
    except Exception as e:
        log.error(f"Unexpected error getting new messages: {e}", exc_info=True)
        raise
