"""
Application Settings

This module defines constants and settings used throughout the application,
including default paths for data, the Go bridge, and the database.
It also handles platform-specific data directory location.
"""

import os
import sys
from pathlib import Path


DEFAULT_DATA_DIR = Path.home() / ".whatsapp_data"

if sys.platform == "win32":
    appdata = os.getenv("APPDATA")
    if appdata:

        DEFAULT_DATA_DIR = Path(appdata) / "Whatsapp"


DATA_DIR = Path(os.getenv("WHATSAPP_PKG_DATA_DIR", DEFAULT_DATA_DIR))


CLONED_REPO_PATH = DATA_DIR / "whatsapp-mcp"
GO_BRIDGE_DIR = CLONED_REPO_PATH / "whatsapp-bridge"
DB_PATH = GO_BRIDGE_DIR / "store" / "messages.db"
GO_BRIDGE_SRC_PATH = GO_BRIDGE_DIR / "main.go"
DOWNLOADED_MEDIA_DIR = DATA_DIR / "downloaded_media"


GO_BRIDGE_API_URL = "http://localhost:8080/api"
WHATSAPP_MCP_REPO_URL = "https://github.com/lharries/whatsapp-mcp.git"


try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    # Use logging instead of print for consistency
    import logging
    log = logging.getLogger(__name__)
    log.warning(f"Could not create data directory {DATA_DIR}: {e}", exc_info=True)
