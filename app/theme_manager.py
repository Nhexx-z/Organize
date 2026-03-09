"""
ThemeManager v2 — Dark/Light manual toggle + accent color picker + persistent prefs.
"""

import json
from pathlib import Path


def _is_windows_dark_mode() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return True


def _get_windows_accent() -> str:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
        value, _ = winreg.QueryValueEx(key, "AccentColor")
        winreg.CloseKey(key)
        abgr = value & 0xFFFFFFFF
        r = abgr & 0xFF
        g = (abgr >> 8) & 0xFF
        b = (abgr >> 16) & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#0078D4"


PREFS_PATH = Path.home() / ".organize" / "theme_prefs.json"


def _load_prefs() -> dict:
    try:
        if PREFS_PATH.exists():
            return json.loads(PREFS_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_prefs(data: dict):
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(data, indent=2))


def _build_stylesheet(dark: bool, accent: str, accent_hover: str, accent_pressed: str) -> str:
    if dark:
        bg="161616"; surface="242424"; surface2="2E2E2E"; border="383838"
        text="F0F0F0"; text2="909090"; text3="555555"
        sidebar_bg="1E1E1E"; sidebar_brd="2E2E2E"
        card_bg="242424"; card_brd="333333"; input_bg="2A2A2A"
        scrollbar="404040"; scrollbar_h="606060"
        toggle_off="484848"; toggle_off_text="888888"
        status_bg="1A1A1A"; list_bg="242424"
        danger="F87171"; danger_bg="rgba(248,113,113,0.10)"; danger_brd="rgba(248,113,113,0.35)"
        hover_generic="rgba(128,128,128,0.10)"
    else:
        bg="F0F0F0"; surface="FAFAFA"; surface2="F4F4F4"; border="E2E2E2"
        text="111111"; text2="666666"; text3="AAAAAA"
        sidebar_bg="E8E8E8"; sidebar_brd="D8D8D8"
        card_bg="FFFFFF"; card_brd="E4E4E4"; input_bg="FFFFFF"
        scrollbar="C8C8C8"; scrollbar_h="AAAAAA"
        toggle_off="C0C0C0"; toggle_off_text="888888"
        status_bg="E4E4E4"; list_bg="FFFFFF"
        danger="DC2626"; danger_bg="rgba(220,38,38,0.07)"; danger_brd="rgba(220,38,38,0.35)"
        hover_generic="rgba(0,0,0,0.06)"

    h = accent.lstrip("#")
    ar,ag,ab = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
    list_sel = f"rgba({ar},{ag},{ab},40)"

    return f"""
QWidget {{
    font-family: "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 13px; color: #{text}; background-color: transparent; border: none; outline: none;
}}
QMainWindow {{ background-color: #{bg}; }}
#sidebar {{
    background-color: #{sidebar_bg}; border-right: 1px solid #{sidebar_brd};
    min-width: 210px; max-width: 210px;
}}
#app_logo_box {{
    background-color: {accent}; border-radius: 12px;
    margin: 24px 18px 0px 18px; min-height: 54px; max-height: 54px;
}}
#app_logo_text {{
    font-size: 20px; font-weight: 700; color: #FFFFFF;
    letter-spacing: -0.5px; padding: 0px 16px;
}}
#app_tagline {{
    font-size: 10px; color: #{text3}; padding: 6px 22px 18px 22px;
    letter-spacing: 1.5px;
}}
#nav_btn {{
    background-color: transparent; color: #{text2}; border: none; border-radius: 8px;
    padding: 9px 14px; text-align: left; font-size: 13px; font-weight: 400;
    margin: 1px 10px; min-height: 40px;
}}
#nav_btn:hover {{ background-color: {hover_generic}; color: #{text}; }}
#nav_btn_active {{
    background-color: {accent}; color: #FFFFFF; border: none; border-radius: 8px;
    padding: 9px 14px; text-align: left; font-size: 13px; font-weight: 600;
    margin: 1px 10px; min-height: 40px;
}}
#nav_btn_active:hover {{ background-color: {accent_hover}; }}
#content_area {{ background-color: #{bg}; }}
#page_title {{ font-size: 26px; font-weight: 600; color: #{text}; letter-spacing: -0.5px; }}
#page_subtitle {{ font-size: 12px; color: #{text2}; }}
#card {{
    background-color: #{card_bg}; border: 1px solid #{card_brd}; border-radius: 12px;
}}
#card_title {{ font-size: 13px; font-weight: 600; color: #{text}; }}
#card_value {{ font-size: 34px; font-weight: 300; color: #{text}; letter-spacing: -1.5px; }}
#card_label {{ font-size: 10px; color: #{text3}; letter-spacing: 1px; }}
#btn_primary {{
    background-color: {accent}; color: #FFFFFF; border: none; border-radius: 8px;
    padding: 10px 22px; font-size: 13px; font-weight: 600; min-height: 38px;
}}
#btn_primary:hover {{ background-color: {accent_hover}; }}
#btn_primary:pressed {{ background-color: {accent_pressed}; }}
#btn_primary:disabled {{ background-color: #{border}; color: #{text3}; }}
#btn_secondary {{
    background-color: #{surface2}; color: #{text}; border: 1px solid #{border};
    border-radius: 8px; padding: 9px 18px; font-size: 13px; min-height: 36px;
}}
#btn_secondary:hover {{ background-color: #{surface}; border-color: #{text3}; }}
#btn_secondary:pressed {{ background-color: #{surface2}; }}
#btn_danger {{
    background-color: {danger_bg}; color: #{danger}; border: 1px solid {danger_brd};
    border-radius: 8px; padding: 7px 14px; font-size: 12px; min-height: 30px;
}}
#btn_danger:hover {{ background-color: rgba(220,38,38,0.15); }}
#toggle_on {{
    background-color: {accent}; border-radius: 11px;
    min-width: 42px; max-width: 42px; min-height: 22px; max-height: 22px;
    color: white; font-size: 10px; font-weight: 700; border: none;
}}
#toggle_off {{
    background-color: #{toggle_off}; border-radius: 11px;
    min-width: 42px; max-width: 42px; min-height: 22px; max-height: 22px;
    color: #{toggle_off_text}; font-size: 10px; font-weight: 600; border: none;
}}
QListWidget {{
    background-color: #{list_bg}; border: 1px solid #{card_brd};
    border-radius: 10px; padding: 4px; color: #{text};
}}
QListWidget::item {{ padding: 9px 12px; border-radius: 6px; margin: 1px 2px; }}
QListWidget::item:hover {{ background-color: {hover_generic}; }}
QListWidget::item:selected {{ background-color: {list_sel}; color: {accent}; }}
QScrollBar:vertical {{
    background: transparent; width: 6px; margin: 4px 2px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{ background: #{scrollbar}; border-radius: 3px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: #{scrollbar_h}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: transparent; height: 6px; margin: 2px 4px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{ background: #{scrollbar}; border-radius: 3px; min-width: 20px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QComboBox {{
    background-color: #{input_bg}; border: 1px solid #{border}; border-radius: 8px;
    padding: 7px 12px; color: #{text}; min-height: 34px;
}}
QComboBox:hover {{ border-color: #{text3}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: #{surface}; border: 1px solid #{border}; border-radius: 8px;
    padding: 4px; color: #{text}; selection-background-color: {list_sel};
}}
QLineEdit {{
    background-color: #{input_bg}; border: 1px solid #{border}; border-radius: 8px;
    padding: 7px 12px; color: #{text}; min-height: 34px;
}}
QLineEdit:focus {{ border-color: {accent}; }}
QProgressBar {{
    background-color: #{border}; border-radius: 3px; border: none;
    min-height: 5px; max-height: 5px;
}}
QProgressBar::chunk {{ background-color: {accent}; border-radius: 3px; }}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: #{border}; margin: 0px 8px; }}
QToolTip {{
    background-color: #{surface}; color: #{text}; border: 1px solid #{border};
    border-radius: 6px; padding: 5px 10px; font-size: 12px;
}}
QStatusBar {{
    background-color: #{status_bg}; color: #{text3}; border-top: 1px solid #{border};
    font-size: 11px; padding: 0px 8px; min-height: 24px; max-height: 24px;
}}
QMessageBox {{ background-color: #{surface}; }}
QMessageBox QLabel {{ color: #{text}; }}
QDialog {{ background-color: #{surface}; }}
QDialogButtonBox QPushButton {{
    background-color: #{surface2}; color: #{text}; border: 1px solid #{border};
    border-radius: 6px; padding: 6px 16px; min-width: 70px; min-height: 30px;
}}
QDialogButtonBox QPushButton:hover {{ background-color: #{card_bg}; }}
"""


class ThemeManager:
    def __init__(self):
        prefs = _load_prefs()
        self.is_dark = prefs.get("dark_mode", _is_windows_dark_mode())
        self.accent = prefs.get("accent", _get_windows_accent())
        self._compute_variants()
        self._app = None

    def _compute_variants(self):
        h = self.accent.lstrip("#")
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        if self.is_dark:
            hr=min(255,int(r*1.15)); hg=min(255,int(g*1.15)); hb=min(255,int(b*1.15))
            pr=max(0,int(r*0.82));   pg=max(0,int(g*0.82));   pb=max(0,int(b*0.82))
        else:
            hr=max(0,int(r*0.88)); hg=max(0,int(g*0.88)); hb=max(0,int(b*0.88))
            pr=max(0,int(r*0.75)); pg=max(0,int(g*0.75)); pb=max(0,int(b*0.75))
        self.accent_hover   = f"#{hr:02x}{hg:02x}{hb:02x}"
        self.accent_pressed = f"#{pr:02x}{pg:02x}{pb:02x}"

    def get_stylesheet(self) -> str:
        return _build_stylesheet(self.is_dark, self.accent, self.accent_hover, self.accent_pressed)

    def apply(self, app):
        self._app = app
        app.setStyleSheet(self.get_stylesheet())

    def _refresh(self):
        if self._app:
            self._app.setStyleSheet(self.get_stylesheet())

    def set_dark(self, dark: bool):
        self.is_dark = dark
        self._compute_variants()
        prefs = _load_prefs()
        prefs["dark_mode"] = dark
        _save_prefs(prefs)
        self._refresh()

    def set_accent(self, color: str):
        self.accent = color
        self._compute_variants()
        prefs = _load_prefs()
        prefs["accent"] = color
        _save_prefs(prefs)
        self._refresh()

    def get_colors(self) -> dict:
        if self.is_dark:
            return {
                "bg":"#161616","surface":"#242424","surface2":"#2E2E2E",
                "border":"#383838","text":"#F0F0F0","text_secondary":"#909090",
                "text_tertiary":"#555555","accent":self.accent,
                "success":"#4ADE80","warning":"#FBBF24","error":"#F87171",
            }
        else:
            return {
                "bg":"#F0F0F0","surface":"#FAFAFA","surface2":"#F4F4F4",
                "border":"#E2E2E2","text":"#111111","text_secondary":"#666666",
                "text_tertiary":"#AAAAAA","accent":self.accent,
                "success":"#16A34A","warning":"#D97706","error":"#DC2626",
            }