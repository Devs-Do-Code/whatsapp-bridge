"""
Stream Handler

This module provides utilities for handling subprocess output streams
in a non-blocking manner using threads and queues.
"""

import logging
from queue import Queue
from typing import Any

log = logging.getLogger(__name__)


def enqueue_output(out: Any, queue: "Queue[str]") -> None:
    """
    Helper function to read stream output without blocking.

    Reads lines from a stream (`out`) and puts them into a queue (`queue`).
    The function stops when the stream is closed or a ValueError occurs.

    Args:
        out (io.BytesIO): The stream to read from (e.g., process.stdout, process.stderr).
        queue (queue.Queue): The queue to put the read lines into.
    """
    try:
        for line in iter(out.readline, b""):
            queue.put(line.decode("utf-8", errors="replace"))
    except ValueError:
        pass
    finally:
        try:
            out.close()
        except Exception:
            pass
