"""
History page — Shows past organization sessions with undo capability.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.engine import OrganizerEngine, HistoryStore, OrganizeSession, format_size, format_date


class SessionCard(QFrame):
    undo_requested = pyqtSignal(object)

    def __init__(self, session: OrganizeSession, colors: dict, parent=None):
        super().__init__(parent)
        self.session = session
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Icon
        icon = QLabel("📦")
        icon.setStyleSheet("font-size: 28px;")
        icon.setFixedWidth(40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Info
        info = QVBoxLayout()
        info.setSpacing(3)

        folder_name = Path(session.source_dir).name
        title = QLabel(f"{folder_name}")
        title.setObjectName("card_title")

        details = QLabel(
            f"{session.total_files} fichier(s) · {format_size(session.total_bytes)} · {format_date(session.timestamp)}"
        )
        details.setObjectName("page_subtitle")

        # Category breakdown
        cats = {}
        for action in session.actions:
            cats[action.category] = cats.get(action.category, 0) + 1
        if cats:
            parts = ", ".join(f"{v} {k}" for k, v in list(cats.items())[:4])
            cats_label = QLabel(parts)
            cats_label.setStyleSheet(f"color: {colors['text_tertiary']}; font-size: 11px;")
            info.addWidget(cats_label)

        info.addWidget(title)
        info.addWidget(details)

        # Undo button
        btn = QPushButton("↩  Annuler")
        btn.setObjectName("btn_danger")
        btn.setFixedWidth(100)
        btn.clicked.connect(lambda: self.undo_requested.emit(session))

        layout.addWidget(icon)
        layout.addLayout(info, 1)
        layout.addWidget(btn)


class HistoryPage(QWidget):
    def __init__(self, engine: OrganizerEngine, history: HistoryStore, theme, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.history = history
        self.colors = theme.get_colors()
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        text = QVBoxLayout()
        text.setSpacing(4)
        title = QLabel("Historique")
        title.setObjectName("page_title")
        subtitle = QLabel("Retrouvez et annulez vos organisations précédentes")
        subtitle.setObjectName("page_subtitle")
        text.addWidget(title)
        text.addWidget(subtitle)

        btn_clear = QPushButton("🗑  Effacer tout")
        btn_clear.setObjectName("btn_danger")
        btn_clear.clicked.connect(self._clear_all)

        header_row.addLayout(text, 1)
        header_row.addWidget(btn_clear, 0, Qt.AlignmentFlag.AlignBottom)

        layout.addLayout(header_row)
        layout.addSpacing(28)

        # ── Scroll area ──────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.addStretch()

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll, 1)

    def refresh(self):
        # Clear existing cards
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sessions = self.history.get_sessions()

        if not sessions:
            empty = QLabel("Aucune organisation effectuée pour l'instant.")
            empty.setObjectName("page_subtitle")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.insertWidget(0, empty)
        else:
            for session in sessions:
                card = SessionCard(session, self.colors)
                card.undo_requested.connect(self._undo_session)
                self.scroll_layout.insertWidget(
                    self.scroll_layout.count() - 1, card
                )

    def _undo_session(self, session: OrganizeSession):
        reply = QMessageBox.question(
            self, "Annuler l'organisation",
            f"Voulez-vous remettre {session.total_files} fichier(s) à leur emplacement d'origine ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            restored, errors = self.engine.undo_session(session)
            if errors:
                QMessageBox.warning(
                    self, "Erreurs",
                    f"{restored} fichier(s) restauré(s).\nErreurs :\n" + "\n".join(errors[:5])
                )
            else:
                QMessageBox.information(
                    self, "Succès",
                    f"{restored} fichier(s) remis en place avec succès."
                )
            self.refresh()

    def _clear_all(self):
        sessions = self.history.get_sessions()
        if not sessions:
            return
        reply = QMessageBox.question(
            self, "Effacer l'historique",
            "Supprimer tout l'historique ? Les fichiers ne seront pas déplacés.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for s in list(sessions):
                self.history.remove_session(s.id)
            self.refresh()