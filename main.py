import asyncio
import logging
import random
import requests
import time
import os
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

# ================= ⚙️ CONFIGURATION ⚙️ =================
BOT_TOKEN = "8595453345:AAFUIOwzQN-1eWAeLprnM6zu4JtwGASp9mI"  # <--- টোকেন বসান
TARGET_CHANNEL = "-1003293007059"   # <--- চ্যানেল আইডি
ADMIN_ID = 123456789  # <--- আপনার টেলিগ্রাম ID (অবশ্যই বসাবেন, নাহলে প্যানেল আসবে না)

# ================= 🎨 ASSETS & STICKERS =================
STICKERS = {
    'BIG_PRED': "CAACAgUAAxkBAAEQThJpcmSl40i0bvVSOxcDpVmqqeuqWQACySIAAlAYqVXUubH8axJhFzgE",
    'SMALL_PRED': "CAACAgUAAxkBAAEQThZpcmTJ3JsaZHTYtVIcE4YEFuXDFgAC9BoAApWhsVWD2IhYoJfTkzgE",
    
    # উইন স্ট্রিক অনুযায়ী ভিন্ন স্টিকার
    'WIN_1': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_STREAK': "CAACAgUAAxkBAAEQTiFpcmUgdgJQ_czeoFyRhNZiZI2lwwAC8BcAAv8UqFSVBQEdUW48HTgE", # Fire
    'WIN_JACKPOT': "CAACAgUAAxkBAAEQTiRpcmUhQJUjd2ukdtfEtBjwtMH4MAACWRgAAsTFqVTato0SmSN-6jgE", # Money
    
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
def home(): return "DK MARUF CONTROL PANEL RUNNING..."

def run_http(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_http).start()

# ================= 🧠 BOT BRAIN =================
class BotState:
    def __init__(self):
        self.running = False
        self.mode = '1M'
        self.history = []
        
        # Stats
        self.real_wins = 0
        self.real_losses = 0
        self.fake_wins = 0 # ম্যানুয়াল উইন এড করার জন্য
        
        self.streak = 0
        self.active_signal = None
        self.next_override = None # এডমিন যা সেট করবে

state = BotState()

# ================= 🔮 DYNAMIC MESSAGE GENERATOR =================

def get_signal_message(issue, prediction, color, emoji):
    # লস স্ট্রিক অনুযায়ী ইনভেস্টমেন্ট প্ল্যান
    lvl = state.streak if state.streak < 0 else 0 # Negative streak means loss
    lvl = abs(lvl) + 1
    
    if lvl == 1:
        plan = "🟢 Start Amount (1X)"
        advice = "Safe Bet"
    elif lvl == 2:
        plan = "🟡 Level 2 (3X)"
        advice = "Recover Now"
    elif lvl == 3:
        plan = "🔴 Level 3 (9X)"
        advice = "High Chance!"
    else:
        plan = "🔥 MAX BET (27X) 🔥"
        advice = "JACKPOT CALL"

    return (
        f"⚡ <b>DK MARUF VIP PREMIUM</b> ⚡\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎲 <b>Period:</b> <code>{issue}</code>\n"
        f"🕒 <b>Market:</b> {state.mode} VIP\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🧨 <b>SIGNAL:</b> {emoji} <b>{prediction}</b> {emoji}\n"
        f"🎨 <b>Color:</b> {color}\n"
        f"💰 <b>Invest:</b> {plan}\n"
        f"💡 <b>Advice:</b> {advice}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"👑 <b>Owner:</b> DK Mentor Maruf"
    )

def get_result_message(issue, res_num, res_type, pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if res_num in [0, 5]: res_emoji = "🟣"
    
    if is_win:
        s = state.streak
        if s == 1:
            header = "✅ <b>GOOD START! WIN!</b> ✅"
            body = "Nice hit! Keep playing."
        elif s <= 3:
            header = f"🔥 <b>BOOM! {s} BACK TO BACK!</b> 🔥"
            body = "The streak is ON FIRE!"
        else:
            header = f"💎 <b>UNSTOPPABLE! {s} WINS!</b> 💎"
            body = "DK MARUF SYSTEM HACKED THE GAME!"
    else:
        header = "❌ <b>MISS! USE LEVEL PLAN</b> ❌"
        body = "Don't panic. Next signal is 100% Sure."

    return (
        f"{header}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🆔 <b>Issue:</b> <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {pick}\n"
        f"📝 <b>Note:</b> {body}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"📶 <b>Confidence:</b> 100%"
    )

def get_fake_summary():
    # এখানে রেজাল্ট সবসময় ভালো দেখাবে
    total_played = state.real_wins + state.real_losses + 5
    
    # Fake Calculation: Loss কমিয়ে Win বাড়িয়ে দেখাবে
    disp_wins = state.real_wins + (state.real_losses) + state.fake_wins + 3
    disp_losses = 1 if state.real_losses > 0 else 0
    
    acc = round((disp_wins / (disp_wins + disp_losses)) * 100, 2)
    
    return (
        f"🛑 <b>VIP SESSION ENDED</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"👨‍💻 <b>Admin:</b> DK MARUF\n"
        f"🏆 <b>Total Wins:</b> {disp_wins} ✅\n"
        f"🗑 <b>Total Loss:</b> {disp_losses} ❌\n"
        f"📊 <b>Accuracy:</b> {acc}% 🔥\n"
        f"💰 <b>Profit:</b> MAX LEVEL\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"<i>Thanks for joining the VIP!</i>"
    )

# ================= 🎮 CONTROL PANEL LOGIC =================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return # সিকিউরিটি
    
    keyboard = [
        [InlineKeyboardButton("🟢 Force BIG", callback_data='set_big'), InlineKeyboardButton("🔴 Force SMALL", callback_data='set_small')],
        [InlineKeyboardButton("✅ Add Fake Win", callback_data='add_win'), InlineKeyboardButton("🛑 End Session", callback_data='end_session')],
        [InlineKeyboardButton("♻️ Reset Override", callback_data='reset_over')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ <b>DK MARUF CONTROL ROOM:</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'set_big':
        state.next_override = "BIG"
        await query.edit_message_text(f"✅ Next Signal Locked: <b>BIG 🟢</b>", parse_mode=ParseMode.HTML)
    elif data == 'set_small':
        state.next_override = "SMALL"
        await query.edit_message_text(f"✅ Next Signal Locked: <b>SMALL 🔴</b>", parse_mode=ParseMode.HTML)
    elif data == 'reset_over':
        state.next_override = None
        await query.edit_message_text(f"🤖 AI Mode Activated (Auto)", parse_mode=ParseMode.HTML)
    elif data == 'add_win':
        state.fake_wins += 1
        await query.edit_message_text(f"✅ Fake Win Added! Total Boost: {state.fake_wins}")
    elif data == 'end_session':
        state.running = False
        await query.edit_message_text("🛑 Session Stopping...")
        try:
            await context.bot.send_message(TARGET_CHANNEL, get_fake_summary(), parse_mode=ParseMode.HTML)
        except: pass

# ================= 🚀 CORE ENGINE =================
async def fetch_data(mode):
    m_str = "1M" if mode == '1M' else "30S"
    for base in API_URLS:
        url = base.format(mode=m_str)
        try:
            r = requests.get(f"{url}?t={int(time.time()*1000)}", timeout=4)
            if r.status_code == 200:
                return r.json()['data']['list'][0]
        except: continue
    return None

async def engine(context: ContextTypes.DEFAULT_TYPE):
    while state.running:
        try:
            latest = await fetch_data(state.mode)
            if not latest:
                await asyncio.sleep(2)
                continue
                
            cur_issue = latest['issueNumber']
            cur_num = int(latest['number'])
            cur_type = "BIG" if cur_num >= 5 else "SMALL"
            nxt_issue = str(int(cur_issue) + 1)
            
            # 1. RESULT CHECKING
            if state.active_signal and state.active_signal['issue'] == cur_issue:
                pick = state.active_signal['pick']
                is_win = (pick == cur_type)
                
                if is_win:
                    if state.streak < 0: state.streak = 0
                    state.streak += 1
                    state.real_wins += 1
                    
                    # Sticker Logic
                    if state.streak >= 4: s = STICKERS['WIN_JACKPOT']
                    elif state.streak >= 2: s = STICKERS['WIN_STREAK']
                    else: s = STICKERS['WIN_1']
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, s)
                    except: pass
                else:
                    if state.streak > 0: state.streak = 0
                    state.streak -= 1 # Negative for loss count
                    state.real_losses += 1
                    try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['LOSS'])
                    except: pass
                
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        get_result_message(cur_issue, cur_num, cur_type, pick, is_win),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
                state.active_signal = None
            
            # 2. NEXT SIGNAL GENERATION
            if not state.active_signal and cur_issue != state.active_signal: 
                # Check control panel override
                if state.next_override:
                    pred = state.next_override
                    state.next_override = None # Reset after usage
                else:
                    # AI Logic (Auto)
                    if not state.history: state.history = ["BIG"]
                    # Simple ZigZag Logic for default
                    pred = "SMALL" if state.history[0] == "BIG" else "BIG"
                
                # Save History
                state.history.insert(0, cur_type)
                
                # Prepare Data
                color = "🟢 GREEN" if pred == "BIG" else "🔴 RED"
                emoji = "🟢" if pred == "BIG" else "🔴"
                
                state.active_signal = {"issue": nxt_issue, "pick": pred}
                
                await asyncio.sleep(2)
                
                # Send Sticker
                s_pred = STICKERS['BIG_PRED'] if pred == "BIG" else STICKERS['SMALL_PRED']
                try: await context.bot.send_sticker(TARGET_CHANNEL, s_pred)
                except: pass
                
                # Send VIP Message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        get_signal_message(nxt_issue, pred, color, emoji),
                        parse_mode=ParseMode.HTML
                    )
                except: pass
                
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Loop error: {e}")
            await asyncio.sleep(3)

# ================= 🕹️ COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['⚡ Start 1M', '⚡ Start 30S']]
    await update.message.reply_text("👋 <b>Welcome Boss!</b>\nSelect market:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode=ParseMode.HTML)

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.running: return
    state.mode = '1M' if '1M' in update.message.text else '30S'
    state.running = True
    state.streak = 0
    state.real_wins = 0
    state.real_losses = 0
    state.fake_wins = 0
    
    await update.message.reply_text(f"✅ <b>Connected: {state.mode}</b>\nUse /panel to control.", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
    try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['START'])
    except: pass
    context.application.create_task(engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", admin_panel)) # <--- নতুন কন্ট্রোল প্যানেল
    app.add_handler(MessageHandler(filters.Regex(r'Start'), connect))
    app.add_handler(CallbackQueryHandler(button_handler)) # বাটন হ্যান্ডলার
    
    print("DK MARUF CONTROL SYSTEM ONLINE...")
    app.run_polling()
