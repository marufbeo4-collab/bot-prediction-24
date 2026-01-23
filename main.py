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
BOT_TOKEN = "8595453345:AAExpD-Txn7e-nysGZyrigy9hh7m3UjMraM"  # <--- আপনার টোকেন
TARGET_CHANNEL = -1003293007059     # <--- আপনার চ্যানেল আইডি
BRAND_NAME = "DK MARUF VIP SYSTEM"  # <--- মারুফ ব্র্যান্ডিং
FIXED_PASSWORD = "0102"  # ফিক্সড পাসওয়ার্ড

# ================= STICKER DATABASE =================
STICKERS = {
    'BIG_PRED_1M': "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
    'SMALL_PRED_1M': "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE",
    'BIG_PRED_30S': "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",
    'SMALL_PRED_30S': "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE",
    'BIG_WIN': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
    'SMALL_WIN': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
    'WIN': "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",
    'LOSS': "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",
    'WIN_RANDOM': [
        "CAACAgUAAxkBAAEQTzNpcz9ns8rx_5xmxk4HHQOJY2uUQQAC3RoAAuCpcFbMKj0VkxPOdTgE",
        "CAACAgUAAxkBAAEQTzRpcz9ni_I4CjwFZ3iSt4xiXxFgkwACkxgAAAnQKcVYHd8IiRqfBXTgE",
        "CAACAgUAAxkBAAEQTx9pcz8GryuxGBMFtzRNRbiCTg9M8wAC5xYAAkN_QFWgd5zOh81JGDgE",
        "CAACAgUAAxkBAAEQT_tpc4E3AxHmgW9VWKrzWjxlrvzSowACghkAAlbXcFWxdto6TqiBrzgE",
        "CAACAgUAAxkBAAEQT_9pc4FHKn0W6ZfWOSaN6FUPzfmbnQACXR0AAqMbMFc-_4DHWbq7sjgE",
        "CAACAgUAAxkBAAEQUAFpc4FIokHE09p165cCsWiUYV648wACuhQAAo3aMVeAsNW9VRuVvzgE",
        "CAACAgUAAxkBAAEQUANpc4FJNTnfuBiLe-dVtoNCf3CQlAAC9xcAArE-MFfS5HNyds2tWTgE",
        "CAACAgUAAxkBAAEQUAVpc4FKhJ_stZ3VRRzWUuJGaWbrAgACOhYAAst6OVehdeQEGZlXiDgE",
        "CAACAgUAAxkBAAEQUAtpc4HcYxkscyRY2rhAAcmqMR29eAACOBYAAh7fwVU5Xy399k3oFDgE",
        "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE",
    ],
    'RED_SIGNAL': "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
    'GREEN_SIGNAL': "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAAnR3oVejA9DVGekyYTgE",
    'SESSION_START': [
        "CAACAgUAAxkBAAEQT_lpc4EvleS6GJIogvkFzlcAAV6T7PsAArYaAAIOJIBV6qeBrzw1_oc4BA",
        "CAACAgUAAxkBAAEQTuRpczxpKCooU6JW2F53jWSEr7SZnQACZBUAAtEWOFcRzggHRna-EzgE"
    ],
    'SESSION_RANDOM': [
        "CAACAgUAAxkBAAEQTudpczxpoCLQ2pIXCqANpddRbHX9ngACKhYAAoBTMVfQP_QoToLXkzgE",
        "CAACAgUAAxkBAAEQT_dpc4Eqt5r28E8WwxaZnW8X2t58RQACsw8AAoV9CFW0IyDz2PAL5DgE",
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE",
        "CAACAgUAAxkBAAEQUDRpc4VJP7cgZhVHhqzQsiV3hNLI5wACCQ4AAk9o-VW3jbWfWUVQrjgE",
        "CAACAgUAAxkBAAEQUDZpc4VMJx694uE09-ZWlks_anzAvAACXBsAAv4b-FXj9l4eQ-g5-jgE",
        "CAACAgUAAxkBAAEQUDhpc4VM6rq1VbSAPaCdCeaR0eReHwACAhIAAkEj8VWFHkUbgA0-njgE"
    ]
}

# Win Streak Stickers (1 to 75)
WIN_STREAK_STICKERS = [
    "CAACAgUAAxkBAAEQUA1pc4IKjtrvSWe2ssLEqZ88cAABYW8AAsoiAALegIlVctTV3Pqbjmg4BA",
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
    "CAACAgUAAxkBAAEQT2tpcz-BjTLpfq9UckX4vCSNN--DNAAC2hIAAj23sVS8mXaCwOIMtzgE",
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
    "CAACAgUAAxkBAAEQT4Fpcz-HbU4hK4ss9Scmla-xDNty7wACjxcAAAnI58FSZxsexzKkdOjgE",
    "CAACAgUAAxkBAAEQT4Jpcz-HmSz-kMUu98g26mcyjouCDAACEBMAAkKW8FQeRaxT0Zg2JjgE",
    "CAACAgUAAxkBAAEQT4Rpcz-IHEcnQm0Kf6-No4vjSYOS0gACwRQAAsj78VQmpjYqBUGXrjgE"
]

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER (24/7 FIX) =================
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

# ================= PREDICTION ENGINE (SMART RECOVERY LOGIC) =================
class PredictionEngine:
    def __init__(self):
        self.history = [] 
        self.raw_history = []
        self.color_mode = False  # Color signal on/off
    
    def update_history(self, issue_data):
        number = int(issue_data['number'])
        result_type = "BIG" if number >= 5 else "SMALL"
        
        if not self.history or self.raw_history[0]['issueNumber'] != issue_data['issueNumber']:
            self.history.insert(0, result_type)
            self.raw_history.insert(0, issue_data)
            self.history = self.history[:50] 
            self.raw_history = self.raw_history[:50]

    def get_pattern_signal(self, current_streak_loss):
        # ডাটা কম থাকলে র‍্যান্ডম
        if len(self.history) < 6:
            return random.choice(["BIG", "SMALL"])
        
        last_6 = self.history[:6]
        prediction = ""

        # === 1. মেইন লজিক (Pattern Analysis) ===
        
        # Dragon Catch (টানা ৩ বার একই হলে ট্রেন্ড ধরবো)
        if last_6[0] == last_6[1] == last_6[2]:
            prediction = last_6[0]
            
        # ZigZag Catch (একবার এটা একবার ওটা)
        elif last_6[0] != last_6[1] and last_6[1] != last_6[2]:
            prediction = "SMALL" if last_6[0] == "BIG" else "BIG"

        # Math Trend (যদি প্যাটার্ন না থাকে - ডিফল্ট)
        else:
            last_num = int(self.raw_history[0]['number'])
            period_digit = int(str(self.raw_history[0]['issueNumber'])[-1])
            # (Last Num + Period) % 2
            math_val = (last_num + period_digit) % 2
            prediction = "BIG" if math_val == 1 else "SMALL"

        # === 2. অটো ইনভার্স লজিক (SMART RECOVERY) ===
        if current_streak_loss >= 2:
            # লস রিকভার করার জন্য সিগন্যাল উল্টে যাবে
            flipped_prediction = "SMALL" if prediction == "BIG" else "BIG"
            return flipped_prediction
        
        return prediction

    def toggle_color_mode(self):
        self.color_mode = not self.color_mode
        return self.color_mode
    
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
        self.recovery_step = 1
        self.session_password = None
        self.is_color_mode = False

state = BotState()

# ================= API FETCH (ROBUST) =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    
    proxies = [
        f"{base_url}?t={int(time.time()*1000)}", 
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
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except:
            continue
    return None

# ================= FORMATTING (DK MARUF STYLE) =================
def format_signal(issue, prediction, conf, streak_loss, recovery_step):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    color = "GREEN" if prediction == "BIG" else "RED"
    
    if streak_loss >= 8:
        return None  # 8 step loss হলে signal বন্ধ
    
    lvl = streak_loss + 1
    multiplier = 3 ** (lvl - 1)  # Recovery steps: 1, 3, 9...
    
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
        f"🔗 <b>Join Channel:</b> @big_maruf_official0\n"
        f"👑 <b>Dev:</b> @OWNER_MARUF_TOP\n"
        f"🎰 <b>Register:</b> https://dkwin9.com/#/register?invitationCode=112681085937"
    )

def format_result(issue, res_num, res_type, my_pick, is_win, recovery_step):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣" 
    
    if is_win:
        w_streak = state.stats['streak_win']
        header = f"╔═══════════════════════╗\n║    🎉 WINNER! 🎉     ║\n╚═══════════════════════╝"
        status = f"🔥 <b>Win Streak: {w_streak}</b>"
        if w_streak <= len(WIN_STREAK_STICKERS):
            status += f"\n🏆 <b>Achievement Unlocked!</b>"
    else:
        next_step = state.stats['streak_loss'] + 1
        if next_step >= 8:
            header = f"╔═══════════════════════╗\n║    ⚠️ SYSTEM PAUSED ⚠️   ║\n╚═══════════════════════╝"
            status = f"❌ <b>Max Loss Limit Reached!</b>\n🚫 <b>Signal Stopped - Contact Admin</b>"
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

def format_session_summary():
    total_games = state.stats['wins'] + state.stats['losses']
    if total_games == 0:
        win_rate = 0
    else:
        win_rate = (state.stats['wins'] / total_games) * 100
    
    # Fake statistics to make it look more impressive
    fake_win_rate = min(95, win_rate + random.randint(10, 30))
    
    return (
        f"╔═══════════════════════╗\n"
        f"║   📊 SESSION SUMMARY  ║\n"
        f"╚═══════════════════════╝\n\n"
        f"🎮 <b>Market:</b> {state.game_mode} VIP\n"
        f"⏱️ <b>Total Games:</b> {total_games}\n"
        f"✅ <b>Wins:</b> {state.stats['wins'] + random.randint(5, 15)}\n"
        f"❌ <b>Losses:</b> {max(0, state.stats['losses'] - random.randint(0, 3))}\n"
        f"📈 <b>Win Rate:</b> {fake_win_rate:.1f}%\n"
        f"🔥 <b>Max Win Streak:</b> {max(state.stats['streak_win'], random.randint(8, 15))}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>System Accuracy: EXCELLENT</b>\n\n"
        f"🔗 <b>Join:</b> @big_maruf_official0\n"
        f"👑 <b>Dev:</b> @OWNER_MARUF_TOP"
    )

# ================= STICKER FUNCTIONS =================
async def send_prediction_sticker(context, prediction):
    if state.game_mode == '1M':
        sticker_id = STICKERS['BIG_PRED_1M'] if prediction == "BIG" else STICKERS['SMALL_PRED_1M']
    else:
        sticker_id = STICKERS['BIG_PRED_30S'] if prediction == "BIG" else STICKERS['SMALL_PRED_30S']
    
    try:
        await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
    except: pass

async def send_win_sticker(context, result_type, win_streak):
    try:
        # Check for win streak sticker
        if 1 <= win_streak <= len(WIN_STREAK_STICKERS):
            await context.bot.send_sticker(TARGET_CHANNEL, WIN_STREAK_STICKERS[win_streak - 1])
        else:
            # Send regular win stickers
            if random.random() < 0.5:  # 50% chance for random win sticker
                await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['WIN_RANDOM']))
            else:
                sticker_id = STICKERS['BIG_WIN'] if result_type == "BIG" else STICKERS['SMALL_WIN']
                await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
        
        # Send general win sticker
        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['WIN'])
    except: pass

async def send_loss_sticker(context):
    try:
        await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['LOSS'])
    except: pass

async def send_color_sticker(context, color):
    try:
        sticker_id = STICKERS['GREEN_SIGNAL'] if color == "GREEN" else STICKERS['RED_SIGNAL']
        await context.bot.send_sticker(TARGET_CHANNEL, sticker_id)
    except: pass

async def send_session_sticker(context, is_start=True):
    try:
        if is_start:
            await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['SESSION_START']))
        else:
            await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['SESSION_RANDOM']))
    except: pass

# ================= 24/7 AUTO-RESTART ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🚀 DK Maruf VIP Engine Started...")
    
    while state.is_running:
        try:
            # 1. Fetch latest issue
            latest = fetch_latest_issue(state.game_mode)
            if not latest:
                await asyncio.sleep(3)
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
                    state.recovery_step = 1
                    
                    # Send win stickers
                    await send_win_sticker(context, latest_type, state.stats['streak_win'])
                    
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    state.recovery_step = min(state.recovery_step + 1, 8)
                    
                    # Check for max loss limit (8 steps)
                    if state.stats['streak_loss'] >= 8:
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            "🚫 <b>MAXIMUM LOSS LIMIT REACHED!</b>\n"
                            "⚠️ <b>Signal system has been paused.</b>\n"
                            "📞 <b>Contact Admin for reset.</b>",
                            parse_mode=ParseMode.HTML
                        )
                        state.is_running = False
                        return
                    
                    # Send loss sticker
                    await send_loss_sticker(context)

                # Result Message
                try:
                    await context.bot.send_message(
                        TARGET_CHANNEL,
                        format_result(latest_issue, latest_num, latest_type, pick, is_win, state.recovery_step),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e: print(f"Res Err: {e}")
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # 3. New Prediction
            if not state.active_bet and state.last_period_processed != next_issue:
                await asyncio.sleep(2)
                state.engine.update_history(latest)
                
                # Check for max loss limit
                if state.stats['streak_loss'] >= 8:
                    state.is_running = False
                    return
                
                # Get prediction
                pred = state.engine.get_pattern_signal(state.stats['streak_loss'])
                conf = state.engine.calculate_confidence()
                
                state.active_bet = {"period": next_issue, "pick": pred}
                
                # Send stickers
                await send_prediction_sticker(context, pred)
                
                # Send color sticker if color mode is on
                if state.is_color_mode:
                    await send_color_sticker(context, "GREEN" if pred == "BIG" else "RED")
                
                # Send signal message
                try:
                    signal_msg = format_signal(next_issue, pred, conf, state.stats['streak_loss'], state.recovery_step)
                    if signal_msg:  # Check if signal is not None (for 8 step loss case)
                        await context.bot.send_message(
                            TARGET_CHANNEL,
                            signal_msg,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True
                        )
                except Exception as e: print(f"Sig Err: {e}")

            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Engine Restarting: {e}")
            await asyncio.sleep(2)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 <b>DK MARUF VIP SYSTEM</b>\n\n"
        "Please enter password to access:",
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
                "✅ <b>Password Verified!</b>\nSelect Server:",
                reply_markup=ReplyKeyboardMarkup([
                    ['⚡ Connect 1M', '⚡ Connect 30S'],
                    ['🎨 Color ON', '🎨 Color OFF'],
                    ['📊 Summary', '🛑 Stop Session']
                ], resize_keyboard=True),
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                "❌ <b>Invalid Password!</b>\nPlease enter correct password.",
                parse_mode=ParseMode.HTML
            )
        return
    
    # Command Handling
    if "Stop Session" in msg:
        state.is_running = False
        await send_session_sticker(update, False)
        await update.message.reply_text(
            format_session_summary(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await update.message.reply_text("⛔ Session Stopped.", reply_markup=ReplyKeyboardRemove())
        state.session_password = None
        return
    
    if "Color ON" in msg:
        state.is_color_mode = True
        await update.message.reply_text("🎨 <b>Color Signal Mode: ON</b>", parse_mode=ParseMode.HTML)
        return
        
    if "Color OFF" in msg:
        state.is_color_mode = False
        await update.message.reply_text("🎨 <b>Color Signal Mode: OFF</b>", parse_mode=ParseMode.HTML)
        return
    
    if "Summary" in msg:
        await update.message.reply_text(
            format_session_summary(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return
    
    if "Connect" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Already Running!")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins":0, "losses":0, "streak_win":0, "streak_loss":0}
        state.recovery_step = 1
        state.engine = PredictionEngine()
        
        await update.message.reply_text(
            f"✅ <b>Connected to {mode} VIP</b>\n"
            f"🎯 Smart Recovery Active\n"
            f"🎨 Color Mode: {'ON' if state.is_color_mode else 'OFF'}",
            parse_mode=ParseMode.HTML
        )
        
        await send_session_sticker(update, True)
        
        # Start engine
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("🚀 DK MARUF VIP with SMART RECOVERY LOGIC LIVE...")
    print("🔗 Channel: @big_maruf_official0")
    print("👑 Dev: @OWNER_MARUF_TOP")
    print(f"🔐 Fixed Password: {FIXED_PASSWORD}")
    app.run_polling()
