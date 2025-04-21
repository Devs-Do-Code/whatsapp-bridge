"""
Core Connection and Setup

This module handles the setup and connection process for the WhatsApp Go bridge.
It includes the `run_setup` function to check prerequisites and clone the
necessary repository, and the `ConnectionManager` class to manage the lifecycle
of the bridge process and monitor its connection state.
"""

# This file now imports from the connection_module package for better code organization
from .connection_module import run_setup, ConnectionManager
