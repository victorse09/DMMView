#!/usr/bin/env python3
"""
DMMView — Digital Multimeter Viewer for Linux Mint 22.3
Main entry point.

Supports:
  - VICTOR 98A+ (DMMVIEW_G Protocol)
  - EEVBlog 121GW (stub - future)
  - Fluke 287 (stub - future)

Usage:
    python3 dmmview.py
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.version import VERSION, APP_NAME


def setup_logging():
    """Configure application logging."""
    log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def main():
    setup_logging()
    logger = logging.getLogger("DMMView")
    logger.info("Starting DMMView for Linux...")

    import platform
    if platform.system() == "Windows":
        logger.warning("Estás ejecutando la versión de Linux (dmmview.py) en Windows. Se recomienda usar dmmwin.py.")

    # Check for dialout/plugdev group permissions (Linux specific)
    try:
        import grp
        import getpass
        user = getpass.getuser()
        groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
        if 'dialout' not in groups and 'uucp' not in groups:
            logger.warning("Tu usuario no está en el grupo 'dialout'. Puede que no tengas permisos para usar el puerto serie.")
            logger.warning("Ejecuta: sudo usermod -a -G dialout $USER")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(APP_NAME)

    # Set default font
    font = QFont("Inter", 11)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply dark stylesheet
    from ui.styles import get_stylesheet
    app.setStyleSheet(get_stylesheet())

    # Create and show main window
    from ui.main_window import MainWindow
    window = MainWindow()
    window.setWindowTitle("DMMView — Digital Multimeter Viewer (Linux Edition)")
    window.show()

    logger.info("DMMView ready")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
