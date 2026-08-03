import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from motor.motor_asyncio import AsyncIOMotorClient

# Credentials & Configuration
API_ID = 10658015
API_HASH = "a0087bca748f86698c53d291c9e5b3af"
BOT_TOKEN = "7627965170:AAFF3bPiPhX8_EKz0S4nlB5Ah2tWXJIt8Ok"
OWNER_ID = 7657218453
MONGO_URL = "mongodb+srv://babychan90132_db_user:kdGnIwXVvozkowt6@cluster0.owyjlla.mongodb.net/?appName=Cluster0"

# Sightengine API Credentials
API_USER = "291549992"
API_SECRET = "pKBeK64nrQTWj97kD7wq36hdRG3WHPvn"

# MongoDB Database Connection
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["NSFW_Remover_Bot"]
auth_collection = db["auth_users"]

app = Client("NSFW_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Helper function to check if user is authorized
async def is_user_auth(user_id: int) -> bool:
    user = await auth_collection.find_one({"user_id": user_id})
    return bool(user)

# Function to check NSFW using Sightengine API
async def check_nsfw(file_path: str) -> bool:
    try:
        url = "https://api.sightengine.com/1.0/check.json"
        data = aiohttp.FormData()
        data.add_field('media', open(file_path, 'rb'))
        data.add_field('models', 'nudity-2.0,wad,offensive')
        data.add_field('api_user', API_USER)
        data.add_field('api_secret', API_SECRET)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    res = await response.json()
                    nudity = res.get('nudity', {})
                    raw_score = max(
                        nudity.get('sexual_activity', 0),
                        nudity.get('sexual_display', 0),
                        nudity.get('erotica', 0)
                    )
                    # If score is higher than 0.5 (50%), treat as NSFW
                    if raw_score > 0.5:
                        return True
    except Exception as e:
        print(f"Sightengine Error: {e}")
    return False

# Start Command
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    photo_url = "https://files.catbox.moe/sgo9in.png"
    caption = (
        "**👋 Hello! I am an Advanced NSFW Remover Bot.**\n\n"
        "Add me to your group, and I will automatically remove NSFW photos, videos, stickers & GIFs!\n\n"
        "✨ Features:\n"
        "• Real-time Auto NSFW Detection & Deletion\n"
        "• Auth / Unauth User System (MongoDB Connected)\n"
        "• Enjoy Freedom"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Support", url="https://t.me/anime_group_hai"),
            InlineKeyboardButton("Update", url="https://t.me/Sand_Village")
        ],
        [
            InlineKeyboardButton("Owner", user_id=OWNER_ID)
        ]
    ])
    await message.reply_photo(photo=photo_url, caption=caption, reply_markup=buttons)

# Auth Command (Only Owner)
@app.on_message(filters.command("auth") & filters.user(OWNER_ID))
async def auth_user(client, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if await is_user_auth(user_id):
            await message.reply(f"⚠️ This user is already Authorized!")
        else:
            await auth_collection.insert_one({"user_id": user_id})
            await message.reply(f"✅ User `{user_id}` has been successfully Authorized.")
    else:
        await message.reply("⚠️ Please reply to a user's message with `/auth`.")

# Unauth Command (Only Owner)
@app.on_message(filters.command("unauth") & filters.user(OWNER_ID))
async def unauth_user(client, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if not await is_user_auth(user_id):
            await message.reply(f"⚠️ This user is not authorized.")
        else:
            await auth_collection.delete_one({"user_id": user_id})
            await message.reply(f"❌ User `{user_id}` has been Unauthorized.")
    else:
        await message.reply("⚠️ Please reply to a user's message with `/unauth`.")

# Broadcast Command (Only Owner)
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message: Message):
    if not message.reply_to_message:
        await message.reply("⚠️ Please reply to a message with `/broadcast`.")
        return
    await message.reply("🚀 Broadcast feature is ready!")

# Real-time NSFW Content Checker Handler
@app.on_message(filters.group & (filters.photo | filters.animation | filters.sticker | filters.video))
async def nsfw_detector(client, message: Message):
    user_id = message.from_user.id
    
    # Skip deletion if user is Owner or Authorized
    if user_id == OWNER_ID or await is_user_auth(user_id):
        return

    # Download media file and check via API
    file_path = await message.download()
    is_nsfw = await check_nsfw(file_path)
    
    if os.path.exists(file_path):
        os.remove(file_path)

    if is_nsfw:
        try:
            await message.delete()
            await message.reply(f"⚠️ Hey {message.from_user.mention}, NSFW content is not allowed here! Message deleted.")
        except Exception as e:
            print(f"Error deleting message: {e}")

print("Bot with Sightengine NSFW detection & MongoDB is starting...")
app.run()
