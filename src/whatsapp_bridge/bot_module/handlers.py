"""
Message Handlers

This module provides handler classes for processing incoming updates
based on specific filters or types.
"""

import logging
from typing import Callable, Any, Optional, Dict, List, Union, Type

from .update import Update
from .filters import Filter

log = logging.getLogger(__name__)


class TypeHandler:
    """
    Handler class to handle updates regardless of their type.

    This handler will be called for every incoming update, regardless of its
    content or type. It is useful for operations that should be performed for
    all updates, such as logging or analytics.
    """

    def __init__(self, callback: Callable[[Update, Any], None]):
        """
        Initializes a new instance of TypeHandler.

        Parameters
        ----------
        callback : Callable[[Update, Any], None]
            The callback function to execute for every update. The function
            should accept two parameters: the update object and a context object.
        """
        self.callback = callback


class MessageHandler:
    """
    Handles incoming messages that match a specific filter.

    When an update arrives, its filter is applied. If the filter passes,
    the handler's callback function is invoked with the update and context.
    """
    def __init__(self, filter: Filter, callback: Callable):
        """
        Initializes a MessageHandler.

        Parameters
        ----------
        filter : Filter
            The filter to apply to incoming updates.
        callback : callable
            The function to call when the filter matches. This function should
            accept `update` and `context` as arguments.

        Raises
        ------
        TypeError
            If `filter` is not a Filter instance or `callback` is not callable.
        """
        if not isinstance(filter, Filter):
             raise TypeError("MessageHandler requires a Filter object")
        if not callable(callback):
             raise TypeError("MessageHandler requires a callable callback")
        self.filter: Filter = filter
        self.callback: Callable = callback


class TypeHandler:
    """
    Handles updates of a specific type (currently only handles all updates).

    This handler type is intended for processing updates based on their type,
    though the current implementation primarily focuses on message updates.
    It is always invoked for every incoming update after the update and context
    objects are created.
    """
    def __init__(self, callback: Callable):
        """
        Initializes a TypeHandler.

        Parameters
        ----------
        callback : callable
            The function to call for the update type. This function should
            accept `update` and `context` as arguments.

        Raises
        ------
        TypeError
            If `callback` is not callable.
        """
        if not callable(callback):
             raise TypeError("TypeHandler requires a callable callback")
        self.callback: Callable = callback
