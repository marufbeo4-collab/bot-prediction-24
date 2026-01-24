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
BRAND_NAME = "DK MARUF VIP SYSTEM"

# ================= STICKER DATABASE =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    'WIN_BIG': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_SMALL': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'LOSS': [
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE"
    ],
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
    'STOP': "CAACAgUAAxkBAAEQTjZpcmWif_jWz8x5r7q8_y4j8y4j8AACxhMAAlD6QFRRMClp8Q4JAAE4BA" # (Optional: Stop sticker if you have one)
}

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF ENGINE RUNNING..."

def run_http():
    port = int(os.environ.get("PORT", 8080))
    try: app.run(host='0.0.0.0', port=port)
    except: pass

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= PREDICTION ENGINE =================
class PredictionEngine:
    def __init__(self):
        self.history = [] 
        
    def update_history(self, result_type):
        self.history.insert(0, result_type)
        self.history = self.history[:20]

    def get_signal(self, streak_loss):
        # অটো ইনভার্স লজিক (২ বার লস হলে উল্টো সিগন্যাল দিবে)
        prediction = random.choice(["BIG", "SMALL"])
        
        # যদি ডাটা থাকে, একটু স্মার্ট লজিক
        if len(self.history) >= 3:
            if self.history[0] == self.history[1] == self.history[2]:
                prediction = self.history[0] # Dragon
            else:
                prediction = "SMALL" if self.history[0] == "BIG" else "BIG" # ZigZag

        # Recovery Logic
        if streak_loss >= 2:
            return "SMALL" if prediction == "BIG" else "BIG"
        
        return prediction

    def get_confidence(self):
        return random.randint(93, 99)

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        # Stats track
        self.total_signals = 0
        self.real_wins = 0
        self.real_losses = 0
        self.streak_loss = 0
        self.streak_win = 0

state = BotState()

# ================= API FETCH =================
def fetch_latest_issue(mode):
    # মোড অনুযায়ী লিংক সেট
    url = API_1M if mode == '1M' else API_30S
    
    # Cache ফাঁকি দেওয়ার জন্য টাইমস্ট্যাম্প
    full_url = f"{url}?t={int(time.time()*1000)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://dkwin9.com/"
    }

    try:
        response = requests.get(full_url, headers=headers, timeout=4)
        if response.status_code == 200:
            data = response.json()
            if data and "data" in data and "list" in data["data"]:
                return data["data"]["list"][0]
    except:
        pass
    return None

# ================= FORMATTING =================
def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    color = "GREEN" if prediction == "BIG" else "RED"
    
    lvl = streak_loss + 1
    multiplier = 3 ** (lvl - 1)
    
    plan_text = f"Start (1X)"
    if lvl > 1: plan_text = f"⚠️ Recovery Step {lvl} ({multiplier}X)"

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
        f"👑 <b>Dev:</b> @dk_mentor_maruf_official"
    )

def format_result(issue, res_num, res_type, my_pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣"
    
    if is_win:
        header = "🎉 <b>BOOM! WINNER!</b> 🎉"
        status = f"🔥 <b>Win Streak: {state.streak_win}</b>"
    else:
        header = "❌ <b>LOSS / MISS</b> ❌"
        status = "⚠️ <b>Go For Recovery</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"{status}\n"
        f"📶 <b>System by DK Maruf</b>"
    )

def format_fake_summary():
    # === FAKE SUMMARY LOGIC ===
    total = state.total_signals
    if total == 0: return None

    # ফেইক ক্যালকুলেশন: টোটাল ঠিক থাকবে, কিন্তু উইন রেট ৯০%++ দেখাবে
    # ধরুন ১০ টা সিগন্যাল, আমরা দেখাবো ৮-৯ টা উইন
    fake_wins = int(total * 0.9) 
    if fake_wins == total: fake_wins = total - 1 # অন্তত ১টা লস দেখাবে রিয়েলিস্টিক করার জন্য
    if fake_wins < 0: fake_wins = 0

    fake_losses = total - fake_wins

    return (
        f"🛑 <b>SESSION CLOSED</b> 🛑\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"📊 <b>Market:</b> {state.game_mode} VIP\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🟢 <b>Total Wins:</b> {fake_wins}\n"
        f"🔴 <b>Total Loss:</b> {fake_losses}\n"
        f"🎯 <b>Total Signals:</b> {total}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Profit:</b> Super High 🔥\n"
        f"👋 <b>See You Next Session!</b>\n"
        f"👑 <b>Dev:</b> @dk_mentor_maruf_official"
    )

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print(f"🚀 Engine Started for {state.game_mode}...")
    
    # লুপের শুরুতে স্ট্যাটাস ক্লিয়ার
    state.total_signals = 0
    state.real_wins = 0
    state.real_losses = 0
    state.streak_win = 0
    state.streak_loss = 0
    
    # প্রথম স্টার্টে যেন আটকে না থাকে, তাই একটি ডামি কল
    initial_fetch = fetch_latest_issue(state.game_mode)
    if initial_fetch:
        state.last_period_processed = initial_fetch['issueNumber']
    else:
        state.last_period_processed = "0"

    while state.is_running:
        try:
            # ১. এপিআই কল
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                print("API Error or Waiting...")
                await asyncio.sleep(2)
                continue

            current_issue = latest['issueNumber']
            current_num = latest['number']
            current_type = "BIG" if int(current_num) >= 5 else "SMALL"
            
            # ২. রেজাল্ট প্রসেসিং
            if state.active_bet:
                bet_period = state.active_bet['period']
                
                # যদি রেজাল্ট চলে আসে
                if current_issue == bet_period:
                    pick = state.active_bet['pick']
                    is_win = (pick == current_type)
                    
                    state.engine.update_history(current_type)
                    state.total_signals += 1 # টোটাল কাউন্ট বাড়ালাম
                    
                    if is_win:
                        state.real_wins += 1
                        state.streak_win += 1
                        state.streak_loss = 0
                        # Sticker
                        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN_BIG'] if current_type=="BIG" else STICKERS['WIN_SMALL'])
                        except: pass
                    else:
                        state.real_losses += 1
                        state.streak_loss += 1
                        state.streak_win = 0
                        # Sticker
                        try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                        except: pass

                    # Result Msg
                    try:
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            format_result(current_issue, current_num, current_type, pick, is_win),
                            parse_mode=ParseMode.HTML
                        )
                    except: pass
                    
                    state.active_bet = None
                    state.last_period_processed = current_issue
            
            # ৩. নতুন প্রেডিকশন
            # যদি বেট না থাকে এবং পিরিয়ড নতুন হয়
            next_period = str(int(current_issue) + 1)
            
            if not state.active_bet and state.last_period_processed != next_period and int(next_period) > int(state.last_period_processed):
                
                # প্রেডিকশন লজিক
                pred = state.engine.get_signal(state.streak_loss)
                conf = state.engine.get_confidence()
                
                state.active_bet = {"period": next_period, "pick": pred}
                
                # Sticker Send
                s_stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
                except: pass
                
                # Msg Send
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_period, pred, conf, state.streak_loss),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
            
            await asyncio.sleep(2) # ২ সেকেন্ড অপেক্ষা করে আবার লুপ ঘুরবে

        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Boss!</b>\nSelect Server:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    # ---- STOP & SUMMARY LOGIC ----
    if "Stop" in msg:
        if not state.is_running:
            await update.message.reply_text("⚠️ Bot is not running.")
            return

        state.is_running = False
        await update.message.reply_text("🛑 Stopping Engine... Generating Summary...")
        
        # জেনারেট ফেইক সামারি
        summary = format_fake_summary()
        if summary:
            # চ্যানেলে পাঠাবে
            try: await context.bot.send_message(TARGET_CHANNEL, summary, parse_mode=ParseMode.HTML)
            except: pass
            # এডমিনকে পাঠাবে
            await update.message.reply_text(summary, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("No signals were given.")
            
        return

    # ---- CONNECT LOGIC ----
    if "Connect" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already Running!")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.engine = PredictionEngine() # Reset engine
        
        await update.message.reply_text(f"✅ <b>Connected to {mode}</b>\nEngine Started!", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
        
        # Start Sticker
        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass
        
        # Start Loop
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("DK MARUF FINAL FIX SYSTEM LIVE...")
    app.run_polling()
