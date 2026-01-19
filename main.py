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
    t = Thread(target=run_flask).start()

# --- 2. BOT INITIALIZATION ---
url = "https://api.safone.me/nsfw"
slangf = 'slang_words.txt'

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
    welcome_text = f"**Greetings {update.from_user.first_name}! 👋**\n\nI am the **Group Guardian**."
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")]])
    await update.reply_text(text=welcome_text, reply_markup=buttons)

# --- 5. THE FINAL EDIT FIX (REACTION PROOF) ---
@Bot.on_edited_message(filters.group)
async def handle_edited(bot, message):
    # Condition 1: Agar message ke paas text nahi hai (Media/Reaction), ignore karo
    if not message.text and not message.caption:
        return

    # Condition 2: Telegram API verification. 
    # Reaction aane par 'edit_date' ya toh update nahi hota, ya purane ke barabar hota hai.
    if message.edit_date and message.date:
        if (message.edit_date - message.date).total_seconds() < 2:
            return # Ye reaction hai, edit nahi.

    try:
        await message.delete()
        reply = await message.reply(
            f"Security Bot 📢\n"
            f"🚫 Hey {message.from_user.mention}, editing is not allowed!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me", url="https://t.me/Yonko_Crew")]])
        )
        asyncio.create_task(auto_delete(reply))
    except:
        pass

# --- 6. MAIN SLANG & PHOTO FILTER ---
@Bot.on_message(filters.group & (filters.text | filters.photo))
async def main_filter(bot, message):
    # Slang Filter
    if message.text and not message.text.startswith("/"):
        clean_text = re.sub(r'[^\w\s]', ' ', message.text).lower()
        if any(word in slang_words for word in clean_text.split()):
            await message.delete()
            reply = await message.reply(f"Security Bot 📢\n🚫 Bad Language Detected!")
            asyncio.create_task(auto_delete(reply))
            
    # NSFW Filter
    elif message.photo:
        try:
            path = await message.download()
            with open(path, "rb") as f:
                res = requests.post(url, files={"image": f}).json()
                if res.get("data", {}).get("is_nsfw", False):
                    await message.delete()
            os.remove(path)
        except: pass

if __name__ == "__main__":
    keep_alive()
    Bot.run()
    
