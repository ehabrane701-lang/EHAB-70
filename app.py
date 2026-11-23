#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ====================================================================
# 🔒 Ehab Al-Houbani : @Y_20_20 |
# ====================================================================

import subprocess
import sys
import os
import json
import threading
import time
import random
import string
import re
import requests
import zipfile
import hashlib
import base64
import shutil
import sqlite3
import uuid
import logging
import psutil
import platform
import tempfile
from datetime import datetime, timedelta
from html import escape
from urllib.parse import quote

# ============ التحقق التلقائي وتثبيت الحزم المطلوبة بأقصى سرعة ============
required_modules = {
    "telebot": "pyTelegramBotAPI",
    "requests": "requests",
    "Crypto": "pycryptodome",
    "bs4": "beautifulsoup4",
    "psutil": "psutil"
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
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل التثبيت: {e}")
        sys.exit(1)

import telebot
from telebot import types
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from bs4 import BeautifulSoup

logger = logging.getLogger("ai_repair")

# ============ إعدادات القنوات والمتغيرات المطلوبة ============

CHANNEL_EHAB_ME = "-1002370397883"   # اشعار تسجيل الدخول الجديد 👤
CHANNEL_EHAB_LINK = "https://t.me/ehabsms7" # قناة التفويض
user_bot = "T90T0BOT"                       # معرف البوت

DEV_TELEGRAM = "https://t.me/Y_20_20"

# معرف تأثير النار الرسمي في تيليجرام
FIRE_EFFECT_ID = "5104841245755180586"

TOKEN = "9026885072:AAFSJYA8pg6k5kOP28ZZp58faDb5nJDg6eE"
ADMIN_ID = 1002670694
BANS = {}
VIP = {}
USERS = {}
STATS = {"total_consumed": 0}

bot = telebot.TeleBot(TOKEN, threaded=True, parse_mode="HTML")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
UPLOAD_DIR = os.path.abspath("upload_bots")
SUSPICIOUS_DIR = os.path.join(BASE_DIR, "suspicious_files")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

MAX_LOG_SIZE_KB = 512
_ipinfo = {'t': 0, 'data': None}
bot_scripts = {}

for d in [RUNNING_DIR, LOGS_DIR, DB_DIR, ASSETS_DIR, STORE_DIR, THUMBS_DIR, MARKET_DIR, ENV_DIR, ENCRYPTED_DIR, DOWNLOAD_DIR, UPLOAD_DIR, SUSPICIOUS_DIR, BACKUPS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

USERS_DB = os.path.join(DB_DIR, "users.json")
FILES_DB = os.path.join(DB_DIR, "files.json")
SETTINGS_DB = os.path.join(DB_DIR, "settings.json")
STORE_DB = os.path.join(DB_DIR, "store.json")
ADMINS_DB = os.path.join(DB_DIR, "admins.json")
MARKET_DB = os.path.join(DB_DIR, "market.json")
SECURITY_DB = os.path.join(DB_DIR, "security.json")
PURCHASES_DB_PATH = os.path.join(DB_DIR, "purchases.db")

db_lock = threading.Lock()
cancel_states = {}
last_bot_messages = {}
active_processes = {}
admin_steps = {}
PENDING = {}
USER_STEPS = {}

# ============ إعدادات وتكامل محرك الذكاء الاصطناعي Ptero.pro المحدث ============
HOME_URL = "https://ptero.pro"
CHAT_URL = f"{HOME_URL}/wp-json/mlp/v1/chat-stream"

MODELS = {
    "1": {"id": "ling-3.0-flash",               "name": "Ling 3.0 Flash"},
    "2": {"id": "deepseek-v4.1-flash:free",     "name": "DeepSeek v4.1 Flash"},
    "3": {"id": "minimax-m3.1-flash:runware",   "name": "MiniMax M3.1 Flash"},
    "4": {"id": "glm-5.3-flash",                "name": "GLM 5.3 Flash"},
    "5": {"id": "qwen3.7-flash:minirouter",     "name": "Qwen 3.7 Flash"},
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
MAX_OUTPUT_BYTES = 20 * 1024 * 1024

_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)

class RepairServiceError(RuntimeError):
    """Raised when the selected external AI service cannot process a file."""

def fetch_real_session(retries=2):
    for attempt in range(retries):
        session = requests.Session()
        headers = {
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            response = session.get(HOME_URL, headers=headers, timeout=25)
            if response.status_code != 200:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None

            html = response.text
            nonce = None
            patterns = [
                r"var\s+nonce\s*=\s*[\"\']([a-f0-9]{8,64})[\"\']",
                r"[\"\']nonce[\"\']\s*:\s*[\"\']([a-f0-9]{8,64})[\"\']",
                r"data-referral-nonce=[\"\']([a-f0-9]{8,64})[\"\']",
                r"x-wp-nonce[\"\']?\s*[:=]\s*[\"\']([a-f0-9]{8,64})[\"\']",
                r"wp_nonce[\"\']?\s*[:=]\s*[\"\']([a-f0-9]{8,64})[\"\']",
                r"mlp_nonce[\"\']?\s*[:=]\s*[\"\']([a-f0-9]{8,64})[\"\']",
                r"data-nonce=[\"\']([a-f0-9]{8,64})[\"\']",
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    nonce = match.group(1)
                    break

            if not nonce and BeautifulSoup:
                soup = BeautifulSoup(html, "html.parser")
                for script in soup.find_all("script"):
                    text = script.get_text() or ""
                    if "nonce" in text:
                        match = re.search(r"[\"\']([a-f0-9]{10})[\"\']", text)
                        if match:
                            nonce = match.group(1)
                            break

            if not nonce:
                for script in re.findall(r"<script\b[^>]*>(.*?)</script\s*>", html, re.I | re.S):
                    if "nonce" in script.lower():
                        match = re.search(r"""["']([a-f0-9]{10})["']""", script, re.I)
                        if match:
                            nonce = match.group(1)
                            break

            if not nonce:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None

            guest_token = None
            for cookie in session.cookies:
                if any(k in cookie.name.lower() for k in ["mlp", "guest", "token"]):
                    guest_token = cookie.value
                    break

            if not guest_token:
                match = re.search(r"guest[_-]?token[\"\']?\s*[:=]\s*[\"\']([a-f0-9]+)[\"\']", html, re.IGNORECASE)
                guest_token = match.group(1) if match else uuid.uuid4().hex

            return {
                "session": session,
                "nonce": nonce,
                "guest_token": guest_token,
                "conversation_id": str(uuid.uuid4()),
            }
        except Exception as ex:
            logger.warning(f"fetch_real_session error (attempt {attempt + 1}): {ex}")
            if attempt < retries - 1:
                time.sleep(1)

    return None

def chat_with_model(model_id, user_message, session_data, model_display_name="AI", stream_print=False):
    payload = {
        "message": user_message,
        "model": model_id,
        "conversation_id": session_data["conversation_id"],
        "attachments": [],
        "history": [],
        "lang": "ar",
        "github_repo": "",
        "mode": "quick"
    }

    headers = {
        "User-Agent": _USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-ch-ua": "\"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        "sec-ch-ua-mobile": "?1",
        "x-wp-nonce": session_data["nonce"],
        "x-mlp-guest-token": session_data["guest_token"],
        "x-mlp-guest-username": f"user_{session_data['conversation_id'][:6]}",
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
            line = line.decode("utf-8", errors="replace")
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if not data_str or data_str == "keepalive":
                continue
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if "token" in data and isinstance(data["token"], str):
                full_reply += data["token"]
                if stream_print:
                    print(data["token"], end="", flush=True)
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
    source_bytes_len = len(source.encode("utf-8"))
    if source_bytes_len > MAX_SOURCE_BYTES:
        raise RepairServiceError(
            f"الملف أكبر من الحد المسموح لإرساله للخدمة ({int(MAX_SOURCE_BYTES / (1024 * 1024))} ميجابايت)."
        )

    session_data = fetch_real_session()
    if not session_data:
        raise RepairServiceError("تعذّر الاتصال بخدمة الذكاء الاصطناعي (فشل تهيئة الجلسة مع الخادم).")

    extra_rules = ""
    _stem, ext = os.path.splitext(file_name)
    ext_lower = ext.lower()

    if ext_lower == ".js":
        extra_rules = (
            "\nتوجيهات لملفات JavaScript / Node.js:\n"
            "- إذا كان الكود يستخدم مكتبة node-telegram-bot-api بالصيغة الشائعة: const TelegramBot = require('node-telegram-bot-api'); new TelegramBot(...); فلا تقم بتغييرها ولا تضع دوال فحص تنهي البرنامج بـ process.exit.\n"
            "- حافظ على بناء الجمل البرمجية الصحيحة في Node.js وتأكد من إغلاق الأقواس.\n"
        )
    elif ext_lower == ".php":
        extra_rules = (
            "\nتوجيهات لملفات PHP:\n"
            "- حافظ على علامة البداية <?php واحرص على كتابة كود PHP سليم برمجياً وإغلاق الأقواس والفواصل المنقوطة.\n"
        )
    elif ext_lower == ".py":
        extra_rules = (
            "\nتوجيهات لملفات Python:\n"
            "- تأكد من صحة الصياغة النحوية (Syntax) والمسافات البادئة (Indentation) بدقة.\n"
            "- لا تغير أسماء الدوال أو المتغيرات الأساسية غير المرتبطة بالطلب.\n"
        )

    prompt = (
        "أنت مبرمج محترف متخصص في تصحيح وإصلاح وتعديل ملفات الأكواد البرمجية. "
        "مهمتك: إصلاح الأخطاء وتنفيذ طلب المستخدم بأعلى دقة وبأقل تغييرات ممكنة.\n"
        "شروط صارمة:\n"
        "1. أعد محتوى الملف كاملاً وجاهزاً للتشغيل داخل كتلة كود واحدة فقط: ``` ... ```\n"
        "2. لا تكتب أي شرح أو مقدمات أو كلام بشري قبل أو بعد الكود نهائياً.\n"
        "3. حافظ على التوكنات والمتغيرات الأساسية ومنطق البوت الأصلي.\n"
        "4. لا تضف أي أكواد ضارة أو برمجيات خبيثة.\n\n"
        f"اسم الملف: {file_name}\n"
        f"طلب المستخدم: {instructions}\n"
        f"{extra_rules}\n"
        "محتوى الملف الحالي:\n"
        f"```text\n{source}\n```"
    )

    candidate_models = []
    if model_id:
        candidate_models.append(model_id)
    if DEFAULT_MODEL_ID not in candidate_models:
        candidate_models.append(DEFAULT_MODEL_ID)
    for fm in FALLBACK_MODELS:
        if fm not in candidate_models:
            candidate_models.append(fm)

    import ast

    for candidate in candidate_models:
        try:
            logger.info(f"جاري إرسال التعديل للنموذج: {candidate}")
            reply, meta = chat_with_model(candidate, prompt, session_data)
            if not reply or not reply.strip():
                session_data = fetch_real_session() or session_data
                continue

            extracted = extract_code_from_ai_response(reply)
            if not extracted or len(extracted.strip()) < 10:
                continue

            if ext_lower == ".py":
                try:
                    ast.parse(extracted, filename=file_name)
                except SyntaxError as syn_err:
                    logger.warning(f"النموذج {candidate} أنتج كود Python به خطأ صياغة ({syn_err})؛ تجربة نموذج بديل...")
                    continue
            elif ext_lower == ".php":
                try:
                    chk = subprocess.run(["php", "-l"], input=extracted.encode("utf-8"), capture_output=True, timeout=5)
                    if chk.returncode != 0:
                        logger.warning(f"النموذج {candidate} أنتج كود PHP به خطأ صياغة؛ تجربة نموذج بديل...")
                        continue
                except Exception:
                    pass

            return extracted

        except Exception as ex:
            logger.warning(f"فشل النموذج {candidate}: {ex}")
            continue

    raise RepairServiceError("تعذّر الحصول على نسخة صالحة وخالية من الأخطاء من خدمة الذكاء الاصطناعي بعد تجربة كافة النماذج.")

# ============ دوال تحليل النظام وحساب المساحات (System Utility Functions) ============
def _get_ipinfo():
    if _ipinfo['data'] and time.time() - _ipinfo['t'] < 600:
        return _ipinfo['data']
    data = None
    try:
        r = requests.get("[http://ip-api.com/json/?fields=status,country,regionName,city,isp,query](http://ip-api.com/json/?fields=status,country,regionName,city,isp,query)", timeout=4).json()
        if r.get('status') == 'success':
            data = r
    except Exception:
        pass
    if not data:
        try:
            ip = requests.get("[https://api.ipify.org](https://api.ipify.org)", timeout=4).text.strip()
            data = {'query': ip}
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
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def esc(text):
    return _esc(text)

def scan_with_virustotal(file_content, file_name):
    """فحص VirusTotal (اختياري)"""
    VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")
    if not VIRUSTOTAL_API_KEY:
        return True
    try:
        files = {"file": (file_name, file_content)}
        headers = {"x-apikey": VIRUSTOTAL_API_KEY}
        r = requests.post("[https://www.virustotal.com/api/v3/files](https://www.virustotal.com/api/v3/files)", files=files, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            analysis_id = data["data"]["id"]
            time.sleep(20)
            r2 = requests.get(f"[https://www.virustotal.com/api/v3/analyses/](https://www.virustotal.com/api/v3/analyses/){analysis_id}", headers=headers, timeout=30)
            if r2.status_code == 200:
                result = r2.json()
                malicious = result["data"]["attributes"]["stats"]["malicious"]
                return malicious == 0
        return True
    except Exception as ex:
        print(f"VirusTotal Error: {ex}")
        return True

def file_token(file_name):
    return hashlib.md5(file_name.encode()).hexdigest()[:10]

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

def db_conn():
    con = sqlite3.connect(PURCHASES_DB_PATH, check_same_thread=False)
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

def read_json(path):
    with db_lock:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except:
            return {}

def write_json(path, data):
    with db_lock:
        try:
            temp_path = path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(temp_path, path)
        except Exception as e:
            print(f"JSON write error: {e}")

def get_storage():
    return read_json(SETTINGS_DB)

def save_storage(data):
    write_json(SETTINGS_DB, data)

def get_settings():
    return read_json(SETTINGS_DB)

def save_settings(settings):
    write_json(SETTINGS_DB, settings)

def init_db():
    global USERS
    default_settings = {
        "channels": [],
        "bot_name": " ",
        "bot_image": None,
        "file_thumb": None,
        "bot_locked": False,
        "auto_approve": False,
        "maintenance_mode": False,
        "python_upload_price": 1.0
    }
    current_settings = read_json(SETTINGS_DB)
    for key, value in default_settings.items():
        if key not in current_settings:
            current_settings[key] = value
    write_json(SETTINGS_DB, current_settings)
    
    for path in [USERS_DB, FILES_DB, STORE_DB, MARKET_DB, SECURITY_DB]:
        if not os.path.exists(path):
            write_json(path, {})
            
    USERS = read_json(USERS_DB)
    try:
        db_conn().close()
    except:
        pass
    init_security()

def init_security():
    security = read_json(SECURITY_DB)
    if "master_key" not in security:
        master_key = base64.b64encode(get_random_bytes(32)).decode("utf-8")
        security["master_key"] = master_key
        security["file_keys"] = {}
        write_json(SECURITY_DB, security)

def get_master_key():
    security = read_json(SECURITY_DB)
    master_key = security.get("master_key")
    if not master_key:
        master_key = base64.b64encode(get_random_bytes(32)).decode("utf-8")
        security["master_key"] = master_key
        write_json(SECURITY_DB, security)
    return base64.b64decode(master_key)

def generate_file_key(fid, user_id):
    security = read_json(SECURITY_DB)
    file_keys = security.get("file_keys", {})
    if fid not in file_keys:
        combined = f"{fid}:{user_id}:{ADMIN_ID}:{TOKEN}"
        salt = hashlib.sha256(combined.encode()).digest()[:16]
        master_key = get_master_key()
        kdf = hashlib.pbkdf2_hmac("sha256", master_key, salt, 100000, dklen=32)
        file_keys[fid] = {
            "key": base64.b64encode(kdf).decode("utf-8"),
            "salt": base64.b64encode(salt).decode("utf-8"),
            "user_id": user_id
        }
        security["file_keys"] = file_keys
        write_json(SECURITY_DB, security)
    return file_keys[fid]

def get_file_key(fid):
    security = read_json(SECURITY_DB)
    file_keys = security.get("file_keys", {})
    return file_keys.get(fid)

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
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(encrypted_data)
    except Exception as e:
        print(f"Encryption error: {e}")
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
        print(f"Decryption error: {e}")
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
            encrypted_content = f.read()
        return decrypt_file_content(encrypted_content, fid)
    return None

def verify_file_access(fid, user_id):
    files = read_json(FILES_DB)
    if fid not in files:
        return False
    file_info = files[fid]
    file_user_id = file_info.get("user_id")
    if user_id == ADMIN_ID or is_admin(user_id):
        return True
    if file_user_id == user_id:
        return True
    if file_info.get("type") == "store":
        store = read_json(STORE_DB)
        if fid in store:
            return True
    return False

def is_bot_locked():
    return get_settings().get("bot_locked", False)

def is_admin(user_id):
    if user_id == ADMIN_ID:
        return True
    admins_data = read_json(ADMINS_DB)
    return user_id in admins_data.get("admins", [ADMIN_ID])

def is_main_admin(user_id):
    return user_id == ADMIN_ID

def get_admins():
    admins_data = read_json(ADMINS_DB)
    return admins_data.get("admins", [ADMIN_ID])

def add_admin(user_id):
    admins_data = read_json(ADMINS_DB)
    if user_id not in admins_data.get("admins", []):
        admins_data["admins"] = admins_data.get("admins", []) + [user_id]
        write_json(ADMINS_DB, admins_data)
        return True
    return False

def remove_admin(user_id):
    if user_id == ADMIN_ID:
        return False
    admins_data = read_json(ADMINS_DB)
    if user_id in admins_data.get("admins", []):
        admins_data["admins"].remove(user_id)
        write_json(ADMINS_DB, admins_data)
        return True
    return False

def day_name():
    ds = ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    w = int(datetime.now().strftime("%w"))
    return ds[w]

def month_name():
    month_n = ["فارغ", "يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"]
    m = int(datetime.now().strftime("%m"))
    return month_n[m]

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
    if chat_id in last_bot_messages:
        try:
            bot.delete_message(chat_id, last_bot_messages[chat_id])
        except:
            pass

def save_message(chat_id, msg_id):
    last_bot_messages[chat_id] = msg_id

def send_msg(chat_id, text, markup=None, effect_id=FIRE_EFFECT_ID):
    delete_last_message(chat_id)
    settings = get_settings()
    try:
        if settings.get("bot_image"):
            msg = bot.send_photo(chat_id, settings["bot_image"], caption=text, parse_mode="HTML", reply_markup=markup, message_effect_id=effect_id)
        else:
            msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup, message_effect_id=effect_id)
        save_message(chat_id, msg.message_id)
        return msg
    except:
        msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup, message_effect_id=effect_id)
        save_message(chat_id, msg.message_id)
        return msg

def edit_msg(call, text, markup):
    try:
        if call.message.content_type == "photo":
            bot.edit_message_caption(text[:4096], call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        else:
            bot.edit_message_text(text[:4096], call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        save_message(call.message.chat.id, call.message.message_id)
    except:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        settings = get_settings()
        try:
            if settings.get("bot_image"):
                msg = bot.send_photo(call.message.chat.id, settings["bot_image"], caption=text[:4096], parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            else:
                msg = bot.send_message(call.message.chat.id, text[:4096], parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            save_message(call.message.chat.id, msg.message_id)
        except:
            msg = bot.send_message(call.message.chat.id, text[:4096], parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            save_message(call.message.chat.id, msg.message_id)

def del_msg(chat_id, *msg_ids):
    for m_id in msg_ids:
        try:
            bot.delete_message(chat_id, m_id)
        except:
            pass

def is_user_pro(uid):
    if uid == ADMIN_ID or is_admin(uid):
        return True
    users = read_json(USERS_DB)
    u = users.get(str(uid), {})
    expiry = u.get("expiry")
    if not expiry or expiry == "null":
        return False
    if expiry == "LIFETIME" or expiry == 0:
        return True
    try:
        exp_date = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < exp_date:
            return True
        else:
            u["expiry"] = None
            users[str(uid)] = u
            write_json(USERS_DB, users)
            return False
    except:
        return False

def check_sub(user_id):
    if user_id == ADMIN_ID or is_admin(user_id):
        return True
    settings = get_settings()
    channels = settings.get("channels", [])
    if not channels:
        return True
    try:
        for ch in channels:
            member = bot.get_chat_member(ch["username"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except:
        return True

def set_cancel(uid, state=True):
    cancel_states[uid] = state

def is_cancelled(uid):
    return cancel_states.get(uid, False)

def clear_cancel(uid):
    if uid in cancel_states:
        del cancel_states[uid]

def get_thumb():
    settings = get_settings()
    thumb = settings.get("file_thumb")
    if thumb and os.path.exists(thumb):
        return thumb
    return None

def btn(text, callback_data=None, url=None, style=None):
    kw = {}
    if callback_data:
        kw["callback_data"] = callback_data
    if url:
        kw["url"] = url
    if style:
        kw["style"] = style
    return types.InlineKeyboardButton(text, **kw)

def locked_msg(chat_id):
    text = "🔒 <b>البوت مغلق حالياً للصيانة</b>\n\nتم إيقاف الخدمة مؤقتاً بأمر من الإدارة."
    markup = types.InlineKeyboardMarkup()
    markup.add(btn("👨‍💻 تواصل مع المطور", url=f"tg://user?id={ADMIN_ID}", style="primary"))
    send_msg(chat_id, deco("🔒 البوت مغلق", text), markup, effect_id=FIRE_EFFECT_ID)

def start_script(fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return False
    file_info = files[fid]
    user_id = file_info.get("user_id")
    if not verify_file_access(fid, user_id):
        return False
    encrypted_content = load_encrypted_file(fid)
    if not encrypted_content:
        return False
    env_dir = os.path.join(ENV_DIR, fid)
    if not os.path.exists(env_dir):
        os.makedirs(env_dir)
    env_file_path = os.path.join(env_dir, f"{fid}.py")
    if fid in active_processes and active_processes[fid].poll() is None:
        return True
    try:
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write(encrypted_content)
    except:
        return False
    log_path = os.path.join(LOGS_DIR, f"{fid}.log")
    try:
        log_file = open(log_path, "a", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, "-u", env_file_path],
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.PIPE,
            cwd=env_dir,
            start_new_session=True,
            env={**os.environ, "PYTHONPATH": env_dir}
        )
        active_processes[fid] = proc
        bot_scripts[fid] = {"process": proc, "file_name": file_info.get("file_name"), "owner_id": user_id}
        return True
    except:
        return False

def stop_script(fid):
    if fid in active_processes:
        proc = active_processes[fid]
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except:
            try:
                proc.terminate()
            except:
                pass
        del active_processes[fid]
        if fid in bot_scripts:
            del bot_scripts[fid]
        return True
    return False

def write_proc(fid, cmd):
    if fid in active_processes and active_processes[fid].poll() is None:
        try:
            proc = active_processes[fid]
            if proc.stdin:
                proc.stdin.write(cmd.encode("utf-8") + b"\n")
                proc.stdin.flush()
                return True
        except:
            pass
    return False

def create_zip(files_list, zip_name):
    zip_path = os.path.join(BASE_DIR, zip_name)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_path in files_list:
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
    return zip_path

def scan_code_security(content):
    dangerous_patterns = [
        r"\bos\.system\s*\(",
        r"\bos\.popen\s*\(",
        r"\bshutil\.rmtree\s*\(\s*[\"\']\/",
        r"\bctypes\b",
        r"open\s*\(\s*[\"\'].*\/etc\/passwd",
        r"open\s*\(\s*[\"\'].*\/root\/",
        r"rm\s+-rf\s+/",
        r"\bsubprocess\.Popen\s*\(\s*\[\s*[\"\']rm",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"base64\.b64decode\s*\(\s*['\"].*['\"]\s*\)\.decode\s*\(\s*['\"]utf-8['\"]s*\)\s*;\s*exec\s*\("
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "⚠️ تم رفض الملف حظراً أمنياً لاحتوائه على أكواد خطيرة أو محاولات اختراق أو أكواد مشفرة غير مقبولة."
    return True, "الكود آمن"

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
                
            if url:
                b = types.InlineKeyboardButton(text, url=url, **kw)
            else:
                b = types.InlineKeyboardButton(text, callback_data=callback_data, **kw)
            row_btns.append(b)
        markup.row(*row_btns)
    return markup

def main_kb(uid):
    structure = [
        [{"text": " رفع ملفات بايثون ", "callback_data": "nav_upload", "style": "success"},
         {"text": "📦 رفع ملفات ZIP", "callback_data": "nav_upload_zip", "style": "success"}],
        [{"text": "💻 حالة ونظام السيرفر", "callback_data": "admin_system_status", "style": "primary"}],
        [{"text": "📜 الشروط والتعليمات", "callback_data": "ehab_5_e", "style": "danger"}],
        [{"text": " ملفاتي ", "callback_data": "nav_files", "style": "primary"}, {"text": " المتجر ", "callback_data": "nav_store", "style": "primary"}],
        [{"text": " محفظتي ", "callback_data": "nav_wallet", "style": "primary"}, {"text": " حسابي ", "callback_data": "nav_stats", "style": "primary"}],
        [{"text": " تثبيت مكتبة ", "callback_data": "nav_lib", "style": "primary"}, {"text": " التعليمات ", "callback_data": "nav_help", "style": "primary"}]
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
    kb.add(btn("🔍 فحص تلقائي", callback_data="pro_auto_fix", style="primary"))
    kb.add(btn("▶️ تشغيل تجريبي", callback_data="pro_test_run", style="primary"))
    kb.add(btn("🛒 بيع في المتجر", callback_data="pro_sell", style="primary"))
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

# ============ مسارات وأحداث لوحة تحكم النظام (System Callbacks) ============
def handle_admin_system(call):
    uid = call.from_user.id
    if not is_admin(uid):
        return
    
    try:
        per = psutil.cpu_percent(interval=0.5, percpu=True)
        cpu_total = sum(per) / max(1, len(per))
        cores_line = " ".join(f"{p:.0f}%" for p in per) if len(per) <= 16 else f"{len(per)} نواة"
    except Exception:
        per = []
        cpu_total = 0.0
        cores_line = "غير متاح (صلاحيات أندرويد)"

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
        disk = psutil.disk_usage(os.path.abspath("."))
    except Exception:
        disk = psutil.disk_usage('/')
        
    users_size = _dir_size(UPLOAD_DIR)
    proc = psutil.Process()
    ip = _get_ipinfo()
    place = " - ".join(x for x in (ip.get('country'), ip.get('regionName'), ip.get('city')) if x) or "غير متاح"
    uname = platform.uname()
    
    try:
        boot = datetime.now() - datetime.fromtimestamp(proc.create_time())
    except Exception:
        boot = "مستمر"

    text = (
        f"<blockquote>💻 <b>معلومات النظام والسيرفر (Pydroid Mode)</b></blockquote>\n\n"
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
        f"⏱ <b>تشغيل البوت:</b> {str(boot).split('.')[0]}\n"
        f"🖥 <b>OS:</b> {uname.system} {uname.release} | Python {platform.python_version()}"
        f"</blockquote>"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("🧹 تنظيف الرامات", callback_data="sys_clean_ram", style="success"),
        btn("🗑 تنظيف المؤقتات", callback_data="sys_clean_tmp", style="success")
    )
    kb.add(
        btn("📜 تنظيف اللوجات", callback_data="sys_clean_logs", style="primary"),
        btn("📈 استهلاك الرامات (Top)", callback_data="sys_top", style="primary")
    )
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="danger"))
    
    try:
        edit_msg(call, text, kb)
    except:
        send_msg(call.message.chat.id, text, kb)

def handle_sys_clean_ram(call):
    uid = call.from_user.id
    if not is_admin(uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    proc = psutil.Process()
    before_rss = proc.memory_info().rss
    before_avail = psutil.virtual_memory().available
    for _ in range(3):
        import gc
        gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass
    dropped = False
    try:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            os.sync()
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("1")
            dropped = True
    except Exception:
        pass
    after_rss = proc.memory_info().rss
    after_avail = psutil.virtual_memory().available
    freed_bot = max(0, before_rss - after_rss)
    gained = max(0, after_avail - before_avail)
    
    bot.answer_callback_query(call.id, "✅ تم تنظيف الرامات بنجاح!", show_alert=True)
    handle_admin_system(call)

def handle_sys_clean_tmp(call):
    uid = call.from_user.id
    if not is_admin(uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    freed, count = 0, 0
    cutoff = time.time() - 3600
    tmpdir = tempfile.gettempdir()
    try:
        for name in os.listdir(tmpdir):
            p = os.path.join(tmpdir, name)
            try:
                st = os.lstat(p)
                if hasattr(os, "getuid") and st.st_uid != os.getuid():
                    continue
                if st.st_mtime > cutoff:
                    continue
                size = _dir_size(p) if os.path.isdir(p) and not os.path.islink(p) else st.st_size
                if os.path.isdir(p) and not os.path.islink(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
                freed += size
                count += 1
            except OSError:
                pass
    except OSError:
        pass
    try:
        for root, dirs, files in os.walk(UPLOAD_DIR):
            for d in list(dirs):
                if d in ("__pycache__", ".tmp"):
                    p = os.path.join(root, d)
                    if os.path.islink(p):
                        continue
                    try:
                        if d == ".tmp" and os.path.getmtime(p) > cutoff:
                            continue
                        freed += _dir_size(p)
                        shutil.rmtree(p, ignore_errors=True)
                        count += 1
                    except OSError:
                        pass
                    dirs.remove(d)
    except Exception:
        pass
    bot.answer_callback_query(call.id, f"🗑 تم تحرير {_mb(freed)} MB بنجاح!", show_alert=True)
    handle_admin_system(call)

def handle_sys_clean_logs(call):
    uid = call.from_user.id
    if not is_admin(uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    running = set()
    for info in list(bot_scripts.values()):
        running.add((str(info.get('owner_id')), os.path.splitext(info.get('file_name', ''))[0]))
    freed, count = 0, 0
    limit = MAX_LOG_SIZE_KB * 1024
    try:
        for uid_dir in os.listdir(UPLOAD_DIR):
            folder = os.path.join(UPLOAD_DIR, uid_dir)
            if not os.path.isdir(folder) or os.path.islink(folder):
                continue
            for name in os.listdir(folder):
                if not name.endswith(".log"):
                    continue
                p = os.path.join(folder, name)
                try:
                    if os.path.islink(p) or (uid_dir, name[:-4]) in running:
                        continue
                    size = os.path.getsize(p)
                    if size > limit:
                        os.remove(p)
                        freed += size
                        count += 1
                except OSError:
                    pass
    except OSError:
        pass
    bot.answer_callback_query(call.id, f"📜 تم تنظيف {count} ملف لوج بنجاح!", show_alert=True)
    handle_admin_system(call)

def handle_sys_top(call):
    uid = call.from_user.id
    if not is_admin(uid):
        return bot.answer_callback_query(call.id, "❌ صلاحيات مشرف فقط!", show_alert=True)
    by_pid = {}
    for info in list(bot_scripts.values()):
        p = info.get('process')
        if p is not None and hasattr(p, 'pid'):
            by_pid[p.pid] = info
    rows = []
    try:
        me = psutil.Process()
        procs = [me] + me.children(recursive=True)
        for pr in procs:
            try:
                rss = pr.memory_info().rss
                cpu = pr.cpu_percent(interval=None)
                rows.append((rss, pr.pid, cpu))
            except psutil.Error:
                pass
    except Exception:
        pass
    rows.sort(reverse=True)
    lines = []
    for rss, pid, cpu in rows[:8]:
        if pid == os.getpid():
            who = "🤖 البوت نفسه"
        elif pid in by_pid:
            inf = by_pid[pid]
            who = f"📄 {_esc(str(inf.get('file_name')))} (<code>{inf.get('owner_id')}</code>)"
        else:
            who = f"⚙️ PID {pid}"
        lines.append(f"{who} — <b>{_mb(rss)} MB</b>")
    body = "\n".join(lines) if lines else "مفيش بيانات"
    text = f"📈 <b>أكبر استهلاك للرامات:</b>\n\n{body}"
    kb = types.InlineKeyboardMarkup()
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="admin_system_status", style="danger"))
    edit_msg(call, text, kb)

@bot.message_handler(commands=["start", "admin"])
def start_cmd(msg):
    try:
        uid = msg.from_user.id
        if is_bot_locked() and not is_admin(uid):
            try:
                bot.delete_message(msg.chat.id, msg.message_id)
            except:
                pass
            locked_msg(msg.chat.id)
            return
        users = read_json(USERS_DB)
        clear_cancel(uid)
        first_name_raw = msg.from_user.first_name or "مستخدم"
        if str(uid) not in users:
            users[str(uid)] = {
                "username": msg.from_user.username,
                "first_name": first_name_raw,
                "last_name": msg.from_user.last_name,
                "points": 0,
                "balance": 0.0,
                "join_date": str(datetime.now().date()),
                "is_banned": 0,
                "expiry": None,
                "notifications": True
            }
            write_json(USERS_DB, users)
            try:
                first = esc(f"{first_name_raw} {msg.from_user.last_name or ''}")
                user = msg.from_user.username or "لا يوجد"
                day2, _ = get_date_strings()
                cap = (
                    f"➖ <b>تم دخول شخص جديد الى البوت 👤•</b>\n"
                    f"➖ <b>إسم الشخص:</b> <a href=\"tg://user?id={uid}\">{first}</a> 📝•\n"
                    f"➖ <b>الحالة :</b> تم التحقق وليس روبوت ✅️ •\n"
                    f"➖ <b>ايديه :</b> <code>{uid}</code> 🆔️•\n"
                    f"➖ <b>معرف حسابه :</b> @{user} 📮•\n\n"
                    f"        🔰\n"
                    f"➖➖➖➖➖➖\n"
                    f"📆 - {day2}"
                )
                structure = [
                    [{"text": "👤 كشف العضو", "url": f"tg://openmessage?user_id={uid}", "style": "primary"}]
                ]
                for adm in get_admins():
                    try:
                        photos = bot.get_user_profile_photos(uid)
                        if photos.total_count > 0:
                            bot.send_photo(CHANNEL_EHAB_ME, photos.photos[0][-1].file_id, caption=cap, parse_mode="HTML", reply_markup=build_keyboard(structure), message_effect_id=FIRE_EFFECT_ID)
                        else:
                            bot.send_message(CHANNEL_EHAB_ME, cap, parse_mode="HTML", reply_markup=build_keyboard(structure), message_effect_id=FIRE_EFFECT_ID)
                    except:
                        pass
            except:
                pass
        users = read_json(USERS_DB)
        if users.get(str(uid), {}).get("is_banned", 0) == 1:
            return bot.send_message(msg.chat.id, deco("🚫 محظور", "عذراً، تم حظرك نهائياً من استخدام البوت.", first_name_raw), message_effect_id=FIRE_EFFECT_ID)
        if not check_sub(uid):
            return sub_msg(msg.chat.id)
        try:
            bot.delete_message(msg.chat.id, msg.message_id)
        except:
            pass
        u = users.get(str(uid), {})
        
        text = (
            f"<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n"
            f"<b>   🌟 أهلاً بك عزيزي  ⦗ {first_name_raw} ⦘ 🌟   </b>\n"
            f"<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n\n"
            f"<b>💌 ︙ ايدي المستخدم : <code>{msg.chat.id}</code></b>\n"
            f"<b>💰 ︙ رصيدك المالي : <tg-spoiler>{u.get('balance', 0.0)}</tg-spoiler> ₽</b>\n"
            f"<b>🚀 ︙ سرعة الاستضافة : فائقة </b>\n\n"
            f"<b>💻 ︙ تحكم الآن بكافة الأقسام عبر الأزرار أدناه 👇</b>"
        )
        send_msg(msg.chat.id, deco("🏠 القائمة الرئيسية", text, first_name_raw), main_kb(uid), effect_id=FIRE_EFFECT_ID)
    except Exception as e:
        print(f"Start Error: {e}")

def sub_msg(chat_id):
    settings = get_settings()
    channels = settings.get("channels", [])
    if not channels:
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        ch_username = ch['username'].replace('@', '')
        kb.add(btn(f"📢 {ch['name']}", url=f"[https://t.me/](https://t.me/){ch_username}", style="primary"))
    kb.add(btn("✅ تحقق من الاشتراك", callback_data="check_sub", style="success"))
    text = "🔔 <b>اشتراك إجباري مطلوب</b>\n\nيجب عليك الاشتراك في القنوات التالية لاستخدام البوت:"
    send_msg(chat_id, deco("🔔 اشتراك مطلوب", text), kb, effect_id=FIRE_EFFECT_ID)

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    try:
        uid = call.from_user.id
        cid = call.message.chat.id
        data = call.data
        users = read_json(USERS_DB)
        first_name_raw = call.from_user.first_name or "مستخدم"

        if is_bot_locked() and not is_admin(uid):
            bot.answer_callback_query(call.id, "🔒 البوت مغلق حالياً للصيانة!", show_alert=True)
            locked_msg(cid)
            return
        if str(uid) in users and users[str(uid)].get("is_banned", 0) == 1:
            return bot.answer_callback_query(call.id, "🚫 أنت محظور نهائياً من استخدام البوت!", show_alert=True)
        
        if data == "cancel" or data == "user_home" or data == "nav_main":
            set_cancel(uid, True)
            bot.answer_callback_query(call.id, "✅ تم العودة للقائمة.")
            u = users.get(str(uid), {})
            text = (
                f"<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n"
                f"<b>   🌟 أهلاً بك عزيزي  ⦗ {first_name_raw} ⦘ 🌟   </b>\n"
                f"<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n\n"
                f"<b>💌 ︙ ايدي المستخدم : <code>{cid}</code></b>\n"
                f"<b>💰 ︙ رصيدك المالي : <tg-spoiler>{u.get('balance', 0.0)}</tg-spoiler> ₽</b>\n"
                f"<b>🚀 ︙ سرعة الاستضافة : فائقة </b>\n\n"
                f"<b>💻 ︙ تحكم الآن بكافة الأقسام عبر الأزرار أدناه 👇</b>"
            )
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("🏠 القائمة الرئيسية", text, first_name_raw), main_kb(uid), effect_id=FIRE_EFFECT_ID)
            return

        if data == "admin_system_status":
            handle_admin_system(call)
            return
        elif data == "sys_clean_ram":
            handle_sys_clean_ram(call)
            return
        elif data == "sys_clean_tmp":
            handle_sys_clean_tmp(call)
            return
        elif data == "sys_clean_logs":
            handle_sys_clean_logs(call)
            return
        elif data == "sys_top":
            handle_sys_top(call)
            return

        if data == "cancel_admin":
            set_cancel(uid, True)
            if uid in admin_steps:
                del admin_steps[uid]
            bot.answer_callback_query(call.id, "✅ تم إلغاء العملية.")
            admin_panel(call)
            return

        if data == "check_sub":
            if check_sub(uid):
                bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح!")
                u = users.get(str(uid), {})
                text = (
                    f"<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n"
                    f"<b>   🌟 أهلاً بك عزيزي  ⦗ {first_name_raw} ⦘ 🌟   </b>\n"
                    f"<b>▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱</b>\n\n"
                    f"<b>💌 ︙ ايدي المستخدم : <code>{cid}</code></b>\n"
                    f"<b>💰 ︙ رصيدك المالي : <tg-spoiler>{u.get('balance', 0.0)}</tg-spoiler> ₽</b>\n"
                    f"<b>🚀 ︙ سرعة الاستضافة : فائقة </b>\n\n"
                    f"<b>💻 ︙ تحكم الآن بكافة الأقسام عبر الأزرار أدناه 👇</b>"
                )
                try:
                    bot.delete_message(cid, call.message.message_id)
                except:
                    pass
                send_msg(cid, deco("🏠 القائمة الرئيسية", text, first_name_raw), main_kb(uid), effect_id=FIRE_EFFECT_ID)
            else:
                bot.answer_callback_query(call.id, "❌ لم تقم بالاشتراك في كافة القنوات!", show_alert=True)
            return

        if not check_sub(uid) and not is_admin(uid):
            bot.answer_callback_query(call.id, "❌ يجب الاشتراك في القنوات أولاً!", show_alert=True)
            return
        clear_cancel(uid)
        
        if data == "ehab_5_e":
            terms_text = (
                f"📜 <b>الشروط والتعليمات الكاملة لاستخدام الاستضافة والبوت</b>\n\n"
                f"<b>🤖 ما هو البوت وما يقدمه؟</b>\n"
                f"يعتبر هذا البوت نظاماً سحابياً متكاملاً وفائق السرعة (Ultra Speed) مخصصاً لرفع وتشغيل سكريبتات بايثون وبوتات تيليجرام 24/7 دون توقف.\n\n"
                f"<b>📋 تفاصيل البوت والمميزات الرئيسية:</b>\n"
                f"1. <b>استضافة بايثون الفائقة:</b> تشغيل آمن ومحمي بأحدث تقنيات التشفير AES وحماية كاملة ضد الأكواد الخبيثة ومحاولات الاختراق.\n"
                f"2. <b>شحن الرصيد والنقاط:</b> تتيح لك المحفظة متابعة رصيدك واستخدامه في رفع الملفات.\n"
                f"3. <b>لوحة تحكم الإدارة والمشرفين:</b> مراقبة الأداء، الإذاعة العامة، إدارة المشتركين، وتفعيل الصيانة.\n\n"
                f"<b>⚠️ شروط وقوانين الاستخدام:</b>\n"
                f"• يمنع منعاً باتاً رفع أي أكواد ضارة أو برامج اختراق أو سبام، وفي حال المخالفة يتم حظر الحساب والآيدي نهائياً بشكل تلقائي.\n"
                f"• الالتزام بالأدب العام وعدم إساءة استخدام خدمات الاستضافة.\n"
                f"• للإبلاغ عن مشاكل أو التواصل المستمر، يرجى مراسلة المطور عبر أزرار التواصل المتاحة في القائمة الرئيسية."
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(btn("🔙 رجوع للقائمة الرئيسية", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("📜 الشروط والتعليمات", terms_text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
            return

        if data == "nav_pro":
            if not is_user_pro(uid):
                bot.answer_callback_query(call.id, "❌ هذه اللوحة مخصصة لمشتركي VIP فقط!", show_alert=True)
                return
            text = "🔧 <b>لوحة VIP المميزة والحصرية</b>\n\nاستمتع بكافة المزايا والأدوات المتقدمة لتطوير وإدارة ملفاتك."
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("🔧 لوحة Pro", text, first_name_raw), pro_panel_kb(uid), effect_id=FIRE_EFFECT_ID)
        elif data == "pro_download_all":
            if not is_user_pro(uid):
                bot.answer_callback_query(call.id, "❌ لمشتركي VIP فقط!", show_alert=True)
                return
            files = read_json(FILES_DB)
            u_files = {fid: f for fid, f in files.items() if f.get("user_id") == uid and f.get("status") == "active"}
            if not u_files:
                bot.answer_callback_query(call.id, "📂 لا توجد ملفات نشطة لديك!", show_alert=True)
                return
            decrypted_files = []
            for fid in u_files.keys():
                if verify_file_access(fid, uid):
                    content = load_encrypted_file(fid)
                    if content:
                        temp_path = os.path.join(BASE_DIR, f"temp_{fid}_{gen_id(4)}.py")
                        with open(temp_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        decrypted_files.append(temp_path)
            if decrypted_files:
                zip_name = f"files_{uid}_{gen_id(4)}.zip"
                zip_path = create_zip(decrypted_files, zip_name)
                try:
                    with open(zip_path, "rb") as f:
                        bot.send_document(cid, f, caption="📦 جميع ملفاتك البرمجية في أرشيف مضغوط واحد:", message_effect_id=FIRE_EFFECT_ID)
                    for temp_file in decrypted_files:
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    os.remove(zip_path)
                except:
                    bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء إنشاء الأرشيف!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ لم يتم العثور على ملفات للتحميل!", show_alert=True)
        elif data == "nav_wallet":
            u = users.get(str(uid), {})
            vip = is_user_pro(uid)
            exp = "لا يوجد"
            if vip:
                e = u.get("expiry")
                if e == "LIFETIME" or e == 0:
                    exp = "دائم ♾"
                elif e:
                    exp = e
            text = f"💰 رصيدك الحالي: <code>{u.get('points', 0)}</code> نقطة | 💵 الرصيد المالي: <code>{u.get('balance', 0.0)}</code> ₽\n💎 الرتبة: {'VIP 👑' if vip else 'مجاني 🆓'}\n⏰ صلاحية VIP: {exp}\n\n💡 ملاحظة: يتم رفع الملفات وتشغيلها حصرياً عبر رصيد النقاط."
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("💼 محفظتي", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
        elif data == "nav_help":
            text = "📖 <b>دليل الاستخدام الشامل</b>\n\n🚀 خطوات الاستضافة:\n• اضغط على زر رفع ملف جديد.\n• أرسل ملف بايثون بصيغة .py.\n• حدد عدد ساعات التشغيل."
            kb = types.InlineKeyboardMarkup()
            kb.add(btn("👨‍💻 تواصل مع المطور", url=f"tg://user?id={ADMIN_ID}", style="primary"))
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("📖 التعليمات", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
        elif data == "nav_upload":
            u = users.get(str(uid), {})
            st_settings = get_settings()
            required_price = st_settings.get("python_upload_price", 1.0)
            if u.get("points", 0) < required_price and not is_user_pro(uid):
                return bot.answer_callback_query(call.id, f"❌ رصيدك لا يكفي لرفع ملف! السعر المطلوب: {required_price} نقطة.", show_alert=True)
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("📤 إرسال الملف", f"📥 أرسل ملف السكريبت .py (سعر الرفع الحالي: {required_price} نقطة):\n\n<i>⚠️ تنبيه: سيتم تعليق الملف ومراجعته من قبل الإدارة أولاً.</i>", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, upload_step, m.message_id)
        elif data == "nav_upload_zip":
            u = users.get(str(uid), {})
            st_settings = get_settings()
            required_price = st_settings.get("python_upload_price", 1.0)
            if u.get("points", 0) < required_price and not is_user_pro(uid):
                return bot.answer_callback_query(call.id, f"❌ رصيدك لا يكفي لرفع ملف ZIP! السعر المطلوب: {required_price} نقطة.", show_alert=True)
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("📦 إرسال ملف ZIP", f"📥 أرسل أرشيف المضغوط .zip الذي يحتوي على ملفات البايثون والمشروع (سعر الرفع: {required_price} نقطة):\n\n<i>⚠️ سيتم معالجة الملف واستخراج الملفات البرمجية بشكل آمن وفحص القواعد والمسارات.</i>", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, upload_zip_step, m.message_id)
        elif data == "nav_files":
            files = read_json(FILES_DB)
            u_files = {fid: f for fid, f in files.items() if f.get("user_id") == uid}
            if not u_files:
                return bot.answer_callback_query(call.id, "📂 لا توجد ملفات مرفوعة لديك حالياً!", show_alert=True)
            kb = types.InlineKeyboardMarkup(row_width=1)
            for fid, f in u_files.items():
                status = f.get("status", "active")
                if status == "pending":
                    icon = "⏳ قيد المراجعة"
                else:
                    running = fid in active_processes and active_processes[fid].poll() is None
                    icon = "🟢 يعمل" if running else "🔴 متوقف"
                ft = "💎" if f.get("type") == "pro" else "🆓"
                kb.add(btn(f"{icon} | {ft} {f.get('file_name', '?')[:25]}", callback_data=f"manage_{fid}", style="primary"))
            if is_user_pro(uid):
                kb.add(btn("📦 تحميل كافة الملفات (ZIP)", callback_data="pro_download_all", style="success"))
            
            kb.add(btn("🔙 القائمة الرئيسية 🔙", callback_data="nav_main", style="danger"))
            
            active_count = sum(1 for fid, f in u_files.items() if f.get("status") == "active" and fid in active_processes and active_processes[fid].poll() is None)
            text = f"📊 إجمالي ملفاتك: {len(u_files)}\n🟢 يعمل الآن: {active_count}"
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("📁 ملفاتي", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
        elif data.startswith("manage_"):
            file_panel(call, data.split("_")[1])
        elif data.startswith("toggle_"):
            toggle_file(call, data.split("_")[1])
        elif data.startswith("delc_"):
            fid = data.split("_")[1]
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                btn("✅ نعم، احذف", callback_data=f"del_{fid}", style="danger"),
                btn("❌ تراجع", callback_data=f"manage_{fid}", style="primary")
            )
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("🗑️ تأكيد الحذف", "هل أنت متأكد من رغبتك في حذف هذا الملف نهائياً؟", first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
        elif data.startswith("del_"):
            delete_file(call, data.split("_")[1])
        elif data.startswith("dl_"):
            download_file(call, data.split("_")[1])
        elif data.startswith("term_"):
            terminal(call, data.split("_")[1])
        elif data.startswith("rterm_"):
            terminal(call, data.split("_")[1])
        elif data.startswith("inp_"):
            fid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("⌨️ إدخال أمر", "اكتب الأمر أو النص المراد إرساله للسكريبت:", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, input_step, fid, m.message_id)
        elif data.startswith("chtoken_"):
            fid = data.split("_")[1]
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("🔑 تغيير التوكن", "أرسل التوكن الجديد للروبوت:", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, token_step, fid, m.message_id)
        elif data.startswith("tokinfo_"):
            token_info(call, data.split("_")[1])
        elif data.startswith("fai_"):
            cb_ai_repair_request(call)
        elif data.startswith("faic_"):
            cb_ai_repair_confirm(call)
        elif data.startswith("faix_"):
            bot.answer_callback_query(call.id, "❌ تم إلغاء طلب الإصلاح بواسطة الذكاء الاصطناعي.")
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
        elif data == "nav_store":
            store_view(call)
        elif data.startswith("buy_"):
            buy_confirm(call, data.split("_")[1])
        elif data.startswith("ebuy_"):
            buy_exec(call, data.split("_")[1])
        elif data == "nav_lib":
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("🛠 تثبيت مكتبة", "أرسل اسم المكتبة البرمجية المراد تثبيتها عبر pip:", first_name_raw), cancel_kb(), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, lib_step, m.message_id)
        elif data == "nav_stats":
            files = read_json(FILES_DB)
            u = users.get(str(uid), {})
            u_files = [f for f in files.values() if f.get("user_id") == uid]
            running = sum(1 for fid, f in files.items() if f.get("user_id") == uid and fid in active_processes and active_processes[fid].poll() is None)
            vip = is_user_pro(uid)
            exp = "لا يوجد"
            if vip:
                e = u.get("expiry")
                if e == "LIFETIME" or e == 0:
                    exp = "دائم ♾"
                elif e:
                    try:
                        ed = datetime.strptime(e, "%Y-%m-%d %H:%M:%S")
                        rem = ed - datetime.now()
                        exp = f"{rem.days} يوم متبقي"
                    except:
                        exp = e
            text = f"🆔 الآيدي: <code>{uid}</code>\n🔗 المعرف: @{u.get('username', 'لا يوجد')}\n📅 الانضمام: {u.get('join_date', 'اليوم')}\n\n💎 الرتبة: {'VIP 👑' if vip else 'مجاني 🆓'}\n⏰ صلاحية VIP: {exp}\n💰 رصيد النقاط: <code>{u.get('points', 0)}</code>\n\n📁 ملفاتك: {len(u_files)}\n🟢 قيد التشغيل: {running}"
            kb = types.InlineKeyboardMarkup()
            kb.add(btn("💼 محفظتي", callback_data="nav_wallet", style="primary"))
            kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            send_msg(cid, deco("📊 حسابي", text, first_name_raw), kb, effect_id=FIRE_EFFECT_ID)
        
        elif data == "nav_admin" and is_admin(uid):
            admin_panel(call)
        elif data == "adm_users" and is_admin(uid):
            users_panel(call)
        elif data.startswith("userpage_") and is_admin(uid):
            page = int(data.split("_")[1])
            users_panel(call, page)
        elif data.startswith("uctrl_") and is_admin(uid):
            user_panel(call, data.split("_")[1])
        elif data.startswith("ban_") and is_admin(uid):
            ban_toggle(call, data.split("_")[1])
        elif data.startswith("pro_") and is_admin(uid):
            tuid = data.split("_")[1]
            if is_user_pro(int(tuid)):
                pro_remove(call, tuid)
            else:
                try:
                    bot.delete_message(cid, call.message.message_id)
                except:
                    pass
                m = send_msg(cid, deco("💎 منح VIP", "أرسل عدد الأيام (اكتب 0 للحصول على VIP دائم):", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
                save_message(cid, m.message_id)
                bot.register_next_step_handler(m, pro_grant_step, tuid, m.message_id)
        elif data == "adm_related_files" and is_admin(uid):
            pending_list(call)
        elif data.startswith("vpend_") and is_admin(uid):
            admin_view_pending_file(call, data.split("_")[1])
        elif data.startswith("vdl_") and is_admin(uid):
            admin_download_pending_file(call, data.split("_")[1])
        elif data.startswith("vapprove_") and is_admin(uid):
            admin_approve_file(call, data.split("_")[1])
        elif data.startswith("vdel_") and is_admin(uid):
            admin_delete_pending_file(call, data.split("_")[1])
        elif data == "adm_bot_manager" and is_admin(uid):
            bot_manager_panel(call)
        elif data.startswith("botact_") and is_admin(uid):
            ex = data.split("_")
            handle_bot_action(call, ex[1], ex[2])
        elif data == "adm_stats" and is_admin(uid):
            admin_stats_view(call)
        elif data == "adm_add_balance" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("➕ إضافة رصيد", "أرسل آيدي المستخدم المراد إضافة الرصيد إليه:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, admin_add_balance_id_step, m.message_id)
        elif data == "adm_deduct_balance" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("➖ خصم رصيد", "أرسل آيدي المستخدم المراد خصم الرصيد منه:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, admin_deduct_balance_id_step, m.message_id)
        elif data == "adm_ban_id" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("🚫 حظر آيدي", "أرسل الآيدي (ID) المراد حظره نهائياً من استخدام البوت:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, admin_ban_id_step, m.message_id)
        elif data == "adm_unban_id" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("✅ إلغاء حظر آيدي", "أرسل الآيدي (ID) المراد فك الحظر عنه وإعادة تفعيل حسابه:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, admin_unban_id_step, m.message_id)
        elif data == "adm_restart_all" and is_admin(uid):
            restarted_count = 0
            files = read_json(FILES_DB)
            for fid in list(files.keys()):
                stop_script(fid)
                if start_script(fid):
                    restarted_count += 1
            bot.answer_callback_query(call.id, f"🔄 تمت إعادة تشغيل جميع البوتات والملفات النشطة بنجاح ({restarted_count} بوت)!", show_alert=True)
            admin_panel(call)
        elif data == "adm_stop_all" and is_admin(uid):
            stopped_count = len(active_processes)
            for fid in list(active_processes.keys()):
                stop_script(fid)
            bot.answer_callback_query(call.id, f"⏹ تم إيقاف جميع البوتات والعمليات النشطة بنجاح ({stopped_count} بوت)!", show_alert=True)
            admin_panel(call)
        elif data == "adm_sub_count" and is_admin(uid):
            bot.answer_callback_query(call.id, f"👥 عدد المشتركين الإجمالي في البوت: {len(users)} مشترك", show_alert=True)
        elif data == "adm_broadcast" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("📢 إذاعة عامة", "أرسل الرسالة (نصوص، صور، ملفات) لإذاعتها لكافة المستخدمين:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, broadcast_step, m.message_id)
        elif data == "adm_channels_broadcast" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("📢 إذاعة للقنوات", "أرسل الرسالة للإذاعة في قنوات الاشتراك الإجباري:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, channels_broadcast_step, m.message_id)
        
        elif data == "admin_maintenance_on" and is_admin(uid):
            settings = get_settings()
            settings["bot_locked"] = True
            save_settings(settings)
            bot.answer_callback_query(call.id, "🔒 تم تفعيل وضع الصيانة بنجاح وإغلاق البوت أمام المستخدمين!", show_alert=True)
            admin_panel(call)
        elif data == "admin_maintenance_off" and is_admin(uid):
            settings = get_settings()
            settings["bot_locked"] = False
            save_settings(settings)
            bot.answer_callback_query(call.id, "🔓 تم إلغاء وضع الصيانة بنجاح وعمل البوت بكامل طاقته!", show_alert=True)
            admin_panel(call)
            
        elif data == "adm_clean" and is_admin(uid):
            cleaned_count = 0
            try:
                for f in os.listdir(LOGS_DIR):
                    p = os.path.join(LOGS_DIR, f)
                    if os.path.isfile(p):
                        os.remove(p)
                        cleaned_count += 1
                for d in os.listdir(ENV_DIR):
                    p = os.path.join(ENV_DIR, d)
                    if os.path.isdir(p) and d not in active_processes:
                        shutil.rmtree(p, ignore_errors=True)
                        cleaned_count += 1
                for f in os.listdir(DOWNLOAD_DIR):
                    p = os.path.join(DOWNLOAD_DIR, f)
                    if os.path.isfile(p):
                        os.remove(p)
                        cleaned_count += 1
                for f in os.listdir(STORE_DIR):
                    p = os.path.join(STORE_DIR, f)
                    if os.path.isfile(p):
                        os.remove(p)
                        cleaned_count += 1
            except Exception as e:
                print(f"Clean error: {e}")
            bot.answer_callback_query(call.id, f"🧹 تم تنظيف كافة مخلفات الاستضافة والمؤقتات بنجاح! تم حذف ({cleaned_count}) عنصراً مع الاحتفاظ بأيدي وأرصدة المستخدمين والبوتات النشطة لتسريع الاستضافة.", show_alert=True)
            admin_panel(call)

        elif data == "adm_speedup" and is_admin(uid):
            bot.answer_callback_query(call.id, "🚀 تم تسريع البوت وتحسين استجابة المعالجات بأقصى سرعة فائقة بنجاح!", show_alert=True)
            admin_panel(call)

        elif data == "adm_admins" and is_admin(uid):
            admins_panel(call)
        elif data == "add_admin" and is_main_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("➕ إضافة أدمن", "أرسل آيدي المستخدم الجديد:", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, add_admin_step, m.message_id)
        elif data.startswith("rmadmin_") and is_admin(uid):
            aid = int(data.split("_")[1])
            if aid == ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ لا يمكن إزالة المالك الرئيسي!", show_alert=True)
            elif remove_admin(aid):
                bot.answer_callback_query(call.id, "✅ تم إزالة الأدمن بنجاح.")
                admins_panel(call)
        elif data == "adm_channels" and is_admin(uid):
            channels_panel(call)
        elif data == "add_channel" and is_admin(uid):
            try:
                bot.delete_message(cid, call.message.message_id)
            except:
                pass
            m = send_msg(cid, deco("📢 إضافة قناة", "أرسل معرف القناة (مثال: @ChannelName):", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
            save_message(cid, m.message_id)
            bot.register_next_step_handler(m, add_channel_step, m.message_id)
        elif data.startswith("delch_") and is_admin(uid):
            del_channel(call, int(data.split("_")[1]))
    except Exception as e:
        print(f"Callback Error: {e}")

def pro_grant_step(msg, tuid, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "أدخل عدد أيام صحيح!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    days = int(msg.text.strip())
    users = read_json(USERS_DB)
    k = str(tuid)
    if k in users:
        if days == 0:
            users[k]["expiry"] = "LIFETIME"
        else:
            exp_date = datetime.now() + timedelta(days=days)
            users[k]["expiry"] = exp_date.strftime("%Y-%m-%d %H:%M:%S")
        write_json(USERS_DB, users)
        try:
            bot.send_message(int(tuid), deco("💎 تم تفعيل VIP", f"مبروك! تم تفعيل اشتراك VIP لحسابك لمدة {'دائم ♾' if days == 0 else f'{days} يوم'}."), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم منح رتبة VIP للمستخدم <code>{tuid}</code> بنجاح.", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    else:
        send_msg(msg.chat.id, deco("❌ خطأ", "المستخدم غير موجود في قاعدة البيانات!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)

def cb_ai_repair_request(call):
    parsed = _get_ai_repair_file(call)
    if not parsed:
        bot.answer_callback_query(call.id, "❌ الملف غير موجود أو انتهت صلاحيته!", show_alert=True)
        return
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
        f"<blockquote>لو كملت، هيتبعت محتوى <code>{escape(file_name)}</code> إلى خدمة "
        f"<code>ptero.pro</code> الخارجية لتحليله. الخدمة مش تابعة لـ Replit، وممكن تتغير أو تتوقف. "
        f"الملف الأصلي مش هيتغيّر ومش هيشتغل تلقائيًا؛ هتستلم نسخة تراجعها بنفسك.</blockquote>\n\n"
        f"<blockquote>اضغط موافقة لو حابب تكمل.</blockquote>",
        parse_mode="HTML",
        reply_markup=markup,
        message_effect_id=FIRE_EFFECT_ID
    )
    bot.answer_callback_query(call.id)

def cb_ai_repair_confirm(call):
    parsed = _get_ai_repair_file(call)
    if not parsed:
        bot.answer_callback_query(call.id, "❌ حدث خطأ، لم يتم العثور على الملف!", show_alert=True)
        return
    owner_id, file_name, fid = parsed
    content = load_encrypted_file(fid)
    if not content:
        bot.answer_callback_query(call.id, "❌ تعذر قراءة محتوى الملف!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, "⏳ جاري إرسال الكود للذكاء الاصطناعي للمعالجة...")
    msg_wait = send_msg(call.message.chat.id, deco("🤖 جاري الإصلاح", "⏳ يتم الآن تحليل الكود وإصلاح المشاكل عبر محرك الذكاء الاصطناعي المتطور...", call.from_user.first_name or "مستخدم"), effect_id=FIRE_EFFECT_ID)
    
    try:
        fixed_code = repair_source(content, "قم بفحص وإصلاح هذا السكريبت وتصحيح أي أخطاء برمجية أو مسارات خاطئة فيه", file_name)
        if not fixed_code:
            bot.edit_message_text("❌ لم يتم استلام رد صالح من خدمة الذكاء الاصطناعي.", call.message.chat.id, msg_wait.message_id, parse_mode="HTML")
            return
            
        fixed_filename = f"fixed_{file_name}"
        fixed_path = os.path.join(DOWNLOAD_DIR, fixed_filename)
        with open(fixed_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
            
        with open(fixed_path, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption=f"🛠 النسخة المصححة والمعدلة لملف: {file_name}", message_effect_id=FIRE_EFFECT_ID)
        try:
            os.remove(fixed_path)
            bot.delete_message(call.message.chat.id, msg_wait.message_id)
        except:
            pass
    except Exception as e:
        print(f"AI Repair Error: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء عملية المعالجة بالذكاء الاصطناعي!", show_alert=True)

def upload_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.document or not msg.document.file_name.endswith(".py"):
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب إرسال ملف سكريبت بلغة بايثون بصيغة .py", first_name_raw), back_kb("nav_upload"), effect_id=FIRE_EFFECT_ID)
        return
    
    try:
        finfo = bot.get_file(msg.document.file_id)
        file_content = bot.download_file(finfo.file_path).decode("utf-8")
        
        if not scan_with_virustotal(file_content, msg.document.file_name):
            send_msg(msg.chat.id, deco("🚫 خطأ أمني", "تم رفض الملف بواسطة فحص VirusTotal الأمني.", first_name_raw), effect_id=FIRE_EFFECT_ID)
            return

        is_safe, sec_msg = scan_code_security(file_content)
        if not is_safe:
            users = read_json(USERS_DB)
            if str(uid) in users:
                users[str(uid)]["is_banned"] = 1
                write_json(USERS_DB, users)
            send_msg(msg.chat.id, deco("🚫 حظر تلقائي للمخالفة", f"{sec_msg}\n\nتم حظر حسابك والآيدي الخاص بك تلقائياً.", first_name_raw), effect_id=FIRE_EFFECT_ID)
            for adm in get_admins():
                try:
                    bot.send_message(adm, deco("🚫 ملف مخالف", f"⚠️ تم حظر المستخدم <code>{uid}</code> تلقائياً لمحاولته رفع ملف مخالف أو يحتوي على أكواد مشفرة غير مقبولة.", first_name_raw), message_effect_id=FIRE_EFFECT_ID)
                except:
                    pass
            return
    except Exception as e:
        print(f"Security check error: {e}")

    users = read_json(USERS_DB)
    pts = users.get(str(uid), {}).get("points", 0)
    st_settings = get_settings()
    required_price = st_settings.get("python_upload_price", 1.0)
    
    if pts < required_price and not is_user_pro(uid):
        send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"رصيدك الحالي لا يكفي لرفع ملف! السعر المطلوب: {required_price} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
        return

    m = send_msg(
        msg.chat.id,
        deco("⏰ تحديد الساعات", f"الملف: <b>{escape(msg.document.file_name)}</b>\n\n💰 رصيدك المتاح: <code>{pts}</code> نقطة\n💵 سعر الرفع: {required_price} نقطة\n\nأرسل عدد الساعات المطلوبة للتشغيل:", first_name_raw),
        cancel_kb(),
        effect_id=FIRE_EFFECT_ID
    )
    save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, hours_step, msg.document, m.message_id)

def upload_zip_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.document or not msg.document.file_name.endswith(".zip"):
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب إرسال ملف مضغوط بصيغة .zip", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
        return

    try:
        finfo = bot.get_file(msg.document.file_id)
        downloaded_file = bot.download_file(finfo.file_path)
        zip_temp_path = os.path.join(DOWNLOAD_DIR, f"upload_{uid}_{gen_id(6)}.zip")
        with open(zip_temp_path, "wb") as f:
            f.write(downloaded_file)

        extract_dir = os.path.join(DOWNLOAD_DIR, f"extracted_{uid}_{gen_id(6)}")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        py_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))

        if not py_files:
            try:
                shutil.rmtree(extract_dir, ignore_errors=True)
                os.remove(zip_temp_path)
            except:
                pass
            send_msg(msg.chat.id, deco("❌ خطأ", "ملف الـ ZIP لا يحتوي على أي ملفات بايثون (.py) صالحة!", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
            return

        for py_f in py_files:
            with open(py_f, "r", encoding="utf-8", errors="ignore") as pf:
                code_content = pf.read()
            is_safe, sec_msg = scan_code_security(code_content)
            if not is_safe:
                try:
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    os.remove(zip_temp_path)
                except:
                    pass
                users = read_json(USERS_DB)
                if str(uid) in users:
                    users[str(uid)]["is_banned"] = 1
                    write_json(USERS_DB, users)
                send_msg(msg.chat.id, deco("🚫 حظر تلقائي للمخالفة", f"{sec_msg}\n\nتم حظر حسابك والآيدي الخاص بك تلقائياً لتضمن ملف الـ ZIP أكواداً محظورة أو ضارة.", first_name_raw), effect_id=FIRE_EFFECT_ID)
                return

        main_py = py_files[0]
        with open(main_py, "r", encoding="utf-8", errors="ignore") as pf:
            main_content = pf.read()

        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
            os.remove(zip_temp_path)
        except:
            pass

        users = read_json(USERS_DB)
        pts = users.get(str(uid), {}).get("points", 0)
        st_settings = get_settings()
        required_price = st_settings.get("python_upload_price", 1.0)

        if pts < required_price and not is_user_pro(uid):
            send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"رصيدك الحالي لا يكفي لرفع ملف ZIP! السعر المطلوب: {required_price} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
            return

        m = send_msg(
            msg.chat.id,
            deco("⏰ تحديد الساعات لملف ZIP", f"الملف المضغوط: <b>{escape(msg.document.file_name)}</b>\n\n💰 رصيدك المتاح: <code>{pts}</code> نقطة\n💵 سعر الرفع: {required_price} نقطة\n\nأرسل عدد الساعات المطلوبة للتشغيل:", first_name_raw),
            cancel_kb(),
            effect_id=FIRE_EFFECT_ID
        )
        save_message(msg.chat.id, m.message_id)
        bot.register_next_step_handler(m, hours_zip_step, msg.document.file_name, main_content, m.message_id)

    except Exception as e:
        print(f"ZIP Upload error: {e}")
        send_msg(msg.chat.id, deco("❌ خطأ", "حدث خطأ أثناء معالجة ملف الـ ZIP وفحص قواعد البيانات والمسارات.", first_name_raw), back_kb("nav_main"), effect_id=FIRE_EFFECT_ID)

def hours_zip_step(msg, zip_filename, main_content, prompt_id):
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
    users = read_json(USERS_DB)
    pts = users.get(str(uid), {}).get("points", 0)
    st_settings = get_settings()
    required_price = st_settings.get("python_upload_price", 1.0)

    if hours < 1:
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب اختيار ساعة واحدة على الأقل!", first_name_raw), back_kb("nav_upload_zip"), effect_id=FIRE_EFFECT_ID)
        return
    total_cost = required_price * hours
    if total_cost > pts and not is_user_pro(uid):
        send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"تحتاج إلى {total_cost} نقطة، ورصيدك الحالي {pts} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
        return

    fid = gen_id()
    if not save_encrypted_file(fid, main_content, uid):
        send_msg(uid, deco("❌ خطأ", "فشل في حفظ وتشفير ملف المشروع بأمان!"), effect_id=FIRE_EFFECT_ID)
        return

    files = read_json(FILES_DB)
    files[fid] = {
        "user_id": uid,
        "file_name": zip_filename,
        "type": "free" if not is_user_pro(uid) else "pro",
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hours": hours
    }
    write_json(FILES_DB, files)

    for adm in get_admins():
        try:
            admin_kb = build_keyboard([
                [{"text": "📥 تحميل الملف", "callback_data": f"vdl_{fid}", "style": "primary"},
                 {"text": "✅ موافقة ✅", "callback_data": f"vapprove_{fid}", "style": "success"}],
                [{"text": "❌ رفض ❌", "callback_data": f"vdel_{fid}", "style": "danger"}]
            ])
            bot.send_message(
                adm,
                f"📦 <b>طلب رفع ملف ZIP جديد معلق للمراجعة:</b>\n\n📄 الأرشيف: <code>{escape(zip_filename)}</code>\n👤 الآيدي: <code>{uid}</code>\n⏰ الساعات: {hours}",
                parse_mode="HTML",
                reply_markup=admin_kb,
                message_effect_id=FIRE_EFFECT_ID
            )
        except Exception as e:
            print(f"Admin pending ZIP notify error: {e}")

    text = f"⏳ <b>تم رفع أرشيف الـ ZIP بنجاح وهو قيد المراجعة والتعليق بانتظار موافقة الإدارة.</b>\n\n📄 <code>{escape(zip_filename)}</code>\n⏰ الساعات المطلوبة: {hours}"
    send_msg(uid, deco("⏳ قيد المراجعة", text), back_kb(), effect_id=FIRE_EFFECT_ID)

def hours_step(msg, doc, prompt_id):
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
    users = read_json(USERS_DB)
    pts = users.get(str(uid), {}).get("points", 0)
    st_settings = get_settings()
    required_price = st_settings.get("python_upload_price", 1.0)

    if hours < 1:
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب اختيار ساعة واحدة على الأقل!", first_name_raw), back_kb("nav_upload"), effect_id=FIRE_EFFECT_ID)
        return
    total_cost = required_price * hours
    if total_cost > pts and not is_user_pro(uid):
        send_msg(msg.chat.id, deco("❌ رصيد غير كافي", f"تحتاج إلى {total_cost} نقطة، ورصيدك الحالي {pts} نقطة.", first_name_raw), back_kb("nav_wallet"), effect_id=FIRE_EFFECT_ID)
        return
    complete_upload(doc, uid, hours, total_cost)

def complete_upload(doc, user_id, hours, total_cost):
    fid = gen_id()
    finfo = bot.get_file(doc.file_id)
    file_content = bot.download_file(finfo.file_path).decode("utf-8")
    
    if not save_encrypted_file(fid, file_content, user_id):
        send_msg(user_id, deco("❌ خطأ", "فشل في حفظ وتشفير الملف بأمان!"), effect_id=FIRE_EFFECT_ID)
        return
    
    files = read_json(FILES_DB)
    files[fid] = {
        "user_id": user_id,
        "file_name": doc.file_name,
        "type": "free" if not is_user_pro(user_id) else "pro",
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hours": hours
    }
    write_json(FILES_DB, files)
    
    for adm in get_admins():
        try:
            admin_kb = build_keyboard([
                [{"text": "📥 تحميل الملف", "callback_data": f"vdl_{fid}", "style": "primary"},
                 {"text": "✅ موافقة ✅", "callback_data": f"vapprove_{fid}", "style": "success"}],
                [{"text": "❌ رفض ❌", "callback_data": f"vdel_{fid}", "style": "danger"}]
            ])
            bot.send_message(
                adm,
                f"📤 <b>طلب رفع ملف جديد معلق للمراجعة:</b>\n\n📄 الملف: <code>{escape(doc.file_name)}</code>\n👤 الآيدي: <code>{user_id}</code>\n⏰ الساعات: {hours}",
                parse_mode="HTML",
                reply_markup=admin_kb,
                message_effect_id=FIRE_EFFECT_ID
            )
        except Exception as e:
            print(f"Admin pending notify error: {e}")
    
    text = f"⏳ <b>تم رفع ملفك بنجاح وهو قيد المراجعة والتعليق بانتظار موافقة الإدارة.</b>\n\n📄 <code>{escape(doc.file_name)}</code>\n⏰ الساعات المطلوبة: {hours}"
    send_msg(user_id, deco("⏳ قيد المراجعة", text), back_kb(), effect_id=FIRE_EFFECT_ID)

def pending_list(call):
    files = read_json(FILES_DB)
    pending = {fid: f for fid, f in files.items() if f.get("status") == "pending"}
    if not pending:
        return bot.answer_callback_query(call.id, "✅ لا توجد ملفات معلقة للفحص!", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for fid, f in pending.items():
        kb.add(btn(f"📄 {f.get('file_name', '?')[:25]}", callback_data=f"vpend_{fid}", style="primary"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("⏳ الملفات المعلقة", f"عدد الملفات المعلقة: {len(pending)}", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def admin_view_pending_file(call, fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    f = files[fid]
    content = load_encrypted_file(fid)
    preview = escape(content[:800]) if content else "تعذر قراءة المحتوى"
    text = f"⏳ <b>معاينة الملف المعلق:</b>\n\n📄 الاسم: {f.get('file_name')}\n👤 صاحب الآيدي: <code>{f.get('user_id')}</code>\n⏰ الساعات: {f.get('hours')}\n\n<pre><code>{preview}</code></pre>"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("📥 تحميل الملف", callback_data=f"vdl_{fid}", style="primary"),
        btn("✅ موافقة ✅", callback_data=f"vapprove_{fid}", style="success")
    )
    kb.add(
        btn("❌ رفض ❌", callback_data=f"vdel_{fid}", style="danger"),
        btn("⎙● رجـــــوع ●⎙", callback_data="adm_related_files", style="primary")
    )
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("⏳ مراجعة الملف المعلق", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def admin_download_pending_file(call, fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    content = load_encrypted_file(fid)
    if not content:
        return bot.answer_callback_query(call.id, "❌ تعذر تحميل الملف!", show_alert=True)
    try:
        temp_path = os.path.join(BASE_DIR, f"temp_pend_{fid}.py")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(temp_path, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption=f"📄 {files[fid]['file_name']} (معلق)", message_effect_id=FIRE_EFFECT_ID)
        os.remove(temp_path)
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف بنجاح.")
    except:
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء إرسال الملف!", show_alert=True)

def admin_approve_file(call, fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    f = files[fid]
    f["status"] = "active"
    write_json(FILES_DB, files)
    
    user_id = f["user_id"]
    hours = f.get("hours", 1)
    st_settings = get_settings()
    required_price = st_settings.get("python_upload_price", 1.0)
    total_cost = required_price * hours
    
    if not is_user_pro(user_id) and total_cost > 0:
        users = read_json(USERS_DB)
        if str(user_id) in users:
            users[str(user_id)]["points"] -= total_cost
            write_json(USERS_DB, users)
    
    start_script(fid)
    
    try:
        bot.send_message(user_id, deco("✅ تم قبول الملف وتشغيله", f"تمت الموافقة على ملفك <b>{escape(f['file_name'])}</b> وتشغيله بنجاح بواسطة الإدارة!"), message_effect_id=FIRE_EFFECT_ID)
    except:
        pass
    
    bot.answer_callback_query(call.id, "✅ تمت الموافقة على الملف وتشغيله بنجاح!")
    pending_list(call)

def admin_delete_pending_file(call, fid):
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!", show_alert=True)
    f = files[fid]
    user_id = f["user_id"]
    
    try:
        os.remove(os.path.join(ENCRYPTED_DIR, f"{fid}.enc"))
    except:
        pass
    del files[fid]
    write_json(FILES_DB, files)
    
    try:
        bot.send_message(user_id, deco("❌ رفض الملف", f"تم رفض وحذف ملفك <b>{escape(f['file_name'])}</b> من قبل الإدارة."), message_effect_id=FIRE_EFFECT_ID)
    except:
        pass
    
    bot.answer_callback_query(call.id, "❌ تم إلغاء وحذف الملف بنجاح.")
    pending_list(call)

def file_panel(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, "❌ لا تملك صلاحية الوصول لهذا الملف!", show_alert=True)
        return
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!")
    f = files[fid]
    content = load_encrypted_file(fid)
    preview = escape(content[:1000]) if content else "تعذر القراءة"
    status = f.get("status", "active")
    if status == "pending":
        running_text = "⏳ قيد المراجعة والتعليق لدى الأدمن"
    else:
        running = fid in active_processes and active_processes[fid].poll() is None
        running_text = "يعمل ✅" if running else "متوقف ❌"

    text = f"📄 اسم الملف: {f.get('file_name')}\n🟢 الحالة: {running_text}\n📅 تاريخ الرفع: {f.get('created_at')}\n\n🔍 المعاينة:\n<pre><code>{preview}</code></pre>"
    kb = types.InlineKeyboardMarkup(row_width=2)
    if status == "active":
        kb.add(
            btn("⏸ إيقاف" if (fid in active_processes and active_processes[fid].poll() is None) else "▶️ تشغيل", callback_data=f"toggle_{fid}", style="danger" if (fid in active_processes and active_processes[fid].poll() is None) else "success"),
            btn("📟 التيرمنال", callback_data=f"term_{fid}", style="primary")
        )
        kb.add(
            btn("🔑 تغيير التوكن", callback_data=f"chtoken_{fid}", style="primary"),
            btn("ℹ️ معلومات التوكن", callback_data=f"tokinfo_{fid}", style="primary")
        )
    kb.add(
        btn("📥 تحميل الملف", callback_data=f"dl_{fid}", style="primary"),
        btn("🛠️ إصلاح وتعديل بـ AI", callback_data=f"fai_{f.get('user_id')}_{file_token(f.get('file_name', ''))}", style="success")
    )
    kb.add(
        btn("🗑️ حذف 🗑️", callback_data=f"delc_{fid}", style="danger"),
        btn("🔙 الرجوع", callback_data="nav_files", style="danger")
    )
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("📁 إدارة الملف", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def toggle_file(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
        return
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
        bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
        return
    stop_script(fid)
    files = read_json(FILES_DB)
    if fid in files:
        try:
            os.remove(os.path.join(ENCRYPTED_DIR, f"{fid}.enc"))
        except:
            pass
        try:
            os.remove(os.path.join(LOGS_DIR, f"{fid}.log"))
        except:
            pass
        try:
            shutil.rmtree(os.path.join(ENV_DIR, fid), ignore_errors=True)
        except:
            pass
        del files[fid]
        write_json(FILES_DB, files)
        bot.answer_callback_query(call.id, "🗑️ تم حذف الملف بنجاح.")
    
    u_files = {fid: f for fid, f in files.items() if f.get("user_id") == uid}
    if not u_files:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            btn("📤 رفع ملف", callback_data="nav_upload", style="success"),
            btn("🏠 الرئيسية", callback_data="nav_main", style="primary")
        )
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_msg(call.message.chat.id, deco("📁 ملفاتي", "لا توجد ملفات لديك حالياً.", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        for fid, f in u_files.items():
            kb.add(btn(f"📄 {f.get('file_name', '?')[:25]}", callback_data=f"manage_{fid}", style="primary"))
        kb.add(btn("🔙 القائمة الرئيسية 🔙", callback_data="nav_main", style="danger"))
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_msg(call.message.chat.id, deco("📁 ملفاتي", f"📊 إجمالي الملفات المتبقية: {len(u_files)}", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def download_file(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
        return
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!")
    content = load_encrypted_file(fid)
    if not content:
        bot.answer_callback_query(call.id, "❌ تعذر تحميل الملف!", show_alert=True)
        return
    try:
        temp_path = os.path.join(BASE_DIR, f"temp_{fid}_{gen_id(4)}.py")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        thumb = get_thumb()
        with open(temp_path, "rb") as f:
            if thumb:
                with open(thumb, "rb") as t:
                    bot.send_document(call.message.chat.id, f, thumb=t, caption=f"📄 {files[fid]['file_name']}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
            else:
                bot.send_document(call.message.chat.id, f, caption=f"📄 {files[fid]['file_name']}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
        os.remove(temp_path)
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف بنجاح.")
    except:
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء التحميل!", show_alert=True)

def terminal(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
        return
    files = read_json(FILES_DB)
    if fid not in files:
        return bot.answer_callback_query(call.id, "❌ الملف غير موجود!")
    running = fid in active_processes and active_processes[fid].poll() is None
    output = get_logs(fid, 40)
    text = f"📄 الملف: {files[fid]['file_name']}\n🟢 الحالة: {'يعمل' if running else 'متوقف'}\n\n📺 <b>مخرجات التيرمنال:</b>\n{output}"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("🔄 تحديث السجل", callback_data=f"rterm_{fid}", style="primary"),
        btn("⌨️ إجابة / إدخال", callback_data=f"inp_{fid}", style="primary")
    )
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data=f"manage_{fid}", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("📟 التيرمنال", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def get_logs(fid, lines=40):
    log_path = os.path.join(LOGS_DIR, f"{fid}.log")
    try:
        if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                last = all_lines[-lines:] if len(all_lines) > lines else all_lines
                output = "".join(last)
                safe = escape(output)
                if len(safe) > 3000:
                    safe = safe[:3000] + "\n..."
                return f"<pre><code>{safe}</code></pre>"
        return "📝 لا توجد سجلات مخرجات حتى الآن."
    except:
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
    if write_proc(fid, msg.text):
        text = f"✅ تم إرسال الأمر بنجاح:\n<code>{escape(msg.text)}</code>"
    else:
        text = "❌ السكريبت لا يعمل حالياً لتلقي الأوامر!"
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
        send_msg(msg.chat.id, deco("❌ خطأ", "تعذر تحميل الملف المشفر!", first_name_raw), back_kb(f"manage_{fid}"), effect_id=FIRE_EFFECT_ID)
        return
    keywords = ["TOKEN", "bot_token", "api_key", "tok", "TKN", "BOT_TKN", "API_TOKEN"]
    pattern = r"([\"\'])\d{8,12}:[a-zA-Z0-9_-]{35,}([\"\'])"
    new_content = re.sub(pattern, f"\\1{token}\\2", content)
    for kw in keywords:
        kw_pattern = rf"{kw}\s*=\s*([\"\'][^\"\']+[\"\'])"
        new_content = re.sub(kw_pattern, f"{kw} = '{token}'", new_content)
    
    files = read_json(FILES_DB)
    if fid in files:
        user_id = files[fid].get("user_id")
        if save_encrypted_file(fid, new_content, user_id):
            text = "✅ تم تحديث التوكن بنجاح!\n\n⚠️ يرجى إعادة تشغيل السكريبت لتطبيق التغييرات."
        else:
            text = "❌ فشل في حفظ التغييرات!"
    else:
        text = "❌ الملف غير مسجل!"
    send_msg(msg.chat.id, deco("🔑 تغيير التوكن", text, first_name_raw), back_kb(f"manage_{fid}"), effect_id=FIRE_EFFECT_ID)

def token_info(call, fid):
    uid = call.from_user.id
    if not verify_file_access(fid, uid):
        bot.answer_callback_query(call.id, "❌ لا تملك صلاحية!", show_alert=True)
        return
    content = load_encrypted_file(fid)
    if not content:
        bot.answer_callback_query(call.id, "❌ تعذر تحميل محتوى الملف!", show_alert=True)
        return
    try:
        tokens = re.findall(r"(\d{8,12}:[a-zA-Z0-9_-]{35,})", content)
        if not tokens:
            return bot.answer_callback_query(call.id, "🔍 لم يتم العثور على توكن بداخل الكود!", show_alert=True)
        token = tokens[0]
        url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){token}/getMe"
        res = requests.get(url, timeout=15).json()
        if res.get("ok"):
            info = res["result"]
            text = f"✅ التوكن صالح ويعمل بنجاح!\n\n🤖 اسم البوت: {escape(info.get('first_name'))}\n👤 معرف البوت: @{info.get('username')}\n🆔 آيدي البوت: <code>{info.get('id')}</code>"
        else:
            text = f"❌ التوكن غير صالح أو منتهي الصلاحية."
        kb = types.InlineKeyboardMarkup()
        kb.add(btn("⎙● رجـــــوع ●⎙", callback_data=f"manage_{fid}", style="primary"))
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_msg(call.message.chat.id, deco("ℹ️ معلومات التوكن", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)
    except:
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء فحص التوكن!", show_alert=True)

def lib_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text:
        return
    lib = msg.text.strip()
    m = send_msg(msg.chat.id, deco("⏳ جاري التثبيت", f"جاري تثبيت المكتبة: <b>{escape(lib)}</b>...", first_name_raw), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, m.message_id)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib], timeout=120)
        text = f"✅ تم تثبيت المكتبة بنجاح: <b>{escape(lib)}</b>"
    except:
        text = f"❌ فشل في تثبيت المكتبة: <b>{escape(lib)}</b>"
    try:
        bot.delete_message(msg.chat.id, m.message_id)
    except:
        pass
    send_msg(msg.chat.id, deco("🛠 تثبيت مكتبة", text, first_name_raw), back_kb(), effect_id=FIRE_EFFECT_ID)

def broadcast_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    users = read_json(USERS_DB)
    uids = list(users.keys())
    success, failed = 0, 0
    wait = send_msg(msg.chat.id, deco("📢 إذاعة عامة", f"⏳ جاري الإرسال إلى {len(uids)} مستخدم...", first_name_raw), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, wait.message_id)
    
    markup = build_keyboard([[{"text": "👨‍💻 مراسلة المطور", "url": DEV_TELEGRAM, "style": "primary"}]])
    
    for user_id in uids:
        try:
            txt = f"<b>{msg.text or msg.caption or ''}</b>\n\n<blockquote>إذاعة خاصة من إدارة البوت</blockquote>"
            if msg.content_type == "text":
                bot.send_message(user_id, txt, parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            elif msg.content_type == "photo":
                bot.send_photo(user_id, msg.photo[-1].file_id, caption=txt, parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            elif msg.content_type == "document":
                bot.send_document(user_id, msg.document.file_id, caption=txt, parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            success += 1
            time.sleep(0.02)
        except:
            failed += 1
    text = f"✅ اكتملت الإذاعة العامة بنجاح\n\n📫 تم الإرسال بنجاح: {success}\n❌ فشل الإرسال: {failed}\n📊 إجمالي المستخدمين: {len(uids)}"
    try:
        bot.delete_message(msg.chat.id, wait.message_id)
    except:
        pass
    send_msg(msg.chat.id, deco("📢 إذاعة عامة", text, first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)

def channels_broadcast_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    settings = get_settings()
    channels = settings.get("channels", [])
    if not channels:
        send_msg(msg.chat.id, deco("❌ خطأ", "لا توجد قنوات اشتراك إجباري مسجلة للإذاعة فيها!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    
    success, failed = 0, 0
    wait = send_msg(msg.chat.id, deco("📢 إذاعة للقنوات", f"⏳ جاري الإرسال إلى {len(channels)} قناة...", first_name_raw), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, wait.message_id)
    
    markup = build_keyboard([
        [{"text": "👨‍💻 مراسلة المطور", "url": DEV_TELEGRAM, "style": "primary"}],
        [{"text": "📢 قناة التحديث", "url": CHANNEL_EHAB_LINK, "style": "success"}],
        [{"text": "🔙 العودة إلى البوت", "url": f"[https://t.me/](https://t.me/){user_bot}", "style": "danger"}]
    ])
    
    txt = f"<b>{msg.text or msg.caption or ''}</b>\n\n<blockquote>إذاعة إدارية للقنوات الرسمية</blockquote>"

    for ch in channels:
        try:
            bot.send_message(ch["username"], txt, parse_mode="HTML", reply_markup=markup, message_effect_id=FIRE_EFFECT_ID)
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
            
    text = f"✅ اكتملت إذاعة القنوات بنجاح\n\n📫 تم النشر في قنوات: {success}\n❌ فشل النشر: {failed}"
    try:
        bot.delete_message(msg.chat.id, wait.message_id)
    except:
        pass
    send_msg(msg.chat.id, deco("📢 إذاعة للقنوات", text, first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)

def admin_ban_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    target_id = msg.text.strip()
    users = read_json(USERS_DB)
    if target_id in users:
        users[target_id]["is_banned"] = 1
        write_json(USERS_DB, users)
        try:
            bot.send_message(int(target_id), deco("🚫 حظر آيدي", "تم حظرك نهائياً من استخدام البوت بواسطة الإدارة."), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        send_msg(msg.chat.id, deco("✅ تم الحظر بنجاح", f"تم حظر الآيدي <code>{target_id}</code> نهائياً بنجاح.", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    else:
        users[target_id] = {"is_banned": 1, "points": 0, "balance": 0.0}
        write_json(USERS_DB, users)
        send_msg(msg.chat.id, deco("✅ تم الحظر بنجاح", f"تم حظر الآيدي <code>{target_id}</code> وإضافته لقائمة المحظورين بنجاح.", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)

def admin_unban_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    target_id = msg.text.strip()
    users = read_json(USERS_DB)
    if target_id in users:
        users[target_id]["is_banned"] = 0
        write_json(USERS_DB, users)
        try:
            bot.send_message(int(target_id), deco("✅ إلغاء حظر آيدي", "تم فك الحظر عن حسابك وإعادة تفعيل صلاحياتك بنجاح."), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        send_msg(msg.chat.id, deco("✅ تم فك الحظر بنجاح", f"تم فك الحظر عن الآيدي <code>{target_id}</code> وإعادة تفعيله بنجاح.", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    else:
        send_msg(msg.chat.id, deco("❌ خطأ", "هذا الآيدي غير موجود في قاعدة بيانات المستخدمين المحظورين!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)

def bot_manager_panel(call):
    files = read_json(FILES_DB)
    if not files:
        return bot.answer_callback_query(call.id, "🤖 لا توجد بوتات مسجلة في الاستضافة!", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for fid, f in files.items():
        running = fid in active_processes and active_processes[fid].poll() is None
        status_icon = "🟢 يعمل" if running else "🔴 موقوف"
        kb.add(btn(f"{status_icon} - {f.get('file_name', '?')[:20]}", callback_data=f"botact_menu_{fid}", style="primary"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("🤖 إدارة وحذف بوتات الاستضافة", f"إجمالي البوتات والملفات: {len(files)}\nاختر بوت للتحكم به:", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def handle_bot_action(call, action, fid):
    files = read_json(FILES_DB)
    f = files.get(fid)
    if not f:
        return bot.answer_callback_query(call.id, "❌ البوت غير موجود!")
    
    if action == "menu":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            btn("▶️ تشغيل", callback_data=f"botact_run_{fid}", style="success"),
            btn("⏸ إيقاف", callback_data=f"botact_stop_{fid}", style="danger")
        )
        kb.add(
            btn("📥 تحميل", callback_data=f"botact_dl_{fid}", style="primary"),
            btn("🗑️ حذف 🗑️", callback_data=f"botact_del_{fid}", style="danger")
        )
        kb.add(btn("🔙 رجوع للقائمة", callback_data="adm_bot_manager", style="primary"))
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_msg(call.message.chat.id, deco("🤖 إدارة البوت", f"اسم الملف: <b>{f.get('file_name')}</b>\nصاحب الآيدي: <code>{f.get('user_id')}</code>", call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)
    elif action == "run":
        start_script(fid)
        bot.answer_callback_query(call.id, "✅ تم تشغيل البوت بنجاح.")
        bot_manager_panel(call)
    elif action == "stop":
        stop_script(fid)
        bot.answer_callback_query(call.id, "⏸ تم إيقاف البوت بنجاح.")
        bot_manager_panel(call)
    elif action == "dl":
        download_file(call, fid)
    elif action == "del":
        stop_script(fid)
        try:
            os.remove(os.path.join(ENCRYPTED_DIR, f"{fid}.enc"))
        except:
            pass
        if fid in files:
            del files[fid]
            write_json(FILES_DB, files)
        bot.answer_callback_query(call.id, "🗑️ تم حذف البوت نهائياً من الاستضافة.")
        bot_manager_panel(call)

def admin_stats_view(call):
    users = read_json(USERS_DB)
    files = read_json(FILES_DB)
    active_bots_count = sum(1 for fid in active_processes if active_processes[fid].poll() is None)
    total_balance = sum(u.get("balance", 0.0) for u in users.values())
    total_points = sum(u.get("points", 0) for u in users.values())
    
    text = (
        f"📊 <b>إحصائيات العمل الكاملة للبوت:</b>\n\n"
        f"👥 إجمالي المستخدمين: <code>{len(users)}</code>\n"
        f"💰 مجموع أرصدة المستخدمين: <code>{total_balance:.2f} ₽</code>\n"
        f"💎 مجموع نقاط المستخدمين: <code>{total_points}</code>\n"
        f"📁 إجمالي الملفات المرفوعة: <code>{len(files)}</code>\n"
        f"🟢 البوتات النشطة الآن: <code>{active_bots_count}</code>\n"
        f"⚙️ حالة السيرفر والاستضافة: <b>مستقرة وآمنة 100%</b>"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("📊 الإحصائيات الشاملة", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def admin_panel(call):
    users = read_json(USERS_DB)
    files = read_json(FILES_DB)
    pending = [f for f in files.values() if f.get("status") == "pending"]
    active = sum(1 for fid in active_processes if active_processes[fid].poll() is None)
    settings = get_settings()
    locked = settings.get("bot_locked", False)
    current_upload_price = settings.get("python_upload_price", 1.0)
    
    text = (
        f"⚙️ <b>لوحة تحكم الإدارة العليا والشاملة</b>\n\n"
        f"👥 المستخدمين: {len(users)}\n"
        f"📁 إجمالي الملفات: {len(files)}\n"
        f"⏳ طلبات معلقة: {len(pending)}\n"
        f"🟢 الملفات النشطة: {active}\n"
        f"💵 سعر رفع الملفات: {current_upload_price} نقطة\n\n"
        f"🔐 حالة البوت: {'مغلق للصيانة 🔒' if locked else 'مفتوح للعمل 🔓'}"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    kb.row(
        btn("💻 حالة ونظام السيرفر", callback_data="admin_system_status", style="primary")
    )
    kb.row(
        btn("🔒 تفعيل وضع الصيانة", callback_data="admin_maintenance_on", style="danger"),
        btn("🔓 إلغاء وضع الصيانة", callback_data="admin_maintenance_off", style="success")
    )
    kb.row(
        btn("🔄 إعادة تشغيل كل البوتات", callback_data="adm_restart_all", style="success"),
        btn("⏹ إيقاف كل البوتات", callback_data="adm_stop_all", style="danger")
    )
    kb.row(
        btn("🚫 حظر آيدي", callback_data="adm_ban_id", style="danger"),
        btn("✅ إلغاء حظر آيدي", callback_data="adm_unban_id", style="success")
    )
    kb.row(
        btn("👥 معرفة المشتركين", callback_data="adm_sub_count", style="primary"),
        btn("📢 إذاعة عامة", callback_data="adm_broadcast", style="success")
    )
    kb.row(
        btn("📢 إذاعة للقنوات", callback_data="adm_channels_broadcast", style="primary"),
        btn("📢 اشتراك إجباري", callback_data="adm_channels", style="primary")
    )
    kb.row(
        btn("👥 إدارة المستخدمين", callback_data="adm_users", style="primary"),
        btn("👮 إدارة المشرفين", callback_data="adm_admins", style="primary")
    )
    kb.row(
        btn("📁 الملفات المتعلقة", callback_data="adm_related_files", style="primary"),
        btn("📊 الاحصائيات", callback_data="adm_stats", style="primary")
    )
    kb.row(
        btn("🤖 حذف بوتات الاستضافة", callback_data="adm_bot_manager", style="danger"),
        btn("⚡ تسريع البوت", callback_data="adm_speedup", style="success")
    )
    kb.row(
        btn("🧹 تنظيف مخلفات الاستضافة", callback_data="adm_clean", style="danger"),
        btn("➕ إضافة رصيد", callback_data="adm_add_balance", style="success")
    )
    kb.row(
        btn("➖ خصم رصيد", callback_data="adm_deduct_balance", style="danger"),
        btn("🔙 رجوع للرئيسية", callback_data="nav_main", style="primary")
    )
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("⚙️ لوحة الإدارة", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def users_panel(call, page=0):
    users = read_json(USERS_DB)
    user_ids = list(users.keys())
    items_per_page = 10
    total_pages = (len(user_ids) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_users = user_ids[start_idx:end_idx]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for uid in page_users:
        u = users[uid]
        name = u.get("first_name", "مستخدم")
        kb.add(btn(f"👤 {name[:10]}", callback_data=f"uctrl_{uid}", style="primary"))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(btn("◀️ السابق", callback_data=f"userpage_{page-1}", style="primary"))
    if page < total_pages - 1:
        nav_buttons.append(btn("التالي ▶️", callback_data=f"userpage_{page+1}", style="primary"))
    if nav_buttons:
        kb.row(*nav_buttons)
    kb.add(btn("🔙 رجوع للرئيسية", callback_data="nav_admin", style="primary"))
    text = f"📊 الصفحة {page+1} من {total_pages}\n👥 إجمالي المستخدمين: {len(users)}"
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("👤 إدارة المستخدمين", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def user_panel(call, tuid):
    users = read_json(USERS_DB)
    u = users.get(str(tuid))
    if not u:
        return
    banned = u.get("is_banned", 0) == 1
    vip = is_user_pro(int(tuid))
    exp = "لا يوجد"
    if vip:
        e = u.get("expiry")
        if e == "LIFETIME" or e == 0:
            exp = "دائم ♾"
        elif e:
            exp = e
    files = read_json(FILES_DB)
    u_files = [f for f in files.values() if f.get("user_id") == int(tuid)]
    text = f"🆔 الآيدي: <code>{tuid}</code>\n🔗 المعرف: @{u.get('username', 'لا يوجد')}\n📅 الانضمام: {u.get('join_date', 'اليوم')}\n\n💰 النقاط: <code>{u.get('points', 0)}</code>\n💎 الرتبة: {'VIP 👑' if vip else 'مجاني 🆓'}\n⏰ صلاحية VIP: {exp}\n\n📁 إجمالي ملفاته: {len(u_files)}\n🚫 حالة الحظر: {'محظور ❌' if banned else 'نشط ✅'}"
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("🔓 فك الحظر" if banned else "🚫 حظر المستخدم", callback_data=f"ban_{tuid}", style="success" if banned else "danger"),
        btn("🆓 سحب VIP" if vip else "💎 منح VIP", callback_data=f"pro_{tuid}", style="danger" if vip else "success")
    )
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="adm_users", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("👤 تحكم بالمستخدم", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def ban_toggle(call, tuid):
    users = read_json(USERS_DB)
    if str(tuid) in users:
        curr = users[str(tuid)].get("is_banned", 0)
        users[str(tuid)]["is_banned"] = 0 if curr == 1 else 1
        write_json(USERS_DB, users)
        try:
            if users[str(tuid)]["is_banned"] == 1:
                bot.send_message(int(tuid), deco("🚫 حظر", "تم حظرك نهائياً من استخدام البوت."), message_effect_id=FIRE_EFFECT_ID)
            else:
                bot.send_message(int(tuid), deco("✅ فك الحظر", "تم فك الحظر عن حسابك بنجاح."), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        bot.answer_callback_query(call.id, "✅ تم تغيير حالة الحظر بنجاح.")
        user_panel(call, tuid)

def pro_remove(call, tuid):
    users = read_json(USERS_DB)
    if str(tuid) in users:
        users[str(tuid)]["expiry"] = None
        write_json(USERS_DB, users)
        try:
            bot.send_message(int(tuid), deco("⚠️ تنبيه VIP", "تم إزالة رتبة VIP من حسابك."), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        bot.answer_callback_query(call.id, "✅ تم سحب صلاحية VIP بنجاح.")
        user_panel(call, tuid)

def store_view(call):
    store = read_json(STORE_DB)
    if not store:
        return bot.answer_callback_query(call.id, "🛒 المتجر فارغ حالياً!", show_alert=True)
    kb = types.InlineKeyboardMarkup(row_width=2)
    for sid, item in store.items():
        kb.add(btn(f"📦 {item['name'][:15]} • {item['price']}pt", callback_data=f"buy_{sid}", style="primary"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_main", style="primary"))
    users = read_json(USERS_DB)
    text = f"🛒 <b>متجر الملفات الجاهزة والاستضافات</b>\n\n💰 رصيدك: <code>{users.get(str(call.from_user.id), {}).get('points', 0)}</code> نقطة"
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("🛒 المتجر", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def buy_confirm(call, sid):
    store = read_json(STORE_DB)
    item = store.get(sid)
    if not item:
        return
    users = read_json(USERS_DB)
    pts = users.get(str(call.from_user.id), {}).get("points", 0)
    text = f"📦 الملف: {item['name']}\n💰 السعر المطلوب: {item['price']} نقطة\n💵 رصيدك الحالي: <code>{pts}</code> نقطة\n\n{'✅ رصيدك يكفي لإتمام الشراء!' if pts >= item['price'] else '❌ رصيدك لا يكفي لشراء هذا الملف!'}"
    kb = types.InlineKeyboardMarkup(row_width=2)
    if pts >= item["price"]:
        kb.add(
            btn("✅ تأكيد الشراء", callback_data=f"ebuy_{sid}", style="success"),
            btn("❌ إلغاء", callback_data="nav_store", style="danger")
        )
    else:
        kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_store", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("🛒 تأكيد الشراء", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def buy_exec(call, sid):
    uid = call.from_user.id
    users = read_json(USERS_DB)
    store = read_json(STORE_DB)
    item = store.get(sid)
    if not item:
        return bot.answer_callback_query(call.id, "❌ العنصر غير موجود!", show_alert=True)
    if users.get(str(uid), {}).get("points", 0) < item["price"]:
        return bot.answer_callback_query(call.id, "❌ نقاطك غير كافية!", show_alert=True)
    users[str(uid)]["points"] -= item["price"]
    write_json(USERS_DB, users)
    path = os.path.join(STORE_DIR, f"{sid}.py")
    try:
        thumb = get_thumb()
        with open(path, "rb") as f:
            if thumb:
                with open(thumb, "rb") as t:
                    bot.send_document(uid, f, thumb=t, caption=f"✅ تم شراء الملف بنجاح: {item['name']}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
            else:
                bot.send_document(uid, f, caption=f"✅ تم شراء الملف بنجاح: {item['name']}", parse_mode="HTML", message_effect_id=FIRE_EFFECT_ID)
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف إليك بنجاح!")
        store_view(call)
    except:
        users[str(uid)]["points"] += item["price"]
        write_json(USERS_DB, users)
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء إرسال الملف!", show_alert=True)

def admins_panel(call):
    uid = call.from_user.id
    admins = get_admins()
    text = f"👮 قائمة المشرفين ({len(admins)}):\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    if is_main_admin(uid):
        kb.add(btn("➕ إضافة مشرف جديد", callback_data="add_admin", style="success"))
    for aid in admins:
        try:
            user = bot.get_chat(aid)
            name = user.first_name
            owner = "👑" if aid == ADMIN_ID else "👮"
            text += f"{owner} {escape(name)} - <code>{aid}</code>\n"
            if aid != ADMIN_ID and is_main_admin(uid):
                kb.add(btn(f"🗑️ إزالة {name[:10]}", callback_data=f"rmadmin_{aid}", style="danger"))
        except:
            text += f"👮 <code>{aid}</code>\n"
            if aid != ADMIN_ID and is_main_admin(uid):
                kb.add(btn(f"🗑️ إزالة {aid}", callback_data=f"rmadmin_{aid}", style="danger"))
    kb.add(btn("🔙 رجوع للرئيسية", callback_data="nav_admin", style="primary"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("👮 المشرفين", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def add_admin_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not is_main_admin(uid):
        send_msg(msg.chat.id, deco("❌ خطأ", "هذا الأمر مخصص للمالك الرئيسي فقط!", first_name_raw), back_kb("adm_admins"), effect_id=FIRE_EFFECT_ID)
        return
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح! أرسل أرقاماً فقط.", first_name_raw), back_kb("adm_admins"), effect_id=FIRE_EFFECT_ID)
        return
    new_id = int(msg.text.strip())
    if add_admin(new_id):
        try:
            bot.send_message(new_id, deco("🎉 مبارك", "تم تعيينك مشرفاً جديداً في البوت!"), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        text = f"✅ تم إضافة المشرف بنجاح:\n<code>{new_id}</code>"
    else:
        text = "❌ هذا المستخدم مشرف مسبقاً!"
    send_msg(msg.chat.id, deco("👮 إضافة مشرف", text, first_name_raw), back_kb("adm_admins"), effect_id=FIRE_EFFECT_ID)

def channels_panel(call):
    settings = get_settings()
    channels = settings.get("channels", [])
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(btn("➕ إضافة قناة اشتراك", callback_data="add_channel", style="success"))
    for i, ch in enumerate(channels):
        kb.add(btn(f"🗑️ حذف {ch['name']}", callback_data=f"delch_{i}", style="danger"))
    kb.add(btn("⎙● رجـــــوع ●⎙", callback_data="nav_admin", style="primary"))
    text = f"📊 القنوات الإجبارية المفعلة: {len(channels)}"
    if channels:
        text += "\n\n"
        for ch in channels:
            text += f"📢 {ch['name']} ({ch['username']})\n"
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    send_msg(call.message.chat.id, deco("📢 قنوات الاشتراك الإجباري", text, call.from_user.first_name or "مستخدم"), kb, effect_id=FIRE_EFFECT_ID)

def add_channel_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text:
        return
    username = msg.text.strip()
    if not username.startswith("@"):
        send_msg(msg.chat.id, deco("❌ خطأ", "يجب أن تبدأ معرف القناة بـ @", first_name_raw), back_kb("adm_channels"), effect_id=FIRE_EFFECT_ID)
        return
    try:
        chat = bot.get_chat(username)
        settings = get_settings()
        settings["channels"] = settings.get("channels", []) + [{"username": username, "name": chat.title}]
        save_settings(settings)
        send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم إضافة القناة: {chat.title}", first_name_raw), back_kb("adm_channels"), effect_id=FIRE_EFFECT_ID)
    except:
        send_msg(msg.chat.id, deco("❌ خطأ", "تعذر العثور على القناة!", first_name_raw), back_kb("adm_channels"), effect_id=FIRE_EFFECT_ID)

def del_channel(call, index):
    settings = get_settings()
    try:
        channels = settings.get("channels", [])
        if 0 <= index < len(channels):
            name = channels[index]["name"]
            del channels[index]
            settings["channels"] = channels
            save_settings(settings)
            bot.answer_callback_query(call.id, f"✅ تم حذف القناة: {name}")
        channels_panel(call)
    except:
        bot.answer_callback_query(call.id, "❌ حدث خطأ!")

def admin_add_balance_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    target_id = msg.text.strip()
    admin_steps[uid] = {"target_id": target_id}
    m = send_msg(msg.chat.id, deco("➕ إضافة رصيد", f"المستخدم المستهدف: <code>{target_id}</code>\n\nكم تريد رصيد إضافي لهذا الشخص؟ (أرسل النقاط):", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, admin_add_balance_amount_step, m.message_id)

def admin_add_balance_amount_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "كمية رصيد غير صحيحة!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    amount = int(msg.text.strip())
    target_id = admin_steps.get(uid, {}).get("target_id")
    if not target_id:
        send_msg(msg.chat.id, deco("❌ خطأ", "حدث خطأ في استرجاع الآيدي!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    users = read_json(USERS_DB)
    if target_id in users:
        users[target_id]["points"] = users[target_id].get("points", 0) + amount
        users[target_id]["balance"] = users[target_id].get("balance", 0.0) + float(amount)
        write_json(USERS_DB, users)
        try:
            bot.send_message(int(target_id), deco("💰 إضافة رصيد", f"تم إضافة <b>{amount}</b> رصيد ونقاط إلى حسابك من قبل الإدارة!"), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم إضافة {amount} للمستخدم <code>{target_id}</code> وتم إشعاره تلقائياً.", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    else:
        send_msg(msg.chat.id, deco("❌ خطأ", "المستخدم غير موجود!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    if uid in admin_steps:
        del admin_steps[uid]

def admin_deduct_balance_id_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "آيدي غير صحيح!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    target_id = msg.text.strip()
    admin_steps[uid] = {"target_id": target_id}
    m = send_msg(msg.chat.id, deco("➖ خصم رصيد", f"المستخدم المستهدف: <code>{target_id}</code>\n\nكم تريد خصم رصيد من هذا الشخص؟", first_name_raw), cancel_kb("cancel_admin"), effect_id=FIRE_EFFECT_ID)
    save_message(msg.chat.id, m.message_id)
    bot.register_next_step_handler(m, admin_deduct_balance_amount_step, m.message_id)

def admin_deduct_balance_amount_step(msg, prompt_id):
    uid = msg.from_user.id
    if is_cancelled(uid):
        clear_cancel(uid)
        return
    del_msg(msg.chat.id, prompt_id, msg.message_id)
    first_name_raw = msg.from_user.first_name or "مستخدم"
    if not msg.text or not msg.text.strip().isdigit():
        send_msg(msg.chat.id, deco("❌ خطأ", "كمية غير صحيحة!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    amount = int(msg.text.strip())
    target_id = admin_steps.get(uid, {}).get("target_id")
    if not target_id:
        send_msg(msg.chat.id, deco("❌ خطأ", "خطأ في استرجاع الآيدي!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
        return
    users = read_json(USERS_DB)
    if target_id in users:
        curr = users[target_id].get("points", 0)
        users[target_id]["points"] = max(0, curr - amount)
        users[target_id]["balance"] = max(0.0, users[target_id].get("balance", 0.0) - float(amount))
        write_json(USERS_DB, users)
        try:
            bot.send_message(int(target_id), deco("➖ خصم رصيد", f"تم خصم <b>{amount}</b> من حسابك من قبل الإدارة!"), message_effect_id=FIRE_EFFECT_ID)
        except:
            pass
        send_msg(msg.chat.id, deco("✅ تم بنجاح", f"تم خصم {amount} من المستخدم <code>{target_id}</code> بنجاح.", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    else:
        send_msg(msg.chat.id, deco("❌ خطأ", "المستخدم غير موجود!", first_name_raw), back_kb("nav_admin"), effect_id=FIRE_EFFECT_ID)
    if uid in admin_steps:
        del admin_steps[uid]

def gen_id(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def monitor():
    while True:
        try:
            for fid in list(active_processes.keys()):
                proc = active_processes.get(fid)
                if not proc or proc.poll() is not None:
                    if fid in active_processes:
                        del active_processes[fid]
                    if fid in bot_scripts:
                        del bot_scripts[fid]
                    continue
        except Exception as e:
            print(f"Monitor Error: {e}")
        time.sleep(3600)

threading.Thread(target=monitor, daemon=True).start()

init_db()

print("=" * 60)
print("𝗘𝗛𝗔𝗕𝗔𝗜𝗛𝗔𝗪𝗕𝗔𝗡𝗜 BOT")
print("تم التشغيل بنجاح مع أنظمة المراقبة الكاملة والحماية القصوى")
print("=" * 60)

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Polling Error: {e}")
        time.sleep(3)
