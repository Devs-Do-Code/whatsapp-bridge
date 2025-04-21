"""
Output Handler

This module provides methods for reading and processing output from
the Go bridge subprocess.
"""

import logging
from queue import Empty
from typing import Tuple, List, Optional, Generator

log = logging.getLogger(__name__)


def read_output_queues(stdout_q, stderr_q) -> Generator[str, None, Tuple[List[str], List[str]]]:
    """
    Reads all available lines from stdout and stderr queues.

    Args:
        stdout_q: Queue containing stdout lines.
        stderr_q: Queue containing stderr lines.

    Returns:
        A generator that yields error messages and finally returns
        a tuple containing two lists: the first with lines from stdout,
        the second with lines from stderr.
    """
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []
    
    try:
        while True:
            stdout_lines.append(stdout_q.get_nowait())
    except Empty:
        pass
    
    try:
        while True:
            line: str = stderr_q.get_nowait()
            stderr_lines.append(line)
            # Return any critical error indicators in stderr
            if "bind: Only one usage" in line:
                yield "Port 8080 already in use."
            elif "cgo: C compiler" in line or "CGO_ENABLED=0" in line:
                yield "C Compiler / CGO issue detected."
    except Empty:
        pass
    
    return stdout_lines, stderr_lines


def check_process_status(process, last_error: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Checks if a process is still running.

    Args:
        process: The subprocess.Popen instance to check.
        last_error: The last error message recorded.

    Returns:
        A tuple containing a boolean indicating if the process is alive,
        and an optional error message if the process has exited.
    """
    if not process:
        return False, None
        
    poll_result: Optional[int] = process.poll()
    if poll_result is not None:
        error_msg = f"Process exited with code: {poll_result}"
        log.error(error_msg)
        
        if not last_error:
            error_msg = f"Process exited unexpectedly (code {poll_result}). Check logs."
        
        return False, error_msg
        
    return True, None
