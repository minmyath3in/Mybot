import os
import threading
import telebot
import yt_dlp
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
    bot.reply_to(message, "မင်္ဂလာပါ! YouTube, TikTok, Facebook လင့်ခ်များ ပို့ပေးပါ မအေဘေးလေးရေ၊ ဗီဒီယိုများ ဒေါင်းလုဒ်လုပ်ပေးပါမည်။")

@bot.message_handler(func=lambda message: True)
def process_link(message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        return

    status_msg = bot.reply_to(message, "⬇️ ဗီဒီယိုကို ရယူနေပါသည်... မအေဘေး ခဏစောင့်ပေးပါ။")

        ydl_opts = {
        'outtmpl': 'downloaded_media.%(ext)s',
        'format': 'best[filesize<50M]/best',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {
            'youtube': {'player_client': ['android', 'ios']}
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as file:
            if info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
                bot.send_photo(message.chat.id, file, reply_to_message_id=message.message_id)
            else:
                bot.send_video(message.chat.id, file, reply_to_message_id=message.message_id)

        if os.path.exists(filename):
            os.remove(filename)

        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ ဒေါင်းလုဒ်လုပ်ရာတွင် အမှားအယွင်းရှိပါသည်: {str(e)}", message.chat.id, status_msg.message_id)

print("Bot is running...")
bot.infinity_polling()
