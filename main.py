import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import Thread
from typing import Dict, List, Optional, Tuple

import requests
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# =========================
# CONFIG (ONLY TOKEN YOU SET)
# =========================
BOT_TOKEN = "8595453345:AAGojMk2ReHFGV9ihJq57JjzMsuW94Ussec"  # <-- ONLY THIS YOU CHANGE

BRAND_NAME = "⚡ DK MARUF OFFICIAL 24/7 SIGNAL"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# Targets (You gave)
TARGETS = {
    "MAIN_GROUP": -1003293007059,
    "VIP": -1002892329434,
    "PUBLIC": -1002629495753,
}

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# BD Time
BD_TZ = timezone(timedelta(hours=6))

# Password source A1 (PUBLIC VIEW required)
PASSWORD_SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
PASSWORD_SHEET_GID = "0"
PASSWORD_FALLBACK = "2222"

# Settings
MAX_RECOVERY_STEPS = 8
FAST_LOOP_30S = 0.85
FAST_LOOP_1M = 1.65
FETCH_TIMEOUT = 5.5
FETCH_RETRY_SLEEP = 0.55


# =========================
# STICKERS (YOUR LIST)
# =========================
STICKERS = {
    # Prediction (1M)
    "PRED_1M_BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",

    # Prediction (30S) — swapped as you requested
    "PRED_30S_BIG": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    "PRED_30S_SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",

    # Start stickers per mode
    "START_30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
    "START_1M": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",

    # Always give this at START/END (but NOT on loss)
    "START_END_ALWAYS": "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE",

    # Win stickers
    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",

    # Every win sticker (required)
    "WIN_ALWAYS": "CAACAgUAAxkBAAEQUTZpdFC4094KaOEdiE3njwhAGVCuBAAC4hoAAt0EqVQXmdKVLGbGmzgE",

    # Any win extra sticker
    "WIN_ANY": "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",

    # Loss sticker
    "LOSS": "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",

    # Random win pool
    "WIN_POOL": [
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

    # Super win streak 2..10 (required)
    "SUPER_WIN": {
        2: "CAACAgUAAxkBAAEQTiBpcmUfm9aQmlIHtPKiG2nE2e6EeAACcRMAAiLWqFSpdxWmKJ1TXzgE",
        3: "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE",
        4: "CAACAgUAAxkBAAEQTiJpcmUgSydN-tKxoSVdFuAvCcJ3fQACvSEAApMRqFQoUYBnH5Pc7TgE",
        5: "CAACAgUAAxkBAAEQTiNpcmUgu_dP3wKT2k94EJCiw3u52QACihoAArkfqFSlrldtXbLGGDgE",
        6: "CAACAgUAAxkBAAEQTiRpcmUhQJUjd2ukdtfEtBjwtMH4MAACWRgAAsTFqVTato0SmSN-6jgE",
        7: "CAACAgUAAxkBAAEQTiVpcmUhha9HAAF19fboYayfUrm3tdYAAioXAAIHgKhUD0QmGyF5Aug4BA",
        8: "CAACAgUAAxkBAAEQTixpcmUmevnNEqUbr0qbbVgW4psMNQACMxUAAow-qFSnSz4Ik1ddNzgE",
        9: "CAACAgUAAxkBAAEQTi1pcmUmpSxAHo2pvR-GjCPTmkLr0AACLh0AAhCRqFRH5-2YyZKq1jgE",
        10: "CAACAgUAAxkBAAEQTi5pcmUmjmjp7oXg4InxI1dGYruxDwACqBgAAh19qVT6X_-oEywCkzgE",
    },

    # Color stickers
    "COLOR_RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
}


# =========================
# FLASK KEEP ALIVE
# =========================
app = Flask("")

@app.route("/")
def home():
    return "ALIVE"

def run_http():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_http, daemon=True)
    t.start()


# =========================
# PASSWORD (A1 CSV EXPORT - STABLE)
# =========================
def fetch_password_a1() -> str:
    """
    Reads A1 via CSV export (stable).
    No prints/logs. Returns fallback if fails.
    """
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/{PASSWORD_SHEET_ID}/export"
            f"?format=csv&gid={PASSWORD_SHEET_GID}&range=A1"
        )
        r = requests.get(
            url,
            timeout=8,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        if r.status_code != 200:
            return PASSWORD_FALLBACK

        val = r.text.strip().strip('"').strip()
        return val if val else PASSWORD_FALLBACK
    except Exception:
        return PASSWORD_FALLBACK

async def get_live_password() -> str:
    return await asyncio.to_thread(fetch_password_a1)


# =========================
# PREDICTION ENGINE (YOUR LOGIC)
# =========================
class PredictionEngine:
    def __init__(self):
        self.history: List[str] = []
        self.raw_history: List[dict] = []
        self.last_prediction: Optional[str] = None

    def update_history(self, issue_data: dict):
        try:
            number = int(issue_data["number"])
            result_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        if (not self.raw_history) or (self.raw_history[0].get("issueNumber") != issue_data.get("issueNumber")):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:120]
            self.raw_history = self.raw_history[:120]

    def get_pattern_signal(self, current_streak_loss: int):
        if len(self.history) < 15:
            return random.choice(["BIG", "SMALL"])

        h = self.history
        votes = []

        last_12 = h[:12]
        votes.append("BIG" if last_12.count("BIG") > last_12.count("SMALL") else "SMALL")
        votes.append(h[0])  # dragon
        votes.append("SMALL" if h[0] == "BIG" else "BIG")  # reverse
        if h[0] == h[1] == h[2]:
            votes.append(h[0])
        if h[0] == h[1] and h[2] == h[3] and h[1] != h[2]:
            votes.append("SMALL" if h[0] == "BIG" else "BIG")

        try:
            r_num = int(self.raw_history[0].get("number", 0))
            p_digit = int(str(self.raw_history[0].get("issueNumber", 0))[-1])
            prev_num = int(self.raw_history[1].get("number", 0))

            votes.append("SMALL" if (p_digit + r_num) % 2 == 0 else "BIG")
            votes.append("SMALL" if (r_num + prev_num) % 2 == 0 else "BIG")
            votes.append("BIG" if r_num >= 5 else "SMALL")
            votes.append("SMALL" if ((r_num * 3) + p_digit) % 2 == 0 else "BIG")
        except Exception:
            pass

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

        votes.append(h[0])  # psych

        if current_streak_loss >= 2 and self.last_prediction:
            rec_vote = "SMALL" if self.last_prediction == "BIG" else "BIG"
            votes += [rec_vote, rec_vote, rec_vote]

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

    def calc_confidence(self, streak_loss: int) -> int:
        base = random.randint(86, 93)
        if streak_loss >= 2:
            base = max(82, base - 2)
        if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
            base = min(96, base + 2)
        return base


# =========================
# BOT STATE
# =========================
def now_bd_str() -> str:
    return datetime.now(BD_TZ).strftime("%H:%M:%S")

def mode_label(mode: str) -> str:
    return "30 SEC" if mode == "30S" else "1 MIN"

@dataclass
class ActiveBet:
    predicted_issue: str
    pick: str
    checking_msg_ids: Dict[int, int] = field(default_factory=dict)  # per chat
    # loss-related messages to delete on stop
    loss_related_ids: Dict[int, List[int]] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    mode: str = "30S"
    session_id: int = 0
    engine: PredictionEngine = field(default_factory=PredictionEngine)
    active: Optional[ActiveBet] = None
    last_result_issue: Optional[str] = None
    last_signal_issue: Optional[str] = None

    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0
    max_win_streak: int = 0
    max_loss_streak: int = 0

    unlocked: bool = False
    expected_password: str = PASSWORD_FALLBACK

    selected_targets: List[int] = field(default_factory=lambda: [TARGETS["MAIN_GROUP"]])

    color_mode: bool = False
    graceful_stop_requested: bool = False

    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

state = BotState()


# =========================
# FETCH (Multi-Gateway, requests)
# =========================
def _fetch_latest_issue_sync(mode: str) -> Optional[dict]:
    base_url = API_30S if mode == "30S" else API_1M
    ts = int(time.time() * 1000)

    gateways = [
        f"{base_url}?t={ts}",
        f"https://corsproxy.io/?{base_url}?t={ts}",
        f"https://api.allorigins.win/raw?url={base_url}",
        f"https://thingproxy.freeboard.io/fetch/{base_url}",
        f"https://api.codetabs.com/v1/proxy?quest={base_url}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(112, 123)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    for url in gateways:
        try:
            r = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)
            if r.status_code != 200:
                continue
            data = r.json()
            if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
                return data["data"]["list"][0]
        except Exception:
            continue
    return None

async def fetch_latest_issue(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(_fetch_latest_issue_sync, mode)


# =========================
# MESSAGES
# =========================
def pretty_pick(pick: str) -> Tuple[str, str]:
    if pick == "BIG":
        return "🟢🟢 <b>BIG</b> 🟢🟢", "GREEN"
    return "🔴🔴 <b>SMALL</b> 🔴🔴", "RED"

def recovery_label(loss_streak: int) -> str:
    # You wanted: 1 step loss, 2 step loss...
    if loss_streak <= 0:
        return f"0 Step / {MAX_RECOVERY_STEPS}"
    return f"{loss_streak} Step Loss / {MAX_RECOVERY_STEPS}"

def format_signal(issue: str, pick: str, conf: int) -> str:
    pick_txt, _ = pretty_pick(pick)
    return (
        f"<b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_txt}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{recovery_label(state.streak_loss)}</b>\n"
        f"⏱ <b>BD Time</b> ➜ <b>{now_bd_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>JOIN</b> ➜ <a href='{CHANNEL_LINK}'>{CHANNEL_LINK}</a>"
    )

def format_checking(wait_issue: str) -> str:
    return (
        f"🛰 <b>CHECKING RESULT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"🧾 <b>Waiting:</b> <code>{wait_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ syncing..."
    )

def format_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool) -> str:
    pick_txt, _ = pretty_pick(pick)
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    color_result = "GREEN" if res_type == "BIG" else "RED"

    if is_win:
        header = "✅ <b>WIN CONFIRMED</b> ✅"
        extra = f"\n🎨 <b>Color Win:</b> <b>{color_result}</b>" if state.color_mode else ""
    else:
        header = "❌ <b>LOSS CONFIRMED</b> ❌"
        extra = ""

    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_txt}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>Recovery:</b> <b>{recovery_label(state.streak_loss)}</b>\n"
        f"{extra}\n"
        f"📊 <b>W:</b> <b>{state.wins}</b> | <b>L:</b> <b>{state.losses}</b> | ⏱ <b>{now_bd_str()}</b>"
    ).strip()

def format_summary() -> str:
    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Mode:</b> {mode_label(state.mode)}\n"
        f"📦 <b>Total:</b> <b>{total}</b>\n"
        f"✅ <b>Win:</b> <b>{state.wins}</b>\n"
        f"❌ <b>Loss:</b> <b>{state.losses}</b>\n"
        f"🎯 <b>Win Rate:</b> <b>{wr:.1f}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>\n"
        f"🧨 <b>Max Loss Streak:</b> <b>{state.max_loss_streak}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed:</b> <b>{now_bd_str()}</b>\n"
        f"🔗 <b>REJOIN</b> ➜ <a href='{CHANNEL_LINK}'>{CHANNEL_LINK}</a>"
    )


# =========================
# PANEL (Premium Selector)
# =========================
def _chat_name(chat_id: int) -> str:
    if chat_id == TARGETS["MAIN_GROUP"]:
        return "MAIN GROUP"
    if chat_id == TARGETS["VIP"]:
        return "VIP"
    if chat_id == TARGETS["PUBLIC"]:
        return "PUBLIC"
    return str(chat_id)

def panel_text() -> str:
    running = "🟢 RUNNING" if state.running else "🔴 STOPPED"
    sel = state.selected_targets[:] if state.selected_targets else [TARGETS["MAIN_GROUP"]]
    sel_lines = "\n".join([f"✅ <b>{_chat_name(cid)}</b> <code>{cid}</code>" for cid in sel])

    total = state.wins + state.losses
    wr = (state.wins / total * 100) if total else 0.0

    color = "🎨 <b>COLOR:</b> <b>ON</b>" if state.color_mode else "🎨 <b>COLOR:</b> <b>OFF</b>"
    grace = "🧠 <b>STOP AFTER RECOVER:</b> ✅" if state.graceful_stop_requested else "🧠 <b>STOP AFTER RECOVER:</b> ❌"

    return (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 <b>Status:</b> {running}\n"
        f"⚡ <b>Mode:</b> <b>{mode_label(state.mode)}</b>\n"
        f"{color}\n"
        f"{grace}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>Send Signals To</b>\n"
        f"{sel_lines}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>Live Stats</b>\n"
        f"✅ Win: <b>{state.wins}</b>\n"
        f"❌ Loss: <b>{state.losses}</b>\n"
        f"🎯 WinRate: <b>{wr:.1f}%</b>\n"
        f"🔥 WinStreak: <b>{state.streak_win}</b> | 🧊 LossStreak: <b>{state.streak_loss}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Select then Start</i>"
    )

def selector_markup() -> InlineKeyboardMarkup:
    def btn(name: str, chat_id: int) -> InlineKeyboardButton:
        on = "✅" if chat_id in state.selected_targets else "⬜"
        return InlineKeyboardButton(f"{on} {name}", callback_data=f"TOGGLE:{chat_id}")

    rows = [
        [btn("MAIN GROUP", TARGETS["MAIN_GROUP"])],
        [btn("VIP", TARGETS["VIP"]), btn("PUBLIC", TARGETS["PUBLIC"])],
        [InlineKeyboardButton("🎨 Color: ON" if state.color_mode else "🎨 Color: OFF", callback_data="TOGGLE_COLOR")],
        [
            InlineKeyboardButton("⚡ Start 30 SEC", callback_data="START:30S"),
            InlineKeyboardButton("⚡ Start 1 MIN", callback_data="START:1M"),
        ],
        [
            InlineKeyboardButton("🧠 Stop After Recover", callback_data="STOP:GRACEFUL"),
            InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE"),
        ],
        [InlineKeyboardButton("🔄 Refresh Panel", callback_data="REFRESH_PANEL")]
    ]
    return InlineKeyboardMarkup(rows)


# =========================
# HELPERS
# =========================
async def safe_delete(bot, chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception:
        pass

async def broadcast_sticker(bot, sticker_id: str):
    for cid in state.selected_targets:
        try:
            await bot.send_sticker(cid, sticker_id)
        except Exception:
            pass

async def broadcast_message(bot, text: str) -> Dict[int, int]:
    out = {}
    for cid in state.selected_targets:
        try:
            m = await bot.send_message(
                cid,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            out[cid] = m.message_id
        except Exception:
            pass
    return out


# =========================
# SESSION CONTROL
# =========================
def reset_stats():
    state.wins = 0
    state.losses = 0
    state.streak_win = 0
    state.streak_loss = 0
    state.max_win_streak = 0
    state.max_loss_streak = 0

async def stop_session(bot, reason: str = "manual"):
    state.session_id += 1
    state.running = False
    state.stop_event.set()

    # delete any checking messages
    if state.active:
        for cid, mid in (state.active.checking_msg_ids or {}).items():
            await safe_delete(bot, cid, mid)

        # delete loss-related messages when stop (your request)
        for cid, mids in (state.active.loss_related_ids or {}).items():
            for mid in mids:
                await safe_delete(bot, cid, mid)

    # END sticker (required, but not in loss time)
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])

    # summary to selected targets
    for cid in state.selected_targets:
        try:
            await bot.send_message(
                cid,
                format_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception:
            pass

    state.unlocked = False
    state.active = None
    state.graceful_stop_requested = False

async def start_session(bot, mode: str):
    state.mode = mode
    state.session_id += 1
    state.running = True
    state.stop_event.clear()
    state.graceful_stop_requested = False

    state.engine = PredictionEngine()
    state.active = None
    state.last_result_issue = None
    state.last_signal_issue = None
    reset_stats()

    # Start sticker per mode
    stk = STICKERS["START_30S"] if mode == "30S" else STICKERS["START_1M"]
    await broadcast_sticker(bot, stk)

    # START sticker always (required; but not for loss time)
    await broadcast_sticker(bot, STICKERS["START_END_ALWAYS"])


# =========================
# ENGINE LOOP
# =========================
async def engine_loop(context: ContextTypes.DEFAULT_TYPE, my_session: int):
    bot = context.bot
    last_seen_issue = None

    while state.running and state.session_id == my_session:
        if state.stop_event.is_set() or (not state.running) or state.session_id != my_session:
            break

        latest = await fetch_latest_issue(state.mode)
        if not latest:
            await asyncio.sleep(FETCH_RETRY_SLEEP)
            continue

        issue = str(latest.get("issueNumber"))
        num = str(latest.get("number"))
        res_type = "BIG" if int(num) >= 5 else "SMALL"
        next_issue = str(int(issue) + 1)

        state.engine.update_history(latest)

        if last_seen_issue == issue:
            await asyncio.sleep(0.2)
        last_seen_issue = issue

        # ---------- RESULT ----------
        if state.active and state.active.predicted_issue == issue:
            if state.last_result_issue == issue:
                await asyncio.sleep(0.1)
                continue

            pick = state.active.pick
            is_win = (pick == res_type)

            if is_win:
                state.wins += 1
                state.streak_win += 1
                state.streak_loss = 0
                state.max_win_streak = max(state.max_win_streak, state.streak_win)
            else:
                state.losses += 1
                state.streak_loss += 1
                state.streak_win = 0
                state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)

            # Stickers order: WIN/LOSS + super win
            if is_win:
                await broadcast_sticker(bot, STICKERS["WIN_ALWAYS"])
                if state.streak_win in STICKERS["SUPER_WIN"]:
                    await broadcast_sticker(bot, STICKERS["SUPER_WIN"][state.streak_win])
                else:
                    await broadcast_sticker(bot, random.choice(STICKERS["WIN_POOL"]))
                await broadcast_sticker(bot, STICKERS["WIN_BIG"] if res_type == "BIG" else STICKERS["WIN_SMALL"])
                await broadcast_sticker(bot, STICKERS["WIN_ANY"])
            else:
                await broadcast_sticker(bot, STICKERS["LOSS"])

            await broadcast_message(bot, format_result(issue, num, res_type, pick, is_win))

            # delete checking messages now
            for cid, mid in (state.active.checking_msg_ids or {}).items():
                await safe_delete(bot, cid, mid)

            state.last_result_issue = issue

            # If stop-after-recover requested: stop only after win
            if state.graceful_stop_requested and is_win:
                state.active = None
                await stop_session(bot, reason="graceful_done")
                break

            state.active = None

        # ---------- SIGNAL ----------
        if (not state.active) and (state.last_signal_issue != next_issue):
            if state.stop_event.is_set() or (not state.running) or state.session_id != my_session:
                break

            # safety: if already hit max recovery steps -> stop
            if state.streak_loss >= MAX_RECOVERY_STEPS:
                for cid in state.selected_targets:
                    try:
                        await bot.send_message(
                            cid,
                            "🧊 <b>SAFETY STOP</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                            "Recovery 8 Step এ চলে গেছে। সেফটির জন্য সেশন বন্ধ করা হলো। ✅",
                            parse_mode=ParseMode.HTML,
                        )
                    except Exception:
                        pass
                await stop_session(bot, reason="max_steps")
                break

            pred = state.engine.get_pattern_signal(state.streak_loss)
            conf = state.engine.calc_confidence(state.streak_loss)

            # Stickers first
            if state.mode == "30S":
                s_stk = STICKERS["PRED_30S_BIG"] if pred == "BIG" else STICKERS["PRED_30S_SMALL"]
            else:
                s_stk = STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"]

            await broadcast_sticker(bot, s_stk)

            if state.color_mode:
                await broadcast_sticker(bot, STICKERS["COLOR_GREEN"] if pred == "BIG" else STICKERS["COLOR_RED"])

            # Prediction message then checking message
            await broadcast_message(bot, format_signal(next_issue, pred, conf))

            checking_ids = {}
            for cid in state.selected_targets:
                try:
                    m = await bot.send_message(
                        cid,
                        format_checking(next_issue),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    checking_ids[cid] = m.message_id
                except Exception:
                    pass

            # store active bet
            bet = ActiveBet(predicted_issue=next_issue, pick=pred)
            bet.checking_msg_ids = checking_ids

            # loss messages to delete on stop: include checking (and later loss result if needed)
            for cid, mid in checking_ids.items():
                bet.loss_related_ids.setdefault(cid, []).append(mid)

            state.active = bet
            state.last_signal_issue = next_issue

        await asyncio.sleep(FAST_LOOP_30S if state.mode == "30S" else FAST_LOOP_1M)


# =========================
# COMMANDS & CALLBACKS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Every time /start => refresh password again (your requirement)
    state.expected_password = await get_live_password()
    state.unlocked = False

    await update.message.reply_text(
        "🔒 <b>SYSTEM LOCKED</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Password দিন:",
        parse_mode=ParseMode.HTML
    )

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.unlocked:
        state.expected_password = await get_live_password()
        await update.message.reply_text("🔒 <b>LOCKED</b>\nPassword দিন:", parse_mode=ParseMode.HTML)
        return

    await update.message.reply_text(
        panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=selector_markup(),
        disable_web_page_preview=True
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()

    # locked => password required
    if not state.unlocked:
        # refresh password each time (your requirement)
        state.expected_password = await get_live_password()

        if txt == state.expected_password:
            state.unlocked = True
            await update.message.reply_text("✅ <b>UNLOCKED</b>", parse_mode=ParseMode.HTML)
            await update.message.reply_text(
                panel_text(),
                parse_mode=ParseMode.HTML,
                reply_markup=selector_markup(),
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text("❌ <b>WRONG PASSWORD</b>", parse_mode=ParseMode.HTML)
        return

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    if not state.unlocked:
        await q.edit_message_text("🔒 <b>LOCKED</b>\n/start দিন।", parse_mode=ParseMode.HTML)
        return

    if data == "REFRESH_PANEL":
        await q.edit_message_text(
            panel_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=selector_markup(),
            disable_web_page_preview=True
        )
        return

    if data.startswith("TOGGLE:"):
        cid = int(data.split(":", 1)[1])
        if cid in state.selected_targets:
            state.selected_targets.remove(cid)
        else:
            state.selected_targets.append(cid)

        if not state.selected_targets:
            state.selected_targets = [TARGETS["MAIN_GROUP"]]

        await q.edit_message_text(
            panel_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=selector_markup(),
            disable_web_page_preview=True
        )
        return

    if data == "TOGGLE_COLOR":
        state.color_mode = not state.color_mode
        await q.edit_message_text(
            panel_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=selector_markup(),
            disable_web_page_preview=True
        )
        return

    if data.startswith("START:"):
        mode = data.split(":", 1)[1]
        if state.running:
            await stop_session(context.bot, reason="restart")

        await start_session(context.bot, mode)
        my_session = state.session_id
        context.application.create_task(engine_loop(context, my_session))

        await q.edit_message_text(
            panel_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=selector_markup(),
            disable_web_page_preview=True
        )
        return

    if data == "STOP:FORCE":
        if state.running:
            await stop_session(context.bot, reason="force")
        await q.edit_message_text(
            panel_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=selector_markup(),
            disable_web_page_preview=True
        )
        return

    if data == "STOP:GRACEFUL":
        if state.running:
            state.graceful_stop_requested = True
            # if not in recovery, stop now
            if state.streak_loss == 0 and state.active is None:
                await stop_session(context.bot, reason="graceful_now")

        await q.edit_message_text(
            panel_text(),
            parse_mode=ParseMode.HTML,
            reply_markup=selector_markup(),
            disable_web_page_preview=True
        )
        return


# =========================
# MAIN
# =========================
def main():
    # Keep logs minimal (no secrets)
    logging.basicConfig(level=logging.WARNING)

    keep_alive()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("panel", cmd_panel))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
