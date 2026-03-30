import json
import aiohttp
from datetime import datetime
from telegram import *
from telegram.ext import *
from config import *

DB_FILE = "db.json"

# ---------- DATABASE ----------
def load():
    try:
        return json.load(open(DB_FILE))
    except:
        return {"users": {}}

def save(db):
    json.dump(db, open(DB_FILE, "w"), indent=4)

db = load()

# ---------- USER ----------
def add_user(uid, name, ref=None):
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": name,
            "search": START_SEARCH,
            "bonus": 0,
            "ref": 0,
            "joined": str(datetime.now().date()),
            "referred": False
        }

        if ref and ref != uid and ref in db["users"] and not db["users"][uid]["referred"]:
            db["users"][uid]["referred"] = True
            db["users"][ref]["ref"] += 1
            db["users"][ref]["bonus"] += REF_BONUS

# ---------- FORCE JOIN ----------
async def check_join(bot, uid):
    try:
        for ch in CHANNELS:
            m = await bot.get_chat_member(ch, uid)
            if m.status in ["left", "kicked"]:
                return False
        return True
    except:
        return False

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    name = update.effective_user.first_name

    ref = None
    if context.args:
        ref = context.args[0].replace("ref_", "")

    add_user(uid, name, ref)
    save(db)

    text = f"""🎬 *CYNEMA BOT*

Hey {name}! 👋

🎥 Movies | 🌸 Anime | 📺 Web Series

👇 Join & Verify First
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Channel 1", url=f"https://t.me/{CHANNELS[0][1:]}")],
        [InlineKeyboardButton("📢 Channel 2", url=f"https://t.me/{CHANNELS[1][1:]}")],
        [
            InlineKeyboardButton("🌐 Instagram", url=WEBSITE_URL),
            InlineKeyboardButton("💰 Earning Adda", url=MOVIES_URL)
        ],
        [InlineKeyboardButton("✅ VERIFY", callback_data="verify")]
    ])

    await update.message.reply_photo(START_IMG, caption=text, reply_markup=kb, parse_mode="Markdown")

# ---------- VERIFY ----------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = str(q.from_user.id)

    if not await check_join(context.bot, uid):
        await q.answer("Join channels first ❌")
        return

    await q.answer("Verified ✅")

    kb = ReplyKeyboardMarkup([
        ["🎬 Movies", "🌸 Anime"],
        ["📺 Web Series", "👥 Invite"],
        ["📊 Stats", "📩 Request"]
    ], resize_keyboard=True)

    await q.message.reply_text("🎉 Welcome!", reply_markup=kb)

# ---------- TMDB SEARCH ----------
async def search_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            d = await r.json()
    return d.get("results", [])[:5]

# ---------- MENU ----------
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    txt = update.message.text

    if txt == "🎬 Movies":
        context.user_data["mode"] = "movie"
        await update.message.reply_text("🎬 Send Movie Name:")
        return

    if txt == "🌸 Anime":
        context.user_data["mode"] = "anime"
        await update.message.reply_text("🌸 Send Anime Name:")
        return

    if txt == "📺 Web Series":
        context.user_data["mode"] = "series"
        await update.message.reply_text("📺 Send Series Name:")
        return

    if txt == "📊 Stats":
        u = db["users"][uid]
        total = u["search"] + u["bonus"]

        await update.message.reply_text(
            f"📊 Stats\n\n👤 {u['name']}\n🔍 {total}\n🎁 {u['bonus']}\n👥 {u['ref']}"
        )
        return

    if txt == "👥 Invite":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start=ref_{uid}"

        await update.message.reply_text(f"Invite & Earn:\n{link}")
        return

    if txt == "📩 Request":
        context.user_data["mode"] = "req"
        await update.message.reply_text("Send request:")
        return

    # SEARCH
    if context.user_data.get("mode") in ["movie", "anime", "series"]:

        user = db["users"][uid]
        total = user["search"] + user["bonus"]

        if total <= 0:
            await update.message.reply_text("❌ No Credits!")
            return

        res = await search_tmdb(txt)

        if not res:
            await update.message.reply_text("❌ No Results Found")
            return

        if user["bonus"] > 0:
            user["bonus"] -= 1
        else:
            user["search"] -= 1

        save(db)

        btn = [[InlineKeyboardButton(i.get("title") or i.get("name"), callback_data=f"id_{i['id']}")] for i in res]
        btn.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        await update.message.reply_text("Select:", reply_markup=InlineKeyboardMarkup(btn))

    # REQUEST
    if context.user_data.get("mode") == "req":
        await context.bot.send_message(ADMIN_ID, f"Request:\n{txt}")
        await update.message.reply_text("Sent")

# ---------- SELECT ----------
async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if data == "cancel":
        context.user_data.clear()
        await q.message.delete()
        return

    mid = data.split("_")[1]

    # movie
    url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={TMDB_API_KEY}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            m = await r.json()

    # fallback tv
    if not m.get("title"):
        url = f"https://api.themoviedb.org/3/tv/{mid}?api_key={TMDB_API_KEY}"
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                m = await r.json()

    title = m.get("title") or m.get("name")
    year = (m.get("release_date") or m.get("first_air_date") or "")[:4]
    rating = m.get("vote_average")
    overview = m.get("overview", "")

    link = f"{VIDLINK_BASE}{mid}"

    await q.message.reply_text(
        f"🎬 {title} ({year})\n⭐ {rating}\n\n{overview[:200]}...\n\n🔗 {link}"
    )

    context.user_data.clear()

# ---------- MAIN ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(select))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

    print("🔥 Bot Running")

    app.run_polling()

if __name__ == "__main__":
    main()
