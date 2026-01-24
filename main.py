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
# ⚠️ Public GitHub এ commit করলে token leak হবে. Private repo best.
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"

TARGET_CHANNEL = -1003293007059
BRAND_NAME = "𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"
BOT_PASSWORD = "2222"   # unlock password

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

# ================= FLASK SERVER (KEEP ALIVE) =================
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
        self.history = []       # ["BIG","SMALL"...]
        self.raw_history = []   # raw issues list
        self.last_prediction = None  # ✅ NEW (for anti-trap)

    def update_history(self, issue_data):
        """
        issue_data: {"issueNumber":..., "number":...}
        newest first রাখে, duplicate avoid করে।
        """
        try:
            number = int(issue_data['number'])
            result_type = "BIG" if number >= 5 else "SMALL"
        except Exception:
            return

        # duplicate avoid (same issueNumber)
        if (not self.raw_history) or (str(self.raw_history[0].get('issueNumber')) != str(issue_data.get('issueNumber'))):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)

            self.history = self.history[:60]
            self.raw_history = self.raw_history[:60]

    # ✅ তোমার দেওয়া prediction logic
    def get_pattern_signal(self, current_streak_loss: int):
        # ইতিহাস খুব ছোট হলে র‍্যান্ডম দিবে
        if len(self.history) < 5:
            prediction = random.choice(["BIG", "SMALL"])
            self.last_prediction = prediction
            return prediction

        last_6 = self.history[:6]  # গত ৬টি রেজাল্ট
        prediction = None

        # =========================================
        # 🛡️ লজিক ১: ANTI-TRAP (লস রিকভারি সিস্টেম)
        # =========================================
        if current_streak_loss >= 2:
            if self.last_prediction == "BIG":
                prediction = "SMALL"
            elif self.last_prediction == "SMALL":
                prediction = "BIG"
            else:
                prediction = "SMALL" if last_6[0] == "BIG" else "BIG"

            self.last_prediction = prediction
            return prediction

        # =========================================
        # 🐉 লজিক ২: DRAGON / STREAK (টানা একই আসলে)
        # =========================================
        if len(last_6) >= 3 and (last_6[0] == last_6[1] == last_6[2]):
            prediction = last_6[0]

        # =========================================
        # ⚡ লজিক ৩: ZIG-ZAG
        # =========================================
        elif len(last_6) >= 3 and (last_6[0] != last_6[1]) and (last_6[1] != last_6[2]):
            prediction = "SMALL" if last_6[0] == "BIG" else "BIG"

        # =========================================
        # 🎲 লজিক ৪: TWO-TWO
        # =========================================
        elif len(last_6) >= 3 and (last_6[0] == last_6[1]) and (last_6[2] != last_6[0]):
            prediction = last_6[0]

        # =========================================
        # 🧮 লজিক ৫: MATH FALLBACK
        # =========================================
        else:
            try:
                last_num = int(self.raw_history[0]['number'])
                period_last_digit = int(str(self.raw_history[0]['issueNumber'])[-1])
                total = last_num + period_last_digit

                prediction = "SMALL" if (total % 2 == 0) else "BIG"
            except:
                prediction = random.choice(["BIG", "SMALL"])

        self.last_prediction = prediction
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
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}

state = BotState()

# ================= REQUESTS + MULTI-GATEWAY (ANTI BLOCK) =================
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
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(110, 123)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
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
    if int(res_num) in [0, 5]:
        res_emoji = "🟣"

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

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE, my_session_id: int):
    print(f"🚀 {BRAND_NAME} Engine Started (Session: {my_session_id})...")

    fail_count = 0

    while state.is_running and state.session_id == my_session_id:
        try:
            latest = await fetch_latest_issue(state.game_mode)

            if not latest:
                # ✅ NO OFFLINE/AUTO SIGNAL — শুধু retry
                fail_count += 1
                base_wait = 1 if state.game_mode == '30S' else 2
                await asyncio.sleep(min(base_wait + fail_count, 10))
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

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except:
                    pass

                state.active_bet = None
                state.last_period_processed = latest_issue

            # -------- SIGNAL --------
            if not state.active_bet and state.last_period_processed != next_issue:
                buffer_time = 1 if state.game_mode == '30S' else 2
                await asyncio.sleep(buffer_time)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        try:
            await context.bot.send_message(TARGET_CHANNEL, format_fake_summary(), parse_mode=ParseMode.HTML)
        except:
            pass
        return

    if "Connect" in msg:
        state.session_id += 1
        current_session = state.session_id

        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_period_processed = None

        await update.message.reply_text(
            f"✅ <b>Connected to {mode}</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass

        context.application.create_task(game_engine(context, current_session))

# ================= MAIN =================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    if not BOT_TOKEN or "PASTE_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN সেট করা হয়নি! main.py এ PASTE_TOKEN_HERE replace করো.")

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
