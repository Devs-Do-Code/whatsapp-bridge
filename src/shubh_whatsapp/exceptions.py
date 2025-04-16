class WhatsappPkgError(Exception):
    """Base exception for this package."""
    pass

class PrerequisitesError(WhatsappPkgError):
    """Raised when Go or Git is not found."""
    pass

class SetupError(WhatsappPkgError):
    """Raised when repository cloning fails."""
    pass

class BridgeError(WhatsappPkgError):
    """Raised for Go bridge process issues."""
    pass

class ApiError(WhatsappPkgError):
    """Raised for errors communication with the Go bridge API."""
    pass

class DbError(WhatsappPkgError):
    """Raised for database reading errors."""
    pass