"""
Connection Manager

This module provides the ConnectionManager class for managing the connection
lifecycle for the WhatsApp Go bridge.
"""

import time
import logging
from typing import Callable
import sys

from ...exceptions import BridgeError

log = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages the connection lifecycle for the WhatsApp Go bridge.

    This class is responsible for starting the bridge process, monitoring
    its output for connection status or QR code prompts, and handling
    disconnection. It interacts with the `BridgeManager` and provides
    feedback on the connection process.
    """

    def __init__(
        self,
        bridge_manager,
        disconnect_func: Callable[[], None],
        is_first_run: bool,
    ):
        """
        Initializes the ConnectionManager.

        Parameters
        ----------
        bridge_manager : BridgeManager
            An instance of the BridgeManager responsible for starting and stopping
            the Go bridge process.
        disconnect_func : Callable[[], None]
            A callable function provided by the client or caller to handle
            disconnection logic when needed (e.g., `client.disconnect`).
        is_first_run : bool
            A boolean flag indicating if this is the first run of the client,
            used to provide more detailed user feedback during the connection process.
        """
        self._bridge_manager = bridge_manager
        self._disconnect_func = disconnect_func
        self._is_first_run = is_first_run

    def connect(self, timeout_sec: int = 180) -> None:
        """
        Starts the Go bridge process and waits for successful connection
        or a QR code prompt within a specified timeout.

        Monitors the standard output and standard error streams of the bridge
        process to detect connection status messages and QR code availability.
        Provides user feedback based on the `is_first_run` flag.

        Parameters
        ----------
        timeout_sec : int, optional
            The maximum time in seconds to wait for connection confirmation
            or QR code prompt from the Go bridge. Defaults to 180 seconds.

        Raises
        ------
        BridgeError
            If the bridge process fails to start, exits unexpectedly during
            startup, or if the connection attempt times out without
            receiving a successful connection message.
        """
        # Check if the bridge is already running and responsive.
        if self._bridge_manager.is_running and self._bridge_manager.check_if_alive():
            # Log at INFO level for first run, DEBUG for subsequent to avoid clutter.
            log.info("Bridge is already running.") if self._is_first_run else log.debug("Bridge is already running.")
            return

        # Start the Go bridge process.
        log.info("Starting Go bridge process...") if self._is_first_run else log.debug("Starting Go bridge process...")
        try:
            self._bridge_manager.start()
        except BridgeError as e:
            log.error(f"Error starting bridge: {e}", exc_info=True)
            raise # Re-raise the specific BridgeError

        # Wait for connection or QR code prompt with a timeout.
        log.info(f"Waiting up to {timeout_sec}s for bridge connection or QR Code prompt...") if self._is_first_run else log.debug(f"Waiting up to {timeout_sec}s for bridge connection or QR Code prompt...")

        start_time = time.monotonic()
        qr_code_detected = False
        connection_success = False
        printing_qr_code = False # Flag to indicate QR code printing mode

        try:
            while time.monotonic() - start_time < timeout_sec:
                # Continuously check if the bridge process is still alive.
                if not self._bridge_manager.check_if_alive():
                    last_err = self._bridge_manager.last_error
                    log.error(f"Bridge process exited unexpectedly during startup. Last error: {last_err or 'Unknown'}")
                    raise BridgeError(
                        f"Bridge process exited unexpectedly during startup. Last error: {last_err or 'Unknown'}"
                    )

                # Read any available output from the bridge process.
                stdout_lines, stderr_lines = self._bridge_manager.read_output()

                # Process Standard Error (stderr) - often contains critical errors.
                for line in stderr_lines:
                    log.error(f"[Bridge STDERR] {line.strip()}")
                    # If BridgeManager has detected a fatal error signal, raise an exception.
                    if self._bridge_manager.last_error:
                        self._disconnect_func() # Clean up the bridge process before raising.
                        raise BridgeError(
                            f"Bridge failed to start: {self._bridge_manager.last_error}"
                        )

                # Process Standard Output (stdout) - often contains status updates.
                for line in stdout_lines:
                    s_line = line.strip() # Use stripped line for checks

                    if printing_qr_code:
                        # Currently printing QR code, output directly
                        print(s_line)
                        # Check for the end of the QR code block
                        if s_line.startswith("▀▀▀▀▀▀"):
                            printing_qr_code = False # End QR printing mode
                            qr_code_detected = True # Ensure flag is set

                            log.info("\n" + "=" * 60 + "\n" +
                                     " ACTION REQUIRED: SCAN QR CODE ABOVE ".center(60, "!") + "\n" +
                                     " Please scan the QR code printed above using your WhatsApp app ".center(60) + "\n" +
                                     " (Settings > Linked Devices > Link a Device) ".center(60) + "\n" +
                                     " Waiting for connection after scan... ".center(60) + "\n" +
                                     "=" * 60 + "\n")
                    else:
                        # Not printing QR code, log normally
                        log.info(f"[Bridge STDOUT] {s_line}")

                        # Detect start of QR Code prompt to switch mode
                        if (
                            "Scan this QR code" in s_line
                            # Add other potential trigger lines if necessary
                            # or s_line.startswith("████") # Alt trigger
                        ):
                            printing_qr_code = True
                            qr_code_detected = True # Mark that QR was prompted
                            # Do NOT print instructions here anymore

                        # Detect successful connection messages (outside QR mode)
                        elif (
                            "Successfully connected and authenticated!" in s_line
                            or "Connected to WhatsApp!" in s_line
                        ):
                            log.info("\n>>> Bridge connected successfully!\n") if self._is_first_run else log.info("WhatsApp connected.")
                            connection_success = True
                            break # Exit the line processing loop

                        # Detect API server start message (optional)
                        elif "Starting REST API server on :8080" in s_line:
                            log.info("Bridge API server starting...")

                # If connection was successful, break the main while loop.
                if connection_success:
                    break

                # Small delay to avoid busy-waiting
                time.sleep(0.5)

            # After the loop, check if connection was successful.
            if not connection_success:
                err_msg = "Timed out waiting for bridge connection."
                if qr_code_detected:
                    err_msg += " QR Code was shown, but connection confirmation wasn't received. Did you scan it?"
                log.error(err_msg)
                self._disconnect_func()
                raise BridgeError(err_msg)

        except BridgeError:
            # If a BridgeError was already raised (e.g., process exited), just re-raise it.
            raise
        except Exception as e:
            # Catch any other unexpected exceptions during the wait loop.
            log.error(f"Unexpected error during connection wait: {e}", exc_info=True)
            self._disconnect_func() # Clean up the bridge process on unexpected error.
            raise BridgeError(f"Unexpected error during connection: {e}") from e
