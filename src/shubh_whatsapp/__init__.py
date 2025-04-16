# Expose the main client class for easy import
from .client import WhatsappClient
from .exceptions import WhatsappPkgError, PrerequisitesError, SetupError, BridgeError, ApiError, DbError

__version__ = "0.1.0" # Define package version

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