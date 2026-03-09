"""
System tray — solid background, appears bottom-right (above taskbar).
"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont
from PyQt6.QtCore import Qt, QRect


def _create_tray_icon(accent: str) -> QIcon:
    size = 64
    px = QPixmap(size, size)
    px.fill(QColor(accent))  # solid — no transparency issues
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI", 26, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "O")
    painter.end()
    return QIcon(px)


class TrayManager:
    def __init__(self, accent, on_show, on_organize, on_quit):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_create_tray_icon(accent))
        self.tray.setToolTip("Organize.")

        menu = QMenu()
        act_show = menu.addAction("📂  Ouvrir Organize.")
        act_show.triggered.connect(on_show)
        act_organize = menu.addAction("⚡  Organiser maintenant")
        act_organize.triggered.connect(on_organize)
        menu.addSeparator()
        act_quit = menu.addAction("✕  Quitter")
        act_quit.triggered.connect(on_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: on_show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray.show()

    def notify(self, title, message):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def hide(self):
        self.tray.hide()