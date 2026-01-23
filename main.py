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
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- আপনার টোকেন বসান
TARGET_CHANNEL = -1003293007059     # <--- আপনার চ্যানেল আইডি

# ================= STICKER DATABASE (PREMIUM) =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    
    # সাধারণ উইন এবং লস
    'WIN_GENERIC': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'LOSS': [
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
        "CAACAgUAAxkBAAEQTh5pcmTbrSEe58RRXvtu_uwEAWZoQQAC5BEAArgxYVUhMlnBGKmcbzgE"
    ],
    
    # স্ট্রিক উইন স্টিকার (আপনার কালেকশন)
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

# API LINKS (Corrected from your code)
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF VIP SYSTEM RUNNING..."

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= ADVANCED LOGIC ENGINE =================
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

    def get_pattern_signal(self):
        # প্যাটার্ন এনালাইসিস লজিক
        if len(self.history) < 6:
            return random.choice(["BIG", "SMALL"])
        
        last_6 = self.history[:6]
        
        # 1. Dragon Pattern Check
        if last_6[0] == last_6[1] == last_6[2] == last_6[3]:
            return last_6[0] # ড্রাগন চললে ড্রাগন ধরবো
            
        # 2. ZigZag Pattern Check
        if last_6[0] != last_6[1] and last_6[1] != last_6[2]:
            return "SMALL" if last_6[0] == "BIG" else "BIG"

        # 3. AABB Pattern
        if last_6[0] == last_6[1] and last_6[2] == last_6[3]:
            return "SMALL" if last_6[0] == "BIG" else "BIG"
            
        # Default: Trend Following
        return last_6[0]

    def calculate_confidence(self):
        if len(self.history) < 5: return 60
        if self.history[0] == self.history[1] == self.history[2]: return 95 # Strong Trend
        if self.history[0] != self.history[1]: return 80 # Zigzag
        return 70

# ================= STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}

state = BotState()

# ================= ROBUST API FETCH (FROM YOUR CODE) =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    
    # আপনার দেওয়া ৫ লেয়ারের বাইপাস সিস্টেম
    proxies = [
        f"{base_url}?t={int(time.time()*1000)}", # Direct
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

    # প্রতিটি প্রক্সি ট্রাই করবে
    for url in proxies:
        try:
            print(f"Trying API: {url[:40]}...") # কনসোলে দেখার জন্য
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    print("✅ API Success!")
                    return data["data"]["list"][0]
        except:
            continue
    
    print("❌ All Proxies Failed")
    return None

# ================= FORMATTING =================
def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    color = "GREEN" if prediction == "BIG" else "RED"
    
    # রিকভারি লজিক
    lvl = streak_loss + 1
    amount_x = 3 ** (lvl - 1) # 1x, 3x, 9x
    
    plan_text = f"Start (1X)"
    if lvl > 1: plan_text = f"⚠️ Recovery Stage {lvl-1} ({amount_x}X)"
    if lvl > 4: plan_text = f"🔥 DO OR DIE ({amount_x}X)"

    return (
        f"🛡 <b>DK MARUF PREMIUM V2</b> 🛡\n"
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
        status = f"⚠️ <b>Next 3X Recovery</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"📶 <b>System by DK Maruf</b>"
    )

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 Premium Engine Started...")
    
    while state.is_running:
        try:
            # 1. Fetch Data (Using YOUR Code's Logic)
            latest = fetch_latest_issue(state.game_mode)
            
            if not latest:
                await asyncio.sleep(2)
                continue
                
            latest_issue = latest['issueNumber']
            latest_num = latest['number']
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)
            
            # 2. Result Processing
            if state.active_bet and state.active_bet['period'] == latest_issue:
                pick = state.active_bet['pick']
                is_win = (pick == latest_type)
                
                # Update Engine Logic
                state.engine.update_history(latest)
                
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_win'] += 1
                    state.stats['streak_loss'] = 0
                    
                    # Sticker Logic (Streak Check)
                    streak = state.stats['streak_win']
                    sticker_id = STICKERS['WIN_GENERIC']
                    if streak in STICKERS['STREAK_WINS']:
                        sticker_id = STICKERS['STREAK_WINS'][streak]
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
                    except: pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except: pass

                # Send Result Msg
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # 3. Prediction Generation
            if not state.active_bet and state.last_period_processed != next_issue:
                # Sync
                await asyncio.sleep(2)
                state.engine.update_history(latest) # Ensure latest data is in logic
                
                # AI Logic
                pred = state.engine.get_pattern_signal()
                conf = state.engine.calculate_confidence()
                
                state.active_bet = {
                    "period": next_issue,
                    "pick": pred
                }
                
                # Signal Sticker
                s_stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
                except: pass
                
                # Signal Msg
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_issue, pred, conf, state.stats['streak_loss']),
                        parse_mode=ParseMode.HTML
                    )
                except: pass

            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Engine Loop Error: {e}")
            await asyncio.sleep(5)

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
        state.engine = PredictionEngine() # Reset Logic
        
        await update.message.reply_text(f"✅ <b>Connected to {mode}</b>\nWait for signals...", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass
        
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("DK MARUF FINAL SYSTEM LIVE...")
    app.run_polling()
