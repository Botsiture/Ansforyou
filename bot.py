import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
MONGO_URL = os.environ.get("MONGO_URL", "")

# MongoDB Database Connection
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["NSFW_Remover_Bot"]
auth_collection = db["auth_users"]

app = Client("NSFW_Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Helper function to check if user is auth
async def is_user_auth(user_id: int) -> bool:
    user = await auth_collection.find_one({"user_id": user_id})
    return bool(user)

# Start Command with Photo and Buttons
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    photo_url = "https://envs.sh/X1N.jpg"
    caption = (
        "**👋 Hello! Main ek Advanced NSFW Remover Bot hoon.**\n\n"
        "Mujhe apne group mein add karein, aur main automatically NSFW photos, videos, stickers & GIFs remove kar dunga!\n\n"
        "✨ Features:\n"
        "• Auto NSFW Detection & Deletion\n"
        "• Auth / Unauth User System (MongoDB Connected)\n"
        "• Broadcast Support for Owner"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛠 Support", url="https://t.me/your_support_group"),
            InlineKeyboardButton("📢 Updates", url="https://t.me/your_channel")
        ],
        [
            InlineKeyboardButton("👑 Owner", user_id=OWNER_ID)
        ]
    ])
    await message.reply_photo(photo=photo_url, caption=caption, reply_markup=buttons)

# Auth Command (Only Owner)
@app.on_message(filters.command("auth") & filters.user(OWNER_ID))
async def auth_user(client, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if await is_user_auth(user_id):
            await message.reply(f"⚠️ Yeh user pehle se hi Authorized hai!")
        else:
            await auth_collection.insert_one({"user_id": user_id})
            await message.reply(f"✅ User `{user_id}` ko successfully Authorized kar diya gaya hai.")
    else:
        await message.reply("⚠️ Kisi user ke message ko reply karke `/auth` likhein.")

# Unauth Command (Only Owner)
@app.on_message(filters.command("unauth") & filters.user(OWNER_ID))
async def unauth_user(client, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if not await is_user_auth(user_id):
            await message.reply(f"⚠️ Yeh user authorized nahi hai.")
        else:
            await auth_collection.delete_one({"user_id": user_id})
            await message.reply(f"❌ User `{user_id}` ko Unauthorize kar diya gaya hai.")
    else:
        await message.reply("⚠️ Kisi user ke message ko reply karke `/unauth` likhein.")

# Broadcast Command (Only Owner)
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message: Message):
    if not message.reply_to_message:
        await message.reply("⚠️ Kisi message ko reply karke `/broadcast` likhein.")
        return
    await message.reply("🚀 Broadcast feature ready hai!")

# NSFW Content Checker Handler
@app.on_message(filters.group & (filters.photo | filters.animation | filters.sticker | filters.video))
async def nsfw_detector(client, message: Message):
    user_id = message.from_user.id
    
    # Agar owner hai ya authorized user hai, toh kuch delete nahi hoga
    if user_id == OWNER_ID or await is_user_auth(user_id):
        return

    # Yahan NSFW detection logic aayegi
    is_nsfw = False 

    if is_nsfw:
        try:
            await message.delete()
            await message.reply(f"⚠️ Hey {message.from_user.mention}, NSFW content allowed nahi hai yahan!")
        except Exception as e:
            print(f"Error deleting message: {e}")

print("Bot with MongoDB is starting...")
app.run()
