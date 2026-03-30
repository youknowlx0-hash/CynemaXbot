import json, asyncio, aiohttp, datetime
from telegram import *
from telegram.ext import *

BOT_TOKEN = "YOUR_BOT_TOKEN"
TMDB_API_KEY = "YOUR_TMDB_KEY"

VIDLINK_BASE = "https://vidlink.pro/movie/"
MOVIE_FILE_BASE = "https://yourserver.com/movies/"

DB_FILE = "db.json"

# ---------------- DB ----------------
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
            "searches": 5,
            "bonus": 0,
            "joined": str(datetime.date.today())
        }
        save(db)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    name = update.effective_user.first_name

    user_init(user, name)

    # Referral system
    if context.args:
        ref = context.args[0].replace("ref_", "")
        if ref != user and user not in db.get(ref, {}).get("invited", []):
            db[ref]["referrals"] += 1
            db[ref]["invited"].append(user)
            db[ref]["bonus"] += 3
            save(db)

    text = f"""
╔══════════════════════════════════╗
║ 🎬  C Y N E M A  B O T
╚══════════════════════════════════╝

Hey {name}! 👋

🎬 Movies | 🌸 Anime | 📺 Series
⚡ Fast Search + Download

Use buttons below 👇
"""

    kb = [
        [InlineKeyboardButton("🎬 Movies", callback_data="movies")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


# ---------------- SEARCH ----------------
async def search_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

    return data.get("results", [])


# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user = str(q.from_user.id)

    if q.data == "movies":
        await q.message.reply_text("🎬 Send movie name:")

    elif q.data == "invite":
        link = f"https://t.me/YOUR_BOT_USERNAME?start=ref_{user}"

        text = f"""
╔══════════════════════════════════╗
║ 👥 REFERRAL
╚══════════════════════════════════╝

🔗 Link:
{link}

👥 Invites: {db[user]['referrals']}
🎁 Bonus: {db[user]['bonus']}
"""
        await q.message.reply_text(text)

    elif q.data == "stats":
        u = db[user]
        text = f"""
╔══════════════════════════════════╗
║ 📊 YOUR STATS
╚══════════════════════════════════╝

👤 {u['name']}
🔍 Searches: {u['searches'] + u['bonus']}
👥 Referrals: {u['referrals']}
📅 Joined: {u['joined']}
"""
        await q.message.reply_text(text)

    elif q.data == "cancel":
        await q.message.delete()


# ---------------- MESSAGE (SEARCH) ----------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    text = update.message.text

    if db[user]["searches"] + db[user]["bonus"] <= 0:
        await update.message.reply_text("❌ No searches left!")
        return

    msg = await update.message.reply_text("🔍 Searching...")

    results = await search_tmdb(text)

    if not results:
        await msg.edit_text("❌ No results found!")
        return

    buttons = []
    text_out = f"🎯 Results for '{text}':\n\n"

    for r in results[:10]:
        title = r["title"]
        text_out += f"• {title}\n"
        buttons.append([InlineKeyboardButton(title, callback_data=f"movie_{r['id']}")])

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    await msg.edit_text(text_out, reply_markup=InlineKeyboardMarkup(buttons))


# ---------------- MOVIE SELECT ----------------
async def movie_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    movie_id = q.data.split("_")[1]

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            m = await r.json()

    title = m.get("title", "Unknown")
    year = m.get("release_date", "N/A")[:4]
    rating = m.get("vote_average", "N/A")
    overview = m.get("overview", "No description")

    genres = ", ".join([g['name'] for g in m.get("genres", [])])
    poster = f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else None

    watch = f"{VIDLINK_BASE}{movie_id}"
    file = f"{MOVIE_FILE_BASE}{title.replace(' ', '_')}.mp4"

    caption = f"""
╔══════════════════════════════════╗
║ 🎬 {title}
╚══════════════════════════════════╝

📅 Year   : {year}
⭐ Rating : {rating}/10
🎭 Genres : {genres}

📖 Synopsis:
{overview[:300]}...

👇 Choose:
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Watch", url=watch)],
        [InlineKeyboardButton("📥 Download", url=file)],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

    if poster:
        await q.message.reply_photo(photo=poster, caption=caption, reply_markup=kb)
    else:
        await q.message.reply_text(caption, reply_markup=kb)


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(movie_select, pattern="movie_"))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT, message_handler))

    print("Bot Running 🚀")
    app.run_polling()

main()
