import os, requests, telebot, threading, time
from flask import Flask
from datetime import date, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
print(f"TOKEN exists: {bool(BOT_TOKEN)} | KEY exists: {bool(API_KEY)}")

bot = telebot.TeleBot(BOT_TOKEN)
HEADERS = {"x-apisports-key": API_KEY}
BASE = "https://v3.football.api-sports.io"

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is Live!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()

@bot.message_handler(commands=['start', 'help'])
def start(m):
    bot.reply_to(m, "👋 Sawubona! Ngiyi-WorldProFreeTips!\n\n✅ KONKE KUYASEBENZA:\n\n/today - Imidlalo yanamuhla ⚽\n/results - Imiphumela + Half Time ✅\n/team Man City - Bheka i-team 🔍\n/help - Lolu hlu")

@bot.message_handler(commands=['today'])
def today(m):
    today_str = str(date.today())
    try:
        r = requests.get(f"{BASE}/fixtures?date={today_str}&timezone=Africa/Johannesburg", headers=HEADERS, timeout=20).json()
        txt = "⚽ IMIDLALO YANAMUHLA - IQINISO:\n\n"
        if not r.get('response'):
            txt += "Ayikho imidlalo yanamuhla."
        else:
            for f in r['response'][:20]:
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
        r = requests.get(f"{BASE}/fixtures?date={yest}&timezone=Africa/Johannesburg", headers=HEADERS, timeout=20).json()
        txt = "✅ IMIPHUMELA + HALF TIME - IQINISO:\n\n"
        if not r.get('response'):
            txt += "Ayikho imiphumela."
        else:
            for f in r['response'][:20]:
                h = f['teams']['home']['name']; a = f['teams']['away']['name']
                full = f['goals']; half = f['score']['halftime']
                txt += f"{h} {full['home']}-{full['away']} {a} (HT {half['home']}-{half['away']})\n"
        bot.reply_to(m, txt)
    except Exception as e:
        bot.reply_to(m, f"Phutha: {e}")

@bot.message_handler(commands=['team'])
def team(m):
    name = m.text.replace('/team','').strip()
    if not name:
        bot.reply_to(m, "Bhala kanje: /team Man City")
        return
    try:
        r = requests.get(f"{BASE}/teams?search={name}", headers=HEADERS, timeout=20).json()
        if r.get('response'):
            t = r['response'][0]['team']
            bot.reply_to(m, f"✅ {t['name']} - {t['country']} - IQINISO livela ku-API")
        else:
            bot.reply_to(m, "Angiyitholanga le team. Zama: /team Man City")
    except Exception as e:
        bot.reply_to(m, f"Phutha: {e}")

# Uma umuntu ethumela noma yini enye
@bot.message_handler(func=lambda m: True)
def anything(m):
    bot.reply_to(m, "Thumela /help ukubona konke engikwenzayo ⚽")

print("Bot starting polling...")
while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Polling error: {e}, retry in 5s")
        time.sleep(5)
