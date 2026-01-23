import asyncio
import logging
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
BOT_TOKEN = "8595453345:AAGndyFZES2qZL37LRc3CeqGxKyWq7HeTxk"  # আপনার টোকেন
TARGET_CHANNEL = -1003293007059     # আপনার চ্যানেল আইডি

# LINKS & BRANDING
BRAND_NAME = "👑 𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐕𝐈𝐏 𝐒𝐘𝐒𝐓𝐄𝐌 👑"
OWNER_LINK = "@OWNER_MARUF_TOP"
CHANNEL_LINK = "https://t.me/big_maruf_official0"
REG_LINK = "https://dkwin9.com/#/register?invitationCode=112681085937"

# GOOGLE SHEET CONFIG (PASSWORD)
# শীটটি অবশ্যই "Anyone with the link" -> "Viewer" মোডে থাকতে হবে
SHEET_ID = "1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# ================= STICKER DATABASE (HUGE COLLECTION) =================
STICKERS = {
    'START': [
        "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA",
        "CAACAgUAAxkBAAEQT_lpc4EvleS6GJIogvkFzlcAAV6T7PsAArYaAAIOJIBV6qeBrzw1_oc4BA",
        "CAACAgUAAxkBAAEQTuRpczxpKCooU6JW2F53jWSEr7SZnQACZBUAAtEWOFcRzggHRna-EzgE"
    ],
    'STOP': [
        "CAACAgUAAxkBAAEQTudpczxpoCLQ2pIXCqANpddRbHX9ngACKhYAAoBTMVfQP_QoToLXkzgE",
        "CAACAgUAAxkBAAEQT_dpc4Eqt5r28E8WwxaZnW8X2t58RQACsw8AAoV9CFW0IyDz2PAL5DgE",
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE",
        "CAACAgUAAxkBAAEQUDRpc4VJP7cgZhVHhqzQsiV3hNLI5wACCQ4AAk9o-VW3jbWfWUVQrjgE"
    ],
    'PRED_1M_BIG': ["CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE"],
    'PRED_1M_SMALL': ["CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE"],
    'PRED_30S_BIG': ["CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE"],
    'PRED_30S_SMALL': ["CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE"],
    
    'WIN_BIG': ["CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE"],
    'WIN_SMALL': ["CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE"],
    'WIN_GENERAL': [
        "CAACAgUAAxkBAAEQTydpcz9Kv1L2PJyNlbkcZpcztKKxfQACDRsAAoq1mFcAAYLsJ33TdUA4BA",
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
    'LOSS': [
        "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",
        "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE"
    ],
    'COLOR_RED': ["CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE"],
    'COLOR_GREEN': ["CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE"],
    
    # Random Win Stickers (Huge List)
    'WIN_STREAK': [
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
        "CAACAgUAAxkBAAEQT4Rpcz-IHEcnQm0Kf6-No4vjSYOS0gACwRQAAsj78VQmpjYqBUGXrjgE",
        "CAACAgUAAxkBAAEQUDZpc4VMJx694uE09-ZWlks_anzAvAACXBsAAv4b-FXj9l4eQ-g5-jgE",
        "CAACAgUAAxkBAAEQUDhpc4VM6rq1VbSAPaCdCeaR0eReHwACAhIAAkEj8VWFHkUbgA0-njgE"
    ]
}

# API LINKS
API_1M = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
API_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# ================= FLASK SERVER (24/7 FIX) =================
app = Flask('')

@app.route('/')
def home():
    return "DK MARUF VIP SYSTEM RUNNING..."

def run_http():
    port = int(os.environ.get("PORT", 8080))
    try: app.run(host='0.0.0.0', port=port)
    except: pass

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ================= HELPER FUNCTIONS =================
def get_sheet_password():
    """Google Sheet এর Cell A1 থেকে পাসওয়ার্ড পড়ে"""
    try:
        response = requests.get(SHEET_URL)
        if response.status_code == 200:
            csv_data = csv.reader(io.StringIO(response.text))
            rows = list(csv_data)
            if rows and rows[0]:
                return rows[0][0].strip() # Return A1 value
    except Exception as e:
        print(f"Sheet Error: {e}")
    return "admin123" # Default fallback (যদি শীট লোড না হয়)

def get_random_sticker(category_list):
    """লিস্ট থেকে র‍্যান্ডম স্টিকার সিলেক্ট করে"""
    if not category_list: return None
    return random.choice(category_list)

def generate_fake_summary(real_wins, real_loss):
    """সেশন শেষে ফেক উইন দেখানোর জন্য"""
    fake_wins = real_wins + random.randint(5, 12)
    fake_streak = random.randint(7, 15)
    profit = (fake_wins * 1000) - (real_loss * 1000) + random.randint(500, 5000)
    return fake_wins, fake_streak, profit

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
        if len(self.history) < 6: return random.choice(["BIG", "SMALL"])
        last_6 = self.history[:6]
        
        # Pattern Logic
        if last_6[0] == last_6[1] == last_6[2]: prediction = last_6[0] # Dragon
        elif last_6[0] != last_6[1] and last_6[1] != last_6[2]: prediction = "SMALL" if last_6[0] == "BIG" else "BIG" # ZigZag
        else:
            last_num = int(self.raw_history[0]['number'])
            period_digit = int(str(self.raw_history[0]['issueNumber'])[-1])
            prediction = "BIG" if ((last_num + period_digit) % 2) == 1 else "SMALL"

        # Smart Recovery (Inverse on streak loss > 2)
        if current_streak_loss >= 2:
            return "SMALL" if prediction == "BIG" else "BIG"
        
        return prediction

# ================= BOT STATE =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.game_mode = '1M'
        self.color_mode = False # কালার সিগন্যাল ডিফল্ট অফ
        self.password_verified = False
        self.engine = PredictionEngine()
        self.active_bet = None
        self.last_period_processed = None
        self.stats = {"wins": 0, "losses": 0, "streak_win": 0, "streak_loss": 0}

state = BotState()

# ================= API FETCH =================
def fetch_latest_issue(mode):
    base_url = API_1M if mode == '1M' else API_30S
    try:
        response = requests.get(f"{base_url}?t={int(time.time()*1000)}", timeout=5)
        data = response.json()
        if data and "data" in data and "list" in data["data"]:
            return data["data"]["list"][0]
    except: pass
    return None

# ================= VIP FORMATTING =================
def format_signal(issue, prediction, conf, streak_loss, show_color):
    emoji = "🟢" if prediction == "BIG" else "🔴"
    
    # 8-Step Recovery Logic
    lvl = streak_loss + 1
    multipliers = [1, 3, 9, 27, 81, 243, 729, 2187] # Martingale / 3x Plan
    amount_x = multipliers[lvl-1] if lvl <= 8 else "MAX"
    
    plan_text = f"⚡ <b>LEVEL {lvl} - BET {amount_x}X</b>"
    if lvl == 1: plan_text = "🟢 <b>START INVESTMENT (1X)</b>"
    if lvl >= 7: plan_text = f"🔥 <b>DO OR DIE - LEVEL {lvl} ({amount_x}X)</b>"

    color_text = ""
    if show_color:
        c_emoji = "🟩" if prediction == "BIG" else "🟥"
        color_text = f"🎨 <b>COLOR:</b> {prediction} {c_emoji}\n"

    return (
        f"💎 <b>{BRAND_NAME}</b> 💎\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"🎲 <b>PREDICTION TIME</b>\n"
        f"🆔 <b>PERIOD:</b> <code>{issue}</code>\n"
        f"📊 <b>SIGNAL:</b> ▶️ <b>{prediction}</b> ◀️\n"
        f"{color_text}"
        f"🎯 <b>CONFIDENCE:</b> {conf}%\n"
        f"💰 <b>STRATEGY:</b> {plan_text}\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"🔗 <a href='{REG_LINK}'><b>REGISTER NOW</b></a> | <a href='{CHANNEL_LINK}'><b>JOIN CHANNEL</b></a>\n"
        f"👨‍💻 <b>OWNER:</b> {OWNER_LINK}"
    )

def format_result(issue, res_num, res_type, my_pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣"
    
    if is_win:
        header = "🎉 <b>BOOM! WINNER!</b> 🎉"
        status = "✅ <b>PROFIT ADDED</b>"
    else:
        header = "❌ <b>LOSS - NEXT LEVEL</b> ❌"
        status = "⚠️ <b>PREPARE FOR RECOVERY</b>"

    return (
        f"{header}\n"
        f"🆔 <b>PERIOD:</b> <code>{issue}</code>\n"
        f"🔢 <b>RESULT:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🙋 <b>MY PICK:</b> {my_pick}\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{status}\n"
        f"🔗 <a href='{REG_LINK}'><b>CREATE ACCOUNT</b></a>"
    )

# ================= ENGINE LOOP =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    # সেশন শুরুর আগে পাসওয়ার্ড রি-চেক
    required_pass = get_sheet_password()
    print(f"Server Pass: {required_pass}") # Debug check

    while state.is_running:
        try:
            # 8-Step Failure Check (Auto Stop)
            if state.stats['streak_loss'] >= 8:
                state.is_running = False
                await context.bot.send_message(
                    TARGET_CHANNEL,
                    "⛔ <b>SESSION STOPPED AUTOMATICALLY</b>\n"
                    "⚠️ <b>Market is too volatile (8 Level Hit).</b>\n"
                    "🛡️ <b>Capital Protection Mode Activated.</b>\n"
                    "Rest for 2 hours and come back!",
                    parse_mode=ParseMode.HTML
                )
                try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(STICKERS['STOP']))
                except: pass
                return

            # 1. Fetch Data
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
                    
                    # Win Sticker Logic
                    if state.game_mode == '1M':
                         stk = STICKERS['WIN_BIG'] if latest_type == "BIG" else STICKERS['WIN_SMALL']
                    else:
                         # 30S or General Win Random
                         stk = STICKERS['WIN_GENERAL'] + STICKERS['WIN_STREAK']
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(stk))
                    except: pass
                    
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_win'] = 0
                    state.stats['streak_loss'] += 1
                    
                    try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(STICKERS['LOSS']))
                    except: pass

                # Send Result Message
                await context.bot.send_message(
                    TARGET_CHANNEL,
                    format_result(latest_issue, latest_num, latest_type, pick, is_win),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                
                state.active_bet = None
                state.last_period_processed = latest_issue

            # 3. New Prediction
            if not state.active_bet and state.last_period_processed != next_issue:
                await asyncio.sleep(2)
                state.engine.update_history(latest)
                
                pred = state.engine.get_pattern_signal(state.stats['streak_loss'])
                conf = random.randint(90, 99)
                
                state.active_bet = {"period": next_issue, "pick": pred}
                
                # Signal Sticker Selection
                if state.game_mode == '1M':
                    s_stk_list = STICKERS['PRED_1M_BIG'] if pred == "BIG" else STICKERS['PRED_1M_SMALL']
                else:
                    s_stk_list = STICKERS['PRED_30S_BIG'] if pred == "BIG" else STICKERS['PRED_30S_SMALL']
                
                try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(s_stk_list))
                except: pass

                # Color Sticker (Optional)
                if state.color_mode:
                    c_stk = STICKERS['COLOR_GREEN'] if pred == "BIG" else STICKERS['COLOR_RED']
                    try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(c_stk))
                    except: pass

                # Signal Message
                await context.bot.send_message(
                    TARGET_CHANNEL,
                    format_signal(next_issue, pred, conf, state.stats['streak_loss'], state.color_mode),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(2)

# ================= COMMAND HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.password_verified = False # Reset verification
    await update.message.reply_text(
        "🔒 <b>SECURITY CHECK</b>\n"
        "Please enter the access password:",
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    user_id = update.effective_user.id
    
    # --- PASSWORD LOGIC ---
    if not state.password_verified:
        correct_pass = get_sheet_password()
        if msg.strip() == correct_pass:
            state.password_verified = True
            await update.message.reply_text(
                f"✅ <b>ACCESS GRANTED</b>\nWelcome Boss {update.effective_user.first_name}",
                parse_mode=ParseMode.HTML,
                reply_markup=ReplyKeyboardMarkup([
                    ['⚡ 1M VIP', '⚡ 30S VIP'],
                    ['🎨 Color: OFF', '🛑 STOP SESSION']
                ], resize_keyboard=True)
            )
        else:
            await update.message.reply_text("❌ <b>WRONG PASSWORD!</b> Try again.")
        return

    # --- CONTROL LOGIC ---
    if "STOP" in msg:
        if state.is_running:
            state.is_running = False
            # Fake Summary Generation
            fw, fs, fp = generate_fake_summary(state.stats['wins'], state.stats['losses'])
            
            summary = (
                f"📊 <b>SESSION SUMMARY</b>\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"✅ <b>Total Wins:</b> {fw}\n"
                f"❌ <b>Total Loss:</b> {random.randint(0,2)}\n"
                f"🔥 <b>Max Streak:</b> {fs}\n"
                f"💵 <b>Est. Profit:</b> +{fp} BDT\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"👋 <i>Session Closed. See you soon!</i>"
            )
            await context.bot.send_message(TARGET_CHANNEL, summary, parse_mode=ParseMode.HTML)
            try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(STICKERS['STOP']))
            except: pass
            
            await update.message.reply_text("⛔ Bot Stopped & Summary Sent.", reply_markup=ReplyKeyboardRemove())
            state.password_verified = False # Lock bot again
        else:
            await update.message.reply_text("⚠️ Bot is not running.")

    elif "Color" in msg:
        state.color_mode = not state.color_mode
        status = "ON" if state.color_mode else "OFF"
        # Update button text
        new_keyboard = [['⚡ 1M VIP', '⚡ 30S VIP'], [f'🎨 Color: {status}', '🛑 STOP SESSION']]
        await update.message.reply_text(f"🎨 Color Signals: <b>{status}</b>", reply_markup=ReplyKeyboardMarkup(new_keyboard, resize_keyboard=True), parse_mode=ParseMode.HTML)

    elif "VIP" in msg:
        if state.is_running:
            await update.message.reply_text("⚠️ Bot already running! Stop first.")
            return
            
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {"wins":0, "losses":0, "streak_win":0, "streak_loss":0}
        state.engine = PredictionEngine()
        
        # Start Sticker
        try: await context.bot.send_sticker(TARGET_CHANNEL, get_random_sticker(STICKERS['START']))
        except: pass
        
        await update.message.reply_text(f"🚀 <b>{mode} VIP ENGINE STARTED</b>", parse_mode=ParseMode.HTML)
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("👑 DK MARUF VIP SYSTEM LIVE...")
    app.run_polling()
