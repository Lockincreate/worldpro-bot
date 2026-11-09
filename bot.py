import os, requests, telebot
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
bot = telebot.TeleBot(BOT_TOKEN)
HEADERS = {"x-apisports-key": API_KEY}
BASE = "https://v3.football.api-sports.io"

@bot.message_handler(commands=['today'])
def today(m):
    r = requests.get(f"{BASE}/fixtures?date=2026-11-09&timezone=Africa/Johannesburg", headers=HEADERS).json()
    txt = "⚽ IMIDLALO YANAMUHLA - IQINISO:\n\n"
    for f in r['response'][:15]:
        h = f['teams']['home']['name']; a = f['teams']['away']['name']
        t = f['fixture']['date'][11:16]
        txt += f"{t} {h} vs {a} - {f['league']['name']}\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['results'])
def results(m):
    r = requests.get(f"{BASE}/fixtures?date=2026-11-08&timezone=Africa/Johannesburg", headers=HEADERS).json()
    txt = "✅ IMIPHUMELA + HALF TIME - IQINISO:\n\n"
    for f in r['response'][:15]:
        h = f['teams']['home']['name']; a = f['teams']['away']['name']
        full = f['goals']; half = f['score']['halftime']
        txt += f"{h} {full['home']}-{full['away']} {a} (HT {half['home']}-{half['away']})\n"
    bot.reply_to(m, txt)

@bot.message_handler(commands=['team'])
def team(m):
    name = m.text.replace('/team','').strip()
    r = requests.get(f"{BASE}/teams?search={name}", headers=HEADERS).json()
    if r['response']:
        t = r['response'][0]['team']
        bot.reply_to(m, f"✅ {t['name']} - {t['country']} - IQINISO livela ku-API-Football\nStadium: {t['venue_name'] if 'venue_name' in t else 'N/A'}")
    else:
        bot.reply_to(m, "Angiyitholanga le team. Zama igama eliphelele: Man City")

bot.polling()m 
