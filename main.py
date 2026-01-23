import asyncio
import random
import requests
import time
import os
import csv
import io
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from flask import Flask

# ================= CONFIGURATION =================
BOT_TOKEN = "8595453345:AAExpD-Txn7e-nysGZyrigy9hh7m3UjMraM"
TARGET_CHANNEL = -1003293007059
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo" # আপনার শিট আইডি

# LINKS
LINK_REG = "https://dkwin9.com/#/register?invitationCode=112681085937"
LINK_CHANNEL = "https://t.me/big_maruf_official0"
LINK_OWNER = "@OWNER_MARUF_TOP"

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= STICKER DATABASE (FULL) =================
STICKERS = {
    'PRED_1M_BIG': "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    'PRED_1M_SMALL': "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    'PRED_30S_BIG': "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",
    'PRED_30S_SMALL': "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    
    'WIN_BIG': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'WIN_SMALL': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'WIN_ANY': "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",
    
    'LOSS_ANY': "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",
    
    'COLOR_RED': "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    'COLOR_GREEN': "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE",
    
    'START': [
        "CAACAgUAAxkBAAEQT_lpc4EvleS6GJIogvkFzlcAAV6T7PsAArYaAAIOJIBV6qeBrzw1_oc4BA",
        "CAACAgUAAxkBAAEQTuRpczxpKCooU6JW2F53jWSEr7SZnQACZBUAAtEWOFcRzggHRna-EzgE"
    ],
    'STOP': [
        "CAACAgUAAxkBAAEQTudpczxpoCLQ2pIXCqANpddRbHX9ngACKhYAAoBTMVfQP_QoToLXkzgE",
        "CAACAgUAAxkBAAEQT_dpc4Eqt5r28E8WwxaZnW8X2t58RQACsw8AAoV9CFW0IyDz2PAL5DgE",
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE",
        "CAACAgUAAxkBAAEQUDRpc4VJP7cgZhVHhqzQsiV3hNLI5wACCQ4AAk9o-VW3jbWfWUVQrjgE",
        "CAACAgUAAxkBAAEQUDZpc4VMJx694uE09-ZWlks_anzAvAACXBsAAv4b-FXj9l4eQ-g5-jgE",
        "CAACAgUAAxkBAAEQUDhpc4VM6rq1VbSAPaCdCeaR0eReHwACAhIAAkEj8VWFHkUbgA0-njgE"
    ],
    
    # Random Win Stickers
    'RANDOM_WIN': [
        "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
        "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAnQKcVYHd8IiRqfBXTgE",
        "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
        "CAACAgUAAxkBAAEQT_tpc4E3AxHmgW9VWKrzWjxlrvzSowACghkAAlbXcFWxdto6TqiBrzgE",
        "CAACAgUAAxkBAAEQT_9pc4FHKn0W6ZfWOSaN6FUPzfmbnQACXR0AAqMbMFc-_4DHWbq7sjgE",
        "CAACAgUAAxkBAAEQUAFpc4FIokHE09p165cCsWiUYV648wACuhQAAo3aMVeAsNW9VRuVvzgE",
        "CAACAgUAAxkBAAEQUANpc4FJNTnfuBiLe-dVtoNCf3CQlAAC9xcAArE-MFfS5HNyds2tWTgE",
        "CAACAgUAAxkBAAEQUAVpc4FKhJ_stZ3VRRzWUuJGaWbrAgACOhYAAst6OVehdeQEGZlXiDgE",
        "CAACAgUAAxkBAAEQUAtpc4HcYxkscyRY2rhAAcmqMR29eAACOBYAAh7fwVU5Xy399k3oFDgE",
        "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE"
    ],
    
    # 1 to 75 Streak Wins (List format for indexing)
    'STREAK_LIST': [
        "CAACAgUAAxkBAAEQUA1pc4IKjtrvSWe2ssLEqZ88cAABYW8AAsoiAALegIlVctTV3Pqbjmg4BA", #1
        "CAACAgUAAxkBAAEQUA5pc4IKOY43Rh4dwtmmwOC55ikPbQAClRkAAgWviFVWRlQ-8i4rHTgE",
        "CAACAgUAAxkBAAEQUA9pc4IL7ALl7rMzh_MNMtRQ7DlLHAACihoAAkI4iFVaqQABGzm-T_Q4BA",
        "CAACAgUAAxkBAAEQUBFpc4ILdPG1eK5pNvXmFC_0vOHp_AACFRsAAr9_iVW18_WchrZ20zgE",
        "CAACAgUAAxkBAAEQUBJpc4IMZqQnZDPs37vLnP3b_J_IewACjhcAAu1YiFVA_VudovtxjDgE",
        "CAACAgUAAxkBAAEQUBRpc4IMQdH7-Ykn95YFoVlYeUhDBAACCxwAAhFLiVUYVv2JfG18AzgE",
        "CAACAgUAAxkBAAEQUBVpc4INgqONigHjBaf9YBYco3kTEwACjBoAAv3AkVUti2I8W2Nq1zgE",
        "CAACAgUAAxkBAAEQUBdpc4INimNkAAHp-GukssM5EUr3778AAq0aAALqAAGQVZdyE0WiCx4COAQ",
        "CAACAgUAAxkBAAEQUBhpc4IOn5oxT8qW8r-aqEGsetWZPQACTxcAAjRYiFUHjTokMOpClDgE",
        "CAACAgUAAxkBAAEQUBppc4IOZeCvBnaSTuKP2h4oTnj0fgACBBUAAlWakFUxHw3S0vZcfTgE",
        "CAACAgUAAxkBAAEQUBxpc4IPa3350tYXUf26d_Nviy8cywACCxYAAsUKkVVwb6huI3B2YzgE",
        "CAACAgUAAxkBAAEQUB1pc4IPfU_gZ6Qys4uCXUlXYmc5UwACKBgAAszSmVWaSI27doSUwTgE",
        "CAACAgUAAxkBAAEQUB9pc4IQMZ9syz2Fdb0qs1aaDhCLQwACJRkAAgvLmVWJ3q_PV1jr0DgE",
        "CAACAgUAAxkBAAEQTv9pcz6SkXdRsH5TsWOPBwN5F56-8wACoBAAAlfqcVUdJ4kalERlTTgE",
        "CAACAgUAAxkBAAEQTwABaXM-k7qfRUzUN78zyPXMs3Hhh4wAAh0TAAL2hWhV3RpXRX1cd8g4BA",
        "CAACAgUAAxkBAAEQTwJpcz6TPM36pjrzC8F-anJNnJbqTgACkBIAAtAqkFUWFLLSNNGZfDgE",
        "CAACAgUAAxkBAAEQTwZpcz6VYJ-aVbWHOsZJcpavAdXdMAACKBcAAqoXkVXuWgWwBVusNzgE",
        "CAACAgUAAxkBAAEQTwZpcz6VYJ-aVbWHOsZJcpavAdXdMAACKBcAAqoXkVXuWgWwBVusNzgE",
        "CAACAgUAAxkBAAEQTwdpcz6VCusuBhcO2wezUqQknqHaBwACthAAAnnrmFWsePzzB00VNzgE",
        "CAACAgUAAxkBAAEQTwlpcz6VONfhZHHu-8tlEJwsOyRNzQACJBEAAmaYkVUu37wFysjR-zgE",
        "CAACAgUAAxkBAAEQTwppcz6WSrm6csgBEyTMYXRfwnpSkQACJxIAAiaykVVCqfU3OG6ECzgE",
        "CAACAgUAAxkBAAEQTwxpcz6WH4uAKaqfS0fvPSdXjLYhswACzxIAAjDdkFW6aCxiX9iZcTgE",
        "CAACAgUAAxkBAAEQTw1pcz6XDQV4XA8wuV0sfPBUd3yMbwACpBAAAlymkFUBzAElsldCQDgE",
        "CAACAgUAAxkBAAEQTw9pcz6XS2m2gEzWEaFrOPBG5g7XVgACXBAAAnnpmFUkULPqb9CWtjgE",
        "CAACAgUAAxkBAAEQTxBpcz6Xl8JEaRiElynIt96QIFFhLgAC1RAAAppZmFUhqvAIRJFOiTgE",
        "CAACAgUAAxkBAAEQTztpcz9zv_PJ_ueievAwdQ4NbhqQeAAChRQAAg02oFQY_rjzLxHMojgE",
        "CAACAgUAAxkBAAEQTzxpcz9zpYuLtX5kDf0WceGoQLmG3gACBBYAAsaqqFTdGFSRXI6vaTgE",
        "CAACAgUAAxkBAAEQTz1pcz9zGy6W5h2FOPRz7bBeQCpzEQAC6RcAArONqVSSKCuWYSwjQjgE",
        "CAACAgUAAxkBAAEQTz9pcz90RLnLD8caB_a9asYM2l_B2QACHhMAAhkFqFRPB9QzOV2bKjgE",
        "CAACAgUAAxkBAAEQT0Bpcz90rHd8Yoee2wwVIZ_UB0owRwACIRUAAstUqVQpHOftLWUOtDgE",
        "CAACAgUAAxkBAAEQT0Fpcz90nR-Q4OYgaejY9deU_TGEIgACmBcAAvbxqVT9ldxH8UG7uzgE",
        "CAACAgUAAxkBAAEQT0Npcz91CcAHS5r80hjuJQGqEBAwCwACjxcAAi4XqFSuMY65BKYvLzgE",
        "CAACAgUAAxkBAAEQT0Rpcz91yp7HSIBW2HiW4nzohLuw3gACWRQAArGMqVS2zthdR-Vk2jgE",
        "CAACAgUAAxkBAAEQT0Vpcz91QWr__pgcauKrt3c2xMfSVQACpBgAAoAkqFReTfwQgeVnWDgE",
        "CAACAgUAAxkBAAEQT0dpcz92q8K-y5nRFNh_6nsQAAEFHLAAArEUAALJi6hU2bdLLAxDgjI4BA",
        "CAACAgUAAxkBAAEQT0ppcz93sao2kKvVsAenpBBc1aStVwACHhQAAqu-qVSq2PMotKpprzgE",
        "CAACAgUAAxkBAAEQT0tpcz93yMPGJWw7TuHS06q5Yo4bIQACeRkAAsoKqFSyigb3qn0s_zgE",
        "CAACAgUAAxkBAAEQT0xpcz948D3tEwQ7LiRJrcRM9dxHOAACTBcAAuiaqVQENM6GYLRBfDgE",
        "CAACAgUAAxkBAAEQT05pcz94_yo-pxTTMrdRKykqgbuH-AACTBcAAmREqFT8HkngFhkhxjgE",
        "CAACAgUAAxkBAAEQT09pcz95XZlIT0eGLYAenXxnla9MHwACFBQAAlyJqVQ3XE8tNzPpHzgE",
        "CAACAgUAAxkBAAEQT1Bpcz95PA9gYdsd0MhbVYaJ-ZFoMAAC5xcAAkA_qFTbijW8ShcgjDgE",
        "CAACAgUAAxkBAAEQT1Jpcz959UnfHm81_CH1HbBBJ95AFAACJRMAAqSIqFTl_pga7Kor6TgE",
        "CAACAgUAAxkBAAEQT1Npcz95PVsNzLbtPElnMPJB2Va97wAC1BYAAov1sVRtAAFZPASO5PY4BA",
        "CAACAgUAAxkBAAEQT1Vpcz96O_xO-VVsBd_XV6-pQXm3jQACGxoAApRZsVSNqC8hjf3-eDgE",
        "CAACAgUAAxkBAAEQT1Zpcz960TnGJKxgi10057NTg5HWuQACHxcAAnQ1qFTPcjLI8e9OczgE",
        "CAACAgUAAxkBAAEQT1hpcz97G85sX5ySXv1M_jECy_EtqQAC8BUAApODqFT3JZAuNhbmNTgE",
        "CAACAgUAAxkBAAEQT1lpcz97O2iT3Yl9W0KFNCTH7qiXQgACgBYAAuEXqVRZv2dpS4EHVzgE",
        "CAACAgUAAxkBAAEQT1tpcz98Im8mVQiU8h6VpXVR3IRsEwACPxEAAhyVsFR8ZRkxStM63zgE",
        "CAACAgUAAxkBAAEQT1xpcz98euWdB8zjPgek_0BAMb1PvQACmhYAAhAisVScH1YlQyt9yjgE",
        "CAACAgUAAxkBAAEQT15pcz998PBuw95G3z0F9cGxuhUVNwACwTMAAtAnqFSybAeoJwzLpjgE",
        "CAACAgUAAxkBAAEQT2Fpcz9-07-taN3PU02zrxQVUR3wTAACAxcAAv9JsVSml6JIBLJVGzgE",
        "CAACAgUAAxkBAAEQT2Jpcz9-97fthHAYG1amMYmLF7gbugACaBQAAuo8sVQwK__LE8DLBDgE",
        "CAACAgUAAxkBAAEQT2Rpcz9_XMk45yJwd41fbHZke9YhBAACPBkAAp0msFR8Qew-_bTkvTgE",
        "CAACAgUAAxkBAAEQT2Vpcz-AViRGFS-q7xgOPCdbx8i1owACPhYAAnFBsVQltR3HtL0kPTgE",
        "CAACAgUAAxkBAAEQT2dpcz-A5zw2-WipUm2kLN24tkjKlwACCRYAAgcssFQZImH_k4AO-jgE",
        "CAACAgUAAxkBAAEQT2hpcz-AKbPVKenz3IYudJb7KpOgiwACQBgAApX3qFTnQzEOrm3CCjgE",
        "CAACAgUAAxkBAAEQT2lpcz-AhNicVAKKm7G1Iqyr_WzniwACaBIAApOXsVRFkKpCG-aXZDgE",
        "CAACAgUAAxkBAAEQT2tpcz-BjTLpfq9UckX4vCSNN--DNAAC1hIAAj23sVS8mXaCwOIMtzgE",
        "CAACAgUAAxkBAAEQT2xpcz-BCi30UnuDynTD13MPS8uRFAACdBoAAsfYsFTYdYGV6ifnnjgE",
        "CAACAgUAAxkBAAEQT25pcz-BVnIngR6hUhCqH3AqetvxVgACAhUAAoaYsFT_eqDmpnebRzgE",
        "CAACAgUAAxkBAAEQT29pcz-Cn9ET9ouZh1vQOgP_5kXhJQACPBQAAtCgqFQ0gy-VPXbzpTgE",
        "CAACAgUAAxkBAAEQT3Fpcz-DsjPeRnkxr-mi8aGDXWo0OQACrhkAAmqcsFQVxXvNiEdCAAE4BA",
        "CAACAgUAAxkBAAEQT3Jpcz-DqXkc0GewJuXx4-eEFJnCFQACGRUAAnnjqFTQoz7jnV1eNzgE",
        "CAACAgUAAxkBAAEQT3Rpcz-Dt8e-P9wCdFV0GUk8OC4zCgACYRUAAncBsVSkNVeXzCnqbzgE",
        "CAACAgUAAxkBAAEQT3Vpcz-EC433LL7rYbDnmQhQNTUJkgACBx4AAtyRsVS-3z6RD8x45jgE",
        "CAACAgUAAxkBAAEQT3dpcz-EN3M9gQhjYyVnAAESH56S77gAAsgSAAJS6bhUU_mpQpSnlp44BA",
        "CAACAgUAAxkBAAEQT3hpcz-EjQ_Rjda0kHragEYCd2mhvQACWBkAAgRxsVQxbUPdu_J53zgE",
        "CAACAgUAAxkBAAEQT3lpcz-FLsH2LpadGa4wab1rfdYWHAACBh4AAuufsFQ_sbI3GX1f-zgE",
        "CAACAgUAAxkBAAEQT3tpcz-FOFok1_f9BM76zXkIKiItngACJxcAAmz9sVSXckkejrlmzzgE",
        "CAACAgUAAxkBAAEQT3xpcz-FI0QW_DbxFlGsfL3f-1Cv1QACqhoAAlbbsVSshO5rtPrgtjgE",
        "CAACAgUAAxkBAAEQT35pcz-GyMT2c5fhD3r_IPiaMD1TsAAC5xQAAl318VT0PIj_HCpCnDgE",
        "CAACAgUAAxkBAAEQT4Bpcz-HKSNXK5rTEEKOIhn8buAIbwAC6RMAArTp8VTLcfmXf2Q8KzgE",
        "CAACAgUAAxkBAAEQT4Fpcz-HbU4hK4ss9Scmla-xDNty7wACjxcAAnI58FSZxsexzKkdOjgE",
        "CAACAgUAAxkBAAEQT4Jpcz-HmSz-kMUu98g26mcyjouCDAACEBMAAkKW8FQeRaxT0Zg2JjgE",
        "CAACAgUAAxkBAAEQT4Rpcz-IHEcnQm0Kf6-No4vjSYOS0gACwRQAAsj78VQmpjYqBUGXrjgE"
    ]
}

# ================= FLASK SERVER =================
app = Flask('')

@app.route('/')
def home(): return "MARUF VIP SYSTEM RUNNING..."

def run_http():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= HELPER FUNCTIONS =================
def get_sheet_password():
    """Fetches the password from Cell A1 of the Google Sheet"""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        csv_data = csv.reader(io.StringIO(response.text))
        for row in csv_data:
            return row[0].strip() # Return content of A1
    except Exception as e:
        print(f"Sheet Error: {e}")
        return None

def get_random_win_sticker(streak):
    """Smartly selects win sticker based on streak or random"""
    if 0 < streak <= len(STICKERS['STREAK_LIST']):
        return STICKERS['STREAK_LIST'][streak - 1]
    return random.choice(STICKERS['RANDOM_WIN'])

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.password_verified = False
        self.game_mode = '1M'
        self.color_active = False # Color Toggle
        self.active_bet = None
        self.last_issue = None
        self.history = []
        self.streak_loss = 0
        self.session_wins = 0
        self.session_losses = 0

state = BotState()

# ================= FORMATTING (VIP STYLE) =================
def format_signal(issue, prediction, level, color_pred=None):
    # Determine Color
    main_color = "🟢 GREEN" if prediction == "BIG" else "🔴 RED"
    
    # VIP Minimalist Design
    msg = (
        f"💠 <b>MARUF VIP SYSTEM</b> 💠\n\n"
        f"🆔 <b>Period:</b> <code>{issue}</code>\n"
        f"🎯 <b>Target:</b> <b>{prediction}</b>\n"
        f"🎨 <b>Signal:</b> {main_color}\n"
    )
    
    if state.color_active and color_pred:
        c_emoji = "🔴" if color_pred == "RED" else "🟢"
        msg += f"🌈 <b>Color Bet:</b> {c_emoji} {color_pred}\n"
        
    multiplier = 3 ** level # 1, 3, 9...
    plan = f"Start (1X)" if level == 0 else f"Recovery Level {level} ({multiplier}X)"
    
    msg += (
        f"💰 <b>Plan:</b> {plan}\n\n"
        f"🔗 <a href='{LINK_REG}'>JOIN VIP NOW</a>"
    )
    return msg

def format_result(issue, result_num, result_type, my_pick, win):
    # Minimalist Result
    emoji = "✅" if win else "❌"
    res_emoji = "🟢" if result_type == "BIG" else "🔴"
    if int(result_num) in [0, 5]: res_emoji = "🟣"
    
    status = "<b>WINNER</b>" if win else "<b>MISS</b>"
    
    msg = (
        f"{emoji} <b>{status}</b> {emoji}\n\n"
        f"🆔 <code>{issue}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {result_num} ({result_type})\n"
        f"♟ <b>Pick:</b> {my_pick}\n\n"
        f"👑 <a href='{LINK_CHANNEL}'>OFFICIAL CHANNEL</a>"
    )
    return msg

def format_summary():
    # Fake Summary
    real_wins = state.session_wins
    fake_wins = real_wins + random.randint(15, 30) # Boost wins
    fake_streak = random.randint(8, 15)
    
    return (
        f"📊 <b>SESSION SUMMARY</b> 📊\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"✅ <b>Total Wins:</b> {fake_wins}\n"
        f"❌ <b>Total Loss:</b> {state.session_losses}\n"
        f"🔥 <b>Max Streak:</b> {fake_streak}\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"👋 Session Closed. See you soon!"
    )

# ================= ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 MARUF VIP Engine Started")
    
    while state.is_running:
        try:
            # 1. Fetch Data
            url = API_1M if state.game_mode == '1M' else API_30S
            resp = requests.get(f"{url}?t={int(time.time()*1000)}").json()
            latest = resp['data']['list'][0]
            issue = latest['issueNumber']
            num = int(latest['number'])
            actual_type = "BIG" if num >= 5 else "SMALL"
            
            # 2. Process Result
            if state.active_bet and state.active_bet['issue'] == issue:
                pick = state.active_bet['pick']
                is_win = (pick == actual_type)
                
                # Update Stats
                if is_win:
                    state.session_wins += 1
                    state.streak_loss = 0 # Reset recovery
                    current_streak_win = state.session_wins # Simplification for sticker
                    
                    # 1. Win Sticker (Logic: Win Big/Small -> Any Win -> Streak Win)
                    # Priority: Win Type -> Streak
                    
                    # Send General Win Sticker first
                    if actual_type == "BIG":
                        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN_BIG'])
                    else:
                        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN_SMALL'])
                    
                    # Send "WIN ANY" sticker
                    await asyncio.sleep(0.5)
                    await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN_ANY'])
                    
                    # Send Streak/Random Win Sticker
                    await asyncio.sleep(0.5)
                    s_id = get_random_win_sticker(current_streak_win)
                    await context.bot.send_sticker(TARGET_CHANNEL, s_id)
                    
                else:
                    state.session_losses += 1
                    state.streak_loss += 1
                    await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['LOSS_ANY'])

                # Send Result Msg
                await context.bot.send_message(
                    TARGET_CHANNEL, 
                    format_result(issue, num, actual_type, pick, is_win),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                # Check Death Condition (8 Step Recovery)
                if state.streak_loss >= 8:
                    await context.bot.send_message(TARGET_CHANNEL, "⚠️ <b>Market Unstable. Stop Trading for Now.</b> ⚠️", parse_mode=ParseMode.HTML)
                    state.is_running = False
                    return

                state.active_bet = None
                state.last_issue = issue
                await asyncio.sleep(3)

            # 3. New Prediction
            next_issue = str(int(issue) + 1)
            if not state.active_bet and state.last_issue != issue:
                
                # Algorithm: Pattern + Inverse on Loss
                # Simple logic for now: Follow trend, invert if loss streak > 1
                pred = actual_type 
                if state.streak_loss >= 2:
                    pred = "SMALL" if actual_type == "BIG" else "BIG"
                
                # Color Logic
                col_pred = None
                if state.color_active:
                    col_pred = "GREEN" if pred == "BIG" else "RED"
                
                # Save Bet
                state.active_bet = {'issue': next_issue, 'pick': pred}
                
                # Send Sticker (Based on Mode & Pick)
                s_key = f"PRED_{state.game_mode}_{pred}" # e.g. PRED_1M_BIG
                await context.bot.send_sticker(TARGET_CHANNEL, STICKERS[s_key])
                
                # Send Color Sticker if active
                if state.color_active:
                    c_key = "COLOR_GREEN" if col_pred == "GREEN" else "COLOR_RED"
                    await asyncio.sleep(0.2)
                    await context.bot.send_sticker(TARGET_CHANNEL, STICKERS[c_key])

                # Send Signal Msg
                await context.bot.send_message(
                    TARGET_CHANNEL,
                    format_signal(next_issue, pred, state.streak_loss, col_pred),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Engine Err: {e}")
            await asyncio.sleep(5)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.password_verified:
        await show_menu(update)
    else:
        await update.message.reply_text("🔒 <b>Enter Password to Unlock System:</b>", parse_mode=ParseMode.HTML)

async def show_menu(update):
    color_status = "ON 🟢" if state.color_active else "OFF 🔴"
    kbd = [
        ['⚡ 1M VIP', '⚡ 30S VIP'],
        [f'🎨 Color: {color_status}', '🛑 STOP SESSION']
    ]
    await update.message.reply_text(
        f"💠 <b>MARUF VIP CONTROL PANEL</b> 💠\nDev: {LINK_OWNER}",
        reply_markup=ReplyKeyboardMarkup(kbd, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    
    # Password Check
    if not state.password_verified:
        real_pass = get_sheet_password()
        if not real_pass:
            await update.message.reply_text("⚠️ Server Error: Cannot fetch password.")
            return
            
        if msg.strip() == real_pass:
            state.password_verified = True
            await update.message.reply_text("✅ <b>Access Granted!</b>", parse_mode=ParseMode.HTML)
            await show_menu(update)
        else:
            await update.message.reply_text("❌ Wrong Password!")
        return

    # Menu Actions
    if "STOP" in msg:
        if state.is_running:
            state.is_running = False
            # Send Stop Stickers
            await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['STOP']))
            # Send Fake Summary
            await context.bot.send_message(TARGET_CHANNEL, format_summary(), parse_mode=ParseMode.HTML)
            await update.message.reply_text("⛔ Bot Stopped.")
        else:
            await update.message.reply_text("⚠️ Not Running.")

    elif "Color" in msg:
        state.color_active = not state.color_active
        await show_menu(update)
        
    elif "1M" in msg or "30S" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already Running!")
            return
            
        state.game_mode = '1M' if '1M' in msg else '30S'
        state.is_running = True
        state.session_wins = 0
        state.session_losses = 0
        state.streak_loss = 0
        
        await update.message.reply_text(f"🚀 <b>Started {state.game_mode} Engine...</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
        
        # Start Sticker
        await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['START']))
        
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_msg))
    print("ALL SYSTEMS GO...")
    app.run_polling()
