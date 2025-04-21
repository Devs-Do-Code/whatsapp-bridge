"""
Message Filters

This module provides filter classes for determining which incoming updates
should be processed by specific handlers. It includes base filter classes
and common filter implementations for text and command messages.
"""

import logging
from types import SimpleNamespace
from typing import Any

from .update import Update

log = logging.getLogger(__name__)


class Filter:
    """
    Base class for message filters.

    Filters are used to determine which incoming updates should be processed
    by a specific handler. Subclasses must override the :meth:`__call__` method
    to implement specific filtering logic.
    """
    def __and__(self, other: "Filter") -> "AndFilter":
        """
        Combines this filter with another using logical AND.

        Parameters
        ----------
        other : Filter
            The other filter to combine with.

        Returns
        -------
        AndFilter
            A new filter representing the logical AND of the two filters.

        Raises
        ------
        TypeError
            If the other object is not a Filter instance.
        """
        if not isinstance(other, Filter):
            raise TypeError("Can only combine Filter objects with &")
        return AndFilter(self, other)

    def __invert__(self) -> "NotFilter":
        """
        Negates this filter using logical NOT.

        Returns
        -------
        NotFilter
            A new filter representing the logical NOT of this filter.
        """
        return NotFilter(self)

    def __call__(self, update: Update) -> bool:
        """
        Applies the filter to an update.

        This method must be overridden by subclasses to implement specific
        filtering logic. The base implementation always returns False.

        Parameters
        ----------
        update : Update
            The incoming update to filter.

        Returns
        -------
        bool
            True if the update passes the filter, False otherwise.
        """
        return False


class AndFilter(Filter):
    """
    Combines two filters with logical AND.

    This filter passes an update only if both of its component filters pass
    the update.
    """
    def __init__(self, f1: Filter, f2: Filter):
        """
        Initializes an AndFilter.

        Parameters
        ----------
        f1 : Filter
            The first filter.
        f2 : Filter
            The second filter.

        Raises
        ------
        TypeError
            If either `f1` or `f2` is not a Filter instance.
        """
        if not isinstance(f1, Filter) or not isinstance(f2, Filter):
             raise TypeError("AndFilter requires two Filter objects")
        self.f1: Filter = f1
        self.f2: Filter = f2

    def __call__(self, update: Update) -> bool:
        """
        Applies the combined filter to an update.

        Checks if both component filters pass the given update.

        Parameters
        ----------
        update : Update
            The incoming update to filter.

        Returns
        -------
        bool
            True if both component filters pass, False otherwise.

        Raises
        ------
        Exception
            Catches and logs any unexpected error during filter evaluation.
            Returns False on error to prevent handler execution.
        """
        try:
            # Evaluate both filters; short-circuits if f1 is False
            return self.f1(update) and self.f2(update)
        except Exception as e:
            # Log errors occurring during filter evaluation to aid debugging
            # Return False on error to prevent handler execution
            log.error(f"Error evaluating AndFilter ({type(self.f1).__name__} & {type(self.f2).__name__}): {e}", exc_info=True)
            return False


class NotFilter(Filter):
    """
    Negates a filter with logical NOT.

    This filter passes an update if and only if its component filter does
    *not* pass the update.
    """
    def __init__(self, f: Filter):
        """
        Initializes a NotFilter.

        Parameters
        ----------
        f : Filter
            The filter to negate.

        Raises
        ------
        TypeError
            If `f` is not a Filter instance.
        """
        if not isinstance(f, Filter):
             raise TypeError("NotFilter requires a Filter object")
        self.f: Filter = f

    def __call__(self, update: Update) -> bool:
        """
        Applies the negated filter to an update.

        Checks if the original filter does *not* pass the given update.

        Parameters
        ----------
        update : Update
            The incoming update to filter.

        Returns
        -------
        bool
            True if the original filter does not pass, False otherwise.

        Raises
        ------
        Exception
            Catches and logs any unexpected error during filter evaluation.
            Returns False on error to prevent handler execution.
        """
        try:
            # Negate the result of the original filter
            return not self.f(update)
        except Exception as e:
            # Log errors occurring during filter evaluation to aid debugging
            # Return False on error to prevent handler execution
            log.error(f"Error evaluating NotFilter (~{type(self.f).__name__}): {e}", exc_info=True)
            return False


class TextFilter(Filter):
    """
    Filters for messages containing non-empty string content in the 'content' field.

    This filter checks if the 'content' field of the message in the update
    exists, is a string, and is not empty.
    """
    def __call__(self, update: Update) -> bool:
        """
        Applies the text filter.

        Parameters
        ----------
        update : Update
            The incoming update to filter.

        Returns
        -------
        bool
            True if the message content is a non-empty string, False otherwise.
        """
        try:
            message = update.message
            content = message.get("content")
            return isinstance(content, str) and bool(content)
        except Exception as e:
            log.error(f"Error evaluating TextFilter: {e}", exc_info=True)
            return False


class CommandFilter(Filter):
    """
    Filters for messages where the 'content' field is a string starting with a command prefix ('/').

    This filter checks if the 'content' field of the message in the update
    exists, is a string, and starts with the '/' character, indicating
    a potential command.
    """
    def __call__(self, update: Update) -> bool:
        """
        Applies the command filter.

        Parameters
        ----------
        update : Update
            The incoming update to filter.

        Returns
        -------
        bool
            True if the message content is a string starting with '/', False otherwise.
        """
        try:
            message = update.message
            content = message.get("content")
            return isinstance(content, str) and content.startswith("/")
        except Exception as e:
            log.error(f"Error evaluating CommandFilter: {e}", exc_info=True)
            return False


# Pre-instantiated common filters for easy access
filters = SimpleNamespace(TEXT=TextFilter(), COMMAND=CommandFilter())
