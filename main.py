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
ADMIN_ID = 123456789 

# STICKER IDS (আপনি চাইলে এগুলো বদলাতে পারেন)
# ডিফল্ট হিসেবে দুটি এনিমেটেড স্টিকার দেওয়া হলো
STICKER_WIN = "CAACAgUAAxkBAAEQTcNpclMMXJSUTpl9-V6LE2R39r4G7gAC0x4AAvodqFXSg4ICDj9BZzgE" # Happy Sticker
STICKER_LOSS = "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE" # Sad Sticker

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
app = Flask('')

@app.route('/')
def home():
    return "Maruf AI Running..."

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
        self.stats = {"wins": 0, "losses": 0, "total": 0}
        self.last_period_processed = None # যে পিরিয়ডের রেজাল্ট দেওয়া হয়েছে
        self.active_prediction = None # {period: '123', type: 'BIG'}

state = BotState()

# ================= LOGIC (Rakib's Logic for BOTH) =================
def generate_prediction():
    # Rakib Logic: 3 Random numbers. If 2 or more are >= 5, then BIG.
    nums = random.sample(range(10), 3) 
    big_count = sum(1 for n in nums if n >= 5)
    prediction = "BIG" if big_count >= 2 else "SMALL"
    
    return {
        "type": prediction,
        "conf": random.randint(95, 99),
        "jackpot": f"{nums[0]}, {nums[1]}", # Fake Jackpot based on nums
        "analysis": "Trend Analysis"
    }

# ================= API FETCH =================
def fetch_latest_issue(mode):
    url = API_1M if mode == '1M' else API_30S
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(f"{url}?t={int(time.time()*1000)}", headers=headers, timeout=5)
        data = response.json()
        if data and "data" in data and "list" in data["data"]:
            return data["data"]["list"][0] 
    except:
        return None

# ================= MESSAGE TEMPLATES =================

def format_signal(issue, data, mode):
    return (
        f"🔥 <b>DK MENTOR MARUF PREDICTION</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎲 <b>Market:</b> {mode} VIP\n"
        f"⏰ <b>Period:</b> <code>{issue}</code>\n"
        f"🎯 <b>Signal:</b>  🚀 <b>{data['type']}</b> 🚀\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💣 <b>Jackpot:</b> {data['jackpot']}\n"
        f"⚡ <b>Confidence:</b> {data['conf']}%\n"
        f"📢 <i>টেলিগ্রাম: {TARGET_CHANNEL}</i>"
    )

def format_result(issue, result_type, result_num, pred_type, is_win):
    status = "✅ WIN WIN WIN ✅" if is_win else "❌ LOSS (Use Level 2) ❌"
    
    total = state.stats["total"]
    win_rate = (state.stats["wins"]/total*100) if total > 0 else 0
    
    return (
        f"📊 <b>RESULT PUBLISHED: {issue}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎲 <b>Result:</b> {result_num} ({result_type})\n"
        f"🎯 <b>Your Bet:</b> {pred_type}\n"
        f"<b>{status}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Stats:</b> {state.stats['wins']} Win | {state.stats['losses']} Loss\n"
        f"💎 <b>Accuracy:</b> {win_rate:.1f}%\n"
        f"©️ {TARGET_CHANNEL}"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    net = wins - losses
    return (
        f"🛑 <b>PREDICTION STOPPED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Owner:</b> DK MENTOR MARUF\n"
        f"✅ <b>Total Wins:</b> {wins}\n"
        f"❌ <b>Total Loss:</b> {losses}\n"
        f"💰 <b>Net Profit:</b> {net} Units\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>ধন্যবাদ আমাদের সাথে থাকার জন্য!</i>"
    )

# ================= GAME LOOP =================

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    while state.is_running:
        try:
            # 1. API Fetch
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(2)
                continue

            latest_issue = latest['issueNumber'] # e.g., 500
            latest_result_num = int(latest['number'])
            latest_result_type = "BIG" if latest_result_num >= 5 else "SMALL"
            
            next_issue = str(int(latest_issue) + 1) # e.g., 501

            # 2. Result Checking Logic
            # যদি আমাদের হাতে একটি প্রেডিকশন থাকে এবং সেই পিরিয়ডটি API তে চলে আসে
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                
                pred_type = state.active_prediction['type']
                is_win = (pred_type == latest_result_type)
                
                # Stats Update
                state.stats["total"] += 1
                if is_win: state.stats["wins"] += 1
                else: state.stats["losses"] += 1
                
                # Send Sticker
                try:
                    sticker_to_send = STICKER_WIN if is_win else STICKER_LOSS
                    await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker_to_send)
                except:
                    pass # Sticker fail হলেও সমস্যা নেই

                # Send Text Result
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_result(latest_issue, latest_result_type, latest_result_num, pred_type, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    print(f"Error sending result: {e}")
                
                # Clear active prediction
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # 3. Next Prediction Logic (Immediate)
            # যদি পরবর্তী পিরিয়ডের জন্য এখনো সিগন্যাল না দিয়ে থাকি
            if state.active_prediction is None and state.last_period_processed != next_issue:
                
                # Generate Logic
                data = generate_prediction()
                
                # Save for checking later
                state.active_prediction = {
                    "period": next_issue,
                    "type": data['type']
                }
                
                await asyncio.sleep(2) # একটু সময় নেওয়া মানুষের মতো
                
                # Send Signal
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_signal(next_issue, data, state.game_mode),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    print(f"Error sending signal: {e}")

            # Smart Sleep
            await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"Loop Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['⚡ Connect 1M', '⚡ Connect 30S']]
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Sir!</b>\nSelect prediction mode:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Bot is running! Use /off first.")
        return

    msg = update.message.text
    mode = '1M' if '1M' in msg else '30S'
    state.game_mode = mode
    state.is_running = True
    state.stats = {"wins": 0, "losses": 0, "total": 0}
    state.active_prediction = None
    state.last_period_processed = None
    
    await update.message.reply_text(f"✅ Started {mode} for {TARGET_CHANNEL}", reply_markup=ReplyKeyboardRemove())
    
    # --- IMMEDIATE START LOGIC ---
    # কানেক্ট করার সাথে সাথেই লেটেস্ট ডাটা এনে পরেরটার সিগন্যাল দিয়ে দিবে
    try:
        latest = fetch_latest_issue(mode)
        if latest:
            latest_issue = latest['issueNumber']
            # আমরা ধরে নিচ্ছি লেটেস্ট পিরিয়ড শেষ, তাই পরেরটার সিগন্যাল দিব
            next_issue = str(int(latest_issue) + 1)
            state.last_period_processed = latest_issue # এটাকে প্রসেসড মার্ক করলাম যাতে লুপে কনফিউশন না হয়
            
            # Predict
            data = generate_prediction()
            state.active_prediction = {
                "period": next_issue,
                "type": data['type']
            }
            
            await context.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=f"🟢 <b>SESSION STARTED ({mode})</b>\nBot active by DK MENTOR MARUF",
                parse_mode=ParseMode.HTML
            )
            
            await asyncio.sleep(1)
            
            # Send First Signal Immediately
            await context.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=format_signal(next_issue, data, mode),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        await update.message.reply_text(f"Error starting: {e}")

    # Start the continuous loop
    context.application.create_task(game_loop(context))

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.is_running:
        await update.message.reply_text("⚠️ Bot is not running.")
        return
    
    state.is_running = False
    await update.message.reply_text("🛑 Bot Stopped.")
    
    # Send Summary
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=format_summary(),
            parse_mode=ParseMode.HTML
        )
    except:
        pass

if __name__ == '__main__':
    keep_alive()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("off", stop_bot))
    application.add_handler(MessageHandler(filters.Regex(r'Connect'), connect_market))
    
    print("Maruf AI is Live...")
    application.run_polling()
