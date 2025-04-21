"""
Bridge Manager

This module provides the BridgeManager class for starting, stopping,
and managing the subprocess running the Go bridge application.
"""

import subprocess
import sys
import os
import threading
import logging
from queue import Queue, Empty
from typing import Tuple, List, Optional, Any

from ...config import settings
from ...exceptions import BridgeError
from .stream_handler import enqueue_output
from .process_management import stop_process
from .output_handler import read_output_queues, check_process_status

log = logging.getLogger(__name__)


class BridgeManager:
    """
    Manages the Go bridge subprocess.

    Handles starting, stopping, and monitoring the Go bridge process.
    Captures process output and provides methods to read it.
    """

    def __init__(self) -> None:
        """
        Initializes the BridgeManager.

        Sets up initial state and variables for managing the subprocess
        and its output streams.
        """
        self._process: Optional[subprocess.Popen] = None
        self._stdout_q: Queue = Queue()
        self._stderr_q: Queue = Queue()
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.last_error: Optional[str] = None
        self.pid: Optional[int] = None

    def start(self) -> bool:
        """
        Starts the Go bridge process.

        Checks if the bridge is already running and if the source path exists.
        Spawns the Go process, captures its stdout and stderr in separate
        threads, and updates the manager's state.

        Returns:
            bool: True if the process was started or was already running.

        Raises
        ------
        BridgeError
            If the Go bridge source is not found, the Go command
            is not in PATH, or any other exception occurs during
            process startup.
        """
        if self.is_running and self._process and self._process.poll() is None:
            log.info("Bridge process is already running.")
            return True

        if not settings.GO_BRIDGE_SRC_PATH.exists():
            error_msg = f"Go bridge source not found at {settings.GO_BRIDGE_SRC_PATH}. Run setup first."
            log.error(error_msg)
            raise BridgeError(error_msg)

        run_env = os.environ.copy()
        run_env["CGO_ENABLED"] = "1"

        command: List[str] = ["go", "run", "main.go"]
        cwd: str = str(settings.GO_BRIDGE_DIR)

        log.info(f"Starting Go bridge: {' '.join(command)} in {cwd}")
        try:
            self._process = subprocess.Popen(
                command,
                cwd=cwd,
                env=run_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == "win32"
                    else 0
                ),
            )
            self.pid = self._process.pid
            log.info(f"Bridge process started with PID: {self.pid}")

            self._stdout_q = Queue()
            self._stderr_q = Queue()
            self._stdout_thread = threading.Thread(
                target=enqueue_output, args=(self._process.stdout, self._stdout_q)
            )
            self._stderr_thread = threading.Thread(
                target=enqueue_output, args=(self._process.stderr, self._stderr_q)
            )
            self._stdout_thread.daemon = True
            self._stderr_thread.daemon = True
            self._stdout_thread.start()
            self._stderr_thread.start()

            self.is_running = True
            self.last_error = None
            return True

        except FileNotFoundError:
            self.is_running = False
            self.last_error = (
                "Go command not found. Ensure Go is installed and in PATH."
            )
            log.critical(self.last_error)
            raise BridgeError(self.last_error) from None
        except Exception as e:
            self.is_running = False
            self.last_error = f"Failed to start Go bridge: {e}"
            log.critical(self.last_error, exc_info=True)
            raise BridgeError(self.last_error) from e
            
    def stop(self) -> None:
        """
        Stops the Go bridge process.
        """
        if not self.is_running or not self._process:
            log.info("Bridge process is not running.")
            return

        log.info(f"Stopping bridge process (PID: {self.pid})...")
        try:
            stop_process(self._process, self.pid)
        finally:
            self._process = None
            self.is_running = False
            self.pid = None

            # Attempt to join threads, but don't block indefinitely
            if self._stdout_thread and self._stdout_thread.is_alive():
                self._stdout_thread.join(timeout=1)
            if self._stderr_thread and self._stderr_thread.is_alive():
                self._stderr_thread.join(timeout=1)

            self._stdout_thread = None
            self._stderr_thread = None
            log.info("Bridge stopped.")
            
    def read_output(self) -> Tuple[List[str], List[str]]:
        """
        Reads all available lines from stdout and stderr queues.

        Checks the internal queues for any output captured from the subprocess.
        Also checks stderr for specific fatal error messages and updates
        `self.last_error`.

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists:
                                          the first with lines from stdout,
                                          the second with lines from stderr.
        """
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []
        
        try:
            while True:
                stdout_lines.append(self._stdout_q.get_nowait())
        except Empty:
            pass
            
        try:
            while True:
                line: str = self._stderr_q.get_nowait()
                stderr_lines.append(line)
                if "bind: Only one usage" in line:
                    self.last_error = "Port 8080 already in use."
                    log.critical(f"FATAL BRIDGE ERROR DETECTED: {self.last_error}")
                elif "cgo: C compiler" in line or "CGO_ENABLED=0" in line:
                    self.last_error = "C Compiler / CGO issue detected."
                    log.critical(f"FATAL BRIDGE ERROR DETECTED: {self.last_error}")
        except Empty:
            pass
            
        return stdout_lines, stderr_lines
        
    def check_if_alive(self) -> bool:
        """
        Checks if the process is still running.

        Polls the subprocess to check its exit code. If the process has exited,
        it updates the `is_running` state and reads any remaining output to
        detect potential errors.

        Returns:
            bool: True if the process is running, False otherwise.
        """
        if not self._process:
            self.is_running = False
            return False
            
        poll_result: Optional[int] = self._process.poll()
        if poll_result is not None:
            log.error(f"Bridge process exited with code: {poll_result}")
            self.is_running = False
            out, err = self.read_output()
            if err:
                log.error("Remaining stderr on exit:\n" + "".join(err))
                if not self.last_error:
                    self.last_error = f"Bridge process exited unexpectedly (code {poll_result}). Check logs."
                    log.critical(self.last_error)
            return False
            
        return True
