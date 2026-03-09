"""
Organize. — Core engine v2.
Adds: Desktop auto-sort with folder consolidation, desktop wallpaper color.
"""

import os
import json
import shutil
import threading
import hashlib
import ctypes
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


DEFAULT_RULES = [
    {"id":"images","name":"Images","icon":"🖼️","color":"#3B82F6","folder":"Images",
     "extensions":[".jpg",".jpeg",".png",".gif",".bmp",".webp",".svg",".ico",".tiff",".tif",".heic",".heif",".raw",".cr2",".nef",".arw"],"enabled":True},
    {"id":"videos","name":"Vidéos","icon":"🎬","color":"#EC4899","folder":"Vidéos",
     "extensions":[".mp4",".avi",".mkv",".mov",".wmv",".flv",".webm",".m4v",".mpeg",".mpg",".3gp",".ts"],"enabled":True},
    {"id":"audio","name":"Musique","icon":"🎵","color":"#A855F7","folder":"Musique",
     "extensions":[".mp3",".wav",".flac",".aac",".ogg",".m4a",".wma",".opus",".aiff",".mid",".midi"],"enabled":True},
    {"id":"documents","name":"Documents","icon":"📄","color":"#0EA5E9","folder":"Documents",
     "extensions":[".pdf",".doc",".docx",".odt",".rtf",".txt",".xls",".xlsx",".ods",".csv",".ppt",".pptx",".odp",".pages",".numbers",".key"],"enabled":True},
    {"id":"archives","name":"Archives","icon":"📦","color":"#F59E0B","folder":"Archives",
     "extensions":[".zip",".rar",".7z",".tar",".gz",".bz2",".xz",".iso",".dmg",".cab",".lz",".lzma"],"enabled":True},
    {"id":"installers","name":"Logiciels","icon":"⚙️","color":"#6366F1","folder":"Logiciels",
     "extensions":[".exe",".msi",".apk",".deb",".rpm",".pkg",".appimage",".run",".bat",".ps1",".sh"],"enabled":True},
    {"id":"code","name":"Code","icon":"💻","color":"#10B981","folder":"Code",
     "extensions":[".py",".js",".ts",".jsx",".tsx",".html",".css",".json",".xml",".yaml",".yml",".toml",".ini",".c",".cpp",".h",".java",".rs",".go",".php",".rb",".swift",".kt",".sql",".md",".ipynb"],"enabled":True},
    {"id":"others","name":"Divers","icon":"❓","color":"#94A3B8","folder":"Divers","extensions":[],"enabled":True},
]


class FileAction:
    def __init__(self, src: Path, dst: Path, category: str, size: int):
        self.src = src; self.dst = dst; self.category = category
        self.size = size; self.timestamp = datetime.now().isoformat(); self.done = False

    def to_dict(self):
        return {"src":str(self.src),"dst":str(self.dst),"category":self.category,
                "size":self.size,"timestamp":self.timestamp,"done":self.done}

    @classmethod
    def from_dict(cls, d):
        a = cls(Path(d["src"]),Path(d["dst"]),d["category"],d["size"])
        a.timestamp = d["timestamp"]; a.done = d["done"]; return a


class OrganizeSession:
    def __init__(self, source_dir: str, actions: list):
        self.id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
        self.source_dir = source_dir; self.actions = actions
        self.timestamp = datetime.now().isoformat()
        self.total_files = len(actions)
        self.total_bytes = sum(a.size for a in actions)

    def to_dict(self):
        return {"id":self.id,"source_dir":self.source_dir,"timestamp":self.timestamp,
                "total_files":self.total_files,"total_bytes":self.total_bytes,
                "actions":[a.to_dict() for a in self.actions]}

    @classmethod
    def from_dict(cls, d):
        actions = [FileAction.from_dict(a) for a in d.get("actions",[])]
        s = cls(d["source_dir"], actions)
        s.id=d["id"]; s.timestamp=d["timestamp"]
        s.total_files=d["total_files"]; s.total_bytes=d["total_bytes"]; return s


class HistoryStore:
    def __init__(self):
        self.path = Path.home()/".organize"/"history.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._sessions = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self._sessions = [OrganizeSession.from_dict(s) for s in data]
            except Exception:
                self._sessions = []

    def _save(self):
        self.path.write_text(json.dumps([s.to_dict() for s in self._sessions], indent=2))

    def add_session(self, session):
        self._sessions.insert(0, session)
        if len(self._sessions) > 50:
            self._sessions = self._sessions[:50]
        self._save()

    def remove_session(self, sid):
        self._sessions = [s for s in self._sessions if s.id != sid]
        self._save()

    def get_sessions(self): return self._sessions

    def get_stats(self):
        return {
            "total_files": sum(s.total_files for s in self._sessions),
            "total_bytes": sum(s.total_bytes for s in self._sessions),
            "sessions": len(self._sessions)
        }


class SettingsStore:
    def __init__(self):
        self.path = Path.home()/".organize"/"settings.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._defaults()
        self._load()

    def _defaults(self):
        return {
            "watch_mode": False,
            "watch_folders": [str(Path.home()/"Downloads")],
            "rules": DEFAULT_RULES,
            "desktop_auto_sort": False,
            "desktop_consolidate_folders": True,
        }

    def _load(self):
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text())
                for k,v in saved.items():
                    self._data[k] = v
            except Exception:
                pass

    def save(self):
        self.path.write_text(json.dumps(self._data, indent=2))

    def get(self, key, default=None): return self._data.get(key, default)
    def set(self, key, value): self._data[key]=value; self.save()

    @property
    def rules(self): return self._data["rules"]
    @rules.setter
    def rules(self, value): self._data["rules"]=value; self.save()


class FileScanner:
    def __init__(self, rules: list):
        self.rules = rules
        self._ext_map = {}
        for rule in rules:
            if rule["id"] != "others":
                for ext in rule["extensions"]:
                    self._ext_map[ext.lower()] = rule

    def categorize(self, file: Path) -> dict:
        return self._ext_map.get(file.suffix.lower(), self._others())

    def _others(self):
        for r in self.rules:
            if r["id"] == "others": return r
        return self.rules[-1]

    def scan(self, folder: Path) -> list:
        actions = []
        if not folder.exists(): return actions
        category_folder_names = {r["folder"] for r in self.rules}
        for item in folder.iterdir():
            if item.is_file() and not item.name.startswith("."):
                rule = self.categorize(item)
                if not rule.get("enabled", True): continue
                if item.parent.name in category_folder_names: continue
                target = folder / rule["folder"] / item.name
                try: size = item.stat().st_size
                except: size = 0
                actions.append(FileAction(item, target, rule["name"], size))
        return actions

    def scan_desktop_consolidate(self, desktop: Path) -> list:
        """
        Scan desktop: moves all files into categories AND
        consolidates loose folders into a single 'Dossiers/' subfolder.
        Returns (file_actions, folder_names_to_consolidate).
        """
        actions = []
        if not desktop.exists(): return actions
        category_folder_names = {r["folder"] for r in self.rules} | {"Dossiers"}

        for item in desktop.iterdir():
            if item.name.startswith("."): continue
            if item.is_file():
                rule = self.categorize(item)
                if not rule.get("enabled", True): continue
                target = desktop / rule["folder"] / item.name
                try: size = item.stat().st_size
                except: size = 0
                actions.append(FileAction(item, target, rule["name"], size))
            elif item.is_dir() and item.name not in category_folder_names:
                # Move existing folders into Dossiers/
                target = desktop / "Dossiers" / item.name
                actions.append(FileAction(item, target, "Dossiers", 0))
        return actions


class OrganizerEngine(QObject):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    file_detected = pyqtSignal(str)

    def __init__(self, settings: SettingsStore, history: HistoryStore):
        super().__init__()
        self.settings = settings
        self.history = history
        self._watching = False
        self._watch_thread = None

    def preview(self, folder_path: str) -> list:
        scanner = FileScanner(self.settings.rules)
        return scanner.scan(Path(folder_path))

    def preview_desktop(self) -> list:
        scanner = FileScanner(self.settings.rules)
        return scanner.scan_desktop_consolidate(Path.home() / "Desktop")

    def organize(self, folder_path: str, actions: list) -> OrganizeSession:
        total = len(actions)
        done = []
        errors = []
        for i, action in enumerate(actions):
            self.progress.emit(i+1, total, action.src.name)
            try:
                action.dst.parent.mkdir(parents=True, exist_ok=True)
                dst = action.dst
                if dst.exists():
                    stem, suffix, counter = dst.stem, dst.suffix, 1
                    while dst.exists():
                        dst = dst.parent / f"{stem} ({counter}){suffix}"
                        counter += 1
                    action.dst = dst
                shutil.move(str(action.src), str(action.dst))
                action.done = True
                done.append(action)
            except Exception as e:
                errors.append(f"{action.src.name}: {e}")
        session = OrganizeSession(folder_path, done)
        self.history.add_session(session)
        if errors: self.error.emit("\n".join(errors))
        self.finished.emit(session)
        return session

    def undo_session(self, session) -> tuple:
        restored = 0; errors = []
        for action in reversed(session.actions):
            if action.done and Path(str(action.dst)).exists():
                try:
                    Path(str(action.src)).parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(action.dst), str(action.src))
                    restored += 1
                except Exception as e:
                    errors.append(f"{action.dst.name}: {e}")
        for action in session.actions:
            try:
                folder = Path(str(action.dst)).parent
                if folder.exists() and not any(folder.iterdir()):
                    folder.rmdir()
            except: pass
        self.history.remove_session(session.id)
        return restored, errors

    def set_desktop_wallpaper_color(self, hex_color: str) -> bool:
        """Set desktop background to a solid color (Windows only)."""
        try:
            import winreg, ctypes
            # Create a 1x1 BMP of the given color and set as wallpaper
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            # Use SystemParametersInfo to set the background color
            # First set the color via registry
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Colors",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "Background", 0, winreg.REG_SZ, f"{r} {g} {b}")
            winreg.CloseKey(key)
            # Clear wallpaper and apply color
            ctypes.windll.user32.SystemParametersInfoW(20, 0, "", 3)
            return True
        except Exception as e:
            print(f"Wallpaper error: {e}")
            return False

    def start_watch(self, folders: list):
        if self._watching: return
        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._watch_loop, args=(folders,), daemon=True
        )
        self._watch_thread.start()

    def stop_watch(self):
        self._watching = False

    def _watch_loop(self, folders: list):
        import time
        known = {}
        for f in folders:
            try:
                p = Path(f)
                known[f] = {i.name for i in p.iterdir() if i.is_file()} if p.exists() else set()
            except: known[f] = set()
        while self._watching:
            time.sleep(3)
            for folder in folders:
                try:
                    p = Path(folder)
                    if not p.exists(): continue
                    current = {i.name for i in p.iterdir() if i.is_file()}
                    new_files = current - known.get(folder, set())
                    if new_files:
                        known[folder] = current
                        time.sleep(1)
                        scanner = FileScanner(self.settings.rules)
                        for fname in new_files:
                            fpath = p / fname
                            if fpath.exists():
                                rule = scanner.categorize(fpath)
                                action = FileAction(
                                    fpath, p/rule["folder"]/fname, rule["name"],
                                    fpath.stat().st_size if fpath.exists() else 0
                                )
                                self.file_detected.emit(fname)
                                try:
                                    action.dst.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(action.src), str(action.dst))
                                    self.history.add_session(OrganizeSession(folder, [action]))
                                except: pass
                except: pass


def format_size(b: int) -> str:
    for u in ["o","Ko","Mo","Go","To"]:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} Po"


def format_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        diff = datetime.now() - dt
        if diff.days == 0: return f"Aujourd'hui à {dt.strftime('%H:%M')}"
        elif diff.days == 1: return f"Hier à {dt.strftime('%H:%M')}"
        elif diff.days < 7:
            days = ["lundi","mardi","mercredi","jeudi","vendredi","samedi","dimanche"]
            return f"{days[dt.weekday()].capitalize()} à {dt.strftime('%H:%M')}"
        else: return dt.strftime("%d/%m/%Y à %H:%M")
    except: return iso