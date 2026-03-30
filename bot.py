import json, time, random, requests
from telegram import *
from telegram.ext import *
from config import *

# ---------------- DB ----------------
def load():
    try:
        return json.load(open("db.json"))
    except:
        return {}

def save(db):
    json.dump(db, open("db.json", "w"), indent=4)

db = load()

# ---------------- FORCE JOIN ----------------
async def check_join(user_id, bot):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    args = context.args

    if user not in db:
        db[user] = {
            "coins": 10,
            "ref": 0,
            "history": [],
            "watchlist": [],
            "last_daily": 0
        }

        # Referral
        if args:
            ref = args[0]
            if ref in db and ref != user:
                db[ref]["coins"] += 5
                db[ref]["ref"] += 1

        save(db)

    # Force Join
    if not await check_join(user, context.bot):
        btn = [
            [InlineKeyboardButton("📢 Join 1", url=f"https://t.me/{CHANNELS[0][1:]}")],
            [InlineKeyboardButton("📢 Join 2", url=f"https://t.me/{CHANNELS[1][1:]}")],
            [InlineKeyboardButton("✅ Verify", callback_data="verify")]
        ]
        await update.message.reply_text("⚠️ Join channels first!", reply_markup=InlineKeyboardMarkup(btn))
        return

    buttons = [
        [InlineKeyboardButton("🎬 Search", callback_data="search")],
        [InlineKeyboardButton("⭐ Watchlist", callback_data="watch")],
        [InlineKeyboardButton("🧠 Recommend", callback_data="rec")],
        [InlineKeyboardButton("🎁 Daily Reward", callback_data="daily")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")]
    ]

    await update.message.reply_text(
        "🎬 CynemaX Ultra Pro\n\nSelect option:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- VERIFY ----------------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = str(q.from_user.id)

    if await check_join(user, context.bot):
        await q.edit_message_text("✅ Verified! Use /start")
    else:
        await q.answer("❌ Not joined!", show_alert=True)

# ---------------- TMDB ----------------
def search_tmdb(q):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={q}"
    r = requests.get(url).json()
    if r["results"]:
        return r["results"][0]
    return None

# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = str(q.from_user.id)

    if q.data == "search":
        await q.message.reply_text("🔍 Send movie name")

    elif q.data == "watch":
        wl = db[user]["watchlist"]
        await q.message.reply_text("\n".join(wl) if wl else "❌ Empty")

    elif q.data == "rec":
        hist = db[user]["history"]
        if hist:
            await q.message.reply_text(f"🎯 Try: {random.choice(hist)}")
        else:
            await q.message.reply_text("Search first")

    elif q.data == "daily":
        now = time.time()
        if now - db[user]["last_daily"] > 86400:
            db[user]["coins"] += 5
            db[user]["last_daily"] = now
            save(db)
            await q.message.reply_text("🎁 +5 coins")
        else:
            await q.message.reply_text("⏳ Come tomorrow")

    elif q.data == "stats":
        d = db[user]
        await q.message.reply_text(f"""
📊 STATS

💰 Coins: {d['coins']}
👥 Referrals: {d['ref']}
⭐ Watchlist: {len(d['watchlist'])}
""")

# ---------------- SEARCH ----------------
async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)
    text = update.message.text

    if db[user]["coins"] <= 0:
        await update.message.reply_text("❌ No coins left")
        return

    m = search_tmdb(text)

    if m:
        title = m.get("title") or m.get("name")
        rating = m.get("vote_average", "N/A")

        db[user]["coins"] -= 1
        db[user]["history"].append(title)
        save(db)

        btn = [[InlineKeyboardButton("⭐ Add Watchlist", callback_data=f"add_{title}")]]
        await update.message.reply_text(
            f"🎬 {title}\n⭐ {rating}",
            reply_markup=InlineKeyboardMarkup(btn)
        )
    else:
        await update.message.reply_text("❌ Not found")

# ---------------- ADD WATCH ----------------
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = str(q.from_user.id)

    movie = q.data.replace("add_", "")
    db[user]["watchlist"].append(movie)
    save(db)

    await q.answer("Added to Watchlist")

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(add, pattern="add_"))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT, msg))

    print("🔥 CynemaX Ultra Pro Running...")
    app.run_polling()

main()
