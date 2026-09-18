import os
import re
import logging
import asyncio
import requests
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token (Render Environment Variable မှ ယူမည်)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! TikTok, YouTube, Facebook, Instagram သို့မဟုတ် Twitter ဗီဒီယို Link ကို ပို့ပေးပါ၊ ဗီဒီယို ဒေါင်းလုဒ်ဆွဲပေးပါမည်။"
    )


def download_tiktok_tikwm(url):
    """TikWM API သုံးပြီး TikTok Video ဒေါင်းလုဒ်ဆွဲခြင်း"""
    api_url = "https://www.tikwm.com/api/"
    params = {"url": url, "hd": 1}
    response = requests.get(api_url, params=params, timeout=15)
    data = response.json()

    if data.get("code") == 0:
        video_data = data.get("data", {})
        play_url = video_data.get("hdplay") or video_data.get("play")
        title = video_data.get("title", "TikTok Video")
        if play_url:
            res = requests.get(play_url, timeout=30)
            file_path = "tiktok_video.mp4"
            with open(file_path, "wb") as f:
                f.write(res.content)
            return file_path, title
    return None, None


async def download_cobalt_api(url):
    """Cobalt Free Public API များသုံးပြီး YouTube Video ဒေါင်းလုဒ်ဆွဲခြင်း (Render IP Block ကျော်ရန်)"""
    instances = [
        "https://api.cobalt.tools",
        "https://co.wuk.sh",
        "https://cobalt.api.scip.be"
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "videoQuality": "720"
    }

    async with aiohttp.ClientSession() as session:
        for instance in instances:
            try:
                async with session.post(instance, json=payload, headers=headers, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        download_url = data.get("url")
                        if download_url:
                            # Direct Video File ကို ဒေါင်းယူမည်
                            async with session.get(download_url, timeout=60) as vid_resp:
                                if vid_resp.status == 200:
                                    file_path = "yt_video.mp4"
                                    with open(file_path, "wb") as f:
                                        f.write(await vid_resp.read())
                                    return file_path, "YouTube Video"
            except Exception as e:
                logger.warning(f"Cobalt instance {instance} failed: {e}")
                continue
    return None, None


def download_ytdlp_youtube(url):
    """yt-dlp သုံးပြီး YouTube Video ဒေါင်းလုဒ်ဆွဲခြင်း (Mobile Client Arguments ဖြင့် Server IP Block ကျော်ရန်)"""
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": "ytdlp_video.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        # Server/Datacenter IP Block မထိအောင် Mobile/iOS Client အနေဖြင့် တောင်းဆိုခြင်း
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "mweb", "android", "web_creator"]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        title = info.get("title", "YouTube Video")
        return filename, title


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Link ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("ကျေးဇူးပြု၍ တရားဝင် Video Link တစ်ခု ပို့ပေးပါ။")
        return

    msg = await update.message.reply_text("⏳ ဗီဒီယို ရယူနေပါသည်... ကျေးဇူးပြု၍ ခဏစောင့်ပါ။")

    file_path = None
    title = None

    try:
        # ၁။ TikTok Link ဖြစ်ပါက TikWM API သုံးမည်
        if "tiktok.com" in url or "douyin.com" in url:
            file_path, title = download_tiktok_tikwm(url)

        # ၂။ YouTube Link ဖြစ်ပါက
        elif "youtube.com" in url or "youtu.be" in url:
            # ပထမနည်း- yt-dlp (iOS/Mobile client) ဖြင့် စမ်းမည်
            try:
                loop = asyncio.get_event_loop()
                file_path, title = await loop.run_in_executor(None, download_ytdlp_youtube, url)
            except Exception as e:
                logger.error(f"yt-dlp failed: {e}")

            # ဒုတိယနည်း- Render IP Block မိပါက Cobalt API ဖြင့် အလိုအလျောက် ပြောင်းဒေါင်းမည်
            if not file_path or not os.path.exists(file_path):
                file_path, title = await download_cobalt_api(url)

        # ၃။ အခြား Platform များအတွက် (Instagram, Facebook, etc.)
        else:
            file_path, title = await download_cobalt_api(url)
            if not file_path:
                try:
                    loop = asyncio.get_event_loop()
                    file_path, title = await loop.run_in_executor(None, download_ytdlp_youtube, url)
                except Exception as e:
                    logger.error(f"Fallback download failed: {e}")

        # ဗီဒီယို ပို့ပေးခြင်း
        if file_path and os.path.exists(file_path):
            await msg.edit_text("⬆️ Telegram သို့ တင်ပေးနေပါသည်...")
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"🎬 {title}\n\nDownloaded by Bot"
                )
            await msg.delete()

            # Server နေရာအလွတ် ရရှိစေရန် ဒေါင်းလုဒ်ဆွဲထားသော File ကို ပြန်ဖျက်မည်
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            await msg.edit_text("❌ ဗီဒီယို ဒေါင်းလုဒ်ဆွဲ၍ မရပါ။ Link မှန်ကန်မှု ရှိ/မရှိ သို့မဟုတ် မူရင်း Video ကို ဖျက်ထားခြင်း ရှိ/မရှိ စစ်ဆေးပါ။")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await msg.edit_text(f"❌ အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်: {str(e)}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


def main():
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN Environment Variable ကို သတ်မှတ်ထားခြင်း မရှိပါ။")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

