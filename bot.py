import json, aiohttp, datetime
from telegram import *
from telegram.ext import *
from config import *

DB_FILE = "db.json"

# ---------- DB ----------
def load():
    try:
        return json.load(open(DB_FILE))
    except:
        return {}

def save(db):
    json.dump(db, open(DB_FILE, "w"), indent=4)

db = load()

def user_init(uid, name):
    if uid not in db:
        db[uid] = {
            "name": name,
            "referrals": 0,
            "invited": [],
            "searches": START_SEARCHES,
            "bonus": 0,
            "joined": str(datetime.date.today())
        }
        save(db)

# ---------- FORCE JOIN CHECK ----------
async def check_join(bot, user_id):
    try:
        for ch in FORCE_CHANNELS:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except:
        return False

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    name = update.effective_user.first_name
    user_init(user, name)

    if not await check_join(context.bot, user):
        buttons = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNELS[0].replace('@','')}")],
                   [InlineKeyboardButton("✅ Verify", callback_data="verify")]]
        await update.message.reply_text("❗ Join channel first", reply_markup=InlineKeyboardMarkup(buttons))
        return

    text = f"""
╔══════════════════════════════════╗
║ 🎬  C Y N E M A
╚══════════════════════════════════╝

Hey {name}! 👋

🎬 Movies | 🌸 Anime | 📺 Series  

👇 Select option:
"""

    kb = [
        [InlineKeyboardButton("🎬 Movies", callback_data="movies")],
        [InlineKeyboardButton("📩 Request", callback_data="request")],
        [InlineKeyboardButton("👥 Invite", callback_data="invite")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


# ---------- SEARCH ----------
async def search_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
    return data.get("results", [])


# ---------- BUTTONS ----------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = str(q.from_user.id)

    if q.data == "verify":
        if await check_join(context.bot, user):
            await q.message.delete()
            await start(update, context)
        else:
            await q.answer("Join first!", show_alert=True)

    elif q.data == "movies":
        context.user_data["mode"] = "search"
        await q.message.reply_text("🎬 Send movie name:")

    elif q.data == "request":
        context.user_data["mode"] = "request"
        await q.message.reply_text("📩 Send movie name to request:")

    elif q.data == "invite":
        link = f"https://t.me/YOUR_BOT_USERNAME?start=ref_{user}"
        await q.message.reply_text(f"🔗 {link}")

    elif q.data == "stats":
        u = db[user]
        await q.message.reply_text(f"👤 {u['name']}\n🔍 {u['searches']+u['bonus']} searches\n👥 {u['referrals']} referrals")

    elif q.data == "cancel":
        context.user_data.clear()
        await q.message.delete()


# ---------- MESSAGE ----------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    text = update.message.text

    mode = context.user_data.get("mode")

    # REQUEST MODE
    if mode == "request":
        await context.bot.send_message(ADMIN_ID, f"📩 Request: {text}\nUser: {user}")
        await update.message.reply_text("✅ Request sent to admin")
        context.user_data.clear()
        return

    # SEARCH MODE
    if mode == "search":
        msg = await update.message.reply_text("🔍 Searching...")

        results = await search_tmdb(text)

        if not results:
            await msg.edit_text("❌ No results found!")
            return

        buttons = []
        out = f"🎯 Results for '{text}':\n\n"

        for r in results[:10]:
            out += f"• {r['title']}\n"
            buttons.append([InlineKeyboardButton(r['title'], callback_data=f"movie_{r['id']}")])

        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        await msg.edit_text(out, reply_markup=InlineKeyboardMarkup(buttons))


# ---------- MOVIE ----------
async def movie_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    movie_id = q.data.split("_")[1]

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            m = await r.json()

    title = m.get("title")
    year = m.get("release_date","")[:4]
    rating = m.get("vote_average")
    overview = m.get("overview")

    genres = ", ".join([g['name'] for g in m.get("genres", [])])

    poster = f"https://image.tmdb.org/t/p/w500{m['poster_path']}"

    caption = f"""
╔══════════════════════════════════╗
║ 🎬 {title}
╚══════════════════════════════════╝

📅 Year : {year}
⭐ Rating : {rating}/10
🎭 Genres : {genres}

📖 {overview[:300]}...

👇 Watch below:
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Watch", url=f"{VIDLINK_BASE}{movie_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

    await q.message.reply_photo(photo=poster, caption=caption, reply_markup=kb)


# ---------- MAIN ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(movie_select, pattern="movie_"))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT, message_handler))

    print("Bot Running 🚀")
    app.run_polling()

main()
