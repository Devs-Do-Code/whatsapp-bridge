"""
Setup Module

This module handles the setup process for the WhatsApp Go bridge,
including checking prerequisites and cloning the necessary repository.
"""

import logging
from typing import List

from ...config import setup as config_setup
from ...exceptions import PrerequisitesError, SetupError

log = logging.getLogger(__name__)


def run_setup(is_first_run: bool) -> None:
    """
    Checks system prerequisites (Go, Git) and clones the required repository
    if it's not already present.

    Detailed status messages are printed only during the first run
    as indicated by the `is_first_run` flag.

    Parameters
    ----------
    is_first_run : bool
        A boolean flag indicating whether this is the first time the setup
        process is being run. Used to control log verbosity.

    Raises
    ------
    PrerequisitesError
        If required system prerequisites (Go, Git) are not found.
    SetupError
        If cloning the necessary repository fails.
    """
    if is_first_run:
        log.info(">>> Running Setup Check...")

    missing = config_setup.check_prerequisites()
    if missing:
        missing_str = "\n".join(f"- {m}" for m in missing)
        log.error(f"Missing prerequisites:\n{missing_str}")
        raise PrerequisitesError(f"Missing prerequisites:\n{missing_str}")

    if is_first_run:
        log.info("Prerequisites (Go, Git) found.")

    if not config_setup.is_repo_cloned():
        if is_first_run:
            log.info("Whatsapp-mcp repository not found. Attempting to clone...")
        try:
            config_setup.clone_repo()
            if is_first_run:
                log.info("Repository cloned successfully.")
        except SetupError as e:
            log.error(f"Failed to clone the necessary repository: {e}", exc_info=True)
            raise SetupError(f"Failed to clone the necessary repository: {e}") from e
    elif is_first_run:
        log.info("Repository found.")

    if is_first_run:
        log.info(">>> Setup Check Complete.")
