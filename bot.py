import json, requests, random, asyncio
from datetime import datetime
from telegram import *
from telegram.ext import *
from config import *

DB_FILE = "db.json"

# --------- DB ----------
def load_db():
    try:
        return json.load(open(DB_FILE))
    except:
        return {"users": {}, "referrals": {}}

def save_db(db):
    json.dump(db, open(DB_FILE, "w"), indent=4)

db = load_db()

# --------- TMDB Search ----------
def search_movie(name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={name}"
    r = requests.get(url).json()
    if r.get("results"):
        m = r["results"][0]
        return {
            "title": m["title"],
            "vote": m["vote_average"],
            "poster": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get('poster_path') else None,
            "link": f"https://www.themoviedb.org/movie/{m['id']}"
        }
    return None

# --------- Force Join ----------
async def check_join(user_id, context):
    for ch in CHANNELS:
        member = await context.bot.get_chat_member(ch, user_id)
        if member.status in ["left", "kicked"]:
            return False
    return True

# --------- Start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ref_code = None
    if context.args:
        ref_code = context.args[0].replace("ref_", "")

    if user_id not in db["users"]:
        db["users"][user_id] = {
            "coins": 2,
            "bonus": 0,
            "referrals": 0,
            "joined": str(datetime.now().date()),
            "history": [],
            "watchlist": []
        }
        save_db(db)

    # Handle referral
    if ref_code and ref_code in db["users"] and ref_code != user_id:
        db["users"][ref_code]["referrals"] += 1
        db["users"][ref_code]["bonus"] += 3
        save_db(db)

    # Poster + description
    poster_text = f"""╔══════════════════════════════════╗
║  🎬✨  C Y N E M A  B O T       ║
╚══════════════════════════════════╝

Hey {update.effective_user.first_name}! 👋 Welcome to the Ultimate Media Bot!

🌟 Stream & download:
├ 🎬 Movies (Hollywood/Bollywood)
├ 🌸 Anime — subbed & dubbed
├ 📺 Web Series — Netflix, Prime, Disney+
└ 🌍 All Languages

📌 Join both channels below, then tap ✅ Verify!
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Verify", callback_data="verify")],
        [InlineKeyboardButton("📺 Channel 1", url=f"https://t.me/{CHANNELS[0][1:]}"),
         InlineKeyboardButton("📺 Channel 2", url=f"https://t.me/{CHANNELS[1][1:]}")],
        [InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_URL)]
    ])
    await update.message.reply_photo(POSTER_URL, caption=poster_text, reply_markup=keyboard)

# --------- Verify ----------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = str(q.from_user.id)
    joined = await check_join(user_id, context)
    if not joined:
        await q.answer("❌ Join all channels first!")
        return
    await q.answer("✅ Verified!")

    # Main Menu
    menu_text = f"""╔══════════════════════════════════╗
║  🎬  C Y N E M A  M E N U        ║
╚══════════════════════════════════╝

Choose what you want to find:
🎬 Movies
🌸 Anime
📺 Web Series
Use the keyboard below!
"""
    buttons = [
        ["🎬 Movies", "🌸 Anime"],
        ["📺 Web Series", "👥 Invite Friends"],
        ["📊 My Stats", "🔔 Request Movie/Anime"]
    ]
    kb = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await q.message.reply_text(menu_text, reply_markup=kb)

# --------- Menu / Keyboard Handler ----------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    mode = context.user_data.get("mode")

    if text == "🎬 Movies":
        await update.message.reply_text("Send Movie Name:")
        context.user_data["mode"] = "movie"
        return
    if text == "🌸 Anime":
        await update.message.reply_text("Send Anime Name:")
        context.user_data["mode"] = "anime"
        return
    if text == "📺 Web Series":
        await update.message.reply_text("Send Web Series Name:")
        context.user_data["mode"] = "webseries"
        return
    if text == "👥 Invite Friends":
        link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
        stats = db["users"][user_id]
        msg = f"""╔══════════════════════════════════╗
║  👥  R E F E R R A L             ║
╚══════════════════════════════════╝

🔗 Your Invite Link:
{link}

📊 Stats:
├ 👫 Friends Invited : {stats['referrals']}
├ 🎁 Bonus Searches  : {stats['bonus']}
├ 🔍 Searches Left   : {stats['coins']}
└ 🎯 Next Reward At  : 2 invites
"""
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Link", callback_data="copy_link")],
            [InlineKeyboardButton("🔗 Share Link", switch_inline_query=link)]
        ])
        await update.message.reply_text(msg, reply_markup=kb)
        return
    if text == "📊 My Stats":
        stats = db["users"][user_id]
        msg = f"""╔══════════════════════════════════╗
║  📊  Y O U R  S T A T S          ║
╚══════════════════════════════════╝

👤 Name      : {update.effective_user.first_name}
🆔 User ID   : {user_id}
🔍 Searches  : {stats['coins']} remaining
  ├ 🆓 Free  : {stats['coins']}
  └ 🎁 Bonus : {stats['bonus']}
👥 Referrals : {stats['referrals']} friends
📅 Joined    : {stats['joined']}
"""
        await update.message.reply_text(msg)
        return
    if text == "🔔 Request Movie/Anime":
        await update.message.reply_text(
            "Please type the exact name of the movie, anime, or web series you want to request from the admins:"
        )
        context.user_data["mode"] = "request"
        return

    # Handle movie/anime/webseries/request input
    if mode in ["movie", "anime", "webseries"]:
        movie_info = search_movie(text)
        if not movie_info:
            await update.message.reply_text("❌ Not found!")
            return

        stats = db["users"][user_id]
        if stats["coins"] <= 0:
            await update.message.reply_text("❌ No coins left!")
            return
        stats["coins"] -= 1
        stats["history"].append(movie_info["title"])
        save_db(db)

        msg = await update.message.reply_photo(
            movie_info["poster"] if movie_info["poster"] else POSTER_URL,
            caption=f"🎬 {movie_info['title']}\n⭐ {movie_info['vote']}\n📎 Link: {movie_info['link']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{user_id}")]
            ])
        )
        await asyncio.sleep(50)
        try:
            await msg.delete()
        except:
            pass
        return

    if mode == "request":
        await update.message.reply_text(
            f"✅ Your request '{text}' has been sent to the admins!"
        )
        context.user_data["mode"] = None
        return

# --------- Cancel Callback ----------
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.message.delete()
        await q.answer("✅ Deleted!")
    except:
        await q.answer("❌ Already deleted")

# --------- Main ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(cancel_callback, pattern="cancel_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("Cynema Premium Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
