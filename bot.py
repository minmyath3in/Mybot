import os
import threading
import telebot
import yt_dlp
import urllib.request
import json
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
    bot.reply_to(message, "မင်္ဂလာပါ! YouTube, TikTok, Facebook လင့်ခ်များ ပို့ပေးပါ၊ မီဒီယာ ဒေါင်းလုဒ်လုပ်ပေးပါမည်။")

@bot.message_handler(func=lambda message: True)
def process_link(message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        return

    status_msg = bot.reply_to(message, "⬇️ မီဒီယာကို ရယူနေပါသည်... ခဏစောင့်ပေးပါ။")

    # 1. TikTok လင့်ခ်ဖြစ်ပါက TikWM API အသုံးပြုမည်
    if "tiktok.com" in url or "douyin.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode())
                if data.get('code') == 0:
                    video_url = data['data']['play']
                    filename = "tiktok_video.mp4"
                    urllib.request.urlretrieve(video_url, filename)
                    with open(filename, 'rb') as file:
                        bot.send_video(message.chat.id, file, reply_to_message_id=message.message_id)
                    if os.path.exists(filename):
                        os.remove(filename)
                    bot.delete_message(message.chat.id, status_msg.message_id)
                    return
        except Exception as e:
            print(f"TikTok API error: {e}")

    # 2. YouTube လင့်ခ်ဖြစ်ပါက Cobalt API ဖြင့် Render IP Block ကျော်လွှားမည်
    if "youtube.com" in url or "youtu.be" in url:
        try:
            cobalt_apis = [
                "https://api.cobalt.tools",
                "https://co.wuk.sh",
                "https://cobalt.api.scip.be"
            ]
            req_data = json.dumps({"url": url, "videoQuality": "720"}).encode('utf-8')
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            
            for api in cobalt_apis:
                try:
                    req = urllib.request.Request(api, data=req_data, headers=headers, method='POST')
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        res_json = json.loads(resp.read().decode('utf-8'))
                        download_url = res_json.get('url')
                        if download_url:
                            filename = "youtube_video.mp4"
                            dl_req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(dl_req, timeout=60) as v_resp, open(filename, 'wb') as f:
                                f.write(v_resp.read())
                            
                            with open(filename, 'rb') as file:
                                bot.send_video(message.chat.id, file, reply_to_message_id=message.message_id)
                            
                            if os.path.exists(filename):
                                os.remove(filename)
                            bot.delete_message(message.chat.id, status_msg.message_id)
                            return
                except Exception as inner_e:
                    print(f"Cobalt instance {api} error: {inner_e}")
                    continue
        except Exception as e:
            print(f"YouTube Cobalt error: {e}")

    # 3. Facebook နှင့် အခြားလင့်ခ်များအတွက် yt-dlp အသုံးပြုမည်
    ydl_opts = {
        'outtmpl': 'downloaded_media.%(ext)s',
        'format': 'best[filesize<50M]/best',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
