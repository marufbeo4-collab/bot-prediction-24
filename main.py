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

# ================= ⚙️ CONFIGURATION ⚙️ =================
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- আপনার টোকেন
TARGET_CHANNEL = "-1003293007059"   # <--- আপনার চ্যানেল আইডি
ADMIN_ID = 123456789  # <--- আপনার টেলিগ্রাম ID (কন্ট্রোলের জন্য)

# ================= 🎨 STICKER ASSETS =================
STICKERS = {
    'BIG': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    'WIN': [
        "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
        "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE"
    ],
    'LOSS': "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
    'START': "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
}

# ================= 🌐 API NETWORK =================
API_URLS = [
    "https://draw.ar-lottery01.com/WinGo/WinGo_{mode}/GetHistoryIssuePage.json",
    "https://api.bdg88zf.com/WinGo/WinGo_{mode}/GetHistoryIssuePage.json",
    "https://dkwin9.com/api/WinGo/WinGo_{mode}/GetHistoryIssuePage.json"
]

# ================= 🖥️ WEB SERVER =================
from flask import Flask
app = Flask('')

@app.route('/')
def home(): return "DK MARUF SUPER AI RUNNING..."

def run_http(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_http).start()

# ================= 🧠 BRAIN & STATE =================
class AdvancedBotState:
    def __init__(self):
        self.running = False
        self.mode = '1M'
        self.history = []
        # Stats
        self.stats = {"wins": 0, "losses": 0, "streak": 0}
        # Control
        self.manual_override = None # এডমিন যা সেট করবে তাই দিবে
        self.force_win_mode = True  # লস হলেও স্ট্যাটিসটিক্স এ উইন দেখাবে (Fake Stats)
        
        self.last_issue = None
        self.active_signal = None

state = AdvancedBotState()

# ================= 🔮 PREDICTION LOGIC (AI) =================
def detect_pattern(history):
    if len(history) < 5: return random.choice(["BIG", "SMALL"])
    
    last_5 = history[:5]
    
    # 1. Dragon Pattern (টানা একই)
    if last_5[0] == last_5[1] == last_5[2]:
        return last_5[0] # Trend Follow
        
    # 2. ZigZag (Flip)
    if last_5[0] != last_5[1] and last_5[1] != last_5[2]:
        return last_5[1] # Follow Pattern
    
    # 3. Default (Statistical Probability)
    big_c = history[:10].count("BIG")
    return "SMALL" if big_c > 5 else "BIG"

def get_next_signal(history):
    # 1. Check Admin Override First
    if state.manual_override:
        signal = state.manual_override
        state.manual_override = None # Reset after use
        return {"type": signal, "conf": "100%", "src": "ADMIN 👑"}
    
    # 2. AI Prediction
    pred = detect_pattern(history)
    color = "🟢 GREEN" if pred == "BIG" else "🔴 RED"
    emoji = "🟢" if pred == "BIG" else "🔴"
    
    return {"type": pred, "conf": "95%", "color": color, "emoji": emoji, "src": "AI 🤖"}

# ================= 🔗 ROBUST DATA FETCHING =================
def get_data(mode):
    m_str = "1M" if mode == '1M' else "30S"
    
    for base_url in API_URLS:
        url = base_url.format(mode=m_str)
        proxies = [
            f"{url}?t={int(time.time()*1000)}",
            f"https://corsproxy.io/?{url}",
            f"https://api.allorigins.win/raw?url={url}"
        ]
        
        for p_url in proxies:
            try:
                r = requests.get(p_url, timeout=4)
                if r.status_code == 200:
                    d = r.json()
                    if d['data']['list']: return d['data']['list'][0]
            except: continue
    return None

# ================= 💬 PREMIUM MESSAGING =================
def msg_signal(issue, data):
    lvl = state.stats['losses'] + 1 # Recovery Level
    invest = f"{3**(lvl-1)}X" if lvl < 5 else "MAX 🔥"
    
    return (
        f"⚡ <b>DK MARUF VIP SIGNAL</b> ⚡\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🆔 <b>Issue:</b> <code>{issue}</code>\n"
        f"⏰ <b>Market:</b> {state.mode}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🎯 <b>BET:</b> {data['emoji']} <b>{data['type']}</b> {data['emoji']}\n"
        f"🎨 <b>Color:</b> {data['color']}\n"
        f"💰 <b>Invest:</b> {invest} (Level {lvl})\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"⚠️ <i>Maintain 5 Level Fund</i>\n"
        f"👑 <b>By:</b> DK Mentor Maruf"
    )

def msg_result(issue, res_num, res_type, my_pick, is_win):
    # Result display
    res_e = "🟢" if res_type == "BIG" else "🔴"
    if res_num in [0,5]: res_e = "🟣"
    
    status = "✅ <b>BOOM! SUPER WIN</b> ✅" if is_win else "❌ <b>MISS - Use 3X Next</b> ❌"
    
    return (
        f"{status}\n"
        f"🆔 <b>Issue:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_e} {res_num} ({res_type})\n"
        f"🎯 <b>Signal:</b> {my_pick}\n"
        f"📶 <b>Confidence:</b> High"
    )

def msg_summary(fake=False):
    # This logic guarantees high wins in summary if 'fake' is True
    real_wins = state.stats['wins']
    real_losses = state.stats['losses']
    
    if fake or state.force_win_mode:
        # Manipulation Logic:
        # Show at least 90% accuracy regardless of reality
        total = real_wins + real_losses + 10
        disp_wins = total - 1
        disp_losses = 1
        acc = "98.5%"
    else:
        disp_wins = real_wins
        disp_losses = real_losses
        acc = f"{round((real_wins/(real_wins+real_losses+0.01))*100)}%"

    return (
        f"🛑 <b>SESSION ENDED</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 <b>Mentor:</b> DK MARUF\n"
        f"🏆 <b>Total Win:</b> {disp_wins} ✅\n"
        f"🗑 <b>Total Loss:</b> {disp_losses} ❌\n"
        f"📊 <b>Accuracy:</b> {acc}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"<i>Next session coming soon!</i>"
    )

# ================= 🚀 CORE ENGINE =================
async def engine(context: ContextTypes.DEFAULT_TYPE):
    fail_c = 0
    print("🚀 Engine Started")
    
    while state.running:
        try:
            latest = get_data(state.mode)
            if not latest:
                fail_c += 1
                if fail_c > 5: print("⚠️ Connection Unstable")
                await asyncio.sleep(2)
                continue
            
            fail_c = 0
            cur_issue = latest['issueNumber']
            cur_num = int(latest['number'])
            cur_type = "BIG" if cur_num >= 5 else "SMALL"
            nxt_issue = str(int(cur_issue) + 1)
            
            # History Update
            if not state.history or state.history[0] != cur_type:
                state.history.insert(0, cur_type)
                state.history = state.history[:15]

            # 1. PROCESS RESULT
            if state.active_signal and state.active_signal['issue'] == cur_issue:
                pick = state.active_signal['pick']
                is_win = (pick == cur_type)
                
                # Update Real Stats
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak'] += 1
                    # Send Win Sticker
                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['WIN']))
                    except: pass
                else:
                    state.stats['losses'] += 1
                    state.stats['streak'] = 0
                    # Send Loss Sticker
                    try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['LOSS'])
                    except: pass

                # Send Result
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        msg_result(cur_issue, cur_num, cur_type, pick, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_signal = None
                state.last_issue = cur_issue

            # 2. GENERATE NEXT SIGNAL
            if not state.active_signal and state.last_issue != nxt_issue:
                await asyncio.sleep(2) # Wait for stability
                
                data = get_next_signal(state.history)
                state.active_signal = {"issue": nxt_issue, "pick": data['type']}
                
                # Sticker
                s_key = 'BIG' if data['type'] == "BIG" else 'SMALL'
                try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS[s_key])
                except: pass
                
                # Message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        msg_signal(nxt_issue, data),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(3)

# ================= 🎮 CONTROL COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['⚡ 1M Market', '⚡ 30S Market']]
    await update.message.reply_text("👋 <b>Boss, System Ready!</b>\nSelect Market:", 
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode=ParseMode.HTML)

async def set_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.running: return
    state.mode = '1M' if '1M' in update.message.text else '30S'
    state.running = True
    state.stats = {'wins':0, 'losses':0, 'streak':0}
    state.history = []
    
    await update.message.reply_text(f"✅ <b>Connected: {state.mode}</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
    try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
    except: pass
    
    context.application.create_task(engine(context))

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.running = False
    await update.message.reply_text("🛑 Session Stopped.")
    
    # Send MANIPULATED Summary (Always High Win)
    try:
        await context.bot.send_message(
            TARGET_CHANNEL,
            msg_summary(fake=True), # <--- This makes the summary look good
            parse_mode=ParseMode.HTML
        )
    except: pass

# --- ADMIN COMMANDS (SECRET) ---

async def set_next_big(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Force Next Signal to BIG
    state.manual_override = "BIG"
    await update.message.reply_text("✅ Next Signal Locked: <b>BIG</b>", parse_mode=ParseMode.HTML)

async def set_next_small(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Force Next Signal to SMALL
    state.manual_override = "SMALL"
    await update.message.reply_text("✅ Next Signal Locked: <b>SMALL</b>", parse_mode=ParseMode.HTML)

async def force_win_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Manually add wins to stats
    state.stats['wins'] += 1
    await update.message.reply_text(f"✅ Win Added. Total: {state.stats['wins']}")

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    
    # User Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("off", stop))
    app.add_handler(MessageHandler(filters.Regex(r'Market'), set_market))
    
    # Admin Controls (Secret)
    app.add_handler(CommandHandler("big", set_next_big))    # Type /big to force BIG
    app.add_handler(CommandHandler("small", set_next_small)) # Type /small to force SMALL
    app.add_handler(CommandHandler("addwin", force_win_add)) # Type /addwin to fake stats
    
    print("DK MARUF AI SYSTEM LIVE...")
    app.run_polling()
