import subprocess
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union

# Setup logger for this module
log = logging.getLogger(__name__)


def run_command(
    cmd_list: List[str],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
    capture: bool = False,
) -> Tuple[bool, str]:
    """
    Helper to run shell commands, capturing output if requested.

    Args:
        cmd_list: List of command arguments.
        cwd: Optional working directory to run the command in.
        env: Optional environment variables dictionary.
        capture: If True, capture and return stdout/stderr.

    Returns
    -------
    Tuple[bool, str]
        A tuple containing:
        - A boolean indicating whether the command executed successfully (True) or failed (False).
        - A string containing the captured output (stdout if successful and capture=True,
          or stderr/error message if unsuccessful).
    """
    cmd_str = " ".join(cmd_list)
    cwd_str = f" in {cwd}" if cwd else ""
    log.debug(f"Running command: {cmd_str}{cwd_str}")
    try:
        process = subprocess.run(
            cmd_list,
            cwd=cwd,
            env=env,
            check=True,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = ""
        if capture:
            output = process.stdout
            log.debug(f"Command stdout:\n{output}")
        if process.stderr:
            log.warning(f"Command stderr:\n{process.stderr}")
        return True, output
    except FileNotFoundError:
        err_msg = f"Error: Command not found: {cmd_list[0]}"
        log.error(err_msg, exc_info=True)
        return False, err_msg
    except subprocess.CalledProcessError as e:
        err_msg = f"Error running command '{cmd_str}': Exit code {e.returncode}"
        log.error(err_msg, exc_info=True)
        if capture:
            log.error(f"Stdout: {e.stdout}")
            log.error(f"Stderr: {e.stderr}")
            err_msg += f"\nStdout: {e.stdout}\nStderr: {e.stderr}"
        return False, e.stderr if capture and e.stderr else err_msg
    except Exception as e:
        err_msg = f"Unexpected error running command '{cmd_str}': {e}"
        log.error(err_msg, exc_info=True)
        return False, err_msg
