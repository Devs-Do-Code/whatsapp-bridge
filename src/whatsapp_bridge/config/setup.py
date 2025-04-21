"""
Setup Utilities

This module provides functions for setting up the application environment,
including checking for prerequisites like Go and Git, and cloning the
necessary Go bridge repository.
"""

import shutil
import sys

from . import settings
from ..exceptions import SetupError
from ..utils import commands


def _find_executable(name: str) -> bool:
    """
    Checks if an executable exists in the system's PATH.

    Args:
        name (str): The name of the executable to search for.

    Returns:
        bool: True if the executable is found, False otherwise.
    """
    return shutil.which(name) is not None


def check_prerequisites() -> list[str]:
    """
    Checks for Go and Git installations.

    Verifies if the 'go' and 'git' executables are available in the system's PATH.

    Returns:
        list[str]: A list of missing prerequisites, if any.
    """
    missing = []
    if not _find_executable("go"):
        missing.append("Go (Please install from https://go.dev/dl/)")
    if not _find_executable("git"):
        missing.append("Git (Please install from https://git-scm.com/downloads)")
    return missing


def is_repo_cloned() -> bool:
    """
    Checks if the whatsapp-mcp repository seems to be cloned.

    This is determined by checking for the existence of the main Go bridge
    source file.

    Returns:
        bool: True if the source file exists, indicating the repo is likely cloned.
    """
    return settings.GO_BRIDGE_SRC_PATH.exists()


import logging
log = logging.getLogger(__name__)

def clone_repo() -> bool:
    """
    Clones the whatsapp-mcp repository using the command utility.

    Clones the repository specified in settings.WHATSAPP_MCP_REPO_URL to
    the path defined in settings.CLONED_REPO_PATH. Handles directory
    creation and basic error checking.

    Returns:
        bool: True if the repository was cloned successfully or was already present.

    Raises:
        SetupError: If the parent directory for cloning cannot be created or
                    if the git clone command fails.
    """
    if is_repo_cloned():
        log.info("Repository already cloned.")
        return True

    repo_url = settings.WHATSAPP_MCP_REPO_URL
    clone_path = settings.CLONED_REPO_PATH

    log.info(f"Cloning repository '{repo_url}' into '{clone_path}'...")
    try:
        clone_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        log.error(
            f"Could not create parent directory {clone_path.parent}: {e}",
            exc_info=True,
        )
        raise SetupError(f"Failed to create directory for cloning: {e}") from e

    success, output = commands.run_command(["git", "clone", repo_url, str(clone_path)])

    if success and is_repo_cloned():
        log.info("Repository cloned successfully.")
        return True
    else:
        log.error(f"Failed to clone repository. Output: {output}")
        if clone_path.exists():
            try:
                log.info(
                    f"Attempting to clean up partially cloned directory: {clone_path}"
                )
                shutil.rmtree(clone_path)
                log.info("Cleaned up directory.")
            except OSError as e:
                log.warning(
                    f"Could not clean up directory {clone_path}: {e}",
                    exc_info=True,
                )
        raise SetupError(
            f"Failed to clone repository from {repo_url}. Git output: {output}"
        )
