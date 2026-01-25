import asyncio
import logging
import random
import time
import os
from threading import Thread
from datetime import datetime

import requests
from flask import Flask
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ========= TIMEZONE FIX (Asia/Dhaka) =========
try:
    from zoneinfo import ZoneInfo  # py3.9+
    TZ = ZoneInfo("Asia/Dhaka")
except Exception:
    TZ = None  # fallback

def now_hms():
    if TZ:
        return datetime.now(TZ).strftime("%H:%M:%S")
    # fallback: force +06 if zoneinfo missing
    return datetime.utcfromtimestamp(time.time() + 6 * 3600).strftime("%H:%M:%S")

# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"  # ✅ শুধু এখানেই টোকেন বসাবি

TARGET_CHANNEL = -1003293007059

BRAND_NAME = "𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# Password from Google Sheet A1
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_GID = "0"
PASSWORD_CACHE_SECONDS = 20

MAX_LOSS_STOP = 8

# ================= API LINKS =================
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= STICKERS =================
STICKERS = {
    # Prediction stickers
    "PRED_1M": {
        "BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
        "SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    },
    "PRED_30S": {
        # ✅ 30S sticker उल্টা যাওয়া ফিক্স: BIG->TuV, SMALL->TuZ
        "BIG": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
        "SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",
    },

    # Win/Loss stickers
    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    "WIN_ANY": "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",
    "LOSS_ANY": "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",

    # Win random
    "WIN_RANDOM": [
        "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
        "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAnQKcVYHd8IiRqfBXTgE",
        "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
        "CAACAgUAAxkBAAEQT_tpc4E3AxHmgW9VWKrzWjxlrvzSowACghkAAlbXcFWxdto6TqiBrzgE",
        "CAACAgUAAxkBAAEQT_9pc4FHKn0W6ZfWOSaN6FUPzfmbnQACXR0AAqMbMFc-_4DHWbq7sjgE",
        "CAACAgUAAxkBAAEQUAFpc4FIokHE09p165cCsWiUYV648wACuhQAAo3aMVeAsNW9VRuVvzgE",
        "CAACAgUAAxkBAAEQUANpc4FJNTnfuBiLe-dVtoNCf3CQlAAC9xcAArE-MFfS5HNyds2tWTgE",
        "CAACAgUAAxkBAAEQUAVpc4FKhJ_stZ3VRRzWUuJGaWbrAgACOhYAAst6OVehdeQEGZlXiDgE",
        "CAACAgUAAxkBAAEQUAtpc4HcYxkscyRY2rhAAcmqMR29eAACOBYAAh7fwVU5Xy399k3oFDgE",
        "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE",
    ],

    # Color signal
    "COLOR": {
        "RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
        "GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
    },

    # Session start base + extra
    "START_BASE": "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
    "START_EXTRA": [
        "CAACAgUAAxkBAAEQT_lpc4EvleS6GJIogvkFzlcAAV6T7PsAArYaAAIOJIBV6qeBrzw1_oc4BA",
        "CAACAgUAAxkBAAEQTuRpczxpKCooU6JW2F53jWSEr7SZnQACZBUAAtEWOFcRzggHRna-EzgE",
    ],

    # ✅ তোমার নতুন mode-select sticker
    "MODE_SELECT": {
        "30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
        "1M": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",
    },

    # Extra random (you added)
    "EXTRA_RANDOM": [
        "CAACAgUAAxkBAAEQTudpczxpoCLQ2pIXCqANpddRbHX9ngACKhYAAoBTMVfQP_QoToLXkzgE",
        "CAACAgUAAxkBAAEQT_dpc4Eqt5r28E8WwxaZnW8X2t58RQACsw8AAoV9CFW0IyDz2PAL5DgE",
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE",
        "CAACAgUAAxkBAAEQUDRpc4VJP7cgZhVHhqzQsiV3hNLI5wACCQ4AAk9o-VW3jbWfWUVQrjgE",
        "CAACAgUAAxkBAAEQUDZpc4VMJx694uE09-ZWlks_anzAvAACXBsAAv4b-FXj9l4eQ-g5-jgE",
        "CAACAgUAAxkBAAEQUDhpc4VM6rq1VbSAPaCdCeaR0eReHwACAhIAAkEj8VWFHkUbgA0-njgE",
    ],

    # Win count serial stickers (all you pasted)
    "WIN_COUNT": [
        "CAACAgUAAxkBAAEQUA1pc4IKjtrvSWe2ssLEqZ88cAABYW8AAsoiAALegIlVctTV3Pqbjmg4BA",
        "CAACAgUAAxkBAAEQUA5pc4IKOY43Rh4dwtmmwOC55ikPbQAClRkAAgWviFVWRlQ-8i4rHTgE",
        "CAACAgUAAxkBAAEQUA9pc4IL7ALl7rMzh_MNMtRQ7DlLHAACihoAAkI4iFVaqQABGzm-T_Q4BA",
        "CAACAgUAAxkBAAEQUBFpc4ILdPG1eK5pNvXmFC_0vOHp_AACFRsAAr9_iVW18_WchrZ20zgE",
        "CAACAgUAAxkBAAEQUBJpc4IMZqQnZDPs37vLnP3b_J_IewACjhcAAu1YiFVA_VudovtxjDgE",
        "CAACAgUAAxkBAAEQUBRpc4IMQdH7-Ykn95YFoVlYeUhDBAACCxwAAhFLiVUYVv2JfG18AzgE",
        "CAACAgUAAxkBAAEQUBVpc4INgqONigHjBaf9YBYco3kTEwACjBoAAv3AkVUti2I8W2Nq1zgE",
        "CAACAgUAAxkBAAEQUBdpc4INimNkAAHp-GukssM5EUr3778AAq0aAALqAAGQVZdyE0WiCx4COAQ",
        "CAACAgUAAxkBAAEQUBhpc4IOn5oxT8qW8r-aqEGsetWZPQACTxcAAjRYiFUHjTokMOpClDgE",
        "CAACAgUAAxkBAAEQUBppc4IOZeCvBnaSTuKP2h4oTnj0fgACBBUAAlWakFUxHw3S0vZcfTgE",
        "CAACAgUAAxkBAAEQUBxpc4IPa3350tYXUf26d_Nviy8cywACCxYAAsUKkVVwb6huI3B2YzgE",
        "CAACAgUAAxkBAAEQUB1pc4IPfU_gZ6Qys4uCXUlXYmc5UwACKBgAAszSmVWaSI27doSUwTgE",
        "CAACAgUAAxkBAAEQUB9pc4IQMZ9syz2Fdb0qs1aaDhCLQwACJRkAAgvLmVWJ3q_PV1jr0DgE",
        "CAACAgUAAxkBAAEQTv9pcz6SkXdRsH5TsWOPBwN5F56-8wACoBAAAlfqcVUdJ4kalERlTTgE",
        "CAACAgUAAxkBAAEQTwABaXM-k7qfRUzUN78zyPXMs3Hhh4wAAh0TAAL2hWhV3RpXRX1cd8g4BA",
        "CAACAgUAAxkBAAEQTwJpcz6TPM36pjrzC8F-anJNnJbqTgACkBIAAtAqkFUWFLLSNNGZfDgE",
        "CAACAgUAAxkBAAEQTwZpcz6VYJ-aVbWHOsZJcpavAdXdMAACKBcAAqoXkVXuWgWwBVusNzgE",
        "CAACAgUAAxkBAAEQTwdpcz6VCusuBhcO2wezUqQknqHaBwACthAAAnnrmFWsePzzB00VNzgE",
        "CAACAgUAAxkBAAEQTwlpcz6VONfhZHHu-8tlEJwsOyRNzQACJBEAAmaYkVUu37wFysjR-zgE",
        "CAACAgUAAxkBAAEQTwppcz6WSrm6csgBEyTMYXRfwnpSkQACJxIAAiaykVVCqfU3OG6ECzgE",
        "CAACAgUAAxkBAAEQTwxpcz6WH4uAKaqfS0fvPSdXjLYhswACzxIAAjDdkFW6aCxiX9iZcTgE",
        "CAACAgUAAxkBAAEQTw1pcz6XDQV4XA8wuV0sfPBUd3yMbwACpBAAAlymkFUBzAElsldCQDgE",
        "CAACAgUAAxkBAAEQTw9pcz6XS2m2gEzWEaFrOPBG5g7XVgACXBAAAnnpmFUkULPqb9CWtjgE",
        "CAACAgUAAxkBAAEQTxBpcz6Xl8JEaRiElynIt96QIFFhLgAC1RAAAppZmFUhqvAIRJFOiTgE",
        "CAACAgUAAxkBAAEQTztpcz9zv_PJ_ueievAwdQ4NbhqQeAAChRQAAg02oFQY_rjzLxHMojgE",
        "CAACAgUAAxkBAAEQTzxpcz9zpYuLtX5kDf0WceGoQLmG3gACBBYAAsaqqFTdGFSRXI6vaTgE",
        "CAACAgUAAxkBAAEQTz1pcz9zGy6W5h2FOPRz7bBeQCpzEQAC6RcAArONqVSSKCuWYSwjQjgE",
        "CAACAgUAAxkBAAEQTz9pcz90RLnLD8caB_a9asYM2l_B2QACHhMAAhkFqFRPB9QzOV2bKjgE",
        "CAACAgUAAxkBAAEQT0Bpcz90rHd8Yoee2wwVIZ_UB0owRwACIRUAAstUqVQpHOftLWUOtDgE",
        "CAACAgUAAxkBAAEQT0Fpcz90nR-Q4OYgaejY9deU_TGEIgACmBcAAvbxqVT9ldxH8UG7uzgE",
        "CAACAgUAAxkBAAEQT0Npcz91CcAHS5r80hjuJQGqEBAwCwACjxcAAi4XqFSuMY65BKYvLzgE",
        "CAACAgUAAxkBAAEQT0Rpcz91yp7HSIBW2HiW4nzohLuw3gACWRQAArGMqVS2zthdR-Vk2jgE",
        "CAACAgUAAxkBAAEQT0Vpcz91QWr__pgcauKrt3c2xMfSVQACpBgAAoAkqFReTfwQgeVnWDgE",
        "CAACAgUAAxkBAAEQT0dpcz92q8K-y5nRFNh_6nsQAAEFHLAAArEUAALJi6hU2bdLLAxDgjI4BA",
        "CAACAgUAAxkBAAEQT0ppcz93sao2kKvVsAenpBBc1aStVwACHhQAAqu-qVSq2PMotKpprzgE",
        "CAACAgUAAxkBAAEQT0tpcz93yMPGJWw7TuHS06q5Yo4bIQACeRkAAsoKqFSyigb3qn0s_zgE",
        "CAACAgUAAxkBAAEQT0xpcz948D3tEwQ7LiRJrcRM9dxHOAACTBcAAuiaqVQENM6GYLRBfDgE",
        "CAACAgUAAxkBAAEQT05pcz94_yo-pxTTMrdRKykqgbuH-AACTBcAAmREqFT8HkngFhkhxjgE",
        "CAACAgUAAxkBAAEQT09pcz95XZlIT0eGLYAenXxnla9MHwACFBQAAlyJqVQ3XE8tNzPpHzgE",
        "CAACAgUAAxkBAAEQT1Bpcz95PA9gYdsd0MhbVYaJ-ZFoMAAC5xcAAkA_qFTbijW8ShcgjDgE",
        "CAACAgUAAxkBAAEQT1Jpcz959UnfHm81_CH1HbBBJ95AFAACJRMAAqSIqFTl_pga7Kor6TgE",
        "CAACAgUAAxkBAAEQT1Npcz95PVsNzLbtPElnMPJB2Va97wAC1BYAAov1sVRtAAFZPASO5PY4BA",
        "CAACAgUAAxkBAAEQT1Vpcz96O_xO-VVsBd_XV6-pQXm3jQACGxoAApRZsVSNqC8hjf3-eDgE",
        "CAACAgUAAxkBAAEQT1Zpcz960TnGJKxgi10057NTg5HWuQACHxcAAnQ1qFTPcjLI8e9OczgE",
        "CAACAgUAAxkBAAEQT1hpcz97G85sX5ySXv1M_jECy_EtqQAC8BUAApODqFT3JZAuNhbmNTgE",
        "CAACAgUAAxkBAAEQT1lpcz97O2iT3Yl9W0KFNCTH7qiXQgACgBYAAuEXqVRZv2dpS4EHVzgE",
        "CAACAgUAAxkBAAEQT1tpcz98Im8mVQiU8h6VpXVR3IRsEwACPxEAAhyVsFR8ZRkxStM63zgE",
        "CAACAgUAAxkBAAEQT1xpcz98euWdB8zjPgek_0BAMb1PvQACmhYAAhAisVScH1YlQyt9yjgE",
        "CAACAgUAAxkBAAEQT15pcz998PBuw95G3z0F9cGxuhUVNwACwTMAAtAnqFSybAeoJwzLpjgE",
    ],
}

# ========= Super Win definition =========
# Super Win = streak_win >= 2 (loss ছাড়া পরপর win)
SUPER_WIN_MIN_STREAK = 2
SUPER_WIN_POOL = STICKERS["WIN_RANDOM"] + STICKERS["EXTRA_RANDOM"]

# ================= FLASK KEEP-ALIVE =================
app = Flask("")

@app.route("/")
def home():
    return f"{BRAND_NAME} • RUNNING"

@app.route("/health")
def health():
    return "ok"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def keep_alive():
    Thread(target=run_http, daemon=True).start()

# ================= PASSWORD FROM GOOGLE SHEET =================
_password_cache = {"value": None, "ts": 0.0}

def _sheet_csv_url() -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

def _fetch_password_sync(timeout: float = 6.0):
    try:
        r = requests.get(_sheet_csv_url(), headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        if r.status_code != 200:
            return None
        lines = (r.text or "").splitlines()
        if not lines:
            return None
        a1 = lines[0].split(",")[0].strip().strip('"').strip("'")
        return a1 if a1 else None
    except:
        return None

async def get_password(force_refresh: bool = False):
    now = time.time()
    if (not force_refresh) and _password_cache["value"] and (now - _password_cache["ts"] < PASSWORD_CACHE_SECONDS):
        return _password_cache["value"]
    pw = await asyncio.to_thread(_fetch_password_sync)
    if pw:
        _password_cache["value"] = pw
        _password_cache["ts"] = now
        return pw
    return None

# ================= PREDICTION ENGINE (YOUR DATA-MINING LOGIC) =================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.raw_history = []
        self.last_prediction = None

    def update_history(self, issue_data):
        try:
            number = int(issue_data["number"])
            result_type = "BIG" if number >= 5 else "SMALL"
        except:
            return

        if (not self.raw_history) or (str(self.raw_history[0].get("issueNumber")) != str(issue_data.get("issueNumber"))):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:500]
            self.raw_history = self.raw_history[:500]

    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 15:
            pred = random.choice(["BIG", "SMALL"])
            self.last_prediction = pred
            return pred

        current_pattern = self.history[:3]
        big_chance = 0
        small_chance = 0

        for i in range(1, len(self.history) - 3):
            past_sequence = self.history[i : i + 3]
            if past_sequence == current_pattern:
                next_result_in_past = self.history[i - 1]
                if next_result_in_past == "BIG":
                    big_chance += 1
                else:
                    small_chance += 1

        if big_chance > small_chance:
            prediction = "BIG"
        elif small_chance > big_chance:
            prediction = "SMALL"
        else:
            prediction = self.history[0]

        if current_streak_loss >= 2:
            prediction = "SMALL" if prediction == "BIG" else "BIG"

        self.last_prediction = prediction
        return prediction

    def confidence(self):
        base = random.randint(86, 92)
        try:
            if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
                base = random.randint(92, 97)
        except:
            pass
        return base

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.session_id = 0
        self.game_mode = "1M"  # "1M" or "30S"
        self.engine = PredictionEngine()

        self.active_bet = None  # {"period":..., "pick":..., "check_mid":..., "check_task":...}
        self.last_period_processed = None

        self.stats = {
            "wins": 0,
            "losses": 0,
            "streak_win": 0,
            "streak_loss": 0,
            "max_streak_win": 0,
            "max_streak_loss": 0,
        }

        self.loss_message_ids = []

state = BotState()
AUTHORIZED_USERS = set()

def lock_all_users():
    AUTHORIZED_USERS.clear()

def mode_label():
    return "1 MIN" if state.game_mode == "1M" else "30 SEC"

def step_text(step: int) -> str:
    return f"{step} Step Loss" if step > 0 else "0 Step"

def pick_badge(pred: str) -> str:
    return "🟢🟢🟢 <b>BIG</b> 🟢🟢🟢" if pred == "BIG" else "🔴🔴🔴 <b>SMALL</b> 🔴🔴🔴"

def fmt_signal(next_issue: str, pred: str, conf: int):
    return (
        f"⚡ <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Market:</b> <code>{mode_label()}</code>\n"
        f"🧾 <b>Next Period:</b> <code>{next_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_badge(pred)}\n"
        f"📈 <b>Confidence:</b> <b>{conf}%</b>\n"
        f"🧠 <b>Tracker:</b> <b>{step_text(state.stats['streak_loss'])}</b> / {MAX_LOSS_STOP}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <code>{now_hms()}</code>\n"
        f"🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>"
    )

def fmt_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool):
    title = "✅ <b>WIN CONFIRMED</b>" if is_win else "❌ <b>LOSS CONFIRMED</b>"
    res_emoji = "🟢" if res_type == "BIG" else "🔴"

    if is_win:
        extra = f"🔥 <b>Win Streak:</b> {state.stats['streak_win']} (Max {state.stats['max_streak_win']})"
    else:
        extra = f"⚠️ <b>{step_text(state.stats['streak_loss'])}</b> / {MAX_LOSS_STOP} (Max {state.stats['max_streak_loss']})"

    return (
        f"{title}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Market:</b> <code>{mode_label()}</code>\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num}</b> (<b>{res_type}</b>)\n"
        f"🎯 <b>Your Pick:</b> <b>{pick}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{extra}\n"
        f"📊 <b>W</b>:{state.stats['wins']}  |  <b>L</b>:{state.stats['losses']}  |  <code>{now_hms()}</code>"
    )

def fmt_summary():
    w = state.stats["wins"]
    l = state.stats["losses"]
    total = w + l
    win_rate = round((w / total) * 100, 2) if total else 0.0

    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Market:</b> <code>{mode_label()}</code>\n"
        f"📦 <b>Total Rounds:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{w}</b>\n"
        f"❌ <b>Loss:</b> <b>{l}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{win_rate}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.stats['max_streak_win']}</b>\n"
        f"🧊 <b>Max Loss Streak:</b> <b>{state.stats['max_streak_loss']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed At:</b> <code>{now_hms()}</code>\n"
        f"🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>"
    )

def fmt_consolation_stop():
    return (
        f"🧊 <b>SAFE GUARD ACTIVATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>{MAX_LOSS_STOP} Step Loss</b> reached.\n"
        f"🛡️ Prediction is now <b>OFF</b> for safety.\n"
        f"✅ Use /start to unlock again.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <a href='{CHANNEL_LINK}'><b>TAKE A BREAK</b></a>"
    )

# ================= API FETCH (requests + gateways) =================
def _fetch_one(url: str, headers: dict, timeout: float):
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        return None
    data = r.json()
    if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
        return data["data"]["list"][0]
    return None

async def fetch_latest_issue(mode: str):
    base_url = API_1M if mode == "1M" else API_30S
    ts = int(time.time() * 1000)

    gateways = [
        f"{base_url}?t={ts}",
        f"https://corsproxy.io/?{base_url}?t={ts}",
        f"https://api.allorigins.win/raw?url={base_url}?t={ts}",
        f"https://thingproxy.freeboard.io/fetch/{base_url}?t={ts}",
        f"https://api.codetabs.com/v1/proxy?quest={base_url}?t={ts}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 Chrome/{random.randint(110, 123)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    timeout = 5 if mode == "30S" else 8

    for url in gateways:
        try:
            res = await asyncio.to_thread(_fetch_one, url, headers, timeout)
            if res:
                return res
        except:
            continue
    return None

# ================= SAFE DELETE =================
async def safe_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def delete_all_loss_messages(context: ContextTypes.DEFAULT_TYPE):
    if not state.loss_message_ids:
        return
    ids = state.loss_message_ids[:]
    state.loss_message_ids.clear()
    for mid in ids:
        await safe_delete(context, TARGET_CHANNEL, mid)

# ================= CHECKING (ANIM + AUTO DELETE) =================
async def start_checking_animation(context: ContextTypes.DEFAULT_TYPE, chat_id: int, period: str):
    title = "⏳ <b>RESULT CHECKER</b>"
    box = (
        f"{title}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 <b>Mode:</b> <code>{mode_label()}</code>\n"
        f"🧾 <b>Tracking Period:</b> <code>{period}</code>\n"
        f"📡 <b>Status:</b> <code>syncing…</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <code>{now_hms()}</code>"
    )
    msg = await context.bot.send_message(chat_id, box, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    async def _animate():
        frames = ["syncing.", "syncing..", "syncing...", "syncing….", "syncing....."]
        i = 0
        while True:
            try:
                box2 = (
                    f"{title}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎮 <b>Mode:</b> <code>{mode_label()}</code>\n"
                    f"🧾 <b>Tracking Period:</b> <code>{period}</code>\n"
                    f"📡 <b>Status:</b> <code>{frames[i % len(frames)]}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏱ <code>{now_hms()}</code>"
                )
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=msg.message_id, text=box2,
                    parse_mode=ParseMode.HTML, disable_web_page_preview=True
                )
            except:
                pass
            i += 1
            await asyncio.sleep(1.0)

    task = asyncio.create_task(_animate())
    return msg.message_id, task

# ================= STICKER SELECTORS =================
def pred_sticker(pred: str) -> str:
    # ✅ Hard fixed mapping
    if state.game_mode == "30S":
        return STICKERS["PRED_30S"]["BIG"] if pred == "BIG" else STICKERS["PRED_30S"]["SMALL"]
    return STICKERS["PRED_1M"]["BIG"] if pred == "BIG" else STICKERS["PRED_1M"]["SMALL"]

def maybe_extra():
    return random.choice(STICKERS["EXTRA_RANDOM"]) if random.random() < 0.08 else None

async def send_session_start_pack(context: ContextTypes.DEFAULT_TYPE):
    # ✅ Always send start sticker pack on every connect
    try:
        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS["START_BASE"])
    except:
        pass

    # mode-select sticker required
    try:
        key = "30S" if state.game_mode == "30S" else "1M"
        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS["MODE_SELECT"][key])
    except:
        pass

    # sometimes extra start sticker
    if STICKERS["START_EXTRA"] and random.random() < 0.60:
        try:
            await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS["START_EXTRA"]))
        except:
            pass

async def send_win_pack(context: ContextTypes.DEFAULT_TYPE, result_type: str):
    # 1) Win Count serial sticker
    try:
        idx = state.stats["wins"] - 1
        if 0 <= idx < len(STICKERS["WIN_COUNT"]):
            await context.bot.send_sticker(TARGET_CHANNEL, STICKERS["WIN_COUNT"][idx])
    except:
        pass

    # 2) Basic win stickers
    pool = [STICKERS["WIN_ANY"], STICKERS["WIN_BIG"] if result_type == "BIG" else STICKERS["WIN_SMALL"]]
    if STICKERS["WIN_RANDOM"]:
        pool.append(random.choice(STICKERS["WIN_RANDOM"]))

    # 3) Super win extra if streak without loss
    if state.stats["streak_win"] >= SUPER_WIN_MIN_STREAK and SUPER_WIN_POOL:
        pool.append(random.choice(SUPER_WIN_POOL))

    # 4) green sometimes
    if random.random() < 0.20:
        pool.append(STICKERS["COLOR"]["GREEN"])

    random.shuffle(pool)
    # avoid spam
    for st in pool[:2]:
        try:
            await context.bot.send_sticker(TARGET_CHANNEL, st)
        except:
            pass

# ================= SUMMARY SENDER (RETRY) =================
async def send_summary_guaranteed(context: ContextTypes.DEFAULT_TYPE, text: str, retries: int = 5):
    last_err = None
    for _ in range(retries):
        try:
            await context.bot.send_message(
                TARGET_CHANNEL, text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            last_err = e
            await asyncio.sleep(1.2)
    logging.error("Summary send failed: %s", last_err)
    return False

# ================= GAME ENGINE =================
async def game_loop(context: ContextTypes.DEFAULT_TYPE, sid: int):
    fail_count = 0

    while state.is_running and state.session_id == sid:
        try:
            latest = await fetch_latest_issue(state.game_mode)
            if not latest:
                fail_count += 1
                await asyncio.sleep(min(2 + fail_count, 12))
                continue

            fail_count = 0

            latest_issue = str(latest["issueNumber"])
            latest_num = str(latest["number"])
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # ---------- RESULT CHECK ----------
            if state.active_bet and state.active_bet.get("period") == latest_issue:
                if state.last_period_processed == latest_issue:
                    await asyncio.sleep(1)
                    continue

                # stop checking animation + delete checking message
                try:
                    if state.active_bet.get("check_task"):
                        state.active_bet["check_task"].cancel()
                except:
                    pass
                if state.active_bet.get("check_mid"):
                    await safe_delete(context, TARGET_CHANNEL, state.active_bet["check_mid"])

                pick = state.active_bet["pick"]
                is_win = (pick == latest_type)

                state.engine.update_history(latest)

                if is_win:
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                    state.stats["max_streak_win"] = max(state.stats["max_streak_win"], state.stats["streak_win"])
                    await send_win_pack(context, latest_type)
                else:
                    state.stats["losses"] += 1
                    state.stats["streak_win"] = 0
                    state.stats["streak_loss"] += 1
                    state.stats["max_streak_loss"] = max(state.stats["max_streak_loss"], state.stats["streak_loss"])

                    # loss stickers (track to delete on stop)
                    try:
                        ms = await context.bot.send_sticker(TARGET_CHANNEL, STICKERS["LOSS_ANY"])
                        state.loss_message_ids.append(ms.message_id)
                    except:
                        pass
                    if random.random() < 0.18:
                        try:
                            ms2 = await context.bot.send_sticker(TARGET_CHANNEL, STICKERS["COLOR"]["RED"])
                            state.loss_message_ids.append(ms2.message_id)
                        except:
                            pass

                # result message (delete later if loss)
                try:
                    mr = await context.bot.send_message(
                        TARGET_CHANNEL,
                        fmt_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    if not is_win:
                        state.loss_message_ids.append(mr.message_id)
                except:
                    pass

                state.active_bet = None
                state.last_period_processed = latest_issue

                # auto stop on MAX_LOSS_STOP
                if state.stats["streak_loss"] >= MAX_LOSS_STOP:
                    state.is_running = False
                    lock_all_users()

                    await delete_all_loss_messages(context)
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        fmt_consolation_stop(),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    # summary must go
                    await send_summary_guaranteed(context, fmt_summary())
                    return

            # ---------- SEND NEW SIGNAL ----------
            if (not state.active_bet) and (state.last_period_processed != next_issue):
                state.engine.update_history(latest)

                pred = state.engine.get_pattern_signal(state.stats["streak_loss"])
                conf = state.engine.confidence()

                state.active_bet = {"period": next_issue, "pick": pred}

                # prediction sticker
                try:
                    await context.bot.send_sticker(TARGET_CHANNEL, pred_sticker(pred))
                except:
                    pass

                ex = maybe_extra()
                if ex:
                    try:
                        await context.bot.send_sticker(TARGET_CHANNEL, ex)
                    except:
                        pass

                # signal message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        fmt_signal(next_issue, pred, conf),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except:
                    pass

                # checking animation
                try:
                    check_mid, check_task = await start_checking_animation(context, TARGET_CHANNEL, next_issue)
                    state.active_bet["check_mid"] = check_mid
                    state.active_bet["check_task"] = check_task
                except:
                    pass

            await asyncio.sleep(1 if state.game_mode == "30S" else 2)

        except Exception:
            await asyncio.sleep(2)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pw = await get_password(force_refresh=True)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).")
        return
    await update.message.reply_text("🔒 Send Password:")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    uid = update.effective_user.id

    pw = await get_password(force_refresh=False)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).")
        return

    # AUTH
    if uid not in AUTHORIZED_USERS:
        if msg == pw:
            AUTHORIZED_USERS.add(uid)
            await update.message.reply_text(
                "✅ Access Granted\n\nSend:\n/connect 1m\n/connect 30s\n/stop",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text("❌ Wrong password")
        return

    # STOP
    if msg.lower() in ["/stop", "stop", "off", "/off"]:
        # stop session
        state.session_id += 1
        state.is_running = False

        # cancel checking + delete checking msg
        if state.active_bet:
            try:
                if state.active_bet.get("check_task"):
                    state.active_bet["check_task"].cancel()
            except:
                pass
            if state.active_bet.get("check_mid"):
                await safe_delete(context, TARGET_CHANNEL, state.active_bet["check_mid"])
        state.active_bet = None

        # delete loss clutter first
        await delete_all_loss_messages(context)

        # summary must go (retry)
        ok = await send_summary_guaranteed(context, fmt_summary())
        if not ok:
            # fallback: also DM user (so you know it failed)
            await update.message.reply_text("⚠️ Summary failed to send in group. Check bot admin permissions.")

        lock_all_users()
        await update.message.reply_text("🛑 Stopped. Use /start again to unlock.")
        return

    # CONNECT
    if msg.lower() in ["/connect 1m", "connect 1m", "1m"]:
        state.game_mode = "1M"
    elif msg.lower() in ["/connect 30s", "connect 30s", "30s"]:
        state.game_mode = "30S"
    else:
        await update.message.reply_text("Commands:\n/connect 1m\n/connect 30s\n/stop")
        return

    # force password check each start (as you requested)
    pw2 = await get_password(force_refresh=True)
    if not pw2:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).")
        return

    # reset session
    state.session_id += 1
    sid = state.session_id
    state.is_running = True
    state.engine = PredictionEngine()
    state.active_bet = None
    state.last_period_processed = None
    state.loss_message_ids = []
    state.stats = {
        "wins": 0,
        "losses": 0,
        "streak_win": 0,
        "streak_loss": 0,
        "max_streak_win": 0,
        "max_streak_loss": 0,
    }

    await update.message.reply_text(f"✅ Connected: {mode_label()} | Engine LIVE")

    # ✅ Always send session start sticker pack every time
    await send_session_start_pack(context)

    context.application.create_task(game_loop(context, sid))

# ================= MAIN =================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    if not BOT_TOKEN or "PASTE_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing! Replace PASTE_TOKEN_HERE in main.py")

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_text))

    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
