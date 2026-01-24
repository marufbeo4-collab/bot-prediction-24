import asyncio
import logging
import random
import time
import os
import httpx
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask

# ================= CONFIGURATION (ENV থেকে নিবে) =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
TARGET_CHANNEL = int(os.getenv("TARGET_CHANNEL", "0"))
BRAND_NAME = os.getenv("BRAND_NAME", "VIP BOT")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "2222")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing! Set it in Render Environment Variables.")

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
        10:"CAACAgUAAxkBAAEQTi5pcmUmjmjp7oXg4InxI1dGYruxDwACqBgAAh19qVT6X_-oEywCkzgE"
    },
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
}

# ================= API LINKS =================
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER (AUTO-WAKEUP) =================
app = Flask('')

@app.route('/')
def home():
    return f"{BRAND_NAME} IS ALIVE & RUNNING..."

@app.route('/health')
def health():
    return "ok"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    Thread(target=run_http, daemon=True).start()

# ================= PREDICTION ENGINE =================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.raw_history = []

    def update_history(self, issue_data):
        try:
            number = int(issue_data['number'])
            result_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        if (not self.raw_history) or (self.raw_history[0].get('issueNumber') != issue_data.get('issueNumber')):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:50]
            self.raw_history = self.raw_history[:50]

    def get_pattern_signal(self, current_streak_loss: int):
        if len(self.history) < 10:
            return random.choice(["BIG", "SMALL"])

        last_6 = self.history[:6]
        prediction = None

        if len(last_6) >= 3 and last_6[0] == last_6[1] == last_6[2]:
            prediction = last_6[0]
        elif len(last_6) >= 3 and (last_6[0] != last_6[1] and last_6[1] != last_6[2]):
            prediction = "SMALL" if last_6[0] == "BIG" else "BIG"
        else:
            try:
                last_num = int(self.raw_history[0]['number'])
                period = int(str(self.raw_history[0]['issueNumber'])[-1])
                calc = (last_num * 3 + period * 7) % 10
                prediction = "BIG" if calc >= 5 else "SMALL"
            except:
                prediction = random.choice(["BIG", "SMALL"])

        if int(current_streak_loss) >= 2:
            return "SMALL" if prediction == "BIG" else "BIG"
        return prediction

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
        self.last_seen_issue = None
        self.last_signal_time = 0.0
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}

state = BotState()

# ================= HTTP CLIENT REUSE =================
_http = None
def client():
    global _http
    if _http is None:
        _http = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
            headers={"Accept": "application/json"}
        )
    return _http

# ================= API FETCH (NEVER FREEZE) =================
async def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    ts = int(time.time() * 1000)

    gateways = [
        f"{base_url}?t={ts}",
        f"{base_url}?pageSize=10&t={ts}",
        f"https://api.allorigins.win/raw?url={base_url}?t={ts}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 Chrome/{random.randint(114, 122)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    c = client()
    for url in gateways:
        try:
            r = await c.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
                    return data["data"]["list"][0]
        except:
            continue
    return None

# ================= FORMATTING =================
def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    lvl = streak_loss + 1
    multiplier = 3 ** (lvl - 1)
    plan_text = "Start (1X)"
    if lvl > 1: plan_text = f"⚠️ Recovery Step {lvl} ({multiplier}X)"
    if lvl > 4: plan_text = f"🔥 DO OR DIE ({multiplier}X)"

    join_line = f"\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN VIP CHANNEL</b></a>" if CHANNEL_LINK else ""
    return (
        f" <b>{BRAND_NAME}</b> \n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Server:</b> {state.game_mode} VIP\n"
        f"🎲 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔮 <b>PREDICTION:</b> {emoji} <b>{prediction}</b> {emoji}\n"
        f"💣 <b>Confidence:</b> {conf}%\n"
        f"💰 <b>Bet:</b> {plan_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{join_line}"
    )

def format_result(issue, res_num, res_type, my_pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣"
    if is_win:
        header = "✅ <b>ＷＩＮ ＷＩＮ ＷＩＮ</b> ✅"
        status = "🔥 <b>PREDICTION PASSED</b>"
    else:
        header = "❌ <b>LOSS / MISS</b> ❌"
        next_step = state.stats['streak_loss'] + 1
        status = f"⚠️ <b>Go For Step {next_step} Recovery</b>"
    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎲 <b>Period:</b> <code>{issue}</code>\n"
        f"🎰 <b>Result:</b> {res_emoji} <b>{res_num} ({res_type})</b>\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{status}\n"
        f"👑 <b>{BRAND_NAME}</b>"
    )

def format_fake_summary():
    real_wins = state.stats['wins']
    real_losses = state.stats['losses']
    fake_wins = real_wins + random.randint(15, 25)
    fake_losses = 1 if real_losses > 3 else 0
    total = fake_wins + fake_losses
    accuracy = int((fake_wins / total) * 100) if total > 0 else 100
    join_line = f"\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN NEXT SESSION</b></a>" if CHANNEL_LINK else ""
    return (
        f"🛑 <b>SESSION CLOSED</b> 🛑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"📊 <b>FINAL REPORT:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>TOTAL WIN:</b> {fake_wins} ✅\n"
        f"🗑 <b>TOTAL LOSS:</b> {fake_losses} ❌\n"
        f"🎯 <b>ACCURACY:</b> {accuracy}% 🔥\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤑 <b>PROFIT:</b> MAX LEVEL"
        f"{join_line}"
    )

# ================= AUTH =================
AUTHORIZED_USERS = set()

# ================= WATCHDOG (signal যেন silent না থাকে) =================
async def watchdog(context: ContextTypes.DEFAULT_TYPE, sid: int):
    while state.is_running and state.session_id == sid:
        try:
            now = time.time()
            max_silence = 25 if state.game_mode == "30S" else 70
            if state.last_signal_time and (now - state.last_signal_time) > max_silence:
                fallback_issue = "AUTO"
                if state.last_seen_issue:
                    try: fallback_issue = str(int(state.last_seen_issue) + 1)
                    except: fallback_issue = state.last_seen_issue

                pred = random.choice(["BIG", "SMALL"])
                conf = random.randint(80, 90)

                if not state.active_bet:
                    state.active_bet = {"period": fallback_issue, "pick": pred}

                stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, stk)
                except: pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        f"⚠️ <b>API DELAY</b>\n🛡 Fallback signal (bot alive)\n\n" +
                        format_signal(fallback_issue, pred, conf, state.stats['streak_loss']),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except:
                    pass

                state.last_signal_time = now
        except:
            pass
        await asyncio.sleep(5)

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE, sid: int):
    fail_count = 0
    while state.is_running and state.session_id == sid:
        try:
            latest = await fetch_latest_issue(state.game_mode)

            if not latest:
                fail_count += 1
                base = 1 if state.game_mode == '30S' else 2
                await asyncio.sleep(min(base + fail_count, 10))
                continue

            fail_count = 0
            latest_issue = str(latest['issueNumber'])
            latest_num = latest['number']
            state.last_seen_issue = latest_issue

            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # Result
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
                        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN_BIG'] if latest_type == "BIG" else STICKERS['WIN_SMALL'])
                        except: pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except: pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except: pass

                state.active_bet = None
                state.last_period_processed = latest_issue

            # Signal
            if not state.active_bet and state.last_period_processed != next_issue:
                buffer_time = 1 if state.game_mode == '30S' else 2
                await asyncio.sleep(buffer_time)

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
                except: pass

                state.last_signal_time = time.time()

            await asyncio.sleep(1 if state.game_mode == '30S' else 2)

        except Exception:
            await asyncio.sleep(2)

# ================= HANDLERS =================
async def show_main_menu(update: Update):
    await update.message.reply_text(
        f"🔓 <b>Unlocked!</b>\n👑 <b>{BRAND_NAME}</b>\nSelect Server:",
        reply_markup=ReplyKeyboardMarkup(
            [['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop & Summary']],
            resize_keyboard=True
        ),
        parse_mode=ParseMode.HTML
    )

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        await show_main_menu(update)
    else:
        await update.message.reply_text("🔒 <b>System Locked!</b>\nEnter Password:", parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        if msg == BOT_PASSWORD:
            AUTHORIZED_USERS.add(user_id)
            await show_main_menu(update)
            return
        await update.message.reply_text("❌ <b>Wrong Password!</b>", parse_mode=ParseMode.HTML)
        return

    if "Stop" in msg or msg == "/off":
        state.session_id += 1
        state.is_running = False
        await update.message.reply_text("🛑 Stopping...", parse_mode=ParseMode.HTML)
        try: await context.bot.send_message(TARGET_CHANNEL, format_fake_summary(), parse_mode=ParseMode.HTML)
        except: pass
        return

    if "Connect" in msg:
        state.session_id += 1
        sid = state.session_id

        state.game_mode = '1M' if '1M' in msg else '30S'
        state.is_running = True
        state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_period_processed = None
        state.last_signal_time = time.time()
        state.last_seen_issue = None

        await update.message.reply_text(
            f"✅ <b>Connected to {state.game_mode}</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass

        context.application.create_task(game_engine(context, sid))
        context.application.create_task(watchdog(context, sid))

# ================= MAIN =================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start_cmd))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
