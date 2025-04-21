import json
import sys
from pathlib import Path

from whatsapp.config import settings

STATE_DIR_NAME = ".dump"
METADATA_FILENAME = "metadata.json"


def _get_state_dir() -> Path:
    """Gets the path to the state directory."""

    return settings.DATA_DIR / STATE_DIR_NAME


def _get_metadata_path() -> Path:
    """Gets the path to the metadata file."""
    return _get_state_dir() / METADATA_FILENAME


def is_first_run() -> bool:
    """
    Checks if this is the first run by looking for the metadata file
    and the 'first_run_completed' flag.
    """
    metadata_path = _get_metadata_path()
    if not metadata_path.is_file():
        return True

    try:
        with open(metadata_path, "r") as f:
            data = json.load(f)
        return not data.get("first_run_completed", False)
    except (json.JSONDecodeError, OSError):

        return True


def mark_first_run_completed():
    """
    Marks the first run as completed by creating the state directory
    and writing the metadata file.
    """
    state_dir = _get_state_dir()
    metadata_path = _get_metadata_path()

    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        metadata = {"first_run_completed": True}
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

    except OSError as e:

        print(
            f"Warning: Could not write first run state to {metadata_path}: {e}",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"Warning: Unexpected error writing first run state to {metadata_path}: {e}",
            file=sys.stderr,
        )
