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
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- টোকেন বসান
TARGET_CHANNEL = -1003293007059     # <--- চ্যানেল আইডি

# ================= STICKER DATABASE (ALL FIXED) =================
STICKERS = {
    # আপনার নতুন সিগন্যাল স্টিকার
    'BIG_PRED': "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    
    # আপনার নতুন ২টা WIN স্টিকার
    'WIN_NORMAL': [
        "CAACAgUAAxkBAAEQTp9pcvGaDIa0xIXW6NaMEyrMDYPhMAACNSQAApOucFd1ls-xMEW5FzgE",
        "CAACAgUAAxkBAAEQTqBpcvGaK5dD4qhRRF4aCj1MVxn45gACxBwAArHqkFcaOXk9J8eCIDgE"
    ],
    
    # আপনার নতুন ১টা LOSS স্টিকার
    'LOSS_NORMAL': "CAACAgUAAxkBAAEQTqFpcvGaFnH_vkTDifzqxFjxnzTHwgACjBoAAhh2mFcTQGE0Czq6hzgE",

    # স্টার্ট এবং স্ট্রিক স্টিকার (আগের গুলো)
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
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
    }
}

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF VIP SYSTEM RUNNING..."

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= PREDICTION LOGIC (Pattern) =================
class PredictionEngine:
    def __init__(self):
        self.history = [] 
        self.raw_history = []
    
    def update_history(self, issue_data):
        number = int(issue_data['number'])
        result_type = "BIG" if number >= 5 else "SMALL"
        
        if not self.history or self.raw_history[0]['issueNumber'] != issue_data['issueNumber']:
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:50] 
            self.raw_history = self.raw_history[:50]

    def get_pattern_signal(self):
        if len(self.history) < 6: return random.choice(["BIG", "SMALL"])
        last_6 = self.history[:6]
        
        # 1. Dragon Pattern
        if last_6[0] == last_6[1] == last_6[2]: return last_6[0]
        # 2. ZigZag Pattern
        if last_6[0] != last_6[1]: return "SMALL" if last_6[0] == "BIG" else "BIG"
        
        return last_6[0]

    def calculate_confidence(self):
        return random.randint(88, 99)

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}

state = BotState()

# ================= API FETCH (YOUR 5-LAYER PROXY LOGIC) =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    
    # 5 Layer Protection to bypass block (From your code)
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

# ================= FORMATTING =================
def format_signal(issue, prediction, conf, streak_loss):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    lvl = streak_loss + 1
    amount_x = 3 ** (lvl - 1)
    
    plan_text = f"Start (1X)"
    if lvl > 1: plan_text = f"⚠️ Recovery Stage {lvl-1} ({amount_x}X)"
    if lvl > 4: plan_text = f"🔥 DO OR DIE ({amount_x}X)"

    return (
        f"🛡 <b>DK MARUF PREMIUM V2</b> 🛡\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"📊 <b>Market:</b> {state.game_mode} VIP\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🔥 <b>SIGNAL:</b>  👉 <b>{prediction}</b> 👈\n"
        f"🎨 <b>Color:</b> GREEN {emoji}" if prediction == "BIG" else f"🎨 <b>Color:</b> RED {emoji}\n"
        f"🚀 <b>Confidence:</b> {conf}%\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Plan:</b> {plan_text}\n"
        f"⚡ <b>Maintain 5 Level Funds!</b>\n"
        f"👑 <b>Dev:</b> @dk_mentor_maruf_official"
    )

def format_result(issue, res_num, res_type, my_pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣" 
    
    if is_win:
        w_streak = state.stats['streak_win']
        header = f"🎉 <b>BOOM! WINNER!</b> 🎉"
        status = f"🔥 <b>Win Streak: {w_streak}</b> 🔥"
    else:
        header = f"❌ <b>LOSS / MISS</b> ❌"
        status = f"⚠️ <b>Next 3X Recovery</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"📶 <b>System by DK Maruf</b>"
    )

# ================= ENGINE LOOP =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 Engine Started...")
    
    while state.is_running:
        try:
            # 1. Fetch
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(2)
                continue
                
            latest_issue = latest['issueNumber']
            latest_num = latest['number']
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)
            
            # 2. Process Result
            if state.active_bet and state.active_bet['period'] == latest_issue:
                pick = state.active_bet['pick']
                is_win = (pick == latest_type)
                
                state.engine.update_history(latest)
                
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_win'] += 1
                    state.stats['streak_loss'] = 0
                    
                    # === STICKER LOGIC ===
                    streak = state.stats['streak_win']
                    
                    # Streak Win (2+)
                    if streak in STICKERS['STREAK_WINS']:
                        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['STREAK_WINS'][streak])
                        except: pass
                    else:
                        # Normal Win (1st)
                        try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['WIN_NORMAL']))
                        except: pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    
                    # Normal Loss
                    try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['LOSS_NORMAL'])
                    except: pass

                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # 3. New Signal
            if not state.active_bet and state.last_period_processed != next_issue:
                await asyncio.sleep(2)
                state.engine.update_history(latest)
                
                pred = state.engine.get_pattern_signal()
                conf = state.engine.calculate_confidence()
                
                state.active_bet = {"period": next_issue, "pick": pred}
                
                # Signal Sticker (New)
                s_stk = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_stk)
                except: pass
                
                # Signal Msg
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_signal(next_issue, pred, conf, state.stats['streak_loss']),
                        parse_mode=ParseMode.HTML
                    )
                except: pass

            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome Maruf Boss!</b>\nSelect Server:",
        reply_markup=ReplyKeyboardMarkup([['⚡ Connect 1M', '⚡ Connect 30S'], ['🛑 Stop']], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    if "Stop" in msg:
        state.is_running = False
        await update.message.reply_text("⛔ Bot Stopped.")
        return

    if "Connect" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already Running!")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins":0, "losses":0, "streak_win":0, "streak_loss":0}
        state.engine = PredictionEngine()
        
        await update.message.reply_text(f"✅ <b>Connected to {mode}</b>\nWait for signals...", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
        try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
        except: pass
        
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("off", handle_message))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("DK MARUF FINAL MERGED SYSTEM LIVE...")
    app.run_polling()
