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
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- টোকেন বসান
TARGET_CHANNEL = "@dk_mentor_maruf_official" 
ADMIN_ID = 123456789 

# STICKERS
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    'WIN_GENERIC': ["CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE"],
    'WIN_BIG': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_SMALL': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'LOSS': ["CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE"],
    'SUPER_WIN': {
        2: "CAACAgUAAxkBAAEQTiBpcmUfm9aQmlIHtPKiG2nE2e6EeAACcRMAAiLWqFSpdxWmKJ1TXzgE",
        3: "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE",
        4: "CAACAgUAAxkBAAEQTiJpcmUgSydN-tKxoSVdFuAvCcJ3fQACvSEAApMRqFQoUYBnH5Pc7TgE",
        5: "CAACAgUAAxkBAAEQTiNpcmUgu_dP3wKT2k94EJCiw3u52QACihoAArkfqFSlrldtXbLGGDgE"
    },
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
}

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
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        self.last_period_processed = None 
        self.active_prediction = None 
        self.messages_to_delete = [] # লস মেসেজ রিমুভার লিস্ট

state = BotState()

# ================= SAFE LOGIC (TREND FOLLOWER) =================
def calculate_prediction(last_result_type):
    """
    Logic: Follow the last result (Trend Strategy).
    If last was BIG -> Predict BIG.
    If last was SMALL -> Predict SMALL.
    This catches 'Dragon' streaks which is most common.
    """
    if not last_result_type:
        return {"type": random.choice(["BIG", "SMALL"]), "conf": 95, "jackpot": "3, 8"}
    
    # 80% Trend Follow, 20% Random (to break zigzag)
    if random.randint(1, 100) <= 80:
        prediction = last_result_type
    else:
        prediction = "SMALL" if last_result_type == "BIG" else "BIG"

    j1 = random.randint(0, 4) if prediction == "SMALL" else random.randint(5, 9)
    j2 = random.randint(0, 9)
    
    return {
        "type": prediction,
        "conf": random.randint(97, 100),
        "jackpot": f"{j1}, {j2}"
    }

# ================= API FETCH =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    proxies = [
        f"https://corsproxy.io/?{base_url}?t={int(time.time()*1000)}", 
        f"https://api.allorigins.win/raw?url={base_url}",
        f"{base_url}?t={int(time.time()*1000)}"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/"
    }

    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except: continue
    return None

# ================= MESSAGES =================
def format_signal(issue, data, mode):
    loss_s = state.stats['streak_loss']
    plan = f"🟢 Start Level 1" if loss_s == 0 else f"⚠️ Recovery Step {loss_s + 1} ({loss_s*2 + 2}X)"
    
    return (
        f"💠 <b>DK MARUF VIP SIGNAL</b>\n"
        f"🔹 <b>Market:</b> {mode}\n"
        f"🔹 <b>Period:</b> <code>{issue}</code>\n"
        f"\n"
        f"🎯 <b>Select:</b>  🔥 <b>{data['type']}</b> 🔥\n"
        f"💰 <b>Plan:</b> {plan}\n"
        f"\n"
        f"📢 <i>Official: {TARGET_CHANNEL}</i>"
    )

def format_result(issue, result_type, result_num, pred_type, is_win):
    if is_win:
        streak = state.stats['streak_win']
        status = f"🔥 {streak} SUPER WIN 🔥" if streak > 1 else "✅ WINNER ✅"
    else:
        status = "❌ LOSS - Use Next Step ❌"

    return (
        f"📊 <b>RESULT: {issue}</b>\n"
        f"🎲 <b>Result:</b> {result_num} ({result_type})\n"
        f"🎯 <b>You Picked:</b> {pred_type}\n"
        f"<b>{status}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>Score:</b> {state.stats['wins']} W - {state.stats['losses']} L\n"
        f"👤 <b>By:</b> DK MENTOR MARUF"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    return (
        f"🛑 <b>SESSION ENDED</b>\n"
        f"✅ <b>Total Wins:</b> {wins}\n"
        f"🗑️ <b>Losses Cleaned!</b>\n"
        f"💰 <b>Net Profit:</b> {wins} Units (Clean)\n"
        f"<i>DK Mentor Maruf AI</i>"
    )

# ================= GAME LOOP =================
async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    last_res_type = None # লজিকের জন্য মেমোরি

    while state.is_running:
        try:
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(2)
                continue

            latest_issue = latest['issueNumber']
            latest_res_num = int(latest['number'])
            latest_res_type = "BIG" if latest_res_num >= 5 else "SMALL"
            last_res_type = latest_res_type # আপডেট করা হচ্ছে
            
            next_issue = str(int(latest_issue) + 1)

            # --- RESULT CHECK ---
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                pred_type = state.active_prediction['type']
                is_win = (pred_type == latest_res_type)
                
                # Stats Update
                state.stats["total"] += 1
                if is_win: 
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                else: 
                    state.stats["losses"] += 1
                    state.stats["streak_loss"] += 1
                    state.stats["streak_win"] = 0
                
                # 1. SEND STICKER
                try:
                    s_id = None
                    if is_win:
                        sw = state.stats['streak_win']
                        s_id = STICKERS['SUPER_WIN'].get(sw, STICKERS['WIN_BIG_RES'] if latest_res_type == "BIG" else STICKERS['WIN_SMALL_RES'])
                    else:
                        s_id = random.choice(STICKERS['LOSS'])
                    
                    if s_id:
                        msg = await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=s_id)
                        if not is_win: state.messages_to_delete.append(msg.message_id) # লস স্টিকার সেভ
                except: pass

                # 2. SEND RESULT TEXT
                try:
                    msg = await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_result(latest_issue, latest_res_type, latest_res_num, pred_type, is_win),
                        parse_mode=ParseMode.HTML
                    )
                    if not is_win: state.messages_to_delete.append(msg.message_id) # লস মেসেজ সেভ
                except: pass
                
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # --- NEXT PREDICTION (IMMEDIATE) ---
            if state.active_prediction is None and state.last_period_processed != next_issue:
                
                # লজিক ব্যবহার করে প্রেডিকশন
                data = calculate_prediction(last_res_type)
                
                state.active_prediction = {"period": next_issue, "type": data['type']}
                
                await asyncio.sleep(2)
                
                try:
                    # সিগন্যাল স্টিকার
                    s = STICKERS['BIG_PRED'] if data['type'] == "BIG" else STICKERS['SMALL_PRED']
                    await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=s)
                    
                    # সিগন্যাল টেক্সট
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_signal(next_issue, data, state.game_mode),
                        parse_mode=ParseMode.HTML
                    )
                except: pass

            await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"Loop: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Maruf AI Ready!</b>",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Running...")
        return
    mode = '1M' if '1M' in update.message.text else '30S'
    state.game_mode = mode
    state.is_running = True
    state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
    state.messages_to_delete = [] # লিস্ট ক্লিয়ার
    state.active_prediction = None
    state.last_period_processed = None
    
    await update.message.reply_text(f"✅ Active: {mode}", reply_markup=ReplyKeyboardRemove())
    
    try:
        await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=STICKERS['START'])
        # Immediate Start
        latest = fetch_latest_issue(mode)
        if latest:
            last_res = "BIG" if int(latest['number']) >= 5 else "SMALL"
            next_iss = str(int(latest['issueNumber']) + 1)
            state.last_period_processed = latest['issueNumber']
            
            data = calculate_prediction(last_res)
            state.active_prediction = {"period": next_iss, "type": data['type']}
            
            await asyncio.sleep(1)
            s = STICKERS['BIG_PRED'] if data['type'] == "BIG" else STICKERS['SMALL_PRED']
            await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=s)
            await context.bot.send_message(chat_id=TARGET_CHANNEL, text=format_signal(next_iss, data, mode), parse_mode=ParseMode.HTML)
    except: pass

    context.application.create_task(game_loop(context))

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.is_running = False
    await update.message.reply_text("🛑 Stopping & Cleaning...")
    
    # --- DELETE LOSS MESSAGES ---
    count = 0
    if state.messages_to_delete:
        for msg_id in state.messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=TARGET_CHANNEL, message_id=msg_id)
                count += 1
                await asyncio.sleep(0.1) 
            except: pass
        state.messages_to_delete = [] 
    
    try: await context.bot.send_message(chat_id=TARGET_CHANNEL, text=format_summary(), parse_mode=ParseMode.HTML)
    except: pass

if __name__ == '__main__':
    keep_alive()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("off", stop))
    app_bot.add_handler(MessageHandler(filters.Regex(r'Connect'), connect))
    app_bot.run_polling()
