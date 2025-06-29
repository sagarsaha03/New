import json
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# --- Config ---
API_ID = 29691930
API_HASH = "d4fee910d5eac3e9c99889e434ffec77"
SESSION = "1BVtsOIABu8SPnjIHHtlArUqI3N5qN_3HuXYEaGDf_n2eHfHKzZOh4uke9N2lY0HV2VxSarMDbvOGvfAhuUk1xuUniM3bT3Ydp37oLDoFdxkmqPJcZGeJkw0FcAE1ULJPQfaUeBua1HuqVZVeGBAf-N9dABQO3CK_M__vxYeQARx9p6Fi9mYz_uZaD8mIttGYBbKcXNaEHNA3SOqZ4r8320l5Nfx66PnhL_QkzTOxBTF-1aHBWsEMTXavsUEDgNbuB-whO0hsxOoGS4IU0C1mDC6A7a-jNXXW5Ly3G2IBiKEpkwO_MrnG5EHJSW7JYhcjXBNMq2uP3J87CxTTzT-bP4dkppMTgCk="
BOT_TOKEN = "7660400157:AAFPrl7zZiz1I41qomJDO-uoN8jVzKi-_80"
DB_FILE = "db.json"
ADMIN_ID = 1588777572

DB_CHANNEL = None
DB_CHANNEL_USERNAME = None

# --- DB Functions ---
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def smart_match(title, query):
    pattern = r'\b' + re.escape(query.lower()) + r'\b'
    return re.search(pattern, title.lower()) or title.lower().startswith(query.lower())

# --- Bot Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send a movie or series name to search!")

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DB_CHANNEL, DB_CHANNEL_USERNAME
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 You're not allowed.")

    if update.message.forward_from_chat:
        chat = update.message.forward_from_chat
        DB_CHANNEL = chat.id
        DB_CHANNEL_USERNAME = chat.username if chat.username else None
        name = f"@{DB_CHANNEL_USERNAME}" if DB_CHANNEL_USERNAME else DB_CHANNEL
        await update.message.reply_text(f"✅ DB channel set: `{name}`", parse_mode="Markdown")
    elif context.args:
        try:
            DB_CHANNEL = int(context.args[0])
            DB_CHANNEL_USERNAME = None
            await update.message.reply_text(f"✅ DB channel manually set: `{DB_CHANNEL}`", parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Invalid channel ID format.")
    else:
        await update.message.reply_text("❗ Please forward a post or use `/setdb <channel_id>`")

async def update_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 You're not allowed.")
    if not DB_CHANNEL:
        return await update.message.reply_text("❗ DB channel not set.")

    await update.message.reply_text("⏳ Updating database...")
    await fetch_posts()
    await update.message.reply_text("✅ Database updated!")

# --- Search Handler ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not DB_CHANNEL:
        return await update.message.reply_text("❗ DB channel not set.")

    db = load_db()
    filtered = [item for item in db if smart_match(item["title"], query)]

    if not filtered:
        return await update.message.reply_text("❌ No results found.")

    user_name = update.effective_user.first_name
    msg = f"👤 {user_name}\n🔎 {query}\n\n"
    msg += "<b><i>📡 Powered by @Sseries_Area</i></b>\n\n"
    msg += "<b><i>📥 Here are the results 👇</i></b>\n\n"

    for r in filtered[:10]:
        title = r['title'].splitlines()[0].strip()
        link = (
            f"https://t.me/{DB_CHANNEL_USERNAME}/{r['id']}"
            if DB_CHANNEL_USERNAME else
            f"https://t.me/c/{str(DB_CHANNEL)[4:]}/{r['id']}"
        )
        msg += f"<b><i>♻️ {title}</i></b>\n🔗 {link}\n\n"

    sent_msg = await update.message.reply_html(msg, disable_web_page_preview=True)

    async def delete_later(m=sent_msg):
        try:
            await asyncio.sleep(590)
            await m.edit_text("⚠️ Auto-deleting in 10 seconds...")
            await asyncio.sleep(10)
            await m.delete()
        except Exception as e:
            print(f"Delete error: {e}")

    asyncio.create_task(delete_later())

# --- Fetch Posts with Telethon ---
async def fetch_posts():
    global DB_CHANNEL_USERNAME
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()

    entity = await client.get_entity(DB_CHANNEL)
    DB_CHANNEL_USERNAME = getattr(entity, "username", None)

    posts = []
    async for msg in client.iter_messages(DB_CHANNEL, reverse=True):
        if msg.message:
            title = msg.message.strip()
            posts.append({"id": msg.id, "title": title})

    save_db(posts)
    await client.disconnect()

# --- Run Bot ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setdb", set_channel))
    app.add_handler(CommandHandler("update", update_db))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
