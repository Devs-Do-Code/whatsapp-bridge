"""
Whatsapp Client Module

This package provides components for interacting with WhatsApp via the Go bridge.
It abstracts the complexities of managing the bridge process and interacting
with its API and database.
"""

from .whatsapp_client import WhatsappClient
from .media_handler import download_media
