"""
Custom exceptions for the Whatsapp package.

This module defines a hierarchy of custom exceptions used throughout the
package to indicate specific error conditions related to prerequisites,
setup, the Go bridge, API communication, and database operations.
"""


class WhatsappPkgError(Exception):
    """
    Base exception for the Whatsapp package.

    All custom exceptions within this package inherit from this class.
    """

    pass


class PrerequisitesError(WhatsappPkgError):
    """
    Raised when required external dependencies are not found.

    This includes dependencies like Go or Git, which are necessary
    for setting up and running the Go bridge.
    """

    pass


class SetupError(WhatsappPkgError):
    """
    Raised when the initial setup process fails.

    This typically occurs during repository cloning or other initial
    configuration steps for the Go bridge.
    """

    pass


class BridgeError(WhatsappPkgError):
    """
    Raised for issues related to the Go bridge process.

    This can include errors starting, stopping, or communicating with
    the background Go process.
    """

    pass


class ApiError(WhatsappPkgError):
    """
    Raised for errors during communication with the Go bridge API.

    This indicates a problem when sending requests to or receiving
    responses from the running Go bridge API server.
    """

    pass


class DbError(WhatsappPkgError):
    """
    Raised for errors encountered during database operations.

    This includes issues with reading from the local SQLite message
    database managed by the Go bridge.
    """

    pass
