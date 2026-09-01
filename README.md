# 🛡️ Website Blocker (Windows Desktop & Android Mobile)

A multi-platform productivity suite to eliminate digital distractions:
1. **Windows Desktop App**: Built with Python 3.13, PySide6 (Qt6), and SQLite with system-level `hosts` file modification.
2. **Android Mobile App**: Built with Kotlin, Jetpack Compose, Room SQLite, and on-device local `VpnService` DNS filtering (no root required).

---

## ✨ Cross-Platform Features

- 🌐 **System-Level Multi-Browser Blocking**: Blocks domains across all browsers (Chrome, Edge, Firefox, Brave, Safari, Samsung Internet) without requiring browser extensions.
- 🎨 **Next-Level Dark UI**: Custom-designed dark theme with glowing circular timer ring, clean navigation, and responsive status indicators.
- 🏷️ **Smart Website Name Detection**: Automatically transforms any pasted link or URL into its clean brand name (e.g. `https://www.youtube.com/watch?v=123` $\rightarrow$ **YouTube**, `reddit.com` $\rightarrow$ **Reddit**, `x.com` $\rightarrow$ **X (Twitter)**, `news.ycombinator.com` $\rightarrow$ **Hacker News**).
- 🖼️ **Automatic Favicon Fetching & Caching**: Automatically downloads official 64×64 website icons in the background via CDN with fallback support.
- ⏱️ **Wall-Clock Precision Timer**: Countdown anchored to system timestamps to prevent drift even if minimized or screen is locked.
- 📊 **Productivity Statistics**: Tracks daily and weekly focus time, session counts, and full chronological session history.
- 📱 **Android Mobile App (`android/`)**: Native Jetpack Compose app with on-device DNS query interception, zero remote servers.
- 📦 **Standalone Windows Desktop Application (`.exe`)**: Packaged with PyInstaller into a standalone executable with desktop shortcut and custom app icon.

---

## 📋 System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Python**: Python 3.10+ (tested on Python 3.13)
- **Privileges**: Administrator privileges (prompted via Windows UAC when writing to `hosts`)

---

## 🚀 Quick Start

### Option 1: Run the Standalone Desktop Executable (`.exe`)

1. Open the project folder.
2. Launch [`dist/WebsiteBlocker.exe`](file:///c:/Users/ankit/OneDrive/ドキュメント/Projects/website-blocker/dist/WebsiteBlocker.exe) or double-click the **Website Blocker** desktop shortcut.
3. Accept the Windows UAC elevation prompt if requested.

### Option 2: Run from Python Source

1. Clone or navigate to the repository:
```powershell
cd website-blocker
```

2. Create and activate a virtual environment (optional but recommended):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install required dependencies:
```powershell
pip install -r requirements.txt
```

4. Launch the application:
```powershell
python run.py
```

---

## 🛠️ Building the Standalone Executable

To compile the application into a standalone `.exe` using PyInstaller:

1. Generate the application icons (if not already present):
```powershell
python generate_icon.py
```

2. Build the binary using the spec configuration:
```powershell
pyinstaller --clean -y WebsiteBlocker.spec
```

3. Create the Windows Desktop shortcut:
```powershell
python create_desktop_shortcut.py
```

The output executable is created at `dist/WebsiteBlocker.exe`.

---

## 🧪 Running Automated Tests

The test suite includes 65 unit and integration tests covering domain validators, brand name deduction, database CRUD, hosts file parsing, session lifecycle, and timer precision:

```powershell
python -m pytest tests/ -v
```

---

## 📁 Project Architecture

```
website-blocker/
│
├── app.py                      # Qt Application initialization and lifecycle
├── run.py                      # Application entrypoint with UAC elevation handler
├── Launch.bat                  # One-click Windows batch launcher
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── WebsiteBlocker.spec         # PyInstaller build specification
├── generate_icon.py            # Icon generator script (ICO/PNG)
├── create_desktop_shortcut.py  # Desktop shortcut creator script
│
├── assets/                     # Application visual assets
│   ├── icon.ico                # Multi-resolution Windows icon (16x16 to 256x256)
│   └── icon.png                # High-resolution application logo
│
├── core/                       # Core blocking & session engine
│   ├── blocker.py              # Session lifecycle orchestration and recovery
│   ├── domain_manager.py       # Domain CRUD, validation, and deduplication
│   ├── hosts_manager.py        # Atomic hosts file reader/writer & DNS flusher
│   └── timer.py                # Wall-clock anchored QObject countdown timer
│
├── database/                   # SQLite persistence layer
│   ├── database.py             # SQLite WAL-mode connection and query manager
│   └── models.py               # Dataclass models (Website, Session, Schedule)
│
├── services/                   # Background services
│   └── favicon_service.py      # Async QNetworkAccessManager favicon fetcher & cache
│
├── ui/                         # PySide6 graphical user interface
│   ├── custom_widgets.py       # CircularTimerWidget, FaviconWidget, Avatar
│   ├── dashboard.py            # Focus dashboard with ring timer & presets
│   ├── main_window.py          # Shell window, global stylesheet, navigation
│   ├── settings.py             # Hosts backup restoration and maintenance
│   ├── statistics.py           # Productivity metric cards and session history
│   └── websites.py             # Configured website list with favicons & badges
│
├── utils/                      # Common utilities and configuration
│   ├── config.py               # Path constants, durations, frozen exe paths
│   ├── logger.py               # Rotating file and console logging
│   ├── permissions.py          # Windows UAC admin checks and ShellExecuteW
│   └── validators.py           # RFC domain validation and friendly brand name detection
│
├── tests/                      # Pytest automated test suite
│   ├── test_blocker.py         # BlockerService unit tests
│   ├── test_domain_manager.py  # DomainManager database tests
│   ├── test_hosts_manager.py   # HostsManager backup and write tests
│   ├── test_timer.py           # BlockTimer wall-clock expiry tests
│   └── test_validators.py      # Normalization, validation & name detection tests
│
├── data/                       # Local application data (created on runtime)
│   ├── blocker.db              # SQLite user database
│   └── favicons/               # Cached website favicon icons (.png)
│
└── logs/                       # Rotating application runtime logs
    └── blocker.log             # Application log file
```

---

## 🔒 Security & Safety Guarantees

- **Non-Destructive Hosts Isolation**: Only entries between the custom start and end markers are modified. Pre-existing system entries and custom mapping rules are preserved unaltered.
- **Atomic File Writes**: The hosts file is updated atomically using a temporary file replaced via `os.replace` to prevent partial writes during unexpected shutdowns.
- **Subprocess Security**: All external commands (e.g. `ipconfig /flushdns`) are executed safely without shell expansion (`shell=False`).
- **No External Daemon Required**: Operates purely within the user application process without installing background Windows services or device drivers.

---

## 📄 License

This project is licensed under the MIT License.
