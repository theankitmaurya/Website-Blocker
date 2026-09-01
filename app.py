"""Application entrypoint and Qt lifecycle."""
import sys
import ctypes
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.config import ASSETS_DIR, APP_NAME
from utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> int:
    """Initializes and runs the Qt Application."""
    # Ensure Windows taskbar displays the custom app icon
    try:
        myappid = "WebsiteBlocker.Productivity.App.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    configure_logging()
    logger.info("Starting Website Blocker application...")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Productivity")

    icon_ico = ASSETS_DIR / "icon.ico"
    icon_png = ASSETS_DIR / "icon.png"
    icon_path = icon_ico if icon_ico.exists() else icon_png
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)

    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()

    exit_code = app.exec()
    logger.info("Application exited with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
