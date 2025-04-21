import json
import sys
import logging
from pathlib import Path
from ..config import settings

# Setup logger for this module
log = logging.getLogger(__name__)

STATE_DIR_NAME = "whatsapp_state"
METADATA_FILENAME = "metadata.json"


def _get_state_dir() -> Path:
    """
    Gets the path to the state directory.

    The state directory is located within the application's data directory
    and is used to store metadata like the first run completion status.

    Returns
    -------
    Path
        The pathlib.Path object representing the state directory.
    """
    return settings.DATA_DIR / STATE_DIR_NAME


def _get_metadata_path() -> Path:
    """
    Gets the path to the metadata file.

    The metadata file is stored within the state directory and contains
    information about the application's state, such as whether the
    first run setup has been completed.

    Returns
    -------
    Path
        The pathlib.Path object representing the metadata file path.
    """
    return _get_state_dir() / METADATA_FILENAME


def is_first_run() -> bool:
    """
    Checks if this is the first run of the application.

    This is determined by looking for the existence of the metadata file
    and checking if the 'first_run_completed' flag within it is True.
    If the file doesn't exist or cannot be read, it's considered the first run.

    Returns
    -------
    bool
        True if this is considered the first run, False otherwise.
    """
    metadata_path = _get_metadata_path()
    log.debug(f"Checking for first run status at {metadata_path}")

    if not metadata_path.is_file():
        log.debug("Metadata file not found. Considered first run.")
        return True

    try:
        with open(metadata_path, "r") as f:
            data = json.load(f)
        is_completed = data.get("first_run_completed", False)
        log.debug(f"Metadata file found. 'first_run_completed' is {is_completed}. First run: {not is_completed}")
        return not is_completed
    except (json.JSONDecodeError, OSError) as e:
        log.warning(f"Could not read or decode metadata file {metadata_path}: {e}. Considered first run.", exc_info=True)
        # If the file exists but is corrupted or unreadable, treat it as first run
        return True


def mark_first_run_completed():
    """
    Marks the first run as completed.

    This function creates the state directory if it doesn't exist and writes
    a metadata file containing the `first_run_completed: True` flag.
    Errors during directory creation or file writing are logged as warnings.
    """
    state_dir = _get_state_dir()
    metadata_path = _get_metadata_path()
    log.debug(f"Attempting to mark first run as completed by writing to {metadata_path}")

    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        metadata = {"first_run_completed": True}
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
        log.info(f"Successfully marked first run as completed in {metadata_path}")

    except OSError as e:
        log.warning(
            f"Could not write first run state to {metadata_path}: {e}",
            exc_info=True,
        )
    except Exception as e:
        log.warning(
            f"Unexpected error writing first run state to {metadata_path}: {e}",
            exc_info=True,
        )
