import asyncio
import logging
import random
import requests
import time
import os
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask

# ================= CONFIGURATION =================

BOT_TOKEN = "8595453345:AAGndyFZES2qZL37LRc3CeqGxKyWq7HeTxk"  # <-- আপনার টোকেন দিন
TARGET_CHANNEL = -1003293007059            # <-- আপনার চ্যানেল আইডি
BRAND_NAME = "𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋🌈™"         # <-- মারুফ ব্র্যান্ডিং

# (Optional) যদি তুমি ফরম্যাটে লিংক দিতে চাও
CHANNEL_LINK = "https://t.me/big_maruf_official0"

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

# ================= FLASK SERVER (24/7 FIX) =================

app = Flask('')

@app.route('/')
def home():
    return "DK MARUF ENGINE RUNNING..."

def run_http():
    # পোর্ট ফিক্স যাতে সার্ভার বন্ধ না করে দেয়
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception:
        pass

def keep_alive():
    t = Thread(target=run_http)
    t.daemon = True
    t.start()

# ================= PREDICTION LOGIC (SMART RECOVERY / AUTO-FLIP) =================
class PredictionEngine:
    def __init__(self):
        self.history = []
        self.raw_history = []

    def update_history(self, issue_data):
        number = int(issue_data['number'])
        result_type = "BIG" if number >= 5 else "SMALL"

        if (not self.raw_history) or (self.raw_history[0]['issueNumber'] != issue_data['issueNumber']):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:50]
            self.raw_history = self.raw_history[:50]

    # ✅ এখানে streak_loss ইনপুট নেয়
    def get_pattern_signal(self, current_streak_loss: int):
        # ডাটা কম থাকলে র‍্যান্ডম
        if len(self.history) < 10 or len(self.raw_history) < 1:
            return random.choice(["BIG", "SMALL"])

        last_6 = self.history[:6]
        prediction = None

        # === A) Main Pattern Logic ===

        # 1) Dragon: টানা ৩ বার একই -> trend follow
        if len(last_6) >= 3 and last_6[0] == last_6[1] == last_6[2]:
            prediction = last_6[0]

        # 2) ZigZag: একবার এটা একবার ওটা -> alternate
        elif len(last_6) >= 3 and (last_6[0] != last_6[1] and last_6[1] != last_6[2]):
            prediction = "SMALL" if last_6[0] == "BIG" else "BIG"

        # 3) Math Trend fallback
        else:
            last_num = int(self.raw_history[0]['number'])
            period_digit = int(str(self.raw_history[0]['issueNumber'])[-1])
            math_val = (last_num + period_digit) % 2
            prediction = "BIG" if math_val == 1 else "SMALL"

        # === B) Auto Inverse Logic (THE FIX) ===
        # টানা ২ বার লস হলে prediction উল্টে দিবে
        if current_streak_loss >= 2:
            return "SMALL" if prediction == "BIG" else "BIG"

        return prediction

    def calculate_confidence(self):
        return random.randint(90, 99)

# ================= BOT STATE =================

class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}

state = BotState()

# ================= API FETCH (ROBUST) =================

def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S

    proxies = [
        f"{base_url}?t={int(time.time()*1000)}",
        f"https://corsproxy.io/?{base_url}?t={int(time.time()*1000)}",
        f"https://api.allorigins.win/raw?url={base_url}",
        f"https://thingproxy.freeboard.io/fetch/{base_url}",
        f"https://api.codetabs.com/v1/proxy?quest={base_url}"
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(100, 120)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Origin": "https://dkwin9.com"
    }

    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except Exception:
            continue

    return None

# ================= FORMATTING (DK MARUF STYLE) =================

def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"

    lvl = streak_loss + 1
    multiplier = 3 ** (lvl - 1)  # 1, 3, 9...

    plan_text = "Start (1X)"
    if lvl > 1:
        plan_text = f"⚠️ Recovery Step {lvl} ({multiplier}X)"
    if lvl > 4:
        plan_text = f"🔥 DO OR DIE ({multiplier}X)"

    join_line = ""
    if CHANNEL_LINK:
        join_line = f"\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN VIP CHANNEL</b></a>"

    return (
        f"🛡 <b>{BRAND_NAME}</b> 🛡\n"
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

    join_line = ""
    if CHANNEL_LINK:
        join_line = f"\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN NEXT SESSION</b></a>"

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
BOT_PASSWORD = "2222"  # <-- চাইলে env থেকে নাও: os.environ.get("BOT_PASSWORD","2222")

# ================= ENGINE =================

async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 DK MARUF Engine Started...")

    while state.is_running:
        try:
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(3)
                continue

            latest_issue = latest['issueNumber']
            latest_num = latest['number']
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # Result
            if state.active_bet and state.active_bet['period'] == latest_issue:
                pick = state.active_bet['pick']
                is_win = (pick == latest_type)

                state.engine.update_history(latest)

                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_win'] += 1
                    state.stats['streak_loss'] = 0

                    streak = state.stats['streak_win']
                    if streak in STICKERS['STREAK_WINS']:
                        try:
                            await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['STREAK_WINS'][streak])
                        except Exception:
                            pass
                    else:
                        try:
                            await context.bot.send_sticker(
                                TARGET_CHANNEL,
                                STICKERS['WIN_BIG'] if latest_type == "BIG" else STICKERS['WIN_SMALL']
                            )
                        except Exception:
                            pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    try:
                        await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except Exception:
                        pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception:
                    pass

                state.active_bet = None
                state.last_period_processed = latest_issue

            # Signal
            if not state.active_bet and state.last_period_processed != next_issue:
                await asyncio.sleep(2)

                state.engine.update_history(latest)
                pred = state.engine.get_pattern_signal(state.stats['streak_loss'])
                conf = state.engine.calculate_confidence()

                state.active_bet = {"period": next_issue, "pick": pred}

                s_stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try:
                    await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
                except Exception:
                    pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_issue, pred, conf, state.stats['streak_loss']),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception:
                    pass

            await asyncio.sleep(2)

        except Exception as e:
            print(f"Loop Restarting: {e}")
            await asyncio.sleep(2)

# ================= HANDLERS =================

async def show_main_menu(update: Update):
    await update.message.reply_text(
        f"🔓 **Unlocked!**\n👑 **{BRAND_NAME}**\nSelect Server:",
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
        await update.message.reply_text(
            "🔒 <b>System Locked!</b>\nEnter Password:",
            parse_mode=ParseMode.HTML
        )

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
        state.is_running = False
        await update.message.reply_text("🛑 Stopping...", parse_mode=ParseMode.HTML)
        try:
            await context.bot.send_message(
                TARGET_CHANNEL,
                format_fake_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception:
            pass
        return

    if "Connect" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already Running!", parse_mode=ParseMode.HTML)
            return

        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        state.engine = PredictionEngine()

        await update.message.reply_text(
            f"✅ <b>Connected to {mode}</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        try:
            await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except Exception:
            pass

        context.application.create_task(game_engine(context))

# ================= MAIN =================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    print(f"{BRAND_NAME} 24/7 FIX LIVE...")
    app_telegram.run_polling()
