"""
Database Reader Utilities

This module provides utility functions for reading data from the WhatsApp
message database.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any, Tuple

from ..exceptions import DbError
from ..config import settings

log = logging.getLogger(__name__)

def get_latest_message_timestamp_utc() -> Optional[datetime]:
    """
    Retrieves the timestamp of the most recent message in the database.

    Queries the message database for the maximum timestamp value across
    all messages, converts it to a UTC datetime object, and returns it.
    This is useful for determining a starting point for polling new messages.

    Returns
    -------
    Optional[datetime]
        The UTC timestamp of the most recent message, or None if no messages
        are found or if an error occurs.

    Raises
    ------
    DbError
        If an error occurs while accessing the database.
    """
    db_path = settings.DB_PATH
    log.debug(f"Attempting to connect to database at: {db_path}")
    try:
        # Connect using the Path object from settings
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(timestamp) FROM messages")
            result = cursor.fetchone()
            
            if result and result[0]:
                # The timestamp from the DB is a string like 'YYYY-MM-DD HH:MM:SS+HH:MM'
                timestamp_str = result[0]
                try:
                    # Parse the string into a timezone-aware datetime object
                    local_dt = datetime.fromisoformat(timestamp_str)
                    # Convert the datetime object to UTC
                    utc_dt = local_dt.astimezone(timezone.utc)
                    log.debug(f"Latest message timestamp from DB: {local_dt}, converted to UTC: {utc_dt}")
                    return utc_dt
                except ValueError as e:
                    log.error(f"Could not parse timestamp string '{timestamp_str}' from database: {e}", exc_info=True)
                    raise DbError(f"Could not parse timestamp string from database: {e}")
            return None
    except sqlite3.Error as e:
        log.error(f"SQLite error retrieving latest message timestamp from '{db_path}': {e}", exc_info=True)
        raise DbError(f"Database error retrieving latest message timestamp: {e}")
    except Exception as e:
        log.error(f"Unexpected error retrieving latest message timestamp from '{db_path}': {e}", exc_info=True)
        raise DbError(f"Unexpected error retrieving latest message timestamp: {e}")
