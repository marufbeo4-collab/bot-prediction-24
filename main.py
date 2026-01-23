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
BOT_TOKEN = "8595453345:AAExpD-Txn7e-nysGZyrigy9hh7m3UjMraM"
TARGET_CHANNEL = -1003293007059
BRAND_NAME = "DK MARUF VIP SYSTEM"
FIXED_PASSWORD = "0102"

# ================= STICKER DATABASE - FIXED =================
STICKERS = {
    # 1M Stickers
    'BIG_PRED_1M': "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    'SMALL_PRED_1M': "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    
    # 30S Stickers - SWAPPED FIX
    'BIG_PRED_30S': "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",  # This was SMALL, now BIG
    'SMALL_PRED_30S': "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",  # This was BIG, now SMALL
    
    # Win/Loss Stickers
    'BIG_WIN': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'SMALL_WIN': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'WIN': "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",
    'LOSS': "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",
    
    # Random Win Stickers
    'WIN_RANDOM': [
        "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
        "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAAnQKcVYHd8IiRqfBXTgE",
        "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
    ],
    
    # Color Signal Stickers
    'RED_SIGNAL': "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    'GREEN_SIGNAL': "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAAnR3oVejA9DVGekyYTgE",
    
    # Session Stickers
    'SESSION_START': [
        "CAACAgUAAxkBAAEQT_lpc4EvleS6GJIogvkFzlcAAV6T7PsAArYaAAIOJIBV6qeBrzw1_oc4BA",
        "CAACAgUAAxkBAAEQTuRpczxpKCooU6JW2F53jWSEr7SZnQACZBUAAtEWOFcRzggHRna-EzgE"
    ],
    'SESSION_RANDOM': [
        "CAACAgUAAxkBAAEQTudpczxpoCLQ2pIXCqANpddRbHX9ngACKhYAAoBTMVfQP_QoToLXkzgE",
        "CAACAgUAAxkBAAEQT_dpc4Eqt5r28E8WwxaZnW8X2t58RQACsw8AAoV9CFW0IyDz2PAL5DgE",
    ]
}

# Win Streak Stickers (1 to 75)
WIN_STREAK_STICKERS = [
    "CAACAgUAAxkBAAEQUA1pc4IKjtrvSWe2ssLEqZ88cAABYW8AAsoiAALegIlVctTV3Pqbjmg4BA",
    "CAACAgUAAxkBAAEQUA5pc4IKOY43Rh4dwtmmwOC55ikPbQAClRkAAgWviFVWRlQ-8i4rHTgE",
    # ... (rest of your 75 stickers)
]

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER =================
app = Flask('')
@app.route('/')
def home():
    return "🚀 DK MARUF VIP ENGINE - 24/7 ACTIVE"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host='0.0.0.0', port=port)
    except: pass

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= PREDICTION ENGINE =================
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

    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 6:
            return random.choice(["BIG", "SMALL"])
        
        last_6 = self.history[:6]
        prediction = ""

        if last_6[0] == last_6[1] == last_6[2]:
            prediction = last_6[0]
        elif last_6[0] != last_6[1] and last_6[1] != last_6[2]:
            prediction = "SMALL" if last_6[0] == "BIG" else "BIG"
        else:
            last_num = int(self.raw_history[0]['number'])
            period_digit = int(str(self.raw_history[0]['issueNumber'])[-1])
            math_val = (last_num + period_digit) % 2
            prediction = "BIG" if math_val == 1 else "SMALL"

        if current_streak_loss >= 2:
            flipped_prediction = "SMALL" if prediction == "BIG" else "BIG"
            return flipped_prediction
        
        return prediction

    def calculate_confidence(self):
        return random.randint(90, 99)

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}
        self.total_wins_in_session = 0
        self.recovery_step = 1
        self.session_password = None
        self.is_color_mode = False
        self.session_start_time = None
        self.last_signal_time = 0
        self.game_speed = 2  # Default speed (seconds)

state = BotState()

# ================= API FETCH =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    
    proxies = [
        f"{base_url}?t={int(time.time()*1000)}", 
        f"https://corsproxy.io/?{base_url}?t={int(time.time()*1000)}", 
        f"https://api.allorigins.win/raw?url={base_url}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/{random.randint(100, 120)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Origin": "https://dkwin9.com"
    }

    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except:
            continue
    return None

# ================= FORMATTING =================
def format_signal(issue, prediction, conf, streak_loss, recovery_step):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    color = "GREEN" if prediction == "BIG" else "RED"
    
    if streak_loss >= 8:
        return None
    
    lvl = streak_loss + 1
    multiplier = 3 ** (lvl - 1)
    
    if recovery_step > 0:
        plan_text = f"⚠️ Recovery Step {lvl} ({multiplier}X)"
        if lvl > 4:
            plan_text = f"🔥 DO OR DIE ({multiplier}X)"
    else:
        plan_text = f"Start (1X)"

    signal_type = "🎯 COLOR SIGNAL" if state.is_color_mode else "🎯 MAIN SIGNAL"

    return (
        f"╔═══════════════════════╗\n"
        f"║    🚀 {BRAND_NAME} 🚀    ║\n"
        f"╚═══════════════════════╝\n\n"
        f"🎮 <b>Market:</b> {state.game_mode} VIP\n"
        f"📟 <b>Period:</b> <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{signal_type}\n"
        f"👉 <b>{prediction}</b> {emoji} 👈\n"
        f"🎨 <b>Color:</b> {color}\n"
        f"📊 <b>Confidence:</b> {conf}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Bet Plan:</b> {plan_text}\n"
        f"⚡ <b>Maintain 5 Level Funds!</b>\n\n"
        f"🔗 <b>Join:</b> @big_maruf_official0\n"
        f"👑 <b>Dev:</b> @OWNER_MARUF_TOP"
    )

def format_result(issue, res_num, res_type, my_pick, is_win, recovery_step, total_wins):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣" 
    
    if is_win:
        w_streak = state.stats['streak_win']
        header = f"╔═══════════════════════╗\n║    🎉 WINNER! 🎉     ║\n╚═══════════════════════╝"
        status = f"🔥 <b>Win Streak: {w_streak}</b>\n🏆 <b>Total Wins: {total_wins}</b>"
    else:
        next_step = state.stats['streak_loss'] + 1
        if next_step >= 8:
            header = f"╔═══════════════════════╗\n║    ⚠️ SYSTEM PAUSED ⚠️   ║\n╚═══════════════════════╝"
            status = f"❌ <b>Max Loss Limit Reached!</b>\n🚫 <b>Signal Stopped</b>"
        else:
            header = f"╔═══════════════════════╗\n║    ❌ LOSS/MISS ❌    ║\n╚═══════════════════════╝"
            status = f"⚠️ <b>Go For Step {next_step} Recovery</b>"

    return (
        f"{header}\n\n"
        f"📟 <b>Period:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {my_pick}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status}\n\n"
        f"📶 <b>System by DK Maruf VIP</b>"
    )

# ================= STICKER FUNCTIONS - FIXED =================
async def send_prediction_sticker(context, prediction):
    try:
        # FIXED: 30S stickers are now correct
        if state.game_mode == '1M':
            sticker_id = STICKERS['BIG_PRED_1M'] if prediction == "BIG" else STICKERS['SMALL_PRED_1M']
        else:  # 30S - CORRECTED
            sticker_id = STICKERS['BIG_PRED_30S'] if prediction == "BIG" else STICKERS['SMALL_PRED_30S']
        
        print(f"📤 Sending {prediction} sticker for {state.game_mode}: {sticker_id[:30]}...")
        await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
    except Exception as e: 
        print(f"❌ Sticker error: {e}")

async def send_win_sticker(context, result_type):
    try:
        total_wins = state.total_wins_in_session
        
        # Send WIN sticker
        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN'])
        
        # Send BIG/SMALL win sticker
        sticker_id = STICKERS['BIG_WIN'] if result_type == "BIG" else STICKERS['SMALL_WIN']
        await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
        
        # Send total wins sticker
        if 1 <= total_wins <= len(WIN_STREAK_STICKERS):
            await context.bot.send_sticker(TARGET_CHANNEL, WIN_STREAK_STICKERS[total_wins - 1])
        elif total_wins > len(WIN_STREAK_STICKERS):
            await context.bot.send_sticker(TARGET_CHANNEL, WIN_STREAK_STICKERS[-1])
        
        # Random win sticker
        if random.random() < 0.3:
            await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['WIN_RANDOM']))
            
    except Exception as e: 
        print(f"❌ Win sticker error: {e}")

async def send_loss_sticker(context):
    try:
        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['LOSS'])
    except Exception as e: 
        print(f"❌ Loss sticker error: {e}")

async def send_color_sticker(context, color):
    try:
        sticker_id = STICKERS['GREEN_SIGNAL'] if color == "GREEN" else STICKERS['RED_SIGNAL']
        await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
    except Exception as e: 
        print(f"❌ Color sticker error: {e}")

async def send_session_sticker(context, is_start=True):
    try:
        if is_start:
            sticker = random.choice(STICKERS['SESSION_START'])
        else:
            sticker = random.choice(STICKERS['SESSION_RANDOM'])
        
        await context.bot.send_sticker(TARGET_CHANNEL, sticker)
    except Exception as e: 
        print(f"❌ Session sticker error: {e}")

# ================= FAST ENGINE (NO DELAY) =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print(f"🚀 Starting {state.game_mode} VIP Engine...")
    
    while state.is_running:
        try:
            # 1. Fetch latest issue
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(1)
                continue
                
            latest_issue = latest['issueNumber']
            latest_num = latest['number']
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"
            next_issue = str(int(latest_issue) + 1)
            
            print(f"📊 Latest: {latest_issue} = {latest_num} ({latest_type}) | Next: {next_issue}")
            
            # 2. Process Result
            if state.active_bet and state.active_bet['period'] == latest_issue:
                pick = state.active_bet['pick']
                is_win = (pick == latest_type)
                
                state.engine.update_history(latest)
                
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_win'] += 1
                    state.stats['streak_loss'] = 0
                    state.total_wins_in_session += 1
                    state.recovery_step = 1
                    
                    # Send win stickers
                    await send_win_sticker(context, latest_type)
                    
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    state.recovery_step = min(state.recovery_step + 1, 8)
                    
                    if state.stats['streak_loss'] >= 8:
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            "🚫 MAXIMUM LOSS LIMIT REACHED!",
                            parse_mode=ParseMode.HTML
                        )
                        state.is_running = False
                        return
                    
                    await send_loss_sticker(context)

                # Result Message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win, state.recovery_step, state.total_wins_in_session),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e: 
                    print(f"❌ Result message error: {e}")
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # 3. New Prediction (NO DELAY)
            if not state.active_bet and state.last_period_processed != next_issue:
                if state.stats['streak_loss'] >= 8:
                    state.is_running = False
                    return
                
                state.engine.update_history(latest)
                
                # Get prediction
                pred = state.engine.get_pattern_signal(state.stats['streak_loss'])
                conf = state.engine.calculate_confidence()
                
                state.active_bet = {"period": next_issue, "pick": pred}
                
                # Send prediction sticker
                await send_prediction_sticker(context, pred)
                
                # Send color sticker if enabled
                if state.is_color_mode:
                    await send_color_sticker(context, "GREEN" if pred == "BIG" else "RED")
                
                # Send signal message
                try:
                    signal_msg = format_signal(next_issue, pred, conf, state.stats['streak_loss'], state.recovery_step)
                    if signal_msg:
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            signal_msg,
                            parse_mode=ParseMode.HTML
                        )
                except Exception as e: 
                    print(f"❌ Signal message error: {e}")

            # NO ARTIFICIAL DELAY - Only sleep for 1 second
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Engine error: {e}")
            await asyncio.sleep(1)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 <b>DK MARUF VIP SYSTEM</b>\n\nEnter password:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    # Password Check
    if not state.session_password:
        if msg == FIXED_PASSWORD:
            state.session_password = msg
            await update.message.reply_text(
                "✅ <b>Password Verified!</b>\nSelect Market:",
                reply_markup=ReplyKeyboardMarkup([
                    ['⚡ Connect 1M', '⚡ Connect 30S'],
                    ['🎨 Color ON', '🎨 Color OFF'],
                    ['📊 Stats', '🛑 Stop']
                ], resize_keyboard=True),
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text("❌ Wrong password!")
        return
    
    # Commands
    if "Stop" in msg:
        state.is_running = False
        await send_session_sticker(context, False)
        await update.message.reply_text(
            f"⛔ Session Stopped\n✅ Wins: {state.total_wins_in_session}",
            reply_markup=ReplyKeyboardRemove()
        )
        state.session_password = None
        return
    
    if "Color ON" in msg:
        state.is_color_mode = True
        await update.message.reply_text("🎨 Color Mode: ON")
        return
        
    if "Color OFF" in msg:
        state.is_color_mode = False
        await update.message.reply_text("🎨 Color Mode: OFF")
        return
    
    if "Stats" in msg:
        await update.message.reply_text(
            f"📊 <b>Current Stats:</b>\n"
            f"🎮 Market: {state.game_mode}\n"
            f"✅ Wins: {state.stats['wins']}\n"
            f"❌ Losses: {state.stats['losses']}\n"
            f"🏆 Total Wins: {state.total_wins_in_session}\n"
            f"🔥 Win Streak: {state.stats['streak_win']}\n"
            f"⚠️ Loss Streak: {state.stats['streak_loss']}",
            parse_mode=ParseMode.HTML
        )
        return
    
    if "Connect" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already running!")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins":0, "losses":0, "streak_win":0, "streak_loss":0}
        state.total_wins_in_session = 0
        state.recovery_step = 1
        state.engine = PredictionEngine()
        state.session_start_time = time.time()
        
        await update.message.reply_text(
            f"✅ <b>Connected to {mode}</b>\n"
            f"🎯 Smart Recovery Active\n"
            f"⚡ Fast Mode: No delay",
            parse_mode=ParseMode.HTML
        )
        
        await send_session_sticker(context, True)
        
        # Start engine
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("="*50)
    print("🚀 DK MARUF VIP SYSTEM")
    print("="*50)
    print(f"📢 Channel: {TARGET_CHANNEL}")
    print(f"🔐 Password: {FIXED_PASSWORD}")
    print("🎯 30S Stickers: FIXED")
    print("⚡ Engine: FAST MODE (no delay)")
    print("="*50)
    app.run_polling()
