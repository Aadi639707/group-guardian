from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re
import config 
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER FOR RENDER (KEEP ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Group Guardian Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- 2. BOT INITIALIZATION ---
url = "https://api.safone.me/nsfw"
SPOILER = config.SPOILER_MODE
slangf = 'slang_words.txt'

try:
    with open(slangf, 'r', encoding='utf-8') as f:
        slang_words = set(line.strip().lower() for line in f)
except FileNotFoundError:
    slang_words = set()
    print("Warning: slang_words.txt not found!")

Bot = Client(
    "antinude",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# --- 3. AUTO-DELETE HELPER ---
async def auto_delete(message, delay=60):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# --- 4. START COMMAND ---
@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    welcome_pic = "https://telegra.ph/file/bc0d8e8784d009d7249a2.jpg" 
    welcome_text = (
        f"**Greetings {update.from_user.first_name}! 👋**\n\n"
        "I am the **Group Guardian**. I protect your community from NSFW content, "
        "multilingual abusive language, and edited messages.\n\n"
        "**💡 Features:**\n"
        "🛡️ **Slang & NSFW Filter:** High-speed detection.\n"
        "🚫 **Edit Policy:** Edited messages are strictly prohibited.\n"
        "⏳ **Auto-Clean:** Notifications self-destruct in 60 seconds."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"),
         InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew")],
        [InlineKeyboardButton("🆘 Help", callback_data="help_cmds"),
         InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/GOJO63970")]
    ])
    try:
        await update.reply_photo(photo=welcome_pic, caption=welcome_text, reply_markup=buttons)
    except:
        await update.reply_text(text=welcome_text, reply_markup=buttons)

# --- 5. EDIT TRACKER (FIXED: IGNORES REACTIONS) ---
@Bot.on_edited_message(filters.group)
async def handle_edited(bot, message):
    # Fix: Reaction triggers an edit event, but the 'text' doesn't exist in reaction updates
    # We only delete if there is actually text/caption being edited.
    if not message.text and not message.caption:
        return

    try:
        await message.delete()
        reply = await message.reply(
            f"Security Bot 📢\n"
            f"🚫 Hey {message.from_user.mention}, your message was removed.\n\n"
            f"**Reason:** Edited message detected.\n"
            f"Please keep the chat respectful.\n\n"
            f"Note: This alert will delete in 60s.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"),
                 InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew")]
            ])
        )
        asyncio.create_task(auto_delete(reply))
    except:
        pass

# --- 6. MULTILINGUAL SLANG & IMAGE FILTERS ---
@Bot.on_message(filters.group & filters.photo)
async def image(bot, message):
    try:
        x = await message.download()
        with open(x, "rb") as photo_file:
            files = {"image": photo_file}
            roi = requests.post(url, files=files)
            data = roi.json()
            
        nsfw = data.get("data", {}).get("is_nsfw", False)
        if nsfw:
            await message.delete()
            reply = await message.reply(
                f"Security Bot 📢\n"
                f"🚫 Hey {message.from_user.mention}, your message was removed.\n\n"
                f"**Reason:** NSFW Content Detected.\n"
                f"Please keep the chat respectful.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"),
                     InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew")]
                ])
            )
            asyncio.create_task(auto_delete(reply))
        if os.path.exists(x):
            os.remove(x) 
    except:
        pass

@Bot.on_message(filters.group & filters.text)
async def slang(bot, message):
    if message.text.startswith("/"):
        return
        
    try:
        sentence = message.text
        clean_text = re.sub(r'[^\w\s]', ' ', sentence).lower()
        isslang = False
        words = clean_text.split()
        
        for word in words:
            if word in slang_words:
                isslang = True
                sentence = re.compile(re.escape(word), re.IGNORECASE).sub("****", sentence)
        
        if isslang:
            await message.delete()
            reply = await message.reply(
                f"Security Bot 📢\n"
                f"🚫 Hey {message.from_user.mention}, your message was removed.\n\n"
                f"🔍 **Censored:** {sentence}\n\n"
                f"Please keep the chat respectful.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"),
                     InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew")]
                ])
            )
            asyncio.create_task(auto_delete(reply))
    except:
        pass

# --- 7. RUN ---
if __name__ == "__main__":
    keep_alive()
    print("Group Guardian Bot is starting...")
    Bot.run()
    
