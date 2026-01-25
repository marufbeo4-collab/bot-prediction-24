import asyncio
import logging
import random
import time
import os
from threading import Thread
from datetime import datetime

import requests
import pytz
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"  # ✅ শুধু টোকেন বসাবি
OWNER_USER_ID = 5815609259       # ✅ এখানে তোর telegram numeric user id বসাবি (must)

BRAND_NAME = "⚡⚡ 𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# ✅ 3 Targets (Default ON: main)
TARGETS = {
    "MAIN":   {"chat_id": -1003293007059, "label": "Main Group",   "enabled": True},
    "VIP":    {"chat_id": -1002892329434, "label": "VIP",          "enabled": False},
    "PUBLIC": {"chat_id": -1002629495753, "label": "Public",       "enabled": False},
}

MAX_LOSS_STOP = 8

API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# Password from Google Sheet A1
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_GID = "0"
PASSWORD_CACHE_SECONDS = 20

# Security lock on wrong attempts
MAX_BAD_ATTEMPTS = 5
LOCK_SECONDS = 300  # 5 minutes

# Timezone BD
BD_TZ = pytz.timezone("Asia/Dhaka")


# ================= STICKERS =================
# ✅ 30S sticker swap fixed (BIG<->SMALL) as you asked earlier
PRED_STICKERS = {
    "1M": {
        "BIG":   "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
        "SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    },
    "30S": {
        "BIG":   "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
        "SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",
    }
}

WIN_BIG = "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE"
WIN_SMALL = "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE"
WIN_ANY = "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA"
LOSS_ANY = "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA"

SUPER_WIN_STREAK = {
    2:  "CAACAgUAAxkBAAEQTiBpcmUfm9aQmlIHtPKiG2nE2e6EeAACcRMAAiLWqFSpdxWmKJ1TXzgE",
    3:  "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE",
    4:  "CAACAgUAAxkBAAEQTiJpcmUgSydN-tKxoSVdFuAvCcJ3fQACvSEAApMRqFQoUYBnH5Pc7TgE",
    5:  "CAACAgUAAxkBAAEQTiNpcmUgu_dP3wKT2k94EJCiw3u52QACihoAArkfqFSlrldtXbLGGDgE",
    6:  "CAACAgUAAxkBAAEQTiRpcmUhQJUjd2ukdtfEtBjwtMH4MAACWRgAAsTFqVTato0SmSN-6jgE",
    7:  "CAACAgUAAxkBAAEQTiVpcmUhha9HAAF19fboYayfUrm3tdYAAioXAAIHgKhUD0QmGyF5Aug4BA",
    8:  "CAACAgUAAxkBAAEQTixpcmUmevnNEqUbr0qbbVgW4psMNQACMxUAAow-qFSnSz4Ik1ddNzgE",
    9:  "CAACAgUAAxkBAAEQTi1pcmUmpSxAHo2pvR-GjCPTmkLr0AACLh0AAhCRqFRH5-2YyZKq1jgE",
    10: "CAACAgUAAxkBAAEQTi5pcmUmjmjp7oXg4InxI1dGYruxDwACqBgAAh19qVT6X_-oEywCkzgE",
}

WIN_RANDOM_POOL = [
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
]

COLOR_STICKERS = {
    "RED":   "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
}

SEASON_START = {
    "30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
    "1M":  "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE"
}

# ✅ must sticker at start + end, not during loss
HYPE_STICKER = "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE"


# ================= FLASK KEEP ALIVE =================
app = Flask("")

@app.route("/")
def home():
    return "OK"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def keep_alive():
    Thread(target=run_http, daemon=True).start()


# ================= PASSWORD FROM SHEET =================
_password_cache = {"value": None, "ts": 0.0}
_security = {"bad": 0, "lock_until": 0.0}
AUTHORIZED = False  # require password each time start/stop

def sheet_csv_url():
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

def fetch_password_sync(timeout=6.0):
    try:
        r = requests.get(sheet_csv_url(), headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        if r.status_code != 200:
            return None
        lines = (r.text or "").splitlines()
        if not lines:
            return None
        return lines[0].split(",")[0].strip().strip('"').strip("'") or None
    except:
        return None

async def get_password(force=False):
    now = time.time()
    if (not force) and _password_cache["value"] and (now - _password_cache["ts"] < PASSWORD_CACHE_SECONDS):
        return _password_cache["value"]
    pw = await asyncio.to_thread(fetch_password_sync)
    if pw:
        _password_cache["value"] = pw
        _password_cache["ts"] = now
    return pw


# ================= HELPERS =================
def now_hms():
    return datetime.now(BD_TZ).strftime("%H:%M:%S")

def mode_label(mode):
    return "30 SEC" if mode == "30S" else "1 MIN"

def pick_badge(pred):
    return "🟢🟢 <b>BIG</b> 🟢🟢" if pred == "BIG" else "🔴🔴 <b>SMALL</b> 🔴🔴"

def step_text(step):
    return f"{step} Step Loss" if step > 0 else "0 Step"

def selected_chat_ids():
    return [v["chat_id"] for v in TARGETS.values() if v["enabled"]]

def target_status_text():
    lines = []
    for k, v in TARGETS.items():
        lines.append(f"{'✅' if v['enabled'] else '❌'} {k} — {v['label']} ({v['chat_id']})")
    return "\n".join(lines)

def targets_keyboard():
    def btn(key):
        return f"{'✅' if TARGETS[key]['enabled'] else '❌'} {key}"
    return ReplyKeyboardMarkup(
        [[btn("MAIN"), btn("VIP"), btn("PUBLIC")],
         ["⚡ Connect 1M", "⚡ Connect 30S"],
         ["🎨 Color: ON/OFF"],
         ["🛑 Stop & Summary"]],
        resize_keyboard=True
    )


# ================= MULTI-GATEWAY FETCH =================
def _fetch_one(url, headers, timeout):
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        return None
    data = r.json()
    if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
        return data["data"]["list"][0]
    return None

async def fetch_latest_issue(mode):
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
        "User-Agent": f"Mozilla/5.0 Chrome/{random.randint(110,123)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    timeout = 4 if mode == "30S" else 7

    for url in gateways:
        try:
            res = await asyncio.to_thread(_fetch_one, url, headers, timeout)
            if res:
                return res
        except:
            continue
    return None


# ================= FAST SENDER QUEUE =================
class TgSender:
    def __init__(self):
        self.q = asyncio.Queue()

    async def start(self):
        while True:
            coro = await self.q.get()
            try:
                await coro
            except:
                pass
            await asyncio.sleep(0.12)  # fast

    async def enqueue(self, coro):
        await self.q.put(coro)

sender = TgSender()


# ================= ENGINE (YOUR NEW LOGIC) =================
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
            self.history = self.history[:1200]
            self.raw_history = self.raw_history[:1200]

    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 15:
            pred = random.choice(["BIG", "SMALL"])
            self.last_prediction = pred
            return pred

        h = self.history
        votes = []

        # Trend majority (12)
        last_12 = h[:12]
        if last_12.count("BIG") > last_12.count("SMALL"):
            votes.append("BIG")
        else:
            votes.append("SMALL")

        # Dragon follower
        votes.append(h[0])

        # Anti-zigzag (reverse)
        votes.append("SMALL" if h[0] == "BIG" else "BIG")

        # Streak hunter
        if h[0] == h[1] == h[2]:
            votes.append(h[0])

        # AABB
        if h[0] == h[1] and h[2] == h[3] and h[1] != h[2]:
            votes.append("SMALL" if h[0] == "BIG" else "BIG")

        # Math / raw_history
        try:
            r_num = int(self.raw_history[0].get("number", 0))
            p_digit = int(str(self.raw_history[0].get("issueNumber", 0))[-1])
            prev_num = int(self.raw_history[1].get("number", 0))

            votes.append("SMALL" if (p_digit + r_num) % 2 == 0 else "BIG")
            votes.append("SMALL" if (r_num + prev_num) % 2 == 0 else "BIG")
            votes.append("BIG" if r_num >= 5 else "SMALL")
            votes.append("SMALL" if ((r_num * 3) + p_digit) % 2 == 0 else "BIG")
        except:
            pass

        # History matching last3
        current_pat = h[:3]
        match_big, match_small = 0, 0
        for i in range(1, len(h) - 3):
            if h[i:i+3] == current_pat:
                if h[i-1] == "BIG":
                    match_big += 1
                else:
                    match_small += 1
        if match_big > match_small:
            votes.append("BIG")
        elif match_small > match_big:
            votes.append("SMALL")

        # Psychological reverse trap (dragon again)
        votes.append(h[0])

        # Loss recovery heavy votes
        if current_streak_loss >= 2 and self.last_prediction in ("BIG", "SMALL"):
            rec_vote = "SMALL" if self.last_prediction == "BIG" else "BIG"
            votes.extend([rec_vote, rec_vote, rec_vote])

        big_votes = votes.count("BIG")
        small_votes = votes.count("SMALL")

        if big_votes > small_votes:
            prediction = "BIG"
        elif small_votes > big_votes:
            prediction = "SMALL"
        else:
            prediction = h[0]

        if current_streak_loss >= 4:
            prediction = h[0]

        self.last_prediction = prediction
        return prediction

    def calculate_confidence(self):
        # simple stable confidence
        base = random.randint(88, 95)
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
        self.game_mode = "30S"
        self.engine = PredictionEngine()
        self.active_bet = None  # {"period": str, "pick": str, "check_ids": {chat_id: msg_id}}
        self.last_seen_issue = None
        self.last_period_processed = None
        self.color_enabled = False
        self.stop_requested = False
        self.loss_message_ids_by_chat = {}  # {chat_id: [msg_ids]}
        self.stats = {
            "wins": 0, "losses": 0,
            "streak_win": 0, "streak_loss": 0,
            "max_streak_win": 0, "max_streak_loss": 0
        }

state = BotState()


def fmt_signal(next_issue, pred, conf, step_loss, mode):
    join = f"\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN / REJOIN</b></a>" if CHANNEL_LINK else ""
    return (
        f"⚡ <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(mode)}</b>\n"
        f"🧾 <b>Period</b>: <code>{next_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_badge(pred)}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{step_text(step_loss)}</b> / {MAX_LOSS_STOP}\n"
        f"⏱ <b>BD Time</b> ➜ <code>{now_hms()}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{join}"
    )

def fmt_checking(wait_issue, mode):
    return (
        f"🛰 <b>LIVE CHECK</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(mode)}</b>\n"
        f"🧾 <b>Waiting</b>: <code>{wait_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <code>syncing…</code>"
    )

def fmt_result(issue, res_num, res_type, pick, is_win, step_loss, w, l, max_ls, max_ws, ws, mode):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    header = "✅ <b>WIN CONFIRMED</b>" if is_win else "❌ <b>LOSS CONFIRMED</b>"
    extra = (f"🔥 <b>Win Streak</b>: {ws} (Max {max_ws})"
             if is_win else
             f"⚠️ <b>{step_text(step_loss)}</b> / {MAX_LOSS_STOP} (Max {max_ls})")
    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(mode)}</b>\n"
        f"🧾 <b>Period</b>: <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 <b>Result</b>: {res_emoji} <b>{res_num}</b> (<b>{res_type}</b>)\n"
        f"🎯 <b>Your Pick</b>: {pick_badge(pick)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{extra}\n"
        f"📊 <b>W</b>:{w} | <b>L</b>:{l} | <code>{now_hms()}</code>"
    )

def fmt_summary():
    w = state.stats["wins"]
    l = state.stats["losses"]
    total = w + l
    win_rate = round((w / total) * 100, 2) if total else 0.0
    join = f"\n🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>" if CHANNEL_LINK else ""
    return (
        f"🛑 <b>SESSION SUMMARY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(state.game_mode)}</b>\n"
        f"📦 <b>Total</b>: <b>{total}</b>\n"
        f"✅ <b>Win</b>: <b>{w}</b>\n"
        f"❌ <b>Loss</b>: <b>{l}</b>\n"
        f"🎯 <b>Win Rate</b>: <b>{win_rate}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak</b>: <b>{state.stats['max_streak_win']}</b>\n"
        f"🧊 <b>Max Loss Streak</b>: <b>{state.stats['max_streak_loss']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed</b>: <code>{now_hms()}</code>"
        f"{join}"
    )

def fmt_consolation_stop():
    return (
        f"🧊 <b>SAFE GUARD ACTIVATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>{MAX_LOSS_STOP} Step Loss</b> reached.\n"
        f"🛡️ Prediction is now <b>OFF</b> for safety.\n"
        f"✅ Use /start and password again.\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


# ================= MULTI-CHAT SEND HELPERS =================
async def send_to_all(context, method_name, *args, **kwargs):
    for chat_id in selected_chat_ids():
        method = getattr(context.bot, method_name)
        await sender.enqueue(method(chat_id, *args, **kwargs))

async def send_sticker_all(context, sticker_id):
    await send_to_all(context, "send_sticker", sticker_id)

async def send_message_all(context, text, **kwargs):
    # returns nothing (since multi chat)
    await send_to_all(context, "send_message", text, **kwargs)


async def delete_loss_clutter(context):
    for chat_id, ids in list(state.loss_message_ids_by_chat.items()):
        for mid in ids:
            try:
                await sender.enqueue(context.bot.delete_message(chat_id, mid))
            except:
                pass
    state.loss_message_ids_by_chat = {}


# ================= ENGINE LOOP =================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE):
    fail_count = 0

    while state.is_running:
        try:
            latest = await fetch_latest_issue(state.game_mode)
            if not latest:
                fail_count += 1
                await asyncio.sleep(min(1 + fail_count, 6))
                continue
            fail_count = 0

            latest_issue = str(latest["issueNumber"])
            latest_num = str(latest["number"])
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # RESULT (only if predicted this period)
            if state.active_bet and state.active_bet["period"] == latest_issue:
                pick = state.active_bet["pick"]
                check_ids = state.active_bet.get("check_ids", {})

                # delete checking across chats
                for chat_id, mid in check_ids.items():
                    try:
                        await sender.enqueue(context.bot.delete_message(chat_id, mid))
                    except:
                        pass

                is_win = (pick == latest_type)
                state.engine.update_history(latest)

                if is_win:
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                    state.stats["max_streak_win"] = max(state.stats["max_streak_win"], state.stats["streak_win"])

                    # hype sticker (not during loss)
                    await send_sticker_all(context, HYPE_STICKER)

                    # super streak sticker 2-10
                    if state.stats["streak_win"] in SUPER_WIN_STREAK:
                        await send_sticker_all(context, SUPER_WIN_STREAK[state.stats["streak_win"]])
                    else:
                        pool = [WIN_ANY, WIN_BIG if latest_type == "BIG" else WIN_SMALL]
                        if state.stats["streak_win"] >= 2:
                            pool.append(random.choice(WIN_RANDOM_POOL))
                        await send_sticker_all(context, random.choice(pool))

                else:
                    state.stats["losses"] += 1
                    state.stats["streak_win"] = 0
                    state.stats["streak_loss"] += 1
                    state.stats["max_streak_loss"] = max(state.stats["max_streak_loss"], state.stats["streak_loss"])

                    # loss sticker + remember to delete on stop
                    for chat_id in selected_chat_ids():
                        async def _loss_send(cid=chat_id):
                            m = await context.bot.send_sticker(cid, LOSS_ANY)
                            state.loss_message_ids_by_chat.setdefault(cid, []).append(m.message_id)
                        await sender.enqueue(_loss_send())

                # result message
                txt = fmt_result(
                    latest_issue, latest_num, latest_type, pick, is_win,
                    state.stats["streak_loss"],
                    state.stats["wins"], state.stats["losses"],
                    state.stats["max_streak_loss"], state.stats["max_streak_win"],
                    state.stats["streak_win"],
                    state.game_mode
                )
                if not is_win:
                    for chat_id in selected_chat_ids():
                        async def _loss_msg(cid=chat_id):
                            m = await context.bot.send_message(
                                cid, txt, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                            )
                            state.loss_message_ids_by_chat.setdefault(cid, []).append(m.message_id)
                        await sender.enqueue(_loss_msg())
                else:
                    await send_message_all(
                        context, txt,
                        parse_mode=ParseMode.HTML, disable_web_page_preview=True
                    )

                state.active_bet = None
                state.last_period_processed = latest_issue

                # stop-after-recovery
                if state.stop_requested and state.stats["streak_loss"] == 0:
                    state.is_running = False
                    state.stop_requested = False
                    await delete_loss_clutter(context)
                    await send_message_all(context, fmt_summary(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                    return

                # auto stop on max loss
                if state.stats["streak_loss"] >= MAX_LOSS_STOP:
                    state.is_running = False
                    state.stop_requested = False
                    await delete_loss_clutter(context)
                    await send_message_all(context, fmt_consolation_stop(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                    await send_message_all(context, fmt_summary(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                    return

            # SIGNAL (only when no active bet)
            if state.active_bet is None and state.last_period_processed != next_issue:
                state.engine.update_history(latest)
                pred = state.engine.get_pattern_signal(state.stats["streak_loss"])
                conf = state.engine.calculate_confidence()

                state.active_bet = {"period": next_issue, "pick": pred, "check_ids": {}}

                # start hype only if not in loss
                if state.stats["streak_loss"] == 0:
                    await send_sticker_all(context, HYPE_STICKER)

                await send_sticker_all(context, PRED_STICKERS[state.game_mode][pred])

                # optional color
                if state.color_enabled:
                    await send_sticker_all(context, COLOR_STICKERS["GREEN" if pred == "BIG" else "RED"])

                await send_message_all(
                    context,
                    fmt_signal(next_issue, pred, conf, state.stats["streak_loss"], state.game_mode),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

                # checking message per chat
                for chat_id in selected_chat_ids():
                    async def _send_check(cid=chat_id):
                        m = await context.bot.send_message(
                            cid, fmt_checking(next_issue, state.game_mode),
                            parse_mode=ParseMode.HTML, disable_web_page_preview=True
                        )
                        if state.active_bet and state.active_bet.get("period") == next_issue:
                            state.active_bet["check_ids"][cid] = m.message_id
                    await sender.enqueue(_send_check())

            await asyncio.sleep(0.45 if state.game_mode == "30S" else 0.9)

        except Exception:
            await asyncio.sleep(1.0)


# ================= SECURITY / MENU HANDLERS =================
def ensure_private(update: Update):
    return update.effective_chat and update.effective_chat.type == "private"

def is_owner(update: Update):
    return update.effective_user and update.effective_user.id == OWNER_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTHORIZED

    if not ensure_private(update):
        return  # only DM

    if not is_owner(update):
        await update.message.reply_text("⛔ Access denied.", parse_mode=ParseMode.HTML)
        return

    now = time.time()
    if _security["lock_until"] > now:
        left = int(_security["lock_until"] - now)
        await update.message.reply_text(f"🔒 Locked. Try after {left}s.", parse_mode=ParseMode.HTML)
        return

    AUTHORIZED = False
    await update.message.reply_text(
        "🔐 <b>LOCKED</b>\nSend Sheet Password:",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove()
    )

async def show_menu(update: Update):
    await update.message.reply_text(
        f"✅ <b>Unlocked</b>\n\n📡 <b>Targets</b>:\n{target_status_text()}\n\nSelect what you want:",
        parse_mode=ParseMode.HTML,
        reply_markup=targets_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTHORIZED

    if not ensure_private(update):
        return

    if not is_owner(update):
        await update.message.reply_text("⛔ Access denied.", parse_mode=ParseMode.HTML)
        return

    msg = (update.message.text or "").strip()

    # if not authorized -> check password
    if not AUTHORIZED:
        now = time.time()
        if _security["lock_until"] > now:
            left = int(_security["lock_until"] - now)
            await update.message.reply_text(f"🔒 Locked. Try after {left}s.", parse_mode=ParseMode.HTML)
            return

        pw = await get_password(force=True)
        if not pw:
            await update.message.reply_text("⚠️ Sheet password system offline.", parse_mode=ParseMode.HTML)
            return

        if msg == pw:
            AUTHORIZED = True
            _security["bad"] = 0
            await show_menu(update)
            return
        else:
            _security["bad"] += 1
            if _security["bad"] >= MAX_BAD_ATTEMPTS:
                _security["lock_until"] = time.time() + LOCK_SECONDS
                _security["bad"] = 0
                await update.message.reply_text("🚫 Too many attempts. Locked for 5 minutes.", parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("❌ Wrong password.", parse_mode=ParseMode.HTML)
            return

    # Toggle targets
    if msg in ("✅ MAIN", "❌ MAIN", "✅ VIP", "❌ VIP", "✅ PUBLIC", "❌ PUBLIC"):
        key = msg.split()[-1]
        TARGETS[key]["enabled"] = not TARGETS[key]["enabled"]
        await show_menu(update)
        return

    # Color toggle
    if "Color" in msg:
        state.color_enabled = not state.color_enabled
        await update.message.reply_text(f"🎨 Color Signal: <b>{'ON' if state.color_enabled else 'OFF'}</b>", parse_mode=ParseMode.HTML)
        await show_menu(update)
        return

    # STOP
    if "Stop" in msg or msg == "/off":
        # require password again next time
        AUTHORIZED = False

        if state.is_running and state.stats["streak_loss"] > 0:
            state.stop_requested = True
            await update.message.reply_text(
                "⏳ Stop queued.\nLoss চলছে—Recovery (next WIN) হলে auto stop + summary হবে।",
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardRemove()
            )
            return

        state.is_running = False
        state.stop_requested = False

        # delete pending checking
        if state.active_bet:
            for chat_id, mid in (state.active_bet.get("check_ids") or {}).items():
                try:
                    await context.bot.delete_message(chat_id, mid)
                except:
                    pass
        state.active_bet = None

        await delete_loss_clutter(context)
        await send_message_all(context, fmt_summary(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        await update.message.reply_text("🛑 Stopped. Use /start আবার.", parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        return

    # CONNECT
    if "Connect" in msg:
        # require password again before connect (high security)
        AUTHORIZED = False

        mode = "1M" if "1M" in msg else "30S"
        state.game_mode = mode

        # reset
        state.is_running = True
        state.stop_requested = False
        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_seen_issue = None
        state.last_period_processed = None
        state.loss_message_ids_by_chat = {}

        state.stats = {
            "wins": 0, "losses": 0,
            "streak_win": 0, "streak_loss": 0,
            "max_streak_win": 0, "max_streak_loss": 0
        }

        # season start sticker to all
        await send_sticker_all(context, SEASON_START[mode])

        await update.message.reply_text(
            f"✅ Connected: <b>{mode_label(mode)}</b>\nNow running in selected targets.\n\n🔐 For next action use /start আবার.",
            parse_mode=ParseMode.HTML,
            reply_markup=ReplyKeyboardRemove()
        )

        context.application.create_task(engine_loop(context))
        return

    # fallback
    await show_menu(update)


# ================= MAIN =================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    if not BOT_TOKEN or "PASTE_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing! Replace PASTE_TOKEN_HERE in main.py")
    if not isinstance(OWNER_USER_ID, int) or OWNER_USER_ID <= 0:
        raise RuntimeError("OWNER_USER_ID missing! Set your Telegram numeric ID.")

    async def _bootstrap(app: Application):
        app.create_task(sender.start())

    app_telegram = Application.builder().token(BOT_TOKEN).post_init(_bootstrap).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    # ✅ drop pending updates reduces burst spam after downtime
    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
