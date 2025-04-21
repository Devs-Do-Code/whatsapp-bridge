"""
Process Management

This module provides methods for managing the Go bridge process lifecycle,
including stopping the process and checking its status.
"""

import sys
import subprocess
import logging
from typing import Optional

log = logging.getLogger(__name__)


def stop_process(process: Optional[subprocess.Popen], pid: Optional[int]) -> None:
    """
    Stops a running subprocess.

    Args:
        process: The subprocess.Popen instance to stop.
        pid: The process ID of the subprocess.

    Returns:
        None
    """
    if not process:
        log.info("Process is not running.")
        return

    log.info(f"Stopping process (PID: {pid})...")
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                check=False,
                capture_output=True,
            )
        else:
            process.terminate()

        try:
            process.wait(timeout=5)
            log.info("Process terminated gracefully.")
        except subprocess.TimeoutExpired:
            log.warning("Process did not terminate gracefully, killing...")
            process.kill()
            process.wait(timeout=2)
            log.info("Process killed.")

    except Exception as e:
        log.error(f"Error stopping process: {e}", exc_info=True)

        try:
            if process and process.poll() is None:
                process.kill()
        except Exception as kill_e:
            log.error(f"Error during force kill: {kill_e}", exc_info=True)
