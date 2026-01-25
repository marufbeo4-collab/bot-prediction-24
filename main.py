import asyncio
import logging
import random
import time
import os
from threading import Thread

import requests
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"  # ✅ শুধু এখানেই টোকেন বসাবি

TARGET_CHANNEL = -1003651634734
BRAND_NAME = "𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

# Password from Google Sheet A1 (Public view needed)
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_GID = "0"
PASSWORD_CACHE_SECONDS = 20

MAX_LOSS_STOP = 8  # 8 step loss হলে auto off + shantona

# ================= STICKER DATABASE =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    'WIN_BIG': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_SMALL': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'LOSS': [
        "CAACAgUAAxkBAAEQUThpdFDWMkZlP8PkRjl82QRGStGpFQACohQAAn_dMVcPP5YV0-TlBTgE",
        "CAACAgUAAxkBAAEQTh5pcmTbrSEe58RRXvtu_uwEAWZoQQAC5BEAArgxYVUhMlnBGKmcbzgE"
    ],
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
}

# ================= API LINKS =================
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK KEEP-ALIVE =================
app = Flask('')

@app.route('/')
def home():
    return f"{BRAND_NAME} • RUNNING"

@app.route('/health')
def health():
    return "ok"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    Thread(target=run_http, daemon=True).start()

# ================= PASSWORD FROM GOOGLE SHEET =================
_password_cache = {"value": None, "ts": 0.0}

def _sheet_csv_url() -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

def _fetch_password_sync(timeout: float = 6.0) -> str | None:
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

async def get_password(force_refresh: bool = False) -> str | None:
    now = time.time()
    if (not force_refresh) and _password_cache["value"] and (now - _password_cache["ts"] < PASSWORD_CACHE_SECONDS):
        return _password_cache["value"]

    pw = await asyncio.to_thread(_fetch_password_sync)
    if pw:
        _password_cache["value"] = pw
        _password_cache["ts"] = now
        return pw
    return None

# ================= PREDICTION ENGINE =================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.raw_history = []
        self.last_prediction = None

    def update_history(self, issue_data):
        try:
            number = int(issue_data['number'])
            result_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        # new issue check
        if (not self.raw_history) or (str(self.raw_history[0].get('issueNumber')) != str(issue_data.get('issueNumber'))):
            self.history.insert(0, result_type)   # newest first
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:300]
            self.raw_history = self.raw_history[:300]

    # ✅ Your requested Data-Mining pattern logic
    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 15:
            pred = random.choice(["BIG", "SMALL"])
            self.last_prediction = pred
            return pred

        current_pattern = self.history[:3]  # newest 3 pattern
        big_chance = 0
        small_chance = 0

        for i in range(1, len(self.history) - 3):
            past_sequence = self.history[i:i+3]
            if past_sequence == current_pattern:
                next_result_in_past = self.history[i - 1]  # next after pattern
                if next_result_in_past == "BIG":
                    big_chance += 1
                else:
                    small_chance += 1

        if big_chance > small_chance:
            prediction = "BIG"
        elif small_chance > big_chance:
            prediction = "SMALL"
        else:
            prediction = self.history[0]  # trend follow

        if current_streak_loss >= 2:
            prediction = "SMALL" if prediction == "BIG" else "BIG"

        self.last_prediction = prediction
        return prediction

    def calculate_confidence(self):
        # stable confidence
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
        self.game_mode = "1M"
        self.engine = PredictionEngine()
        self.active_bet = None  # {"period":..., "pick":..., "check_mid":..., "check_task":...}
        self.last_period_processed = None

        self.stats = {
            "wins": 0,
            "losses": 0,
            "streak_win": 0,
            "streak_loss": 0,
            "max_streak_win": 0,
            "max_streak_loss": 0
        }

        self.loss_message_ids = []  # loss sticker + loss message ids (delete on stop)

state = BotState()

AUTHORIZED_USERS = set()

def lock_all_users():
    AUTHORIZED_USERS.clear()

# ================= REQUESTS MULTI-GATEWAY =================
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

# ================= CHECKING ANIMATION =================
async def start_checking_animation(context: ContextTypes.DEFAULT_TYPE, chat_id: int, base_text: str):
    msg = await context.bot.send_message(
        chat_id,
        f"⏳ <b>{base_text}</b>\n<code>syncing…</code>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

    async def _animate():
        frames = ["syncing.", "syncing..", "syncing...", "syncing….", "syncing....."]
        i = 0
        while True:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=f"⏳ <b>{base_text}</b>\n<code>{frames[i % len(frames)]}</code>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except:
                pass
            i += 1
            await asyncio.sleep(1.0)

    task = asyncio.create_task(_animate())
    return msg.message_id, task

# ================= MESSAGE STYLE =================
def now_hms():
    return time.strftime("%H:%M:%S")

def step_text(step: int) -> str:
    return f"{step} Step Loss" if step > 0 else "Step 0"

def pick_badge(pred: str) -> str:
    if pred == "BIG":
        return "🟢🟢 <b>BIG</b> 🟢🟢"
    return "🔴🔴 <b>SMALL</b> 🔴🔴"

def fmt_signal(next_issue: str, pred: str, conf: int):
    join = f"\n🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>" if CHANNEL_LINK else ""
    return (
        f"⚡ <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Next Period</b> ➜ <code>{next_issue}</code>\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_badge(pred)}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>Step {state.stats['streak_loss']}</b> / {MAX_LOSS_STOP}\n"
        f"⏱ <b>Time</b> ➜ <code>{now_hms()}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{join}"
    )

def fmt_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]:
        res_emoji = "🟣"

    if is_win:
        title = "✅ <b>WIN CONFIRMED</b>"
        extra = f"🔥 <b>Win Streak:</b> {state.stats['streak_win']} (Max {state.stats['max_streak_win']})"
    else:
        title = "❌ <b>LOSS CONFIRMED</b>"
        extra = f"⚠️ <b>{step_text(state.stats['streak_loss'])}</b> / {MAX_LOSS_STOP} (Max {state.stats['max_streak_loss']})"

    return (
        f"{title}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period</b>: <code>{issue}</code>\n"
        f"🎰 <b>Result</b>: {res_emoji} <b>{res_num}</b> (<b>{res_type}</b>)\n"
        f"🎯 <b>Your Pick</b>: <b>{pick}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{extra}\n"
        f"📊 <b>W</b>:{state.stats['wins']}  |  <b>L</b>:{state.stats['losses']}  |  <code>{now_hms()}</code>"
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
        f"🎮 <b>Mode</b>: <code>{state.game_mode}</code>\n"
        f"📦 <b>Total Rounds</b>: <b>{total}</b>\n"
        f"✅ <b>Win</b>: <b>{w}</b>\n"
        f"❌ <b>Loss</b>: <b>{l}</b>\n"
        f"🎯 <b>Win Rate</b>: <b>{win_rate}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak</b>: <b>{state.stats['max_streak_win']}</b>\n"
        f"🧊 <b>Max Loss Streak</b>: <b>{state.stats['max_streak_loss']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed At</b>: <code>{now_hms()}</code>"
        f"{join}"
    )

def fmt_consolation_stop():
    join = f"\n🔗 <a href='{CHANNEL_LINK}'><b>TAKE A BREAK</b></a>" if CHANNEL_LINK else ""
    return (
        f"🧊 <b>SAFE GUARD ACTIVATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>{MAX_LOSS_STOP} Step Loss</b> reached.\n"
        f"🛡️ Prediction is now <b>OFF</b> for safety.\n"
        f"✅ Use /start to unlock again.\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{join}"
    )

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE, sid: int):
    fail_count = 0

    while state.is_running and state.session_id == sid:
        try:
            latest = await fetch_latest_issue(state.game_mode)

            if not latest:
                fail_count += 1
                base_wait = 1 if state.game_mode == "30S" else 2
                await asyncio.sleep(min(base_wait + fail_count, 12))
                continue

            fail_count = 0

            latest_issue = str(latest["issueNumber"])
            latest_num = str(latest["number"])
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # ---------- RESULT ----------
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

                # update history
                state.engine.update_history(latest)

                # update stats
                if is_win:
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                    state.stats["max_streak_win"] = max(state.stats["max_streak_win"], state.stats["streak_win"])

                    # win sticker
                    try:
                        st = STICKERS["WIN_BIG"] if latest_type == "BIG" else STICKERS["WIN_SMALL"]
                        await context.bot.send_sticker(TARGET_CHANNEL, st)
                    except:
                        pass
                else:
                    state.stats["losses"] += 1
                    state.stats["streak_win"] = 0
                    state.stats["streak_loss"] += 1
                    state.stats["max_streak_loss"] = max(state.stats["max_streak_loss"], state.stats["streak_loss"])

                    # loss sticker (track for deletion)
                    try:
                        ms = await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS["LOSS"]))
                        state.loss_message_ids.append(ms.message_id)
                    except:
                        pass

                # result message (track only if loss)
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

                # auto stop at MAX_LOSS_STOP
                if state.stats["streak_loss"] >= MAX_LOSS_STOP:
                    state.is_running = False
                    lock_all_users()

                    # delete loss clutter first
                    await delete_all_loss_messages(context)

                    # send consolation
                    try:
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            fmt_consolation_stop(),
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                    except:
                        pass
                    return

            # ---------- SIGNAL ----------
            if (not state.active_bet) and (state.last_period_processed != next_issue):
                await asyncio.sleep(1 if state.game_mode == "30S" else 2)
                if state.session_id != sid:
                    return

                state.engine.update_history(latest)
                pred = state.engine.get_pattern_signal(state.stats["streak_loss"])
                conf = state.engine.calculate_confidence()

                state.active_bet = {"period": next_issue, "pick": pred}

                # prediction sticker
                try:
                    s_stk = STICKERS["BIG_PRED"] if pred == "BIG" else STICKERS["SMALL_PRED"]
                    await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
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

                # checking animation message (delete later)
                try:
                    check_mid, check_task = await start_checking_animation(
                        context,
                        TARGET_CHANNEL,
                        f"Checking Result • Period {next_issue}"
                    )
                    state.active_bet["check_mid"] = check_mid
                    state.active_bet["check_task"] = check_task
                except:
                    pass

            await asyncio.sleep(1 if state.game_mode == "30S" else 2)

        except Exception:
            await asyncio.sleep(2)

async def run_engine_forever(context: ContextTypes.DEFAULT_TYPE, sid: int):
    while state.is_running and state.session_id == sid:
        try:
            await game_engine(context, sid)
        except Exception:
            await asyncio.sleep(2)
        await asyncio.sleep(1)

# ================= HANDLERS =================
async def show_main_menu(update: Update):
    await update.message.reply_text(
        f"🔓 <b>ACCESS GRANTED</b>\n<b>{BRAND_NAME}</b>\n\nSelect Mode:",
        reply_markup=ReplyKeyboardMarkup(
            [['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop & Summary']],
            resize_keyboard=True
        ),
        parse_mode=ParseMode.HTML
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pw = await get_password(force_refresh=True)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
        return

    uid = update.effective_user.id
    if uid in AUTHORIZED_USERS:
        await show_main_menu(update)
    else:
        await update.message.reply_text("🔒 <b>LOCKED</b>\nSend Password:", parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    uid = update.effective_user.id

    pw = await get_password(force_refresh=False)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
        return

    # AUTH
    if uid not in AUTHORIZED_USERS:
        if msg == pw:
            AUTHORIZED_USERS.add(uid)
            await show_main_menu(update)
            return
        await update.message.reply_text("❌ Wrong password", parse_mode=ParseMode.HTML)
        return

    # STOP
    if "Stop" in msg or msg == "/off":
        state.session_id += 1
        state.is_running = False

        # cancel checking + delete checking message if exists
        if state.active_bet:
            try:
                if state.active_bet.get("check_task"):
                    state.active_bet["check_task"].cancel()
            except:
                pass
            if state.active_bet.get("check_mid"):
                await safe_delete(context, TARGET_CHANNEL, state.active_bet["check_mid"])
        state.active_bet = None

        await update.message.reply_text("🛑 Stopping…", parse_mode=ParseMode.HTML)

        # ✅ delete loss messages first
        await delete_all_loss_messages(context)

        # ✅ send summary (clean group)
        try:
            await context.bot.send_message(
                TARGET_CHANNEL,
                fmt_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except:
            pass

        lock_all_users()
        return

    # CONNECT
    if "Connect" in msg:
        pw2 = await get_password(force_refresh=True)
        if not pw2:
            await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
            return

        state.session_id += 1
        sid = state.session_id

        mode = "1M" if "1M" in msg else "30S"
        state.game_mode = mode
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
            "max_streak_loss": 0
        }

        await update.message.reply_text(
            f"✅ Connected: <b>{mode}</b>\nEngine: <b>LIVE</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        try:
            await context.bot.send_sticker(TARGET_CHANNEL, STICKERS["START"])
        except:
            pass

        context.application.create_task(run_engine_forever(context, sid))

# ================= MAIN =================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    if not BOT_TOKEN or "PASTE_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing! Replace PASTE_TOKEN_HERE in main.py")

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
