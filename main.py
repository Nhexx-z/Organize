"""
Organize. v1.1 — Entry point
"""
import sys
import os

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"]   = "1"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.main_window import MainWindow
from app.theme_manager import ThemeManager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Organize.")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("Organize")

    theme = ThemeManager()
    theme.apply(app)

    window = MainWindow(theme)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
