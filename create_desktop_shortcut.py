"""Creates a Windows Desktop shortcut for Website Blocker with icon and admin privileges."""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ICON_PATH = PROJECT_ROOT / "assets" / "icon.ico"
DIST_EXE = PROJECT_ROOT / "dist" / "WebsiteBlocker.exe"
RUN_PY = PROJECT_ROOT / "run.py"


def get_desktop_dir() -> Path:
    """Returns the user's Desktop directory path."""
    # Try standard Windows user profile desktop
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        d = Path(user_profile) / "Desktop"
        if d.exists():
            return d
        # Try OneDrive Desktop if applicable
        onedrive = os.environ.get("OneDrive")
        if onedrive:
            d_one = Path(onedrive) / "Desktop"
            if d_one.exists():
                return d_one
            d_one_jp = Path(onedrive) / "デスクトップ"
            if d_one_jp.exists():
                return d_one_jp
    return Path.home() / "Desktop"


def create_shortcut():
    desktop = get_desktop_dir()
    shortcut_path = desktop / "Website Blocker.lnk"

    target = DIST_EXE if DIST_EXE.exists() else Path(sys.executable).parent / "pythonw.exe"
    arguments = "" if DIST_EXE.exists() else f'"{RUN_PY}"'
    working_dir = PROJECT_ROOT
    icon = ICON_PATH if ICON_PATH.exists() else target

    # Use PowerShell to create the .lnk shortcut
    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{str(shortcut_path)}')
    $Shortcut.TargetPath = '{str(target)}'
    $Shortcut.Arguments = '{arguments}'
    $Shortcut.WorkingDirectory = '{str(working_dir)}'
    $Shortcut.IconLocation = '{str(icon)}, 0'
    $Shortcut.Description = 'Website Blocker - Focus & Productivity Desktop App'
    $Shortcut.Save()
    """

    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True, capture_output=True)
        print(f"Desktop shortcut created successfully at: {shortcut_path.name}")
        return True
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False


if __name__ == "__main__":
    create_shortcut()
