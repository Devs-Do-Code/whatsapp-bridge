"""
Go Bridge Manager Module

This package provides components for starting, stopping, and managing 
the subprocess running the Go bridge application.
"""

from .bridge_manager import BridgeManager
from .stream_handler import enqueue_output
from .process_management import stop_process
from .output_handler import read_output_queues, check_process_status
