"""
WhatsApp Listener Entry Point

This module serves as the primary entry point for the WhatsApp message listener functionality.
It imports and re-exports the core components from the refactored `listener_module`
package, providing a cleaner interface for users of the library.
"""

# Import necessary components from the listener_module package
from .listener_module import (
    MessageListener,
    # Add other relevant components if needed, e.g., constants like BASE_DATA_DIR
)

# Explicitly re-export the components for external use
__all__ = [
    "MessageListener",
    # Add other exported names here
]
