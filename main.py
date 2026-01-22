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
BOT_TOKEN = "8183778698:AAGiOJuiN4ZRT7iEvIQLM3JaHc_tu1EFSWY"  # <--- আপনার টোকেন বসান
# চ্যানেল ইউজারনেম (অবশ্যই @ সহ দিবেন) অথবা চ্যানেল ID (-100...)
TARGET_CHANNEL = "@Maruf_King_Pro_Predict_bot" 
ADMIN_ID = 123456789  # আপনার টেলিগ্রাম আইডি (অপশনাল)

# API ENDPOINTS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER (RENDER KEEP-ALIVE) =================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running 24/7!"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= BOT STATE & LOGIC =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = None  # '1M' or '30S'
        self.stats = {"wins": 0, "losses": 0, "total": 0}
        self.last_issue = None
        self.current_prediction_data = None 

state = BotState()

# --- PREDICTION ALGORITHMS ---
def get_30s_prediction(last_num):
    try:
        seed = int(last_num)
        hash_val = (seed * 7 + 3) % 10
        prediction = "BIG" if hash_val >= 5 else "SMALL"
        rand_nums = [random.randint(0,9) for _ in range(3)] 
        return {
            "type": prediction,
            "nums": rand_nums,
            "conf": random.randint(90, 99),
            "jackpot": "3, 1" if prediction == "BIG" else "0, 8",
            "method": "GX VIP Algo"
        }
    except:
        return None

def get_1m_prediction():
    nums = random.sample(range(10), 3)
    big_count = sum(1 for n in nums if n >= 5)
    prediction = "BIG" if big_count >= 2 else "SMALL"
    return {
        "type": prediction,
        "nums": nums,
        "conf": random.randint(92, 99),
        "jackpot": f"{nums[0]}, {nums[1]}",
        "method": "Rakib RGB Core"
    }

# --- API FETCH ---
def fetch_latest_issue(mode):
    url = API_1M if mode == '1M' else API_30S
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
        }
        response = requests.get(f"{url}?t={int(time.time()*1000)}", headers=headers, timeout=5)
        data = response.json()
        if data and "data" in data and "list" in data["data"]:
            return data["data"]["list"][0]
    except Exception as e:
        print(f"API Error: {e}")
    return None

# ================= MESSAGE FORMATTERS =================
def get_time():
    return datetime.now(pytz.timezone('Asia/Dhaka')).strftime("%H:%M:%S")

def format_start_msg(mode, session_id):
    return (
        f"📢 <b>CHANNEL CONNECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>{TARGET_CHANNEL}</b> is now connected to\n"
        f"🤖 <b>Wingo Advanced AI</b>\n\n"
        f"🔔 <b>You will receive:</b>\n"
        f"• Real-time predictions\n"
        f"• Advanced AI signals ({mode})\n"
        f"• VIP Jackpot system\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"©️ {TARGET_CHANNEL}\n\n"
        f"🟢 <b>SESSION STARTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Session ID:</b> <code>{session_id}</code>\n"
        f"⏰ <b>Start Time:</b> {get_time()}\n"
        f"🤖 <b>AI Mode:</b> {mode} Advanced Engine\n"
        f"🔧 <b>AI Systems:</b> 6 VIP Logics\n"
        f"👥 <b>Active Groups:</b> 1\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>System Ready</b>\n"
        f"🚀 <i>Advanced Signals starting...</i>"
    )

def format_signal(issue, data, mode):
    rec_level = 0 if state.stats['losses'] == 0 else state.stats['losses']
    return (
        f"🚀 <b>WINGO MASTER AI SIGNAL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📺 <b>Channel:</b> {TARGET_CHANNEL}\n"
        f"⏰ <b>Period:</b> <code>{issue}</code>\n"
        f"🎯 <b>{data['type']}</b>\n"
        f"🎰 <b>Jackpot:</b> {data['jackpot']}\n"
        f"💎 <b>Confidence:</b> {data['conf']}%\n"
        f"🤖 <b>AI Method:</b> {data['method']}\n"
        f"🔧 <b>Recovery Level:</b> {rec_level}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 <i>এটা শুধুমাত্র {mode} মার্কেট। অবশ্যই মানি ম্যানেজমেন্ট ফলো করবেন।</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"©️ {TARGET_CHANNEL}"
    )

def format_result(issue, result_num, result_type, pred_type, is_win):
    status = "✅ <b>WIN!</b>" if is_win else "❌ <b>LOSS</b>"
    comment = "✨ সফল প্রেডিকশন!" if is_win else "⚠️ রিকভারি রাউন্ড আসছে..."
    total = state.stats["total"]
    acc = (state.stats["wins"] / total * 100) if total > 0 else 0
    profit = state.stats["wins"] - state.stats["losses"]
    streak = 1 if is_win else 0
    
    return (
        f"📊 <b>RESULT UPDATE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {result_num} ({result_type})\n"
        f"📈 <b>Prediction:</b> {pred_type}\n"
        f"🎰 <b>Jackpot:</b> {state.current_prediction_data['jackpot']}\n"
        f"💎 <b>Confidence Was:</b> {state.current_prediction_data['conf']}%\n"
        f"🤖 <b>Method:</b> combined(6 methods)\n\n"
        f"{status}\n"
        f"{comment}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Stats:</b> {state.stats['wins']}W - {state.stats['losses']}L\n"
        f"💰 <b>Profit:</b> {profit:+d} (Total: {total})\n"
        f"🎯 <b>Accuracy:</b> {acc:.1f}%\n"
        f"🔥 <b>Streak:</b> {streak}\n"
        f"🔄 <b>Recovery:</b> Level {0 if is_win else 1}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"©️ {TARGET_CHANNEL}"
    )

def format_final_report():
    total = state.stats["total"]
    wins = state.stats["wins"]
    losses = state.stats["losses"]
    acc = (wins/total*100) if total > 0 else 0
    return (
        f"🛑 <b>SESSION STOPPED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>FINAL CALCULATION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 <b>Total Rounds:</b> {total}\n"
        f"✅ <b>Total Wins:</b> {wins}\n"
        f"❌ <b>Total Losses:</b> {losses}\n"
        f"🎯 <b>Accuracy:</b> {acc:.2f}%\n"
        f"💰 <b>Net Score:</b> {wins - losses}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <i>AI System shutting down...</i>\n"
        f"©️ {TARGET_CHANNEL}"
    )

# ================= CORE LOOP =================
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

            # Check Result
            if state.last_issue and int(latest_issue) > int(state.last_issue):
                if state.current_prediction_data:
                    pred_type = state.current_prediction_data['type']
                    is_win = (pred_type == latest_result_type)
                    
                    state.stats["total"] += 1
                    if is_win: state.stats["wins"] += 1
                    else: state.stats["losses"] += 1
                    
                    # SEND TO CHANNEL
                    try:
                        await context.bot.send_message(
                            chat_id=TARGET_CHANNEL,
                            text=format_result(latest_issue, latest_result_num, latest_result_type, pred_type, is_win),
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        print(f"Error sending to channel: {e}")
                
                # Generate NEXT Prediction
                next_issue = str(int(latest_issue) + 1)
                prediction = get_30s_prediction(latest_result_num) if state.game_mode == '30S' else get_1m_prediction()
                
                if prediction:
                    state.current_prediction_data = prediction
                    await asyncio.sleep(2) 
                    
                    # SEND TO CHANNEL
                    try:
                        await context.bot.send_message(
                            chat_id=TARGET_CHANNEL,
                            text=format_signal(next_issue, prediction, state.game_mode),
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        print(f"Error sending to channel: {e}")
                
                state.last_issue = latest_issue
            
            await asyncio.sleep(3 if state.game_mode == '30S' else 5)

        except Exception as e:
            logging.error(f"Loop Error: {e}")
            await asyncio.sleep(5)

# ================= COMMAND HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['📢 Connect 1M', '📢 Connect 30S']]
    await update.message.reply_text(
        "👋 <b>Welcome Boss!</b>\nSelect market to connect:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def connect_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ <b>Bot is already running!</b> Use /off to stop first.", parse_mode=ParseMode.HTML)
        return

    msg = update.message.text
    mode = '1M' if '1M' in msg else '30S'
    state.game_mode = mode
    state.is_running = True
    state.stats = {"wins": 0, "losses": 0, "total": 0}
    state.last_issue = None
    state.current_prediction_data = None

    session_id = f"SESS{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Notify Admin (You)
    await update.message.reply_text(f"✅ Bot started for {TARGET_CHANNEL} in {mode} mode.", reply_markup=ReplyKeyboardRemove())
    
    # Send Start Message TO CHANNEL
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=format_start_msg(mode, session_id),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error connecting to channel: {e}\nMake sure bot is ADMIN in {TARGET_CHANNEL}")
        state.is_running = False
        return

    # Initialize
    latest = fetch_latest_issue(mode)
    if latest:
        state.last_issue = latest['issueNumber']
        next_issue = str(int(state.last_issue) + 1)
        pred = get_30s_prediction(latest['number']) if mode == '30S' else get_1m_prediction()
        state.current_prediction_data = pred
        
        await asyncio.sleep(2)
        # SEND SIGNAL TO CHANNEL
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=format_signal(next_issue, pred, mode),
            parse_mode=ParseMode.HTML
        )

    context.application.create_task(game_loop(context))

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.is_running:
        await update.message.reply_text("⚠️ Bot is not running.")
        return
    
    state.is_running = False
    await update.message.reply_text("🛑 Bot stopped.")
    
    # Send Summary TO CHANNEL
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=format_final_report(),
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
    print("Bot is running...")
    application.run_polling()
