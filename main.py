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
TARGET_CHANNEL = "-1003293007059"   # <--- আপনার চ্যানেল আইডি
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
    return "DK Mentor Maruf AI Running..."

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
        self.history = [] # For trend analysis

state = BotState()

# ================= ADVANCED LOGIC (Trend + Color) =================
def analyze_trend(history):
    # Simple logic: If last 3 results are same, probability of switch increases
    if len(history) < 3:
        return random.choice(["BIG", "SMALL"])
    
    last_3 = history[:3]
    if last_3.count("BIG") == 3:
        return "SMALL" # Break trend
    elif last_3.count("SMALL") == 3:
        return "BIG" # Break trend
    else:
        # Follow recent hit (Zigzag or 2x2)
        return history[0] 

def generate_prediction_data(history):
    # 1. Decide Big/Small
    prediction = analyze_trend(history)
    
    # 2. Assign Color based on Prediction
    # Big (5-9): Mostly Green (5,7,9), Red (6,8). 
    # Small (0-4): Mostly Red (0,2,4), Green (1,3).
    # Logic: Big = Green Dominant, Small = Red Dominant
    
    if prediction == "BIG":
        color = "🟢 GREEN"
        color_code = "🟢"
    else:
        color = "🔴 RED"
        color_code = "🔴"
        
    return {
        "type": prediction,
        "color": color,
        "emoji": color_code
    }

# ================= API FETCH =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    proxies = [
        f"{base_url}?t={int(time.time()*1000)}",
        f"https://corsproxy.io/?{base_url}",
        f"https://api.allorigins.win/raw?url={base_url}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Referer": "https://dkwin9.com/",
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

# ================= PREMIUM MESSAGE FORMATTING =================

def format_signal(issue, data, mode):
    # Recovery & Balance Management Text
    loss_streak = state.stats['streak_loss']
    
    if loss_streak == 0:
        advice = "✅ Safe Bet (Start)"
        multi = "1X"
    elif loss_streak == 1:
        advice = "⚠️ Recov. Level 1"
        multi = "3X"
    elif loss_streak == 2:
        advice = "🔥 Recov. Level 2"
        multi = "9X"
    else:
        advice = "💎 DO OR DIE (Max)"
        multi = "MAX"

    # PREMIUM BOX DESIGN
    return (
        f"╔══════════════════╗\n"
        f"  💎 <b>DK MARUF VIP PREMIUM</b> 💎\n"
        f"╚══════════════════╝\n"
        f"⚙️ <b>Server:</b> {mode} | ⏳ <b>Wait..</b>\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔥 <b>SIGNAL:</b>  {data['emoji']} <b>{data['type']}</b> {data['emoji']}\n"
        f"🎨 <b>Color:</b> {data['color']}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Plan:</b> {advice}\n"
        f"🚀 <b>Inv:</b> {multi}\n"
        f"👑 <b>Owner:</b> @dk_mentor_maruf_official"
    )

def format_result(issue, result_type, result_num, pred_type, is_win):
    # Result Emoji Logic
    res_emoji = "🟢" if result_type == "BIG" else "🔴"
    if result_num == 0 or result_num == 5:
        res_emoji = "🟣" # Violet

    if is_win:
        streak = state.stats['streak_win']
        header = f"✅✅ <b>WINNER WINNER</b> ✅✅"
        status = f"🔥 <b>SUPER WIN STREAK: {streak}</b> 🔥"
    else:
        header = f"❌❌ <b>MISS / LOSS</b> ❌❌"
        status = f"⚠️ <b>Next Signal High Chance!</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {result_num} ({result_type})\n"
        f"🎯 <b>My Pick:</b> {pred_type}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"📶 <b>System by DK Mentor Maruf</b>"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    acc = 0
    if (wins + losses) > 0:
        acc = round((wins / (wins + losses)) * 100, 2)
        
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🏆 <b>Total Wins:</b> {wins}\n"
        f"🗑 <b>Total Loss:</b> {losses}\n"
        f"📊 <b>Accuracy:</b> {acc}%\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Thank you for playing with DK Maruf!</i>"
    )

# ================= GAME LOOP =================

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    while state.is_running:
        try:
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(2)
                continue

            latest_issue = latest['issueNumber']
            latest_result_num = int(latest['number'])
            latest_result_type = "BIG" if latest_result_num >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)

            # Update History for Logic
            if not state.history or state.history[0] != latest_result_type:
                state.history.insert(0, latest_result_type)
                if len(state.history) > 10: state.history.pop()

            # --- PROCESS RESULT ---
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                pred_type = state.active_prediction['type']
                is_win = (pred_type == latest_result_type)
                
                # Stats & Stickers
                sticker = None
                if is_win: 
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                    
                    streak = state.stats['streak_win']
                    if streak in STICKERS['SUPER_WIN']:
                        sticker = STICKERS['SUPER_WIN'][streak]
                    elif latest_result_type == "BIG":
                        sticker = STICKERS['WIN_BIG_RES']
                    else:
                        sticker = STICKERS['WIN_SMALL_RES']
                else: 
                    state.stats["losses"] += 1
                    state.stats["streak_loss"] += 1
                    state.stats["streak_win"] = 0
                    sticker = random.choice(STICKERS['LOSS'])
                
                # Send Sticker
                if sticker:
                    try: await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker)
                    except: pass

                # Send Result Text
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_result(latest_issue, latest_result_type, latest_result_num, pred_type, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # --- SEND NEXT SIGNAL ---
            if state.active_prediction is None and state.last_period_processed != next_issue:
                # Generate Prediction with Color
                data = generate_prediction_data(state.history)
                
                state.active_prediction = {
                    "period": next_issue,
                    "type": data['type']
                }
                
                await asyncio.sleep(1.5) # Little delay for realism
                
                # 1. Sticker
                try:
                    s_key = 'BIG_PRED' if data['type'] == "BIG" else 'SMALL_PRED'
                    await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=STICKERS[s_key])
                except: pass

                # 2. VIP Message
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_signal(next_issue, data, state.game_mode),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logging.error(f"Send Error: {e}")

            await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"Loop Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 <b>Welcome Boss {user.first_name}!</b>\n\n"
        "Select Market to Start VIP Prediction:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S']], resize_keyboard=True, one_time_keyboard=False),
        parse_mode=ParseMode.HTML
    )

async def connect_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Bot already running! Use /off to stop.")
        return

    msg = update.message.text
    mode = '1M' if '1M' in msg else '30S'
    state.game_mode = mode
    state.is_running = True
    state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
    state.active_prediction = None
    state.last_period_processed = None
    state.history = []
    
    await update.message.reply_text(f"✅ <b>Active Mode: {mode}</b>\nConnecting to Server...", parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
    
    # Pre-Session Animation
    for sticker in STICKERS['PRE_SESSION']:
        try:
            await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker)
            await asyncio.sleep(0.8)
        except: pass

    try:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=f"🚨 <b>OFFICIAL SESSION STARTED</b> 🚨\n\n💎 <b>Server:</b> {mode}\n👑 <b>Host:</b> DK MENTOR MARUF\n\n<i>Get ready for back to back wins!</i>",
            parse_mode=ParseMode.HTML
        )
    except: pass

    # Instant Start Logic
    latest = fetch_latest_issue(mode)
    if latest:
        # Pre-fill history to start logic immediately
        l_res = "BIG" if int(latest['number']) >= 5 else "SMALL"
        state.history.append(l_res)
        state.last_period_processed = latest['issueNumber']

    context.application.create_task(game_loop(context))

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.is_running = False
    await update.message.reply_text("🛑 Stopping Bot Loop...")
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
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("off", stop_bot))
    application.add_handler(MessageHandler(filters.Regex(r'Connect'), connect_market))
    
    print("DK MARUF AI System Live...")
    application.run_polling()
