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

# ================= STICKER DATABASE =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    
    'WIN_GENERIC': [
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE",
        "CAACAgUAAxkBAAEQTcNpclMMXJSUTpl9-V6LE2R39r4G7gAC0x4AAvodqFXSg4ICDj9BZzgE",
        "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE"
    ],
    'WIN_BIG_RES': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_SMALL_RES': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    
    'LOSS': [
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
        "CAACAgUAAxkBAAEQTh5pcmTbrSEe58RRXvtu_uwEAWZoQQAC5BEAArgxYVUhMlnBGKmcbzgE"
    ],
    
    'SUPER_WIN': {
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
    
    'SESSION_START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
    'PRE_SESSION': [
        "CAACAgUAAxkBAAEQTj5pcmYuCpb0VS-W9iuzJATH4zgn1gACfxYAAtvLoFcMDo6GKtMAASA4BA",
        "CAACAgUAAxkBAAEQTj9pcmYu-XvfmFN6-Ev7kexvYH1WhAACDxYAAiQ7mVcedoBI8tsCvDgE",
        "CAACAgUAAxkBAAEQTkJpcmYz7CETjTbVuTaTloOWj0w1NgACrxkAAg8OoVfAIXjvhcHVhDgE"
    ]
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
        self.stats = {
            "wins": 0, "losses": 0, 
            "streak_win": 0, "streak_loss": 0
        }
        self.last_period_processed = None 
        self.active_prediction = None 
        # লস মেসেজ ট্র্যাক করার জন্য নতুন লিস্ট
        self.loss_messages_ids = []

state = BotState()

# ================= LOGIC (TREND FOLLOWING) =================
def generate_prediction(last_result_type):
    if last_result_type:
        chance = random.randint(1, 100)
        if chance <= 60:
            prediction = last_result_type # Follow Trend
        else:
            prediction = "SMALL" if last_result_type == "BIG" else "BIG" # Reverse
    else:
        prediction = random.choice(["BIG", "SMALL"])
        
    return {
        "type": prediction
    }

# ================= ROBUST API FETCH =================
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
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except:
            continue
    return None

# ================= MESSAGES =================

def format_signal(issue, data, mode):
    loss_streak = state.stats['streak_loss']
    if loss_streak == 0:
        rec_text = "🟢 Start Level 1"
    elif loss_streak == 1:
        rec_text = "🟡 One Step Recovery"
    elif loss_streak == 2:
        rec_text = "🟠 Two Step Recovery"
    elif loss_streak == 3:
        rec_text = "🔴 Three Step Recovery"
    else:
        rec_text = f"⚠️ Recovery Step {loss_streak}"

    return (
        f"💠 <b>DK MARUF VIP SIGNAL</b>\n"
        f"🔹 <b>Market:</b> {mode}\n"
        f"🔹 <b>Period:</b> <code>{issue}</code>\n"
        f"\n"
        f"🎯 <b>Select:</b>  🔥 <b>{data['type']}</b> 🔥\n"
        f"💰 <b>Plan:</b> {rec_text}\n"
        f"\n"
        f"📢 <i>Official: {TARGET_CHANNEL}</i>"
    )

def format_result(issue, result_type, result_num, pred_type, is_win):
    if is_win:
        streak = state.stats['streak_win']
        if streak >= 2:
            status = f"🔥 {streak} SUPER WIN 🔥"
        else:
            status = "✅ WIN ✅"
    else:
        status = "❌ LOSS - Use Next Step ❌"

    return (
        f"📊 <b>RESULT: {issue}</b>\n"
        f"🎲 <b>Result:</b> {result_num} ({result_type})\n"
        f"🎯 <b>You Picked:</b> {pred_type}\n"
        f"<b>{status}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>By:</b> DK MENTOR MARUF"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    return (
        f"🛑 <b>SESSION ENDED</b>\n"
        f"✅ <b>Wins:</b> {wins}\n"
        f"❌ <b>Losses:</b> {losses}\n"
        f"🧹 <i>Cleaning Loss History...</i>"
    )

# ================= GAME LOOP =================

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    last_known_result_type = None 

    while state.is_running:
        try:
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(2)
                continue

            latest_issue = latest['issueNumber']
            latest_result_num = int(latest['number'])
            latest_result_type = "BIG" if latest_result_num >= 5 else "SMALL"
            
            last_known_result_type = latest_result_type
            next_issue = str(int(latest_issue) + 1)

            # --- PROCESS RESULT ---
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                pred_type = state.active_prediction['type']
                is_win = (pred_type == latest_result_type)
                
                # Stats
                if is_win: 
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                else: 
                    state.stats["losses"] += 1
                    state.stats["streak_loss"] += 1
                    state.stats["streak_win"] = 0
                
                # 1. Send Sticker
                try:
                    sticker = None
                    if is_win:
                        streak = state.stats['streak_win']
                        if streak in STICKERS['SUPER_WIN']:
                            sticker = STICKERS['SUPER_WIN'][streak]
                        elif latest_result_type == "BIG":
                            sticker = STICKERS['WIN_BIG_RES']
                        elif latest_result_type == "SMALL":
                            sticker = STICKERS['WIN_SMALL_RES']
                        else:
                            sticker = random.choice(STICKERS['WIN_GENERIC'])
                    else:
                        sticker = random.choice(STICKERS['LOSS'])
                    
                    if sticker:
                        sent_sticker = await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker)
                        # লস হলে স্টিকার আইডি সেভ করুন
                        if not is_win:
                            state.loss_messages_ids.append(sent_sticker.message_id)
                except: pass

                # 2. Send Result Message
                try:
                    sent_msg = await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_result(latest_issue, latest_result_type, latest_result_num, pred_type, is_win),
                        parse_mode=ParseMode.HTML
                    )
                    # লস হলে মেসেজ আইডি সেভ করুন
                    if not is_win:
                        state.loss_messages_ids.append(sent_msg.message_id)
                except: pass
                
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # --- SEND NEXT SIGNAL ---
            if state.active_prediction is None and state.last_period_processed != next_issue:
                data = generate_prediction(last_known_result_type)
                state.active_prediction = {
                    "period": next_issue,
                    "type": data['type']
                }
                
                await asyncio.sleep(1)
                
                try:
                    pred_sticker = STICKERS['BIG_PRED'] if data['type'] == "BIG" else STICKERS['SMALL_PRED']
                    await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=pred_sticker)
                except: pass

                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_signal(next_issue, data, state.game_mode),
                        parse_mode=ParseMode.HTML
                    )
                except: pass

            await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Sir!</b>\nChoose:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Bot is running. /off first.")
        return

    msg = update.message.text
    mode = '1M' if '1M' in msg else '30S'
    state.game_mode = mode
    state.is_running = True
    # রিসেট সবকিছু
    state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
    state.active_prediction = None
    state.last_period_processed = None
    state.loss_messages_ids = [] # লিস্ট ক্লিয়ার
    
    await update.message.reply_text(f"✅ Active: {mode}", reply_markup=ReplyKeyboardRemove())
    
    # Pre-Session
    for sticker in STICKERS['PRE_SESSION']:
        try:
            await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker)
            await asyncio.sleep(0.5)
        except: pass

    try:
        await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=STICKERS['SESSION_START'])
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=f"🟢 <b>SESSION STARTED ({mode})</b>\nBot active by DK MENTOR MARUF",
            parse_mode=ParseMode.HTML
        )
    except: pass

    # Immediate Start
    latest = fetch_latest_issue(mode)
    if latest:
        latest_issue = latest['issueNumber']
        latest_res_type = "BIG" if int(latest['number']) >= 5 else "SMALL"
        next_issue = str(int(latest_issue) + 1)
        
        state.last_period_processed = latest_issue
        data = generate_prediction(latest_res_type)
        state.active_prediction = {"period": next_issue, "type": data['type']}
        
        await asyncio.sleep(1)
        try:
            s = STICKERS['BIG_PRED'] if data['type'] == "BIG" else STICKERS['SMALL_PRED']
            await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=s)
            await context.bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=format_signal(next_issue, data, mode),
                parse_mode=ParseMode.HTML
            )
        except: pass

    context.application.create_task(game_loop(context))

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.is_running = False
    await update.message.reply_text("🛑 Stopping & Cleaning Losses...")

    # --- DELETE LOSS MESSAGES ---
    if state.loss_messages_ids:
        deleted_count = 0
        for msg_id in state.loss_messages_ids:
            try:
                # মেসেজ ডিলিট কমান্ড
                await context.bot.delete_message(chat_id=TARGET_CHANNEL, message_id=msg_id)
                deleted_count += 1
                await asyncio.sleep(0.1) # Telegram API limit এড়াতে একটু গ্যাপ
            except Exception as e:
                print(f"Failed to delete {msg_id}: {e}")
        
        # লিস্ট ক্লিয়ার
        state.loss_messages_ids.clear()
        await update.message.reply_text(f"🗑️ Deleted {deleted_count} loss messages.")
    else:
        await update.message.reply_text("✅ No losses to delete.")

    try:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=format_summary(),
            parse_mode=ParseMode.HTML
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
