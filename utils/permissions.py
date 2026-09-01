"""Windows administrator privilege detection and elevation."""
import sys
import os
import ctypes
from utils.logger import get_logger

logger = get_logger(__name__)


def is_admin() -> bool:
    """
    Checks if the current process is running with Windows Administrator privileges.
    Returns True if elevated, False otherwise.
    """
    try:
        if os.name == "nt":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        else:
            # Unix-like fallback
            return os.geteuid() == 0  # type: ignore[attr-defined]
    except Exception as e:
        logger.warning("Error checking admin privileges: %s", e)
        return False


def request_elevation() -> bool:
    """
    Relaunches the current script with elevated administrator privileges via UAC.
    Returns True if the elevation request was dispatched, False otherwise.
    """
    if is_admin():
        return True

    if os.name != "nt":
        logger.error("Privilege elevation via UAC is only supported on Windows.")
        return False

    try:
        if getattr(sys, "frozen", False):
            # In compiled exe mode, sys.executable is the application exe
            exe = sys.executable
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        else:
            # In script mode, relaunch python interpreter with the script path
            exe = sys.executable
            script = os.path.abspath(sys.argv[0])
            params = f'"{script}" ' + " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            params = params.strip()

        # Call ShellExecuteW with 'runas' verb to trigger UAC
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            exe,
            params,
            None,
            1  # SW_SHOWNORMAL
        )
        
        # ShellExecute returns > 32 on success
        if ret > 32:
            logger.info("UAC elevation prompt triggered successfully.")
            return True
        else:
            logger.error("ShellExecute returned code %s for runas.", ret)
            return False
    except Exception as e:
        logger.error("Failed to request admin elevation: %s", e)
        return False
