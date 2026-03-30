import json, aiohttp, asyncio
from datetime import datetime, timedelta
from telegram import *
from telegram.ext import *
from config import *

DB_FILE = "db.json"

# ---------- DB ----------
def load():
    try: return json.load(open(DB_FILE))
    except: return {"users":{}, "popup":"Join our channel 🔥"}

def save(db):
    json.dump(db, open(DB_FILE,"w"), indent=4)

db = load()

# ---------- USER INIT ----------
def user_add(uid,name,ref=None):
    if uid not in db["users"]:
        db["users"][uid] = {
            "name":name,
            "search":START_SEARCH,
            "bonus":0,
            "ref":0,
            "joined":str(datetime.now().date()),
            "referred":False,
            "last_popup":None
        }

        # referral
        if ref and ref!=uid and ref in db["users"] and not db["users"][uid]["referred"]:
            db["users"][uid]["referred"] = True
            db["users"][ref]["ref"] += 1
            db["users"][ref]["bonus"] += REF_BONUS

# ---------- FORCE JOIN ----------
async def join_check(bot, uid):
    try:
        for ch in CHANNELS:
            m = await bot.get_chat_member(ch, uid)
            if m.status in ["left","kicked"]:
                return False
        return True
    except:
        return False

# ---------- START ----------
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    u = str(update.effective_user.id)
    name = update.effective_user.first_name

    ref = None
    if context.args:
        ref = context.args[0].replace("ref_","")

    user_add(u,name,ref)
    save(db)

    text = f"""╔══════════════════════════════════╗
║  🎬✨  C I N E V E R S E  B O T  ║
╚══════════════════════════════════╝

Hey {name}! 👋 Welcome to the Ultimate Media Bot!

🌟 What you can stream & download:
├ 🎬 Movies
├ 🌸 Anime
├ 📺 Web Series
└ 🌍 All Languages

📌 Join both channels below then verify!
"""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel 1", url=f"https://t.me/{CHANNELS[0][1:]}")],
        [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/{CHANNELS[1][1:]}")],
        [InlineKeyboardButton("🌐 Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("🎬 Movies", callback_data="movies")],
        [InlineKeyboardButton("✅ I AM VERIFIED", callback_data="verify")]
    ])

    await update.message.reply_text(text, reply_markup=kb)

# ---------- VERIFY ----------
async def verify(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = str(q.from_user.id)

    if not await join_check(context.bot, uid):
        await q.answer("Join channels first ❌")
        return

    await q.answer("Verified ✅")

    kb = ReplyKeyboardMarkup([
        ["🎬 Movies","🌸 Anime"],
        ["📺 Web Series","👥 Invite"],
        ["📊 Stats","📩 Request"]
    ], resize_keyboard=True)

    await q.message.reply_text("Select option 👇", reply_markup=kb)

# ---------- SEARCH ----------
async def tmdb(q):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={q}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            d = await r.json()
    return d.get("results",[])[:5]

# ---------- MENU ----------
async def menu(update:Update, context:ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    txt = update.message.text

    # popup 24h
    now = datetime.now()
    last = db["users"][uid].get("last_popup")
    if not last or (now - datetime.fromisoformat(last)) > timedelta(hours=24):
        await update.message.reply_text(f"📢 {db.get('popup','Join channel')}")
        db["users"][uid]["last_popup"] = now.isoformat()
        save(db)

    if txt=="🎬 Movies":
        context.user_data["mode"]="movie"
        await update.message.reply_text("Send movie name:")
        return

    if txt=="📊 Stats":
        u=db["users"][uid]
        await update.message.reply_text(f"""╔══════════════════════════════════╗
║  📊  Y O U R  S T A T S
╚══════════════════════════════════╝

👤 {u['name']}
🆔 {uid}
🔍 {u['search']}
🎁 {u['bonus']}
👥 {u['ref']}
📅 {u['joined']}
""")
        return

    if txt=="👥 Invite":
        link=f"https://t.me/YOUR_BOT?start=ref_{uid}"
        u=db["users"][uid]
        await update.message.reply_text(f"""╔══════════════════════════════════╗
║  👥  R E F E R R A L
╚══════════════════════════════════╝

{link}

Invites: {u['ref']}
Bonus: {u['bonus']}
""")
        return

    if txt=="📩 Request":
        context.user_data["mode"]="req"
        await update.message.reply_text("Send request:")
        return

    # SEARCH
    if context.user_data.get("mode")=="movie":
        res = await tmdb(txt)
        btn = [[InlineKeyboardButton(i["title"], callback_data=f"m_{i['id']}")] for i in res]
        btn.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        await update.message.reply_text("Select:", reply_markup=InlineKeyboardMarkup(btn))

    if context.user_data.get("mode")=="req":
        await context.bot.send_message(ADMIN_ID,f"Request from {uid}: {txt}")
        await update.message.reply_text("Sent ✅")

# ---------- SELECT ----------
async def select(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if data=="cancel":
        await q.message.delete()
        return

    mid = data.split("_")[1]

    url=f"https://api.themoviedb.org/3/movie/{mid}?api_key={TMDB_API_KEY}"

    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            m=await r.json()

    title=m.get("title")
    year=m.get("release_date","")[:4]
    rating=m.get("vote_average")
    overview=m.get("overview","")

    watch=f"{VIDLINK_BASE}{mid}"

    await q.message.reply_text(f"""🎬 {title}
📅 {year}
⭐ {rating}

{overview[:200]}...

▶️ {watch}
""")

# ---------- ADMIN ----------
async def admin(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: return

    txt = update.message.text

    if txt.startswith("/broadcast"):
        msg = txt.replace("/broadcast ","")
        for u in db["users"]:
            try:
                await context.bot.send_message(u,msg)
            except: pass

    if txt.startswith("/popup"):
        db["popup"]=txt.replace("/popup ","")
        save(db)
        await update.message.reply_text("Popup updated")

# ---------- MAIN ----------
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    await app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(select))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    app.add_handler(MessageHandler(filters.COMMAND, admin))

    print("🔥 Cineverse Bot Running")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__=="__main__":
    asyncio.run(main())
