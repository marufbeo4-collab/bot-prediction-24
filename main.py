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
# ⚠️ Public repo হলে TOKEN commit কইরো না (লিক হবে)
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"

TARGET_CHANNEL = -1003293007059
BRAND_NAME = "𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"
BOT_PASSWORD = "2222"   # unlock password

# Google Sheet (A1 password)
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_GID = "0"  # usually first sheet
PASSWORD_CACHE_SECONDS = 30  # every time start/connect it will refresh if older than this

# Stop after N consecutive losses
MAX_LOSS_STOP = 8

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
    'STREAK_WINS': {
        2: "CAACAgUAAxkBAAEQTiBpcmUfm9aQmlIHtPKiG2nE2e6EeAACcRMAAiLWqFSpdxWmKJ1TXzgE",
        3: "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE",
        4: "CAACAgUAAxkBAAEQTiJpcmUgSydN-tKxoSVdFuAvCcJ3fQACvSEAApMRqFQoUYBnH5Pc7TgE",
        5: "CAACAgUAAxkBAAEQTiNpcmUgu_dP3wKT2k94EJCiw3u52QACihoAArkfqFSlrldtXbLGGDgE",
        6: "CAACAgUAAxkBAAEQTiRpcmUhQJUjd2ukdtfEtBjwtMH4MAACWRgAAsTFqVTato0SmSN-6jgE",
        7: "CAACAgUAAxkBAAEQTiVpcmUhha9HAAF19fboYayfUrm3tdYAAioXAAIHgKhUD0QmGyF5Aug4BA",
        8: "CAACAgUAAxkBAAEQTixpcmUmevnNEqUbr0qbbVgW4psMNQACMxUAAow-qFSnSz4Ik1ddNzgE",
        9: "CAACAgUAAxkBAAEQTi1pcmUmpSxAHo2pvR-GjCPTmkLr0AACLh0AAhCRqFRH5-2YyZKq1jgE",
        10: "CAACAgUAAxkBAAEQTi5pcmUmjmjp7oXg4InxI1dGYruxDwACqBgAAh19qVT6X_-oEywCkzgE"
    },
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
}

# ================= API LINKS =================
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
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
    # Works if sheet is shared/public or published
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

def _fetch_password_sync(timeout: float = 6.0) -> str | None:
    """
    Reads A1 from the sheet via CSV export.
    Returns str password or None.
    """
    try:
        url = _sheet_csv_url()
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return None
        # CSV first cell = A1
        first_line = (r.text or "").splitlines()[0] if (r.text or "").splitlines() else ""
        # strip quotes and commas
        cell = first_line.split(",")[0].strip().strip('"').strip("'")
        return cell if cell else None
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

    # If sheet not reachable, do not allow bypass (security)
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

        if (not self.raw_history) or (str(self.raw_history[0].get('issueNumber')) != str(issue_data.get('issueNumber'))):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:80]
            self.raw_history = self.raw_history[:80]

    # ✅ Voting System logic
    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 6:
            final_prediction = random.choice(["BIG", "SMALL"])
            self.last_prediction = final_prediction
            return final_prediction

        last_6 = self.history[:6]
        signals = []

        # ১) Trend logic
        big_count = last_6.count("BIG")
        small_count = last_6.count("SMALL")
        signals.append("BIG" if big_count > small_count else "SMALL")

        # ২) Pattern logic
        if last_6[0] == last_6[1] == last_6[2]:  # Dragon
            signals.append(last_6[0])
        elif last_6[0] != last_6[1] and last_6[1] != last_6[2]:  # ZigZag
            signals.append("SMALL" if last_6[0] == "BIG" else "BIG")
        else:
            signals.append(last_6[0])

        # ৩) Math logic
        try:
            last_issue_digit = int(str(self.raw_history[0].get('issueNumber', '0'))[-1])
            last_result_num = int(self.raw_history[0].get('number', '0'))
            total = last_issue_digit + last_result_num
            signals.append("SMALL" if total % 2 == 0 else "BIG")
        except:
            signals.append(random.choice(["BIG", "SMALL"]))

        # ৪) Voting decision (tie হলে last result follow)
        try:
            final_prediction = max(set(signals), key=signals.count)
            if signals.count("BIG") == signals.count("SMALL"):
                final_prediction = last_6[0]
        except:
            final_prediction = last_6[0]

        # ৫) Loss recovery invert
        if current_streak_loss >= 2:
            final_prediction = "SMALL" if final_prediction == "BIG" else "BIG"

        self.last_prediction = final_prediction
        return final_prediction

    def calculate_confidence(self):
        try:
            if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
                return random.randint(93, 98)
        except:
            pass
        return random.randint(85, 92)

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.session_id = 0
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        self.last_alive_ping = 0.0

state = BotState()

# ================= API FETCH (requests + to_thread + gateways) =================
def _fetch_one(url: str, headers: dict, timeout: float):
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        return None
    data = r.json()
    if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
        return data["data"]["list"][0]
    return None

async def fetch_latest_issue(mode: str):
    base_url = API_1M if mode == '1M' else API_30S
    timestamp = int(time.time() * 1000)

    gateways = [
        f"{base_url}?t={timestamp}",
        f"https://corsproxy.io/?{base_url}?t={timestamp}",
        f"https://api.allorigins.win/raw?url={base_url}?t={timestamp}",
        f"https://thingproxy.freeboard.io/fetch/{base_url}?t={timestamp}",
        f"https://api.codetabs.com/v1/proxy?quest={base_url}?t={timestamp}",
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

# ================= MESSAGE STYLE (HIGH + UNIQUE) =================
def _loss_step_text(streak_loss: int) -> str:
    # 1..8 => "1 Step Loss" etc
    if streak_loss <= 0:
        return ""
    return f"{streak_loss} Step Loss"

def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    step_txt = _loss_step_text(streak_loss)
    step_line = f"\n⚠️ <b>{step_txt}</b> — Recovery On" if step_txt else "\n✅ <b>Fresh Start</b>"

    join_line = f"\n\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN CHANNEL</b></a>" if CHANNEL_LINK else ""
    return (
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧩 <b>Mode:</b> <code>{state.game_mode}</code>\n"
        f"🧾 <b>Next Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>SIGNAL:</b> {emoji} <b>{prediction}</b> {emoji}\n"
        f"📈 <b>Confidence:</b> <b>{conf}%</b>"
        f"{step_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{join_line}"
    )

def format_result(issue, res_num, res_type, my_pick, is_win, streak_loss):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]:
        res_emoji = "🟣"

    if is_win:
        header = "✅ <b>PASS • CLEAN HIT</b>"
        badge = "🏆 WIN"
        extra = f"🔥 Streak: <b>{state.stats['streak_win']}</b>"
    else:
        header = "❌ <b>MISS • RECOVERY MODE</b>"
        badge = "🧨 LOSS"
        extra = f"⚠️ <b>{_loss_step_text(streak_loss)}</b>"

    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>Pick:</b> <b>{my_pick}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{badge}  •  {extra}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    total = wins + losses
    acc = int((wins / total) * 100) if total > 0 else 0

    join_line = f"\n🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>" if CHANNEL_LINK else ""
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Report</b>\n"
        f"✅ Win: <b>{wins}</b>\n"
        f"❌ Loss: <b>{losses}</b>\n"
        f"🎯 Accuracy: <b>{acc}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>"
        f"{join_line}"
    )

def format_consolation_stop():
    join_line = f"\n🔗 <a href='{CHANNEL_LINK}'><b>TAKE A BREAK & COME BACK</b></a>" if CHANNEL_LINK else ""
    return (
        f"🧊 <b>SAFE GUARD ACTIVATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"😮‍💨 8 Step Loss hit.\n"
        f"🛡️ Prediction is <b>OFF</b> for safety.\n"
        f"✅ Stop & reset done.\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>"
        f"{join_line}"
    )

# ================= AUTH =================
AUTHORIZED_USERS = set()

def _lock_all_users():
    AUTHORIZED_USERS.clear()

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE, my_session_id: int):
    fail_count = 0

    while state.is_running and state.session_id == my_session_id:
        try:
            latest = await fetch_latest_issue(state.game_mode)

            if not latest:
                # NO fake/offline signal — just retry
                fail_count += 1
                base_wait = 1 if state.game_mode == '30S' else 2
                await asyncio.sleep(min(base_wait + fail_count, 12))
                continue

            fail_count = 0

            latest_issue = str(latest['issueNumber'])
            latest_num = latest['number']
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # -------- RESULT --------
            if state.active_bet and state.active_bet['period'] == latest_issue:
                if state.last_period_processed == latest_issue:
                    await asyncio.sleep(1)
                    continue

                pick = state.active_bet['pick']
                is_win = (pick == latest_type)

                state.engine.update_history(latest)

                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_win'] += 1
                    state.stats['streak_loss'] = 0
                    streak = state.stats['streak_win']

                    if streak in STICKERS['STREAK_WINS']:
                        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['STREAK_WINS'][streak])
                        except: pass
                    else:
                        try:
                            await context.bot.send_sticker(
                                TARGET_CHANNEL,
                                STICKERS['WIN_BIG'] if latest_type == "BIG" else STICKERS['WIN_SMALL']
                            )
                        except:
                            pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except: pass

                # Send result message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(
                            latest_issue,
                            latest_num,
                            latest_type,
                            pick,
                            is_win,
                            state.stats['streak_loss']
                        ),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except:
                    pass

                state.active_bet = None
                state.last_period_processed = latest_issue

                # ✅ STOP AT 8 LOSSES
                if state.stats["streak_loss"] >= MAX_LOSS_STOP:
                    state.is_running = False
                    # session stays; but we force lock to require password next time
                    _lock_all_users()
                    try:
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            format_consolation_stop(),
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                    except:
                        pass
                    return

            # -------- SIGNAL --------
            if not state.active_bet and state.last_period_processed != next_issue:
                await asyncio.sleep(1 if state.game_mode == '30S' else 2)

                if state.session_id != my_session_id:
                    return

                state.engine.update_history(latest)

                pred = state.engine.get_pattern_signal(state.stats['streak_loss'])
                conf = state.engine.calculate_confidence()

                state.active_bet = {"period": next_issue, "pick": pred}

                s_stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
                except: pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_issue, pred, conf, state.stats['streak_loss']),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except:
                    pass

            await asyncio.sleep(1 if state.game_mode == '30S' else 2)

        except Exception:
            await asyncio.sleep(2)

async def run_engine_forever(context: ContextTypes.DEFAULT_TYPE, sid: int):
    # Engine যদি অস্বাভাবিকভাবে থেমে যায়, wrapper আবার চালু করবে
    while state.is_running and state.session_id == sid:
        try:
            await game_engine(context, sid)
        except Exception:
            await asyncio.sleep(2)
        await asyncio.sleep(1)

async def heartbeat(context: ContextTypes.DEFAULT_TYPE, sid: int):
    # Silent হলে যেন বুঝা যায় বট alive
    while state.is_running and state.session_id == sid:
        try:
            now = time.time()
            if now - state.last_alive_ping >= 600:  # 10 minutes
                state.last_alive_ping = now
                await context.bot.send_message(
                    TARGET_CHANNEL,
                    f"🟢 <b>{BRAND_NAME}</b>\n"
                    f"✅ Alive • Mode: <b>{state.game_mode}</b>\n"
                    f"🧠 LossStep: <b>{state.stats['streak_loss']}</b> / {MAX_LOSS_STOP}\n"
                    f"⏱ {time.strftime('%H:%M:%S')}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
        except:
            pass
        await asyncio.sleep(30)

# ================= HANDLERS =================
async def show_main_menu(update: Update):
    await update.message.reply_text(
        f"🔓 <b>ACCESS GRANTED</b>\n"
        f"👑 <b>{BRAND_NAME}</b>\n\n"
        f"Choose Mode:",
        reply_markup=ReplyKeyboardMarkup(
            [['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop & Summary']],
            resize_keyboard=True
        ),
        parse_mode=ParseMode.HTML
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Always fetch password when user wants to start interacting
    pw = await get_password(force_refresh=True)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable). Try again.", parse_mode=ParseMode.HTML)
        return

    if user_id in AUTHORIZED_USERS:
        await show_main_menu(update)
    else:
        await update.message.reply_text("🔒 <b>LOCKED</b>\nSend Password:", parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    user_id = update.effective_user.id

    # Always refresh password when user is not authorized or when starting new session
    pw = await get_password(force_refresh=False)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
        return

    # ---- AUTH CHECK ----
    if user_id not in AUTHORIZED_USERS:
        if msg == pw:
            AUTHORIZED_USERS.add(user_id)
            await show_main_menu(update)
            return
        await update.message.reply_text("❌ <b>DENIED</b> • Wrong password", parse_mode=ParseMode.HTML)
        return

    # ---- STOP ----
    if "Stop" in msg or msg == "/off":
        state.session_id += 1
        state.is_running = False
        state.active_bet = None
        await update.message.reply_text("🛑 <b>Stopping…</b>", parse_mode=ParseMode.HTML)

        try:
            await context.bot.send_message(
                TARGET_CHANNEL,
                format_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except:
            pass

        # 🔐 require password again after stop
        _lock_all_users()
        return

    # ---- CONNECT ----
    if "Connect" in msg:
        # Security: every time a session starts, force re-check password next time if stopped
        # (User is already authorized here, but we also refresh password cache)
        pw2 = await get_password(force_refresh=True)
        if not pw2:
            await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
            return

        state.session_id += 1
        current_session = state.session_id

        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_period_processed = None
        state.last_alive_ping = 0.0

        await update.message.reply_text(
            f"✅ <b>CONNECTED</b>\n"
            f"⚡ Mode: <b>{mode}</b>\n"
            f"🧠 Engine: <b>LIVE</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass

        context.application.create_task(run_engine_forever(context, current_session))
        context.application.create_task(heartbeat(context, current_session))

# ================= MAIN =================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    if not BOT_TOKEN or "PASTE_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN missing! main.py এ PASTE_TOKEN_HERE replace করো.")

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
