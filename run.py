"""Bootstrap launcher with Windows Administrator privilege verification and elevation."""
import sys
import os
from utils.permissions import is_admin, request_elevation
from utils.logger import configure_logging, get_logger

# Ensure root directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


def launch() -> None:
    try:
        configure_logging()
        logger = get_logger("Launcher")

        if not is_admin():
            logger.info("Administrator privileges not detected. Prompting for UAC elevation...")
            elevated = request_elevation()
            if elevated:
                # Elevation dispatched, exit the un-elevated parent process cleanly
                sys.exit(0)
            else:
                logger.warning("Elevation was cancelled or failed. Running in standard user mode.")

        from app import main
        sys.exit(main())
    except Exception as e:
        import traceback
        import ctypes
        err_msg = traceback.format_exc()
        try:
            logger.critical("Fatal startup error:\n%s", err_msg)
        except Exception:
            pass
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Error starting Website Blocker:\n\n{err_msg}",
            "Website Blocker Error",
            0x10  # MB_ICONERROR
        )
        sys.exit(1)


if __name__ == "__main__":
    launch()
