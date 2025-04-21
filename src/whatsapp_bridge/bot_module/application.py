"""
Application Module

This module provides the main Application class for running a WhatsApp bot
and the ApplicationBuilder class for configuring and creating Application instances.
"""

import time
import logging
import inspect
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Type, Set, Callable, TypeVar

from ..listener_module import MessageListener
from ..utils.db_reader import get_latest_message_timestamp_utc
from ..exceptions import DbError, BridgeError, ApiError, WhatsappPkgError
from .context import ContextTypes
from .update import Update
from .handlers import TypeHandler, MessageHandler

log = logging.getLogger(__name__)


class Application:
    """
    The main application class for running a WhatsApp bot.

    Manages listeners, handlers, and the polling loop for new messages.
    It initializes the WhatsApp client, dispatches incoming messages
    to registered handlers based on defined filters, and handles the polling
    process to fetch new updates from the database.

    Attributes
    ----------
    listener : MessageListener
        The listener instance responsible for fetching and processing messages.
    _type_handlers : List[TypeHandler]
        A list of registered TypeHandler instances.
    _message_handlers : List[MessageHandler]
        A list of registered MessageHandler instances.
    logger : logging.Logger
        The logger instance for the Application class.
    _seen_ids : set[str]
        A set to keep track of message IDs that have already been processed
        in the current polling session to prevent duplicates.
    """
    def __init__(self):
        """
        Initializes a new instance of the Application.

        Sets up the message listener, initializes empty handler lists for both
        type handlers and message handlers, and creates an empty set to track
        seen message IDs to prevent duplicate processing.
        """
        # Initialize the logger for this instance
        self.logger = logging.getLogger(__name__)
        
        # Create a message listener with default poll interval
        self.listener = MessageListener()
        
        # Initialize empty lists for handlers
        self._type_handlers: List[TypeHandler] = []
        self._message_handlers: List[MessageHandler] = []
        
        # Set to track message IDs that have already been processed
        # to prevent duplicate processing in the polling loop
        self._seen_ids: Set[str] = set()

    def add_handler(self, handler: Union[TypeHandler, MessageHandler], group: int = 0):
        """
        Adds a handler to the application.

        Handlers are processed in the order they are added within their group
        (grouping is not currently fully implemented; handlers are added to simple lists).

        Parameters
        ----------
        handler : TypeHandler or MessageHandler
            The handler instance to add.
        group : int, optional
            The group for the handler. Defaults to 0 (currently unused for prioritization).

        Returns
        -------
        Application
            The application instance, allowing for method chaining.

        Raises
        -------
        TypeError
            If the provided handler is not an instance of TypeHandler or MessageHandler.
        """
        if not isinstance(handler, (TypeHandler, MessageHandler)):
            raise TypeError("Handler must be an instance of TypeHandler or MessageHandler")

        if isinstance(handler, TypeHandler):
            self._type_handlers.append(handler)
            self.logger.debug(f"Added TypeHandler: {getattr(handler.callback, '__name__', 'unknown')}")
        elif isinstance(handler, MessageHandler):
            self._message_handlers.append(handler)
            self.logger.debug(f"Added MessageHandler: {getattr(handler.callback, '__name__', 'unknown')}")

        # For future implementation, a dictionary mapping group numbers to lists of handlers
        # or a sorted list of (group, handler) tuples could be used to manage execution order.

        return self
        
    def run_polling(self) -> None:
        """
        Starts the main polling loop to fetch and process new messages.

        This method initializes the WhatsApp client, determines the starting
        timestamp for fetching messages (based on the latest message recorded
        in the database), and then enters a continuous loop to poll for new
        messages. Each incoming message is wrapped in an :class:`Update` object
        and subsequently dispatched to registered :class:`TypeHandler` and
        :class:`MessageHandler` instances whose filters match the update.

        The loop includes mechanisms to handle unexpected termination of the
        underlying Go bridge process by attempting to reinitialize the client
        and reconnect. Basic error handling and logging are implemented to
        monitor the polling process and handler execution. The polling loop
        continues until it is explicitly stopped (e.g., by a KeyboardInterrupt)
        or a critical error occurs that prevents further operation.

        Raises
        ------
        DbError
            If an error occurs while attempting to retrieve the latest message
            timestamp from the database during initialization or reconnection.
        BridgeError
            If an error related to the Go bridge connection occurs during the
            polling cycle or during attempts to reinitialize the client.
        ApiError
            If an error occurs during an API call made to the Go bridge
            while fetching messages or reinitializing the client.
        WhatsappPkgError
            For other package-specific errors encountered during the polling
            process or client reinitialization.
        KeyboardInterrupt
            If the polling loop is interrupted by the user, typically via
            a signal like Ctrl+C.
        Exception
            For any other unexpected errors that occur within the main polling loop.
        """
        self.logger.info("Bot started and polling for updates...")

        # Attempt to initialize the client. If this fails, the bot cannot run.
        if not self.listener._initialize_client():
            self.logger.critical("Listener cannot start due to client initialization failure.")
            return

        # Determine the starting timestamp for fetching messages to avoid processing old messages
        start_time: datetime
        try:
            self.logger.info("Determining initial message check timestamp from database...")
            latest_db_ts = get_latest_message_timestamp_utc()
            if latest_db_ts:
                # Start checking from 1 millisecond after the latest known message to avoid duplicates
                start_time = latest_db_ts + timedelta(milliseconds=1)
                self.logger.info(
                    f"Found latest DB timestamp: {latest_db_ts.isoformat()}. Starting poll from {start_time.isoformat()}."
                )
            else:
                # If no timestamp in DB (e.g., first run), start checking from 1 minute ago
                start_time = datetime.now(timezone.utc) - timedelta(minutes=1)
                self.logger.info(
                    f"No DB timestamp found. Starting poll from {start_time.isoformat()} (last minute)."
                )
            if self.listener.client:
                 self.listener.client._last_message_check_time = start_time
        except DbError as e:
            self.logger.error(
                f"DB error getting latest timestamp: {e}. Defaulting poll start to 1 min ago.",
                exc_info=True,
            )
            if self.listener.client:
                 self.listener.client._last_message_check_time = datetime.now(
                    timezone.utc
                ) - timedelta(minutes=1)
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting latest timestamp: {e}. Defaulting poll start to 1 min ago.",
                exc_info=True,
            )
            if self.listener.client:
                 self.listener.client._last_message_check_time = datetime.now(
                    timezone.utc
                ) - timedelta(minutes=1)

        # Clear the set of seen message IDs at the start of polling to ensure a clean state
        # This set prevents reprocessing messages seen within the current polling session.
        self._seen_ids.clear()
        self.listener._running = True
        self.logger.info(f"Starting polling loop with interval: {self.listener.poll_interval}s")

        try:
            # Main polling loop runs as long as the listener's _running flag is True
            while self.listener._running:
                # Periodically check if the underlying Go bridge process is still alive
                # If it's not alive, attempt reconnection.
                # Reconnection logic after bridge death is handled in Application.run_polling,
                # but the listener itself should stop if its bridge becomes unresponsive.
                if self.listener.client and not self.listener.client._bridge_manager.check_if_alive():
                    self.logger.error(
                        "Bridge process died unexpectedly. Attempting reconnection..."
                    )
                    # Attempt to reinitialize the client and bridge.
                    # If reinitialization fails, log the error and continue the loop,
                    # allowing the next iteration to attempt reconnection again.
                    if not self.listener._initialize_client():
                        self.logger.error(
                            "Client reinitialization failed. Will retry in next interval."
                        )
                        # Sleep longer on failure before retrying the loop check to prevent rapid failure loops
                        time.sleep(self.listener.poll_interval * 2)
                    else:
                        self.logger.info(
                            "Client reinitialized and bridge connected successfully."
                        )
                        # Reset the timestamp for the *new* client instance after successful reconnect
                        try:
                            self.logger.info(
                                "Determining message check timestamp after reconnect..."
                            )
                            latest_db_ts_reconnect = get_latest_message_timestamp_utc()
                            if latest_db_ts_reconnect:
                                start_time_reconnect = (
                                    latest_db_ts_reconnect + timedelta(milliseconds=1)
                                )
                                self.logger.info(
                                    f"Found latest DB timestamp: {latest_db_ts_reconnect.isoformat()}. Starting poll from {start_time_reconnect.isoformat()}."
                                )
                            else:
                                start_time_reconnect = datetime.now(
                                    timezone.utc
                                ) - timedelta(minutes=1)
                                self.logger.info(
                                    f"No DB timestamp found. Starting poll from {start_time_reconnect.isoformat()} (last minute)."
                                )
                            if self.listener.client:
                                self.listener.client._last_message_check_time = (
                                    start_time_reconnect
                                )
                            # Also clear seen IDs after a successful reconnect to ensure no messages are missed
                            self._seen_ids.clear()
                        except DbError as e_reconnect:
                            self.logger.error(
                                f"DB error getting latest timestamp after reconnect: {e_reconnect}. Defaulting poll start to 1 min ago.",
                                exc_info=True,
                            )
                            if self.listener.client:
                                self.listener.client._last_message_check_time = (
                                    datetime.now(timezone.utc) - timedelta(minutes=1)
                                )
                        except Exception as e_reconnect_other:
                            self.logger.error(
                                f"Unexpected error getting latest timestamp after reconnect: {e_reconnect_other}. Defaulting poll start to 1 min ago.",
                                exc_info=True,
                            )
                            if self.listener.client:
                                self.listener.client._last_message_check_time = (
                                    datetime.now(timezone.utc) - timedelta(minutes=1)
                                )

                    # Sleep briefly before continuing the loop after handling bridge status
                    time.sleep(self.listener.poll_interval)
                    continue

                # Fetch new messages from the client. Media download is handled by the listener's
                # _process_message method if needed, so we request download here.
                new_messages: List[Dict[str, Any]] = []
                if self.listener.client:
                    try:
                         new_messages = self.listener.client.get_new_messages(
                            download_media=True
                        )
                    except (BridgeError, ApiError) as e:
                        self.logger.error(f"Error fetching new messages: {e}", exc_info=True)
                        # Continue the loop after logging the error, allowing for potential recovery
                        time.sleep(self.listener.poll_interval)
                        continue

                # Filter out messages sent by the bot itself and messages already seen
                # Messages sent by self are typically echo responses or other outgoing messages.
                # The _seen_ids set prevents reprocessing messages seen within the current polling session.
                processable_messages = [
                    m
                    for m in new_messages
                    if not m.get("is_from_me", False) and m.get("id") not in self._seen_ids
                ]

                # Process each new message that passes the filter
                for msg in processable_messages:
                    # Add the message ID to the seen set to prevent reprocessing
                    if msg.get("id"):
                        self._seen_ids.add(msg["id"])

                    # Create an Update object to wrap the message data
                    update = Update(msg)

                    # Create a context object to pass to handlers
                    # This could be extended in the future to include more context data
                    context = ContextTypes.DEFAULT_TYPE()
                    # Add the bot instance (client) to the context for handlers to use
                    context.bot = self.listener.client

                    # First, process all type handlers which are always invoked for every update
                    for handler in self._type_handlers:
                        self._invoke_handler(handler.callback, update, context)

                    # Then, process message handlers whose filters match the update
                    for handler in self._message_handlers:
                        try:
                            if handler.filter(update):
                                self._invoke_handler(handler.callback, update, context)
                        except Exception as e:
                            self.logger.error(
                                f"Error evaluating filter for handler {getattr(handler.callback, '__name__', 'unknown')}: {e}",
                                exc_info=True,
                            )

                # Sleep for the configured poll interval before checking for new messages again
                time.sleep(self.listener.poll_interval)

        except KeyboardInterrupt:
            self.logger.info("Bot polling stopped by keyboard interrupt.")
        except Exception as e:
            self.logger.critical(f"Bot polling stopped due to critical error: {e}", exc_info=True)
        finally:
            # Ensure the listener is stopped properly when exiting the polling loop
            self.listener._running = False
            if self.listener.client:
                try:
                    self.listener.client.disconnect()
                    self.logger.info("WhatsApp client disconnected.")
                except Exception as e:
                    self.logger.error(f"Error disconnecting WhatsApp client: {e}", exc_info=True)
            self.logger.info("Bot polling stopped.")
            
    def _invoke_handler(self, callback, update, context):
        """
        Invokes a handler callback function.

        This helper method is responsible for executing a given handler
        `callback` with the provided `update` and `context` objects.
        It supports both synchronous and asynchronous callbacks. Any exceptions
        raised during the callback's execution are caught internally and logged
        to prevent a single handler error from stopping the main polling loop.

        Parameters
        ----------
        callback : callable
            The handler function to invoke. This can be a synchronous or
            asynchronous function.
        update : Update
            The incoming update object to pass as the first argument to the handler.
        context : SimpleNamespace
            The context object to pass as the second argument to the handler.

        Raises
        ------
        Exception
            Catches and logs any exception raised by the handler callback.
            Exceptions are not re-raised to protect the polling loop's stability.
        """
        try:
            # Check if the callback is a coroutine function (async def)
            if inspect.iscoroutinefunction(callback):
                # Create a new event loop for this async callback
                loop = asyncio.new_event_loop()
                try:
                    # Run the coroutine in the event loop
                    loop.run_until_complete(callback(update, context))
                finally:
                    # Always close the loop to free resources
                    loop.close()
            else:
                # For regular synchronous functions, just call directly
                callback(update, context)
        except Exception as e:
            # Log the error but don't re-raise to protect the polling loop
            self.logger.error(
                f"Error in handler {getattr(callback, '__name__', 'unknown')}: {e}",
                exc_info=True,
            )


class ApplicationBuilder:
    """
    Builds an instance of the Application.

    Provides a fluent interface for configuring and creating the Application.
    """
    def __init__(self):
        """
        Initializes the ApplicationBuilder.
        """
        # Currently no specific builder parameters are strictly needed for
        # Application initialization, but this class follows a common builder
        # pattern and can be extended for future configuration options.
        pass
        
    def token(self, token: str) -> 'ApplicationBuilder':
        """
        Sets the token for the application (currently unused in Application init).

        This method exists for potential future use or compatibility with
        telegram-bot-like builder patterns. The token is not stored or used
        by the current Application implementation.

        Parameters
        ----------
        token : str
            The token string.

        Returns
        -------
        ApplicationBuilder
            The builder instance, allowing for method chaining.
        """
        # Token is not currently used in the WhatsApp implementation
        # but the method is provided for API compatibility with similar bot frameworks
        return self
        
    def build(self) -> Application:
        """
        Builds and returns a new Application instance.

        Returns
        -------
        Application
            The created Application instance.
        """
        return Application()
