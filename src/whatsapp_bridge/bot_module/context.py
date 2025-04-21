"""
Context Types

This module provides context objects that are passed to handler callbacks
when processing updates.
"""

from types import SimpleNamespace
from typing import Type, ClassVar


class ContextTypes:
    """
    Container for context types used in handler callbacks.

    This class defines the context types that will be passed to handler callbacks
    when processing updates. It provides a default context type and allows for
    custom context types to be defined.
    """

    DEFAULT_TYPE: ClassVar[Type[SimpleNamespace]] = SimpleNamespace

    def __init__(self, context_type: Type[SimpleNamespace] = None):
        """
        Initializes a new instance of ContextTypes.

        Parameters
        ----------
        context_type : Type[SimpleNamespace], optional
            The type to use for the context object. If None, the default type
            will be used.
        """
        self.context_type = context_type or self.DEFAULT_TYPE
