#!/usr/bin/env python3
"""
DMMView — Digital Multimeter Viewer
Windows 10/11 specific entry point.

Handles High-DPI scaling and Windows specific fonts (Segoe UI).
"""

import sys
import os
import logging
import platform
import ctypes

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set AppUserModelID for Windows taskbar icon support
if platform.system() == "Windows":
    myappid = 'DMMView.Vito.3.3'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.version import VERSION, APP_NAME

def setup_logging():
    """Configure application logging for Windows."""
    # Ensure logs directory exists in AppData or fallback to local dir
    appdata = os.environ.get('APPDATA')
    if appdata:
        log_dir = os.path.join(appdata, "DMMView", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "dmmview.log")
    else:
        log_file = "dmmview_windows.log"

    log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return log_file


def main():
    # Enable High DPI scaling for Windows
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    log_path = setup_logging()
    logger = logging.getLogger("DMMWin")
    logger.info(f"Starting DMMView for Windows (Log: {log_path})...")

    # Check Windows version
    win_ver = platform.release()
    logger.info(f"Running on Windows {win_ver}")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(APP_NAME)

    # Set default font optimized for Windows (ClearType)
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply dark stylesheet
    from ui.styles import get_stylesheet
    app.setStyleSheet(get_stylesheet())

    # Create and show main window
    from ui.main_window import MainWindow
    window = MainWindow()
    window.setWindowTitle("DMMView — Digital Multimeter Viewer (Windows Edition)")
    window.show()

    logger.info("DMMView ready")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
