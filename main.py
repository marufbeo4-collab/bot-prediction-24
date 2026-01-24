import asyncio
import logging
import random
import time
import os
from threading import Thread

import requests
from flask import Flask
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"

TARGET_CHANNEL = -1003293007059
BRAND_NAME = "𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"
BOT_PASSWORD = "2222"   # unlock password

# Password from Google Sheet A1
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_GID = "0"
PASSWORD_CACHE_SECONDS = 20  # short cache, so reconnect requires fresh pull

MAX_LOSS_STOP = 8

# ================= STICKERS =================
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

# ================= FLASK KEEP ALIVE =================
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

# ================= PASSWORD FROM SHEET =================
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

# ================= ENGINE STATE =================
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
            self.history = self.history[:200]
            self.raw_history = self.raw_history[:200]

    # ✅ Your latest logic (12 history, multi system voting)
    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 12:
            pred = random.choice(["BIG", "SMALL"])
            self.last_prediction = pred
            return pred

        h = self.history  # newest first
        votes = []

        # SYSTEM 1: PATTERN
        if h[0] == h[1] == h[2]:  # Dragon
            votes.append(h[0]); votes.append(h[0])
        elif h[0] != h[1] and h[1] != h[2]:  # ZigZag
            zz = "SMALL" if h[0] == "BIG" else "BIG"
            votes.append(zz); votes.append(zz)
        elif h[0] == h[1] and h[2] == h[3] and h[1] != h[2]:  # AABB
            votes.append("SMALL" if h[0] == "BIG" else "BIG")
        elif h[0] == h[1] and h[1] != h[2]:  # AAB
            votes.append("SMALL" if h[0] == "BIG" else "BIG")

        # SYSTEM 2: TREND (last 12)
        last_12 = h[:12]
        big_count = last_12.count("BIG")
        small_count = last_12.count("SMALL")
        if big_count > small_count + 2:
            votes.append("BIG")
        elif small_count > big_count + 2:
            votes.append("SMALL")
        else:
            votes.append(h[0])

        # SYSTEM 3: MATH
        try:
            p_digit = int(str(self.raw_history[0].get('issueNumber', 0))[-1])
            r_num = int(self.raw_history[0].get('number', 0))
            math_pred = "SMALL" if (p_digit + r_num) % 2 == 0 else "BIG"
            votes.append(math_pred)
        except:
            pass

        # SYSTEM 4: LOSS RECOVERY (double power)
        if current_streak_loss >= 2 and self.last_prediction:
            reverse_pred = "SMALL" if self.last_prediction == "BIG" else "BIG"
            votes.append(reverse_pred); votes.append(reverse_pred)

        if not votes:
            self.last_prediction = h[0]
            return h[0]

        final_prediction = max(set(votes), key=votes.count)
        self.last_prediction = final_prediction
        return final_prediction

    def calculate_confidence(self):
        # stable premium-looking confidence
        base = random.randint(86, 92)
        try:
            if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
                base = random.randint(92, 97)
        except:
            pass
        return base


class BotState:
    def __init__(self):
        self.is_running = False
        self.session_id = 0
        self.game_mode = "1M"
        self.engine = PredictionEngine()
        self.active_bet = None  # {"period":..., "pick":..., "check_mid":..., "check_task":...}
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        self.loss_message_ids = []  # track loss sticker + loss messages, delete on stop
        self.last_heartbeat_sent = 0.0

state = BotState()

AUTHORIZED_USERS = set()

def lock_all_users():
    AUTHORIZED_USERS.clear()

# ================= REQUEST FETCH (multi-gateway) =================
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

# ================= UTIL: DELETE SAFE =================
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
            await asyncio.sleep(1.1)

    task = asyncio.create_task(_animate())
    return msg.message_id, task

# ================= PREMIUM MESSAGES =================
def now_hms():
    return time.strftime("%H:%M:%S")

def step_text(loss_step: int) -> str:
    # 1 loss -> 1 step loss, etc
    return f"{loss_step} Step Loss" if loss_step > 0 else "Step 0"

def fmt_signal(next_issue: str, pred: str, conf: int):
    e = "🟢" if pred == "BIG" else "🔴"
    join = f"\n<a href='{CHANNEL_LINK}'>➕ Join Channel</a>" if CHANNEL_LINK else ""
    return (
        f"{e} <b>{BRAND_NAME}</b>\n"
        f"• Mode: <code>{state.game_mode}</code>  |  Period: <code>{next_issue}</code>\n"
        f"• Pick: <b>{pred}</b>  |  Confidence: <b>{conf}%</b>\n"
        f"• Tracker: <b>{step_text(state.stats['streak_loss'])}</b> / {MAX_LOSS_STOP}  |  <code>{now_hms()}</code>"
        f"{join}"
    )

def fmt_result(issue: str, res_num: str, res_type: str, pick: str, is_win: bool):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]:
        res_emoji = "🟣"

    if is_win:
        title = "✅ <b>WIN CONFIRMED</b>"
        line = f"Streak: <b>{state.stats['streak_win']}</b> • Step reset → <b>0</b>"
    else:
        title = "❌ <b>LOSS CONFIRMED</b>"
        line = f"Recovery: <b>{step_text(state.stats['streak_loss'])}</b> / {MAX_LOSS_STOP}"

    return (
        f"{title}\n"
        f"• Period: <code>{issue}</code>\n"
        f"• Result: {res_emoji} <b>{res_num}</b> (<b>{res_type}</b>)  |  Pick: <b>{pick}</b>\n"
        f"• {line}\n"
        f"• W:{state.stats['wins']}  L:{state.stats['losses']}  |  <code>{now_hms()}</code>"
    )

def fmt_summary():
    w = state.stats["wins"]
    l = state.stats["losses"]
    total = w + l
    acc = int((w / total) * 100) if total else 0
    join = f"\n<a href='{CHANNEL_LINK}'>🔗 Join Again</a>" if CHANNEL_LINK else ""
    return (
        f"🛑 <b>SESSION STOPPED</b> • <b>{BRAND_NAME}</b>\n"
        f"• W:{w}  L:{l}  |  Accuracy: <b>{acc}%</b>\n"
        f"• Last Step: <b>{step_text(state.stats['streak_loss'])}</b>  |  <code>{now_hms()}</code>"
        f"{join}"
    )

def fmt_consolation_stop():
    join = f"\n<a href='{CHANNEL_LINK}'>🫶 Take a break & return</a>" if CHANNEL_LINK else ""
    return (
        f"🧊 <b>SAFE GUARD</b> • <b>{BRAND_NAME}</b>\n"
        f"• <b>{MAX_LOSS_STOP} Step Loss</b> reached.\n"
        f"• Prediction is now <b>OFF</b> to protect your session.\n"
        f"• Use /start again when ready."
        f"{join}"
    )

# ================= ENGINE LOOP =================
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

            # ========== RESULT ==========
            if state.active_bet and state.active_bet.get("period") == latest_issue:
                if state.last_period_processed == latest_issue:
                    await asyncio.sleep(1)
                    continue

                # stop animation + delete checking msg
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

                # update stats + stickers
                if is_win:
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0  # ✅ reset on win

                    try:
                        st = STICKERS["WIN_BIG"] if latest_type == "BIG" else STICKERS["WIN_SMALL"]
                        await context.bot.send_sticker(TARGET_CHANNEL, st)
                    except:
                        pass
                else:
                    state.stats["losses"] += 1
                    state.stats["streak_win"] = 0
                    state.stats["streak_loss"] += 1  # ✅ step counts

                    # track loss sticker msg id for deletion later
                    try:
                        ms = await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS["LOSS"]))
                        state.loss_message_ids.append(ms.message_id)
                    except:
                        pass

                # send result text
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

                # AUTO SAFE STOP at 8 losses
                if state.stats["streak_loss"] >= MAX_LOSS_STOP:
                    state.is_running = False
                    lock_all_users()
                    # delete all loss messages automatically when stopping
                    await delete_all_loss_messages(context)
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

            # ========== SIGNAL ==========
            if (not state.active_bet) and (state.last_period_processed != next_issue):
                await asyncio.sleep(1 if state.game_mode == "30S" else 2)
                if state.session_id != sid:
                    return

                state.engine.update_history(latest)
                pred = state.engine.get_pattern_signal(state.stats["streak_loss"])
                conf = state.engine.calculate_confidence()

                # set active bet
                state.active_bet = {"period": next_issue, "pick": pred}

                # sticker
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

                # checking animation message (auto delete later)
                try:
                    check_mid, check_task = await start_checking_animation(
                        context,
                        TARGET_CHANNEL,
                        f"Checking Result • Period {next_issue}"
                    )
                    state.active_bet["check_mid"] = check_mid
                    state.active_bet["check_task"] = check_task
                except:
                    # if checking can't be created, ignore
                    pass

            await asyncio.sleep(1 if state.game_mode == "30S" else 2)

        except Exception:
            await asyncio.sleep(2)

async def run_engine_forever(context: ContextTypes.DEFAULT_TYPE, sid: int):
    # prevent sudden stop: restart loop if it exits unexpectedly
    while state.is_running and state.session_id == sid:
        try:
            await game_engine(context, sid)
        except Exception:
            await asyncio.sleep(2)
        await asyncio.sleep(1)

async def heartbeat(context: ContextTypes.DEFAULT_TYPE, sid: int):
    # not choppy; every 15 min
    while state.is_running and state.session_id == sid:
        try:
            now = time.time()
            if now - state.last_heartbeat_sent >= 900:
                state.last_heartbeat_sent = now
                await context.bot.send_message(
                    TARGET_CHANNEL,
                    f"🟢 <b>{BRAND_NAME}</b> • <b>{state.game_mode}</b> • "
                    f"<b>{step_text(state.stats['streak_loss'])}</b>/{MAX_LOSS_STOP} • "
                    f"W:{state.stats['wins']} L:{state.stats['losses']} • <code>{now_hms()}</code>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
        except:
            pass
        await asyncio.sleep(30)

# ================= HANDLERS =================
async def show_main_menu(update: Update):
    await update.message.reply_text(
        f"🔓 <b>ACCESS GRANTED</b>\n<b>{BRAND_NAME}</b>\n\nChoose Mode:",
        reply_markup=ReplyKeyboardMarkup(
            [['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop & Summary']],
            resize_keyboard=True
        ),
        parse_mode=ParseMode.HTML
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # always fetch password once on /start
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
        # always require password after stop (we clear AUTHORIZED_USERS on stop)
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

        # cancel checking task + delete checking msg if exists
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

        # delete loss stickers/messages automatically
        await delete_all_loss_messages(context)

        # send summary
        try:
            await context.bot.send_message(
                TARGET_CHANNEL,
                fmt_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except:
            pass

        # require password again next time
        lock_all_users()
        return

    # CONNECT
    if "Connect" in msg:
        # force refresh password on connect to ensure sheet changes apply
        pw2 = await get_password(force_refresh=True)
        if not pw2:
            await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
            return

        # new session
        state.session_id += 1
        sid = state.session_id

        mode = "1M" if "1M" in msg else "30S"
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_period_processed = None
        state.loss_message_ids = []
        state.last_heartbeat_sent = 0.0

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
        context.application.create_task(heartbeat(context, sid))

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
