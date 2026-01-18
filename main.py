from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import re
import config 
import os
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER FOR RENDER (KEEP ALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Group Guardian Bot is running!"

def run_flask():
    # Render automatically sets the PORT
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

# Slang words file read karna
try:
    with open(slangf, 'r') as f:
        slang_words = set(line.strip().lower() for line in f)
except FileNotFoundError:
    slang_words = set()
    print("Warning: slang_words.txt file nahi mili!")

Bot = Client(
    "antinude",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# --- 3. COMMAND HANDLERS ---

@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    # Professional Guardian Bot Image
    welcome_pic = "https://graph.org/file/e642337d10e5446078e63.jpg" 
    
    welcome_text = (
        f"**Namaste {update.from_user.first_name}! 👋**\n\n"
        "Main hoon **Group Guardian**, aapke group ka digital chowkidar. "
        "Mera kaam aapke group ko gande words aur NSFW (adult) content se saaf rakhna hai.\n\n"
        "**💡 Main kya kar sakta hoon?**\n"
        "🛡️ **Slang Detection:** Inappropriate language ko turant delete karta hoon.\n"
        "🔞 **NSFW Filter:** Har photo ko scan karke adult content hata deta hoon.\n"
        "👮‍♂️ **Admin Safe:** Admins par mera koi asar nahi hota.\n\n"
        "**Kaise use karein?**\n"
        "Muze apne group mein add karein aur **Admin** banayein!"
    )

    await update.reply_photo(
        photo=welcome_pic,
        caption=welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew"),
                InlineKeyboardButton("👥 Group", url="https://t.me/SENPAI_GC")
            ],
            [
                InlineKeyboardButton("🆘 Help", callback_data="help_cmds"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/GOJO63970")
            ]
        ])
    )

@Bot.on_callback_query(filters.regex("help_cmds"))
async def help_callback(bot, query):
    help_text = (
        "**📜 All Commands & Usage:**\n\n"
        "• `/start` - Bot ko start karne ke liye.\n"
        "• Bas bot ko group mein add karein aur admin banayein.\n"
        "• Bot automatically saare photos aur texts scan karega.\n\n"
        "Note: Admin ke messages filter nahi hote."
    )
    await query.message.edit_caption(
        caption=help_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_start")]])
    )

@Bot.on_callback_query(filters.regex("back_start"))
async def back_callback(bot, query):
    # Wapas original message par jaane ke liye
    await start(bot, query.message)
    await query.message.delete()

# --- 4. IMAGE & TEXT FILTERS ---

@Bot.on_message(filters.group & filters.photo)
async def image(bot, message):
    try:
        sender = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if sender.privileges: # Admin check
            return
            
        x = await message.download()
        with open(x, "rb") as photo_file:
            files = {"image": photo_file}
            roi = requests.post(url, files=files)
            data = roi.json()
            
        nsfw = data.get("data", {}).get("is_nsfw", False)
        porn = data.get("data", {}).get("porn", 0)
        
        if nsfw:
            name = message.from_user.first_name
            await message.delete()
            if SPOILER:
                await message.reply_photo(
                    x, 
                    caption=f"⚠️ **NSFW Alert!**\n\nUser **{name}** ne ek nude photo bheji thi.\n**Porn Score:** {porn}%", 
                    has_spoiler=True
                )
        os.remove(x) # Clean up downloaded file
    except Exception as e:
        print(f"Error in image filter: {e}")

@Bot.on_message(filters.group & filters.text)
async def slang(bot, message):
    try:
        sender = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if sender.privileges:
            return

        sentence = message.text
        sent = re.sub(r'\W+', ' ', sentence)
        isslang = False
        words = sent.split()
        
        for word in words:
            if word.lower() in slang_words:
                isslang = True
                sentence = sentence.replace(word, f"||{word}||")
        
        if isslang:
            name = message.from_user.first_name
            await message.delete()
            msgtxt = f"🚫 **Bad Language Detected!**\n\n{name}, aapke message mein galat shabd the.\n\n**Censored:** {sentence}"
            if SPOILER:
                await message.reply(msgtxt)
    except Exception as e:
        print(f"Error in slang filter: {e}")

# --- 5. RUN BOT ---
if __name__ == "__main__":
    keep_alive() # Starts Flask server in background
    print("Bot is starting...")
    Bot.run()
    
