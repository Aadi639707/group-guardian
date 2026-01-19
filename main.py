from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re
import config 
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is active!"

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

# Memory Cache for Reaction Protection
msg_text_cache = {}

try:
    with open(slangf, 'r', encoding='utf-8') as f:
        slang_words = set(line.strip().lower() for line in f)
except FileNotFoundError:
    slang_words = set()

Bot = Client(
    "antinude",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# --- 3. AUTO-DELETE HELPER ---
async def auto_delete(message, delay=60):
    await asyncio.sleep(delay)
    try: await message.delete()
    except: pass

# --- 4. START COMMAND ---
@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    welcome_pic = "https://telegra.ph/file/bc0d8e8784d009d7249a2.jpg"
    welcome_text = (
        f"**Greetings {update.from_user.first_name}! 👋**\n\n"
        "I am the **Group Guardian**. I protect your community from NSFW, Slang, and Edits.\n\n"
        "**Note:** Admin messages are also monitored as per your request."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true"),
         InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew")]
    ])
    try: await update.reply_photo(photo=welcome_pic, caption=welcome_text, reply_markup=buttons)
    except: await update.reply_text(text=welcome_text, reply_markup=buttons)

# --- 5. EDIT TRACKER (100% REACTION PROOF) ---
@Bot.on_edited_message(filters.group)
async def handle_edited(bot, message):
    msg_id = message.id
    new_content = message.text or message.caption

    # Agar reaction aaya hai toh text cache mein match karega
    if msg_id in msg_text_cache and msg_text_cache[msg_id] == new_content:
        return # Sirf reaction hai, ignore it

    try:
        await message.delete()
        reply = await message.reply(
            f"Security Bot 📢\n"
            f"🚫 Hey {message.from_user.mention}, your message was removed.\n\n"
            f"**Reason:** Edited message detected.\n"
            f"Please keep the chat respectful.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")]
            ])
        )
        asyncio.create_task(auto_delete(reply))
    except: pass

# --- 6. MULTILINGUAL SLANG & PHOTO FILTER ---
@Bot.on_message(filters.group & (filters.text | filters.photo))
async def main_filter(bot, message):
    # Store message content in cache for reaction check later
    msg_text_cache[message.id] = message.text or message.caption
    
    # 1. PHOTO/NSFW FILTER
    if message.photo:
        try:
            x = await message.download()
            with open(x, "rb") as photo_file:
                roi = requests.post(url, files={"image": photo_file})
                if roi.json().get("data", {}).get("is_nsfw", False):
                    await message.delete()
                    reply = await message.reply(f"Security Bot 📢\n🚫 Hey {message.from_user.mention}, NSFW is not allowed.")
                    asyncio.create_task(auto_delete(reply))
            if os.path.exists(x): os.remove(x)
        except: pass

    # 2. SLANG FILTER
    elif message.text and not message.text.startswith("/"):
        try:
            sentence = message.text
            clean_text = re.sub(r'[^\w\s]', ' ', sentence).lower()
            words = clean_text.split()
            if any(word in slang_words for word in words):
                await message.delete()
                reply = await message.reply(f"Security Bot 📢\n🚫 Hey {message.from_user.mention}, bad language detected.")
                asyncio.create_task(auto_delete(reply))
        except: pass

# --- 7. RUN ---
if __name__ == "__main__":
    keep_alive()
    Bot.run()
    
