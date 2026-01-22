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
ADMIN_ID = -1003293007059 

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
        self.history_pattern = [] # প্যাটার্ন এনালাইসিস এর জন্য

state = BotState()

# ================= ADVANCED LOGIC (HIGH MODE) =================
def analyze_and_predict(history_data):
    # history_data তে শেষ ৫টি রেজাল্ট থাকবে (BIG/SMALL)
    if not history_data or len(history_data) < 3:
        return random.choice(["BIG", "SMALL"])

    last_1 = history_data[0] # Latest
    last_2 = history_data[1]
    last_3 = history_data[2]
    
    prediction = ""

    # Strategy 1: Dragon Cutting (যদি টানা ৩ বার একই আসে, উল্টা ধরবে)
    if last_1 == last_2 == last_3:
        prediction = "SMALL" if last_1 == "BIG" else "BIG"
    
    # Strategy 2: ZigZag Follow (B S B -> S)
    elif last_1 != last_2 and last_2 != last_3:
        prediction = last_2 # আগেরটার কপি
    
    # Strategy 3: Trend Follow (Default)
    else:
        # ৬০% চান্স লাস্ট রেজাল্ট ফলো করার
        if random.randint(1, 100) <= 60:
            prediction = last_1
        else:
            prediction = "SMALL" if last_1 == "BIG" else "BIG"
            
    return prediction

def get_color_for_size(size):
    # কালার প্রেডিকশন লজিক
    # BIG usually Green (5,7,9), but 6,8 Red.
    # SMALL usually Red (0,2,4), but 1,3 Green.
    
    if size == "BIG":
        # BIG এর সাথে 60% Green, 40% Red
        return "🟢 Green" if random.randint(1, 10) <= 6 else "🔴 Red"
    else:
        # SMALL এর সাথে 60% Red, 40% Green
        return "🔴 Red" if random.randint(1, 10) <= 6 else "🟢 Green"

# ================= ROBUST API FETCH =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    proxies = [
        f"{base_url}?t={int(time.time()*1000)}", 
        f"https://corsproxy.io/?{base_url}?t={int(time.time()*1000)}", 
        f"https://api.allorigins.win/raw?url={base_url}",
        f"https://thingproxy.freeboard.io/fetch/{base_url}"
    ]
    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(100, 120)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/"
    }

    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"] # পুরা লিস্ট রিটার্ন করলাম প্যাটার্ন এর জন্য
        except:
            continue
    return None

# ================= PREMIUM MESSAGES =================

def format_signal(issue, prediction, color, mode):
    # রিকভারি লজিক
    loss_streak = state.stats['streak_loss']
    plan_emoji = "🟢" if loss_streak == 0 else "🟡" if loss_streak == 1 else "🔴"
    multiplier = 1 if loss_streak == 0 else (3 ** loss_streak) # 1x, 3x, 9x strategy
    
    # মেইন প্রেডিকশন হাইলাইট
    main_pred = f"🔥 {prediction} 🔥"
    if prediction == "BIG":
        main_pred = "🔥 𝐁𝐈𝐆 ( বড় ) 🐯"
    else:
        main_pred = "🔥 𝐒𝐌𝐀𝐋𝐋 ( ছোট ) 🐜"

    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  <b>💎 DK MENTOR VIP S1 💎</b>\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━┛\n"
        f"🎮 <b>Game Type:</b> WinGo {mode}\n"
        f"📅 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>PREDICTION (Signal):</b>\n"
        f"\n"
        f"   👉 {main_pred}\n"
        f"   🎨 <b>Color:</b> {color}\n"
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Manage Funds:</b> {plan_emoji} Level {loss_streak + 1} (x{multiplier})\n"
        f"📢 <i>Join: {TARGET_CHANNEL}</i>"
    )

def format_result(issue, result_type, result_num, result_color, pred_type, is_win):
    if is_win:
        streak = state.stats['streak_win']
        header = "✅ 𝐖𝐈𝐍 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋 ✅"
        body_emoji = "🤑"
        profit_text = f"Profit Added! (Streak: {streak})"
    else:
        header = "❌ 𝐋𝐎𝐒𝐒 - 𝐍𝐄𝐗𝐓 𝐋𝐄𝐕𝐄𝐋 ❌"
        body_emoji = "⚠️"
        profit_text = "Use 3X Plan Next Round"

    color_blob = "🟢" if "Green" in result_color else "🔴" if "Red" in result_color else "🟣"
    
    return (
        f"<b>{header}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {result_num} {color_blob} ({result_type})\n"
        f"🎯 <b>Your Pick:</b> {pred_type}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{body_emoji} <b>Status:</b> {profit_text}\n"
        f"👤 <b>Official:</b> DK MENTOR MARUF"
    )

def format_summary():
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    accuracy = 0
    if (wins + losses) > 0:
        accuracy = int((wins / (wins + losses)) * 100)
        
    return (
        f"🛑 <b>SESSION CLOSED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>Total Wins:</b> {wins}\n"
        f"💔 <b>Total Loss:</b> {losses}\n"
        f"📈 <b>Accuracy:</b> {accuracy}%\n"
        f"<i>Thank you for playing with DK Maruf!</i>"
    )

# ================= GAME LOOP =================

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    while state.is_running:
        try:
            data_list = fetch_latest_issue(state.game_mode)
            if not data_list:
                await asyncio.sleep(2)
                continue
            
            latest = data_list[0]
            latest_issue = latest['issueNumber']
            latest_result_num = int(latest['number'])
            latest_result_type = "BIG" if latest_result_num >= 5 else "SMALL"
            
            # Color calculation for Result
            latest_color_res = "🟣 Violet" if latest_result_num in [0, 5] else ("🟢 Green" if latest_result_num in [1,3,7,9] else "🔴 Red")
            
            next_issue = str(int(latest_issue) + 1)

            # --- PROCESS RESULT ---
            if state.active_prediction and state.active_prediction['period'] == latest_issue:
                pred_type = state.active_prediction['type']
                is_win = (pred_type == latest_result_type)
                
                # Update Stats
                if is_win: 
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                else: 
                    state.stats["losses"] += 1
                    state.stats["streak_loss"] += 1
                    state.stats["streak_win"] = 0
                
                # Send Sticker
                try:
                    sticker = None
                    if is_win:
                        streak = state.stats['streak_win']
                        if streak in STICKERS['SUPER_WIN']:
                            sticker = STICKERS['SUPER_WIN'][streak]
                        elif latest_result_type == "BIG":
                            sticker = STICKERS['WIN_BIG_RES']
                        else:
                            sticker = STICKERS['WIN_SMALL_RES']
                    else:
                        sticker = random.choice(STICKERS['LOSS'])
                    
                    if sticker:
                        await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=sticker)
                except: pass

                # Send Result Message
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_result(latest_issue, latest_result_type, latest_result_num, latest_color_res, pred_type, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_prediction = None
                state.last_period_processed = latest_issue

            # --- PREPARE NEXT SIGNAL ---
            if state.active_prediction is None and state.last_period_processed != next_issue:
                # History Pattern তৈরি করা
                history_types = []
                for item in data_list[:5]: # লাস্ট ৫ টা
                    num = int(item['number'])
                    t = "BIG" if num >= 5 else "SMALL"
                    history_types.append(t)
                
                # AI Prediction Logic
                pred_type = analyze_and_predict(history_types)
                pred_color = get_color_for_size(pred_type)
                
                state.active_prediction = {
                    "period": next_issue,
                    "type": pred_type,
                    "color": pred_color
                }
                
                await asyncio.sleep(2) # একটু সময় নিয়ে পাঠানো যাতে রিয়েল মনে হয়
                
                # 1. Prediction Sticker
                try:
                    s = STICKERS['BIG_PRED'] if pred_type == "BIG" else STICKERS['SMALL_PRED']
                    await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=s)
                except: pass

                # 2. Prediction Message (High Quality)
                try:
                    await context.bot.send_message(
                        chat_id=TARGET_CHANNEL,
                        text=format_signal(next_issue, pred_type, pred_color, state.game_mode),
                        parse_mode=ParseMode.HTML
                    )
                except: pass

            await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Access Denied!")
        return
        
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Sir!</b>\nSystem is Ready.\nChoose Market:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return

    if state.is_running:
        await update.message.reply_text("⚠️ Bot is already running!")
        return

    msg = update.message.text
    mode = '1M' if '1M' in msg else '30S'
    state.game_mode = mode
    state.is_running = True
    state.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
    state.active_prediction = None
    state.last_period_processed = None
    
    await update.message.reply_text(f"🚀 <b>Connecting to {mode} Server...</b>", parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
    
    # Pre-Session Animation
    try:
        await context.bot.send_sticker(chat_id=TARGET_CHANNEL, sticker=STICKERS['SESSION_START'])
        await asyncio.sleep(1)
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=f"🟢 <b>OFFICIAL SESSION STARTED</b>\nMarket: WinGo {mode}\nAdmin: DK MENTOR MARUF",
            parse_mode=ParseMode.HTML
        )
    except: pass

    context.application.create_task(game_loop(context))

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    state.is_running = False
    await update.message.reply_text("🛑 Stopping Engine...")
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
    
    print("DK Maruf AI System Live...")
    application.run_polling()
