"""
Settings page v2 — Dark/Light toggle, accent color picker, watch mode, desktop sort.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QSizePolicy,
    QColorDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.engine import SettingsStore, OrganizerEngine


class ToggleButton(QPushButton):
    def __init__(self, initial=False, parent=None):
        super().__init__(parent)
        self._state = initial
        self._update()
        self.clicked.connect(self._toggle)

    def _update(self):
        self.setText("ON" if self._state else "OFF")
        self.setObjectName("toggle_on" if self._state else "toggle_off")
        self.setStyle(self.style())

    def _toggle(self): self._state = not self._state; self._update()
    def is_on(self): return self._state
    def set_state(self, s): self._state = s; self._update()


class SectionHeader(QLabel):
    def __init__(self, text, colors, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color:{colors['text_tertiary']};font-size:10px;font-weight:700;"
            f"letter-spacing:2px;padding:4px 0px 2px 0px;"
        )


class SettingRow(QFrame):
    def __init__(self, title, description, control, colors, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(16)
        text = QVBoxLayout(); text.setSpacing(2)
        t = QLabel(title); t.setObjectName("card_title")
        d = QLabel(description); d.setObjectName("page_subtitle")
        d.setWordWrap(True)
        text.addWidget(t); text.addWidget(d)
        lay.addLayout(text, 1)
        lay.addWidget(control, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class FolderListWidget(QWidget):
    changed = pyqtSignal(list)

    def __init__(self, folders, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self._folders = list(folders)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0,0,0,0)
        self._lay.setSpacing(6)
        self._rebuild()

    def _rebuild(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not self._folders:
            lbl = QLabel("Aucun dossier configuré")
            lbl.setStyleSheet(f"color:{self.colors['text_tertiary']};font-size:12px;")
            self._lay.addWidget(lbl)
        else:
            for f in self._folders:
                row = QFrame()
                row.setStyleSheet(
                    f"background-color:{self.colors['surface2']};border-radius:6px;"
                    f"border:1px solid {self.colors['border']};"
                )
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12,7,7,7); rl.setSpacing(8)
                icon = QLabel("📂"); icon.setStyleSheet("font-size:14px;border:none;background:transparent;")
                lbl = QLabel(f); lbl.setStyleSheet(f"font-size:12px;color:{self.colors['text_secondary']};border:none;background:transparent;")
                rm = QPushButton("✕"); rm.setObjectName("btn_danger")
                rm.setFixedSize(26,26)
                rm.clicked.connect(lambda _, folder=f: self._remove(folder))
                rl.addWidget(icon); rl.addWidget(lbl,1); rl.addWidget(rm)
                self._lay.addWidget(row)

        add = QPushButton("＋  Ajouter un dossier")
        add.setObjectName("btn_secondary")
        add.clicked.connect(self._add)
        self._lay.addWidget(add)

    def _add(self):
        f = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if f and f not in self._folders:
            self._folders.append(f); self._rebuild(); self.changed.emit(self._folders)

    def _remove(self, f):
        if f in self._folders: self._folders.remove(f); self._rebuild(); self.changed.emit(self._folders)

    def get_folders(self): return self._folders


class AccentColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, current_color, parent=None):
        super().__init__(parent)
        self._color = current_color
        self._update_style()
        self.setFixedSize(80, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._pick)

    def _update_style(self):
        self.setStyleSheet(
            f"background-color:{self._color};border-radius:8px;border:none;"
            f"color:white;font-size:11px;font-weight:600;"
        )
        self.setText(self._color.upper())

    def _pick(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Choisir une couleur d'accent")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self): return self._color


class WallpaperColorButton(QPushButton):
    applied = pyqtSignal(str)

    def __init__(self, colors, parent=None):
        super().__init__("🎨  Choisir la couleur", parent)
        self.setObjectName("btn_secondary")
        self._current = "#1C1C1C"
        self.colors = colors
        self.setFixedWidth(160)
        self.clicked.connect(self._pick)

    def _pick(self):
        color = QColorDialog.getColor(QColor(self._current), self, "Couleur de fond du Bureau")
        if color.isValid():
            self._current = color.name()
            self.applied.emit(self._current)


class SettingsPage(QWidget):
    watch_mode_changed = pyqtSignal(bool, list)

    def __init__(self, settings: SettingsStore, engine: OrganizerEngine, theme, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.engine = engine
        self.theme = theme
        self.colors = theme.get_colors()
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(36, 36, 36, 36)
        lay.setSpacing(0)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(scroll)

        c = self.colors

        # ── Title ───────────────────────────────────────────────────────
        title = QLabel("Paramètres")
        title.setObjectName("page_title")
        sub = QLabel("Personnalisez Organize. selon vos préférences")
        sub.setObjectName("page_subtitle")
        lay.addWidget(title); lay.addSpacing(4); lay.addWidget(sub)
        lay.addSpacing(28)

        # ── APPARENCE ───────────────────────────────────────────────────
        lay.addWidget(SectionHeader("APPARENCE", c))
        lay.addSpacing(8)

        # Dark / Light mode
        self.theme_toggle = ToggleButton(self.theme.is_dark)
        self.theme_toggle.clicked.connect(self._on_theme_toggle)
        dark_row = SettingRow(
            "Mode nuit",
            "Basculez entre le thème clair et le thème sombre",
            self.theme_toggle, c
        )
        lay.addWidget(dark_row)
        lay.addSpacing(8)

        # Accent color
        self.accent_btn = AccentColorButton(self.theme.accent)
        self.accent_btn.color_changed.connect(self._on_accent_changed)
        accent_row = SettingRow(
            "Couleur d'accent",
            "Personnalisez la couleur principale de l'interface",
            self.accent_btn, c
        )
        lay.addWidget(accent_row)
        lay.addSpacing(8)

        # Wallpaper color
        self.wallpaper_btn = WallpaperColorButton(c)
        self.wallpaper_btn.applied.connect(self._on_wallpaper_color)
        self.wallpaper_status = QLabel("")
        self.wallpaper_status.setObjectName("page_subtitle")

        wall_card = QFrame(); wall_card.setObjectName("card")
        wall_lay = QHBoxLayout(wall_card)
        wall_lay.setContentsMargins(20,14,20,14); wall_lay.setSpacing(16)
        wall_text = QVBoxLayout(); wall_text.setSpacing(2)
        wt = QLabel("Couleur du Bureau Windows"); wt.setObjectName("card_title")
        wd = QLabel("Définit le fond d'écran comme une couleur unie (Windows uniquement)")
        wd.setObjectName("page_subtitle"); wd.setWordWrap(True)
        wall_text.addWidget(wt); wall_text.addWidget(wd)
        wall_text.addWidget(self.wallpaper_status)
        wall_right = QVBoxLayout(); wall_right.setSpacing(6)
        wall_right.addWidget(self.wallpaper_btn)

        # Color swatches
        swatches = QHBoxLayout(); swatches.setSpacing(6)
        preset_colors = ["#1C1C1C","#0A1628","#1A0A2E","#0A2818","#2E1A0A","#FFFFFF"]
        for hex_c in preset_colors:
            sw = QPushButton()
            sw.setFixedSize(24,24)
            sw.setToolTip(hex_c)
            sw.setStyleSheet(
                f"background-color:{hex_c};border-radius:5px;border:2px solid rgba(128,128,128,0.3);"
            )
            sw.setCursor(Qt.CursorShape.PointingHandCursor)
            sw.clicked.connect(lambda _, col=hex_c: self._on_wallpaper_color(col))
            swatches.addWidget(sw)
        wall_right.addLayout(swatches)

        wall_lay.addLayout(wall_text, 1)
        wall_lay.addLayout(wall_right)
        lay.addWidget(wall_card)
        lay.addSpacing(20)

        # ── SURVEILLANCE ─────────────────────────────────────────────────
        lay.addWidget(SectionHeader("SURVEILLANCE AUTOMATIQUE", c))
        lay.addSpacing(8)

        self.watch_toggle = ToggleButton(self.settings.get("watch_mode", False))
        self.watch_toggle.clicked.connect(self._on_watch_toggle)
        watch_row = SettingRow(
            "Mode surveillance",
            "Organise automatiquement les nouveaux fichiers dès leur apparition",
            self.watch_toggle, c
        )
        lay.addWidget(watch_row)
        lay.addSpacing(8)

        # Folder list card
        folders_card = QFrame(); folders_card.setObjectName("card")
        fl = QVBoxLayout(folders_card)
        fl.setContentsMargins(20,18,20,18); fl.setSpacing(10)
        fl_title = QLabel("Dossiers surveillés"); fl_title.setObjectName("card_title")
        self.folder_list = FolderListWidget(
            self.settings.get("watch_folders", [str(Path.home()/"Downloads")]), c
        )
        self.folder_list.changed.connect(self._on_folders_changed)
        fl.addWidget(fl_title); fl.addWidget(self.folder_list)
        lay.addWidget(folders_card)
        lay.addSpacing(20)

        # ── À PROPOS ─────────────────────────────────────────────────────
        lay.addWidget(SectionHeader("À PROPOS", c))
        lay.addSpacing(8)

        about = QFrame(); about.setObjectName("card")
        about_lay = QHBoxLayout(about)
        about_lay.setContentsMargins(20,16,20,16)
        at = QVBoxLayout(); at.setSpacing(3)
        a1 = QLabel("Organize.")
        a1.setStyleSheet(f"font-size:18px;font-weight:700;letter-spacing:-0.5px;color:{c['accent']};")
        a2 = QLabel("Version 1.1.0  ·  Organiseur de fichiers automatique")
        a2.setObjectName("page_subtitle")
        at.addWidget(a1); at.addWidget(a2)
        about_lay.addLayout(at, 1)
        lay.addWidget(about)
        lay.addStretch()

    def _on_theme_toggle(self):
        self.theme.set_dark(self.theme_toggle.is_on())

    def _on_accent_changed(self, color):
        self.theme.set_accent(color)

    def _on_wallpaper_color(self, color):
        ok = self.engine.set_desktop_wallpaper_color(color)
        if ok:
            self.wallpaper_status.setText(f"✅  Couleur appliquée : {color}")
            self.wallpaper_status.setStyleSheet(f"color:{self.colors['success']};font-size:11px;")
        else:
            self.wallpaper_status.setText("⚠️  Nécessite Windows pour fonctionner")
            self.wallpaper_status.setStyleSheet(f"color:{self.colors['warning']};font-size:11px;")

    def _on_watch_toggle(self):
        state = self.watch_toggle.is_on()
        self.settings.set("watch_mode", state)
        folders = self.folder_list.get_folders()
        self.watch_mode_changed.emit(state, folders)

    def _on_folders_changed(self, folders):
        self.settings.set("watch_folders", folders)
        if self.watch_toggle.is_on():
            self.watch_mode_changed.emit(True, folders)