"""
MainWindow v2 — cleaner sidebar, better nav, no transparency issues.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QApplication, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QFont

from app.engine import OrganizerEngine, SettingsStore, HistoryStore
from app.page_dashboard import DashboardPage
from app.page_history import HistoryPage
from app.page_rules import RulesPage
from app.page_settings import SettingsPage
from app.tray import TrayManager


def _make_icon(accent):
    size = 128
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(8, 8, size-16, size-16, 22, 22)
    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Segoe UI", 50, QFont.Weight.Bold))
    p.drawText(QRect(0,0,size,size), Qt.AlignmentFlag.AlignCenter, "O.")
    p.end()
    return QIcon(px)


class NavButton(QPushButton):
    def __init__(self, emoji, label, parent=None):
        super().__init__(parent)
        self._emoji = emoji
        self._label = label
        self.setText(f"  {emoji}   {label}")
        self.setObjectName("nav_btn")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active):
        self.setObjectName("nav_btn_active" if active else "nav_btn")
        self.setStyle(self.style())


class MainWindow(QMainWindow):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.colors = theme.get_colors()

        self.settings = SettingsStore()
        self.history  = HistoryStore()
        self.engine   = OrganizerEngine(self.settings, self.history)

        self.setWindowTitle("Organize.")
        self.setWindowIcon(_make_icon(self.colors["accent"]))
        self.setMinimumSize(920, 620)
        self.resize(1080, 680)

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width()-1080)//2, (screen.height()-680)//2)

        self._build_ui()
        self._setup_tray()
        self._setup_watch()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 16)
        sb.setSpacing(0)

        # Logo box
        logo_box = QFrame()
        logo_box.setObjectName("app_logo_box")
        logo_box.setFixedHeight(54)
        logo_inner = QHBoxLayout(logo_box)
        logo_inner.setContentsMargins(16, 0, 16, 0)
        logo_txt = QLabel("Organize.")
        logo_txt.setObjectName("app_logo_text")
        logo_inner.addWidget(logo_txt)
        sb.addWidget(logo_box)

        tagline = QLabel("FILE ORGANIZER")
        tagline.setObjectName("app_tagline")
        sb.addWidget(tagline)

        # Nav
        self._nav_btns = []
        nav_items = [
            ("🏠", "Accueil"),
            ("📋", "Historique"),
            ("⚙️", "Règles"),
            ("🔧", "Paramètres"),
        ]
        for emoji, label in nav_items:
            btn = NavButton(emoji, label)
            btn.clicked.connect(lambda _, l=label: self._navigate(l))
            self._nav_btns.append((label, btn))
            sb.addWidget(btn)

        sb.addStretch()

        # Version badge at bottom
        ver = QLabel("v1.1.0")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet(f"color:{self.colors['text_tertiary']};font-size:10px;padding:0px;")
        sb.addWidget(ver)

        # ── Pages ──────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_area")

        self._page_dashboard = DashboardPage(self.engine, self.settings, self.history, self.theme)
        self._page_history   = HistoryPage(self.engine, self.history, self.theme)
        self._page_rules     = RulesPage(self.settings, self.theme)
        self._page_settings  = SettingsPage(self.settings, self.engine, self.theme)

        self._pages = {
            "Accueil":    self._page_dashboard,
            "Historique": self._page_history,
            "Règles":     self._page_rules,
            "Paramètres": self._page_settings,
        }
        for page in self._pages.values():
            self._stack.addWidget(page)

        self._page_dashboard.organize_done.connect(self._on_organize_done)
        self._page_settings.watch_mode_changed.connect(self._on_watch_changed)

        root.addWidget(sidebar)
        root.addWidget(self._stack, 1)

        self.statusBar().showMessage("Prêt  ·  Organize. v1.1.0")
        self._navigate("Accueil")

    def _navigate(self, label):
        for lbl, btn in self._nav_btns:
            btn.set_active(lbl == label)
        page = self._pages.get(label)
        if page: self._stack.setCurrentWidget(page)
        if label == "Historique": self._page_history.refresh()

    def _setup_tray(self):
        self._tray = TrayManager(
            self.colors["accent"],
            on_show=self._show_window,
            on_organize=self._quick_organize,
            on_quit=self._quit_app
        )

    def _setup_watch(self):
        if self.settings.get("watch_mode", False):
            folders = self.settings.get("watch_folders", [])
            self.engine.start_watch(folders)
            self.engine.file_detected.connect(self._on_file_detected)
            self._page_dashboard.update_watch_status(True, folders)

    def _on_organize_done(self, session):
        self._page_history.refresh()
        self._tray.notify("Organisation terminée",
                          f"{session.total_files} fichier(s) organisé(s) !")
        self.statusBar().showMessage(
            f"✅  {session.total_files} fichier(s) organisé(s) · Session {session.id}"
        )

    def _on_watch_changed(self, active, folders):
        if active:
            self.engine.start_watch(folders)
            self.engine.file_detected.connect(self._on_file_detected)
            self._tray.notify("Surveillance activée", f"{len(folders)} dossier(s) surveillé(s)")
        else:
            self.engine.stop_watch()
        self._page_dashboard.update_watch_status(active, folders)

    def _on_file_detected(self, fname):
        self._tray.notify("Fichier organisé", f"{fname} déplacé automatiquement")
        self._page_history.refresh()
        self._page_dashboard._refresh_stats()

    def _show_window(self):
        self.show(); self.raise_(); self.activateWindow()

    def _quick_organize(self):
        self._show_window(); self._navigate("Accueil")
        self._page_dashboard._do_preview()

    def _quit_app(self):
        self.engine.stop_watch(); QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self._tray.notify("Organize. tourne en arrière-plan",
                          "Double-clic sur l'icône pour rouvrir")