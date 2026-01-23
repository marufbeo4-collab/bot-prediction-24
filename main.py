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
# আপনার বট টোকেন এবং চ্যানেল আইডি এখানে বসান
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI" 
TARGET_CHANNEL = "-1003293007059"

# ================= STICKER DATABASE (UPDATED) =================
# আপনার দেওয়া স্টিকার আইডি গুলো এখানে ইন্টিগ্রেট করা হয়েছে
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    
    # সাধারণ উইন এবং লস
    'WIN_GENERIC': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'LOSS': [
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
        "CAACAgUAAxkBAAEQTh5pcmTbrSEe58RRXvtu_uwEAWZoQQAC5BEAArgxYVUhMlnBGKmcbzgE"
    ],
    
    # স্ট্রিক উইন স্টিকার (আপনার লিস্ট অনুযায়ী)
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

# API LINKS
API_URLS = {
    '1M': "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    '30S': "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
    '5M': "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json"
}

# ================= FLASK SERVER (KEEP ALIVE) =================
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF VIP SYSTEM V2.0 RUNNING..."

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= ADVANCED LOGIC ENGINE =================
class PredictionEngine:
    def __init__(self):
        self.history = [] # Stores 'BIG' or 'SMALL'
        self.raw_history = [] # Stores full issue data
    
    def update_history(self, issue_data):
        number = int(issue_data['number'])
        result_type = "BIG" if number >= 5 else "SMALL"
        
        # ডুপ্লিকেট এড়াতে চেক
        if not self.history or self.raw_history[0]['issueNumber'] != issue_data['issueNumber']:
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            # মেমোরি সেভের জন্য ৫০টার বেশি ডাটা রাখবো না
            self.history = self.history[:50] 
            self.raw_history = self.raw_history[:50]

    def get_pattern_signal(self):
        """
        এখানে আমরা কমপ্লেক্স প্যাটার্ন চেক করবো।
        """
        if len(self.history) < 10:
            return random.choice(["BIG", "SMALL"]) # পর্যাপ্ত ডাটা না থাকলে র‍্যান্ডম
        
        last_6 = self.history[:6]
        
        # 1. Dragon Pattern (টানা ৪+ একই কালার)
        if last_6[0] == last_6[1] == last_6[2] == last_6[3]:
            # ড্রাগন প্যাটার্ন চললে আমরা ট্রেন্ডের সাথেই থাকবো
            return last_6[0]
            
        # 2. ZigZag Pattern (ABABAB) - এখানে ব্রেক হওয়ার চান্স বেশি
        if last_6[0] != last_6[1] and last_6[1] != last_6[2] and last_6[2] != last_6[3]:
            # যদি ৩ বারের বেশি জিগজ্যাগ হয়, তবে এবার জিগজ্যাগ ফলো করবে
            if last_6[0] == "BIG": return "SMALL"
            else: return "BIG"

        # 3. AABB Pattern (2 Big, 2 Small)
        if last_6[0] == last_6[1] and last_6[2] == last_6[3] and last_6[1] != last_6[2]:
            # প্যাটার্ন অনুযায়ী এখন চেঞ্জ হওয়ার কথা
            if last_6[0] == "BIG": return "SMALL"
            else: return "BIG"
            
        # 4. 1-2-1 Pattern (A B B A)
        if last_6[0] != last_6[1] and last_6[1] == last_6[2] and last_6[2] != last_6[3]:
             return last_6[0] # আগেরটাই রিপিট হবে

        # ডিফল্ট লজিক: মেজরিটি ভোট (গত ৫ বারে যেটা বেশি এসেছে তার বিপরীত বা পক্ষে)
        big_count = last_6[:5].count("BIG")
        if big_count >= 3: 
            return "SMALL" # Trend Reversal try
        else:
            return "BIG"

    def calculate_confidence(self):
        """সিগন্যাল কতটা শক্তিশালী তার পার্সেন্টেজ"""
        if len(self.history) < 5: return 50
        
        # সহজ লজিক: লাস্ট রেজাল্ট যদি আগের প্যাটার্নের সাথে মিলে যায়, কনফিডেন্স বেশি
        last = self.history[0]
        if self.history.count(last) > 3: return 90 # স্ট্রং ট্রেন্ড
        if self.history[0] != self.history[1]: return 75 # জিগজ্যাগ
        return 60

# ================= BOT STATE MANAGEMENT =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None # {period, pick, stage}
        self.last_period_processed = None
        
        # স্ট্যাটিসটিক্স
        self.wins = 0
        self.losses = 0
        self.current_streak = 0
        self.recovery_stage = 1 # 1 = 1x, 2 = 3x, 3 = 9x ...

state = BotState()

# ================= HELPER FUNCTIONS =================
def get_proxied_request(url):
    """শক্তিশালী API ফেচার যা সহজে ব্লক হবে না"""
    headers = {
        "User-Agent": f"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.0.0 Mobile Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Accept": "application/json"
    }
    
    # টাইমস্ট্যাম্প দিয়ে ক্যাশ বাইপাস
    final_url = f"{url}?t={int(time.time()*1000)}"
    
    try:
        # মেইন রিকোয়েস্ট
        req = requests.get(final_url, headers=headers, timeout=5)
        if req.status_code == 200: return req.json()
    except:
        pass
    
    return None

def get_bet_amount(stage):
    if stage == 1: return "100-500 TK"
    elif stage == 2: return "300-1500 TK (3X)"
    elif stage == 3: return "900-4500 TK (9X)"
    elif stage == 4: return "2700-13500 TK (27X)"
    else: return "🔥 MAX BET (Recover All)"

# ================= MESSAGE FORMATTING =================
def format_signal_msg(period, prediction, confidence, stage):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    color_txt = "GREEN" if prediction == "BIG" else "RED"
    
    # রিকভারি অনুযায়ী ইনভেস্টমেন্ট প্ল্যান
    invest = "Start (1X)"
    if stage > 1: invest = f"Recovery Level {stage-1} ({3**(stage-1)}X)"
    
    return (
        f"🛡 <b>DK MARUF PREMIUM V2</b> 🛡\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"📊 <b>Market:</b> {state.game_mode}\n"
        f"🆔 <b>Period:</b> <code>{period}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔥 <b>SIGNAL:</b>  {emoji} <b>{prediction}</b> {emoji}\n"
        f"🎨 <b>Color:</b> {color_txt}\n"
        f"🚀 <b>Confidence:</b> {confidence}%\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Strategy:</b> {invest}\n"
        f"💵 <b>Bet:</b> {get_bet_amount(stage)}\n"
        f"⚡ <i>Maintain Level 5 Funds!</i>\n"
        f"👑 <b>Dev:</b> @dk_mentor_maruf_official"
    )

def format_result_msg(period, result_num, result_type, my_pick, is_win):
    res_emoji = "🟢" if result_type == "BIG" else "🔴"
    if int(result_num) in [0, 5]: res_emoji = "🟣" # Violet
    
    if is_win:
        header = "🎉 <b>CONGRATULATIONS</b> 🎉"
        status = f"✅ <b>WIN! WIN! WIN!</b>"
        streak_txt = f"🔥 <b>Running Streak: {state.current_streak}</b>"
    else:
        header = "⚠️ <b>MISS / LOSS</b> ⚠️"
        status = "❌ <b>Prediction Failed</b>"
        streak_txt = "🔄 <b>Starting Recovery...</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{period}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {result_num} ({result_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"{streak_txt}\n"
        f"📶 <b>System by DK Maruf</b>"
    )

# ================= MAIN GAME LOOP =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 Premium Engine Started...")
    
    while state.is_running:
        try:
            # ১. ডাটা আনা
            url = API_URLS.get(state.game_mode, API_URLS['1M'])
            data = get_proxied_request(url)
            
            if not data or 'data' not in data:
                await asyncio.sleep(2)
                continue
                
            latest_item = data['data']['list'][0]
            latest_issue = latest_item['issueNumber']
            
            # ২. রেজাল্ট প্রসেসিং (যদি বেট ধরা থাকে)
            if state.active_bet and state.active_bet['period'] == latest_issue:
                # রেজাল্ট চেক
                actual_num = latest_item['number']
                actual_type = "BIG" if int(actual_num) >= 5 else "SMALL"
                
                is_win = (state.active_bet['pick'] == actual_type)
                
                # স্ট্যাটস আপডেট
                state.engine.update_history(latest_item)
                
                if is_win:
                    state.wins += 1
                    state.current_streak += 1
                    state.recovery_stage = 1 # উইন হলে স্টেজ রিসেট
                    
                    # স্টিকার সিলেকশন (লজিক: স্ট্রিক অনুযায়ী)
                    sticker_to_send = STICKERS['WIN_GENERIC']
                    if state.current_streak in STICKERS['STREAK_WINS']:
                        sticker_to_send = STICKERS['STREAK_WINS'][state.current_streak]
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, sticker_to_send)
                    except: pass
                    
                else:
                    state.losses += 1
                    state.current_streak = 0
                    state.recovery_stage += 1 # লস হলে স্টেজ বাড়বে
                    
                    # লস স্টিকার
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['LOSS']))
                    except: pass

                # রেজাল্ট মেসেজ
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result_msg(latest_issue, actual_num, actual_type, state.active_bet['pick'], is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # ৩. নতুন সিগন্যাল জেনারেট করা
            next_period = str(int(latest_issue) + 1)
            
            if not state.active_bet and state.last_period_processed != latest_issue:
                # ডাটা সিঙ্ক করার জন্য একটু ওয়েট
                await asyncio.sleep(2)
                
                # হিস্ট্রি আপডেট (যদি মিস হয়ে থাকে)
                state.engine.update_history(latest_item)
                
                # প্রেডিকশন
                prediction = state.engine.get_pattern_signal()
                confidence = state.engine.calculate_confidence()
                
                # অটো-স্কিপ লজিক (কনফিডেন্স খুব কম হলে)
                if confidence < 40 and state.recovery_stage == 1:
                    print("Skipping due to low confidence...")
                    # স্কিপ করলে আমরা জাস্ট ওয়েট করবো, মেসেজ দিবো না
                    state.last_period_processed = latest_issue 
                    continue

                state.active_bet = {
                    "period": next_period,
                    "pick": prediction,
                    "stage": state.recovery_stage
                }
                
                # সিগন্যাল স্টিকার
                s_sticker = STICKERS['BIG_PRED'] if prediction == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_sticker)
                except: pass
                
                # সিগন্যাল মেসেজ
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal_msg(next_period, prediction, confidence, state.recovery_stage),
                        parse_mode=ParseMode.HTML
                    )
                except: pass

            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"Error in Loop: {e}")
            await asyncio.sleep(5)

# ================= TELEGRAM HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 <b>Welcome {user} Boss!</b>\n"
        "I am Ready with Premium Logic.\nSelect Server:",
        reply_markup=ReplyKeyboardMarkup([['🚀 Wingo 1M', '🚀 Wingo 30S'], ['🛑 Stop Bot']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    if "Stop" in msg:
        state.is_running = False
        await update.message.reply_text("⛔ Bot Stopped.", reply_markup=ReplyKeyboardRemove())
        return

    if "Wingo" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Bot is already running!")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.current_streak = 0
        state.recovery_stage = 1
        
        # রিসেট হিস্ট্রি
        state.engine = PredictionEngine()
        
        await update.message.reply_text(f"✅ <b>Connected to {mode} VIP Server</b>", parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass
        
        # ব্যাকগ্রাউন্ড টাস্ক শুরু
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("DK MARUF VIP BOT IS LIVE...")
    app.run_polling()
