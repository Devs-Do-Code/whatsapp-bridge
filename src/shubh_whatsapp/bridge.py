import subprocess
import sys
import os
import threading
import time
from queue import Queue, Empty
from . import config
from .exceptions import BridgeError

# --- Non-blocking stream reader ---
# (From https://stackoverflow.com/a/4896288/1493081)
def enqueue_output(out, queue):
    try:
        for line in iter(out.readline, b''):
            queue.put(line.decode('utf-8', errors='replace')) # Decode safely
    except ValueError: # Handle case where stream is closed abruptly
         pass
    finally:
        try:
            out.close()
        except Exception:
            pass # Ignore errors during close

class BridgeManager:
    """Manages the Go bridge subprocess."""
    def __init__(self):
        self._process = None
        self._stdout_q = Queue()
        self._stderr_q = Queue()
        self._stdout_thread = None
        self._stderr_thread = None
        self.is_running = False
        self.last_error = None
        self.pid = None

    def start(self):
        """Starts the Go bridge process."""
        if self.is_running and self._process and self._process.poll() is None:
            print("Bridge process is already running.")
            return True

        if not config.GO_BRIDGE_SRC_PATH.exists():
             raise BridgeError(f"Go bridge source not found at {config.GO_BRIDGE_SRC_PATH}. Run setup first.")

        # Environment variables for Go
        run_env = os.environ.copy()
        run_env["CGO_ENABLED"] = "1" # Essential for go-sqlite3

        command = ["go", "run", "main.go"]
        cwd = str(config.GO_BRIDGE_DIR)

        print(f"Starting Go bridge: {' '.join(command)} in {cwd}")
        try:
            # Use Popen for non-blocking execution and stream handling
            self._process = subprocess.Popen(
                command,
                cwd=cwd,
                env=run_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # Use platform-specific process creation flags if needed (e.g., for clean termination)
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            self.pid = self._process.pid
            print(f"Bridge process started with PID: {self.pid}")

            # Start threads to read stdout and stderr without blocking
            self._stdout_q = Queue()
            self._stderr_q = Queue()
            self._stdout_thread = threading.Thread(target=enqueue_output, args=(self._process.stdout, self._stdout_q))
            self._stderr_thread = threading.Thread(target=enqueue_output, args=(self._process.stderr, self._stderr_q))
            self._stdout_thread.daemon = True # Allow Python to exit even if these threads are stuck
            self._stderr_thread.daemon = True
            self._stdout_thread.start()
            self._stderr_thread.start()

            self.is_running = True
            self.last_error = None
            return True

        except FileNotFoundError:
             self.is_running = False
             self.last_error = "Go command not found. Ensure Go is installed and in PATH."
             raise BridgeError(self.last_error) from None
        except Exception as e:
            self.is_running = False
            self.last_error = f"Failed to start Go bridge: {e}"
            raise BridgeError(self.last_error) from e

    def stop(self):
        """Stops the Go bridge process."""
        if not self.is_running or not self._process:
            print("Bridge process is not running.")
            return

        print(f"Stopping bridge process (PID: {self.pid})...")
        try:
            # Terminate politely first
            if sys.platform == "win32":
                # Send Ctrl+Break event on Windows
                 subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.pid)], check=False, capture_output=True)
            else:
                # Send SIGTERM on Unix-like systems
                self._process.terminate()

            # Wait a bit for graceful shutdown
            try:
                self._process.wait(timeout=5)
                print("Bridge process terminated gracefully.")
            except subprocess.TimeoutExpired:
                print("Bridge process did not terminate gracefully, killing...")
                self._process.kill() # Force kill if necessary
                self._process.wait(timeout=2) # Wait for kill
                print("Bridge process killed.")

        except Exception as e:
            print(f"Error stopping bridge process: {e}")
            # Attempt to kill anyway if termination failed
            try:
                if self._process.poll() is None:
                    self._process.kill()
            except Exception as kill_e:
                 print(f"Error during force kill: {kill_e}")
        finally:
            self._process = None
            self.is_running = False
            self.pid = None
            # Wait briefly for threads to potentially finish writing
            if self._stdout_thread: self._stdout_thread.join(timeout=0.5)
            if self._stderr_thread: self._stderr_thread.join(timeout=0.5)
            self._stdout_thread = None
            self._stderr_thread = None
            print("Bridge stopped.")

    def read_output(self):
        """Reads all available lines from stdout and stderr queues."""
        stdout_lines = []
        stderr_lines = []
        try:
            while True: # Read until queues are empty
                stdout_lines.append(self._stdout_q.get_nowait())
        except Empty:
            pass
        try:
             while True:
                 line = self._stderr_q.get_nowait()
                 stderr_lines.append(line)
                 # Check for common fatal errors
                 if "bind: Only one usage" in line:
                      self.last_error = "Port 8080 already in use."
                      print(f"FATAL BRIDGE ERROR DETECTED: {self.last_error}")
                      # Consider stopping the bridge here or letting the caller handle it
                      # self.stop()
                 elif "cgo: C compiler" in line or "CGO_ENABLED=0" in line:
                      self.last_error = "C Compiler / CGO issue detected."
                      print(f"FATAL BRIDGE ERROR DETECTED: {self.last_error}")

        except Empty:
            pass
        return stdout_lines, stderr_lines

    def check_if_alive(self):
        """Checks if the process is still running."""
        if not self._process:
            self.is_running = False
            return False
        poll_result = self._process.poll() # None if running, exit code otherwise
        if poll_result is not None:
            print(f"Bridge process exited with code: {poll_result}")
            self.is_running = False
            # Read any remaining output
            out, err = self.read_output()
            if err:
                 print("Remaining stderr on exit:\n" + "".join(err))
                 if not self.last_error: # Store last error if not already set
                      self.last_error = f"Bridge process exited unexpectedly (code {poll_result}). Check logs."
            return False
        return True