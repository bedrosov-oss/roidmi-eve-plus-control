import json
import copy
import os
import sys
import threading
import traceback
import webbrowser
import ipaddress
import base64
import hashlib
import hmac
import gzip
import random
import time
import tarfile
import socket
import subprocess
import itertools
import ctypes
import tkinter.font as tkfont
import shutil
import zipfile
import sqlite3
import platform
import smtplib
from email.message import EmailMessage
import tempfile
import xml.sax.saxutils as xmlutils
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import parse as urlparse
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
import requests
from Crypto.Cipher import ARC4
from tkinter import ttk, messagebox, filedialog, simpledialog
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

try:
    import pystray
except Exception:
    pystray = None

try:
    from vacuum_map_parser_base.config.color import ColorsPalette
    from vacuum_map_parser_base.config.drawable import Drawable
    from vacuum_map_parser_base.config.image_config import ImageConfig
    from vacuum_map_parser_base.config.size import Sizes
    from vacuum_map_parser_base.config.text import Text
    from vacuum_map_parser_roidmi.map_data_parser import RoidmiMapDataParser
except Exception:
    ColorsPalette = None
    Drawable = None
    ImageConfig = None
    Sizes = None
    Text = None
    RoidmiMapDataParser = None

APP_TITLE = "ROIDMI EVE Plus Control v21.5 - GitHub Auto Update"
MODEL = "roidmi.vacuum.v60"
CURRENT_VERSION = "21.5"
GITHUB_REPOSITORY = "bedrosov-oss/roidmi-eve-plus-control"
GITHUB_REPOSITORY_URL = f"https://github.com/{GITHUB_REPOSITORY}"
GITHUB_MANIFEST_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/main/releases/latest.json"
)
GITHUB_LATEST_ZIP_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/main/dist/"
    "ROIDMI_EVE_Plus_Control_Windows_latest.zip"
)

FLOOR_TYPES = [
    "Плитка",
    "Ламинат",
    "Паркет",
    "Линолеум",
    "Плитка/ламинат",
    "Ламинат + ковёр",
    "Ковёр",
    "Другое",
]
DIRT_LEVELS = ["Низкий", "Средний", "Высокий"]

# ROIDMI EVE Plus / SDJ01RM technical references.
# Roidmi's regional product page states a 250 ml tank.
# Several manuals for SDJ01RM list about 220 ml. The app therefore shows
# both the nominal figure and a conservative usable estimate.
TECH_SPECS = {
    "product_model": "SDJ01RM",
    "battery_mah": 5200,
    "rated_power_w": 50,
    "max_suction_pa": 2700,
    "dust_box_ml": 300,
    "water_tank_nominal_ml": 250,
    "water_tank_conservative_ml": 220,
    "cleaning_time_min": 250,
    "max_obstacle_cm": 2.0,
    "station_bag_l": 3.0,
    "station_power_w": 850,
}

# Estimated flow model derived from published coverage / field measurements.
# level 1: Roidmi marketing ~250 ml / 250 m² => ~1.0 ml/m².
# level 4: independent test used ~40% of a 250 ml tank over 24 m² => ~4.2 ml/m².
# Intermediate levels are interpolated estimates and are labelled as such in UI.
WATER_FLOW_ML_PER_M2 = {
    0: 0.0,
    1: 1.0,
    2: 2.1,
    3: 3.2,
    4: 4.2,
}

FIRMWARE_4PDA_CATALOG = [
    {
        "version": "0.8.1_2281",
        "status": "старая / пользователи называли стабильной",
        "year": "2021-2022",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628&st=2760",
        "note": "На 4PDA встречается как предпочитаемая более старая версия. Не считать рекомендацией для отката без совместимого файла."
    },
    {
        "version": "0.9.0_2342",
        "status": "описаны изменения прошивки",
        "year": "2021",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628&st=860",
        "note": "В теме опубликованы изменения логики индикации станции, времени смачивания мопа и стартовой громкости."
    },
    {
        "version": "0.9.6_2365",
        "status": "широко встречается в теме",
        "year": "2021-2024",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628&st=2760",
        "note": "Долгое время пользователи видели её как актуальную в Roidmi/Xiaomi Home."
    },
    {
        "version": "1.1.0_2404",
        "status": "зафиксирована у пользователя на 4PDA",
        "year": "2024",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628&st=4960",
        "note": "Упоминается как текущая версия у пользователя, который искал 1.1.2_2415."
    },
    {
        "version": "1.1.2_2415",
        "status": "пользователь искал файл",
        "year": "2024",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628&st=4960",
        "note": "На 4PDA спрашивали файл этой версии; упоминался Mindsolo. Наличие сообщения не подтверждает универсальную совместимость."
    },
    {
        "version": "1.1.1.2405",
        "status": "OTA получена пользователем",
        "year": "2026",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628&st=5800",
        "note": "В мае 2026 пользователь сообщил о прилетевшем OTA. Версии могут различаться по региону/ветке."
    },
]

VOICE_SOURCES = [
    {
        "name": "Mindsolo Voicepacks",
        "kind": "Онлайн-каталог / установщик",
        "compatibility": "Много моделей; совместимость v60 проверять на сайте",
        "url": "https://vacuum.mindsolo.net/",
        "direct_url": None,
        "note": "Каталог озвучек и установка через браузер; поддерживает загрузку собственных пакетов."
    },
    {
        "name": "McDoS - Roidmi EVE Plus",
        "kind": "Гайд + материалы",
        "compatibility": "ROIDMI EVE Plus",
        "url": "https://mc-dos.ru/language-packs-roidmi-eve-plus/",
        "direct_url": None,
        "note": "Инструкция именно для EVE Plus, структура voice_config и сборка tar.gz."
    },
    {
        "name": "McDoS - оригинальная русская озвучка",
        "kind": "ZIP-шаблон",
        "compatibility": "ROIDMI EVE Plus",
        "url": "https://mc-dos.ru/language-packs-roidmi-eve-plus/",
        "direct_url": "https://mc-dos.ru/upload/roidmi/girl_ru_orig.zip",
        "note": "Разархивированный оригинальный русский голос."
    },
    {
        "name": "McDoS - русский шаблон с подписями фраз",
        "kind": "ZIP-шаблон",
        "compatibility": "ROIDMI EVE Plus",
        "url": "https://mc-dos.ru/language-packs-roidmi-eve-plus/",
        "direct_url": "https://mc-dos.ru/upload/roidmi/original_girl_ru_named.zip",
        "note": "Оригинальные фразы с понятными названиями для создания собственного пакета."
    },
    {
        "name": "4PDA - Roidmi EVE Plus",
        "kind": "Форум / пользовательские пакеты",
        "compatibility": "ROIDMI EVE Plus",
        "url": "https://4pda.to/forum/index.php?showtopic=1023628",
        "direct_url": None,
        "note": "Тема модели, пользовательские озвучки и опыт установки."
    },
    {
        "name": "Звукограм",
        "kind": "TTS / создание MP3",
        "compatibility": "Создание собственного голосового пакета",
        "url": "https://zvukogram.com/speech/",
        "direct_url": None,
        "note": "Синтез речи; MP3 затем собираются в структуру ROIDMI."
    },
    {
        "name": "Видео McDoS по установке",
        "kind": "Видеоинструкция",
        "compatibility": "ROIDMI EVE Plus",
        "url": "https://www.youtube.com/watch?v=hxU6SzgRmjg",
        "direct_url": None,
        "note": "Наглядная инструкция по сторонним языковым пакетам."
    },
]

VOICE_PRESETS = [
    {"name": "Русский штатный", "audio_id": "girl_ru"},
    {"name": "English штатный", "audio_id": "girl_en"},
]

# Cross-checked against current GitHub implementations for roidmi.vacuum.v60.
# This table is intentionally explicit so the GUI does not guess MIoT ids.
VERIFIED_MIOT = {
    "status": (2, 1),
    "fault": (2, 2),
    "fanspeed_mode": (2, 4),
    "sweep_type": (2, 8),
    "battery_level": (3, 1),
    "charging_state": (3, 2),
    "mop_present": (8, 1),
    "work_station_freq": (8, 2),
    "timing": (8, 6),
    "auto_boost": (8, 9),
    "forbid_mode": (8, 10),
    "water_level": (8, 11),
    "double_clean": (8, 20),
    "led_switch": (8, 22),
    "lidar_collision": (8, 23),
    "station_key": (8, 24),
    "station_led": (8, 25),
    "current_audio": (8, 26),
    "voice_conf": (8, 30),
    "volume": (9, 1),
    "mute": (9, 2),
    "path_mode": (13, 8),
    "sweep_mode": (14, 1),
}

VERIFIED_ACTIONS = {
    "start": (2, 1),
    "stop": (2, 2),
    "home": (3, 1),
    "identify": (8, 1),
    "start_dust": (8, 6),
    "update_audio": (8, 11),
    "set_voice": (8, 12),
    "reset_filter": (10, 1),
    "reset_main_brush": (11, 1),
    "reset_side_brush": (12, 1),
    "reset_sensors": (15, 1),
    # Selective room sweep is independently implemented as siid=14, aiid=1
    # by node-xmihome and the Roidmi-EVE-Plus HA configuration.
    "start_room_segments": (14, 1),
}

FAULT_RU = {
    0: "Нет ошибок",
    1: "Низкий заряд, возврат на базу",
    2: "Низкий заряд, отключение",
    3: "Заблокировано колесо",
    4: "Ошибка датчика столкновения",
    5: "Робот наклонён",
    6: "LiDAR заблокирован",
    7: "Загрязнён передний датчик столкновений",
    8: "Загрязнён боковой датчик стены",
    9: "Заблокирована основная щётка",
    10: "Заблокирована боковая щётка",
    11: "Ошибка вентилятора",
    12: "Заблокирована крышка LiDAR",
    13: "Пылесборник заполнен",
    14: "Пылесборник извлечён",
    15: "Пылесборник заполнен или требует проверки",
    16: "Робот застрял",
    17: "Робот поднят",
    18: "Бак для воды извлечён",
    19: "Недостаточно воды",
    20: "Заданная зона недоступна",
    21: "Запуск из запретной зоны невозможен",
    22: "Сработал датчик перепада высоты",
    23: "Ошибка тока водяного насоса",
    24: "Не удалось вернуться на базу",
    25: "Ошибка водяного насоса при низком заряде",
    27: "LiDAR механически заблокирован",
    30: "Ошибка электроники LiDAR",
    31: "Ошибка аккумулятора",
    32: "Ошибка основной щётки",
    33: "Ошибка ведущего колеса",
    34: "Ошибка боковой щётки",
    35: "Ошибка вентилятора",
    37: "Ошибка обновления прошивки",
}
ROOT = Path(__file__).resolve().parent
CRASH_REPORT_PATH = ROOT / "CRASH_REPORT.txt"

# Package cache is read-only compatibility data shipped with a build.
PACKAGE_BACKUP_DIR = ROOT / "backups"
PACKAGE_BACKUP_DIR.mkdir(exist_ok=True)

# Persistent user data lives outside version folders.
SHARED_APP_DIR = Path(os.environ.get("LOCALAPPDATA") or ROOT) / "ROIDMI_EVE_Plus_Control"
SHARED_APP_DIR.mkdir(parents=True, exist_ok=True)
SHARED_DATA_DIR = SHARED_APP_DIR / "data"
SHARED_DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = SHARED_DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
VOICEPACKS_DIR = SHARED_DATA_DIR / "voicepacks"
VOICEPACKS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR = SHARED_DATA_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
MAP_HISTORY_DIR = SHARED_DATA_DIR / "map_history"
MAP_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
UPDATES_DIR = SHARED_DATA_DIR / "updates"
UPDATES_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = SHARED_DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

AUTO_CONFIG_PATH = SHARED_APP_DIR / "AUTO_CONFIG.json"
CLOUD_SESSION_PATH = ROOT / "CLOUD_SESSION.json"  # old-build compatibility
SHARED_CLOUD_SESSION_PATH = SHARED_APP_DIR / "CLOUD_SESSION.json"
PRIVATE_NOTIFY_CONFIG_PATH = SHARED_APP_DIR / "PRIVATE_NOTIFY_CONFIG.json"

LAST_APPLIED_PATH = SHARED_DATA_DIR / "LAST_APPLIED_OPTIMIZATION.json"
USER_PROFILE_PATH = SHARED_DATA_DIR / "USER_PROFILE.json"
ROOM_PROFILES_PATH = SHARED_DATA_DIR / "ROOM_PROFILES.json"
APP_SETTINGS_PATH = SHARED_DATA_DIR / "APP_SETTINGS.json"
RUNTIME_STATE_PATH = SHARED_DATA_DIR / "RUNTIME_STATE.json"
HISTORY_DB_PATH = SHARED_DATA_DIR / "history.sqlite3"
VOICE_CATALOG_PATH = SHARED_DATA_DIR / "VOICE_SOURCES.json"
FIRMWARE_REPORT_PATH = SHARED_DATA_DIR / "FIRMWARE_REPORT.json"
FIRMWARE_DOWNLOAD_DIR = SHARED_DATA_DIR / "firmware"
FIRMWARE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

LIVE_MAP_RAW_PATH = BACKUP_DIR / "last_live_map_roidmi.gz"
LIVE_MAP_PNG_PATH = BACKUP_DIR / "last_live_map_roidmi.png"
LIVE_MAP_ANALYSIS_PATH = BACKUP_DIR / "last_live_map_analysis.json"
LIVE_MAP_REPORT_PATH = BACKUP_DIR / "last_live_map_optimization.txt"
LAST_MAP_INFO_PATH = BACKUP_DIR / "last_map_info.json"
LAST_ROOMS_PATH = BACKUP_DIR / "last_rooms_raw.json"

TOKEN_EXTRACTOR_URL = "https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/releases/latest"
MIOT_SPEC_URL = "https://home.miot-spec.com/spec/roidmi.vacuum.v60"


CLOUD_DEBUG_PATH = LOG_DIR / "cloud_debug.log"

def cloud_log(message):
    try:
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        with CLOUD_DEBUG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")
    except Exception:
        pass


def atomic_write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    tmp.replace(path)


def load_json_file(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return {} if default is None else default


def migrate_legacy_persistent_data():
    """One-way migration from packaged/older version folders into LocalAppData."""
    candidates = []

    # Current package files.
    for name, dst in [
        ("USER_PROFILE.json", USER_PROFILE_PATH),
        ("ROOM_PROFILES.json", ROOM_PROFILES_PATH),
        ("AUTO_CONFIG.json", AUTO_CONFIG_PATH),
        ("VOICE_SOURCES.json", VOICE_CATALOG_PATH),
    ]:
        candidates.append((ROOT / name, dst))

    # Shipped real-map cache.
    for name, dst in [
        ("last_live_map_roidmi.gz", LIVE_MAP_RAW_PATH),
        ("last_live_map_roidmi.png", LIVE_MAP_PNG_PATH),
        ("last_live_map_analysis.json", LIVE_MAP_ANALYSIS_PATH),
        ("last_live_map_optimization.txt", LIVE_MAP_REPORT_PATH),
        ("last_map_info.json", LAST_MAP_INFO_PATH),
        ("last_rooms_raw.json", LAST_ROOMS_PATH),
    ]:
        candidates.append((PACKAGE_BACKUP_DIR / name, dst))

    # Nearby previous versions. Newest mtime wins, but never overwrite shared data.
    sibling_dirs = []
    try:
        sibling_dirs = [
            p for p in ROOT.parent.glob("ROIDMI_EVE_Plus_Control_Windows_v*")
            if p.is_dir() and p.resolve() != ROOT.resolve()
        ]
        sibling_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        sibling_dirs = []

    for folder in sibling_dirs:
        for name, dst in [
            ("USER_PROFILE.json", USER_PROFILE_PATH),
            ("ROOM_PROFILES.json", ROOM_PROFILES_PATH),
            ("AUTO_CONFIG.json", AUTO_CONFIG_PATH),
        ]:
            candidates.append((folder / name, dst))
        old_backup = folder / "backups"
        for name, dst in [
            ("last_live_map_roidmi.gz", LIVE_MAP_RAW_PATH),
            ("last_live_map_roidmi.png", LIVE_MAP_PNG_PATH),
            ("last_live_map_analysis.json", LIVE_MAP_ANALYSIS_PATH),
            ("last_live_map_optimization.txt", LIVE_MAP_REPORT_PATH),
            ("last_map_info.json", LAST_MAP_INFO_PATH),
            ("last_rooms_raw.json", LAST_ROOMS_PATH),
        ]:
            candidates.append((old_backup / name, dst))
        old_vp = folder / "voicepacks"
        if old_vp.exists():
            for p in old_vp.iterdir():
                if p.is_file():
                    target = VOICEPACKS_DIR / p.name
                    if not target.exists():
                        try:
                            shutil.copy2(p, target)
                        except Exception:
                            pass

    for source, target in candidates:
        try:
            if source.exists() and source.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        except Exception:
            pass


def db_connect():
    con = sqlite3.connect(str(HISTORY_DB_PATH), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def init_history_db():
    with db_connect() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS cleaning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT,
                ended_at TEXT NOT NULL,
                source TEXT NOT NULL,
                rooms_json TEXT,
                area_m2 REAL,
                duration_sec REAL,
                fan INTEGER,
                water INTEGER,
                sweep_type INTEGER,
                path_mode INTEGER,
                result TEXT,
                error_code INTEGER,
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_cleaning_sessions_ended
                ON cleaning_sessions(ended_at);
            CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                value REAL,
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_maintenance_kind_time
                ON maintenance(kind, occurred_at);
            CREATE TABLE IF NOT EXISTS status_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                state INTEGER,
                error_code INTEGER,
                battery INTEGER,
                clean_counts INTEGER,
                total_area REAL,
                total_time_sec REAL
            );
            CREATE TABLE IF NOT EXISTS map_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                map_id TEXT,
                sha256 TEXT UNIQUE,
                raw_path TEXT,
                png_path TEXT,
                analysis_path TEXT
            );
            CREATE TABLE IF NOT EXISTS water_tank_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                mop_present INTEGER,
                absence_sec REAL,
                assumed_full INTEGER NOT NULL DEFAULT 0,
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_water_tank_events_time
                ON water_tank_events(occurred_at);
            """
        )


migrate_legacy_persistent_data()
init_history_db()

try:
    from miio.miot_device import MiotDevice
except Exception:
    MiotDevice = None

try:
    from miio.integrations.roidmi.vacuum.roidmivacuum_miot import RoidmiVacuumMiot
except Exception:
    try:
        from miio.integrations.vacuum.roidmi.roidmivacuum_miot import RoidmiVacuumMiot
    except Exception as e:
        RoidmiVacuumMiot = None
        IMPORT_ERROR = e
    else:
        IMPORT_ERROR = None
else:
    IMPORT_ERROR = None


FAN = {
    "0 - выключено": 0,
    "1 - тихо": 1,
    "2 - стандарт": 2,
    "3 - сильный": 3,
    "4 - MAX": 4,
}
SWEEP_TYPE = {
    "0 - сухая уборка": 0,
    "1 - только влажная": 1,
    "2 - сухая + влажная": 2,
}
WATER = {
    "0 - вода выключена": 0,
    "1 - низкая подача": 1,
    "2 - средняя подача": 2,
    "3 - высокая подача": 3,
    "4 - уровень 4": 4,
}
PATH_MODE = {
    "0 - обычный маршрут": 0,
    "1 - Y-образная мойка": 1,
    "2 - повторная мойка": 2,
}
STATION_FREQ = {
    "0 - отключено/по настройке станции": 0,
    "1 - после каждой уборки": 1,
    "2 - после каждой второй уборки": 2,
    "3 - после каждой третьей уборки": 3,
}
DAY_NAMES = {1:"Пн",2:"Вт",3:"Ср",4:"Чт",5:"Пт",6:"Сб",0:"Вс"}
DAY_ORDER = [1,2,3,4,5,6,0]

# Фактическое соответствие комнат пользователя.
ROOM_LABELS = {
    1: "Кухня",
    2: "Спальня",
    3: "Коридор",
    4: "Зал",
    5: "Ванная",
}
OPTIMAL_ROOM_ORDER = [2, 4, 1, 3, 5]

SMART_OPTIMIZED_PROPERTIES = {
    "fanspeed_mode": 3,
    "sweep_type": 2,
    "water_level": 1,
    "path_mode": 0,
    "work_station_freq": 2,
    "volume": 23,
    "auto_boost": True,
    "double_clean": False,
    "led_switch": True,
    "lidar_collision": True,
    "station_led": True,
    "station_key": True,
    "mute": False,
}

# Balanced weekly plan based on the user's real map:
# 30.37 m² mapped cleanable area; kitchen/corridor are high-dirt zones.
SMART_OPTIMIZED_TIMING = {
    "time": [
        # Full clean: Mon / Thu / Sat. Low water protects laminate / carpet zones.
        [39600, 1, 3, 2, [1, 4, 6], 1, [1, 2, 3, 4, 5], 0],
        # High-dirt kitchen + corridor: Tue / Wed / Fri.
        [39600, 1, 4, 2, [2, 3, 5], 2, [1, 3], 0],
        # Sunday: dirty zones + bathroom.
        [39600, 1, 4, 2, [0], 2, [1, 3, 5], 0],
    ],
    "tz": 3,
    "tzs": 10800,
}

SMART_ROOM_PROFILES = {
    1: {
        "name": "Кухня", "floor_type": "Плитка", "dirt_level": "Высокий",
        "fan": 4, "water": 2, "sweep_type": 2, "path_mode": 0, "double_clean": False,
    },
    2: {
        "name": "Спальня", "floor_type": "Ламинат", "dirt_level": "Низкий",
        "fan": 2, "water": 1, "sweep_type": 2, "path_mode": 0, "double_clean": False,
    },
    3: {
        "name": "Коридор", "floor_type": "Плитка/ламинат", "dirt_level": "Высокий",
        "fan": 4, "water": 2, "sweep_type": 2, "path_mode": 0, "double_clean": False,
    },
    4: {
        "name": "Зал", "floor_type": "Ламинат + ковёр", "dirt_level": "Средний",
        "fan": 3, "water": 1, "sweep_type": 2, "path_mode": 0, "double_clean": False,
    },
    5: {
        "name": "Ванная", "floor_type": "Плитка", "dirt_level": "Средний",
        "fan": 3, "water": 2, "sweep_type": 2, "path_mode": 1, "double_clean": False,
    },
}

SMART_OPTIMIZATION_STATS = {
    "mapped_area_m2": 30.37,
    "current_weekly_nominal_area_m2": 162.67,
    "optimized_weekly_nominal_area_m2": 149.05,
    "current_water_load_units": 325.34,
    "optimized_water_load_units": 207.02,
    "historical_seconds_per_m2": 95.83,
}

VACUUM_CAPABILITIES = [
    ("Старт / стоп уборки", "Да", "2/1, 2/2", "Прямое MIoT действие"),
    ("Возврат на базу", "Да", "3/1", "Прямое MIoT действие"),
    ("Поиск робота", "Да", "8/1", "Голосовой сигнал"),
    ("Сбор пыли станцией", "Да", "8/6", "Принудительная самоочистка"),
    ("Выборочная уборка комнат", "Да", "14/1", "mapId + segmentId"),
    ("Мощность всасывания", "Да", "2/4", "0-4"),
    ("Тип уборки", "Да", "2/8", "сухая / влажная / сухая+влажная"),
    ("Подача воды", "Да", "8/11", "0-4"),
    ("Маршрут", "Да", "13/8", "Normal / Y / Repeat"),
    ("Double clean", "Да", "8/20", "Глобальный флаг"),
    ("Carpet auto boost", "Да", "8/9", "Глобальный флаг"),
    ("Расписание", "Да", "8/6 property", "В строке есть fan/type/water/rooms"),
    ("DND", "Да", "8/10", "Интервал времени"),
    ("LiDAR collision", "Да", "8/23", "Вкл./выкл."),
    ("Голос", "Да", "8/12 action", "current_audio 8/26"),
    ("Ресурс фильтра/щёток/датчиков", "Да", "10/1, 11/1, 12/1, 15/1", "Сброс счётчиков"),
    ("Порядок комнат", "Есть в MIoT", "13/11", "Формат строкового payload прошивки не подтверждён"),
    ("Native fan/water по комнате", "Есть в MIoT", "13/10 area-custom", "Вход auto-area строкой; внутренний формат не опубликован"),
]

DEFAULT_ROOM_PROFILES = {
    1: {"name":"Кухня", "floor_type":"Плитка", "dirt_level":"Высокий", "fan":4, "water":3, "sweep_type":2, "path_mode":1, "double_clean":True},
    2: {"name":"Спальня", "floor_type":"Ламинат", "dirt_level":"Низкий", "fan":2, "water":1, "sweep_type":2, "path_mode":0, "double_clean":False},
    3: {"name":"Коридор", "floor_type":"Плитка/ламинат", "dirt_level":"Высокий", "fan":4, "water":2, "sweep_type":2, "path_mode":0, "double_clean":True},
    4: {"name":"Зал", "floor_type":"Ламинат + ковёр", "dirt_level":"Средний", "fan":3, "water":1, "sweep_type":2, "path_mode":0, "double_clean":False},
    5: {"name":"Ванная", "floor_type":"Плитка", "dirt_level":"Средний", "fan":3, "water":3, "sweep_type":2, "path_mode":1, "double_clean":False},
}

# Проверенный рабочий профиль квартиры ~45 м².
OPTIMIZED_PROPERTIES = {
    "fanspeed_mode": 3,
    "sweep_type": 2,
    "water_level": 2,
    "path_mode": 0,
    "work_station_freq": 1,
    "volume": 23,
    "auto_boost": True,
    "double_clean": False,
    "led_switch": True,
    "lidar_collision": True,
    "station_led": True,
    "station_key": True,
    "mute": False,
}
OPTIMIZED_TIMING = {
    "time": [
        [39600, 1, 3, 2, [1,3,5,0], 2, [1,2,3,4,5], 0],
        [39600, 1, 4, 2, [2,4,6], 2, [1,3], 0],
    ],
    "tz": 3,
    "tzs": 10800,
}


def reverse_lookup(mapping, value, fallback=None):
    for k, v in mapping.items():
        if v == value:
            return k
    return fallback if fallback is not None else next(iter(mapping))


def seconds_to_hhmm(sec):
    try:
        sec = int(sec)
        return f"{sec//3600:02d}:{(sec%3600)//60:02d}"
    except Exception:
        return "??:??"


def local_tz_payload():
    offset = datetime.now().astimezone().utcoffset()
    sec = int(offset.total_seconds()) if offset else 0
    hours = int(sec / 3600)
    return hours, sec


class XiaomiCloudLite:
    """Minimal Xiaomi Home cloud client used only to retrieve the ROIDMI map file.

    Credentials live only in memory. The class does not write username/password/service
    tokens to disk.
    """
    COUNTRIES = ["ru", "de", "cn", "us", "sg", "tw", "in", "i2"]

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.agent = self._generate_agent()
        self.device_id = self._generate_device_id()
        self.sign = None
        self.ssecurity = None
        self.user_id = None
        self.location = None
        self.service_token = None
        self.two_factor_url = None
        self.identity_session = None
        self.step1_auth = {}
        self.pass_token = None

    @staticmethod
    def _to_json(txt):
        return json.loads(txt.replace("&&&START&&&", ""))

    @staticmethod
    def _generate_agent():
        prefix = "".join(chr(random.randint(97, 122)) for _ in range(18))
        suffix = "".join(chr(random.randint(65, 69)) for _ in range(13))
        return f"{prefix}-{suffix} APP/com.xiaomi.mihome APPV/10.5.201"

    @staticmethod
    def _generate_device_id():
        return "".join(chr(random.randint(97, 122)) for _ in range(6))

    def login(self, captcha_code=None, captcha_ick=None, reuse_session=False):
        """Xiaomi xiaomiio login with CAPTCHA/2FA support.

        Critical detail:
        /pass/serviceLogin (step 1) may already return ssecurity/userId/passToken.
        Those values MUST be preserved before serviceLoginAuth2. During Xiaomi 2FA
        the verify endpoint often returns location but no ssecurity.
        """
        if not reuse_session:
            self.session.close()
            self.session = requests.Session()
            self.agent = self._generate_agent()
            self.device_id = self._generate_device_id()
            self.session.cookies.set("sdkVersion", "3.8.6", domain="mi.com")
            self.session.cookies.set("sdkVersion", "3.8.6", domain="xiaomi.com")
            self.session.cookies.set("deviceId", self.device_id, domain="mi.com")
            self.session.cookies.set("deviceId", self.device_id, domain="xiaomi.com")

            headers = {
                "User-Agent": self.agent,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            r = self.session.get(
                "https://account.xiaomi.com/pass/serviceLogin",
                params={"sid": "xiaomiio", "_json": "true"},
                headers=headers,
                cookies={"userId": self.username},
                timeout=15,
            )
            r.raise_for_status()
            step1 = self._to_json(r.text)

            if "_sign" not in step1:
                raise RuntimeError("Xiaomi Cloud: serviceLogin не вернул _sign.")

            # THIS is the v10 fix: keep the authentication material from step 1.
            self.sign = step1["_sign"]
            self.user_id = step1.get("userId") or self.user_id
            self.ssecurity = step1.get("ssecurity") or self.ssecurity
            self.pass_token = step1.get("passToken") if hasattr(self, "pass_token") else step1.get("passToken")
            self.step1_auth = dict(step1)

            cloud_log(
                "step1: "
                f"code={step1.get('code')}, "
                f"has_sign={bool(step1.get('_sign'))}, "
                f"has_ssecurity={bool(step1.get('ssecurity'))}, "
                f"has_user_id={bool(step1.get('userId'))}"
            )
        else:
            step1 = getattr(self, "step1_auth", {}) or {}

        headers = {
            "User-Agent": self.agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Match Xiaomi's own values from serviceLogin step1 instead of hard-coding
        # callback/qs when the server supplied them.
        fields = {
            "user": self.username,
            "hash": hashlib.md5(self.password.encode()).hexdigest().upper(),
            "callback": step1.get("callback") or "https://sts.api.io.mi.com/sts",
            "sid": step1.get("sid") or "xiaomiio",
            "qs": step1.get("qs") or "",
            "_sign": step1.get("_sign") or self.sign,
        }
        params = {"_json": "true"}
        cookies = {}

        if captcha_code:
            fields["captCode"] = captcha_code
            params["_dc"] = int(time.time() * 1000)
            if captcha_ick:
                cookies["ick"] = captcha_ick

        r = self.session.post(
            "https://account.xiaomi.com/pass/serviceLoginAuth2",
            headers=headers,
            data=fields,
            params=params,
            cookies=cookies,
            timeout=15,
        )
        r.raise_for_status()
        auth = self._to_json(r.text)

        # Preserve any additional values returned by step2.
        self.user_id = auth.get("userId") or self.user_id
        self.ssecurity = auth.get("ssecurity") or self.ssecurity

        cloud_log(
            "step2: "
            f"code={auth.get('code')}, "
            f"has_location={bool(auth.get('location'))}, "
            f"has_notification={bool(auth.get('notificationUrl'))}, "
            f"has_captcha={bool(auth.get('captchaUrl'))}, "
            f"effective_ssecurity={bool(self.ssecurity)}"
        )

        ntf = auth.get("notificationUrl")
        if ntf:
            if not ntf.startswith("http"):
                ntf = "https://account.xiaomi.com" + ntf
            self.two_factor_url = ntf
            cloud_log(
                f"login: 2FA required, code={auth.get('code')}, "
                f"effective_ssecurity={bool(self.ssecurity)}"
            )
            return {"two_factor_required": True, "url": ntf}

        cap = auth.get("captchaUrl")
        if cap:
            if not cap.startswith("http"):
                cap = "https://account.xiaomi.com" + cap
            cap_resp = self.session.get(
                cap,
                headers={"User-Agent": self.agent},
                timeout=15,
            )
            cap_resp.raise_for_status()
            ick = cap_resp.cookies.get("ick") or self.session.cookies.get("ick")
            if not ick:
                raise RuntimeError("Xiaomi Cloud: CAPTCHA получена, но cookie ick отсутствует.")
            return {
                "captcha_required": True,
                "captcha_bytes": cap_resp.content,
                "captcha_ick": ick,
                "captcha_url": cap,
                "code": auth.get("code"),
            }

        location = auth.get("location")
        if location:
            self.location = location
            rr = self.session.get(
                self._abs_account_url(location),
                headers=headers,
                allow_redirects=True,
                timeout=15,
            )
            rr.raise_for_status()
            self.service_token = (
                rr.cookies.get("serviceToken")
                or self.session.cookies.get("serviceToken")
            )
            self.user_id = (
                rr.cookies.get("userId")
                or self.session.cookies.get("userId")
                or self.user_id
            )
            if not self.service_token:
                raise RuntimeError("Xiaomi Cloud: serviceToken не получен после redirect.")
            if not self.ssecurity:
                raise RuntimeError(
                    "Xiaomi Cloud: serviceToken получен, но ssecurity отсутствует "
                    "и в step1, и в step2."
                )
            cloud_log("login: SUCCESS without 2FA")
            return {"ok": True}

        code = auth.get("code")
        desc = auth.get("description") or auth.get("desc") or auth.get("result") or "неизвестная причина"
        if code == 87001 and captcha_code:
            raise RuntimeError("Xiaomi отклонил введённую CAPTCHA. Повторите с новым изображением.")
        if code in (20003, 70002, 70016):
            raise RuntimeError("Xiaomi отклонил логин или пароль.")
        raise RuntimeError(
            f"Xiaomi Cloud: авторизация не выполнена (code={code}, {desc})."
        )

    def _abs_account_url(self, url):
        if not url:
            return url
        return url if url.startswith("http") else "https://account.xiaomi.com" + url

    def _account_json(self, response):
        try:
            return self._to_json(response.text)
        except Exception as e:
            raise RuntimeError(f"Xiaomi Cloud: не удалось разобрать ответ аккаунта: {e}")

    def verify_ticket(self, ticket):
        """Verify Xiaomi phone/email ticket in the same login session.

        This intentionally does NOT start a new serviceLogin after successful verification.
        A new login is what caused the repeated CAPTCHA/2FA loop in v8.
        """
        url = self.two_factor_url
        if not url:
            raise RuntimeError("Xiaomi Cloud: отсутствует URL подтверждения 2FA.")

        path = "fe/service/identity/authStart"
        if path not in url:
            # Some accounts omit the "fe/service/" prefix.
            path = "identity/authStart"
        if path not in url:
            raise RuntimeError("Xiaomi Cloud: неизвестный формат verification URL.")

        cloud_log("2FA: requesting identity/list")
        list_url = url.replace(path, "identity/list")
        resp = self.session.get(
            list_url,
            headers={"User-Agent": self.agent},
            timeout=12
        )
        resp.raise_for_status()

        identity_session = (
            resp.cookies.get("identity_session")
            or self.session.cookies.get("identity_session")
        )
        if not identity_session:
            raise RuntimeError("Xiaomi Cloud: identity_session не получен.")

        data = self._account_json(resp)
        flag = data.get("flag", 4)
        options = data.get("options", [flag]) or [flag]
        cloud_log(f"2FA: methods={options}")

        last = None
        for flg in options:
            api = {4: "/identity/auth/verifyPhone", 8: "/identity/auth/verifyEmail"}.get(flg)
            if not api:
                continue

            cloud_log(f"2FA: submitting ticket via flag={flg}")
            vr = self.session.post(
                "https://account.xiaomi.com" + api,
                params={"_dc": int(time.time() * 1000)},
                data={
                    "_flag": flg,
                    "ticket": ticket,
                    "trust": "false",
                    "_json": "true",
                },
                cookies={"identity_session": identity_session},
                headers={
                    "User-Agent": self.agent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=12
            )
            vr.raise_for_status()
            vd = self._account_json(vr)
            last = vd
            cloud_log(
                f"2FA: verify response code={vd.get('code')}, "
                f"has_location={bool(vd.get('location'))}, "
                f"has_ssecurity={bool(vd.get('ssecurity'))}"
            )

            if vd.get("code") != 0:
                continue

            # Preserve any security values returned by the verification endpoint.
            self.user_id = vd.get("userId") or self.user_id
            self.ssecurity = vd.get("ssecurity") or self.ssecurity

            location = vd.get("location")
            if not location:
                raise RuntimeError(
                    "Xiaomi принял код 2FA, но не вернул location. "
                    "Повторный вход не запускается, чтобы не вызвать новый цикл CAPTCHA."
                )

            cloud_log("2FA: following verification location")
            self._follow_verification_location(location)

            if not self.service_token:
                raise RuntimeError(
                    "Код 2FA принят, но Xiaomi не выдал serviceToken. "
                    "Смотрите cloud_debug.log."
                )

            if not self.ssecurity:
                cloud_log(
                    "2FA: serviceToken present but ssecurity missing; "
                    "trying authenticated serviceLogin refresh"
                )
                self._refresh_ssecurity_after_verified_session()

            if not self.ssecurity:
                raise RuntimeError(
                    "2FA успешно принят и serviceToken получен, но Xiaomi не выдал "
                    "ssecurity даже после повторного serviceLogin в уже подтверждённой "
                    "сессии. Пришлите cloud_debug.log."
                )

            self.identity_session = None
            cloud_log("2FA: SUCCESS - serviceToken + ssecurity obtained")
            return {"ok": True}

        code = last.get("code") if isinstance(last, dict) else None
        desc = ""
        if isinstance(last, dict):
            desc = last.get("description") or last.get("desc") or ""
        raise RuntimeError(
            f"Xiaomi отклонил код подтверждения (code={code}). {desc}".strip()
        )

    def _cookie_names_safe(self):
        try:
            return sorted({c.name for c in self.session.cookies})
        except Exception:
            return []

    @staticmethod
    def _cookie_values(jar, name):
        """Return all matching cookie values without RequestsCookieJar.get() ambiguity."""
        values = []
        try:
            for c in jar:
                if c.name == name:
                    values.append(c.value)
        except Exception:
            pass
        return values

    def _cookie_get_safe(self, name, response=None):
        """Get the newest matching cookie without CookieConflictError.

        Xiaomi may set duplicate userId/cUserId cookies for different paths/domains.
        RequestsCookieJar.get('userId') raises CookieConflictError in that case.
        """
        values = []
        if response is not None:
            values.extend(self._cookie_values(response.cookies, name))
        values.extend(self._cookie_values(self.session.cookies, name))
        return values[-1] if values else None

    def _cookie_count_safe(self, name):
        return len(self._cookie_values(self.session.cookies, name))

    def _follow_verification_location(self, location):
        """Follow Xiaomi verification redirects manually.

        Manual redirect handling prevents requests from appearing to hang on a long
        or circular STS/account redirect chain and lets us record exactly which host
        was reached. Secret query values are never written to the log.
        """
        url = self._abs_account_url(location)
        headers = {
            "User-Agent": self.agent,
            "Referer": "https://account.xiaomi.com/",
        }

        for hop in range(12):
            parsed = urlparse.urlparse(url)
            cloud_log(
                f"2FA redirect hop={hop} host={parsed.netloc} path={parsed.path} "
                f"cookies={self._cookie_names_safe()}"
            )

            try:
                resp = self.session.get(
                    url,
                    headers=headers,
                    allow_redirects=False,
                    timeout=(5, 8),
                )
            except requests.exceptions.Timeout:
                raise RuntimeError(
                    f"Xiaomi redirect timeout: {parsed.netloc}{parsed.path}. "
                    "Проверьте VPN/Firewall. Подробности в cloud_debug.log."
                )

            cloud_log(
                f"2FA redirect response hop={hop} status={resp.status_code} "
                f"set_cookie_names={sorted(resp.cookies.keys())}"
            )

            # Cookies from response are already merged into the session by requests.
            self.service_token = (
                self._cookie_get_safe("serviceToken", resp)
                or self.service_token
            )
            self.user_id = (
                self._cookie_get_safe("userId", resp)
                or self.user_id
            )

            cloud_log(
                f"2FA redirect cookie counts: "
                f"userId={self._cookie_count_safe('userId')}, "
                f"cUserId={self._cookie_count_safe('cUserId')}, "
                f"passToken={self._cookie_count_safe('passToken')}, "
                f"serviceToken={self._cookie_count_safe('serviceToken')}"
            )

            if self.service_token:
                cloud_log("2FA redirect: serviceToken obtained")
                return resp

            if resp.status_code in (301, 302, 303, 307, 308):
                nxt = resp.headers.get("Location")
                if not nxt:
                    cloud_log("2FA redirect: response has no Location header")
                    break
                next_url = urlparse.urljoin(url, nxt)
                next_parsed = urlparse.urlparse(next_url)
                cloud_log(
                    f"2FA redirect next host={next_parsed.netloc} "
                    f"path={next_parsed.path}"
                )
                url = next_url
                continue

            # Xiaomi may finish on an HTML confirm page containing skipUrl.
            final_url = str(resp.url or url)
            parsed_final = urlparse.urlparse(final_url)
            qs = urlparse.parse_qs(parsed_final.query)
            skip_url = (qs.get("skipUrl") or [None])[0]
            if skip_url:
                cloud_log("2FA redirect: skipUrl detected")
                url = self._abs_account_url(skip_url)
                continue

            break

        raise RuntimeError(
            "Xiaomi 2FA принят, но redirect-цепочка не выдала serviceToken. "
            "Смотрите cloud_debug.log."
        )

    def _refresh_ssecurity_after_verified_session(self):
        """Get xiaomiio ssecurity after identity verification.

        Once 2FA has established account cookies (typically userId/passToken),
        serviceLogin can return a completed xiaomiio login context without starting
        a new password/2FA flow. We do NOT call serviceLoginAuth2 here.
        """
        cloud_log(
            "post-2FA serviceLogin refresh: begin "
            f"cookies={self._cookie_names_safe()}"
        )
        try:
            resp = self.session.get(
                "https://account.xiaomi.com/pass/serviceLogin",
                params={"sid": "xiaomiio", "_json": "true"},
                headers={"User-Agent": self.agent},
                timeout=(5, 8),
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                "Xiaomi serviceLogin после 2FA не ответил вовремя. "
                "Проверьте VPN/Firewall."
            )

        resp.raise_for_status()
        data = self._account_json(resp)
        cloud_log(
            "post-2FA serviceLogin refresh: "
            f"code={data.get('code')}, "
            f"has_ssecurity={bool(data.get('ssecurity'))}, "
            f"has_location={bool(data.get('location'))}, "
            f"cookies={self._cookie_names_safe()}"
        )

        self.user_id = data.get("userId") or self.user_id
        self.ssecurity = data.get("ssecurity") or self.ssecurity
        if data.get("passToken"):
            self.pass_token = data.get("passToken")

        # If the already-authenticated session returns a completed location, follow it.
        if data.get("location"):
            try:
                self._follow_verification_location(data["location"])
            except Exception as exc:
                cloud_log(f"post-2FA location follow warning: {type(exc).__name__}")

        return bool(self.ssecurity)

    def export_auth(self):
        if not (self.user_id and self.service_token and self.ssecurity):
            return None
        return {
            "username": self.username,
            "user_id": str(self.user_id),
            "service_token": self.service_token,
            "ssecurity": self.ssecurity,
            "agent": self.agent,
            "device_id": self.device_id,
            "saved_at": datetime.now().astimezone().isoformat(),
        }

    def import_auth(self, data):
        if not isinstance(data, dict):
            return False
        if str(data.get("username", "")) != str(self.username):
            return False
        if not all(data.get(k) for k in ("user_id", "service_token", "ssecurity")):
            return False
        self.user_id = str(data["user_id"])
        self.service_token = data["service_token"]
        self.ssecurity = data["ssecurity"]
        self.agent = data.get("agent") or self.agent
        self.device_id = data.get("device_id") or self.device_id
        return True

    @staticmethod
    def _api_url(country):
        return "https://" + ("" if country == "cn" else country + ".") + "api.io.mi.com/app"

    @staticmethod
    def _nonce():
        millis = round(time.time() * 1000)
        b = os.urandom(8) + int(millis / 60000).to_bytes(4, byteorder="big")
        return base64.b64encode(b).decode()

    def _signed_nonce(self, nonce):
        h = hashlib.sha256(base64.b64decode(self.ssecurity) + base64.b64decode(nonce))
        return base64.b64encode(h.digest()).decode()

    @staticmethod
    def _enc_signature(url, method, signed_nonce, params):
        parts = [method.upper(), url.split("com")[1].replace("/app/", "/")]
        parts.extend(f"{k}={v}" for k, v in params.items())
        parts.append(signed_nonce)
        return base64.b64encode(hashlib.sha1("&".join(parts).encode()).digest()).decode()

    @staticmethod
    def _rc4_encrypt(password, payload):
        cipher = ARC4.new(base64.b64decode(password))
        cipher.encrypt(bytes(1024))
        return base64.b64encode(cipher.encrypt(payload.encode())).decode()

    @staticmethod
    def _rc4_decrypt(password, payload):
        cipher = ARC4.new(base64.b64decode(password))
        cipher.encrypt(bytes(1024))
        return cipher.encrypt(base64.b64decode(payload))

    def api(self, country, path, data_obj):
        url = self._api_url(country) + path
        params = {"data": json.dumps(data_obj, ensure_ascii=False, separators=(",", ":"))}
        nonce = self._nonce()
        signed = self._signed_nonce(nonce)

        params["rc4_hash__"] = self._enc_signature(url, "POST", signed, params)
        encrypted = {k: self._rc4_encrypt(signed, v) for k, v in params.items()}
        encrypted.update({
            "signature": self._enc_signature(url, "POST", signed, encrypted),
            "ssecurity": self.ssecurity,
            "_nonce": nonce,
        })

        headers = {
            "Accept-Encoding": "identity",
            "User-Agent": self.agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
            "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        }
        cookies = {
            "userId": str(self.user_id),
            "yetAnotherServiceToken": str(self.service_token),
            "serviceToken": str(self.service_token),
            "locale": "ru_RU",
            "timezone": "GMT+03:00",
            "is_daylight": "0",
            "dst_offset": "0",
            "channel": "MI_APP_STORE",
        }
        r = self.session.post(url, headers=headers, cookies=cookies, data=encrypted, timeout=10)
        r.raise_for_status()
        decoded = self._rc4_decrypt(self._signed_nonce(encrypted["_nonce"]), r.text)
        return json.loads(decoded)

    def do_miot_action(self, country, did, siid, aiid, in_params):
        """Execute MIoT action through Xiaomi Cloud.

        This is used for ROIDMI map actions because some v60 firmwares answer
        local miIO action calls with -9999 "user ack timeout".
        """
        payload = {
            "params": {
                "did": str(did),
                "siid": int(siid),
                "aiid": int(aiid),
                "in": list(in_params or []),
            }
        }
        cloud_log(
            f"cloud action: did={did} siid={siid} aiid={aiid} "
            f"in_count={len(in_params or [])}"
        )
        resp = self.api(country, "/miotspec/action", payload)
        cloud_log(
            "cloud action response: "
            f"top_code={resp.get('code') if isinstance(resp, dict) else None}"
        )
        if not isinstance(resp, dict):
            raise RuntimeError("Xiaomi Cloud вернул неожиданный ответ на MIoT action.")

        top_code = resp.get("code")
        if top_code not in (0, None):
            raise RuntimeError(
                f"Xiaomi Cloud MIoT action: code={top_code}, "
                f"message={resp.get('message')}"
            )

        result = resp.get("result")
        if isinstance(result, dict):
            action_code = result.get("code", 0)
            if action_code not in (0, None):
                raise RuntimeError(
                    f"Устройство отклонило cloud action: code={action_code}, "
                    f"description={result.get('description')}"
                )
        return resp

    def find_device(self, token, preferred_country="auto"):
        countries = self.COUNTRIES if preferred_country == "auto" else [preferred_country]
        token_cf = token.casefold()

        # Fast legacy device-list API.
        for country in countries:
            try:
                r = self.api(country, "/home/device_list",
                             {"getVirtualModel": False, "getHuamiDevices": 0})
                for d in (r.get("result", {}) or {}).get("list", []) or []:
                    if str(d.get("token", "")).casefold() == token_cf:
                        return {
                            "country": country,
                            "user_id": d.get("uid"),
                            "device_id": d.get("did"),
                            "model": d.get("model"),
                            "name": d.get("name"),
                        }
            except Exception:
                pass

        # Newer homes API fallback.
        for country in countries:
            try:
                h = self.api(country, "/v2/homeroom/gethome",
                             {"fg": True, "fetch_share": True, "fetch_share_dev": True,
                              "limit": 300, "app_ver": 7})
                result = h.get("result", {}) or {}
                homes = (result.get("homelist") or []) + (result.get("share_home_list") or [])
                for home in homes:
                    home_id = int(home["id"])
                    owner = home["uid"]
                    devs = self.api(country, "/v2/home/home_device_list",
                                    {"home_id": home_id, "home_owner": owner, "limit": 200,
                                     "get_split_device": True, "support_smart_home": True})
                    for d in (devs.get("result", {}) or {}).get("device_info", []) or []:
                        if str(d.get("token", "")).casefold() == token_cf:
                            return {
                                "country": country,
                                "user_id": owner,
                                "device_id": d.get("did"),
                                "model": d.get("model"),
                                "name": d.get("name"),
                            }
            except Exception:
                pass

        return None

    def firmware_info(self, country, did, pid=0):
        """Read Xiaomi firmware metadata without starting any upgrade."""
        result = {
            "country": country,
            "did": str(did),
            "pid": int(pid or 0),
            "checkversion": None,
            "multi_checkversion": None,
            "history": None,
            "errors": {},
        }
        calls = [
            ("checkversion", "/home/checkversion", {"did": str(did), "pid": int(pid or 0)}),
            ("multi_checkversion", "/home/multi_checkversion", {"dids": [str(did)]}),
            ("history", "/v2/device/get_firmware_history", {"did": str(did)}),
        ]
        for key, path, payload in calls:
            try:
                result[key] = self.api(country, path, payload)
            except Exception as e:
                result["errors"][key] = f"{type(e).__name__}: {e}"
        return result

    def get_roidmi_map(self, country, user_id, device_id):
        # ROIDMI EVE Plus uses the interim-file API. For this model the map object name is "0".
        resp = self.api(
            country,
            "/v2/home/get_interim_file_url",
            {"obj_name": f"{user_id}/{device_id}/0"}
        )
        url = (resp.get("result") or {}).get("url")
        if not url:
            raise RuntimeError("Xiaomi Cloud не вернул URL карты.")
        r = self.session.get(url, timeout=20)
        r.raise_for_status()
        return r.content

    @staticmethod
    def parse_roidmi_rooms(raw_map):
        try:
            unzipped = gzip.decompress(raw_map)
        except Exception as e:
            raise RuntimeError(f"Не удалось распаковать карту ROIDMI: {e}")

        marker = unzipped.find(bytes([127, 123]))  # 0x7F followed by '{'
        if marker < 0:
            # fallback: look for the JSON block from the tail
            marker2 = unzipped.rfind(b'{"width"')
            if marker2 < 0:
                raise RuntimeError("В карте не найден JSON-блок с описанием комнат.")
            info_raw = unzipped[marker2:]
        else:
            info_raw = unzipped[marker + 1:]

        try:
            info = json.loads(info_raw.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"JSON карты не разобран: {e}")

        areas = info.get("autoArea")
        if areas is None:
            areas = info.get("autoAreaValue")
        areas = areas or []

        rooms = []
        for a in areas:
            try:
                rid = int(a.get("id"))
            except Exception:
                continue
            system_name = str(a.get("name") or f"Room{rid}")
            clean_count = a.get("CleanCount")
            rooms.append({
                "id": rid,
                "name": system_name,
                "friendly_name": ROOM_LABELS.get(rid, system_name),
                "clean_count": clean_count,
            })

        meta = {
            "mapId": info.get("mapId"),
            "width": info.get("width"),
            "height": info.get("height"),
            "resolution": info.get("resolution"),
            "x_min": info.get("x_min"),
            "y_min": info.get("y_min"),
        }
        return rooms, meta, info


def write_crash_report(exc_type, exc_value, exc_tb, context="UNCAUGHT"):
    try:
        report = [
            "=" * 80,
            datetime.now().astimezone().isoformat(),
            f"CONTEXT: {context}",
            f"EXCEPTION: {exc_type.__name__}: {exc_value}",
            "",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
            "",
        ]
        with CRASH_REPORT_PATH.open("a", encoding="utf-8") as f:
            f.write("\n".join(report))
    except Exception:
        pass


def global_excepthook(exc_type, exc_value, exc_tb):
    write_crash_report(exc_type, exc_value, exc_tb, "sys.excepthook")
    try:
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    except Exception:
        pass


sys.excepthook = global_excepthook



def enable_windows_dpi_awareness():
    """Enable crisp rendering on Windows 10/11 at 100-150% display scaling."""
    if os.name != "nt":
        return
    try:
        # Per-monitor v2. Available on current Windows 10/11.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        enable_windows_dpi_awareness()
        super().__init__()
        self.report_callback_exception = self._tk_callback_exception
        self.title(APP_TITLE)
        # 1920x1080 target: start large, then maximize to the Windows work area.
        self.geometry("1720x930")
        self.minsize(1180, 700)
        self.device = None
        self.last_data = {}
        self.imported_config = None
        self.imported_config_path = None
        self.current_timing = {"time": []}
        self.schedule_unknown = {}
        self.rooms_data = []
        self.current_map_id = None
        self.room_select_vars = {}
        self.dashboard_map_canvas = None
        self.dashboard_schedule_list = None
        self.dashboard_status_lines = None
        self.dashboard_consumables_lines = None
        self.dashboard_room_box_refs = {}
        self.dashboard_room_label_refs = {}
        self.dashboard_room_names = {1:"Кухня",2:"Спальня",3:"Коридор",4:"Зал",5:"Ванная"}
        self.dashboard_status_var = tk.StringVar(value="Не подключено")
        self.dashboard_substatus_var = tk.StringVar(value="Подключите робот и прочитайте состояние")
        self.dashboard_battery_var = tk.StringVar(value="-")
        self.dashboard_error_var = tk.StringVar(value="-")
        self.dashboard_device_var = tk.StringVar(value="ROIDMI EVE Plus / roidmi.vacuum.v60")
        self.dashboard_ip_var = tk.StringVar(value="IP: -")
        self.dashboard_token_var = tk.StringVar(value="Токен: ••••••••")
        self.dashboard_map_meta_var = tk.StringVar(value="Карта: не загружена")
        self.dashboard_map_mode_var = tk.StringVar(value="live")
        self.dashboard_real_map_photo = None
        self.dashboard_real_map_source_var = tk.StringVar(value="Локальный скриншот Xiaomi (не живая карта)")
        self.dashboard_real_map_path = ROOT / "assets" / "real_map_reference.png"
        self.dashboard_live_map_path = LIVE_MAP_PNG_PATH
        self.dashboard_live_map_available = False
        self.dashboard_live_map_status_var = tk.StringVar(value="Живая карта Xiaomi Cloud ещё не загружена.")
        self.last_raw_map = None
        self.last_map_analysis = None
        self.pending_map_export = False
        self.map_optimization_status_var = tk.StringVar(value="Оптимизация карты ещё не выполнена.")
        self.dashboard_real_map_boxes = {
            2: (22, 45, 365, 246),
            4: (382, 36, 540, 255),
            1: (132, 266, 364, 530),
            3: (356, 256, 568, 480),
            5: (410, 485, 540, 705),
        }
        self.voice_current_var = tk.StringVar(value="-")
        self.voice_preset_var = tk.StringVar(value="Русский штатный (girl_ru)")
        self.voice_raw_var = tk.StringVar(value="girl_ru")
        self.voice_cloud_fallback_var = tk.BooleanVar(value=True)
        self.voice_status_var = tk.StringVar(value="Голос ещё не прочитан.")
        self.voice_pack_path_var = tk.StringVar(value="")
        self.voice_pack_info_var = tk.StringVar(value="Файл пакета не выбран.")
        self.voice_download_url_var = tk.StringVar(value="")
        self.voice_library_status_var = tk.StringVar(value="Локальная библиотека голосов готова.")
        self.voice_sources_tree = None
        self.voice_library_tree = None
        self._voice_library_files = []
        self.export_status_var = tk.StringVar(value="Центр экспорта готов.")
        self.smart_optimization_status_var = tk.StringVar(value="Умная оптимизация готова к применению.")
        self.cloud_session_status_var = tk.StringVar(value="Xiaomi Cloud: проверка сохранённой авторизации...")
        self.pending_full_export_path = None
        self.discovery_status_var = tk.StringVar(value="Автопоиск ещё не запускался.")
        self.room_profile_select_vars = {}
        self.room_profile_fan_vars = {}
        self.room_profile_water_vars = {}
        self.room_profile_sweep_vars = {}
        self.room_profile_path_vars = {}
        self.room_profile_double_vars = {}
        self.room_profile_floor_vars = {}
        self.room_profile_dirt_vars = {}
        self.room_profiles_status_var = tk.StringVar(value="Профили комнат готовы.")
        self.room_profile_sequence_cancel = False
        self.room_profile_sequence_running = False
        self.dashboard_rooms_var = tk.StringVar(value="Комнаты: 1 Кухня, 2 Спальня, 3 Коридор, 4 Зал, 5 Ванная")
        self.direct_room_use_cloud_fallback = tk.BooleanVar(value=False)
        self.direct_room_map_id_var = tk.StringVar(value="")
        self.map_info_raw = {}
        self.auto_area_raw = []
        self.room_profile_vars = {}
        self.profile_clean_count_vars = {}
        self.cloud_2fa_url = None
        self.pending_cloud_client = None
        self.active_cloud_client = None
        self.active_cloud_device = None
        self.pending_captcha_ick = None
        self.pending_captcha_path = None
        self.suspend_live_autosave = False
        self.live_autosave_enabled = True
        self.live_general_job = None
        self.live_schedule_job = None
        self.live_dnd_job = None
        self.live_room_order_job = None
        self.auto_apply_in_progress = False
        self.auto_apply_global_done = False
        self.auto_apply_order_done = False
        self.busy = False
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="roidmi")
        self.monitor_job = None
        self.monitor_inflight = False
        saved_runtime = load_json_file(RUNTIME_STATE_PATH, {})
        self._last_counter_snapshot = (
            saved_runtime if isinstance(saved_runtime, dict) and saved_runtime else None
        )
        self._last_status_db_write = 0.0
        self._last_status_signature = None
        self._active_manual_session = None
        self._notification_cooldowns = {}
        self._closing = False
        self._tray_icon = None
        self._tray_thread = None
        self._map_room_screen_points = {}
        self._live_map_display = None
        self.performance_status_var = tk.StringVar(value="Производительность: оптимизированный режим")
        self._last_center_refresh = 0.0
        self._center_refresh_job = None
        self.ui_screen_var = tk.StringVar(value="Интерфейс: определение экрана...")
        self.ui_dpi = 96.0
        self.app_settings = self._load_app_settings()
        self.notify_config = self._load_notify_config()
        self.season_mode_var = tk.StringVar(value=self.app_settings.get("season_mode", "Авто"))
        self.minimize_to_tray_var = tk.BooleanVar(value=bool(self.app_settings.get("minimize_to_tray", True)))
        self.update_manifest_url_var = tk.StringVar(value=self.app_settings.get("update_manifest_url", ""))
        self.notify_windows_var = tk.BooleanVar(value=bool(self.notify_config.get("windows", True)))
        self.notify_telegram_var = tk.BooleanVar(value=bool(self.notify_config.get("telegram_enabled", False)))
        self.telegram_token_var = tk.StringVar(value=self.notify_config.get("telegram_token", ""))
        self.telegram_chat_var = tk.StringVar(value=self.notify_config.get("telegram_chat_id", ""))
        self.notify_ntfy_var = tk.BooleanVar(value=bool(self.notify_config.get("ntfy_enabled", False)))
        self.ntfy_url_var = tk.StringVar(value=self.notify_config.get("ntfy_url", ""))
        self.notify_email_var = tk.BooleanVar(
            value=bool(self.notify_config.get("email_enabled", False))
        )
        self.email_to_var = tk.StringVar(
            value=self.notify_config.get("email_to", "")
        )
        self.smtp_host_var = tk.StringVar(
            value=self.notify_config.get("smtp_host", "smtp.gmail.com")
        )
        self.smtp_port_var = tk.IntVar(
            value=int(self.notify_config.get("smtp_port", 587) or 587)
        )
        self.smtp_user_var = tk.StringVar(
            value=self.notify_config.get("smtp_user", "")
        )
        self.smtp_password_var = tk.StringVar(
            value=self.notify_config.get("smtp_password", "")
        )
        self.email_status_var = tk.StringVar(
            value="Email: настройте SMTP/App Password для автоматической отправки."
        )
        self.water_low_threshold_var = tk.IntVar(
            value=int(self.app_settings.get("water_low_threshold_pct", 30) or 30)
        )
        self.center_status_var = tk.StringVar(value="Интеллектуальный центр готов.")
        self.service_forecast_var = tk.StringVar(value="Прогноз обслуживания ещё не рассчитан.")
        self.water_forecast_var = tk.StringVar(value="Прогноз воды ещё не рассчитан.")
        self.auto_water_refill_var = tk.BooleanVar(
            value=bool(self.app_settings.get("auto_water_refill_on_tank_reinsert", True))
        )
        self.water_tank_state_var = tk.StringVar(value="Бак воды: состояние ещё не определено.")
        self.water_virtual_level_var = tk.StringVar(value="Виртуальный бак: нет отметки о заполнении.")
        self._last_mop_present = None
        self._tank_removed_at = None
        self._tank_removed_confirmed = False
        self.adaptive_plan_var = tk.StringVar(value="Адаптивный план ещё не рассчитан.")
        self.update_status_var = tk.StringVar(value="Обновления: источник не настроен.")
        self.github_auto_check_var = tk.BooleanVar(
            value=bool(self.app_settings.get("github_auto_check", True))
        )
        self.github_update_busy = False
        self.github_latest_manifest = None
        self.firmware_current_var = tk.StringVar(value="-")
        self.firmware_hw_var = tk.StringVar(value="-")
        self.firmware_model_var = tk.StringVar(value=MODEL)
        self.firmware_mac_var = tk.StringVar(value="-")
        self.firmware_latest_var = tk.StringVar(value="не проверено")
        self.firmware_cloud_status_var = tk.StringVar(value="Официальная проверка Xiaomi Cloud ещё не выполнялась.")
        self.firmware_ota_state_var = tk.StringVar(value="idle / неизвестно")
        self.firmware_ota_progress_var = tk.IntVar(value=0)
        self.firmware_url_var = tk.StringVar(value="")
        self.firmware_md5_var = tk.StringVar(value="")
        self.firmware_expected_var = tk.StringVar(value="")
        self.firmware_expert_var = tk.BooleanVar(value=False)
        self.firmware_auto_check_var = tk.BooleanVar(value=bool(self.app_settings.get("firmware_auto_check", True)))
        self.firmware_monitor_cancel = False
        self.firmware_last_report = {}
        self.firmware_4pda_tree = None
        self.map_editor_status_var = tk.StringVar(value="Редактор карты: нажмите на комнату.")
        self.history_tree = None
        self.room_stats_tree = None
        self.maintenance_tree = None
        self.map_history_tree = None

        self._configure_modern_theme()
        self._build_top()
        self._build_tabs()
        self._build_statusbar()
        self.auto_config = self._load_auto_config()
        self._apply_auto_config_to_ui()
        if not self.update_manifest_url_var.get().strip():
            self.update_manifest_url_var.set(GITHUB_MANIFEST_URL)
        self._load_cached_map_snapshot()
        self.live_autosave_enabled = bool(self.auto_config.get("live_autosave", True))
        self._install_live_autosave_traces()
        self.after(80, self._apply_1080p_window)
        self.after(120, self._refresh_cloud_session_status)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(160, self._start_background_services)

        if RoidmiVacuumMiot is None:
            self.after(400, self._show_dependency_error)
        elif self.auto_config.get("auto_connect", False):
            self.after(1800, self.safe_autostart)

    def _apply_1080p_window(self):
        """Fit the GUI to the Windows work area, with 1920x1080 as the primary target."""
        try:
            sw = int(self.winfo_screenwidth())
            sh = int(self.winfo_screenheight())
            dpi = float(self.winfo_fpixels("1i"))
            self.ui_dpi = dpi
            scale_pct = int(round(dpi / 96.0 * 100))
            self.ui_screen_var.set(
                f"Экран: {sw}x{sh} | Windows DPI: {scale_pct}% | профиль UI: 1080p"
            )
            if os.name == "nt" and sw >= 1500 and sh >= 850:
                try:
                    self.state("zoomed")
                    return
                except Exception:
                    pass
            width = min(1720, max(1180, sw - 50))
            height = min(930, max(700, sh - 90))
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def _load_cached_map_snapshot(self):
        """Use the last downloaded real map immediately, before a new cloud refresh."""
        try:
            if LIVE_MAP_PNG_PATH.exists():
                self.dashboard_live_map_available = True
                self.dashboard_live_map_path = LIVE_MAP_PNG_PATH
                self.dashboard_live_map_status_var.set(
                    "Показана последняя сохранённая живая карта. Нажмите «Обновить карту» для свежей версии."
                )
            if LIVE_MAP_RAW_PATH.exists():
                self.last_raw_map = LIVE_MAP_RAW_PATH.read_bytes()
            if LIVE_MAP_ANALYSIS_PATH.exists():
                self.last_map_analysis = json.loads(
                    LIVE_MAP_ANALYSIS_PATH.read_text(encoding="utf-8")
                )
                if self.last_map_analysis.get("map_id") is not None:
                    self.current_map_id = self.last_map_analysis.get("map_id")
                    self.direct_room_map_id_var.set(str(self.current_map_id))
                route = self.last_map_analysis.get("recommended_route_names") or []
                if route:
                    self.map_optimization_status_var.set(
                        "Последний анализ карты: " + " -> ".join(route)
                    )
            if LAST_ROOMS_PATH.exists():
                try:
                    self.rooms_data = json.loads(LAST_ROOMS_PATH.read_text(encoding="utf-8-sig"))
                except Exception:
                    pass
            cached_info = LAST_MAP_INFO_PATH
            if cached_info.exists():
                try:
                    self.map_info_raw = json.loads(cached_info.read_text(encoding="utf-8"))
                except Exception:
                    pass
            self._refresh_dashboard()
        except Exception:
            pass

    def _tk_callback_exception(self, exc_type, exc_value, exc_tb):
        """Never let a Tk callback fail silently or close the application."""
        write_crash_report(
            exc_type, exc_value, exc_tb, "tkinter_callback"
        )
        self.statusbar_var.set(
            "Ошибка интерфейса перехвачена. См. CRASH_REPORT.txt."
        )
        try:
            messagebox.showerror(
                "Ошибка программы",
                f"{exc_type.__name__}: {exc_value}\n\n"
                "Программа оставлена открытой.\n"
                "Подробности сохранены в CRASH_REPORT.txt."
            )
        except Exception:
            pass

    def safe_autostart(self):
        """Run automatic connection only after the GUI is fully painted."""
        try:
            if os.environ.get("ROIDMI_NO_AUTOCONNECT") == "1":
                self.statusbar_var.set(
                    "Диагностический запуск: автоподключение отключено."
                )
                return
            if self.auto_config.get("auto_connect", False):
                self.auto_connect_all()
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            write_crash_report(
                exc_type, exc_value, exc_tb, "safe_autostart"
            )
            try:
                self.statusbar_var.set(
                    "Автоподключение не выполнено. Можно подключиться вручную."
                )
            except Exception:
                pass

    def open_user_profile(self):
        """Open USER_PROFILE.json with the Windows default application.

        If the profile does not yet exist, create/load it first.
        """
        try:
            profile = self._load_user_profile()
        except Exception as e:
            messagebox.showerror(
                "USER_PROFILE.json",
                f"Не удалось подготовить профиль:\n{e}"
            )
            return

        try:
            os.startfile(str(USER_PROFILE_PATH))
        except Exception:
            try:
                messagebox.showinfo(
                    "USER_PROFILE.json",
                    json.dumps(profile, ensure_ascii=False, indent=2)
                )
            except Exception as e:
                messagebox.showerror(
                    "USER_PROFILE.json",
                    f"Не удалось открыть профиль:\n{e}"
                )

    def _load_auto_config(self):
        if not AUTO_CONFIG_PATH.exists():
            return {}
        try:
            obj = json.loads(AUTO_CONFIG_PATH.read_text(encoding="utf-8-sig"))
            return obj if isinstance(obj, dict) else {}
        except Exception as e:
            self.after(300, lambda: messagebox.showwarning(
                "AUTO_CONFIG.json",
                f"Не удалось прочитать AUTO_CONFIG.json:\n{e}"
            ))
            return {}

    def _apply_auto_config_to_ui(self):
        cfg = self.auto_config or {}
        if cfg.get("ip"):
            self.ip_var.set(str(cfg["ip"]))
        if cfg.get("token"):
            self.token_var.set(str(cfg["token"]))
        if cfg.get("xiaomi_username"):
            self.cloud_user_var.set(str(cfg["xiaomi_username"]))
        if cfg.get("xiaomi_password"):
            self.cloud_pass_var.set(str(cfg["xiaomi_password"]))
        if cfg.get("xiaomi_region"):
            region = str(cfg["xiaomi_region"])
            if region in ("auto","ru","de","cn","us","sg","tw","in","i2"):
                self.cloud_country_var.set(region)

    def _default_user_profile(self):
        return {
            "model": MODEL,
            "properties": dict(OPTIMIZED_PROPERTIES),
            "timing": json.loads(json.dumps(OPTIMIZED_TIMING)),
            "forbid_mode": {
                "time": [79200, 28800, 1],
                "tz": 3,
                "tzs": 10800,
            },
            "room_order": list(OPTIMAL_ROOM_ORDER),
            "updated_at": datetime.now().astimezone().isoformat(),
        }

    def _load_user_profile(self):
        if USER_PROFILE_PATH.exists():
            try:
                obj = json.loads(
                    USER_PROFILE_PATH.read_text(encoding="utf-8-sig")
                )
                if isinstance(obj, dict) and obj.get("model") in (None, MODEL):
                    return obj
            except Exception as e:
                with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
                    f.write(
                        datetime.now().isoformat() +
                        f" PROFILE_READ_ERROR {e}\n"
                    )
        profile = self._default_user_profile()
        USER_PROFILE_PATH.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return profile

    def _write_user_profile(self, profile):
        profile = dict(profile or {})
        profile["model"] = MODEL
        profile["updated_at"] = datetime.now().astimezone().isoformat()
        tmp = USER_PROFILE_PATH.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        tmp.replace(USER_PROFILE_PATH)

    def _update_user_profile(
        self,
        status=None,
        timing=None,
        forbid_mode=None,
        room_order=None,
        property_values=None,
    ):
        profile = self._load_user_profile()
        props = dict(profile.get("properties") or {})

        if status:
            for key in OPTIMIZED_PROPERTIES.keys():
                if key in status and status.get(key) is not None:
                    props[key] = status.get(key)

        if property_values:
            for key, value in property_values.items():
                if key in OPTIMIZED_PROPERTIES:
                    props[key] = value

        profile["properties"] = props

        if timing is not None:
            profile["timing"] = self._normalize_json_obj(timing)
        elif status and status.get("timing") is not None:
            profile["timing"] = self._normalize_json_obj(
                status.get("timing")
            )

        if forbid_mode is not None:
            profile["forbid_mode"] = self._normalize_json_obj(forbid_mode)
        elif status and status.get("forbid_mode") is not None:
            profile["forbid_mode"] = self._normalize_json_obj(
                status.get("forbid_mode")
            )

        if room_order is not None:
            profile["room_order"] = [int(x) for x in room_order]

        self._write_user_profile(profile)
        return profile

    def _saved_profile_room_order(self):
        try:
            p = self._load_user_profile()
            order = p.get("room_order")
            if isinstance(order, list) and sorted(map(int, order)) == [1,2,3,4,5]:
                return [int(x) for x in order]
        except Exception:
            pass
        return list(OPTIMAL_ROOM_ORDER)

    @staticmethod
    def _private_24_network(ip_text):
        try:
            ip = ipaddress.ip_address(str(ip_text).strip())
            if not ip.is_private:
                return None
            return ipaddress.ip_network(f"{ip}/24", strict=False)
        except Exception:
            return None

    @staticmethod
    def _local_ipv4_addresses():
        found = set()
        try:
            host = socket.gethostname()
            for ip in socket.gethostbyname_ex(host)[2]:
                if ip and ":" not in ip:
                    found.add(ip)
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            found.add(s.getsockname()[0])
            s.close()
        except Exception:
            pass
        return sorted(found)

    @staticmethod
    def _miio_handshake_probe(ip, timeout=0.28):
        hello = bytes.fromhex(
            "21310020ffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(hello, (str(ip), 54321))
            data, addr = s.recvfrom(1024)
            if data and addr:
                return addr[0]
        except Exception:
            return None
        finally:
            try:
                s.close()
            except Exception:
                pass
        return None

    @staticmethod
    def _broadcast_miio(networks, timeout=0.9):
        hello = bytes.fromhex(
            "21310020ffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )
        found = set()
        for net in networks:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.settimeout(timeout)
                targets = [str(net.broadcast_address), "255.255.255.255"]
                for target in targets:
                    try:
                        s.sendto(hello, (target, 54321))
                    except Exception:
                        pass
                deadline = time.time() + timeout
                while time.time() < deadline:
                    try:
                        data, addr = s.recvfrom(1024)
                        if data and addr:
                            found.add(addr[0])
                    except socket.timeout:
                        break
                    except Exception:
                        break
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        return sorted(found)

    def _discovery_networks(self, vacuum_ip=None):
        nets = set()
        for raw in [vacuum_ip]:
            net = self._private_24_network(raw)
            if net is not None:
                nets.add(net)
        for raw in self._local_ipv4_addresses():
            net = self._private_24_network(raw)
            if net is not None:
                nets.add(net)
        return sorted(nets, key=lambda n: str(n))

    def _verify_vacuum_at_ip(self, ip, token):
        d = RoidmiVacuumMiot(str(ip), token, model=MODEL, timeout=1.4)
        # A single known ROIDMI property verifies both reachability and token.
        raw = d.get_property_by(3, 1)
        ok = False
        if isinstance(raw, list) and raw:
            item = raw[0]
            ok = isinstance(item, dict) and item.get("code", 0) == 0
        if not ok:
            raise RuntimeError("MIoT battery property verification failed")
        status = d.status().data
        return d, status

    def _discover_vacuum_sync(self, token, vacuum_ip=None):
        networks = self._discovery_networks(vacuum_ip)
        if not networks:
            raise RuntimeError("Не удалось определить локальную IPv4 сеть для поиска.")

        responsive = set(self._broadcast_miio(networks))
        checked = set()

        # Verify broadcast responders first.
        for ip in sorted(responsive):
            checked.add(ip)
            try:
                dev, status = self._verify_vacuum_at_ip(ip, token)
                return {
                    "ip": ip,
                    "device": dev,
                    "status": status,
                    "networks": [str(n) for n in networks],
                    "responders": sorted(responsive),
                    "method": "broadcast",
                }
            except Exception:
                pass

        # Fallback: fast /24 unicast handshake scan. This avoids assuming the old subnet.
        hosts = []
        for net in networks:
            hosts.extend(str(h) for h in net.hosts())
        with ThreadPoolExecutor(max_workers=80) as pool:
            futures = {
                pool.submit(self._miio_handshake_probe, ip, 0.24): ip
                for ip in hosts if ip not in checked
            }
            for fut in as_completed(futures):
                try:
                    got = fut.result()
                except Exception:
                    got = None
                if got:
                    responsive.add(got)

        for ip in sorted(responsive):
            if ip in checked:
                continue
            checked.add(ip)
            try:
                dev, status = self._verify_vacuum_at_ip(ip, token)
                return {
                    "ip": ip,
                    "device": dev,
                    "status": status,
                    "networks": [str(n) for n in networks],
                    "responders": sorted(responsive),
                    "method": "unicast-scan",
                }
            except Exception:
                pass

        raise RuntimeError(
            "ROIDMI EVE Plus не найден с текущим token. "
            f"Проверены сети: {', '.join(str(n) for n in networks)}. "
            f"MiIO-устройства, ответившие на handshake: {', '.join(sorted(responsive)) or 'нет'}."
        )

    def _save_discovered_vacuum_ip(self, ip):
        try:
            cfg = {}
            if AUTO_CONFIG_PATH.exists():
                cfg = json.loads(AUTO_CONFIG_PATH.read_text(encoding="utf-8-sig"))
                if not isinstance(cfg, dict):
                    cfg = {}
            cfg["ip"] = str(ip)
            cfg["model"] = MODEL
            AUTO_CONFIG_PATH.write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self.auto_config = cfg
        except Exception as e:
            with (ROOT / "discovery.log").open("a", encoding="utf-8") as f:
                f.write(datetime.now().isoformat() + f" SAVE_IP_ERROR {e}\n")

    def discover_vacuum(self):
        try:
            _, token = self.validate_connection()
        except Exception:
            # validate_connection requires current IP. For discovery only token must be valid.
            token = self.token_var.get().strip().lower()
            if len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
                messagebox.showerror("Автопоиск", "Введите корректный 32-символьный token ROIDMI.")
                return

        vacuum_ip = self.ip_var.get().strip()
        self.discovery_status_var.set("Поиск MiIO-устройств в локальной сети...")

        def task():
            return self._discover_vacuum_sync(token, vacuum_ip)

        def done(result):
            self.device = result["device"]
            self.ip_var.set(result["ip"])
            self._save_discovered_vacuum_ip(result["ip"])
            self.discovery_status_var.set(
                f"ROIDMI найден: {result['ip']} | метод: {result['method']} | "
                f"сети: {', '.join(result['networks'])}"
            )
            with (ROOT / "discovery.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " " +
                    json.dumps(
                        {
                            "found_ip": result["ip"],
                            "method": result["method"],
                            "networks": result["networks"],
                            "responders": result["responders"],
                        },
                        ensure_ascii=False
                    ) + "\n"
                )
            self.on_status(result["status"])

        self.async_run(task, done, "Автопоиск ROIDMI EVE Plus...")

    def _connect_with_recovery(self, ip, token):
        try:
            d = RoidmiVacuumMiot(ip, token, model=MODEL, timeout=2)
            status = d.status().data
            return {
                "ip": ip, "device": d, "status": status,
                "auto_found": False, "method": "configured-ip"
            }
        except Exception as e:
            if "Unable to discover the device" not in str(e):
                raise
        found = self._discover_vacuum_sync(token, ip)
        found["auto_found"] = True
        return found

    def auto_connect_all(self):
        """Connect and automatically recover a changed DHCP IP when necessary."""
        if self.busy:
            return
        try:
            ip, token = self.validate_connection()
        except Exception as e:
            messagebox.showerror("Автовход", str(e))
            return
        def task():
            return self._connect_with_recovery(ip, token)

        def done(result):
            self.device = result["device"]
            if result["ip"] != self.ip_var.get().strip():
                self.ip_var.set(result["ip"])
                self._save_discovered_vacuum_ip(result["ip"])
            if result.get("auto_found"):
                self.discovery_status_var.set(
                    f"IP восстановлен автоматически: {result['ip']} ({result.get('method')})"
                )
            self.on_status(result["status"])
            self.statusbar_var.set("Автовход: подключение выполнено.")
            if self.auto_config.get("auto_apply_saved_profile", True):
                self.after(150, self.auto_apply_saved_profile_silent)
            elif self.auto_config.get("auto_fetch_rooms", False):
                self.after(250, self.fetch_rooms)

        self.async_run(task, done, "Автовход: подключение / поиск ROIDMI...")

    def _install_live_autosave_traces(self):
        """Bind UI variables to debounced writes to the actual robot."""
        general_vars = [
            self.fan_var, self.sweep_var, self.water_var, self.path_var,
            self.station_freq_var, self.volume_var, self.auto_boost_var,
            self.double_clean_var, self.led_var, self.lidar_var,
            self.station_led_var, self.station_key_var, self.mute_var,
        ]
        for var in general_vars:
            var.trace_add("write", self._schedule_live_general_save)

        for var in [
            self.dnd_start_h, self.dnd_start_m,
            self.dnd_end_h, self.dnd_end_m,
        ]:
            var.trace_add("write", self._schedule_live_dnd_save)

        self.room_order_var.trace_add(
            "write", self._schedule_live_room_order_save
        )

    def _cancel_job(self, attr):
        job = getattr(self, attr, None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
            setattr(self, attr, None)

    def _schedule_live_general_save(self, *_):
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        self._cancel_job("live_general_job")
        self.live_general_job = self.after(
            650, self._live_save_general_settings
        )
        self.statusbar_var.set("AutoSave: изменение параметров ожидает записи...")

    def _schedule_live_schedule_save(self):
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        self._cancel_job("live_schedule_job")
        self.live_schedule_job = self.after(
            700, self._live_save_schedule
        )
        self.statusbar_var.set("AutoSave: расписание ожидает записи...")

    def _schedule_live_dnd_save(self, *_):
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        self._cancel_job("live_dnd_job")
        self.live_dnd_job = self.after(
            900, self._live_save_dnd
        )
        self.statusbar_var.set("AutoSave: DND ожидает записи...")

    def _schedule_live_room_order_save(self, *_):
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        self._cancel_job("live_room_order_job")
        self.live_room_order_job = self.after(
            1100, self._live_save_room_order
        )
        self.statusbar_var.set("AutoSave: порядок комнат ожидает записи...")

    def _general_values_from_ui(self):
        return {
            "fanspeed_mode": FAN[self.fan_var.get()],
            "sweep_type": SWEEP_TYPE[self.sweep_var.get()],
            "water_level": WATER[self.water_var.get()],
            "path_mode": PATH_MODE[self.path_var.get()],
            "work_station_freq": STATION_FREQ[self.station_freq_var.get()],
            "volume": max(0, min(100, int(self.volume_var.get()))),
            "auto_boost": bool(self.auto_boost_var.get()),
            "double_clean": bool(self.double_clean_var.get()),
            "led_switch": bool(self.led_var.get()),
            "lidar_collision": bool(self.lidar_var.get()),
            "station_led": bool(self.station_led_var.get()),
            "station_key": bool(self.station_key_var.get()),
            "mute": bool(self.mute_var.get()),
        }

    @staticmethod
    def _values_equal(current, wanted):
        if isinstance(wanted, bool):
            return bool(current) == wanted
        return current == wanted

    def _live_save_general_settings(self):
        self.live_general_job = None
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        if self.busy:
            self.live_general_job = self.after(
                700, self._live_save_general_settings
            )
            return
        try:
            values = self._general_values_from_ui()
        except Exception:
            # Spinbox may briefly contain an incomplete value while typing.
            self.live_general_job = self.after(
                800, self._live_save_general_settings
            )
            return

        def task():
            d = self.ensure_device()
            before = d.status().data
            changed = {
                k: v for k, v in values.items()
                if not self._values_equal(before.get(k), v)
            }
            results = {"changed": sorted(changed)}
            if changed:
                results["backup"] = str(
                    self.backup_data(before, "before_live_settings")
                )
                for key, value in changed.items():
                    try:
                        results[key] = d.set_property(key, value)
                    except Exception as e:
                        results[key] = f"ERROR: {e}"
            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)
            changed = results.get("changed") or []
            errors = {
                k:v for k,v in results.items()
                if isinstance(v, str) and v.startswith("ERROR:")
            }
            self._write_last_applied(after, results=results)
            self._update_user_profile(
                status=after,
                property_values=values,
            )
            with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " GENERAL " +
                    json.dumps(results, ensure_ascii=False, default=str) + "\n"
                )
            if errors:
                self.statusbar_var.set(
                    "AutoSave: часть параметров не записалась. См. autosave.log."
                )
            elif changed:
                self.statusbar_var.set(
                    "AutoSave: параметры записаны в пылесос и перечитаны."
                )
            else:
                self.statusbar_var.set(
                    "AutoSave: изменений для записи нет."
                )

        self.async_run(task, done, "AutoSave: сохраняю параметры...")

    def _timing_payload_from_editor(self):
        payload = {
            k:v for k,v in self.current_timing.items()
            if not str(k).startswith("_")
        }
        if "tz" not in payload or "tzs" not in payload:
            tz, tzs = local_tz_payload()
            payload["tz"] = tz
            payload["tzs"] = tzs
        return payload

    def _live_save_schedule(self):
        self.live_schedule_job = None
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        if self.busy:
            self.live_schedule_job = self.after(
                700, self._live_save_schedule
            )
            return
        payload = self._timing_payload_from_editor()

        def task():
            d = self.ensure_device()
            before = d.status().data
            current = self._normalize_json_obj(before.get("timing"))
            results = {"changed": current != payload}
            if current != payload:
                results["backup"] = str(
                    self.backup_data(before, "before_live_timing")
                )
                raw = json.dumps(
                    payload, ensure_ascii=False, separators=(",",":")
                )
                results["timing"] = d.set_timing(raw)
            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)
            self._write_last_applied(after, results=results)
            self._update_user_profile(
                status=after,
                timing=payload,
            )
            with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " TIMING " +
                    json.dumps(results, ensure_ascii=False, default=str) + "\n"
                )
            self.statusbar_var.set(
                "AutoSave: расписание сохранено в пылесосе."
                if results.get("changed")
                else "AutoSave: расписание уже совпадает."
            )

        self.async_run(task, done, "AutoSave: сохраняю расписание...")

    def _live_save_dnd(self):
        self.live_dnd_job = None
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return
        if self.busy:
            self.live_dnd_job = self.after(700, self._live_save_dnd)
            return
        try:
            h1 = int(self.dnd_start_h.get())
            m1 = int(self.dnd_start_m.get())
            h2 = int(self.dnd_end_h.get())
            m2 = int(self.dnd_end_m.get())
        except Exception:
            self.live_dnd_job = self.after(800, self._live_save_dnd)
            return
        if not (0 <= h1 <= 23 and 0 <= h2 <= 23 and
                0 <= m1 <= 59 and 0 <= m2 <= 59):
            return

        wanted = [h1*3600+m1*60, h2*3600+m2*60, 1]

        def task():
            d = self.ensure_device()
            before = d.status().data
            current_obj = self._normalize_json_obj(before.get("forbid_mode"))
            current = (
                current_obj.get("time")
                if isinstance(current_obj, dict) else None
            )
            changed = current != wanted
            results = {"changed": changed}
            if changed:
                results["backup"] = str(
                    self.backup_data(before, "before_live_dnd")
                )
                results["forbid_mode"] = d.set_dnd(h1, m1, h2, m2)
            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)
            self._write_last_applied(after, results=results)
            self._update_user_profile(
                status=after,
                forbid_mode={
                    "time": wanted,
                    "tz": 3,
                    "tzs": 10800,
                },
            )
            with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " DND " +
                    json.dumps(results, ensure_ascii=False, default=str) + "\n"
                )
            self.statusbar_var.set(
                "AutoSave: DND сохранён."
                if results.get("changed")
                else "AutoSave: DND уже совпадает."
            )

        self.async_run(task, done, "AutoSave: сохраняю DND...")

    def _live_save_room_order(self):
        """Persist requested room order locally only.

        The public MIoT spec exposes area-order but does not document the internal
        JSON schema for its string parameter. The previously inferred autoArea-list
        payload is rejected by this v60 firmware with -704220035 (action argument
        error), so v14.1 intentionally does NOT send area-order to the device/cloud.
        """
        self.live_room_order_job = None
        if self.suspend_live_autosave or not self.live_autosave_enabled:
            return

        try:
            order = self._room_order()
        except Exception as e:
            self.profile_status_var.set(f"Порядок комнат не сохранён: {e}")
            return

        profile = self._update_user_profile(room_order=order)

        with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
            f.write(
                datetime.now().isoformat() + " ROOM_ORDER_LOCAL_ONLY " +
                json.dumps({"order": order}, ensure_ascii=False) + "\n"
            )

        self.profile_status_var.set(
            "Порядок комнат сохранён в USER_PROFILE.json: " +
            " → ".join(map(str, order)) +
            ". В пылесос не отправлен: формат area-order вашей прошивки не подтверждён."
        )
        self.statusbar_var.set(
            "AutoSave: порядок комнат сохранён локально; устройство не изменялось."
        )

    def _show_dependency_error(self):
        messagebox.showerror(
            "python-miio не установлен",
            "Не удалось загрузить библиотеку python-miio.\n\n"
            "Запускайте программу через START.bat. Он создаст локальное окружение "
            "и установит необходимую библиотеку.\n\n"
            f"Техническая ошибка:\n{IMPORT_ERROR}"
        )


    def _configure_modern_theme(self):
        # Segoe UI at 10pt is the Windows-native density for a 1920x1080 work area.
        # DPI awareness keeps it crisp at 100/125/150% Windows scaling.
        try:
            self.ui_dpi = float(self.winfo_fpixels("1i"))
            self.tk.call("tk", "scaling", max(1.0, self.ui_dpi / 72.0))
        except Exception:
            self.ui_dpi = 96.0

        try:
            named_fonts = {
                "TkDefaultFont": ("Segoe UI", 10, "normal"),
                "TkTextFont": ("Segoe UI", 10, "normal"),
                "TkMenuFont": ("Segoe UI", 9, "normal"),
                "TkHeadingFont": ("Segoe UI Semibold", 10, "bold"),
                "TkCaptionFont": ("Segoe UI Semibold", 10, "bold"),
                "TkSmallCaptionFont": ("Segoe UI", 9, "normal"),
                "TkIconFont": ("Segoe UI", 9, "normal"),
                "TkTooltipFont": ("Segoe UI", 9, "normal"),
                "TkFixedFont": ("Consolas", 9, "normal"),
            }
            for name, (family, size, weight) in named_fonts.items():
                try:
                    f = tkfont.nametofont(name)
                    f.configure(family=family, size=size, weight=weight)
                except Exception:
                    pass
        except Exception:
            pass

        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*Menu.font", ("Segoe UI", 9))
        self.configure(bg="#0b1220")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        base_bg = "#0b1220"
        panel_bg = "#121b2e"
        card_bg = "#16233a"
        elevated_bg = "#1b2c47"
        text_main = "#eef4ff"
        text_muted = "#9fb4d1"
        accent = "#3b82f6"
        accent_2 = "#8b5cf6"
        border = "#2a3b5e"
        ok = "#22c55e"

        style.configure(".", background=base_bg, foreground=text_main, fieldbackground=panel_bg, font=("Segoe UI", 10))
        style.configure("TFrame", background=base_bg)
        style.configure("Card.TFrame", background=card_bg)
        style.configure("Panel.TFrame", background=panel_bg)
        style.configure("Toolbar.TFrame", background=elevated_bg)

        style.configure("TLabel", background=base_bg, foreground=text_main, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=card_bg, foreground=text_muted, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=base_bg, foreground=text_main, font=("Segoe UI Semibold", 16))
        style.configure("SubHeader.TLabel", background=base_bg, foreground=text_muted, font=("Segoe UI", 9))
        style.configure("StatusOk.TLabel", background=panel_bg, foreground=ok, font=("Segoe UI Semibold", 10))

        style.configure("Section.TLabelframe", background=card_bg, foreground=text_main, borderwidth=1, relief="solid")
        style.configure("Section.TLabelframe.Label", background=card_bg, foreground=text_main, font=("Segoe UI Semibold", 10))
        style.configure("TLabelframe", background=card_bg, foreground=text_main)
        style.configure("TLabelframe.Label", background=card_bg, foreground=text_main, font=("Segoe UI Semibold", 10))

        style.configure("TButton", background=panel_bg, foreground=text_main, bordercolor=border,
                        relief="flat", padding=(9, 6), font=("Segoe UI", 9))
        style.map("TButton",
                  background=[("active", elevated_bg), ("pressed", accent)],
                  foreground=[("disabled", "#6f809d")])
        style.configure("Accent.TButton", background=accent, foreground="white",
                        padding=(11, 7), font=("Segoe UI Semibold", 9))
        style.map("Accent.TButton", background=[("active", "#2563eb"), ("pressed", "#1d4ed8")])
        style.configure("Accent2.TButton", background=accent_2, foreground="white",
                        padding=(11, 7), font=("Segoe UI Semibold", 9))
        style.map("Accent2.TButton", background=[("active", "#7c3aed"), ("pressed", "#6d28d9")])

        style.configure("Treeview", background=panel_bg, fieldbackground=panel_bg, foreground=text_main,
                        bordercolor=border, rowheight=25, font=("Segoe UI", 9))
        style.map("Treeview", background=[("selected", accent)], foreground=[("selected", "white")])
        style.configure("Treeview.Heading", background=elevated_bg, foreground=text_main,
                        relief="flat", font=("Segoe UI Semibold", 9))

        style.configure("TEntry", fieldbackground=panel_bg, foreground=text_main, insertcolor=text_main,
                        padding=(5, 4), font=("Segoe UI", 10))
        style.configure("TCombobox", fieldbackground=panel_bg, foreground=text_main,
                        padding=(4, 3), font=("Segoe UI", 9))
        style.map("TCombobox", fieldbackground=[("readonly", panel_bg)], foreground=[("readonly", text_main)])
        style.configure("TSpinbox", fieldbackground=panel_bg, foreground=text_main, font=("Segoe UI", 9))
        style.configure("TCheckbutton", background=card_bg, foreground=text_main, font=("Segoe UI", 9))
        style.configure("TRadiobutton", background=card_bg, foreground=text_main, font=("Segoe UI", 9))
        style.configure("Horizontal.TSeparator", background=border)

        style.configure("TNotebook", background=base_bg, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure("TNotebook.Tab", background=panel_bg, foreground=text_muted,
                        padding=(10, 7), font=("Segoe UI Semibold", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", elevated_bg), ("active", card_bg)],
                  foreground=[("selected", text_main), ("active", text_main)])


    def _build_top(self):
        box = ttk.LabelFrame(self, text="Подключение к ROIDMI EVE Plus", style="Section.TLabelframe")
        box.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Label(box, text="IP:").grid(row=0, column=0, padx=(8, 4), pady=5, sticky="e")
        self.ip_var = tk.StringVar()
        ttk.Entry(box, textvariable=self.ip_var, width=16).grid(row=0, column=1, padx=4, sticky="w")

        ttk.Label(box, text="Token:").grid(row=0, column=2, padx=(10, 4), sticky="e")
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(box, textvariable=self.token_var, width=34, show="•")
        self.token_entry.grid(row=0, column=3, padx=4, sticky="ew")

        self.show_token_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            box, text="Показать", variable=self.show_token_var,
            command=lambda: self.token_entry.configure(show="" if self.show_token_var.get() else "•")
        ).grid(row=0, column=4, padx=4)

        ttk.Button(
            box, text="ПОДКЛЮЧИТЬСЯ", style="Accent.TButton",
            command=self.connect_and_read
        ).grid(row=0, column=5, padx=4)
        ttk.Button(
            box, text="НАЙТИ ROIDMI",
            command=self.discover_vacuum
        ).grid(row=0, column=6, padx=4)

        tools = ttk.Frame(box, style="Card.TFrame")
        tools.grid(row=1, column=0, columnspan=7, sticky="ew", padx=7, pady=(2, 4))
        ttk.Button(tools, text="Автовход", command=self.auto_connect_all).pack(side="left", padx=3)
        ttk.Button(tools, text="Где взять token", command=lambda: webbrowser.open(TOKEN_EXTRACTOR_URL)).pack(side="left", padx=3)
        ttk.Button(tools, text="MIoT-спецификация", command=lambda: webbrowser.open(MIOT_SPEC_URL)).pack(side="left", padx=3)
        ttk.Label(tools, textvariable=self.ui_screen_var, style="Muted.TLabel").pack(side="right", padx=6)

        ttk.Label(
            box,
            textvariable=self.discovery_status_var,
            foreground="#4f9cff"
        ).grid(row=2, column=0, columnspan=7, padx=8, pady=(0, 6), sticky="w")

        box.grid_columnconfigure(3, weight=1)


    def _build_tabs(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(4, 5))

        self.tab_dashboard = ttk.Frame(self.nb)
        self.tab_control = ttk.Frame(self.nb)
        self.tab_settings = ttk.Frame(self.nb)
        self.tab_voice = ttk.Frame(self.nb)
        self.tab_room_modes = ttk.Frame(self.nb)
        self.tab_capabilities = ttk.Frame(self.nb)
        self.tab_schedule = ttk.Frame(self.nb)
        self.tab_rooms = ttk.Frame(self.nb)
        self.tab_profiles = ttk.Frame(self.nb)
        self.tab_dnd = ttk.Frame(self.nb)
        self.tab_raw = ttk.Frame(self.nb)
        self.tab_sources = ttk.Frame(self.nb)
        self.tab_export = ttk.Frame(self.nb)
        self.tab_center = ttk.Frame(self.nb)
        self.tab_firmware = ttk.Frame(self.nb)

        self.nb.add(self.tab_dashboard, text="Панель")
        self.nb.add(self.tab_control, text="Управление")
        self.nb.add(self.tab_settings, text="Настройки")
        self.nb.add(self.tab_voice, text="Голос")
        self.nb.add(self.tab_room_modes, text="Режимы комнат")
        self.nb.add(self.tab_capabilities, text="Возможности")
        self.nb.add(self.tab_schedule, text="Расписание")
        self.nb.add(self.tab_rooms, text="Комнаты/карта")
        self.nb.add(self.tab_profiles, text="Профили")
        self.nb.add(self.tab_dnd, text="DND")
        self.nb.add(self.tab_raw, text="Диагностика")
        self.nb.add(self.tab_sources, text="MIoT/GitHub")
        self.nb.add(self.tab_export, text="Экспорт")
        self.nb.add(self.tab_center, text="Интеллект")
        self.nb.add(self.tab_firmware, text="Прошивка")

        self._build_control_tab()
        self._build_settings_tab()
        self._build_voice_tab()
        self._build_schedule_tab()
        self._build_rooms_tab()
        self._build_room_modes_tab()
        self._build_capabilities_tab()
        self._build_profiles_tab()
        self._build_dnd_tab()
        self._build_raw_tab()
        self._build_sources_tab()
        self._build_export_tab()
        self._build_center_tab()
        self._build_firmware_tab()
        self._build_dashboard_tab()


    def _build_dashboard_tab(self):
        root = ttk.Frame(self.tab_dashboard)
        root.pack(fill="both", expand=True, padx=10, pady=9)

        head = ttk.Frame(root, style="Toolbar.TFrame")
        head.pack(fill="x", pady=(0, 8))
        ttk.Label(head, text="ROIDMI EVE Plus Control", style="Header.TLabel").grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        ttk.Label(head, text="Эргономичная панель прямого управления по LAN / Xiaomi Cloud", style="SubHeader.TLabel").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
        status = ttk.Frame(head, style="Toolbar.TFrame")
        status.grid(row=0, column=1, rowspan=2, sticky="e", padx=16)
        ttk.Label(status, textvariable=self.dashboard_status_var, style="StatusOk.TLabel").pack(anchor="e")
        ttk.Label(status, textvariable=self.dashboard_substatus_var, style="SubHeader.TLabel").pack(anchor="e")
        head.grid_columnconfigure(0, weight=1)

        content = ttk.Frame(root)
        content.pack(fill="both", expand=True)
        left = ttk.Frame(content)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(content)
        right.pack(side="left", fill="y", padx=(12, 0))

        map_card = ttk.LabelFrame(left, text="Карта квартиры", style="Section.TLabelframe")
        map_card.pack(fill="both", expand=True)
        info_row = ttk.Frame(map_card, style="Card.TFrame")
        info_row.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(info_row, textvariable=self.dashboard_map_meta_var, style="Muted.TLabel").pack(side="left")
        ttk.Button(info_row, text="Обновить карту", command=self.fetch_rooms).pack(side="right", padx=4)
        ttk.Button(info_row, text="Обновить состояние", command=self.read_status).pack(side="right", padx=4)

        mode_row = ttk.Frame(map_card, style="Card.TFrame")
        mode_row.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Label(mode_row, text="Вид карты:", style="Muted.TLabel").pack(side="left")
        ttk.Button(mode_row, text="Живая Xiaomi", style="Accent.TButton", command=lambda: self.set_dashboard_map_mode("live")).pack(side="left", padx=(8, 4))
        ttk.Button(mode_row, text="Скриншот", command=lambda: self.set_dashboard_map_mode("real")).pack(side="left", padx=4)
        ttk.Button(mode_row, text="Схема", command=lambda: self.set_dashboard_map_mode("schematic")).pack(side="left", padx=4)
        ttk.Button(mode_row, text="Редактор карты", command=self.open_map_editor_help).pack(side="right", padx=4)
        ttk.Button(mode_row, text="Скачать карту ZIP", command=self.export_live_map_bundle).pack(side="right", padx=4)
        ttk.Button(mode_row, text="Загрузить PNG/JPG", command=self.load_real_map_image).pack(side="right", padx=4)
        ttk.Button(mode_row, text="Встроенный скриншот", command=self.reset_real_map_image).pack(side="right", padx=4)
        ttk.Label(map_card, textvariable=self.dashboard_live_map_status_var, style="Muted.TLabel").pack(anchor="w", padx=12, pady=(0, 4))

        map_body = ttk.Frame(map_card, style="Card.TFrame")
        map_body.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        self.dashboard_map_canvas = tk.Canvas(
            map_body, width=820, height=365, bg="#0f172a",
            highlightthickness=1, highlightbackground="#263956"
        )
        self.dashboard_map_canvas.pack(fill="both", expand=True)
        self.dashboard_map_canvas.bind("<Button-1>", self._on_dashboard_map_click)
        self._draw_dashboard_map()

        lower = ttk.Frame(left)
        lower.pack(fill="x", pady=(12, 0))

        rooms_card = ttk.LabelFrame(lower, text="Комнаты", style="Section.TLabelframe")
        rooms_card.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(rooms_card, text="Выберите помещения для локальной уборки по сегментам.", style="Muted.TLabel").pack(anchor="w", padx=10, pady=(10, 2))
        rooms_toolbar = ttk.Frame(rooms_card, style="Card.TFrame")
        rooms_toolbar.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(rooms_toolbar, text="Выбрать все", command=self._select_all_rooms_dashboard).pack(side="left", padx=(0, 6))
        ttk.Button(rooms_toolbar, text="Сбросить", command=self._clear_all_rooms_dashboard).pack(side="left", padx=6)
        ttk.Button(rooms_toolbar, text="Убрать комнаты", style="Accent.TButton", command=self.start_selected_rooms_direct).pack(side="right")

        for rid in [1, 2, 3, 4, 5]:
            row = ttk.Frame(rooms_card, style="Card.TFrame")
            row.pack(fill="x", padx=10, pady=4)
            ttk.Checkbutton(
                row,
                text=f"Room {rid}: {self.dashboard_room_names[rid]}",
                variable=self.room_select_vars[rid],
                command=self._draw_dashboard_map
            ).pack(side="left", anchor="w")
            ttk.Label(row, text=self._room_cleanliness_text(rid), style="Muted.TLabel").pack(side="right")

        sched_card = ttk.LabelFrame(lower, text="Расписание", style="Section.TLabelframe")
        sched_card.pack(side="left", fill="both", expand=True, padx=(6, 0))
        toolbar = ttk.Frame(sched_card, style="Card.TFrame")
        toolbar.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Label(toolbar, text="Активные сценарии уборки", style="Muted.TLabel").pack(side="left")
        ttk.Button(toolbar, text="Перейти к расписанию", command=lambda: self.nb.select(self.tab_schedule)).pack(side="right")
        self.dashboard_schedule_list = tk.Listbox(
            sched_card, height=6, bg="#121b2e", fg="#eef4ff",
            selectbackground="#2563eb", relief="flat", activestyle="none",
            highlightthickness=1, highlightbackground="#263956"
        )
        self.dashboard_schedule_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        control_card = ttk.LabelFrame(right, text="Управление", style="Section.TLabelframe")
        control_card.pack(fill="x")
        btns = ttk.Frame(control_card, style="Card.TFrame")
        btns.pack(fill="x", padx=10, pady=10)
        ttk.Button(btns, text="Начать уборку", style="Accent.TButton", command=lambda: self.run_action("start")).grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(btns, text="Стоп", command=lambda: self.run_action("stop")).grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Button(btns, text="На базу", command=lambda: self.run_action("home")).grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(btns, text="Найти робот", style="Accent2.TButton", command=lambda: self.run_action("identify")).grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        ttk.Button(btns, text="Сбор пыли", command=lambda: self.run_action("start_dust")).grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        ttk.Button(btns, text="Голос робота", command=lambda: self.nb.select(self.tab_voice)).grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))
        ttk.Button(btns, text="Режимы по комнатам", style="Accent2.TButton", command=lambda: self.nb.select(self.tab_room_modes)).grid(row=4, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))
        ttk.Button(btns, text="Интеллект / история", command=lambda: self.nb.select(self.tab_center)).grid(row=5, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 8))
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)

        settings_card = ttk.LabelFrame(right, text="Быстрые параметры", style="Section.TLabelframe")
        settings_card.pack(fill="x", pady=(12, 0))
        quick = ttk.Frame(settings_card, style="Card.TFrame")
        quick.pack(fill="x", padx=10, pady=10)
        ttk.Label(quick, text="Мощность", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(quick, textvariable=self.fan_var, values=list(FAN.keys()), state="readonly", width=24).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Label(quick, text="Вода", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(quick, textvariable=self.water_var, values=list(WATER.keys()), state="readonly", width=24).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Label(quick, text="Тип уборки", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Combobox(quick, textvariable=self.sweep_var, values=list(SWEEP_TYPE.keys()), state="readonly", width=24).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Label(quick, text="Маршрут", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Combobox(quick, textvariable=self.path_var, values=list(PATH_MODE.keys()), state="readonly", width=24).grid(row=3, column=1, sticky="ew", padx=8)
        ttk.Checkbutton(quick, text="Усиление на ковре", variable=self.auto_boost_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 3))
        ttk.Checkbutton(quick, text="LiDAR collision", variable=self.lidar_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Button(quick, text="Применить параметры", style="Accent.TButton", command=self.apply_settings).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 2))
        quick.grid_columnconfigure(1, weight=1)

        state_card = ttk.LabelFrame(right, text="Состояние и расходники", style="Section.TLabelframe")
        state_card.pack(fill="both", expand=True, pady=(12, 0))
        top_state = ttk.Frame(state_card, style="Card.TFrame")
        top_state.pack(fill="x", padx=10, pady=(10, 8))
        ttk.Label(top_state, textvariable=self.dashboard_device_var).pack(anchor="w")
        ttk.Label(top_state, textvariable=self.dashboard_ip_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(top_state, textvariable=self.dashboard_token_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(top_state, textvariable=self.dashboard_rooms_var, style="Muted.TLabel", wraplength=390, justify="left").pack(anchor="w", pady=(4, 0))

        meta = ttk.Frame(state_card, style="Card.TFrame")
        meta.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Label(meta, text="Аккумулятор:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(meta, textvariable=self.dashboard_battery_var).grid(row=0, column=1, sticky="w", padx=10)
        ttk.Label(meta, text="Ошибка:", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(meta, textvariable=self.dashboard_error_var).grid(row=1, column=1, sticky="w", padx=10)

        ttk.Label(state_card, text="Статус", style="Muted.TLabel").pack(anchor="w", padx=10)
        self.dashboard_status_lines = tk.Text(
            state_card, height=10, bg="#121b2e", fg="#eef4ff",
            relief="flat", wrap="word", highlightthickness=1,
            highlightbackground="#263956"
        )
        self.dashboard_status_lines.pack(fill="both", expand=True, padx=10, pady=(4, 8))
        self.dashboard_status_lines.insert("1.0", "После чтения состояния здесь появится сводка по устройству.\n")
        self.dashboard_status_lines.configure(state="disabled")

        ttk.Label(state_card, text="Расходники", style="Muted.TLabel").pack(anchor="w", padx=10)
        self.dashboard_consumables_lines = tk.Text(
            state_card, height=8, bg="#121b2e", fg="#eef4ff",
            relief="flat", wrap="word", highlightthickness=1,
            highlightbackground="#263956"
        )
        self.dashboard_consumables_lines.pack(fill="both", expand=False, padx=10, pady=(4, 10))
        self.dashboard_consumables_lines.insert("1.0", "Нет данных по расходникам.\n")
        self.dashboard_consumables_lines.configure(state="disabled")

        self._refresh_dashboard()

    def _room_cleanliness_text(self, rid):
        if rid in (1, 3):
            return "Высокая загрязнённость"
        if rid == 4:
            return "Средняя загрязнённость"
        return "Низкая загрязнённость"

    def _select_all_rooms_dashboard(self):
        for rid in self.room_select_vars:
            self.room_select_vars[rid].set(True)
        self._draw_dashboard_map()

    def _clear_all_rooms_dashboard(self):
        for rid in self.room_select_vars:
            self.room_select_vars[rid].set(False)
        self._draw_dashboard_map()

    def set_dashboard_map_mode(self, mode):
        self.dashboard_map_mode_var.set(mode)
        self._draw_dashboard_map()

    def load_real_map_image(self):
        path = filedialog.askopenfilename(
            title="Выберите реальную карту / скриншот Xiaomi",
            filetypes=[
                ("Изображения", "*.png;*.jpg;*.jpeg;*.bmp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg;*.jpeg"),
                ("Все файлы", "*.*"),
            ]
        )
        if not path:
            return
        dst = ROOT / "assets" / "real_map_user.png"
        dst.parent.mkdir(exist_ok=True)
        try:
            shutil.copyfile(path, dst)
            self.dashboard_real_map_path = dst
            self.dashboard_real_map_source_var.set(f"Реальная карта: {dst.name}")
            self.dashboard_map_mode_var.set("real")
            self._draw_dashboard_map()
            self.statusbar_var.set("Реальная карта загружена.")
        except Exception as e:
            messagebox.showerror("Реальная карта", f"Не удалось загрузить изображение:\n{e}")

    def reset_real_map_image(self):
        self.dashboard_real_map_path = ROOT / "assets" / "real_map_reference.png"
        self.dashboard_real_map_source_var.set("Локальный скриншот Xiaomi (не живая карта)")
        self.dashboard_map_mode_var.set("real")
        self._draw_dashboard_map()

    def _draw_dashboard_map_schematic(self):
        c = self.dashboard_map_canvas
        if c is None:
            return
        c.delete("all")
        W = int(c.winfo_width() or 650)
        H = int(c.winfo_height() or 430)
        c.create_rectangle(0, 0, W, H, fill="#0f172a", outline="#0f172a")
        step = 24
        for x in range(0, W, step):
            c.create_line(x, 0, x, H, fill="#13213a")
        for y in range(0, H, step):
            c.create_line(0, y, W, y, fill="#13213a")

        rooms = {
            2: (90, 55, 345, 200, "#68d391"),
            5: (382, 45, 500, 205, "#c4b5fd"),
            4: (125, 230, 305, 398, "#7dd3fc"),
            3: (352, 218, 528, 327, "#fcd34d"),
            1: (360, 335, 483, 430, "#fda4af"),
        }
        c.create_rectangle(330, 186, 392, 228, fill="#111b30", outline="#111b30")
        c.create_rectangle(305, 280, 358, 318, fill="#111b30", outline="#111b30")
        self.dashboard_room_box_refs = {}
        self.dashboard_room_label_refs = {}
        for rid, (x1, y1, x2, y2, fill) in rooms.items():
            selected = bool(self.room_select_vars.get(rid) and self.room_select_vars[rid].get())
            outline = "#ffffff" if selected else "#8ea4c6"
            width = 3 if selected else 1
            rect = c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)
            label = c.create_text(
                (x1+x2)//2, (y1+y2)//2,
                text=self.dashboard_room_names.get(rid, f"Room {rid}"),
                fill="#1f2937", font=("Segoe UI Semibold", 11)
            )
            self.dashboard_room_box_refs[rid] = rect
            self.dashboard_room_label_refs[rid] = label

        c.create_oval(424, 182, 446, 204, fill="#38bdf8", outline="white", width=2)
        c.create_text(435, 193, text="R", fill="white", font=("Segoe UI", 9, "bold"))
        c.create_rectangle(420, 70, 452, 102, fill="#27364f", outline="#93c5fd")
        c.create_text(436, 86, text="DOC", fill="#dbeafe", font=("Segoe UI", 8, "bold"))
        c.create_text(16, 14, anchor="nw", text="Условная схема квартиры", fill="#9fb4d1", font=("Segoe UI", 10))
        c.create_text(W - 14, H - 14, anchor="se", text="≈ 45 м²", fill="#9fb4d1", font=("Segoe UI", 10))
        c.create_text(16, H - 14, anchor="sw", text=self.dashboard_map_meta_var.get(), fill="#9fb4d1", font=("Segoe UI", 9))

    def _build_roidmi_live_map_png(self, raw_map):
        if RoidmiMapDataParser is None:
            raise RuntimeError(
                "Не установлен пакет vacuum-map-parser-roidmi. "
                "Запустите START_ONE_CLICK.cmd для установки зависимостей."
            )
        if Image is None:
            raise RuntimeError("Pillow не установлен.")

        palette = ColorsPalette()
        sizes = Sizes()
        drawables = [
            Drawable.PATH,
            Drawable.CHARGER,
            Drawable.VACUUM_POSITION,
            Drawable.ROOM_NAMES,
            Drawable.NO_GO_AREAS,
            Drawable.NO_MOPPING_AREAS,
            Drawable.VIRTUAL_WALLS,
        ]
        image_config = ImageConfig()
        texts = []
        parser = RoidmiMapDataParser(
            palette, sizes, drawables, image_config, texts
        )
        unpacked = parser.unpack_map(raw_map)
        parsed = parser.parse(unpacked)
        if parsed.image is None or parsed.image.is_empty:
            raise RuntimeError("Парсер вернул пустую карту ROIDMI.")
        img = parsed.image.data
        LIVE_MAP_RAW_PATH.write_bytes(raw_map)
        img.save(LIVE_MAP_PNG_PATH)
        meta = {
            "rooms": sorted(list((parsed.rooms or {}).keys())),
            "vacuum_room": parsed.vacuum_room,
            "vacuum_room_name": parsed.vacuum_room_name,
            "vacuum_position": (
                parsed.vacuum_position.as_dict()
                if parsed.vacuum_position is not None else None
            ),
            "charger": (
                parsed.charger.as_dict()
                if parsed.charger is not None else None
            ),
        }
        return str(LIVE_MAP_PNG_PATH), meta

    def _parse_raw_map_geometry(self, raw_map, map_info=None):
        unpacked = gzip.decompress(raw_map)
        marker = unpacked.find(bytes([127, 123]))
        if marker < 0:
            raise RuntimeError("В raw-map не найден разделитель бинарной карты и JSON.")
        map_image = unpacked[16:marker + 1]
        if map_info is None:
            map_info = json.loads(unpacked[marker + 1:].decode("utf-8"))

        width = int(map_info.get("width") or 0)
        height = int(map_info.get("height") or 0)
        if width <= 0 or height <= 0:
            raise RuntimeError("В карте отсутствуют корректные width/height.")
        if len(map_image) < width * height:
            raise RuntimeError(
                f"Размер бинарной карты меньше ожидаемого: {len(map_image)} < {width * height}."
            )

        areas = map_info.get("autoArea")
        if areas is None:
            areas = map_info.get("autoAreaValue")
        areas = areas or []
        room_ids = []
        room_names = {}
        for area in areas:
            try:
                rid = int(area.get("id"))
            except Exception:
                continue
            room_ids.append(rid)
            room_names[rid] = ROOM_LABELS.get(rid, str(area.get("name") or f"Room{rid}"))
        room_set = set(room_ids)

        stats = {
            rid: {"pixels": 0, "sum_x": 0.0, "sum_y": 0.0}
            for rid in room_ids
        }
        adjacency_edges = Counter()

        usable = map_image[:width * height]
        for idx, value in enumerate(usable):
            if value not in room_set:
                continue
            x = idx % width
            y = idx // width
            s = stats[value]
            s["pixels"] += 1
            s["sum_x"] += x
            s["sum_y"] += y

            if x + 1 < width:
                other = usable[idx + 1]
                if other in room_set and other != value:
                    adjacency_edges[tuple(sorted((value, other)))] += 1
            if y + 1 < height:
                other = usable[idx + width]
                if other in room_set and other != value:
                    adjacency_edges[tuple(sorted((value, other)))] += 1

        resolution = map_info.get("resolution")
        try:
            resolution = float(resolution)
        except Exception:
            resolution = None

        room_metrics = {}
        for rid in room_ids:
            s = stats[rid]
            pixels = int(s["pixels"])
            cx = (s["sum_x"] / pixels) if pixels else None
            cy = (s["sum_y"] / pixels) if pixels else None
            area_m2 = None
            if resolution is not None and 0 < resolution < 1 and pixels:
                area_m2 = pixels * resolution * resolution
            room_metrics[rid] = {
                "id": rid,
                "name": room_names.get(rid, f"Room {rid}"),
                "pixels": pixels,
                "area_m2_approx": round(area_m2, 2) if area_m2 is not None else None,
                "centroid_px": [round(cx, 2), round(cy, 2)] if cx is not None else None,
            }

        adjacency = {rid: [] for rid in room_ids}
        for (a, b), border in adjacency_edges.items():
            adjacency[a].append({"room": b, "shared_border_px": int(border)})
            adjacency[b].append({"room": a, "shared_border_px": int(border)})
        for rid in adjacency:
            adjacency[rid].sort(key=lambda x: (-x["shared_border_px"], x["room"]))

        # Determine the room containing the charger from its map coordinate when possible.
        charger_room = None
        charger_px = None
        charge = map_info.get("chargeHandlePos")
        if isinstance(charge, (list, tuple)) and len(charge) >= 2 and resolution:
            try:
                x_min = float(map_info.get("x_min") or 0)
                y_min = float(map_info.get("y_min") or 0)
                chx = (float(charge[0]) / 1000.0 - x_min) / resolution
                chy = (float(charge[1]) / 1000.0 - y_min) / resolution
                charger_px = [round(chx, 2), round(chy, 2)]
                ix, iy = int(round(chx)), int(round(chy))
                if 0 <= ix < width and 0 <= iy < height:
                    rv = usable[ix + iy * width]
                    if rv in room_set:
                        charger_room = int(rv)
            except Exception:
                charger_room = None

        # Known physical installation fallback: dock is in bathroom (Room 5).
        if charger_room is None and 5 in room_set:
            charger_room = 5

        def centroid_dist(a, b):
            ca = room_metrics[a].get("centroid_px")
            cb = room_metrics[b].get("centroid_px")
            if not ca or not cb:
                return 999999.0
            dx = ca[0] - cb[0]
            dy = ca[1] - cb[1]
            return (dx * dx + dy * dy) ** 0.5

        # Graph distance: direct neighboring rooms are preferred; non-neighbor transitions receive a large penalty.
        neighbors = {
            rid: {x["room"] for x in adjacency.get(rid, [])}
            for rid in room_ids
        }
        best_route = []
        best_cost = None
        if room_ids:
            dock = charger_room if charger_room in room_set else room_ids[0]
            others = [r for r in room_ids if r != dock]
            for perm in itertools.permutations(others):
                seq = list(perm) + [dock]
                prev = dock
                cost = 0.0
                valid = True
                for cur in seq:
                    d = centroid_dist(prev, cur)
                    if cur not in neighbors.get(prev, set()) and prev != cur:
                        d += max(width, height) * 2.5
                    cost += d
                    prev = cur
                if not valid:
                    continue
                # Stable tie-break: prefer the user's established room ordering when costs are very close.
                preferred = [2, 4, 1, 3, 5]
                tie_penalty = sum(
                    abs(preferred.index(r) - i) if r in preferred else 10
                    for i, r in enumerate(seq)
                ) * 0.001
                cost += tie_penalty
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_route = seq

        profile_suggestions = {}
        saved_profiles = self._read_room_profiles_payload()
        for rid in room_ids:
            name = room_names.get(rid, f"Room {rid}")
            saved = saved_profiles.get(str(rid), DEFAULT_ROOM_PROFILES.get(rid, {}))
            prof = self._recommend_profile_for_floor_dirt(
                rid,
                saved.get("floor_type", "Другое"),
                saved.get("dirt_level", "Средний"),
            )
            profile_suggestions[rid] = {"name": name, **prof}

        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "map_id": map_info.get("mapId"),
            "width_px": width,
            "height_px": height,
            "resolution": resolution,
            "charger_room": charger_room,
            "charger_px": charger_px,
            "rooms": room_metrics,
            "adjacency": adjacency,
            "recommended_geometric_route": best_route,
            "recommended_route_names": [
                room_names.get(r, f"Room {r}") for r in best_route
            ],
            "profile_suggestions": profile_suggestions,
            "notes": [
                "Площадь является приблизительной и рассчитывается по числу пикселей комнаты и resolution карты.",
                "Маршрут рассчитывается по центрам комнат и фактическому соседству пиксельных сегментов.",
                "Это рекомендация программы; внутренний планировщик ROIDMI может выбрать собственную траекторию.",
                "area-order 13/11 автоматически не записывается, пока точный payload вашей прошивки не подтверждён.",
            ],
        }

    def _format_map_optimization_report(self, analysis):
        lines = []
        lines.append("ROIDMI EVE Plus - анализ реальной карты")
        lines.append("=" * 52)
        lines.append(f"Map ID: {analysis.get('map_id')}")
        lines.append(
            f"Размер карты: {analysis.get('width_px')} x {analysis.get('height_px')} px"
        )
        lines.append(f"Resolution: {analysis.get('resolution')}")
        lines.append(f"Комната базы: {analysis.get('charger_room')}")
        lines.append("")
        lines.append("КОМНАТЫ")
        lines.append("-" * 52)
        for rid in sorted((analysis.get("rooms") or {}).keys()):
            r = analysis["rooms"][rid]
            area = r.get("area_m2_approx")
            area_txt = f"{area:.2f} м²" if isinstance(area, (int, float)) else "нет оценки"
            adj = [
                f"{x['room']} ({x['shared_border_px']} px)"
                for x in (analysis.get("adjacency") or {}).get(rid, [])
            ]
            lines.append(
                f"{rid}. {r.get('name')}: {area_txt}; пикселей {r.get('pixels')}; "
                f"соседи: {', '.join(adj) if adj else '-'}"
            )

        route = analysis.get("recommended_geometric_route") or []
        names = analysis.get("recommended_route_names") or []
        lines.append("")
        lines.append("РЕКОМЕНДУЕМЫЙ ГЕОМЕТРИЧЕСКИЙ ПОРЯДОК")
        lines.append("-" * 52)
        if route:
            lines.append("ID: " + " -> ".join(map(str, route)))
            lines.append("Комнаты: " + " -> ".join(names))
        else:
            lines.append("Маршрут не рассчитан.")

        lines.append("")
        lines.append("РЕКОМЕНДУЕМЫЕ ПРОФИЛИ")
        lines.append("-" * 52)
        for rid in sorted((analysis.get("profile_suggestions") or {}).keys()):
            p = analysis["profile_suggestions"][rid]
            lines.append(
                f"{rid}. {p.get('name')}: floor={p.get('floor_type')}, dirt={p.get('dirt_level')}, "
                f"fan={p.get('fan')}, water={p.get('water')}, "
                f"sweep={p.get('sweep_type')}, path={p.get('path_mode')}, "
                f"double={p.get('double_clean')}"
            )

        lines.append("")
        lines.append("ОГРАНИЧЕНИЯ")
        lines.append("-" * 52)
        for note in analysis.get("notes") or []:
            lines.append("* " + note)
        return "\n".join(lines)

    def _update_map_analysis(self, raw_map, map_info):
        analysis = self._parse_raw_map_geometry(raw_map, map_info)
        self.last_map_analysis = analysis
        LIVE_MAP_ANALYSIS_PATH.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        report = self._format_map_optimization_report(analysis)
        LIVE_MAP_REPORT_PATH.write_text(report, encoding="utf-8")
        route_names = analysis.get("recommended_route_names") or []
        if route_names:
            self.map_optimization_status_var.set(
                "Оптимизация по реальной карте: " + " -> ".join(route_names)
            )
        else:
            self.map_optimization_status_var.set(
                "Карта загружена, но маршрут автоматически не рассчитан."
            )
        return analysis

    def save_live_map_png_as(self):
        if not LIVE_MAP_PNG_PATH.exists():
            messagebox.showinfo(
                "Карта",
                "Живая карта ещё не загружена. Нажмите «Получить комнаты из карты» или «Обновить карту»."
            )
            return
        dst = filedialog.asksaveasfilename(
            title="Сохранить PNG реальной карты",
            defaultextension=".png",
            initialfile=f"ROIDMI_real_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            filetypes=[("PNG", "*.png"), ("Все файлы", "*.*")]
        )
        if not dst:
            return
        shutil.copyfile(LIVE_MAP_PNG_PATH, dst)
        self.statusbar_var.set(f"PNG карты сохранён: {dst}")

    def export_live_map_bundle(self):
        if self.last_raw_map is None or not LIVE_MAP_RAW_PATH.exists():
            self.pending_map_export = True
            messagebox.showinfo(
                "Скачать карту",
                "Сначала будет загружена актуальная карта из Xiaomi Cloud. "
                "После успешной загрузки программа автоматически предложит сохранить ZIP-пакет."
            )
            self.fetch_rooms()
            return
        self._export_live_map_bundle_now()

    def _export_live_map_bundle_now(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = filedialog.asksaveasfilename(
            title="Сохранить полный пакет реальной карты",
            defaultextension=".zip",
            initialfile=f"ROIDMI_EVE_Plus_real_map_{stamp}.zip",
            filetypes=[("ZIP", "*.zip"), ("Все файлы", "*.*")]
        )
        if not dst:
            return

        export_dir = BACKUP_DIR / f"map_export_{stamp}"
        export_dir.mkdir(parents=True, exist_ok=True)

        raw_path = export_dir / "map_raw_roidmi.gz"
        png_path = export_dir / "map_rendered.png"
        info_path = export_dir / "map_info.json"
        rooms_path = export_dir / "rooms.json"
        analysis_path = export_dir / "optimization_analysis.json"
        report_path = export_dir / "optimization_report.txt"
        readme_path = export_dir / "README.txt"

        raw_path.write_bytes(self.last_raw_map or LIVE_MAP_RAW_PATH.read_bytes())
        if LIVE_MAP_PNG_PATH.exists():
            shutil.copyfile(LIVE_MAP_PNG_PATH, png_path)
        info_path.write_text(
            json.dumps(self.map_info_raw or {}, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        rooms_path.write_text(
            json.dumps(self.rooms_data or [], ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )

        analysis = self.last_map_analysis
        if analysis is None and self.last_raw_map is not None:
            analysis = self._update_map_analysis(self.last_raw_map, self.map_info_raw or {})
        if analysis is not None:
            analysis_path.write_text(
                json.dumps(analysis, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
            report_path.write_text(
                self._format_map_optimization_report(analysis),
                encoding="utf-8"
            )

        readme_path.write_text(
            "ROIDMI EVE Plus - пакет реальной карты\n\n"
            "map_raw_roidmi.gz - оригинальная raw-карта Xiaomi Cloud\n"
            "map_rendered.png - отрисованная карта\n"
            "map_info.json - JSON-метаданные карты\n"
            "rooms.json - список комнат\n"
            "optimization_analysis.json - машинный анализ геометрии\n"
            "optimization_report.txt - человекочитаемые рекомендации\n\n"
            "Файл не содержит пароль Xiaomi и serviceToken.\n",
            encoding="utf-8"
        )

        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            for p in export_dir.iterdir():
                if p.is_file():
                    z.write(p, arcname=p.name)

        self.statusbar_var.set(f"Пакет реальной карты сохранён: {dst}")
        messagebox.showinfo(
            "Карта сохранена",
            f"Полный пакет реальной карты сохранён:\n{dst}\n\n"
            "Внутри: raw-map, PNG, JSON комнат, метаданные и отчёт оптимизации."
        )

    def show_map_optimization_report(self):
        if self.last_map_analysis is None:
            if self.last_raw_map is None:
                messagebox.showinfo(
                    "Оптимизация",
                    "Сначала загрузите актуальную живую карту Xiaomi Cloud."
                )
                return
            try:
                self._update_map_analysis(self.last_raw_map, self.map_info_raw or {})
            except Exception as e:
                messagebox.showerror("Оптимизация", str(e))
                return

        report = self._format_map_optimization_report(self.last_map_analysis)
        win = tk.Toplevel(self)
        win.title("Оптимизация уборки по реальной карте")
        win.geometry("900x650")
        txt = tk.Text(
            win, wrap="word", bg="#121b2e", fg="#eef4ff",
            insertbackground="white", relief="flat"
        )
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", report)
        txt.configure(state="disabled")
        buttons = ttk.Frame(win)
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(
            buttons, text="Скачать полный ZIP карты",
            command=self.export_live_map_bundle
        ).pack(side="left")
        ttk.Button(
            buttons, text="Закрыть",
            command=win.destroy
        ).pack(side="right")

    def _draw_dashboard_map_live(self):
        c = self.dashboard_map_canvas
        if c is None:
            return
        c.delete("all")
        W = int(c.winfo_width() or 650)
        H = int(c.winfo_height() or 430)
        c.create_rectangle(0, 0, W, H, fill="#0b1220", outline="#0b1220")

        path = self.dashboard_live_map_path
        if not self.dashboard_live_map_available or not path.exists():
            c.create_text(
                W // 2, H // 2 - 20,
                text="Живая карта Xiaomi Cloud ещё не загружена.",
                fill="#dbeafe", font=("Segoe UI Semibold", 12),
                justify="center"
            )
            c.create_text(
                W // 2, H // 2 + 18,
                text="Нажмите «Обновить карту». Если Xiaomi запросит CAPTCHA/2FA, завершите авторизацию.",
                fill="#9fb4d1", font=("Segoe UI", 10),
                justify="center", width=max(300, W - 100)
            )
            return

        if Image is None or ImageTk is None:
            c.create_text(
                W // 2, H // 2,
                text="Для живой карты требуется Pillow.",
                fill="#fecaca", font=("Segoe UI", 12)
            )
            return

        try:
            img = Image.open(path).convert("RGBA")
            iw, ih = img.size
            scale = min((W - 20) / max(iw, 1), (H - 20) / max(ih, 1))
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            img = img.resize((nw, nh))
            self.dashboard_real_map_photo = ImageTk.PhotoImage(img)
            ox = (W - nw) // 2
            oy = (H - nh) // 2
            c.create_image(ox, oy, image=self.dashboard_real_map_photo, anchor="nw")
            self._live_map_display = {
                "ox": ox, "oy": oy, "scale": scale,
                "image_w": iw, "image_h": ih,
            }
            self._map_room_screen_points = {}
            analysis = self.last_map_analysis or {}
            raw_h = float(analysis.get("height_px") or ih)
            for key, room in (analysis.get("rooms") or {}).items():
                if not isinstance(room, dict):
                    continue
                try:
                    rid = int(room.get("id", key))
                except Exception:
                    continue
                centroid = room.get("centroid_px")
                if not centroid or len(centroid) < 2:
                    continue
                sx = ox + float(centroid[0]) * scale
                sy = oy + (raw_h - 1.0 - float(centroid[1])) * scale
                self._map_room_screen_points[rid] = (sx, sy)
                selected = bool(self.room_select_vars.get(rid) and self.room_select_vars[rid].get())
                fill = "#ffffff" if selected else "#dbeafe"
                c.create_oval(sx-10, sy-10, sx+10, sy+10, fill="#2563eb", outline=fill, width=2)
                c.create_text(
                    sx, sy-18, text=f"{rid} {ROOM_LABELS.get(rid, '')}",
                    fill=fill, font=("Segoe UI Semibold", 9)
                )
            c.create_text(
                16, 14, anchor="nw",
                text="Живая карта ROIDMI / Xiaomi Cloud | клик по комнате = параметры",
                fill="#cfe2ff", font=("Segoe UI Semibold", 10)
            )
            c.create_text(
                16, H - 12, anchor="sw",
                text=self.dashboard_map_meta_var.get(),
                fill="#9fb4d1", font=("Segoe UI", 9)
            )
        except Exception as e:
            c.create_text(
                W // 2, H // 2,
                text=f"Не удалось открыть живую карту:\n{e}",
                fill="#fecaca", font=("Segoe UI", 12), justify="center"
            )

    def open_map_editor_help(self):
        self.dashboard_map_mode_var.set("live")
        self._draw_dashboard_map()
        self.map_editor_status_var.set(
            "Кликните по синей метке комнаты на живой карте, чтобы изменить её покрытие и условия."
        )
        messagebox.showinfo(
            "Редактор карты",
            "Переключено на живую карту.\n\n"
            "Нажмите на синюю метку нужной комнаты. Можно указать покрытие, загрязнение, "
            "ковёр, порог, узкий проход, провода, шерсть животных и заметки."
        )

    def _on_dashboard_map_click(self, event):
        if self.dashboard_map_mode_var.get() != "live":
            return
        if not self._map_room_screen_points:
            return
        best = None
        best_d2 = None
        for rid, (x, y) in self._map_room_screen_points.items():
            d2 = (event.x - x) ** 2 + (event.y - y) ** 2
            if best_d2 is None or d2 < best_d2:
                best = rid
                best_d2 = d2
        if best is not None and best_d2 is not None and best_d2 <= 65 ** 2:
            self.open_room_environment_editor(best)

    def open_room_environment_editor(self, rid):
        profiles = self._read_room_profiles_payload()
        p = dict(profiles.get(str(rid), {}))
        win = tk.Toplevel(self)
        win.title(f"Комната {rid}: {ROOM_LABELS.get(rid, rid)}")
        win.geometry("520x560")
        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        floor = tk.StringVar(value=p.get("floor_type", DEFAULT_ROOM_PROFILES[rid]["floor_type"]))
        dirt = tk.StringVar(value=p.get("dirt_level", DEFAULT_ROOM_PROFILES[rid]["dirt_level"]))
        rug = tk.BooleanVar(value=bool(p.get("has_rug", "ковёр" in str(floor.get()).lower())))
        pet = tk.BooleanVar(value=bool(p.get("pet_hair", False)))
        cables = tk.BooleanVar(value=bool(p.get("cables", False)))
        narrow = tk.BooleanVar(value=bool(p.get("narrow_passage", False)))
        try:
            threshold_default = float(p.get("threshold_cm", 0) or 0)
        except Exception:
            threshold_default = 0.0
        threshold = tk.DoubleVar(value=threshold_default)
        notes = tk.StringVar(value=str(p.get("notes", "")))

        rows = [
            ("Покрытие пола", floor, FLOOR_TYPES),
            ("Загрязнение", dirt, DIRT_LEVELS),
        ]
        for i, (label, var, values) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="e", padx=6, pady=7)
            ttk.Combobox(frame, textvariable=var, values=values, state="readonly", width=28).grid(
                row=i, column=1, sticky="w", padx=6, pady=7
            )

        ttk.Checkbutton(frame, text="Есть ковёр / ковровая зона", variable=rug).grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=5)
        ttk.Checkbutton(frame, text="Есть шерсть животных", variable=pet).grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=5)
        ttk.Checkbutton(frame, text="Есть провода / мелкие препятствия", variable=cables).grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=5)
        ttk.Checkbutton(frame, text="Есть узкий проход", variable=narrow).grid(row=5, column=0, columnspan=2, sticky="w", padx=12, pady=5)
        ttk.Label(frame, text="Порог, см").grid(row=6, column=0, sticky="e", padx=6, pady=7)
        ttk.Spinbox(frame, from_=0, to=5, increment=0.1, textvariable=threshold, width=10).grid(row=6, column=1, sticky="w", padx=6, pady=7)
        ttk.Label(frame, text="Заметки").grid(row=7, column=0, sticky="e", padx=6, pady=7)
        ttk.Entry(frame, textvariable=notes, width=34).grid(row=7, column=1, sticky="ew", padx=6, pady=7)

        preview_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=preview_var, style="Muted.TLabel", wraplength=450, justify="left").grid(
            row=8, column=0, columnspan=2, sticky="w", padx=8, pady=10
        )

        def update_preview(*_):
            rec = self._recommend_profile_for_floor_dirt(rid, floor.get(), dirt.get())
            if rug.get():
                rec["water"] = min(rec["water"], 1)
                rec["fan"] = max(rec["fan"], 3)
            preview_var.set(
                f"Рекомендация: fan {rec['fan']}, water {rec['water']}, "
                f"path {rec['path_mode']}, double {int(rec['double_clean'])}."
            )

        floor.trace_add("write", update_preview)
        dirt.trace_add("write", update_preview)
        rug.trace_add("write", update_preview)
        update_preview()

        def save():
            profiles_now = self._read_room_profiles_payload()
            current = dict(profiles_now.get(str(rid), {}))
            current.update({
                "name": ROOM_LABELS[rid],
                "floor_type": floor.get(),
                "dirt_level": dirt.get(),
                "has_rug": bool(rug.get()),
                "pet_hair": bool(pet.get()),
                "cables": bool(cables.get()),
                "narrow_passage": bool(narrow.get()),
                "threshold_cm": float(threshold.get() or 0),
                "notes": notes.get().strip(),
            })
            rec = self._recommend_profile_for_floor_dirt(rid, floor.get(), dirt.get())
            if rug.get():
                rec["water"] = min(rec["water"], 1)
                rec["fan"] = max(rec["fan"], 3)
            for key in ("fan", "water", "sweep_type", "path_mode", "double_clean"):
                current[key] = rec[key]
            profiles_now[str(rid)] = current
            payload = {
                "model": MODEL,
                "saved_at": datetime.now().astimezone().isoformat(),
                "profiles": profiles_now,
                "implementation": "safe_runtime_profile_before_each_room",
            }
            atomic_write_json(ROOM_PROFILES_PATH, payload)
            if rid in self.room_profile_floor_vars:
                self.room_profile_floor_vars[rid].set(current["floor_type"])
                self.room_profile_dirt_vars[rid].set(current["dirt_level"])
                self.room_profile_fan_vars[rid].set(reverse_lookup(FAN, current["fan"]))
                self.room_profile_water_vars[rid].set(reverse_lookup(WATER, current["water"]))
                self.room_profile_sweep_vars[rid].set(reverse_lookup(SWEEP_TYPE, current["sweep_type"]))
                self.room_profile_path_vars[rid].set(reverse_lookup(PATH_MODE, current["path_mode"]))
                self.room_profile_double_vars[rid].set(bool(current["double_clean"]))
            self.map_editor_status_var.set(f"{ROOM_LABELS[rid]}: параметры сохранены.")
            self._refresh_center_views_if_present()
            win.destroy()

        ttk.Button(frame, text="СОХРАНИТЬ", style="Accent.TButton", command=save).grid(
            row=9, column=0, columnspan=2, pady=12
        )
        frame.grid_columnconfigure(1, weight=1)

    def _draw_dashboard_map_real(self):
        c = self.dashboard_map_canvas
        if c is None:
            return
        c.delete("all")
        W = int(c.winfo_width() or 650)
        H = int(c.winfo_height() or 430)
        c.create_rectangle(0, 0, W, H, fill="#0b1220", outline="#0b1220")

        map_path = self.dashboard_real_map_path
        if Image is None or ImageTk is None:
            c.create_text(
                W//2, H//2,
                text="Для режима реальной карты требуется Pillow.\nПерезапустите установку пакета.",
                fill="#dbeafe", font=("Segoe UI", 12), justify="center"
            )
            return
        if not map_path.exists():
            c.create_text(
                W//2, H//2,
                text="Файл реальной карты не найден.\nЗагрузите PNG/JPG кнопкой выше.",
                fill="#dbeafe", font=("Segoe UI", 12), justify="center"
            )
            return

        try:
            img = Image.open(map_path).convert("RGBA")
            iw, ih = img.size
            scale = min((W - 20) / max(iw, 1), (H - 20) / max(ih, 1))
            nw = max(1, int(iw * scale))
            nh = max(1, int(ih * scale))
            img = img.resize((nw, nh))
            self.dashboard_real_map_photo = ImageTk.PhotoImage(img)
            ox = (W - nw) // 2
            oy = (H - nh) // 2
            c.create_image(ox, oy, image=self.dashboard_real_map_photo, anchor="nw")

            for rid, (x1, y1, x2, y2) in self.dashboard_real_map_boxes.items():
                rx1 = ox + int(x1 * nw / iw)
                ry1 = oy + int(y1 * nh / ih)
                rx2 = ox + int(x2 * nw / iw)
                ry2 = oy + int(y2 * nh / ih)
                selected = bool(self.room_select_vars.get(rid) and self.room_select_vars[rid].get())
                if selected:
                    c.create_rectangle(rx1, ry1, rx2, ry2, outline="#ffffff", width=3)
                    c.create_text(
                        (rx1 + rx2) // 2, max(18, ry1 - 12),
                        text=self.dashboard_room_names.get(rid, f"Room {rid}"),
                        fill="#ffffff", font=("Segoe UI", 10, "bold")
                    )

            c.create_text(16, 14, anchor="nw", text="Скриншот карты Xiaomi", fill="#cfe2ff", font=("Segoe UI", 10, "bold"))
            c.create_text(16, H - 30, anchor="sw", text=self.dashboard_real_map_source_var.get(), fill="#9fb4d1", font=("Segoe UI", 9))
            c.create_text(16, H - 12, anchor="sw", text=self.dashboard_map_meta_var.get(), fill="#9fb4d1", font=("Segoe UI", 9))
        except Exception as e:
            c.create_text(
                W//2, H//2,
                text=f"Не удалось отрисовать реальную карту:\n{e}",
                fill="#fecaca", font=("Segoe UI", 12), justify="center"
            )

    def _draw_dashboard_map(self):
        mode = self.dashboard_map_mode_var.get().strip().lower()
        if mode == "live":
            self._draw_dashboard_map_live()
        elif mode == "real":
            self._draw_dashboard_map_real()
        else:
            self._draw_dashboard_map_schematic()

    def _refresh_dashboard(self):

        try:
            token = self.token_var.get().strip()
            ip = self.ip_var.get().strip()
        except Exception:
            token = ""
            ip = ""
        masked = ("•" * max(0, len(token)-4) + token[-4:]) if len(token) >= 4 else "••••"
        self.dashboard_ip_var.set(f"IP: {ip or '-'}")
        self.dashboard_token_var.set(f"Токен: {masked}")
        self.dashboard_device_var.set(f"ROIDMI EVE Plus | {MODEL}")

        if self.rooms_data:
            rooms_sorted = sorted(self.rooms_data, key=lambda x: int(x.get("id", 0)))
            txt = ", ".join(f"{r.get('id')}: {r.get('name')}" for r in rooms_sorted)
            self.dashboard_rooms_var.set("Комнаты: " + txt)
        else:
            self.dashboard_rooms_var.set("Комнаты: 1 Кухня, 2 Спальня, 3 Коридор, 4 Зал, 5 Ванная")

        if self.current_map_id:
            self.dashboard_map_meta_var.set(f"Xiaomi Cloud: карта загружена | mapId: {self.current_map_id}")
        elif self.dashboard_live_map_available:
            self.dashboard_map_meta_var.set("Xiaomi Cloud: живая карта загружена")
        else:
            self.dashboard_map_meta_var.set("Xiaomi Cloud: карта не загружена")

        d = dict(self.last_data or {})
        if d:
            state_names = {1:"сон",2:"ожидание",3:"пауза",4:"уборка",5:"возврат на базу",
                           6:"зарядка",7:"ошибка",8:"ручное управление",9:"заряжен",10:"выключен",11:"пауза возврата"}
            state_name = state_names.get(d.get("state"), d.get("state"))
            self.dashboard_status_var.set("Подключено")
            self.dashboard_substatus_var.set(f"Состояние: {state_name}")
            self.dashboard_battery_var.set(f"{d.get('battery_level', '-')} %")
            error_code = d.get("error_code")
            self.dashboard_error_var.set(f"{error_code} - {FAULT_RU.get(error_code, 'Нет данных')}")
            status_lines = [
                f"Состояние: {state_name}",
                f"Мощность: {reverse_lookup(FAN, d.get('fanspeed_mode')) if d.get('fanspeed_mode') is not None else d.get('fanspeed_mode')}",
                f"Тип уборки: {reverse_lookup(SWEEP_TYPE, d.get('sweep_type')) if d.get('sweep_type') is not None else d.get('sweep_type')}",
                f"Подача воды: {reverse_lookup(WATER, d.get('water_level')) if d.get('water_level') is not None else d.get('water_level')}",
                f"Маршрут: {reverse_lookup(PATH_MODE, d.get('path_mode')) if d.get('path_mode') is not None else d.get('path_mode')}",
                f"Самоочистка станции: {reverse_lookup(STATION_FREQ, d.get('work_station_freq')) if d.get('work_station_freq') is not None else d.get('work_station_freq')}",
                f"Громкость: {d.get('volume', '-')} %",
                f"Boost на ковре: {bool(d.get('auto_boost'))}",
                f"LiDAR collision: {bool(d.get('lidar_collision'))}",
                f"Уборок всего: {d.get('clean_counts', '-')}",
                f"Площадь последней/текущей уборки: {d.get('clean_area', '-')}",
                f"Время последней/текущей уборки: {d.get('clean_time_sec', '-')} сек.",
            ]
            consumable_lines = [
                f"HEPA-фильтр: {d.get('filter_life', '-')} %",
                f"Основная щётка: {d.get('main_brush_life', '-')} %",
                f"Боковая щётка: {d.get('edge_brush_life', '-')} %",
                f"Датчики: {d.get('sensor_dirty_life', '-')} %",
                f"Одноразовый мешок/контейнер: {d.get('dust_bag_life', '-')} %",
            ]
        else:
            self.dashboard_status_var.set("Не подключено")
            self.dashboard_substatus_var.set("Подключите робот и прочитайте состояние")
            self.dashboard_battery_var.set("-")
            self.dashboard_error_var.set("-")
            status_lines = ["Нет данных состояния. Нажмите «Подключиться и прочитать»."]
            consumable_lines = ["Нет данных по расходникам."]

        if self.dashboard_status_lines is not None:
            self.dashboard_status_lines.configure(state="normal")
            self.dashboard_status_lines.delete("1.0", "end")
            self.dashboard_status_lines.insert("1.0", "\n".join(status_lines) + "\n")
            self.dashboard_status_lines.configure(state="disabled")

        if self.dashboard_consumables_lines is not None:
            self.dashboard_consumables_lines.configure(state="normal")
            self.dashboard_consumables_lines.delete("1.0", "end")
            self.dashboard_consumables_lines.insert("1.0", "\n".join(consumable_lines) + "\n")
            self.dashboard_consumables_lines.configure(state="disabled")

        if self.dashboard_schedule_list is not None:
            self.dashboard_schedule_list.delete(0, "end")
            timing = self.current_timing or {"time": []}
            rows = timing.get("time", []) if isinstance(timing, dict) else []
            if not rows:
                self.dashboard_schedule_list.insert("end", "Расписание пока не загружено.")
            else:
                day_map = {0:"Вс",1:"Пн",2:"Вт",3:"Ср",4:"Чт",5:"Пт",6:"Сб"}
                for row in rows:
                    try:
                        sec, enabled, fan, sweep, days, water, rooms = row[:7]
                        hh = int(sec) // 3600
                        mm = (int(sec) % 3600) // 60
                        days_txt = "Ежедневно" if sorted(days) == [0,1,2,3,4,5,6] else ", ".join(day_map.get(int(d), str(d)) for d in days)
                        rooms_txt = "вся квартира" if not rooms else ", ".join(self.dashboard_room_names.get(int(r), f"Room {r}") for r in rooms)
                        onoff = "●" if enabled else "○"
                        self.dashboard_schedule_list.insert("end", f"{onoff} {hh:02d}:{mm:02d} | {days_txt} | {rooms_txt}")
                    except Exception:
                        self.dashboard_schedule_list.insert("end", str(row))

        self._draw_dashboard_map()

    def _build_control_tab(self):
        left = ttk.LabelFrame(self.tab_control, text="Команды")
        left.pack(side="left", fill="y", padx=10, pady=10)

        for text, fn in [
            ("▶ Начать уборку", lambda: self.run_action("start")),
            ("⏹ Остановить", lambda: self.run_action("stop")),
            ("⌂ На базу", lambda: self.run_action("home")),
            ("🔎 Найти робот", lambda: self.run_action("identify")),
            ("🗑 Запустить сбор пыли", lambda: self.run_action("start_dust")),
        ]:
            ttk.Button(left, text=text, command=fn, width=30).pack(padx=10, pady=6)

        ttk.Separator(left).pack(fill="x", padx=8, pady=8)
        ttk.Button(left, text="Обновить состояние", command=self.read_status, width=30).pack(padx=10, pady=6)
        ttk.Button(left, text="Сделать резервную копию", command=self.backup_now, width=30).pack(padx=10, pady=6)

        rooms_box = ttk.LabelFrame(left, text="Прямая уборка комнат")
        rooms_box.pack(fill="x", padx=8, pady=(10,6))
        ttk.Label(
            rooms_box,
            text="Формат команды проверен по Roidmi-EVE-Plus и node-xmihome: action 14/1, mapId + segmentId.",
            wraplength=260,
            foreground="#555"
        ).pack(anchor="w", padx=6, pady=(5,4))

        names = {1:"Кухня",2:"Спальня",3:"Коридор",4:"Зал",5:"Ванная"}
        for rid in [1,2,3,4,5]:
            v = tk.BooleanVar(value=False)
            self.room_select_vars[rid] = v
            ttk.Checkbutton(
                rooms_box, text=f"Room {rid}: {names[rid]}", variable=v
            ).pack(anchor="w", padx=8, pady=1)

        maprow = ttk.Frame(rooms_box)
        maprow.pack(fill="x", padx=6, pady=4)
        ttk.Label(maprow, text="mapId:").pack(side="left")
        ttk.Entry(maprow, textvariable=self.direct_room_map_id_var, width=16).pack(side="left", padx=4)
        ttk.Button(maprow, text="Из карты", command=self.fill_map_id_from_map).pack(side="left", padx=2)

        ttk.Checkbutton(
            rooms_box,
            text="Если локальная команда не прошла, разрешить Xiaomi Cloud fallback",
            variable=self.direct_room_use_cloud_fallback
        ).pack(anchor="w", padx=6, pady=3)

        ttk.Button(
            rooms_box,
            text="УБРАТЬ ВЫБРАННЫЕ КОМНАТЫ", style="Accent.TButton",
            command=self.start_selected_rooms_direct,
            width=30
        ).pack(padx=6, pady=(4,7))

        right = ttk.LabelFrame(self.tab_control, text="Текущее состояние")
        right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.status_text = tk.Text(right, wrap="word", height=25, font=("Consolas", 10))
        self.status_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.status_text.insert("1.0", "Подключитесь к роботу и нажмите «Подключиться и прочитать».\n")
        self.status_text.configure(state="disabled")

    def _build_settings_tab(self):
        outer = ttk.Frame(self.tab_settings)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        form = ttk.LabelFrame(outer, text="Рабочие параметры")
        form.pack(side="left", fill="y", padx=(0,10))

        self.fan_var = tk.StringVar(value=reverse_lookup(FAN, 3))
        self.sweep_var = tk.StringVar(value=reverse_lookup(SWEEP_TYPE, 2))
        self.water_var = tk.StringVar(value=reverse_lookup(WATER, 2))
        self.path_var = tk.StringVar(value=reverse_lookup(PATH_MODE, 0))
        self.station_freq_var = tk.StringVar(value=reverse_lookup(STATION_FREQ, 1))
        self.volume_var = tk.IntVar(value=23)

        rows = [
            ("Мощность:", self.fan_var, FAN),
            ("Тип уборки:", self.sweep_var, SWEEP_TYPE),
            ("Подача воды:", self.water_var, WATER),
            ("Маршрут:", self.path_var, PATH_MODE),
            ("Самоочистка станции:", self.station_freq_var, STATION_FREQ),
        ]
        for i,(label,var,mapping) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=i, column=0, padx=7, pady=7, sticky="e")
            cb = ttk.Combobox(form, textvariable=var, values=list(mapping.keys()), state="readonly", width=37)
            cb.grid(row=i, column=1, padx=7, pady=7, sticky="w")

        ttk.Label(form, text="Громкость 0–100:").grid(row=5, column=0, padx=7, pady=7, sticky="e")
        ttk.Spinbox(form, from_=0, to=100, textvariable=self.volume_var, width=10).grid(row=5,column=1,padx=7,pady=7,sticky="w")

        self.auto_boost_var = tk.BooleanVar()
        self.double_clean_var = tk.BooleanVar()
        self.led_var = tk.BooleanVar()
        self.lidar_var = tk.BooleanVar()
        self.station_led_var = tk.BooleanVar()
        self.station_key_var = tk.BooleanVar()
        self.mute_var = tk.BooleanVar()

        bools = [
            ("Усиление на ковре", self.auto_boost_var),
            ("Двойная уборка", self.double_clean_var),
            ("Подсветка робота", self.led_var),
            ("Предотвращение столкновений LiDAR", self.lidar_var),
            ("Дисплей/подсветка станции", self.station_led_var),
            ("Кнопка сбора пыли на станции", self.station_key_var),
            ("Без звука", self.mute_var),
        ]
        for idx,(label,var) in enumerate(bools, start=6):
            ttk.Checkbutton(form, text=label, variable=var).grid(row=idx,column=0,columnspan=2,padx=15,pady=5,sticky="w")

        ttk.Button(form, text="Загрузить текущие настройки", command=self.read_status).grid(row=14,column=0,columnspan=2,pady=(16,6))
        ttk.Button(form, text="ПРИМЕНИТЬ НАСТРОЙКИ", command=self.apply_settings, style="Accent.TButton").grid(row=15,column=0,columnspan=2,pady=6)
        ttk.Button(
            form,
            text="ПРИМЕНИТЬ ОПТИМАЛЬНЫЙ ПРОФИЛЬ 45 м²", style="Accent2.TButton",
            command=self.apply_optimized_global_profile
        ).grid(row=16,column=0,columnspan=2,pady=(10,6))

        ttk.Label(
            form,
            text="PERSISTENT AUTOSAVE: ВКЛЮЧЁН - изменение сразу пишется в робот и USER_PROFILE.json",
            foreground="#1f6b2a",
            wraplength=350,
            justify="center"
        ).grid(row=17,column=0,columnspan=2,padx=8,pady=(8,4))
        ttk.Button(
            form,
            text="Открыть сохранённый профиль",
            command=self.open_user_profile
        ).grid(row=18,column=0,columnspan=2,pady=(4,6))

        info = ttk.LabelFrame(outer, text="Что изменяется")
        info.pack(side="left", fill="both", expand=True)
        ttk.Label(
            info,
            text="Интерфейс v21.0 оптимизирован под Windows 1920x1080: DPI-aware, Segoe UI, компактные вкладки и автоматическое разворачивание.",
            style="Muted.TLabel", wraplength=850, justify="left"
        ).pack(anchor="w", padx=12, pady=(10, 0))
        explanation = (
            "Параметры записываются напрямую в MIoT-свойства roidmi.vacuum.v60 по локальной сети. Home Assistant не используется.\n\n"
            "Перед каждой записью программа автоматически сохраняет резервную копию текущего состояния.\n\n"
            "Самоочистка станции: значение 2 означает очистку контейнера после каждой второй уборки.\n\n"
            "«Уровень 4» воды присутствует в MIoT-спецификации, но фактическое поведение зависит от прошивки.\n\n"
            "LiDAR: у EVE Plus нет настройки «силы», дальности или чувствительности лазера. "
            "Доступен только штатный флаг предотвращения столкновений lidar_collision - его рекомендуется оставить включённым.\n\n"
            "Параметр edge-sweep намеренно не выставляется: для EVE Plus его практический эффект не подтверждён."
        )
        ttk.Label(info, text=explanation, wraplength=500, justify="left").pack(anchor="nw", padx=12, pady=12)

    def _build_voice_tab(self):
        root = ttk.Frame(self.tab_voice)
        root.pack(fill="both", expand=True, padx=12, pady=12)

        title = ttk.Frame(root, style="Toolbar.TFrame")
        title.pack(fill="x", pady=(0, 8))
        ttk.Label(title, text="Голос робота и каталог озвучек", style="Header.TLabel").pack(anchor="w", padx=14, pady=(12, 2))
        ttk.Label(
            title,
            text="Штатное set-voice 8/12, локальная библиотека и ссылки на каталоги/материалы для ROIDMI.",
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=14, pady=(0, 12))

        paned = ttk.Panedwindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        controls = ttk.LabelFrame(left, text="Выбор и переключение", style="Section.TLabelframe")
        controls.pack(fill="x", padx=(0, 5), pady=(0, 8))

        current = ttk.Frame(controls, style="Card.TFrame")
        current.pack(fill="x", padx=10, pady=10)
        ttk.Label(current, text="Текущий голос:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(current, textvariable=self.voice_current_var, font=("Segoe UI Semibold", 11)).grid(row=0, column=1, sticky="w", padx=8)
        ttk.Button(current, text="Обновить", command=self.read_status).grid(row=0, column=2, padx=4)
        ttk.Button(current, text="Проверить", command=lambda: self.run_action("identify")).grid(row=0, column=3, padx=4)
        current.grid_columnconfigure(1, weight=1)

        preset = ttk.Frame(controls, style="Card.TFrame")
        preset.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(preset, text="Предустановка", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        cb = ttk.Combobox(
            preset,
            textvariable=self.voice_preset_var,
            state="readonly",
            values=[
                "Русский штатный (girl_ru)",
                "English штатный (girl_en)",
                "Свой ID / имя пакета"
            ],
            width=34
        )
        cb.grid(row=0, column=1, sticky="ew", padx=8)
        cb.bind("<<ComboboxSelected>>", self._voice_preset_changed)
        ttk.Label(preset, text="audio ID", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(preset, textvariable=self.voice_raw_var, width=44).grid(row=1, column=1, sticky="ew", padx=8)
        preset.grid_columnconfigure(1, weight=1)

        options = ttk.Frame(controls, style="Card.TFrame")
        options.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Checkbutton(
            options,
            text="Если LAN недоступен, попробовать Xiaomi Cloud",
            variable=self.voice_cloud_fallback_var
        ).pack(anchor="w", pady=3)

        actions = ttk.Frame(controls, style="Card.TFrame")
        actions.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(actions, text="ПРИМЕНИТЬ ГОЛОС", style="Accent.TButton", command=self.apply_voice).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Русский", command=lambda: self._set_voice_quick("girl_ru")).pack(side="left", padx=3)
        ttk.Button(actions, text="English", command=lambda: self._set_voice_quick("girl_en")).pack(side="left", padx=3)

        ttk.Label(
            controls, textvariable=self.voice_status_var, style="Muted.TLabel",
            wraplength=620, justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        library = ttk.LabelFrame(left, text="Локальная библиотека", style="Section.TLabelframe")
        library.pack(fill="both", expand=True, padx=(0, 5))
        lib_cols = ("name", "type", "size")
        self.voice_library_tree = ttk.Treeview(library, columns=lib_cols, show="headings", height=9)
        self.voice_library_tree.heading("name", text="Голос / файл")
        self.voice_library_tree.heading("type", text="Тип")
        self.voice_library_tree.heading("size", text="Размер")
        self.voice_library_tree.column("name", width=300, anchor="w")
        self.voice_library_tree.column("type", width=100, anchor="center")
        self.voice_library_tree.column("size", width=100, anchor="e")
        self.voice_library_tree.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        lib_buttons = ttk.Frame(library, style="Card.TFrame")
        lib_buttons.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Button(lib_buttons, text="Обновить", command=self.refresh_voice_library).pack(side="left", padx=3)
        ttk.Button(lib_buttons, text="Добавить файл", command=self.select_voice_pack).pack(side="left", padx=3)
        ttk.Button(lib_buttons, text="Выбрать как audio ID", command=self.use_selected_voice_library_item).pack(side="left", padx=3)
        ttk.Button(lib_buttons, text="Собрать tar.gz из папки", command=self.build_voice_tar_from_folder).pack(side="left", padx=3)
        ttk.Button(lib_buttons, text="Папка", command=self.open_voicepacks_folder).pack(side="right", padx=3)
        ttk.Label(library, textvariable=self.voice_library_status_var, style="Muted.TLabel").pack(anchor="w", padx=12, pady=(0, 8))

        sources = ttk.LabelFrame(right, text="Сайты и каталоги", style="Section.TLabelframe")
        sources.pack(fill="both", expand=True, padx=(5, 0))
        src_cols = ("name", "kind", "compat")
        self.voice_sources_tree = ttk.Treeview(sources, columns=src_cols, show="headings", height=12)
        self.voice_sources_tree.heading("name", text="Источник")
        self.voice_sources_tree.heading("kind", text="Тип")
        self.voice_sources_tree.heading("compat", text="Совместимость")
        self.voice_sources_tree.column("name", width=230, anchor="w")
        self.voice_sources_tree.column("kind", width=150, anchor="w")
        self.voice_sources_tree.column("compat", width=260, anchor="w")
        for idx, source in enumerate(VOICE_SOURCES):
            self.voice_sources_tree.insert(
                "", "end", iid=str(idx),
                values=(source["name"], source["kind"], source["compatibility"])
            )
        self.voice_sources_tree.pack(fill="both", expand=True, padx=10, pady=(10, 6))

        src_buttons = ttk.Frame(sources, style="Card.TFrame")
        src_buttons.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Button(src_buttons, text="Открыть сайт", command=self.open_selected_voice_source).pack(side="left", padx=3)
        ttk.Button(src_buttons, text="Скачать файл", command=self.download_selected_voice_source).pack(side="left", padx=3)
        ttk.Button(src_buttons, text="Mindsolo", command=lambda: webbrowser.open("https://vacuum.mindsolo.net/")).pack(side="left", padx=3)
        ttk.Button(src_buttons, text="4PDA", command=lambda: webbrowser.open("https://4pda.to/forum/index.php?showtopic=1023628")).pack(side="left", padx=3)

        urlbox = ttk.Frame(sources, style="Card.TFrame")
        urlbox.pack(fill="x", padx=10, pady=(0, 6))
        ttk.Label(urlbox, text="Прямая ссылка:", style="Muted.TLabel").pack(side="left")
        ttk.Entry(urlbox, textvariable=self.voice_download_url_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(urlbox, text="Скачать", command=self.download_voice_url).pack(side="right")

        ttk.Label(
            sources,
            text=(
                "Mindsolo открывается как внешний установщик через браузер. McDoS содержит материалы именно "
                "для Roidmi EVE Plus. Скачанные архивы сохраняются только в папку voicepacks и не запускаются. "
                "Произвольный локальный архив нельзя безопасно отправлять в робот без подтверждённой схемы update-audio."
            ),
            style="Muted.TLabel", wraplength=650, justify="left"
        ).pack(anchor="w", padx=12, pady=(4, 8))

        self._write_voice_sources_file()
        self.after(50, self.refresh_voice_library)


    def _write_voice_sources_file(self):
        try:
            VOICE_CATALOG_PATH.write_text(
                json.dumps(VOICE_SOURCES, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    @staticmethod
    def _human_size(size):
        try:
            size = float(size)
        except Exception:
            return "-"
        units = ["B", "KiB", "MiB", "GiB"]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
            size /= 1024
        return "-"

    def refresh_voice_library(self):
        if self.voice_library_tree is None:
            return
        for item in self.voice_library_tree.get_children():
            self.voice_library_tree.delete(item)

        for preset in VOICE_PRESETS:
            self.voice_library_tree.insert(
                "", "end", iid="builtin:" + preset["audio_id"],
                values=(
                    preset["name"] + f" [{preset['audio_id']}]",
                    "встроенный", "-"
                )
            )

        current = self.last_data.get("current_audio")
        if current:
            cur = str(current)
            self.voice_library_tree.insert(
                "", "end", iid="current:" + hashlib.sha1(cur.encode("utf-8")).hexdigest()[:12],
                values=(cur, "текущий", "-")
            )

        files = []
        for p in sorted(VOICEPACKS_DIR.iterdir()):
            if p.is_file() and p.name.lower().endswith((".tar.gz", ".tgz", ".zip", ".rar", ".gz")):
                files.append(p)
        self._voice_library_files = files
        for i, p in enumerate(files):
            ext = "tar.gz" if p.name.lower().endswith(".tar.gz") else p.suffix.lower().lstrip(".")
            self.voice_library_tree.insert(
                "", "end", iid=f"file:{i}",
                values=(p.name, ext, self._human_size(p.stat().st_size))
            )

        self.voice_library_status_var.set(
            f"Встроенных: {len(VOICE_PRESETS)}; локальных архивов: {len(files)}."
        )

    def use_selected_voice_library_item(self):
        if self.voice_library_tree is None:
            return
        sel = self.voice_library_tree.selection()
        if not sel:
            messagebox.showinfo("Голос", "Выберите строку в локальной библиотеке.")
            return
        iid = sel[0]
        if iid.startswith("builtin:"):
            audio = iid.split(":", 1)[1]
            self.voice_raw_var.set(audio)
            self.voice_preset_var.set(
                "Русский штатный (girl_ru)" if audio == "girl_ru"
                else "English штатный (girl_en)"
            )
            return
        if iid.startswith("current:"):
            vals = self.voice_library_tree.item(iid, "values")
            if vals:
                self.voice_raw_var.set(str(vals[0]))
                self.voice_preset_var.set("Свой ID / имя пакета")
            return
        if iid.startswith("file:"):
            try:
                idx = int(iid.split(":", 1)[1])
                p = self._voice_library_files[idx]
            except Exception:
                messagebox.showerror("Голос", "Не удалось определить выбранный файл.")
                return
            self.voice_pack_path_var.set(str(p))
            self.voice_raw_var.set(p.name)
            self.voice_preset_var.set("Свой ID / имя пакета")
            self.voice_status_var.set(
                f"Выбран файл {p.name}. Имя подставлено как audio ID. "
                "Это сработает только если данный пакет уже доступен роботу/серверу озвучек."
            )

    def build_voice_tar_from_folder(self):
        folder = filedialog.askdirectory(title="Папка с файлами голосового пакета")
        if not folder:
            return
        folder = Path(folder)
        files = [p for p in folder.rglob("*") if p.is_file()]
        mp3 = [p for p in files if p.suffix.lower() == ".mp3"]
        if not mp3:
            messagebox.showerror("Голосовой пакет", "В выбранной папке не найдено MP3.")
            return

        name = simpledialog.askstring(
            "Имя пакета",
            "Имя tar.gz (без пути):",
            initialvalue=f"custom_roidmi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        )
        if not name:
            return
        name = re.sub(r'[^A-Za-zА-Яа-я0-9._()\\-]+', "_", name)
        if not name.lower().endswith(".tar.gz"):
            name += ".tar.gz"
        dst = VOICEPACKS_DIR / name

        def task():
            with tarfile.open(dst, "w:gz") as tf:
                for p in files:
                    # Never include links outside the selected folder.
                    if p.is_symlink():
                        continue
                    tf.add(p, arcname=str(p.relative_to(folder)), recursive=False)
            return {
                "path": dst,
                "size": dst.stat().st_size,
                "md5": self._hash_file(dst, "md5"),
                "files": len(files),
                "mp3": len(mp3),
                "has_voice_config": any(p.name.lower() == "voice_config.json" for p in files),
            }

        def done(info):
            self.refresh_voice_library()
            self.voice_pack_path_var.set(str(info["path"]))
            self.voice_pack_info_var.set(
                f"Собрано: {info['path'].name}\\n"
                f"Файлов: {info['files']}; MP3: {info['mp3']}; "
                f"voice_config.json: {'да' if info['has_voice_config'] else 'нет'}\\n"
                f"Размер: {self._human_size(info['size'])}; MD5: {info['md5']}"
            )
            messagebox.showinfo(
                "Голосовой пакет",
                "tar.gz создан. Совместимость зависит от структуры выбранных исходных файлов; "
                "программа не отправляет пакет в робот без подтверждённой схемы update-audio."
            )

        self.async_run(task, done, "Сборка голосового tar.gz...")

    def open_voicepacks_folder(self):
        VOICEPACKS_DIR.mkdir(exist_ok=True)
        try:
            os.startfile(str(VOICEPACKS_DIR))
        except Exception as e:
            messagebox.showerror("Голоса", str(e))

    def _selected_voice_source(self):
        if self.voice_sources_tree is None:
            return None
        sel = self.voice_sources_tree.selection()
        if not sel:
            return None
        try:
            idx = int(sel[0])
            return VOICE_SOURCES[idx]
        except Exception:
            return None

    def open_selected_voice_source(self):
        source = self._selected_voice_source()
        if not source:
            messagebox.showinfo("Каталог голосов", "Выберите источник.")
            return
        webbrowser.open(source["url"])

    def _download_voice_file(self, url):
        parsed = urlparse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Разрешены только http/https ссылки.")
        name = Path(urlparse.unquote(parsed.path)).name or "voicepack_download"
        name = re.sub(r'[^A-Za-zА-Яа-я0-9._()\\-]+', "_", name)
        if not name:
            name = "voicepack_download"
        dst = VOICEPACKS_DIR / name
        max_bytes = 120 * 1024 * 1024

        with requests.get(
            url,
            stream=True,
            timeout=30,
            headers={"User-Agent": "ROIDMI-EVE-Plus-Control/20.5"}
        ) as response:
            response.raise_for_status()
            try:
                declared = int(response.headers.get("Content-Length") or 0)
            except Exception:
                declared = 0
            if declared > max_bytes:
                raise RuntimeError("Файл больше 120 MiB; загрузка остановлена.")
            total = 0
            with dst.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        raise RuntimeError("Файл превысил лимит 120 MiB.")
                    f.write(chunk)
        return dst

    def download_selected_voice_source(self):
        source = self._selected_voice_source()
        if not source:
            messagebox.showinfo("Каталог голосов", "Выберите источник.")
            return
        url = source.get("direct_url")
        if not url:
            messagebox.showinfo(
                "Каталог голосов",
                "У этого источника нет прямой ссылки на один файл. "
                "Открою страницу, где можно выбрать пакет."
            )
            webbrowser.open(source["url"])
            return
        self.voice_download_url_var.set(url)
        self.download_voice_url()

    def download_voice_url(self):
        url = self.voice_download_url_var.get().strip()
        if not url:
            messagebox.showinfo("Скачать голос", "Вставьте прямую http/https ссылку.")
            return

        def task():
            return self._download_voice_file(url)

        def done(path):
            self.voice_pack_path_var.set(str(path))
            self.voice_library_status_var.set(f"Скачано: {path.name}")
            self.refresh_voice_library()
            messagebox.showinfo(
                "Голос скачан",
                f"Файл сохранён в локальную библиотеку:\n{path}\n\n"
                "Архив не запускается и автоматически не прошивается в робот."
            )

        self.async_run(task, done, "Скачивание голосового пакета...")

    def _voice_preset_changed(self, event=None):
        val = self.voice_preset_var.get()
        if val.startswith("Русский"):
            self.voice_raw_var.set("girl_ru")
        elif val.startswith("English"):
            self.voice_raw_var.set("girl_en")

    def _set_voice_quick(self, voice_id):
        self.voice_raw_var.set(voice_id)
        self.voice_preset_var.set(
            "Русский штатный (girl_ru)" if voice_id == "girl_ru"
            else "English штатный (girl_en)"
        )
        self.apply_voice()

    def select_voice_pack(self):
        path = filedialog.askopenfilename(
            title="Выберите голосовой пакет ROIDMI",
            filetypes=[
                ("Voice package", "*.tar.gz"),
                ("GZip archive", "*.gz"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        p = Path(path)
        self.voice_pack_path_var.set(str(p))
        try:
            size = p.stat().st_size
            md5 = self._hash_file(p, "md5")
            mp3_count = 0
            total_members = 0
            valid_tar = False
            try:
                with tarfile.open(p, "r:gz") as tf:
                    members = [m for m in tf.getmembers() if m.isfile()]
                    total_members = len(members)
                    mp3_count = sum(1 for m in members if m.name.lower().endswith(".mp3"))
                    valid_tar = True
            except Exception:
                valid_tar = False

            msg = (
                f"Файл: {p.name}\n"
                f"Размер: {size:,} байт\n"
                f"MD5: {md5}\n"
                f"tar.gz: {'да' if valid_tar else 'не подтверждён'}"
            )
            if valid_tar:
                msg += f"\nФайлов в архиве: {total_members}; MP3: {mp3_count}"
            self.voice_pack_info_var.set(msg)
            try:
                local_copy = VOICEPACKS_DIR / p.name
                if p.resolve() != local_copy.resolve():
                    shutil.copy2(p, local_copy)
                self.voice_pack_path_var.set(str(local_copy))
                self.refresh_voice_library()
            except Exception as copy_error:
                self.voice_library_status_var.set(
                    f"Файл выбран, но не скопирован в библиотеку: {copy_error}"
                )
        except Exception as e:
            self.voice_pack_info_var.set(f"Не удалось проверить пакет: {e}")

    def voice_pack_name_to_id(self):
        raw = self.voice_pack_path_var.get().strip()
        if not raw:
            messagebox.showinfo("Голосовой пакет", "Сначала выберите файл.")
            return
        name = Path(raw).name
        self.voice_raw_var.set(name)
        self.voice_preset_var.set("Свой ID / имя пакета")
        self.voice_status_var.set(
            f"В поле audio установлено имя файла: {name}. "
            "Отправляйте его только если этот идентификатор уже доступен роботу/серверу голосовых пакетов."
        )

    def _cloud_voice_context(self):
        client = self.active_cloud_client or self.pending_cloud_client
        dev = self.active_cloud_device
        if not client or not dev:
            raise ValueError(
                "Xiaomi Cloud-сессия ещё не создана. Сначала нажмите "
                "«Получить комнаты из карты» во вкладке «Комнаты и карта»."
            )
        country = dev.get("country")
        did = dev.get("device_id")
        if not country or not did:
            raise ValueError("Не найден country/device_id Xiaomi Cloud.")
        return client, country, did

    def apply_voice(self):
        audio = self.voice_raw_var.get().strip()
        if not audio:
            messagebox.showerror("Голос", "Введите параметр audio, например girl_ru.")
            return
        if len(audio) > 1024:
            messagebox.showerror("Голос", "Параметр audio слишком длинный.")
            return
        if not messagebox.askyesno(
            "Смена голоса",
            f"Отправить роботу штатную команду set-voice (8/12)?\n\n"
            f"audio = {audio}\n\n"
            "После переключения робот может несколько секунд загружать/активировать пакет."
        ):
            return

        use_cloud = bool(self.voice_cloud_fallback_var.get())

        def task():
            local_error = None
            try:
                d = self.ensure_device()
                # MIoT spec: action 8/12, one input property 8/27 (string audio).
                if hasattr(d, "call_action_by"):
                    response = d.call_action_by(8, 12, [audio])
                else:
                    response = d.call_action_from_mapping("set_voice", [audio])
                time.sleep(2.0)
                try:
                    after = d.status().data
                except Exception:
                    after = dict(self.last_data or {})
                    after["current_audio"] = audio
                return {
                    "mode": "LAN",
                    "response": response,
                    "after": after,
                    "audio": audio,
                }
            except Exception as e:
                local_error = str(e)

            if not use_cloud:
                raise RuntimeError(
                    f"LAN set-voice не выполнен: {local_error}"
                )

            client, country, did = self._cloud_voice_context()
            response = client.do_miot_action(country, did, 8, 12, [audio])
            return {
                "mode": "Xiaomi Cloud",
                "response": response,
                "after": dict(self.last_data or {}),
                "audio": audio,
                "local_error": local_error,
            }

        def done(result):
            after = result.get("after") or {}
            if after:
                self.last_data.update(after)
                self._show_status(self.last_data)
                self._show_raw(self.last_data)
            self.voice_current_var.set(
                self.last_data.get("current_audio") or result.get("audio") or "-"
            )
            self.voice_status_var.set(
                f"Команда set-voice отправлена через {result.get('mode')}. "
                f"Запрошенный audio: {result.get('audio')}. "
                "Нажмите «Обновить» через 5-15 секунд и проверьте current_audio."
            )
            with (ROOT / "voice_actions.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " " +
                    json.dumps(
                        {
                            "mode": result.get("mode"),
                            "audio": result.get("audio"),
                            "response": result.get("response"),
                            "local_error": result.get("local_error"),
                        },
                        ensure_ascii=False,
                        default=str
                    ) + "\n"
                )
            self.statusbar_var.set(
                f"Голос: set-voice отправлен через {result.get('mode')}."
            )
            self._refresh_dashboard()

        self.async_run(task, done, "Переключение голоса робота...")

    def _smart_optimization_report_text(self):
        s = SMART_OPTIMIZATION_STATS
        area_reduction = (
            100.0 * (s["current_weekly_nominal_area_m2"] - s["optimized_weekly_nominal_area_m2"])
            / s["current_weekly_nominal_area_m2"]
        )
        water_reduction = (
            100.0 * (s["current_water_load_units"] - s["optimized_water_load_units"])
            / s["current_water_load_units"]
        )
        current_hours = (
            s["current_weekly_nominal_area_m2"] * s["historical_seconds_per_m2"] / 3600.0
        )
        optimized_hours = (
            s["optimized_weekly_nominal_area_m2"] * s["historical_seconds_per_m2"] / 3600.0
        )
        saved_minutes = (current_hours - optimized_hours) * 60.0

        return (
            "SMART-ОПТИМИЗАЦИЯ ROIDMI EVE PLUS\\n"
            "====================================\\n\\n"
            "Основа расчёта\\n"
            f"- фактическая площадь сегментов карты: {s['mapped_area_m2']:.2f} м²\\n"
            "- база: ванная, Room 5\\n"
            "- кухня: 8.44 м², плитка, высокая загрязнённость\\n"
            "- спальня: 9.61 м², ламинат, низкая загрязнённость\\n"
            "- коридор: 5.29 м², плитка/ламинат, высокая загрязнённость\\n"
            "- зал: 4.01 м², ламинат + ковёр, средняя загрязнённость\\n"
            "- ванная: 3.02 м², плитка, средняя загрязнённость\\n"
            "- порядок профильной уборки: Спальня -> Зал -> Кухня -> Коридор -> Ванная\\n\\n"
            "Недельный график\\n"
            "- Пн / Чт / Сб, 11:00: вся квартира, fan 3, вода 1, сухая+влажная\\n"
            "- Вт / Ср / Пт, 11:00: кухня + коридор, fan 4, вода 2\\n"
            "- Вс, 11:00: кухня + коридор + ванная, fan 4, вода 2\\n\\n"
            "Почему так\\n"
            "- кухня и коридор получают уборку каждый день;\\n"
            "- спальня и зал сокращены с 4 до 3 полных уборок в неделю;\\n"
            "- на общих уборках вода снижена до 1 для ламината и зоны с ковром;\\n"
            "- ковровый boost остаётся включён;\\n"
            "- double-clean выключен для регулярных уборок, потому что грязные зоны убираются ежедневно;\\n"
            "- Y-маршрут оставлен только для профильной уборки ванной / плитки;\\n"
            "- самоочистка станции: каждая 2-я уборка вместо каждой, чтобы сократить шум и расход мешка.\\n\\n"
            "Оценка экономии\\n"
            f"- номинальный недельный пробег по площади: {s['current_weekly_nominal_area_m2']:.2f} -> "
            f"{s['optimized_weekly_nominal_area_m2']:.2f} м² ({area_reduction:.1f}% меньше);\\n"
            f"- расчётная водяная нагрузка: {s['current_water_load_units']:.1f} -> "
            f"{s['optimized_water_load_units']:.1f} условных единиц ({water_reduction:.1f}% меньше);\\n"
            f"- по вашей исторической средней скорости уборки: примерно {current_hours:.2f} -> "
            f"{optimized_hours:.2f} ч/нед., экономия около {saved_minutes:.0f} мин/нед.\\n\\n"
            "Важно\\n"
            "- скорость движения робота отдельно в MIoT v60 не регулируется;\\n"
            "- параметр 'скорость' в интерфейсе фактически означает мощность всасывания fan 1-4;\\n"
            "- фактическое время зависит от мебели, препятствий, ковра и повторных проходов.\\n"
        )

    def show_smart_optimization_report(self):
        win = tk.Toplevel(self)
        win.title("Smart-оптимизация ROIDMI EVE Plus")
        win.geometry("980x720")
        txt = tk.Text(
            win, wrap="word", bg="#121b2e", fg="#eef4ff",
            insertbackground="white", relief="flat", font=("Segoe UI", 10)
        )
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", self._smart_optimization_report_text())
        txt.configure(state="disabled")
        buttons = ttk.Frame(win)
        buttons.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(
            buttons, text="Загрузить расписание в редактор",
            command=self.load_smart_schedule_local
        ).pack(side="left", padx=3)
        ttk.Button(
            buttons, text="Применить smart-профили комнат",
            command=self.apply_smart_room_profiles
        ).pack(side="left", padx=3)
        ttk.Button(
            buttons, text="Применить всё в робот",
            style="Accent.TButton", command=self.apply_smart_optimization_to_robot
        ).pack(side="left", padx=3)
        ttk.Button(buttons, text="Закрыть", command=win.destroy).pack(side="right")

    def _smart_timing_payload(self):
        # Preserve the timezone actually reported by the robot when available.
        current = self._parse_timing((self.last_data or {}).get("timing"))
        tz = current.get("tz", SMART_OPTIMIZED_TIMING["tz"])
        tzs = current.get("tzs", SMART_OPTIMIZED_TIMING["tzs"])
        payload = json.loads(json.dumps(SMART_OPTIMIZED_TIMING))
        payload["tz"] = tz
        payload["tzs"] = tzs
        return payload

    def load_smart_schedule_local(self):
        self.current_timing = self._smart_timing_payload()
        self._populate_schedule(self.current_timing)
        self.smart_optimization_status_var.set(
            "Smart-расписание загружено в редактор. Оно ещё не записано в робот."
        )
        try:
            self.nb.select(self.tab_schedule)
        except Exception:
            pass

    def apply_smart_room_profiles(self):
        for rid in range(1, 6):
            p = SMART_ROOM_PROFILES[rid]
            self.room_profile_floor_vars[rid].set(p["floor_type"])
            self.room_profile_dirt_vars[rid].set(p["dirt_level"])
            self.room_profile_fan_vars[rid].set(reverse_lookup(FAN, p["fan"]))
            self.room_profile_water_vars[rid].set(reverse_lookup(WATER, p["water"]))
            self.room_profile_sweep_vars[rid].set(reverse_lookup(SWEEP_TYPE, p["sweep_type"]))
            self.room_profile_path_vars[rid].set(reverse_lookup(PATH_MODE, p["path_mode"]))
            self.room_profile_double_vars[rid].set(bool(p["double_clean"]))
        self.room_order_var.set(",".join(map(str, OPTIMAL_ROOM_ORDER)))
        self._save_room_profiles(show_message=False)
        self.room_profiles_status_var.set(
            "Smart-профили применены: ежедневные грязные зоны без лишнего double-clean; "
            "низкая вода для ламината; Y-маршрут для ванной."
        )
        self.smart_optimization_status_var.set("Smart-профили комнат сохранены.")

    def apply_smart_optimization_to_robot(self):
        timing = self._smart_timing_payload()
        props = dict(SMART_OPTIMIZED_PROPERTIES)

        if not messagebox.askyesno(
            "Применить Smart-оптимизацию",
            "Будут изменены общие настройки и полностью заменено расписание робота.\\n\\n"
            "План:\\n"
            "• Пн/Чт/Сб - вся квартира, fan 3, вода 1\\n"
            "• Вт/Ср/Пт - кухня+коридор, fan 4, вода 2\\n"
            "• Вс - кухня+коридор+ванная, fan 4, вода 2\\n"
            "• Carpet boost: ВКЛ\\n"
            "• Double-clean: ВЫКЛ\\n"
            "• Самоочистка станции: каждая 2-я уборка\\n\\n"
            "Перед записью будет сделана резервная копия. Продолжить?"
        ):
            return

        # Keep local per-room profiles aligned with the optimized plan.
        self.apply_smart_room_profiles()
        self.current_timing = timing
        self._populate_schedule(timing)

        def task():
            d = self.ensure_device()
            before = d.status().data
            self.backup_data(before, "before_smart_optimization")
            results = {}

            for key, val in props.items():
                try:
                    results[key] = d.set_property(key, val)
                except Exception as e:
                    results[key] = f"ERROR: {e}"

            try:
                raw_timing = json.dumps(
                    timing, ensure_ascii=False, separators=(",", ":")
                )
                results["timing"] = d.set_timing(raw_timing)
            except Exception as e:
                results["timing"] = f"ERROR: {e}"

            after = d.status().data
            return {"before": before, "after": after, "results": results}

        def done(result):
            after = result["after"]
            results = result["results"]
            self.on_status(after)
            self._update_user_profile(
                status=after,
                timing=timing,
                room_order=OPTIMAL_ROOM_ORDER,
                property_values=props,
            )
            self._write_last_applied(
                after, results=results, room_order=OPTIMAL_ROOM_ORDER
            )
            errors = {
                k: v for k, v in results.items()
                if isinstance(v, str) and v.startswith("ERROR")
            }
            if errors:
                self.smart_optimization_status_var.set(
                    "Smart-оптимизация применена частично. Есть ошибки записи."
                )
                messagebox.showwarning(
                    "Smart-оптимизация",
                    "Часть параметров не записалась:\\n\\n" +
                    json.dumps(errors, ensure_ascii=False, indent=2)
                )
            else:
                self.smart_optimization_status_var.set(
                    "Smart-оптимизация записана в робот и сохранена как пользовательский профиль."
                )
                messagebox.showinfo(
                    "Smart-оптимизация",
                    "Оптимизированные настройки и расписание успешно записаны в робот."
                )

        self.async_run(task, done, "Применение Smart-оптимизации...")

    def _build_schedule_tab(self):
        top = ttk.Frame(self.tab_schedule)
        top.pack(fill="both", expand=True, padx=8, pady=8)

        smart = ttk.LabelFrame(top, text="Оптимизированный недельный план", style="Section.TLabelframe")
        smart.pack(fill="x", pady=(0, 7))
        smart_body = ttk.Frame(smart, style="Card.TFrame")
        smart_body.pack(fill="x", padx=9, pady=8)
        ttk.Label(
            smart_body,
            text=(
                "Пн/Чт/Сб 11:00 - вся квартира: мощность 3, вода 1.  "
                "Вт/Ср/Пт 11:00 - кухня + коридор: MAX 4, вода 2.  "
                "Вс 11:00 - кухня + коридор + ванная: MAX 4, вода 2."
            ),
            style="Muted.TLabel", wraplength=1120, justify="left"
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(
            smart_body, text="ПОКАЗАТЬ РАСЧЁТ",
            command=self.show_smart_optimization_report
        ).pack(side="right", padx=3)
        ttk.Button(
            smart_body, text="ЗАГРУЗИТЬ В РЕДАКТОР",
            command=self.load_smart_schedule_local
        ).pack(side="right", padx=3)
        ttk.Button(
            smart_body, text="ПРИМЕНИТЬ ВСЁ В РОБОТ",
            style="Accent.TButton", command=self.apply_smart_optimization_to_robot
        ).pack(side="right", padx=3)
        ttk.Label(
            smart, textvariable=self.smart_optimization_status_var,
            style="Muted.TLabel", wraplength=1500, justify="left"
        ).pack(anchor="w", padx=11, pady=(0, 7))

        table_frame = ttk.LabelFrame(top, text="Текущее расписание")
        table_frame.pack(fill="both", expand=True)

        cols = ("idx","time","enabled","days","fan","type","water","rooms")
        self.sch_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=9)
        headings = {
            "idx":"№","time":"Время","enabled":"Вкл.","days":"Дни",
            "fan":"Мощн.","type":"Тип","water":"Вода","rooms":"Комнаты"
        }
        widths = {"idx":40,"time":75,"enabled":50,"days":190,"fan":75,"type":130,"water":75,"rooms":180}
        for c in cols:
            self.sch_tree.heading(c, text=headings[c])
            self.sch_tree.column(c, width=widths[c], anchor="center")
        self.sch_tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.sch_tree.bind("<<TreeviewSelect>>", self.load_selected_schedule)

        edit = ttk.LabelFrame(top, text="Редактор строки расписания")
        edit.pack(fill="x", pady=(8,0))

        self.sch_hour = tk.IntVar(value=9)
        self.sch_min = tk.IntVar(value=0)
        self.sch_enabled = tk.BooleanVar(value=True)
        self.sch_fan = tk.StringVar(value=reverse_lookup(FAN,3))
        self.sch_type = tk.StringVar(value=reverse_lookup(SWEEP_TYPE,0))
        self.sch_water = tk.StringVar(value=reverse_lookup(WATER,0))
        self.sch_rooms = tk.StringVar(value="")
        self.sch_index = None
        self.day_vars = {d: tk.BooleanVar(value=(d in [1,2,3,4,5])) for d in DAY_ORDER}

        ttk.Label(edit,text="Время:").grid(row=0,column=0,padx=5,pady=6)
        ttk.Spinbox(edit,from_=0,to=23,textvariable=self.sch_hour,width=4,format="%02.0f").grid(row=0,column=1)
        ttk.Label(edit,text=":").grid(row=0,column=2)
        ttk.Spinbox(edit,from_=0,to=59,textvariable=self.sch_min,width=4,format="%02.0f").grid(row=0,column=3)
        ttk.Checkbutton(edit,text="Включено",variable=self.sch_enabled).grid(row=0,column=4,padx=8)

        col=5
        for d in DAY_ORDER:
            ttk.Checkbutton(edit,text=DAY_NAMES[d],variable=self.day_vars[d]).grid(row=0,column=col,padx=2)
            col += 1

        ttk.Label(edit,text="Мощность:").grid(row=1,column=0,padx=5,pady=6,sticky="e")
        ttk.Combobox(edit,textvariable=self.sch_fan,values=list(FAN.keys()),state="readonly",width=21).grid(row=1,column=1,columnspan=3,sticky="w")
        ttk.Label(edit,text="Тип:").grid(row=1,column=4,padx=5,sticky="e")
        ttk.Combobox(edit,textvariable=self.sch_type,values=list(SWEEP_TYPE.keys()),state="readonly",width=23).grid(row=1,column=5,columnspan=3,sticky="w")
        ttk.Label(edit,text="Вода:").grid(row=1,column=8,padx=5,sticky="e")
        ttk.Combobox(edit,textvariable=self.sch_water,values=list(WATER.keys()),state="readonly",width=21).grid(row=1,column=9,columnspan=3,sticky="w")

        ttk.Label(edit,text="ID комнат через запятую:").grid(row=2,column=0,columnspan=2,padx=5,pady=6,sticky="e")
        ttk.Entry(edit,textvariable=self.sch_rooms,width=38).grid(row=2,column=2,columnspan=4,sticky="w")
        ttk.Label(edit,text="пусто = все комнаты",foreground="#555").grid(row=2,column=6,columnspan=3,sticky="w")

        ttk.Button(edit,text="Добавить как новую",command=self.add_schedule).grid(row=3,column=0,columnspan=3,padx=5,pady=8)
        ttk.Button(edit,text="Обновить выбранную",command=self.update_schedule).grid(row=3,column=3,columnspan=3,padx=5,pady=8)
        ttk.Button(edit,text="Удалить выбранную",command=self.delete_schedule).grid(row=3,column=6,columnspan=3,padx=5,pady=8)
        ttk.Button(edit,text="ЗАПИСАТЬ РАСПИСАНИЕ В РОБОТ",command=self.save_schedule_to_robot).grid(row=3,column=9,columnspan=4,padx=5,pady=8)

        ttk.Label(
            top,
            text=("LIVE AUTOSAVE: после добавления, изменения или удаления строки расписание сразу записывается в робот. "
                  "Перед фактической записью создаётся резервная копия. Неизвестное восьмое поле существующих строк сохраняется."),
            foreground="#8a5200",
            wraplength=1000
        ).pack(anchor="w", pady=(6,0))

    def _build_rooms_tab(self):
        top = ttk.Frame(self.tab_rooms)
        top.pack(fill="both", expand=True, padx=10, pady=10)

        auth = ttk.LabelFrame(top, text="Xiaomi Cloud - только для чтения карты")
        auth.pack(fill="x")

        self.cloud_user_var = tk.StringVar()
        self.cloud_pass_var = tk.StringVar()
        self.cloud_country_var = tk.StringVar(value="auto")

        ttk.Label(auth, text="Логин Xiaomi:").grid(row=0, column=0, padx=6, pady=7, sticky="e")
        ttk.Entry(auth, textvariable=self.cloud_user_var, width=34).grid(row=0, column=1, padx=6, pady=7)

        ttk.Label(auth, text="Пароль:").grid(row=0, column=2, padx=6, pady=7, sticky="e")
        ttk.Entry(auth, textvariable=self.cloud_pass_var, width=28, show="•").grid(row=0, column=3, padx=6, pady=7)

        ttk.Label(auth, text="Регион:").grid(row=0, column=4, padx=6, pady=7, sticky="e")
        ttk.Combobox(
            auth, textvariable=self.cloud_country_var,
            values=["auto","ru","de","cn","us","sg","tw","in","i2"],
            state="readonly", width=8
        ).grid(row=0, column=5, padx=6, pady=7)

        ttk.Button(auth, text="Получить комнаты из карты", command=self.fetch_rooms).grid(
            row=0, column=6, padx=8, pady=7
        )
        self.btn_2fa = ttk.Button(auth, text="Открыть подтверждение 2FA", command=self.open_cloud_2fa, state="disabled")
        self.btn_2fa.grid(row=0, column=7, padx=6, pady=7)

        ttk.Button(
            auth, text="Импорт сессии старой версии",
            command=self.import_cloud_session_from_file
        ).grid(row=1, column=0, columnspan=2, padx=6, pady=(0, 5), sticky="w")

        ttk.Label(
            auth, textvariable=self.cloud_session_status_var,
            foreground="#4f9cff", wraplength=1150, justify="left"
        ).grid(row=1, column=2, columnspan=6, padx=7, pady=(0,5), sticky="w")

        ttk.Label(
            auth,
            text=(
                "Начиная с v20.8 авторизация Xiaomi Cloud хранится общей для всех версий в "
                "%LOCALAPPDATA%\\ROIDMI_EVE_Plus_Control\\CLOUD_SESSION.json. "
                "При обновлении программа сначала использует эту сессию и автоматически ищет CLOUD_SESSION.json "
                "в соседних старых версиях. Пароль и код подтверждения нужны только если Xiaomi отозвала/просрочила сессию."
            ),
            foreground="#555", wraplength=1250, justify="left"
        ).grid(row=2, column=0, columnspan=8, padx=7, pady=(0,7), sticky="w")

        body = ttk.LabelFrame(top, text="Комнаты текущей карты")
        body.pack(fill="both", expand=True, pady=(10,0))

        cols = ("id","friendly","system","clean_count")
        self.rooms_tree = ttk.Treeview(body, columns=cols, show="headings", selectmode="extended", height=14)
        self.rooms_tree.heading("id", text="ID")
        self.rooms_tree.heading("friendly", text="Комната")
        self.rooms_tree.heading("system", text="Имя в карте")
        self.rooms_tree.heading("clean_count", text="CleanCount")
        self.rooms_tree.column("id", width=70, anchor="center")
        self.rooms_tree.column("friendly", width=250, anchor="w")
        self.rooms_tree.column("system", width=250, anchor="w")
        self.rooms_tree.column("clean_count", width=120, anchor="center")
        self.rooms_tree.pack(fill="both", expand=True, padx=7, pady=7)

        controls = ttk.Frame(body)
        controls.pack(fill="x", padx=7, pady=(0,8))
        ttk.Button(
            controls, text="Вставить выбранные ID в расписание",
            command=self.rooms_to_schedule
        ).pack(side="left", padx=4)
        ttk.Button(
            controls, text="Экспорт списка комнат JSON",
            command=self.export_rooms
        ).pack(side="left", padx=4)
        ttk.Button(
            controls, text="Скачать реальную карту ZIP",
            style="Accent.TButton",
            command=self.export_live_map_bundle
        ).pack(side="left", padx=4)
        ttk.Button(
            controls, text="Сохранить PNG карты",
            command=self.save_live_map_png_as
        ).pack(side="left", padx=4)
        ttk.Button(
            controls, text="Анализ / оптимизация карты",
            command=self.show_map_optimization_report
        ).pack(side="left", padx=4)

        self.rooms_info_var = tk.StringVar(value="Карта ещё не загружена.")
        ttk.Label(controls, textvariable=self.dashboard_live_map_status_var, foreground="#4f9cff").pack(side="left", padx=15)
        ttk.Label(controls, textvariable=self.rooms_info_var, foreground="#555").pack(side="left", padx=15)

        ttk.Label(
            body, textvariable=self.map_optimization_status_var,
            foreground="#4f9cff", wraplength=1050, justify="left"
        ).pack(anchor="w", padx=8, pady=(0,4))

        ttk.Label(
            body,
            text=("Список autoArea сам по себе содержит минимум метаданных, но raw-карта ROIDMI содержит "
                  "пиксельную геометрию комнат. v20.4 считает фактические пиксели, площадь, центры и соседство "
                  "комнат из raw-map и не выдумывает недостающие поля. CleanCount показывается для контроля."),
            foreground="#555", wraplength=1050, justify="left"
        ).pack(anchor="w", padx=8, pady=(0,8))

    def _default_room_profiles(self):
        return {
            str(rid): dict(profile)
            for rid, profile in DEFAULT_ROOM_PROFILES.items()
        }

    def _load_room_profiles(self):
        if ROOM_PROFILES_PATH.exists():
            try:
                raw = json.loads(ROOM_PROFILES_PATH.read_text(encoding="utf-8-sig"))
                if isinstance(raw, dict):
                    result = self._default_room_profiles()
                    for rid in range(1, 6):
                        src = raw.get(str(rid)) or raw.get(rid)
                        if isinstance(src, dict):
                            result[str(rid)].update(src)
                    return result
            except Exception as e:
                with (ROOT / "room_profiles.log").open("a", encoding="utf-8") as f:
                    f.write(datetime.now().isoformat() + f" LOAD_ERROR {e}\n")
        profiles = self._default_room_profiles()
        ROOM_PROFILES_PATH.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return profiles

    def _save_room_profiles(self, show_message=True):
        existing = self._read_room_profiles_payload()
        profiles = {}
        for rid in range(1, 6):
            profiles[str(rid)] = dict(existing.get(str(rid), {}))
            profiles[str(rid)].update({
                "name": ROOM_LABELS[rid],
                "floor_type": self.room_profile_floor_vars[rid].get(),
                "dirt_level": self.room_profile_dirt_vars[rid].get(),
                "fan": FAN[self.room_profile_fan_vars[rid].get()],
                "water": WATER[self.room_profile_water_vars[rid].get()],
                "sweep_type": SWEEP_TYPE[self.room_profile_sweep_vars[rid].get()],
                "path_mode": PATH_MODE[self.room_profile_path_vars[rid].get()],
                "double_clean": bool(self.room_profile_double_vars[rid].get()),
            })
        payload = {
            "model": MODEL,
            "saved_at": datetime.now().astimezone().isoformat(),
            "profiles": profiles,
            "implementation": "safe_runtime_profile_before_each_room",
            "native_area_custom": {
                "exists": True,
                "siid": 13,
                "aiid": 10,
                "enabled": False,
                "reason": "firmware auto-area string schema not confirmed"
            }
        }
        atomic_write_json(ROOM_PROFILES_PATH, payload)
        self.room_profiles_status_var.set("Профили комнат сохранены в ROOM_PROFILES.json.")
        if show_message:
            messagebox.showinfo(
                "Режимы по комнатам",
                "Профили сохранены.\n\n"
                "Они применяются безопасно перед запуском каждой комнаты: "
                "мощность, вода, тип уборки, маршрут и double-clean."
            )
        return profiles

    def _read_room_profiles_payload(self):
        profiles = self._default_room_profiles()
        if ROOM_PROFILES_PATH.exists():
            try:
                obj = json.loads(ROOM_PROFILES_PATH.read_text(encoding="utf-8-sig"))
                raw = obj.get("profiles") if isinstance(obj, dict) and "profiles" in obj else obj
                if isinstance(raw, dict):
                    for rid in range(1, 6):
                        p = raw.get(str(rid)) or raw.get(rid)
                        if isinstance(p, dict):
                            profiles[str(rid)].update(p)
            except Exception:
                pass
        return profiles

    def _populate_room_profiles_ui(self):
        profiles = self._read_room_profiles_payload()
        for rid in range(1, 6):
            p = profiles[str(rid)]
            self.room_profile_fan_vars[rid].set(reverse_lookup(FAN, int(p.get("fan", DEFAULT_ROOM_PROFILES[rid]["fan"]))))
            self.room_profile_water_vars[rid].set(reverse_lookup(WATER, int(p.get("water", DEFAULT_ROOM_PROFILES[rid]["water"]))))
            self.room_profile_sweep_vars[rid].set(reverse_lookup(SWEEP_TYPE, int(p.get("sweep_type", DEFAULT_ROOM_PROFILES[rid]["sweep_type"]))))
            self.room_profile_path_vars[rid].set(reverse_lookup(PATH_MODE, int(p.get("path_mode", DEFAULT_ROOM_PROFILES[rid]["path_mode"]))))
            self.room_profile_double_vars[rid].set(bool(p.get("double_clean", False)))
            self.room_profile_floor_vars[rid].set(str(p.get("floor_type", DEFAULT_ROOM_PROFILES[rid]["floor_type"])))
            self.room_profile_dirt_vars[rid].set(str(p.get("dirt_level", DEFAULT_ROOM_PROFILES[rid]["dirt_level"])))

    def _build_room_modes_tab(self):
        root = ttk.Frame(self.tab_room_modes)
        root.pack(fill="both", expand=True, padx=14, pady=14)

        head = ttk.Frame(root, style="Toolbar.TFrame")
        head.pack(fill="x", pady=(0, 12))
        ttk.Label(head, text="Режимы отдельно для каждой комнаты", style="Header.TLabel").pack(anchor="w", padx=16, pady=(14, 2))
        ttk.Label(
            head,
            text=(
                "Безопасная реализация: перед запуском каждой комнаты программа выставляет её профиль, "
                "запускает только эту комнату и после завершения переходит к следующей."
            ),
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=16, pady=(0, 14))

        table = ttk.LabelFrame(root, text="Профили комнат", style="Section.TLabelframe")
        table.pack(fill="x")

        headers = ["Вкл.", "ID", "Комната", "Покрытие", "Загрязнение", "Мощность", "Вода", "Тип уборки", "Маршрут", "2x"]
        for col, h in enumerate(headers):
            ttk.Label(table, text=h, font=("Segoe UI Semibold", 10)).grid(
                row=0, column=col, padx=6, pady=8, sticky="w"
            )

        for row, rid in enumerate([1,2,3,4,5], start=1):
            self.room_profile_select_vars[rid] = tk.BooleanVar(value=True)
            self.room_profile_fan_vars[rid] = tk.StringVar()
            self.room_profile_water_vars[rid] = tk.StringVar()
            self.room_profile_sweep_vars[rid] = tk.StringVar()
            self.room_profile_path_vars[rid] = tk.StringVar()
            self.room_profile_double_vars[rid] = tk.BooleanVar(value=False)
            self.room_profile_floor_vars[rid] = tk.StringVar(value=DEFAULT_ROOM_PROFILES[rid]["floor_type"])
            self.room_profile_dirt_vars[rid] = tk.StringVar(value=DEFAULT_ROOM_PROFILES[rid]["dirt_level"])

            ttk.Checkbutton(table, variable=self.room_profile_select_vars[rid]).grid(row=row, column=0, padx=3, pady=5)
            ttk.Label(table, text=str(rid)).grid(row=row, column=1, padx=3, pady=5)
            ttk.Label(table, text=ROOM_LABELS[rid], font=("Segoe UI Semibold", 10)).grid(row=row, column=2, padx=3, pady=5, sticky="w")
            ttk.Combobox(
                table, textvariable=self.room_profile_floor_vars[rid],
                values=FLOOR_TYPES, state="readonly", width=14
            ).grid(row=row, column=3, padx=3, pady=5)
            ttk.Combobox(
                table, textvariable=self.room_profile_dirt_vars[rid],
                values=DIRT_LEVELS, state="readonly", width=10
            ).grid(row=row, column=4, padx=3, pady=5)
            ttk.Combobox(
                table, textvariable=self.room_profile_fan_vars[rid],
                values=list(FAN.keys()), state="readonly", width=13
            ).grid(row=row, column=5, padx=3, pady=5)
            ttk.Combobox(
                table, textvariable=self.room_profile_water_vars[rid],
                values=list(WATER.keys()), state="readonly", width=13
            ).grid(row=row, column=6, padx=3, pady=5)
            ttk.Combobox(
                table, textvariable=self.room_profile_sweep_vars[rid],
                values=list(SWEEP_TYPE.keys()), state="readonly", width=16
            ).grid(row=row, column=7, padx=3, pady=5)
            ttk.Combobox(
                table, textvariable=self.room_profile_path_vars[rid],
                values=list(PATH_MODE.keys()), state="readonly", width=15
            ).grid(row=row, column=8, padx=3, pady=5)
            ttk.Checkbutton(table, variable=self.room_profile_double_vars[rid]).grid(row=row, column=9, padx=3, pady=5)

        self._populate_room_profiles_ui()

        controls = ttk.Frame(root, style="Card.TFrame")
        controls.pack(fill="x", pady=(12, 0))
        ttk.Button(
            controls, text="СОХРАНИТЬ ПРОФИЛИ",
            style="Accent.TButton", command=self._save_room_profiles
        ).pack(side="left", padx=6, pady=10)
        ttk.Button(
            controls, text="АВТОПОДБОР ПО ПОЛУ И ЗАГРЯЗНЕНИЮ",
            command=self.auto_tune_room_profiles
        ).pack(side="left", padx=6)
        ttk.Button(
            controls, text="ПРИМЕНИТЬ SMART-ПРОФИЛИ",
            command=self.apply_smart_room_profiles
        ).pack(side="left", padx=6)
        ttk.Button(
            controls, text="ВЫБРАТЬ ВСЕ",
            command=lambda: [v.set(True) for v in self.room_profile_select_vars.values()]
        ).pack(side="left", padx=6)
        ttk.Button(
            controls, text="СБРОСИТЬ ВЫБОР",
            command=lambda: [v.set(False) for v in self.room_profile_select_vars.values()]
        ).pack(side="left", padx=6)
        ttk.Button(
            controls, text="ЗАПУСТИТЬ ПО ПРОФИЛЯМ",
            style="Accent2.TButton", command=self.start_profiled_room_sequence
        ).pack(side="right", padx=6)
        ttk.Button(
            controls, text="ОСТАНОВИТЬ ПОСЛЕДОВАТЕЛЬНОСТЬ",
            command=self.cancel_profiled_room_sequence
        ).pack(side="right", padx=6)

        info = ttk.LabelFrame(root, text="Как это работает", style="Section.TLabelframe")
        info.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(
            info,
            text=(
                "У ROIDMI EVE Plus существует native map.area-custom (13/10), предназначенный для "
                "покомнатных fan/water. Но его входной auto-area является строкой с внутренним форматом, "
                "который публично не описан и на вашей прошивке не подтверждён. Поэтому v20 не отправляет "
                "непроверенный payload.\n\n"
                "Вместо этого используется безопасный способ: глобальные свойства fan / water / sweep_type / "
                "path_mode / double_clean выставляются перед стартом одной комнаты. Затем запускается room sweep "
                "только выбранного сегмента. После завершения комнаты применяется профиль следующей. "
                "По окончании исходные общие настройки восстанавливаются.\n\n"
                "Для последовательной уборки сначала один раз получите карту, чтобы программа знала актуальный mapId."
            ),
            style="Muted.TLabel", wraplength=1580, justify="left"
        ).pack(anchor="w", padx=12, pady=12)

        ttk.Label(
            root, textvariable=self.room_profiles_status_var,
            style="Muted.TLabel", wraplength=1580, justify="left"
        ).pack(anchor="w", pady=(8, 0))

    def _build_capabilities_tab(self):
        root = ttk.Frame(self.tab_capabilities)
        root.pack(fill="both", expand=True, padx=14, pady=14)

        ttk.Label(root, text="Возможности ROIDMI EVE Plus / roidmi.vacuum.v60", style="Header.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(
            root,
            text="Матрица функций, используемых или подтверждённых для этой модели.",
            style="SubHeader.TLabel"
        ).pack(anchor="w", pady=(0, 10))

        cols = ("feature","support","miot","note")
        tree = ttk.Treeview(root, columns=cols, show="headings", height=22)
        tree.heading("feature", text="Функция")
        tree.heading("support", text="Поддержка")
        tree.heading("miot", text="MIoT")
        tree.heading("note", text="Комментарий")
        tree.column("feature", width=310, anchor="w")
        tree.column("support", width=110, anchor="center")
        tree.column("miot", width=160, anchor="center")
        tree.column("note", width=900, anchor="w")
        for row in VACUUM_CAPABILITIES:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True)

        ttk.Label(
            root,
            text=(
                "Ключевой вывод: разные режимы по комнатам возможны. v20 реализует это безопасно "
                "как последовательное применение профиля перед каждой room sweep. Native area-custom 13/10 "
                "пока не используется до получения подтверждённого формата payload для вашей прошивки."
            ),
            style="Muted.TLabel", wraplength=1580, justify="left"
        ).pack(anchor="w", pady=(10,0))

    def _recommend_profile_for_floor_dirt(self, rid, floor_type, dirt_level):
        # Conservative defaults: less water on wood/laminate, no water on carpet.
        floor = str(floor_type or "Другое")
        dirt = str(dirt_level or "Средний")

        if floor == "Плитка":
            fan, water, sweep, path = 3, 3, 2, 1
        elif floor == "Ламинат":
            fan, water, sweep, path = 3, 1, 2, 0
        elif floor == "Паркет":
            fan, water, sweep, path = 2, 1, 2, 0
        elif floor == "Линолеум":
            fan, water, sweep, path = 3, 2, 2, 1
        elif floor == "Плитка/ламинат":
            fan, water, sweep, path = 3, 2, 2, 0
        elif floor == "Ламинат + ковёр":
            fan, water, sweep, path = 3, 1, 2, 0
        elif floor == "Ковёр":
            fan, water, sweep, path = 4, 0, 0, 0
        else:
            fan, water, sweep, path = 3, 2, 2, 0

        double_clean = False
        if dirt == "Низкий":
            fan = min(fan, 2)
        elif dirt == "Высокий":
            fan = 4
            double_clean = True

        # Known dirty zones get at least strong cleaning.
        if rid in (1, 3) and dirt != "Низкий":
            fan = 4

        return {
            "floor_type": floor,
            "dirt_level": dirt,
            "fan": fan,
            "water": water,
            "sweep_type": sweep,
            "path_mode": path,
            "double_clean": double_clean,
        }

    def auto_tune_room_profiles(self):
        if not messagebox.askyesno(
            "Автоподбор",
            "Пересчитать мощность, воду, тип уборки, маршрут и 2x "
            "по выбранному покрытию пола и уровню загрязнения?"
        ):
            return
        notes = []
        for rid in range(1, 6):
            rec = self._recommend_profile_for_floor_dirt(
                rid,
                self.room_profile_floor_vars[rid].get(),
                self.room_profile_dirt_vars[rid].get(),
            )
            self.room_profile_fan_vars[rid].set(reverse_lookup(FAN, rec["fan"]))
            self.room_profile_water_vars[rid].set(reverse_lookup(WATER, rec["water"]))
            self.room_profile_sweep_vars[rid].set(reverse_lookup(SWEEP_TYPE, rec["sweep_type"]))
            self.room_profile_path_vars[rid].set(reverse_lookup(PATH_MODE, rec["path_mode"]))
            self.room_profile_double_vars[rid].set(bool(rec["double_clean"]))
            notes.append(
                f"{ROOM_LABELS[rid]}: {rec['floor_type']}, {rec['dirt_level']} -> "
                f"fan {rec['fan']}, water {rec['water']}, path {rec['path_mode']}, 2x={int(rec['double_clean'])}"
            )
        self._save_room_profiles(show_message=False)
        self.room_profiles_status_var.set("Автоподбор выполнен. " + " | ".join(notes))

    def _profile_for_room_from_ui(self, rid):
        return {
            "floor_type": self.room_profile_floor_vars[rid].get(),
            "dirt_level": self.room_profile_dirt_vars[rid].get(),
            "fan": FAN[self.room_profile_fan_vars[rid].get()],
            "water": WATER[self.room_profile_water_vars[rid].get()],
            "sweep_type": SWEEP_TYPE[self.room_profile_sweep_vars[rid].get()],
            "path_mode": PATH_MODE[self.room_profile_path_vars[rid].get()],
            "double_clean": bool(self.room_profile_double_vars[rid].get()),
        }

    def _selected_profile_rooms_in_order(self):
        selected = {rid for rid, v in self.room_profile_select_vars.items() if v.get()}
        if not selected:
            return []
        order = []
        try:
            raw = [int(x.strip()) for x in self.room_order_var.get().split(",") if x.strip()]
            if sorted(raw) == [1,2,3,4,5]:
                order = raw
        except Exception:
            pass
        if not order:
            order = list(OPTIMAL_ROOM_ORDER)
        return [rid for rid in order if rid in selected]

    def _send_one_room_action(self, d, rid, map_id):
        params = self._build_room_action_params([rid], map_id)
        local_error = None
        try:
            result = d.call_action_by(14, 1, params)
            return {"channel":"local", "result":result}
        except Exception as e:
            local_error = str(e)

        allow_cloud = bool(self.direct_room_use_cloud_fallback.get())
        if not allow_cloud:
            raise RuntimeError(
                f"Комната {rid}: локальная room-action не выполнена: {local_error}"
            )

        client = self.active_cloud_client or self.pending_cloud_client
        dev = self.active_cloud_device
        if not client or not dev:
            raise RuntimeError(
                f"Комната {rid}: локальная команда не прошла, Xiaomi Cloud fallback не готов. "
                f"Локальная ошибка: {local_error}"
            )
        result = client.do_miot_action(
            dev.get("country"), dev.get("device_id"), 14, 1, params
        )
        return {"channel":"cloud", "result":result, "local_error":local_error}

    def _set_sequence_status_threadsafe(self, message):
        try:
            self.after(0, lambda m=message: self.room_profiles_status_var.set(m))
        except Exception:
            pass

    def _wait_for_room_completion(self, d, rid, timeout_sec=5400):
        start_deadline = time.time() + 45
        started = False
        last_state = None
        while time.time() < start_deadline:
            if self.room_profile_sequence_cancel:
                raise RuntimeError("Последовательность остановлена пользователем.")
            st = d.status().data
            last_state = st.get("state")
            if last_state == 4:
                started = True
                break
            time.sleep(3)

        if not started:
            raise RuntimeError(
                f"{ROOM_LABELS[rid]}: робот не перешёл в состояние уборки. Последнее state={last_state}."
            )

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if self.room_profile_sequence_cancel:
                try:
                    d.stop()
                except Exception:
                    pass
                raise RuntimeError("Последовательность остановлена пользователем.")
            time.sleep(8)
            st = d.status().data
            state = st.get("state")
            if state != 4:
                return st

        try:
            d.stop()
        except Exception:
            pass
        raise RuntimeError(
            f"{ROOM_LABELS[rid]}: превышено максимальное время ожидания уборки."
        )

    def start_profiled_room_sequence(self):
        if self.room_profile_sequence_running:
            messagebox.showinfo("Режимы по комнатам", "Последовательность уже выполняется.")
            return

        rooms = self._selected_profile_rooms_in_order()
        if not rooms:
            messagebox.showinfo("Режимы по комнатам", "Выберите хотя бы одну комнату.")
            return

        raw_map_id = self.direct_room_map_id_var.get().strip()
        if not raw_map_id:
            messagebox.showinfo(
                "mapId",
                "Для профильной уборки нужен mapId. Сначала нажмите «Получить комнаты из карты»."
            )
            return
        try:
            map_id = int(raw_map_id)
        except Exception:
            messagebox.showerror("mapId", "mapId должен быть целым числом.")
            return

        self._save_room_profiles(show_message=False)
        profiles = {rid: self._profile_for_room_from_ui(rid) for rid in rooms}
        room_names = " → ".join(ROOM_LABELS[rid] for rid in rooms)
        if not messagebox.askyesno(
            "Профильная уборка",
            "Запустить последовательную уборку с отдельным режимом для каждой комнаты?\n\n"
            f"Порядок: {room_names}\n\n"
            "Перед каждой комнатой будут изменены мощность, вода, тип уборки, маршрут и double-clean. "
            "После окончания исходные общие настройки будут восстановлены."
        ):
            return

        self.room_profile_sequence_cancel = False
        self.room_profile_sequence_running = True

        def task():
            d = self.ensure_device()
            before = d.status().data
            self.backup_data(before, "before_profiled_room_sequence")
            restore = {
                "fanspeed_mode": before.get("fanspeed_mode"),
                "water_level": before.get("water_level"),
                "sweep_type": before.get("sweep_type"),
                "path_mode": before.get("path_mode"),
                "double_clean": bool(before.get("double_clean")),
            }
            results = []
            try:
                for idx, rid in enumerate(rooms, start=1):
                    if self.room_profile_sequence_cancel:
                        raise RuntimeError("Последовательность остановлена пользователем.")
                    profile = profiles[rid]
                    self._set_sequence_status_threadsafe(
                        f"[{idx}/{len(rooms)}] {ROOM_LABELS[rid]}: применяю профиль..."
                    )
                    for key, val in [
                        ("fanspeed_mode", profile["fan"]),
                        ("water_level", profile["water"]),
                        ("sweep_type", profile["sweep_type"]),
                        ("path_mode", profile["path_mode"]),
                        ("double_clean", profile["double_clean"]),
                    ]:
                        d.set_property(key, val)

                    self._set_sequence_status_threadsafe(
                        f"[{idx}/{len(rooms)}] {ROOM_LABELS[rid]}: запускаю уборку..."
                    )
                    before_room = d.status().data
                    room_started_at = datetime.now().astimezone().isoformat()
                    action_result = self._send_one_room_action(d, rid, map_id)
                    self._set_sequence_status_threadsafe(
                        f"[{idx}/{len(rooms)}] {ROOM_LABELS[rid]}: уборка выполняется..."
                    )
                    final_status = self._wait_for_room_completion(d, rid)
                    try:
                        room_duration = max(
                            0.0,
                            float(final_status.get("total_clean_time_sec") or 0)
                            - float(before_room.get("total_clean_time_sec") or 0)
                        )
                        room_area = max(
                            0.0,
                            float(final_status.get("total_clean_areas") or 0)
                            - float(before_room.get("total_clean_areas") or 0)
                        )
                        self._record_cleaning_session(
                            "profile_sequence",
                            [rid],
                            room_area,
                            room_duration,
                            fan=profile["fan"],
                            water=profile["water"],
                            sweep_type=profile["sweep_type"],
                            path_mode=profile["path_mode"],
                            error_code=final_status.get("error_code") or 0,
                            started_at=room_started_at,
                        )
                        self._last_counter_snapshot = {
                            "clean_counts": final_status.get("clean_counts"),
                            "total_clean_areas": final_status.get("total_clean_areas"),
                            "total_clean_time_sec": final_status.get("total_clean_time_sec"),
                            "state": final_status.get("state"),
                        }
                    except Exception:
                        room_duration = None
                        room_area = None
                    results.append({
                        "room": rid,
                        "name": ROOM_LABELS[rid],
                        "profile": profile,
                        "action": action_result,
                        "final_state": final_status.get("state"),
                        "duration_sec": room_duration,
                        "area_m2": room_area,
                    })
            finally:
                self._set_sequence_status_threadsafe("Восстанавливаю общие настройки...")
                for key, val in restore.items():
                    if val is None:
                        continue
                    try:
                        d.set_property(key, val)
                    except Exception:
                        pass

            after = d.status().data
            return {
                "rooms": rooms,
                "results": results,
                "restore": restore,
                "after": after,
            }

        def done(result):
            self.room_profile_sequence_running = False
            self.room_profile_sequence_cancel = False
            self.on_status(result["after"])
            with (ROOT / "room_profiles.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " SEQUENCE " +
                    json.dumps(result, ensure_ascii=False, default=str) + "\n"
                )
            self.room_profiles_status_var.set(
                "Профильная уборка завершена: " +
                " → ".join(ROOM_LABELS[rid] for rid in result["rooms"]) +
                ". Общие настройки восстановлены."
            )

        self.async_run(task, done, "Профильная уборка комнат...")

    def cancel_profiled_room_sequence(self):
        if not self.room_profile_sequence_running:
            self.room_profiles_status_var.set("Последовательность сейчас не выполняется.")
            return
        self.room_profile_sequence_cancel = True
        self.room_profiles_status_var.set("Запрошена остановка. Жду безопасного завершения текущей операции...")

    def _build_profiles_tab(self):
        top = ttk.Frame(self.tab_profiles)
        top.pack(fill="both", expand=True, padx=10, pady=10)

        info = ttk.LabelFrame(top, text="Квартира 45 м² - фактическая планировка")
        info.pack(fill="x")
        ttk.Label(
            info,
            text=(
                "База: ванная (Room 5) → коридор (Room 3). "
                "Из коридора: кухня (Room 1) и зал (Room 4); из зала - спальня (Room 2).\n"
                "Оптимальный полный маршрут: Спальня 2 → Зал 4 → Кухня 1 → "
                "Коридор 3 → Ванная 5 → база.\n"
                "Во Вт/Чт/Сб отдельная уборка: Кухня 1 → Коридор 3."
            ),
            wraplength=1080, justify="left"
        ).pack(anchor="w", padx=8, pady=8)

        table = ttk.LabelFrame(top, text="Комнаты и рекомендуемые режимы")
        table.pack(fill="x", pady=(10,0))

        headers = ["ID","Комната","CleanCount карты","Рекоменд. мощность","Рекоменд. вода"]
        for c,h in enumerate(headers):
            ttk.Label(table, text=h, font=("Segoe UI", 9, "bold")).grid(
                row=0, column=c, padx=7, pady=5, sticky="w"
            )

        defaults = {
            1: ("Кухня", 4, 2),
            2: ("Спальня", 2, 1),
            3: ("Коридор", 4, 2),
            4: ("Зал", 3, 2),
            5: ("Ванная", 3, 3),
        }
        self.profile_name_vars = {}
        self.profile_fan_vars = {}
        self.profile_water_vars = {}
        self.profile_clean_count_vars = {}

        for row, rid in enumerate([1,2,3,4,5], start=1):
            name, fan, water = defaults[rid]
            self.profile_name_vars[rid] = tk.StringVar(value=name)
            self.profile_fan_vars[rid] = tk.StringVar(value=reverse_lookup(FAN, fan))
            self.profile_water_vars[rid] = tk.StringVar(value=reverse_lookup(WATER, water))
            self.profile_clean_count_vars[rid] = tk.StringVar(value="1")

            ttk.Label(table, text=str(rid), width=5).grid(row=row,column=0,padx=7,pady=5,sticky="w")
            ttk.Label(table, text=name, width=20).grid(row=row,column=1,padx=7,pady=5,sticky="w")
            ttk.Label(table, textvariable=self.profile_clean_count_vars[rid], width=15).grid(
                row=row,column=2,padx=7,pady=5,sticky="w"
            )
            ttk.Combobox(
                table, textvariable=self.profile_fan_vars[rid],
                values=list(FAN.keys()), state="readonly", width=26
            ).grid(row=row,column=3,padx=7,pady=5,sticky="w")
            ttk.Combobox(
                table, textvariable=self.profile_water_vars[rid],
                values=list(WATER.keys()), state="readonly", width=26
            ).grid(row=row,column=4,padx=7,pady=5,sticky="w")

        ttk.Label(
            table,
            text=(
                "Важно: покомнатные значения мощности/воды здесь являются рекомендуемым профилем. "
                "В вашей фактической autoArea нет полей мощности/воды, поэтому v13 не отправляет "
                "неподтверждённый area-custom и не рискует картой."
            ),
            foreground="#8a5200", wraplength=1050, justify="left"
        ).grid(row=7,column=0,columnspan=5,padx=7,pady=(10,7),sticky="w")

        route = ttk.LabelFrame(top, text="Порядок полной уборки")
        route.pack(fill="x", pady=(10,0))
        self.room_order_var = tk.StringVar(value="2,4,1,3,5")
        ttk.Label(route, text="ID через запятую:").pack(side="left", padx=8, pady=8)
        ttk.Entry(route, textvariable=self.room_order_var, width=24).pack(side="left", padx=5)
        ttk.Button(
            route, text="Оптимальный 2→4→1→3→5",
            command=self.set_optimal_room_order
        ).pack(side="left", padx=6)
        ttk.Label(
            route,
            text="Спальня → Зал → Кухня → Коридор → Ванная",
            foreground="#555"
        ).pack(side="left", padx=10)

        buttons = ttk.LabelFrame(top, text="Применение")
        buttons.pack(fill="x", pady=(10,0))

        ttk.Button(
            buttons, text="1. Получить/обновить карту",
            command=self.fetch_rooms
        ).pack(side="left", padx=5, pady=8)

        ttk.Button(
            buttons, text="2. СОХРАНИТЬ ПОРЯДОК КОМНАТ",
            command=self.apply_room_order
        ).pack(side="left", padx=5, pady=8)

        ttk.Button(
            buttons, text="ПРИМЕНИТЬ ОПТИМАЛЬНЫЕ ОБЩИЕ НАСТРОЙКИ",
            command=self.apply_optimized_global_profile
        ).pack(side="left", padx=5, pady=8)

        ttk.Button(
            buttons, text="ПРИМЕНИТЬ НАСТРОЙКИ + СОХРАНИТЬ ПРОФИЛЬ", style="Accent.TButton",
            command=self.apply_all_optimization
        ).pack(side="left", padx=5, pady=8)

        self.profile_status_var = tk.StringVar(
            value="Карта ещё не загружена. Порядок комнат можно записывать только после получения autoArea."
        )
        ttk.Label(
            top, textvariable=self.profile_status_var,
            wraplength=1080, foreground="#555", justify="left"
        ).pack(anchor="w", pady=(8,0))

        nav = ttk.LabelFrame(top, text="LiDAR и навигация")
        nav.pack(fill="x", pady=(10,0))
        ttk.Label(
            nav,
            text=(
                "«Силы LiDAR» у roidmi.vacuum.v60 нет. Доступен только lidar_collision "
                "(предотвращение столкновений) - оптимальный профиль держит его включённым. "
                "Маршрут: Normal=0, Y-Mopping=1, Repeat-Mopping=2. "
                "Для ежедневного режима оставлен Normal; глубокую Y/Repeat мойку лучше включать вручную по необходимости."
            ),
            wraplength=1080, justify="left"
        ).pack(anchor="w", padx=8, pady=8)

    def _build_dnd_tab(self):
        box = ttk.LabelFrame(self.tab_dnd, text="Режим «Не беспокоить»")
        box.pack(anchor="nw", padx=15, pady=15)

        self.dnd_start_h = tk.IntVar(value=22)
        self.dnd_start_m = tk.IntVar(value=0)
        self.dnd_end_h = tk.IntVar(value=8)
        self.dnd_end_m = tk.IntVar(value=0)

        ttk.Label(box,text="Начало:").grid(row=0,column=0,padx=7,pady=10)
        ttk.Spinbox(box,from_=0,to=23,textvariable=self.dnd_start_h,width=5).grid(row=0,column=1)
        ttk.Label(box,text=":").grid(row=0,column=2)
        ttk.Spinbox(box,from_=0,to=59,textvariable=self.dnd_start_m,width=5).grid(row=0,column=3)

        ttk.Label(box,text="Окончание:").grid(row=1,column=0,padx=7,pady=10)
        ttk.Spinbox(box,from_=0,to=23,textvariable=self.dnd_end_h,width=5).grid(row=1,column=1)
        ttk.Label(box,text=":").grid(row=1,column=2)
        ttk.Spinbox(box,from_=0,to=59,textvariable=self.dnd_end_m,width=5).grid(row=1,column=3)

        ttk.Button(box,text="Включить / изменить DND",command=self.apply_dnd).grid(row=2,column=0,columnspan=2,padx=7,pady=12)
        ttk.Button(box,text="Отключить DND",command=self.disable_dnd).grid(row=2,column=2,columnspan=2,padx=7,pady=12)
        ttk.Label(
            box,
            text="LIVE AUTOSAVE: изменение времени автоматически включает/обновляет DND.",
            foreground="#1f6b2a", wraplength=420
        ).grid(row=3,column=0,columnspan=4,padx=7,pady=(0,10))

    def _build_raw_tab(self):
        buttons = ttk.Frame(self.tab_raw)
        buttons.pack(fill="x", padx=8, pady=8)
        ttk.Button(buttons,text="Обновить JSON",command=self.read_status).pack(side="left",padx=4)
        ttk.Button(buttons,text="Экспорт JSON",command=self.export_raw).pack(side="left",padx=4)
        ttk.Button(buttons,text="Импорт конфигурации JSON",command=self.import_config_json).pack(side="left",padx=4)
        ttk.Button(buttons,text="ПРИМЕНИТЬ ИМПОРТИРОВАННОЕ",command=self.apply_imported_config).pack(side="left",padx=4)
        ttk.Button(buttons,text="Применить RAW timing",command=self.apply_raw_timing).pack(side="left",padx=4)

        self.raw_text = tk.Text(self.tab_raw, wrap="none", font=("Consolas",9))
        self.raw_text.pack(fill="both", expand=True, padx=8, pady=(0,8))
        self.raw_text.insert("1.0", "{\n  \"status\": \"Подключитесь к роботу\"\n}")

    def _safe_application_snapshot(self):
        d = dict(self.last_data or {})
        timing = self._parse_timing(d.get("timing"))
        try:
            dnd = json.loads(d.get("forbid_mode")) if isinstance(d.get("forbid_mode"), str) else d.get("forbid_mode")
        except Exception:
            dnd = d.get("forbid_mode")

        return {
            "exported_at": datetime.now().astimezone().isoformat(),
            "application": APP_TITLE,
            "model": MODEL,
            "robot": {
                "ip": self.ip_var.get().strip(),
                "status": d,
            },
            "schedule": timing,
            "dnd": dnd,
            "rooms": self.rooms_data,
            "map_meta": {
                "map_id": self.current_map_id,
                "map_info": self.map_info_raw,
                "optimization": self.last_map_analysis,
            },
            "room_profiles": self._read_room_profiles_payload(),
            "voice": {
                "current_audio": d.get("current_audio"),
                "volume": d.get("volume"),
                "mute": d.get("mute"),
                "sources": VOICE_SOURCES,
            },
            "privacy_note": (
                "Пароли Xiaomi, serviceToken, robot token и общая Xiaomi Cloud сессия "
                "намеренно не включены в этот экспорт."
            ),
        }

    @staticmethod
    def _hash_file(path, algorithm="md5", chunk_size=1024 * 1024):
        h = hashlib.new(algorithm)
        with Path(path).open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def _voice_library_manifest(self):
        result = []
        for p in sorted(VOICEPACKS_DIR.iterdir()):
            if not p.is_file():
                continue
            try:
                md5 = self._hash_file(p, "md5")
            except Exception:
                md5 = None
            result.append({
                "name": p.name,
                "size": p.stat().st_size,
                "md5": md5,
            })
        return result

    def _export_full_bundle_now(self, destination):
        destination = Path(destination)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp = EXPORTS_DIR / f"full_export_{stamp}"
        if temp.exists():
            shutil.rmtree(temp)
        temp.mkdir(parents=True)

        snapshot = self._safe_application_snapshot()
        (temp / "application_snapshot.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        (temp / "room_profiles.json").write_text(
            json.dumps(self._read_room_profiles_payload(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        (temp / "voice_sources.json").write_text(
            json.dumps(VOICE_SOURCES, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        (temp / "voice_library_manifest.json").write_text(
            json.dumps(self._voice_library_manifest(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        if APP_SETTINGS_PATH.exists():
            shutil.copy2(APP_SETTINGS_PATH, temp / "app_settings.json")
        if FIRMWARE_REPORT_PATH.exists():
            shutil.copy2(FIRMWARE_REPORT_PATH, temp / "firmware_report.json")
        if HISTORY_DB_PATH.exists():
            # SQLite backup API creates a consistent snapshot even with WAL enabled.
            db_copy = temp / "history.sqlite3"
            with db_connect() as source_con:
                dest_con = sqlite3.connect(str(db_copy))
                try:
                    source_con.backup(dest_con)
                finally:
                    dest_con.close()
        try:
            with db_connect() as con:
                history_rows = [dict(r) for r in con.execute(
                    "SELECT * FROM cleaning_sessions ORDER BY id DESC LIMIT 1000"
                ).fetchall()]
                maintenance_rows = [dict(r) for r in con.execute(
                    "SELECT * FROM maintenance ORDER BY id DESC LIMIT 1000"
                ).fetchall()]
                water_tank_rows = [dict(r) for r in con.execute(
                    "SELECT * FROM water_tank_events ORDER BY id DESC LIMIT 1000"
                ).fetchall()]
            (temp / "history.json").write_text(
                json.dumps(history_rows, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
            (temp / "maintenance.json").write_text(
                json.dumps(maintenance_rows, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
            (temp / "water_tank_events.json").write_text(
                json.dumps(water_tank_rows, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception:
            pass

        # Current map files.
        map_dir = temp / "map"
        map_dir.mkdir()
        for source, name in [
            (LIVE_MAP_RAW_PATH, "map_raw_roidmi.gz"),
            (LIVE_MAP_PNG_PATH, "map_rendered.png"),
            (LIVE_MAP_ANALYSIS_PATH, "optimization_analysis.json"),
            (LIVE_MAP_REPORT_PATH, "optimization_report.txt"),
        ]:
            if source.exists():
                shutil.copy2(source, map_dir / name)
        if self.map_info_raw:
            (map_dir / "map_info.json").write_text(
                json.dumps(self.map_info_raw, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        if self.rooms_data:
            (map_dir / "rooms.json").write_text(
                json.dumps(self.rooms_data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )

        # Documentation and protocol research.
        docs_dir = temp / "docs"
        docs_dir.mkdir()
        for name in [
            "SOURCE_MATRIX.json",
            "GITHUB_RESEARCH.md",
            "THIRD_PARTY_NOTICES.md",
            "README.txt",
        ]:
            p = ROOT / name
            if p.exists():
                shutil.copy2(p, docs_dir / p.name)

        # Local voice files are included so the backup is complete.
        vp_dir = temp / "voicepacks"
        vp_dir.mkdir()
        for p in VOICEPACKS_DIR.iterdir():
            if p.is_file():
                try:
                    shutil.copy2(p, vp_dir / p.name)
                except Exception:
                    pass

        (temp / "README_EXPORT.txt").write_text(
            "Полный безопасный экспорт ROIDMI EVE Plus Control.\n\n"
            "Включено: статус, расписание, DND, карта, комнаты, анализ карты, "
            "покомнатные профили, покрытие пола, загрязнение, голосовой каталог, "
            "локальные голосовые архивы и документация.\n\n"
            "Не включено: пароли Xiaomi, serviceToken, robot token, CLOUD_SESSION.json.\n",
            encoding="utf-8"
        )

        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as z:
            for p in temp.rglob("*"):
                if p.is_file():
                    z.write(p, arcname=p.relative_to(temp))

        return destination

    def export_everything_bundle(self):
        dst = filedialog.asksaveasfilename(
            title="Скачать всё из приложения",
            defaultextension=".zip",
            initialfile=f"ROIDMI_EVE_Plus_FULL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            filetypes=[("ZIP", "*.zip"), ("Все файлы", "*.*")]
        )
        if not dst:
            return

        # For the most complete export, refresh map first if it has not been obtained.
        if self.last_raw_map is None:
            self.pending_full_export_path = dst
            self.export_status_var.set("Сначала загружаю свежую Xiaomi Cloud карту...")
            messagebox.showinfo(
                "Скачать всё",
                "Для полного архива сначала будет загружена актуальная карта Xiaomi Cloud. "
                "После успешной загрузки ZIP создастся автоматически."
            )
            self.fetch_rooms()
            return

        try:
            result = self._export_full_bundle_now(dst)
            self.export_status_var.set(f"Полный архив создан: {result}")
            messagebox.showinfo("Экспорт", f"Готово:\n{result}")
        except Exception as e:
            messagebox.showerror("Экспорт", str(e))

    def export_voice_library_bundle(self):
        dst = filedialog.asksaveasfilename(
            title="Экспорт локальной библиотеки голосов",
            defaultextension=".zip",
            initialfile=f"ROIDMI_voice_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            filetypes=[("ZIP", "*.zip")]
        )
        if not dst:
            return
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            for p in VOICEPACKS_DIR.iterdir():
                if p.is_file():
                    z.write(p, arcname=p.name)
            z.writestr(
                "VOICE_SOURCES.json",
                json.dumps(VOICE_SOURCES, ensure_ascii=False, indent=2)
            )
            z.writestr(
                "manifest.json",
                json.dumps(self._voice_library_manifest(), ensure_ascii=False, indent=2)
            )
        self.export_status_var.set(f"Библиотека голосов экспортирована: {dst}")

    def _build_export_tab(self):
        root = ttk.Frame(self.tab_export)
        root.pack(fill="both", expand=True, padx=14, pady=14)

        head = ttk.Frame(root, style="Toolbar.TFrame")
        head.pack(fill="x", pady=(0, 12))
        ttk.Label(head, text="Скачать данные из приложения", style="Header.TLabel").pack(anchor="w", padx=16, pady=(14, 2))
        ttk.Label(
            head,
            text="Один ZIP без паролей и токенов: состояние, карта, комнаты, профили, расписание, голосовые файлы и анализ.",
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=16, pady=(0, 14))

        actions = ttk.LabelFrame(root, text="Полный экспорт", style="Section.TLabelframe")
        actions.pack(fill="x")
        box = ttk.Frame(actions, style="Card.TFrame")
        box.pack(fill="x", padx=12, pady=12)
        ttk.Button(
            box, text="СКАЧАТЬ ВСЁ (ZIP)",
            style="Accent.TButton", command=self.export_everything_bundle
        ).pack(side="left", padx=4)
        ttk.Button(
            box, text="Карта ZIP",
            command=self.export_live_map_bundle
        ).pack(side="left", padx=4)
        ttk.Button(
            box, text="PNG карты",
            command=self.save_live_map_png_as
        ).pack(side="left", padx=4)
        ttk.Button(
            box, text="Комнаты JSON",
            command=self.export_rooms
        ).pack(side="left", padx=4)
        ttk.Button(
            box, text="Состояние JSON",
            command=self.export_raw
        ).pack(side="left", padx=4)
        ttk.Button(
            box, text="Голоса ZIP",
            command=self.export_voice_library_bundle
        ).pack(side="left", padx=4)

        ttk.Label(
            root, textvariable=self.export_status_var,
            style="Muted.TLabel", wraplength=1100, justify="left"
        ).pack(anchor="w", pady=(10, 8))

        contents = ttk.LabelFrame(root, text="Что попадёт в полный ZIP", style="Section.TLabelframe")
        contents.pack(fill="both", expand=True)
        ttk.Label(
            contents,
            text=(
                "• текущий status JSON и параметры робота\n"
                "• расписание и DND\n"
                "• список комнат, raw-карта, PNG, map_info и анализ геометрии\n"
                "• профили комнат, включая покрытие пола и уровень загрязнения\n"
                "• текущий голос, каталог сайтов и локальные голосовые архивы\n"
                "• SOURCE_MATRIX, GitHub research и инструкции\n\n"
                "Не экспортируются пароль Xiaomi, serviceToken, robot token и CLOUD_SESSION.json."
            ),
            style="Muted.TLabel", justify="left", wraplength=1100
        ).pack(anchor="nw", padx=14, pady=14)

    def _build_center_tab(self):
        root = ttk.Frame(self.tab_center)
        root.pack(fill="both", expand=True, padx=10, pady=8)

        head = ttk.Frame(root, style="Toolbar.TFrame")
        head.pack(fill="x", pady=(0, 7))
        ttk.Label(head, text="Интеллектуальный центр", style="Header.TLabel").pack(anchor="w", padx=14, pady=(10, 2))
        ttk.Label(
            head,
            text="История, обучение по комнатам, обслуживание, вода, уведомления, backup и обновления.",
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=14, pady=(0, 10))
        ttk.Label(head, textvariable=self.center_status_var, style="Muted.TLabel").pack(anchor="e", padx=14, pady=(0, 8))

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True)

        tab_opt = ttk.Frame(nb)
        tab_hist = ttk.Frame(nb)
        tab_service = ttk.Frame(nb)
        tab_notify = ttk.Frame(nb)
        tab_system = ttk.Frame(nb)
        nb.add(tab_opt, text="Оптимизация")
        nb.add(tab_hist, text="История")
        nb.add(tab_service, text="Сервис и вода")
        nb.add(tab_notify, text="Уведомления")
        nb.add(tab_system, text="Backup / Диагностика / Update")

        # Optimization
        bar = ttk.Frame(tab_opt, style="Card.TFrame")
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Label(bar, text="Сезонный профиль:", style="Muted.TLabel").pack(side="left", padx=(8,4))
        ttk.Combobox(
            bar, textvariable=self.season_mode_var,
            values=["Авто", "Обычный", "Грязный сезон", "Экономичный"],
            state="readonly", width=18
        ).pack(side="left", padx=4)
        ttk.Button(bar, text="Пересчитать", command=self._refresh_center_views_if_present).pack(side="left", padx=4)
        ttk.Button(bar, text="Сохранить", command=self._save_app_settings).pack(side="left", padx=4)
        ttk.Button(
            bar, text="ОПТИМИЗИРОВАТЬ ВСЁ",
            style="Accent.TButton", command=self.show_adaptive_diff_dialog
        ).pack(side="right", padx=6)

        opt_text = tk.Text(
            tab_opt, wrap="word", bg="#121b2e", fg="#eef4ff",
            relief="flat", font=("Segoe UI", 10)
        )
        opt_text.pack(fill="both", expand=True, padx=8, pady=(0,8))
        opt_text.insert("1.0", self.adaptive_plan_var.get())
        opt_text.configure(state="disabled")
        self.adaptive_plan_text = opt_text

        def sync_opt_text(*_):
            try:
                opt_text.configure(state="normal")
                opt_text.delete("1.0", "end")
                opt_text.insert("1.0", self.adaptive_plan_var.get())
                opt_text.configure(state="disabled")
            except Exception:
                pass
        self.adaptive_plan_var.trace_add("write", sync_opt_text)

        # History
        cols = ("time","source","rooms","area","mins","result")
        self.history_tree = ttk.Treeview(tab_hist, columns=cols, show="headings", height=13)
        labels = {"time":"Время","source":"Источник","rooms":"Комнаты","area":"м²","mins":"Мин","result":"Результат"}
        widths = {"time":185,"source":130,"rooms":340,"area":80,"mins":80,"result":110}
        for c in cols:
            self.history_tree.heading(c, text=labels[c])
            self.history_tree.column(c, width=widths[c], anchor="w" if c in ("time","source","rooms") else "center")
        self.history_tree.pack(fill="both", expand=True, padx=8, pady=(8,4))

        stats_frame = ttk.LabelFrame(tab_hist, text="Обучение по комнатам")
        stats_frame.pack(fill="x", padx=8, pady=(4,8))
        scols = ("id","room","samples","spm","estimate")
        self.room_stats_tree = ttk.Treeview(stats_frame, columns=scols, show="headings", height=5)
        for c, label, width in [
            ("id","ID",50),("room","Комната",180),("samples","Замеров",90),
            ("spm","сек/м²",100),("estimate","Оценка, мин",110)
        ]:
            self.room_stats_tree.heading(c, text=label)
            self.room_stats_tree.column(c, width=width, anchor="center" if c!="room" else "w")
        self.room_stats_tree.pack(fill="x", padx=6, pady=6)

        # Service / water
        forecasts = ttk.Frame(tab_service)
        forecasts.pack(fill="x", padx=8, pady=8)
        left = ttk.LabelFrame(forecasts, text="Расходники")
        right = ttk.LabelFrame(forecasts, text="Вода")
        left.pack(side="left", fill="both", expand=True, padx=(0,4))
        right.pack(side="left", fill="both", expand=True, padx=(4,0))
        ttk.Label(left, textvariable=self.service_forecast_var, wraplength=650, justify="left").pack(anchor="w", padx=10, pady=10)
        ttk.Label(right, textvariable=self.water_forecast_var, wraplength=650, justify="left").pack(anchor="w", padx=10, pady=(10,6))
        ttk.Label(
            right,
            text=(
                "Техническая база прогноза: SDJ01RM, бак 250 мл по региональной странице ROIDMI; "
                "в части руководств указано около 220 мл. Для консервативного остатка используется 220 мл."
            ),
            style="Muted.TLabel", wraplength=650, justify="left"
        ).pack(anchor="w", padx=10, pady=(0,10))
        auto_box = ttk.Frame(right, style="Card.TFrame")
        auto_box.pack(fill="x", padx=10, pady=(0,10))
        ttk.Checkbutton(
            auto_box,
            text="После снятия и повторной установки считать бак заново заполненным",
            variable=self.auto_water_refill_var,
            command=self._save_app_settings
        ).pack(anchor="w", pady=(4,2))
        ttk.Label(
            auto_box,
            textvariable=self.water_tank_state_var,
            style="Muted.TLabel", wraplength=620, justify="left"
        ).pack(anchor="w", pady=2)
        ttk.Label(
            auto_box,
            textvariable=self.water_virtual_level_var,
            style="Muted.TLabel", wraplength=620, justify="left"
        ).pack(anchor="w", pady=2)
        ttk.Button(
            auto_box,
            text="БАК ЗАПОЛНЕН СЕЙЧАС",
            command=self.mark_water_tank_full_manual
        ).pack(anchor="w", pady=(4,4))
        ttk.Label(
            auto_box,
            text="Напоминание раз в 2 дня отключено. Теперь порог рассчитывается по фактическим влажным уборкам; Email отправляется при достижении 30% (или выбранного порога).",
            style="Muted.TLabel", wraplength=620, justify="left"
        ).pack(anchor="w", pady=(2,4))

        maint = ttk.LabelFrame(tab_service, text="Журнал обслуживания")
        maint.pack(fill="both", expand=True, padx=8, pady=(0,8))
        actions = ttk.Frame(maint)
        actions.pack(fill="x", padx=6, pady=6)
        for label, kind in [
            ("Долил воду","water_fill"),("Фильтр заменён","filter"),
            ("Основная щётка","main_brush"),("Боковые щётки","side_brush"),
            ("Датчики очищены","sensors"),("Мешок станции","station_bag"),
            ("Салфетка/моп","mop")
        ]:
            ttk.Button(
                actions, text=label,
                command=lambda k=kind, l=label: self.add_maintenance_event(k, l)
            ).pack(side="left", padx=3)
        mcols = ("time","kind","notes")
        self.maintenance_tree = ttk.Treeview(maint, columns=mcols, show="headings", height=8)
        for c,label,width in [("time","Дата",190),("kind","Событие",180),("notes","Комментарий",700)]:
            self.maintenance_tree.heading(c,text=label)
            self.maintenance_tree.column(c,width=width,anchor="w")
        self.maintenance_tree.pack(fill="both", expand=True, padx=6, pady=(0,6))

        # Notifications
        notif = ttk.LabelFrame(tab_notify, text="Каналы уведомлений")
        notif.pack(fill="x", padx=8, pady=8)
        ttk.Checkbutton(notif, text="Windows notifications", variable=self.notify_windows_var).grid(row=0,column=0,columnspan=2,sticky="w",padx=8,pady=6)
        ttk.Checkbutton(notif, text="Telegram", variable=self.notify_telegram_var).grid(row=1,column=0,sticky="w",padx=8,pady=6)
        ttk.Label(notif,text="Bot token").grid(row=1,column=1,sticky="e")
        ttk.Entry(notif,textvariable=self.telegram_token_var,width=48,show="•").grid(row=1,column=2,padx=6)
        ttk.Label(notif,text="Chat ID").grid(row=1,column=3,sticky="e")
        ttk.Entry(notif,textvariable=self.telegram_chat_var,width=20).grid(row=1,column=4,padx=6)
        ttk.Checkbutton(notif, text="ntfy (подходит для iPhone)", variable=self.notify_ntfy_var).grid(row=2,column=0,sticky="w",padx=8,pady=6)
        ttk.Label(notif,text="Topic URL").grid(row=2,column=1,sticky="e")
        ttk.Entry(notif,textvariable=self.ntfy_url_var,width=70).grid(row=2,column=2,columnspan=3,padx=6,sticky="ew")

        ttk.Checkbutton(
            notif, text="Email при низком уровне воды",
            variable=self.notify_email_var
        ).grid(row=3,column=0,sticky="w",padx=8,pady=6)
        ttk.Label(notif,text="Получатель").grid(row=3,column=1,sticky="e")
        ttk.Entry(notif,textvariable=self.email_to_var,width=32).grid(row=3,column=2,padx=6,sticky="w")
        ttk.Label(notif,text="Порог воды, %").grid(row=3,column=3,sticky="e")
        ttk.Spinbox(
            notif, from_=5, to=95, increment=5,
            textvariable=self.water_low_threshold_var, width=7
        ).grid(row=3,column=4,padx=6,sticky="w")

        ttk.Label(notif,text="SMTP server").grid(row=4,column=1,sticky="e")
        ttk.Entry(notif,textvariable=self.smtp_host_var,width=28).grid(row=4,column=2,padx=6,sticky="w")
        ttk.Label(notif,text="Port").grid(row=4,column=3,sticky="e")
        ttk.Spinbox(notif,from_=1,to=65535,textvariable=self.smtp_port_var,width=7).grid(row=4,column=4,padx=6,sticky="w")

        ttk.Label(notif,text="SMTP / Gmail user").grid(row=5,column=1,sticky="e")
        ttk.Entry(notif,textvariable=self.smtp_user_var,width=32).grid(row=5,column=2,padx=6,sticky="w")
        ttk.Label(notif,text="App Password").grid(row=5,column=3,sticky="e")
        ttk.Entry(notif,textvariable=self.smtp_password_var,width=24,show="•").grid(row=5,column=4,padx=6,sticky="w")

        ttk.Label(
            notif, textvariable=self.email_status_var,
            style="Muted.TLabel", wraplength=950, justify="left"
        ).grid(row=6,column=0,columnspan=5,sticky="w",padx=8,pady=(2,6))

        ttk.Checkbutton(
            notif, text="Сворачивать в системный трей",
            variable=self.minimize_to_tray_var
        ).grid(row=7,column=0,columnspan=2,sticky="w",padx=8,pady=6)

        ttk.Button(
            notif,text="Сохранить",
            command=lambda:(self._save_notify_config(),self._save_app_settings())
        ).grid(row=8,column=0,padx=8,pady=10)
        ttk.Button(
            notif,text="Тест push",
            command=self.test_notifications
        ).grid(row=8,column=1,padx=8,pady=10)
        ttk.Button(
            notif,text="Тест Email",
            style="Accent.TButton",command=self.test_email_notification
        ).grid(row=8,column=2,padx=8,pady=10)

        ttk.Label(
            notif,
            text=(
                "Для Gmail используйте smtp.gmail.com:587 и App Password Google, "
                "а не обычный пароль аккаунта. SMTP/App Password хранятся только в "
                "PRIVATE_NOTIFY_CONFIG.json и не включаются в backup/export."
            ),
            style="Muted.TLabel", wraplength=1150, justify="left"
        ).grid(row=9,column=0,columnspan=5,sticky="w",padx=8,pady=(0,8))
        notif.grid_columnconfigure(2, weight=1)

        # System / map history / updates
        system_top = ttk.LabelFrame(tab_system, text="Системные данные")
        system_top.pack(fill="x", padx=8, pady=8)
        ttk.Button(system_top,text="Создать backup",command=self.create_safe_persistent_backup).pack(side="left",padx=5,pady=8)
        ttk.Button(system_top,text="Восстановить backup",command=self.restore_safe_persistent_backup).pack(side="left",padx=5,pady=8)
        ttk.Button(system_top,text="Диагностический ZIP",command=self.create_diagnostics_zip).pack(side="left",padx=5,pady=8)
        ttk.Button(system_top,text="Открыть папку данных",command=lambda: os.startfile(str(SHARED_APP_DIR))).pack(side="left",padx=5,pady=8)
        ttk.Label(system_top,textvariable=self.performance_status_var,style="Muted.TLabel").pack(side="right",padx=8)

        update = ttk.LabelFrame(tab_system, text="GitHub Auto Update")
        update.pack(fill="x", padx=8, pady=(0,8))
        update_top = ttk.Frame(update, style="Card.TFrame")
        update_top.pack(fill="x", padx=6, pady=6)
        ttk.Label(update_top,text="Manifest:").pack(side="left",padx=(4,3))
        ttk.Entry(
            update_top,textvariable=self.update_manifest_url_var,width=68
        ).pack(side="left",fill="x",expand=True,padx=4)
        ttk.Button(
            update_top,text="Проверить сейчас",command=self.check_for_updates
        ).pack(side="left",padx=4)
        ttk.Button(
            update_top,text="Открыть GitHub",
            command=lambda: webbrowser.open(GITHUB_REPOSITORY_URL)
        ).pack(side="left",padx=4)

        update_bottom = ttk.Frame(update, style="Card.TFrame")
        update_bottom.pack(fill="x", padx=6, pady=(0,6))
        ttk.Checkbutton(
            update_bottom,
            text="Автоматически проверять GitHub каждые 12 часов",
            variable=self.github_auto_check_var,
            command=self._save_app_settings
        ).pack(side="left",padx=4)
        ttk.Label(
            update_bottom,textvariable=self.update_status_var,style="Muted.TLabel"
        ).pack(side="right",padx=8)

        mh = ttk.LabelFrame(tab_system, text="История карт (последние снимки)")
        mh.pack(fill="both", expand=True, padx=8, pady=(0,8))
        mcols = ("time","mapid","hash","png")
        self.map_history_tree = ttk.Treeview(mh, columns=mcols, show="headings", height=8)
        for c,label,width in [("time","Дата",190),("mapid","Map ID",130),("hash","SHA256",150),("png","PNG",70)]:
            self.map_history_tree.heading(c,text=label)
            self.map_history_tree.column(c,width=width,anchor="w" if c=="time" else "center")
        self.map_history_tree.pack(fill="both",expand=True,padx=6,pady=6)

        self._refresh_center_views_if_present()

    def show_adaptive_diff_dialog(self):
        plan = self._adaptive_room_plan()
        current = self.last_data or {}
        suggested = {
            "fanspeed_mode": 3,
            "sweep_type": 2,
            "water_level": 1,
            "path_mode": 0,
            "work_station_freq": 2,
            "auto_boost": True,
            "double_clean": False,
            "lidar_collision": True,
        }

        win = tk.Toplevel(self)
        win.title("Оптимизировать всё - предварительный diff")
        win.geometry("920x720")
        body = ttk.Frame(win)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Label(
            body,
            text="Сначала сравнение. Снимите галочку с любого изменения, которое не хотите записывать.",
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0,8))

        checks = {}
        rows = ttk.LabelFrame(body, text="Глобальные параметры")
        rows.pack(fill="x")
        for key, newval in suggested.items():
            oldval = current.get(key)
            v = tk.BooleanVar(value=(oldval != newval))
            checks[key] = v
            ttk.Checkbutton(
                rows,
                text=f"{key}: {oldval} -> {newval}",
                variable=v
            ).pack(anchor="w", padx=10, pady=3)

        schedule_var = tk.BooleanVar(value=True)
        profiles_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rows, text="Заменить расписание адаптивным недельным планом", variable=schedule_var).pack(anchor="w", padx=10, pady=3)
        ttk.Checkbutton(rows, text="Сохранить адаптивные профили комнат", variable=profiles_var).pack(anchor="w", padx=10, pady=3)

        preview = tk.Text(body, height=18, wrap="word", bg="#121b2e", fg="#eef4ff", relief="flat")
        preview.pack(fill="both", expand=True, pady=8)
        preview.insert("1.0", self._adaptive_summary_text())
        preview.configure(state="disabled")

        buttons = ttk.Frame(body)
        buttons.pack(fill="x")

        def apply_selected():
            selected = {k: suggested[k] for k,v in checks.items() if v.get()}
            use_schedule = bool(schedule_var.get())
            use_profiles = bool(profiles_var.get())
            win.destroy()
            self._apply_adaptive_changes(selected, use_schedule, use_profiles)

        ttk.Button(buttons,text="Отмена",command=win.destroy).pack(side="right",padx=4)
        ttk.Button(buttons,text="ПРИМЕНИТЬ ВЫБРАННОЕ",style="Accent.TButton",command=apply_selected).pack(side="right",padx=4)

    def _adaptive_timing_payload(self):
        plan = self._adaptive_room_plan()
        # Group a practical schedule around the user's established 11:00 start.
        high = [rid for rid,p in plan.items() if p["frequency_per_week"] >= 6]
        medium_plus = [rid for rid,p in plan.items() if p["frequency_per_week"] >= 4]
        all_rooms = [1,2,3,4,5]
        rows = [
            [39600,1,3,2,[1,4,6],1,all_rooms,0],
        ]
        if high:
            rows.append([39600,1,4,2,[2,3,5],2,high,0])
        sunday_rooms = sorted(set(high + [rid for rid in medium_plus if rid not in high]))
        if sunday_rooms:
            rows.append([39600,1,4 if high else 3,2,[0],2,sunday_rooms,0])

        current = self._parse_timing((self.last_data or {}).get("timing"))
        return {
            "time": rows,
            "tz": current.get("tz", 3),
            "tzs": current.get("tzs", 10800),
        }

    def _apply_adaptive_changes(self, props, apply_schedule, apply_profiles):
        timing = self._adaptive_timing_payload()

        if apply_profiles:
            profiles = self._read_room_profiles_payload()
            plan = self._adaptive_room_plan()
            for rid in range(1,6):
                current = dict(profiles.get(str(rid), {}))
                rec = plan[rid]["profile"]
                current.update(rec)
                current["name"] = ROOM_LABELS[rid]
                profiles[str(rid)] = current
            atomic_write_json(
                ROOM_PROFILES_PATH,
                {
                    "model": MODEL,
                    "saved_at": datetime.now().astimezone().isoformat(),
                    "profiles": profiles,
                    "implementation": "adaptive_v21_runtime_profile",
                }
            )
            try:
                self._populate_room_profiles_ui()
            except Exception:
                pass

        def task():
            d = self.ensure_device()
            before = d.status().data
            self.backup_data(before, "before_adaptive_v21")
            results = {}
            for key, value in props.items():
                try:
                    results[key] = d.set_property(key, value)
                except Exception as e:
                    results[key] = f"ERROR: {e}"
            if apply_schedule:
                try:
                    raw = json.dumps(timing, ensure_ascii=False, separators=(",", ":"))
                    results["timing"] = d.set_timing(raw)
                except Exception as e:
                    results["timing"] = f"ERROR: {e}"
            after = d.status().data
            return before, after, results

        def done(result):
            before, after, results = result
            self.on_status(after)
            if apply_schedule:
                self.current_timing = timing
                self._populate_schedule(timing)
            errors = {k:v for k,v in results.items() if isinstance(v,str) and v.startswith("ERROR")}
            if errors:
                messagebox.showwarning(
                    "Адаптивная оптимизация",
                    "Часть изменений не записалась:\n\n" + json.dumps(errors, ensure_ascii=False, indent=2)
                )
            else:
                messagebox.showinfo(
                    "Адаптивная оптимизация",
                    "Выбранные изменения применены. История продолжит уточнять рекомендации."
                )

        self.async_run(task, done, "Применение адаптивной оптимизации...")

    @staticmethod
    def _firmware_recursive_values(obj, wanted):
        found = {}
        wanted = set(wanted)

        def walk(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    if k in wanted and k not in found:
                        found[k] = v
                    walk(v)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(obj)
        return found

    def _firmware_normalize_cloud(self, cloud_result):
        keys = self._firmware_recursive_values(
            cloud_result,
            {
                "curr", "curVersion", "current_version", "currentVersion",
                "latest", "newVersion", "latest_version", "latestVersion",
                "isLatest", "is_latest", "hasNewFirmware", "has_new_firmware",
                "isForce", "is_force", "description",
                "ota_status", "ota_progress", "state", "progress",
            }
        )
        current = (
            keys.get("curr")
            or keys.get("curVersion")
            or keys.get("current_version")
            or keys.get("currentVersion")
        )
        latest = (
            keys.get("latest")
            or keys.get("newVersion")
            or keys.get("latest_version")
            or keys.get("latestVersion")
        )
        is_latest = keys.get("isLatest")
        if is_latest is None:
            is_latest = keys.get("is_latest")
        has_new = keys.get("hasNewFirmware")
        if has_new is None:
            has_new = keys.get("has_new_firmware")
        if has_new is None and current and latest:
            has_new = str(current) != str(latest)
        if is_latest is None and has_new is not None:
            is_latest = not bool(has_new)

        return {
            "current": current,
            "latest": latest,
            "is_latest": is_latest,
            "has_new": has_new,
            "is_force": keys.get("isForce", keys.get("is_force")),
            "description": keys.get("description"),
            "ota_state": keys.get("ota_status", keys.get("state")),
            "ota_progress": keys.get("ota_progress", keys.get("progress")),
        }

    def _firmware_local_info(self):
        d = self.ensure_device()
        info = d.info(skip_cache=True)
        status = d.status().data
        ota_state = None
        ota_progress = None
        ota_errors = {}

        try:
            state = d.update_state()
            ota_state = getattr(state, "value", state)
        except Exception as e:
            ota_errors["state"] = f"{type(e).__name__}: {e}"

        try:
            ota_progress = d.update_progress()
        except Exception as e:
            ota_errors["progress"] = f"{type(e).__name__}: {e}"

        return {
            "read_at": datetime.now().astimezone().isoformat(),
            "model": info.model,
            "firmware": info.firmware_version,
            "hardware": info.hardware_version,
            "mac": info.mac_address,
            "ip": info.ip_address,
            "status": status,
            "ota_state": ota_state,
            "ota_progress": ota_progress,
            "ota_errors": ota_errors,
            "miio_info": {
                k: v for k, v in (info.raw or {}).items()
                if k not in ("token",)
            },
        }

    def check_firmware_local(self, silent=False):
        def task():
            return self._firmware_local_info()

        def done(result):
            self.firmware_current_var.set(str(result.get("firmware") or "-"))
            self.firmware_hw_var.set(str(result.get("hardware") or "-"))
            self.firmware_model_var.set(str(result.get("model") or MODEL))
            self.firmware_mac_var.set(str(result.get("mac") or "-"))
            self.firmware_ota_state_var.set(str(result.get("ota_state") or "не поддерживается/неизвестно"))
            try:
                self.firmware_ota_progress_var.set(max(0, min(100, int(result.get("ota_progress") or 0))))
            except Exception:
                self.firmware_ota_progress_var.set(0)
            self.firmware_last_report["local"] = result
            self._save_firmware_report()
            if not silent:
                messagebox.showinfo(
                    "Прошивка",
                    f"Модель: {result.get('model')}\n"
                    f"FW: {result.get('firmware')}\n"
                    f"HW: {result.get('hardware')}\n"
                    f"OTA: {result.get('ota_state')} / {result.get('ota_progress')}%"
                )

        if silent:
            future = self.executor.submit(task)
            def finish(fut):
                try:
                    result = fut.result()
                except Exception:
                    return
                try:
                    self.after(0, lambda: done(result))
                except Exception:
                    pass
            future.add_done_callback(finish)
        else:
            self.async_run(task, done, "Чтение версии прошивки...")

    def _firmware_cloud_client(self):
        username = self.cloud_user_var.get().strip()
        password = self.cloud_pass_var.get()

        if not username:
            saved = (
                self._read_cloud_session_file(SHARED_CLOUD_SESSION_PATH)
                or self._read_cloud_session_file(CLOUD_SESSION_PATH)
                or self._migrate_old_cloud_session()
            )
            if saved:
                username = str(saved.get("username") or "")
                self.cloud_user_var.set(username)

        if not username:
            raise RuntimeError("Не найден Xiaomi Cloud аккаунт.")

        client = XiaomiCloudLite(username, password or "")
        saved = self._load_cloud_session(username)
        if not saved or not client.import_auth(saved):
            raise RuntimeError(
                "Нет действующей сохранённой Xiaomi Cloud сессии. "
                "Сначала обновите карту/авторизацию во вкладке «Комнаты/карта»."
            )
        return client

    def _firmware_cloud_check_worker(self):
        token = self.token_var.get().strip()
        if not token:
            raise RuntimeError("Token робота не указан.")

        client = self._firmware_cloud_client()
        country_pref = self.cloud_country_var.get().strip() or "auto"
        dev = client.find_device(token, country_pref)
        if not dev:
            raise RuntimeError("ROIDMI не найден в Xiaomi Cloud по текущему token.")

        cloud = client.firmware_info(
            dev["country"],
            dev["device_id"],
            dev.get("pid", 0) or 0,
        )
        normalized = self._firmware_normalize_cloud(cloud)
        return {
            "read_at": datetime.now().astimezone().isoformat(),
            "device": dev,
            "raw": cloud,
            "normalized": normalized,
        }

    def check_firmware_cloud(self, silent=False):
        def done(result):
            norm = result.get("normalized") or {}
            latest = norm.get("latest")
            current_cloud = norm.get("current")
            self.firmware_latest_var.set(str(latest or "сервер не сообщил версию"))

            has_new = norm.get("has_new")
            if has_new is True:
                msg = f"Xiaomi Cloud: доступна новая прошивка {latest or '?'}."
                self.firmware_cloud_status_var.set(msg)
                self._queue_notification("ROIDMI: обновление прошивки", msg)
            elif norm.get("is_latest") is True:
                msg = "Xiaomi Cloud: установленная прошивка отмечена как актуальная."
                self.firmware_cloud_status_var.set(msg)
            else:
                msg = (
                    "Xiaomi Cloud ответил, но доступность новой версии не определена. "
                    "Смотрите FIRMWARE_REPORT.json."
                )
                self.firmware_cloud_status_var.set(msg)

            self.firmware_last_report["cloud"] = result
            self._save_firmware_report()

            if not silent:
                messagebox.showinfo(
                    "Официальная проверка Xiaomi Cloud",
                    f"Текущая (cloud): {current_cloud or '-'}\n"
                    f"Последняя: {latest or '-'}\n"
                    f"Есть обновление: {has_new}\n"
                    f"Принудительная: {norm.get('is_force')}\n\n"
                    f"{norm.get('description') or msg}"
                )

        if silent:
            future = self.executor.submit(self._firmware_cloud_check_worker)
            def finish(fut):
                try:
                    result = fut.result()
                except Exception:
                    return
                try:
                    self.after(0, lambda: done(result))
                except Exception:
                    pass
            future.add_done_callback(finish)
        else:
            self.async_run(
                self._firmware_cloud_check_worker,
                done,
                "Проверка прошивки через Xiaomi Cloud..."
            )

    def refresh_ota_status(self):
        def task():
            d = self.ensure_device()
            state = None
            progress = None
            errors = {}
            try:
                st = d.update_state()
                state = getattr(st, "value", st)
            except Exception as e:
                errors["state"] = f"{type(e).__name__}: {e}"
            try:
                progress = d.update_progress()
            except Exception as e:
                errors["progress"] = f"{type(e).__name__}: {e}"
            return {"state": state, "progress": progress, "errors": errors}

        def done(result):
            self.firmware_ota_state_var.set(str(result.get("state") or "неизвестно"))
            try:
                self.firmware_ota_progress_var.set(int(result.get("progress") or 0))
            except Exception:
                self.firmware_ota_progress_var.set(0)
            self.firmware_last_report["ota"] = {
                **result,
                "read_at": datetime.now().astimezone().isoformat(),
            }
            self._save_firmware_report()

        self.async_run(task, done, "Проверка OTA-статуса...")

    def _save_firmware_report(self):
        report = {
            "model": MODEL,
            "saved_at": datetime.now().astimezone().isoformat(),
            "local": self.firmware_last_report.get("local"),
            "cloud": self.firmware_last_report.get("cloud"),
            "ota": self.firmware_last_report.get("ota"),
            "ota_update": self.firmware_last_report.get("ota_update"),
            "safety": {
                "automatic_flash": False,
                "official_cloud_check_only": True,
                "expert_ota_requires_url_md5_confirmation": True,
            }
        }
        try:
            atomic_write_json(FIRMWARE_REPORT_PATH, report)
        except Exception:
            pass

    def export_firmware_report(self):
        self._save_firmware_report()
        if not FIRMWARE_REPORT_PATH.exists():
            messagebox.showinfo("Прошивка", "Сначала выполните проверку.")
            return
        dst = filedialog.asksaveasfilename(
            title="Сохранить отчёт о прошивке",
            defaultextension=".json",
            initialfile=f"ROIDMI_firmware_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            filetypes=[("JSON", "*.json")]
        )
        if dst:
            shutil.copy2(FIRMWARE_REPORT_PATH, dst)

    def verify_firmware_url_md5(self):
        url = self.firmware_url_var.get().strip()
        expected = self.firmware_md5_var.get().strip().lower()
        if not re.fullmatch(r"https?://.+", url):
            messagebox.showerror("OTA", "Укажите http/https URL файла прошивки.")
            return
        if not re.fullmatch(r"[0-9a-fA-F]{32}", expected):
            messagebox.showerror("OTA", "MD5 должен содержать ровно 32 шестнадцатеричных символа.")
            return

        def task():
            parsed = urlparse.urlparse(url)
            name = Path(urlparse.unquote(parsed.path)).name or "firmware.pkg"
            name = re.sub(r'[^A-Za-z0-9._()\\-]+', "_", name)
            dst = FIRMWARE_DOWNLOAD_DIR / name
            tmp = dst.with_suffix(dst.suffix + ".part")
            h = hashlib.md5()
            total = 0
            max_bytes = 1024 * 1024 * 1024
            with requests.get(
                url, stream=True, timeout=60,
                headers={"User-Agent": "ROIDMI-EVE-Plus-Control/21.1"}
            ) as r:
                r.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_bytes:
                            raise RuntimeError("Файл больше 1 GiB. Проверка остановлена.")
                        h.update(chunk)
                        f.write(chunk)
            actual = h.hexdigest()
            if actual.lower() != expected.lower():
                tmp.unlink(missing_ok=True)
                raise RuntimeError(
                    f"MD5 не совпадает.\nОжидался: {expected}\nПолучен: {actual}"
                )
            tmp.replace(dst)
            return {"path": str(dst), "size": total, "md5": actual}

        def done(result):
            messagebox.showinfo(
                "Проверка прошивки",
                f"Файл скачан на ПК и MD5 подтверждён.\n\n"
                f"{result['path']}\n"
                f"Размер: {self._human_size(result['size'])}\n"
                f"MD5: {result['md5']}\n\n"
                "Это проверяет целостность файла, но не подтверждает его совместимость с roidmi.vacuum.v60."
            )

        self.async_run(task, done, "Скачивание и проверка MD5...")

    def _firmware_preflight(self):
        d = self.ensure_device()
        info = d.info(skip_cache=True)
        status = d.status().data

        errors = []
        if str(info.model) != MODEL:
            errors.append(f"Модель {info.model}, ожидалась {MODEL}.")
        try:
            battery = int(status.get("battery_level") or 0)
        except Exception:
            battery = 0
        if battery < 80:
            errors.append(f"Аккумулятор {battery}%. Для OTA требуется не менее 80%.")
        if int(status.get("charging_state") or 0) != 1:
            errors.append("Робот должен стоять на базе и заряжаться.")
        if int(status.get("error_code") or 0) != 0:
            errors.append(f"Есть ошибка робота: {status.get('error_code')}.")
        if int(status.get("state") or 0) == 4:
            errors.append("Нельзя обновлять прошивку во время уборки.")

        return {
            "ok": not errors,
            "errors": errors,
            "info": {
                "model": info.model,
                "firmware": info.firmware_version,
                "hardware": info.hardware_version,
                "mac": info.mac_address,
            },
            "status": status,
        }

    def start_expert_firmware_ota(self):
        if not self.firmware_expert_var.get():
            messagebox.showerror(
                "OTA",
                "Включите флажок экспертного режима после прочтения предупреждения."
            )
            return

        url = self.firmware_url_var.get().strip()
        md5 = self.firmware_md5_var.get().strip().lower()
        if not re.fullmatch(r"https?://.+", url):
            messagebox.showerror("OTA", "Нужен прямой http/https URL прошивки.")
            return
        if not re.fullmatch(r"[0-9a-fA-F]{32}", md5):
            messagebox.showerror("OTA", "Нужен корректный MD5.")
            return

        def preflight_task():
            return self._firmware_preflight()

        def preflight_done(result):
            if not result["ok"]:
                messagebox.showerror(
                    "OTA заблокирована",
                    "\n".join("• " + x for x in result["errors"])
                )
                return

            current_fw = result["info"].get("firmware")
            expected_fw = self.firmware_expected_var.get().strip() or "не указана"
            confirm = simpledialog.askstring(
                "КРИТИЧЕСКОЕ ПОДТВЕРЖДЕНИЕ OTA",
                "Обновление прошивки может вывести робот из строя при неверном файле.\n\n"
                f"Модель: {MODEL}\n"
                f"Текущая FW: {current_fw}\n"
                f"Ожидаемая FW: {expected_fw}\n"
                f"Батарея: {result['status'].get('battery_level')}%\n\n"
                "Используйте только прошивку для roidmi.vacuum.v60.\n"
                "Для продолжения введите UPDATE:"
            )
            if confirm != "UPDATE":
                return

            self.backup_data(result["status"], "before_firmware_ota")
            self._start_firmware_ota_worker(url, md5, expected_fw)

        self.async_run(preflight_task, preflight_done, "Предварительная проверка OTA...")

    def _start_firmware_ota_worker(self, url, md5, expected_fw):
        self.firmware_monitor_cancel = False

        def task():
            d = self.ensure_device()
            old_fw = self.firmware_current_var.get()
            started = d.update(url, md5)
            if not started:
                raise RuntimeError("Робот не подтвердил команду miIO.ota.")

            samples = []
            started_at = time.time()
            last_progress = 0
            while time.time() - started_at < 35 * 60:
                if self.firmware_monitor_cancel:
                    break
                state = None
                progress = None
                err = None
                try:
                    st = d.update_state()
                    state = getattr(st, "value", st)
                    progress = d.update_progress()
                    try:
                        last_progress = int(progress)
                    except Exception:
                        pass
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"

                samples.append({
                    "at": datetime.now().astimezone().isoformat(),
                    "state": state,
                    "progress": progress,
                    "error": err,
                })

                try:
                    self.after(
                        0,
                        lambda s=state, p=last_progress: (
                            self.firmware_ota_state_var.set(str(s or "переподключение...")),
                            self.firmware_ota_progress_var.set(max(0, min(100, int(p or 0))))
                        )
                    )
                except Exception:
                    pass

                if state == "failed" or last_progress >= 100:
                    break
                time.sleep(5)

            final_info = None
            for _ in range(24):
                if self.firmware_monitor_cancel:
                    break
                try:
                    time.sleep(5)
                    inf = d.info(skip_cache=True)
                    final_info = {
                        "model": inf.model,
                        "firmware": inf.firmware_version,
                        "hardware": inf.hardware_version,
                    }
                    if final_info.get("firmware") and final_info.get("firmware") != old_fw:
                        break
                except Exception:
                    continue

            return {
                "started": started,
                "url": url,
                "md5": md5,
                "expected_firmware": expected_fw,
                "samples": samples[-300:],
                "final_info": final_info,
                "ended_at": datetime.now().astimezone().isoformat(),
            }

        def done(result):
            self.firmware_last_report["ota_update"] = result
            self._save_firmware_report()
            final_fw = (result.get("final_info") or {}).get("firmware")
            if final_fw:
                self.firmware_current_var.set(str(final_fw))
            self.firmware_ota_state_var.set("мониторинг завершён")
            expected = self.firmware_expected_var.get().strip()

            if expected and final_fw and str(final_fw) != expected:
                messagebox.showwarning(
                    "OTA завершена",
                    f"Робот снова доступен, но версия {final_fw} не совпадает с ожидаемой {expected}."
                )
            else:
                messagebox.showinfo(
                    "OTA",
                    f"Мониторинг завершён.\nВерсия после переподключения: {final_fw or 'не удалось прочитать'}."
                )

        self.async_run(task, done, "Запуск OTA и мониторинг...")

    def cancel_firmware_monitor(self):
        self.firmware_monitor_cancel = True
        self.firmware_ota_state_var.set(
            "Мониторинг остановлен. Сам процесс OTA на роботе не отменяется."
        )

    def _maybe_auto_firmware_check(self):
        if not bool(self.firmware_auto_check_var.get()):
            return
        now = time.time()
        last = float(self.app_settings.get("firmware_last_auto_check", 0) or 0)
        if now - last < 24 * 3600:
            return
        self.app_settings["firmware_last_auto_check"] = now
        self.app_settings["firmware_auto_check"] = True
        atomic_write_json(APP_SETTINGS_PATH, self.app_settings)

        if self.ip_var.get().strip() and self.token_var.get().strip():
            self.check_firmware_local(silent=True)

        if self._read_cloud_session_file(SHARED_CLOUD_SESSION_PATH):
            self.check_firmware_cloud(silent=True)

    def open_4pda_firmware_topic(self):
        webbrowser.open("https://4pda.to/forum/index.php?showtopic=1023628")

    def open_selected_4pda_firmware(self):
        tree = self.firmware_4pda_tree
        if tree is None:
            return
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("4PDA", "Выберите строку прошивки.")
            return
        try:
            idx = int(sel[0])
            item = FIRMWARE_4PDA_CATALOG[idx]
        except Exception:
            return
        webbrowser.open(item["url"])

    def use_selected_4pda_version_as_expected(self):
        tree = self.firmware_4pda_tree
        if tree is None:
            return
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("4PDA", "Выберите версию.")
            return
        try:
            idx = int(sel[0])
            item = FIRMWARE_4PDA_CATALOG[idx]
        except Exception:
            return
        self.firmware_expected_var.set(item["version"])
        messagebox.showinfo(
            "4PDA",
            f"Версия {item['version']} подставлена только как ожидаемая версия. "
            "Это НЕ означает, что найден совместимый файл прошивки."
        )

    def _build_firmware_tab(self):
        root = ttk.Frame(self.tab_firmware)
        root.pack(fill="both", expand=True, padx=10, pady=8)

        head = ttk.Frame(root, style="Toolbar.TFrame")
        head.pack(fill="x", pady=(0, 8))
        ttk.Label(head, text="Прошивка ROIDMI EVE Plus", style="Header.TLabel").pack(
            anchor="w", padx=14, pady=(10, 2)
        )
        ttk.Label(
            head,
            text=(
                "miIO.info + официальная Xiaomi Cloud проверка + OTA state/progress. "
                "Автоматическая установка без подтверждения отключена."
            ),
            style="SubHeader.TLabel"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        top = ttk.Frame(root)
        top.pack(fill="x")
        local = ttk.LabelFrame(top, text="Установленная прошивка", style="Section.TLabelframe")
        cloud = ttk.LabelFrame(top, text="Xiaomi Cloud", style="Section.TLabelframe")
        local.pack(side="left", fill="both", expand=True, padx=(0, 4))
        cloud.pack(side="left", fill="both", expand=True, padx=(4, 0))

        for i, (label, var) in enumerate([
            ("Модель", self.firmware_model_var),
            ("Firmware", self.firmware_current_var),
            ("Hardware", self.firmware_hw_var),
            ("MAC", self.firmware_mac_var),
        ]):
            ttk.Label(local, text=label + ":", style="Muted.TLabel").grid(
                row=i, column=0, sticky="e", padx=8, pady=5
            )
            ttk.Label(local, textvariable=var).grid(
                row=i, column=1, sticky="w", padx=8, pady=5
            )
        ttk.Button(
            local, text="ПРОВЕРИТЬ ЛОКАЛЬНО",
            style="Accent.TButton", command=self.check_firmware_local
        ).grid(row=4, column=0, columnspan=2, padx=8, pady=10)

        ttk.Label(cloud, text="Последняя версия:", style="Muted.TLabel").pack(
            anchor="w", padx=10, pady=(10, 2)
        )
        ttk.Label(
            cloud, textvariable=self.firmware_latest_var,
            font=("Segoe UI Semibold", 12)
        ).pack(anchor="w", padx=10, pady=(0, 5))
        ttk.Label(
            cloud, textvariable=self.firmware_cloud_status_var,
            style="Muted.TLabel", wraplength=680, justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))
        cbar = ttk.Frame(cloud, style="Card.TFrame")
        cbar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(
            cbar, text="ОФИЦИАЛЬНАЯ ПРОВЕРКА",
            style="Accent.TButton", command=self.check_firmware_cloud
        ).pack(side="left", padx=4, pady=5)
        ttk.Button(
            cbar, text="Экспорт JSON",
            command=self.export_firmware_report
        ).pack(side="left", padx=4, pady=5)
        ttk.Checkbutton(
            cbar, text="Автопроверка раз в сутки",
            variable=self.firmware_auto_check_var,
            command=self._save_app_settings
        ).pack(side="right", padx=8)

        ota = ttk.LabelFrame(root, text="OTA status", style="Section.TLabelframe")
        ota.pack(fill="x", pady=(8, 0))
        row = ttk.Frame(ota, style="Card.TFrame")
        row.pack(fill="x", padx=8, pady=8)
        ttk.Label(row, text="Состояние:", style="Muted.TLabel").pack(side="left")
        ttk.Label(row, textvariable=self.firmware_ota_state_var).pack(side="left", padx=6)
        ttk.Progressbar(
            row, maximum=100, variable=self.firmware_ota_progress_var, length=420
        ).pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(row, textvariable=self.firmware_ota_progress_var).pack(side="left")
        ttk.Label(row, text="%").pack(side="left")
        ttk.Button(row, text="Обновить статус", command=self.refresh_ota_status).pack(
            side="right", padx=4
        )
        ttk.Button(row, text="Стоп мониторинга", command=self.cancel_firmware_monitor).pack(
            side="right", padx=4
        )

        forum = ttk.LabelFrame(
            root, text="4PDA: найденные упоминания прошивок",
            style="Section.TLabelframe"
        )
        forum.pack(fill="x", pady=(8, 0))
        cols = ("version", "status", "year")
        self.firmware_4pda_tree = ttk.Treeview(
            forum, columns=cols, show="headings", height=6
        )
        self.firmware_4pda_tree.heading("version", text="Версия")
        self.firmware_4pda_tree.heading("status", text="Что найдено на 4PDA")
        self.firmware_4pda_tree.heading("year", text="Период")
        self.firmware_4pda_tree.column("version", width=150, anchor="center")
        self.firmware_4pda_tree.column("status", width=760, anchor="w")
        self.firmware_4pda_tree.column("year", width=130, anchor="center")
        for idx, item in enumerate(FIRMWARE_4PDA_CATALOG):
            self.firmware_4pda_tree.insert(
                "", "end", iid=str(idx),
                values=(item["version"], item["status"], item["year"])
            )
        self.firmware_4pda_tree.pack(fill="x", padx=8, pady=(8,4))
        fbar = ttk.Frame(forum, style="Card.TFrame")
        fbar.pack(fill="x", padx=8, pady=(0,8))
        ttk.Button(
            fbar, text="Открыть выбранное сообщение",
            command=self.open_selected_4pda_firmware
        ).pack(side="left", padx=4)
        ttk.Button(
            fbar, text="Открыть тему 4PDA",
            command=self.open_4pda_firmware_topic
        ).pack(side="left", padx=4)
        ttk.Button(
            fbar, text="Подставить версию в поле «Ожидаемая»",
            command=self.use_selected_4pda_version_as_expected
        ).pack(side="left", padx=4)
        ttk.Label(
            fbar,
            text="4PDA - источник пользовательских сообщений, не автоматическое подтверждение совместимости.",
            style="Muted.TLabel"
        ).pack(side="right", padx=8)

        expert = ttk.LabelFrame(
            root, text="Экспертный OTA по URL + MD5",
            style="Section.TLabelframe"
        )
        expert.pack(fill="both", expand=True, pady=(8, 0))

        ttk.Label(
            expert,
            text=(
                "Используйте только проверенную прошивку именно для roidmi.vacuum.v60. "
                "Перед OTA программа проверит модель, заряд >=80%, базу/зарядку, ошибки и активную уборку."
            ),
            style="Muted.TLabel", wraplength=1500, justify="left"
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 6))

        ttk.Label(expert, text="Прямой URL:").grid(row=1, column=0, sticky="e", padx=8, pady=5)
        ttk.Entry(expert, textvariable=self.firmware_url_var).grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=8, pady=5
        )
        ttk.Label(expert, text="MD5:").grid(row=2, column=0, sticky="e", padx=8, pady=5)
        ttk.Entry(expert, textvariable=self.firmware_md5_var, width=40).grid(
            row=2, column=1, sticky="w", padx=8, pady=5
        )
        ttk.Label(expert, text="Ожидаемая версия:").grid(row=3, column=0, sticky="e", padx=8, pady=5)
        ttk.Entry(expert, textvariable=self.firmware_expected_var, width=30).grid(
            row=3, column=1, sticky="w", padx=8, pady=5
        )

        ttk.Checkbutton(
            expert,
            text="Экспертный режим: я понимаю риск неверной прошивки",
            variable=self.firmware_expert_var
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=8)

        buttons = ttk.Frame(expert, style="Card.TFrame")
        buttons.grid(row=5, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 10))
        ttk.Button(
            buttons, text="Скачать на ПК и проверить MD5",
            command=self.verify_firmware_url_md5
        ).pack(side="left", padx=4, pady=5)
        ttk.Button(
            buttons, text="ЗАПУСТИТЬ OTA",
            style="Accent2.TButton", command=self.start_expert_firmware_ota
        ).pack(side="right", padx=4, pady=5)

        expert.grid_columnconfigure(1, weight=1)

    def _build_sources_tab(self):
        outer = ttk.Frame(self.tab_sources)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        intro = (
            "Эта версия не использует Home Assistant. Управление свойствами и основными действиями идёт напрямую "
            "по LAN MIoT через IP/token. Xiaomi Cloud используется только опционально для карты и fallback выборочной уборки."
        )
        ttk.Label(outer, text=intro, wraplength=1080, justify="left").pack(anchor="w", pady=(0,8))

        cols = ("feature","miot","sources")
        tree = ttk.Treeview(outer, columns=cols, show="headings", height=18)
        tree.heading("feature", text="Функция")
        tree.heading("miot", text="MIoT")
        tree.heading("sources", text="Проверено по GitHub")
        tree.column("feature", width=260, anchor="w")
        tree.column("miot", width=160, anchor="center")
        tree.column("sources", width=640, anchor="w")
        rows = [
            ("Старт / стоп", "2/1, 2/2", "python-miio; node-xmihome; com.xiaomi-miio; openHAB"),
            ("Возврат на базу", "3/1", "python-miio; node-xmihome; com.xiaomi-miio; openHAB"),
            ("Мощность", "2/4", "python-miio; node-xmihome; com.xiaomi-miio; openHAB"),
            ("Тип уборки", "2/8", "python-miio; node-xmihome; openHAB; Roidmi-EVE-Plus"),
            ("Подача воды", "8/11", "python-miio; node-xmihome; openHAB; Roidmi-EVE-Plus"),
            ("Расписание", "8/6", "python-miio; openHAB"),
            ("DND", "8/10", "python-miio; openHAB"),
            ("Ковровый boost", "8/9", "python-miio; openHAB; Roidmi-EVE-Plus"),
            ("Double clean", "8/20", "python-miio; openHAB; Roidmi-EVE-Plus"),
            ("LiDAR collision", "8/23", "python-miio; openHAB; Roidmi-EVE-Plus"),
            ("Станция: частота", "8/2", "python-miio; openHAB; Roidmi-EVE-Plus"),
            ("Станция: сбор пыли", "8/6 action", "python-miio; hass-xiaomi-miot; openHAB"),
            ("Выборочная уборка", "14/1 action", "node-xmihome; Roidmi-EVE-Plus; Xiaomi map format"),
            ("Голос: current-audio", "8/26 property", "MIoT spec; python-miio; openHAB"),
            ("Голос: set-voice", "8/12 action, input 8/27", "MIoT spec; python-miio; openHAB"),            ("Автопоиск ROIDMI", "UDP 54321 handshake", "python-miio MiIOProtocol discovery"),
            ("Реальная карта", "скриншот Xiaomi / PNG/JPG", "встроенный real_map_reference.png + загрузка пользовательского файла"),
            ("Native покомнатные fan/water", "13/10 area-custom", "openHAB MIoT database; payload string schema not decoded"),
            ("Профильная уборка комнат", "14/1 + property writes", "v20 safe sequential implementation"),
            ("Карта / комнаты", "cloud map /0", "node-xmihome; Xiaomi Cloud Map Extractor"),
            ("Бак воды", "250 мл nominal / 220 мл conservative", "ROIDMI regional product page; SDJ01RM manuals"),
            ("Аккумулятор", "5200 mAh", "SDJ01RM manuals"),
            ("Макс. всасывание", "2700 Pa", "ROIDMI product page"),
            ("Мешок станции", "3 L", "SDJ01RM manuals / ROIDMI product page"),
        ]
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True)

        btn = ttk.Frame(outer)
        btn.pack(fill="x", pady=(8,0))
        ttk.Button(
            btn, text="Открыть GITHUB_RESEARCH.md",
            command=lambda: os.startfile(str(ROOT / "GITHUB_RESEARCH.md"))
        ).pack(side="left", padx=4)
        ttk.Button(
            btn, text="Открыть SOURCE_MATRIX.json",
            command=lambda: os.startfile(str(ROOT / "SOURCE_MATRIX.json"))
        ).pack(side="left", padx=4)

    def _build_statusbar(self):
        self.statusbar_var = tk.StringVar(value="Готово.")
        bar = ttk.Frame(self, style="Toolbar.TFrame")
        bar.pack(fill="x", side="bottom", padx=10, pady=(0, 8))
        ttk.Label(bar, textvariable=self.statusbar_var, style="SubHeader.TLabel", anchor="w").pack(fill="x", padx=12, pady=8)

    def set_busy(self, value, text=None):
        self.busy = value
        if text:
            self.statusbar_var.set(text)
        elif not value:
            self.statusbar_var.set("Готово.")

    def async_run(self, fn, on_success=None, label="Выполняется..."):
        if self.busy:
            messagebox.showinfo("Операция выполняется", "Дождитесь завершения текущей операции.")
            return
        self.set_busy(True, label)

        future = self.executor.submit(fn)

        def finished(fut):
            try:
                result = fut.result()
            except Exception as e:
                tb = traceback.format_exc()
                try:
                    self.after(0, lambda err=e, trace=tb: self._async_error(err, trace))
                except Exception:
                    pass
            else:
                try:
                    self.after(0, lambda result=result: self._async_success(result, on_success))
                except Exception:
                    pass

        future.add_done_callback(finished)


    def _async_error(self, e, tb):
        self.set_busy(False)
        self.statusbar_var.set("Ошибка.")
        msg = str(e)
        if "Unable to discover the device" in msg:
            detail = (
                "Робот не отвечает по указанному IP. Это происходит до проверки token.\n\n"
                "Проверьте, что ROIDMI включён и подключён к Wi-Fi, а IP в программе всё ещё актуален. "
                "После перезапуска роутера DHCP мог выдать роботу другой адрес. "
                "ПК и робот должны быть в одной локальной сети; VPN/Firewall не должны блокировать LAN/UDP."
            )
            try:
                self.dashboard_status_var.set("Нет связи")
                self.dashboard_substatus_var.set(f"Робот не найден по IP {self.ip_var.get().strip()}")
            except Exception:
                pass
        else:
            detail = "Проверьте IP, token, доступность робота в локальной сети и VPN/Firewall."
        messagebox.showerror(
            "Ошибка",
            f"{e}\n\n{detail}\n\nПодробности записаны в error.log."
        )
        (ROOT/"error.log").write_text(tb, encoding="utf-8")

    def _async_success(self, result, callback):
        self.set_busy(False)
        if callback:
            callback(result)

    def validate_connection(self):
        ip = self.ip_var.get().strip()
        token = self.token_var.get().strip().lower()
        try:
            ipaddress.ip_address(ip)
        except Exception:
            raise ValueError("Некорректный IP-адрес.")
        if len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
            raise ValueError("Token должен содержать 32 шестнадцатеричных символа.")
        if RoidmiVacuumMiot is None:
            raise RuntimeError(f"python-miio не загружен: {IMPORT_ERROR}")
        return ip, token

    def make_device(self):
        ip, token = self.validate_connection()
        return RoidmiVacuumMiot(ip, token, model=MODEL)

    def connect_and_read(self):
        try:
            ip, token = self.validate_connection()
        except Exception as e:
            messagebox.showerror("Подключение", str(e))
            return
        def task():
            return self._connect_with_recovery(ip, token)

        def done(result):
            self.device = result["device"]
            if result["ip"] != self.ip_var.get().strip():
                self.ip_var.set(result["ip"])
                self._save_discovered_vacuum_ip(result["ip"])
                self.discovery_status_var.set(
                    f"Старый IP не отвечал. Новый IP ROIDMI: {result['ip']}."
                )
            self.on_status(result["status"])

        self.async_run(task, done, "Подключение; при необходимости автопоиск IP...")

    def ensure_device(self):
        if self.device is None:
            self.device = self.make_device()
        return self.device

    def read_status(self):
        def task():
            d = self.ensure_device()
            return d.status().data
        self.async_run(task, self.on_status, "Чтение состояния...")

    def _default_app_settings(self):
        return {
            "season_mode": "Авто",
            "minimize_to_tray": True,
            "update_manifest_url": GITHUB_MANIFEST_URL,
            "github_auto_check": True,
            "github_check_interval_hours": 12,
            "max_map_snapshots": 20,
            "monitor_enabled": True,
            "water_model": "roidmi_eve_plus_specs_v1",
            "auto_water_refill_on_tank_reinsert": True,
            "water_tank_reinsert_min_absence_sec": 3,
            "water_low_threshold_pct": 30,
            "firmware_auto_check": True,
            "firmware_last_auto_check": 0,
        }

    def _load_app_settings(self):
        data = self._default_app_settings()
        obj = load_json_file(APP_SETTINGS_PATH, {})
        if isinstance(obj, dict):
            data.update(obj)
        return data

    def _save_app_settings(self):
        self.app_settings.update({
            "season_mode": self.season_mode_var.get(),
            "minimize_to_tray": bool(self.minimize_to_tray_var.get()),
            "update_manifest_url": self.update_manifest_url_var.get().strip() or GITHUB_MANIFEST_URL,
            "github_auto_check": bool(self.github_auto_check_var.get()),
            "firmware_auto_check": bool(self.firmware_auto_check_var.get()),
            "auto_water_refill_on_tank_reinsert": bool(self.auto_water_refill_var.get()),
            "water_low_threshold_pct": int(self.water_low_threshold_var.get() or 30),
        })
        atomic_write_json(APP_SETTINGS_PATH, self.app_settings)
        self.center_status_var.set("Настройки интеллектуального центра сохранены.")

    def _load_notify_config(self):
        obj = load_json_file(PRIVATE_NOTIFY_CONFIG_PATH, {})
        return obj if isinstance(obj, dict) else {}

    def _save_notify_config(self):
        data = {
            "windows": bool(self.notify_windows_var.get()),
            "telegram_enabled": bool(self.notify_telegram_var.get()),
            "telegram_token": self.telegram_token_var.get().strip(),
            "telegram_chat_id": self.telegram_chat_var.get().strip(),
            "ntfy_enabled": bool(self.notify_ntfy_var.get()),
            "ntfy_url": self.ntfy_url_var.get().strip(),
            "email_enabled": bool(self.notify_email_var.get()),
            "email_to": self.email_to_var.get().strip(),
            "smtp_host": self.smtp_host_var.get().strip() or "smtp.gmail.com",
            "smtp_port": int(self.smtp_port_var.get() or 587),
            "smtp_user": self.smtp_user_var.get().strip(),
            "smtp_password": self.smtp_password_var.get(),
        }
        atomic_write_json(PRIVATE_NOTIFY_CONFIG_PATH, data)
        self.notify_config = data
        self.center_status_var.set(
            "Уведомления сохранены. Приватные токены не включаются в обычный экспорт."
        )

    def _season_factor(self):
        mode = self.season_mode_var.get()
        if mode == "Грязный сезон":
            return 1.20
        if mode == "Экономичный":
            return 0.80
        if mode == "Обычный":
            return 1.0
        month = datetime.now().month
        # Auto: winter and wet shoulder months increase entrance/corridor attention.
        if month in (12, 1, 2, 3, 11):
            return 1.15
        if month in (6, 7, 8):
            return 0.90
        return 1.0

    def _room_area_map(self):
        result = {}
        analysis = self.last_map_analysis or load_json_file(LIVE_MAP_ANALYSIS_PATH, {})
        rooms = analysis.get("rooms") if isinstance(analysis, dict) else {}
        if isinstance(rooms, dict):
            for key, value in rooms.items():
                try:
                    rid = int(key)
                except Exception:
                    rid = int(value.get("id")) if isinstance(value, dict) and value.get("id") is not None else None
                if rid is None or not isinstance(value, dict):
                    continue
                area = value.get("area_m2_approx")
                if isinstance(area, (int, float)) and area > 0:
                    result[rid] = float(area)
        return result

    def _last_cleaned_by_room(self):
        last = {}
        try:
            with db_connect() as con:
                rows = con.execute(
                    """
                    SELECT ended_at, rooms_json
                    FROM cleaning_sessions
                    WHERE result='completed'
                    ORDER BY ended_at DESC
                    LIMIT 300
                    """
                ).fetchall()
            for row in rows:
                try:
                    rooms = json.loads(row["rooms_json"] or "[]")
                except Exception:
                    rooms = []
                for rid in rooms:
                    try:
                        rid = int(rid)
                    except Exception:
                        continue
                    if rid not in last:
                        last[rid] = row["ended_at"]
        except Exception:
            pass
        return last

    def _adaptive_room_plan(self):
        profiles = self._read_room_profiles_payload()
        hist = self._history_room_stats()
        areas = self._room_area_map()
        last_cleaned = self._last_cleaned_by_room()
        season = self._season_factor()
        fallback_spm = SMART_OPTIMIZATION_STATS["historical_seconds_per_m2"]
        plan = {}

        dirt_base = {"Высокий": 7, "Средний": 4, "Низкий": 3}
        max_days = {"Высокий": 1, "Средний": 2, "Низкий": 3}
        now = datetime.now().astimezone()

        for rid in range(1, 6):
            p = dict(profiles.get(str(rid), {}))
            dirt = p.get("dirt_level", "Средний")
            floor = p.get("floor_type", "Другое")
            frequency = dirt_base.get(dirt, 4)

            if rid in (1, 3):
                frequency = max(frequency, 6)
            if season > 1.05 and rid == 3:
                frequency = 7
            elif season < 0.95 and dirt == "Низкий":
                frequency = max(2, frequency - 1)

            learned = hist.get(rid, {})
            spm = learned.get("sec_per_m2")
            if not spm or learned.get("samples", 0) < 2:
                spm = fallback_spm
            area = areas.get(rid)
            duration_min = (area * spm / 60.0) if area else None

            overdue = False
            last_ts = last_cleaned.get(rid)
            days_since = None
            if last_ts:
                try:
                    dt = datetime.fromisoformat(last_ts)
                    days_since = (now - dt).total_seconds() / 86400.0
                    overdue = days_since > max_days.get(dirt, 2)
                except Exception:
                    pass

            rec = self._recommend_profile_for_floor_dirt(rid, floor, dirt)
            # Regular daily high-dirt schedule makes double-clean unnecessary.
            if frequency >= 6:
                rec["double_clean"] = False

            plan[rid] = {
                "room": ROOM_LABELS[rid],
                "floor_type": floor,
                "dirt_level": dirt,
                "frequency_per_week": int(frequency),
                "max_days_without_clean": max_days.get(dirt, 2),
                "last_cleaned": last_ts,
                "days_since_clean": round(days_since, 1) if days_since is not None else None,
                "overdue": overdue,
                "learned_samples": learned.get("samples", 0),
                "sec_per_m2": round(float(spm), 1),
                "area_m2": area,
                "estimated_duration_min": round(duration_min, 1) if duration_min is not None else None,
                "profile": rec,
            }
        return plan

    def _adaptive_summary_text(self):
        plan = self._adaptive_room_plan()
        lines = ["Адаптивная оптимизация по карте, истории и профилям"]
        lines.append("=" * 58)
        lines.append(f"Сезонный режим: {self.season_mode_var.get()} (коэффициент {self._season_factor():.2f})")
        lines.append("")
        total_week_min = 0.0
        for rid in range(1, 6):
            p = plan[rid]
            dur = p["estimated_duration_min"]
            if dur:
                total_week_min += dur * p["frequency_per_week"]
            due = " | ПРОСРОЧЕНА" if p["overdue"] else ""
            learned = (
                f"обучение {p['learned_samples']} замеров"
                if p["learned_samples"] else "оценка по общей статистике"
            )
            lines.append(
                f"{rid}. {p['room']}: {p['frequency_per_week']} раз/нед.; "
                f"{p['floor_type']}; загрязнение {p['dirt_level']}; "
                f"{p['estimated_duration_min'] if p['estimated_duration_min'] is not None else '-'} мин; "
                f"{learned}{due}"
            )
        lines.append("")
        lines.append(f"Расчётная суммарная занятость: около {total_week_min:.0f} мин/нед.")
        lines.append(
            "План автоматически уточняется, когда появляются точные замеры отдельных комнат."
        )
        return "\n".join(lines)

    def _consumable_forecast_text(self):
        d = self.last_data or {}
        daily = self._daily_cleaning_minutes()
        items = [
            ("Фильтр", d.get("filter_left_minutes"), d.get("filter_life_level")),
            ("Основная щётка", d.get("main_brush_left_minutes"), d.get("main_brush_life_level")),
            ("Боковые щётки", d.get("side_brushes_left_minutes"), d.get("side_brushes_life_level")),
            ("Датчики", d.get("sensor_dirty_time_left_minutes"), d.get("sensor_dirty_remaning_level")),
        ]
        lines = [f"Средняя нагрузка: {daily:.1f} мин уборки/день."]
        for name, mins, pct in items:
            if isinstance(mins, (int, float)) and mins >= 0 and daily > 0:
                days = mins / daily
                lines.append(f"{name}: {pct if pct is not None else '-'}% | ~{days:.0f} дней")
            else:
                lines.append(f"{name}: недостаточно данных")
        return "\n".join(lines)

    def _water_usage_since_fill(self):
        """Estimate actual used water from recorded completed wet-cleaning sessions."""
        capacity = float(TECH_SPECS["water_tank_conservative_ml"])
        last_fill = self._last_assumed_water_fill()
        if not last_fill:
            return {
                "last_fill": None,
                "used_ml": 0.0,
                "remaining_ml": capacity,
                "remaining_pct": 100.0,
                "sessions": 0,
                "estimated_sessions": 0,
            }

        used_ml = 0.0
        sessions = 0
        estimated_sessions = 0

        try:
            with db_connect() as con:
                rows = con.execute(
                    """
                    SELECT ended_at, source, rooms_json, area_m2, water, sweep_type, path_mode, notes
                    FROM cleaning_sessions
                    WHERE ended_at >= ? AND result='completed'
                    ORDER BY ended_at ASC
                    """,
                    (last_fill,)
                ).fetchall()
        except Exception:
            rows = []

        for row in rows:
            try:
                area = float(row["area_m2"] or 0.0)
                water = int(row["water"] or 0)
                sweep = int(row["sweep_type"] or 0)
                path = int(row["path_mode"] or 0)
            except Exception:
                continue

            # Dry-only cleaning consumes no tank water.
            if area <= 0 or water <= 0 or sweep not in (1, 2):
                continue

            rate = float(
                WATER_FLOW_ML_PER_M2.get(
                    water,
                    WATER_FLOW_ML_PER_M2[max(WATER_FLOW_ML_PER_M2)]
                )
            )
            # Y and repeat mopping increase actual travel / wet passes.
            path_factor = 1.0
            if path == 1:
                path_factor = 1.25
            elif path == 2:
                path_factor = 1.50

            session_ml = area * rate * path_factor
            used_ml += session_ml
            sessions += 1

            if str(row["source"] or "") == "detected":
                estimated_sessions += 1

        used_ml = max(0.0, used_ml)
        remaining_ml = max(0.0, capacity - used_ml)
        remaining_pct = max(0.0, min(100.0, remaining_ml / capacity * 100.0))

        return {
            "last_fill": last_fill,
            "used_ml": used_ml,
            "remaining_ml": remaining_ml,
            "remaining_pct": remaining_pct,
            "sessions": sessions,
            "estimated_sessions": estimated_sessions,
        }

    def _low_water_alert_exists_for_fill(self, last_fill):
        if not last_fill:
            return False
        try:
            with db_connect() as con:
                row = con.execute(
                    """
                    SELECT id FROM water_tank_events
                    WHERE event_type='low_water_alert'
                      AND occurred_at >= ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (last_fill,)
                ).fetchone()
            return row is not None
        except Exception:
            return False

    def _record_low_water_alert(self, usage, threshold):
        self._record_water_tank_event(
            "low_water_alert",
            source="calculated_usage",
            mop_present=(self.last_data or {}).get("mop_present"),
            assumed_full=False,
            notes=(
                f"Расчётный остаток {usage['remaining_pct']:.1f}% "
                f"({usage['remaining_ml']:.0f} мл), порог {threshold}%."
            )
        )

    def _check_low_water_threshold(self):
        usage = self._water_usage_since_fill()
        last_fill = usage.get("last_fill")
        if not last_fill:
            return

        try:
            threshold = int(self.water_low_threshold_var.get() or 30)
        except Exception:
            threshold = 30
        threshold = max(5, min(95, threshold))

        pct = float(usage.get("remaining_pct") or 0.0)
        if pct > threshold:
            return
        if self._low_water_alert_exists_for_fill(last_fill):
            return

        self._record_low_water_alert(usage, threshold)

        subject = f"ROIDMI EVE Plus - осталось около {pct:.0f}% воды"
        body = (
            f"Расчётный остаток воды в баке ROIDMI EVE Plus достиг порога {threshold}%.\n\n"
            f"Остаток: примерно {usage['remaining_ml']:.0f} мл ({pct:.0f}%).\n"
            f"Израсходовано с последнего заполнения: примерно {usage['used_ml']:.0f} мл.\n"
            f"Учтено влажных уборок: {usage['sessions']}.\n"
            f"Последнее заполнение: {last_fill}.\n\n"
            "Рекомендуется долить воду перед следующей влажной уборкой.\n"
            "Расчёт является программной оценкой, так как ROIDMI EVE Plus не измеряет фактический объём воды датчиком."
        )

        self._queue_notification(
            "ROIDMI: осталось мало воды",
            f"Расчётный остаток {pct:.0f}% ({usage['remaining_ml']:.0f} мл)."
        )
        self._queue_email_notification(subject, body)

    def _send_email_notification(self, subject, body, force=False):
        cfg = self.notify_config or {}
        if not cfg.get("email_enabled"):
            return False

        host = str(cfg.get("smtp_host") or "smtp.gmail.com").strip()
        try:
            port = int(cfg.get("smtp_port") or 587)
        except Exception:
            port = 587
        username = str(cfg.get("smtp_user") or "").strip()
        password = str(cfg.get("smtp_password") or "")
        recipient = str(cfg.get("email_to") or "").strip()

        if not host or not username or not password or not recipient:
            try:
                self.after(
                    0,
                    lambda: self.email_status_var.set(
                        "Email не отправлен: заполните SMTP user, App Password и получателя."
                    )
                )
            except Exception:
                pass
            return False

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = username
        msg["To"] = recipient
        msg.set_content(body)

        try:
            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
                    smtp.login(username, password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=20) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(username, password)
                    smtp.send_message(msg)
            try:
                self.after(
                    0,
                    lambda: self.email_status_var.set(
                        f"Email отправлен: {recipient}"
                    )
                )
            except Exception:
                pass
            return True
        except Exception as e:
            try:
                self.after(
                    0,
                    lambda err=str(e): self.email_status_var.set(
                        f"Ошибка Email: {err}"
                    )
                )
            except Exception:
                pass
            return False

    def _queue_email_notification(self, subject, body):
        if self._closing:
            return
        try:
            self.executor.submit(self._send_email_notification, subject, body)
        except Exception:
            pass

    def test_email_notification(self):
        self._save_notify_config()

        def task():
            return self._send_email_notification(
                "ROIDMI EVE Plus - тест уведомлений",
                "Тестовое письмо из ROIDMI EVE Plus Control.\n"
                "Если вы получили это сообщение, Email-уведомления настроены правильно.",
                force=True,
            )

        def done(ok):
            if ok:
                messagebox.showinfo("Email", "Тестовое письмо отправлено.")
            else:
                messagebox.showwarning(
                    "Email",
                    "Письмо не отправлено. Проверьте SMTP/App Password."
                )

        self.async_run(task, done, "Проверка Email...")

    def _water_forecast_text(self):
        areas = self._room_area_map()
        plan = self._adaptive_room_plan()

        # Future plan estimate.
        weekly_ml = 0.0
        for rid, p in plan.items():
            area = float(areas.get(rid, 0.0) or 0.0)
            level = int(p["profile"].get("water", 0) or 0)
            rate = float(
                WATER_FLOW_ML_PER_M2.get(
                    level,
                    WATER_FLOW_ML_PER_M2[max(WATER_FLOW_ML_PER_M2)]
                )
            )
            freq = int(p.get("frequency_per_week", 0) or 0)
            path = int(p["profile"].get("path_mode", 0) or 0)
            path_factor = 1.25 if path == 1 else (1.50 if path == 2 else 1.0)
            weekly_ml += area * rate * freq * path_factor

        daily_ml = weekly_ml / 7.0 if weekly_ml > 0 else 0.0
        nominal = float(TECH_SPECS["water_tank_nominal_ml"])
        conservative = float(TECH_SPECS["water_tank_conservative_ml"])

        usage = self._water_usage_since_fill()
        pct = float(usage["remaining_pct"])
        remaining = float(usage["remaining_ml"])
        last_fill = usage.get("last_fill")

        self.water_virtual_level_var.set(
            f"Виртуальный бак: ~{pct:.0f}% / {remaining:.0f} мл."
            if last_fill
            else "Виртуальный бак: нет отметки о заполнении."
        )

        try:
            threshold = int(self.water_low_threshold_var.get() or 30)
        except Exception:
            threshold = 30

        if daily_ml > 0:
            days_left = remaining / daily_ml
            future_line = (
                f"При текущем адаптивном графике ожидаемый средний расход "
                f"~{daily_ml:.0f} мл/день; расчётно воды осталось примерно на {days_left:.1f} дня."
            )
        else:
            future_line = "Будущий средний расход не рассчитан."

        source_note = (
            f"Учтено фактических/зафиксированных влажных уборок после заполнения: "
            f"{usage['sessions']}."
        )
        if usage["estimated_sessions"]:
            source_note += (
                f" Из них {usage['estimated_sessions']} восстановлены по общим счётчикам "
                f"и являются приблизительными."
            )

        return (
            f"Бак: {nominal:.0f} мл nominal / {conservative:.0f} мл conservative.\n"
            f"Расчёт ведётся НЕ по календарным дням, а по записанным влажным уборкам, "
            f"их площади, water level и path mode.\n"
            f"После последнего заполнения израсходовано примерно {usage['used_ml']:.0f} мл; "
            f"остаток ~{remaining:.0f} мл ({pct:.0f}%).\n"
            f"{source_note}\n"
            f"{future_line}\n"
            f"Email-порог: {threshold}%. При первом достижении/переходе ниже порога "
            f"письмо отправляется один раз до следующего заполнения бака."
        )


    def _record_maintenance(self, kind, notes="", value=None):
        with db_connect() as con:
            con.execute(
                "INSERT INTO maintenance(occurred_at, kind, value, notes) VALUES (?, ?, ?, ?)",
                (datetime.now().astimezone().isoformat(), kind, value, notes)
            )
        self._refresh_center_views_if_present()

    def add_maintenance_event(self, kind, label):
        note = simpledialog.askstring(
            "Журнал обслуживания",
            f"{label}\n\nКомментарий (необязательно):"
        )
        if note is None:
            return
        self._record_maintenance(kind, note)
        messagebox.showinfo("Журнал обслуживания", f"Записано: {label}")

    def _last_maintenance_time(self, kind):
        try:
            with db_connect() as con:
                row = con.execute(
                    "SELECT occurred_at FROM maintenance WHERE kind=? ORDER BY occurred_at DESC LIMIT 1",
                    (kind,)
                ).fetchone()
            return row["occurred_at"] if row else None
        except Exception:
            return None

    def _windows_toast(self, title, message):
        if os.name != "nt":
            return
        title_xml = xmlutils.escape(str(title))
        msg_xml = xmlutils.escape(str(message))
        toast_xml = (
            "<toast><visual><binding template='ToastGeneric'>"
            f"<text>{title_xml}</text><text>{msg_xml}</text>"
            "</binding></visual></toast>"
        )
        encoded = base64.b64encode(toast_xml.encode("utf-8")).decode("ascii")
        script = (
            "$ErrorActionPreference='SilentlyContinue';"
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;"
            "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null;"
            f"$s=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}'));"
            "$xml=New-Object Windows.Data.Xml.Dom.XmlDocument;"
            "$xml.LoadXml($s);"
            "$toast=[Windows.UI.Notifications.ToastNotification]::new($xml);"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('ROIDMI EVE Plus').Show($toast);"
        )
        try:
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        except Exception:
            pass


    def _queue_notification(self, title, message, severity="info", force=False):
        if self._closing:
            return
        try:
            self.executor.submit(self._send_notification, title, message, severity, force)
        except Exception:
            pass

    def _send_notification(self, title, message, severity="info", force=False):
        key = f"{title}|{message}"
        now = time.time()
        if not force and now - self._notification_cooldowns.get(key, 0) < 3600:
            return
        self._notification_cooldowns[key] = now

        cfg = self.notify_config or {}
        if cfg.get("windows", True):
            self._windows_toast(title, message)

        if cfg.get("telegram_enabled") and cfg.get("telegram_token") and cfg.get("telegram_chat_id"):
            try:
                requests.post(
                    f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage",
                    data={"chat_id": cfg["telegram_chat_id"], "text": f"{title}\n{message}"},
                    timeout=10,
                ).raise_for_status()
            except Exception:
                pass

        if cfg.get("ntfy_enabled") and cfg.get("ntfy_url"):
            try:
                requests.post(
                    cfg["ntfy_url"],
                    data=str(message).encode("utf-8"),
                    headers={"Title": str(title), "Priority": "4" if severity == "error" else "3"},
                    timeout=10,
                ).raise_for_status()
            except Exception:
                pass

    def test_notifications(self):
        self._save_notify_config()
        def task():
            self._send_notification(
                "ROIDMI EVE Plus",
                "Тестовое уведомление из программы.",
                force=True
            )
            return True
        self.async_run(task, lambda _: messagebox.showinfo("Уведомления", "Тест отправлен."), "Проверка уведомлений...")

    def _record_water_tank_event(
        self, event_type, source="status", mop_present=None,
        absence_sec=None, assumed_full=False, notes=""
    ):
        try:
            with db_connect() as con:
                con.execute(
                    """
                    INSERT INTO water_tank_events
                    (occurred_at, event_type, source, mop_present, absence_sec, assumed_full, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now().astimezone().isoformat(),
                        str(event_type),
                        str(source),
                        int(mop_present) if mop_present is not None else None,
                        float(absence_sec) if absence_sec is not None else None,
                        1 if assumed_full else 0,
                        str(notes or ""),
                    )
                )
        except Exception:
            pass

    def _last_assumed_water_fill(self):
        # Prefer explicit maintenance event because older versions already used it.
        last = self._last_maintenance_time("water_fill")
        try:
            with db_connect() as con:
                row = con.execute(
                    """
                    SELECT occurred_at
                    FROM water_tank_events
                    WHERE assumed_full=1
                    ORDER BY id DESC LIMIT 1
                    """
                ).fetchone()
            event_ts = row["occurred_at"] if row else None
        except Exception:
            event_ts = None

        if not last:
            return event_ts
        if not event_ts:
            return last
        try:
            return max(datetime.fromisoformat(last), datetime.fromisoformat(event_ts)).isoformat()
        except Exception:
            return last or event_ts

    def _mark_water_tank_full_automatic(self, absence_sec=None):
        note = (
            "Автоматически отмечено как заполнено после снятия и повторной установки бака. "
            "Программа предполагает, что пользователь долил воду во время снятия."
        )
        try:
            self._record_maintenance("water_fill", note)
        except Exception:
            pass
        self._record_water_tank_event(
            "reinserted",
            source="mop_present_transition",
            mop_present=1,
            absence_sec=absence_sec,
            assumed_full=True,
            notes=note,
        )
        self.water_virtual_level_var.set(
            "Виртуальный бак: 100% - автоматически отмечен после повторной установки."
        )
        self.email_status_var.set(
            "Новый цикл воды: порог Email 30% будет рассчитан заново."
        )
        self.water_tank_state_var.set(
            "Бак установлен. Повторная установка распознана как новый полный бак."
        )
        self._queue_notification(
            "ROIDMI: вода",
            "Бак снят и установлен заново. В приложении отмечено: бак заполнен водой."
        )
        self._refresh_center_views_if_present()

    def mark_water_tank_full_manual(self):
        self._record_maintenance(
            "water_fill",
            "Пользователь вручную отметил бак как заполненный."
        )
        self._record_water_tank_event(
            "manual_fill",
            source="user",
            mop_present=(self.last_data or {}).get("mop_present"),
            assumed_full=True,
            notes="Ручная отметка заполнения бака."
        )
        self.water_virtual_level_var.set(
            "Виртуальный бак: 100% - ручная отметка пользователя."
        )
        self.email_status_var.set(
            "Новый цикл воды: порог Email 30% будет рассчитан заново."
        )
        self.water_tank_state_var.set("Бак отмечен как заполненный.")
        self._refresh_center_views_if_present()

    def _handle_water_tank_presence(self, data):
        raw = data.get("mop_present")
        if raw is None:
            return
        try:
            present = int(raw)
        except Exception:
            return

        now = time.time()
        previous = self._last_mop_present

        if previous is None:
            self._last_mop_present = present
            self.water_tank_state_var.set(
                "Бак/моп установлен." if present == 1 else "Бак/моп снят."
            )
            return

        if previous == 1 and present == 0:
            self._tank_removed_at = now
            self._tank_removed_confirmed = True
            self.water_tank_state_var.set(
                "Бак снят. После повторной установки приложение может отметить его заполненным."
            )
            self._record_water_tank_event(
                "removed",
                source="mop_present_transition",
                mop_present=0,
                assumed_full=False,
                notes="Зафиксирован переход mop_present 1 -> 0."
            )

        elif previous == 0 and present == 1:
            absence_sec = (
                now - self._tank_removed_at
                if self._tank_removed_at is not None else None
            )
            min_absence = float(
                self.app_settings.get("water_tank_reinsert_min_absence_sec", 3) or 3
            )
            valid_cycle = (
                self._tank_removed_confirmed
                and absence_sec is not None
                and absence_sec >= min_absence
            )

            if valid_cycle and bool(self.auto_water_refill_var.get()):
                self._mark_water_tank_full_automatic(absence_sec)
            else:
                self._record_water_tank_event(
                    "reinserted",
                    source="mop_present_transition",
                    mop_present=1,
                    absence_sec=absence_sec,
                    assumed_full=False,
                    notes=(
                        "Повторная установка зафиксирована, но автоматическая отметка "
                        "полного бака не применена."
                    )
                )
                self.water_tank_state_var.set("Бак снова установлен.")

            self._tank_removed_at = None
            self._tank_removed_confirmed = False

        self._last_mop_present = present

    def _check_smart_alerts(self, data):
        try:
            err = int(data.get("error_code") or 0)
        except Exception:
            err = 0
        if err:
            self._queue_notification(
                "ROIDMI: ошибка",
                FAULT_RU.get(err, f"Код ошибки {err}"),
                severity="error"
            )

        for key, label in [
            ("filter_life_level", "Фильтр"),
            ("main_brush_life_level", "Основная щётка"),
            ("side_brushes_life_level", "Боковые щётки"),
            ("sensor_dirty_remaning_level", "Датчики"),
        ]:
            value = data.get(key)
            if isinstance(value, (int, float)) and value <= 10:
                self._queue_notification(
                    "ROIDMI: обслуживание",
                    f"{label}: осталось {value}%."
                )
        self._check_low_water_threshold()

    def _refresh_center_views_if_present(self):
        now = time.time()
        if now - getattr(self, "_last_center_refresh", 0.0) < 1.5:
            if self._center_refresh_job is None:
                self._center_refresh_job = self.after(1600, self._refresh_center_views_if_present)
            return
        self._last_center_refresh = now
        self._center_refresh_job = None
        try:
            self.adaptive_plan_var.set(self._adaptive_summary_text())
            self.service_forecast_var.set(self._consumable_forecast_text())
            self.water_forecast_var.set(self._water_forecast_text())
        except Exception:
            pass
        self._refresh_history_tree()
        self._refresh_maintenance_tree()
        self._refresh_map_history_tree()

    def _refresh_history_tree(self):
        tree = getattr(self, "history_tree", None)
        stats_tree = getattr(self, "room_stats_tree", None)
        if tree is not None:
            try:
                for item in tree.get_children():
                    tree.delete(item)
                with db_connect() as con:
                    rows = con.execute(
                        """
                        SELECT id, ended_at, source, rooms_json, area_m2, duration_sec, result
                        FROM cleaning_sessions
                        ORDER BY id DESC LIMIT 120
                        """
                    ).fetchall()
                for row in rows:
                    try:
                        rooms = json.loads(row["rooms_json"] or "[]")
                    except Exception:
                        rooms = []
                    names = ", ".join(ROOM_LABELS.get(int(r), str(r)) for r in rooms) if rooms else "не определены"
                    tree.insert(
                        "", "end",
                        values=(
                            row["ended_at"], row["source"], names,
                            f"{float(row['area_m2'] or 0):.1f}",
                            f"{float(row['duration_sec'] or 0)/60:.1f}",
                            row["result"],
                        )
                    )
            except Exception:
                pass

        if stats_tree is not None:
            try:
                for item in stats_tree.get_children():
                    stats_tree.delete(item)
                stats = self._history_room_stats()
                areas = self._room_area_map()
                for rid in range(1, 6):
                    s = stats[rid]
                    samples = s["samples"]
                    spm = s["sec_per_m2"]
                    est = None
                    if areas.get(rid):
                        est = areas[rid] * (spm if spm and samples >= 2 else SMART_OPTIMIZATION_STATS["historical_seconds_per_m2"]) / 60
                    stats_tree.insert(
                        "", "end",
                        values=(
                            rid, ROOM_LABELS[rid], samples,
                            f"{spm:.1f}" if spm else "-",
                            f"{est:.1f}" if est else "-"
                        )
                    )
            except Exception:
                pass

    def _refresh_maintenance_tree(self):
        tree = getattr(self, "maintenance_tree", None)
        if tree is None:
            return
        try:
            for item in tree.get_children():
                tree.delete(item)
            with db_connect() as con:
                rows = con.execute(
                    "SELECT occurred_at, kind, value, notes FROM maintenance ORDER BY id DESC LIMIT 100"
                ).fetchall()
            labels = {
                "water_fill": "Долив воды",
                "filter": "Фильтр",
                "main_brush": "Основная щётка",
                "side_brush": "Боковые щётки",
                "sensors": "Очистка датчиков",
                "station_bag": "Мешок станции",
                "mop": "Салфетка/моп",
                "custom": "Другое",
            }
            for row in rows:
                tree.insert("", "end", values=(
                    row["occurred_at"], labels.get(row["kind"], row["kind"]), row["notes"] or ""
                ))
        except Exception:
            pass

    def _archive_map_snapshot(self, raw_map, analysis=None):
        if not raw_map:
            return
        digest = hashlib.sha256(raw_map).hexdigest()
        try:
            with db_connect() as con:
                exists = con.execute(
                    "SELECT id FROM map_snapshots WHERE sha256=? LIMIT 1", (digest,)
                ).fetchone()
            if exists:
                return
        except Exception:
            pass

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = MAP_HISTORY_DIR / f"{stamp}_{digest[:10]}"
        raw_path = prefix.with_suffix(".gz")
        png_path = Path(str(prefix) + ".png")
        analysis_path = Path(str(prefix) + ".json")
        try:
            raw_path.write_bytes(raw_map)
            if LIVE_MAP_PNG_PATH.exists():
                shutil.copy2(LIVE_MAP_PNG_PATH, png_path)
            if analysis:
                atomic_write_json(analysis_path, analysis)
            map_id = None
            if isinstance(analysis, dict):
                map_id = analysis.get("map_id")
            with db_connect() as con:
                con.execute(
                    """
                    INSERT OR IGNORE INTO map_snapshots
                    (captured_at, map_id, sha256, raw_path, png_path, analysis_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now().astimezone().isoformat(),
                        str(map_id) if map_id is not None else None,
                        digest, str(raw_path), str(png_path), str(analysis_path)
                    )
                )
            self._prune_map_history()
        except Exception:
            pass

    def _prune_map_history(self):
        keep = int(self.app_settings.get("max_map_snapshots", 20) or 20)
        keep = max(5, min(100, keep))
        try:
            with db_connect() as con:
                rows = con.execute(
                    "SELECT id, raw_path, png_path, analysis_path FROM map_snapshots ORDER BY id DESC"
                ).fetchall()
                stale = rows[keep:]
                for row in stale:
                    for field in ("raw_path", "png_path", "analysis_path"):
                        try:
                            Path(row[field]).unlink(missing_ok=True)
                        except Exception:
                            pass
                    con.execute("DELETE FROM map_snapshots WHERE id=?", (row["id"],))
        except Exception:
            pass

    def _refresh_map_history_tree(self):
        tree = getattr(self, "map_history_tree", None)
        if tree is None:
            return
        try:
            for item in tree.get_children():
                tree.delete(item)
            with db_connect() as con:
                rows = con.execute(
                    "SELECT captured_at, map_id, sha256, png_path FROM map_snapshots ORDER BY id DESC LIMIT 50"
                ).fetchall()
            for row in rows:
                tree.insert("", "end", values=(
                    row["captured_at"], row["map_id"] or "-", row["sha256"][:12],
                    "PNG" if row["png_path"] and Path(row["png_path"]).exists() else "-"
                ))
        except Exception:
            pass

    def create_safe_persistent_backup(self):
        dst = filedialog.asksaveasfilename(
            title="Резервная копия пользовательских данных",
            defaultextension=".zip",
            initialfile=f"ROIDMI_user_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            filetypes=[("ZIP", "*.zip")]
        )
        if not dst:
            return

        safe_files = [
            USER_PROFILE_PATH, ROOM_PROFILES_PATH, APP_SETTINGS_PATH,
            LIVE_MAP_RAW_PATH, LIVE_MAP_PNG_PATH, LIVE_MAP_ANALYSIS_PATH,
            LIVE_MAP_REPORT_PATH, LAST_MAP_INFO_PATH, LAST_ROOMS_PATH,
            FIRMWARE_REPORT_PATH
        ]
        with tempfile.TemporaryDirectory() as td:
            db_copy = Path(td) / "history.sqlite3"
            if HISTORY_DB_PATH.exists():
                with db_connect() as source_con:
                    dest_con = sqlite3.connect(str(db_copy))
                    try:
                        source_con.backup(dest_con)
                    finally:
                        dest_con.close()

            with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
                for p in safe_files:
                    if p.exists() and p.is_file():
                        z.write(p, arcname=f"data/{p.name}")
                if db_copy.exists():
                    z.write(db_copy, arcname="data/history.sqlite3")
                for folder, arc in [
                    (VOICEPACKS_DIR, "voicepacks"),
                    (MAP_HISTORY_DIR, "map_history"),
                ]:
                    for p in folder.rglob("*"):
                        if p.is_file():
                            z.write(p, arcname=f"{arc}/{p.relative_to(folder)}")
                z.writestr(
                    "README.txt",
                    "Безопасная резервная копия. Xiaomi/robot/robot tokens, CLOUD_SESSION и PRIVATE_NOTIFY_CONFIG не включены."
                )
        self.center_status_var.set(f"Backup создан: {dst}")


    def restore_safe_persistent_backup(self):
        src = filedialog.askopenfilename(
            title="Восстановить резервную копию",
            filetypes=[("ZIP", "*.zip")]
        )
        if not src:
            return
        if not messagebox.askyesno(
            "Восстановление",
            "Текущие пользовательские профили, история и карта могут быть заменены. Продолжить?"
        ):
            return
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(src, "r") as z:
                z.extractall(td)
            td = Path(td)
            data_dir = td / "data"
            if data_dir.exists():
                for p in data_dir.iterdir():
                    if p.is_file():
                        target = SHARED_DATA_DIR / p.name
                        shutil.copy2(p, target)
            for folder_name, target_dir in [("voicepacks", VOICEPACKS_DIR), ("map_history", MAP_HISTORY_DIR)]:
                source_dir = td / folder_name
                if source_dir.exists():
                    for p in source_dir.rglob("*"):
                        if p.is_file():
                            rel = p.relative_to(source_dir)
                            target = target_dir / rel
                            target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(p, target)
        messagebox.showinfo(
            "Восстановление",
            "Данные восстановлены. Перезапустите программу для полной синхронизации интерфейса."
        )

    def create_diagnostics_zip(self):
        dst = filedialog.asksaveasfilename(
            title="Сохранить диагностический ZIP",
            defaultextension=".zip",
            initialfile=f"ROIDMI_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            filetypes=[("ZIP", "*.zip")]
        )
        if not dst:
            return
        summary = {
            "app": APP_TITLE,
            "python": sys.version,
            "platform": platform.platform(),
            "screen": self.ui_screen_var.get(),
            "model": MODEL,
            "status": self.last_data,
            "map_id": self.current_map_id,
            "rooms": self.rooms_data,
            "history_db_bytes": HISTORY_DB_PATH.stat().st_size if HISTORY_DB_PATH.exists() else 0,
            "privacy": "tokens/passwords/cloud session excluded",
        }
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("diagnostic_summary.json", json.dumps(summary, ensure_ascii=False, indent=2, default=str))
            for p in [
                LOG_DIR / "cloud_debug.log",
                ROOT / "error.log",
                ROOT / "CRASH_REPORT.txt",
                ROOT / "live_map_error.log",
                ROOT / "GITHUB_RESEARCH.md",
                ROOT / "SOURCE_MATRIX.json",
            ]:
                if p.exists() and p.is_file():
                    z.write(p, arcname=p.name)
        self.center_status_var.set(f"Диагностический ZIP создан: {dst}")

    @staticmethod
    def _version_tuple(value):
        nums = re.findall(r"\d+", str(value or ""))
        return tuple(int(x) for x in nums[:4]) or (0,)

    def _fetch_update_manifest(self):
        url = self.update_manifest_url_var.get().strip() or GITHUB_MANIFEST_URL
        r = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": f"ROIDMI-EVE-Plus-Control/{CURRENT_VERSION}"}
        )
        r.raise_for_status()
        manifest = r.json()
        if not isinstance(manifest, dict):
            raise RuntimeError("Манифест обновления имеет неверный формат.")
        version = str(manifest.get("version") or "").strip()
        download_url = str(manifest.get("url") or "").strip()
        sha256 = str(manifest.get("sha256") or "").strip().lower()
        if not version or not re.fullmatch(r"https?://.+", download_url):
            raise RuntimeError("В манифесте отсутствуют version/url.")
        if sha256 and not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise RuntimeError("В манифесте некорректный SHA256.")
        return manifest

    def check_for_updates(self, silent=False):
        self._save_app_settings()

        def task():
            return self._fetch_update_manifest()

        def done(manifest):
            self.github_latest_manifest = manifest
            version = str(manifest.get("version") or "")
            notes = str(manifest.get("notes") or "").strip()
            current_v = self._version_tuple(CURRENT_VERSION)
            latest_v = self._version_tuple(version)

            if latest_v <= current_v:
                self.update_status_var.set(
                    f"GitHub: установлена актуальная версия {CURRENT_VERSION}."
                )
                return

            self.update_status_var.set(f"GitHub: доступна версия {version}.")
            self._queue_notification(
                "ROIDMI: обновление программы",
                f"На GitHub доступна версия {version}."
            )

            if silent:
                return

            msg = f"На GitHub доступна версия {version}."
            if notes:
                msg += f"\n\n{notes[:900]}"
            msg += "\n\nСкачать, проверить SHA256 и установить?"
            if messagebox.askyesno("Обновление программы", msg):
                self._download_update_zip(
                    version,
                    manifest.get("url"),
                    manifest.get("sha256"),
                    offer_install=True,
                )

        if silent:
            if self.github_update_busy:
                return
            self.github_update_busy = True
            future = self.executor.submit(task)

            def finish(fut):
                try:
                    result = fut.result()
                    err = None
                except Exception as exc:
                    result = None
                    err = str(exc)

                def deliver():
                    self.github_update_busy = False
                    if result:
                        done(result)
                    elif err:
                        self.update_status_var.set(f"GitHub update check: {err}")
                try:
                    self.after(0, deliver)
                except Exception:
                    pass

            future.add_done_callback(finish)
        else:
            self.async_run(task, done, "Проверка обновлений GitHub...")

    def _maybe_auto_program_update(self):
        if self._closing or not bool(self.github_auto_check_var.get()):
            return
        self.check_for_updates(silent=True)
        try:
            hours = float(self.app_settings.get("github_check_interval_hours", 12) or 12)
        except Exception:
            hours = 12
        hours = max(1, min(168, hours))
        self.after(int(hours * 3600 * 1000), self._maybe_auto_program_update)


    def _download_update_zip(
        self, version, url, expected_sha256=None, offer_install=True
    ):
        def task():
            path = UPDATES_DIR / f"ROIDMI_update_{version}.zip"
            tmp = path.with_suffix(".zip.part")
            h = hashlib.sha256()
            total = 0
            limit = 500 * 1024 * 1024
            with requests.get(
                url,
                stream=True,
                timeout=60,
                headers={"User-Agent": f"ROIDMI-EVE-Plus-Control/{CURRENT_VERSION}"}
            ) as r:
                r.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > limit:
                            raise RuntimeError(
                                "Обновление больше 500 MiB; загрузка остановлена."
                            )
                        h.update(chunk)
                        f.write(chunk)

            digest = h.hexdigest()
            if expected_sha256 and digest.lower() != str(expected_sha256).lower():
                tmp.unlink(missing_ok=True)
                raise RuntimeError(
                    "SHA256 скачанного обновления не совпадает с GitHub-манифестом."
                )

            tmp.replace(path)
            return {"path": path, "sha256": digest, "size": total}

        def done(result):
            path = result["path"]
            self.update_status_var.set(
                f"GitHub: версия {version} скачана и SHA256 проверен."
            )
            if offer_install and messagebox.askyesno(
                "Установить обновление",
                f"Версия {version} скачана и проверена.\n\n"
                "Установить её сейчас? Текущая программа закроется, "
                "новая версия будет распакована в соседнюю папку. "
                "Пользовательские данные останутся в LocalAppData."
            ):
                self._launch_external_update_installer(version, path)

        self.async_run(task, done, f"Скачивание GitHub версии {version}...")

    @staticmethod
    def _ps_quote(value):
        return str(value).replace("'", "''")

    def _launch_external_update_installer(self, version, archive_path):
        archive_path = Path(archive_path)
        if not archive_path.exists():
            messagebox.showerror("Обновление", "ZIP обновления не найден.")
            return

        safe_version = re.sub(r"[^0-9A-Za-z._-]+", "_", str(version))
        target = ROOT.parent / f"ROIDMI_EVE_Plus_Control_Windows_v{safe_version}_AUTO"
        script = UPDATES_DIR / f"apply_update_{safe_version}.ps1"
        pid = os.getpid()

        ps = (
            '$ErrorActionPreference = "Stop"\n'
            f'$pidToWait = {pid}\n'
            f"$archive = '{self._ps_quote(archive_path)}'\n"
            f"$target = '{self._ps_quote(target)}'\n"
            'while (Get-Process -Id $pidToWait -ErrorAction SilentlyContinue) {\n'
            '    Start-Sleep -Milliseconds 500\n'
            '}\n'
            'if (Test-Path $target) { Remove-Item -Recurse -Force $target }\n'
            'New-Item -ItemType Directory -Force -Path $target | Out-Null\n'
            'Expand-Archive -LiteralPath $archive -DestinationPath $target -Force\n'
            '$start = Join-Path $target "START_ONE_CLICK.cmd"\n'
            'if (-not (Test-Path $start)) {\n'
            '    $dirs = @(Get-ChildItem -LiteralPath $target -Directory)\n'
            '    if ($dirs.Count -eq 1) {\n'
            '        $candidate = Join-Path $dirs[0].FullName "START_ONE_CLICK.cmd"\n'
            '        if (Test-Path $candidate) { $start = $candidate }\n'
            '    }\n'
            '}\n'
            'if (-not (Test-Path $start)) { exit 2 }\n'
            'Start-Process -FilePath $start -WorkingDirectory (Split-Path $start)\n'
        )
        script.write_text(ps, encoding="utf-8-sig")

        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(script),
            ],
            cwd=str(UPDATES_DIR),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.minimize_to_tray_var.set(False)
        self._closing = True
        self.after(250, self._on_close)


    def _create_tray_image(self):
        if Image is None:
            return None
        img = Image.new("RGBA", (64, 64), (15, 23, 42, 255))
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.ellipse((10, 10, 54, 54), fill=(59, 130, 246, 255), outline=(255,255,255,255), width=3)
            draw.ellipse((26, 26, 38, 38), fill=(255,255,255,255))
        except Exception:
            pass
        return img

    def _show_from_tray(self):
        self.deiconify()
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.lift()
        self.focus_force()

    def _start_tray(self):
        if pystray is None or self._tray_icon is not None:
            return
        image = self._create_tray_image()
        if image is None:
            return

        def show(icon=None, item=None):
            self.after(0, self._show_from_tray)

        def start_clean(icon=None, item=None):
            self.after(0, lambda: self.run_action("start"))

        def go_home(icon=None, item=None):
            self.after(0, lambda: self.run_action("home"))

        def exit_app(icon=None, item=None):
            def do_exit():
                self.minimize_to_tray_var.set(False)
                self._closing = True
                try:
                    icon.stop()
                except Exception:
                    pass
                self._tray_icon = None
                self._on_close()
            self.after(0, do_exit)

        menu = pystray.Menu(
            pystray.MenuItem("Открыть", show, default=True),
            pystray.MenuItem("Начать уборку", start_clean),
            pystray.MenuItem("На базу", go_home),
            pystray.MenuItem("Выход", exit_app),
        )
        self._tray_icon = pystray.Icon("ROIDMI_EVE_Plus", image, "ROIDMI EVE Plus", menu)
        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    def _on_close(self):
        if not self._closing and bool(self.minimize_to_tray_var.get()) and pystray is not None:
            self.withdraw()
            self._start_tray()
            self.center_status_var.set("Программа свёрнута в системный трей.")
            return
        self._closing = True
        if self.monitor_job:
            try:
                self.after_cancel(self.monitor_job)
            except Exception:
                pass
        try:
            if self._tray_icon is not None:
                self._tray_icon.stop()
        except Exception:
            pass
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self.destroy()

    def _start_background_services(self):
        self.performance_status_var.set(
            "Performance: ThreadPool x4 | SQLite WAL | Map worker | adaptive monitor 20/120s"
        )
        self._ensure_status_monitor()
        self._refresh_center_views_if_present()
        self.after(5000, self._maybe_auto_firmware_check)
        self.after(8000, self._maybe_auto_program_update)

    def _ensure_status_monitor(self):
        if self._closing:
            return
        if self.monitor_job:
            try:
                self.after_cancel(self.monitor_job)
            except Exception:
                pass
        state = (self.last_data or {}).get("state")
        delay_ms = 20000 if state == 4 else 120000
        self.monitor_job = self.after(delay_ms, self._status_monitor_tick)

    def _status_monitor_tick(self):
        self.monitor_job = None
        if self._closing:
            return
        if self.device is None or self.busy or self.monitor_inflight:
            self._ensure_status_monitor()
            return
        self.monitor_inflight = True

        def task():
            return self.device.status().data

        future = self.executor.submit(task)

        def finished(fut):
            try:
                result = fut.result()
            except Exception:
                result = None
            def deliver():
                self.monitor_inflight = False
                if result:
                    self.on_status(result)
                else:
                    self._ensure_status_monitor()
            try:
                self.after(0, deliver)
            except Exception:
                pass

        future.add_done_callback(finished)

    def _record_cleaning_session(
        self, source, rooms, area_m2, duration_sec,
        fan=None, water=None, sweep_type=None, path_mode=None,
        result="completed", error_code=0, notes=None,
        started_at=None, ended_at=None
    ):
        ended_at = ended_at or datetime.now().astimezone().isoformat()
        if started_at is None and duration_sec:
            try:
                started_at = datetime.fromtimestamp(
                    datetime.now().timestamp() - float(duration_sec)
                ).astimezone().isoformat()
            except Exception:
                started_at = None
        with db_connect() as con:
            con.execute(
                """
                INSERT INTO cleaning_sessions
                (started_at, ended_at, source, rooms_json, area_m2, duration_sec,
                 fan, water, sweep_type, path_mode, result, error_code, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at, ended_at, source,
                    json.dumps(list(rooms or []), ensure_ascii=False),
                    area_m2, duration_sec, fan, water, sweep_type, path_mode,
                    result, error_code, notes
                )
            )
        try:
            self._check_low_water_threshold()
        except Exception:
            pass

    def _record_status_snapshot(self, data):
        if not data:
            return
        now = time.time()
        sig = (
            data.get("state"), data.get("error_code"), data.get("battery_level"),
            data.get("clean_counts"), data.get("total_clean_areas"),
            data.get("total_clean_time_sec")
        )
        meaningful = sig != self._last_status_signature
        if meaningful or now - self._last_status_db_write >= 300:
            try:
                with db_connect() as con:
                    con.execute(
                        """
                        INSERT INTO status_snapshots
                        (captured_at, state, error_code, battery, clean_counts, total_area, total_time_sec)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            datetime.now().astimezone().isoformat(),
                            data.get("state"), data.get("error_code"), data.get("battery_level"),
                            data.get("clean_counts"), data.get("total_clean_areas"),
                            data.get("total_clean_time_sec")
                        )
                    )
                self._last_status_db_write = now
                self._last_status_signature = sig
            except Exception:
                pass

        current = {
            "clean_counts": data.get("clean_counts"),
            "total_clean_areas": data.get("total_clean_areas"),
            "total_clean_time_sec": data.get("total_clean_time_sec"),
            "state": data.get("state"),
        }
        prev = self._last_counter_snapshot
        if prev is not None:
            try:
                dc = int(current["clean_counts"] or 0) - int(prev.get("clean_counts") or 0)
                da = float(current["total_clean_areas"] or 0) - float(prev.get("total_clean_areas") or 0)
                dt = float(current["total_clean_time_sec"] or 0) - float(prev.get("total_clean_time_sec") or 0)
            except Exception:
                dc, da, dt = 0, 0, 0

            # Global aggregate fallback for cleanings not launched by this app.
            if dc > 0 and (da > 0 or dt > 0):
                note = None
                if dc > 1:
                    note = f"Обнаружено {dc} уборок между чтениями состояния; запись агрегирована."
                try:
                    self._record_cleaning_session(
                        "detected",
                        [],
                        max(0.0, da),
                        max(0.0, dt),
                        fan=data.get("fanspeed_mode"),
                        water=data.get("water_level"),
                        sweep_type=data.get("sweep_type"),
                        path_mode=data.get("path_mode"),
                        error_code=data.get("error_code") or 0,
                        notes=note,
                    )
                except Exception:
                    pass

        self._last_counter_snapshot = current
        try:
            atomic_write_json(RUNTIME_STATE_PATH, current)
        except Exception:
            pass

        # Finalize a manually started all-room session on transition out of cleaning.
        if self._active_manual_session and prev:
            if prev.get("state") == 4 and current.get("state") != 4:
                sess = self._active_manual_session
                self._active_manual_session = None
                try:
                    duration = max(
                        0.0,
                        float(current.get("total_clean_time_sec") or 0)
                        - float(sess.get("total_clean_time_sec") or 0)
                    )
                    area = max(
                        0.0,
                        float(current.get("total_clean_areas") or 0)
                        - float(sess.get("total_clean_areas") or 0)
                    )
                    self._record_cleaning_session(
                        sess.get("source", "manual"),
                        sess.get("rooms", []),
                        area, duration,
                        fan=sess.get("fan"), water=sess.get("water"),
                        sweep_type=sess.get("sweep_type"), path_mode=sess.get("path_mode"),
                        error_code=data.get("error_code") or 0,
                        started_at=sess.get("started_at"),
                    )
                except Exception:
                    pass

    def _history_room_stats(self):
        stats = {rid: {"samples": 0, "duration_sec": 0.0, "area_m2": 0.0} for rid in range(1, 6)}
        try:
            with db_connect() as con:
                rows = con.execute(
                    """
                    SELECT rooms_json, duration_sec, area_m2
                    FROM cleaning_sessions
                    WHERE result='completed'
                    ORDER BY id DESC
                    LIMIT 500
                    """
                ).fetchall()
            for row in rows:
                try:
                    rooms = json.loads(row["rooms_json"] or "[]")
                except Exception:
                    rooms = []
                if len(rooms) != 1:
                    continue
                rid = int(rooms[0])
                if rid not in stats:
                    continue
                duration = float(row["duration_sec"] or 0)
                area = float(row["area_m2"] or 0)
                if duration <= 0:
                    continue
                stats[rid]["samples"] += 1
                stats[rid]["duration_sec"] += duration
                stats[rid]["area_m2"] += max(0.0, area)
        except Exception:
            pass

        for rid, s in stats.items():
            samples = s["samples"]
            s["avg_duration_sec"] = (s["duration_sec"] / samples) if samples else None
            s["sec_per_m2"] = (
                s["duration_sec"] / s["area_m2"]
                if s["area_m2"] > 0 else None
            )
        return stats

    def _daily_cleaning_minutes(self):
        try:
            cutoff = datetime.fromtimestamp(
                time.time() - 30 * 86400
            ).astimezone().isoformat()
            with db_connect() as con:
                row = con.execute(
                    """
                    SELECT SUM(duration_sec) AS seconds
                    FROM cleaning_sessions
                    WHERE ended_at >= ? AND result='completed'
                    """,
                    (cutoff,)
                ).fetchone()
            seconds = float(row["seconds"] or 0) if row else 0.0
            if seconds > 0:
                return max(1.0, seconds / 60.0 / 30.0)
        except Exception:
            pass
        # Fallback to current optimized weekly load.
        return max(
            1.0,
            SMART_OPTIMIZATION_STATS["optimized_weekly_nominal_area_m2"]
            * SMART_OPTIMIZATION_STATS["historical_seconds_per_m2"] / 60.0 / 7.0
        )

    def on_status(self, data):
        self.last_data = dict(data or {})
        self._handle_water_tank_presence(self.last_data)
        self._record_status_snapshot(self.last_data)
        self.suspend_live_autosave = True
        try:
            self._populate_settings(data)
            self._populate_schedule(data.get("timing"))
            self._populate_dnd(data.get("forbid_mode"))
            self._show_status(data)
            self._show_raw(data)
            self._refresh_dashboard()
            self._refresh_center_views_if_present()
            self._check_smart_alerts(data)
        finally:
            self.suspend_live_autosave = False
        self.statusbar_var.set("Состояние прочитано. Adaptive Monitor включён.")
        self._ensure_status_monitor()

    def _show_status(self, d):
        state_names = {1:"сон",2:"ожидание",3:"пауза",4:"уборка",5:"возврат на базу",
                       6:"зарядка",7:"ошибка",8:"ручное управление",9:"заряжен",10:"выключен",11:"пауза возврата"}
        lines = [
            f"Модель: {MODEL}",
            f"Состояние: {state_names.get(d.get('state'), d.get('state'))}",
            f"Заряд: {d.get('battery_level')} %",
            f"Код ошибки: {d.get('error_code')} - {FAULT_RU.get(d.get('error_code'), 'Неизвестная ошибка')}",
            f"Мощность: {d.get('fanspeed_mode')}",
            f"Тип уборки: {d.get('sweep_type')}",
            f"Подача воды: {d.get('water_level')}",
            f"Маршрут: {d.get('path_mode')}",
            f"Ковровый boost: {d.get('auto_boost')}",
            f"Двойная уборка: {d.get('double_clean')}",
            f"Самоочистка станции: каждые {d.get('work_station_freq')} уборок",
            f"Громкость: {d.get('volume')} %",
            f"Mute: {d.get('mute')}",
            f"Текущий голос: {d.get('current_audio')}",
            "",
            f"Текущая уборка - площадь: {d.get('clean_area')}, время: {d.get('clean_time_sec')} сек.",
            f"Всего уборок: {d.get('clean_counts')}",
            f"Всего площадь: {d.get('total_clean_areas')}",
            f"Всего время: {d.get('total_clean_time_sec')} сек.",
            "",
            "Расписание:",
            str(d.get("timing")),
            "",
            "Комнаты: 1=Кухня, 2=Спальня, 3=Коридор, 4=Зал, 5=Ванная",
            "Оптимальный порядок полной уборки: 2 → 4 → 1 → 3 → 5",
            "",
            "Не беспокоить:",
            str(d.get("forbid_mode")),
        ]
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0","end")
        self.status_text.insert("1.0","\n".join(lines))
        self.status_text.configure(state="disabled")

    def _show_raw(self, d):
        raw = {
            "model": MODEL,
            "read_at": datetime.now().astimezone().isoformat(),
            "data": d,
        }
        self.raw_text.delete("1.0","end")
        self.raw_text.insert("1.0", json.dumps(raw, ensure_ascii=False, indent=2, default=str))

    def _populate_settings(self, d):
        if d.get("fanspeed_mode") is not None: self.fan_var.set(reverse_lookup(FAN,d["fanspeed_mode"]))
        if d.get("sweep_type") is not None: self.sweep_var.set(reverse_lookup(SWEEP_TYPE,d["sweep_type"]))
        if d.get("water_level") is not None: self.water_var.set(reverse_lookup(WATER,d["water_level"]))
        if d.get("path_mode") is not None: self.path_var.set(reverse_lookup(PATH_MODE,d["path_mode"]))
        if d.get("work_station_freq") is not None: self.station_freq_var.set(reverse_lookup(STATION_FREQ,d["work_station_freq"]))
        if d.get("volume") is not None: self.volume_var.set(int(d["volume"]))
        if d.get("current_audio") is not None:
            self.voice_current_var.set(str(d.get("current_audio")))
            self.voice_status_var.set(f"Текущий голос робота: {d.get('current_audio')}")
        for key,var in [
            ("auto_boost",self.auto_boost_var),("double_clean",self.double_clean_var),
            ("led_switch",self.led_var),("lidar_collision",self.lidar_var),
            ("station_led",self.station_led_var),("station_key",self.station_key_var),
            ("mute",self.mute_var)
        ]:
            if d.get(key) is not None: var.set(bool(d[key]))

    def backup_data(self, data=None, reason="manual"):
        if data is None:
            data = self.last_data
        payload = {
            "model": MODEL,
            "created_at": datetime.now().astimezone().isoformat(),
            "reason": reason,
            "ip": self.ip_var.get().strip(),
            "token": "NOT_SAVED",
            "data": data,
        }
        name = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{reason}.json"
        path = BACKUP_DIR / name
        path.write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        return path

    def backup_now(self):
        if not self.last_data:
            self.read_status()
            return
        p = self.backup_data(reason="manual")
        messagebox.showinfo("Резервная копия", f"Сохранено:\n{p}\n\nToken в резервную копию не записывается.")

    def _optimized_timing_raw(self):
        return json.dumps(
            OPTIMIZED_TIMING, ensure_ascii=False, separators=(",",":")
        )

    def _apply_optimized_properties_to_ui(self):
        self.fan_var.set(reverse_lookup(FAN, OPTIMIZED_PROPERTIES["fanspeed_mode"]))
        self.sweep_var.set(reverse_lookup(SWEEP_TYPE, OPTIMIZED_PROPERTIES["sweep_type"]))
        self.water_var.set(reverse_lookup(WATER, OPTIMIZED_PROPERTIES["water_level"]))
        self.path_var.set(reverse_lookup(PATH_MODE, OPTIMIZED_PROPERTIES["path_mode"]))
        self.station_freq_var.set(reverse_lookup(STATION_FREQ, OPTIMIZED_PROPERTIES["work_station_freq"]))
        self.volume_var.set(int(OPTIMIZED_PROPERTIES["volume"]))
        self.auto_boost_var.set(bool(OPTIMIZED_PROPERTIES["auto_boost"]))
        self.double_clean_var.set(bool(OPTIMIZED_PROPERTIES["double_clean"]))
        self.led_var.set(bool(OPTIMIZED_PROPERTIES["led_switch"]))
        self.lidar_var.set(bool(OPTIMIZED_PROPERTIES["lidar_collision"]))
        self.station_led_var.set(bool(OPTIMIZED_PROPERTIES["station_led"]))
        self.station_key_var.set(bool(OPTIMIZED_PROPERTIES["station_key"]))
        self.mute_var.set(bool(OPTIMIZED_PROPERTIES["mute"]))

    def _normalize_json_obj(self, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

    def _same_timing(self, current):
        return self._normalize_json_obj(current) == OPTIMIZED_TIMING

    def _same_dnd(self, current):
        obj = self._normalize_json_obj(current)
        if not isinstance(obj, dict):
            return False
        arr = obj.get("time")
        return isinstance(arr, list) and len(arr) >= 3 and [
            int(arr[0]), int(arr[1]), int(arr[2])
        ] == [79200, 28800, 1]

    def _write_last_applied(self, status, results=None, room_order=None):
        payload = {
            "model": MODEL,
            "saved_at": datetime.now().astimezone().isoformat(),
            "properties": {
                k: status.get(k) for k in OPTIMIZED_PROPERTIES.keys()
            },
            "timing": self._normalize_json_obj(status.get("timing")),
            "forbid_mode": self._normalize_json_obj(status.get("forbid_mode")),
            "room_order": room_order,
            "results": results or {},
        }
        LAST_APPLIED_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )

    def auto_apply_saved_profile_silent(self):
        """Restore exactly what the user last saved, not hard-coded defaults."""
        if self.busy or self.auto_apply_in_progress:
            return
        self.auto_apply_in_progress = True
        profile = self._load_user_profile()

        wanted_props = dict(profile.get("properties") or {})
        wanted_timing = profile.get("timing")
        wanted_dnd = profile.get("forbid_mode")

        def task():
            d = self.ensure_device()
            before = d.status().data
            changes = {}

            for key, wanted in wanted_props.items():
                if key not in OPTIMIZED_PROPERTIES:
                    continue
                current = before.get(key)
                if not self._values_equal(current, wanted):
                    changes[key] = (current, wanted)

            current_timing = self._normalize_json_obj(before.get("timing"))
            if isinstance(wanted_timing, dict) and current_timing != wanted_timing:
                changes["timing"] = (current_timing, wanted_timing)

            current_dnd = self._normalize_json_obj(before.get("forbid_mode"))
            if isinstance(wanted_dnd, dict) and current_dnd != wanted_dnd:
                changes["forbid_mode"] = (current_dnd, wanted_dnd)

            results = {"changed": sorted(changes.keys())}

            if changes:
                results["backup"] = str(
                    self.backup_data(before, "before_restore_user_profile")
                )

                for key, pair in changes.items():
                    if key in ("timing", "forbid_mode"):
                        continue
                    try:
                        results[key] = d.set_property(key, pair[1])
                    except Exception as e:
                        results[key] = f"ERROR: {e}"

                if "timing" in changes:
                    try:
                        raw = json.dumps(
                            wanted_timing,
                            ensure_ascii=False,
                            separators=(",",":")
                        )
                        results["timing"] = d.set_timing(raw)
                    except Exception as e:
                        results["timing"] = f"ERROR: {e}"

                if "forbid_mode" in changes:
                    try:
                        arr = wanted_dnd.get("time") if isinstance(wanted_dnd, dict) else None
                        if isinstance(arr, list) and len(arr) >= 3 and int(arr[2]) == 1:
                            sh, rem = divmod(int(arr[0]), 3600)
                            sm = rem // 60
                            eh, rem = divmod(int(arr[1]), 3600)
                            em = rem // 60
                            results["forbid_mode"] = d.set_dnd(
                                sh, sm, eh, em
                            )
                        else:
                            results["forbid_mode"] = d.disable_dnd()
                    except Exception as e:
                        results["forbid_mode"] = f"ERROR: {e}"

            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.auto_apply_in_progress = False
            self.auto_apply_global_done = True
            self.on_status(after)
            self._write_last_applied(after, results=results)

            with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " RESTORE_USER_PROFILE " +
                    json.dumps(results, ensure_ascii=False, default=str) + "\n"
                )

            errors = {
                k:v for k,v in results.items()
                if isinstance(v, str) and v.startswith("ERROR:")
            }
            if errors:
                self.statusbar_var.set(
                    "Persistent AutoSave: профиль восстановлен частично."
                )
            elif results.get("changed"):
                self.statusbar_var.set(
                    "Persistent AutoSave: сохранённый профиль восстановлен."
                )
            else:
                self.statusbar_var.set(
                    "Persistent AutoSave: робот уже соответствует сохранённому профилю."
                )

            if self.auto_config.get("auto_fetch_rooms", False):
                self.after(250, self.fetch_rooms)

        self.async_run(
            task, done,
            "Persistent AutoSave: восстанавливаю сохранённый профиль..."
        )

    def auto_apply_optimized_global_silent(self):
        """Immediately enforce changed global settings; skip already-correct values."""
        if self.busy or self.auto_apply_in_progress:
            return
        self.auto_apply_in_progress = True

        def task():
            d = self.ensure_device()
            before = d.status().data
            changes = {}

            for key, wanted in OPTIMIZED_PROPERTIES.items():
                current = before.get(key)
                # bool/int values are equivalent for MIoT flags.
                same = (
                    bool(current) == bool(wanted)
                    if isinstance(wanted, bool)
                    else current == wanted
                )
                if not same:
                    changes[key] = (current, wanted)

            if not self._same_timing(before.get("timing")):
                changes["timing"] = (before.get("timing"), OPTIMIZED_TIMING)

            if not self._same_dnd(before.get("forbid_mode")):
                changes["forbid_mode"] = (before.get("forbid_mode"), "22:00-08:00")

            results = {"changed": sorted(changes.keys())}

            if changes:
                backup = self.backup_data(before, "before_auto_apply")
                results["backup"] = str(backup)

                for key, wanted in OPTIMIZED_PROPERTIES.items():
                    if key not in changes:
                        continue
                    try:
                        results[key] = d.set_property(key, wanted)
                    except Exception as e:
                        results[key] = f"ERROR: {e}"

                if "timing" in changes:
                    try:
                        results["timing"] = d.set_timing(self._optimized_timing_raw())
                    except Exception as e:
                        results["timing"] = f"ERROR: {e}"

                if "forbid_mode" in changes:
                    try:
                        results["forbid_mode"] = d.set_dnd(22, 0, 8, 0)
                    except Exception as e:
                        results["forbid_mode"] = f"ERROR: {e}"

            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.auto_apply_in_progress = False
            self.auto_apply_global_done = True
            self.on_status(after)
            self._apply_optimized_properties_to_ui()
            self._write_last_applied(after, results=results)

            errors = {
                k:v for k,v in results.items()
                if isinstance(v, str) and v.startswith("ERROR:")
            }
            changed = results.get("changed") or []
            if errors:
                self.statusbar_var.set(
                    "Автооптимизация: часть параметров не записалась. См. optimization.log."
                )
            elif changed:
                self.statusbar_var.set(
                    "Автооптимизация: настройки изменены и сохранены в пылесосе."
                )
            else:
                self.statusbar_var.set(
                    "Автооптимизация: настройки уже оптимальны, запись не требовалась."
                )

            with (ROOT / "optimization.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " AUTO_GLOBAL " +
                    json.dumps(results, ensure_ascii=False, default=str) + "\n"
                )

            if self.auto_config.get("auto_fetch_rooms", False):
                self.after(250, self.fetch_rooms)

        def failed_reset():
            self.auto_apply_in_progress = False

        # async_run itself handles UI errors. The flag will normally reset in done.
        self.async_run(task, done, "Автооптимизация: проверяю и сохраняю настройки...")

    def _current_auto_area_order(self):
        order = []
        for obj in self.auto_area_raw or []:
            if isinstance(obj, dict) and "id" in obj:
                try:
                    order.append(int(obj["id"]))
                except Exception:
                    pass
        return order

    def auto_apply_room_order_silent(self):
        """Load the saved room order into UI without sending unsupported area-order."""
        if self.auto_apply_order_done:
            return

        wanted_order = self._saved_profile_room_order()
        self.auto_apply_order_done = True

        self.suspend_live_autosave = True
        try:
            self.room_order_var.set(",".join(map(str, wanted_order)))
        finally:
            self.suspend_live_autosave = False

        self.profile_status_var.set(
            "Сохранённый порядок: " +
            " → ".join(map(str, wanted_order)) +
            ". Автозапись area-order отключена: устройство отклоняет текущий формат параметра."
        )

    def apply_optimized_global_profile(self):
        if not messagebox.askyesno(
            "Оптимальный профиль 45 м²",
            "Будут применены проверенные общие параметры и расписание:\n\n"
            "• ручной режим: Strong 3, сухая+влажная, вода 2;\n"
            "• автоочистка станции после каждой уборки;\n"
            "• громкость 23%;\n"
            "• ковровый boost включён;\n"
            "• lidar_collision включён;\n"
            "• двойная уборка выключена;\n"
            "• DND 22:00–08:00;\n"
            "• Пн/Ср/Пт/Вс - вся квартира в 11:00;\n"
            "• Вт/Чт/Сб - кухня+коридор в 11:00.\n\n"
            "Порядок комнат этой кнопкой не меняется.\n"
            "Перед записью будет создан backup. Продолжить?"
        ):
            return

        def task():
            d = self.ensure_device()
            before = d.status().data
            backup = self.backup_data(before, "before_optimized_profile")
            results = {"backup": str(backup)}

            for key, val in OPTIMIZED_PROPERTIES.items():
                try:
                    results[key] = d.set_property(key, val)
                except Exception as e:
                    results[key] = f"ERROR: {e}"

            try:
                results["timing"] = d.set_timing(self._optimized_timing_raw())
            except Exception as e:
                results["timing"] = f"ERROR: {e}"

            try:
                results["forbid_mode"] = d.set_dnd(22, 0, 8, 0)
            except Exception as e:
                results["forbid_mode"] = f"ERROR: {e}"

            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)
            self._apply_optimized_properties_to_ui()
            self._update_user_profile(
                status=after,
                timing=OPTIMIZED_TIMING,
                forbid_mode={
                    "time": [79200, 28800, 1],
                    "tz": 3,
                    "tzs": 10800,
                },
            )
            errors = {
                k:v for k,v in results.items()
                if isinstance(v, str) and v.startswith("ERROR:")
            }
            if errors:
                messagebox.showwarning(
                    "Применено частично",
                    json.dumps(errors, ensure_ascii=False, indent=2)
                )
            else:
                messagebox.showinfo(
                    "Готово",
                    "Оптимальный общий профиль и расписание записаны.\n"
                    f"Backup: {results.get('backup')}"
                )

        self.async_run(task, done, "Применение оптимального профиля...")

    def apply_all_optimization(self):
        if not self.auto_area_raw:
            messagebox.showwarning(
                "Нужна карта",
                "Для безопасной записи порядка комнат сначала получите карту "
                "во вкладке «Комнаты и карта».\n\n"
                "Общие настройки можно применить отдельной кнопкой без карты."
            )
            return

        # Room order is saved locally only in v14.1 because the device
        # rejects the inferred area-order payload schema.

        if not messagebox.askyesno(
            "Применить всю оптимизацию",
            "Будет применено:\n\n"
            "1. Общие параметры робота.\n"
            "2. Автоочистка после каждой уборки.\n"
            "3. Громкость 23%.\n"
            "4. DND 22:00–08:00.\n"
            "5. Оптимизированное недельное расписание.\n"
            "6. lidar_collision = включено.\n"
            "7. Порядок 2→4→1→3→5 сохраняется в USER_PROFILE.json (в устройство не отправляется).\n\n"
            "Порядок комнат сохраняется локально, поскольку точный формат area-order "
            "для вашей прошивки не подтверждён.\n\n"
            "Покомнатная мощность/вода НЕ отправляется, потому что формат "
            "не подтверждён вашей картой.\n\nПродолжить?"
        ):
            return

        def task():
            d = self.ensure_device()
            before = d.status().data
            backup = self.backup_data(before, "before_full_optimization")
            results = {"backup": str(backup)}

            for key, val in OPTIMIZED_PROPERTIES.items():
                try:
                    results[key] = d.set_property(key, val)
                except Exception as e:
                    results[key] = f"ERROR: {e}"

            try:
                results["timing"] = d.set_timing(self._optimized_timing_raw())
            except Exception as e:
                results["timing"] = f"ERROR: {e}"

            try:
                results["forbid_mode"] = d.set_dnd(22, 0, 8, 0)
            except Exception as e:
                results["forbid_mode"] = f"ERROR: {e}"

            results["area_order"] = "LOCAL_ONLY_UNSUPPORTED_DEVICE_FORMAT"

            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)
            self.suspend_live_autosave = True
            try:
                self.room_order_var.set(",".join(map(str, OPTIMAL_ROOM_ORDER)))
            finally:
                self.suspend_live_autosave = False
            self._apply_optimized_properties_to_ui()
            self._update_user_profile(
                status=after,
                timing=OPTIMIZED_TIMING,
                forbid_mode={
                    "time": [79200, 28800, 1],
                    "tz": 3,
                    "tzs": 10800,
                },
                room_order=OPTIMAL_ROOM_ORDER,
            )
            errors = {
                k:v for k,v in results.items()
                if isinstance(v, str) and v.startswith("ERROR:")
            }
            log = ROOT / "optimization.log"
            with log.open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " " +
                    json.dumps(results, ensure_ascii=False, default=str) + "\n"
                )
            if errors:
                messagebox.showwarning(
                    "Оптимизация завершена частично",
                    "Некоторые действия не выполнены:\n\n" +
                    json.dumps(errors, ensure_ascii=False, indent=2)
                )
            else:
                messagebox.showinfo(
                    "Готово",
                    "Полная оптимизация применена.\n"
                    "Порядок: Спальня → Зал → Кухня → Коридор → Ванная.\n"
                    f"Backup: {results.get('backup')}"
                )

        self.async_run(task, done, "Применение полной оптимизации...")

    def apply_settings(self):
        if not messagebox.askyesno(
            "Подтверждение",
            "Записать выбранные параметры в пылесос?\n\nПеред записью будет сделана резервная копия."
        ):
            return

        values = {
            "fanspeed_mode": FAN[self.fan_var.get()],
            "sweep_type": SWEEP_TYPE[self.sweep_var.get()],
            "water_level": WATER[self.water_var.get()],
            "path_mode": PATH_MODE[self.path_var.get()],
            "work_station_freq": STATION_FREQ[self.station_freq_var.get()],
            "volume": max(0,min(100,int(self.volume_var.get()))),
            "auto_boost": bool(self.auto_boost_var.get()),
            "double_clean": bool(self.double_clean_var.get()),
            "led_switch": bool(self.led_var.get()),
            "lidar_collision": bool(self.lidar_var.get()),
            "station_led": bool(self.station_led_var.get()),
            "station_key": bool(self.station_key_var.get()),
            "mute": bool(self.mute_var.get()),
        }

        def task():
            d = self.ensure_device()
            before = d.status().data
            self.backup_data(before, "before_settings_write")
            results = {}
            for key,val in values.items():
                try:
                    results[key] = d.set_property(key,val)
                except Exception as e:
                    results[key] = f"ERROR: {e}"
            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)
            errors = {k:v for k,v in results.items() if isinstance(v,str) and v.startswith("ERROR")}
            if errors:
                messagebox.showwarning("Запись завершена частично", json.dumps(errors,ensure_ascii=False,indent=2))
            else:
                messagebox.showinfo("Готово","Настройки записаны и перечитаны с робота.")

        self.async_run(task, done, "Запись настроек...")

    def fill_map_id_from_map(self):
        if self.current_map_id is None:
            messagebox.showinfo(
                "mapId",
                "mapId ещё не получен. Откройте вкладку «Комнаты и карта» и загрузите карту, либо введите mapId вручную."
            )
            return
        self.direct_room_map_id_var.set(str(self.current_map_id))

    def _selected_room_ids(self):
        return [rid for rid,var in sorted(self.room_select_vars.items()) if var.get()]

    def _build_room_action_params(self, room_ids, map_id):
        # Exact serialization used by poisondima/Roidmi-EVE-Plus:
        # [2,"{\\"mapId\\":<id>,\\"segmentId\\":[1,3]}"]
        room_obj = {
            "mapId": int(map_id),
            "segmentId": [int(x) for x in room_ids],
        }
        return [2, json.dumps(room_obj, ensure_ascii=False, separators=(",",":"))]

    def start_selected_rooms_direct(self):
        rooms = self._selected_room_ids()
        if not rooms:
            messagebox.showinfo("Комнаты", "Выберите хотя бы одну комнату.")
            return
        raw_map_id = self.direct_room_map_id_var.get().strip()
        if not raw_map_id:
            messagebox.showinfo(
                "mapId",
                "Для выборочной уборки нужен mapId. Получите карту один раз или введите mapId вручную."
            )
            return
        try:
            map_id = int(raw_map_id)
        except Exception:
            messagebox.showerror("mapId", "mapId должен быть целым числом.")
            return

        params = self._build_room_action_params(rooms, map_id)
        room_names = ", ".join(ROOM_LABELS.get(x, str(x)) for x in rooms)
        if not messagebox.askyesno(
            "Уборка комнат",
            f"Запустить уборку: {room_names}?\n\n"
            f"Direct MIoT action: siid=14, aiid=1\n"
            f"mapId={map_id}, segmentId={rooms}"
        ):
            return

        allow_cloud = bool(self.direct_room_use_cloud_fallback.get())

        def task():
            d = self.ensure_device()
            local_error = None
            try:
                # Direct LAN call. This does not require Home Assistant.
                result = d.call_action_by(14, 1, params)
                return {"channel":"local", "result":result}
            except Exception as e:
                local_error = str(e)

            if not allow_cloud:
                raise RuntimeError(
                    "Локальная room-action не выполнена: " + local_error
                )

            client = self.active_cloud_client or self.pending_cloud_client
            dev = self.active_cloud_device
            if not client or not dev:
                raise RuntimeError(
                    "Локальная команда не прошла, а Xiaomi Cloud fallback не готов. "
                    "Сначала получите карту во вкладке «Комнаты и карта». "
                    f"Локальная ошибка: {local_error}"
                )
            result = client.do_miot_action(
                dev.get("country"), dev.get("device_id"), 14, 1, params
            )
            return {"channel":"cloud", "result":result, "local_error":local_error}

        def done(result):
            with (ROOT / "direct_actions.log").open("a", encoding="utf-8") as f:
                f.write(
                    datetime.now().isoformat() + " ROOM_SWEEP " +
                    json.dumps({"rooms":rooms,"mapId":map_id,**result}, ensure_ascii=False, default=str) + "\n"
                )
            self.statusbar_var.set(
                f"Уборка комнат отправлена через {result.get('channel')}: {room_names}"
            )
            self.after(1200, self.read_status)

        self.async_run(task, done, "Запуск уборки выбранных комнат...")

    def run_action(self, action):
        names = {
            "start":"начать уборку","stop":"остановить уборку","home":"вернуться на базу",
            "identify":"подать голосовой сигнал","start_dust":"запустить сбор пыли"
        }
        if not messagebox.askyesno("Команда", f"Отправить команду: {names[action]}?"):
            return

        if action == "start":
            before = dict(self.last_data or {})
            self._active_manual_session = {
                "source": "manual_all",
                "rooms": [1, 2, 3, 4, 5],
                "started_at": datetime.now().astimezone().isoformat(),
                "total_clean_time_sec": before.get("total_clean_time_sec"),
                "total_clean_areas": before.get("total_clean_areas"),
                "fan": before.get("fanspeed_mode"),
                "water": before.get("water_level"),
                "sweep_type": before.get("sweep_type"),
                "path_mode": before.get("path_mode"),
            }

        def task():
            d = self.ensure_device()
            getattr(d, action)()
            return d.status().data

        self.async_run(task, self.on_status, f"Команда: {names[action]}...")

    def _parse_timing(self, timing):
        if isinstance(timing, dict):
            return timing
        if timing in (None,"","null"):
            tz, tzs = local_tz_payload()
            return {"time":[],"tz":tz,"tzs":tzs}
        try:
            obj = json.loads(timing)
            if isinstance(obj,dict) and isinstance(obj.get("time"),list):
                return obj
        except Exception:
            pass
        tz, tzs = local_tz_payload()
        return {"time":[],"tz":tz,"tzs":tzs,"_unparsed_original":timing}

    def _populate_schedule(self, timing):
        self.current_timing = self._parse_timing(timing)
        for i in self.sch_tree.get_children():
            self.sch_tree.delete(i)
        for idx,row in enumerate(self.current_timing.get("time",[])):
            try:
                sec, enabled, fan, sweep, days, water, rooms = row[:7]
                days_txt = ",".join(DAY_NAMES.get(x,str(x)) for x in days)
                rooms_txt = "все" if not rooms else ",".join(map(str,rooms))
                self.sch_tree.insert("", "end", iid=str(idx), values=(
                    idx+1, seconds_to_hhmm(sec), "да" if enabled else "нет",
                    days_txt, fan, sweep, water, rooms_txt
                ))
            except Exception:
                self.sch_tree.insert("", "end", iid=str(idx), values=(idx+1,"?","?","?","?","?","?","RAW"))

    def load_selected_schedule(self, event=None):
        sel = self.sch_tree.selection()
        if not sel: return
        idx = int(sel[0])
        rows = self.current_timing.get("time",[])
        if idx >= len(rows): return
        row = rows[idx]
        try:
            sec, enabled, fan, sweep, days, water, rooms = row[:7]
        except Exception:
            messagebox.showerror("Нестандартная строка","Строка расписания имеет неизвестный формат. Используйте RAW JSON.")
            return
        self.sch_index = idx
        self.sch_hour.set(int(sec)//3600)
        self.sch_min.set((int(sec)%3600)//60)
        self.sch_enabled.set(bool(enabled))
        self.sch_fan.set(reverse_lookup(FAN,int(fan)))
        self.sch_type.set(reverse_lookup(SWEEP_TYPE,int(sweep)))
        self.sch_water.set(reverse_lookup(WATER,int(water)))
        self.sch_rooms.set(",".join(map(str,rooms or [])))
        for d,var in self.day_vars.items():
            var.set(d in days)

    def build_schedule_row(self, preserve_tail=None):
        h = int(self.sch_hour.get()); m = int(self.sch_min.get())
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Некорректное время.")
        days = [d for d in DAY_ORDER if self.day_vars[d].get()]
        if not days:
            raise ValueError("Выберите хотя бы один день недели.")
        rooms_txt = self.sch_rooms.get().strip()
        rooms = []
        if rooms_txt:
            try:
                rooms = [int(x.strip()) for x in rooms_txt.split(",") if x.strip()]
            except Exception:
                raise ValueError("ID комнат должны быть целыми числами через запятую.")
        row = [
            h*3600+m*60,
            1 if self.sch_enabled.get() else 0,
            FAN[self.sch_fan.get()],
            SWEEP_TYPE[self.sch_type.get()],
            days,
            WATER[self.sch_water.get()],
            rooms,
            None
        ]
        if preserve_tail is not None and len(preserve_tail) >= 8:
            row[7:] = preserve_tail[7:]
        return row

    def add_schedule(self):
        try:
            row = self.build_schedule_row()
        except Exception as e:
            messagebox.showerror("Ошибка",str(e)); return
        self.current_timing.setdefault("time",[]).append(row)
        self._populate_schedule(self.current_timing)
        self._schedule_live_schedule_save()

    def update_schedule(self):
        sel = self.sch_tree.selection()
        if not sel:
            messagebox.showinfo("Выбор","Выберите строку расписания."); return
        idx = int(sel[0])
        old = self.current_timing["time"][idx]
        try:
            row = self.build_schedule_row(old)
        except Exception as e:
            messagebox.showerror("Ошибка",str(e)); return
        self.current_timing["time"][idx] = row
        self._populate_schedule(self.current_timing)
        self._schedule_live_schedule_save()

    def delete_schedule(self):
        sel = self.sch_tree.selection()
        if not sel:
            messagebox.showinfo("Выбор","Выберите строку расписания."); return
        idx = int(sel[0])
        if messagebox.askyesno("Удаление","Удалить выбранную строку из локального проекта расписания?"):
            self.current_timing["time"].pop(idx)
            self._populate_schedule(self.current_timing)
            self._schedule_live_schedule_save()

    def save_schedule_to_robot(self):
        payload = {k:v for k,v in self.current_timing.items() if not str(k).startswith("_")}
        if "tz" not in payload or "tzs" not in payload:
            tz,tzs = local_tz_payload()
            payload["tz"] = tz
            payload["tzs"] = tzs

        pretty = json.dumps(payload,ensure_ascii=False,indent=2)
        if not messagebox.askyesno(
            "ВНИМАНИЕ: замена расписания",
            "Свойство timing будет записано целиком и заменит текущее расписание робота.\n\n"
            "Перед записью будет сохранён исходный timing.\n\nПродолжить?"
        ):
            return

        def task():
            d = self.ensure_device()
            before = d.status().data
            self.backup_data(before,"before_timing_write")
            raw = json.dumps(payload,ensure_ascii=False,separators=(",",":"))
            d.set_timing(raw)
            return d.status().data

        self.async_run(task, self.on_status, "Запись расписания...")

    def _populate_dnd(self, raw):
        try:
            obj = json.loads(raw) if isinstance(raw,str) else raw
            arr = obj.get("time",[])
            if len(arr)>=3:
                self.dnd_start_h.set(int(arr[0])//3600)
                self.dnd_start_m.set((int(arr[0])%3600)//60)
                self.dnd_end_h.set(int(arr[1])//3600)
                self.dnd_end_m.set((int(arr[1])%3600)//60)
        except Exception:
            pass

    def apply_dnd(self):
        h1,m1,h2,m2 = map(int,[self.dnd_start_h.get(),self.dnd_start_m.get(),self.dnd_end_h.get(),self.dnd_end_m.get()])
        if not all([0<=h1<=23,0<=h2<=23,0<=m1<=59,0<=m2<=59]):
            messagebox.showerror("Ошибка","Некорректное время."); return
        if not messagebox.askyesno("DND",f"Включить «Не беспокоить» с {h1:02d}:{m1:02d} до {h2:02d}:{m2:02d}?"):
            return
        def task():
            d=self.ensure_device()
            before=d.status().data
            self.backup_data(before,"before_dnd_write")
            d.set_dnd(h1,m1,h2,m2)
            return d.status().data
        self.async_run(task,self.on_status,"Запись DND...")

    def disable_dnd(self):
        if not messagebox.askyesno("DND","Отключить режим «Не беспокоить»?"): return
        def task():
            d=self.ensure_device()
            before=d.status().data
            self.backup_data(before,"before_dnd_disable")
            d.disable_dnd()
            return d.status().data
        self.async_run(task,self.on_status,"Отключение DND...")

    def fetch_rooms(self):
        username = self.cloud_user_var.get().strip()
        password = self.cloud_pass_var.get()
        country = self.cloud_country_var.get().strip() or "auto"

        if not username:
            # Try to recover the username from a reusable saved session.
            saved_any = (
                self._read_cloud_session_file(SHARED_CLOUD_SESSION_PATH)
                or self._read_cloud_session_file(CLOUD_SESSION_PATH)
                or self._migrate_old_cloud_session()
            )
            if saved_any:
                username = str(saved_any.get("username") or "")
                self.cloud_user_var.set(username)

        if not username:
            messagebox.showinfo(
                "Xiaomi Cloud",
                "Не найден логин Xiaomi и сохранённая сессия. Введите логин аккаунта."
            )
            return

        saved_before = self._load_cloud_session(username)
        if not saved_before and not password:
            messagebox.showinfo(
                "Xiaomi Cloud",
                "Сохранённая сессия не найдена. Для нового входа нужен пароль Xiaomi."
            )
            return

        def task():
            client = XiaomiCloudLite(username, password or "")

            # First try the previously verified Xiaomi Cloud session.
            saved = self._load_cloud_session(username)
            if saved and client.import_auth(saved):
                try:
                    result = self._fetch_rooms_after_cloud_login(client, country)
                    self.pending_cloud_client = client
                    return result
                except Exception:
                    # Token/session may have expired. Fall back to interactive login.
                    self._delete_cloud_session()

            login_result = client.login()
            if login_result.get("captcha_required"):
                self.pending_cloud_client = client
                self.pending_captcha_ick = login_result.get("captcha_ick")
                cap_path = ROOT / "xiaomi_captcha.jpg"
                cap_path.write_bytes(login_result["captcha_bytes"])
                self.pending_captcha_path = cap_path
                return {"captcha_required": True, "captcha_path": str(cap_path)}
            if login_result.get("two_factor_required"):
                self.pending_cloud_client = client
                return {"two_factor_url": login_result.get("url")}
            self._save_cloud_session(client)
            self.pending_cloud_client = client
            return self._fetch_rooms_after_cloud_login(client, country)

        self.async_run(task, self.on_rooms_result, "Вход в Xiaomi Cloud...")

    def _fetch_rooms_after_cloud_login(self, client, country):
        _, token = self.validate_connection()
        self.after(0, lambda: self.statusbar_var.set(f"Xiaomi Cloud: ищу EVE Plus, регион={country}..."))
        cloud_log(f"device lookup: region={country}")
        dev = client.find_device(token, country)
        if not dev:
            raise RuntimeError(
                "Устройство с этим token не найдено в Xiaomi Cloud. "
                "Проверьте аккаунт и регион."
            )
        if dev.get("model") != MODEL:
            raise RuntimeError(f"Найдена модель {dev.get('model')}, ожидалась {MODEL}.")

        self.after(0, lambda: self.statusbar_var.set("Xiaomi Cloud: устройство найдено. Загружаю карту..."))
        cloud_log(f"device found: model={dev.get('model')}, country={dev.get('country')}")
        raw = client.get_roidmi_map(dev["country"], dev["user_id"], dev["device_id"])
        rooms, meta, info = client.parse_roidmi_rooms(raw)

        # CPU-heavy image parsing and geometry analysis happen in this worker,
        # not on Tk's main UI thread.
        live_render = None
        live_render_error = None
        analysis = None
        analysis_error = None
        try:
            live_render = self._build_roidmi_live_map_png(raw)
        except Exception as e:
            live_render_error = str(e)
        try:
            analysis = self._parse_raw_map_geometry(raw, info)
        except Exception as e:
            analysis_error = str(e)

        return {
            "device": dev,
            "rooms": rooms,
            "meta": meta,
            "map_info": info,
            "raw_map": raw,
            "live_render": live_render,
            "live_render_error": live_render_error,
            "map_analysis": analysis,
            "map_analysis_error": analysis_error,
            "_cloud_client": client,
        }

    def on_rooms_result(self, result):
        if result.get("captcha_required"):
            cap_path = result.get("captcha_path")
            try:
                os.startfile(cap_path)
            except Exception:
                pass
            code = simpledialog.askstring(
                "Xiaomi CAPTCHA",
                "Xiaomi запросил CAPTCHA.\n\n"
                "Изображение открыто в стандартном просмотрщике Windows.\n"
                "Введите символы с картинки ТОЧНО с учётом регистра:"
            )
            if not code:
                self.statusbar_var.set("CAPTCHA отменена.")
                return
            self.retry_cloud_with_captcha(code.strip())
            return

        if result.get("two_factor_url"):
            self.cloud_2fa_url = result["two_factor_url"]
            self.btn_2fa.configure(state="normal")
            self.start_two_factor_flow()
            return

        self.cloud_2fa_url = None
        self.btn_2fa.configure(state="disabled")
        self.active_cloud_client = result.get("_cloud_client") or self.pending_cloud_client
        self.active_cloud_device = result.get("device") or None
        self.rooms_data = result.get("rooms", [])
        self.current_map_id = (result.get("meta") or {}).get("mapId")
        if self.current_map_id is not None:
            self.direct_room_map_id_var.set(str(self.current_map_id))
        self.map_info_raw = result.get("map_info", {}) or {}
        try:
            atomic_write_json(LAST_MAP_INFO_PATH, self.map_info_raw)
        except Exception:
            pass
        raw_live_map = result.get("raw_map")
        if raw_live_map:
            self.last_raw_map = raw_live_map
            live_render = result.get("live_render")
            if live_render:
                live_path, live_meta = live_render
                self.dashboard_live_map_path = Path(live_path)
                self.dashboard_live_map_available = True
                self.dashboard_map_mode_var.set("live")
                self.dashboard_live_map_status_var.set(
                    "Живая карта Xiaomi Cloud загружена: "
                    f"комнат {len(live_meta.get('rooms') or [])}; "
                    f"текущая комната робота: {live_meta.get('vacuum_room_name') or live_meta.get('vacuum_room') or '-'}."
                )
            else:
                self.dashboard_live_map_available = LIVE_MAP_PNG_PATH.exists()
                self.dashboard_live_map_status_var.set(
                    "Raw-карта получена; ошибка фонового рендера: "
                    + str(result.get("live_render_error") or "неизвестная ошибка")
                )

            analysis = result.get("map_analysis")
            if analysis:
                self.last_map_analysis = analysis
                atomic_write_json(LIVE_MAP_ANALYSIS_PATH, analysis)
                report = self._format_map_optimization_report(analysis)
                LIVE_MAP_REPORT_PATH.write_text(report, encoding="utf-8")
                route_names = analysis.get("recommended_route_names") or []
                if route_names:
                    self.map_optimization_status_var.set(
                        "Оптимизация по реальной карте: " + " -> ".join(route_names)
                    )
            else:
                self.map_optimization_status_var.set(
                    "Карта загружена; фоновый анализ не выполнен: "
                    + str(result.get("map_analysis_error") or "неизвестная ошибка")
                )

            self._archive_map_snapshot(raw_live_map, self.last_map_analysis)
        self.auto_area_raw = (
            self.map_info_raw.get("autoArea")
            if self.map_info_raw.get("autoArea") is not None
            else self.map_info_raw.get("autoAreaValue")
        ) or []

        for i in self.rooms_tree.get_children():
            self.rooms_tree.delete(i)

        for room in self.rooms_data:
            rid = room["id"]
            friendly = ROOM_LABELS.get(rid, room.get("friendly_name") or room["name"])
            clean_count = room.get("clean_count")
            self.rooms_tree.insert(
                "", "end", iid=str(rid),
                values=(rid, friendly, room["name"], clean_count)
            )
            if rid in getattr(self, "profile_clean_count_vars", {}):
                self.profile_clean_count_vars[rid].set(
                    "" if clean_count is None else str(clean_count)
                )

        dev = result.get("device", {})
        meta = result.get("meta", {})
        self.rooms_info_var.set(
            f"Найдено комнат: {len(self.rooms_data)} | фактические ID: " + ",".join(str(r.get("id")) for r in sorted(self.rooms_data, key=lambda x: x.get("id", 0))) + " | "
            f"регион: {dev.get('country')} | карта: {meta.get('width')}×{meta.get('height')}"
        )
        self.statusbar_var.set(f"Комнаты карты получены: {len(self.rooms_data)}.")
        try:
            atomic_write_json(LAST_ROOMS_PATH, self.rooms_data)
        except Exception:
            pass

        if self.pending_map_export and self.last_raw_map is not None:
            self.pending_map_export = False
            self.after(150, self._export_live_map_bundle_now)

        if self.pending_full_export_path and self.last_raw_map is not None:
            export_path = self.pending_full_export_path
            self.pending_full_export_path = None
            def finish_full_export(path=export_path):
                try:
                    result_path = self._export_full_bundle_now(path)
                    self.export_status_var.set(f"Полный архив создан: {result_path}")
                    messagebox.showinfo("Экспорт", f"Готово:\n{result_path}")
                except Exception as export_error:
                    messagebox.showerror("Экспорт", str(export_error))
            self.after(200, finish_full_export)

        payload = {
            "model": MODEL,
            "read_at": datetime.now().astimezone().isoformat(),
            "device_name": dev.get("name"),
            "country": dev.get("country"),
            "rooms": self.rooms_data,
            "map_meta": meta,
        }
        (BACKUP_DIR / "last_rooms.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )

        # Full map metadata is stored locally for protocol-safe room profile editing.
        # It contains map geometry/room data but no Xiaomi password/serviceToken.
        try:
            (BACKUP_DIR / "last_map_info.json").write_text(
                json.dumps(self.map_info_raw, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
            (BACKUP_DIR / "last_auto_area.json").write_text(
                json.dumps(self.auto_area_raw, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception:
            pass

        self.profile_status_var.set(
            f"Карта загружена. Комнат: {len(self.rooms_data)}; "
            f"autoArea объектов: {len(self.auto_area_raw)}."
        )
        self._refresh_dashboard()

        if not self.rooms_data:
            messagebox.showwarning(
                "Комнаты не найдены",
                "Карта получена, но autoArea/autoAreaValue не содержит комнат. "
                "Проверьте, что в Xiaomi Home карта сохранена и помещения разделены."
            )

        elif self.auto_config.get("auto_apply_room_order", True):
            self.after(250, self.auto_apply_room_order_silent)

    def retry_cloud_with_captcha(self, captcha_code):
        client = self.pending_cloud_client
        ick = self.pending_captcha_ick
        country = self.cloud_country_var.get().strip() or "auto"
        if client is None:
            messagebox.showerror("Xiaomi CAPTCHA", "Сессия CAPTCHA потеряна. Запустите получение комнат заново.")
            return

        def task():
            result = client.login(
                captcha_code=captcha_code,
                captcha_ick=ick,
                reuse_session=True
            )
            if result.get("captcha_required"):
                self.pending_captcha_ick = result.get("captcha_ick")
                cap_path = ROOT / "xiaomi_captcha.jpg"
                cap_path.write_bytes(result["captcha_bytes"])
                self.pending_captcha_path = cap_path
                return {"captcha_required": True, "captcha_path": str(cap_path)}
            if result.get("two_factor_required"):
                self.pending_cloud_client = client
                return {"two_factor_url": result.get("url")}
            self._save_cloud_session(client)
            self.pending_cloud_client = client
            return self._fetch_rooms_after_cloud_login(client, country)

        self.async_run(task, self.on_rooms_result, "Проверка CAPTCHA Xiaomi...")

    def start_two_factor_flow(self):
        if not self.cloud_2fa_url or not self.pending_cloud_client:
            messagebox.showerror("Xiaomi 2FA", "Сессия подтверждения потеряна. Запустите получение комнат заново.")
            return

        try:
            webbrowser.open(self.cloud_2fa_url)
        except Exception:
            pass

        ticket = simpledialog.askstring(
            "Xiaomi - код подтверждения",
            "Xiaomi запросил проверку аккаунта.\n\n"
            "1. В открывшейся странице Xiaomi НАЖМИТЕ отправку кода на телефон/e-mail.\n"
            "2. Получите код.\n"
            "3. НЕ вводите полученный код на веб-странице Xiaomi.\n"
            "4. Вернитесь в это окно и введите код здесь.\n\n"
            "Это важно: программа должна отправить код в той же сессии входа."
        )
        if not ticket:
            self.statusbar_var.set("2FA отменена. Сессия сохранена до закрытия программы.")
            return
        self.retry_cloud_with_2fa(ticket.strip())

    def retry_cloud_with_2fa(self, ticket):
        client = self.pending_cloud_client
        country = self.cloud_country_var.get().strip() or "auto"
        if client is None:
            messagebox.showerror("Xiaomi 2FA", "Сессия 2FA потеряна. Запустите получение комнат заново.")
            return

        def task():
            self.after(0, lambda: self.statusbar_var.set("2FA: отправляю код Xiaomi..."))
            result = client.verify_ticket(ticket)
            if not result.get("ok"):
                raise RuntimeError("Xiaomi 2FA не завершена.")
            self.after(0, lambda: self.statusbar_var.set("2FA: код принят. Получены Xiaomi Cloud токены..."))
            self._save_cloud_session(client)
            self.after(0, lambda: self.statusbar_var.set("2FA: получаю устройство и карту..."))
            return self._fetch_rooms_after_cloud_login(client, country)

        self.async_run(task, self.on_rooms_result, "Проверка кода Xiaomi 2FA...")

    def _read_cloud_session_file(self, path, username=None):
        path = Path(path)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        if username is not None and str(data.get("username", "")) != str(username):
            return None
        if not all(data.get(k) for k in ("username", "user_id", "service_token", "ssecurity")):
            return None
        return data

    def _write_cloud_session_file(self, path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        tmp.replace(path)

    def _find_old_cloud_sessions(self, username=None):
        """Search only nearby old ROIDMI folders, never the whole drive."""
        found = []
        candidates = []

        # Sibling version folders, usually on Desktop.
        try:
            for p in ROOT.parent.glob("ROIDMI_EVE_Plus_Control_Windows_v*"):
                if p.is_dir() and p.resolve() != ROOT.resolve():
                    candidates.append(p / "CLOUD_SESSION.json")
        except Exception:
            pass

        # Current folder local session.
        candidates.append(CLOUD_SESSION_PATH)

        seen = set()
        for path in candidates:
            try:
                rp = str(Path(path).resolve())
            except Exception:
                rp = str(path)
            if rp in seen:
                continue
            seen.add(rp)
            data = self._read_cloud_session_file(path, username)
            if data:
                try:
                    mtime = Path(path).stat().st_mtime
                except Exception:
                    mtime = 0
                found.append((mtime, Path(path), data))
        found.sort(key=lambda x: x[0], reverse=True)
        return found

    def _migrate_old_cloud_session(self, username=None):
        # Shared session already exists and matches.
        shared = self._read_cloud_session_file(SHARED_CLOUD_SESSION_PATH, username)
        if shared:
            return shared

        old = self._find_old_cloud_sessions(username)
        if not old:
            return None

        _mtime, source, data = old[0]
        try:
            self._write_cloud_session_file(SHARED_CLOUD_SESSION_PATH, data)
            # Keep a local compatibility copy too.
            self._write_cloud_session_file(CLOUD_SESSION_PATH, data)
            cloud_log(f"auth migration: {source} -> {SHARED_CLOUD_SESSION_PATH}")
            return data
        except Exception as e:
            cloud_log(f"auth migration failed: {e}")
            return data

    def _delete_cloud_session(self):
        for p in (CLOUD_SESSION_PATH, SHARED_CLOUD_SESSION_PATH):
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
        self._refresh_cloud_session_status()

    def _refresh_cloud_session_status(self):
        shared = self._read_cloud_session_file(SHARED_CLOUD_SESSION_PATH)
        local = self._read_cloud_session_file(CLOUD_SESSION_PATH)
        data = shared or local
        if not data:
            migrated = self._migrate_old_cloud_session()
            data = migrated
        if data:
            saved_at = data.get("saved_at") or "дата неизвестна"
            self.cloud_session_status_var.set(
                f"Xiaomi Cloud: сохранённая авторизация найдена. "
                f"Аккаунт {data.get('username')}; сохранено {saved_at}. "
                f"Новая версия будет использовать её автоматически."
            )
            try:
                if hasattr(self, "cloud_user_var") and not self.cloud_user_var.get().strip():
                    self.cloud_user_var.set(str(data.get("username") or ""))
            except Exception:
                pass
        else:
            self.cloud_session_status_var.set(
                "Xiaomi Cloud: сохранённая авторизация не найдена. "
                "При первом входе может потребоваться CAPTCHA/код."
            )

    def import_cloud_session_from_file(self):
        path = filedialog.askopenfilename(
            title="Выберите CLOUD_SESSION.json из старой версии",
            filetypes=[("Xiaomi Cloud session", "CLOUD_SESSION.json"), ("JSON", "*.json"), ("Все файлы", "*.*")]
        )
        if not path:
            return
        data = self._read_cloud_session_file(path)
        if not data:
            messagebox.showerror(
                "Xiaomi Cloud",
                "Файл не похож на сохранённую сессию этой программы."
            )
            return
        try:
            self._write_cloud_session_file(SHARED_CLOUD_SESSION_PATH, data)
            self._write_cloud_session_file(CLOUD_SESSION_PATH, data)
            if hasattr(self, "cloud_user_var"):
                self.cloud_user_var.set(str(data.get("username") or ""))
            self._refresh_cloud_session_status()
            messagebox.showinfo(
                "Xiaomi Cloud",
                "Сессия импортирована. Новые версии программы смогут использовать её "
                "из общей папки LocalAppData."
            )
        except Exception as e:
            messagebox.showerror("Xiaomi Cloud", str(e))

    def _save_cloud_session(self, client):
        data = client.export_auth()
        if not data:
            return
        # Shared copy survives unpacking/upgrading to a new application folder.
        self._write_cloud_session_file(SHARED_CLOUD_SESSION_PATH, data)
        # Local copy remains for backwards compatibility with old builds.
        self._write_cloud_session_file(CLOUD_SESSION_PATH, data)
        self._refresh_cloud_session_status()


    def _load_cloud_session(self, username):
        # 1. Shared LocalAppData session (preferred).
        data = self._read_cloud_session_file(SHARED_CLOUD_SESSION_PATH, username)
        if data:
            return data

        # 2. Local current-version session.
        data = self._read_cloud_session_file(CLOUD_SESSION_PATH, username)
        if data:
            try:
                self._write_cloud_session_file(SHARED_CLOUD_SESSION_PATH, data)
            except Exception:
                pass
            return data

        # 3. Automatic migration from a sibling old-version folder.
        return self._migrate_old_cloud_session(username)


    def open_cloud_2fa(self):
        if self.cloud_2fa_url:
            self.start_two_factor_flow()

    def rooms_to_schedule(self):
        selected = self.rooms_tree.selection()
        if not selected:
            messagebox.showinfo("Комнаты", "Выберите одну или несколько комнат в списке.")
            return
        ids = [str(int(x)) for x in selected]
        self.sch_rooms.set(",".join(ids))
        self.nb.select(self.tab_schedule)
        self.statusbar_var.set("ID выбранных комнат перенесены в редактор расписания.")

    def export_rooms(self):
        if not self.rooms_data:
            messagebox.showinfo("Комнаты", "Сначала получите список комнат.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить комнаты",
            defaultextension=".json",
            filetypes=[("JSON","*.json")],
            initialfile=f"roidmi_rooms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if not path:
            return
        Path(path).write_text(
            json.dumps({"model":MODEL,"rooms":self.rooms_data}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _room_profile_dict(self):
        out = {}
        for rid in [1,2,3,4,5]:
            out[rid] = {
                "name": self.profile_name_vars[rid].get().strip(),
                "fan": FAN[self.profile_fan_vars[rid].get()],
                "water": WATER[self.profile_water_vars[rid].get()],
            }
        return out

    def _room_order(self):
        try:
            order = [int(x.strip()) for x in self.room_order_var.get().split(",") if x.strip()]
        except Exception:
            raise ValueError("Порядок комнат должен содержать целые ID через запятую.")
        if sorted(order) != [1,2,3,4,5]:
            raise ValueError("Для полной уборки укажите каждый ID 1–5 ровно один раз.")
        return order

    def set_optimal_room_order(self):
        self.room_order_var.set(",".join(map(str, OPTIMAL_ROOM_ORDER)))
        self.profile_status_var.set(
            "Установлен рекомендуемый порядок: 2 → 4 → 1 → 3 → 5."
        )

    def save_room_profiles_local(self):
        try:
            payload = {
                "model": MODEL,
                "room_order": self._room_order(),
                "profiles": self._room_profile_dict(),
                "saved_at": datetime.now().astimezone().isoformat(),
            }
        except Exception as e:
            messagebox.showerror("Профили комнат", str(e))
            return
        path = ROOT / "room_profiles.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        messagebox.showinfo("Профили комнат", f"Сохранено локально:\n{path}")

    def inspect_auto_area(self):
        if not self.auto_area_raw:
            messagebox.showinfo(
                "autoArea",
                "Сначала получите карту во вкладке «Комнаты и карта»."
            )
            return
        keys = sorted({
            k for obj in self.auto_area_raw if isinstance(obj, dict) for k in obj.keys()
        })
        self.profile_status_var.set(
            "Поля реального autoArea: " + ", ".join(keys)
        )
        known = set(keys) == {"CleanCount", "id", "name"}
        extra = (
            "\n\nЭто соответствует вашей фактической прошивке: "
            "покомнатной мощности/воды в autoArea нет."
            if known else
            "\n\nСтруктура отличается от ранее полученной; проверьте сохранённый JSON."
        )
        messagebox.showinfo(
            "Структура autoArea",
            "Обнаруженные поля:\n\n" + ", ".join(keys) + extra +
            "\n\nПолная структура сохранена в backups\\last_auto_area.json."
        )

    def _area_objects_by_id(self):
        if not self.auto_area_raw:
            raise ValueError("Карта/autoArea ещё не загружены.")
        by_id = {}
        for obj in self.auto_area_raw:
            if not isinstance(obj, dict) or "id" not in obj:
                continue
            try:
                by_id[int(obj["id"])] = copy.deepcopy(obj)
            except Exception:
                pass
        missing = [rid for rid in [1,2,3,4,5] if rid not in by_id]
        if missing:
            raise ValueError(f"В autoArea отсутствуют комнаты: {missing}")
        return by_id

    def _require_cloud_map_action_context(self):
        client = self.active_cloud_client or self.pending_cloud_client
        dev = self.active_cloud_device
        if not client or not dev:
            raise ValueError(
                "Для изменения порядка комнат сначала получите карту во вкладке "
                "«Комнаты и карта». Это создаёт подтверждённую Xiaomi Cloud-сессию."
            )
        country = dev.get("country")
        did = dev.get("device_id")
        if not country or not did:
            raise ValueError("Не найден country/device_id Xiaomi Cloud.")
        return client, dev, country, did

    def apply_room_order(self):
        try:
            order = self._room_order()
        except Exception as e:
            messagebox.showerror("Порядок комнат", str(e))
            return

        self._update_user_profile(room_order=order)
        with (ROOT / "autosave.log").open("a", encoding="utf-8") as f:
            f.write(
                datetime.now().isoformat() + " ROOM_ORDER_LOCAL_ONLY " +
                json.dumps({"order": order}, ensure_ascii=False) + "\n"
            )

        messagebox.showinfo(
            "Порядок комнат сохранён",
            "Порядок сохранён в USER_PROFILE.json:\n\n" +
            " → ".join(map(str, order)) +
            "\n\nВ ROIDMI он не отправлен. Ваш робот отклоняет ранее "
            "использованный формат area-order с ошибкой -704220035 "
            "(ошибка параметра действия). До подтверждения точного формата "
            "v14.1 не отправляет эту команду."
        )
        self.profile_status_var.set(
            "Порядок комнат сохранён локально: " +
            " → ".join(map(str, order))
        )

    def _detect_existing_key(self, objects, candidates):
        keys = set()
        for obj in objects:
            if isinstance(obj, dict):
                keys.update(obj.keys())
        for c in candidates:
            if c in keys:
                return c
        return None

    def apply_room_custom(self):
        messagebox.showinfo(
            "Покомнатная мощность/вода",
            "Функция записи intentionally отключена в v13.\n\n"
            "В фактическом last_auto_area вашей прошивки присутствуют только "
            "CleanCount, id и name. Публичная MIoT-спецификация подтверждает "
            "само действие area-custom, но не раскрывает его внутренний JSON-формат.\n\n"
            "Поэтому программа не придумывает поля мощности/воды и не отправляет "
            "потенциально повреждающую карту команду."
        )

    def import_config_json(self):
        path = filedialog.askopenfilename(
            title="Выберите JSON конфигурации ROIDMI",
            filetypes=[("JSON","*.json"),("Все файлы","*.*")]
        )
        if not path:
            return

        try:
            obj = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except Exception as e:
            messagebox.showerror("Импорт JSON", f"Не удалось прочитать JSON:\n{e}")
            return

        # Accept either full exported structure {"model":..., "data":{...}}
        # or direct data object.
        if isinstance(obj, dict) and isinstance(obj.get("data"), dict):
            cfg = obj["data"]
            model = obj.get("model")
            if model and model != MODEL:
                messagebox.showerror(
                    "Импорт JSON",
                    f"Файл относится к модели {model}, ожидалась {MODEL}."
                )
                return
        elif isinstance(obj, dict):
            cfg = obj
        else:
            messagebox.showerror("Импорт JSON", "Ожидался JSON-объект.")
            return

        supported = {
            "fanspeed_mode", "sweep_type", "water_level", "path_mode",
            "work_station_freq", "volume", "auto_boost", "double_clean",
            "led_switch", "lidar_collision", "station_led", "station_key",
            "mute", "timing", "forbid_mode"
        }
        selected = {k: cfg[k] for k in supported if k in cfg}

        if not selected:
            messagebox.showwarning(
                "Импорт JSON",
                "В файле нет поддерживаемых изменяемых параметров."
            )
            return

        self.imported_config = selected
        self.imported_config_path = path

        # Show a safe preview. Sensitive values such as token/password are never imported.
        current = self.last_data or {}
        preview = {
            "source_file": str(path),
            "model": MODEL,
            "will_apply_only": selected,
            "differences_vs_current": {
                k: {"current": current.get(k), "imported": v}
                for k, v in selected.items()
                if current.get(k) != v
            }
        }
        self.raw_text.delete("1.0","end")
        self.raw_text.insert(
            "1.0",
            json.dumps(preview, ensure_ascii=False, indent=2, default=str)
        )

        messagebox.showinfo(
            "Импорт выполнен",
            "Конфигурация загружена в программу, но ЕЩЁ НЕ записана в пылесос.\n\n"
            "Проверьте изменения во вкладке «Диагностика / JSON» и нажмите "
            "«ПРИМЕНИТЬ ИМПОРТИРОВАННОЕ»."
        )

    def _parse_json_string_or_obj(self, value, field_name):
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                obj = json.loads(value)
            except Exception as e:
                raise ValueError(f"{field_name}: некорректный JSON: {e}")
            if not isinstance(obj, dict):
                raise ValueError(f"{field_name}: ожидался JSON-объект.")
            return obj
        raise ValueError(f"{field_name}: неподдерживаемый тип {type(value).__name__}.")

    def apply_imported_config(self):
        if not self.imported_config:
            messagebox.showinfo(
                "Импорт конфигурации",
                "Сначала нажмите «Импорт конфигурации JSON» и выберите файл."
            )
            return

        cfg = dict(self.imported_config)

        # Compute preview/diff using the freshest known status.
        diff = {
            k: {"current": self.last_data.get(k), "new": v}
            for k, v in cfg.items()
            if self.last_data.get(k) != v
        }
        if not diff:
            messagebox.showinfo(
                "Конфигурация",
                "Импортированные параметры уже совпадают с текущими."
            )
            return

        diff_text = "\n".join(
            f"{k}: {v['current']}  ->  {v['new']}" for k, v in diff.items()
        )
        if len(diff_text) > 2500:
            diff_text = diff_text[:2500] + "\n..."

        if not messagebox.askyesno(
            "Запись конфигурации",
            "Будут записаны ТОЛЬКО поддерживаемые изменяемые параметры.\n"
            "Счётчики, состояние, расходники, карта, голосовой пакет и прочие "
            "поля JSON не затрагиваются.\n\n"
            "Перед записью программа сохранит резервную копию текущего состояния.\n\n"
            "Изменения:\n" + diff_text + "\n\nПродолжить?"
        ):
            return

        property_keys = [
            "fanspeed_mode", "sweep_type", "water_level", "path_mode",
            "work_station_freq", "volume", "auto_boost", "double_clean",
            "led_switch", "lidar_collision", "station_led", "station_key", "mute"
        ]

        def task():
            d = self.ensure_device()
            before = d.status().data
            backup_path = self.backup_data(before, "before_imported_config")
            results = {"backup": str(backup_path)}

            # Apply ordinary writable properties individually.
            for key in property_keys:
                if key not in cfg:
                    continue
                try:
                    results[key] = d.set_property(key, cfg[key])
                except Exception as e:
                    results[key] = f"ERROR: {e}"

            # Apply timing via model-specific method.
            if "timing" in cfg:
                try:
                    timing_obj = self._parse_json_string_or_obj(cfg["timing"], "timing")
                    raw_timing = json.dumps(
                        timing_obj, ensure_ascii=False, separators=(",",":")
                    )
                    results["timing"] = d.set_timing(raw_timing)
                except Exception as e:
                    results["timing"] = f"ERROR: {e}"

            # Apply DND via dedicated method where possible.
            if "forbid_mode" in cfg:
                try:
                    fm = self._parse_json_string_or_obj(cfg["forbid_mode"], "forbid_mode")
                    arr = fm.get("time")
                    if isinstance(arr, list) and len(arr) >= 3 and int(arr[2]) == 1:
                        start_sec = int(arr[0])
                        end_sec = int(arr[1])
                        sh, sm = divmod(start_sec, 3600)
                        sm //= 60
                        eh, em = divmod(end_sec, 3600)
                        em //= 60
                        results["forbid_mode"] = d.set_dnd(sh, sm, eh, em)
                    else:
                        results["forbid_mode"] = d.disable_dnd()
                except Exception as e:
                    results["forbid_mode"] = f"ERROR: {e}"

            after = d.status().data
            return results, after

        def done(result):
            results, after = result
            self.on_status(after)

            errors = {
                k:v for k,v in results.items()
                if isinstance(v, str) and v.startswith("ERROR:")
            }
            if errors:
                messagebox.showwarning(
                    "Запись завершена частично",
                    "Некоторые параметры не записались:\n\n" +
                    json.dumps(errors, ensure_ascii=False, indent=2)
                )
            else:
                messagebox.showinfo(
                    "Готово",
                    "Импортированная конфигурация записана.\n"
                    "Состояние перечитано с пылесоса.\n\n"
                    f"Резервная копия: {results.get('backup')}"
                )

        self.async_run(task, done, "Запись импортированной конфигурации...")

    def export_raw(self):
        if not self.last_data:
            messagebox.showinfo("Нет данных","Сначала прочитайте состояние робота."); return
        path = filedialog.asksaveasfilename(
            title="Сохранить JSON", defaultextension=".json",
            filetypes=[("JSON","*.json")],
            initialfile=f"roidmi_v60_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if not path: return
        payload={"model":MODEL,"read_at":datetime.now().astimezone().isoformat(),"data":self.last_data}
        Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str),encoding="utf-8")

    def apply_raw_timing(self):
        try:
            obj=json.loads(self.raw_text.get("1.0","end"))
            if isinstance(obj,dict) and "data" in obj:
                timing=obj["data"].get("timing")
            elif isinstance(obj,dict) and "time" in obj:
                timing=obj
            else:
                raise ValueError("В JSON не найден timing.")
            if isinstance(timing,dict):
                raw=json.dumps(timing,ensure_ascii=False,separators=(",",":"))
            elif isinstance(timing,str):
                json.loads(timing)  # validation
                raw=timing
            else:
                raise ValueError("timing должен быть строкой JSON или объектом.")
        except Exception as e:
            messagebox.showerror("RAW timing",f"Не удалось разобрать timing:\n{e}"); return

        if not messagebox.askyesno(
            "RAW timing - повышенный риск",
            "Вы собираетесь записать timing вручную. Ошибочный формат может нарушить расписание.\n"
            "Исходное состояние будет сохранено в backups.\n\nПродолжить?"
        ): return

        def task():
            d=self.ensure_device()
            before=d.status().data
            self.backup_data(before,"before_raw_timing")
            d.set_timing(raw)
            return d.status().data
        self.async_run(task,self.on_status,"Запись RAW timing...")


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        write_crash_report(
            exc_type, exc_value, exc_tb, "application_start_or_mainloop"
        )
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "ROIDMI Control - аварийная ошибка",
                f"{exc_type.__name__}: {exc_value}\n\n"
                "Подробности сохранены в CRASH_REPORT.txt."
            )
            root.destroy()
        except Exception:
            pass
        raise
