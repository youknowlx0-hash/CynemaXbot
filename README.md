🎬 CynemaXbot

CynemaXbot is a Telegram media discovery bot built with Python, python-telegram-bot, aiohttp, and the TMDB API.

It allows users to search for Movies, Anime, and Web Series, manage search credits, invite friends for bonus searches, and submit movie requests.

---

✨ Features

- 🎬 Movie Search
- 🌸 Anime Search
- 📺 Web Series Search
- 🔎 TMDB-powered search
- 📢 Force Join verification
- 👥 Referral / Invite system
- 🎁 Bonus search credits
- 📊 User statistics
- 📩 Movie request system
- 💾 JSON-based user database
- ⚡ Async API requests using "aiohttp"
- 🤖 Telegram Bot API
- 🔗 Media/link integration through configurable base URL
- 🌍 Supports multiple languages and media types

---

🛠️ Tech Stack

- Python 3
- python-telegram-bot
- aiohttp
- TMDB API
- JSON Database
- Telegram Bot API

---

📂 Project Structure

CynemaXbot/
│
├── bot.py
├── config.py
├── db.json
├── requirements.txt
├── Procfile
└── README.md

---

⚙️ Configuration

Create or edit "config.py":

BOT_TOKEN = "YOUR_BOT_TOKEN"

TMDB_API_KEY = "YOUR_TMDB_API_KEY"

ADMIN_ID = 123456789

CHANNELS = [
    "@your_channel_1",
    "@your_channel_2"
]

START_IMG = "YOUR_START_IMAGE_URL"

WEBSITE_URL = "YOUR_INSTAGRAM_OR_WEBSITE_URL"

MOVIES_URL = "YOUR_EARNING_OR_MOVIE_CHANNEL_URL"

VIDLINK_BASE = "YOUR_MEDIA_BASE_URL"

START_SEARCH = 3
REF_BONUS = 3

Configuration Details

Variable| Description
"BOT_TOKEN"| Telegram bot token
"TMDB_API_KEY"| TMDB API key
"ADMIN_ID"| Admin Telegram user ID
"CHANNELS"| Force-join channels
"START_IMG"| Start/menu image
"WEBSITE_URL"| Website/Instagram URL
"MOVIES_URL"| Additional channel/link
"VIDLINK_BASE"| Media/link base URL
"START_SEARCH"| Initial free searches
"REF_BONUS"| Referral bonus searches

---

🔑 Get Telegram Bot Token

Create a bot using @BotFather on Telegram and copy the generated bot token.

Add it to:

BOT_TOKEN = "YOUR_BOT_TOKEN"

---

🎬 Get TMDB API Key

Create a TMDB account and generate an API key from your account settings.

Then add:

TMDB_API_KEY = "YOUR_TMDB_API_KEY"

The bot uses TMDB to search for:

- Movies
- TV Shows
- Anime
- Other media results supported by TMDB

---

📦 Installation

Clone the repository:

git clone https://github.com/youknowlx0-hash/CynemaXbot.git

Enter the directory:

cd CynemaXbot

Install dependencies:

pip install -r requirements.txt

Configure your "config.py".

Then run:

python bot.py

If everything is configured correctly, you should see:

🔥 Bot Running

---

🤖 Bot Flow

"/start"

When a user starts the bot:

1. User is registered in "db.json"
2. Referral information is processed
3. Force-join buttons are displayed
4. User joins the required channels
5. User presses VERIFY
6. Main menu is displayed

---

🎬 Movies

Select:

🎬 Movies

Then send a movie name.

The bot searches TMDB and displays up to 5 results.

Select a result to receive:

- 🎬 Title
- 📅 Release year
- ⭐ Rating
- 📝 Overview
- 🔗 Configured media link

---

🌸 Anime

Select:

🌸 Anime

Then send the anime name.

The bot searches TMDB and returns matching results.

---

📺 Web Series

Select:

📺 Web Series

Then send the series name.

The bot searches TMDB for matching movies/TV content.

---

👥 Referral System

Every user receives a personal referral link:

https://t.me/YOUR_BOT?start=ref_USER_ID

Users can share their link with friends.

Referral information is stored in "db.json".

The configured referral reward is controlled by:

REF_BONUS = 3

---

📊 My Stats

Users can check:

- 👤 Name
- 🆔 Telegram ID
- 🔍 Remaining searches
- 🆓 Free searches
- 🎁 Bonus searches
- 👥 Referrals
- 📅 Join date

---

📩 Movie Request

Users can select:

📩 Movie Request

and send a request.

The request is forwarded to the configured:

ADMIN_ID

---

💾 Database

The bot uses a simple JSON database:

db.json

Example structure:

{
    "users": {
        "123456789": {
            "name": "User",
            "search": 3,
            "bonus": 0,
            "ref": 0,
            "joined": "2026-08-14",
            "referred": false
        }
    }
}

«For larger deployments, consider migrating from JSON to SQLite, PostgreSQL, or MongoDB.»

---

🔐 Security

Never upload sensitive credentials such as:

BOT_TOKEN
TMDB_API_KEY
ADMIN_ID

directly into a public repository.

For production deployments, environment variables are recommended.

---

🚀 Deployment

The project includes a "Procfile", making it suitable for platforms that support Python worker processes.

Typical command:

worker: python bot.py

You can also run it directly on:

- Termux
- Linux VPS
- Railway
- Render
- Other Python-compatible hosting platforms

---

📱 Termux

Install the required packages:

pkg update
pkg install python git

Clone the repository:

git clone https://github.com/youknowlx0-hash/CynemaXbot.git
cd CynemaXbot

Install Python dependencies:

pip install -r requirements.txt

Run:

python bot.py

---

⚠️ Disclaimer

CynemaXbot is intended as a media discovery and Telegram bot development project.

The bot uses TMDB for metadata/search information. Any external media links or content integrations configured through "VIDLINK_BASE" are the responsibility of the operator.

Make sure your deployment and content distribution comply with applicable laws, copyright rules, and the terms of the services you use.

---

👨‍💻 Developer

CynemaXbot

GitHub:
https://github.com/youknowlx0-hash/CynemaXbot

---

⭐ Support

If you find this project useful:

⭐ Star the repository
🍴 Fork the repository
🐛 Report issues
💡 Contribute improvements

---

🎬 CynemaXbot — Search. Discover. Enjoy.
