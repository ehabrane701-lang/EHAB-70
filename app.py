#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ====================================================================
# 🔒 Ehab Al-Houbani : @Y_20_20 | ابن اليمن Unified Host & Web Server
# ====================================================================

import ast
import atexit
import base64
import gc
import hashlib
import json
import logging
import os
import platform
import random
import re
import shutil
import sqlite3
import string
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from datetime import datetime, timedelta
from functools import wraps
from html import escape

# ============ التحقق التلقائي وتثبيت الحزم المطلوبة ============
required_modules = {
    "telebot": "pyTelegramBotAPI",
    "requests": "requests",
    "Crypto": "pycryptodome",
    "bs4": "beautifulsoup4",
    "psutil": "psutil",
    "flask": "Flask",
    "werkzeug": "Werkzeug",
}
missing_packages = []

for module, package in required_modules.items():
    try:
        __import__(module)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f"📦 جاري تثبيت الحزم المفقودة: {missing_packages}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ تم التثبيت بنجاح، يرجى إعادة تشغيل السكريبت.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل التثبيت: {e}")
        sys.exit(1)

from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
import psutil
import requests
import telebot
from telebot import types
from werkzeug.security import check_password_hash, generate_password_hash

# --- السجلات ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("IbnAlYemenHost")

# ============ الإعدادات الأساسية والثوابت ============
TOKEN = os.environ.get("BOT_TOKEN", "9026885072:AAFSJYA8pg6k5kOP28ZZp58faDb5nJDg6eE")


def _parse_id(val, default=0):
    try:
        return int(str(val).strip())
    except (TypeError, ValueError):
        return default


OWNER_ID = _parse_id(os.environ.get("OWNER_ID", "1002670694"), 0)
ADMIN_ID = _parse_id(os.environ.get("ADMIN_ID", str(OWNER_ID)), OWNER_ID)
YOUR_USERNAME = os.environ.get("OWNER_USERNAME", "Y_20_20").lstrip("@")
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "https://t.me/Y_20_20")
UPDATE_CHANNEL_CHAT = os.environ.get("UPDATE_CHANNEL_CHAT", "@Y_20_20")

CHANNEL_EHAB_ME = _parse_id(os.environ.get("CHANNEL_EHAB_ME", str(OWNER_ID or ADMIN_ID)), OWNER_ID or ADMIN_ID)
CHANNEL_EHAB_LINK = UPDATE_CHANNEL
user_bot = os.environ.get("BOT_USERNAME", "your_bot_username").lstrip("@")

PAGE_BRAND_NAME = "ابن اليمن"
BOT_BRAND_NAME = "ابن اليمن — 𝗘𝗛𝗔𝗕𝗔𝗜𝗛𝗔𝗪𝗕𝗔𝗡𝗜"
DEV_TELEGRAM = f"https://t.me/{YOUR_USERNAME}" if YOUR_USERNAME else "https://t.me/Y_20_20"
jiminot = PAGE_BRAND_NAME
FIRE_EFFECT_ID = "5104841245755180586"

FREE_USER_LIMIT = 3
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 99999
OWNER_LIMIT = float("inf")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_LOG_SIZE_KB = 512

ALLOWED_SCRIPT_EXTS = {".py", ".js"}
ALLOWED_UPLOAD_EXTS = {".py", ".js", ".zip"}
ALLOWED_EXTRA_EXTS = {".py", ".js", ".json", ".txt", ".md", ".html", ".css", ".env"}

# ============ المسارات والمجلدات ============
BASE_DIR = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
RUNNING_DIR = os.path.join(BASE_DIR, "active_bots")
LOGS_DIR = os.path.join(BASE_DIR, "bot_logs")
DB_DIR = os.path.join(BASE_DIR, "database")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
STORE_DIR = os.path.join(BASE_DIR, "store_files")
THUMBS_DIR = os.path.join(ASSETS_DIR, "thumbs")
MARKET_DIR = os.path.join(BASE_DIR, "market")
ENV_DIR = os.path.join(BASE_DIR, "bot_environments")
ENCRYPTED_DIR = os.path.join(BASE_DIR, "encrypted_files")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
UPLOAD_DIR = os.path.realpath(os.path.join(BASE_DIR, "upload_bots"))
SUSPICIOUS_DIR = os.path.join(BASE_DIR, "suspicious_files")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
SQLITE_DB_PATH = os.path.join(DB_DIR, "host_unified.db")

for _d in [
    TEMPLATES_DIR, RUNNING_DIR, LOGS_DIR, DB_DIR, ASSETS_DIR, STORE_DIR,
    THUMBS_DIR, MARKET_DIR, ENV_DIR, ENCRYPTED_DIR, DOWNLOAD_DIR, UPLOAD_DIR,
    SUSPICIOUS_DIR, BACKUPS_DIR
]:
    os.makedirs(_d, exist_ok=True)

USERS_DB = os.path.join(DB_DIR, "users.json")
FILES_DB = os.path.join(DB_DIR, "files.json")
SETTINGS_DB = os.path.join(DB_DIR, "settings.json")
STORE_DB = os.path.join(DB_DIR, "store.json")
ADMINS_DB = os.path.join(DB_DIR, "admins.json")
MARKET_DB = os.path.join(DB_DIR, "market.json")
SECURITY_DB = os.path.join(DB_DIR, "security.json")
WEB_USERS_DB = os.path.join(DB_DIR, "web_accounts.json")
PURCHASES_DB_PATH = os.path.join(DB_DIR, "purchases.db")

# ============ أقفال التزامن والبيانات المشتركة ============
db_lock = threading.RLock()
process_lock = threading.RLock()
state_lock = threading.RLock()

BANS = {}
VIP = {}
USERS = {}
STATS = {"total_consumed": 0}
_ipinfo = {"t": 0, "data": None}
bot_scripts = {}
active_processes = {}
cancel_states = {}
last_bot_messages = {}
admin_steps = {}
PENDING = {}
USER_STEPS = {}

# ============ تعريف كائن البوت مبكراً لتفادي NameError ============
bot = telebot.TeleBot(TOKEN, threaded=True)

# ============ إعدادات محرك الذكاء الاصطناعي Ptero.pro ============
HOME_URL = "https://ptero.pro"
CHAT_URL = f"{HOME_URL}/wp-json/mlp/v1/chat-stream"

MODELS = {
    "1": {"id": "ling-3.0-flash", "name": "Ling 3.0 Flash"},
    "2": {"id": "deepseek-v4.1-flash:free", "name": "DeepSeek v4.1 Flash"},
    "3": {"id": "minimax-m3.1-flash:runware", "name": "MiniMax M3.1 Flash"},
    "4": {"id": "glm-5.3-flash", "name": "GLM 5.3 Flash"},
    "5": {"id": "qwen3.7-flash:minirouter", "name": "Qwen 3.7 Flash"},
}

DEFAULT_MODEL_ID = "ling-3.0-flash"
FALLBACK_MODELS = [
    "deepseek-v4.1-flash:free",
    "minimax-m3.1-flash:runware",
    "glm-5.3-flash",
    "qwen3.7-flash:minirouter",
    "ling-3.0-flash:free",
]

MAX_SOURCE_BYTES = 20 * 1024 * 1024
_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


class RepairServiceError(RuntimeError):
    """خطأ عند تعذر معالجة الملف عبر خدمة الذكاء الاصطناعي الخارجية."""


# ============ أدوات قواعد البيانات الموحدة ============
def read_json(path):
    with db_lock:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            return {}
        except Exception as e:
            logger.warning(f"JSON read error ({path}): {e}")
            return {}


def write_json(path, data):
    with db_lock:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            temp_path = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(temp_path, path)
            return True
        except Exception as e:
            logger.error(f"JSON write error ({path}): {e}")
            return False


def db_conn():
    con = sqlite3.connect(PURCHASES_DB_PATH, check_same_thread=False, timeout=15.0)
    con.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            item TEXT,
            cost REAL,
            status TEXT,
            ts INTEGER
        )
    """)
    con.commit()
    return con


def init_unified_sqlite():
    with db_lock:
        con = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False, timeout=15.0)
        try:
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute("""
                CREATE TABLE IF NOT EXISTS user_addons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    addon_name TEXT NOT NULL,
                    addon_type TEXT DEFAULT 'pip',
                    created_at TEXT
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT
                )
            """)
            con.commit()
        finally:
            con.close()


def record_addon(user_id, file_id, addon_name, addon_type="pip"):
    clean_addon = re.sub(r"[^a-zA-Z0-9._-]", "", str(addon_name).strip())
    if not clean_addon:
        return
    with db_lock:
        con = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False, timeout=15.0)
        try:
            con.execute(
                "INSERT INTO user_addons (user_id, file_id, addon_name, addon_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (int(user_id), str(file_id), clean_addon, addon_type, datetime.now().isoformat())
            )
            con.commit()
        finally:
            con.close()

        files = read_json(FILES_DB)
        fid = str(file_id)
        if fid in files:
            addons = list(files[fid].get("addons", []))
            if clean_addon not in addons:
                addons.append(clean_addon)
                files[fid]["addons"] = addons
                write_json(FILES_DB, files)


def get_settings():
    return read_json(SETTINGS_DB)


def save_settings(settings):
    return write_json(SETTINGS_DB, settings)


def get_storage():
    return get_settings()


def save_storage(data):
    return save_settings(data)


def init_security():
    with db_lock:
        security = read_json(SECURITY_DB)
        changed = False
        if "master_key" not in security:
            security["master_key"] = base64.b64encode(get_random_bytes(32)).decode("utf-8")
            changed = True
        if "file_keys" not in security:
            security["file_keys"] = {}
            changed = True
        if "flask_secret" not in security:
            security["flask_secret"] = base64.urlsafe_b64encode(get_random_bytes(32)).decode("utf-8")
            changed = True
        if changed:
            write_json(SECURITY_DB, security)


def init_db():
    global USERS
    with db_lock:
        default_settings = {
            "channels": [],
            "bot_name": BOT_BRAND_NAME,
            "page_name": PAGE_BRAND_NAME,
            "bot_image": None,
            "file_thumb": None,
            "bot_locked": False,
            "auto_approve": False,
            "maintenance_mode": False,
            "python_upload_price": 1.0,
        }
        current_settings = read_json(SETTINGS_DB)
        for key, value in default_settings.items():
            if key not in current_settings:
                current_settings[key] = value
        write_json(SETTINGS_DB, current_settings)

        for path in [USERS_DB, FILES_DB, STORE_DB, MARKET_DB, SECURITY_DB, WEB_USERS_DB]:
            if not os.path.exists(path):
                write_json(path, {})

        admins_data = read_json(ADMINS_DB)
        adm_list = set(admins_data.get("admins", []))
        for aid in (OWNER_ID, ADMIN_ID):
            if aid and aid > 0:
                adm_list.add(int(aid))
        if adm_list:
            write_json(ADMINS_DB, {"admins": sorted(adm_list)})

        USERS = read_json(USERS_DB)
        try:
            con = db_conn()
            con.close()
        except Exception:
            pass
        init_unified_sqlite()
        init_security()


# ============ التشفير والأمان والحظر الفوري ============
def get_master_key():
    with db_lock:
        security = read_json(SECURITY_DB)
        master_key = security.get("master_key")
        if not master_key:
            master_key = base64.b64encode(get_random_bytes(32)).decode("utf-8")
            security["master_key"] = master_key
            write_json(SECURITY_DB, security)
        return base64.b64decode(master_key)


def generate_file_key(fid, user_id):
    with db_lock:
        security = read_json(SECURITY_DB)
        file_keys = security.get("file_keys", {})
        if fid not in file_keys:
            combined = f"{fid}:{user_id}:{ADMIN_ID}:{TOKEN}"
            salt = hashlib.sha256(combined.encode("utf-8")).digest()[:16]
            master_key = get_master_key()
            kdf = hashlib.pbkdf2_hmac("sha256", master_key, salt, 100000, dklen=32)
            file_keys[fid] = {
                "key": base64.b64encode(kdf).decode("utf-8"),
                "salt": base64.b64encode(salt).decode("utf-8"),
                "user_id": user_id,
            }
            security["file_keys"] = file_keys
            write_json(SECURITY_DB, security)
        return file_keys[fid]


def get_file_key(fid):
    security = read_json(SECURITY_DB)
    return security.get("file_keys", {}).get(fid)


def encrypt_file_content(content, fid, user_id):
    try:
        file_key_info = generate_file_key(fid, user_id)
        key = base64.b64decode(file_key_info["key"])
        salt = base64.b64decode(file_key_info["salt"])
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(content.encode("utf-8"), AES.block_size))
        encrypted_data = {
            "iv": base64.b64encode(cipher.iv).decode("utf-8"),
            "ciphertext": base64.b64encode(ct_bytes).decode("utf-8"),
            "salt": base64.b64encode(salt).decode("utf-8"),
            "fid": fid,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(encrypted_data)
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return None


def decrypt_file_content(encrypted_json, fid):
    try:
        data = json.loads(encrypted_json)
        file_key_info = get_file_key(fid)
        if not file_key_info:
            return None
        key = base64.b64decode(file_key_info["key"])
        iv = base64.b64decode(data["iv"])
        ct = base64.b64decode(data["ciphertext"])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode("utf-8")
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return None


def save_encrypted_file(fid, content, user_id):
    encrypted_content = encrypt_file_content(content, fid, user_id)
    if encrypted_content:
        encrypted_path = os.path.join(ENCRYPTED_DIR, f"{fid}.enc")
        with open(encrypted_path, "w", encoding="utf-8") as f:
            f.write(encrypted_content)
        return True
    return False


def load_encrypted_file(fid):
    encrypted_path = os.path.join(ENCRYPTED_DIR, f"{fid}.enc")
    if os.path.exists(encrypted_path):
        with open(encrypted_path, "r", encoding="utf-8") as f:
            return decrypt_file_content(f.read(), fid)
    return None


def is_admin(user_id):
    if not user_id:
        return False
    try:
        uid_int = int(user_id)
    except (TypeError, ValueError):
        return False
    if uid_int in (OWNER_ID, ADMIN_ID) and uid_int > 0:
        return True
    admins_data = read_json(ADMINS_DB)
    return uid_int in admins_data.get("admins", [])


def is_main_admin(user_id):
    try:
        uid_int = int(user_id)
    except (TypeError, ValueError):
        return False
    return uid_int in (OWNER_ID, ADMIN_ID) and uid_int > 0


def get_admins():
    admins_data = read_json(ADMINS_DB)
    adm = set(admins_data.get("admins", []))
    for aid in (OWNER_ID, ADMIN_ID):
        if aid and aid > 0:
            adm.add(int(aid))
    return sorted(adm)


def add_admin(user_id):
    with db_lock:
        user_id = int(user_id)
        admins_data = read_json(ADMINS_DB)
        lst = admins_data.get("admins", [])
        if user_id not in lst:
            lst.append(user_id)
            admins_data["admins"] = lst
            write_json(ADMINS_DB, admins_data)
            return True
        return False


def remove_admin(user_id):
    with db_lock:
        user_id = int(user_id)
        if user_id in (OWNER_ID, ADMIN_ID):
            return False
        admins_data = read_json(ADMINS_DB)
        lst = admins_data.get("admins", [])
        if user_id in lst:
            lst.remove(user_id)
            admins_data["admins"] = lst
            write_json(ADMINS_DB, admins_data)
            return True
        return False


def verify_file_access(fid, user_id):
    files = read_json(FILES_DB)
    if fid not in files:
        return False
    file_info = files[fid]
    if is_admin(user_id):
        return True
    if str(file_info.get("user_id")) == str(user_id):
        return True
    if file_info.get("type") == "store":
        store = read_json(STORE_DB)
        if fid in store:
            return True
    return False


def is_bot_locked():
    return bool(get_settings().get("bot_locked", False))


def scan_code_security(content, strict_text=True):
    if not content:
        return True, "الكود آمن"
    if strict_text and "\x00" in content:
        return False, "وجود بايتات ثنائية أو مشفّرة داخل ملف نصي."
    for line in content.splitlines():
        stripped = line.strip()
        if len(stripped) > 2500 and re.fullmatch(r"[A-Za-z0-9+/=_\-$@!%*?]+", stripped):
            return False, "وجود سلسلة مشفّرة أو مموّهة بطول غير طبيعي."

    dangerous_patterns = [
        (r"\bmarshal\s*\.\s*loads\s*\(", "استخدام marshal.loads لإخفاء كود مشفّر."),
        (r"\bzlib\s*\.\s*decompress\s*\(.*?(exec|eval|compile)", "فك ضغط كود مشفّر وتنفيذه مباشرة."),
        (r"\bbase64\s*\.\s*(b64decode|decodebytes)\s*\(.*?(exec|eval|compile)", "فك تشفير Base64 وتنفيذ كود مخفي."),
        (r"\bos\.system\s*\(", "محاولة تنفيذ أوامر نظام مباشرة عبر os.system."),
        (r"\bos\.popen\s*\(", "محاولة فتح أنبوب أوامر نظام عبر os.popen."),
        (r"\bshutil\.rmtree\s*\(\s*[\"']?(/|\.\.|~|[A-Za-z]:\\\\)", "محاولة حذف مسارات خارج مجلد المستخدم."),
        (r"\bctypes\b", "الوصول المباشر إلى ذاكرة النظام عبر ctypes."),
        (r"open\s*\(\s*[\"']?.*(/etc/passwd|/root/|/proc/|/var/|C:\\\\Windows)", "محاولة الوصول إلى ملفات نظام حساسة."),
        (r"rm\s+-rf\s+/", "أمر حذف خطير للنظام."),
        (r"\bsubprocess\.Popen\s*\(\s*\[\s*[\"']?rm", "محاولة تشغيل أمر حذف عبر subprocess."),
        (r"\beval\s*\(", "استخدام eval الخطير لتنفيذ نصوص برمجية."),
        (r"\bexec\s*\(", "استخدام exec الخطير لتنفيذ أكواد ديناميكية."),
    ]
    for pattern, reason in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            return False, f"تم رصد مخالفة أمنية: {reason}"
    return True, "الكود آمن"


def ban_user_for_security(uid, reason):
    uid = int(uid)
    if is_main_admin(uid) or uid <= 0:
        return
    with db_lock:
        users = read_json(USERS_DB)
        u_entry = users.get(str(uid), {"points": 0.0, "balance": 0.0, "join_date": str(datetime.now().date())})
        u_entry["is_banned"] = 1
        u_entry["ban_reason"] = reason
        users[str(uid)] = u_entry
        write_json(USERS_DB, users)

        files = read_json(FILES_DB)
        for fid in [k for k, v in files.items() if str(v.get("user_id")) == str(uid)]:
            stop_script(fid)
            for p_rem in (os.path.join(ENCRYPTED_DIR, f"{fid}.enc"), os.path.join(LOGS_DIR, f"{fid}.log")):
                try:
                    os.remove(p_rem)
                except Exception:
                    pass
            del files[fid]
        write_json(FILES_DB, files)

        try:
            shutil.rmtree(get_user_isolation_dir(uid), ignore_errors=True)
        except Exception:
            pass

        con = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False, timeout=15.0)
        try:
            con.execute(
                "INSERT INTO security_events (user_id, event_type, details, created_at) VALUES (?, ?, ?, ?)",
                (uid, "AUTO_BAN", reason, datetime.now().isoformat())
            )
            con.commit()
        finally:
            con.close()

    for adm in get_admins():
        try:
            bot.send_message(
                adm,
                f"🚫 <b>حظر أمني فوري!</b>\n\n👤 المستخدم: <code>{uid}</code>\n🛡️ السبب: <b>{escape(reason)}</b>",
                parse_mode="HTML",
                message_effect_id=FIRE_EFFECT_ID
            )
        except Exception:
            pass


# ============ أدوات النظام والمسارات والعزل ============
def _get_ipinfo():
    if _ipinfo["data"] is not None and time.time() - _ipinfo["t"] < 600:
        return _ipinfo["data"]
    data = None
    try:
        r = requests.get("http://ip-api.com/json/?fields=status,country,regionName,city,isp,query", timeout=4).json()
        if r.get("status") == "success":
            data = r
    except Exception:
        pass
    if not data:
        try:
            ip = requests.get("https://api.ipify.org", timeout=4).text.strip()
            data = {"query": ip}
        except Exception:
            data = {}
    _ipinfo.update(t=time.time(), data=data)
    return data


def _dir_size(path, limit=50000):
    total, n = 0, 0
    stack = [path]
    while stack and n < limit:
        try:
            with os.scandir(stack.pop()) as it:
                for ent in it:
                    n += 1
                    try:
                        if ent.is_symlink():
                            continue
                        if ent.is_dir(follow_symlinks=False):
                            stack.append(ent.path)
                        else:
                            total += ent.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total


def _gb(x):
    return f"{x / (1024 ** 3):.1f}"


def _mb(x):
    return f"{x / (1024 ** 2):.0f}"


def _esc(text):
    return escape(str(text))


def esc(text):
    return escape(str(text))


def get_user_isolation_dir(uid):
    uid_int = int(uid)
    if uid_int <= 0:
        raise PermissionError("معرف مستخدم غير صالح")
    folder = os.path.realpath(os.path.join(UPLOAD_DIR, str(uid_int)))
    if os.path.commonpath([UPLOAD_DIR, folder]) != UPLOAD_DIR:
        raise PermissionError("محاولة تجاوز مجلد المستخدم")
    os.makedirs(folder, exist_ok=True)
    return folder


def safe_join_user_file(user_folder, filename):
    clean = os.path.basename(str(filename))
    if not clean or clean in (".", ".."):
        raise PermissionError("اسم ملف غير مسموح")
    base_real = os.path.realpath(user_folder)
    target_real = os.path.realpath(os.path.join(base_real, clean))
    if os.path.commonpath([base_real, target_real]) != base_real:
        raise PermissionError("محاولة اختراق مسارات الملفات")
    return target_real


def generate_english_name(original_name, ext_with_dot, uid):
    ext = ext_with_dot.lower()
    if ext not in ALLOWED_SCRIPT_EXTS:
        ext = ".py"
    digest = hashlib.sha256(f"{uid}:{original_name}:{time.time_ns()}:{uuid.uuid4().hex}".encode("utf-8")).hexdigest()[:10]
    prefix = "py_app" if ext == ".py" else "js_app"
    return f"{prefix}_{digest}{ext}"


def gen_id(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def file_token(file_name):
    return hashlib.md5(str(file_name).encode("utf-8")).hexdigest()[:10]


def _get_ai_repair_file(call):
    data_parts = call.data.split("_")
    if len(data_parts) >= 3:
        owner_id = data_parts[1]
        token = data_parts[2]
        files = read_json(FILES_DB)
        for fid, f in files.items():
            if str(f.get("user_id")) == str(owner_id) and file_token(f.get("file_name", "")) == token:
                return owner_id, f.get("file_name"), fid
    return None


# ============ محرك الذكاء الاصطناعي Ptero.pro ============
def fetch_real_session(retries=2):
    for attempt in range(retries):
        session_http = requests.Session()
        headers = {
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            response = session_http.get(HOME_URL, headers=headers, timeout=25)
            if response.status_code != 200:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None

            html = response.text
            nonce = None
            patterns = [
                r"var\s+nonce\s*=\s*[\"']([a-f0-9]{8,64})[\"']",
                r"[\"']nonce[\"']\s*:\s*[\"']([a-f0-9]{8,64})[\"']",
                r"data-referral-nonce=[\"']([a-f0-9]{8,64})[\"']",
                r"x-wp-nonce[\"']?\s*[:=]\s*[\"']([a-f0-9]{8,64})[\"']",
                r"wp_nonce[\"']?\s*[:=]\s*[\"']([a-f0-9]{8,64})[\"']",
                r"mlp_nonce[\"']?\s*[:=]\s*[\"']([a-f0-9]{8,64})[\"']",
                r"data-nonce=[\"']([a-f0-9]{8,64})[\"']",
            ]
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    nonce = match.group(1)
                    break

            if not nonce:
                soup = BeautifulSoup(html, "html.parser")
                for script in soup.find_all("script"):
                    text = script.get_text() or ""
                    if "nonce" in text:
                        match = re.search(r"[\"']([a-f0-9]{10})[\"']", text)
                        if match:
                            nonce = match.group(1)
                            break

            if not nonce:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None

            guest_token = None
            for cookie in session_http.cookies:
                if any(k in cookie.name.lower() for k in ["mlp", "guest", "token"]):
                    guest_token = cookie.value
                    break

            if not guest_token:
                match = re.search(r"guest[_-]?token[\"']?\s*[:=]\s*[\"']([a-f0-9]+)[\"']", html, re.IGNORECASE)
                guest_token = match.group(1) if match else uuid.uuid4().hex

            return {
                "session": session_http,
                "nonce": nonce,
                "guest_token": guest_token,
                "conversation_id": str(uuid.uuid4()),
            }
        except Exception as ex:
            logger.warning(f"fetch_real_session error (attempt {attempt + 1}): {ex}")
            if attempt < retries - 1:
                time.sleep(1)
    return None


def chat_with_model(model_id, user_message, session_data):
    conv_id = session_data["conversation_id"]
    payload = {
        "message": user_message,
        "model": model_id,
        "conversation_id": conv_id,
        "attachments": [],
        "history": [],
        "lang": "ar",
        "github_repo": "",
        "mode": "quick",
    }
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?1",
        "x-wp-nonce": session_data["nonce"],
        "x-mlp-guest-token": session_data["guest_token"],
        "x-mlp-guest-username": f"user_{conv_id[:6]}",
        "origin": HOME_URL,
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": f"{HOME_URL}/",
        "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=1, i",
    }
    try:
        response = session_data["session"].post(
            CHAT_URL, json=payload, headers=headers, stream=True, timeout=(30, 240)
        )
        if response.status_code != 200:
            return None, None
        full_reply = ""
        for line in response.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8", errors="replace")
            if not decoded.startswith("data:"):
                continue
            data_str = decoded[5:].strip()
            if not data_str or data_str == "keepalive":
                continue
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            if "token" in data and isinstance(data["token"], str):
                full_reply += data["token"]
            elif data.get("done"):
                if data.get("conversation_id"):
                    session_data["conversation_id"] = data["conversation_id"]
                return full_reply, data
        return full_reply, None
    except requests.exceptions.RequestException as ex:
        logger.warning(f"chat_with_model request error ({model_id}): {ex}")
        return None, None


def extract_code_from_ai_response(raw_text):
    if not raw_text:
        return ""
    text = raw_text.strip()
    blocks = re.findall(r"```(?:[a-zA-Z0-9_\-\.\+]*\n)?(.*?)(?:```|$)", text, flags=re.DOTALL)
    if blocks:
        clean_blocks = [b.strip() for b in blocks if b.strip()]
        if clean_blocks:
            best_block = max(clean_blocks, key=len)
            if len(best_block) >= 15:
                return best_block
    if text.startswith("```"):
        text = re.sub(r"^```[^\n]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
        return text.strip()
    return text


def repair_source(source, instructions, file_name, model_id=None):
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise RepairServiceError("الملف أكبر من الحد المسموح لإرساله لخدمة الذكاء الاصطناعي (20 ميجابايت).")

    session_data = fetch_real_session()
    if not session_data:
        raise RepairServiceError("تعذّر الاتصال بخدمة الذكاء الاصطناعي.")

    _, ext = os.path.splitext(file_name)
    ext_lower = ext.lower()
    extra_rules = ""
    if ext_lower == ".js":
        extra_rules = "\n- حافظ على صياغة Node.js الصحيحة وتجنب إنهاء العملية بـ process.exit.\n"
    elif ext_lower == ".py":
        extra_rules = "\n- تأكد من صحة الصياغة النحوية في Python والمسافات البادئة.\n"

    prompt = (
        "أنت مبرمج محترف متخصص في تصحيح وإصلاح وتعديل ملفات الأكواد البرمجية.\n"
        "1. أعد محتوى الملف كاملاً داخل كتلة كود واحدة فقط: ``` ... ```\n"
        "2. لا تكتب أي شرح قبل أو بعد الكود.\n"
        "3. لا تضف أي أكواد ضارة أو برمجيات خبيثة.\n\n"
        f"اسم الملف: {file_name}\n"
        f"طلب المستخدم: {instructions}\n"
        f"{extra_rules}\n"
        f"محتوى الملف الحالي:\n```text\n{source}\n```"
    )

    candidate_models = []
    if model_id:
        candidate_models.append(model_id)
    if DEFAULT_MODEL_ID not in candidate_models:
        candidate_models.append(DEFAULT_MODEL_ID)
    for fm in FALLBACK_MODELS:
        if fm not in candidate_models:
            candidate_models.append(fm)

    for candidate in candidate_models:
        try:
            reply, _ = chat_with_model(candidate, prompt, session_data)
            if not reply or not reply.strip():
                session_data = fetch_real_session() or session_data
                continue
            extracted = extract_code_from_ai_response(reply)
            if not extracted or len(extracted.strip()) < 10:
                continue
            if ext_lower == ".py":
                try:
                    ast.parse(extracted, filename=file_name)
                except SyntaxError:
                    continue
            return extracted
        except Exception as ex:
            logger.warning(f"فشل النموذج {candidate}: {ex}")
            continue

    raise RepairServiceError("تعذّر الحصول على نسخة صالحة من خدمة الذكاء الاصطناعي.")


# ============ تشغيل وإيقاف السكربتات (Python و JavaScript فقط) ============
def start_script(fid):
    with process_lock:
        files = read_json(FILES_DB)
        if fid not in files:
            return False
        file_info = files[fid]
        user_id = int(file_info.get("user_id", 0))
        if not verify_file_access(fid, user_id):
            return False

        ext = str(file_info.get("ext", ".py")).lower()
        if ext not in ALLOWED_SCRIPT_EXTS:
            return False

        script_content = load_encrypted_file(fid)
        if not script_content:
            user_iso_dir = get_user_isolation_dir(user_id)
            stored_name_check = file_info.get("stored_name")
            if stored_name_check:
                candidate_p = safe_join_user_file(user_iso_dir, stored_name_check)
                if os.path.isfile(candidate_p):
                    with open(candidate_p, "r", encoding="utf-8", errors="strict") as rf:
                        script_content = rf.read()
        if not script_content:
            return False

        if fid in active_processes and active_processes[fid].poll() is None:
            return True

        try:
            user_iso_dir = get_user_isolation_dir(user_id)
            env_dir = os.path.realpath(os.path.join(ENV_DIR, str(user_id), fid))
            if os.path.commonpath([ENV_DIR, env_dir]) != ENV_DIR:
                return False
            os.makedirs(env_dir, exist_ok=True)

            stored_name = file_info.get("stored_name") or generate_english_name(
                file_info.get("file_name", f"app{ext}"), ext, user_id
            )
            env_file_path = safe_join_user_file(env_dir, stored_name)

            with open(env_file_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            for extra_rel in file_info.get("project_files", []):
                safe_extra = os.path.basename(str(extra_rel))
                if os.path.splitext(safe_extra)[1].lower() in ALLOWED_EXTRA_EXTS:
                    src_p = safe_join_user_file(user_iso_dir, safe_extra)
                    dst_p = safe_join_user_file(env_dir, safe_extra)
                    if os.path.isfile(src_p) and not os.path.islink(src_p):
                        shutil.copy2(src_p, dst_p)

            log_path = os.path.join(LOGS_DIR, f"{fid}.log")
            log_file = open(log_path, "a", encoding="utf-8")

            isolated_env = {
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "HOME": env_dir,
                "TMPDIR": env_dir,
                "PYTHONPATH": env_dir,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONDONTWRITEBYTECODE": "1",
            }

            cmd = [sys.executable, "-u", env_file_path] if ext == ".py" else ["node", env_file_path]
            popen_kwargs = {
                "stdout": log_file,
                "stderr": log_file,
                "stdin": subprocess.PIPE,
                "cwd": env_dir,
                "env": isolated_env,
            }
            if os.name == "posix":
                popen_kwargs["start_new_session"] = True

            proc = subprocess.Popen(cmd, **popen_kwargs)
            active_processes[fid] = proc
            bot_scripts[fid] = {
                "process": proc,
                "log_file": log_file,
                "file_name": file_info.get("file_name"),
                "stored_name": stored_name,
                "owner_id": user_id,
                "ext": ext,
            }
            return True
        except Exception as e:
            logger.error(f"start_script error ({fid}): {e}")
            return False


def stop_script(fid):
    with process_lock:
        if fid in active_processes:
            proc = active_processes.pop(fid)
            info = bot_scripts.pop(fid, None)
            if info and info.get("log_file"):
                try:
                    info["log_file"].close()
                except Exception:
                    pass
            try:
                if os.name == "posix":
                    os.killpg(os.getpgid(proc.pid), 9)
                else:
                    proc.terminate()
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
            return True
        bot_scripts.pop(fid, None)
        return False


def write_proc(fid, cmd):
    with process_lock:
        if fid in active_processes and active_processes[fid].poll() is None:
            try:
                proc = active_processes[fid]
                if proc.stdin:
                    proc.stdin.write(cmd.encode("utf-8") + b"\n")
                    proc.stdin.flush()
                    return True
            except Exception:
                pass
        return False


def create_zip(files_list, zip_name):
    zip_path = safe_join_user_file(DOWNLOAD_DIR, zip_name)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_path in files_list:
            if os.path.exists(file_path) and not os.path.islink(file_path):
                zipf.write(file_path, os.path.basename(file_path))
    return zip_path


# ============ تسجيل الملفات والرصيد وحسابات الويب ============
def _reserve_or_charge_points(user_id, cost, charge_immediately=True):
    with db_lock:
        if is_user_pro(user_id) or cost <= 0:
            return True, 0.0
        users = read_json(USERS_DB)
        uid_str = str(user_id)
        u = users.get(uid_str)
        if not u:
            return False, 0.0
        pts = float(u.get("points", 0.0))
        if pts < float(cost):
            return False, pts
        if charge_immediately:
            u["points"] = round(max(0.0, pts - float(cost)), 4)
            users[uid_str] = u
            write_json(USERS_DB, users)
        return True, u.get("points", pts)


def _refund_points(user_id, cost):
    with db_lock:
        if cost <= 0:
            return
        users = read_json(USERS_DB)
        uid_str = str(user_id)
        if uid_str in users:
            u = users[uid_str]
            u["points"] = round(float(u.get("points", 0.0)) + float(cost), 4)
            users[uid_str] = u
            write_json(USERS_DB, users)


def _register_pending_script(
    user_id,
    original_name,
    content_str,
    ext,
    hours,
    extra_files=None,
    charged_cost=0.0,
    auto_activate=False,
):
    with db_lock:
        fid = gen_id()
        stored_name = generate_english_name(original_name, ext, user_id)
        if not save_encrypted_file(fid, content_str, user_id):
            return None, None

        user_dir = get_user_isolation_dir(user_id)
        stored_path = safe_join_user_file(user_dir, stored_name)
        with open(stored_path, "w", encoding="utf-8") as f:
            f.write(content_str)

        saved_extras = []
        for ef_name, ef_bytes in (extra_files or []):
            safe_ef_name = os.path.basename(str(ef_name))
            ef_ext = os.path.splitext(safe_ef_name)[1].lower()
            if ef_ext in ALLOWED_EXTRA_EXTS:
                ef_path = safe_join_user_file(user_dir, safe_ef_name)
                with open(ef_path, "wb") as f:
                    f.write(ef_bytes)
                saved_extras.append(safe_ef_name)

        files = read_json(FILES_DB)
        files[fid] = {
            "user_id": int(user_id),
            "file_name": original_name,
            "stored_name": stored_name,
            "ext": ext,
            "type": "free" if not is_user_pro(user_id) else "pro",
            "status": "active" if auto_activate else "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hours": int(hours),
            "charged_cost": float(charged_cost),
            "addons": [],
            "project_files": saved_extras,
        }
        write_json(FILES_DB, files)

    if auto_activate:
        start_script(fid)
        return fid, stored_name

    for adm in get_admins():
        try:
            admin_kb = build_keyboard([
                [
                    {"text": "📥 تحميل الملف", "callback_data": f"vdl_{fid}", "style": "primary"},
                    {"text": "✅ موافقة ✅", "callback_data": f"vapprove_{fid}", "style": "success"},
                ],
                [{"text": "❌ رفض ❌", "callback_data": f"vdel_{fid}", "style": "danger"}],
            ])
            bot.send_message(
                adm,
                f"📤 <b>طلب رفع ملف جديد ({escape(ext)}) معلق للمراجعة — {escape(PAGE_BRAND_NAME)}:</b>\n\n"
                f"📄 الاسم الأصلي: <code>{escape(original_name)}</code>\n"
                f"🔤 الاسم الإنجليزي: <code>{escape(stored_name)}</code>\n"
                f"👤 الآيدي: <code>{user_id}</code>\n"
                f"⏰ الساعات: {hours}",
                parse_mode="HTML",
                reply_markup=admin_kb,
                message_effect_id=FIRE_EFFECT_ID
            )
        except Exception as e:
            logger.error(f"Admin notify error: {e}")

    return fid, stored_name


def parse_and_validate_zip_bytes(raw_zip_bytes, uid):
    extract_dir = tempfile.mkdtemp(prefix=f"zip_{uid}_")
    extract_real = os.path.realpath(extract_dir)
    zip_temp_path = os.path.join(extract_real, "upload.zip")
    try:
        with open(zip_temp_path, "wb") as f:
            f.write(raw_zip_bytes)

        script_candidates = []
        extra_files = []

        with zipfile.ZipFile(zip_temp_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    return False, "محاولة رفع رابط رمزي داخل ملف ZIP", None, None
                target_p = os.path.realpath(os.path.join(extract_real, member.filename))
                if os.path.commonpath([extract_real, target_p]) != extract_real:
                    return False, "محاولة اختراق مسارات ZIP Slip", None, None
                if member.is_dir():
                    continue
                m_ext = os.path.splitext(member.filename)[1].lower()
                if m_ext not in ALLOWED_EXTRA_EXTS:
                    return False, f"ملف غير مسموح داخل ZIP: {member.filename}", None, None
                raw_m = zip_ref.read(member.filename)
                if m_ext in ALLOWED_SCRIPT_EXTS:
                    try:
                        text_m = raw_m.decode("utf-8")
                    except UnicodeDecodeError:
                        return False, f"ملف برمجي غير صالح أو مشفّر داخل ZIP: {member.filename}", None, None
                    is_safe, sec_msg = scan_code_security(text_m, strict_text=True)
                    if not is_safe:
                        return False, f"كود مشفّر/مخالف داخل ZIP ({member.filename}): {sec_msg}", None, None
                    script_candidates.append((os.path.basename(member.filename), text_m, m_ext))
                else:
                    extra_files.append((os.path.basename(member.filename), raw_m))

        if not script_candidates:
            return False, "الأرشيف لا يحتوي على أي ملفات .py أو .js صالحة!", None, None

        main_item = script_candidates[0]
        for cand in script_candidates:
            if cand[0].lower() in ("main.py", "bot.py", "app.py", "index.js", "main.js", "bot.js"):
                main_item = cand
                break

        return True, None, main_item, extra_files
    finally:
        shutil.rmtree(extract_real, ignore_errors=True)


# ============ حسابات الويب ============
def ensure_default_web_accounts():
    with db_lock:
        accounts = read_json(WEB_USERS_DB)
        changed = False
        default_admin_user = os.environ.get("WEB_ADMIN_USERNAME", "yemen_admin").strip().lower()
        default_admin_pass = os.environ.get("WEB_ADMIN_PASSWORD", "Yemen@2026")
        if default_admin_user not in accounts:
            accounts[default_admin_user] = {
                "username": default_admin_user,
                "display_name": f"مدير {PAGE_BRAND_NAME}",
                "telegram_id": OWNER_ID or ADMIN_ID or 1002670694,
                "role": "admin",
                "password_hash": generate_password_hash(default_admin_pass),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            changed = True
        if changed:
            write_json(WEB_USERS_DB, accounts)


def register_web_account(username, password, display_name="", telegram_id=0):
    clean_user = re.sub(r"[^a-zA-Z0-9_.-]", "", (username or "").strip().lower())
    if len(clean_user) < 3:
        return False, "اسم المستخدم يجب أن يكون 3 أحرف إنجليزية أو أرقام على الأقل."
    if not password or len(password) < 6:
        return False, "كلمة المرور يجب أن تكون 6 أحرف على الأقل."

    parsed_tg = _parse_id(telegram_id, 0)
    if parsed_tg <= 0:
        parsed_tg = int(time.time()) % 900000000 + 100000000

    with db_lock:
        accounts = read_json(WEB_USERS_DB)
        if clean_user in accounts:
            return False, "اسم المستخدم مسجل مسبقاً في منصة ابن اليمن."

        accounts[clean_user] = {
            "username": clean_user,
            "display_name": (display_name or clean_user).strip()[:60],
            "telegram_id": parsed_tg,
            "role": "admin" if is_admin(parsed_tg) else "user",
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        write_json(WEB_USERS_DB, accounts)

        users = read_json(USERS_DB)
        tg_str = str(parsed_tg)
        if tg_str not in users:
            users[tg_str] = {
                "username": clean_user,
                "first_name": (display_name or clean_user).strip()[:60],
                "last_name": "",
                "points": 25.0,
                "balance": 25.0,
                "join_date": str(datetime.now().date()),
                "is_banned": 0,
                "expiry": None,
                "notifications": True,
            }
            write_json(USERS_DB, users)

    return True, accounts[clean_user]


def authenticate_web_account(username, password):
    clean_user = (username or "").strip().lower()
    if not clean_user or not password:
        return None
    accounts = read_json(WEB_USERS_DB)
    acc = accounts.get(clean_user)
    if not acc:
        return None
    if check_password_hash(acc.get("password_hash", ""), password):
        users = read_json(USERS_DB)
        if users.get(str(acc.get("telegram_id")), {}).get("is_banned", 0) == 1:
            return {"banned": True}
        return acc
    return None


def get_current_web_user():
    uname = session.get("web_user")
    if not uname:
        return None
    accounts = read_json(WEB_USERS_DB)
    acc = accounts.get(uname)
    if not acc:
        session.pop("web_user", None)
        return None
    users = read_json(USERS_DB)
    if users.get(str(acc.get("telegram_id")), {}).get("is_banned", 0) == 1:
        session.pop("web_user", None)
        return None
    return acc


def web_login_required(api_mode=False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            acc = get_current_web_user()
            if not acc:
                if api_mode:
                    return jsonify({"ok": False, "error": "يرجى تسجيل الدخول أولاً في منصة ابن اليمن."}), 401
                return redirect(url_for("login_page"))
            return fn(acc, *args, **kwargs)
        return wrapper
    return decorator


# ============ دوال التاريخ والرسائل والأزرار ============
def day_name():
    ds = ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    return ds[int(datetime.now().strftime("%w"))]


def month_name():
    month_n = [
        "فارغ", "يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو",
        "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"
    ]
    return month_n[int(datetime.now().strftime("%m"))]


def get_date_strings():
    now = datetime.now()
    tim1 = now.strftime("%H:%M:%S")
    ampm = now.strftime("%p").lower()
    e_ar = "مسائاً" if ampm == "pm" else "صباحاً"
    y = now.strftime("%Y")
    m = now.strftime("%m")
    d = now.strftime("%d")
    dy = day_name()
    mh = month_name()
    day2 = f"{dy} {d} {mh} {y} | {tim1} {e_ar}"
    day3 = f"{d}-{m}-{y} | {tim1} {e_ar}"
    return day2, day3


def deco(title, content, first="مستخدم"):
    return f"<blockquote><b>{content}</b></blockquote>\n\n"


def delete_last_message(chat_id):
    with state_lock:
        mid = last_bot_messages.get(chat_id)
    if mid:
        try:
            bot.delete_message(chat_id, mid)
        except Exception:
            pass


def save_message(chat_id, msg_id):
    with state_lock:
        last_bot_messages[chat_id] = msg_id


def send_msg(chat_id, text, markup=None, effect_id=FIRE_EFFECT_ID):
    delete_last_message(chat_id)
    settings = get_settings()
    try:
        if settings.get("bot_image"):
            msg = bot.send_photo(
                chat_id, settings["bot_image"], caption=text,
                parse_mode="HTML", reply_markup=markup, message_effect_id=effect_id
            )
        else:
            msg = bot.send_message(
                chat_id, text, parse_mode="HTML",
                reply_markup=markup, message_effect_id=effect_id
            )
        save_message(chat_id, msg.message_id)
        return msg
    except Exception:
        msg = bot.send_message(
            chat_id, text, parse_mode="HTML",
            reply_markup=markup, message_effect_id=effect_id
        )
        save_message(chat_id, msg.message_id)
        return msg


def edit_msg(call, text, markup):
    try:
        if call.message.content_type == "photo":
            bot.edit_message_caption(
                text[:4096], call.message.chat.id, call.message.message_id,
                parse_mode="HTML", reply_markup=markup
            )
        else:
            bot.edit_message_text(
                text[:4096], call.message.chat.id, call.message.message_id,
                parse_mode="HTML", reply_markup=markup
            )
        save_message(call.message.chat.id, call.message.message_id)
    except Exception:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_msg(call.message.chat.id, text[:4096], markup, effect_id=FIRE_EFFECT_ID)


def del_msg(chat_id, *msg_ids):
    for m_id in msg_ids:
        try:
            bot.delete_message(chat_id, m_id)
        except Exception:
            pass


def btn(text, callback_data=None, url=None, style=None):
    kw = {}
    if callback_data:
        kw["callback_data"] = callback_data
    if url:
        kw["url"] = url
    if style:
        kw["style"] = style
    try:
        return types.InlineKeyboardButton(text, **kw)
    except TypeError:
        kw.pop("style", None)
        return types.InlineKeyboardButton(text, **kw)


def build_keyboard(menu_structure):
    markup = types.InlineKeyboardMarkup()
    for row in menu_structure:
        row_btns = []
        for btn_dict in row:
            text = btn_dict.get("text")
            callback_data = btn_dict.get("callback_data")
            url = btn_dict.get("url")
            style = btn_dict.get("style", "primary")
            icon_emoji = btn_dict.get("icon_custom_emoji_id")
            kw = {}
            if style:
                kw["style"] = style
            if icon_emoji:
                kw["icon_custom_emoji_id"] = icon_emoji
            try:
                if url:
                    b = types.InlineKeyboardButton(text, url=url, **kw)
                else:
                    b = types.InlineKeyboardButton(text, callback_data=callback_data, **kw)
            except TypeError:
                kw.pop("style", None)
                kw.pop("icon_custom_emoji_id", None)
                if url:
                    b = types.InlineKeyboardButton(text, url=url, **kw)
                else:
                    b = types.InlineKeyboardButton(text, callback_data=callback_data, **kw)
            row_btns.append(b)
        markup.row(*row_btns)
    return markup


def is_user_pro(uid):
    if is_admin(uid):
        return True
    with db_lock:
        users = read_json(USERS_DB)
        u = users.get(str(uid), {})
        expiry = u.get("expiry")
        if not expiry or expiry == "null":
            return False
        if expiry in ("LIFETIME", 0, "0"):
            return True
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < exp_date:
                return True
            u["expiry"] = None
            users[str(uid)] = u
            write_json(USERS_DB, users)
            return False
        except Exception:
            return False


def main_kb(uid):
    structure = [
        [
            {"text": "📤 رفع ملف (.py / .js)", "callback_data": "nav_upload", "style": "success"},
            {"text": "📦 رفع ملف مضغوط (.zip)", "callback_data": "nav_upload_zip", "style": "success"},
        ],
        [{"text": f"🌐 صفحة {PAGE_BRAND_NAME}", "callback_data": "nav_web_portal", "style": "primary"}],
        [{"text": "💻 حالة ونظام السيرفر", "callback_data": "admin_system_status", "style": "primary"}],
        [{"text": "📜 الشروط والتعليمات", "callback_data": "ehab_5_e", "style": "danger"}],
        [
            {"text": "📁 ملفاتي", "callback_data": "nav_files", "style": "primary"},
            {"text": "🛒 المتجر", "callback_data": "nav_store", "style": "primary"},
        ],
        [
            {"text": "💼 محفظتي", "callback_data": "nav_wallet", "style": "primary"},
            {"text": "📊 حسابي", "callback_data": "nav_stats", "style": "primary"},
        ],
        [
            {"text": "🛠 تثبيت مكتبة", "callback_data": "nav_lib", "style": "primary"},
            {"text": "📖 التعليمات", "callback_data": "nav_help", "style": "primary"},
        ],
    ]
    if is_user_pro(uid):
        structure.append([{"text": "🔧 لوحة Pro", "callback_data": "nav_pro", "style": "success"}])
    structure.append([{"text": "👨‍💻 تواصل مع المطور", "url": DEV_TELEGRAM, "style": "primary"}])
    if is_admin(uid):
        structure.append([{"text": "⚙️ لوحة الإدارة", "callback_data": "nav_admin", "style": "danger"}])
    return build_keyboard(structure)


def pro_panel_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(btn("📥 تحميل جميع الملفات", callback_data="pro_download_all", style="success"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
    return kb


def cancel_kb(data="cancel"):
    kb = types.InlineKeyboardMarkup()
    kb.add(btn("❌ إلغاء", callback_data=data, style="danger"))
    return kb


def back_kb(data="nav_main"):
    kb = types.InlineKeyboardMarkup()
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data=data, style="primary"))
    return kb


def locked_msg(chat_id):
    text = "🔒 <b>البوت مغلق حالياً للصيانة</b>\n\nتم إيقاف الخدمة مؤقتاً بأمر من الإدارة."
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("👨‍💻 تواصل مع المطور", url=DEV_TELEGRAM, style="primary"))
    send_msg(chat_id, deco("🔒 البوت مغلق", text), markup, effect_id=FIRE_EFFECT_ID)


def check_sub(user_id):
    if is_admin(user_id):
        return True
    channels = get_settings().get("channels", [])
    if not channels:
        return True
    try:
        for ch in channels:
            member = bot.get_chat_member(ch["username"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except Exception:
        return True


def set_cancel(uid, state=True):
    with state_lock:
        cancel_states[uid] = state


def is_cancelled(uid):
    with state_lock:
        return cancel_states.get(uid, False)


def clear_cancel(uid):
    with state_lock:
        cancel_states.pop(uid, None)


def get_thumb():
    thumb = get_settings().get("file_thumb")
    if thumb and os.path.exists(thumb):
        return thumb
    return None


# ============ شاشات النظام والإدارة ============
def handle_admin_system(call):
    uid = call.from_user.id
    if not is_admin(uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)

    try:
        per = psutil.cpu_percent(interval=0.4, percpu=True)
        cpu_total = sum(per) / max(1, len(per))
        cores_line = " ".join(f"{p:.0f}%" for p in per) if len(per) <= 16 else f"{len(per)} نواة"
    except Exception:
        cpu_total = 0.0
        cores_line = "غير متاح"

    logical = psutil.cpu_count(logical=True) or 1
    physical = psutil.cpu_count(logical=False) or logical
    try:
        freq = psutil.cpu_freq()
        freq_s = f"{freq.current:.0f} MHz" if freq else "—"
    except Exception:
        freq_s = "—"
    try:
        load = " / ".join(f"{x:.2f}" for x in os.getloadavg())
    except Exception:
        load = "—"

    mem = psutil.virtual_memory()
    sw = psutil.swap_memory()
    try:
        disk = psutil.disk_usage(BASE_DIR)
    except Exception:
        disk = psutil.disk_usage("/")

    users_size = _dir_size(UPLOAD_DIR)
    proc = psutil.Process()
    ip = _get_ipinfo()
    place = " - ".join(x for x in (ip.get("country"), ip.get("regionName"), ip.get("city")) if x) or "غير متاح"
    uname = platform.uname()
    try:
        boot = datetime.now() - datetime.fromtimestamp(proc.create_time())
        boot_str = str(boot).split(".")[0]
    except Exception:
        boot_str = "مستمر"

    text = (
        f"<blockquote>💻 <b>معلومات النظام والسيرفر ({escape(PAGE_BRAND_NAME)})</b></blockquote>\n\n"
        f"<blockquote>"
        f"🌍 <b>الموقع:</b> {_esc(place)}\n"
        f"🌐 <b>IP:</b> <code>{_esc(str(ip.get('query', 'غير متاح')))}</code>\n"
        f"🏢 <b>المزود:</b> {_esc(str(ip.get('isp', '—')))}"
        f"</blockquote>\n\n"
        f"<blockquote>"
        f"🧠 <b>CPU:</b> {cpu_total:.0f}% | {freq_s}\n"
        f"⚙️ <b>Cores:</b> {physical} فعلي / {logical} منطقي\n"
        f"📊 <b>الأنوية:</b> {cores_line}\n"
        f"📈 <b>Load:</b> {load}"
        f"</blockquote>\n\n"
        f"<blockquote>"
        f"💾 <b>RAM:</b> {_gb(mem.used)}/{_gb(mem.total)} GB ({mem.percent}%)\n"
        f"✅ <b>متاح:</b> {_gb(mem.available)} GB\n"
        f"🔁 <b>Swap:</b> {_gb(sw.used)}/{_gb(sw.total)} GB"
        f"</blockquote>\n\n"
        f"<blockquote>"
        f"💽 <b>التخزين:</b> {_gb(disk.used)}/{_gb(disk.total)} GB ({disk.percent}%)\n"
        f"🆓 <b>فاضي:</b> {_gb(disk.free)} GB\n"
        f"📁 <b>ملفات المستخدمين:</b> {_mb(users_size)} MB"
        f"</blockquote>\n\n"
        f"<blockquote>"
        f"🤖 <b>البوت:</b> {_mb(proc.memory_info().rss)} MB | {proc.num_threads()} thread\n"
        f"▶️ <b>سكربتات شغالة:</b> {len(bot_scripts)}\n"
        f"⏱ <b>تشغيل البوت:</b> {boot_str}\n"
        f"🖥 <b>OS:</b> {uname.system} {uname.release} | Python {platform.python_version()}"
        f"</blockquote>"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("🧹 تنظيف الرامات", callback_data="sys_clean_ram", style="success"),
        btn("🗑 تنظيف المؤقتات", callback_data="sys_clean_tmp", style="success"),
    )
    kb.add(
        btn("📜 تنظيف اللوجات", callback_data="sys_clean_logs", style="primary"),
        btn("📈 استهلاك الرامات (Top)", callback_data="sys_top", style="primary"),
    )
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="danger"))
    edit_msg(call, text, kb)


def handle_sys_clean_ram(call):
    if not is_admin(call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    for _ in range(3):
        gc.collect()
    bot.answer_callback_query(call.id, "✅ تم تنظيف الرامات بنجاح!", show_alert=True)
    handle_admin_system(call)


def handle_sys_clean_tmp(call):
    if not is_admin(call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    freed, count = 0, 0
    cutoff = time.time() - 3600
    tmpdir = tempfile.gettempdir()
    try:
        for name in os.listdir(tmpdir):
            p = os.path.join(tmpdir, name)
            try:
                st = os.lstat(p)
                if st.st_mtime > cutoff or os.path.islink(p):
                    continue
                size = _dir_size(p) if os.path.isdir(p) else st.st_size
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
                freed += size
                count += 1
            except OSError:
                pass
    except OSError:
        pass
    bot.answer_callback_query(call.id, f"🗑 تم تحرير {_mb(freed)} MB ({count} عنصر)!", show_alert=True)
    handle_admin_system(call)


def handle_sys_clean_logs(call):
    if not is_admin(call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    count = 0
    limit = MAX_LOG_SIZE_KB * 1024
    try:
        for name in os.listdir(LOGS_DIR):
            fid = os.path.splitext(name)[0]
            if fid in active_processes:
                continue
            p = os.path.join(LOGS_DIR, name)
            if os.path.isfile(p) and not os.path.islink(p) and os.path.getsize(p) > limit:
                os.remove(p)
                count += 1
    except OSError:
        pass
    bot.answer_callback_query(call.id, f"📜 تم تنظيف {count} ملف لوج بنجاح!", show_alert=True)
    handle_admin_system(call)


def handle_sys_top(call):
    if not is_admin(call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    by_pid = {}
    with process_lock:
        for info in list(bot_scripts.values()):
            p = info.get("process")
            if p is not None and hasattr(p, "pid"):
                by_pid[p.pid] = info
    rows = []
    try:
        me = psutil.Process()
        for pr in [me] + me.children(recursive=True):
            try:
                rows.append((pr.memory_info().rss, pr.pid, pr.cpu_percent(interval=None)))
            except psutil.Error:
                pass
    except Exception:
        pass
    rows.sort(reverse=True)
    lines = []
    for rss, pid, _ in rows[:8]:
        if pid == os.getpid():
            who = "🤖 البوت نفسه"
        elif pid in by_pid:
            inf = by_pid[pid]
            who = f"📄 {_esc(str(inf.get('file_name')))} (<code>{inf.get('owner_id')}</code>)"
        else:
            who = f"⚙️ PID {pid}"
        lines.append(f"{who} — <b>{_mb(rss)} MB</b>")
    body = "\n".join(lines) if lines else "لا توجد بيانات"
    kb = types.InlineKeyboardMarkup()
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="admin_system_status", style="danger"))
    edit_msg(call, f"📈 <b>أكبر استهلاك للرامات:</b>\n\n{body}", kb)


# ============ الأوامر ومعالجة الملفات (.py, .js, .zip فقط) ============
@bot.message_handler(commands=["start", "admin"])
def start_cmd(msg):
    try:
        uid = msg.from_user.id
        users = read_json(USERS_DB)
        first_name_raw = msg.from_user.first_name or "مستخدم"

        if users.get(str(uid), {}).get("is_banned", 0) == 1:
            return bot.send_message(
                msg.chat.id,
                deco("🚫 محظور", "عذراً، تم حظرك نهائياً من استخدام البوت.", first_name_raw),
                message_effect_id=FIRE_EFFECT_ID
            )

        if is_bot_locked() and not is_admin(uid):
            try:
                bot.delete_message(msg.chat.id, msg.message_id)
            except Exception:
                pass
            locked_msg(msg.chat.id)
            return

        clear_cancel(uid)
        if str(uid) not in users:
            with db_lock:
                users = read_json(USERS_DB)
                users[str(uid)] = {
                    "username": msg.from_user.username,
                    "first_name": first_name_raw,
                    "last_name": msg.from_user.last_name,
                    "points": 10.0,
                    "balance": 10.0,
                    "join_date": str(datetime.now().date()),
                    "is_banned": 0,
                    "expiry": None,
                    "notifications": True,
                }
                write_json(USERS_DB, users)
            try:
                first = esc(f"{first_name_raw} {msg.from_user.last_name or ''}".strip())
                user = msg.from_user.username or "لا يوجد"
                day2, _ = get_date_strings()
                cap = (
                    f"➖ <b>تم دخول شخص جديد الى {escape(PAGE_BRAND_NAME)} 👤•</b>\n"
                    f"➖ <b>إسم الشخص:</b> <a href=\"tg://user?id={uid}\">{first}</a> 📝•\n"
                    f"➖ <b>الحالة :</b> تم التحقق وليس روبوت ✅️ •\n"
                    f"➖ <b>ايديه :</b> <code>{uid}</code> 🆔️•\n"
                    f"➖ <b>معرف حسابه :</b> @{user} 📮•\n\n"
                    f"➖➖➖➖➖➖\n📆 - {day2}"
                )
                structure = [[{"text": "👤 كشف العضو", "url": f"tg://openmessage?user_id={uid}", "style": "primary"}]]
                if CHANNEL_EHAB_ME:
                    bot.send_message(
                        CHANNEL_EHAB_ME, cap, parse_mode="HTML",
                        reply_markup=build_keyboard(structure), message_effect_id=FIRE_EFFECT_ID
                    )
            except Exception:
                pass

        if not check_sub(uid):
            return sub_msg(msg.chat.id)

        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except Exception:
            pass

        u = users.get(str(uid), {})
        text = (
            "<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n"
            f"<b>   🌟 أهلاً بك عزيزي في {escape(PAGE_BRAND_NAME)} ⦗ {escape(first_name_raw)} ⦘ 🌟   </b>\n"
            "<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n\n"
            f"<b>💌 ︙ ايدي المستخدم : <code>{msg.chat.id}</code></b>\n"
            f"<b>💰 ︙ رصيدك المالي : <tg-spoiler>{u.get('balance', 0.0)}</tg-spoiler> ₽</b>\n"
            "<b>🚀 ︙ سرعة الاستضافة : فائقة </b>\n\n"
            "<b>💻 ︙ تحكم الآن بكافة الأقسام عبر الأزرار أدناه 👇</b>"
        )
        send_msg(msg.chat.id, deco("🏠 القائمة الرئيسية", text, first_name_raw), main_kb(uid), effect_id=FIRE_EFFECT_ID)
    except Exception as e:
        logger.error(f"Start Error: {e}")


def sub_msg(chat_id):
    channels = get_settings().get("channels", [])
    if not channels:
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        uname = ch["username"].replace("@", "")
        kb.add(btn(f"📢 {ch['name']}", url=f"[https://t.me/](https://t.me/){uname}", style="primary"))
    kb.add(btn("✅ تحقق من الاشتراك", callback_data="check_sub", style="success"))
    send_msg(
        chat_id,
        deco("🔔 اشتراك مطلوب", "🔔 <b>اشتراك إجباري مطلوب</b>\n\nيجب عليك الاشتراك في القنوات التالية لاستخدام البوت:"),
        kb,
        effect_id=FIRE_EFFECT_ID
    )


def upload_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"

    if not msg.document or not msg.document.file_name:
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب إرسال ملف بصيغة .py أو .js فقط.", first_name_raw), back_kb("nav_upload"), effect_id=FIRE_EFFECT_ID)
        return

    fn = msg.document.file_name
    ext = os.path.splitext(fn)[1].lower()
    if ext not in ALLOWED_SCRIPT_EXTS:
        ban_user_for_security(uid, f"محاولة رفع امتداد غير مسموح: {fn}")
        send_msg(msg.chat.id, deco("🚫 حظر فوري", "يُسمح فقط بملفات البايثون (.py) وجافا سكريبت (.js) والملفات المضغوطة (.zip). تم حظرك تلقائياً.", first_name_raw), effect_id=FIRE_EFFECT_ID)
        return

    if msg.document.file_size and msg.document.file_size > MAX_FILE_SIZE:
        send_msg(msg.chat.id, deco("❌ خطأ", "حجم الملف يتجاوز 20 ميجابايت.", first_name_raw), back_kb("nav_upload"), effect_id=FIRE_EFFECT_ID)
        return

    try:
        finfo = bot.get_file(msg.document.file_id)
        raw_bytes = bot.download_file(finfo.file_path)
        file_content = raw_bytes.decode("utf-8")
        is_safe, sec_msg = scan_code_security(file_content, strict_text=True)
        if not is_safe:
            ban_user_for_security(uid, f"رفع ملف مشفّر أو مخالف ({fn}): {sec_msg}")
            send_msg(msg.chat.id, deco("🚫 حظر تلقائي للمخالفة", f"{sec_msg}\n\nتم حظرك فوراً وحذف ملفاتك.", first_name_raw), effect_id=FIRE_EFFECT_ID)
            return
    except Exception as e:
        ban_user_for_security(uid, f"ملف غير نصي أو مشفّر ({fn}): {e}")
        send_msg(msg.chat.id, deco("🚫 حظر فوري", "تم رفض الملف وحظرك لوجود محتوى مشفّر أو غير صالح.", first_name_raw), effect_id=FIRE_EFFECT_ID)
        return

    users = read_json(USERS_DB)
    pts = float(users.get(str(uid), {}).get("points", 0.0))
    required_price = float(get_settings().get("python_upload_price", 1.0))
    if pts < required_price and not is_user_pro(uid):
        send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"رصيدك الحالي لا يكفي! السعر المطلوب: {required_price} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
        return

    m = send_msg(
        msg.chat.id,
        deco("⏰ تحديد الساعات", f"الملف: <b>{escape(fn)}</b> ({ext})\n\n💰 رصيدك: <code>{pts}</code> نقطة\n💵 السعر: {required_price} نقطة / ساعة\n\nأرسل عدد الساعات المطلوبة للتشغيل:", first_name_raw),
        cancel_kb(),
        effect_id=FIRE_EFFECT_ID
    )
    save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, hours_step, fn, file_content, ext, m.message_id)


def hours_step(msg, original_name, file_content, ext, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "أرسل رقماً صحيحاً للساعات!", first_name_raw), back_kb("nav_upload"), effect_id=FIRE_EFFECT_ID)
        return
    hours = int(msg.text.strip())
    if hours < 1:
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب اختيار ساعة واحدة على الأقل!", first_name_raw), back_kb("nav_upload"), effect_id=FIRE_EFFECT_ID)
        return

    required_price = float(get_settings().get("python_upload_price", 1.0))
    total_cost = round(required_price * hours, 4)
    ok, current_pts = _reserve_or_charge_points(uid, total_cost, charge_immediately=True)
    if not ok:
        send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"تحتاج إلى {total_cost} نقطة، ورصيدك الحالي {current_pts} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
        return

    fid, stored_name = _register_pending_script(
        uid, original_name, file_content, ext, hours, charged_cost=total_cost
    )
    if not fid:
        _refund_points(uid, total_cost)
        send_msg(uid, deco("❌ خطأ", "فشل حفظ وتشفير الملف!"), effect_id=FIRE_EFFECT_ID)
        return
    send_msg(
        uid,
        deco("⏳ قيد المراجعة", f"تم رفع الملف وتسميته إنجليزياً: <code>{stored_name}</code>\n⏰ الساعات: {hours}\n💳 النقاط المخصومة: {total_cost if not is_user_pro(uid) else 0}\nبانتظار موافقة الإدارة."),
        back_kb(),
        effect_id=FIRE_EFFECT_ID
    )


def upload_zip_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.document or not msg.document.file_name.lower().endswith(".zip"):
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب إرسال ملف مضغوط بصيغة .zip فقط.", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
        return

    if msg.document.file_size and msg.document.file_size > MAX_FILE_SIZE:
        send_msg(msg.chat.id, deco("❌ خطأ", "حجم الأرشيف يتجاوز 20 ميجابايت.", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
        return

    zip_filename = msg.document.file_name
    try:
        finfo = bot.get_file(msg.document.file_id)
        downloaded_file = bot.download_file(finfo.file_path)
        ok_zip, reason_zip, main_item, extra_files = parse_and_validate_zip_bytes(downloaded_file, uid)
        if not ok_zip:
            if reason_zip and ("رمز" in reason_zip or "Slip" in reason_zip or "مشفّر" in reason_zip or "غير مسموح" in reason_zip):
                ban_user_for_security(uid, reason_zip)
                send_msg(msg.chat.id, deco("🚫 حظر فوري", f"{reason_zip}\n\nتم حظرك تلقائياً.", first_name_raw), effect_id=FIRE_EFFECT_ID)
            else:
                send_msg(msg.chat.id, deco("❌ خطأ", reason_zip or "تعذر قراءة الأرشيف.", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
            return

        main_name, main_content, main_ext = main_item
        users = read_json(USERS_DB)
        pts = float(users.get(str(uid), {}).get("points", 0.0))
        required_price = float(get_settings().get("python_upload_price", 1.0))
        if pts < required_price and not is_user_pro(uid):
            send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"رصيدك لا يكفي لرفع ZIP! السعر المطلوب: {required_price} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
            return

        m = send_msg(
            msg.chat.id,
            deco("⏰ تحديد الساعات لملف ZIP", f"الأرشيف: <b>{escape(zip_filename)}</b>\nالملف الرئيسي: <code>{escape(main_name)}</code> ({main_ext})\n\nأرسل عدد الساعات المطلوبة للتشغيل:", first_name_raw),
            cancel_kb(),
            effect_id=FIRE_EFFECT_ID
        )
        save_message(msg.chat.id, m.message_id)
        bot.register_next_step_handler(m, hours_zip_step, f"{zip_filename} ({main_name})", main_content, main_ext, extra_files, m.message_id)
    except Exception as e:
        logger.error(f"ZIP Upload error: {e}")
        send_msg(msg.chat.id, deco("❌ خطأ", f"تعذر معالجة ملف ZIP: {e}", first_name_raw), back_kb("nav_main"), effect_id=FIRE_EFFECT_ID)


def hours_zip_step(msg, display_name, main_content, main_ext, extra_files, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "أرسل رقماً صحيحاً للساعات!", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
        return
    hours = int(msg.text.strip())
    if hours < 1:
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب اختيار ساعة واحدة على الأقل!", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
        return

    required_price = float(get_settings().get("python_upload_price", 1.0))
    total_cost = round(required_price * hours, 4)
    ok, current_pts = _reserve_or_charge_points(uid, total_cost, charge_immediately=True)
    if not ok:
        send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"تحتاج إلى {total_cost} نقطة، ورصيدك الحالي {current_pts} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
        return

    fid, stored_name = _register_pending_script(
        uid, display_name, main_content, main_ext, hours, extra_files=extra_files, charged_cost=total_cost
    )
    if not fid:
        _refund_points(uid, total_cost)
        send_msg(uid, deco("❌ خطأ", "فشل حفظ وتشفير ملف المشروع!"), effect_id=FIRE_EFFECT_ID)
        return
    send_msg(
        uid,
        deco("⏳ قيد المراجعة", f"تم تجهيز الأرشيف بالاسم الإنجليزي: <code>{stored_name}</code>\n⏰ الساعات: {hours}\n💳 النقاط المخصومة: {total_cost if not is_user_pro(uid) else 0}\nبانتظار موافقة الإدارة."),
        back_kb(),
        effect_id=FIRE_EFFECT_ID
    )


# ============ مسارات الاستدعاءات والأزرار ============
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    try:
        uid = call.from_user.id
        cid = call.message.chat.id
        data = call.data
        users = read_json(USERS_DB)
        first_name_raw = call.from_user.first_name or "مستخدم"

        if users.get(str(uid), {}).get("is_banned", 0) == 1:
            return bot.answer_callback_query(call.id, "🚫 أنت محظور نهائياً من استخدام البوت!", show_alert=True)

        if is_bot_locked() and not is_admin(uid):
            bot.answer_callback_query(call.id, "🔒 البوت مغلق حالياً للصيانة!", show_alert=True)
            locked_msg(cid)
            return

        if data in ("cancel", "user_home", "nav_main"):
            set_cancel(uid, True)
            bot.answer_callback_query(call.id, "✅ تم العودة للقائمة.")
            u = users.get(str(uid), {})
            text = (
                "<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n"
                f"<b>   🌟 أهلاً بك عزيزي في {escape(PAGE_BRAND_NAME)} ⦗ {escape(first_name_raw)} ⦘ 🌟   </b>\n"
                "<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n\n"
                f"<b>💌 ︙ ايدي المستخدم : <code>{cid}</code></b>\n"
                f"<b>💰 ︙ رصيدك المالي : <tg-spoiler>{u.get('balance', 0.0)}</tg-spoiler> ₽</b>\n"
                "<b>🚀 ︙ سرعة الاستضافة : فائقة </b>\n\n"
                "<b>💻 ︙ تحكم الآن بكافة الأقسام عبر الأزرار أدناه 👇</b>"
            )
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            send_msg(cid, deco("🏠 القائمة الرئيسية", text, first_name_raw), main_kb(uid), effect_id=FIRE_EFFECT_ID)
            return

        if data == "nav_web_portal":
            port_val = os.environ.get("PORT", "8080")
            base_url = os.environ.get("PUBLIC_SERVER_URL", f"[http://127.0.0.1](http://127.0.0.1):{port_val}").rstrip("/")
            info_txt = (
                f"🌐 <b>منصة {escape(PAGE_BRAND_NAME)} السحابية</b>\n\n"
                f"• رابط لوحة وصفحة {escape(PAGE_BRAND_NAME)}: <code>{escape(base_url)}/</code>\n"
                f"• صفحة تسجيل الدخول وإنشاء حساب: <code>{escape(base_url)}/login</code>\n"
                "• تدعم رفع ملفات (.py / .js / .zip) مباشرة من ذاكرة الهاتف أو الحاسوب."
            )
            kb = types.InlineKeyboardMarkup()
            if base_url.startswith(("http://", "https://")) and "127.0.0.1" not in base_url:
                kb.add(btn(f"🌐 فتح صفحة {PAGE_BRAND_NAME}", url=base_url, style="success"))
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            return send_msg(cid, deco(f"🌐 {PAGE_BRAND_NAME}", info_txt, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)

        if data == "admin_system_status":
            return handle_admin_system(call)
        if data == "sys_clean_ram":
            return handle_sys_clean_ram(call)
        if data == "sys_clean_tmp":
            return handle_sys_clean_tmp(call)
        if data == "sys_clean_logs":
            return handle_sys_clean_logs(call)
        if data == "sys_top":
            return handle_sys_top(call)

        if data == "cancel_admin":
            set_cancel(uid, True)
            admin_steps.pop(uid, None)
            bot.answer_callback_query(call.id, "✅ تم إلغاء العملية.")
            return admin_panel(call)

        if data == "check_sub":
            if check_sub(uid):
                bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح!")
                u = users.get(str(uid), {})
                text = (
                    "<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n"
                    f"<b>   🌟 أهلاً بك عزيزي في {escape(PAGE_BRAND_NAME)} ⦗ {escape(first_name_raw)} ⦘ 🌟   </b>\n"
                    "<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n\n"
                    f"<b>💌 ︙ ايدي المستخدم : <code>{cid}</code></b>\n"
                    f"<b>💰 ︙ رصيدك المالي : <tg-spoiler>{u.get('balance', 0.0)}</tg-spoiler> ₽</b>\n"
                    "<b>🚀 ︙ سرعة الاستضافة : فائقة </b>\n\n"
                    "<b>💻 ︙ تحكم الآن بكافة الأقسام عبر الأزرار أدناه 👇</b>"
                )
                try:
                    bot.delete_message(cid, call.message.message_id)
                except Exception:
                    pass
                send_msg(cid, deco("🏠 القائمة الرئيسية", text, first_name_raw), main_kb(uid), effect_id=FIRE_EFFECT_ID)
            else:
                bot.answer_callback_query(call.id, "❌ لم تقم بالاشتراك في كافة القنوات!", show_alert=True)
            return

        if not check_sub(uid) and not is_admin(uid):
            return bot.answer_callback_query(call.id, "❌ يجب الاشتراك في القنوات أولاً!", show_alert=True)

        clear_cancel(uid)

        if data == "ehab_5_e":
            terms_text = (
                f"📜 <b>الشروط والتعليمات الكاملة لاستخدام {escape(PAGE_BRAND_NAME)} والبوت</b>\n\n"
                "• يتم تشغيل ملفات <b>Python (.py)</b> و <b>JavaScript (.js)</b> والملفات المضغوطة <b>(.zip)</b> فقط.\n"
                "• يتم تشفير الملفات بـ AES وعزل كل مستخدم داخل مجلده الخاص وتحويل أسماء الملفات إلى الإنجليزية.\n"
                "• يمنع منعاً باتاً رفع الأكواد المشفّرة أو الضارة أو محاولة اختراق المسارات، وفي حال المخالفة يتم الحظر الفوري."
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(btn("🔙 رجوع للقائمة الرئيسية", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            send_msg(cid, deco("📜 الشروط والتعليمات", terms_text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
            return

        if data == "nav_pro":
            if not is_user_pro(uid):
                return bot.answer_callback_query(call.id, "❌ هذه اللوحة مخصصة لمشتركي VIP فقط!", show_alert=True)
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            send_msg(cid, deco("🔧 لوحة Pro", "🔧 <b>لوحة VIP المميزة</b>", first_name_raw), pro_panel_kb(uid), effect_id=FIRE_EFFECT_ID)
            return

        if data == "pro_download_all":
            if not is_user_pro(uid):
                return bot.answer_callback_query(call.id, "❌ لمشتركي VIP فقط!", show_alert=True)
            files = read_json(FILES_DB)
            u_files = {fid: f for fid, f in files.items() if str(f.get("user_id")) == str(uid) and f.get("status") == "active"}
            if not u_files:
                return bot.answer_callback_query(call.id, "📂 لا توجد ملفات نشطة لديك!", show_alert=True)
            tmp_work = tempfile.mkdtemp(prefix=f"dlall_{uid}_")
            try:
                created = []
                for fid, finfo in u_files.items():
                    if verify_file_access(fid, uid):
                        content = load_encrypted_file(fid)
                        if content:
                            ext = finfo.get("ext", ".py")
                            tp = safe_join_user_file(tmp_work, f"{fid}{ext}")
                            with open(tp, "w", encoding="utf-8") as f:
                                f.write(content)
                            created.append(tp)
                if created:
                    zname = f"files_{uid}_{gen_id(4)}.zip"
                    zpath = create_zip(created, zname)
                    with open(zpath, "rb") as f:
                        bot.send_document(cid, f, caption="📦 جميع ملفاتك البرمجية في أرشيف ZIP:", message_effect_id=FIRE_EFFECT_ID)
                    try:
                        os.remove(zpath)
                    except Exception:
                        pass
                else:
                    bot.answer_callback_query(call.id, "❌ لم يتم العثور على ملفات للتحميل!", show_alert=True)
            finally:
                shutil.rmtree(tmp_work, ignore_errors=True)
            return

        if data == "nav_wallet":
            u = users.get(str(uid), {})
            vip = is_user_pro(uid)
            exp = "لا يوجد"
            if vip:
                e = u.get("expiry")
                exp = "دائم ♾" if e in ("LIFETIME", 0, "0") else (e or "لا يوجد")
            vip_label = "VIP 👑" if vip else "مجاني 🆓"
            text = (
                f"💰 رصيدك الحالي: <code>{u.get('points', 0)}</code> نقطة | 💵 الرصيد المالي: <code>{u.get('balance', 0.0)}</code> ₽\n"
                f"💎 الرتبة: {vip_label}\n"
                f"⏰ صلاحية VIP: {exp}"
            )
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            send_msg(cid, deco("💼 محفظتي", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
            return

        if data == "nav_help":
            text = f"📖 <b>دليل استخدام {escape(PAGE_BRAND_NAME)}</b>\n\n• ارفع ملف <code>.py</code> أو <code>.js</code> أو أرشيف <code>.zip</code>.\n• سيتم تحويل الاسم إلى الإنجليزية وفحص الكود وحمايته ثم تشغيله."
            kb = types.InlineKeyboardMarkup()
            kb.add(btn("👨‍💻 تواصل مع المطور", url=DEV_TELEGRAM, style="primary"))
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            send_msg(cid, deco("📖 التعليمات", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
            return

        if data == "nav_upload":
            u = users.get(str(uid), {})
            required_price = float(get_settings().get("python_upload_price", 1.0))
            if float(u.get("points", 0.0)) < required_price and not is_user_pro(uid):
                return bot.answer_callback_query(call.id, f"❌ رصيدك لا يكفي! السعر المطلوب: {required_price} نقطة.", show_alert=True)
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("📤 إرسال الملف", f"📥 أرسل ملف <code>.py</code> أو <code>.js</code> (سعر الرفع: {required_price} نقطة / ساعة):", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, upload_step, m.message_id)
            return

        if data == "nav_upload_zip":
            u = users.get(str(uid), {})
            required_price = float(get_settings().get("python_upload_price", 1.0))
            if float(u.get("points", 0.0)) < required_price and not is_user_pro(uid):
                return bot.answer_callback_query(call.id, f"❌ رصيدك لا يكفي لرفع ZIP! السعر المطلوب: {required_price} نقطة.", show_alert=True)
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("📦 إرسال ملف ZIP", f"📥 أرسل ملف <code>.zip</code> يحتوي على سكربتات <code>.py</code> أو <code>.js</code> (السعر: {required_price} نقطة / ساعة):", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, upload_zip_step, m.message_id)
            return

        if data == "nav_files":
            files = read_json(FILES_DB)
            u_files = {fid: f for fid, f in files.items() if str(f.get("user_id")) == str(uid)}
            if not u_files:
                return bot.answer_callback_query(call.id, "📂 لا توجد ملفات مرفوعة لديك حالياً!", show_alert=True)
            kb = types.InlineKeyboardMarkup(row_width=1)
            for fid, f in u_files.items():
                if f.get("status") == "pending":
                    icon = "⏳ قيد المراجعة"
                else:
                    running = fid in active_processes and active_processes[fid].poll() is None
                    icon = "🟢 يعمل" if running else "🔴 متوقف"
                ft = "💎" if f.get("type") == "pro" else "🆓"
                label = f.get("stored_name") or f.get("file_name", "?")
                kb.add(btn(f"{icon} | {ft} {label[:25]}", callback_data=f"manage_{fid}", style="primary"))
            if is_user_pro(uid):
                kb.add(btn("📦 تحميل كافة الملفات (ZIP)", callback_data="pro_download_all", style="success"))
            kb.add(btn("🔙 القائمة الرئيسية 🔙", callback_data="nav_main", style="danger"))
            active_count = sum(1 for fid, f in u_files.items() if f.get("status") == "active" and fid in active_processes and active_processes[fid].poll() is None)
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            send_msg(cid, deco("📁 ملفاتي", f"📊 إجمالي ملفاتك: {len(u_files)}\n🟢 يعمل الآن: {active_count}", first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
            return

        if data.startswith("manage_"):
            return file_panel(call, data.split("_", 1)[1])
        if data.startswith("toggle_"):
            return toggle_file(call, data.split("_", 1)[1])
        if data.startswith("delc_"):
            fid = data.split("_", 1)[1]
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                btn("✅ نعم، احذف", callback_data=f"del_{fid}", style="danger"),
                btn("❌ تراجع", callback_data=f"manage_{fid}", style="primary"),
            )
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            return send_msg(cid, deco("🗑️ تأكيد الحذف", "هل أنت متأكد من حذف هذا الملف نهائياً؟", first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
        if data.startswith("del_"):
            return delete_file(call, data.split("_", 1)[1])
        if data.startswith("dl_"):
            return download_file(call, data.split("_", 1)[1])
        if data.startswith("term_") or data.startswith("rterm_"):
            return terminal(call, data.split("_", 1)[1])
        if data.startswith("inp_"):
            fid = data.split("_", 1)[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("⌨️ إدخال أمر", "اكتب الأمر أو النص المراد إرساله للسكريبت:", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, input_step, fid, m.message_id)
        if data.startswith("chtoken_"):
            fid = data.split("_", 1)[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("🔑 تغيير التوكن", "أرسل التوكن الجديد للروبوت:", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, token_step, fid, m.message_id)
        if data.startswith("tokinfo_"):
            return token_info(call, data.split("_", 1)[1])
        if data.startswith("fai_"):
            return cb_ai_repair_request(call)
        if data.startswith("faic_"):
            return cb_ai_repair_confirm(call)
        if data.startswith("faix_"):
            bot.answer_callback_query(call.id, "❌ تم إلغاء طلب الإصلاح بالذكاء الاصطناعي.")
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            return
        if data == "nav_store":
            return store_view(call)
        if data.startswith("buy_"):
            return buy_confirm(call, data.split("_", 1)[1])
        if data.startswith("ebuy_"):
            return buy_exec(call, data.split("_", 1)[1])
        if data == "nav_lib":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("🛠 تثبيت مكتبة", "أرسل اسم المكتبة البرمجية المراد تثبيتها عبر pip:", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, lib_step, m.message_id)
        if data == "nav_stats":
            files = read_json(FILES_DB)
            u = users.get(str(uid), {})
            u_files = [f for f in files.values() if str(f.get("user_id")) == str(uid)]
            running = sum(1 for fid, f in files.items() if str(f.get("user_id")) == str(uid) and fid in active_processes and active_processes[fid].poll() is None)
            vip = is_user_pro(uid)
            exp = "لا يوجد"
            if vip:
                e = u.get("expiry")
                if e in ("LIFETIME", 0, "0"):
                    exp = "دائم ♾"
                elif e:
                    try:
                        rem = datetime.strptime(e, "%Y-%m-%d %H:%M:%S") - datetime.now()
                        exp = f"{max(0, rem.days)} يوم متبقي"
                    except Exception:
                        exp = e
            vip_label = "VIP 👑" if vip else "مجاني 🆓"
            uname_val = u.get("username") or "لا يوجد"
            jdate_val = u.get("join_date") or "اليوم"
            text = (
                f"🆔 الآيدي: <code>{uid}</code>\n"
                f"🔗 المعرف: @{uname_val}\n"
                f"📅 الانضمام: {jdate_val}\n\n"
                f"💎 الرتبة: {vip_label}\n"
                f"⏰ صلاحية VIP: {exp}\n"
                f"💰 رصيد النقاط: <code>{u.get('points', 0)}</code>\n\n"
                f"📁 ملفاتك: {len(u_files)}\n"
                f"🟢 قيد التشغيل: {running}"
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(btn("💼 محفظتي", callback_data="nav_wallet", style="primary"))
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            return send_msg(cid, deco("📊 حسابي", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)

        if not is_admin(uid):
            return

        if data == "nav_admin":
            return admin_panel(call)
        if data == "adm_users":
            return users_panel(call)
        if data.startswith("userpage_"):
            return users_panel(call, int(data.split("_")[1]))
        if data.startswith("uctrl_"):
            return user_panel(call, data.split("_")[1])
        if data.startswith("ban_"):
            return ban_toggle(call, data.split("_")[1])
        if data.startswith("pro_"):
            tuid = data.split("_")[1]
            if is_user_pro(int(tuid)):
                return pro_remove(call, tuid)
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("💎 منح VIP", "أرسل عدد الأيام (0 للدائم):", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, pro_grant_step, tuid, m.message_id)
        if data == "adm_related_files":
            return pending_list(call)
        if data.startswith("vpend_"):
            return admin_view_pending_file(call, data.split("_")[1])
        if data.startswith("vdl_"):
            return admin_download_pending_file(call, data.split("_")[1])
        if data.startswith("vapprove_"):
            return admin_approve_file(call, data.split("_")[1])
        if data.startswith("vdel_"):
            return admin_delete_pending_file(call, data.split("_")[1])
        if data == "adm_bot_manager":
            return bot_manager_panel(call)
        if data.startswith("botact_"):
            ex = data.split("_", 2)
            return handle_bot_action(call, ex[1], ex[2])
        if data == "adm_stats":
            return admin_stats_view(call)
        if data == "adm_add_balance":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("➕ إضافة رصيد", "أرسل آيدي المستخدم:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, admin_add_balance_id_step, m.message_id)
        if data == "adm_deduct_balance":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("➖ خصم رصيد", "أرسل آيدي المستخدم:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, admin_deduct_balance_id_step, m.message_id)
        if data == "adm_ban_id":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("🚫 حظر آيدي", "أرسل الآيدي المراد حظره:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, admin_ban_id_step, m.message_id)
        if data == "adm_unban_id":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("✅ إلغاء حظر آيدي", "أرسل الآيدي المراد فك الحظر عنه:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, admin_unban_id_step, m.message_id)
        if data == "adm_restart_all":
            restarted_count = 0
            for fid in list(read_json(FILES_DB).keys()):
                stop_script(fid)
                if start_script(fid):
                    restarted_count += 1
            bot.answer_callback_query(call.id, f"🔄 تمت إعادة تشغيل {restarted_count} بوت!", show_alert=True)
            return admin_panel(call)
        if data == "adm_stop_all":
            with process_lock:
                stopped_count = len(active_processes)
                for fid in list(active_processes.keys()):
                    stop_script(fid)
            bot.answer_callback_query(call.id, f"⏹ تم إيقاف {stopped_count} بوت!", show_alert=True)
            return admin_panel(call)
        if data == "adm_sub_count":
            return bot.answer_callback_query(call.id, f"👥 عدد المستخدمين: {len(users)}", show_alert=True)
        if data == "adm_broadcast":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("📢 إذاعة عامة", "أرسل الرسالة للإذاعة:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, broadcast_step, m.message_id)
        if data == "adm_channels_broadcast":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("📢 إذاعة للقنوات", "أرسل الرسالة للإذاعة في القنوات:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, channels_broadcast_step, m.message_id)
        if data == "admin_maintenance_on":
            st = get_settings()
            st["bot_locked"] = True
            save_settings(st)
            bot.answer_callback_query(call.id, "🔒 تم تفعيل وضع الصيانة!", show_alert=True)
            return admin_panel(call)
        if data == "admin_maintenance_off":
            st = get_settings()
            st["bot_locked"] = False
            save_settings(st)
            bot.answer_callback_query(call.id, "🔓 تم إلغاء وضع الصيانة!", show_alert=True)
            return admin_panel(call)
        if data == "adm_clean":
            cleaned = 0
            for dpath in (LOGS_DIR, DOWNLOAD_DIR):
                for fn in os.listdir(dpath):
                    fp = os.path.join(dpath, fn)
                    if os.path.isfile(fp) and not os.path.islink(fp):
                        os.remove(fp)
                        cleaned += 1
            for dname in os.listdir(ENV_DIR):
                ep = os.path.join(ENV_DIR, dname)
                if os.path.isdir(ep) and not os.path.islink(ep):
                    shutil.rmtree(ep, ignore_errors=True)
                    cleaned += 1
            bot.answer_callback_query(call.id, f"🧹 تم تنظيف {cleaned} عنصر مؤقت!", show_alert=True)
            return admin_panel(call)
        if data == "adm_speedup":
            gc.collect()
            bot.answer_callback_query(call.id, "🚀 تم تحسين الأداء بنجاح!", show_alert=True)
            return admin_panel(call)
        if data == "adm_admins":
            return admins_panel(call)
        if data == "add_admin" and is_main_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("➕ إضافة أدمن", "أرسل آيدي المستخدم الجديد:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, add_admin_step, m.message_id)
        if data.startswith("rmadmin_"):
            aid = int(data.split("_")[1])
            if aid in (OWNER_ID, ADMIN_ID):
                return bot.answer_callback_query(call.id, "❌ لا يمكن إزالة المالك الرئيسي!", show_alert=True)
            if remove_admin(aid):
                bot.answer_callback_query(call.id, "✅ تم إزالة الأدمن بنجاح.")
                return admins_panel(call)
        if data == "adm_channels":
            return channels_panel(call)
        if data == "add_channel":
            try:
                bot.delete_message(cid, call.message.message_id)
            except Exception:
                pass
            m = send_msg(cid, deco("📢 إضافة قناة", "أرسل معرف القناة (مثال: @ChannelName):", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            return bot.register_next_step_handler(m, add_channel_step, m.message_id)
        if data.startswith("delch_"):
            return del_channel(call, int(data.split("_")[1]))
    except Exception as e:
        logger.error(f"Callback Error: {e}")


# ============ دوال الإصلاح بالذكاء الاصطناعي وإدارة الملفات والإدارة ============
def cb_ai_repair_request(call):
    parsed = _get_ai_repair_file(call)
    if not parsed:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    owner_id, file_name, _ = parsed
    token = file_token(file_name)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        btn("أوافق وأكمل", callback_data=f"faic_{owner_id}_{token}", style="success"),
        btn("إلغاء", callback_data=f"faix_{owner_id}_{token}", style="danger"),
    )
    bot.send_message(
        call.message.chat.id,
        f"<blockquote><b>إصلاح وتعديل الملف بـ AI</b></blockquote>\n\n"
        f"<blockquote>سيتم إرسال محتوى <code>{escape(file_name)}</code> إلى خدمة <code>ptero.pro</code> لتحليله وإصلاحه.</blockquote>",
        parse_mode="HTML",
        reply_markup=markup,
        message_effect_id=FIRE_EFFECT_ID
    )
    bot.answer_callback_query(call.id)


def cb_ai_repair_confirm(call):
    parsed = _get_ai_repair_file(call)
    if not parsed:
        return bot.answer_callback_query(call.id, "❌ لم يتم العثور على الملف!", show_alert=True)
    _, file_name, fid = parsed
    content = load_encrypted_file(fid)
    if not content:
        return bot.answer_callback_query(call.id, "❌ تعذر قراءة محتوى الملف!", show_alert=True)

    bot.answer_callback_query(call.id, "⏳ جاري إرسال الكود للذكاء الاصطناعي...")
    msg_wait = send_msg(
        call.message.chat.id,
        deco("🤖 جاري الإصلاح", "⏳ يتم الآن تحليل الكود وإصلاح المشاكل...", call.from_user.first_name or "مستخدم"),
        effect_id=FIRE_EFFECT_ID
    )
    try:
        fixed_code = repair_source(content, "افحص وأصلح هذا السكريبت وصحح أي أخطاء برمجية أو مسارات فيه", file_name)
        if not fixed_code:
            bot.edit_message_text("❌ لم يتم استلام رد صالح.", call.message.chat.id, msg_wait.message_id, parse_mode="HTML")
            return
        ext = os.path.splitext(file_name)[1].lower() or ".py"
        fixed_path = safe_join_user_file(DOWNLOAD_DIR, f"fixed_{fid}{ext}")
        with open(fixed_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        with open(fixed_path, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption=f"🛠 النسخة المصححة لملف: {file_name}", message_effect_id=FIRE_EFFECT_ID)
        try:
            os.remove(fixed_path)
            bot.delete_message(call.message.chat.id, msg_wait.message_id)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"AI Repair Error: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء المعالجة بالذكاء الاصطناعي!", show_alert=True)


def pending_list(call):
    files = read_json(FILES_DB)
    pending = {fid: f for fid, f in files.items() if f.get("status") == "pending"}
    if not pending:
        return bot.answer_callback_query(call.id, "✅ لا توجد ملفات معلقة!", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for fid, f in pending.items():
        lbl = (f.get("stored_name") or f.get("file_name", "?"))[:25]
        kb.add(btn(f"📄 {lbl}", callback_data=f"vpend_{fid}", style="primary"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("⏳ الملفات المعلقة", f"عدد الملفات المعلقة: {len(pending)}", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def admin_view_pending_file(call, fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    f = files[fid]
    content = load_encrypted_file(fid)
    preview = escape(content[:800]) if content else "تعذر قراءة المحتوى"
    text = (
        "⏳ <b>معاينة الملف المعلق:</b>\n\n"
        f"📄 الاسم الأصلي: {escape(str(f.get('file_name')))}\n"
        f"🔤 الاسم الإنجليزي: <code>{escape(str(f.get('stored_name', '')))}</code>\n"
        f"👤 صاحب الآيدي: <code>{f.get('user_id')}</code>\n"
        f"⏰ الساعات: {f.get('hours')}\n\n"
        f"<pre><code>{preview}</code></pre>"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("📥 تحميل الملف", callback_data=f"vdl_{fid}", style="primary"),
        btn("✅ موافقة ✅", callback_data=f"vapprove_{fid}", style="success"),
    )
    kb.add(
        btn("❌ رفض ❌", callback_data=f"vdel_{fid}", style="danger"),
        btn("⎙● رجـــــوع ●⎙", callback_data="adm_related_files", style="primary"),
    )
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("⏳ مراجعة الملف المعلق", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def admin_download_pending_file(call, fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    content = load_encrypted_file(fid)
    if not content:
        return bot.answer_callback_query(call.id, "❌ تعذر تحميل الملف!", show_alert=True)
    ext = files[fid].get("ext", ".py")
    temp_path = safe_join_user_file(DOWNLOAD_DIR, f"temp_pend_{fid}{ext}")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(temp_path, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption=f"📄 {files[fid]['file_name']} (معلق)", message_effect_id=FIRE_EFFECT_ID)
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def admin_approve_file(call, fid):
    with db_lock:
        files = read_json(FILES_DB)
        if fid not in files:
            return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
        f = files[fid]
        f["status"] = "active"
        write_json(FILES_DB, files)

    user_id = int(f["user_id"])
    start_script(fid)
    try:
        bot.send_message(user_id, deco("✅ تم قبول الملف وتشغيله", f"تمت الموافقة على ملفك <b>{escape(f['file_name'])}</b> وتشغيله بنجاح!"), message_effect_id=FIRE_EFFECT_ID)
    except Exception:
        pass
    bot.answer_callback_query(call.id, "✅ تمت الموافقة على الملف وتشغيله!")
    pending_list(call)


def admin_delete_pending_file(call, fid):
    with db_lock:
        files = read_json(FILES_DB)
        if fid not in files:
            return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
        f = files[fid]
        user_id = int(f["user_id"])
        refund_amt = float(f.get("charged_cost", 0.0))
        if refund_amt > 0:
            _refund_points(user_id, refund_amt)
        try:
            os.remove(os.path.join(ENCRYPTED_DIR, f"{fid}.enc"))
        except Exception:
            pass
        del files[fid]
        write_json(FILES_DB, files)
    try:
        bot.send_message(user_id, deco("❌ رفض الملف", f"تم رفض وحذف ملفك <b>{escape(f['file_name'])}</b> من الإدارة وتم إرجاع النقاط."), message_effect_id=FIRE_EFFECT_ID)
    except Exception:
        pass
    bot.answer_callback_query(call.id, "❌ تم رفض وحذف الملف.")
    pending_list(call)


def file_panel(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحية الوصول لهذا الملف!", show_alert=True)
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!")
    f = files[fid]
    content = load_encrypted_file(fid)
    preview = escape(content[:1000]) if content else "تعذر القراءة"
    if f.get("status") == "pending":
        running_text = "⏳ قيد المراجعة لدى الأدمن"
    else:
        running = fid in active_processes and active_processes[fid].poll() is None
        running_text = "يعمل ✅" if running else "متوقف ❌"

    addons_txt = ", ".join(f.get("addons", [])) or "لا يوجد"
    text = (
        f"📄 الاسم الأصلي: {escape(str(f.get('file_name')))}\n"
        f"🔤 الاسم الإنجليزي: <code>{escape(str(f.get('stored_name', '')))}</code>\n"
        f"📦 الإضافات: <code>{escape(addons_txt)}</code>\n"
        f"🟢 الحالة: {running_text}\n"
        f"📅 تاريخ الرفع: {f.get('created_at')}\n\n"
        f"🔍 المعاينة:\n<pre><code>{preview}</code></pre>"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    if f.get("status") == "active":
        is_run = fid in active_processes and active_processes[fid].poll() is None
        kb.add(
            btn("⏸ إيقاف" if is_run else "▶️ تشغيل", callback_data=f"toggle_{fid}", style="danger" if is_run else "success"),
            btn("📟 التيرمنال", callback_data=f"term_{fid}", style="primary"),
        )
        kb.add(
            btn("🔑 تغيير التوكن", callback_data=f"chtoken_{fid}", style="primary"),
            btn("ℹ️ معلومات التوكن", callback_data=f"tokinfo_{fid}", style="primary"),
        )
    kb.add(
        btn("📥 تحميل الملف", callback_data=f"dl_{fid}", style="primary"),
        btn("🛠️ إصلاح وتعديل بـ AI", callback_data=f"fai_{f.get('user_id')}_{file_token(f.get('file_name', ''))}", style="success"),
    )
    kb.add(
        btn("🗑️ حذف 🗑️", callback_data=f"delc_{fid}", style="danger"),
        btn("🔙 الرجوع", callback_data="nav_files", style="danger"),
    )
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("📁 إدارة الملف", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def toggle_file(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
    running = fid in active_processes and active_processes[fid].poll() is None
    if running:
        stop_script(fid)
        bot.answer_callback_query(call.id, "✅ تم إيقاف الملف.")
    else:
        if start_script(fid):
            bot.answer_callback_query(call.id, "🚀 تم تشغيل الملف بنجاح.")
        else:
            bot.answer_callback_query(call.id, "❌ فشل في تشغيل الملف!")
    file_panel(call, fid)


def delete_file(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
    stop_script(fid)
    with db_lock:
        files = read_json(FILES_DB)
        if fid in files:
            owner_id = files[fid].get("user_id")
            stored_name = files[fid].get("stored_name")
            for p_rem in (os.path.join(ENCRYPTED_DIR, f"{fid}.enc"), os.path.join(LOGS_DIR, f"{fid}.log")):
                try:
                    os.remove(p_rem)
                except Exception:
                    pass
            try:
                if owner_id and stored_name:
                    up = safe_join_user_file(get_user_isolation_dir(owner_id), stored_name)
                    if os.path.exists(up):
                        os.remove(up)
            except Exception:
                pass
            del files[fid]
            write_json(FILES_DB, files)
            bot.answer_callback_query(call.id, "🗑️ تم حذف الملف بنجاح.")

    u_files = {k: v for k, v in files.items() if str(v.get("user_id")) == str(uid)}
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k, v in u_files.items():
        lbl = (v.get("stored_name") or v.get("file_name", "?"))[:25]
        kb.add(btn(f"📄 {lbl}", callback_data=f"manage_{k}", style="primary"))
    if not u_files:
        kb.add(btn("📤 رفع ملف", callback_data="nav_upload", style="success"))
    kb.add(btn("🔙 القائمة الرئيسية 🔙", callback_data="nav_main", style="danger"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("📁 ملفاتي", f"📊 إجمالي الملفات المتبقية: {len(u_files)}", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def download_file(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!")
    content = load_encrypted_file(fid)
    if not content:
        return bot.answer_callback_query(call.id, "❌ تعذر تحميل الملف!", show_alert=True)
    ext = files[fid].get("ext", ".py")
    temp_path = safe_join_user_file(DOWNLOAD_DIR, f"temp_{fid}_{gen_id(4)}{ext}")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        thumb = get_thumb()
        with open(temp_path, "rb") as f:
            if thumb:
                with open(thumb, "rb") as t:
                    bot.send_document(call.message.chat.id, f, thumb=t, caption=f"📄 {files[fid]['file_name']}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
            else:
                bot.send_document(call.message.chat.id, f, caption=f"📄 {files[fid]['file_name']}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف بنجاح.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def terminal(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!")
    running = fid in active_processes and active_processes[fid].poll() is None
    output = get_logs(fid, 40)
    status_lbl = "يعمل ✅" if running else "متوقف ❌"
    text = f"📄 الملف: {escape(str(files[fid]['file_name']))}\n🟢 الحالة: {status_lbl}\n\n📺 <b>مخرجات التيرمنال:</b>\n{output}"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("🔄 تحديث السجل", callback_data=f"rterm_{fid}", style="primary"),
        btn("⌨️ إجابة / إدخال", callback_data=f"inp_{fid}", style="primary"),
    )
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data=f"manage_{fid}", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("📟 التيرمنال", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def get_logs(fid, lines=40):
    log_path = os.path.join(LOGS_DIR, f"{fid}.log")
    try:
        if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                last = f.readlines()[-lines:]
                safe = escape("".join(last))
                if len(safe) > 3000:
                    safe = safe[:3000] + "\n..."
                return f"<pre><code>{safe}</code></pre>"
        return "📝 لا توجد سجلات مخرجات حتى الآن."
    except Exception:
        return "❌ خطأ في قراءة السجلات."


def input_step(msg, fid, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text:
        return
    text = f"✅ تم إرسال الأمر:\n<code>{escape(msg.text)}</code>" if write_proc(fid, msg.text) else "❌ السكريبت لا يعمل حالياً!"
    send_msg(msg.chat.id, deco("⌨️ إدخال", text, first_name_raw), back_kb(f"term_{fid}"), effect_id=FIRE_EFFECT_ID)


def token_step(msg, fid, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text:
        return
    token = msg.text.strip()
    content = load_encrypted_file(fid)
    if not content:
        return send_msg(msg.chat.id, deco("❌ خطأ", "تعذر تحميل الملف المشفر!", first_name_raw), back_kb(f"manage_{fid}"), effect_id=FIRE_EFFECT_ID)
    new_content = re.sub(r"([\"'])\d{8,12}:[a-zA-Z0-9_-]{35,}([\"'])", rf"\g<1>{token}\g<2>", content)
    files = read_json(FILES_DB)
    if fid in files and save_encrypted_file(fid, new_content, files[fid].get("user_id")):
        text = "✅ تم تحديث التوكن بنجاح! أعد تشغيل السكريبت لتطبيق التغيير."
    else:
        text = "❌ فشل في حفظ التغييرات!"
    send_msg(msg.chat.id, deco("🔑 تغيير التوكن", text, first_name_raw), back_kb(f"manage_{fid}"), effect_id=FIRE_EFFECT_ID)


def token_info(call, fid):
    if not verify_file_access(fid, call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
    content = load_encrypted_file(fid)
    if not content:
        return bot.answer_callback_query(call.id, "❌ تعذر تحميل المحتوى!", show_alert=True)
    tokens = re.findall(r"(\d{8,12}:[a-zA-Z0-9_-]{35,})", content)
    if not tokens:
        return bot.answer_callback_query(call.id, "🔍 لم يتم العثور على توكن داخل الكود!", show_alert=True)
    try:
        res = requests.get(f"[https://api.telegram.org/bot](https://api.telegram.org/bot){tokens[0]}/getMe", timeout=15).json()
        if res.get("ok"):
            info = res["result"]
            text = f"✅ التوكن صالح!\n\n🤖 الاسم: {escape(str(info.get('first_name')))}\n👤 المعرف: @{info.get('username')}\n🆔 الآيدي: <code>{info.get('id')}</code>"
        else:
            text = "❌ التوكن غير صالح."
        kb = types.InlineKeyboardMarkup()
        kb.add(btn("⎙● رجـــــوع ●⎙", callback_data=f"manage_{fid}", style="primary"))
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_msg(call.message.chat.id, deco("ℹ️ معلومات التوكن", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)
    except Exception:
        bot.answer_callback_query(call.id, "❌ تعذر فحص التوكن!", show_alert=True)


def lib_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text:
        return
    lib = re.sub(r"[^a-zA-Z0-9._-]", "", msg.text.strip())
    if not lib:
        return send_msg(msg.chat.id, deco("❌ خطأ", "اسم مكتبة غير صالح.", first_name_raw), back_kb(), effect_id=FIRE_EFFECT_ID)
    m = send_msg(msg.chat.id, deco("⏳ جاري التثبيت", f"جاري تثبيت: <b>{escape(lib)}</b>...", first_name_raw), effect_id=FIRE_EFFECT_ID)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", lib], timeout=120)
        record_addon(uid, "manual_lib", lib, "pip")
        text = f"✅ تم تثبيت وتسجيل المكتبة: <b>{escape(lib)}</b>"
    except Exception:
        text = f"❌ فشل تثبيت المكتبة: <b>{escape(lib)}</b>"
    try:
        bot.delete_message(msg.chat.id, m.message_id)
    except Exception:
        pass
    send_msg(msg.chat.id, deco("🛠 تثبيت مكتبة", text, first_name_raw), back_kb(), effect_id=FIRE_EFFECT_ID)


def store_view(call):
    store = read_json(STORE_DB)
    if not store:
        return bot.answer_callback_query(call.id, "🛒 المتجر فارغ حالياً!", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for sid, item in store.items():
        nm = str(item.get("name", "?"))[:15]
        kb.add(btn(f"📦 {nm} • {item.get('price', 0)}pt", callback_data=f"buy_{sid}", style="primary"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
    pts = read_json(USERS_DB).get(str(call.from_user.id), {}).get("points", 0)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("🛒 المتجر", f"🛒 <b>متجر الملفات الجاهزة</b>\n\n💰 رصيدك: <code>{pts}</code> نقطة", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def buy_confirm(call, sid):
    item = read_json(STORE_DB).get(sid)
    if not item:
        return
    pts = read_json(USERS_DB).get(str(call.from_user.id), {}).get("points", 0)
    price = item.get("price", 0)
    can_buy = pts >= price
    afford_msg = "✅ رصيدك يكفي لإتمام الشراء!" if can_buy else "❌ رصيدك لا يكفي!"
    text = (
        f"📦 الملف: {escape(str(item.get('name')))}\n"
        f"💰 السعر المطلوب: {price} نقطة\n"
        f"💵 رصيدك الحالي: <code>{pts}</code> نقطة\n\n"
        f"{afford_msg}"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    if can_buy:
        kb.add(btn("✅ تأكيد الشراء", callback_data=f"ebuy_{sid}", style="success"), btn("❌ إلغاء", callback_data="nav_store", style="danger"))
    else:
        kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_store", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("🛒 تأكيد الشراء", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def buy_exec(call, sid):
    uid = call.from_user.id
    with db_lock:
        users = read_json(USERS_DB)
        item = read_json(STORE_DB).get(sid)
        if not item:
            return bot.answer_callback_query(call.id, "❌ العنصر غير موجود!", show_alert=True)
        price = float(item.get("price", 0))
        if float(users.get(str(uid), {}).get("points", 0)) < price:
            return bot.answer_callback_query(call.id, "❌ نقاطك غير كافية!", show_alert=True)
        path = safe_join_user_file(STORE_DIR, f"{sid}.py")
        if not os.path.exists(path):
            return bot.answer_callback_query(call.id, "❌ ملف المتجر غير متوفر!", show_alert=True)
        users[str(uid)]["points"] = round(float(users[str(uid)].get("points", 0)) - price, 4)
        write_json(USERS_DB, users)
    try:
        with open(path, "rb") as f:
            bot.send_document(uid, f, caption=f"✅ تم شراء الملف: {item.get('name')}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف بنجاح!")
        store_view(call)
    except Exception:
        _refund_points(uid, price)
        bot.answer_callback_query(call.id, "❌ تعذر إرسال الملف!", show_alert=True)


def admin_panel(call):
    users = read_json(USERS_DB)
    files = read_json(FILES_DB)
    pending = [f for f in files.values() if f.get("status") == "pending"]
    active = sum(1 for fid in active_processes if active_processes[fid].poll() is None)
    settings = get_settings()
    locked = bool(settings.get("bot_locked", False))
    price = settings.get("python_upload_price", 1.0)
    lock_label = "مغلق للصيانة 🔒" if locked else "مفتوح للعمل 🔓"

    text = (
        f"⚙️ <b>لوحة تحكم الإدارة العليا — {escape(PAGE_BRAND_NAME)}</b>\n\n"
        f"👥 المستخدمين: {len(users)}\n"
        f"📁 إجمالي الملفات: {len(files)}\n"
        f"⏳ طلبات معلقة: {len(pending)}\n"
        f"🟢 الملفات النشطة: {active}\n"
        f"💵 سعر رفع الملفات: {price} نقطة\n\n"
        f"🔐 حالة البوت: {lock_label}"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(btn("💻 حالة ونظام السيرفر", callback_data="admin_system_status", style="primary"))
    kb.row(
        btn("🔒 تفعيل وضع الصيانة", callback_data="admin_maintenance_on", style="danger"),
        btn("🔓 إلغاء وضع الصيانة", callback_data="admin_maintenance_off", style="success"),
    )
    kb.row(
        btn("🔄 إعادة تشغيل كل البوتات", callback_data="adm_restart_all", style="success"),
        btn("⏹ إيقاف كل البوتات", callback_data="adm_stop_all", style="danger"),
    )
    kb.row(
        btn("🚫 حظر آيدي", callback_data="adm_ban_id", style="danger"),
        btn("✅ إلغاء حظر آيدي", callback_data="adm_unban_id", style="success"),
    )
    kb.row(
        btn("👥 معرفة المشتركين", callback_data="adm_sub_count", style="primary"),
        btn("📢 إذاعة عامة", callback_data="adm_broadcast", style="success"),
    )
    kb.row(
        btn("📢 إذاعة للقنوات", callback_data="adm_channels_broadcast", style="primary"),
        btn("📢 اشتراك إجباري", callback_data="adm_channels", style="primary"),
    )
    kb.row(
        btn("👥 إدارة المستخدمين", callback_data="adm_users", style="primary"),
        btn("👮 إدارة المشرفين", callback_data="adm_admins", style="primary"),
    )
    kb.row(
        btn("📁 الملفات المتعلقة", callback_data="adm_related_files", style="primary"),
        btn("📊 الاحصائيات", callback_data="adm_stats", style="primary"),
    )
    kb.row(
        btn("🤖 حذف بوتات الاستضافة", callback_data="adm_bot_manager", style="danger"),
        btn("⚡ تسريع البوت", callback_data="adm_speedup", style="success"),
    )
    kb.row(
        btn("🧹 تنظيف مخلفات الاستضافة", callback_data="adm_clean", style="danger"),
        btn("➕ إضافة رصيد", callback_data="adm_add_balance", style="success"),
    )
    kb.row(
        btn("➖ خصم رصيد", callback_data="adm_deduct_balance", style="danger"),
        btn("🔙 رجوع للرئيسية", callback_data="nav_main", style="primary"),
    )
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("⚙️ لوحة الإدارة", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def users_panel(call, page=0):
    users = read_json(USERS_DB)
    user_ids = list(users.keys())
    per_page = 10
    total_pages = max(1, (len(user_ids) + per_page - 1) // per_page)
    page_users = user_ids[page * per_page : (page + 1) * per_page]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for uid in page_users:
        name = str(users[uid].get("first_name", "مستخدم"))[:10]
        kb.add(btn(f"👤 {name}", callback_data=f"uctrl_{uid}", style="primary"))
    nav = []
    if page > 0:
        nav.append(btn("◀️ السابق", callback_data=f"userpage_{page-1}", style="primary"))
    if page < total_pages - 1:
        nav.append(btn("التالي ▶️", callback_data=f"userpage_{page+1}", style="primary"))
    if nav:
        kb.row(*nav)
    kb.add(btn("🔙 رجوع للرئيسية", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("👤 إدارة المستخدمين", f"الصفحة {page+1} من {total_pages}\n👥 الإجمالي: {len(users)}", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def user_panel(call, tuid):
    users = read_json(USERS_DB)
    u = users.get(str(tuid))
    if not u:
        return
    banned = u.get("is_banned", 0) == 1
    vip = is_user_pro(int(tuid))
    exp = "دائم ♾" if (vip and u.get("expiry") in ("LIFETIME", 0, "0")) else (u.get("expiry") or "لا يوجد")
    u_files = [f for f in read_json(FILES_DB).values() if str(f.get("user_id")) == str(tuid)]
    vip_label = "VIP 👑" if vip else "مجاني 🆓"
    ban_label = "محظور ❌" if banned else "نشط ✅"
    uname_val = u.get("username") or "لا يوجد"
    text = (
        f"🆔 الآيدي: <code>{tuid}</code>\n"
        f"🔗 المعرف: @{uname_val}\n"
        f"💰 النقاط: <code>{u.get('points', 0)}</code>\n"
        f"💎 الرتبة: {vip_label}\n"
        f"⏰ صلاحية VIP: {exp}\n"
        f"📁 ملفاته: {len(u_files)}\n"
        f"🚫 الحظر: {ban_label}"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("🔓 فك الحظر" if banned else "🚫 حظر المستخدم", callback_data=f"ban_{tuid}", style="success" if banned else "danger"),
        btn("🆓 سحب VIP" if vip else "💎 منح VIP", callback_data=f"pro_{tuid}", style="danger" if vip else "success"),
    )
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="adm_users", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("👤 تحكم بالمستخدم", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def ban_toggle(call, tuid):
    with db_lock:
        users = read_json(USERS_DB)
        if str(tuid) in users:
            curr = users[str(tuid)].get("is_banned", 0)
            users[str(tuid)]["is_banned"] = 0 if curr == 1 else 1
            write_json(USERS_DB, users)
            bot.answer_callback_query(call.id, "✅ تم تحديث حالة الحظر.")
            user_panel(call, tuid)


def pro_grant_step(msg, tuid, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "أرسل رقماً صحيحاً للأيام."), back_kb("adm_users"), effect_id=FIRE_EFFECT_ID)
    days = int(msg.text.strip())
    with db_lock:
        users = read_json(USERS_DB)
        u = users.setdefault(str(tuid), {"points": 0.0, "balance": 0.0, "join_date": str(datetime.now().date()), "is_banned": 0})
        u["expiry"] = "LIFETIME" if days == 0 else (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        write_json(USERS_DB, users)
    send_msg(msg.chat.id, deco("✅ تم منح VIP", f"تم منح VIP للمستخدم <code>{tuid}</code>."), back_kb("adm_users"), effect_id=FIRE_EFFECT_ID)


def pro_remove(call, tuid):
    with db_lock:
        users = read_json(USERS_DB)
        if str(tuid) in users:
            users[str(tuid)]["expiry"] = None
            write_json(USERS_DB, users)
            bot.answer_callback_query(call.id, "✅ تم سحب VIP.")
            user_panel(call, tuid)


def bot_manager_panel(call):
    files = read_json(FILES_DB)
    if not files:
        return bot.answer_callback_query(call.id, "🤖 لا توجد بوتات مسجلة!", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for fid, f in files.items():
        running = fid in active_processes and active_processes[fid].poll() is None
        icon = "🟢 يعمل" if running else "🔴 موقوف"
        lbl = str(f.get("stored_name") or f.get("file_name", "?"))[:20]
        kb.add(btn(f"{icon} - {lbl}", callback_data=f"botact_menu_{fid}", style="primary"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("🤖 إدارة البوتات", f"الإجمالي: {len(files)}", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def handle_bot_action(call, action, fid):
    with db_lock:
        files = read_json(FILES_DB)
        f = files.get(fid)
        if not f:
            return bot.answer_callback_query(call.id, "❌ البوت غير موجود!")
        if action == "menu":
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(btn("▶️ تشغيل", callback_data=f"botact_run_{fid}", style="success"), btn("⏸ إيقاف", callback_data=f"botact_stop_{fid}", style="danger"))
            kb.add(btn("📥 تحميل", callback_data=f"botact_dl_{fid}", style="primary"), btn("🗑️ حذف", callback_data=f"botact_del_{fid}", style="danger"))
            kb.add(btn("🔙 رجوع", callback_data="adm_bot_manager", style="primary"))
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            return send_msg(call.message.chat.id, deco("🤖 إدارة البوت", f"الملف: <b>{escape(str(f.get('file_name')))}</b>\nالآيدي: <code>{f.get('user_id')}</code>", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)
        if action == "run":
            start_script(fid)
            bot.answer_callback_query(call.id, "✅ تم التشغيل.")
            return bot_manager_panel(call)
        if action == "stop":
            stop_script(fid)
            bot.answer_callback_query(call.id, "⏸ تم الإيقاف.")
            return bot_manager_panel(call)
        if action == "dl":
            return download_file(call, fid)
        if action == "del":
            stop_script(fid)
            try:
                os.remove(os.path.join(ENCRYPTED_DIR, f"{fid}.enc"))
            except Exception:
                pass
            files.pop(fid, None)
            write_json(FILES_DB, files)
            bot.answer_callback_query(call.id, "🗑️ تم الحذف.")
            return bot_manager_panel(call)


def admin_stats_view(call):
    users = read_json(USERS_DB)
    files = read_json(FILES_DB)
    active_bots = sum(1 for fid in active_processes if active_processes[fid].poll() is None)
    total_bal = sum(float(u.get("balance", 0.0)) for u in users.values())
    total_pts = sum(float(u.get("points", 0)) for u in users.values())
    text = (
        f"📊 <b>إحصائيات الاستضافة الكاملة — {escape(PAGE_BRAND_NAME)}:</b>\n\n"
        f"👥 المستخدمون: <code>{len(users)}</code>\n"
        f"💰 إجمالي الأرصدة: <code>{total_bal:.2f} ₽</code>\n"
        f"💎 إجمالي النقاط: <code>{total_pts}</code>\n"
        f"📁 الملفات المرفوعة: <code>{len(files)}</code>\n"
        f"🟢 البوتات النشطة: <code>{active_bots}</code>"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("📊 الإحصائيات الشاملة", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def admins_panel(call):
    uid = call.from_user.id
    admins = get_admins()
    text = f"👮 قائمة المشرفين ({len(admins)}):\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    if is_main_admin(uid):
        kb.add(btn("➕ إضافة مشرف جديد", callback_data="add_admin", style="success"))
    for aid in admins:
        owner_mark = "👑" if aid in (OWNER_ID, ADMIN_ID) else "👮"
        text += f"{owner_mark} <code>{aid}</code>\n"
        if aid not in (OWNER_ID, ADMIN_ID) and is_main_admin(uid):
            kb.add(btn(f"🗑️ إزالة {aid}", callback_data=f"rmadmin_{aid}", style="danger"))
    kb.add(btn("🔙 رجوع للرئيسية", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("👮 المشرفين", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def add_admin_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    if not is_main_admin(uid) or not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح أو لا تملك الصلاحية."), back_kb("adm_admins"), effect_id=FIRE_EFFECT_ID)
    new_id = int(msg.text.strip())
    txt = f"✅ تم إضافة المشرف <code>{new_id}</code>." if add_admin(new_id) else "❌ هذا المستخدم مشرف مسبقاً!"
    send_msg(msg.chat.id, deco("👮 إضافة مشرف", txt), back_kb("adm_admins"), effect_id=FIRE_EFFECT_ID)


def channels_panel(call):
    channels = get_settings().get("channels", [])
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn("➕ إضافة قناة اشتراك", callback_data="add_channel", style="success"))
    for i, ch in enumerate(channels):
        kb.add(btn(f"🗑️ حذف {ch['name']}", callback_data=f"delch_{i}", style="danger"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    text = f"📊 القنوات الإجبارية: {len(channels)}"
    for ch in channels:
        text += f"\n📢 {escape(str(ch['name']))} ({escape(str(ch['username']))})"
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_msg(call.message.chat.id, deco("📢 قنوات الاشتراك الإجباري", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)


def add_channel_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    username = (msg.text or "").strip()
    if not username.startswith("@"):
        return send_msg(msg.chat.id, deco("❌ خطأ", "يجب أن يبدأ معرف القناة بـ @"), back_kb("adm_channels"), effect_id=FIRE_EFFECT_ID)
    try:
        chat = bot.get_chat(username)
        with db_lock:
            st = get_settings()
            st["channels"] = st.get("channels", []) + [{"username": username, "name": chat.title or username}]
            save_settings(st)
        send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم إضافة القناة: {escape(str(chat.title or username))}"), back_kb("adm_channels"), effect_id=FIRE_EFFECT_ID)
    except Exception:
        send_msg(msg.chat.id, deco("❌ خطأ", "تعذر العثور على القناة!"), back_kb("adm_channels"), effect_id=FIRE_EFFECT_ID)


def del_channel(call, index):
    with db_lock:
        st = get_settings()
        channels = st.get("channels", [])
        if 0 <= index < len(channels):
            channels.pop(index)
            st["channels"] = channels
            save_settings(st)
            bot.answer_callback_query(call.id, "✅ تم حذف القناة.")
    channels_panel(call)


def broadcast_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    uids = list(read_json(USERS_DB).keys())
    wait = send_msg(msg.chat.id, deco("📢 إذاعة عامة", f"⏳ جاري الإرسال إلى {len(uids)} مستخدم..."), effect_id=FIRE_EFFECT_ID)
    markup = build_keyboard([[{"text": "👨‍💻 مراسلة المطور", "url": DEV_TELEGRAM, "style": "primary"}]])
    success, failed = 0, 0
    body_txt = escape(msg.text or msg.caption or "")
    txt = f"<b>{body_txt}</b>\n\n<blockquote>إذاعة من إدارة {escape(PAGE_BRAND_NAME)}</blockquote>"
    for user_id in uids:
        try:
            if msg.content_type == "photo":
                bot.send_photo(user_id, msg.photo[-1].file_id, caption=txt, parse_mode="HTML", reply_markup=markup)
            elif msg.content_type == "document":
                bot.send_document(user_id, msg.document.file_id, caption=txt, parse_mode="HTML", reply_markup=markup)
            else:
                bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup)
            success += 1
            time.sleep(0.02)
        except Exception:
            failed += 1
    try:
        bot.delete_message(msg.chat.id, wait.message_id)
    except Exception:
        pass
    send_msg(msg.chat.id, deco("📢 إذاعة عامة", f"✅ تم الإرسال: {success}\n❌ فشل: {failed}"), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)


def channels_broadcast_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    channels = get_settings().get("channels", [])
    if not channels:
        return send_msg(msg.chat.id, deco("❌ خطأ", "لا توجد قنوات مسجلة."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    markup = build_keyboard([
        [{"text": "👨‍💻 مراسلة المطور", "url": DEV_TELEGRAM, "style": "primary"}],
        [{"text": "📢 قناة التحديث", "url": CHANNEL_EHAB_LINK, "style": "success"}],
    ])
    body_txt = escape(msg.text or msg.caption or "")
    txt = f"<b>{body_txt}</b>\n\n<blockquote>إذاعة للقنوات الرسمية — {escape(PAGE_BRAND_NAME)}</blockquote>"
    success, failed = 0, 0
    for ch in channels:
        try:
            bot.send_message(ch["username"], txt, parse_mode="HTML", reply_markup=markup)
            success += 1
        except Exception:
            failed += 1
    send_msg(msg.chat.id, deco("📢 إذاعة للقنوات", f"✅ تم النشر في {success} قناة\n❌ فشل: {failed}"), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)


def admin_ban_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    target_id = msg.text.strip()
    ban_user_for_security(int(target_id), "حظر إداري بواسطة الأدمن")
    send_msg(msg.chat.id, deco("✅ تم الحظر", f"تم حظر الآيدي <code>{target_id}</code>."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)


def admin_unban_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    target_id = msg.text.strip()
    with db_lock:
        users = read_json(USERS_DB)
        if target_id in users:
            users[target_id]["is_banned"] = 0
            write_json(USERS_DB, users)
            send_msg(msg.chat.id, deco("✅ تم فك الحظر", f"تم فك الحظر عن <code>{target_id}</code>."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        else:
            send_msg(msg.chat.id, deco("❌ خطأ", "الآيدي غير موجود."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)


def admin_add_balance_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    with state_lock:
        admin_steps[uid] = {"target_id": msg.text.strip()}
    m = send_msg(msg.chat.id, deco("➕ إضافة رصيد", f"المستخدم: <code>{msg.text.strip()}</code>\nأرسل كمية النقاط:"), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, admin_add_balance_amount_step, m.message_id)


def admin_add_balance_amount_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    with state_lock:
        target_id = admin_steps.pop(uid, {}).get("target_id")
    if not target_id or not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "بيانات غير صحيحة."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    amount = int(msg.text.strip())
    with db_lock:
        users = read_json(USERS_DB)
        if target_id in users:
            users[target_id]["points"] = float(users[target_id].get("points", 0.0)) + amount
            users[target_id]["balance"] = float(users[target_id].get("balance", 0.0)) + float(amount)
            write_json(USERS_DB, users)
            send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم إضافة {amount} للمستخدم <code>{target_id}</code>."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        else:
            send_msg(msg.chat.id, deco("❌ خطأ", "المستخدم غير موجود."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)


def admin_deduct_balance_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    if not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    with state_lock:
        admin_steps[uid] = {"target_id": msg.text.strip()}
    m = send_msg(msg.chat.id, deco("➖ خصم رصيد", f"المستخدم: <code>{msg.text.strip()}</code>\nأرسل كمية الخصم:"), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, admin_deduct_balance_amount_step, m.message_id)


def admin_deduct_balance_amount_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    with state_lock:
        target_id = admin_steps.pop(uid, {}).get("target_id")
    if not target_id or not msg.text or not msg.text.strip().isdigit():
        return send_msg(msg.chat.id, deco("❌ خطأ", "بيانات غير صحيحة."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    amount = int(msg.text.strip())
    with db_lock:
        users = read_json(USERS_DB)
        if target_id in users:
            users[target_id]["points"] = max(0.0, float(users[target_id].get("points", 0.0)) - amount)
            users[target_id]["balance"] = max(0.0, float(users[target_id].get("balance", 0.0)) - float(amount))
            write_json(USERS_DB, users)
            send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم خصم {amount} من المستخدم <code>{target_id}</code>."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        else:
            send_msg(msg.chat.id, deco("❌ خطأ", "المستخدم غير موجود."), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)


# ============ صفحة تسجيل الدخول ============
LOGIN_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ابن اليمن — منصة التحكم السحابية وإدارة الموارد</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script>
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          fontFamily: {
            sans: ["Cairo", "Tajawal", "sans-serif"],
            mono: ["JetBrains Mono", "monospace"],
          },
          colors: {
            obsidian: "#06080f",
            midnight: "#0b101d",
            slateCard: "#101729",
            slateElevated: "#162038",
            slateBorder: "#22304f",
          }
        }
      }
    };
  </script>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: "Cairo", "Tajawal", sans-serif;
      background-color: #06080f;
      color: #f1f5f9;
      overflow-x: hidden;
    }
    .font-mono-code { font-family: "JetBrains Mono", monospace; }
    .wisp-backdrop {
      background-image:
        radial-gradient(circle at 12% 10%, rgba(99, 102, 241, 0.14), transparent 36%),
        radial-gradient(circle at 88% 8%, rgba(6, 182, 212, 0.12), transparent 36%),
        radial-gradient(circle at 50% 95%, rgba(16, 185, 129, 0.06), transparent 45%),
        linear-gradient(to right, rgba(148, 163, 184, 0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(148, 163, 184, 0.03) 1px, transparent 1px);
      background-size: 100% 100%, 100% 100%, 100% 100%, 36px 36px, 36px 36px;
    }
    .btn-electric {
      background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #06b6d4 100%);
      transition: transform 0.18s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }
    .btn-electric:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 26px -6px rgba(99, 102, 241, 0.45);
      filter: brightness(1.06);
    }
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: #090d18; }
    ::-webkit-scrollbar-thumb { background: #243354; border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: #364b7a; }
    @keyframes pulseDot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.45; transform: scale(1.2); }
    }
    .dot-pulse { animation: pulseDot 2s infinite ease-in-out; }
  </style>
</head>
<body class="wisp-backdrop min-h-screen antialiased selection:bg-indigo-500/30 selection:text-cyan-200">
  <div id="toastStack" class="fixed bottom-5 left-5 z-[70] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none"></div>
  <div id="mobileBackdrop" onclick="setMobileDrawer(false)" class="fixed inset-0 bg-black/75 backdrop-blur-xs z-30 hidden lg:hidden"></div>

  <div class="flex min-h-screen w-full">
    <aside id="appSidebar" class="fixed lg:sticky top-0 right-0 z-40 h-screen w-72 bg-midnight/95 backdrop-blur-xl border-l border-slateBorder flex flex-col justify-between transition-transform duration-300 translate-x-full lg:translate-x-0">
      <div class="overflow-y-auto">
        <div class="px-5 py-4 border-b border-slateBorder flex items-center justify-between">
          <a href="/" class="flex items-center gap-3 group">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-sky-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform">
              <i data-lucide="cpu" class="w-5 h-5 text-white"></i>
            </div>
            <div>
              <div class="flex items-center gap-1.5">
                <span class="font-extrabold text-lg tracking-tight text-white">ابن اليمن</span>
                <span class="text-[10px] font-mono-code font-bold px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">v5.0</span>
              </div>
              <p class="text-[11px] text-slate-400">مركز العمليات والاستضافة الموزعة</p>
            </div>
          </a>
          <button onclick="setMobileDrawer(false)" class="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slateElevated" aria-label="إغلاق القائمة">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>

        <nav class="p-3.5 space-y-1" aria-label="أقسام لوحة التحكم">
          <button data-tab="overview" onclick="navigateTo('overview')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold bg-indigo-500/15 text-white border border-indigo-500/35 transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="gauge" class="w-4 h-4 text-cyan-400"></i>
              <span>نظرة عامة والتحكم</span>
            </span>
            <span class="w-2 h-2 rounded-full bg-emerald-400 dot-pulse"></span>
          </button>

          <button data-tab="workloads" onclick="navigateTo('workloads')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="server" class="w-4 h-4 text-indigo-400"></i>
              <span>أحمال العمل والعقد</span>
            </span>
            <span id="navWorkloadsBadge" class="font-mono-code text-xs px-2 py-0.5 rounded-md bg-slateElevated text-slate-200 border border-slateBorder">0</span>
          </button>

          <button data-tab="console" onclick="navigateTo('console')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="terminal" class="w-4 h-4 text-emerald-400"></i>
              <span>الطرفية والسجلات الحية</span>
            </span>
            <span class="font-mono-code text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">LIVE</span>
          </button>

          <button data-tab="files" onclick="navigateTo('files')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="folder-code" class="w-4 h-4 text-amber-400"></i>
              <span>مدير الملفات والمحرر</span>
            </span>
          </button>

          <button data-tab="databases" onclick="navigateTo('databases')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="database" class="w-4 h-4 text-cyan-400"></i>
              <span>قواعد البيانات والتخزين</span>
            </span>
          </button>

          <button data-tab="network" onclick="navigateTo('network')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="globe" class="w-4 h-4 text-sky-400"></i>
              <span>الشبكة، النطاقات والإضافات</span>
            </span>
          </button>

          <button data-tab="billing" onclick="navigateTo('billing')" class="nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer">
            <span class="flex items-center gap-3">
              <i data-lucide="wallet" class="w-4 h-4 text-rose-400"></i>
              <span>الفوترة، الحصص والإعدادات</span>
            </span>
          </button>
        </nav>
      </div>

      <div class="p-4 border-t border-slateBorder space-y-3 bg-midnight/90">
        <div class="p-3 rounded-xl bg-slateCard border border-slateBorder">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <span class="text-slate-400">العقدة النشطة</span>
            <span class="font-mono-code text-cyan-300 font-semibold">yemen-cloud-01</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-slate-400">الرصيد المتاح</span>
            <span id="sidebarPointsBadge" class="font-mono-code font-bold text-emerald-300">0 pt</span>
          </div>
        </div>

        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center font-mono-code text-xs font-bold text-cyan-300 shrink-0">
              YB
            </div>
            <div class="min-w-0">
              <p id="sidebarUserName" class="text-xs font-bold text-white truncate">مستخدم ابن اليمن</p>
              <p id="sidebarUserMeta" class="font-mono-code text-[11px] text-slate-400 truncate">@user</p>
            </div>
          </div>
          <button onclick="logoutWebAccount()" title="تسجيل الخروج" class="px-2 py-1 rounded-lg text-[11px] font-bold bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 cursor-pointer shrink-0">
            خروج
          </button>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col min-w-0">
      <header class="sticky top-0 z-20 bg-obsidian/85 backdrop-blur-xl border-b border-slateBorder px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3 min-w-0">
          <button onclick="setMobileDrawer(true)" class="lg:hidden p-2.5 rounded-xl bg-slateCard border border-slateBorder text-slate-200 hover:bg-slateElevated cursor-pointer" aria-label="فتح القائمة">
            <i data-lucide="menu" class="w-5 h-5"></i>
          </button>
          <div class="min-w-0">
            <div class="flex items-center gap-2.5 flex-wrap">
              <h1 id="activeViewTitle" class="text-lg sm:text-xl font-extrabold text-white truncate">نظرة عامة والتحكم — ابن اليمن</h1>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/25">
                <span class="w-2 h-2 rounded-full bg-emerald-400 dot-pulse"></span>
                <span>ابن اليمن • متصل ومزامن</span>
              </span>
            </div>
            <p id="activeViewSubtitle" class="text-xs text-slate-400 hidden sm:block mt-0.5">مراقبة الأداء اللحظي، رفع الملفات من الهاتف، وإدارة السكربتات الفورية</p>
          </div>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <button onclick="refreshAllFromBackend(true)" class="p-2.5 rounded-xl bg-slateCard hover:bg-slateElevated border border-slateBorder text-slate-300 hover:text-cyan-300 transition-colors cursor-pointer" title="تحديث البيانات">
            <i id="topRefreshIcon" data-lucide="refresh-cw" class="w-4 h-4"></i>
          </button>
          <button onclick="openPhoneUploadModal()" class="btn-electric inline-flex items-center gap-2 px-3.5 sm:px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold text-white cursor-pointer">
            <i data-lucide="smartphone-nfc" class="w-4 h-4"></i>
            <span>رفع ملف من الهاتف</span>
          </button>
        </div>
      </header>

      <main class="flex-1 px-4 sm:px-6 lg:px-8 py-6 space-y-6 max-w-[1640px] w-full mx-auto">
        <section id="view-overview" class="app-view space-y-6">
          <div class="p-5 rounded-2xl bg-slateCard/95 border border-indigo-500/35 space-y-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 class="text-base sm:text-lg font-extrabold text-white flex items-center gap-2">
                  <i data-lucide="upload-cloud" class="w-5 h-5 text-cyan-400"></i>
                  <span>رفع السكربتات (.py / .js / .zip) مباشرة من ذاكرة الهاتف</span>
                </h2>
                <p class="text-xs text-slate-400">يتم فحص الكود أمنياً وتشفيره بـ AES وحفظه باسم إنجليزي وربطه بحسابك في ابن اليمن</p>
              </div>
              <span id="uploadPriceHint" class="font-mono-code text-xs px-3 py-1 rounded-xl bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">السعر: 1.0 نقطة / ساعة</span>
            </div>

            <form onsubmit="submitPhoneFileUpload(event)" class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
              <div class="md:col-span-6">
                <label class="block text-xs font-bold text-slate-300 mb-1.5">اختر ملفاً من ذاكرة الهاتف (.py, .js, .zip)</label>
                <input
                  id="phoneFileInput"
                  type="file"
                  accept=".py,.js,.zip,application/zip,text/plain,text/javascript"
                  required
                  class="w-full px-3 py-2 rounded-xl bg-obsidian border border-slateBorder text-xs text-slate-200 file:ml-3 file:px-3 file:py-1.5 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                />
              </div>
              <div class="md:col-span-3">
                <label class="block text-xs font-bold text-slate-300 mb-1.5">عدد الساعات</label>
                <input id="phoneUploadHours" type="number" min="1" max="720" value="1" required class="w-full px-3.5 py-2 rounded-xl bg-obsidian border border-slateBorder font-mono-code text-xs sm:text-sm text-white" />
              </div>
              <div class="md:col-span-3">
                <button type="submit" class="btn-electric w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-bold text-white inline-flex items-center justify-center gap-2 cursor-pointer">
                  <i data-lucide="send" class="w-4 h-4"></i>
                  <span>رفع وتشغيل</span>
                </button>
              </div>
            </form>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6 gap-4">
            <div class="p-4 rounded-2xl bg-slateCard border border-slateBorder">
              <div class="flex items-center justify-between mb-2.5">
                <span class="text-xs font-semibold text-slate-400">حمل المعالج (CPU)</span>
                <span class="p-1.5 rounded-lg bg-indigo-500/15 text-indigo-400"><i data-lucide="cpu" class="w-4 h-4"></i></span>
              </div>
              <div class="flex items-baseline justify-between">
                <span id="kpiCpu" class="font-mono-code text-xl font-bold text-white">0%</span>
                <span id="kpiCores" class="font-mono-code text-[11px] text-emerald-400">vCPU</span>
              </div>
              <div class="mt-2.5 w-full h-1.5 rounded-full bg-obsidian overflow-hidden">
                <div id="kpiCpuBar" class="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-500" style="width: 0%"></div>
              </div>
            </div>

            <div class="p-4 rounded-2xl bg-slateCard border border-slateBorder">
              <div class="flex items-center justify-between mb-2.5">
                <span class="text-xs font-semibold text-slate-400">الذاكرة (RAM)</span>
                <span class="p-1.5 rounded-lg bg-cyan-500/15 text-cyan-400"><i data-lucide="memory-stick" class="w-4 h-4"></i></span>
              </div>
              <div class="flex items-baseline justify-between">
                <span id="kpiRam" class="font-mono-code text-xl font-bold text-white">0 GB</span>
                <span id="kpiRamSub" class="font-mono-code text-[11px] text-cyan-300">/ 0 GB</span>
              </div>
              <div class="mt-2.5 w-full h-1.5 rounded-full bg-obsidian overflow-hidden">
                <div id="kpiRamBar" class="h-full bg-gradient-to-r from-cyan-500 to-indigo-400 transition-all duration-500" style="width: 0%"></div>
              </div>
            </div>

            <div class="p-4 rounded-2xl bg-slateCard border border-slateBorder">
              <div class="flex items-center justify-between mb-2.5">
                <span class="text-xs font-semibold text-slate-400">التخزين والقرص</span>
                <span class="p-1.5 rounded-lg bg-amber-500/15 text-amber-400"><i data-lucide="hard-drive" class="w-4 h-4"></i></span>
              </div>
              <div class="flex items-baseline justify-between">
                <span id="kpiDiskIo" class="font-mono-code text-xl font-bold text-white">0%</span>
                <span id="kpiDiskFree" class="font-mono-code text-[11px] text-amber-300">Free</span>
              </div>
              <div class="mt-2.5 w-full h-1.5 rounded-full bg-obsidian overflow-hidden">
                <div id="kpiDiskBar" class="h-full bg-gradient-to-r from-amber-500 to-yellow-300 transition-all duration-500" style="width: 0%"></div>
              </div>
            </div>

            <div class="p-4 rounded-2xl bg-slateCard border border-slateBorder">
              <div class="flex items-center justify-between mb-2.5">
                <span class="text-xs font-semibold text-slate-400">تدفق الشبكة</span>
                <span class="p-1.5 rounded-lg bg-emerald-500/15 text-emerald-400"><i data-lucide="activity" class="w-4 h-4"></i></span>
              </div>
              <div class="flex items-baseline justify-between">
                <span id="kpiNet" class="font-mono-code text-xl font-bold text-white">640 Mbps</span>
                <span class="font-mono-code text-[11px] text-emerald-400">HTTP/3</span>
              </div>
              <div class="mt-2.5 w-full h-1.5 rounded-full bg-obsidian overflow-hidden">
                <div id="kpiNetBar" class="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-500" style="width: 60%"></div>
              </div>
            </div>

            <div class="p-4 rounded-2xl bg-slateCard border border-slateBorder">
              <div class="flex items-center justify-between mb-2.5">
                <span class="text-xs font-semibold text-slate-400">الملفات والسكربتات</span>
                <span class="p-1.5 rounded-lg bg-indigo-500/15 text-indigo-400"><i data-lucide="box" class="w-4 h-4"></i></span>
              </div>
              <div class="flex items-baseline justify-between">
                <span id="kpiActiveContainers" class="font-mono-code text-xl font-bold text-white">0 / 0</span>
                <span class="font-mono-code text-[11px] text-emerald-400">ACTIVE</span>
              </div>
              <p class="mt-2.5 text-[11px] text-slate-400">مزامنة مباشرة مع الاستضافة</p>
            </div>

            <div class="p-4 rounded-2xl bg-slateCard border border-slateBorder">
              <div class="flex items-center justify-between mb-2.5">
                <span class="text-xs font-semibold text-slate-400">وضع السيرفر</span>
                <span class="p-1.5 rounded-lg bg-cyan-500/15 text-cyan-400"><i data-lucide="clock" class="w-4 h-4"></i></span>
              </div>
              <div class="flex items-baseline justify-between">
                <span id="kpiServerMode" class="font-mono-code text-sm font-bold text-emerald-300">ONLINE</span>
                <span class="font-mono-code text-[11px] text-slate-400">ابن اليمن</span>
              </div>
              <p class="mt-2.5 text-[11px] text-slate-400">حماية وتشفير مستمر</p>
            </div>
          </div>

          <div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <div class="p-5 rounded-2xl bg-slateCard border border-slateBorder space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
                    <span>منحنى استهلاك المعالج (CPU Telemetry)</span>
                  </h2>
                  <p class="text-xs text-slate-400">قراءات حية من سيرفر ابن اليمن</p>
                </div>
                <div class="flex items-center gap-1 bg-obsidian p-1 rounded-xl border border-slateBorder">
                  <button data-range="15m" onclick="setTelemetryRange('15m')" class="range-btn px-2.5 py-1 rounded-lg font-mono-code text-xs font-bold bg-indigo-500/25 text-indigo-200 cursor-pointer">15m</button>
                  <button data-range="1h" onclick="setTelemetryRange('1h')" class="range-btn px-2.5 py-1 rounded-lg font-mono-code text-xs font-semibold text-slate-400 hover:text-white cursor-pointer">1h</button>
                  <button data-range="24h" onclick="setTelemetryRange('24h')" class="range-btn px-2.5 py-1 rounded-lg font-mono-code text-xs font-semibold text-slate-400 hover:text-white cursor-pointer">24h</button>
                </div>
              </div>
              <div class="relative rounded-xl bg-obsidian/90 border border-slateBorder/80 p-3">
                <svg id="cpuChartSvg" viewBox="0 0 600 180" class="w-full h-44 overflow-visible">
                  <defs>
                    <linearGradient id="cpuAreaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#6366f1" stop-opacity="0.45" />
                      <stop offset="100%" stop-color="#6366f1" stop-opacity="0.02" />
                    </linearGradient>
                  </defs>
                  <line x1="0" y1="45" x2="600" y2="45" stroke="#1e293b" stroke-dasharray="4 4" />
                  <line x1="0" y1="90" x2="600" y2="90" stroke="#1e293b" stroke-dasharray="4 4" />
                  <line x1="0" y1="135" x2="600" y2="135" stroke="#1e293b" stroke-dasharray="4 4" />
                  <path id="cpuAreaPath" fill="url(#cpuAreaGrad)" d="" />
                  <path id="cpuLinePath" fill="none" stroke="#818cf8" stroke-width="2.5" stroke-linecap="round" d="" />
                </svg>
                <div class="flex items-center justify-between text-[11px] font-mono-code text-slate-500 mt-1 px-1">
                  <span>-100%</span>
                  <span id="cpuChartLabel">النطاق: 15m</span>
                  <span>الآن</span>
                </div>
              </div>
            </div>

            <div class="p-5 rounded-2xl bg-slateCard border border-slateBorder space-y-4">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 class="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                    <span>منحنى استهلاك الذاكرة (Memory Allocation)</span>
                  </h2>
                  <p class="text-xs text-slate-400">توزيع الذاكرة الحية للعمليات والسكربتات</p>
                </div>
                <span class="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/25 text-xs font-mono-code" id="memPeakBadge">Peak: 0 GB</span>
              </div>
              <div class="relative rounded-xl bg-obsidian/90 border border-slateBorder/80 p-3">
                <svg id="memChartSvg" viewBox="0 0 600 180" class="w-full h-44 overflow-visible">
                  <defs>
                    <linearGradient id="memAreaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.42" />
                      <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.02" />
                    </linearGradient>
                  </defs>
                  <line x1="0" y1="45" x2="600" y2="45" stroke="#1e293b" stroke-dasharray="4 4" />
                  <line x1="0" y1="90" x2="600" y2="90" stroke="#1e293b" stroke-dasharray="4 4" />
                  <line x1="0" y1="135" x2="600" y2="135" stroke="#1e293b" stroke-dasharray="4 4" />
                  <path id="memAreaPath" fill="url(#memAreaGrad)" d="" />
                  <path id="memLinePath" fill="none" stroke="#22d3ee" stroke-width="2.5" stroke-linecap="round" d="" />
                </svg>
                <div class="flex items-center justify-between text-[11px] font-mono-code text-slate-500 mt-1 px-1">
                  <span>0 GB</span>
                  <span id="memChartLabel">النطاق: 15m</span>
                  <span id="memMaxAxis">Max</span>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-2xl bg-slateCard border border-slateBorder overflow-hidden">
            <div class="px-5 py-4 border-b border-slateBorder flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 class="text-base font-bold text-white">الملفات والسكربتات المستضافة في ابن اليمن</h2>
                <p class="text-xs text-slate-400">تشغيل وإيقاف وعرض السجلات وحذف الملفات مباشرة من السيرفر</p>
              </div>
              <button onclick="navigateTo('workloads')" class="text-xs font-bold text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1 cursor-pointer">
                <span>إدارة كافة السكربتات</span>
                <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
              </button>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-right border-collapse">
                <thead>
                  <tr class="bg-slateElevated/60 text-slate-400 text-xs font-bold border-b border-slateBorder">
                    <th class="py-3 px-4">الاسم / الاسم الإنجليزي</th>
                    <th class="py-3 px-4">النوع</th>
                    <th class="py-3 px-4">الحالة</th>
                    <th class="py-3 px-4">تاريخ الرفع</th>
                    <th class="py-3 px-4 text-center">إجراءات</th>
                  </tr>
                </thead>
                <tbody id="overviewWorkloadsBody" class="divide-y divide-slateBorder/60 text-sm"></tbody>
              </table>
            </div>
          </div>
        </section>

        <section id="view-workloads" class="app-view hidden space-y-6">
          <div class="p-5 rounded-2xl bg-slateCard border border-slateBorder flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h2 class="text-lg font-bold text-white">مدير السكربتات والعمليات — ابن اليمن</h2>
              <p class="text-xs text-slate-400">بحث وتصفية وتشغيل وإيقاف ومشاهدة السجلات الحية لملفاتك</p>
            </div>
            <div class="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2.5">
              <input id="workloadSearch" type="text" oninput="renderWorkloadsManager()" placeholder="بحث باسم الملف..." class="px-3.5 py-2 rounded-xl bg-obsidian border border-slateBorder text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500" />
              <select id="workloadStatusFilter" onchange="renderWorkloadsManager()" class="px-3 py-2 rounded-xl bg-obsidian border border-slateBorder text-xs sm:text-sm text-slate-200 cursor-pointer">
                <option value="all">جميع الحالات</option>
                <option value="running">يعمل الآن</option>
                <option value="pending">قيد المراجعة</option>
                <option value="stopped">متوقف</option>
              </select>
            </div>
          </div>
          <div id="workloadsCardsGrid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"></div>
        </section>

        <section id="view-console" class="app-view hidden space-y-4">
          <div class="rounded-2xl bg-slateCard border border-slateBorder overflow-hidden">
            <div class="p-4 sm:p-5 border-b border-slateBorder flex flex-wrap items-center justify-between gap-3">
              <div class="flex flex-wrap items-center gap-2">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono-code text-xs font-bold">
                  <span class="w-2 h-2 rounded-full bg-emerald-400 dot-pulse"></span> LIVE LOGS
                </span>
                <select id="consoleScriptSelect" onchange="loadScriptLogs(this.value)" class="px-3 py-1.5 rounded-xl bg-obsidian border border-slateBorder font-mono-code text-xs text-cyan-300">
                  <option value="">-- اختر سكربت لعرض سجله الحقيقي --</option>
                </select>
              </div>
              <div class="flex items-center gap-2">
                <button onclick="loadScriptLogs(document.getElementById('consoleScriptSelect').value)" class="px-3 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-bold cursor-pointer">تحديث السجل</button>
                <button onclick="copyConsoleLogs()" class="px-3 py-1.5 rounded-xl bg-slateElevated text-xs font-bold text-slate-200 cursor-pointer">نسخ</button>
              </div>
            </div>
            <div id="consoleOutputBox" dir="ltr" class="p-4 sm:p-5 bg-[#04060b] font-mono-code text-xs sm:text-[13px] space-y-1.5 h-[390px] overflow-y-auto text-left"></div>
            <form onsubmit="handleTerminalCommand(event)" dir="ltr" class="p-3.5 bg-midnight border-t border-slateBorder flex items-center gap-2.5">
              <span class="font-mono-code text-xs sm:text-sm font-bold text-cyan-400 shrink-0">yemen@host:~#</span>
              <input id="terminalCmdInput" type="text" autocomplete="off" placeholder="Type command: help, status, ps, clear" class="flex-1 bg-transparent font-mono-code text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none" />
              <button type="submit" class="px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/35 font-mono-code text-xs font-bold cursor-pointer">RUN</button>
            </form>
          </div>
        </section>

        <section id="view-files" class="app-view hidden space-y-5">
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div class="lg:col-span-4 rounded-2xl bg-slateCard border border-slateBorder p-4 space-y-4">
              <div class="flex items-center justify-between pb-3 border-b border-slateBorder">
                <h2 class="text-sm font-bold text-white">ملفاتك المرفوعة على السيرفر</h2>
                <button onclick="openPhoneUploadModal()" class="px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-200 border border-indigo-500/30 text-xs font-bold cursor-pointer">+ رفع ملف</button>
              </div>
              <div id="fileTreeList" dir="ltr" class="space-y-1.5 font-mono-code text-xs text-left"></div>
            </div>

            <div class="lg:col-span-8 rounded-2xl bg-slateCard border border-slateBorder overflow-hidden flex flex-col">
              <div class="px-4 py-3 bg-slateElevated/70 border-b border-slateBorder flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span id="editorActiveFileName" dir="ltr" class="font-mono-code text-xs sm:text-sm font-bold text-white">اختر ملفاً</span>
                  <span id="editorLangBadge" class="font-mono-code text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">CODE</span>
                </div>
                <button onclick="saveActiveFileToServer()" class="btn-electric px-3.5 py-1.5 rounded-lg text-xs font-bold text-white cursor-pointer">حفظ وتشفير على السيرفر</button>
              </div>
              <textarea id="codeEditorTextarea" dir="ltr" spellcheck="false" class="w-full h-80 p-4 bg-[#050811] text-slate-100 font-mono-code text-xs sm:text-[13px] leading-relaxed focus:outline-none"></textarea>
            </div>
          </div>
        </section>

        <section id="view-databases" class="app-view hidden space-y-6">
          <div class="rounded-2xl bg-slateCard border border-slateBorder p-5 space-y-3">
            <h2 class="text-lg font-bold text-white">قواعد البيانات والتخزين المشفر في ابن اليمن</h2>
            <p class="text-xs text-slate-400">البيانات مخزنة محلياً ومشفّرة بـ AES-CBC مع SQLite WAL وملفات JSON الموحدة، ويدعم الفحص التلقائي للأكواد.</p>
            <div id="dbSummaryCards" class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 font-mono-code text-xs"></div>
          </div>
        </section>

        <section id="view-network" class="app-view hidden space-y-6">
          <div class="rounded-2xl bg-slateCard border border-slateBorder p-5 space-y-4">
            <h2 class="text-lg font-bold text-white">مسارات وخدمات ابن اليمن</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono-code text-xs">
              <div class="p-3.5 rounded-xl bg-obsidian border border-slateBorder">
                <p class="text-cyan-300 font-bold">GET /</p>
                <p class="text-slate-400 mt-1">لوحة تحكم منصة ابن اليمن الرئيسية (index.html)</p>
              </div>
              <div class="p-3.5 rounded-xl bg-obsidian border border-slateBorder">
                <p class="text-cyan-300 font-bold">GET /login</p>
                <p class="text-slate-400 mt-1">صفحة تسجيل الدخول وإنشاء حساب جديد</p>
              </div>
              <div class="p-3.5 rounded-xl bg-obsidian border border-slateBorder">
                <p class="text-cyan-300 font-bold">POST /api/upload</p>
                <p class="text-slate-400 mt-1">رفع ملفات (.py / .js / .zip) مباشرة من الهاتف أو المتصفح</p>
              </div>
              <div class="p-3.5 rounded-xl bg-obsidian border border-slateBorder">
                <p class="text-cyan-300 font-bold">GET /api/overview</p>
                <p class="text-slate-400 mt-1">جلب حالة النظام والملفات والرصيد والمستخدم الحالي</p>
              </div>
            </div>
          </div>
        </section>

        <section id="view-billing" class="app-view hidden space-y-6">
          <div class="rounded-2xl bg-slateCard border border-slateBorder p-5 space-y-4">
            <h2 class="text-lg font-bold text-white">بيانات الحساب والرصيد — ابن اليمن</h2>
            <div id="accountBillingBox" class="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono-code text-xs"></div>
          </div>
        </section>
      </main>
    </div>
  </div>

  <div id="phoneUploadModal" class="fixed inset-0 z-50 hidden items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
    <div class="w-full max-w-md rounded-2xl bg-slateCard border border-slateBorder shadow-2xl overflow-hidden">
      <div class="px-5 py-4 border-b border-slateBorder flex items-center justify-between">
        <h3 class="text-base font-bold text-white">رفع ملف من ذاكرة الهاتف — ابن اليمن</h3>
        <button onclick="closePhoneUploadModal()" class="p-1.5 rounded-lg text-slate-400 hover:text-white cursor-pointer"><i data-lucide="x" class="w-4 h-4"></i></button>
      </div>
      <form onsubmit="submitPhoneFileUpload(event)" class="p-5 space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1">الملف (.py, .js, .zip)</label>
          <input id="modalPhoneFileInput" type="file" accept=".py,.js,.zip" required class="w-full px-3 py-2 rounded-xl bg-obsidian border border-slateBorder text-xs text-slate-200 cursor-pointer" />
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1">عدد الساعات</label>
          <input id="modalPhoneHoursInput" type="number" min="1" max="720" value="1" required class="w-full px-3 py-2 rounded-xl bg-obsidian border border-slateBorder font-mono-code text-sm text-white" />
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button type="button" onclick="closePhoneUploadModal()" class="px-4 py-2 rounded-xl bg-slateElevated text-xs font-bold text-slate-300 cursor-pointer">إلغاء</button>
          <button type="submit" class="btn-electric px-4 py-2 rounded-xl text-xs font-bold text-white cursor-pointer">رفع الآن</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    const state = {
      currentTab: "overview",
      telemetryRange: "15m",
      cpuSeries: [22, 26, 30, 28, 34, 31, 29, 35, 32, 30],
      memSeries: [1.1, 1.2, 1.3, 1.25, 1.4, 1.35, 1.3, 1.42, 1.38, 1.36],
      ramTotalGb: 8,
      user: null,
      system: null,
      files: [],
      activeFileId: null,
      logsText: ""
    };

    const viewMeta = {
      overview: { title: "نظرة عامة والتحكم — ابن اليمن", subtitle: "مراقبة الأداء اللحظي، رفع الملفات من الهاتف، وإدارة السكربتات الفورية" },
      workloads: { title: "أحمال العمل والسكربتات — ابن اليمن", subtitle: "تشغيل وإيقاف ومراقبة كافة السكربتات والعمليات" },
      console: { title: "الطرفية والسجلات الحية — ابن اليمن", subtitle: "استعراض السجلات الحقيقية للملفات والأوامر المباشرة" },
      files: { title: "مدير الملفات والمحرر — ابن اليمن", subtitle: "قراءة وتعديل وحفظ الملفات المشفّرة على السيرفر" },
      databases: { title: "قواعد البيانات والتخزين — ابن اليمن", subtitle: "حالة قواعد البيانات والملفات والتشفير" },
      network: { title: "الشبكة والخدمات — ابن اليمن", subtitle: "مسارات API وصفحات ابن اليمن" },
      billing: { title: "الحساب والرصيد — ابن اليمن", subtitle: "رصيد النقاط والرصيد المالي وبيانات المستخدم" }
    };

    document.addEventListener("DOMContentLoaded", () => {
      lucide.createIcons();
      refreshAllFromBackend(false);
      setInterval(() => refreshAllFromBackend(false), 6000);
    });

    function navigateTo(tabName) {
      if (!viewMeta[tabName]) return;
      state.currentTab = tabName;
      document.querySelectorAll(".app-view").forEach(s => s.classList.add("hidden"));
      document.getElementById(`view-${tabName}`)?.classList.remove("hidden");
      document.getElementById("activeViewTitle").textContent = viewMeta[tabName].title;
      document.getElementById("activeViewSubtitle").textContent = viewMeta[tabName].subtitle;
      document.querySelectorAll(".nav-link").forEach(btn => {
        const active = btn.getAttribute("data-tab") === tabName;
        btn.className = active
          ? "nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-bold bg-indigo-500/15 text-white border border-indigo-500/35 transition-all cursor-pointer"
          : "nav-link w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-slateElevated/80 border border-transparent transition-all cursor-pointer";
      });
      setMobileDrawer(false);
      lucide.createIcons();
    }

    function setMobileDrawer(open) {
      const sb = document.getElementById("appSidebar");
      const bd = document.getElementById("mobileBackdrop");
      if (open) { sb.classList.remove("translate-x-full"); bd.classList.remove("hidden"); }
      else { sb.classList.add("translate-x-full"); bd.classList.add("hidden"); }
    }

    async function refreshAllFromBackend(notify = false) {
      const icon = document.getElementById("topRefreshIcon");
      if (notify && icon) icon.classList.add("animate-spin");
      try {
        const res = await fetch("/api/overview");
        if (res.status === 401) {
          window.location.href = "/login";
          return;
        }
        const data = await res.json();
        if (!data.ok) return;

        state.user = data.user;
        state.system = data.system;
        state.files = data.files || [];

        const uName = data.user.display_name || data.user.username || "مستخدم ابن اليمن";
        document.getElementById("sidebarUserName").textContent = uName;
        document.getElementById("sidebarUserMeta").textContent = `@${data.user.username} • ID:${data.user.telegram_id}`;
        document.getElementById("sidebarPointsBadge").textContent = `${data.user.points} pt | ${data.user.balance} ₽`;
        document.getElementById("uploadPriceHint").textContent = `السعر: ${data.upload_price} نقطة / ساعة`;

        const sys = data.system || {};
        const cpu = Number(sys.cpu_percent || 0);
        const ramUsed = Number(sys.ram_used_gb || 0);
        const ramTotal = Math.max(1, Number(sys.ram_total_gb || 4));
        const diskPct = Number(sys.disk_percent || 0);

        state.ramTotalGb = ramTotal;
        state.cpuSeries.push(cpu);
        if (state.cpuSeries.length > 14) state.cpuSeries.shift();
        state.memSeries.push(ramUsed);
        if (state.memSeries.length > 14) state.memSeries.shift();

        document.getElementById("kpiCpu").textContent = `${cpu.toFixed(1)}%`;
        document.getElementById("kpiCpuBar").style.width = `${Math.min(100, cpu)}%`;
        document.getElementById("kpiCores").textContent = `${sys.cpu_count || 1} vCPU`;

        document.getElementById("kpiRam").textContent = `${ramUsed.toFixed(2)} GB`;
        document.getElementById("kpiRamSub").textContent = `/ ${ramTotal.toFixed(1)} GB`;
        document.getElementById("kpiRamBar").style.width = `${Math.min(100, (ramUsed / ramTotal) * 100)}%`;

        document.getElementById("kpiDiskIo").textContent = `${diskPct.toFixed(1)}%`;
        document.getElementById("kpiDiskFree").textContent = `${Number(sys.disk_free_gb || 0).toFixed(1)} GB Free`;
        document.getElementById("kpiDiskBar").style.width = `${Math.min(100, diskPct)}%`;

        const runningCount = state.files.filter(f => f.running).length;
        document.getElementById("kpiActiveContainers").textContent = `${runningCount} / ${state.files.length}`;
        document.getElementById("navWorkloadsBadge").textContent = String(state.files.length);
        document.getElementById("kpiServerMode").textContent = sys.bot_locked ? "MAINTENANCE" : "ONLINE";
        document.getElementById("memMaxAxis").textContent = `${ramTotal.toFixed(1)} GB`;
        document.getElementById("memPeakBadge").textContent = `Peak: ${Math.max(...state.memSeries).toFixed(2)} GB`;

        renderCharts();
        renderOverviewFiles();
        renderWorkloadsManager();
        renderFileTree();
        populateConsoleSelect();
        renderDbAndBilling();

        if (notify) showToast("تم تحديث بيانات ابن اليمن بنجاح", "success");
      } catch (err) {
        if (notify) showToast("تعذر الاتصال بالخادم", "warning");
      } finally {
        if (icon) setTimeout(() => icon.classList.remove("animate-spin"), 350);
      }
    }

    function setTelemetryRange(range) {
      state.telemetryRange = range;
      document.getElementById("cpuChartLabel").textContent = `النطاق: ${range}`;
      document.getElementById("memChartLabel").textContent = `النطاق: ${range}`;
      document.querySelectorAll(".range-btn").forEach(b => {
        const active = b.getAttribute("data-range") === range;
        b.className = active
          ? "range-btn px-2.5 py-1 rounded-lg font-mono-code text-xs font-bold bg-indigo-500/25 text-indigo-200 cursor-pointer"
          : "range-btn px-2.5 py-1 rounded-lg font-mono-code text-xs font-semibold text-slate-400 hover:text-white cursor-pointer";
      });
      renderCharts();
    }

    function renderCharts() {
      buildAreaSvg(state.cpuSeries, 0, 100, "cpuLinePath", "cpuAreaPath");
      buildAreaSvg(state.memSeries, 0, state.ramTotalGb, "memLinePath", "memAreaPath");
    }

    function buildAreaSvg(values, minVal, maxVal, lineId, areaId) {
      const width = 600, height = 170;
      const stepX = width / Math.max(1, values.length - 1);
      const coords = values.map((val, idx) => {
        const x = Number((idx * stepX).toFixed(1));
        const clamped = Math.min(maxVal, Math.max(minVal, val));
        const ratio = (clamped - minVal) / (maxVal - minVal || 1);
        const y = Number((height - ratio * (height - 20) - 10).toFixed(1));
        return { x, y };
      });
      if (!coords.length) return;
      const lineD = coords.map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x} ${pt.y}`).join(" ");
      const areaD = `${lineD} L ${coords[coords.length - 1].x} ${height} L ${coords[0].x} ${height} Z`;
      document.getElementById(lineId).setAttribute("d", lineD);
      document.getElementById(areaId).setAttribute("d", areaD);
    }

    function fileStatusBadge(f) {
      if (f.status === "pending") {
        return '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">قيد المراجعة</span>';
      }
      if (f.running) {
        return '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">يعمل الآن</span>';
      }
      return '<span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">متوقف</span>';
    }

    function renderOverviewFiles() {
      const tbody = document.getElementById("overviewWorkloadsBody");
      if (!tbody) return;
      if (!state.files.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-slate-400 text-xs">لا توجد ملفات مرفوعة بعد. ارفع ملف (.py / .js / .zip) من ذاكرة الهاتف للبدء.</td></tr>';
        return;
      }
      tbody.innerHTML = state.files.map(f => `
        <tr class="hover:bg-slateElevated/35">
          <td class="py-3 px-4">
            <div class="font-bold text-white">${escapeHtml(f.file_name)}</div>
            <div class="font-mono-code text-xs text-cyan-300">${escapeHtml(f.stored_name || "")}</div>
          </td>
          <td class="py-3 px-4 font-mono-code text-xs text-slate-300">${escapeHtml(f.ext || ".py")}</td>
          <td class="py-3 px-4">${fileStatusBadge(f)}</td>
          <td class="py-3 px-4 font-mono-code text-xs text-slate-400">${escapeHtml(f.created_at || "")}</td>
          <td class="py-3 px-4">
            <div class="flex items-center justify-center gap-1.5">
              <button onclick="controlScript('${escapeAttr(f.id)}', '${f.running ? "stop" : "start"}')" class="px-2.5 py-1 rounded-lg text-xs font-bold cursor-pointer ${f.running ? "bg-amber-500/15 text-amber-300" : "bg-emerald-500/15 text-emerald-300"}">
                ${f.running ? "إيقاف" : "تشغيل"}
              </button>
              <button onclick="openFileInEditor('${escapeAttr(f.id)}')" class="px-2.5 py-1 rounded-lg bg-indigo-500/15 text-indigo-200 text-xs font-bold cursor-pointer">تحرير</button>
              <button onclick="controlScript('${escapeAttr(f.id)}', 'delete')" class="px-2.5 py-1 rounded-lg bg-rose-500/15 text-rose-300 text-xs font-bold cursor-pointer">حذف</button>
            </div>
          </td>
        </tr>
      `).join("");
    }

    function renderWorkloadsManager() {
      const grid = document.getElementById("workloadsCardsGrid");
      if (!grid) return;
      const q = (document.getElementById("workloadSearch")?.value || "").trim().toLowerCase();
      const st = document.getElementById("workloadStatusFilter")?.value || "all";
      const list = state.files.filter(f => {
        const matchQ = !q || (f.file_name || "").toLowerCase().includes(q) || (f.stored_name || "").toLowerCase().includes(q);
        const matchSt = st === "all" || (st === "running" && f.running) || (st === "pending" && f.status === "pending") || (st === "stopped" && !f.running && f.status !== "pending");
        return matchQ && matchSt;
      });
      if (!list.length) {
        grid.innerHTML = '<div class="col-span-full p-8 text-center rounded-2xl bg-slateCard border border-slateBorder text-slate-400 text-xs">لا توجد سكربتات مطابقة.</div>';
        return;
      }
      grid.innerHTML = list.map(f => `
        <div class="p-5 rounded-2xl bg-slateCard border border-slateBorder space-y-4">
          <div class="flex items-start justify-between gap-2">
            <div>
              <h3 class="font-bold text-white text-sm">${escapeHtml(f.file_name)}</h3>
              <p class="font-mono-code text-xs text-cyan-300 mt-0.5">${escapeHtml(f.stored_name || "")}</p>
            </div>
            ${fileStatusBadge(f)}
          </div>
          <div class="text-xs font-mono-code text-slate-400 space-y-1">
            <div>ID: ${escapeHtml(f.id)} • Type: ${escapeHtml(f.ext || ".py")}</div>
            <div>Hours: ${escapeHtml(String(f.hours || 1))}h</div>
          </div>
          <div class="pt-3 border-t border-slateBorder flex flex-wrap gap-2">
            <button onclick="controlScript('${escapeAttr(f.id)}', '${f.running ? "stop" : "start"}')" class="px-3 py-1.5 rounded-lg text-xs font-bold cursor-pointer ${f.running ? "bg-amber-500/15 text-amber-300" : "bg-emerald-500/15 text-emerald-300"}">${f.running ? "إيقاف" : "تشغيل"}</button>
            <button onclick="openFileInEditor('${escapeAttr(f.id)}')" class="px-3 py-1.5 rounded-lg bg-indigo-500/15 text-indigo-200 text-xs font-bold cursor-pointer">المحرر</button>
            <button onclick="viewScriptLogFromCard('${escapeAttr(f.id)}')" class="px-3 py-1.5 rounded-lg bg-cyan-500/15 text-cyan-300 text-xs font-bold cursor-pointer">السجل</button>
            <button onclick="controlScript('${escapeAttr(f.id)}', 'delete')" class="px-3 py-1.5 rounded-lg bg-rose-500/15 text-rose-300 text-xs font-bold cursor-pointer">حذف</button>
          </div>
        </div>
      `).join("");
    }

    async function controlScript(fid, action) {
      const res = await fetch("/api/script/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fid, action })
      });
      const data = await res.json();
      if (data.ok) {
        showToast(data.message || "تم تنفيذ العملية بنجاح", "success");
        if (action === "delete" && state.activeFileId === fid) {
          state.activeFileId = null;
          document.getElementById("codeEditorTextarea").value = "";
          document.getElementById("editorActiveFileName").textContent = "اختر ملفاً";
        }
        await refreshAllFromBackend(false);
      } else {
        showToast(data.error || "تعذر تنفيذ العملية", "warning");
      }
    }

    function renderFileTree() {
      const tree = document.getElementById("fileTreeList");
      if (!tree) return;
      if (!state.files.length) {
        tree.innerHTML = '<div class="text-slate-500">لا توجد ملفات بعد.</div>';
        return;
      }
      tree.innerHTML = state.files.map(f => {
        const active = f.id === state.activeFileId;
        return `
          <button onclick="openFileInEditor('${escapeAttr(f.id)}')" class="w-full flex items-center justify-between px-3 py-2 rounded-xl text-left cursor-pointer ${active ? "bg-indigo-500/20 text-cyan-200 border border-indigo-500/40 font-bold" : "text-slate-300 hover:bg-slateElevated/70"}">
            <span class="truncate">${escapeHtml(f.stored_name || f.file_name)}</span>
            <span class="text-[10px] text-slate-400">${escapeHtml(f.ext || "")}</span>
          </button>
        `;
      }).join("");
    }

    async function openFileInEditor(fid) {
      navigateTo("files");
      const res = await fetch(`/api/file/content?file_id=${encodeURIComponent(fid)}`);
      const data = await res.json();
      if (data.ok) {
        state.activeFileId = fid;
        document.getElementById("editorActiveFileName").textContent = data.stored_name || data.file_name;
        document.getElementById("editorLangBadge").textContent = (data.ext || ".py").replace(".", "").toUpperCase();
        document.getElementById("codeEditorTextarea").value = data.content || "";
        renderFileTree();
      } else {
        showToast(data.error || "تعذر فتح الملف", "warning");
      }
    }

    async function saveActiveFileToServer() {
      if (!state.activeFileId) {
        showToast("اختر ملفاً أولاً من القائمة", "warning");
        return;
      }
      const content = document.getElementById("codeEditorTextarea").value;
      const res = await fetch("/api/file/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: state.activeFileId, content })
      });
      const data = await res.json();
      if (data.ok) {
        showToast("تم حفظ وتشفير الملف على السيرفر بنجاح", "success");
      } else {
        showToast(data.error || "تعذر حفظ الملف", "warning");
      }
    }

    function populateConsoleSelect() {
      const sel = document.getElementById("consoleScriptSelect");
      if (!sel) return;
      const current = sel.value;
      sel.innerHTML = '<option value="">-- اختر سكربت لعرض سجله الحقيقي --</option>' +
        state.files.map(f => `<option value="${escapeAttr(f.id)}">${escapeHtml(f.stored_name || f.file_name)}</option>`).join("");
      if (current) sel.value = current;
    }

    async function viewScriptLogFromCard(fid) {
      navigateTo("console");
      document.getElementById("consoleScriptSelect").value = fid;
      await loadScriptLogs(fid);
    }

    async function loadScriptLogs(fid) {
      const box = document.getElementById("consoleOutputBox");
      if (!box) return;
      if (!fid) {
        box.innerHTML = '<div class="text-slate-500">Select a script above to view live output logs.</div>';
        return;
      }
      const res = await fetch(`/api/script/logs?file_id=${encodeURIComponent(fid)}`);
      const data = await res.json();
      if (data.ok) {
        state.logsText = data.logs || "";
        box.innerHTML = `<pre class="whitespace-pre-wrap text-cyan-200">${escapeHtml(state.logsText || "No logs yet.")}</pre>`;
        box.scrollTop = box.scrollHeight;
      } else {
        box.innerHTML = `<div class="text-rose-400">${escapeHtml(data.error || "Error loading logs")}</div>`;
      }
    }

    function handleTerminalCommand(e) {
      e.preventDefault();
      const inp = document.getElementById("terminalCmdInput");
      const cmd = inp.value.trim();
      if (!cmd) return;
      inp.value = "";
      const box = document.getElementById("consoleOutputBox");
      if (cmd.toLowerCase() === "clear") {
        box.innerHTML = "";
        return;
      }
      let reply = "Commands: help | status | ps | clear";
      if (cmd.toLowerCase() === "status") {
        reply = `CPU=${document.getElementById("kpiCpu").textContent} RAM=${document.getElementById("kpiRam").textContent}`;
      } else if (cmd.toLowerCase() === "ps") {
        reply = state.files.map(f => `${f.stored_name || f.file_name}(${f.running ? "running" : "stopped"})`).join(", ") || "No scripts";
      }
      box.innerHTML += `<div class="text-emerald-400">$ ${escapeHtml(cmd)}</div><div class="text-slate-200 mb-1">${escapeHtml(reply)}</div>`;
      box.scrollTop = box.scrollHeight;
    }

    function copyConsoleLogs() {
      navigator.clipboard?.writeText(state.logsText || "").catch(() => {});
      showToast("تم نسخ السجلات", "success");
    }

    function renderDbAndBilling() {
      const dbBox = document.getElementById("dbSummaryCards");
      if (dbBox && state.system) {
        dbBox.innerHTML = `
          <div class="p-4 rounded-xl bg-obsidian border border-slateBorder">
            <p class="text-cyan-300 font-bold">AES-256-CBC Encrypted Vault</p>
            <p class="text-slate-400 mt-1">Encrypted Files: ${escapeHtml(String(state.system.encrypted_files_count || 0))}</p>
          </div>
          <div class="p-4 rounded-xl bg-obsidian border border-slateBorder">
            <p class="text-indigo-300 font-bold">Unified SQLite WAL + JSON</p>
            <p class="text-slate-400 mt-1">Total Hosted Files: ${escapeHtml(String(state.system.total_files_count || 0))}</p>
          </div>
          <div class="p-4 rounded-xl bg-obsidian border border-slateBorder">
            <p class="text-emerald-300 font-bold">Isolated User Sandboxes</p>
            <p class="text-slate-400 mt-1">Active Processes: ${escapeHtml(String(state.system.active_processes_count || 0))}</p>
          </div>
        `;
      }
      const billBox = document.getElementById("accountBillingBox");
      if (billBox && state.user) {
        billBox.innerHTML = `
          <div class="p-4 rounded-xl bg-obsidian border border-slateBorder">
            <p class="text-slate-400">المستخدم</p>
            <p class="text-white font-bold text-sm mt-1">${escapeHtml(state.user.display_name || state.user.username)}</p>
          </div>
          <div class="p-4 rounded-xl bg-obsidian border border-slateBorder">
            <p class="text-slate-400">رصيد النقاط</p>
            <p class="text-cyan-300 font-bold text-sm mt-1">${escapeHtml(String(state.user.points))} نقطة</p>
          </div>
          <div class="p-4 rounded-xl bg-obsidian border border-slateBorder">
            <p class="text-slate-400">الرصيد المالي</p>
            <p class="text-emerald-300 font-bold text-sm mt-1">${escapeHtml(String(state.user.balance))} ₽</p>
          </div>
        `;
      }
    }

    function openPhoneUploadModal() {
      const m = document.getElementById("phoneUploadModal");
      m.classList.remove("hidden");
      m.classList.add("flex");
    }

    function closePhoneUploadModal() {
      const m = document.getElementById("phoneUploadModal");
      m.classList.add("hidden");
      m.classList.remove("flex");
    }

    async function submitPhoneFileUpload(e) {
      e.preventDefault();
      const modalFile = document.getElementById("modalPhoneFileInput")?.files?.[0];
      const pageFile = document.getElementById("phoneFileInput")?.files?.[0];
      const file = modalFile || pageFile;
      const hours = document.getElementById("modalPhoneFileInput")?.files?.[0]
        ? document.getElementById("modalPhoneHoursInput").value
        : document.getElementById("phoneUploadHours").value;

      if (!file) {
        showToast("اختر ملفاً من ذاكرة الهاتف أولاً", "warning");
        return;
      }

      const fd = new FormData();
      fd.append("file", file);
      fd.append("hours", String(hours || 1));

      showToast("جاري رفع الملف وفحصه أمنياً...", "info");
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      const data = await res.json();
      if (data.ok) {
        showToast(data.message || "تم رفع الملف بنجاح إلى ابن اليمن", "success");
        if (document.getElementById("phoneFileInput")) document.getElementById("phoneFileInput").value = "";
        if (document.getElementById("modalPhoneFileInput")) document.getElementById("modalPhoneFileInput").value = "";
        closePhoneUploadModal();
        await refreshAllFromBackend(false);
      } else {
        showToast(data.error || "تعذر رفع الملف", "warning");
      }
    }

    async function logoutWebAccount() {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/login";
    }

    function showToast(message, type = "info") {
      const stack = document.getElementById("toastStack");
      if (!stack) return;
      const palette = {
        success: "bg-emerald-950/95 border-emerald-500/40 text-emerald-200",
        warning: "bg-amber-950/95 border-amber-500/40 text-amber-200",
        info: "bg-slate-900/95 border-cyan-500/40 text-cyan-200"
      };
      const el = document.createElement("div");
      el.className = `px-4 py-3 rounded-xl border text-xs font-bold shadow-xl ${palette[type] || palette.info}`;
      el.textContent = message;
      stack.appendChild(el);
      setTimeout(() => { el.remove(); }, 3400);
    }

    function escapeHtml(str) {
      return String(str ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function escapeAttr(str) {
      return String(str ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
    }
  </script>
</body>
</html>

"""


# ============ خادم الويب Flask المرتبط بـ index.html ============
init_db()
ensure_default_web_accounts()

app = Flask(__name__, template_folder=TEMPLATES_DIR)
_sec = read_json(SECURITY_DB)
app.secret_key = _sec.get("flask_secret") or "ibn-al-yemen-secret-key"
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE + (2 * 1024 * 1024)


def _render_index_html():
    template_path = os.path.join(TEMPLATES_DIR, "index.html")
    root_path = os.path.join(BASE_DIR, "index.html")
    if os.path.isfile(template_path):
        return render_template("index.html")
    if os.path.isfile(root_path):
        with open(root_path, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="text/html; charset=utf-8")
    return Response("<h1>index.html غير موجود</h1>", status=404, mimetype="text/html; charset=utf-8")


@app.route("/login", methods=["GET"])
def login_page():
    if get_current_web_user():
        return redirect(url_for("index"))
    return Response(LOGIN_HTML, mimetype="text/html; charset=utf-8")


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    payload = request.get_json(silent=True) or request.form
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    acc = authenticate_web_account(username, password)
    if not acc:
        return jsonify({"ok": False, "error": "اسم المستخدم أو كلمة المرور غير صحيحة."}), 401
    if isinstance(acc, dict) and acc.get("banned"):
        return jsonify({"ok": False, "error": "هذا الحساب محظور من منصة ابن اليمن."}), 403
    session["web_user"] = acc["username"]
    return jsonify({"ok": True, "user": {"username": acc["username"], "display_name": acc["display_name"]}})


@app.route("/api/auth/register", methods=["POST"])
def api_auth_register():
    payload = request.get_json(silent=True) or request.form
    ok, res_data = register_web_account(
        username=payload.get("username", ""),
        password=payload.get("password", ""),
        display_name=payload.get("display_name", ""),
        telegram_id=payload.get("telegram_id", 0),
    )
    if not ok:
        return jsonify({"ok": False, "error": res_data}), 400
    session["web_user"] = res_data["username"]
    return jsonify({"ok": True, "user": {"username": res_data["username"], "display_name": res_data["display_name"]}})


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    session.pop("web_user", None)
    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
@web_login_required(api_mode=False)
def index(acc):
    return _render_index_html()


@app.route("/api/overview", methods=["GET"])
@web_login_required(api_mode=True)
def api_overview(acc):
    tg_id = int(acc.get("telegram_id", 0))
    users = read_json(USERS_DB)
    u_bot = users.get(str(tg_id), {})
    files = read_json(FILES_DB)

    user_files_list = []
    for fid, finfo in files.items():
        if is_admin(tg_id) or str(finfo.get("user_id")) == str(tg_id):
            is_run = fid in active_processes and active_processes[fid].poll() is None
            user_files_list.append({
                "id": fid,
                "user_id": finfo.get("user_id"),
                "file_name": finfo.get("file_name"),
                "stored_name": finfo.get("stored_name"),
                "ext": finfo.get("ext"),
                "status": finfo.get("status"),
                "running": is_run,
                "created_at": finfo.get("created_at"),
                "hours": finfo.get("hours", 1),
            })

    mem = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage(BASE_DIR)
    except Exception:
        disk = psutil.disk_usage("/")
    try:
        cpu_pct = float(psutil.cpu_percent(interval=0.1))
    except Exception:
        cpu_pct = 0.0

    enc_count = len([n for n in os.listdir(ENCRYPTED_DIR) if n.endswith(".enc")])
    active_cnt = sum(1 for fid in active_processes if active_processes[fid].poll() is None)

    return jsonify({
        "ok": True,
        "upload_price": float(get_settings().get("python_upload_price", 1.0)),
        "user": {
            "username": acc.get("username"),
            "display_name": acc.get("display_name"),
            "telegram_id": tg_id,
            "role": acc.get("role", "user"),
            "points": float(u_bot.get("points", 0.0)),
            "balance": float(u_bot.get("balance", 0.0)),
        },
        "system": {
            "cpu_percent": cpu_pct,
            "cpu_count": psutil.cpu_count(logical=True) or 1,
            "ram_used_gb": round(mem.used / (1024 ** 3), 2),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "disk_percent": float(disk.percent),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "bot_locked": is_bot_locked(),
            "encrypted_files_count": enc_count,
            "total_files_count": len(files),
            "active_processes_count": active_cnt,
        },
        "files": user_files_list,
    })


@app.route("/api/upload", methods=["POST"])
@web_login_required(api_mode=True)
def api_upload(acc):
    tg_id = int(acc.get("telegram_id", 0))
    if users_banned := read_json(USERS_DB).get(str(tg_id), {}).get("is_banned", 0) == 1:
        return jsonify({"ok": False, "error": "الحساب محظور."}), 403

    upload_file = request.files.get("file")
    if not upload_file or not upload_file.filename:
        return jsonify({"ok": False, "error": "لم يتم اختيار ملف من الهاتف."}), 400

    try:
        hours = int(request.form.get("hours", "1"))
    except ValueError:
        hours = 1
    if hours < 1 or hours > 720:
        return jsonify({"ok": False, "error": "عدد الساعات يجب أن يكون بين 1 و 720."}), 400

    orig_name = os.path.basename(upload_file.filename)
    ext = os.path.splitext(orig_name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTS:
        ban_user_for_security(tg_id, f"محاولة رفع امتداد غير مسموح عبر الويب: {orig_name}")
        return jsonify({"ok": False, "error": "يُسمح فقط بملفات .py أو .js أو .zip."}), 400

    raw_bytes = upload_file.read()
    if not raw_bytes or len(raw_bytes) > MAX_FILE_SIZE:
        return jsonify({"ok": False, "error": "الملف فارغ أو يتجاوز 20 ميجابايت."}), 400

    required_price = float(get_settings().get("python_upload_price", 1.0))
    total_cost = round(required_price * hours, 4)
    ok_pts, cur_pts = _reserve_or_charge_points(tg_id, total_cost, charge_immediately=True)
    if not ok_pts:
        return jsonify({"ok": False, "error": f"رصيدك غير كافي ({cur_pts} نقطة) والمطلوب {total_cost} نقطة."}), 400

    extra_files = []
    if ext == ".zip":
        ok_zip, reason_zip, main_item, extra_files = parse_and_validate_zip_bytes(raw_bytes, tg_id)
        if not ok_zip:
            _refund_points(tg_id, total_cost)
            if reason_zip and ("رمز" in reason_zip or "Slip" in reason_zip or "مشفّر" in reason_zip or "غير مسموح" in reason_zip):
                ban_user_for_security(tg_id, reason_zip)
            return jsonify({"ok": False, "error": reason_zip or "ملف ZIP غير صالح."}), 400
        main_name, content_str, script_ext = main_item
        display_name = f"{orig_name} ({main_name})"
    else:
        try:
            content_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            _refund_points(tg_id, total_cost)
            ban_user_for_security(tg_id, f"ملف غير نصي عبر الويب: {orig_name}")
            return jsonify({"ok": False, "error": "الملف غير صالح أو مشفّر."}), 400
        is_safe, sec_msg = scan_code_security(content_str, strict_text=True)
        if not is_safe:
            _refund_points(tg_id, total_cost)
            ban_user_for_security(tg_id, f"كود مخالف عبر الويب ({orig_name}): {sec_msg}")
            return jsonify({"ok": False, "error": sec_msg}), 400
        script_ext = ext
        display_name = orig_name

    auto_act = bool(is_admin(tg_id) or get_settings().get("auto_approve", False))
    fid, stored_name = _register_pending_script(
        user_id=tg_id,
        original_name=display_name,
        content_str=content_str,
        ext=script_ext,
        hours=hours,
        extra_files=extra_files,
        charged_cost=total_cost,
        auto_activate=auto_act,
    )
    if not fid:
        _refund_points(tg_id, total_cost)
        return jsonify({"ok": False, "error": "تعذر حفظ وتشفير الملف."}), 500

    msg_status = "وتم تشغيله فوراً" if auto_act else "وهو قيد المراجعة لدى الإدارة"
    return jsonify({
        "ok": True,
        "file_id": fid,
        "stored_name": stored_name,
        "message": f"تم رفع {stored_name} {msg_status}."
    })


@app.route("/api/script/control", methods=["POST"])
@web_login_required(api_mode=True)
def api_script_control(acc):
    tg_id = int(acc.get("telegram_id", 0))
    payload = request.get_json(silent=True) or {}
    fid = str(payload.get("file_id") or "").strip()
    action = str(payload.get("action") or "").strip().lower()

    if not fid or not verify_file_access(fid, tg_id):
        return jsonify({"ok": False, "error": "الملف غير موجود أو لا تملك صلاحية الوصول إليه."}), 403

    if action == "start":
        with db_lock:
            files = read_json(FILES_DB)
            if fid in files and files[fid].get("status") == "pending" and not is_admin(tg_id):
                return jsonify({"ok": False, "error": "الملف بانتظار موافقة الإدارة."}), 400
            if fid in files and files[fid].get("status") == "pending" and is_admin(tg_id):
                files[fid]["status"] = "active"
                write_json(FILES_DB, files)
        if start_script(fid):
            return jsonify({"ok": True, "message": "تم تشغيل السكربت بنجاح."})
        return jsonify({"ok": False, "error": "تعذر تشغيل السكربت."}), 400

    if action == "stop":
        stop_script(fid)
        return jsonify({"ok": True, "message": "تم إيقاف السكربت."})

    if action == "delete":
        stop_script(fid)
        with db_lock:
            files = read_json(FILES_DB)
            finfo = files.pop(fid, None)
            write_json(FILES_DB, files)
            if finfo:
                for p_rem in (os.path.join(ENCRYPTED_DIR, f"{fid}.enc"), os.path.join(LOGS_DIR, f"{fid}.log")):
                    try:
                        os.remove(p_rem)
                    except Exception:
                        pass
                try:
                    if finfo.get("user_id") and finfo.get("stored_name"):
                        up = safe_join_user_file(get_user_isolation_dir(finfo["user_id"]), finfo["stored_name"])
                        if os.path.exists(up):
                            os.remove(up)
                except Exception:
                    pass
        return jsonify({"ok": True, "message": "تم حذف الملف من السيرفر."})

    return jsonify({"ok": False, "error": "إجراء غير معروف."}), 400


@app.route("/api/script/logs", methods=["GET"])
@web_login_required(api_mode=True)
def api_script_logs(acc):
    tg_id = int(acc.get("telegram_id", 0))
    fid = str(request.args.get("file_id") or "").strip()
    if not fid or not verify_file_access(fid, tg_id):
        return jsonify({"ok": False, "error": "غير مصرح."}), 403
    log_path = os.path.join(LOGS_DIR, f"{fid}.log")
    if not os.path.exists(log_path):
        return jsonify({"ok": True, "logs": ""})
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-120:]
        return jsonify({"ok": True, "logs": "".join(lines)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/file/content", methods=["GET"])
@web_login_required(api_mode=True)
def api_file_content(acc):
    tg_id = int(acc.get("telegram_id", 0))
    fid = str(request.args.get("file_id") or "").strip()
    if not fid or not verify_file_access(fid, tg_id):
        return jsonify({"ok": False, "error": "غير مصرح."}), 403
    files = read_json(FILES_DB)
    finfo = files.get(fid)
    if not finfo:
        return jsonify({"ok": False, "error": "الملف غير موجود."}), 404
    content = load_encrypted_file(fid) or ""
    return jsonify({
        "ok": True,
        "file_id": fid,
        "file_name": finfo.get("file_name"),
        "stored_name": finfo.get("stored_name"),
        "ext": finfo.get("ext", ".py"),
        "content": content,
    })


@app.route("/api/file/save", methods=["POST"])
@web_login_required(api_mode=True)
def api_file_save(acc):
    tg_id = int(acc.get("telegram_id", 0))
    payload = request.get_json(silent=True) or {}
    fid = str(payload.get("file_id") or "").strip()
    content = payload.get("content")
    if not fid or not isinstance(content, str) or not verify_file_access(fid, tg_id):
        return jsonify({"ok": False, "error": "غير مصرح أو بيانات غير صالحة."}), 403
    is_safe, sec_msg = scan_code_security(content, strict_text=True)
    if not is_safe:
        return jsonify({"ok": False, "error": sec_msg}), 400
    files = read_json(FILES_DB)
    finfo = files.get(fid)
    if not finfo:
        return jsonify({"ok": False, "error": "الملف غير موجود."}), 404
    owner_id = int(finfo.get("user_id", tg_id))
    if not save_encrypted_file(fid, content, owner_id):
        return jsonify({"ok": False, "error": "تعذر تشفير وحفظ الملف."}), 500
    try:
        if finfo.get("stored_name"):
            up = safe_join_user_file(get_user_isolation_dir(owner_id), finfo["stored_name"])
            with open(up, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception:
        pass
    return jsonify({"ok": True, "message": "تم حفظ وتشفير الملف بنجاح."})


def run_flask_server():
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)


# ============ تشغيل البوت وسيرفر الويب معاً ============
def _cleanup_on_exit():
    with process_lock:
        for fid in list(active_processes.keys()):
            try:
                stop_script(fid)
            except Exception:
                pass


atexit.register(_cleanup_on_exit)


def run_bot_polling():
    logger.info(f"🚀 {BOT_BRAND_NAME} bot polling started...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)


def main():
    web_thread = threading.Thread(target=run_flask_server, name="IbnAlYemenWeb", daemon=True)
    web_thread.start()
    run_bot_polling()


if __name__ == "__main__":
    main()

@app.route("/ping")
def ping():
    return "OK", 200
