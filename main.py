import asyncio
import logging
import random
import requests
import time
import os
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- আপনার টোকেন বসান
TARGET_CHANNEL = "@dk_mentor_maruf_official" 
CHANNEL_LINK = "https://t.me/dk_mentor_maruf_official"

# STICKERS (Customize if needed)
STICKER_WIN = "CAACAgUAAxkBAAEQTcNpclMMXJSUTpl9-V6LE2R39r4G7gAC0x4AAvodqFXSg4ICDj9BZzgE" 
STICKER_LOSS = "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE"

# API ENDPOINTS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
app = Flask('')

@app.route('/')
def home():
    return "DK MENTOR AI RUNNING..."

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = None 
        # Stats Tracking
        self.stats = {
            "wins": 0, 
            "losses": 0, 
            "total": 0,
            "streak_win": 0,  # পরপর উইন কাউন্ট
            "streak_loss": 0  # পরপর লস কাউন্ট (রিকভারি লেভেল)
        }
        self.last_period_processed = None 
        self.active_prediction = None 

state = BotState()

# ================= LOGIC GENERATOR =================
def generate_prediction():
    # Rakib's Logic: 3 Random Nums
    nums = random.sample(range(10), 3) 
    big_count = sum(1 for n in nums if n >= 5)
    prediction = "BIG" if big_count >= 2 else "SMALL"
    
    return {
        "type": prediction,
        "conf": random.randint(96, 99),
        "jackpot": f"{nums[0]}, {nums[1]}", 
    }

# ================= ROBUST API FETCH =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    
    # 5 Layer Protection to bypass block
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

    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except:
            continue
    
    return None

# ================= PREMIUM MESSAGES =================

def format_signal(issue, data, mode):
    # Recovery & Streak Logic Display
    status_text = ""
    if state.stats['streak_loss'] > 0:
        # Loss चलছে -> Recovery Mode
        lvl = state.stats['streak_loss'] + 1
        status_text = f"⚠️ <b>Recovery Level: {lvl}</b> (Use {lvl*2}X)"
    elif state.stats['streak_win'] > 1:
        # Streak চলছে -> Winning Mode
        status_text = f"🔥 <b>WINNING STREAK: {state.stats['streak_win']}</b> 🔥"
    else:
        # Normal
        status_text = "🟢 <b>Start Level 1</b>"

    return (
        f"🚀 <b>DK MENTOR VIP SIGNAL</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Market:</b> {mode} VIP\n"
        f"⏰ <b>Period:</b> <code>{issue}</code>\n"
        f"🎯 <b>Signal:</b>  👉 <b>{data['type']}</b> 👈\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{status_text}\n"
        f"💎 <b>Confidence:</b> {data['conf']}%\n"
        f"🎰 <b>Jackpot:</b> {data['jackpot']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <a href='{CHANNEL_LINK}'>JOIN OFFICIAL CHANNEL</a>"
    )

def format_result(issue, result_type, result_num, pred_type, is_win):
    if is_win:
        if state.stats['streak_win'] > 1:
            header = f"🔥 {state.stats['streak_win']} SUPER WIN 🔥"
        else:
            header = "✅ WIN WIN WIN ✅"
    else:
        header = "❌ LOSS - Next Recovery ❌"

    return (
        f"📊 <b>RESULT UPDATE: {issue}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎲 <b>Result:</b> {result_num} ({result_type})\n"
        f"📝 <b>Prediction:</b> {pred_type}\n"
        f"\n"
        f"<b>{header}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Score:</b> {state.stats['wins']} W - {state.stats['losses']} L\n"
        f"👤 <b>By:</b> DK MENTOR MARUF"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    net = wins - losses
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Owner:</b> DK MENTOR MARUF\n"
        f"📊 <b>Final Report:</b>\n"
        f"✅ <b>Total Wins:</b> {wins}\n"
        f"❌ <b>Total Loss:</b> {losses}\n"
        f"💰 <b>Net Session:</b> {net} Units\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <a href='{CHANNEL_LINK}'>JOIN VIP CHANNEL</a>"
    )

# ================= ENGINE LOOP =================

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    fail_count = 0
    while state.is_running:
        try:
            # 1. Fetch Data
            latest = fetch_latest_issue(state.game_mode)
            
            if not latest:
                fail_count += 1
                if fail_count >= 10: # অনেকক্ষণ ডাটা না পেলে ওয়ার্নিং
                    print("⚠️ Severe API Blockage.")
                    fail_count = 0
                await asyncio.sleep(2)
                continue
            
            fail_count = 0 

            latest_issue = latest['issueNumber']
            latest_result_num = int(latest['number'])
            latest_result_type = "BIG" if latest_result_num >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # 2. Result Processing
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                pred_type = state.active_prediction['type']
                is_win = (pred_type == latest_result_type)
                
                # Logic for Streak/Recovery
                state.stats["total"] += 1
                if is_win: 
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1 # Streak বাড়ছে
                    state.stats["streak_loss"] = 0 # Loss reset
                else: 
                    state.stats["losses"] += 1
                    state.stats["streak_loss"] += 1 # Recovery Level বাড়ছে
                    state.stats["streak_win"] = 0 # Streak reset
                
                # Send Sticker
                try:
                    sticker = STICKER_WIN if is_win else STICKER_LOSS
                    await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker)
                except: pass

                # Send Result
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_result(latest_issue, latest_result_type, latest_result_num, pred_type, is_win),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e: print(f"Send Err: {e}")
                
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # 3. Next Prediction
            if state.active_prediction is None and state.last_period_processed != next_issue:
                data = generate_prediction()
                state.active_prediction = {"period": next_issue, "type": data['type']}
                
                await asyncio.sleep(2)
                
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_signal(next_issue, data, state.game_mode),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e: print(f"Send Err: {e}")

            await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"Loop: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['⚡ Connect 1M', '⚡ Connect 30S']]
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Sir!</b>\nChoose Market:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Bot is active. Use /off to stop.")
        return

    msg = update.message.text
    mode = '1M' if '1M' in msg else '30S'
    state.game_mode = mode
    state.is_running = True
    # Reset stats on new session
    state.stats = {"wins": 0, "losses": 0, "total": 0, "streak_win": 0, "streak_loss": 0}
    state.active_prediction = None
    state.last_period_processed = None
    
    await update.message.reply_text(f"✅ Started {mode} for {TARGET_CHANNEL}", reply_markup=ReplyKeyboardRemove())
    
    # Immediate Start Logic
    latest = fetch_latest_issue(mode)
    if not latest:
        await update.message.reply_text("⏳ <b>Connecting to server...</b> Data will appear shortly.")
    else:
        latest_issue = latest['issueNumber']
        next_issue = str(int(latest_issue) + 1)
        state.last_period_processed = latest_issue
        
        data = generate_prediction()
        state.active_prediction = {"period": next_issue, "type": data['type']}
        
        await asyncio.sleep(1)
        try:
            await context.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=format_signal(next_issue, data, mode),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}\nCheck if bot is Admin!")
            state.is_running = False
            return

    context.application.create_task(game_loop(context))

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.is_running:
        await update.message.reply_text("⚠️ Bot is not running.")
        return
    
    state.is_running = False
    await update.message.reply_text("🛑 Bot Stopped.")
    
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=format_summary(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except: pass

if __name__ == '__main__':
    keep_alive()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("off", stop_bot))
    application.add_handler(MessageHandler(filters.Regex(r'Connect'), connect_market))
    print("Maruf AI Live...")
    application.run_polling()
