import os
import sys
import shutil
import subprocess
from pathlib import Path

# Define a user-specific directory for storing the cloned repo and DB
DEFAULT_DATA_DIR = Path.home() / ".shubh_whatsapp_data"
# Try to get APPDATA on Windows for a more standard location
if sys.platform == "win32":
    appdata = os.getenv('APPDATA')
    if appdata:
        DEFAULT_DATA_DIR = Path(appdata) / "ShubhWhatsApp" # Use roaming appdata

DATA_DIR = Path(os.getenv("SHUBH_WHATSAPP_PKG_DATA_DIR", DEFAULT_DATA_DIR))
CLONED_REPO_PATH = DATA_DIR / "whatsapp-mcp"
GO_BRIDGE_DIR = CLONED_REPO_PATH / "whatsapp-bridge"
DB_PATH = GO_BRIDGE_DIR / "store" / "messages.db"
GO_BRIDGE_SRC_PATH = GO_BRIDGE_DIR / "main.go"
GO_BRIDGE_API_URL = "http://localhost:8080/api" # Default, could be configurable

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

WHATSAPP_MCP_REPO_URL = "https://github.com/lharries/whatsapp-mcp.git"

def _find_executable(name):
    """Checks if an executable exists in PATH."""
    return shutil.which(name) is not None

def check_prerequisites():
    """Checks for Go and Git installations."""
    missing = []
    if not _find_executable("go"):
        missing.append("Go (Please install from https://go.dev/dl/)")
    if not _find_executable("git"):
        missing.append("Git (Please install from https://git-scm.com/downloads)")
    return missing

def is_repo_cloned():
    """Checks if the repo seems to be cloned."""
    return GO_BRIDGE_SRC_PATH.exists()

def run_command(cmd_list, cwd=None, env=None, capture=False):
    """Helper to run shell commands."""
    print(f"Running command: {' '.join(cmd_list)} {'in '+str(cwd) if cwd else ''}")
    try:
        process = subprocess.run(
            cmd_list,
            cwd=cwd,
            env=env,
            check=True, # Raise exception on non-zero exit code
            capture_output=capture,
            text=True,
            encoding='utf-8' # Be explicit about encoding
        )
        if capture:
            print(f"Command stdout:\n{process.stdout}")
        if process.stderr:
             print(f"Command stderr:\n{process.stderr}")
        return True, process.stdout if capture else ""
    except FileNotFoundError:
         print(f"Error: Command not found: {cmd_list[0]}")
         return False, "Command not found"
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if capture:
             print(f"Stdout: {e.stdout}")
             print(f"Stderr: {e.stderr}")
        return False, e.stderr if capture else str(e)
    except Exception as e:
         print(f"Unexpected error running command: {e}")
         return False, str(e)

def clone_repo():
    """Clones the whatsapp-mcp repository."""
    if is_repo_cloned():
        print("Repository already cloned.")
        return True

    print(f"Cloning repository '{WHATSAPP_MCP_REPO_URL}' into '{CLONED_REPO_PATH}'...")
    # Ensure parent directory exists
    CLONED_REPO_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Clone into the specific directory
    success, _ = run_command(["git", "clone", WHATSAPP_MCP_REPO_URL, str(CLONED_REPO_PATH)])
    if success and is_repo_cloned():
         print("Repository cloned successfully.")
         return True
    else:
         print("Error: Failed to clone repository.")
         # Optional: Clean up partial clone attempt
         if CLONED_REPO_PATH.exists():
              try:
                   shutil.rmtree(CLONED_REPO_PATH)
                   print("Cleaned up partially cloned directory.")
              except OSError as e:
                   print(f"Warning: Could not clean up directory {CLONED_REPO_PATH}: {e}")
         return False