"""
Database Reader Module

This module provides functions for reading data from the local SQLite
message database managed by the Go bridge. It includes functions for
retrieving messages based on timestamp and filtering by chat JID,
as well as getting the timestamp of the latest message.
"""

import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any
from ..config import settings
from ..exceptions import DbError

# Setup logger for this module
log = logging.getLogger(__name__)


def get_messages_since_db(
    last_check_time_utc: datetime, chat_jid_filter: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], datetime]:
    """
    Retrieves messages from the database newer than the last check time (UTC).

    Uses a >= query initially and then filters precisely in Python using
    datetime objects to ensure only strictly newer messages are returned.

    Parameters
    ----------
    last_check_time_utc : datetime
        Datetime object representing the last check (MUST be timezone-aware UTC).
    chat_jid_filter : Optional[str], optional
        Optional JID to filter messages for a specific chat. Defaults to None.

    Returns
    -------
    Tuple[List[Dict[str, Any]], datetime]
        A tuple containing:
        - A list of new messages (as dictionaries with UTC timestamps).
        - The timestamp of the latest message found *that is strictly newer*
          than `last_check_time_utc`, or the original `last_check_time_utc`
          if no strictly newer messages were found or the database is missing.

    Raises
    ------
    DbError
        If an error occurs while reading messages from the database.
    """
    new_messages: List[Dict[str, Any]] = []
    # Initialize latest_processed_timestamp_utc to the check time. It will only be updated
    # if a strictly newer message is found and processed.
    latest_processed_timestamp_utc = last_check_time_utc
    db_path = settings.DB_PATH

    if not db_path.exists():
        log.warning(f"Database file not found at {db_path}. Cannot retrieve messages.")
        # Return the original check time as the latest processed time
        return [], latest_processed_timestamp_utc

    if last_check_time_utc.tzinfo is None or last_check_time_utc.tzinfo.utcoffset(
        last_check_time_utc
    ) != timedelta(0):
        log.warning(
            f"Received last_check_time without UTC timezone ({last_check_time_utc.tzinfo}). Converting to UTC."
        )
        last_check_time_utc = last_check_time_utc.astimezone(timezone.utc)
        latest_processed_timestamp_utc = last_check_time_utc  # Update this too

    # Use ISO format *without* microseconds for the initial >= query.
    # This aims to fetch the last known message and anything potentially newer.
    query_start_iso = last_check_time_utc.isoformat(sep=" ", timespec="seconds")
    log.debug(
        f"Querying DB for messages WHERE timestamp >= '{query_start_iso}' (UTC, seconds precision)"
    )

    conn = None
    try:
        db_uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        cursor = conn.cursor()

        # Query using >= to catch messages at the boundary and newer ones
        query = """
            SELECT
                id, chat_jid, sender, content, timestamp, is_from_me,
                media_type, filename
            FROM messages
            WHERE timestamp >= ?
        """
        params = [query_start_iso]

        if chat_jid_filter:
            query += " AND chat_jid = ?"
            params.append(chat_jid_filter)

        # Order by timestamp to process chronologically
        query += " ORDER BY timestamp ASC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        log.debug(f"Initial DB query returned {len(rows)} rows.")

        # --- Python Filtering Step ---
        for row in rows:
            (
                msg_id_idx,
                chat_jid_idx,
                sender_idx,
                content_idx,
                ts_idx,
                from_me_idx,
                media_idx,
                filename_idx,
            ) = range(8)

            msg_id = row[msg_id_idx]
            msg_timestamp_str = row[ts_idx]
            msg_timestamp_utc = None

            # Parse the timestamp from DB
            try:
                dt_from_db = datetime.fromisoformat(msg_timestamp_str)
                if dt_from_db.tzinfo is None:
                    msg_timestamp_utc = dt_from_db.replace(tzinfo=timezone.utc)
                else:
                    msg_timestamp_utc = dt_from_db.astimezone(timezone.utc)
            except ValueError as e:
                log.error(
                    f"Failed parsing timestamp '{msg_timestamp_str}' for msg {msg_id}: {e}"
                )
                continue  # Skip this message if timestamp is invalid

            # Compare datetime objects directly for precise filtering
            if msg_timestamp_utc <= last_check_time_utc:
                continue

            # If we reach here, the message is strictly newer
            log.debug(
                f"Including message {msg_id} (ts {msg_timestamp_utc}) - newer than check time {last_check_time_utc}"
            )

            media_type = row[media_idx]
            is_from_me = bool(row[from_me_idx])

            message_data = {
                "id": msg_id,
                "chat_jid": row[chat_jid_idx],
                "sender": row[sender_idx],
                "content": row[content_idx],
                "timestamp": msg_timestamp_utc,
                "is_from_me": is_from_me,
                "media_type": media_type,
                "filename": row[filename_idx],
                "needs_download": bool(media_type) and not is_from_me,
            }
            new_messages.append(message_data)

            # Update the latest *processed* timestamp
            if msg_timestamp_utc > latest_processed_timestamp_utc:
                latest_processed_timestamp_utc = msg_timestamp_utc

    except sqlite3.OperationalError as e:
        if "attempt to write a readonly database" in str(e):
            raise DbError(
                f"Database error: Cannot write to read-only DB at {db_path}. Check permissions or connection mode."
            ) from e
        raise DbError(
            f"Database operational error reading messages from {db_path}: {e}"
        ) from e
    except sqlite3.DatabaseError as e:
        raise DbError(
            f"General database error reading messages from {db_path}: {e}"
        ) from e
    except Exception as e:
        raise DbError(f"Unexpected error during message retrieval: {e}") from e
    finally:
        if conn:
            conn.close()

    log.debug(
        f"Returning {len(new_messages)} new messages. Latest processed timestamp: {latest_processed_timestamp_utc}"
    )
    # Return the list of strictly newer messages and the timestamp of the latest one among them
    # (or the original check time if none were newer).
    return new_messages, latest_processed_timestamp_utc


def get_latest_message_timestamp_utc() -> Optional[datetime]:
    """
    Retrieves the timestamp of the most recent message in the database (UTC).

    Queries the database for the maximum timestamp among all messages.

    Returns
    -------
    Optional[datetime]
        A timezone-aware datetime object representing the timestamp of the
        latest message in UTC, or None if the database is empty, not found,
        or if the timestamp cannot be parsed.

    Raises
    ------
    DbError
        If a database error occurs during the query.
    """
    latest_timestamp_utc: Optional[datetime] = None
    db_path = settings.DB_PATH

    if not db_path.exists():
        log.warning(
            f"Database file not found at {db_path}. Cannot get latest timestamp."
        )
        return None

    conn = None
    log.debug(f"Querying MAX(timestamp) from {db_path}")
    try:
        # Connect in read-only mode to be safe
        db_uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        cursor = conn.cursor()

        query = "SELECT MAX(timestamp) FROM messages"
        cursor.execute(query)
        result = cursor.fetchone()

        if result and result[0]:
            max_ts_str = result[0]
            log.debug(f"Raw MAX(timestamp) from DB: '{max_ts_str}'")
            try:
                # Attempt parsing, assuming ISO format possibly without timezone
                dt_from_db = datetime.fromisoformat(max_ts_str)
                # Ensure timezone is UTC
                if dt_from_db.tzinfo is None:
                    latest_timestamp_utc = dt_from_db.replace(tzinfo=timezone.utc)
                else:
                    latest_timestamp_utc = dt_from_db.astimezone(timezone.utc)
                log.debug(
                    f"Parsed latest timestamp as UTC: {latest_timestamp_utc.isoformat()}"
                )
            except ValueError as e:
                log.error(f"Failed parsing max timestamp '{max_ts_str}': {e}")
                return None  # Indicate failure to parse
        else:
            log.debug("MAX(timestamp) query returned no result (DB likely empty).")

    except sqlite3.OperationalError as e:
        # Log specific error but raise generic DbError for handling upstream
        log.error(
            f"Database operational error getting max timestamp from {db_path}: {e}",
            exc_info=True,
        )
        raise DbError(f"Database operational error getting max timestamp: {e}") from e
    except sqlite3.DatabaseError as e:
        log.error(
            f"General database error getting max timestamp from {db_path}: {e}",
            exc_info=True,
        )
        raise DbError(f"General database error getting max timestamp: {e}") from e
    except Exception as e:
        log.error(
            f"Unexpected error during max timestamp retrieval: {e}", exc_info=True
        )
        raise DbError(f"Unexpected error during max timestamp retrieval: {e}") from e
    finally:
        if conn:
            conn.close()

    log.debug(f"Returning latest timestamp: {latest_timestamp_utc}")
    return latest_timestamp_utc
