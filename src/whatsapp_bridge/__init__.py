"""
Whatsapp Bridge Package

This package provides a client for interacting with WhatsApp,
including functionalities for sending/receiving messages, managing
connections, and handling various aspects of WhatsApp communication.

- PyPI package name: 'whatsapp-bridge'
- Importable module: 'whatsapp_bridge'

It exports the main WhatsappClient class and custom exception types.
"""

from .core.client import WhatsappClient
from .exceptions import (
    WhatsappPkgError,
    PrerequisitesError,
    SetupError,
    BridgeError,
    ApiError,
    DbError,
)


__version__ = "0.1.0"


__all__ = [
    "WhatsappClient",
    "WhatsappPkgError",
    "PrerequisitesError",
    "SetupError",
    "BridgeError",
    "ApiError",
    "DbError",
    "__version__",
]
