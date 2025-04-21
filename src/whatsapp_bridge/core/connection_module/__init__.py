"""
Core Connection and Setup Module

This package provides components for handling the setup and connection process 
for the WhatsApp Go bridge. It includes functions to check prerequisites and 
clone repositories, and classes to manage connection lifecycle.
"""

from .setup import run_setup
from .connection_manager import ConnectionManager
