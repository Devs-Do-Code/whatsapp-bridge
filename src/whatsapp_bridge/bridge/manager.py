"""
Go Bridge Manager

This module provides the BridgeManager class for starting, stopping,
and managing the subprocess running the Go bridge application. It
handles capturing stdout and stderr from the subprocess using threads
and queues.
"""

# This file now imports from the manager_module package for better code organization
from .manager_module import BridgeManager, enqueue_output