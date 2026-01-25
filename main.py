import asyncio
import logging
import random
import time
import os
from threading import Thread

import requests
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAGMYQFxohNbvz16cZTcP8HF2mqydRMZjMI"  # ✅ শুধু এখানে টোকেন বসাবি

TARGET_CHANNEL = -1003293007059
BRAND_NAME = "⚡ 𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝟐𝟒/𝟕 𝐒𝐈𝐆𝐍𝐀𝐋"
CHANNEL_LINK = "https://t.me/big_maruf_official0"

SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_GID = "0"
PASSWORD_CACHE_SECONDS = 20

MAX_LOSS_STOP = 8  # 8 step loss হলে auto off

API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"


# ================= STICKERS (YOUR PROVIDED) =================
PRED_STICKERS = {
    "1M": {
        "BIG": "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
        "SMALL": "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    },
    "30S": {
        "BIG": "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",
        "SMALL": "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    }
}

WIN_BIG = "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE"
WIN_SMALL = "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE"
WIN_ANY = "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA"
LOSS_ANY = "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA"

WIN_RANDOM_POOL = [
    "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
    "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAnQKcVYHd8IiRqfBXTgE",
    "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
    "CAACAgUAAxkBAAEQT_tpc4E3AxHmgW9VWKrzWjxlrvzSowACghkAAlbXcFWxdto6TqiBrzgE",
    "CAACAgUAAxkBAAEQT_9pc4FHKn0W6ZfWOSaN6FUPzfmbnQACXR0AAqMbMFc-_4DHWbq7sjgE",
    "CAACAgUAAxkBAAEQUAFpc4FIokHE09p165cCsWiUYV648wACuhQAAo3aMVeAsNW9VRuVvzgE",
    "CAACAgUAAxkBAAEQUANpc4FJNTnfuBiLe-dVtoNCf3CQlAAC9xcAArE-MFfS5HNyds2tWTgE",
    "CAACAgUAAxkBAAEQUAVpc4FKhJ_stZ3VRRzWUuJGaWbrAgACOhYAAst6OVehdeQEGZlXiDgE",
    "CAACAgUAAxkBAAEQUAtpc4HcYxkscyRY2rhAAcmqMR29eAACOBYAAh7fwVU5Xy399k3oFDgE",
    "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE",
]

COLOR_STICKERS = {
    "RED": "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    "GREEN": "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
}

SEASON_START = {
    "30S": "CAACAgUAAxkBAAEQUrNpdYvDXIBff9O8TCRlI3QYJgfGiAAC1RQAAjGFMVfjtqxbDWbuEzgE",
    "1M":  "CAACAgUAAxkBAAEQUrRpdYvESSIrn4-Lm936I6F8_BaN-wACChYAAuBHOVc6YQfcV-EKqjgE"
}

# ✅ This sticker must go "start & end always", but NOT during loss
HYPE_STICKER = "CAACAgUAAxkBAAEQTjRpcmWdzXBzA7e9KNz8QgTI6NXlxgACuRcAAh2x-FaJNjq4QG_DujgE"


# ================= FLASK KEEP ALIVE =================
app = Flask("")

@app.route("/")
def home():
    return "OK"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def keep_alive():
    Thread(target=run_http, daemon=True).start()


# ================= PASSWORD FROM SHEET =================
_password_cache = {"value": None, "ts": 0.0}

def _sheet_csv_url():
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

def _fetch_password_sync(timeout=6.0):
    try:
        r = requests.get(_sheet_csv_url(), headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        if r.status_code != 200:
            return None
        lines = (r.text or "").splitlines()
        if not lines:
            return None
        a1 = lines[0].split(",")[0].strip().strip('"').strip("'")
        return a1 or None
    except:
        return None

async def get_password(force_refresh=False):
    now = time.time()
    if (not force_refresh) and _password_cache["value"] and (now - _password_cache["ts"] < PASSWORD_CACHE_SECONDS):
        return _password_cache["value"]
    pw = await asyncio.to_thread(_fetch_password_sync)
    if pw:
        _password_cache["value"] = pw
        _password_cache["ts"] = now
        return pw
    return None


# ================= MULTI-GATEWAY FETCH =================
def _fetch_one(url, headers, timeout):
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        return None
    data = r.json()
    if data and "data" in data and "list" in data["data"] and data["data"]["list"]:
        return data["data"]["list"][0]
    return None

async def fetch_latest_issue(mode):
    base_url = API_1M if mode == "1M" else API_30S
    ts = int(time.time() * 1000)

    gateways = [
        f"{base_url}?t={ts}",
        f"https://corsproxy.io/?{base_url}?t={ts}",
        f"https://api.allorigins.win/raw?url={base_url}?t={ts}",
        f"https://thingproxy.freeboard.io/fetch/{base_url}?t={ts}",
        f"https://api.codetabs.com/v1/proxy?quest={base_url}?t={ts}",
    ]

    headers = {
        "User-Agent": f"Mozilla/5.0 Chrome/{random.randint(110,123)}.0.0.0 Safari/537.36",
        "Referer": "https://dkwin9.com/",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    timeout = 5 if mode == "30S" else 8

    for url in gateways:
        try:
            res = await asyncio.to_thread(_fetch_one, url, headers, timeout)
            if res:
                return res
        except:
            continue
    return None


# ================= SAFE TELEGRAM SENDER (ANTI-SPAM BURST) =================
class TgSender:
    def __init__(self):
        self.q = asyncio.Queue()

    async def start(self, context: ContextTypes.DEFAULT_TYPE):
        while True:
            fn, args = await self.q.get()
            try:
                await fn(*args)
            except:
                pass
            # ✅ anti-burst delay
            await asyncio.sleep(0.7)

    async def send_sticker(self, context, chat_id, sticker_id, track_list=None):
        async def _do():
            m = await context.bot.send_sticker(chat_id, sticker_id)
            if track_list is not None:
                track_list.append(m.message_id)
        await self.q.put((_do, tuple()))

    async def send_message(self, context, chat_id, text, track_list=None):
        async def _do():
            m = await context.bot.send_message(
                chat_id,
                text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            if track_list is not None:
                track_list.append(m.message_id)
        await self.q.put((_do, tuple()))

    async def edit_message(self, context, chat_id, mid, text):
        async def _do():
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=mid,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        await self.q.put((_do, tuple()))

    async def delete_message(self, context, chat_id, mid):
        async def _do():
            try:
                await context.bot.delete_message(chat_id, mid)
            except:
                pass
        await self.q.put((_do, tuple()))


# ================= ENGINE =================
AUTHORIZED_USERS = set()

def now_hms():
    return time.strftime("%H:%M:%S")

def mode_label(mode):
    return "30 SEC" if mode == "30S" else "1 MIN"

def pick_badge(pred):
    return "🟢🟢 <b>BIG</b> 🟢🟢" if pred == "BIG" else "🔴🔴 <b>SMALL</b> 🔴🔴"

def step_text(step):
    return f"{step} Step Loss" if step > 0 else "0 Step"

def fmt_signal(next_issue, pred, conf, step_loss):
    join = f"\n🔗 <a href='{CHANNEL_LINK}'><b>JOIN / REJOIN</b></a>" if CHANNEL_LINK else ""
    return (
        f"⚡ <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(state.game_mode)}</b>\n"
        f"🧾 <b>Period</b>: <code>{next_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>PREDICTION</b> ➜ {pick_badge(pred)}\n"
        f"📈 <b>Confidence</b> ➜ <b>{conf}%</b>\n"
        f"🧠 <b>Recovery</b> ➜ <b>{step_text(step_loss)}</b> / {MAX_LOSS_STOP}\n"
        f"⏱ <b>Time</b> ➜ <code>{now_hms()}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
        f"{join}"
    )

def fmt_checking(next_issue, dots):
    return (
        f"🛰 <b>LIVE CHECK</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(state.game_mode)}</b>\n"
        f"🧾 <b>Waiting Result</b>: <code>{next_issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ <code>syncing{dots}</code>"
    )

def fmt_result(issue, res_num, res_type, pick, is_win, step_loss, w, l, max_ls, max_ws, ws, ls):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    header = "✅ <b>WIN CONFIRMED</b>" if is_win else "❌ <b>LOSS CONFIRMED</b>"
    extra = (f"🔥 <b>Win Streak</b>: {ws} (Max {max_ws})"
             if is_win else
             f"⚠️ <b>{step_text(step_loss)}</b> / {MAX_LOSS_STOP} (Max {max_ls})")
    return (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(state.game_mode)}</b>\n"
        f"🧾 <b>Period</b>: <code>{issue}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 <b>Result</b>: {res_emoji} <b>{res_num}</b> (<b>{res_type}</b>)\n"
        f"🎯 <b>Your Pick</b>: {pick_badge(pick)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{extra}\n"
        f"📊 <b>W</b>:{w} | <b>L</b>:{l} | <code>{now_hms()}</code>"
    )

def fmt_summary():
    w = state.stats["wins"]
    l = state.stats["losses"]
    total = w + l
    win_rate = round((w / total) * 100, 2) if total else 0.0
    join = f"\n🔗 <a href='{CHANNEL_LINK}'><b>REJOIN</b></a>" if CHANNEL_LINK else ""
    return (
        f"🛑 <b>SESSION SUMMARY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 <b>Mode</b>: <b>{mode_label(state.game_mode)}</b>\n"
        f"📦 <b>Total</b>: <b>{total}</b>\n"
        f"✅ <b>Win</b>: <b>{w}</b>\n"
        f"❌ <b>Loss</b>: <b>{l}</b>\n"
        f"🎯 <b>Win Rate</b>: <b>{win_rate}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 <b>Max Win Streak</b>: <b>{state.stats['max_streak_win']}</b>\n"
        f"🧊 <b>Max Loss Streak</b>: <b>{state.stats['max_streak_loss']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Closed</b>: <code>{now_hms()}</code>"
        f"{join}"
    )

def fmt_consolation_stop():
    return (
        f"🧊 <b>SAFE GUARD ACTIVATED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>{BRAND_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>{MAX_LOSS_STOP} Step Loss</b> reached.\n"
        f"🛡️ Prediction is now <b>OFF</b> for safety.\n"
        f"✅ Use /start and password again.\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )


class PredictionEngine:
    def __init__(self):
        self.history = []
        self.raw_history = []
        self.last_prediction = None

    def update_history(self, issue_data):
        try:
            number = int(issue_data["number"])
            result_type = "BIG" if number >= 5 else "SMALL"
        except:
            return

        if (not self.raw_history) or (str(self.raw_history[0].get("issueNumber")) != str(issue_data.get("issueNumber"))):
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:800]
            self.raw_history = self.raw_history[:800]

    # ✅ YOUR NEW LOGIC (Trend 12 + loss>=3 flip)
    def get_pattern_signal(self, current_streak_loss):
        if len(self.history) < 12:
            pred = random.choice(["BIG", "SMALL"])
            self.last_prediction = pred
            return pred

        last_12 = self.history[:12]
        big_count = last_12.count("BIG")
        small_count = last_12.count("SMALL")

        if big_count > small_count:
            prediction = "BIG"
        elif small_count > big_count:
            prediction = "SMALL"
        else:
            prediction = self.history[0]

        if current_streak_loss >= 3:
            prediction = "SMALL" if prediction == "BIG" else "BIG"

        self.last_prediction = prediction
        return prediction

    def calculate_confidence(self):
        # confidence slightly higher on streak signals
        base = random.randint(86, 92)
        try:
            if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
                base = random.randint(92, 97)
        except:
            pass
        return base


class BotState:
    def __init__(self):
        self.is_running = False
        self.session_id = 0
        self.game_mode = "30S"

        self.engine = PredictionEngine()

        # active_bet:
        # {
        #   "period": str, "pick": str,
        #   "sent": bool,
        #   "check_mid": int|None,
        #   "check_task": task|None
        # }
        self.active_bet = None

        self.last_seen_issue = None
        self.last_period_processed = None

        self.color_enabled = False

        self.stop_requested = False  # ✅ stop after recovery system

        self.stats = {
            "wins": 0, "losses": 0,
            "streak_win": 0, "streak_loss": 0,
            "max_streak_win": 0, "max_streak_loss": 0
        }

        # track loss clutter to delete later
        self.loss_message_ids = []


state = BotState()


async def delete_loss_clutter(sender: TgSender, context: ContextTypes.DEFAULT_TYPE):
    ids = state.loss_message_ids[:]
    state.loss_message_ids.clear()
    for mid in ids:
        await sender.delete_message(context, TARGET_CHANNEL, mid)


async def checking_anim(sender: TgSender, context: ContextTypes.DEFAULT_TYPE, mid: int, period: str):
    dots = ""
    while True:
        try:
            dots = "." if dots == "" else (".." if dots == "." else ("..." if dots == ".." else ""))
            await sender.edit_message(context, TARGET_CHANNEL, mid, fmt_checking(period, dots))
        except:
            pass
        await asyncio.sleep(1.0)


async def engine_loop(context: ContextTypes.DEFAULT_TYPE):
    sender = TgSender()
    context.application.create_task(sender.start(context))

    fail_count = 0

    while state.is_running:
        sid = state.session_id

        try:
            latest = await fetch_latest_issue(state.game_mode)
            if not latest:
                fail_count += 1
                await asyncio.sleep(min(2 + fail_count, 12))
                continue
            fail_count = 0

            latest_issue = str(latest["issueNumber"])
            latest_num = str(latest["number"])
            latest_type = "BIG" if int(latest_num) >= 5 else "SMALL"

            # API jump -> resync (prevents random burst)
            if state.last_seen_issue is not None:
                try:
                    if int(latest_issue) > int(state.last_seen_issue) + 1:
                        state.active_bet = None
                        state.last_period_processed = latest_issue
                except:
                    pass
            state.last_seen_issue = latest_issue

            next_issue = str(int(latest_issue) + 1)

            # ===== RESULT =====
            if state.active_bet and state.active_bet.get("period") == latest_issue:
                if state.last_period_processed == latest_issue:
                    await asyncio.sleep(1)
                    continue

                # if prediction wasn't sent -> don't send feedback
                if not state.active_bet.get("sent", False):
                    # cleanup checking
                    if state.active_bet.get("check_task"):
                        state.active_bet["check_task"].cancel()
                    if state.active_bet.get("check_mid"):
                        await sender.delete_message(context, TARGET_CHANNEL, state.active_bet["check_mid"])
                    state.active_bet = None
                    state.last_period_processed = latest_issue
                    await asyncio.sleep(1)
                    continue

                # stop checking
                if state.active_bet.get("check_task"):
                    state.active_bet["check_task"].cancel()
                if state.active_bet.get("check_mid"):
                    await sender.delete_message(context, TARGET_CHANNEL, state.active_bet["check_mid"])

                pick = state.active_bet["pick"]
                is_win = (pick == latest_type)

                # update history
                state.engine.update_history(latest)

                if is_win:
                    state.stats["wins"] += 1
                    state.stats["streak_win"] += 1
                    state.stats["streak_loss"] = 0
                    state.stats["max_streak_win"] = max(state.stats["max_streak_win"], state.stats["streak_win"])

                    # ✅ HYPE sticker on end (win) always (not during loss)
                    await sender.send_sticker(context, TARGET_CHANNEL, HYPE_STICKER)

                    # win sticker (type + random on streak)
                    pool = [WIN_ANY, (WIN_BIG if latest_type == "BIG" else WIN_SMALL)]
                    if state.stats["streak_win"] >= 2:
                        pool.append(random.choice(WIN_RANDOM_POOL))
                    await sender.send_sticker(context, TARGET_CHANNEL, random.choice(pool))

                else:
                    state.stats["losses"] += 1
                    state.stats["streak_win"] = 0
                    state.stats["streak_loss"] += 1
                    state.stats["max_streak_loss"] = max(state.stats["max_streak_loss"], state.stats["streak_loss"])

                    # loss sticker (track)
                    await sender.send_sticker(context, TARGET_CHANNEL, LOSS_ANY, track_list=state.loss_message_ids)

                # result message
                txt = fmt_result(
                    latest_issue, latest_num, latest_type, pick, is_win,
                    state.stats["streak_loss"],
                    state.stats["wins"], state.stats["losses"],
                    state.stats["max_streak_loss"], state.stats["max_streak_win"],
                    state.stats["streak_win"], state.stats["streak_loss"],
                )
                if not is_win:
                    await sender.send_message(context, TARGET_CHANNEL, txt, track_list=state.loss_message_ids)
                else:
                    await sender.send_message(context, TARGET_CHANNEL, txt)

                state.active_bet = None
                state.last_period_processed = latest_issue

                # ✅ stop-after-recovery feature
                if state.stop_requested and state.stats["streak_loss"] == 0:
                    state.is_running = False
                    state.stop_requested = False
                    AUTHORIZED_USERS.clear()
                    await delete_loss_clutter(sender, context)
                    await sender.send_message(context, TARGET_CHANNEL, fmt_summary())
                    return

                # auto stop on max loss
                if state.stats["streak_loss"] >= MAX_LOSS_STOP:
                    state.is_running = False
                    state.stop_requested = False
                    AUTHORIZED_USERS.clear()
                    await delete_loss_clutter(sender, context)
                    await sender.send_message(context, TARGET_CHANNEL, fmt_consolation_stop())
                    await sender.send_message(context, TARGET_CHANNEL, fmt_summary())
                    return

            # ===== SIGNAL =====
            if (state.active_bet is None) and (state.last_period_processed != next_issue):
                state.engine.update_history(latest)

                pred = state.engine.get_pattern_signal(state.stats["streak_loss"])
                conf = state.engine.calculate_confidence()

                state.active_bet = {"period": next_issue, "pick": pred, "sent": False, "check_mid": None, "check_task": None}

                # ✅ HYPE sticker on start always, but NOT during loss
                if state.stats["streak_loss"] == 0:
                    await sender.send_sticker(context, TARGET_CHANNEL, HYPE_STICKER)

                # prediction stickers
                await sender.send_sticker(context, TARGET_CHANNEL, PRED_STICKERS[state.game_mode][pred])

                # color sticker optional
                if state.color_enabled:
                    # BIG -> GREEN, SMALL -> RED
                    await sender.send_sticker(context, TARGET_CHANNEL, COLOR_STICKERS["GREEN" if pred == "BIG" else "RED"])

                # signal message (mark sent only if enqueue success)
                try:
                    await sender.send_message(context, TARGET_CHANNEL, fmt_signal(next_issue, pred, conf, state.stats["streak_loss"]))
                    state.active_bet["sent"] = True
                except:
                    state.active_bet = None

                # checking message + animation
                if state.active_bet and state.active_bet["sent"]:
                    # send checking message first (we need message id)
                    # we do direct send to get id (1 time)
                    try:
                        m = await context.bot.send_message(
                            TARGET_CHANNEL,
                            fmt_checking(next_issue, ""),
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                        state.active_bet["check_mid"] = m.message_id
                        state.active_bet["check_task"] = asyncio.create_task(checking_anim(sender, context, m.message_id, next_issue))
                    except:
                        pass

            await asyncio.sleep(1 if state.game_mode == "30S" else 2)

        except Exception:
            await asyncio.sleep(2)

        if state.session_id != sid:
            await asyncio.sleep(1)


# ================= MENU / HANDLERS =================
def menu_keyboard():
    color_btn = "🎨 Color: ON" if state.color_enabled else "🎨 Color: OFF"
    return ReplyKeyboardMarkup(
        [['⚡ Connect 1M', '⚡ Connect 30S'],
         [color_btn],
         ['🛑 Stop & Summary']],
        resize_keyboard=True
    )

async def show_main_menu(update: Update):
    await update.message.reply_text(
        f"🔓 <b>ACCESS GRANTED</b>\n<b>{BRAND_NAME}</b>\n\nChoose:",
        reply_markup=menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pw = await get_password(force_refresh=True)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
        return

    uid = update.effective_user.id
    if uid in AUTHORIZED_USERS:
        await show_main_menu(update)
    else:
        await update.message.reply_text("🔒 <b>LOCKED</b>\nSend Password:", parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    uid = update.effective_user.id

    pw = await get_password(force_refresh=False)
    if not pw:
        await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
        return

    # AUTH
    if uid not in AUTHORIZED_USERS:
        if msg == pw:
            AUTHORIZED_USERS.add(uid)
            await show_main_menu(update)
            return
        await update.message.reply_text("❌ Wrong password", parse_mode=ParseMode.HTML)
        return

    # Toggle color
    if msg.startswith("🎨 Color:"):
        state.color_enabled = not state.color_enabled
        await update.message.reply_text(
            f"✅ Color Signal: <b>{'ON' if state.color_enabled else 'OFF'}</b>",
            reply_markup=menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return

    # STOP
    if "Stop" in msg or msg == "/off":
        # ✅ Stop-after-recovery:
        # যদি loss চলতে থাকে -> stop_requested True, recovery win না হওয়া পর্যন্ত চলবে
        if state.is_running and state.stats["streak_loss"] > 0:
            state.stop_requested = True
            await update.message.reply_text(
                "⏳ <b>Stop Requested</b>\nLoss চলছে—Recovery (next WIN) হলে auto stop + summary হবে।",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML
            )
            return

        # no loss -> stop immediately
        state.session_id += 1
        state.is_running = False
        state.stop_requested = False

        # cancel checking
        if state.active_bet:
            try:
                if state.active_bet.get("check_task"):
                    state.active_bet["check_task"].cancel()
            except:
                pass
            if state.active_bet.get("check_mid"):
                try:
                    await context.bot.delete_message(TARGET_CHANNEL, state.active_bet["check_mid"])
                except:
                    pass
        state.active_bet = None

        await update.message.reply_text("🛑 Stopping…", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)

        # delete loss clutter + send summary
        try:
            for mid in state.loss_message_ids[:]:
                try:
                    await context.bot.delete_message(TARGET_CHANNEL, mid)
                except:
                    pass
            state.loss_message_ids.clear()
        except:
            pass

        try:
            await context.bot.send_message(
                TARGET_CHANNEL,
                fmt_summary(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except:
            pass

        AUTHORIZED_USERS.clear()
        return

    # CONNECT
    if "Connect" in msg:
        # refresh password on every start
        pw2 = await get_password(force_refresh=True)
        if not pw2:
            await update.message.reply_text("⚠️ Password system offline (Sheet not reachable).", parse_mode=ParseMode.HTML)
            return

        state.session_id += 1
        mode = "1M" if "1M" in msg else "30S"
        state.game_mode = mode

        # reset state
        state.is_running = True
        state.stop_requested = False

        state.engine = PredictionEngine()
        state.active_bet = None
        state.last_seen_issue = None
        state.last_period_processed = None
        state.loss_message_ids = []

        state.stats = {
            "wins": 0, "losses": 0,
            "streak_win": 0, "streak_loss": 0,
            "max_streak_win": 0, "max_streak_loss": 0
        }

        await update.message.reply_text(
            f"✅ Connected: <b>{mode_label(mode)}</b>\nEngine: <b>LIVE</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        # Season start sticker
        try:
            await context.bot.send_sticker(TARGET_CHANNEL, SEASON_START[mode])
        except:
            pass

        context.application.create_task(engine_loop(context))
        return


# ================= MAIN =================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    keep_alive()

    if not BOT_TOKEN or "PASTE_TOKEN_HERE" in BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing! Replace PASTE_TOKEN_HERE in main.py")

    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("off", handle_message))
    app_telegram.add_handler(MessageHandler(filters.TEXT, handle_message))

    app_telegram.run_polling(drop_pending_updates=True, close_loop=False)
