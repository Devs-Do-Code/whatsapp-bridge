"""
Update and Context Types

This module provides the Update class for representing incoming updates
from WhatsApp and the ContextTypes class for defining context objects
passed to handlers.
"""

from types import SimpleNamespace
from typing import Dict, Any, TypeVar, Type

# Define a type variable for ContextTypes for better type hinting
ContextType = TypeVar("ContextType", bound=SimpleNamespace)


class Update:
    """
    Represents an incoming update from WhatsApp.

    This class is used to wrap raw message data fetched from the WhatsApp
    client and provide a consistent structure for processing by handlers.

    Attributes
    ----------
    message : Dict[str, Any]
        The raw message data dictionary as returned by
        :meth:`whatsapp.core.client.WhatsappClient.get_new_messages`.
    """
    def __init__(self, message: Dict[str, Any]):
        """
        Initializes an Update object.

        Parameters
        ----------
        message : Dict[str, Any]
            The raw message data dictionary.
        """
        self.message: Dict[str, Any] = message


class ContextTypes:
    """
    Defines the types of context objects passed to handlers.

    This class provides a way to specify the expected type of the `context`
    object that will be passed to handler callbacks. It currently provides
    a default :class:`types.SimpleNamespace` type but can be extended
    to support custom context types in the future.

    Attributes
    ----------
    DEFAULT_TYPE : Type[SimpleNamespace]
        The default context type, which is :class:`types.SimpleNamespace`.
    """
    DEFAULT_TYPE: Type[SimpleNamespace] = SimpleNamespace
