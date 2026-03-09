"""
Dashboard v2 — Clean, modern, with Desktop sort section.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QProgressBar, QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from app.engine import OrganizerEngine, SettingsStore, HistoryStore, FileAction, format_size


class OrganizeWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, engine, folder, actions):
        super().__init__()
        self.engine = engine; self.folder = folder; self.actions = actions

    def run(self):
        self.engine.progress.connect(self.progress)
        self.engine.finished.connect(self.finished)
        self.engine.error.connect(self.error)
        self.engine.organize(self.folder, self.actions)


class StatCard(QFrame):
    def __init__(self, value, label, color, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(4)
        self.val = QLabel(value)
        self.val.setObjectName("card_value")
        self.val.setStyleSheet(f"color:{color};font-size:32px;font-weight:300;letter-spacing:-1.5px;")
        lbl = QLabel(label)
        lbl.setObjectName("card_label")
        lay.addWidget(self.val)
        lay.addWidget(lbl)

    def update(self, v): self.val.setText(v)


class DashboardPage(QWidget):
    organize_done = pyqtSignal(object)

    def __init__(self, engine: OrganizerEngine, settings: SettingsStore,
                 history: HistoryStore, theme, parent=None):
        super().__init__(parent)
        self.engine = engine; self.settings = settings
        self.history = history; self.theme = theme
        self.colors = theme.get_colors()
        self._pending = []; self._worker = None
        self._build_ui()
        self._refresh_stats()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        root_widget = QWidget()
        root = QVBoxLayout(root_widget)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(0)
        scroll.setWidget(root_widget)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0,0,0,0)
        outer.addWidget(scroll)

        # ── Title ─────────────────────────────────────────────────────
        title = QLabel("Accueil")
        title.setObjectName("page_title")
        sub = QLabel("Organisez vos fichiers en quelques secondes")
        sub.setObjectName("page_subtitle")
        root.addWidget(title)
        root.addSpacing(4)
        root.addWidget(sub)
        root.addSpacing(28)

        # ── Stats ──────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        c = self.colors
        self.card_files    = StatCard("—", "FICHIERS ORGANISÉS", c["accent"])
        self.card_size     = StatCard("—", "ESPACE GÉRÉ",        c["success"])
        self.card_sessions = StatCard("—", "SESSIONS TOTALES",   c["text_secondary"])
        for card in [self.card_files, self.card_size, self.card_sessions]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            stats_row.addWidget(card)
        root.addLayout(stats_row)
        root.addSpacing(24)

        # ── Section: Organiser un dossier ──────────────────────────────
        section_label = QLabel("Organiser un dossier")
        section_label.setStyleSheet(
            f"font-size:11px;font-weight:600;color:{c['text_tertiary']};"
            f"letter-spacing:1.5px;text-transform:uppercase;"
        )
        root.addWidget(section_label)
        root.addSpacing(8)

        org_card = QFrame()
        org_card.setObjectName("card")
        org_lay = QVBoxLayout(org_card)
        org_lay.setContentsMargins(22, 22, 22, 22)
        org_lay.setSpacing(14)

        # Folder row
        folder_row = QHBoxLayout(); folder_row.setSpacing(10)
        self.folder_combo = QComboBox()
        self._populate_folders()
        self.folder_combo.currentIndexChanged.connect(self._on_folder_changed)
        self.btn_browse = QPushButton("Parcourir…")
        self.btn_browse.setObjectName("btn_secondary")
        self.btn_browse.setFixedWidth(100)
        self.btn_browse.clicked.connect(self._browse)
        folder_row.addWidget(self.folder_combo, 1)
        folder_row.addWidget(self.btn_browse)
        org_lay.addLayout(folder_row)

        # Status
        self.status_label = QLabel("Sélectionnez un dossier, puis cliquez sur Aperçu")
        self.status_label.setObjectName("page_subtitle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        org_lay.addWidget(self.status_label)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_lbl = QLabel("")
        self.progress_lbl.setObjectName("page_subtitle")
        self.progress_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_lbl.setVisible(False)
        org_lay.addWidget(self.progress_bar)
        org_lay.addWidget(self.progress_lbl)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self.btn_preview = QPushButton("👁  Aperçu")
        self.btn_preview.setObjectName("btn_secondary")
        self.btn_preview.clicked.connect(self._do_preview)
        self.btn_organize = QPushButton("⚡  Organiser")
        self.btn_organize.setObjectName("btn_primary")
        self.btn_organize.setEnabled(False)
        self.btn_organize.clicked.connect(self._do_organize)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_preview)
        btn_row.addWidget(self.btn_organize)
        org_lay.addLayout(btn_row)

        root.addWidget(org_card)
        root.addSpacing(24)

        # ── Section: Bureau ────────────────────────────────────────────
        desktop_label = QLabel("Bureau")
        desktop_label.setStyleSheet(
            f"font-size:11px;font-weight:600;color:{c['text_tertiary']};"
            f"letter-spacing:1.5px;"
        )
        root.addWidget(desktop_label)
        root.addSpacing(8)

        desk_card = QFrame()
        desk_card.setObjectName("card")
        desk_lay = QHBoxLayout(desk_card)
        desk_lay.setContentsMargins(22, 20, 22, 20)
        desk_lay.setSpacing(16)

        desk_icon = QLabel("🖥️")
        desk_icon.setStyleSheet("font-size:28px;")

        desk_text = QVBoxLayout(); desk_text.setSpacing(3)
        desk_title = QLabel("Trier le Bureau automatiquement")
        desk_title.setObjectName("card_title")
        self.desk_sub = QLabel("Déplace les fichiers en catégories et regroupe tous les dossiers dans 'Dossiers/'")
        self.desk_sub.setObjectName("page_subtitle")
        self.desk_sub.setWordWrap(True)
        desk_text.addWidget(desk_title)
        desk_text.addWidget(self.desk_sub)

        desk_btns = QVBoxLayout(); desk_btns.setSpacing(6)
        self.btn_desk_preview = QPushButton("Aperçu Bureau")
        self.btn_desk_preview.setObjectName("btn_secondary")
        self.btn_desk_preview.clicked.connect(self._desk_preview)
        self.btn_desk_organize = QPushButton("⚡  Trier Bureau")
        self.btn_desk_organize.setObjectName("btn_primary")
        self.btn_desk_organize.setEnabled(False)
        self.btn_desk_organize.clicked.connect(self._desk_organize)
        desk_btns.addWidget(self.btn_desk_preview)
        desk_btns.addWidget(self.btn_desk_organize)

        desk_lay.addWidget(desk_icon)
        desk_lay.addLayout(desk_text, 1)
        desk_lay.addLayout(desk_btns)

        root.addWidget(desk_card)
        root.addSpacing(24)

        # ── Watch status ───────────────────────────────────────────────
        watch_card = QFrame()
        watch_card.setObjectName("card")
        watch_lay = QHBoxLayout(watch_card)
        watch_lay.setContentsMargins(22, 16, 22, 16)
        watch_lay.setSpacing(14)
        watch_icon = QLabel("👁"); watch_icon.setStyleSheet("font-size:22px;")
        watch_info = QVBoxLayout(); watch_info.setSpacing(2)
        wt = QLabel("Mode surveillance"); wt.setObjectName("card_title")
        self.watch_sub = QLabel("Inactif")
        self.watch_sub.setObjectName("page_subtitle")
        watch_info.addWidget(wt); watch_info.addWidget(self.watch_sub)
        watch_lay.addWidget(watch_icon)
        watch_lay.addLayout(watch_info, 1)
        root.addWidget(watch_card)
        root.addStretch()

        self._desk_pending = []

    def _populate_folders(self):
        self.folder_combo.clear()
        home = Path.home()
        for label, path in [
            ("📥  Téléchargements", str(home/"Downloads")),
            ("🖥️  Bureau", str(home/"Desktop")),
            ("📁  Documents", str(home/"Documents")),
        ]:
            self.folder_combo.addItem(label, path)

    def _on_folder_changed(self, _):
        self.btn_organize.setEnabled(False)
        self._pending = []
        self.status_label.setText("Cliquez sur Aperçu pour analyser ce dossier")
        self.status_label.setStyleSheet("")

    def _browse(self):
        from PyQt6.QtWidgets import QFileDialog
        f = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if f:
            self.folder_combo.addItem(f"📂  {Path(f).name}", f)
            self.folder_combo.setCurrentIndex(self.folder_combo.count()-1)

    def _do_preview(self):
        folder = self.folder_combo.currentData()
        if not folder: return
        actions = self.engine.preview(folder)
        self._pending = actions
        if not actions:
            self.status_label.setText("✅  Ce dossier est déjà bien organisé !")
            self.status_label.setStyleSheet(f"color:{self.colors['success']};")
            self.btn_organize.setEnabled(False)
        else:
            cats = {}
            for a in actions: cats[a.category] = cats.get(a.category, 0)+1
            parts = ", ".join(f"{v} {k}" for k,v in cats.items())
            total_size = format_size(sum(a.size for a in actions))
            self.status_label.setText(f"{len(actions)} fichier(s) · {total_size}  —  {parts}")
            self.status_label.setStyleSheet(f"color:{self.colors['accent']};")
            self.btn_organize.setEnabled(True)

    def _do_organize(self):
        if not self._pending: return
        folder = self.folder_combo.currentData()
        self._set_busy(True)
        self._worker = OrganizeWorker(self.engine, folder, self._pending)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _desk_preview(self):
        actions = self.engine.preview_desktop()
        self._desk_pending = actions
        if not actions:
            self.desk_sub.setText("✅  Le bureau est déjà bien organisé !")
            self.btn_desk_organize.setEnabled(False)
        else:
            cats = {}
            for a in actions: cats[a.category] = cats.get(a.category, 0)+1
            parts = ", ".join(f"{v} {k}" for k,v in cats.items())
            self.desk_sub.setText(f"{len(actions)} élément(s) à déplacer : {parts}")
            self.btn_desk_organize.setEnabled(True)

    def _desk_organize(self):
        if not self._desk_pending: return
        self._set_busy(True)
        desktop = str(Path.home()/"Desktop")
        self._worker = OrganizeWorker(self.engine, desktop, self._desk_pending)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _set_busy(self, busy):
        self.btn_organize.setEnabled(not busy)
        self.btn_preview.setEnabled(not busy)
        self.btn_desk_preview.setEnabled(not busy)
        self.btn_desk_organize.setEnabled(not busy)
        self.folder_combo.setEnabled(not busy)
        self.btn_browse.setEnabled(not busy)
        self.progress_bar.setVisible(busy)
        self.progress_lbl.setVisible(busy)
        if busy: self.progress_bar.setValue(0)

    def _on_progress(self, cur, total, fname):
        pct = int((cur/total)*100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.progress_lbl.setText(f"Déplacement de {fname}…")

    def _on_finished(self, session):
        self._set_busy(False); self._pending = []; self._desk_pending = []
        self.btn_organize.setEnabled(False); self.btn_desk_organize.setEnabled(False)
        self.status_label.setText(f"✅  {session.total_files} fichier(s) organisé(s) !")
        self.status_label.setStyleSheet(f"color:{self.colors['success']};")
        self.desk_sub.setText("Déplace les fichiers en catégories et regroupe tous les dossiers dans 'Dossiers/'")
        self._refresh_stats()
        self.organize_done.emit(session)

    def _on_error(self, msg):
        self.status_label.setText(f"⚠️  Erreur : {msg[:60]}")
        self.status_label.setStyleSheet(f"color:{self.colors['error']};")

    def _refresh_stats(self):
        s = self.history.get_stats()
        self.card_files.update(str(s["total_files"]))
        self.card_size.update(format_size(s["total_bytes"]))
        self.card_sessions.update(str(s["sessions"]))

    def update_watch_status(self, active, folders=None):
        if active:
            self.watch_sub.setText(f"Surveillance active — {len(folders or [])} dossier(s)")
            self.watch_sub.setStyleSheet(f"color:{self.colors['success']};")
        else:
            self.watch_sub.setText("Inactif")
            self.watch_sub.setStyleSheet("")