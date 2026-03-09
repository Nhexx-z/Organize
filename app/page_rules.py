"""
Rules page — Edit file categories and their extensions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QLineEdit, QDialog,
    QDialogButtonBox, QFormLayout, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from app.engine import SettingsStore


class RuleCard(QFrame):
    def __init__(self, rule: dict, colors: dict, on_toggle, on_edit, parent=None):
        super().__init__(parent)
        self.rule = rule
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        # Colored icon badge
        badge = QLabel(rule["icon"])
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"font-size: 20px; background-color: {rule['color']}22; "
            f"border-radius: 10px; border: 1px solid {rule['color']}44;"
        )

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_label = QLabel(rule["name"])
        name_label.setObjectName("card_title")
        folder_label = QLabel(f"→ {rule['folder']}/")
        folder_label.setStyleSheet(f"color: {rule['color']}; font-size: 12px; font-weight: 500;")
        name_row.addWidget(name_label)
        name_row.addWidget(folder_label)
        name_row.addStretch()

        exts = rule.get("extensions", [])
        if exts:
            ext_text = "  ".join(exts[:8])
            if len(exts) > 8:
                ext_text += f"  +{len(exts)-8}"
        else:
            ext_text = "Tous les autres fichiers"
        ext_label = QLabel(ext_text)
        ext_label.setStyleSheet(f"color: {colors['text_tertiary']}; font-size: 11px; font-family: monospace;")
        ext_label.setWordWrap(True)

        info.addLayout(name_row)
        info.addWidget(ext_label)

        # Toggle button
        self.toggle_btn = QPushButton("ON" if rule.get("enabled", True) else "OFF")
        self.toggle_btn.setObjectName("toggle_on" if rule.get("enabled", True) else "toggle_off")
        self.toggle_btn.clicked.connect(lambda: on_toggle(rule))

        # Edit button
        edit_btn = QPushButton("✏️")
        edit_btn.setObjectName("btn_secondary")
        edit_btn.setFixedSize(36, 36)
        edit_btn.setToolTip("Modifier la règle")
        edit_btn.clicked.connect(lambda: on_edit(rule))

        layout.addWidget(badge)
        layout.addLayout(info, 1)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(edit_btn)


class EditRuleDialog(QDialog):
    def __init__(self, rule: dict, parent=None):
        super().__init__(parent)
        self.rule = rule.copy()
        self.setWindowTitle(f"Modifier — {rule['name']}")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_edit = QLineEdit(rule["name"])
        self.folder_edit = QLineEdit(rule["folder"])

        exts = ", ".join(rule.get("extensions", []))
        self.exts_edit = QLineEdit(exts)
        self.exts_edit.setPlaceholderText(".jpg, .png, .gif, …")

        form.addRow("Nom :", self.name_edit)
        form.addRow("Dossier destination :", self.folder_edit)
        if rule.get("extensions"):  # Don't show for catch-all
            form.addRow("Extensions (séparées par virgule) :", self.exts_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def get_result(self) -> dict:
        self.rule["name"] = self.name_edit.text().strip()
        self.rule["folder"] = self.folder_edit.text().strip()
        if self.rule.get("extensions"):
            raw = self.exts_edit.text()
            self.rule["extensions"] = [
                e.strip() if e.strip().startswith(".") else f".{e.strip()}"
                for e in raw.split(",") if e.strip()
            ]
        return self.rule


class RulesPage(QWidget):
    def __init__(self, settings: SettingsStore, theme, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.colors = theme.get_colors()
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────
        title = QLabel("Règles d'organisation")
        title.setObjectName("page_title")
        subtitle = QLabel("Configurez les catégories et les extensions de fichiers")
        subtitle.setObjectName("page_subtitle")

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        # ── Scroll ──────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 8, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll, 1)

    def _refresh(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for rule in self.settings.rules:
            card = RuleCard(rule, self.colors, self._toggle_rule, self._edit_rule)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _toggle_rule(self, rule: dict):
        rules = self.settings.rules
        for r in rules:
            if r["id"] == rule["id"]:
                r["enabled"] = not r.get("enabled", True)
        self.settings.rules = rules
        self._refresh()

    def _edit_rule(self, rule: dict):
        dialog = EditRuleDialog(rule, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_result()
            rules = self.settings.rules
            for i, r in enumerate(rules):
                if r["id"] == rule["id"]:
                    rules[i] = updated
            self.settings.rules = rules
            self._refresh()