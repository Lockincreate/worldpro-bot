import os, requests, telebot, threading
from flask import Flask
from datetime import date, timedelta
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
bot = telebot.TeleBot(BOT_TOKEN)
HEADERS = {"x-apisports-key": API_KEY}
BASE = "https://v3.football.api-sports.io"
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Live!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))).start()
@bot.message_handler(commands=['today'])
def today(m):
    today_str = str(date.today())
    try:
        r = requests.get(f"{BASE}/fixtures?date={today_str}&timezone=Africa/Johannesburg", headers=HEADERS, timeout=15).json()
        txt = "⚽ IMIDLALO YANAMUHLA - IQINISO:\n\n"
        if not r.get('response'):
            txt += "Ayikho imidlalo yanamuhla."
        for f in r['response'][:15]:
            h = f['teams']['home']['name']; a = f['teams']['away']['name']
            t = f['fixture']['date'][11:16]
            txt += f"{t} {h} vs {a} - {f['league']['name']}\n"
        bot.reply_to(m, txt)
    except Exception as e:
        bot.reply_to(m, f"Phutha: {e}")
@bot.message_handler(commands=['results'])
def results(m):
    yest = str(date.today() - timedelta(days=1))
    try:
        r = requests.get(f"{BASE}/fixtures?date={yest}&timezone=Africa/Johannesburg", headers=HEADERS, timeout=15).json()
        txt = "✅ IMIPHUMELA + HALF TIME - IQINISO:\n\n"
        for f in r['response'][:15]:
            h = f['teams']['home']['name']; a = f['teams']['away']['name']
            full = f['goals']; half = f['score']['halftime']
            txt += f"{h} {full['home']}-{full['away']} {a} (HT {half['home']}-{half['away']})\n"
        bot.reply_to(m, txt)
    except Exception as e:
        bot.reply_to(m, f"Phutha: {e}")
@bot.message_handler(commands=['team'])
def team(m):
    name = m.text.replace('/team','').strip()
    try:
        r = requests.get(f"{BASE}/teams?search={name}", headers=HEADERS, timeout=15).json()
        if r.get('response'):
            t = r['response'][0]['team']
            bot.reply_to(m, f"✅ {t['name']} - {t['country']} - IQINISO")
        else:
            bot.reply_to(m, "Angiyitholanga le team. Zama: /team Man City")
    except Exception as e:
        bot.reply_to(m, f"Phutha: {e}")
bot.polling()
