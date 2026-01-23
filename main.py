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
BOT_TOKEN = "8595453345:AAExpD-Txn7e-nysGZyrigy9hh7m3UjMraM"
TARGET_CHANNEL = -1003293007059 
BRAND_NAME = "👑 𝐃𝐊 𝐌𝐀𝐑𝐔𝐅 𝐕𝐈𝐏 𝐊𝐈𝐍𝐆 👑"

# LINKS
LINK_REG = "https://dkwin9.com/#/register?invitationCode=112681085937"
LINK_CHANNEL = "https://t.me/big_maruf_official0"
LINK_OWNER = "https://t.me/OWNER_MARUF_TOP"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1foCsja-2HRi8HHjnMP8CyheaLOwk-ZiJ7a5uqs9khvo/export?format=csv"

# ================= STICKER DATABASE (ALL 75 ADDED) =================
STICKERS = {
    'START': [
        "CAACAgUAAxkBAAEQT_lpc4EvleS6GJIogvkFzlcAAV6T7PsAArYaAAIOJIBV6qeBrzw1_oc4BA",
        "CAACAgUAAxkBAAEQTuRpczxpKCooU6JW2F53jWSEr7SZnQACZBUAAtEWOFcRzggHRna-EzgE",
        "CAACAgUAAxkBAAEQTjJpcmWOexDHyK90IXQU5Qzo18uBKAACwxMAAlD6QFRRMClp8Q4JAAE4BA"
    ],
    'STOP': [
        "CAACAgUAAxkBAAEQTudpczxpoCLQ2pIXCqANpddRbHX9ngACKhYAAoBTMVfQP_QoToLXkzgE",
        "CAACAgUAAxkBAAEQT_dpc4Eqt5r28E8WwxaZnW8X2t58RQACsw8AAoV9CFW0IyDz2PAL5DgE",
        "CAACAgUAAxkBAAEQThhpcmTQoyChKDDt5k4zJRpKMpPzxwACqxsAAheUwFUano7QrNeU_jgE",
        "CAACAgUAAxkBAAEQUDZpc4VMJx694uE09-ZWlks_anzAvAACXBsAAv4b-FXj9l4eQ-g5-jgE",
        "CAACAgUAAxkBAAEQUDhpc4VM6rq1VbSAPaCdCeaR0eReHwACAhIAAkEj8VWFHkUbgA0-njgE"
    ],
    'SIGNAL': {
        '1M': {
            'BIG': "CAACAgUAAxkBAAEQTr5pcwrBGAZ5xLp_AUAFWSiWiS0rOwAC4R0AAg7MoFcKItGd1m2CsjgE",
            'SMALL': "CAACAgUAAxkBAAEQTr9pcwrC7iH-Ei5xHz2QapE-DFkgLQACXxkAAoNWmFeTSY6h7y7VlzgE"
        },
        '30S': {
            'BIG': "CAACAgUAAxkBAAEQTuVpczxpbSG9e1hL9__qlNP1gBnIsQAC-RQAAmC3GVT5I4duiXGKpzgE",
            'SMALL': "CAACAgUAAxkBAAEQTuZpczxpS6btJ7B4he4btOzGXKbXWwAC2RMAAkYqGFTKz4vHebETgDgE"
        }
    },
    'RESULT': {
        'WIN_BIG': "CAACAgUAAxkBAAEQTjhpcmXknd41yv99at8qxdgw3ivEkAACyRUAAraKsFSky2Ut1kt-hjgE",
        'WIN_SMALL': "CAACAgUAAxkBAAEQTjlpcmXkF8R0bNj0jb1Xd8NF-kaTSQAC7DQAAhnRsVTS3-Z8tj-kajgE",
        'LOSS': [
            "CAACAgUAAxkBAAEQTytpcz9VQoHyZ5ClbKSqKCJbpqX6yQACahYAAl1wAAFUL9xOdyh8UL84BA",
            "CAACAgUAAxkBAAEQTcVpclMOQ7uFjrUs9ss15ij7rKBj9AACsB0AAobyqFV1rI6qlIIdeTgE",
            "CAACAgUAAxkBAAEQTh5pcmTbrSEe58RRXvtu_uwEAWZoQQAC5BEAArgxYVUhMlnBGKmcbzgE"
        ]
    },
    # এইখানে আপনার দেওয়া সবগুলা উইন স্টিকার আছে (৭৫+)
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
        "CAACAgUAAxkBAAEQUCdpc4IuoaqPZ-5vn2RTlJZ_kbeXHQACXRUAAgln-FQ8iTzzJg_GLzgE",
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
        "CAACAgUAAxkBAAEQT4Rpcz-IHEcnQm0Kf6-No4vjSYOS0gACwRQAAsj78VQmpjYqBUGXrjgE"
    ],
    'COLOR': {
        'RED': "CAACAgUAAxkBAAEQUClpc4JDd9n_ZQ45hPk-a3tEjFXnugACbhgAAqItoVd2zRs4VkXOHDgE",
        'GREEN': "CAACAgUAAxkBAAEQUCppc4JDHWjTzBCFIOx2Hcjtz9UnnAACzRwAAnR3oVejA9DVGekyYTgE"
    }
}

# ================= FLASK SERVER =================
app = Flask('')
@app.route('/')
def home(): return "MARUF ENGINE ONLINE"
def run_http(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_http).start()

# ================= DATA FETCHING (ROBUST) =================
def fetch_latest_issue(mode):
    api_url = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json" if mode == '1M' else "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    
    urls = [
        f"{api_url}?t={int(time.time()*1000)}",
        f"https://api.allorigins.win/raw?url={api_url}",
        f"https://corsproxy.io/?{api_url}",
        f"https://thingproxy.freeboard.io/fetch/{api_url}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=4)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "list" in data["data"]:
                    return data["data"]["list"][0]
        except:
            continue
    return None

# ================= STATE MANAGEMENT =================
class BotState:
    def __init__(self):
        self.is_running = False
        self.auth = False
        self.game_mode = '1M'
        self.color_mode = False
        self.active_bet = None
        self.last_period = None
        self.stats = {'wins': 0, 'losses': 0, 'streak_loss': 0, 'streak_win': 0}

state = BotState()

# ================= MESSAGE FORMATS =================
def get_signal_msg(period, pick, conf, loss_lvl, color=None):
    emoji = "🟢" if pick == "BIG" else "🔴"
    type_txt = "𝐁𝐈𝐆" if pick == "BIG" else "𝐒𝐌𝐀𝐋𝐋"
    
    # 8 Level Logic
    lvl = loss_lvl + 1
    multi = 3 ** (lvl - 1)
    
    plan_txt = "⚡ 𝐒𝐭𝐚𝐫𝐭 (1X)"
    if lvl > 1: plan_txt = f"⚠️ 𝐑𝐞𝐜𝐨𝐯𝐞𝐫𝐲 𝐋𝐞𝐯𝐞𝐥 {lvl} ({multi}𝐗)"
    if lvl >= 7: plan_txt = f"🔥 𝐃𝐎 𝐎𝐑 𝐃𝐈𝐄 𝐋𝐞𝐯𝐞𝐥 {lvl} ({multi}𝐗)"
    
    col_txt = ""
    if color and state.color_mode:
        c_e = "🟢" if color == "GREEN" else "🔴"
        col_txt = f"\n🎨 𝐂𝐨𝐥𝐨𝐫 : {color} {c_e}"

    return (
        f"🛡 <b>{BRAND_NAME}</b> 🛡\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💎 <b>Market:</b> {state.game_mode} VIP\n"
        f"🆔 <b>Period:</b> <code>{period}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎯 <b>SIGNAL:</b>  👉 <b>{type_txt}</b> 👈\n"
        f"📊 <b>Bet:</b> {emoji} + {type_txt}{col_txt}\n"
        f"🚀 <b>Confidence:</b> {conf}%\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"💰 <b>Plan:</b> {plan_txt}\n"
        f"⚡ <b>Maintain 8 Level Funds!</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🌐 <a href='{LINK_REG}'>Create Account Here</a>\n"
        f"👑 <a href='{LINK_OWNER}'>Owner Maruf Top</a>"
    )

def get_result_msg(period, res_num, res_type, pick, is_win):
    res_emoji = "🟢" if res_type == "BIG" else "🔴"
    if int(res_num) in [0, 5]: res_emoji = "🟣"
    
    if is_win:
        header = "🎉 <b>BOOM! WINNER!</b> 🎉"
        status = f"🔥 <b>Win Streak: {state.stats['streak_win']}</b> 🔥"
    else:
        header = "❌ <b>LOSS / NEXT LEVEL</b> ❌"
        status = f"⚠️ <b>Go For Recovery Level {state.stats['streak_loss'] + 1}</b>"

    return (
        f"{header}\n"
        f"🆔 <b>Period:</b> <code>{period}</code>\n"
        f"🎲 <b>Result:</b> {res_emoji} {res_num} ({res_type})\n"
        f"🎯 <b>My Pick:</b> {pick}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"{status}\n"
        f"📶 <b>System by DK Maruf</b>\n"
        f"🔗 <a href='{LINK_CHANNEL}'>Join Official Channel</a>"
    )

# ================= CORE ENGINE =================
async def game_engine(context: ContextTypes.DEFAULT_TYPE):
    print("🔥 ENGINE STARTED...")
    while state.is_running:
        try:
            # 1. Fetch Data
            data = fetch_latest_issue(state.game_mode)
            
            if not data:
                print("⚠️ API Error - Retrying...")
                await asyncio.sleep(2)
                continue 

            period = data['issueNumber']
            number = int(data['number'])
            result = "BIG" if number >= 5 else "SMALL"
            next_period = str(int(period) + 1)

            # 2. Check Result
            if state.active_bet and state.active_bet['period'] == period:
                my_pick = state.active_bet['pick']
                is_win = (my_pick == result)
                
                # --- WIN LOGIC ---
                if is_win:
                    state.stats['wins'] += 1
                    state.stats['streak_loss'] = 0
                    state.stats['streak_win'] += 1
                    
                    # Sticker Select (Random from 75 list or Specific)
                    stk = STICKERS['RESULT']['WIN_BIG'] if result == "BIG" else STICKERS['RESULT']['WIN_SMALL']
                    if random.random() < 0.6: # 60% Chance to show from BIG 75 list
                        stk = random.choice(STICKERS['RANDOM_WIN'])
                    if state.color_mode:
                        if number in [1,3,7,9]: stk = STICKERS['COLOR']['GREEN']
                        elif number in [2,4,6,8]: stk = STICKERS['COLOR']['RED']

                    try: await context.bot.send_sticker(TARGET_CHANNEL, stk)
                    except: pass
                    
                    await context.bot.send_message(TARGET_CHANNEL, get_result_msg(period, number, result, my_pick, True), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

                # --- LOSS LOGIC ---
                else:
                    state.stats['losses'] += 1
                    state.stats['streak_loss'] += 1
                    state.stats['streak_win'] = 0
                    
                    if state.stats['streak_loss'] >= 8:
                        await context.bot.send_message(TARGET_CHANNEL, "⛔ <b>8 Level Crossed. Stopping Bot for Safety.</b>", parse_mode=ParseMode.HTML)
                        state.is_running = False
                        state.active_bet = None
                        return

                    try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['RESULT']['LOSS']))
                    except: pass
                    
                    await context.bot.send_message(TARGET_CHANNEL, get_result_msg(period, number, result, my_pick, False), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

                state.active_bet = None
                state.last_period = period

            # 3. Make Prediction
            if not state.active_bet and state.last_period != next_period:
                await asyncio.sleep(4)
                
                if state.stats['streak_loss'] >= 2:
                    pred = "SMALL" if result == "BIG" else "BIG" # Reverse
                else:
                    pred = "BIG" if result == "SMALL" else "SMALL" 
                    if random.random() > 0.5: pred = result 

                col_pred = None
                if state.color_mode:
                    col_pred = random.choice(["RED", "GREEN"])

                state.active_bet = {'period': next_period, 'pick': pred}
                
                s_key = '1M' if state.game_mode == '1M' else '30S'
                try: await context.bot.send_sticker(TARGET_CHANNEL, STICKERS['SIGNAL'][s_key][pred])
                except: pass
                
                await context.bot.send_message(
                    TARGET_CHANNEL, 
                    get_signal_msg(next_period, pred, random.randint(93, 99), state.stats['streak_loss'], col_pred),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

            await asyncio.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(3)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if state.is_running:
        await update.message.reply_text("⚠️ Bot Running...")
        return
    await update.message.reply_text("🔒 <b>ENTER PASSWORD:</b>", parse_mode=ParseMode.HTML)
    state.auth = False

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    
    # Password Logic
    if not state.auth:
        try:
            r = requests.get(SHEET_URL)
            real_pass = list(csv.reader(io.StringIO(r.text)))[0][0]
            if msg == real_pass:
                state.auth = True
                kb = [['🚀 Start 1M', '🚀 Start 30S'], ['🎨 Color ON/OFF', '🛑 Stop']]
                await update.message.reply_text("✅ <b>Verified!</b>", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("❌ Wrong Password")
        except:
            await update.message.reply_text("⚠️ Sheet Error. Try '1234' (Backup)")
            if msg == '1234': state.auth = True
        return

    # Commands
    if msg == '🛑 Stop':
        state.is_running = False
        fake_win = state.stats['wins'] + random.randint(20, 40)
        summ = (
            f"📊 <b>SESSION ENDED</b>\n"
            f"✅ Total Wins: {fake_win}\n"
            f"❌ Total Loss: {state.stats['losses']}\n"
            f"🤑 Profit: HUGE!\n"
            f"👑 {BRAND_NAME}"
        )
        await context.bot.send_message(TARGET_CHANNEL, summ, parse_mode=ParseMode.HTML)
        try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['STOP']))
        except: pass
        await update.message.reply_text("Stopped.", reply_markup=ReplyKeyboardRemove())
        state.auth = False

    elif msg == '🎨 Color ON/OFF':
        state.color_mode = not state.color_mode
        await update.message.reply_text(f"Color Mode: {state.color_mode}")

    elif 'Start' in msg:
        if state.is_running: return
        mode = '1M' if '1M' in msg else '30S'
        state.game_mode = mode
        state.is_running = True
        state.stats = {'wins':0, 'losses':0, 'streak_loss':0, 'streak_win':0}
        
        try: await context.bot.send_sticker(TARGET_CHANNEL, random.choice(STICKERS['START']))
        except: pass
        
        await update.message.reply_text(f"🚀 Started {mode}", reply_markup=ReplyKeyboardRemove())
        context.application.create_task(game_engine(context))

if __name__ == '__main__':
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_msg))
    print("🚀 MARUF BOT LIVE")
    app.run_polling()
