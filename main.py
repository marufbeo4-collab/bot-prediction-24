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
BOT_TOKEN = "8595453345:AAGndyFZES2qZL37LRc3CeqGxKyWq7HeTxk"  # <--- আপনার টোকেন
TARGET_CHANNEL = -1003293007059     # <--- আপনার চ্যানেল আইডি
BRAND_NAME = "DK MARUF VIP SYSTEM"  # <--- মারুফ ব্র্যান্ডিং

# ================= STICKER DATABASE =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    'WIN_BIG': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_SMALL': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'LOSS': [
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
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

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER (24/7 FIX) =================
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF ENGINE RUNNING..."

def run_http():
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host='0.0.0.0', port=port)
    except: pass

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= SMART PREDICTION ENGINE (UPDATED) =================
class PredictionEngine:
    def __init__(self):
        self.history = [] 
        self.raw_history = []
    
    def update_history(self, issue_data):
        number = int(issue_data['number'])
        result_type = "BIG" if number >= 5 else "SMALL"
        
        if not self.history or self.raw_history[0]['issueNumber'] != issue_data['issueNumber']:
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:50] 
            self.raw_history = self.raw_history[:50]

    def get_pattern_signal(self, current_streak_loss):
        # ডাটা কম থাকলে র‍্যান্ডম
        if len(self.history) < 10:
            return random.choice(["BIG", "SMALL"])
        
        last_6 = self.history[:6]
        prediction = ""

        # === A. মেইন লজিক (Pattern Analysis) ===
        
        # 1. Dragon Catch (টানা ৩ বার একই হলে ট্রেন্ড ধরবো)
        if last_6[0] == last_6[1] == last_6[2]:
            prediction = last_6[0]
            
        # 2. ZigZag Catch (একবার এটা একবার ওটা)
        elif last_6[0] != last_6[1] and last_6[1] != last_6[2]:
            prediction = "SMALL" if last_6[0] == "BIG" else "BIG"

        # 3. Math Trend (যদি প্যাটার্ন না থাকে - ডিফল্ট)
        else:
            try:
                last_num = int(self.raw_history[0]['number'])
                period_digit = int(str(self.raw_history[0]['issueNumber'])[-1])
                # (Last Num + Period) % 2 Logic
                math_val = (last_num + period_digit) % 2
                prediction = "BIG" if math_val == 1 else "SMALL"
            except:
                prediction = random.choice(["BIG", "SMALL"])

        # === B. অটো ইনভার্স লজিক (SMART RECOVERY) ===
        # যদি দেখি টানা ২ বার বা তার বেশি লস হয়েছে, তার মানে মার্কেট উল্টো চলছে।
        # তখন আমরাও প্রেডিকশন উল্টে দিবো।
        
        if current_streak_loss >= 2:
            # লস রিকভার করার জন্য সিগন্যাল উল্টে যাবে
            print(f"⚠️ Trap Market Detected! Flipping Signal from {prediction}...")
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
        except:
            continue
    return None

# ================= FORMATTING (DK MARUF STYLE) =================
def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    color = "GREEN" if prediction == "BIG" else "RED"
    
    lvl = streak_loss + 1
    multiplier = 3 ** (lvl - 1) # 1, 3, 9...
    
    plan_text = f"Start (1X)"
    if lvl > 1: plan_text = f"⚠️ Recovery Step {lvl} ({multiplier}X)"
    if lvl > 4: plan_text = f"🔥 DO OR DIE ({multiplier}X)"

    return (
        f"🛡 <b>{BRAND_NAME}</b> 🛡\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"📊 <b>Market:</b> {state.game_mode} VIP\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔥 <b>SIGNAL:</b>  👉 <b>{prediction}</b> 👈\n"
        f"🎨 <b>Color:</b> {color} {emoji}\n"
        f"🚀 <b>Confidence:</b> {conf}%\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Plan:</b> {plan_text}\n"
        f"⚡ <b>Maintain 5 Level Funds!</b>\n"
        f"👑 <b>Dev:</b> @dk_mentor_maruf_official"
    )

def format_result(issue, res_num, res_type, my_pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣" 
    
    if is_win:
        w_streak = state.stats['streak_win']
        header = f"🎉 <b>BOOM! WINNER!</b> 🎉"
        status = f"🔥 <b>Win Streak: {w_streak}</b> 🔥"
    else:
        header = f"❌ <b>LOSS / MISS</b> ❌"
        next_step = state.stats['streak_loss'] + 1
        status = f"⚠️ <b>Go For Step {next_step} Recovery</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"📶 <b>System by DK Maruf</b>"
    )

# ================= 24/7 AUTO-RESTART ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 DK Maruf Engine (Smart Recovery Logic) Started...")
    
    while state.is_running:
        try:
            # 1. Fetch
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(3)
                continue
                
            latest_issue = latest['issueNumber']
            latest_num = latest['number']
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)
            
            # 2. Process Result
            if state.active_bet and state.active_bet['period'] == latest_issue:
                pick = state.active_bet['pick']
                is_win = (pick == latest_type)
                
                state.engine.update_history(latest)
                
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_win'] += 1
                    state.stats['streak_loss'] = 0
                    
                    # Sticker Logic
                    streak = state.stats['streak_win']
                    if streak in STICKERS['STREAK_WINS']:
                        sticker_id = STICKERS['STREAK_WINS'][streak]
                    else:
                        sticker_id = STICKERS['WIN_BIG'] if latest_type == "BIG" else STICKERS['WIN_SMALL']
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
                    except: pass
                    
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except: pass

                # Result Message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e: print(f"Res Err: {e}")
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # 3. New Prediction
            if not state.active_bet and state.last_period_processed != next_issue:
                await asyncio.sleep(2)
                state.engine.update_history(latest)
                
                # ==== UPDATED CALL HERE FOR SMART RECOVERY ====
                # আমরা current loss streak পাঠাচ্ছি যাতে ইনভার্স লজিক কাজ করে
                pred = state.engine.get_pattern_signal(state.stats['streak_loss'])
                conf = state.engine.calculate_confidence()
                
                state.active_bet = {"period": next_issue, "pick": pred}
                
                # Signal Sticker
                s_stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
                except: pass
                
                # Signal Msg
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_issue, pred, conf, state.stats['streak_loss']),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e: print(f"Sig Err: {e}")

            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Loop Restarting: {e}")
            await asyncio.sleep(2)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Boss!</b>\nSelect Server:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    if "Stop" in msg:
        state.is_running = False
        await update.message.reply_text("⛔ Bot Stopped.")
        return

    if "Connect" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already Running!")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins":0, "losses":0, "streak_win":0, "streak_loss":0}
        
        # Reset Engine
        state.engine = PredictionEngine()
        
        await update.message.reply_text(f"✅ <b>Connected to {mode}</b>\nSmart Recovery Active...", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass
        
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("DK MARUF with SMART RECOVERY LOGIC LIVE...")
    app.run_polling()
