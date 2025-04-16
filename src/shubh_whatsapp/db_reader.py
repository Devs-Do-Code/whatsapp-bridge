import sqlite3
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any
from . import config
from .exceptions import DbError

def get_messages_since_db(last_check_time_utc: datetime, chat_jid_filter: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[datetime]]:
    """Retrieves messages from the database newer than the last check time (UTC).

    Args:
        last_check_time_utc: Datetime object representing the last check (MUST be timezone-aware UTC).
        chat_jid_filter: Optional JID to filter messages for a specific chat.

    Returns:
        A tuple containing:
        - A list of new messages (as dictionaries with UTC timestamps).
        - The timestamp of the latest message found (as timezone-aware UTC, or None).
    """
    new_messages = []
    latest_timestamp_utc = None
    db_path = config.DB_PATH

    if not db_path.exists():
        print(f"Warning: Database file not found at {db_path}. Cannot retrieve messages.")
        return [], last_check_time_utc # Return original time if DB missing

    # Ensure the input time is UTC and aware
    if last_check_time_utc.tzinfo is None or last_check_time_utc.tzinfo.utcoffset(last_check_time_utc) != timedelta(0):
         last_check_time_utc = last_check_time_utc.astimezone(timezone.utc)

    # Use ISO format with space separator and seconds precision for query
    last_check_iso_for_query = last_check_time_utc.isoformat(sep=' ', timespec='seconds')
    print(f"DB Reader: Querying for messages WHERE timestamp > '{last_check_iso_for_query}'")

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = """
            SELECT
                id, chat_jid, sender, content, timestamp, is_from_me,
                media_type, filename
            FROM messages
            WHERE timestamp > ?
        """
        params = [last_check_iso_for_query]

        if chat_jid_filter:
            query += " AND chat_jid = ?"
            params.append(chat_jid_filter)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        # print(f"DB Reader DEBUG: Found {len(rows)} rows matching time criteria.") # Optional debug

        for row in rows:
            msg_id = row[0]
            msg_timestamp_str = row[4]
            msg_timestamp_utc = None

            try:
                dt_from_db = datetime.fromisoformat(msg_timestamp_str)
                msg_timestamp_utc = dt_from_db.astimezone(timezone.utc)
            except ValueError as e:
                print(f"DB Reader Error: Failed parsing timestamp '{msg_timestamp_str}' for msg {msg_id}: {e}")
                continue # Skip this message

            message_data = {
                "id": msg_id,
                "chat_jid": row[1],
                "sender": row[2],
                "content": row[3],
                "timestamp": msg_timestamp_utc, # Store UTC datetime object
                "is_from_me": bool(row[5]),
                "media_type": row[6],
                "filename": row[7],
                # Add fields needed for potential download later
                "needs_download": bool(row[6]) and not bool(row[5]) # If media and not from me
            }
            new_messages.append(message_data)

            if latest_timestamp_utc is None or msg_timestamp_utc > latest_timestamp_utc:
                latest_timestamp_utc = msg_timestamp_utc

    except sqlite3.Error as e:
        raise DbError(f"Database error reading messages: {e}") from e
    except Exception as e:
        raise DbError(f"Unexpected error during message retrieval: {e}") from e
    finally:
        if conn:
            conn.close()

    # Return the list and the latest UTC timestamp found (or the original if none found)
    return new_messages, latest_timestamp_utc if latest_timestamp_utc else last_check_time_utc