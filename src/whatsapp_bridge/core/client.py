"""
WhatsApp Client Entry Point

This module serves as the primary entry point for the WhatsApp client functionality.
It imports and re-exports the core components from the refactored `client_module`
package, providing a cleaner interface for users of the library.
"""

# Import the core WhatsappClient class from the client_module package
from .client_module import WhatsappClient

# Explicitly re-export the main client class for external use
__all__ = [
    "WhatsappClient",
]
