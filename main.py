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
    return "Group Guardian Bot is active!"

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

# Load Slang Words
try:
    with open(slangf, 'r') as f:
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

# --- 3. COMMAND HANDLERS ---

@Bot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    # Professional Guardian Image
    welcome_pic = "https://telegra.ph/file/bc0d8e8784d009d7249a2.jpg" 
    
    welcome_text = (
        f"**Greetings {update.from_user.first_name}! 👋**\n\n"
        "I am the **Group Guardian**, your advanced security assistant. "
        "My mission is to keep your groups clean and safe from inappropriate language and NSFW content.\n\n"
        "**💡 Key Features:**\n"
        "🛡️ **Slang Detection:** I instantly detect and remove messages containing vulgar language.\n"
        "🔞 **NSFW Filter:** Every photo is scanned. Adult or pornographic images are removed immediately.\n"
        "👮‍♂️ **Admin Immunity:** Administrators are exempt from these filters.\n\n"
        "**How to Use?**\n"
        "Add me to your group and grant me **Admin Rights** to start protecting your community!"
    )

    buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/Yonko_Crew"),
                InlineKeyboardButton("👥 Group", url="https://t.me/SENPAI_GC")
            ],
            [
                InlineKeyboardButton("🆘 Help", callback_data="help_cmds"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/GOJO63970")
            ]
        ])

    try:
        await update.reply_photo(
            photo=welcome_pic,
            caption=welcome_text,
            reply_markup=buttons
        )
    except Exception:
        # Fallback to text if image fails
        await update.reply_text(
            text=welcome_text,
            reply_markup=buttons
        )

@Bot.on_callback_query(filters.regex("help_cmds"))
async def help_callback(bot, query):
    help_text = (
        "**📜 User Manual & Commands:**\n\n"
        "• `/start` - Initialize the bot.\n"
        "• Simply add the bot to your group and promote it to Admin.\n"
        "• The bot will automatically monitor all text and media.\n\n"
        "**Note:** Admin messages are never deleted or censored."
    )
    await query.message.edit_caption(
        caption=help_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_start")]])
    )

@Bot.on_callback_query(filters.regex("back_start"))
async def back_callback(bot, query):
    await query.message.delete()
    await start(bot, query.message)

# --- 4. IMAGE & TEXT FILTERS ---

@Bot.on_message(filters.group & filters.photo)
async def image(bot, message):
    try:
        sender = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if sender.privileges: 
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
                    caption=f"⚠️ **NSFW Alert!**\n\nUser **{name}** sent an inappropriate image.\n**Porn Score:** {porn}%", 
                    has_spoiler=True
                )
        if os.path.exists(x):
            os.remove(x) 
    except Exception as e:
        print(f"Image filtering error: {e}")

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
            msgtxt = f"🚫 **Bad Language Detected!**\n\n{name}, your message was deleted for containing prohibited words.\n\n**Censored:** {sentence}"
            if SPOILER:
                await message.reply(msgtxt)
    except Exception as e:
        print(f"Text filtering error: {e}")

# --- 5. EXECUTION ---
if __name__ == "__main__":
    keep_alive() 
    print("Group Guardian Bot is starting...")
    Bot.run()
                
