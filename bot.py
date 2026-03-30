import json, aiohttp, asyncio
from datetime import datetime
from telegram import *
from telegram.ext import *
from config import *

DB_FILE = "db.json"

# ---------- DB ----------
def load_db():
    try:
        return json.load(open(DB_FILE))
    except:
        return {"users": {}, "referrals": {}}

def save_db(db):
    json.dump(db, open(DB_FILE,"w"), indent=4)

db = load_db()

# ---------- TMDB SEARCH ----------
async def search_tmdb(name, type_="movie"):
    endpoint = "search/tv" if type_=="webseries" else "search/movie"
    url = f"https://api.themoviedb.org/3/{endpoint}?api_key={TMDB_API_KEY}&query={name}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

    results = []
    for m in data.get("results", [])[:5]:
        results.append({
            "id": m["id"],
            "title": m.get("title") or m.get("name"),
            "vote": m.get("vote_average","N/A"),
            "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else POSTER_URL
        })
    return results

# ---------- FORCE JOIN ----------
async def check_join(user_id, context):
    try:
        for ch in CHANNELS:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left","kicked"]:
                return False
        return True
    except:
        return False

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in db["users"]:
        db["users"][user_id] = {
            "coins":2,"bonus":0,"referrals":0,
            "joined":str(datetime.now().date()),
            "referred_by":None
        }

    save_db(db)

    text = f"""╔══════════════════════════════════╗
║ 🎬 C Y N E M A  B O T
╚══════════════════════════════════╝

Hey {update.effective_user.first_name}! 👋

📌 Join channels & Verify 👇
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Verify", callback_data="verify")],
        [InlineKeyboardButton("📺 Channel 1", url=f"https://t.me/{CHANNELS[0][1:]}"),
         InlineKeyboardButton("📺 Channel 2", url=f"https://t.me/{CHANNELS[1][1:]}")]
    ])

    await update.message.reply_photo(POSTER_URL, caption=text, reply_markup=kb)

# ---------- VERIFY ----------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = str(q.from_user.id)

    if not await check_join(user_id, context):
        await q.answer("Join channels first ❌")
        return

    await q.answer("Verified ✅")

    buttons = [
        ["🎬 Movies","🌸 Anime"],
        ["📺 Web Series","👥 Invite"],
        ["📊 Stats","📩 Request"]
    ]

    await q.message.reply_text("Select option 👇", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

# ---------- MENU ----------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    if text == "🎬 Movies":
        context.user_data["mode"] = "movie"
        await update.message.reply_text("Send movie name:")
        return

    if text == "🌸 Anime":
        context.user_data["mode"] = "anime"
        await update.message.reply_text("Send anime name:")
        return

    if text == "📺 Web Series":
        context.user_data["mode"] = "webseries"
        await update.message.reply_text("Send series name:")
        return

    if text == "📩 Request":
        context.user_data["mode"] = "request"
        await update.message.reply_text("Send request name:")
        return

    if text == "📊 Stats":
        u = db["users"][user_id]
        await update.message.reply_text(f"Search: {u['coins']} | Referrals: {u['referrals']}")
        return

    # ---------- SEARCH ----------
    mode = context.user_data.get("mode")

    if mode in ["movie","anime","webseries"]:
        msg = await update.message.reply_text("🔍 Searching...")
        results = await search_tmdb(text, mode)

        if not results:
            await msg.edit_text("No results ❌")
            return

        buttons = []
        for r in results:
            buttons.append([
                InlineKeyboardButton(r['title'], callback_data=f"sel_{mode}_{r['id']}"),
                InlineKeyboardButton("❌", callback_data=f"cancel")
            ])

        await msg.edit_text("Select movie 👇", reply_markup=InlineKeyboardMarkup(buttons))

    # ---------- REQUEST ----------
    if mode == "request":
        await context.bot.send_message(ADMIN_ID, f"Request: {text}")
        await update.message.reply_text("Sent ✅")
        context.user_data.clear()

# ---------- SELECT ----------
async def selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if data == "cancel":
        context.user_data.clear()
        await q.message.delete()
        return

    _, type_, id_ = data.split("_")

    url = f"https://api.themoviedb.org/3/{'tv' if type_=='webseries' else 'movie'}/{id_}?api_key={TMDB_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            m = await r.json()

    title = m.get("title") or m.get("name")
    vote = m.get("vote_average","N/A")
    poster = f"https://image.tmdb.org/t/p/w500{m['poster_path']}"

    watch = f"{VIDLINK_BASE}{id_}"

    await q.message.reply_photo(
        photo=poster,
        caption=f"🎬 {title}\n⭐ {vote}\n\nWatch 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch", url=watch)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
    )

# ---------- MAIN ----------
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # 🔥 FIX ERROR
    await app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(selection_callback, pattern="^(sel_|cancel)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("Bot Running 🚀")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
