import json, aiohttp, asyncio, random
from datetime import datetime
from telegram import *
from telegram.ext import *
from config import *

DB_FILE = "db.json"
db = {}

# ---------- DB ----------
def load_db():
    global db
    try:
        db = json.load(open(DB_FILE))
    except:
        db = {"users": {}, "referrals": {}}
    return db

def save_db():
    json.dump(db, open(DB_FILE,"w"), indent=4)

load_db()

# ---------- Async TMDB Search ----------
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

# ---------- Force Join Check ----------
async def check_join(user_id, context):
    for ch in CHANNELS:
        member = await context.bot.get_chat_member(ch, user_id)
        if member.status in ["left","kicked"]:
            return False
    return True

# ---------- Start + Referral ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    referred_id = None
    if args and args[0].startswith("ref_"):
        referred_id = args[0].replace("ref_","")

    if user_id not in db["users"]:
        db["users"][user_id] = {"coins":2,"bonus":0,"referrals":0,"joined":str(datetime.now().date()),"history":[],"watchlist":[],"referred_by":None}

        # Unique referral
        if referred_id and referred_id != user_id and db["users"][user_id]["referred_by"] is None:
            db["users"][user_id]["referred_by"] = referred_id
            db["users"][referred_id]["referrals"] += 1
            db["users"][referred_id]["bonus"] += 3
            if referred_id not in db["referrals"]:
                db["referrals"][referred_id] = []
            db["referrals"][referred_id].append(user_id)

    save_db()

    poster_text = f"""╔══════════════════════════════════╗
║  🎬✨  C Y N E M A  B O T       ║
╚══════════════════════════════════╝

Hey {update.effective_user.first_name}! 👋 Welcome to Cynema Bot Premium!

🌟 Stream & download:
├ 🎬 Movies
├ 🌸 Anime
├ 📺 Web Series
└ 🌍 All Languages

📌 Join channels below and tap ✅ Verify!
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Verify", callback_data="verify")],
        [InlineKeyboardButton("📺 Channel 1", url=f"https://t.me/{CHANNELS[0][1:]}"),
         InlineKeyboardButton("📺 Channel 2", url=f"https://t.me/{CHANNELS[1][1:]}")],
        [InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_URL)]
    ])
    await update.message.reply_photo(POSTER_URL, caption=poster_text, reply_markup=keyboard)

# ---------- Verify ----------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = str(q.from_user.id)
    if not await check_join(user_id, context):
        await q.answer("❌ Join all channels first!")
        return
    await q.answer("✅ Verified!")
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
        ["🎬 Movies","🌸 Anime"],
        ["📺 Web Series","👥 Invite Friends"],
        ["📊 My Stats","🔔 Request Movie/Anime"]
    ]
    kb = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await q.message.reply_text(menu_text, reply_markup=kb)

# ---------- Menu Handler ----------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    mode = context.user_data.get("mode")

    if text == "🎬 Movies":
        await update.message.reply_text("🔎 Send Movie Name:")
        context.user_data["mode"] = "movie"
        return
    if text == "🌸 Anime":
        await update.message.reply_text("🔎 Send Anime Name:")
        context.user_data["mode"] = "anime"
        return
    if text == "📺 Web Series":
        await update.message.reply_text("🔎 Send Web Series Name:")
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
        await update.message.reply_text("Please type the exact name of the movie, anime, or web series you want to request:")
        context.user_data["mode"] = "request"
        return

    # ---- Handle searches ----
    if mode in ["movie","anime","webseries"]:
        msg = await update.message.reply_text(f"⚡ Searching for '{text}' ...")
        results = await search_tmdb(text, mode)
        if not results:
            await msg.edit_text("❌ No results found!")
            return
        buttons = [[InlineKeyboardButton(r['title'], callback_data=f"sel_{mode}_{r['id']}")] for r in results]
        kb = InlineKeyboardMarkup(buttons)
        await msg.edit_text(f"🎯 Results for '{text}':", reply_markup=kb)
        return

    if mode == "request":
        await context.bot.send_message(ADMIN_ID, f"📌 Request from {update.effective_user.first_name} ({user_id}): {text}")
        await update.message.reply_text("✅ Your request has been sent to the admins!")
        context.user_data["mode"] = None
        return

# ---------- Selection Callback ----------
async def selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    _, type_, id_ = data.split("_")
    url = f"https://api.themoviedb.org/3/{'tv' if type_=='webseries' else 'movie'}/{id_}?api_key={TMDB_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            r = await r.json()
    title = r.get("title") or r.get("name")
    vote = r.get("vote_average","N/A")
    poster = f"https://image.tmdb.org/t/p/w500{r['poster_path']}" if r.get("poster_path") else POSTER_URL
    watch_url = f"{VIDLINK_BASE}{id_}"

    await q.message.reply_text(
        f"🎬 *{title}*\n⭐ Rating: {vote}\n📺 Watch/Download: {watch_url}",
        parse_mode="Markdown"
    )

# ---------- Main ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(selection_callback, pattern="sel_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    print("🔥 Cynema Premium Bot Running...")
    app.run_polling()

if __name__=="__main__":
    main()
