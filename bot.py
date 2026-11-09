import os, requests, telebot, threading, time
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
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000))), daemon=True).start()

def get_fixtures(d):
    r = requests.get(f"{BASE}/fixtures?date={d}&timezone=Africa/Johannesburg", headers=HEADERS, timeout=20).json()
    return r.get('response', [])

@bot.message_handler(commands=['start','help'])
def start(m):
    bot.reply_to(m, "👋 WORLDPRO FREETIPS - YONKE INTO:\n\n/today - Yanamuhla ⚽\n/tomorrow - Yakusasa 📅\n/live - Edlalwayo manje 🔴\n/results - Imiphumela + HT ✅\n/team Barcelona - I-team 🔍\n/standings EPL - Ithebula 🏆\n/tip - Ithiphu 💰")

@bot.message_handler(commands=['today'])
def today(m):
    try:
        res = get_fixtures(str(date.today()))
        if not res:
            bot.reply_to(m, "⚽ Namuhla ayikho imidlalo emikhulu.\nZama /tomorrow 📅 noma /live 🔴"); return
        txt = "⚽ IMIDLALO YANAMUHLA:\n\n"
        for f in res[:25]:
            txt += f"{f['fixture']['date'][11:16]} {f['teams']['home']['name']} vs {f['teams']['away']['name']} - {f['league']['name']}\n"
        bot.reply_to(m, txt)
    except Exception as e: bot.reply_to(m, f"Phutha: {e}")

@bot.message_handler(commands=['tomorrow'])
def tomorrow(m):
    try:
        res = get_fixtures(str(date.today()+timedelta(days=1)))
        txt = "📅 IMIDLALO YAKUSASA:\n\n"
        if not res: txt += "Ayikho."
        for f in res[:25]:
            txt += f"{f['fixture']['date'][11:16]} {f['teams']['home']['name']} vs {f['teams']['away']['name']} - {f['league']['name']}\n"
        bot.reply_to(m, txt)
    except Exception as e: bot.reply_to(m, f"Phutha: {e}")

@bot.message_handler(commands=['live'])
def live(m):
    try:
        r = requests.get(f"{BASE}/fixtures?live=all&timezone=Africa/Johannesburg", headers=HEADERS, timeout=20).json()
        res = r.get('response', [])
        txt = "🔴 IMIDLALO EDALALWAYO MANJE:\n\n"
        if not res: txt += "Ayikho edlalwayo manje."
        for f in res[:20]:
            g = f['goals']; s = f['fixture']['status']['elapsed']
            txt += f"{s}' {f['teams']['home']['name']} {g['home']}-{g['away']} {f['teams']['away']['name']}\n"
        bot.reply_to(m, txt)
    except Exception as e: bot.reply_to(m, f"Phutha: {e}")

@bot.message_handler(commands=['results'])
def results(m):
    try:
        res = get_fixtures(str(date.today()-timedelta(days=1)))
        txt = "✅ IMIPHUMELA + HALF TIME:\n\n"
        if not res: txt += "Ayikho."
        for f in res[:25]:
            h=f['teams']['home']['name']; a=f['teams']['away']['name']; full=f['goals']; half=f['score']['halftime']
            txt += f"{h} {full['home']}-{full['away']} {a} (HT {half['home']}-{half['away']})\n"
        bot.reply_to(m, txt)
    except Exception as e: bot.reply_to(m, f"Phutha: {e}")

@bot.message_handler(commands=['team'])
def team(m):
    name = m.text.replace('/team','').strip()
    if not name: bot.reply_to(m, "Bhala: /team Barcelona"); return
    try:
        r = requests.get(f"{BASE}/teams?search={name}", headers=HEADERS, timeout=20).json()
        if r.get('response'):
            t=r['response'][0]['team']
            bot.reply_to(m, f"✅ {t['name']} - {t['country']} - {t['founded']}")
        else: bot.reply_to(m, "Angiyitholanga. Zama: /team Barcelona")
    except Exception as e: bot.reply_to(m, f"Phutha: {e}")

@bot.message_handler(commands=['standings'])
def standings(m):
    league = m.text.replace('/standings','').strip().upper()
    leagues = {"EPL":39,"LALIGA":140,"SERIE A":135,"BUNDESLIGA":78,"LIGUE 1":61,"PSL":288}
    lid = leagues.get(league, 39)
    try:
        r = requests.get(f"{BASE}/standings?league={lid}&season=2026", headers=HEADERS, timeout=20).json()
        table = r['response'][0]['league']['standings'][0]
        txt = f"🏆 ITHEBULA - {league}:\n\n"
        for t in table[:10]:
            txt += f"{t['rank']}. {t['team']['name']} - {t['points']} pts ({t['all']['played']} P)\n"
        bot.reply_to(m, txt)
    except Exception as e: bot.reply_to(m, f"Phutha: {e}\nZama: /standings EPL")

@bot.message_handler(commands=['tip'])
def tip(m):
    bot.reply_to(m, "💰 ITHIPHU YANAMUHLA:\n\nBheka /today bese ukhetha Over 1.5 Goals emidlalweni emikhulu.\nDlala ngokuhlakanipha, ungabhejeli konke! 🙏")

@bot.message_handler(func=lambda m: True)
def anything(m):
    bot.reply_to(m, "Thumela /help ukubona KONKE ⚽")

print("Bot starting FINAL...")
while True:
    try: bot.polling(none_stop=True, timeout=60)
    except Exception as e: print(e); time.sleep(5)
