"""Application configuration and constants."""
import sys
import os
from pathlib import Path

# Base directories
if getattr(sys, "frozen", False):
    # Running in a PyInstaller bundle
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", sys.executable)).resolve()
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent.parent
    BASE_DIR = BUNDLE_DIR

ASSETS_DIR = BUNDLE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure data and logs directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database and log paths
DB_PATH = DATA_DIR / "blocker.db"
LOG_PATH = LOGS_DIR / "blocker.log"

# Windows Hosts File Path
DEFAULT_HOSTS_PATH = Path(os.environ.get("SystemRoot", r"C:\Windows")) / r"System32\drivers\etc\hosts"
DEFAULT_HOSTS_BACKUP_PATH = Path(os.environ.get("SystemRoot", r"C:\Windows")) / r"System32\drivers\etc\hosts.backup"

# Markers for safe hosts file modification
BLOCK_MARKER_START = "# === WEBSITE BLOCKER START ==="
BLOCK_MARKER_END = "# === WEBSITE BLOCKER END ==="

# Loopback redirection target
LOOPBACK_IPV4 = "127.0.0.1"
LOOPBACK_IPV6 = "::1"

# Duration constraints (in seconds)
MIN_DURATION_SECONDS = 60  # 1 minute
MAX_DURATION_SECONDS = 86400  # 24 hours

# Common preset durations in seconds
PRESET_DURATIONS = {
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "2h": 2 * 60 * 60,
    "4h": 4 * 60 * 60,
}

# App info
APP_NAME = "Website Blocker"
APP_VERSION = "1.0.0"
