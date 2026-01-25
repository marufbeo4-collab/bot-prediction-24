# ===========================
# DK MARUF SIGNAL BOT (Render Ready)
# python-telegram-bot==20.7
# Flask==3.0.3
# requests==2.32.3
# ===========================

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from threading import Thread
from typing import Dict, List, Optional

import requests
from flask import Flask
from zoneinfo import ZoneInfo
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ===========================
# CONFIG
# ===========================

BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"  # <-- only token placeholder

BRAND_NAME = "⚡⚡⚡ 𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
REJOIN_LINK = "https://t.me/big_maruf_official0"

# Targets
TARGETS = {
    "MAIN_GROUP": -1003293007059,
    "VIP": -1002892329434,
    "PUBLIC": -1002629495753,
}

# Sheet password (A1)
SHEET_CELL_A1_CSV = "https://docs.google.com/spreadsheets/d/1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo/export?format=csv&gid=0"

# API
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ===========================
# STICKERS (Your Provided)
# ===========================

STICKERS = {
    # 1M prediction
    "PRED_1M_BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    "PRED_1M_SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",

    # 30S prediction (SWAP FIXED)
    "PRED_30S_BIG": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    "PRED_30S_SMALL": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",

    # Win/Loss
    "WIN_BIG": "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    "WIN_SMALL": "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    "WIN_ANY": "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",
    "LOSS": "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",

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

    # Color
    "COLOR_RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "COLOR_GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",

    # Start by mode
    "START_30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
    "START_1M": "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE",

    # Always badge (start/end)
    "ALWAYS_BADGE": "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE",
}

# ===========================
# Flask keep-alive (Render web service)
# ===========================

app = Flask(__name__)

@app.get("/")
def home():
    return "DK MARUF BOT ALIVE ✅"

def run_http():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_http, daemon=True)
    t.start()

# ===========================
# Utils
# ===========================

def bd_now_str() -> str:
    dt = datetime.now(ZoneInfo("Asia/Dhaka"))
    return dt.strftime("%H:%M:%S")

def mode_label(mode: str) -> str:
    return "30 SEC" if mode == "30S" else "1 MIN"

def api_url_for(mode: str) -> str:
    return API_30S if mode == "30S" else API_1M

def pred_sticker_for(mode: str, pred: str) -> str:
    if mode == "30S":
        return STICKERS["PRED_30S_BIG"] if pred == "BIG" else STICKERS["PRED_30S_SMALL"]
    return STICKERS["PRED_1M_BIG"] if pred == "BIG" else STICKERS["PRED_1M_SMALL"]

def color_name_from_pick(pick: str) -> str:
    # BIG = GREEN, SMALL = RED
    return "GREEN" if pick == "BIG" else "RED"

def safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default

# ===========================
# Password from Sheet (A1)
# ===========================

def fetch_password_from_sheet(timeout=6) -> Optional[str]:
    try:
        r = requests.get(SHEET_CELL_A1_CSV, timeout=timeout)
        if r.status_code != 200:
            return None
        val = (r.text or "").strip().splitlines()[0].split(",")[0].strip().strip('"')
        return val if val else None
    except Exception:
        return None

# ===========================
# Multi-gateway fetch (requests + rotation)
# ===========================

def fetch_latest_issue_sync(mode: str) -> Optional[dict]:
    base = api_url_for(mode)
    ts = int(time.time() * 1000)

    gateways = [
        f"{base}?t={ts}",
        f"https://corsproxy.io/?{base}?t={ts}",
        f"https://api.allorigins.win/raw?url={base}",
        f"https://thingproxy.freeboard.io/fetch/{base}",
        f"https://api.codetabs.com/v1/proxy?quest={base}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 Chrome/{random.randint(110,125)}.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
    }

    for url in gateways:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code != 200:
                continue
            data = resp.json()
            issue_list = data.get("data", {}).get("list", [])
            if not issue_list:
                continue
            return issue_list[0]
        except Exception:
            continue
    return None

async def fetch_latest_issue(mode: str) -> Optional[dict]:
    return await asyncio.to_thread(fetch_latest_issue_sync, mode)

# ===========================
# Prediction Engine (YOUR FINAL LOGIC)
# ===========================

class PredictionEngine:
    def __init__(self):
        self.history: List[str] = []
        self.raw_history: List[dict] = []
        self.last_prediction: Optional[str] = None

    def update_history(self, issue_data: dict):
        num = safe_int(issue_data.get("number"), None)
        issue_no = issue_data.get("issueNumber")
        if num is None or issue_no is None:
            return
        result_type = "BIG" if num >= 5 else "SMALL"

        if (not self.raw_history) or (self.raw_history[0].get("issueNumber") != issue_no):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:80]
            self.raw_history = self.raw_history[:80]

    def get_pattern_signal(self, current_streak_loss: int):
        if len(self.history) < 15:
            return random.choice(["BIG", "SMALL"])

        h = self.history
        votes: List[str] = []

        last_12 = h[:12]
        votes.append("BIG" if last_12.count("BIG") > last_12.count("SMALL") else "SMALL")
        votes.append(h[0])
        votes.append("SMALL" if h[0] == "BIG" else "BIG")

        if h[0] == h[1] == h[2]:
            votes.append(h[0])

        if h[0] == h[1] and h[2] == h[3] and h[1] != h[2]:
            votes.append("SMALL" if h[0] == "BIG" else "BIG")

        try:
            r_num = safe_int(self.raw_history[0].get("number"), 0)
            p_digit = safe_int(str(self.raw_history[0].get("issueNumber", 0))[-1], 0)
            prev_num = safe_int(self.raw_history[1].get("number"), 0) if len(self.raw_history) > 1 else r_num

            votes.append("SMALL" if (p_digit + r_num) % 2 == 0 else "BIG")
            votes.append("SMALL" if (r_num + prev_num) % 2 == 0 else "BIG")
            votes.append("BIG" if r_num >= 5 else "SMALL")
            votes.append("SMALL" if ((r_num * 3) + p_digit) % 2 == 0 else "BIG")
        except Exception:
            pass

        current_pat = h[:3]
        mb, ms = 0, 0
        for i in range(1, len(h) - 3):
            if h[i:i+3] == current_pat:
                nxt = h[i-1]
                mb += 1 if nxt == "BIG" else 0
                ms += 1 if nxt == "SMALL" else 0
        if mb > ms:
            votes.append("BIG")
        elif ms > mb:
            votes.append("SMALL")

        votes.append(h[0])

        if current_streak_loss >= 2 and self.last_prediction:
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

    def confidence(self, streak_loss: int) -> int:
        base = random.randint(86, 93)
        if streak_loss >= 2:
            base = random.randint(87, 95)
        if streak_loss >= 6:
            base = random.randint(88, 96)
        return base

# ===========================
# Bot State
# ===========================

@dataclass
class ActiveBet:
    period: str
    pick: str
    check_msg_ids: Dict[int, int] = field(default_factory=dict)

@dataclass
class BotState:
    running: bool = False
    mode: str = "30S"
    engine: PredictionEngine = field(default_factory=PredictionEngine)

    active_bet: Optional[ActiveBet] = None
    last_period_processed: Optional[str] = None

    wins: int = 0
    losses: int = 0
    streak_win: int = 0
    streak_loss: int = 0
    max_win_streak: int = 0
    max_loss_streak: int = 0

    stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    engine_task: Optional[asyncio.Task] = None

    authorized_users: set = field(default_factory=set)

    selected_targets: List[int] = field(default_factory=lambda: [TARGETS["MAIN_GROUP"]])
    color_mode: bool = True

    graceful_stop_requested: bool = False

state = BotState()

# ===========================
# Premium messages
# ===========================

def format_prediction_msg(mode: str, period: str, pred: str, conf: int, step_loss: int) -> str:
    emoji = "🟢🟢" if pred == "BIG" else "🔴🔴"
    step_txt = "0 Step" if step_loss == 0 else f"{step_loss} Step Loss"
    color_line = ""
    if state.color_mode:
        color_line = f"\n🎨 <b>Color Pick</b> ➜ <b>{color_name_from_pick(pred)}</b>"

    return (
        f"{BRAND_NAME}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> <b>{mode_label(mode)}</b>\n"
        f"🧾 <b>Period:</b> <code>{period}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {emoji} <b>{pred}</b> {emoji}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{step_txt}</b> / <b>8</b>"
        f"{color_line}\n"
        f"🕒 <b>BD Time</b> ➜ <b>{bd_now_str()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>JOIN / REJOIN</b> ➜ <a href='{REJOIN_LINK}'>CLICK HERE</a>"
    )

def format_checking_msg(mode: str, waiting_period: str) -> str:
    return (
        f"🛰️ <b>LIVE CHECK</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> {mode_label(mode)}\n"
        f"🧾 <b>Waiting Result:</b> <code>{waiting_period}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <i>syncing…</i>"
    )

def format_result_msg(mode: str, period: str, res_num: int, res_type: str, pick: str, is_win: bool) -> str:
    head = "✅ <b>WIN CONFIRMED</b>" if is_win else "❌ <b>LOSS CONFIRMED</b>"
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    pick_emoji = "🟢🟢" if pick == "BIG" else "🔴🔴"
    step_line = "0 Step" if state.streak_loss == 0 else f"{state.streak_loss} Step Loss"

    # color win text
    color_text = ""
    if state.color_mode and is_win:
        # If pick won, then the picked color won
        color_text = f"\n🎨 <b>Color Win:</b> <b>{color_name_from_pick(pick)}</b> ✅"
    elif state.color_mode and (not is_win):
        color_text = f"\n🎨 <b>Color:</b> <b>{color_name_from_pick(pick)}</b> ❌"

    return (
        f"{head}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> {mode_label(mode)}\n"
        f"🧾 <b>Period:</b> <code>{period}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Your Pick:</b> {pick_emoji} <b>{pick}</b>\n"
        f"{color_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>{step_line}</b> / <b>8</b>\n"
        f"📊 <b>W:{state.wins}</b> | <b>L:{state.losses}</b> | <b>{bd_now_str()}</b>\n"
        f"🔥 <b>Max Win Streak:</b> <b>{state.max_win_streak}</b>"
    )

def format_summary(mode: str) -> str:
    total = state.wins + state.losses
    rate = (state.wins / total * 100) if total else 0.0
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>Mode:</b> {mode_label(mode)}\n"
        f"📦 <b>Total:</b> {total}\n"
        f"✅ <b>Win:</b> {state.wins}\n"
        f"❌ <b>Loss:</b> {state.losses}\n"
        f"🎯 <b>Win Rate:</b> {rate:.1f}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak:</b> {state.max_win_streak}\n"
        f"🧊 <b>Max Loss Streak:</b> {state.max_loss_streak}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 <b>Closed:</b> {bd_now_str()}\n"
        f"🔗 <b>REJOIN</b> ➜ <a href='{REJOIN_LINK}'>CLICK</a>"
    )

# ===========================
# Send helpers
# ===========================

async def send_to_targets(bot, method: str, *args, **kwargs):
    for chat_id in state.selected_targets:
        try:
            fn = getattr(bot, method)
            await fn(chat_id, *args, **kwargs)
        except Exception:
            pass

async def send_msg_collect_ids(bot, text: str, **kwargs) -> Dict[int, int]:
    ids = {}
    for chat_id in state.selected_targets:
        try:
            msg = await bot.send_message(chat_id, text, **kwargs)
            ids[chat_id] = msg.message_id
        except Exception:
            pass
    return ids

async def delete_msg_ids(bot, msg_ids: Dict[int, int]):
    for chat_id, mid in msg_ids.items():
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass

# ===========================
# Engine loop
# ===========================

async def stop_session(context: ContextTypes.DEFAULT_TYPE):
    state.running = False
    state.stop_event.set()
    state.graceful_stop_requested = False

    await send_to_targets(context.bot, "send_sticker", STICKERS["ALWAYS_BADGE"])
    await send_to_targets(
        context.bot,
        "send_message",
        format_summary(state.mode),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

    if state.engine_task and (not state.engine_task.done()):
        state.engine_task.cancel()
        try:
            await state.engine_task
        except Exception:
            pass
    state.engine_task = None

async def engine_loop(context: ContextTypes.DEFAULT_TYPE):
    logging.info("Engine loop started ✅")
    state.stop_event.clear()

    await send_to_targets(context.bot, "send_sticker", STICKERS["ALWAYS_BADGE"])
    await send_to_targets(context.bot, "send_sticker", STICKERS["START_30S"] if state.mode == "30S" else STICKERS["START_1M"])

    while state.running and (not state.stop_event.is_set()):
        try:
            latest = await fetch_latest_issue(state.mode)
            if not latest:
                await asyncio.sleep(0.6 if state.mode == "30S" else 1.2)
                continue

            latest_issue = str(latest.get("issueNumber"))
            latest_num = safe_int(latest.get("number"), 0)
            latest_type = "BIG" if latest_num >= 5 else "SMALL"

            state.engine.update_history(latest)

            # Resolve result if active bet matches
            if state.active_bet and state.active_bet.period == latest_issue:
                if state.last_period_processed == latest_issue:
                    await asyncio.sleep(0.2)
                    continue

                pick = state.active_bet.pick
                is_win = (pick == latest_type)

                # delete checking msg
                await delete_msg_ids(context.bot, state.active_bet.check_msg_ids)

                # sticker + stats
                if is_win:
                    state.wins += 1
                    state.streak_win += 1
                    state.streak_loss = 0
                    state.max_win_streak = max(state.max_win_streak, state.streak_win)

                    if random.random() < 0.55:
                        await send_to_targets(context.bot, "send_sticker", random.choice(STICKERS["WIN_RANDOM"]))
                    else:
                        await send_to_targets(context.bot, "send_sticker", STICKERS["WIN_ANY"])
                else:
                    state.losses += 1
                    state.streak_win = 0
                    state.streak_loss += 1
                    state.max_loss_streak = max(state.max_loss_streak, state.streak_loss)
                    await send_to_targets(context.bot, "send_sticker", STICKERS["LOSS"])

                # result msg
                await send_to_targets(
                    context.bot,
                    "send_message",
                    format_result_msg(state.mode, latest_issue, latest_num, latest_type, pick, is_win),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

                state.last_period_processed = latest_issue
                state.active_bet = None

                # auto stop at 8 step
                if state.streak_loss >= 8:
                    await send_to_targets(context.bot, "send_message",
                                          "🧸 <b>8 Step Reached</b> — Cool down ✅\n<b>Auto Stop Activated.</b>",
                                          parse_mode=ParseMode.HTML)
                    await stop_session(context)
                    break

                if state.graceful_stop_requested and state.streak_loss == 0:
                    await stop_session(context)
                    break

            # Create next prediction
            if (not state.running) or state.stop_event.is_set():
                break

            if not state.active_bet:
                next_issue = str(int(latest_issue) + 1)
                await asyncio.sleep(0.25 if state.mode == "30S" else 0.55)

                if (not state.running) or state.stop_event.is_set():
                    break

                pred = state.engine.get_pattern_signal(state.streak_loss)
                conf = state.engine.confidence(state.streak_loss)

                # prediction sticker
                await send_to_targets(context.bot, "send_sticker", pred_sticker_for(state.mode, pred))

                # color sticker (if on)
                if state.color_mode:
                    await send_to_targets(
                        context.bot,
                        "send_sticker",
                        STICKERS["COLOR_GREEN"] if pred == "BIG" else STICKERS["COLOR_RED"]
                    )

                # prediction message
                await send_to_targets(
                    context.bot,
                    "send_message",
                    format_prediction_msg(state.mode, next_issue, pred, conf, state.streak_loss),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

                # checking message (store ids to delete)
                chk_ids = await send_msg_collect_ids(
                    context.bot,
                    format_checking_msg(state.mode, next_issue),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

                state.active_bet = ActiveBet(period=next_issue, pick=pred, check_msg_ids=chk_ids)

            await asyncio.sleep(0.35 if state.mode == "30S" else 0.9)

        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(0.8)

    logging.info("Engine loop ended ✅")

# ===========================
# UI Panel
# ===========================

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
            InlineKeyboardButton("🛑 Stop Now", callback_data="STOP:FORCE"),
            InlineKeyboardButton("🧠 Stop After Recover", callback_data="STOP:GRACEFUL"),
        ]
    ]
    return InlineKeyboardMarkup(rows)

async def send_selector(update: Update):
    txt = (
        "🔐 <b>CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>Select Targets</b> (Run in 1/2/3 chats)\n"
        "🎨 <b>Color Trade</b> toggle available\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 Select then Start"
    )
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML, reply_markup=selector_markup())

# ===========================
# Auth
# ===========================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in state.authorized_users:
        await send_selector(update)
        return

    await update.message.reply_text("🔒 <b>LOCKED</b>\nEnter Password:", parse_mode=ParseMode.HTML)

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in state.authorized_users:
        await update.message.reply_text("🔒 Locked. Use /start", parse_mode=ParseMode.HTML)
        return
    await send_selector(update)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = (update.message.text or "").strip()

    if uid not in state.authorized_users:
        sheet_pw = await asyncio.to_thread(fetch_password_from_sheet)
        if sheet_pw and msg == sheet_pw:
            state.authorized_users.add(uid)
            await send_selector(update)
        else:
            await update.message.reply_text("❌ <b>Wrong Password</b>", parse_mode=ParseMode.HTML)
        return

    await update.message.reply_text("⚙️ Open Panel: /panel", parse_mode=ParseMode.HTML)

# ===========================
# Callback
# ===========================

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    if uid not in state.authorized_users:
        try:
            await q.edit_message_text("🔒 Locked. Use /start")
        except Exception:
            pass
        return

    data = q.data or ""

    if data.startswith("TOGGLE:"):
        chat_id = int(data.split(":")[1])
        if chat_id in state.selected_targets:
            if len(state.selected_targets) > 1:
                state.selected_targets.remove(chat_id)
        else:
            state.selected_targets.append(chat_id)

        try:
            await q.edit_message_reply_markup(reply_markup=selector_markup())
        except Exception:
            pass
        return

    if data == "TOGGLE_COLOR":
        state.color_mode = not state.color_mode
        try:
            await q.edit_message_reply_markup(reply_markup=selector_markup())
        except Exception:
            pass
        return

    if data.startswith("START:"):
        mode = data.split(":")[1]

        # reset session
        state.mode = mode
        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_period_processed = None

        state.wins = 0
        state.losses = 0
        state.streak_win = 0
        state.streak_loss = 0
        state.max_win_streak = 0
        state.max_loss_streak = 0

        state.running = True
        state.stop_event.clear()
        state.graceful_stop_requested = False

        if state.engine_task and (not state.engine_task.done()):
            state.engine_task.cancel()
            try:
                await state.engine_task
            except Exception:
                pass

        state.engine_task = context.application.create_task(engine_loop(context))

        try:
            await q.edit_message_text(
                f"✅ Started: <b>{mode_label(mode)}</b>\nTargets Selected: <b>{len(state.selected_targets)}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=selector_markup()
            )
        except Exception:
            pass
        return

    if data.startswith("STOP:"):
        if not state.running:
            try:
                await q.edit_message_text("ℹ️ Already stopped.", reply_markup=selector_markup())
            except Exception:
                pass
            return

        typ = data.split(":")[1]
        if typ == "GRACEFUL":
            state.graceful_stop_requested = True
            try:
                await q.edit_message_text(
                    "🧠 Graceful Stop armed ✅\nWill stop after recovery (loss -> 0).",
                    parse_mode=ParseMode.HTML,
                    reply_markup=selector_markup()
                )
            except Exception:
                pass
            return

        # FORCE
        try:
            await q.edit_message_text("🛑 Stopping now…", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await stop_session(context)
        return

# ===========================
# Main
# ===========================

def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    app_telegram = Application.builder().token(BOT_TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", cmd_start))
    app_telegram.add_handler(CommandHandler("panel", cmd_panel))

    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    # ✅ Correct callback handler (Fix for your error)
    app_telegram.add_handler(CallbackQueryHandler(on_callback))

    app_telegram.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
