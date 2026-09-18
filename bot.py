import os
import threading
import telebot
import yt_dlp
import requests
from flask import Flask

# Web Server Setup
app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# Telegram Bot Setup
BOT_TOKEN = "8327092903:AAEy1qO1_zXNLVQbzQ0y6PVz8jdLBP6p-Ss"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "မင်္ဂလာပါ! TikTok, YouTube, Facebook လင့်ခ်များ ပို့ပေးပါ၊ မီဒီယာ ဒေါင်းလုဒ်လုပ်ပေးပါမည်။")

@bot.message_handler(func=lambda message: True)
def process_link(message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        return

    status_msg = bot.reply_to(message, "⬇️ မီဒီယာကို ရယူနေပါသည်... ခဏစောင့်ပေးပါ။")
    filename = "downloaded_media.mp4"

    # 1. TikTok ဒေါင်းလုဒ်ဆွဲခြင်း (ကြော်ငြာ စစ်ထုတ်ထားသည်)
    if "tiktok.com" in url or "douyin.com" in url:
        try:
            api_res = requests.get(f"https://www.tikwm.com/api/?url={url}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
            if api_res.get('code') == 0 and 'data' in api_res and 'play' in api_res['data']:
                video_url = api_res['data']['play']
                video_bytes = requests.get(video_url, timeout=30).content
                with open(filename, 'wb') as f:
                    f.write(video_bytes)
                
                with open(filename, 'rb') as f:
                    bot.send_video(message.chat.id, f, reply_to_message_id=message.message_id)
                
                if os.path.exists(filename):
                    os.remove(filename)
                bot.delete_message(message.chat.id, status_msg.message_id)
                return
        except Exception:
            pass

    # 2. YouTube / Facebook / အခြား လင့်ခ်များ ဒေါင်းလုဒ်ဆွဲခြင်း
    ydl_opts = {
        'outtmpl': filename,
        'format': 'best[filesize<50M]/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {
            'youtube': {'player_client': ['android', 'ios']}
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                bot.send_video(message.chat.id, f, reply_to_message_id=message.message_id)
            os.remove(filename)
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ မီဒီယာ ဒေါင်းလုဒ်လုပ်၍ မရပါ၊ လင့်ခ်ကို ပြန်စစ်ပေးပါ။", message.chat.id, status_msg.message_id)

    except Exception:
        bot.edit_message_text("❌ မီဒီယာ ရယူရာတွင် အမှားအယွင်း ရှိနေပါသည်။ ခဏစောင့်ပြီး ပြန်စမ်းပါ။", message.chat.id, status_msg.message_id)

print("Bot is running...")
bot.infinity_polling()

