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

# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- আপনার টোকেন বসান
TARGET_CHANNEL = "-1003293007059"   # <--- আপনার চ্যানেল আইডি

# ================= STICKER DATABASE =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    
    'WIN': [
        "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE", # Big Win
        "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE", # Small Win
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE"  # Generic
    ],
    
    'LOSS': [
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
        "CAACAgUAAxkBAAEQTh5pcmTbrSEe58RRXvtu_uwEAWZoQQAC5BEAArgxYVUhMlnBGKmcbzgE"
    ],
    
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
}

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
from flask import Flask
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF VIP SYSTEM RUNNING..."

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        self.last_period_processed = None 
        self.active_prediction = None 
        self.history = [] 

state = BotState()

# ================= LOGIC & PREDICTION =================
def analyze_trend(history):
    # স্মার্ট ট্রেন্ড এনালাইসিস
    if len(history) < 3:
        return random.choice(["BIG", "SMALL"])
    
    last_3 = history[:3]
    # যদি টানা ৩ বার একই আসে, ট্রেন্ড ব্রেক করার জন্য বিপরীত সিগন্যাল
    if last_3.count("BIG") == 3: return "SMALL"
    if last_3.count("SMALL") == 3: return "BIG"
    
    # ZigZag Pattern (Big-Small-Big...) ফলো করা
    if len(history) >= 2 and history[0] != history[1]:
        return history[1] 
        
    return history[0] # ডিফল্ট

def generate_signal(history):
    pred = analyze_trend(history)
    
    # কালার লজিক: BIG হলে সাধারণত GREEN, SMALL হলে RED
    if pred == "BIG":
        return {"type": "BIG", "emoji": "🟢", "color": "GREEN 🟢"}
    else:
        return {"type": "SMALL", "emoji": "🔴", "color": "RED 🔴"}

# ================= ROBUST API FETCH (UPDATED) =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    
    # আপনার দেওয়া ৫ লেয়ারের বাইপাস সিস্টেম
    proxies = [
        f"{base_url}?t={int(time.time()*1000)}", # Direct Timestamped
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

    # প্রতিটি প্রক্সি ট্রাই করবে যতক্ষণ না ডাটা পায়
    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except:
            continue # পরের প্রক্সিতে যাবে
    
    return None

# ================= VIP MESSAGE FORMATS =================
def format_signal(issue, data):
    # রিকভারি প্ল্যান টেক্সট
    lvl = state.stats['streak_loss'] + 1
    
    if lvl == 1:
        plan = "✅ Safe Bet (1X)"
    elif lvl == 2:
        plan = "⚠️ Recovery Stage 1 (3X)"
    elif lvl == 3:
        plan = "🔥 Recovery Stage 2 (9X)"
    else:
        plan = "💎 DO OR DIE (Max Bet)"

    return (
        f"╔══════════════════╗\n"
        f"  💎 <b>DK MARUF VIP PREMIUM</b> 💎\n"
        f"╚══════════════════╝\n"
        f"⚙️ <b>Server:</b> {state.game_mode} | ⏳ <b>Wait..</b>\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔥 <b>SIGNAL:</b>  {data['emoji']} <b>{data['type']}</b> {data['emoji']}\n"
        f"🎨 <b>Color:</b> {data['color']}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Plan:</b> {plan}\n"
        f"⚡ <b>Maintain Balance!</b>\n"
        f"👑 <b>Owner:</b> @dk_mentor_maruf_official"
    )

def format_result(issue, res_type, res_num, my_pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if res_num in [0, 5]: res_emoji = "🟣" # Violet
    
    if is_win:
        streak = state.stats['streak_win']
        header = f"✅✅ <b>WINNER WINNER</b> ✅✅"
        status = f"🔥 <b>STREAK: {streak} WINS</b> 🔥"
    else:
        header = f"❌❌ <b>MISS / LOSS</b> ❌❌"
        status = f"⚠️ <b>Next Signal Strong!</b>"
    
    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"📶 <b>System by DK Maruf</b>"
    )

# ================= MAIN LOOP =================
async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    print("🟢 Engine Started...")
    fail_count = 0
    
    while state.is_running:
        try:
            # 1. Fetch Data
            latest = fetch_latest_issue(state.game_mode)
            
            if not latest:
                fail_count += 1
                if fail_count >= 5: print("⚠️ Retrying API Connection...")
                await asyncio.sleep(2)
                continue
            
            fail_count = 0 
            latest_issue = latest['issueNumber']
            latest_res_num = int(latest['number'])
            latest_res_type = "BIG" if latest_res_num >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # Update History for Logic
            if not state.history or state.history[0] != latest_res_type:
                state.history.insert(0, latest_res_type)
                state.history = state.history[:12]

            # 2. PROCESS RESULT
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                pick = state.active_prediction['type']
                is_win = (pick == latest_res_type)
                
                # Stats
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_loss'] = 0
                    state.stats['streak_win'] += 1
                    # Win Sticker
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['WIN']))
                    except: pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_loss'] += 1
                    state.stats['streak_win'] = 0
                    # Loss Sticker
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except: pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL, 
                        format_result(latest_issue, latest_res_type, latest_res_num, pick, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e: print(f"Msg Error: {e}")
                
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # 3. GENERATE NEW SIGNAL
            if state.active_prediction is None and state.last_period_processed != next_issue:
                # Wait slightly for server sync
                await asyncio.sleep(2) 
                
                data = generate_signal(state.history)
                state.active_prediction = {"period": next_issue, "type": data['type']}
                
                # Sticker Prediction
                try:
                    s = STICKERS['BIG_PRED'] if data['type'] == "BIG" else STICKERS['SMALL_PRED']
                    await context.bot.send_sticker(TARGET_CHANNEL, s)
                except: pass
                
                # VIP Message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_issue, data),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e: print(f"Signal Send Error: {e}")

            await asyncio.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome Boss!</b>\nSelect Market to Start:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running: return
    
    mode = '1M' if '1M' in update.message.text else '30S'
    state.game_mode = mode
    state.is_running = True
    state.stats = {"wins":0, "losses":0, "streak_win":0, "streak_loss":0}
    state.active_prediction = None
    state.last_period_processed = None
    state.history = []

    await update.message.reply_text(f"✅ <b>Connected to {mode}</b>\nWait for next signal...", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
    
    # Send Start Sticker
    try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
    except: pass

    # Fetch initial data to sync
    latest = fetch_latest_issue(mode)
    if latest:
        state.last_period_processed = latest['issueNumber']
        # History তে ডাটা এড করা লজিকের জন্য
        res_type = "BIG" if int(latest['number']) >= 5 else "SMALL"
        state.history.append(res_type)
    
    context.application.create_task(game_loop(context))

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.is_running = False
    await update.message.reply_text("🛑 Bot Stopped")

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("off", stop))
    app.add_handler(MessageHandler(filters.Regex(r'Connect'), connect))
    
    print("DK MARUF AI Online...")
    app.run_polling()
