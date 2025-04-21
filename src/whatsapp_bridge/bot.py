"""
WhatsApp Bot Entry Point

This module serves as the primary entry point for the WhatsApp bot application functionality.
It imports and re-exports the core components from the refactored `bot_module`
package, providing a cleaner interface for users building bots with the library.
"""

# Import necessary components from the bot_module package
from .bot_module import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    Update,
    MessageHandler,
    TypeHandler,
    Filter,
    TextFilter,
    CommandFilter,
)

# Explicitly re-export the components for external use
__all__ = [
    "Application",
    "ApplicationBuilder",
    "ContextTypes",
    "Update",
    "MessageHandler",
    "TypeHandler",
    "Filter",
    "TextFilter",
    "CommandFilter",
]
